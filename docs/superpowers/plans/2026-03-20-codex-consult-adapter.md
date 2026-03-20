# Codex Consultation Adapter + Safety Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `codex_consult.py` adapter for `codex exec` / `codex exec resume` consultation transport, and extract shared safety logic from `codex_guard.py` into `consultation_safety.py`.

**Architecture:** Two independent deliverables. T2 (safety extraction) creates a shared module from existing `codex_guard.py` code — `ToolScanPolicy`, `_extract_strings`, and a new `check_tool_input` function. T1 (adapter) wraps `codex exec` subprocess invocation with JSONL parsing, credential scanning (via the shared module), and opaque continuation tokens. The adapter is a transport layer — no analytics emission (skills own that). A future MCP shim (T3, separate plan) will call this adapter and translate responses into `structuredContent.threadId` format.

**Tech Stack:** Python 3.11+, pytest, no new dependencies (uses existing `credential_scan`, `event_log` siblings)

**Ticket:** `docs/tickets/2026-03-19-codex-mcp-to-exec-migration.md` (T-20260319-01)

**Codex dialogue thread:** `019d097e-7350-7171-ab28-2d0220ae6dea` (converged architecture: D-prime)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `scripts/consultation_safety.py` | Shared safety primitives: `ToolScanPolicy`, `_extract_strings`, `SafetyVerdict`, `check_tool_input`, policy constants |
| `scripts/codex_consult.py` | Consultation adapter: input parse → credential scan → version check → build command → run subprocess → parse JSONL → structured output |
| `tests/test_consultation_safety.py` | Safety module unit tests |
| `tests/test_codex_consult.py` | Adapter unit tests |

### Modified Files

| File | Change |
|------|--------|
| `scripts/codex_guard.py:63-103` | Replace inline `ToolScanPolicy`, `_extract_strings`, policies with imports from `consultation_safety` |

### Unchanged (reference only)

| File | Why referenced |
|------|---------------|
| `scripts/codex_delegate.py` | Pattern for JSONL parsing (L386-481), subprocess invocation (L638-670), version check (L210-235) |
| `scripts/credential_scan.py` | `scan_text()` API — called by both `consultation_safety.check_tool_input` and `codex_consult._credential_scan` |
| `scripts/event_log.py` | `ts()`, `append_log()`, `session_id()` — used by adapter for audit logging |

---

## Key Design Decisions

**Opaque continuation tokens:** The delegate adapter uses first-wins for `thread_id` (L427: `if thread_id is None`). The consult adapter uses **last-wins** — `codex exec resume` may emit a new `thread.started` event with a different ID. Callers must persist the newest returned `continuation_id` and never assume ID equality across resumes.

**4-state dispatch model:** The adapter tracks subprocess lifecycle as an enum: `no_dispatch` → `dispatched_no_token` → `dispatched_with_token_uncertain` → `complete`. On timeout with a partial token, the adapter returns `status: "timeout_uncertain"` with the `continuation_id`, enabling the caller to decide whether to resume.

**No analytics emission:** Unlike `codex_delegate.py` (which emits `delegation_outcome`), the consult adapter is a pure transport layer. Analytics emission stays at the skill level (`/codex` emits `consultation_outcome`, `/dialogue` emits `dialogue_outcome`). This prevents coupling the adapter to specific event schemas.

**`CODEX_SANDBOX=seatbelt`:** The current `.mcp.json` injects this env var to prevent macOS startup panics. The adapter must propagate it to the subprocess environment.

**Read-only only:** Sandbox is always `read-only`. No clean-tree or secret-file gates (those exist in `codex_delegate.py` because delegation writes files).

---

## Task 1: Extract `ToolScanPolicy` and `_extract_strings` into `consultation_safety.py`

**Files:**
- Create: `scripts/consultation_safety.py`
- Create: `tests/test_consultation_safety.py`

- [ ] **Step 1: Write failing test for extract_strings**

```python
# tests/test_consultation_safety.py
"""Tests for consultation_safety shared module."""

from __future__ import annotations

import pytest

from scripts.consultation_safety import (
    ToolScanPolicy,
    extract_strings,
    ToolInputLimitExceeded,
)


class TestExtractStrings:
    """extract_strings traverses tool_input per policy."""

    def test_scans_content_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox"},
            content_fields={"prompt"},
        )
        texts, unexpected = extract_strings(
            {"prompt": "hello world", "sandbox": "read-only"}, policy
        )
        assert texts == ["hello world"]
        assert unexpected == []

    def test_skips_expected_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox", "model"},
            content_fields={"prompt"},
        )
        texts, _ = extract_strings(
            {"prompt": "test", "sandbox": "read-only", "model": "gpt-5"}, policy
        )
        assert texts == ["test"]

    def test_reports_unexpected_fields(self) -> None:
        policy = ToolScanPolicy(
            expected_fields={"sandbox"},
            content_fields={"prompt"},
        )
        texts, unexpected = extract_strings(
            {"prompt": "test", "diagnostics": "extra"}, policy
        )
        assert "diagnostics" in unexpected

    def test_traverses_nested_dicts(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"config"},
        )
        texts, _ = extract_strings(
            {"config": {"nested": "secret value"}}, policy
        )
        assert "secret value" in texts

    def test_rejects_non_dict_input(self) -> None:
        policy = ToolScanPolicy(expected_fields=set(), content_fields=set())
        with pytest.raises(TypeError, match="tool_input must be dict"):
            extract_strings("not a dict", policy)

    def test_node_cap_exceeded(self) -> None:
        policy = ToolScanPolicy(
            expected_fields=set(),
            content_fields={"data"},
            scan_unknown_fields=True,
        )
        # Build deeply nested structure exceeding 10k nodes
        data: dict = {"data": {}}
        current = data["data"]
        for i in range(200):
            current[f"k{i}"] = {}
            for j in range(60):
                current[f"k{i}"][f"v{j}"] = "x"
        with pytest.raises(ToolInputLimitExceeded):
            extract_strings(data, policy)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -v`

Expected: `ModuleNotFoundError: No module named 'scripts.consultation_safety'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/consultation_safety.py
"""Shared safety primitives for cross-model consultation.

Extracted from codex_guard.py to serve both the PreToolUse hook and the
codex_consult.py adapter. This module owns:
- ToolScanPolicy: controls which tool_input fields are scanned
- extract_strings: policy-driven traversal of tool_input dicts
- Policy constants: START_POLICY, REPLY_POLICY

This module does NOT own:
- Hook dispatch logic (stays in codex_guard.py)
- Credential pattern matching (stays in credential_scan.py)
- Event logging (stays in event_log.py)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

_NODE_CAP = 10_000
_CHAR_CAP = 256 * 1024


@dataclass(frozen=True)
class ToolScanPolicy:
    """Controls which tool_input fields are scanned for egress secrets."""

    expected_fields: set[str]
    content_fields: set[str]
    scan_unknown_fields: bool = True


class ToolInputLimitExceeded(RuntimeError):
    """Raised when tool_input traversal exceeds configured safety caps."""


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

START_POLICY = ToolScanPolicy(
    expected_fields={"sandbox", "approval-policy", "model", "profile"},
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)

REPLY_POLICY = ToolScanPolicy(
    expected_fields={
        "sandbox",
        "approval-policy",
        "model",
        "profile",
        "threadId",
        "conversationId",
    },
    content_fields={"prompt", "base-instructions", "developer-instructions", "config"},
)


def policy_for_tool(tool_name: str) -> ToolScanPolicy:
    """Return the scan policy for a given MCP tool name."""
    if tool_name == "mcp__plugin_cross-model_codex__codex-reply":
        return REPLY_POLICY
    return START_POLICY


# ---------------------------------------------------------------------------
# String extraction
# ---------------------------------------------------------------------------


def extract_strings(tool_input: object, policy: ToolScanPolicy) -> tuple[list[str], list[str]]:
    """Extract string-bearing values selected by the scan policy.

    Returns (texts_to_scan, unexpected_fields).

    Traverses the tool_input dict. For root-level keys:
    - content_fields: scan all nested strings
    - expected_fields: skip (known safe structural fields)
    - unknown fields: scan if policy.scan_unknown_fields is True

    Raises TypeError if tool_input is not a dict.
    Raises ToolInputLimitExceeded if traversal exceeds node or char caps.
    """
    if not isinstance(tool_input, dict):
        raise TypeError(f"tool_input must be dict. Got: {tool_input!r:.100}")

    texts_to_scan: list[str] = []
    unexpected_fields: list[str] = []
    seen_unexpected: set[str] = set()
    node_count = 0
    char_count = 0
    stack: list[tuple[object, bool, bool]] = [(tool_input, False, True)]

    while stack:
        value, scan_strings, is_root = stack.pop()
        node_count += 1
        if node_count > _NODE_CAP:
            raise ToolInputLimitExceeded("tool_input traversal failed: node cap exceeded")

        if isinstance(value, str):
            char_count += len(value)
            if char_count > _CHAR_CAP:
                raise ToolInputLimitExceeded("tool_input traversal failed: char cap exceeded")
            if scan_strings:
                texts_to_scan.append(value)
            continue

        if value is None or isinstance(value, (bool, int, float)):
            continue

        if isinstance(value, dict):
            for key, child in reversed(list(value.items())):
                child_scan = scan_strings
                if is_root:
                    if key in policy.content_fields:
                        child_scan = True
                    elif key in policy.expected_fields:
                        child_scan = False
                    else:
                        key_name = str(key)
                        if key_name not in seen_unexpected:
                            unexpected_fields.append(key_name)
                            seen_unexpected.add(key_name)
                        child_scan = policy.scan_unknown_fields
                stack.append((child, child_scan, False))
            continue

        if isinstance(value, (list, tuple)):
            for child in reversed(value):
                stack.append((child, scan_strings, False))
            continue

        if isinstance(value, (set, frozenset)):
            for child in value:
                stack.append((child, scan_strings, False))
            continue

        raise TypeError(f"tool_input traversal failed: unsupported value. Got: {value!r:.100}")

    return texts_to_scan, unexpected_fields
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -v`

Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/consultation_safety.py tests/test_consultation_safety.py
git commit -m "feat(cross-model): extract consultation_safety module from codex_guard

Moves ToolScanPolicy, extract_strings, and policy constants into a
shared module. This prepares for codex_consult.py to reuse the same
safety primitives without duplicating codex_guard logic."
```

---

## Task 2: Add `SafetyVerdict` and `check_tool_input` to `consultation_safety.py`

**Files:**
- Modify: `scripts/consultation_safety.py`
- Modify: `tests/test_consultation_safety.py`

- [ ] **Step 1: Write failing tests for SafetyVerdict and check_tool_input**

Append to `tests/test_consultation_safety.py`:

```python
from unittest.mock import patch, MagicMock

from scripts.consultation_safety import SafetyVerdict, check_tool_input, START_POLICY


class TestSafetyVerdict:
    """SafetyVerdict represents credential scan outcome."""

    def test_allow_verdict(self) -> None:
        v = SafetyVerdict(action="allow")
        assert v.action == "allow"
        assert v.reason is None

    def test_block_verdict(self) -> None:
        v = SafetyVerdict(action="block", reason="AWS key detected", tier="strict")
        assert v.action == "block"
        assert v.tier == "strict"

    def test_unexpected_fields_tracked(self) -> None:
        v = SafetyVerdict(action="allow", unexpected_fields=["bogus"])
        assert v.unexpected_fields == ["bogus"]


class TestCheckToolInput:
    """check_tool_input runs credential scan on tool_input per policy."""

    @patch("scripts.consultation_safety.scan_text")
    def test_clean_input_allows(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="allow", tier=None, reason=None)
        verdict = check_tool_input({"prompt": "fix the test"}, START_POLICY)
        assert verdict.action == "allow"

    @patch("scripts.consultation_safety.scan_text")
    def test_credential_blocks(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="block", tier="strict", reason="AWS key")
        verdict = check_tool_input({"prompt": "AKIAIOSFODNN7EXAMPLE"}, START_POLICY)
        assert verdict.action == "block"
        assert verdict.tier == "strict"

    @patch("scripts.consultation_safety.scan_text")
    def test_shadow_allows_with_reason(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="shadow", tier="broad", reason="password-like")
        verdict = check_tool_input({"prompt": "password=foo"}, START_POLICY)
        assert verdict.action == "shadow"

    @patch("scripts.consultation_safety.scan_text")
    def test_worst_verdict_wins(self, mock_scan: MagicMock) -> None:
        """When multiple texts scanned, worst action wins (block > shadow > allow)."""
        mock_scan.side_effect = [
            MagicMock(action="allow", tier=None, reason=None),
            MagicMock(action="block", tier="strict", reason="key found"),
        ]
        verdict = check_tool_input(
            {"prompt": "safe", "base-instructions": "has key"}, START_POLICY
        )
        assert verdict.action == "block"

    def test_non_dict_raises(self) -> None:
        with pytest.raises(TypeError):
            check_tool_input("not a dict", START_POLICY)

    @patch("scripts.consultation_safety.scan_text")
    def test_unexpected_fields_reported(self, mock_scan: MagicMock) -> None:
        mock_scan.return_value = MagicMock(action="allow", tier=None, reason=None)
        verdict = check_tool_input(
            {"prompt": "test", "bogus_field": "data"}, START_POLICY
        )
        assert "bogus_field" in verdict.unexpected_fields
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py::TestSafetyVerdict -v`

Expected: `ImportError: cannot import name 'SafetyVerdict'`

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/consultation_safety.py` — imports at top, code after `extract_strings`:

```python
# Add to imports at top of file:
from dataclasses import field
from typing import Literal

# Add sibling import after existing imports:
if __package__:
    from scripts.credential_scan import scan_text
else:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from credential_scan import scan_text  # type: ignore[import-not-found,no-redef]


# Add after extract_strings function:

# ---------------------------------------------------------------------------
# Safety verdict
# ---------------------------------------------------------------------------

_ACTION_RANK = {"block": 0, "shadow": 1, "allow": 2}
_TIER_RANK = {"strict": 0, "contextual": 1}


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of running credential scan on tool_input."""

    action: Literal["allow", "block", "shadow"]
    reason: str | None = None
    tier: str | None = None
    unexpected_fields: list[str] = field(default_factory=list)


def check_tool_input(tool_input: object, policy: ToolScanPolicy) -> SafetyVerdict:
    """Run credential scan on tool_input per policy. Returns worst verdict.

    Traverses tool_input using extract_strings, scans each text via
    credential_scan.scan_text, returns the worst verdict found.

    Raises TypeError if tool_input is not a dict.
    Raises ToolInputLimitExceeded if traversal exceeds caps.
    """
    texts, unexpected = extract_strings(tool_input, policy)

    worst_action = "allow"
    worst_reason: str | None = None
    worst_tier: str | None = None

    for text in texts:
        result = scan_text(text)

        result_rank = _ACTION_RANK.get(result.action, 2)
        current_rank = _ACTION_RANK.get(worst_action, 2)

        if result_rank < current_rank:
            worst_action = result.action
            worst_reason = result.reason
            worst_tier = result.tier
        elif result_rank == current_rank and result.action == "block":
            # Among blocks, prefer stricter tier
            if _TIER_RANK.get(result.tier or "", 99) < _TIER_RANK.get(worst_tier or "", 99):
                worst_reason = result.reason
                worst_tier = result.tier

    return SafetyVerdict(
        action=worst_action,
        reason=worst_reason,
        tier=worst_tier,
        unexpected_fields=unexpected,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_consultation_safety.py -v`

Expected: All 12 tests PASS (6 from Task 1 + 6 new)

- [ ] **Step 5: Commit**

```bash
git add scripts/consultation_safety.py tests/test_consultation_safety.py
git commit -m "feat(cross-model): add SafetyVerdict and check_tool_input

Provides a single-call safety check for adapter and hook consumers.
Worst-verdict-wins logic ensures block > shadow > allow when multiple
texts are scanned. Tier ranking prefers strict over contextual."
```

---

## Task 3: Update `codex_guard.py` to import from `consultation_safety`

**Files:**
- Modify: `scripts/codex_guard.py:29-103`

- [ ] **Step 1: Run existing guard tests to establish baseline**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py tests/test_codex_guard_legacy.py tests/test_codex_guard_log_delegation.py -v`

Expected: All tests PASS (record count)

- [ ] **Step 2: Replace inline code with imports**

In `scripts/codex_guard.py`, replace lines 59-103 (the `_NODE_CAP`, `_CHAR_CAP`, `ToolScanPolicy`, `ToolInputLimitExceeded`, `CODEX_POLICY`, `CODEX_REPLY_POLICY`, `_policy_for_tool`, and `_extract_strings`) with imports:

```python
# Replace the entire block from _NODE_CAP through CODEX_REPLY_POLICY and
# _policy_for_tool with:

if __package__:
    from scripts.consultation_safety import (
        ToolScanPolicy,
        ToolInputLimitExceeded,
        extract_strings as _extract_strings,
        START_POLICY as CODEX_POLICY,
        REPLY_POLICY as CODEX_REPLY_POLICY,
        policy_for_tool as _policy_for_tool,
    )
else:
    from consultation_safety import (  # type: ignore[import-not-found,no-redef]
        ToolScanPolicy,
        ToolInputLimitExceeded,
        extract_strings as _extract_strings,
        START_POLICY as CODEX_POLICY,
        REPLY_POLICY as CODEX_REPLY_POLICY,
        policy_for_tool as _policy_for_tool,
    )
```

Keep the `_extract_strings` function removed from `codex_guard.py` — it now lives in `consultation_safety.py`. The local aliases (`CODEX_POLICY`, `CODEX_REPLY_POLICY`, `_policy_for_tool`, `_extract_strings`) preserve existing call sites so `handle_pre` and `handle_post` require zero changes.

- [ ] **Step 3: Run guard tests to verify no regression**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_guard.py tests/test_codex_guard_legacy.py tests/test_codex_guard_log_delegation.py -v`

Expected: Same count, all PASS

- [ ] **Step 4: Run full test suite to check nothing else broke**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/ -v --tb=short`

Expected: All tests PASS (631+ total)

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_guard.py
git commit -m "refactor(cross-model): codex_guard imports from consultation_safety

Replaces inline ToolScanPolicy, _extract_strings, and policy constants
with imports from the shared consultation_safety module. Local aliases
preserve existing call sites — zero changes to handle_pre/handle_post."
```

---

## Task 4: Create `codex_consult.py` — error hierarchy, constants, input parsing

**Files:**
- Create: `scripts/codex_consult.py`
- Create: `tests/test_codex_consult.py`

- [ ] **Step 1: Write failing tests for input parsing**

```python
# tests/test_codex_consult.py
"""Tests for codex_consult consultation adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestParseInput:
    """Phase A: structural parse of input JSON."""

    def test_valid_new_conversation(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "explain this code"}))
        result = _parse_input(f)
        assert result["prompt"] == "explain this code"
        assert result["sandbox"] == "read-only"
        assert result["thread_id"] is None

    def test_valid_resume(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({
            "prompt": "follow up question",
            "thread_id": "thr_abc123",
        }))
        result = _parse_input(f)
        assert result["thread_id"] == "thr_abc123"

    def test_defaults(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))
        result = _parse_input(f)
        assert result["sandbox"] == "read-only"
        assert result["reasoning_effort"] == "xhigh"
        assert result["model"] is None

    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text("not json")
        with pytest.raises(ConsultationError, match="invalid JSON"):
            _parse_input(f)

    def test_missing_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"model": "gpt-5"}))
        with pytest.raises(ConsultationError, match="prompt is required"):
            _parse_input(f)

    def test_non_string_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": ["not", "a", "string"]}))
        with pytest.raises(ConsultationError, match="prompt must be string"):
            _parse_input(f)

    def test_invalid_reasoning_effort_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "reasoning_effort": "ultra"}))
        with pytest.raises(ConsultationError, match="invalid reasoning_effort"):
            _parse_input(f)

    def test_missing_file_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        with pytest.raises(ConsultationError, match="input read failed"):
            _parse_input(tmp_path / "missing.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestParseInput -v`

Expected: `ModuleNotFoundError: No module named 'scripts.codex_consult'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/codex_consult.py
"""Consultation adapter for codex exec.

Pipeline: parse input → credential scan → version check → build command →
run subprocess → parse JSONL → structured output.

Read-only consultation — no clean-tree gate, no secret-file gate, no output
file. Sandbox is always read-only. Supports resume via codex exec resume.

Design decisions:
- Opaque continuation tokens: last-wins for thread_id (exec resume may
  emit new thread.started). Callers persist newest continuation_id.
- 4-state dispatch model: no_dispatch, dispatched_no_token,
  dispatched_with_token_uncertain, complete.
- No analytics emission: skills own event production. Adapter is transport.
- CODEX_SANDBOX=seatbelt: propagated to subprocess environment.

Usage:
    python3 codex_consult.py <input_file.json>

Exit codes:
    0 — success or blocked (check status field)
    1 — adapter error
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from tempfile import TemporaryFile

if __package__:
    from scripts.consultation_safety import check_tool_input, START_POLICY
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from consultation_safety import check_tool_input, START_POLICY  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError as exc:
        print(f"codex-consult: fatal: cannot import sibling modules: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class ConsultationError(Exception):
    """Adapter-level error (exit 1)."""

class CredentialBlockError(Exception):
    """Credential detected in prompt (exit 0, status=blocked)."""

class SubprocessTimeout(ConsultationError):
    """Timeout with partial stdout available for token extraction."""
    def __init__(self, partial_stdout: str):
        super().__init__("exec failed: process timeout")
        self.partial_stdout = partial_stdout


# ---------------------------------------------------------------------------
# Dispatch state
# ---------------------------------------------------------------------------

class DispatchState(Enum):
    NO_DISPATCH = "no_dispatch"
    DISPATCHED_NO_TOKEN = "dispatched_no_token"
    DISPATCHED_WITH_TOKEN_UNCERTAIN = "dispatched_with_token_uncertain"
    COMPLETE = "complete"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_EFFORTS = {"minimal", "low", "medium", "high", "xhigh"}
_MIN_VERSION = (0, 111, 0)
_STDOUT_MAX_BYTES = 50 * 1024 * 1024
_SUBPROCESS_TIMEOUT = 300  # 5 min (shorter than delegate's 10 min — consultation is lighter)
_KNOWN_FIELDS = {"prompt", "thread_id", "model", "reasoning_effort"}


# ---------------------------------------------------------------------------
# Pipeline functions
# ---------------------------------------------------------------------------


def _parse_input(input_path: Path) -> dict:
    """Phase A: structural parse of input JSON.

    Returns dict with defaults applied. Does not echo user content in errors.
    """
    try:
        raw = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConsultationError(f"input read failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConsultationError(f"invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ConsultationError("expected JSON object at top level")

    prompt = data.get("prompt")
    if prompt is None:
        raise ConsultationError("prompt is required")
    if not isinstance(prompt, str):
        raise ConsultationError("prompt must be string")

    reasoning_effort = data.get("reasoning_effort", "xhigh")
    if reasoning_effort not in _VALID_EFFORTS:
        raise ConsultationError(
            f"invalid reasoning_effort: must be one of {sorted(_VALID_EFFORTS)}"
        )

    model = data.get("model") or None
    if model is not None and not isinstance(model, str):
        raise ConsultationError("model must be string")

    thread_id = data.get("thread_id") or None
    if thread_id is not None and not isinstance(thread_id, str):
        raise ConsultationError("thread_id must be string")

    return {
        "prompt": prompt,
        "thread_id": thread_id,
        "sandbox": "read-only",
        "model": model,
        "reasoning_effort": reasoning_effort,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestParseInput -v`

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): codex_consult input parsing and error hierarchy

Phase A structural parse with defaults: sandbox=read-only,
reasoning_effort=xhigh. Supports optional thread_id for resume.
No user content echoed in error messages."
```

---

## Task 5: Add command building (exec + resume) and version check

**Files:**
- Modify: `scripts/codex_consult.py`
- Modify: `tests/test_codex_consult.py`

- [ ] **Step 1: Write failing tests for command building**

Append to `tests/test_codex_consult.py`:

```python
class TestBuildCommand:
    """Build codex exec command for new and resume conversations."""

    def test_new_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="explain this", thread_id=None, sandbox="read-only",
            model=None, reasoning_effort="xhigh",
        )
        assert cmd[:3] == ["codex", "exec", "--json"]
        assert "-s" in cmd
        idx = cmd.index("-s")
        assert cmd[idx + 1] == "read-only"
        assert "--" in cmd
        assert cmd[-1] == "explain this"

    def test_resume_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="follow up", thread_id="thr_abc", sandbox="read-only",
            model=None, reasoning_effort="xhigh",
        )
        assert cmd[:4] == ["codex", "exec", "resume", "thr_abc"]
        assert "--json" in cmd
        assert cmd[-1] == "follow up"

    def test_includes_model_when_set(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="test", thread_id=None, sandbox="read-only",
            model="o3", reasoning_effort="xhigh",
        )
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"

    def test_omits_model_when_none(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="test", thread_id=None, sandbox="read-only",
            model=None, reasoning_effort="xhigh",
        )
        assert "-m" not in cmd

    def test_includes_reasoning_effort(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="test", thread_id=None, sandbox="read-only",
            model=None, reasoning_effort="high",
        )
        assert "-c" in cmd
        idx = cmd.index("-c")
        assert cmd[idx + 1] == "model_reasoning_effort=high"

    def test_dash_prompt_protected(self) -> None:
        """Dash-prefixed prompts must not be parsed as flags."""
        from scripts.codex_consult import _build_command
        cmd = _build_command(
            prompt="--dangerous-looking", thread_id=None, sandbox="read-only",
            model=None, reasoning_effort="xhigh",
        )
        dd_idx = cmd.index("--")
        assert cmd[dd_idx + 1] == "--dangerous-looking"


class TestCheckCodexVersion:
    """Version check requires >= 0.111.0."""

    def test_valid_version_passes(self) -> None:
        from scripts.codex_consult import _check_codex_version
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.116.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            _check_codex_version()  # should not raise

    def test_old_version_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.100.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="requires codex"):
                _check_codex_version()

    def test_missing_codex_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.side_effect = FileNotFoundError("codex not found")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="codex not found"):
                _check_codex_version()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestBuildCommand -v`

Expected: `ImportError: cannot import name '_build_command'`

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/codex_consult.py` after `_parse_input`:

```python
def _check_codex_version() -> None:
    """Verify codex CLI >= 0.111.0."""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise ConsultationError("codex not found on PATH")
    except subprocess.TimeoutExpired:
        raise ConsultationError("codex --version timed out")

    if result.returncode != 0:
        raise ConsultationError("codex --version failed")

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout)
    if not match:
        raise ConsultationError("codex --version: cannot parse version")

    version = tuple(int(g) for g in match.groups())
    if version < _MIN_VERSION:
        raise ConsultationError(
            f"requires codex >= {'.'.join(str(v) for v in _MIN_VERSION)}, "
            f"found {'.'.join(str(v) for v in version)}"
        )


def _build_command(
    prompt: str,
    thread_id: str | None,
    sandbox: str,
    model: str | None,
    reasoning_effort: str,
) -> list[str]:
    """Build codex exec command. Supports new and resume conversations."""
    if thread_id:
        cmd = ["codex", "exec", "resume", thread_id, "--json"]
    else:
        cmd = ["codex", "exec", "--json"]

    cmd.extend(["-s", sandbox])

    if model:
        cmd.extend(["-m", model])

    cmd.extend(["-c", f"model_reasoning_effort={reasoning_effort}"])

    # Prevent dash-prefixed prompts from being parsed as flags
    cmd.append("--")
    cmd.append(prompt)
    return cmd
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestBuildCommand tests/test_codex_consult.py::TestCheckCodexVersion -v`

Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): codex_consult command building + version check

Supports codex exec (new) and codex exec resume (continue).
Version gate at 0.111.0 matching codex_delegate.py."
```

---

## Task 6: Add JSONL parsing with opaque continuation tokens

**Files:**
- Modify: `scripts/codex_consult.py`
- Modify: `tests/test_codex_consult.py`

- [ ] **Step 1: Write failing tests for JSONL parsing**

Append to `tests/test_codex_consult.py`:

```python
class TestParseJsonl:
    """JSONL parsing extracts continuation_id, response, usage."""

    def _make_jsonl(self, *events: dict) -> str:
        return "\n".join(json.dumps(e) for e in events)

    def test_extracts_thread_id(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_001"},
            {"type": "turn.started"},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        )
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_last_thread_id_wins(self) -> None:
        """Opaque token: resume may emit new thread.started."""
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_old"},
            {"type": "thread.started", "thread_id": "thr_new"},
            {"type": "turn.completed", "usage": {}},
        )
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_new"

    def test_extracts_agent_message(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_001"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "The answer is 42."}},
            {"type": "turn.completed", "usage": {}},
        )
        result = _parse_jsonl(stdout)
        assert result["response_text"] == "The answer is 42."

    def test_concatenates_multiple_messages(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_001"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 1."}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 2."}},
            {"type": "turn.completed", "usage": {}},
        )
        result = _parse_jsonl(stdout)
        assert "Part 1." in result["response_text"]
        assert "Part 2." in result["response_text"]

    def test_extracts_token_usage(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_001"},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}},
        )
        result = _parse_jsonl(stdout)
        assert result["token_usage"] == {"input_tokens": 100, "output_tokens": 50}

    def test_captures_runtime_failures(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "thread.started", "thread_id": "thr_001"},
            {"type": "turn.failed", "error": "model overloaded"},
        )
        result = _parse_jsonl(stdout)
        assert "model overloaded" in result["runtime_failures"]

    def test_no_usable_events_errors(self) -> None:
        from scripts.codex_consult import _parse_jsonl, ConsultationError
        with pytest.raises(ConsultationError, match="no usable JSONL events"):
            _parse_jsonl("")

    def test_skips_malformed_lines(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = "not json\n" + json.dumps(
            {"type": "thread.started", "thread_id": "thr_001"}
        ) + "\n" + json.dumps(
            {"type": "turn.completed", "usage": {}}
        )
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_null_thread_id_on_missing_event(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl(
            {"type": "turn.started"},
            {"type": "turn.completed", "usage": {}},
        )
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestParseJsonl -v`

Expected: `ImportError: cannot import name '_parse_jsonl'`

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/codex_consult.py`:

```python
_KNOWN_EVENT_TYPES = {
    "thread.started", "turn.started", "turn.completed", "turn.failed",
    "item.started", "item.completed", "error",
}


def _parse_jsonl(stdout: str) -> dict:
    """Parse JSONL events from codex exec stdout.

    Opaque continuation tokens: uses LAST thread_id from thread.started
    (not first-wins like codex_delegate.py). exec resume may emit a new
    thread.started with a different ID.

    Returns dict with: continuation_id, response_text, token_usage,
    runtime_failures.
    """
    continuation_id: str | None = None  # last-wins
    response_parts: list[str] = []
    token_usage: dict | None = None
    runtime_failures: list[str] = []
    usable_count = 0

    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print("codex-consult: skipped malformed JSONL line", file=sys.stderr)
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type", "")
        if event_type not in _KNOWN_EVENT_TYPES:
            continue
        usable_count += 1

        if event_type == "thread.started":
            tid = event.get("thread_id")
            if isinstance(tid, str):
                continuation_id = tid  # last-wins (opaque token)

        elif event_type == "item.completed":
            item = event.get("item", {})
            if not isinstance(item, dict):
                continue
            if item.get("type") == "agent_message":
                text_val = item.get("text")
                if isinstance(text_val, str):
                    response_parts.append(text_val)

        elif event_type == "turn.completed":
            usage = event.get("usage", {})
            if isinstance(usage, dict) and usage:
                token_usage = {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                }

        elif event_type == "turn.failed":
            runtime_failures.append(str(event.get("error", "unknown error")))

        elif event_type == "error":
            runtime_failures.append(
                str(event.get("message", event.get("error", "unknown error")))
            )

    if usable_count == 0:
        raise ConsultationError("parse failed: no usable JSONL events from codex exec")

    if continuation_id is None:
        print("codex-consult: no thread.started event, continuation_id will be null", file=sys.stderr)

    return {
        "continuation_id": continuation_id,
        "response_text": "\n\n".join(response_parts) if response_parts else None,
        "token_usage": token_usage,
        "runtime_failures": runtime_failures,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestParseJsonl -v`

Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): codex_consult JSONL parsing with opaque tokens

Last-wins for thread_id (unlike delegate's first-wins) to support
codex exec resume emitting new thread IDs. Extracts agent_message
text, token usage, and runtime failures."
```

---

## Task 7: Add subprocess execution with 4-state dispatch and `CODEX_SANDBOX=seatbelt`

**Files:**
- Modify: `scripts/codex_consult.py`
- Modify: `tests/test_codex_consult.py`

- [ ] **Step 1: Write failing tests for subprocess execution**

Append to `tests/test_codex_consult.py`:

```python
from unittest.mock import patch, MagicMock
import subprocess as _subprocess


class TestRunSubprocess:
    """Subprocess execution with env propagation and dispatch tracking."""

    @patch("scripts.codex_consult.subprocess")
    def test_propagates_seatbelt_env(self, mock_sub: MagicMock) -> None:
        from scripts.codex_consult import _run_subprocess
        mock_proc = MagicMock()
        mock_proc.wait.return_value = None
        mock_proc.returncode = 0
        mock_sub.Popen.return_value = mock_proc
        mock_sub.TimeoutExpired = _subprocess.TimeoutExpired

        mock_stdout = MagicMock()
        mock_stdout.tell.return_value = 10
        mock_stdout.read.return_value = b'{"type":"turn.completed","usage":{}}'
        mock_stdout.seek = MagicMock()
        mock_stderr = MagicMock()

        with patch("scripts.codex_consult.TemporaryFile", side_effect=[mock_stdout, mock_stderr]):
            mock_stdout.__enter__ = MagicMock(return_value=mock_stdout)
            mock_stdout.__exit__ = MagicMock(return_value=False)
            mock_stderr.__enter__ = MagicMock(return_value=mock_stderr)
            mock_stderr.__exit__ = MagicMock(return_value=False)
            _run_subprocess(["codex", "exec", "--json", "--", "test"])

        # Verify CODEX_SANDBOX=seatbelt in env
        call_kwargs = mock_sub.Popen.call_args
        env = call_kwargs.kwargs.get("env") or call_kwargs[1].get("env", {})
        assert env.get("CODEX_SANDBOX") == "seatbelt"

    def test_dispatch_state_values(self) -> None:
        from scripts.codex_consult import DispatchState
        assert DispatchState.NO_DISPATCH.value == "no_dispatch"
        assert DispatchState.COMPLETE.value == "complete"
        assert DispatchState.DISPATCHED_WITH_TOKEN_UNCERTAIN.value == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult.subprocess")
    def test_timeout_returns_partial_stdout(self, mock_sub: MagicMock) -> None:
        """Timeout should raise SubprocessTimeout carrying partial stdout."""
        from scripts.codex_consult import _run_subprocess, SubprocessTimeout
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = _subprocess.TimeoutExpired(cmd=["codex"], timeout=300)
        mock_proc.kill = MagicMock()
        mock_sub.Popen.return_value = mock_proc
        mock_sub.TimeoutExpired = _subprocess.TimeoutExpired

        partial_jsonl = '{"type":"thread.started","thread_id":"thr_partial"}\n'
        mock_stdout = MagicMock()
        mock_stdout.tell.return_value = len(partial_jsonl)
        mock_stdout.read.return_value = partial_jsonl.encode()
        mock_stdout.seek = MagicMock()
        mock_stderr = MagicMock()

        with patch("scripts.codex_consult.TemporaryFile", side_effect=[mock_stdout, mock_stderr]):
            mock_stdout.__enter__ = MagicMock(return_value=mock_stdout)
            mock_stdout.__exit__ = MagicMock(return_value=False)
            mock_stderr.__enter__ = MagicMock(return_value=mock_stderr)
            mock_stderr.__exit__ = MagicMock(return_value=False)
            with pytest.raises(SubprocessTimeout) as exc_info:
                _run_subprocess(["codex", "exec", "--json", "--", "test"])
            assert "thr_partial" in exc_info.value.partial_stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestRunSubprocess -v`

Expected: `ImportError: cannot import name '_run_subprocess'`

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/codex_consult.py`:

```python
def _read_stdout(stdout_sink) -> str:
    """Read and decode stdout from the sink file, enforcing size cap."""
    stdout_sink.seek(0, os.SEEK_END)
    stdout_size = stdout_sink.tell()
    stdout_sink.seek(0)
    stdout_bytes = stdout_sink.read(_STDOUT_MAX_BYTES + 1)
    if stdout_size > _STDOUT_MAX_BYTES:
        print("codex-consult: stdout truncated (exceeded 50MB cap)", file=sys.stderr)
    return stdout_bytes[:_STDOUT_MAX_BYTES].decode("utf-8", errors="replace")


def _run_subprocess(cmd: list[str]) -> tuple[str, int]:
    """Execute codex exec and return (stdout_text, returncode).

    Propagates CODEX_SANDBOX=seatbelt to prevent macOS startup panics.
    Caps stdout at 50MB. Timeout at 300s (5 min).

    On timeout: reads partial stdout and raises SubprocessTimeout with it,
    enabling callers to extract continuation_id for recovery.
    Raises ConsultationError on spawn failure.
    """
    env = os.environ.copy()
    env["CODEX_SANDBOX"] = "seatbelt"

    try:
        with TemporaryFile() as stdout_sink, TemporaryFile() as stderr_sink:
            proc = subprocess.Popen(
                cmd,
                stdout=stdout_sink,
                stderr=stderr_sink,
                env=env,
                text=False,
            )
            try:
                proc.wait(timeout=_SUBPROCESS_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                # Read partial stdout for token extraction before raising
                partial = _read_stdout(stdout_sink)
                raise SubprocessTimeout(partial)

            return _read_stdout(stdout_sink), proc.returncode
    except FileNotFoundError:
        raise ConsultationError("exec failed: codex not found")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestRunSubprocess -v`

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): codex_consult subprocess execution

CODEX_SANDBOX=seatbelt propagated to env. 50MB stdout cap.
300s timeout. 4-state dispatch model enum defined."
```

---

## Task 8: Add main pipeline orchestrator with structured output

**Files:**
- Modify: `scripts/codex_consult.py`
- Modify: `tests/test_codex_consult.py`

- [ ] **Step 1: Write failing tests for end-to-end pipeline**

Append to `tests/test_codex_consult.py`:

```python
class TestRun:
    """End-to-end pipeline: input → output."""

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_successful_consultation(
        self, mock_safety: MagicMock, mock_version: MagicMock,
        mock_run: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_test"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Hello!"}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n',
            0,
        )
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "hi"}))

        exit_code = run(f)
        assert exit_code == 0

        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "ok"
        assert output["continuation_id"] == "thr_test"
        assert output["response_text"] == "Hello!"
        assert output["dispatched"] is True

    @patch("scripts.codex_consult.check_tool_input")
    def test_credential_blocked(
        self, mock_safety: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(
            action="block", reason="AWS key detected", tier="strict"
        )
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "AKIAIOSFODNN7EXAMPLE"}))

        exit_code = run(f)
        assert exit_code == 0  # blocked is not an error

        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "blocked"
        assert output["dispatched"] is False
        assert "AWS key" in output["error"]

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_surfaces_partial_token(
        self, mock_safety: MagicMock, mock_version: MagicMock,
        mock_run: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_consult import run, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        partial = '{"type":"thread.started","thread_id":"thr_partial"}\n'
        mock_run.side_effect = SubprocessTimeout(partial)

        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))

        exit_code = run(f)
        assert exit_code == 1

        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "timeout_uncertain"
        assert output["continuation_id"] == "thr_partial"
        assert output["dispatch_state"] == "dispatched_with_token_uncertain"

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_timeout_without_token(
        self, mock_safety: MagicMock, mock_version: MagicMock,
        mock_run: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_consult import run, SubprocessTimeout, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.side_effect = SubprocessTimeout("")  # no partial output

        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))

        exit_code = run(f)
        assert exit_code == 1

        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "timeout_uncertain"
        assert output["continuation_id"] is None
        assert output["dispatch_state"] == "dispatched_no_token"

    def test_invalid_input_returns_error(self, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run
        f = tmp_path / "input.json"
        f.write_text("not json")

        exit_code = run(f)
        assert exit_code == 1

        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "error"
        assert output["dispatched"] is False

    @patch("scripts.codex_consult._run_subprocess")
    @patch("scripts.codex_consult._check_codex_version")
    @patch("scripts.codex_consult.check_tool_input")
    def test_resume_uses_thread_id(
        self, mock_safety: MagicMock, mock_version: MagicMock,
        mock_run: MagicMock, tmp_path: Path, capsys,
    ) -> None:
        from scripts.codex_consult import run, SafetyVerdict
        mock_safety.return_value = SafetyVerdict(action="allow")
        mock_run.return_value = (
            '{"type":"thread.started","thread_id":"thr_resumed"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"Continued."}}\n'
            '{"type":"turn.completed","usage":{}}\n',
            0,
        )
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "continue", "thread_id": "thr_original"}))

        exit_code = run(f)
        assert exit_code == 0

        output = json.loads(capsys.readouterr().out)
        assert output["continuation_id"] == "thr_resumed"  # last-wins


class TestOutput:
    """Output format validation."""

    def test_all_required_fields_present(self, tmp_path: Path, capsys) -> None:
        from scripts.codex_consult import run
        f = tmp_path / "input.json"
        f.write_text("not json")

        run(f)
        output = json.loads(capsys.readouterr().out)
        required = {"status", "dispatched", "continuation_id", "response_text",
                     "token_usage", "runtime_failures", "error", "dispatch_state"}
        assert required.issubset(set(output.keys()))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py::TestRun -v`

Expected: `ImportError: cannot import name 'run'`

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/codex_consult.py`:

```python
# Add import at top (with existing consultation_safety imports):
from scripts.consultation_safety import SafetyVerdict  # (or non-package path)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_OUTPUT_REQUIRED = {
    "status", "dispatched", "continuation_id", "response_text",
    "token_usage", "runtime_failures", "error", "dispatch_state",
}


def _output(status: str, **kwargs: object) -> str:
    """Format adapter output as JSON. Validates all required fields present."""
    result: dict = {"status": status}
    result.update(kwargs)
    missing = _OUTPUT_REQUIRED - set(result.keys())
    assert not missing, f"_output missing fields: {missing}"
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def run(input_path: Path) -> int:
    """Execute the consultation pipeline. Returns exit code.

    0 — success or blocked (check status field)
    1 — adapter error
    """
    dispatch = DispatchState.NO_DISPATCH
    parsed: dict | None = None

    try:
        # Phase A: parse input
        phase_a = _parse_input(input_path)

        # Credential scan
        verdict = check_tool_input({"prompt": phase_a["prompt"]}, START_POLICY)
        if verdict.action == "block":
            raise CredentialBlockError(verdict.reason or "credential detected")

        # Version check
        _check_codex_version()

        # Build command
        cmd = _build_command(
            prompt=phase_a["prompt"],
            thread_id=phase_a["thread_id"],
            sandbox=phase_a["sandbox"],
            model=phase_a["model"],
            reasoning_effort=phase_a["reasoning_effort"],
        )

        # Run subprocess
        dispatch = DispatchState.DISPATCHED_NO_TOKEN
        stdout_text, returncode = _run_subprocess(cmd)

        # Parse JSONL
        parsed = _parse_jsonl(stdout_text)

        if parsed["continuation_id"]:
            dispatch = DispatchState.COMPLETE
        else:
            dispatch = DispatchState.DISPATCHED_NO_TOKEN

        print(_output(
            "ok",
            dispatched=True,
            continuation_id=parsed["continuation_id"],
            response_text=parsed["response_text"],
            token_usage=parsed["token_usage"],
            runtime_failures=parsed["runtime_failures"],
            error=None,
            dispatch_state=dispatch.value,
        ))
        return 0

    except CredentialBlockError as exc:
        print(_output(
            "blocked", dispatched=False, error=str(exc),
            continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=DispatchState.NO_DISPATCH.value,
        ))
        return 0

    except SubprocessTimeout as exc:
        # Try to extract continuation_id from partial stdout for recovery
        partial_token = None
        try:
            partial = _parse_jsonl(exc.partial_stdout)
            partial_token = partial.get("continuation_id")
        except ConsultationError:
            pass  # No usable events in partial output

        if partial_token:
            dispatch = DispatchState.DISPATCHED_WITH_TOKEN_UNCERTAIN

        print(_output(
            "timeout_uncertain", dispatched=True, error=str(exc),
            continuation_id=partial_token, response_text=None,
            token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        ))
        return 1

    except ConsultationError as exc:
        print(_output(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=str(exc), continuation_id=parsed["continuation_id"] if parsed else None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        ))
        return 1

    except Exception as exc:
        print(_output(
            "error", dispatched=(dispatch != DispatchState.NO_DISPATCH),
            error=f"internal error: {exc}", continuation_id=None,
            response_text=None, token_usage=None, runtime_failures=[],
            dispatch_state=dispatch.value,
        ))
        return 1


def main() -> int:
    if len(sys.argv) < 2:
        print(_output(
            "error", error="usage: codex_consult.py <input_file.json>",
            dispatched=False, continuation_id=None, response_text=None,
            token_usage=None, runtime_failures=[], dispatch_state="no_dispatch",
        ))
        return 1
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/test_codex_consult.py -v`

Expected: All tests PASS (8 + 9 + 10 + 4 + 6 + 1 = 38 total)

- [ ] **Step 5: Run full test suite for regression check**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/worktrees/cross-model-updates/packages/plugins/cross-model && uv run pytest tests/ -v --tb=short`

Expected: All tests PASS (631 existing + 38 new ≈ 669 total)

- [ ] **Step 6: Commit**

```bash
git add scripts/codex_consult.py tests/test_codex_consult.py
git commit -m "feat(cross-model): codex_consult main pipeline orchestrator

End-to-end: parse → credential scan → version check → build command →
subprocess (with CODEX_SANDBOX=seatbelt) → parse JSONL → structured output.
4-state dispatch model tracks subprocess lifecycle. Opaque continuation
tokens use last-wins for thread_id."
```

---

## Post-Implementation Verification

After all 8 tasks complete:

- [ ] Run: `uv run pytest tests/ -v --tb=short` — full suite green
- [ ] Run: `uv run ruff check scripts/consultation_safety.py scripts/codex_consult.py` — no lint issues
- [ ] Run: `uv run ruff format --check scripts/consultation_safety.py scripts/codex_consult.py` — formatted
- [ ] Verify `codex_guard.py` tests still pass with shared module
- [ ] Manual smoke test: `echo '{"prompt":"What is 2+2?"}' > /tmp/test_consult.json && python3 scripts/codex_consult.py /tmp/test_consult.json` — should return JSON with `status: "ok"`, `continuation_id`, `response_text`

## What This Does NOT Cover (Next Ticket: T3 MCP Shim)

- MCP shim that translates `codex`/`codex-reply` tool calls to adapter invocations
- `.mcp.json` entry replacement
- Skill/agent/contract updates
- Analytics `transport` field addition
- Phase 2 shim removal
