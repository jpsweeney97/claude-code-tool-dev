# Delegation Capability — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the `/delegate` capability — a skill that delegates coding tasks to Codex CLI (`codex exec`) for autonomous execution with credential scanning, safety gates, and analytics.

**Architecture:** An adapter script (`codex_delegate.py`) with a 14-step pipeline handles all safety checks and subprocess execution. Two shared modules (`credential_scan.py`, `event_log.py`) are extracted from existing scripts for reuse. The skill (`SKILL.md`, already created) orchestrates argument parsing, adapter invocation, and change review.

**Tech Stack:** Python 3.11+, no external dependencies. Subprocess via `subprocess.run`. Tests via pytest. All paths relative to `packages/plugins/cross-model/`.

**Design Spec:** `docs/plans/2026-03-06-delegation-capability-design.md` — the authoritative source for all field names, enum values, pipeline steps, and decision rationale.

**Codex Review Round 1:** Deep-review dialogue (evaluative, 5/8 turns, thread `019cc469-92bd-7090-93f9-2df20f7cb982`). 13 findings (F1-F13) integrated below. Key changes:
- F1+F8: Split `_parse_and_validate_input()` → `_parse_input()` + `_validate_input()` so analytics emits for credential blocks
- F2: `_validate_events()` uses `_REQUIRED_FIELDS` keys instead of hardcoded tuple
- F3: `delegations_completed_total` counts only `dispatched=true` events
- F4: Added `run()` orchestrator tests
- F5: Split `_SECRET_PATHSPECS` into `_SECRET_EXACT_NAMES` + `_SECRET_GLOBS`
- F6: Creation-ownership — adapter cleans output only, skill cleans input
- F7+F9: Delegation excluded from `active_utc_days`, `schema_version_counts`, `invocations_completed_total`
- F10: `model` and `reasoning_effort` added to `_REQUIRED_FIELDS`
- F11: Period filtering added for `delegation_outcomes`
- F12: Root-level test alignment noted
- F13: `_compute_delegation()` handles non-canonical types defensively

**Codex Review Round 2:** Adversarial dialogue (5/10 turns, thread `019cc48a-e680-7b21-be1a-7c62650a072f`). 10 blocking + 6 advisory findings. Key changes:
- B1: F10 cascade — add `model` + `reasoning_effort` to both `_make_delegation_event()` test helpers
- B2: F7/F9 type mismatch — `active_utc_days == 0` not `== []`
- B3: Add `import subprocess` to `test_codex_delegate.py` header
- B4: Add success-path orchestrator test (`test_success_path`)
- B5: Add period filtering test with shared `now` threading
- B6: Update design spec `_REQUIRED_FIELDS` to 17 fields + `included` key in template
- B7: F12 root-level test update promoted from risk note to task
- B8: NEW — dispatched-analytics bug: track `did_dispatch` flag in `run()` exception handlers
- B9: NEW — `_parse_jsonl` usable count: filter unknown event types before counting
- B10: NEW — verification commands must include root-level test suite
- A1 (advisory): F2 import pattern simplified to `read_events._REQUIRED_FIELDS`
- A2 (advisory): F6 risk note removed (design spec already correct)
- A3 (advisory): Task 8 exit code claim fixed (exit 1 deterministic without codex)

---

## Task 1: Create `scripts/credential_scan.py`

Extract credential detection logic from `codex_guard.py` into a shared public module. Both `codex_guard.py` (hook) and `codex_delegate.py` (adapter) will import from this.

**Files:**
- Create: `scripts/credential_scan.py`
- Test: `tests/test_credential_scan.py`

**Step 1: Write the failing tests**

Create `tests/test_credential_scan.py`:

```python
"""Tests for credential_scan module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.credential_scan import ScanResult, scan_text


class TestScanResult:
    """ScanResult dataclass shape."""

    def test_allow_result(self) -> None:
        r = ScanResult(action="allow", tier=None, reason=None)
        assert r.action == "allow"
        assert r.tier is None

    def test_block_result(self) -> None:
        r = ScanResult(action="block", tier="strict", reason="AWS key")
        assert r.action == "block"
        assert r.tier == "strict"


class TestScanTextStrict:
    """Strict tier — hard-block, near-zero FP."""

    def test_aws_access_key(self) -> None:
        result = scan_text("key is AKIAIOSFODNN7EXAMPLE")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_pem_private_key(self) -> None:
        result = scan_text("-----BEGIN RSA PRIVATE KEY-----")
        assert result.action == "block"
        assert result.tier == "strict"

    def test_jwt_token(self) -> None:
        result = scan_text("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U")
        assert result.action == "block"
        assert result.tier == "strict"


class TestScanTextContextual:
    """Contextual tier — block unless placeholder suppression."""

    def test_github_pat_blocked(self) -> None:
        result = scan_text("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_github_pat_suppressed_by_placeholder(self) -> None:
        result = scan_text("example: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn")
        assert result.action == "allow"

    def test_openai_sk_key(self) -> None:
        result = scan_text("sk-" + "a" * 40)
        assert result.action == "block"
        assert result.tier == "contextual"

    def test_bearer_token(self) -> None:
        result = scan_text("Authorization: Bearer abcdefghij1234567890xyz")
        assert result.action == "block"
        assert result.tier == "contextual"


class TestScanTextBroad:
    """Broad tier — shadow only, no blocking."""

    def test_password_assignment_shadows(self) -> None:
        result = scan_text("password = mysecretvalue123")
        assert result.action == "shadow"
        assert result.tier == "broad"


class TestScanTextClean:
    """Clean text — no matches."""

    def test_normal_text_allows(self) -> None:
        result = scan_text("Fix the flaky test in auth_test.py")
        assert result.action == "allow"
        assert result.tier is None
        assert result.reason is None

    def test_empty_string_allows(self) -> None:
        result = scan_text("")
        assert result.action == "allow"


class TestScanTextPriority:
    """Strict takes precedence over contextual."""

    def test_strict_before_contextual(self) -> None:
        text = "AKIAIOSFODNN7EXAMPLE and ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"
        result = scan_text(text)
        assert result.tier == "strict"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_scan.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.credential_scan'`

**Step 3: Write the implementation**

Create `scripts/credential_scan.py`:

```python
"""Shared credential scanning for cross-model plugin.

Extracts tiered credential detection from codex_guard.py into a public module.
Both the hook (codex_guard.py) and the delegation adapter (codex_delegate.py)
import from this module.

Tiers:
  strict:      Hard-block. High-confidence patterns (AWS keys, PEM, JWT).
  contextual:  Block unless placeholder/example words appear nearby.
  broad:       Shadow telemetry only. No blocking.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Pattern definitions (extracted from codex_guard.py)
# ---------------------------------------------------------------------------

_STRICT: list[re.Pattern[str]] = [
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(
        r"-----BEGIN\s+(?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
    ),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
]

_CONTEXTUAL: list[re.Pattern[str]] = [
    re.compile(r"\b(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9\-_]{20,}\b"),
    re.compile(r"\b(?:pk_live|pk_test)_[A-Za-z0-9]{24,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{40,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{20,}"),
    re.compile(r"://[^@\s]+:[^@\s]{6,}@"),
]

_PLACEHOLDER_WORDS: frozenset[str] = frozenset([
    "format", "example", "looks", "placeholder", "dummy",
    "sample", "suppose", "hypothetical", "redact", "redacted",
    "your-", "my-", "[redacted",
])

_BROAD: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)\b(?:password|passwd|secret|api_key|apikey|access_token|"
        r"auth_token|private_key|client_secret)\s*[=:]\s*.{6,}"
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning text for credentials."""

    action: Literal["allow", "block", "shadow"]
    tier: str | None
    reason: str | None


def _has_placeholder_context(
    text: str, match_start: int, match_end: int, window: int = 100
) -> bool:
    """Return True if a placeholder/example word appears near the match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    context = text[start:end].lower()
    return any(word in context for word in _PLACEHOLDER_WORDS)


def scan_text(text: str) -> ScanResult:
    """Scan text for credentials. Returns on first match.

    Priority: strict > contextual > broad > allow.
    """
    # Strict tier
    for pat in _STRICT:
        if pat.search(text):
            return ScanResult(
                action="block",
                tier="strict",
                reason=f"strict:{pat.pattern[:60]}",
            )

    # Contextual tier
    for pat in _CONTEXTUAL:
        for m in pat.finditer(text):
            if not _has_placeholder_context(text, m.start(), m.end()):
                return ScanResult(
                    action="block",
                    tier="contextual",
                    reason=f"contextual:{pat.pattern[:60]}",
                )

    # Broad tier
    for pat in _BROAD:
        if pat.search(text):
            return ScanResult(
                action="shadow",
                tier="broad",
                reason=f"broad:{pat.pattern[:60]}",
            )

    return ScanResult(action="allow", tier=None, reason=None)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_credential_scan.py -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add scripts/credential_scan.py tests/test_credential_scan.py
git commit -m "feat(delegation): extract credential_scan.py from codex_guard

Public module with ScanResult dataclass and scan_text() API.
Patterns extracted from codex_guard.py (strict, contextual, broad tiers)."
```

---

## Task 2: Update `scripts/codex_guard.py` to import from `credential_scan.py`

Replace inline pattern definitions and detection functions with imports from the shared module. Hook entry point, stdin parsing, exit code semantics, and PostToolUse logic are unchanged.

**Files:**
- Modify: `scripts/codex_guard.py`
- Test: existing hook behavior preserved (manual verification)

**Step 1: Write a regression test**

Add `tests/test_codex_guard.py`:

```python
"""Regression tests for codex_guard hook after credential_scan extraction."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.codex_guard import handle_pre, handle_post


def _make_pre_data(prompt: str, tool: str = "mcp__codex") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "session_id": "test-session",
        "tool_input": {"prompt": prompt},
    }


class TestHandlePre:
    """PreToolUse handler blocks on credentials."""

    @patch("scripts.codex_guard._append_log")
    def test_clean_prompt_allows(self, mock_log: object) -> None:
        assert handle_pre(_make_pre_data("fix the auth test")) == 0

    @patch("scripts.codex_guard._append_log")
    def test_aws_key_blocks(self, mock_log: object) -> None:
        assert handle_pre(_make_pre_data("key AKIAIOSFODNN7EXAMPLE")) == 2

    @patch("scripts.codex_guard._append_log")
    def test_broad_tier_allows(self, mock_log: object) -> None:
        """Broad tier is shadow-only, does not block."""
        assert handle_pre(_make_pre_data("password = mysecretvalue123")) == 0


class TestHandlePost:
    """PostToolUse handler always returns 0."""

    @patch("scripts.codex_guard._append_log")
    def test_always_allows(self, mock_log: object) -> None:
        data = {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__codex",
            "session_id": "test-session",
            "tool_input": {"prompt": "test"},
            "tool_response": {"content": "response"},
        }
        assert handle_post(data) == 0
```

**Step 2: Run regression test to verify it passes on current code**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py -v`
Expected: All pass (validates current behavior).

**Step 3: Update `codex_guard.py` to import from `credential_scan`**

Replace lines 37-159 (pattern definitions + detection helpers) with imports. Key changes:

1. Remove: `_STRICT`, `_CONTEXTUAL`, `_PLACEHOLDER_WORDS`, `_BROAD` pattern lists
2. Remove: `_has_placeholder_context()`, `_check_strict()`, `_check_contextual()`, `_broad_tag()` functions
3. Add: `from credential_scan import scan_text` import
4. Update `handle_pre()` to use `scan_text()`:
   - `scan_text(prompt)` returns `ScanResult`
   - `action == "block"` → log + return 2
   - `action == "shadow"` → log shadow telemetry
   - `action == "allow"` → return 0

The guard's `_LOG_PATH`, `_ts()`, `_append_log()` stay as-is (D26 — guard keeps its own log implementation with microsecond timestamps and `session_id="unknown"` default).

```python
# Replace the detection section in handle_pre with:
from credential_scan import scan_text

# In handle_pre():
    result = scan_text(prompt)
    if result.action == "block":
        _append_log({
            "ts": _ts(),
            "event": "block",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt),
            "reason": result.reason,
        })
        print(f"codex-guard: dispatch blocked ({result.reason})", file=sys.stderr)
        return 2

    if result.action == "shadow":
        _append_log({
            "ts": _ts(),
            "event": "shadow",
            "tool": tool,
            "session_id": session_id,
            "prompt_length": len(prompt),
            "reason": result.reason,
        })

    return 0
```

**Step 4: Run regression tests to verify behavior preserved**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py tests/test_credential_scan.py -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add scripts/codex_guard.py tests/test_codex_guard.py
git commit -m "refactor(delegation): codex_guard imports from credential_scan

Replace inline pattern definitions and detection helpers with
scan_text() import. Hook entry point and exit code semantics unchanged.
Guard retains its own _ts() and _append_log() per D26."
```

---

## Task 3: Create `scripts/event_log.py`

Extract shared log helpers from `emit_analytics.py` into a module for use by `emit_analytics.py` and `codex_delegate.py`.

**Files:**
- Create: `scripts/event_log.py`
- Test: `tests/test_event_log.py`

**Step 1: Write the failing tests**

Create `tests/test_event_log.py`:

```python
"""Tests for event_log shared module."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.event_log import LOG_PATH, ts, append_log, session_id


class TestLogPath:
    def test_points_to_codex_events(self) -> None:
        assert LOG_PATH.name == ".codex-events.jsonl"
        assert ".claude" in str(LOG_PATH)


class TestTs:
    def test_format_utc_z_suffix(self) -> None:
        result = ts()
        assert result.endswith("Z")
        assert "T" in result
        # Second precision — no microseconds
        assert "." not in result

    def test_is_parseable(self) -> None:
        from datetime import datetime
        result = ts()
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert dt is not None


class TestAppendLog:
    def test_writes_json_line(self, tmp_path: Path) -> None:
        log_file = tmp_path / ".codex-events.jsonl"
        with patch("scripts.event_log.LOG_PATH", log_file):
            result = append_log({"event": "test", "value": 42})
        assert result is True
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "test"

    def test_returns_false_on_write_error(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "nonexistent" / "deep" / "path" / "log.jsonl"
        # Patch to a directory that exists but file path is a dir
        dir_as_file = tmp_path / "adir"
        dir_as_file.mkdir()
        with patch("scripts.event_log.LOG_PATH", dir_as_file):
            result = append_log({"event": "test"})
        assert result is False

    def test_appends_not_overwrites(self, tmp_path: Path) -> None:
        log_file = tmp_path / ".codex-events.jsonl"
        with patch("scripts.event_log.LOG_PATH", log_file):
            append_log({"event": "first"})
            append_log({"event": "second"})
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2


class TestSessionId:
    def test_returns_value_from_env(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "abc-123"}):
            assert session_id() == "abc-123"

    def test_returns_none_for_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLAUDE_SESSION_ID", None)
            assert session_id() is None

    def test_returns_none_for_whitespace(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "   "}):
            assert session_id() is None

    def test_returns_none_for_empty(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": ""}):
            assert session_id() is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_event_log.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write the implementation**

Create `scripts/event_log.py`:

```python
"""Shared event log helpers for cross-model plugin analytics.

Extracted from emit_analytics.py for reuse by codex_delegate.py.
Scope: analytics-emitter consumers only. codex_guard.py is NOT migrated
(D26 — keeps its own _ts and _append_log with different semantics).

Exports:
    LOG_PATH: Path to ~/.claude/.codex-events.jsonl
    ts() -> str: ISO 8601 UTC with Z suffix (second precision)
    append_log(entry) -> bool: Atomic append, returns success
    session_id() -> str | None: From CLAUDE_SESSION_ID, nullable
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH: Path = Path.home() / ".claude" / ".codex-events.jsonl"


def ts() -> str:
    """ISO 8601 UTC timestamp with Z suffix. Second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_log(entry: dict) -> bool:
    """Append a JSON line to the event log. Returns True on success."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True
    except OSError as exc:
        print(f"log write failed: {exc}", file=sys.stderr)
        return False


def session_id() -> str | None:
    """Read session ID from environment. Never fabricated.

    Returns None if CLAUDE_SESSION_ID is absent, empty, or whitespace-only.
    """
    value = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    return value or None
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_event_log.py -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add scripts/event_log.py tests/test_event_log.py
git commit -m "feat(delegation): extract event_log.py from emit_analytics

Shared LOG_PATH, ts(), append_log(), session_id() for analytics emitters.
codex_guard.py retains its own implementation per D26."
```

---

## Task 4: Update `scripts/emit_analytics.py` to import from `event_log.py`

Replace local `_ts()`, `_append_log()`, `_session_id()`, and `_LOG_PATH` with imports from the shared module.

**Files:**
- Modify: `scripts/emit_analytics.py`
- Test: `tests/test_emit_analytics.py` (existing, must still pass)

**Step 1: Run existing tests to establish baseline**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py -v`
Expected: All pass.

**Step 2: Update `emit_analytics.py`**

1. Add import: `from event_log import LOG_PATH, ts as _ts, append_log as _append_log, session_id as _session_id`
2. Remove: local `_LOG_PATH` (line 37), `_ts()` (lines 146-148), `_append_log()` (lines 151-160), `_session_id()` (lines 163-169)
3. Keep the `_LOG_PATH` reference in the `finally` cleanup block — update to use imported `LOG_PATH` name

Import aliases (`ts as _ts`, etc.) preserve existing call sites throughout the file — no changes needed in `build_dialogue_outcome`, `build_consultation_outcome`, or `_process`.

**Step 3: Run tests to verify behavior preserved**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_emit_analytics.py tests/test_event_log.py -v`
Expected: All pass.

**Step 4: Commit**

```bash
git add scripts/emit_analytics.py
git commit -m "refactor(delegation): emit_analytics imports from event_log

Replace local _ts, _append_log, _session_id, _LOG_PATH with shared imports.
Function aliases preserve existing call sites. No behavior change."
```

---

## Task 5: Update `scripts/read_events.py` — add `delegation_outcome`

Add `delegation_outcome` to `_REQUIRED_FIELDS` so event validation accepts delegation events.

**Files:**
- Modify: `scripts/read_events.py:29-58`
- Test: `tests/test_read_events.py`

**Step 1: Write the failing test**

Create `tests/test_read_events.py`:

```python
"""Tests for read_events delegation_outcome support."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.read_events import validate_event, classify, _REQUIRED_FIELDS


class TestDelegationOutcomeSchema:
    """delegation_outcome in _REQUIRED_FIELDS."""

    def test_delegation_outcome_in_required_fields(self) -> None:
        assert "delegation_outcome" in _REQUIRED_FIELDS

    def test_required_fields_complete(self) -> None:
        expected = {
            "schema_version", "event", "ts", "consultation_id",
            "session_id", "thread_id", "dispatched", "sandbox",
            "full_auto", "credential_blocked", "dirty_tree_blocked",
            "readable_secret_file_blocked", "commands_run_count",
            "exit_code", "termination_reason",
            "model", "reasoning_effort",  # F10: nullable but present
        }
        assert _REQUIRED_FIELDS["delegation_outcome"] == expected


class TestDelegationOutcomeValidation:
    """validate_event with delegation_outcome events."""

    def _make_delegation_event(self, **overrides: object) -> dict:
        event = {
            "schema_version": "0.1.0",
            "event": "delegation_outcome",
            "ts": "2026-03-06T12:00:00Z",
            "consultation_id": "test-uuid",
            "session_id": None,
            "thread_id": None,
            "dispatched": True,
            "sandbox": "workspace-write",
            "model": None,
            "reasoning_effort": "high",
            "full_auto": False,
            "credential_blocked": False,
            "dirty_tree_blocked": False,
            "readable_secret_file_blocked": False,
            "commands_run_count": 3,
            "exit_code": 0,
            "termination_reason": "complete",
        }
        event.update(overrides)
        return event

    def test_valid_event_passes(self) -> None:
        errors = validate_event(self._make_delegation_event())
        assert errors == []

    def test_missing_field_fails(self) -> None:
        event = self._make_delegation_event()
        del event["dispatched"]
        errors = validate_event(event)
        assert any("dispatched" in e for e in errors)

    def test_classify_returns_delegation_outcome(self) -> None:
        event = self._make_delegation_event()
        assert classify(event) == "delegation_outcome"
```

**Step 2: Run test to verify it fails**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_read_events.py -v`
Expected: FAIL — `delegation_outcome` not in `_REQUIRED_FIELDS`

**Step 3: Update `read_events.py`**

Add to `_REQUIRED_FIELDS` dict (after `consultation_outcome`):

```python
    "delegation_outcome": {
        "schema_version",
        "event",
        "ts",
        "consultation_id",
        "session_id",
        "thread_id",
        "dispatched",
        "sandbox",
        "full_auto",
        "credential_blocked",
        "dirty_tree_blocked",
        "readable_secret_file_blocked",
        "commands_run_count",
        "exit_code",
        "termination_reason",
        "model",              # F10: nullable but present in event
        "reasoning_effort",   # F10: nullable but present in event
    },
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_read_events.py -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add scripts/read_events.py tests/test_read_events.py
git commit -m "feat(delegation): add delegation_outcome to read_events

17 required fields for delegation event validation (F10: includes model,
reasoning_effort). Nullable fields (session_id, thread_id, exit_code,
model, reasoning_effort) are present but may be null — validation checks
presence, not value."
```

---

## Task 6: Update `scripts/compute_stats.py` — add delegation section

Add `_DELEGATION_TEMPLATE`, `_compute_delegation()`, `--type delegation`, `delegations_completed_total` in usage, and `--json` no-op flag.

**Files:**
- Modify: `scripts/compute_stats.py`
- Test: `tests/test_compute_stats.py`

**Step 1: Write the failing tests**

Create `tests/test_compute_stats.py`:

```python
"""Tests for compute_stats delegation support."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.compute_stats import (
    compute,
    _DELEGATION_TEMPLATE,
    _SECTION_MATRIX,
    _USAGE_TEMPLATE,
)


def _make_delegation_event(**overrides: object) -> dict:
    event = {
        "schema_version": "0.1.0",
        "event": "delegation_outcome",
        "ts": "2026-03-06T12:00:00Z",
        "consultation_id": "test-uuid",
        "session_id": None,
        "thread_id": None,
        "dispatched": True,
        "sandbox": "workspace-write",
        "model": None,
        "reasoning_effort": "high",
        "full_auto": False,
        "credential_blocked": False,
        "dirty_tree_blocked": False,
        "readable_secret_file_blocked": False,
        "commands_run_count": 5,
        "exit_code": 0,
        "termination_reason": "complete",
    }
    event.update(overrides)
    return event


class TestDelegationTemplate:
    def test_template_has_required_keys(self) -> None:
        expected_keys = {
            "included", "sample_size", "complete_count", "error_count",
            "blocked_count", "credential_block_count", "dirty_tree_block_count",
            "readable_secret_file_block_count", "sandbox_counts",
            "full_auto_count", "avg_commands_run", "avg_commands_run_observed_count",
        }
        assert set(_DELEGATION_TEMPLATE.keys()) == expected_keys


class TestSectionMatrix:
    def test_delegation_type_in_matrix(self) -> None:
        assert "delegation" in _SECTION_MATRIX

    def test_delegation_includes_delegation_section(self) -> None:
        assert _SECTION_MATRIX["delegation"]["delegation"] is True
        assert _SECTION_MATRIX["delegation"]["usage"] is True


class TestUsageTemplate:
    def test_delegations_completed_total_field(self) -> None:
        assert "delegations_completed_total" in _USAGE_TEMPLATE


class TestComputeDelegation:
    def test_single_complete_event(self) -> None:
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["sample_size"] == 1
        assert result["delegation"]["complete_count"] == 1
        assert result["delegation"]["sandbox_counts"] == {"workspace-write": 1}

    def test_blocked_event(self) -> None:
        events = [_make_delegation_event(
            dispatched=False,
            termination_reason="blocked",
            credential_blocked=True,
            exit_code=None,
            commands_run_count=0,
        )]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["blocked_count"] == 1
        assert result["delegation"]["credential_block_count"] == 1

    def test_usage_counts_only_dispatched(self) -> None:
        """F3: delegations_completed_total counts only dispatched=true."""
        events = [
            _make_delegation_event(dispatched=True),
            _make_delegation_event(dispatched=True),
            _make_delegation_event(dispatched=False, termination_reason="blocked"),
        ]
        result = compute(events, 0, 0, "delegation")
        assert result["usage"]["delegations_completed_total"] == 2

    def test_all_type_includes_delegation(self) -> None:
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "all")
        assert result["delegation"]["included"] is True

    def test_delegation_excluded_from_invocations_total(self) -> None:
        """F9: invocations_completed_total excludes delegation."""
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "all")
        assert result["usage"]["invocations_completed_total"] == 0

    def test_delegation_excluded_from_aggregate_metrics(self) -> None:
        """F7: Delegation does not widen active_utc_days or schema_version_counts."""
        events = [_make_delegation_event()]
        result = compute(events, 0, 0, "delegation")
        # Delegation section has its own metrics; usage aggregates unchanged
        assert result["usage"]["active_utc_days"] == 0
        assert result["usage"]["schema_version_counts"] == {}

    def test_type_robust_sandbox_counts(self) -> None:
        """F13: Non-string sandbox value handled defensively."""
        events = [_make_delegation_event(sandbox=123)]
        result = compute(events, 0, 0, "delegation")
        # Non-string sandbox should not contribute to sandbox_counts
        assert result["delegation"]["sandbox_counts"] == {}

    def test_type_robust_full_auto(self) -> None:
        """F13: Non-bool full_auto handled defensively."""
        events = [_make_delegation_event(full_auto="yes")]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["full_auto_count"] == 0

    def test_type_robust_commands_run_count(self) -> None:
        """F13: Non-numeric commands_run_count handled defensively."""
        events = [_make_delegation_event(commands_run_count="five")]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["avg_commands_run"] == 0.0

    def test_period_filtering_reduces_events(self) -> None:
        """B5: Period filtering with shared `now` reduces delegation_outcomes."""
        old_event = _make_delegation_event(ts="2025-01-01T00:00:00Z")
        recent_event = _make_delegation_event(ts="2026-03-06T12:00:00Z")
        events = [old_event, recent_event]
        result = compute(events, 30, 0, "delegation")
        assert result["delegation"]["sample_size"] == 1

    def test_mixed_type_avg_commands_run(self) -> None:
        """F13: avg_commands_run_observed_count reflects numeric subset only."""
        events = [
            _make_delegation_event(commands_run_count=10),
            _make_delegation_event(commands_run_count="invalid"),
            _make_delegation_event(commands_run_count=None, dispatched=False),
        ]
        result = compute(events, 0, 0, "delegation")
        assert result["delegation"]["avg_commands_run_observed_count"] == 1  # only 1 dispatched+numeric


class TestJsonFlag:
    def test_json_flag_accepted(self) -> None:
        """--json flag does not cause argparse error."""
        import subprocess
        script = str(Path(__file__).resolve().parent.parent / "scripts" / "compute_stats.py")
        proc = subprocess.run(
            [sys.executable, script, "--json", "/dev/null"],
            capture_output=True, text=True, timeout=10,
        )
        # Should not fail with "unrecognized arguments: --json"
        assert "unrecognized arguments" not in proc.stderr
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_compute_stats.py -v`
Expected: FAIL — `_DELEGATION_TEMPLATE` does not exist

**Step 3: Update `compute_stats.py`**

Add after `_SECURITY_TEMPLATE` (around line 101):

```python
_DELEGATION_TEMPLATE: dict = {
    "included": False,
    "sample_size": 0,
    "complete_count": 0,
    "error_count": 0,
    "blocked_count": 0,
    "credential_block_count": 0,
    "dirty_tree_block_count": 0,
    "readable_secret_file_block_count": 0,
    "sandbox_counts": {},
    "full_auto_count": 0,
    "avg_commands_run": 0.0,
    "avg_commands_run_observed_count": 0,
}
```

Add `"delegations_completed_total": 0` to `_USAGE_TEMPLATE`.

Add `_compute_delegation()` function:

```python
def _compute_delegation(delegation_outcomes: list[dict]) -> dict:
    """Compute the delegation section from delegation_outcome events.

    F13: Type-robust — handles non-canonical types defensively.
    Raw Phase-A values may be logged before Phase B validation,
    so sandbox may be non-string, full_auto non-bool, commands_run_count
    non-numeric.
    """
    result = copy.deepcopy(_DELEGATION_TEMPLATE)
    result["included"] = True
    result["sample_size"] = len(delegation_outcomes)

    for event in delegation_outcomes:
        reason = event.get("termination_reason")
        if reason == "complete":
            result["complete_count"] += 1
        elif reason == "error":
            result["error_count"] += 1
        elif reason == "blocked":
            result["blocked_count"] += 1

        if event.get("credential_blocked"):
            result["credential_block_count"] += 1
        if event.get("dirty_tree_blocked"):
            result["dirty_tree_block_count"] += 1
        if event.get("readable_secret_file_blocked"):
            result["readable_secret_file_block_count"] += 1

        # F13: Only count sandbox if string
        sandbox = event.get("sandbox")
        if isinstance(sandbox, str) and sandbox:
            result["sandbox_counts"][sandbox] = result["sandbox_counts"].get(sandbox, 0) + 1

        # F13: Only increment full_auto when `is True`
        if event.get("full_auto") is True:
            result["full_auto_count"] += 1

    # Average commands run (dispatched events only)
    dispatched = [e for e in delegation_outcomes if e.get("dispatched") is True]
    # F13: Filter to numeric commands_run_count before averaging
    numeric_dispatched = [
        e for e in dispatched
        if isinstance(e.get("commands_run_count"), (int, float))
    ]
    avg_cmd, obs_cmd = stats_common.observed_avg(numeric_dispatched, "commands_run_count")
    result["avg_commands_run"] = avg_cmd if avg_cmd is not None else 0.0
    result["avg_commands_run_observed_count"] = obs_cmd

    return result
```

Update `_SECTION_MATRIX` to add `"delegation"` key:

```python
_SECTION_MATRIX: dict[str, dict[str, bool]] = {
    "all":          {"usage": True,  "dialogue": True,  "context": True,  "security": True,  "delegation": True},
    "dialogue":     {"usage": True,  "dialogue": True,  "context": True,  "security": False, "delegation": False},
    "consultation": {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": False},
    "security":     {"usage": False, "dialogue": False, "context": False, "security": True,  "delegation": False},
    "delegation":   {"usage": True,  "dialogue": False, "context": False, "security": False, "delegation": True},
}
```

Update `_SECTION_TYPE` literal: add `"delegation"`.

Update event classifier in `compute()` to route `delegation_outcome`:

```python
    delegation_outcomes: list[dict] = []
    # ... in the classifier loop:
    elif event_type == "delegation_outcome":
        delegation_outcomes.append(event)
```

Update `_compute_usage()` to accept delegation outcomes (F3, F7, F9):

```python
def _compute_usage(
    dialogue_outcomes, consultation_outcomes, delegation_outcomes,
    consultations, blocks, shadows,
) -> dict:
    # ...
    # F3: Count only dispatched=true events
    result["delegations_completed_total"] = sum(
        1 for e in delegation_outcomes if e.get("dispatched") is True
    )
    # F7+F9: Delegation excluded from invocations_completed_total,
    # active_utc_days, and schema_version_counts. Only dialogue +
    # consultation contribute to these aggregate metrics.
    outcome_events = dialogue_outcomes + consultation_outcomes
    # rest unchanged...
```

Update the call site in `compute()` at line ~424 to pass the new 6th argument:

```python
    usage = _compute_usage(
        dialogue_outcomes, consultation_outcomes, delegation_outcomes,
        consultations, blocks, shadows,
    )
```

Add delegation section computation in the orchestrator:

```python
    if matrix.get("delegation"):
        delegation_section = _compute_delegation(delegation_outcomes)
    else:
        delegation_section = copy.deepcopy(_DELEGATION_TEMPLATE)

    # Add to output envelope:
    "delegation": delegation_section,
```

**F2: Update `_validate_events()` to use schema registry** (around line 307):

Replace the hardcoded event type tuple with `read_events._REQUIRED_FIELDS` keys:

```python
# Before (hardcoded):
# if event.get("event") in ("dialogue_outcome", "consultation_outcome"):

# After (F2 — schema registry, A1: simplified import):
import read_events

# In _validate_events():
if event.get("event") in read_events._REQUIRED_FIELDS:
```

This ensures delegation_outcome events are validated automatically when added to `_REQUIRED_FIELDS` in read_events.py. A1: Uses direct attribute access instead of try/except import since `read_events` is already imported at module level.

**F11: Add period filtering for delegation_outcomes** in `compute()`:

After the event classifier loop and before calling `_compute_delegation()`, apply the same period filter used for other event lists. Use the shared `now` timestamp (B5: consistent cutoff across all event types):

```python
    # Apply period filter (F11: delegation was missing from this)
    # B5: Use shared `now` for consistent period boundary
    if period_days:
        delegation_outcomes = stats_common.filter_by_period(
            delegation_outcomes, period_days, now=now
        ).events
```

Add `--json` no-op flag to argparse:

```python
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output as JSON (default, kept for compatibility)",
    )
```

Add `"delegation"` to `--type` choices.

**Step 4: Run all tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add scripts/compute_stats.py tests/test_compute_stats.py
git commit -m "feat(delegation): add delegation section to compute_stats

_DELEGATION_TEMPLATE with 11 metrics, _compute_delegation() (F13: type-robust),
--type delegation, delegations_completed_total (F3: dispatched-only count),
_validate_events() uses schema registry (F2), period filtering (F11),
delegation excluded from aggregate metrics (F7/F9), --json no-op flag."
```

---

## Task 7: Create `scripts/codex_delegate.py` — the adapter

The 14-step delegation adapter. This is the largest task — build incrementally with tests for each pipeline phase.

**Files:**
- Create: `scripts/codex_delegate.py`
- Test: `tests/test_codex_delegate.py`

### Step 1: Write tests for pipeline functions and run() orchestrator (F4)

Create `tests/test_codex_delegate.py`:

```python
"""Tests for codex_delegate adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestResolveRepoRoot:
    """Pipeline step 1: resolve repo root."""

    def test_returns_toplevel_path(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _resolve_repo_root
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(
                returncode=0, stdout=str(tmp_path) + "\n"
            )
            assert _resolve_repo_root() == tmp_path

    def test_raises_on_not_git_repo(self) -> None:
        from scripts.codex_delegate import _resolve_repo_root
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=128, stdout="", stderr="not a git repo")
            with pytest.raises(RuntimeError, match="not a git repository"):
                _resolve_repo_root()


class TestParseInput:
    """F1+F8: Phase A parse (_parse_input) — structural only."""

    def test_valid_minimal_input(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "fix the test"}))
        result = _parse_input(f)
        assert result["prompt"] == "fix the test"
        assert result["sandbox"] == "workspace-write"  # default

    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input, DelegationError
        f = tmp_path / "input.json"
        f.write_text("not json at all")
        with pytest.raises(DelegationError, match="invalid JSON"):
            _parse_input(f)

    def test_returns_raw_keys(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "bogus": True}))
        result = _parse_input(f)
        assert "bogus" in result["_raw_keys"]


class TestValidateInput:
    """F1+F8: Phase B validate (_validate_input) — field validation."""

    def test_missing_prompt_errors(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": None, "sandbox": "workspace-write",
                  "reasoning_effort": "high", "full_auto": False, "_raw_keys": {"sandbox"}}
        with pytest.raises(DelegationError, match="prompt required"):
            _validate_input(parsed)

    def test_danger_full_access_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "danger-full-access",
                  "reasoning_effort": "high", "full_auto": False, "_raw_keys": {"prompt", "sandbox"}}
        with pytest.raises(DelegationError, match="not supported"):
            _validate_input(parsed)

    def test_full_auto_read_only_conflict(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "read-only",
                  "reasoning_effort": "high", "full_auto": True,
                  "_raw_keys": {"prompt", "sandbox", "full_auto"}}
        with pytest.raises(DelegationError, match="mutually exclusive"):
            _validate_input(parsed)

    def test_unknown_field_rejected(self) -> None:
        from scripts.codex_delegate import _validate_input, DelegationError
        parsed = {"prompt": "test", "sandbox": "workspace-write",
                  "reasoning_effort": "high", "full_auto": False,
                  "_raw_keys": {"prompt", "bogus_field"}}
        with pytest.raises(DelegationError, match="unknown field"):
            _validate_input(parsed)


class TestCredentialScan:
    """Step 4: credential scan (between Phase A and Phase B in run())."""

    def test_credential_in_prompt_blocked(self, tmp_path: Path) -> None:
        """F1+F8: Credential scan runs after Phase A, raises CredentialBlockError."""
        from scripts.codex_delegate import _parse_input, CredentialBlockError
        from scripts.credential_scan import scan_text
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "use key AKIAIOSFODNN7EXAMPLE"}))
        phase_a = _parse_input(f)
        result = scan_text(phase_a["prompt"])
        assert result.action == "block"


class TestVersionCheck:
    """Pipeline step 6: CLI version check."""

    def test_valid_version_passes(self) -> None:
        from scripts.codex_delegate import _check_codex_version
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.111.0\n")
            _check_codex_version()  # should not raise

    def test_old_version_fails(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.110.0\n")
            with pytest.raises(DelegationError, match="< 0.111.0"):
                _check_codex_version()

    def test_codex_not_found(self) -> None:
        from scripts.codex_delegate import _check_codex_version, DelegationError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.side_effect = FileNotFoundError
            with pytest.raises(DelegationError, match="not found"):
                _check_codex_version()


class TestCleanTreeGate:
    """Pipeline step 7: clean-tree gate."""

    def test_clean_tree_passes(self) -> None:
        from scripts.codex_delegate import _check_clean_tree
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="")
            _check_clean_tree()  # should not raise

    def test_dirty_tree_blocked(self) -> None:
        from scripts.codex_delegate import _check_clean_tree, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=" M src/main.py\0")
            with pytest.raises(GateBlockError, match="dirty"):
                _check_clean_tree()


class TestSecretFileGate:
    """Pipeline step 8: readable-secret-file gate (F5: clean pathspec split)."""

    def test_no_secrets_passes(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="")
            _check_secret_files()  # should not raise

    def test_env_file_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_env_example_exempt(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.example\n")
            _check_secret_files()  # should not raise

    def test_env_sample_exempt(self) -> None:
        """F5: All three template exemptions covered."""
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.sample\n")
            _check_secret_files()  # should not raise

    def test_env_template_exempt(self) -> None:
        from scripts.codex_delegate import _check_secret_files
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.template\n")
            _check_secret_files()  # should not raise

    def test_pem_file_blocked(self) -> None:
        """F5: Glob patterns (*.pem) correctly match."""
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="certs/server.pem\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_key_file_blocked(self) -> None:
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="id_rsa.key\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()

    def test_env_production_blocked(self) -> None:
        """F5: .env.* variants not in exemptions are blocked."""
        from scripts.codex_delegate import _check_secret_files, GateBlockError
        with patch("scripts.codex_delegate.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout=".env.production\n")
            with pytest.raises(GateBlockError, match="secret"):
                _check_secret_files()


class TestBuildCommand:
    """Pipeline step 9: build codex exec command."""

    def test_minimal_command(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        output_file = tmp_path / "output.txt"
        cmd = _build_command(
            prompt="fix tests",
            sandbox="workspace-write",
            model=None,
            reasoning_effort="high",
            full_auto=False,
            output_file=output_file,
        )
        assert cmd[0] == "codex"
        assert "exec" in cmd
        assert "--json" in cmd
        assert "-o" in cmd
        assert "-s" in cmd
        assert "workspace-write" in cmd

    def test_full_auto_flag(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        cmd = _build_command("fix", "workspace-write", None, "high", True, tmp_path / "o.txt")
        assert "--full-auto" in cmd

    def test_model_flag(self, tmp_path: Path) -> None:
        from scripts.codex_delegate import _build_command
        cmd = _build_command("fix", "workspace-write", "o3", "high", False, tmp_path / "o.txt")
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"


class TestParseJsonlEvents:
    """Pipeline steps 11-12: JSONL parsing."""

    def test_extracts_thread_id(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = '{"type":"thread.started","thread_id":"abc-123"}\n'
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "abc-123"

    def test_extracts_commands(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = '{"type":"item.completed","item":{"type":"command_execution","command":"ls","exit_code":0}}\n'
        result = _parse_jsonl(lines)
        assert len(result["commands_run"]) == 1
        assert result["commands_run"][0]["command"] == "ls"

    def test_skips_malformed_lines(self) -> None:
        from scripts.codex_delegate import _parse_jsonl
        lines = 'not json\n{"type":"thread.started","thread_id":"abc"}\n'
        result = _parse_jsonl(lines)
        assert result["thread_id"] == "abc"

    def test_zero_usable_events_errors(self) -> None:
        from scripts.codex_delegate import _parse_jsonl, DelegationError
        with pytest.raises(DelegationError, match="no usable JSONL"):
            _parse_jsonl("not json\nalso not json\n")

    def test_unknown_event_types_not_counted(self) -> None:
        """B9: Unknown event types are ignored — only known types count as usable."""
        from scripts.codex_delegate import _parse_jsonl, DelegationError
        lines = '{"type":"unknown.event","data":"foo"}\n{"type":"custom.thing"}\n'
        with pytest.raises(DelegationError, match="no usable JSONL"):
            _parse_jsonl(lines)


class TestRunOrchestrator:
    """F4: run() orchestrator tests — wires pipeline steps together."""

    def _write_input(self, tmp_path: Path, data: dict) -> Path:
        f = tmp_path / "input.json"
        f.write_text(json.dumps(data))
        return f

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_credential_block_emits_analytics(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        """F1+F8: CredentialBlockError emits analytics using Phase A data."""
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")
        f = self._write_input(tmp_path, {"prompt": "use key AKIAIOSFODNN7EXAMPLE"})
        exit_code = run(f)
        assert exit_code == 0  # blocked = exit 0
        # Verify analytics was emitted (append_log called)
        assert mock_log.called

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_gate_block_emits_analytics(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        """GateBlockError emits analytics."""
        from scripts.codex_delegate import run
        # Step 1 returns repo root, steps 3-5 pass, step 6 passes, step 7 blocks
        mock_sub.run.side_effect = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),  # git rev-parse
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),     # codex --version
            MagicMock(returncode=0, stdout=" M dirty.py\0"),       # git status (dirty)
        ]
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        exit_code = run(f)
        assert exit_code == 0  # blocked = exit 0
        assert mock_log.called

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_subprocess_timeout(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        """Step 10 timeout produces DelegationError → exit 1."""
        from scripts.codex_delegate import run
        responses = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),  # git rev-parse
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),     # codex --version
            MagicMock(returncode=0, stdout=""),                    # git status (clean)
            MagicMock(returncode=0, stdout=""),                    # git ls-files (no secrets)
        ]
        call_idx = 0
        def side_effect(*args, **kwargs):
            nonlocal call_idx
            if call_idx < len(responses):
                result = responses[call_idx]
                call_idx += 1
                return result
            raise subprocess.TimeoutExpired(cmd=["codex"], timeout=600)
        mock_sub.run.side_effect = side_effect
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        f = self._write_input(tmp_path, {"prompt": "fix tests"})
        exit_code = run(f)
        assert exit_code == 1  # error

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_finally_cleans_output_file(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        """F6: Adapter cleans output file in finally block."""
        from scripts.codex_delegate import run
        mock_sub.run.return_value = MagicMock(returncode=128, stdout="", stderr="not a git repo")
        f = self._write_input(tmp_path, {"prompt": "test"})
        run(f)
        # Input file should NOT be cleaned by adapter (F6: skill owns it)
        assert f.exists()

    @patch("scripts.codex_delegate.append_log", return_value=True)
    @patch("scripts.codex_delegate.subprocess")
    def test_success_path(
        self, mock_sub: MagicMock, mock_log: MagicMock, tmp_path: Path,
    ) -> None:
        """B4: Full success path — all steps pass, JSONL parsed, analytics emitted."""
        from scripts.codex_delegate import run
        output_file = tmp_path / "codex_output.txt"
        output_file.write_text("Summary of changes made.")
        jsonl_output = (
            '{"type":"thread.started","thread_id":"t-123"}\n'
            '{"type":"item.completed","item":{"type":"command_execution","command":"ls","exit_code":0}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":100,"output_tokens":50}}\n'
        )
        responses = [
            MagicMock(returncode=0, stdout=str(tmp_path) + "\n"),    # git rev-parse
            MagicMock(returncode=0, stdout="codex 0.111.0\n"),       # codex --version
            MagicMock(returncode=0, stdout=""),                      # git status (clean)
            MagicMock(returncode=0, stdout=""),                      # git ls-files (no secrets)
            MagicMock(returncode=0, stdout=jsonl_output, stderr=""), # codex exec
        ]
        mock_sub.run.side_effect = responses
        mock_sub.TimeoutExpired = subprocess.TimeoutExpired
        f = self._write_input(tmp_path, {"prompt": "fix the tests"})
        exit_code = run(f)
        assert exit_code == 0
        # Analytics emitted with dispatched=True
        assert mock_log.called
        log_event = mock_log.call_args[0][0]
        assert log_event["dispatched"] is True
        assert log_event["thread_id"] == "t-123"
        assert log_event["commands_run_count"] == 1
```

### Step 2: Run tests to verify they fail

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py -v`
Expected: FAIL — `ModuleNotFoundError`

### Step 3: Write the adapter implementation

Create `scripts/codex_delegate.py`. This is the largest file — ~350 lines implementing the 14-step pipeline. Key structure (F1+F8: Phase A/B split, F5: clean pathspec sets, F6: creation-ownership cleanup):

```python
#!/usr/bin/env python3
"""Delegation adapter for codex exec.

14-step pipeline: resolve repo → Phase A parse → credential scan →
Phase B validate → version check → clean-tree gate → secret-file gate →
build command → run subprocess → parse JSONL → read output → emit analytics →
cleanup (output file only — F6 creation-ownership).

Usage:
    python3 codex_delegate.py <input_file.json>

Exit codes:
    0 — success, blocked, or degraded (check status field)
    1 — adapter error
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

# Sibling imports (same scripts/ directory)
try:
    from credential_scan import scan_text
    from event_log import LOG_PATH, ts, append_log, session_id
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from credential_scan import scan_text
    from event_log import LOG_PATH, ts, append_log, session_id


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class DelegationError(Exception):
    """Adapter-level error (exit 1)."""

class CredentialBlockError(Exception):
    """Credential detected in prompt (exit 0, status=blocked)."""

class GateBlockError(Exception):
    """Pre-dispatch gate failed (exit 0, status=blocked)."""
    def __init__(self, reason: str, gate: str, paths: list[str] | None = None):
        super().__init__(reason)
        self.gate = gate
        self.paths = paths or []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_SANDBOXES = {"read-only", "workspace-write"}
_VALID_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
_KNOWN_FIELDS = {"prompt", "model", "sandbox", "reasoning_effort", "full_auto"}
_MIN_VERSION = (0, 111, 0)

# F5: Split into exact names and glob patterns for clarity
_SECRET_EXACT_NAMES = {".env", ".npmrc", ".netrc", "auth.json"}
_SECRET_GLOBS = {"*.pem", "*.key", "*.p12", ".env.*"}
_TEMPLATE_EXEMPTIONS = {".env.example", ".env.sample", ".env.template"}


# ---------------------------------------------------------------------------
# Pipeline functions (one per step)
# ---------------------------------------------------------------------------


def _resolve_repo_root() -> Path:
    """Step 1: Resolve git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("repo resolution failed: not a git repository")
    return Path(result.stdout.strip())


def _parse_input(input_path: Path) -> dict:
    """Step 3 — Phase A: structural parse. No user content echoed.

    F1+F8: Split from _parse_and_validate_input so that run() can
    capture Phase A data before credential scan. This ensures analytics
    emits for credential blocks (spec: emit if step 3 succeeds).

    Returns raw parsed dict with defaults applied (for analytics).
    Does NOT validate field values — that's Phase B (_validate_input).
    """
    try:
        raw = input_path.read_text()
    except OSError as exc:
        raise DelegationError(f"input read failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise DelegationError("input parse failed: invalid JSON")

    if not isinstance(data, dict):
        raise DelegationError("input parse failed: expected JSON object")

    # Apply defaults but preserve raw values for analytics (F13)
    return {
        "prompt": data.get("prompt"),
        "model": data.get("model"),
        "sandbox": data.get("sandbox", "workspace-write"),
        "reasoning_effort": data.get("reasoning_effort", "high"),
        "full_auto": data.get("full_auto", False),
        "_raw_keys": set(data.keys()),  # for unknown-field check in Phase B
    }


def _validate_input(parsed: dict) -> dict:
    """Step 5 — Phase B: field validation. May reference field names,
    never echoes user content.

    Called AFTER credential scan (step 4). Validates enums, conflicts,
    unknown fields.
    """
    # Prompt presence (Phase B — semantic validation)
    prompt = parsed.get("prompt")
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise DelegationError("validation failed: prompt required")

    # Unknown fields
    unknown = parsed.get("_raw_keys", set()) - _KNOWN_FIELDS
    if unknown:
        raise DelegationError(f"validation failed: unknown field '{next(iter(unknown))}'")

    sandbox = parsed["sandbox"]
    if sandbox == "danger-full-access":
        raise DelegationError("policy: danger-full-access not supported in Step 1")
    if sandbox not in _VALID_SANDBOXES:
        raise DelegationError("validation failed: invalid sandbox value")

    effort = parsed["reasoning_effort"]
    if effort not in _VALID_EFFORTS:
        raise DelegationError("validation failed: invalid reasoning_effort value")

    full_auto = parsed["full_auto"]
    if not isinstance(full_auto, bool):
        raise DelegationError("validation failed: full_auto must be boolean")
    if full_auto and sandbox == "read-only":
        raise DelegationError("conflict: --full-auto and -s read-only are mutually exclusive")

    return {
        "prompt": prompt.strip(),
        "model": parsed.get("model"),
        "sandbox": sandbox,
        "reasoning_effort": effort,
        "full_auto": full_auto,
    }


def _check_codex_version() -> None:
    """Step 6: Verify codex CLI version >= 0.111.0."""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise DelegationError("version check failed: codex not found in PATH")

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)
    if not match:
        raise DelegationError("version check failed: cannot parse codex --version output")

    version = tuple(int(x) for x in match.groups())
    if version < _MIN_VERSION:
        raise DelegationError(
            f"version check failed: codex {'.'.join(match.groups())} < 0.111.0"
        )


def _check_clean_tree() -> None:
    """Step 7: Clean-tree gate."""
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--ignore-submodules=none"],
        capture_output=True, text=True, timeout=10,
    )
    if result.stdout.strip():
        # Parse NUL-separated entries for path listing
        entries = [e.strip() for e in result.stdout.split("\0") if e.strip()]
        paths = [e[3:] if len(e) > 3 else e for e in entries]
        raise GateBlockError(
            "dirty working tree", gate="clean_tree", paths=paths
        )


def _check_secret_files() -> None:
    """Step 8: Readable-secret-file gate.

    F5: Clean separation of exact names and glob patterns. No mixed
    iteration or startswith fallback. Each matching path is added once.
    """
    import fnmatch

    result = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        capture_output=True, text=True, timeout=10,
    )
    if not result.stdout.strip():
        return

    matched: list[str] = []
    for filepath in result.stdout.strip().split("\n"):
        filepath = filepath.strip()
        if not filepath:
            continue
        name = Path(filepath).name

        # Template exemptions (checked first)
        if name in _TEMPLATE_EXEMPTIONS:
            continue

        # Exact name match
        if name in _SECRET_EXACT_NAMES:
            matched.append(filepath)
            continue

        # Glob pattern match (*.pem, *.key, *.p12, .env.*)
        if any(fnmatch.fnmatch(name, pat) for pat in _SECRET_GLOBS):
            matched.append(filepath)
            continue

    if matched:
        raise GateBlockError(
            "readable secret files found", gate="secret_files", paths=matched
        )


def _build_command(
    prompt: str,
    sandbox: str,
    model: str | None,
    reasoning_effort: str,
    full_auto: bool,
    output_file: Path,
) -> list[str]:
    """Step 9: Build codex exec command."""
    cmd = ["codex", "exec", "--json", "-o", str(output_file), "-s", sandbox]

    if model:
        cmd.extend(["-m", model])

    cmd.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])

    if full_auto:
        cmd.append("--full-auto")

    cmd.append(prompt)
    return cmd


def _parse_jsonl(stdout: str) -> dict:
    """Steps 11-12: Parse JSONL events from codex exec stdout."""
    thread_id: str | None = None
    commands_run: list[dict] = []
    token_usage: dict | None = None
    runtime_failures: list[str] = []
    last_message: str | None = None
    usable_count = 0
    # B9: Only known event types count as usable — unknown types are
    # silently skipped. Prevents false status=ok when all events are
    # unrecognized (e.g., fabricated thread ID from unknown events).
    _KNOWN_EVENT_TYPES = {"thread.started", "item.completed", "turn.completed", "turn.failed"}

    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print(f"codex-delegate: skipped malformed JSONL line", file=sys.stderr)
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        if event_type not in _KNOWN_EVENT_TYPES:
            continue
        usable_count += 1

        if event_type == "thread.started":
            thread_id = event.get("thread_id")

        elif event_type == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "command_execution":
                commands_run.append({
                    "command": item.get("command", ""),
                    "exit_code": item.get("exit_code"),
                })
            elif item.get("type") == "agent_message":
                last_message = item.get("text")

        elif event_type == "turn.completed":
            usage = event.get("usage", {})
            if usage:
                token_usage = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

        elif event_type == "turn.failed":
            runtime_failures.append(str(event.get("error", "unknown error")))

    if usable_count == 0:
        raise DelegationError("parse failed: no usable JSONL events from codex exec")

    if thread_id is None:
        thread_id = str(uuid.uuid4())
        print("codex-delegate: no thread.started event, generated UUID", file=sys.stderr)

    return {
        "thread_id": thread_id,
        "commands_run": commands_run,
        "token_usage": token_usage,
        "runtime_failures": runtime_failures,
        "summary": last_message,
    }


def _emit_analytics(
    phase_a: dict,
    parsed: dict | None,
    exit_code: int | None,
    blocked_by: str | None,
    dispatched: bool,
) -> None:
    """Step 13: Emit delegation_outcome event.

    F1+F8: Takes Phase A data (not validated dict) so analytics
    emits even for credential blocks and pre-Phase-B errors.
    Logs raw values including invalid ones (F13 handles downstream).
    """
    event = {
        "schema_version": "0.1.0",
        "event": "delegation_outcome",
        "ts": ts(),
        "consultation_id": str(uuid.uuid4()),
        "session_id": session_id(),
        "thread_id": parsed["thread_id"] if parsed else None,
        "dispatched": dispatched,
        "sandbox": phase_a.get("sandbox", "workspace-write"),
        "model": phase_a.get("model"),
        "reasoning_effort": phase_a.get("reasoning_effort", "high"),
        "full_auto": phase_a.get("full_auto", False),
        "credential_blocked": blocked_by == "credential",
        "dirty_tree_blocked": blocked_by == "clean_tree",
        "readable_secret_file_blocked": blocked_by == "secret_files",
        "commands_run_count": len(parsed["commands_run"]) if parsed else 0,
        "exit_code": exit_code,
        "termination_reason": (
            "blocked" if blocked_by
            else "complete" if exit_code == 0
            else "error"
        ),
    }
    if not append_log(event):
        print("codex-delegate: analytics emission failed", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON."""
    result: dict = {"status": status}
    result.update(kwargs)
    return json.dumps(result)


def run(input_path: Path) -> int:
    """Execute the 14-step delegation pipeline. Returns exit code.

    F1+F8: Phase A data captured before credential scan so analytics
    can emit for all post-step-3 failures (including credential blocks).
    F6: Adapter cleans output file only (creation-ownership). Skill
    cleans its own input file.
    """
    output_file: Path | None = None
    phase_a: dict | None = None  # F1: Phase A data for analytics
    validated: dict | None = None
    parsed: dict | None = None
    did_dispatch: bool = False  # B8: Track whether subprocess actually ran

    try:
        # Step 1: resolve repo root
        repo_root = _resolve_repo_root()
        os.chdir(repo_root)

        # Step 2: allocate output temp file only (F6: adapter owns output)
        fd, output_path = tempfile.mkstemp(prefix="codex_delegate_output_", suffix=".txt")
        os.close(fd)
        os.chmod(output_path, 0o600)
        output_file = Path(output_path)

        # Step 3 — Phase A: structural parse (captures data for analytics)
        phase_a = _parse_input(input_path)

        # Step 4: credential scan on prompt
        prompt = phase_a.get("prompt")
        if prompt and isinstance(prompt, str):
            scan_result = scan_text(prompt)
            if scan_result.action == "block":
                raise CredentialBlockError(scan_result.reason or "credential detected")

        # Step 5 — Phase B: field validation
        validated = _validate_input(phase_a)

        # Step 6: version check
        _check_codex_version()

        # Step 7: clean-tree gate
        _check_clean_tree()

        # Step 8: secret-file gate
        _check_secret_files()

        # Step 9: build command
        cmd = _build_command(
            prompt=validated["prompt"],
            sandbox=validated["sandbox"],
            model=validated["model"],
            reasoning_effort=validated["reasoning_effort"],
            full_auto=validated["full_auto"],
            output_file=output_file,
        )

        # Step 10: run subprocess
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        did_dispatch = True  # B8: subprocess ran — even if it failed

        # Steps 11-12: parse JSONL + read output file
        parsed = _parse_jsonl(proc.stdout)

        # Read -o output for summary (nullable)
        if output_file.exists():
            content = output_file.read_text().strip()
            if content:
                parsed["summary"] = content

        # Step 13: emit analytics
        _emit_analytics(phase_a, parsed, proc.returncode, None, dispatched=True)

        # Return structured output
        print(_output(
            "ok",
            thread_id=parsed["thread_id"],
            summary=parsed["summary"],
            commands_run=parsed["commands_run"],
            exit_code=proc.returncode,
            token_usage=parsed["token_usage"],
            runtime_failures=parsed["runtime_failures"],
            error=None,
        ))
        return 0

    except CredentialBlockError as exc:
        # F1+F8: Always emit — phase_a is set (step 3 succeeded)
        if phase_a:
            _emit_analytics(phase_a, None, None, "credential", dispatched=False)
        print(_output("blocked", error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None, runtime_failures=[]))
        return 0

    except GateBlockError as exc:
        if phase_a:
            _emit_analytics(phase_a, None, None, exc.gate, dispatched=False)
        print(_output("blocked", error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None,
                       runtime_failures=[], blocked_paths=exc.paths))
        return 0

    except DelegationError as exc:
        # B8: Use did_dispatch to correctly report whether subprocess ran
        if phase_a:
            _emit_analytics(phase_a, parsed, None, None, dispatched=did_dispatch)
        print(_output("error", error=str(exc), thread_id=None, summary=None,
                       commands_run=[], exit_code=None, token_usage=None, runtime_failures=[]))
        return 1

    except Exception as exc:
        # B8: Use did_dispatch — generic handler may catch post-dispatch failures
        if phase_a:
            _emit_analytics(phase_a, parsed, None, None, dispatched=did_dispatch)
        print(_output("error", error=f"internal error: {exc}", thread_id=None,
                       summary=None, commands_run=[], exit_code=None,
                       token_usage=None, runtime_failures=[]))
        return 1

    finally:
        # Step 14: cleanup
        if output_file:
            try:
                output_file.unlink(missing_ok=True)
            except OSError as exc:
                print(f"codex-delegate: output cleanup failed: {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 2:
        print(_output("error", error="usage: codex_delegate.py <input_file.json>"))
        return 1
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Run tests to verify they pass

Run: `cd packages/plugins/cross-model && uv run pytest tests/test_codex_delegate.py -v`
Expected: All pass.

### Step 5: Run the full test suite

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v`
Expected: All pass.

### Step 6: Commit

```bash
git add scripts/codex_delegate.py tests/test_codex_delegate.py
git commit -m "feat(delegation): implement codex_delegate.py adapter

14-step pipeline with Phase A/B split (F1+F8): _parse_input() captures
data for analytics before credential scan. _validate_input() runs after.
Secret file gate uses clean pathspec split (F5). Adapter cleans output
file only (F6). Analytics emits for all post-step-3 paths including
credential blocks.

Exit 0 for blocked (prevents PostToolUseFailure hook). Exit 1 for errors."
```

---

## Task 8: Integration verification

Run the full test suite and verify all modules work together.

**Step 1: Run all tests**

Run: `cd packages/plugins/cross-model && uv run pytest tests/ -v --tb=short`
Expected: All pass across all 6 test files.

**Step 1b: Run root-level test suite (B7, B10)**

Run: `uv run pytest tests/test_compute_stats.py tests/test_read_events.py -v --tb=short`
Expected: All pass. These tests exercise `_compute_usage()` (now 6 args) and usage key assertions (now includes `delegations_completed_total`). B7: Update root-level tests first if they fail — see Task 6 Step 3b below.

**Step 2: Verify imports resolve correctly**

Run: `cd packages/plugins/cross-model && python3 -c "from scripts.credential_scan import scan_text; from scripts.event_log import ts, append_log; from scripts.codex_delegate import run; print('all imports OK')"`
Expected: "all imports OK"

**Step 3: Verify the adapter's CLI interface**

Run: `cd packages/plugins/cross-model && echo '{"prompt": "test"}' > /tmp/test_delegate.json && python3 scripts/codex_delegate.py /tmp/test_delegate.json 2>/dev/null; echo "exit: $?"`
Expected: JSON output with `status=error` and exit code 1 (codex not installed in PATH). A3: Without codex in PATH, `_check_codex_version()` fails deterministically — exit 1 is guaranteed, not variable.

**Step 4: Commit any fixes**

If any tests needed adjustment, commit fixes.

**Step 5: Final commit**

```bash
git add -A
git commit -m "test(delegation): integration verification — all modules pass"
```

---

## Dependency Graph

```
Task 1 (credential_scan.py) ──┬──→ Task 2 (codex_guard.py update)
                               └──→ Task 7 (codex_delegate.py)
Task 3 (event_log.py) ────────┬──→ Task 4 (emit_analytics.py update)
                               └──→ Task 7 (codex_delegate.py)
Task 5 (read_events.py) ──────→ Task 6 (compute_stats.py + root-level tests [B7])
Task 7 depends on Tasks 1 + 3
Task 8 depends on all (includes root-level test suite [B10])
```

**Parallel opportunities:**
- Tasks 1, 3, 5 have no dependencies — can run in parallel
- Tasks 2 and 4 can run in parallel (after 1 and 3 respectively)
- Task 7 waits for 1 + 3
- Task 6 Step 3b (root-level test updates) runs after Task 6 Step 3

## Risk Notes

- **Codex CLI availability:** Task 7's integration tests require `codex` in PATH. Unit tests mock subprocess calls, so they run without Codex. End-to-end testing requires a valid OpenAI API key.
- **Clean-tree gate testing:** Tests mock `git status`. Real integration testing requires a real git repo with known state.
- **`stats_common.observed_avg`:** Task 6 assumes `observed_avg` handles the `commands_run_count` field correctly for delegation events. Verify the function works with delegation event shapes. F13 adds a numeric type filter before calling `observed_avg`, so non-numeric values won't reach it.

## Task 6 Step 3b: Root-level test suite updates (B7)

The root-level test suite (`tests/test_compute_stats.py`, `tests/test_read_events.py`) will break after Task 5 and 6 changes. Update these tests as part of Task 6:

**`tests/test_compute_stats.py` — 2 breakages:**

1. **Signature change:** `_compute_usage()` now takes 6 args (added `delegation_outcomes`). All call sites with 5 args (lines ~144, ~163, ~171, ~182, ~187) must add `[]` as the 3rd positional argument:

```python
# Before:
result = MODULE._compute_usage(dialogues, consultations_out, raw_calls, blocks, shadows)
# After (B7: add empty delegation_outcomes list):
result = MODULE._compute_usage(dialogues, consultations_out, [], raw_calls, blocks, shadows)
```

2. **Usage key assertion:** The expected keys set (line ~454-469) must include `"delegations_completed_total"`.

**`tests/test_read_events.py`:** Verify `_REQUIRED_FIELDS` now includes `"delegation_outcome"` with 17 fields. Add a test if one doesn't exist.

Run: `uv run pytest tests/test_compute_stats.py tests/test_read_events.py -v --tb=short` after updates.
