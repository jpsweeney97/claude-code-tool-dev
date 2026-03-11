# T-03 Closeout + T-04a Envelope Consumer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close out T-03 (audit repair safety fix + missing tests) and implement T-04a (DeferredWorkEnvelope schema + ticket-side consumer).

**Architecture:** T-03 flips the `_parse_args` default from repair to dry-run (safety) and adds 3 missing tests. T-04a adds `ticket_envelope.py` (schema validation + field mapper), one line in `_execute_create` (defer pass-through), and envelope lifecycle (move to `.processed/`). The envelope consumer is a boundary adapter — it maps envelope JSON to engine fields, then delegates to the existing create pipeline.

**Tech Stack:** Python 3.14, pytest, uv

**Source:** Codex dialogue (collaborative, 5 turns, full convergence) — `~/.claude/.codex-events.jsonl` entry `019cd88d-bd82-7163-8a87-a422bc9851d3`.

---

## File Structure

### T-03 Files

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/ticket_audit.py` | Modify | Fix `_parse_args` dry-run default, add `--fix` flag |
| `tests/test_audit.py` | Modify | Update 3 CLI tests to use `--fix`, add 3 new tests |

### T-04a Files

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/ticket_envelope.py` | Create | Envelope schema validation + field mapping + lifecycle |
| `scripts/ticket_engine_core.py` | Modify (1 line) | Pass `defer` through to `render_ticket` in `_execute_create` |
| `references/ticket-contract.md` | Modify | Document envelope schema in new §11 |
| `tests/test_envelope.py` | Create | Schema validation, field mapping, lifecycle, integration |

All paths relative to `packages/plugins/ticket/`.

---

## Chunk 1: T-03 Audit Repair Closeout

### Task 1: Fix dry-run default safety bug

The `_parse_args` function defaults to `dry_run = False` (line 31), meaning `ticket_audit.py repair <dir>` modifies files without explicit opt-in. The ticket spec says `--dry-run` should be default. This is a safety bug: audit repair should never modify files without explicit `--fix`.

**Files:**
- Modify: `scripts/ticket_audit.py:30-38`
- Modify: `tests/test_audit.py`

- [ ] **Step 1: Write failing test for new default behavior**

Add to `TestAuditRepairCli` in `tests/test_audit.py`:

```python
def test_audit_repair_default_is_dry_run(self, tmp_tickets: Path) -> None:
    """Calling repair without --fix defaults to dry-run (no file modification)."""
    project_root = tmp_tickets.parents[1]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_dir = tmp_tickets / ".audit" / today
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "default-mode.jsonl"
    original = (
        json.dumps({"action": "create", "result": "ok_create"}) + "\n"
        + "CORRUPT LINE\n"
    )
    audit_file.write_text(original, encoding="utf-8")

    result = _run_audit_cli("repair", "docs/tickets", cwd=project_root)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["corrupt_files"] == 1
    assert payload["data"]["repaired_files"] == [], "Default should be dry-run"
    assert audit_file.read_text(encoding="utf-8") == original, "File should be unchanged"
    assert list(audit_dir.glob("*.bak-*")) == [], "No backup created in dry-run"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli::test_audit_repair_default_is_dry_run -v`
Expected: FAIL — `repaired_files` is non-empty because the current default repairs.

- [ ] **Step 3: Write failing test for --fix flag**

Add to `TestAuditRepairCli`:

```python
def test_audit_repair_fix_flag_enables_repair(self, tmp_tickets: Path) -> None:
    """--fix flag enables actual file modification."""
    project_root = tmp_tickets.parents[1]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_dir = tmp_tickets / ".audit" / today
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "fix-mode.jsonl"
    valid_entry = {"action": "create", "result": "ok_create"}
    audit_file.write_text(
        json.dumps(valid_entry) + "\n" + "CORRUPT\n", encoding="utf-8"
    )

    result = _run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["repaired_files"] == [str(audit_file)]
    assert len(payload["data"]["backup_paths"]) == 1
    assert audit_file.read_text(encoding="utf-8") == json.dumps(valid_entry) + "\n"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli::test_audit_repair_fix_flag_enables_repair -v`
Expected: FAIL — `--fix` is not a recognized flag, `_parse_args` returns usage error.

- [ ] **Step 5: Fix `_parse_args` — flip default and add --fix**

In `scripts/ticket_audit.py`, replace `_parse_args`:

```python
def _parse_args(argv: list[str]) -> tuple[str | None, str | None, bool, str | None]:
    dry_run = True  # Default: safe mode (report only)
    args = list(argv)
    if "--fix" in args:
        dry_run = False
        args.remove("--fix")
    if "--dry-run" in args:
        dry_run = True
        args.remove("--dry-run")
    if len(args) != 2 or args[0] != "repair":
        return None, None, True, "Usage: ticket_audit.py repair <tickets_dir> [--fix | --dry-run]"
    return args[0], args[1], dry_run, None
```

- [ ] **Step 6: Run both new tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli::test_audit_repair_default_is_dry_run tests/test_audit.py::TestAuditRepairCli::test_audit_repair_fix_flag_enables_repair -v`
Expected: PASS

- [ ] **Step 7: Update 3 existing CLI tests to use --fix**

The following tests call `_run_audit_cli("repair", "docs/tickets", cwd=...)` without flags and expect actual repair. Add `"--fix"` to each:

1. `test_audit_repair_creates_backup_and_rewrites_valid_lines` (line 585):
   `_run_audit_cli("repair", "docs/tickets", cwd=project_root)` → `_run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)`

2. `test_audit_repair_ignores_clean_files` (line 618):
   `_run_audit_cli("repair", "docs/tickets", cwd=project_root)` → `_run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)`

3. `test_audit_repair_drops_trailing_partial_line` (line 642):
   `_run_audit_cli("repair", "docs/tickets", cwd=project_root)` → `_run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)`

- [ ] **Step 8: Run all CLI tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli -v`
Expected: All 6 tests PASS (4 existing + 2 new)

- [ ] **Step 9: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_audit.py packages/plugins/ticket/tests/test_audit.py
git commit -m "fix(ticket): flip audit repair default to dry-run and add --fix flag (T-03)"
```

### Task 2: Add empty-file audit test

An empty audit file (0 bytes) should be valid — no corruption, no lines. The current code handles this implicitly via `splitlines()` returning `[]`, but there's no test.

**Files:**
- Modify: `tests/test_audit.py`

- [ ] **Step 1: Write the test**

Add to `TestAuditRepairCli`:

```python
def test_audit_repair_empty_file_is_valid(self, tmp_tickets: Path) -> None:
    """Empty audit file is valid — 0 lines, no corruption."""
    project_root = tmp_tickets.parents[1]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_dir = tmp_tickets / ".audit" / today
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "empty.jsonl"
    audit_file.write_text("", encoding="utf-8")

    result = _run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["files_scanned"] == 1
    assert payload["data"]["corrupt_files"] == 0
    assert payload["data"]["repaired_files"] == []
```

- [ ] **Step 2: Run test**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli::test_audit_repair_empty_file_is_valid -v`
Expected: PASS (existing code handles this correctly)

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/tests/test_audit.py
git commit -m "test(ticket): add empty-file audit repair test (T-03)"
```

### Task 3: Add permission-error repair test

The `repair_audit_logs` function catches `OSError` from `_scan_audit_file` and returns an error response. This path is untested in the CLI tests.

**Files:**
- Modify: `tests/test_audit.py`

- [ ] **Step 1: Write the test**

Add to `TestAuditRepairCli`:

```python
def test_audit_repair_permission_error_reported(self, tmp_tickets: Path) -> None:
    """Permission error reading audit file returns error state."""
    import os

    if sys.platform == "win32":
        pytest.skip("chmod not effective on Windows")

    project_root = tmp_tickets.parents[1]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    audit_dir = tmp_tickets / ".audit" / today
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "perm.jsonl"
    audit_file.write_text(
        json.dumps({"action": "create"}) + "\n", encoding="utf-8"
    )
    try:
        os.chmod(audit_file, 0o000)
        result = _run_audit_cli("repair", "docs/tickets", "--fix", cwd=project_root)
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["state"] == "error"
        assert "cannot read" in payload["message"]
    finally:
        os.chmod(audit_file, 0o644)
```

- [ ] **Step 2: Run test**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairCli::test_audit_repair_permission_error_reported -v`
Expected: PASS (existing error handling covers this)

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/tests/test_audit.py
git commit -m "test(ticket): add permission-error audit repair test (T-03)"
```

### Task 4: Add e2e repair-then-count integration test

Verify that after repairing a corrupt audit file, `engine_count_session_creates` correctly counts the remaining valid entries. This is the acceptance test: corrupt file → repair → counting works.

**Files:**
- Modify: `tests/test_audit.py`

- [ ] **Step 1: Write the test**

Add a new test class in `tests/test_audit.py`:

```python
class TestAuditRepairIntegration:
    """End-to-end: corrupt → repair → count."""

    def test_repair_then_count_returns_correct_count(self, tmp_tickets: Path) -> None:
        """After repairing a corrupt audit file, session counting works correctly."""
        session_id = "sess-repair-count"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_dir = tmp_tickets / ".audit" / today
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_file = audit_dir / f"{session_id}.jsonl"

        # Write 3 valid create attempts + 2 corrupt lines
        lines = [
            json.dumps({"action": "attempt_started", "intent": "create", "request_origin": "agent", "ts": "t1"}),
            json.dumps({"action": "create", "result": "ok_create", "request_origin": "agent"}),
            "NOT JSON AT ALL",
            json.dumps({"action": "attempt_started", "intent": "create", "request_origin": "agent", "ts": "t2"}),
            "ANOTHER BAD LINE {{{",
        ]
        audit_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Before repair: count still works (skips corrupt lines)
        assert engine_count_session_creates(session_id, tmp_tickets) == 2

        # Repair
        from scripts.ticket_audit import repair_audit_logs
        response, exit_code = repair_audit_logs(tickets_dir=tmp_tickets, dry_run=False)
        assert exit_code == 0
        assert response["data"]["corrupt_files"] == 1
        assert response["data"]["repaired_files"] == [str(audit_file)]

        # After repair: count is the same, file is clean
        assert engine_count_session_creates(session_id, tmp_tickets) == 2
        repaired_lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(repaired_lines) == 3, "Only 3 valid JSON lines should remain"
        for line in repaired_lines:
            json.loads(line)  # All lines should be valid JSON
```

- [ ] **Step 2: Run test**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_audit.py::TestAuditRepairIntegration::test_repair_then_count_returns_correct_count -v`
Expected: PASS

- [ ] **Step 3: Run full test suite to verify no regressions**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS, no regressions

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/ticket/tests/test_audit.py
git commit -m "test(ticket): add repair-then-count integration test (T-03 closeout)"
```

---

## Chunk 2: T-04a Envelope Schema + Consumer

### Task 5: Define envelope schema and validator

Create `ticket_envelope.py` with the envelope JSON schema, validation function, and field mapper.

**Design decisions (from Codex dialogue):**
- Fixed fields mirroring engine create-path vocabulary (not generic sections)
- No `status` field — consumer synthesizes `open` + `defer.active: true`
- Required `emitted_at` timestamp for provenance
- `defer.reason` = `"deferred via envelope"`

**Files:**
- Create: `scripts/ticket_envelope.py`
- Create: `tests/test_envelope.py`

- [ ] **Step 1: Write failing tests for schema validation**

Create `tests/test_envelope.py`:

```python
"""Tests for DeferredWorkEnvelope schema, validation, and ingestion."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _valid_envelope() -> dict:
    """Return a minimal valid envelope."""
    return {
        "envelope_version": "1.0",
        "title": "Fix auth timeout on large payloads",
        "problem": "Auth handler times out for payloads >10MB.",
        "source": {"type": "handoff", "ref": "session-abc", "session": "abc-123"},
        "emitted_at": "2026-03-10T06:00:00Z",
    }


class TestEnvelopeValidation:
    """Tests for validate_envelope()."""

    def test_valid_minimal_envelope(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        errors = validate_envelope(_valid_envelope())
        assert errors == []

    def test_valid_full_envelope(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        envelope = _valid_envelope()
        envelope.update({
            "context": "Found during API refactor.",
            "prior_investigation": "Checked handler.py:45.",
            "approach": "Increase timeout to 30s.",
            "acceptance_criteria": ["Payloads >10MB succeed"],
            "verification": "pytest tests/test_auth.py -v",
            "key_files": [{"file": "handler.py:45", "role": "Timeout logic", "look_for": "timeout constant"}],
            "key_file_paths": ["handler.py"],
            "suggested_priority": "high",
            "suggested_tags": ["auth", "api"],
        })
        errors = validate_envelope(envelope)
        assert errors == []

    def test_missing_required_field_title(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        del env["title"]
        errors = validate_envelope(env)
        assert any("title" in e for e in errors)

    def test_missing_required_field_problem(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        del env["problem"]
        errors = validate_envelope(env)
        assert any("problem" in e for e in errors)

    def test_missing_required_field_source(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        del env["source"]
        errors = validate_envelope(env)
        assert any("source" in e for e in errors)

    def test_missing_required_field_emitted_at(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        del env["emitted_at"]
        errors = validate_envelope(env)
        assert any("emitted_at" in e for e in errors)

    def test_invalid_envelope_version(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        env["envelope_version"] = "2.0"
        errors = validate_envelope(env)
        assert any("envelope_version" in e for e in errors)

    def test_source_missing_required_keys(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        env["source"] = {"type": "handoff"}  # missing ref, session
        errors = validate_envelope(env)
        assert any("ref" in e for e in errors)
        assert any("session" in e for e in errors)

    def test_invalid_suggested_priority(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        env["suggested_priority"] = "urgent"
        errors = validate_envelope(env)
        assert any("suggested_priority" in e for e in errors)

    def test_key_files_missing_required_keys(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        env["key_files"] = [{"file": "foo.py"}]  # missing role, look_for
        errors = validate_envelope(env)
        assert any("role" in e for e in errors)

    def test_unknown_fields_rejected(self) -> None:
        from scripts.ticket_envelope import validate_envelope
        env = _valid_envelope()
        env["unknown_field"] = "surprise"
        errors = validate_envelope(env)
        assert any("unknown" in e.lower() for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeValidation -v`
Expected: FAIL — `scripts.ticket_envelope` does not exist.

- [ ] **Step 3: Implement validate_envelope**

Create `scripts/ticket_envelope.py`:

```python
"""DeferredWorkEnvelope schema validation, field mapping, and lifecycle.

Envelopes are the bridge between the handoff plugin's /save skill and the
ticket plugin's creation pipeline. The handoff writes envelopes; the ticket
plugin consumes them through the normal engine pipeline.

Schema version: 1.0
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ENVELOPE_VERSION = "1.0"

_REQUIRED_FIELDS = ("envelope_version", "title", "problem", "source", "emitted_at")

_OPTIONAL_FIELDS = (
    "context",
    "prior_investigation",
    "approach",
    "acceptance_criteria",
    "verification",
    "key_files",
    "key_file_paths",
    "suggested_priority",
    "suggested_tags",
)

_ALL_FIELDS = frozenset(_REQUIRED_FIELDS + _OPTIONAL_FIELDS)

_VALID_PRIORITIES = frozenset({"critical", "high", "medium", "low"})

_SOURCE_REQUIRED_KEYS = ("type", "ref", "session")

_KEY_FILE_REQUIRED_KEYS = ("file", "role", "look_for")


def validate_envelope(envelope: dict[str, Any]) -> list[str]:
    """Validate envelope against the DeferredWorkEnvelope schema.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # Unknown fields
    unknown = set(envelope.keys()) - _ALL_FIELDS
    if unknown:
        errors.append(f"Unknown fields: {sorted(unknown)}")

    # Required fields
    for field in _REQUIRED_FIELDS:
        if field not in envelope:
            errors.append(f"Missing required field: {field}")

    # envelope_version
    if "envelope_version" in envelope:
        if envelope["envelope_version"] != _ENVELOPE_VERSION:
            errors.append(
                f"envelope_version must be {_ENVELOPE_VERSION!r}, "
                f"got {envelope['envelope_version']!r}"
            )

    # title, problem: must be non-empty strings
    for field in ("title", "problem"):
        if field in envelope:
            v = envelope[field]
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{field} must be a non-empty string, got {v!r:.80}")

    # emitted_at: must be a non-empty string (ISO 8601)
    if "emitted_at" in envelope:
        v = envelope["emitted_at"]
        if not isinstance(v, str) or not v.strip():
            errors.append(f"emitted_at must be a non-empty string, got {v!r:.80}")

    # source: must be dict with {type, ref, session}
    if "source" in envelope:
        v = envelope["source"]
        if not isinstance(v, dict):
            errors.append(f"source must be a dict, got {type(v).__name__}")
        else:
            for key in _SOURCE_REQUIRED_KEYS:
                if key not in v:
                    errors.append(f"source must contain '{key}' key")
            if not all(isinstance(val, str) for val in v.values()):
                errors.append("source values must all be strings")

    # suggested_priority
    if "suggested_priority" in envelope:
        v = envelope["suggested_priority"]
        if not isinstance(v, str) or v not in _VALID_PRIORITIES:
            errors.append(
                f"suggested_priority must be one of {sorted(_VALID_PRIORITIES)}, "
                f"got {v!r}"
            )

    # suggested_tags: list of strings
    if "suggested_tags" in envelope:
        v = envelope["suggested_tags"]
        if not isinstance(v, list):
            errors.append(f"suggested_tags must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, str) for item in v):
            errors.append("suggested_tags must contain only strings")

    # acceptance_criteria: list of strings
    if "acceptance_criteria" in envelope:
        v = envelope["acceptance_criteria"]
        if not isinstance(v, list):
            errors.append(f"acceptance_criteria must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, str) for item in v):
            errors.append("acceptance_criteria must contain only strings")

    # key_file_paths: list of strings
    if "key_file_paths" in envelope:
        v = envelope["key_file_paths"]
        if not isinstance(v, list):
            errors.append(f"key_file_paths must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, str) for item in v):
            errors.append("key_file_paths must contain only strings")

    # key_files: list of dicts with {file, role, look_for}
    if "key_files" in envelope:
        v = envelope["key_files"]
        if not isinstance(v, list):
            errors.append(f"key_files must be a list, got {type(v).__name__}")
        elif not all(isinstance(item, dict) for item in v):
            errors.append("key_files must contain only dicts")
        else:
            for i, item in enumerate(v):
                for key in _KEY_FILE_REQUIRED_KEYS:
                    if key not in item:
                        errors.append(f"key_files[{i}] must contain '{key}' key")

    # context, prior_investigation, approach, verification: strings
    for field in ("context", "prior_investigation", "approach", "verification"):
        if field in envelope:
            v = envelope[field]
            if not isinstance(v, str):
                errors.append(f"{field} must be a string, got {type(v).__name__}")

    return errors
```

- [ ] **Step 4: Run validation tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeValidation -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_envelope.py packages/plugins/ticket/tests/test_envelope.py
git commit -m "feat(ticket): add DeferredWorkEnvelope schema validator (T-04a)"
```

### Task 6: Add defer pass-through to _execute_create

The `_execute_create` function calls `render_ticket()` but doesn't pass the `defer` field from `fields`. This is a one-line fix needed for envelope-created tickets to carry `defer.active: true`.

**Files:**
- Modify: `scripts/ticket_engine_core.py:1508-1529`
- Modify: `tests/test_envelope.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_envelope.py`:

```python
from scripts.ticket_dedup import dedup_fingerprint as compute_dedup_fp
from scripts.ticket_engine_core import engine_execute


class TestDeferPassThrough:
    """Verify _execute_create passes defer field to render_ticket."""

    def test_create_with_defer_field_persists_in_yaml(self, tmp_tickets: Path) -> None:
        """When fields include defer, the created ticket has defer in frontmatter."""
        import yaml

        problem = "Auth handler times out."
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Fix auth timeout",
                "problem": problem,
                "defer": {
                    "active": True,
                    "reason": "deferred via envelope",
                    "deferred_at": "2026-03-10T06:00:00Z",
                },
            },
            session_id="sess-defer-1",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint=compute_dedup_fp(problem, []),
        )
        assert resp.state == "ok_create"

        ticket_path = Path(resp.data["ticket_path"])
        content = ticket_path.read_text(encoding="utf-8")

        # Extract YAML block
        import re
        yaml_match = re.search(r"```ya?ml\s*\n(.*?)```", content, re.DOTALL)
        assert yaml_match, "YAML block not found"
        frontmatter = yaml.safe_load(yaml_match.group(1))

        assert frontmatter["defer"]["active"] is True
        assert frontmatter["defer"]["reason"] == "deferred via envelope"
        assert frontmatter["defer"]["deferred_at"] == "2026-03-10T06:00:00Z"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestDeferPassThrough::test_create_with_defer_field_persists_in_yaml -v`
Expected: FAIL — `defer` key missing from frontmatter (not passed through).

- [ ] **Step 3: Add defer pass-through in _execute_create**

In `scripts/ticket_engine_core.py:1528`, within `_execute_create`'s `render_ticket(...)` call, add one line after `contract_version=_CONTRACT_VERSION,`:

```python
            contract_version=_CONTRACT_VERSION,
            defer=fields.get("defer"),  # <-- ADD THIS LINE
        )
```

This is a single-line addition. Do not replace the entire `render_ticket(...)` call.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestDeferPassThrough -v`
Expected: PASS

- [ ] **Step 5: Run full test suite for regressions**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_core.py packages/plugins/ticket/tests/test_envelope.py
git commit -m "feat(ticket): pass defer field through _execute_create to render_ticket (T-04a)"
```

### Task 7: Implement envelope-to-fields mapper

Map envelope JSON to the `fields` dict that `engine_execute` expects.

**Files:**
- Modify: `scripts/ticket_envelope.py`
- Modify: `tests/test_envelope.py`

- [ ] **Step 1: Write failing tests for field mapping**

Add to `tests/test_envelope.py`:

```python
class TestEnvelopeToFields:
    """Tests for map_envelope_to_fields()."""

    def test_minimal_envelope_mapping(self) -> None:
        from scripts.ticket_envelope import map_envelope_to_fields
        fields = map_envelope_to_fields(_valid_envelope())

        assert fields["title"] == "Fix auth timeout on large payloads"
        assert fields["problem"] == "Auth handler times out for payloads >10MB."
        assert fields["source"] == {"type": "handoff", "ref": "session-abc", "session": "abc-123"}
        assert fields["priority"] == "medium"  # default
        assert fields["tags"] == []  # default
        assert fields["defer"] == {
            "active": True,
            "reason": "deferred via envelope",
            "deferred_at": "2026-03-10T06:00:00Z",
        }

    def test_full_envelope_mapping(self) -> None:
        from scripts.ticket_envelope import map_envelope_to_fields
        env = _valid_envelope()
        env.update({
            "context": "Found during refactor.",
            "prior_investigation": "Checked handler.py.",
            "approach": "Increase timeout.",
            "acceptance_criteria": ["Large payloads succeed"],
            "verification": "pytest tests/ -v",
            "key_files": [{"file": "handler.py", "role": "Timeout", "look_for": "constant"}],
            "key_file_paths": ["handler.py"],
            "suggested_priority": "high",
            "suggested_tags": ["auth"],
        })
        fields = map_envelope_to_fields(env)

        assert fields["priority"] == "high"
        assert fields["tags"] == ["auth"]
        assert fields["context"] == "Found during refactor."
        assert fields["prior_investigation"] == "Checked handler.py."
        assert fields["approach"] == "Increase timeout."
        assert fields["acceptance_criteria"] == ["Large payloads succeed"]
        assert fields["verification"] == "pytest tests/ -v"
        assert fields["key_files"] == [{"file": "handler.py", "role": "Timeout", "look_for": "constant"}]
        assert fields["key_file_paths"] == ["handler.py"]

    def test_envelope_never_carries_status(self) -> None:
        from scripts.ticket_envelope import map_envelope_to_fields
        fields = map_envelope_to_fields(_valid_envelope())
        assert "status" not in fields, "Consumer synthesizes status; envelope must not carry it"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeToFields -v`
Expected: FAIL — `map_envelope_to_fields` does not exist.

- [ ] **Step 3: Implement map_envelope_to_fields**

Add to `scripts/ticket_envelope.py`:

```python
def map_envelope_to_fields(envelope: dict[str, Any]) -> dict[str, Any]:
    """Map a validated envelope to the fields dict for engine_execute.

    The consumer synthesizes ticket state — the envelope carries no status.
    Result: status=open, defer.active=true, defer.reason="deferred via envelope".
    """
    fields: dict[str, Any] = {
        "title": envelope["title"],
        "problem": envelope["problem"],
        "source": envelope["source"],
        "priority": envelope.get("suggested_priority", "medium"),
        "tags": envelope.get("suggested_tags", []),
        "defer": {
            "active": True,
            "reason": "deferred via envelope",
            "deferred_at": envelope["emitted_at"],
        },
    }

    # Optional content fields — only include if present
    for field in ("context", "prior_investigation", "approach", "verification"):
        if field in envelope:
            fields[field] = envelope[field]

    if "acceptance_criteria" in envelope:
        fields["acceptance_criteria"] = envelope["acceptance_criteria"]
    if "key_files" in envelope:
        fields["key_files"] = envelope["key_files"]
    if "key_file_paths" in envelope:
        fields["key_file_paths"] = envelope["key_file_paths"]

    return fields
```

- [ ] **Step 4: Run tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeToFields -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_envelope.py packages/plugins/ticket/tests/test_envelope.py
git commit -m "feat(ticket): add envelope-to-fields mapper (T-04a)"
```

### Task 8: Implement envelope lifecycle

Read an envelope file, validate, create ticket, and move the envelope to `.processed/`.

**Files:**
- Modify: `scripts/ticket_envelope.py`
- Modify: `tests/test_envelope.py`

- [ ] **Step 1: Write failing tests for read + lifecycle**

Add to `tests/test_envelope.py`:

```python
class TestEnvelopeRead:
    """Tests for read_envelope()."""

    def test_read_valid_envelope(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import read_envelope
        path = tmp_path / "envelope.json"
        path.write_text(json.dumps(_valid_envelope()), encoding="utf-8")

        envelope, errors = read_envelope(path)
        assert errors == []
        assert envelope is not None
        assert envelope["title"] == "Fix auth timeout on large payloads"

    def test_read_invalid_json(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import read_envelope
        path = tmp_path / "bad.json"
        path.write_text("NOT JSON {{{", encoding="utf-8")

        envelope, errors = read_envelope(path)
        assert envelope is None
        assert any("parse" in e.lower() or "json" in e.lower() for e in errors)

    def test_read_missing_file(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import read_envelope
        path = tmp_path / "missing.json"

        envelope, errors = read_envelope(path)
        assert envelope is None
        assert any("not found" in e.lower() or "does not exist" in e.lower() for e in errors)

    def test_read_invalid_schema(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import read_envelope
        path = tmp_path / "bad-schema.json"
        path.write_text(json.dumps({"title": "only title"}), encoding="utf-8")

        envelope, errors = read_envelope(path)
        assert envelope is None
        assert len(errors) > 0


class TestEnvelopeLifecycle:
    """Tests for move_to_processed()."""

    def test_move_creates_processed_dir(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import move_to_processed
        envelopes_dir = tmp_path / ".envelopes"
        envelopes_dir.mkdir()
        path = envelopes_dir / "2026-03-10T060000Z-fix-auth.json"
        path.write_text("{}", encoding="utf-8")

        dest = move_to_processed(path)

        assert dest.parent == envelopes_dir / ".processed"
        assert dest.name == path.name
        assert dest.exists()
        assert not path.exists()

    def test_move_existing_processed_dir(self, tmp_path: Path) -> None:
        from scripts.ticket_envelope import move_to_processed
        envelopes_dir = tmp_path / ".envelopes"
        processed_dir = envelopes_dir / ".processed"
        processed_dir.mkdir(parents=True)
        path = envelopes_dir / "envelope.json"
        path.write_text("{}", encoding="utf-8")

        dest = move_to_processed(path)
        assert dest.exists()
        assert not path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeRead tests/test_envelope.py::TestEnvelopeLifecycle -v`
Expected: FAIL — functions do not exist.

- [ ] **Step 3: Implement read_envelope and move_to_processed**

Add to `scripts/ticket_envelope.py` (`json` is already imported from Task 5):

```python
def read_envelope(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read and validate an envelope JSON file.

    Returns (envelope_dict, errors). On success, errors is empty.
    On failure, envelope is None and errors contains the reasons.
    """
    if not path.exists():
        return None, [f"Envelope not found: {path} does not exist"]

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"Cannot read envelope: {exc}"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"Envelope JSON parse failed: {exc}"]

    if not isinstance(data, dict):
        return None, [f"Envelope must be a JSON object, got {type(data).__name__}"]

    errors = validate_envelope(data)
    if errors:
        return None, errors

    return data, []


def move_to_processed(envelope_path: Path) -> Path:
    """Move a consumed envelope to the .processed/ subdirectory.

    Creates .processed/ if it doesn't exist. Returns the destination path.
    """
    processed_dir = envelope_path.parent / ".processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    dest = processed_dir / envelope_path.name
    envelope_path.rename(dest)
    return dest
```

- [ ] **Step 4: Run tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeRead tests/test_envelope.py::TestEnvelopeLifecycle -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_envelope.py packages/plugins/ticket/tests/test_envelope.py
git commit -m "feat(ticket): add envelope read, validation, and lifecycle (T-04a)"
```

### Task 9: End-to-end envelope ingestion test

Verify the full path: read envelope → validate → map fields → create ticket via engine → move to processed.

**Files:**
- Modify: `tests/test_envelope.py`

- [ ] **Step 1: Write the integration test**

Add to `tests/test_envelope.py`:

```python
class TestEnvelopeIngestion:
    """End-to-end: envelope file → ticket creation → envelope archived."""

    def test_envelope_to_ticket_full_pipeline(self, tmp_tickets: Path) -> None:
        """Read envelope, map fields, create ticket, move to processed."""
        import re
        import yaml
        from scripts.ticket_envelope import read_envelope, map_envelope_to_fields, move_to_processed
        from scripts.ticket_dedup import dedup_fingerprint as compute_dedup_fp

        # Set up envelope
        envelopes_dir = tmp_tickets / ".envelopes"
        envelopes_dir.mkdir()
        envelope_data = _valid_envelope()
        envelope_data["suggested_priority"] = "high"
        envelope_data["suggested_tags"] = ["auth"]
        envelope_data["context"] = "Found during API refactor."
        envelope_path = envelopes_dir / "2026-03-10T060000Z-fix-auth.json"
        envelope_path.write_text(json.dumps(envelope_data), encoding="utf-8")

        # Read and validate
        envelope, errors = read_envelope(envelope_path)
        assert errors == []
        assert envelope is not None

        # Map to engine fields
        fields = map_envelope_to_fields(envelope)

        # Create ticket via engine
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="sess-envelope-1",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
            hook_injected=True,
            hook_request_origin="user",
            classify_intent="create",
            classify_confidence=0.95,
            dedup_fingerprint=compute_dedup_fp(fields["problem"], fields.get("key_file_paths", [])),
        )
        assert resp.state == "ok_create"

        # Verify ticket content
        ticket_path = Path(resp.data["ticket_path"])
        content = ticket_path.read_text(encoding="utf-8")
        yaml_match = re.search(r"```ya?ml\s*\n(.*?)```", content, re.DOTALL)
        assert yaml_match
        frontmatter = yaml.safe_load(yaml_match.group(1))

        assert frontmatter["priority"] == "high"
        assert frontmatter["tags"] == ["auth"]
        assert frontmatter["defer"]["active"] is True
        assert frontmatter["defer"]["reason"] == "deferred via envelope"
        assert frontmatter["source"]["type"] == "handoff"
        assert "## Context" in content
        assert "Found during API refactor." in content

        # Move envelope to processed
        dest = move_to_processed(envelope_path)
        assert dest.exists()
        assert not envelope_path.exists()
        assert dest.parent.name == ".processed"
```

- [ ] **Step 2: Run test**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py::TestEnvelopeIngestion -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS, no regressions

- [ ] **Step 4: Commit**

```bash
git add packages/plugins/ticket/tests/test_envelope.py
git commit -m "test(ticket): add end-to-end envelope ingestion test (T-04a)"
```

### Task 10: Update ticket-contract.md with envelope schema

Document the DeferredWorkEnvelope schema in the ticket contract.

**Files:**
- Modify: `references/ticket-contract.md`

- [ ] **Step 1: Add §11 Envelope Schema**

Append after `## 10. Versioning` in `references/ticket-contract.md` (§9 is Integration, §10 is Versioning — both already exist):

```markdown
## 11. DeferredWorkEnvelope Schema (v1.0)

Bridge format for deferred work items from the handoff plugin. Envelopes are JSON files consumed by the ticket engine to create deferred tickets.

### Storage

- Incoming: `docs/tickets/.envelopes/<timestamp>-<slug>.json`
- Processed: `docs/tickets/.envelopes/.processed/<filename>`
- Retention: processed envelopes follow the same retention policy as archived tickets

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `envelope_version` | string | Must be "1.0" |
| `title` | string | Ticket title |
| `problem` | string | Problem description |
| `source` | object | `{type: string, ref: string, session: string}` |
| `emitted_at` | string | ISO 8601 UTC timestamp when envelope was created |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `context` | string | "" | Context section content |
| `prior_investigation` | string | "" | Prior investigation section content |
| `approach` | string | "" | Approach section content |
| `acceptance_criteria` | list[string] | [] | Acceptance criteria items |
| `verification` | string | "" | Verification command |
| `key_files` | list[object] | [] | `{file, role, look_for}` table rows |
| `key_file_paths` | list[string] | [] | File paths for dedup fingerprinting |
| `suggested_priority` | string | "medium" | One of: critical, high, medium, low |
| `suggested_tags` | list[string] | [] | Categorization tags |

### Consumer Behavior

The ticket engine's envelope consumer:
1. Reads and validates the JSON against this schema
2. Maps fields to engine create vocabulary (no `status` — consumer synthesizes `open` with `defer.active: true`)
3. Sets `defer.reason` to `"deferred via envelope"` and `defer.deferred_at` to `emitted_at`
4. Creates ticket through the normal engine pipeline
5. Moves consumed envelope to `.processed/`

### Invariants

- Envelopes carry no `status` field — the consumer is the sole authority for initial ticket state
- `emitted_at` is required for provenance — it becomes `defer.deferred_at`
- Unknown fields are rejected (closed schema)
```

- [ ] **Step 2: Commit**

```bash
git add packages/plugins/ticket/references/ticket-contract.md
git commit -m "docs(ticket): add DeferredWorkEnvelope schema to contract §9 (T-04a)"
```

---

## Summary

| Chunk | Tasks | Tests Added | Commits |
|-------|-------|-------------|---------|
| 1: T-03 closeout | 4 | +5 | 4 |
| 2: T-04a envelope | 6 | ~20 | 5 |
| **Total** | **10** | **~25** | **9** |

### Post-Implementation Checklist

- [ ] All existing tests still pass (630 baseline)
- [ ] T-03 acceptance criteria can be checked off
- [ ] T-04a acceptance criteria (ticket-side only) can be checked off
- [ ] Backlog rewrite: update T-04 to reflect T-04a/T-04b/T-04c split
the sole authority for initial ticket state
- `emitted_at` is required for provenance — it becomes `defer.deferred_at`
- Unknown fields are rejected (closed schema)
```

- [ ] **Step 2: Commit**

```bash
git add packages/plugins/ticket/references/ticket-contract.md
git commit -m "docs(ticket): add DeferredWorkEnvelope schema to contract §9 (T-04a)"
```

---

## Summary

| Chunk | Tasks | Tests Added | Commits |
|-------|-------|-------------|---------|
| 1: T-03 closeout | 4 | +5 | 4 |
| 2: T-04a envelope | 6 | ~20 | 5 |
| **Total** | **10** | **~25** | **9** |

### Post-Implementation Checklist

- [ ] All existing tests still pass (630 baseline)
- [ ] T-03 acceptance criteria can be checked off
- [ ] T-04a acceptance criteria (ticket-side only) can be checked off
- [ ] Backlog rewrite: update T-04 to reflect T-04a/T-04b/T-04c split
