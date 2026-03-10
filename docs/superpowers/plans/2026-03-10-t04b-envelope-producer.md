# T-04b: Envelope Producer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert `/defer` from direct ticket writing to envelope emission through the ticket engine pipeline.

**Architecture:** `defer.py` emits DeferredWorkEnvelope JSON to `.envelopes/`. SKILL.md then calls `ticket_engine_user.py ingest` (a new subcommand) which runs the full engine pipeline (plan → preflight → execute) and moves the envelope to `.processed/`. Cross-plugin boundary is a JSON file on disk + CLI subprocess.

**Tech Stack:** Python 3.14, pytest, uv. Ticket plugin at `packages/plugins/ticket/`, handoff plugin at `packages/plugins/handoff/`.

**Spec:** `docs/superpowers/specs/2026-03-10-t04b-envelope-producer-design.md`

**Test runner:**
- Ticket: `cd packages/plugins/ticket && uv run pytest tests/ -v`
- Handoff: `cd packages/plugins/handoff && uv run pytest tests/ -v`

---

## Chunk 1: Ticket Plugin — Envelope Schema + Ingest Subcommand

### Task 1: Add `effort` to envelope schema

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_envelope.py`
- Modify: `packages/plugins/ticket/tests/test_envelope.py`
- Modify: `packages/plugins/ticket/references/ticket-contract.md`

- [ ] **Step 1: Write failing tests for effort field**

Add to `tests/test_envelope.py` in `TestEnvelopeValidation`:

```python
def test_effort_accepted_as_optional(self) -> None:
    """effort is a valid optional string field."""
    from scripts.ticket_envelope import validate_envelope

    envelope = _valid_envelope()
    envelope["effort"] = "M"
    errors = validate_envelope(envelope)
    assert errors == []

def test_effort_non_string_rejected(self) -> None:
    """Non-string effort is rejected."""
    from scripts.ticket_envelope import validate_envelope

    envelope = _valid_envelope()
    envelope["effort"] = 42
    errors = validate_envelope(envelope)
    assert any("effort" in e for e in errors)
```

Add to `TestEnvelopeToFields`:

```python
def test_effort_passed_through(self) -> None:
    """effort is mapped to fields when present."""
    from scripts.ticket_envelope import map_envelope_to_fields

    envelope = _valid_envelope()
    envelope["effort"] = "XL"
    fields = map_envelope_to_fields(envelope)
    assert fields["effort"] == "XL"

def test_effort_absent_not_in_fields(self) -> None:
    """effort is not in fields when absent from envelope."""
    from scripts.ticket_envelope import map_envelope_to_fields

    envelope = _valid_envelope()
    fields = map_envelope_to_fields(envelope)
    assert "effort" not in fields
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py -v -k "effort"`
Expected: 2 FAIL (effort_accepted rejected as unknown field, effort_passed_through has no effort in fields), 2 PASS (effort_non_string_rejected passes via unknown-field error containing "effort", effort_absent passes trivially)

- [ ] **Step 3: Implement effort support**

In `packages/plugins/ticket/scripts/ticket_envelope.py`:

Add `"effort"` to `_OPTIONAL_FIELDS` tuple (after `"suggested_tags"`):

```python
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
    "effort",
)
```

Add effort type validation in `validate_envelope()`, after the `verification` string checks:

```python
# effort: optional string
if "effort" in envelope:
    v = envelope["effort"]
    if not isinstance(v, str):
        errors.append(f"effort must be a string, got {type(v).__name__}")
```

Add effort pass-through in `map_envelope_to_fields()`, after the `key_file_paths` block:

```python
if "effort" in envelope:
    fields["effort"] = envelope["effort"]
```

Fix module docstring (line 5): change `/save` to `/defer` (or "handoff plugin's /save and /defer skills").

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py -v -k "effort"`
Expected: 4 PASS

- [ ] **Step 5: Update contract §11**

In `packages/plugins/ticket/references/ticket-contract.md`, add `effort` row to the Optional Fields table:

```markdown
| `effort` | string | "S" | Effort estimate (freeform) |
```

- [ ] **Step 6: Run full envelope test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_envelope.py -v`
Expected: All pass (existing 23 + 4 new = 27)

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_envelope.py packages/plugins/ticket/tests/test_envelope.py packages/plugins/ticket/references/ticket-contract.md
git commit -m "feat(ticket): add effort field to DeferredWorkEnvelope schema (T-04b)"
```

---

### Task 2: Add `ingest` to guard VALID_SUBCOMMANDS

**Files:**
- Modify: `packages/plugins/ticket/hooks/ticket_engine_guard.py`

- [ ] **Step 1: Add `"ingest"` to VALID_SUBCOMMANDS**

In `packages/plugins/ticket/hooks/ticket_engine_guard.py`, change:

```python
VALID_SUBCOMMANDS = frozenset({"classify", "plan", "preflight", "execute"})
```

to:

```python
VALID_SUBCOMMANDS = frozenset({"classify", "plan", "preflight", "execute", "ingest"})
```

- [ ] **Step 2: Run guard tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v -k "guard"`
Expected: All existing guard tests pass (the guard uses this frozenset for validation; adding a value doesn't break existing tests).

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/hooks/ticket_engine_guard.py
git commit -m "feat(ticket): add ingest to guard VALID_SUBCOMMANDS (T-04b)"
```

---

### Task 3: Add IngestInput stage model

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_stage_models.py`

- [ ] **Step 1: Add IngestInput dataclass**

At the end of `packages/plugins/ticket/scripts/ticket_stage_models.py` (after `ExecuteInput`), add:

```python
@dataclass(frozen=True)
class IngestInput:
    """Input model for the ingest stage.

    Receives an envelope path. The ingest handler reads, validates, maps,
    and runs the full engine pipeline internally.
    """

    envelope_path: str
    session_id: str
    hook_injected: bool
    hook_request_origin: str | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> IngestInput:
        envelope_path = _get_str(payload, "envelope_path", default="")
        if not envelope_path:
            raise PayloadError(
                "envelope_path is required",
                code="need_fields",
                state="need_fields",
            )
        return cls(
            envelope_path=envelope_path,
            session_id=_get_str(payload, "session_id", default=""),
            hook_injected=_get_bool(payload, "hook_injected", default=False),
            hook_request_origin=_get_optional_str(payload, "hook_request_origin"),
        )
```

- [ ] **Step 2: Verify import and construction works**

Run: `cd packages/plugins/ticket && uv run python -c "from scripts.ticket_stage_models import IngestInput; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_stage_models.py
git commit -m "feat(ticket): add IngestInput stage model (T-04b)"
```

---

### Task 4: Implement ingest subcommand in runner

This is the largest task — the ingest handler orchestrates read → validate → map → plan → preflight → execute → move.

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_runner.py`
- Create: `packages/plugins/ticket/tests/test_ingest.py`

- [ ] **Step 1: Write the ingest e2e test**

Create `packages/plugins/ticket/tests/test_ingest.py`:

```python
"""Tests for the ingest subcommand."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


def _valid_envelope() -> dict:
    """Minimal valid envelope for testing."""
    return {
        "envelope_version": "1.0",
        "title": "Fix timeout in auth handler",
        "problem": "Auth handler times out for payloads >10MB.",
        "source": {"type": "handoff", "ref": "session-abc", "session": "abc-123"},
        "emitted_at": "2026-03-10T12:00:00Z",
    }


def _write_envelope(envelope: dict, envelopes_dir: Path) -> Path:
    """Write envelope JSON to the envelopes directory."""
    envelopes_dir.mkdir(parents=True, exist_ok=True)
    path = envelopes_dir / "2026-03-10T120000Z-fix-timeout.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return path


class TestIngestSubcommand:
    def test_happy_path(self, tmp_path: Path) -> None:
        """Ingest reads envelope, creates ticket, moves to processed."""
        from scripts.ticket_engine_runner import run

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)
        envelopes_dir = tickets_dir / ".envelopes"
        envelope_path = _write_envelope(_valid_envelope(), envelopes_dir)

        payload = {
            "envelope_path": str(envelope_path),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }

        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload))

        exit_code = run(
            "user",
            argv=["ingest", str(payload_file)],
            prog="test",
        )

        assert exit_code == 0
        # Envelope moved to .processed/
        assert not envelope_path.exists()
        processed = envelopes_dir / ".processed" / envelope_path.name
        assert processed.exists()
        # Ticket created
        ticket_files = list(tickets_dir.glob("*.md"))
        assert len(ticket_files) == 1

    def test_invalid_envelope_returns_error(self, tmp_path: Path) -> None:
        """Ingest with invalid envelope returns error response."""
        from scripts.ticket_engine_runner import run

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)
        envelopes_dir = tickets_dir / ".envelopes"
        bad_envelope = {"envelope_version": "1.0"}  # Missing required fields
        envelope_path = _write_envelope(bad_envelope, envelopes_dir)

        payload = {
            "envelope_path": str(envelope_path),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }

        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload))

        exit_code = run(
            "user",
            argv=["ingest", str(payload_file)],
            prog="test",
        )

        assert exit_code == 1
        # Envelope NOT moved (still in place)
        assert envelope_path.exists()

    def test_missing_envelope_returns_error(self, tmp_path: Path) -> None:
        """Ingest with nonexistent envelope path returns error."""
        from scripts.ticket_engine_runner import run

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)

        payload = {
            "envelope_path": str(tmp_path / "nonexistent.json"),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }

        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload))

        exit_code = run(
            "user",
            argv=["ingest", str(payload_file)],
            prog="test",
        )

        assert exit_code == 1

    def test_dedup_detected(self, tmp_path: Path) -> None:
        """Ingest detects duplicate and returns duplicate_candidate state."""
        from scripts.ticket_engine_runner import run

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)
        envelopes_dir = tickets_dir / ".envelopes"

        # Ingest first envelope — should succeed.
        envelope_path_1 = _write_envelope(_valid_envelope(), envelopes_dir)
        payload = {
            "envelope_path": str(envelope_path_1),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }
        payload_file = tmp_path / "payload1.json"
        payload_file.write_text(json.dumps(payload))
        exit_code = run("user", argv=["ingest", str(payload_file)], prog="test")
        assert exit_code == 0

        # Ingest second envelope with same problem text — should detect duplicate.
        envelope_path_2 = envelopes_dir / "2026-03-10T120001Z-fix-timeout-2.json"
        envelope_path_2.write_text(json.dumps(_valid_envelope()), encoding="utf-8")
        payload2 = {
            "envelope_path": str(envelope_path_2),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }
        payload_file2 = tmp_path / "payload2.json"
        payload_file2.write_text(json.dumps(payload2))
        exit_code2 = run("user", argv=["ingest", str(payload_file2)], prog="test")
        assert exit_code2 == 1  # Duplicate detected, not created

    def test_ingest_with_effort(self, tmp_path: Path) -> None:
        """Envelope with effort field creates ticket with effort in frontmatter."""
        from scripts.ticket_engine_runner import run

        tickets_dir = tmp_path / "docs" / "tickets"
        tickets_dir.mkdir(parents=True)
        envelopes_dir = tickets_dir / ".envelopes"
        envelope = _valid_envelope()
        envelope["effort"] = "M"
        envelope_path = _write_envelope(envelope, envelopes_dir)

        payload = {
            "envelope_path": str(envelope_path),
            "tickets_dir": str(tickets_dir),
            "session_id": "test-session",
            "hook_injected": True,
            "hook_request_origin": "user",
        }

        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload))

        exit_code = run(
            "user",
            argv=["ingest", str(payload_file)],
            prog="test",
        )

        assert exit_code == 0
        ticket_files = list(tickets_dir.glob("*.md"))
        assert len(ticket_files) == 1
        content = ticket_files[0].read_text()
        assert "effort:" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_ingest.py -v`
Expected: All FAIL (Unknown subcommand: 'ingest')

Note: the dedup test (`test_dedup_detected`) will also fail because the first ingest fails before creating any ticket.

- [ ] **Step 3: Extend runner trust triple check to cover ingest**

In `packages/plugins/ticket/scripts/ticket_engine_runner.py`, change line 89:

```python
if subcommand == "execute":
```

to:

```python
if subcommand in ("execute", "ingest"):
```

- [ ] **Step 4: Add ingest import and dispatch branch**

At the top of `ticket_engine_runner.py`, add to imports:

```python
from scripts.ticket_stage_models import (
    ClassifyInput,
    ExecuteInput,
    IngestInput,
    PlanInput,
    PreflightInput,
)
```

In `_dispatch()`, add a new `elif` branch before the `else` at the end:

```python
elif subcommand == "ingest":
    inp = IngestInput.from_payload(payload)
    return _dispatch_ingest(inp, payload, tickets_dir, request_origin)
```

- [ ] **Step 5: Implement _dispatch_ingest**

Add this function to `ticket_engine_runner.py` (before `_dispatch`):

```python
def _dispatch_ingest(
    inp: IngestInput,
    payload: dict[str, Any],
    tickets_dir: Path,
    request_origin: str,
) -> EngineResponse:
    """Orchestrate envelope ingestion: read → validate → map → plan → preflight → execute → move."""
    from scripts.ticket_envelope import map_envelope_to_fields, move_to_processed, read_envelope

    envelope_path = Path(inp.envelope_path)

    # Step 1: Read and validate envelope.
    envelope, errors = read_envelope(envelope_path)
    if envelope is None:
        return EngineResponse(
            state="need_fields",
            message=f"Envelope validation failed: {'; '.join(errors)}",
            error_code="need_fields",
            data={"validation_errors": errors},
        )

    # Step 2: Map envelope fields to engine vocabulary.
    fields = map_envelope_to_fields(envelope)

    # Step 3: Plan — computes dedup fingerprint, scans for duplicates.
    plan_resp = engine_plan(
        intent="create",
        fields=fields,
        session_id=inp.session_id,
        request_origin=request_origin,
        tickets_dir=tickets_dir,
        ticket_id=None,
    )
    if plan_resp.state != "ok":
        return plan_resp

    # Extract plan outputs for preflight.
    plan_data = plan_resp.data or {}
    dedup_fp = plan_data.get("dedup_fingerprint")
    duplicate_of = plan_data.get("duplicate_of")

    # Step 4: Preflight — all policy checks.
    preflight_resp = engine_preflight(
        ticket_id=None,
        action="create",
        session_id=inp.session_id,
        request_origin=request_origin,
        classify_confidence=1.0,
        classify_intent="create",
        dedup_fingerprint=dedup_fp,
        target_fingerprint=None,
        fields=fields,
        duplicate_of=duplicate_of,
        dedup_override=False,
        dependency_override=False,
        hook_injected=inp.hook_injected,
        tickets_dir=tickets_dir,
    )
    if preflight_resp.state != "ok":
        return preflight_resp

    # Step 5: Execute — create the ticket.
    exec_resp = engine_execute(
        action="create",
        ticket_id=None,
        fields=fields,
        session_id=inp.session_id,
        request_origin=request_origin,
        dedup_override=False,
        dependency_override=False,
        tickets_dir=tickets_dir,
        target_fingerprint=None,
        hook_injected=inp.hook_injected,
        hook_request_origin=inp.hook_request_origin,
        classify_intent="create",
        classify_confidence=1.0,
        dedup_fingerprint=dedup_fp,
        duplicate_of=duplicate_of,
    )
    if not exec_resp.state.startswith("ok"):
        return exec_resp

    # Step 6: Move envelope to processed.
    try:
        move_to_processed(envelope_path)
    except FileExistsError as exc:
        # Ticket was created but envelope move failed. Not fatal — report in data.
        exec_resp = EngineResponse(
            state=exec_resp.state,
            message=f"{exec_resp.message}; envelope move failed: {exc}",
            ticket_id=exec_resp.ticket_id,
            data={**(exec_resp.data or {}), "envelope_move_error": str(exc)},
        )

    return exec_resp
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_ingest.py -v`
Expected: 5 PASS

- [ ] **Step 7: Run full ticket test suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass (658 existing + 4 new ingest + 4 new effort = 666)

- [ ] **Step 8: Commit**

```bash
git add packages/plugins/ticket/scripts/ticket_engine_runner.py packages/plugins/ticket/tests/test_ingest.py
git commit -m "feat(ticket): add ingest subcommand for envelope ingestion (T-04b)"
```

---

## Chunk 2: Handoff Plugin — Envelope Producer

### Task 5: Rewrite defer.py to emit envelopes

**Files:**
- Modify: `packages/plugins/handoff/scripts/defer.py`
- Modify: `packages/plugins/handoff/tests/test_defer.py`

- [ ] **Step 1: Write failing tests for emit_envelope**

Add new test class to `packages/plugins/handoff/tests/test_defer.py`:

```python
from datetime import datetime, timezone


class TestEmitEnvelope:
    def test_minimal_candidate(self, tmp_path: Path) -> None:
        """Minimal candidate produces valid envelope JSON."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Fix auth timeout",
            "problem": "Auth handler times out for large payloads.",
            "source_text": "Found during review.",
            "proposed_approach": "Increase timeout.",
            "acceptance_criteria": ["Timeout works for 10MB"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-1",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        assert path.exists()
        assert path.suffix == ".json"
        data = json.loads(path.read_text())
        assert data["envelope_version"] == "1.0"
        assert data["title"] == "Fix auth timeout"
        assert data["problem"] == "Auth handler times out for large payloads."
        assert data["source"]["type"] == "ad-hoc"
        assert data["source"]["session"] == "sess-1"
        assert data["suggested_priority"] == "medium"
        assert data["approach"] == "Increase timeout."
        assert data["acceptance_criteria"] == ["Timeout works for 10MB"]
        assert "emitted_at" in data
        assert "status" not in data

    def test_full_candidate_with_effort_and_files(self, tmp_path: Path) -> None:
        """All candidate fields mapped correctly including effort."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Refactor parser",
            "problem": "Parser is too slow.",
            "source_text": "Profiling showed bottleneck.",
            "proposed_approach": "Use streaming parser.",
            "acceptance_criteria": ["10x faster", "No regressions"],
            "priority": "high",
            "effort": "M",
            "source_type": "pr-review",
            "source_ref": "PR #42",
            "session_id": "sess-2",
            "branch": "feature/parser",
            "files": ["src/parser.py", "src/lexer.py"],
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert data["effort"] == "M"
        assert data["key_file_paths"] == ["src/parser.py", "src/lexer.py"]
        assert data["suggested_priority"] == "high"
        assert data["source"]["ref"] == "PR #42"

    def test_context_composition(self, tmp_path: Path) -> None:
        """Branch and source_text composed into context field."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Test context",
            "problem": "Problem text.",
            "source_text": "User said to defer this.",
            "proposed_approach": "TBD.",
            "acceptance_criteria": ["Done"],
            "priority": "low",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-3",
            "branch": "fix/auth",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert "context" in data
        assert "Captured on branch `fix/auth`" in data["context"]
        assert 'Evidence anchor:' in data["context"]
        assert "User said to defer this." in data["context"]

    def test_no_status_field(self, tmp_path: Path) -> None:
        """Envelope never contains status field."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "No status",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Fixed"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-4",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        assert "status" not in data

    def test_emitted_at_is_iso8601(self, tmp_path: Path) -> None:
        """emitted_at is a valid ISO 8601 timestamp."""
        from scripts.defer import emit_envelope

        candidate = {
            "summary": "Timestamp test",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Fixed"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-5",
        }
        envelopes_dir = tmp_path / ".envelopes"
        path = emit_envelope(candidate, envelopes_dir)

        data = json.loads(path.read_text())
        # Should parse without error
        ts = datetime.fromisoformat(data["emitted_at"])
        assert ts.tzinfo is not None  # Must be timezone-aware
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestEmitEnvelope -v`
Expected: All FAIL (emit_envelope doesn't exist)

- [ ] **Step 3: Implement emit_envelope**

Replace the entire `packages/plugins/handoff/scripts/defer.py` with:

```python
"""Envelope emission logic for /defer skill.

Deterministic: builds DeferredWorkEnvelope JSON, writes to .envelopes/.
LLM extraction happens in the SKILL.md — this script receives candidates.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _slug(title: str) -> str:
    """Generate a filename slug from a title.

    Lowercase, alphanumeric + hyphens, max 50 chars.
    """
    slug = re.sub(r"[^a-z0-9\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    slug = re.sub(r"-+", "-", slug)[:50].rstrip("-")
    return slug


def emit_envelope(candidate: dict[str, Any], envelopes_dir: Path) -> Path:
    """Write a DeferredWorkEnvelope JSON file. Returns the path.

    Maps /defer candidate fields to envelope schema v1.0. The envelope
    carries no status — the ticket engine consumer synthesizes it.
    """
    now = datetime.now(timezone.utc)

    envelope: dict[str, Any] = {
        "envelope_version": "1.0",
        "title": candidate["summary"],
        "problem": candidate["problem"],
        "source": {
            "type": candidate.get("source_type", "ad-hoc"),
            "ref": candidate.get("source_ref", ""),
            "session": candidate.get("session_id", ""),
        },
        "emitted_at": now.isoformat(),
    }

    # Optional fields — only include if present and non-empty.
    if candidate.get("proposed_approach"):
        envelope["approach"] = candidate["proposed_approach"]
    if candidate.get("acceptance_criteria"):
        envelope["acceptance_criteria"] = candidate["acceptance_criteria"]
    if candidate.get("priority"):
        envelope["suggested_priority"] = candidate["priority"]
    if candidate.get("effort"):
        envelope["effort"] = candidate["effort"]
    if candidate.get("files"):
        envelope["key_file_paths"] = candidate["files"]

    # Context composition: branch + source_text folded into context.
    context_parts: list[str] = []
    if candidate.get("branch"):
        context_parts.append(f"Captured on branch `{candidate['branch']}`.")
    if candidate.get("source_text"):
        context_parts.append(f"Evidence anchor:\n> \"{candidate['source_text']}\"")
    if context_parts:
        envelope["context"] = "\n\n".join(context_parts)

    # Write to envelopes directory.
    envelopes_dir.mkdir(parents=True, exist_ok=True)
    timestamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    filename = f"{timestamp}-{_slug(candidate['summary'])}.json"
    path = envelopes_dir / filename
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    return path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Reads candidate JSON from stdin, writes envelope files."""
    import argparse

    parser = argparse.ArgumentParser(description="Emit deferred work envelopes")
    parser.add_argument("--tickets-dir", type=Path, default=Path("docs/tickets"))
    args = parser.parse_args(argv)

    try:
        candidates = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        json.dump(
            {"status": "error", "envelopes": [], "errors": [{"summary": "stdin", "error": f"Invalid JSON input: {exc}"}]},
            sys.stdout,
        )
        return 1

    if not isinstance(candidates, list):
        candidates = [candidates]

    envelopes_dir = args.tickets_dir / ".envelopes"
    created: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for cand in candidates:
        if not isinstance(cand, dict):
            errors.append({
                "summary": "unknown",
                "error": f"Candidate must be a dict, got {type(cand).__name__}",
            })
            continue
        try:
            path = emit_envelope(cand, envelopes_dir)
            created.append({"path": str(path)})
        except (KeyError, OSError, TypeError, ValueError) as exc:
            errors.append({
                "summary": cand.get("summary", "unknown"),
                "error": f"{type(exc).__name__}: {exc}",
            })

    if errors and created:
        json.dump({"status": "partial_success", "envelopes": created, "errors": errors}, sys.stdout)
    elif errors:
        json.dump({"status": "error", "envelopes": [], "errors": errors}, sys.stdout)
    else:
        json.dump({"status": "ok", "envelopes": created}, sys.stdout)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run emit_envelope tests**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py::TestEmitEnvelope -v`
Expected: 5 PASS

- [ ] **Step 5: Update existing tests that test removed functions**

All existing test classes in `test_defer.py` now test dead code after the rewrite. Remove all 11 classes: `TestAllocateId`, `TestFilenameSlug`, `TestFilenameSlugThreeDigit`, `TestRenderTicket`, `TestRenderTicketEdgeCases`, `TestWriteTicket`, `TestQuoteEscaping`, `TestEnumCoercionWarning`, `TestPriorityEffortValidation`, `TestEndToEnd`, `TestMain`. Then add tests for the new `main()` output format:

```python
class TestMainEmitsEnvelopes:
    def test_main_output_format(self, tmp_path: Path) -> None:
        """CLI writes envelopes and outputs JSON with 'envelopes' key."""
        import io

        from scripts.defer import main

        candidate = {
            "summary": "CLI test",
            "problem": "Test problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"],
            "priority": "medium",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-cli",
        }
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps([candidate]))
        try:
            buf = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = buf
            try:
                code = main(["--tickets-dir", str(tmp_path)])
            finally:
                sys.stdout = original_stdout
        finally:
            sys.stdin = original_stdin

        assert code == 0
        output = json.loads(buf.getvalue())
        assert output["status"] == "ok"
        assert "envelopes" in output
        assert len(output["envelopes"]) == 1
        assert output["envelopes"][0]["path"].endswith(".json")

    def test_envelopes_written_to_dir(self, tmp_path: Path) -> None:
        """Envelopes are written to .envelopes/ subdirectory."""
        import io

        from scripts.defer import main

        candidate = {
            "summary": "Dir test",
            "problem": "Problem.",
            "source_text": "Quote.",
            "proposed_approach": "Fix.",
            "acceptance_criteria": ["Done"],
            "priority": "low",
            "source_type": "ad-hoc",
            "source_ref": "",
            "session_id": "sess-dir",
        }
        original_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps([candidate]))
        try:
            buf = io.StringIO()
            original_stdout = sys.stdout
            sys.stdout = buf
            try:
                main(["--tickets-dir", str(tmp_path)])
            finally:
                sys.stdout = original_stdout
        finally:
            sys.stdin = original_stdin

        envelopes = list((tmp_path / ".envelopes").glob("*.json"))
        assert len(envelopes) == 1
```

- [ ] **Step 6: Run full defer test suite**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_defer.py -v`
Expected: All new tests pass. (Old test classes for removed functions should be deleted; if any remain, they'll fail — remove them.)

- [ ] **Step 7: Commit**

```bash
git add packages/plugins/handoff/scripts/defer.py packages/plugins/handoff/tests/test_defer.py
git commit -m "feat(handoff): rewrite defer.py to emit envelopes instead of tickets (T-04b)"
```

---

### Task 6: Update /defer SKILL.md

**Files:**
- Modify: `packages/plugins/handoff/skills/defer/SKILL.md`

- [ ] **Step 1: Update Step 4 (create tickets via defer.py)**

Replace the current Step 4 section with the two-phase flow. Key changes:

Phase 1 — Emit envelopes (same as before but without `--date`):
```bash
echo '<candidates_json>' | python "${CLAUDE_PLUGIN_ROOT}/scripts/defer.py" --tickets-dir "<project_root>/docs/tickets"
```

Phase 2 — Ingest each envelope:
```bash
# For each envelope path from Phase 1 response:
echo '{"envelope_path": "<path>"}' > /tmp/ingest_payload.json
python3 "${CLAUDE_PLUGIN_ROOT}/../ticket/scripts/ticket_engine_user.py" ingest /tmp/ingest_payload.json
```

Parse the JSON response from Phase 2 for ticket IDs and success/failure.

- [ ] **Step 2: Update Step 5 (commit)**

Add `.envelopes/.processed/*.json` to staged files alongside ticket `.md` files.

- [ ] **Step 3: Update Step 6 (report)**

Report both envelope paths (Phase 1) and ticket IDs (Phase 2).

- [ ] **Step 4: Update response status table**

Change `created` to `envelopes` in the Phase 1 response parsing.

- [ ] **Step 5: Remove `--date` from CLI examples**

The `--date` flag is no longer needed — `emitted_at` uses UTC now.

- [ ] **Step 6: Commit**

```bash
git add packages/plugins/handoff/skills/defer/SKILL.md
git commit -m "docs(handoff): update /defer SKILL.md for envelope pipeline (T-04b)"
```

---

### Task 7: Integration verification

- [ ] **Step 1: Run ticket plugin full suite**

Run: `cd packages/plugins/ticket && uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 2: Run handoff plugin full suite**

Run: `cd packages/plugins/handoff && uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 3: Verify guard allows ingest**

Run: `cd packages/plugins/ticket && uv run python -c "from hooks.ticket_engine_guard import VALID_SUBCOMMANDS; assert 'ingest' in VALID_SUBCOMMANDS; print('Guard OK')"`
Expected: `Guard OK`

- [ ] **Step 4: Verify envelope schema includes effort**

Run: `cd packages/plugins/ticket && uv run python -c "from scripts.ticket_envelope import _OPTIONAL_FIELDS; assert 'effort' in _OPTIONAL_FIELDS; print('Schema OK')"`
Expected: `Schema OK`
