# Ticket Plugin Phase 1 — Module 4: Engine

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the engine pipeline: classify, plan, preflight, and execute subcommands in `ticket_engine_core.py`.

**Architecture:** Hybrid adapter pattern (Architecture E). All four subcommands live in `ticket_engine_core.py`. Each subcommand is a pure function taking a request dict and returning a result dict. The execute subcommand contains 6 vertical TDD slices for the 4 lifecycle operations (create, update, close, reopen) plus shared helpers and a dispatcher.

**Tech Stack:** Python 3.11+, PyYAML, pytest

**References (read-only — do not modify these files):**
- Canonical plan: `docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`
- Modularization design: `docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`
- Design doc: `docs/plans/2026-03-02-ticket-plugin-design.md` (canonical spec)

**Scope:** Module 4 of 5. Creates `scripts/ticket_engine_core.py` and `tests/test_engine.py`. Tasks 8-10 are standard. Task 11 is decomposed into 6 slices (11.1-11.6) with internal checkpoints.

**Internal Checkpoint Schedule:**

| After | Checkpoint Type | What to Do |
|-------|-----------------|------------|
| Task 8 | Full | Test barrier + git commit + invariant ledger |
| Task 9 | Full | Test barrier + git commit + invariant ledger |
| Task 10 | Full | Test barrier + git commit + invariant ledger |
| Task 11.1 | Full | Test barrier + git commit + invariant ledger |
| Task 11.2 | Commit only | Git commit |
| Task 11.3 | Full | Test barrier + git commit + invariant ledger |
| Task 11.4 | Commit only | Git commit |
| Task 11.5 | Commit only | Git commit |
| Task 11.6 | Full (final) | Test barrier + git commit + invariant ledger |

---

## Phase 1 Scope Policy

**Phase 1 Scope Policy (strict fail-closed):**
- All agent mutations are **hard-blocked** in Phase 1 — `engine_preflight` returns `policy_blocked` for `request_origin="agent"` regardless of autonomy mode. Rationale: the PreToolUse hook (Phase 2) is required to inject `hook_injected: true` and `session_id`; without it, agent paths cannot be legitimately exercised.
- `hook_injected` field validation is **deferred to Phase 2** — the hook that sets it doesn't exist yet.
- Audit trail writes (`attempt_started`/`attempt_result` JSONL) are **deferred to Phase 2** — they require `session_id` injection from the hook.
- `auto_audit` and `auto_silent` autonomy modes are structurally unreachable in Phase 1 (blocked by the hard-block above). Tests verify the hard-block, not the mode-specific behavior.
- `ticket_triage.py` is **deferred to Phase 2** — the design doc lists it in the plugin structure, but it implements read-only analysis capabilities (orphan detection, audit trail reporting) that depend on the Phase 2 audit trail. No task in this plan creates `ticket_triage.py` or `test_triage.py`.

**Deferred tickets (not Phase 1):**
- T-20260302-01: auto_audit notification UX flows (Phase 2 — skill UX)
- T-20260302-02: merge_into_existing v1.1 (reserved state, escalate fallback)
- T-20260302-03: ticket audit repair (Phase 2 — added to ticket-ops)
- T-20260302-04: DeferredWorkEnvelope (Phase 4)
- T-20260302-05: foreground-only enforcement (Phase 3)

---

## Prerequisites

**From Module 1:** Plugin scaffold, conftest.py with all helpers and fixtures.

**From Module 2:** `scripts/ticket_parse.py`:
- `ParsedTicket`, `parse_ticket`, `extract_fenced_yaml`, `parse_yaml_block`

**From Module 3 — all utility modules:**
- `scripts/ticket_id.py`: `allocate_id`, `build_filename`
- `scripts/ticket_render.py`: `render_ticket`
- `scripts/ticket_read.py`: `find_ticket_by_id`, `list_tickets`
- `scripts/ticket_dedup.py`: `dedup_fingerprint`, `normalize`, `target_fingerprint`

**Cumulative test files (all passing):** test_parse.py, test_migration.py, test_id.py, test_render.py, test_read.py, test_dedup.py

**M3→M4 gate passed:** Critical gate — full upstream re-run + M4's complete import subset verified.

## Gate Entry: M3 → M4

Verify before starting:
```bash
cd packages/plugins/ticket && uv run pytest tests/ -v
```
All 6 test files must pass. All import sentinels from M3→M4 gate card must succeed.

---

## Task 8: ticket_engine_core.py — classify Subcommand

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Create: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Engine Design" (lines ~301-340), "Engine Interface" (contract section 4), "Autonomy Enforcement" (lines ~409-451). This task implements `classify` only — subsequent tasks add `plan`, `preflight`, and `execute`.

**Step 1: Write failing tests**

```python
"""Tests for ticket_engine_core.py — engine pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
)


class TestEngineClassify:
    def test_create_intent(self):
        resp = engine_classify(
            action="create",
            args={"title": "Fix auth bug"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "create"
        assert resp.data["confidence"] >= 0.0

    def test_update_intent(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "update"

    def test_close_intent(self):
        resp = engine_classify(
            action="close",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "close"

    def test_reopen_intent(self):
        resp = engine_classify(
            action="reopen",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "ok"
        assert resp.data["intent"] == "reopen"

    def test_unknown_action(self):
        resp = engine_classify(
            action="banana",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.state == "escalate"

    def test_unknown_origin_fails_closed(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="unknown",
        )
        assert resp.state == "escalate"
        assert "caller identity" in resp.message.lower()

    def test_resolved_ticket_id(self):
        resp = engine_classify(
            action="update",
            args={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] == "T-20260302-01"

    def test_create_has_no_resolved_id(self):
        resp = engine_classify(
            action="create",
            args={},
            session_id="test-session",
            request_origin="user",
        )
        assert resp.data["resolved_ticket_id"] is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineClassify -v`
Expected: ImportError

**Step 3: Write implementation**

```python
"""Ticket engine core — classify | plan | preflight | execute pipeline.

All mutation and policy-enforcement logic lives here. Entrypoints
(ticket_engine_user.py, ticket_engine_agent.py) set request_origin
and delegate to this module.

Subcommand contract: each function returns an EngineResponse with
{state, ticket_id, message, data}.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# --- Response envelope ---


@dataclass
class EngineResponse:
    """Common response envelope for all engine subcommands.

    state: machine state (one of 14 defined states, or "ok" for classify/plan success)
    error_code: machine-readable error code (one of 11 defined codes, or None on success)
    ticket_id: affected ticket ID or None
    message: human-readable description
    data: subcommand-specific output
    """

    state: str
    message: str
    error_code: str | None = None
    ticket_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "state": self.state,
            "ticket_id": self.ticket_id,
            "message": self.message,
            "data": self.data,
        }
        if self.error_code is not None:
            d["error_code"] = self.error_code
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# --- Valid actions and origins ---

VALID_ACTIONS = frozenset({"create", "update", "close", "reopen"})
VALID_ORIGINS = frozenset({"user", "agent"})


# --- classify ---


def engine_classify(
    *,
    action: str,
    args: dict[str, Any],
    session_id: str,
    request_origin: str,
) -> EngineResponse:
    """Classify the caller's intent and validate the action.

    Input action (from first-token routing) is authoritative. Classify validates
    but does not remap. If classify's intent disagrees → intent_mismatch → escalate.

    Returns EngineResponse with state="ok" on success, or error state on failure.
    """
    # Fail closed on unknown origin.
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
        )

    # Validate action.
    if action not in VALID_ACTIONS:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}. Valid: {', '.join(sorted(VALID_ACTIONS))}",
        )

    # Resolve ticket ID from args (for non-create actions).
    resolved_ticket_id = args.get("ticket_id") if action != "create" else None

    # Confidence: high for explicit invocations (first-token routing provides strong signal).
    # This is a provisional default — calibration on labeled corpus required pre-GA.
    confidence = 0.95

    return EngineResponse(
        state="ok",
        message=f"Classified as {action}",
        data={
            "intent": action,
            "confidence": confidence,
            "resolved_ticket_id": resolved_ticket_id,
        },
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineClassify -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_classify with intent validation

Validates action and origin, resolves ticket ID, returns confidence.
EngineResponse envelope for all subcommands.
```

### Checkpoint: After Task 8

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 8
   test_classes: [TestEngineClassify]
   per_class_counts: {TestEngineClassify: 8}
   exports: [EngineResponse, engine_classify, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [EngineResponse, VALID_ACTIONS, VALID_ORIGINS]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Task 9: ticket_engine_core.py — plan Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Pipeline" (lines ~305-312), "Dedup" (lines ~341-357), I/O shapes table (lines ~576-583).

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
from scripts.ticket_engine_core import engine_plan


class TestEnginePlan:
    def test_create_with_all_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": ["handler.py"],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup_fingerprint" in resp.data
        assert resp.data["missing_fields"] == []

    def test_create_missing_required_fields(self, tmp_tickets):
        resp = engine_plan(
            intent="create",
            fields={"title": "No problem section"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert "problem" in resp.data["missing_fields"]

    def test_dedup_detection(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-03-02-auth.md",
            id="T-20260302-01",
            problem="Auth times out.",
            title="Fix auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": [],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.data["duplicate_of"] is not None

    def test_no_dedup_outside_24h(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-02-28-old.md",
            id="T-20260228-01",
            date="2026-02-28",
            problem="Auth times out.",
            title="Old auth bug",
        )
        resp = engine_plan(
            intent="create",
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out.",
                "priority": "high",
                "key_files": [],
            },
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        # Old ticket outside 24h window — no dedup match.
        assert resp.state == "ok"

    def test_non_create_skips_dedup(self, tmp_tickets):
        resp = engine_plan(
            intent="update",
            fields={"ticket_id": "T-20260302-01"},
            session_id="test-session",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        # No dedup for non-create.
        assert resp.data.get("dedup_fingerprint") is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePlan -v`
Expected: ImportError (engine_plan doesn't exist)

**Step 3: Implement engine_plan**

Add to `ticket_engine_core.py`:

```python
from datetime import datetime, timedelta, timezone
from scripts.ticket_dedup import dedup_fingerprint, normalize, target_fingerprint
from scripts.ticket_read import list_tickets
from scripts.ticket_parse import ParsedTicket

# Required fields for create.
_CREATE_REQUIRED = ("title", "problem", "priority")

# Dedup window.
_DEDUP_WINDOW_HOURS = 24


def engine_plan(
    *,
    intent: str,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage: validate fields and check for duplicates (create only).

    For create: validates required fields, computes dedup fingerprint,
    scans for duplicates within 24h window.
    For other intents: passes through (plan is create-specific).
    """
    if intent == "create":
        return _plan_create(fields, session_id, request_origin, tickets_dir)

    # Non-create: plan is a pass-through.
    return EngineResponse(
        state="ok",
        message=f"Plan pass-through for {intent}",
        data={
            "dedup_fingerprint": None,
            "target_fingerprint": None,
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": intent},
        },
    )


def _plan_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Plan stage for create: field validation + dedup."""
    # Check required fields.
    missing = [f for f in _CREATE_REQUIRED if not fields.get(f)]
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields: {', '.join(missing)}",
            error_code="need_fields",
            data={"missing_fields": missing},
        )

    # Compute dedup fingerprint.
    problem_text = fields["problem"]
    key_files = fields.get("key_files", [])
    fp = dedup_fingerprint(problem_text, key_files)

    # Scan for duplicates within 24h window.
    duplicate_of = None
    dup_target_fp = None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=_DEDUP_WINDOW_HOURS)

    existing = list_tickets(tickets_dir)
    for ticket in existing:
        # Check if ticket is within dedup window.
        try:
            ticket_date = datetime.strptime(ticket.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if ticket_date < cutoff:
            continue

        # Compute fingerprint for this ticket's problem text.
        ticket_problem = ticket.sections.get("Problem", "")
        ticket_key_files = []
        # Extract file paths from Key Files section if present.
        key_files_section = ticket.sections.get("Key Files", "")
        if key_files_section:
            # Parse table rows for file paths (first column).
            import re
            for match in re.finditer(r"^\| ([^|]+) \|", key_files_section, re.MULTILINE):
                cell = match.group(1).strip()
                if cell and cell != "File" and not cell.startswith("-"):
                    ticket_key_files.append(cell)

        existing_fp = dedup_fingerprint(ticket_problem, ticket_key_files)
        if existing_fp == fp:
            duplicate_of = ticket.id
            # Compute target fingerprint for the duplicate.
            dup_target_fp = target_fingerprint(Path(ticket.path))
            break

    if duplicate_of:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Potential duplicate of {duplicate_of}",
            ticket_id=duplicate_of,
            error_code="duplicate_candidate",
            data={
                "dedup_fingerprint": fp,
                "target_fingerprint": dup_target_fp,
                "duplicate_of": duplicate_of,
                "missing_fields": [],
                "action_plan": {"intent": "create", "duplicate_candidate": True},
            },
        )

    return EngineResponse(
        state="ok",
        message="Plan complete, no duplicates found",
        data={
            "dedup_fingerprint": fp,
            "target_fingerprint": None,  # No target ticket exists yet.
            "duplicate_of": None,
            "missing_fields": [],
            "action_plan": {"intent": "create"},
        },
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePlan -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_plan with dedup detection

Field validation for create, 24h dedup window, fingerprint generation.
Non-create intents pass through (plan is create-specific).
```

### Checkpoint: After Task 9

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 9
   test_classes: [TestEngineClassify, TestEnginePlan]
   per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5}
   exports: [EngineResponse, engine_classify, engine_plan, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [EngineResponse, VALID_ACTIONS, VALID_ORIGINS]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Task 10: ticket_engine_core.py — preflight Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Autonomy Enforcement" (lines ~409-451), "Preflight" description (lines ~314-324), I/O shapes (line ~582). Preflight is the single enforcement point for all mutating operations.

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
from scripts.ticket_engine_core import engine_preflight


class TestEnginePreflight:
    def test_user_create_passes(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert len(resp.data["checks_passed"]) > 0

    def test_unknown_origin_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="unknown",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"

    def test_low_confidence_rejected(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "confidence" in resp.message.lower()

    def test_agent_hard_blocked_phase1(self, tmp_tickets):
        """Phase 1 strict fail-closed: all agent mutations are hard-blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc",
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "phase 1" in resp.message.lower() or "hard-blocked" in resp.message.lower()

    def test_agent_reopen_hard_blocked_phase1(self, tmp_tickets):
        """Agent reopen also hard-blocked (not just user-only check)."""
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="reopen",
            session_id="test-session",
            request_origin="agent",
            classify_confidence=0.95,
            classify_intent="reopen",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"

    def test_non_create_without_ticket_id_rejected(self, tmp_tickets):
        """Non-create actions require ticket_id."""
        resp = engine_preflight(
            ticket_id=None,
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"

    def test_intent_mismatch_escalates(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",  # Mismatch!
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert "intent_mismatch" in resp.message.lower() or "mismatch" in resp.message.lower()

    def test_stale_target_fingerprint(self, tmp_tickets):
        from tests.conftest import make_ticket

        path = make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_preflight(
            ticket_id="T-20260302-01",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint="stale-fingerprint",
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert "stale" in resp.message.lower() or "fingerprint" in resp.message.lower()

    def test_update_ticket_not_found(self, tmp_tickets):
        resp = engine_preflight(
            ticket_id="T-99999999-99",
            action="update",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="update",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"

    def test_close_with_open_blockers(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "dependency_blocked"

    def test_close_with_open_blockers_override(self, tmp_tickets):
        """dependency_override=True allows closing with open blockers."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "blocker.md", id="T-20260302-01", status="open")
        make_ticket(
            tmp_tickets,
            "target.md",
            id="T-20260302-02",
            blocked_by=["T-20260302-01"],
        )
        resp = engine_preflight(
            ticket_id="T-20260302-02",
            action="close",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="close",
            dedup_fingerprint=None,
            target_fingerprint=None,
            dependency_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dependencies_overridden" in resp.data["checks_passed"]

    def test_dedup_blocks_without_override(self, tmp_tickets):
        """Preflight blocks create when duplicate detected and no override."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "duplicate_candidate"
        assert resp.error_code == "duplicate_candidate"

    def test_dedup_passes_with_override(self, tmp_tickets):
        """Preflight allows create when duplicate detected but override=True."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.95,
            classify_intent="create",
            dedup_fingerprint="abc123",
            target_fingerprint=None,
            duplicate_of="T-20260302-01",
            dedup_override=True,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok"
        assert "dedup" in resp.data["checks_passed"]

    def test_confidence_gate_no_policy_blocked_code(self, tmp_tickets):
        """Confidence gate returns error_code=None, not policy_blocked."""
        resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="test-session",
            request_origin="user",
            classify_confidence=0.1,
            classify_intent="create",
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "preflight_failed"
        assert resp.error_code is None
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePreflight -v`
Expected: ImportError

**Step 3: Implement engine_preflight**

Add to `ticket_engine_core.py`:

```python
# Confidence thresholds (provisional — calibrate pre-GA).
_T_BASE = 0.5
_ORIGIN_MODIFIER = {"user": 0.0, "agent": 0.15}

# Terminal statuses for dependency resolution.
_TERMINAL_STATUSES = frozenset({"done", "wontfix"})


def _read_autonomy_mode(tickets_dir: Path) -> str:
    """Read autonomy mode from .claude/ticket.local.md.

    Returns 'suggest' as default if file missing or malformed.
    """
    # Walk up from tickets_dir to find project root.
    project_root = tickets_dir
    while project_root != project_root.parent:
        if (project_root / ".claude").is_dir():
            break
        project_root = project_root.parent

    config_path = project_root / ".claude" / "ticket.local.md"
    if not config_path.is_file():
        return "suggest"

    try:
        import yaml

        text = config_path.read_text(encoding="utf-8")
        # Parse YAML frontmatter (--- delimited).
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1])
                if isinstance(data, dict):
                    mode = data.get("autonomy_mode", "suggest")
                    if mode in ("suggest", "auto_audit", "auto_silent"):
                        return mode
    except Exception:
        pass

    return "suggest"


def engine_preflight(
    *,
    ticket_id: str | None,
    action: str,
    session_id: str,
    request_origin: str,
    classify_confidence: float,
    classify_intent: str,
    dedup_fingerprint: str | None,
    target_fingerprint: str | None,
    duplicate_of: str | None = None,
    dedup_override: bool = False,
    dependency_override: bool = False,
    tickets_dir: Path,
) -> EngineResponse:
    """Preflight: single enforcement point for all mutating operations.

    Checks in order: origin, confidence, intent match, agent policy,
    ticket existence, dependency integrity, TOCTOU fingerprint.
    """
    checks_passed: list[str] = []
    checks_failed: list[dict[str, str]] = []

    # --- Origin check ---
    if request_origin not in VALID_ORIGINS:
        return EngineResponse(
            state="escalate",
            message=f"Cannot determine caller identity: request_origin={request_origin!r}",
            error_code="origin_mismatch",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "origin", "reason": "unknown origin"}]},
        )
    checks_passed.append("origin")

    # --- Confidence gate ---
    modifier = _ORIGIN_MODIFIER.get(request_origin, 0.0)
    threshold = _T_BASE + modifier
    if classify_confidence < threshold:
        # error_code=None: the 11-code table has no confidence-specific code.
        # policy_blocked is reserved for autonomy enforcement (design doc line 593).
        # A confidence-specific code may be added post-v1.0.
        return EngineResponse(
            state="preflight_failed",
            message=f"Low confidence classification: {classify_confidence:.2f} (threshold: {threshold:.2f}). Rephrase or specify the operation.",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "confidence", "reason": f"below threshold {threshold}"}]},
        )
    checks_passed.append("confidence")

    # --- Intent match ---
    if classify_intent != action:
        return EngineResponse(
            state="escalate",
            message=f"Intent_mismatch: classify returned {classify_intent!r} but action is {action!r}",
            error_code="intent_mismatch",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "intent_match", "reason": "mismatch"}]},
        )
    checks_passed.append("intent_match")

    # --- Agent policy: Phase 1 strict fail-closed ---
    # All agent mutations are hard-blocked in Phase 1.
    # The PreToolUse hook (Phase 2) is required for hook_injected and session_id injection.
    if request_origin == "agent":
        return EngineResponse(
            state="policy_blocked",
            message="Agent mutations are hard-blocked in Phase 1. The PreToolUse hook (Phase 2) is required for legitimate agent invocations.",
            error_code="policy_blocked",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "agent_phase1_block", "reason": "Phase 1 fail-closed policy"}]},
        )
    checks_passed.append("autonomy_policy")

    # --- Dedup enforcement (create action) ---
    # Plan stage returns duplicate_of when a match is found. Preflight enforces
    # the dedup decision: if a duplicate was detected and the caller hasn't
    # overridden, block the operation. Without this check, dedup is advisory only.
    if action == "create" and duplicate_of and not dedup_override:
        return EngineResponse(
            state="duplicate_candidate",
            message=f"Duplicate of {duplicate_of} detected in plan stage. Pass dedup_override=True to proceed.",
            error_code="duplicate_candidate",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "dedup", "reason": f"duplicate_of={duplicate_of}"}]},
        )
    if action == "create":
        checks_passed.append("dedup")

    # --- Ticket ID required for non-create ---
    if action != "create" and not ticket_id:
        return EngineResponse(
            state="need_fields",
            message=f"ticket_id required for {action}",
            error_code="need_fields",
            data={"checks_passed": checks_passed, "checks_failed": [{"check": "ticket_id", "reason": "missing for non-create"}]},
        )

    # --- Ticket existence check (non-create) ---
    if action != "create" and ticket_id:
        from scripts.ticket_read import find_ticket_by_id

        ticket = find_ticket_by_id(tickets_dir, ticket_id)
        if ticket is None:
            return EngineResponse(
                state="not_found",
                message=f"No ticket found matching {ticket_id}",
                ticket_id=ticket_id,
                error_code="not_found",
                data={"checks_passed": checks_passed, "checks_failed": [{"check": "ticket_exists", "reason": "not found"}]},
            )
        checks_passed.append("ticket_exists")

        # --- Dependency check (close action) ---
        if action == "close" and ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                if dependency_override:
                    checks_passed.append("dependencies_overridden")
                else:
                    return EngineResponse(
                        state="dependency_blocked",
                        message=f"Ticket has open blockers: {unresolved}. Resolve or pass dependency_override: true.",
                        ticket_id=ticket_id,
                        error_code="dependency_blocked",
                        data={"checks_passed": checks_passed, "checks_failed": [{"check": "dependencies", "reason": f"unresolved: {unresolved}"}]},
                    )
            else:
                checks_passed.append("dependencies")

        # --- TOCTOU fingerprint check ---
        if target_fingerprint is not None:
            from scripts.ticket_dedup import target_fingerprint as compute_fp

            current_fp = compute_fp(Path(ticket.path))
            if current_fp != target_fingerprint:
                return EngineResponse(
                    state="preflight_failed",
                    message="Stale fingerprint — ticket was modified since read. Re-run to get a fresh plan.",
                    ticket_id=ticket_id,
                    error_code="stale_plan",
                    data={"checks_passed": checks_passed, "checks_failed": [{"check": "target_fingerprint", "reason": "stale"}]},
                )
            checks_passed.append("target_fingerprint")

    return EngineResponse(
        state="ok",
        message="All preflight checks passed",
        data={"checks_passed": checks_passed, "checks_failed": checks_failed},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEnginePreflight -v`
Expected: All tests PASS

**Step 5: Commit**

```
feat(ticket): add engine_preflight with autonomy enforcement

Confidence gate, intent match, origin validation, autonomy policy,
TOCTOU fingerprint, dependency checks, ticket existence.
```

### Checkpoint: After Task 10

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 10
   test_classes: [TestEngineClassify, TestEnginePlan, TestEnginePreflight]
   per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5, TestEnginePreflight: 15}
   exports: [EngineResponse, engine_classify, engine_plan, engine_preflight, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [EngineResponse, VALID_ACTIONS, VALID_ORIGINS, _TERMINAL_STATUSES]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Task 11: ticket_engine_core.py — execute Subcommand

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

**Context:** Read design doc: "Execute" in pipeline (lines ~305-312), I/O shapes (line ~583), "Status Transitions" (lines ~607-631), "Audit Trail" (lines ~491-527).

Task 11 is decomposed into 6 vertical TDD slices (11.1-11.6). Each slice adds one function and its tests. Slices 1, 3, and 6 have full checkpoints; slices 2, 4, and 5 have commit-only snapshots.

---

## Task 11.1: Execute Subcommand — Shared Helpers

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice adds the shared constants, transition table, and helper functions that all execute operations depend on: `_CANONICAL_FIELD_ORDER`, `_VALID_TRANSITIONS`, `_TRANSITION_PRECONDITIONS`, `_render_canonical_frontmatter`, `_is_valid_transition`, and `_check_transition_preconditions`.

**Step 1: Write failing tests**

Add to `tests/test_engine.py`. These tests exercise the shared helpers via the execute interface — transition validation and canonical rendering are tested through the update/close paths that will be added in subsequent slices. For now, add tests that validate the helpers directly:

```python
from scripts.ticket_engine_core import engine_execute


class TestEngineExecute:
    def test_invalid_transition_terminal_via_update(self, tmp_tickets):
        """done → in_progress via update is invalid (must reopen first)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "reopen" in resp.message.lower()

    def test_invalid_transition_wontfix_via_update(self, tmp_tickets):
        """wontfix → open via update is invalid (must reopen)."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wontfix.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "open"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_transition_to_blocked_requires_blocked_by(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open", blocked_by=[])
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "blocked"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "blocked_by" in resp.message.lower()

    def test_agent_override_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01")
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={"title": "Test", "problem": "Test", "priority": "medium"},
            session_id="test-session",
            request_origin="agent",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "policy_blocked"
        assert "agent" in resp.message.lower() or "override" in resp.message.lower()

    def test_error_code_on_all_error_returns(self, tmp_tickets):
        """All error EngineResponse returns include error_code."""
        # Test update need_fields.
        resp = engine_execute(
            action="update",
            ticket_id=None,
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "need_fields"
        assert resp.error_code == "need_fields"

        # Test update not_found.
        resp = engine_execute(
            action="update",
            ticket_id="T-99999999-99",
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "not_found"
        assert resp.error_code == "not_found"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: ImportError (engine_execute doesn't exist)

**Step 3: Implement shared helpers and engine_execute stub**

Add to `ticket_engine_core.py`:

```python
from datetime import date as Date
from scripts.ticket_id import allocate_id, build_filename
from scripts.ticket_render import render_ticket
from scripts.ticket_parse import parse_ticket as _parse_ticket, extract_fenced_yaml, parse_yaml_block

# Canonical field order for YAML frontmatter rendering.
# Known fields are written in this order. Unknown keys are preserved at the end
# (forward-compatible: "ignored" means "not processed", not "destroyed on rewrite").
_CANONICAL_FIELD_ORDER = [
    "id", "date", "status", "priority", "effort",
    "source", "tags", "blocked_by", "blocks",
    "contract_version",
]


def _render_canonical_frontmatter(data: dict[str, Any]) -> str:
    """Render YAML frontmatter with controlled field order and quoting.

    Unlike yaml.dump(), this function:
    - Preserves field order (canonical, not alphabetical)
    - Always quotes date strings (prevents PyYAML date coercion)
    - Only emits known fields (drops unknown keys)
    - Uses consistent list formatting (flow style for simple lists)
    """
    lines: list[str] = []
    for key in _CANONICAL_FIELD_ORDER:
        if key not in data:
            continue
        value = data[key]
        # None guard: skip fields explicitly set to None rather than
        # rendering "key: None" (Python str) which YAML reads as string "None".
        if value is None:
            continue
        if key == "date":
            # Always quote dates to prevent PyYAML auto-conversion.
            lines.append(f'{key}: "{value}"')
        elif key == "source" and isinstance(value, dict):
            lines.append("source:")
            for sk, sv in value.items():
                lines.append(f'  {sk}: "{sv}"' if isinstance(sv, str) else f"  {sk}: {sv}")
        elif key == "contract_version":
            lines.append(f'{key}: "{value}"')
        elif isinstance(value, list):
            # Render lists as YAML flow sequences with proper quoting.
            # Python repr uses single quotes; YAML requires brackets with no quotes
            # for simple strings, or double quotes for strings with special chars.
            items = ", ".join(str(item) for item in value)
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str):
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    # Preserve unknown keys (forward-compat: "ignored" means "not processed",
    # not "destroyed on rewrite"). Appended after canonical fields.
    known_keys = set(_CANONICAL_FIELD_ORDER) | {"defer"}
    for key in data:
        if key not in known_keys:
            value = data[key]
            if value is not None:
                lines.append(f"{key}: {value}")
    # Include defer if present (optional field, not in canonical order).
    if "defer" in data and data["defer"] is not None:
        defer = data["defer"]
        lines.append("defer:")
        for dk, dv in defer.items():
            if isinstance(dv, bool):
                lines.append(f"  {dk}: {'true' if dv else 'false'}")
            else:
                lines.append(f'  {dk}: "{dv}"' if isinstance(dv, str) else f"  {dk}: {dv}")
    return "\n".join(lines) + "\n"

# Valid status transitions for update action (from → set of valid to statuses).
# done/wontfix are terminal — only reopen (separate action) can transition out.
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "blocked", "wontfix"},
    "in_progress": {"open", "blocked", "done", "wontfix"},
    "blocked": {"open", "in_progress", "wontfix"},
    "done": set(),  # Terminal — reopen action required.
    "wontfix": set(),  # Terminal — reopen action required.
}

# Transitions that require preconditions.
_TRANSITION_PRECONDITIONS: dict[tuple[str, str], str] = {
    # → blocked requires blocked_by non-empty.
    ("open", "blocked"): "blocked_by_required",
    ("in_progress", "blocked"): "blocked_by_required",
    # → done requires acceptance criteria present.
    ("in_progress", "done"): "acceptance_criteria_required",
    # blocked → open requires all blocked_by resolved.
    ("blocked", "open"): "blockers_resolved_required",
    ("blocked", "in_progress"): "blockers_resolved_required",
}


def _is_valid_transition(current: str, target: str, action: str) -> bool:
    """Check if a status transition is valid per the contract."""
    # Close can set done or wontfix from any non-terminal status.
    # Terminal statuses (done/wontfix) cannot be closed again — must reopen first.
    if action == "close":
        if current in _TERMINAL_STATUSES:
            return False
        return target in ("done", "wontfix")
    # Reopen: done/wontfix → open.
    if action == "reopen":
        return current in ("done", "wontfix") and target == "open"
    # Update: follow transition table (terminal statuses have empty set).
    valid = _VALID_TRANSITIONS.get(current, set())
    return target in valid


def _check_transition_preconditions(
    current: str, target: str, ticket: Any, tickets_dir: Path,
    fields: dict[str, Any] | None = None,
) -> str | None:
    """Check transition preconditions. Returns error message or None if OK.

    Uses merged state: fields (pending update) take precedence over ticket
    (pre-update) for fields that are being changed in this operation.
    """
    key = (current, target)
    precondition = _TRANSITION_PRECONDITIONS.get(key)
    if precondition is None:
        return None

    _fields = fields or {}

    if precondition == "blocked_by_required":
        # Use merged blocked_by: pending fields override pre-update ticket state.
        blocked_by = _fields.get("blocked_by", ticket.blocked_by)
        if not blocked_by:
            return f"Transition to 'blocked' requires non-empty blocked_by"
        return None

    if precondition == "acceptance_criteria_required":
        ac = ticket.sections.get("Acceptance Criteria", "")
        if not ac.strip():
            return f"Transition to 'done' requires acceptance criteria section"
        return None

    if precondition == "blockers_resolved_required":
        if ticket.blocked_by:
            from scripts.ticket_read import list_tickets as _list_tickets

            all_tickets = _list_tickets(tickets_dir)
            ticket_map = {t.id: t for t in all_tickets}
            unresolved = [
                bid for bid in ticket.blocked_by
                if bid in ticket_map and ticket_map[bid].status not in _TERMINAL_STATUSES
            ]
            if unresolved:
                return f"Blockers still open: {unresolved}. Resolve or use dependency_override."
        return None

    return None


def engine_execute(
    *,
    action: str,
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    dedup_override: bool,
    dependency_override: bool,
    tickets_dir: Path,
) -> EngineResponse:
    """Execute the mutation: create, update, close, or reopen.

    Assumes preflight has already passed. Writes ticket files and audit trail.
    """
    # Agent callers cannot use overrides.
    if request_origin == "agent" and (dedup_override or dependency_override):
        return EngineResponse(
            state="policy_blocked",
            message="Agent callers cannot use dedup_override or dependency_override",
            error_code="policy_blocked",
        )

    if action == "create":
        return _execute_create(fields, session_id, request_origin, tickets_dir)
    elif action == "update":
        return _execute_update(ticket_id, fields, session_id, request_origin, tickets_dir)
    elif action == "close":
        return _execute_close(ticket_id, fields, session_id, request_origin, tickets_dir)
    elif action == "reopen":
        return _execute_reopen(ticket_id, fields, session_id, request_origin, tickets_dir)
    else:
        return EngineResponse(
            state="escalate",
            message=f"Unknown action: {action!r}",
            error_code="intent_mismatch",
        )


# --- Stubs for execute sub-functions (implemented in subsequent slices) ---
# These stubs allow the dispatcher and shared-helper tests to run.
# Each stub will be replaced by its full implementation in slices 11.2-11.5.


def _execute_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Create a new ticket file with all required contract fields.

    STUB — full implementation in Task 11.2.
    """
    raise NotImplementedError("_execute_create not yet implemented (Task 11.2)")


def _execute_update(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Update an existing ticket's frontmatter fields.

    STUB — full implementation in Task 11.3.
    """
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for update", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    # Check status transition validity (shared helper from this slice).
    new_status = fields.get("status")
    if new_status and new_status != ticket.status:
        if not _is_valid_transition(ticket.status, new_status, "update"):
            return EngineResponse(
                state="invalid_transition",
                message=f"Cannot transition from {ticket.status} to {new_status} via update"
                + (" (use reopen action)" if ticket.status in _TERMINAL_STATUSES else ""),
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )
        # Check transition preconditions (pass fields for merged state).
        precondition_error = _check_transition_preconditions(
            ticket.status, new_status, ticket, tickets_dir, fields=fields,
        )
        if precondition_error:
            return EngineResponse(
                state="invalid_transition",
                message=precondition_error,
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )

    raise NotImplementedError("_execute_update file write not yet implemented (Task 11.3)")


def _execute_close(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Close a ticket (set status to done or wontfix, optionally archive).

    STUB — full implementation in Task 11.4.
    """
    raise NotImplementedError("_execute_close not yet implemented (Task 11.4)")


def _execute_reopen(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Reopen a done/wontfix ticket.

    STUB — full implementation in Task 11.5.
    """
    raise NotImplementedError("_execute_reopen not yet implemented (Task 11.5)")
```

Note: The `_execute_update` stub includes transition validation logic (using the shared helpers from this slice) so the transition tests can pass, while raising `NotImplementedError` for the file-write path. The other stubs are pure `NotImplementedError` — their tests are added in subsequent slices.

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All 5 tests PASS (transition tests use shared helpers, agent override uses dispatcher, error codes use update stub)

**Step 5: Commit**

```
feat(ticket): add execute shared helpers — transition table, canonical renderer, preconditions

_render_canonical_frontmatter, _is_valid_transition, _check_transition_preconditions,
_CANONICAL_FIELD_ORDER, _VALID_TRANSITIONS, _TRANSITION_PRECONDITIONS.
engine_execute dispatcher with stubs for create/update/close/reopen.
```

### Checkpoint: After Task 11.1

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 11.1
   test_classes: [TestEngineClassify, TestEnginePlan, TestEnginePreflight, TestEngineExecute]
   per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5, TestEnginePreflight: 15, TestEngineExecute: 5}
   exports: [EngineResponse, engine_classify, engine_plan, engine_preflight, engine_execute, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [engine_execute, _execute_create, allocate_id, build_filename, render_ticket]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Task 11.2: Execute Subcommand — Execute Create

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice replaces the `_execute_create` stub with the full implementation and adds create-specific tests.

**Step 1: Write failing tests**

Add to `TestEngineExecute` class in `tests/test_engine.py`:

```python
    def test_create_ticket(self, tmp_tickets):
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Fix auth bug",
                "problem": "Auth times out for large payloads.",
                "priority": "high",
                "effort": "S",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["auth"],
                "approach": "Make timeout configurable.",
                "acceptance_criteria": ["Timeout configurable", "Default remains 30s"],
                "verification": "uv run pytest tests/test_auth.py",
                "key_files": [{"file": "handler.py:45", "role": "Timeout", "look_for": "hardcoded"}],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        assert resp.ticket_id is not None
        assert resp.ticket_id.startswith("T-")
        assert resp.data["ticket_path"] is not None
        # Verify file was created.
        ticket_path = Path(resp.data["ticket_path"])
        assert ticket_path.exists()
        content = ticket_path.read_text(encoding="utf-8")
        assert "Fix auth bug" in content
        assert "## Problem" in content
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute::test_create_ticket -v`
Expected: NotImplementedError from stub

**Step 3: Replace _execute_create stub with full implementation**

Replace the `_execute_create` stub in `ticket_engine_core.py` with:

```python
def _execute_create(
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Create a new ticket file with all required contract fields."""
    # Validate required create fields.
    missing = []
    if not fields.get("title"):
        missing.append("title")
    if not fields.get("problem"):
        missing.append("problem")
    if missing:
        return EngineResponse(
            state="need_fields",
            message=f"Missing required fields for create: {missing}",
            error_code="need_fields",
        )

    # Ensure directory exists.
    tickets_dir.mkdir(parents=True, exist_ok=True)

    today = Date.today()
    ticket_id = allocate_id(tickets_dir, today)
    title = fields.get("title", "Untitled")
    filename = build_filename(ticket_id, title)

    source = fields.get("source", {"type": "ad-hoc", "ref": "", "session": session_id})
    if "session" not in source:
        source["session"] = session_id

    content = render_ticket(
        id=ticket_id,
        title=title,
        date=today.isoformat(),
        status="open",
        priority=fields.get("priority", "medium"),
        effort=fields.get("effort", ""),
        source=source,
        tags=fields.get("tags", []),
        problem=fields.get("problem", ""),
        approach=fields.get("approach", ""),
        acceptance_criteria=fields.get("acceptance_criteria"),
        verification=fields.get("verification", ""),
        key_files=fields.get("key_files"),
        context=fields.get("context", ""),
        prior_investigation=fields.get("prior_investigation", ""),
        decisions_made=fields.get("decisions_made", ""),
        related=fields.get("related", ""),
    )

    ticket_path = tickets_dir / filename
    ticket_path.write_text(content, encoding="utf-8")

    return EngineResponse(
        state="ok_create",
        message=f"Created {ticket_id} at {ticket_path}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": None},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All tests PASS (including prior tests from 11.1)

**Step 5: Commit**

```
feat(ticket): implement _execute_create — ticket file creation with ID allocation

Replaces stub. Uses allocate_id, build_filename, render_ticket (from Module 2/3, already implemented).
```

### Commit Point: After Task 11.2

Commit all changes. No full checkpoint required — the next full checkpoint at Task 11.3 will verify.

---

## Task 11.3: Execute Subcommand — Execute Update

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice replaces the `_execute_update` stub with the full implementation (including file write via `_render_canonical_frontmatter`) and adds update-specific tests.

**Step 1: Write failing tests**

Add to `TestEngineExecute` class in `tests/test_engine.py`:

```python
    def test_update_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        # Verify status changed.
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: in_progress" in content
        # Verify date is still quoted (canonical renderer, not yaml.dump).
        assert 'date: "2026-03-02"' in content
        # Verify unknown fields are NOT written back.
        assert "extra_yaml" not in content or "```" in content  # Only in YAML block context

    def test_update_preserves_field_order(self, tmp_tickets):
        """Canonical renderer emits fields in defined order, not alphabetical."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"priority": "critical"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        # id should appear before status in the YAML block.
        id_pos = content.index("id: T-20260302-01")
        status_pos = content.index("status: open")
        assert id_pos < status_pos

    def test_update_preserves_full_field_order(self, tmp_tickets):
        """Verify all canonical field positions, not just id < status."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open",
                     priority="medium", effort="S")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        id_pos = content.index("id:")
        status_pos = content.index("status:")
        priority_pos = content.index("priority:")
        effort_pos = content.index("effort:")
        tags_pos = content.index("tags:")
        assert id_pos < status_pos < priority_pos < effort_pos < tags_pos

    def test_canonical_renderer_none_skipped(self, tmp_tickets):
        """Fields set to None are omitted, not rendered as 'key: None'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"effort": None},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "effort: None" not in content

    def test_canonical_renderer_list_format(self, tmp_tickets):
        """Lists render as YAML flow sequences, not Python repr."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"tags": ["bug", "urgent"]},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        # Should be YAML flow format, not Python repr with single quotes.
        assert "tags: [bug, urgent]" in content
        assert "['bug'" not in content
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute::test_update_ticket -v`
Expected: NotImplementedError from update stub (file write path)

**Step 3: Replace _execute_update stub with full implementation**

Replace the `_execute_update` stub in `ticket_engine_core.py` with:

```python
def _execute_update(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Update an existing ticket's frontmatter fields."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for update", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")

    # Check status transition validity.
    new_status = fields.get("status")
    if new_status and new_status != ticket.status:
        if not _is_valid_transition(ticket.status, new_status, "update"):
            return EngineResponse(
                state="invalid_transition",
                message=f"Cannot transition from {ticket.status} to {new_status} via update"
                + (" (use reopen action)" if ticket.status in _TERMINAL_STATUSES else ""),
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )
        # Check transition preconditions (pass fields for merged state).
        precondition_error = _check_transition_preconditions(
            ticket.status, new_status, ticket, tickets_dir, fields=fields,
        )
        if precondition_error:
            return EngineResponse(
                state="invalid_transition",
                message=precondition_error,
                ticket_id=ticket_id,
                error_code="invalid_transition",
            )

    # Update frontmatter fields.
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    changes: dict[str, list] = {"frontmatter": {}, "sections_changed": []}
    for key, value in fields.items():
        if key in data and data[key] != value:
            changes["frontmatter"][key] = [data[key], value]
        data[key] = value

    # Re-render using canonical frontmatter renderer (not yaml.dump —
    # yaml.dump reorders keys, changes quoting, and coerces dates).
    new_yaml = _render_canonical_frontmatter(data)
    import re

    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_update",
        message=f"Updated {ticket_id}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All tests PASS (including all prior tests from 11.1 and 11.2)

**Step 5: Commit**

```
feat(ticket): implement _execute_update — frontmatter field updates with canonical renderer

Replaces stub. Uses _render_canonical_frontmatter for field-order-preserving writes.
extract_fenced_yaml, parse_yaml_block (from Module 2, already implemented).
```

### Checkpoint: After Task 11.3

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 11.3
   test_classes: [TestEngineClassify, TestEnginePlan, TestEnginePreflight, TestEngineExecute]
   per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5, TestEnginePreflight: 15, TestEngineExecute: 11}
   exports: [EngineResponse, engine_classify, engine_plan, engine_preflight, engine_execute, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [engine_execute, _execute_close, _is_valid_transition, _check_transition_preconditions, _render_canonical_frontmatter]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Task 11.4: Execute Subcommand — Execute Close

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice replaces the `_execute_close` stub with the full implementation and adds close-specific tests.

**Step 1: Write failing tests**

Add to `TestEngineExecute` class in `tests/test_engine.py`:

```python
    def test_close_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_archive(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done", "archive": True},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close_archived"
        # Verify file moved to closed-tickets/.
        assert not (tmp_tickets / "2026-03-02-test.md").exists()
        assert (tmp_tickets / "closed-tickets" / "2026-03-02-test.md").exists()

    def test_close_from_open_succeeds(self, tmp_tickets):
        """Close directly validates with action='close', not 'update'."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

    def test_close_with_invalid_resolution_rejected(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_close_terminal_ticket_rejected(self, tmp_tickets):
        """Closing an already-done ticket is invalid — must reopen first."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-done.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert resp.error_code == "invalid_transition"

    def test_close_wontfix_to_done_rejected(self, tmp_tickets):
        """wontfix → done via close is invalid — terminal state."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-wf.md", id="T-20260302-01", status="wontfix")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"

    def test_close_checks_acceptance_criteria(self, tmp_tickets):
        """Close to 'done' from in_progress requires acceptance criteria."""
        from tests.conftest import make_ticket

        # Create ticket with empty acceptance criteria section.
        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="in_progress")
        resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "invalid_transition"
        assert "acceptance" in resp.message.lower() or "criteria" in resp.message.lower()
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute::test_close_ticket -v`
Expected: NotImplementedError from stub

**Step 3: Replace _execute_close stub with full implementation**

Replace the `_execute_close` stub in `ticket_engine_core.py` with:

```python
def _execute_close(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Close a ticket (set status to done or wontfix, optionally archive).

    Unlike update, close validates transitions with action='close', which allows
    done/wontfix from any non-terminal status. This avoids the delegation-to-update
    bug where close-specific transition logic becomes dead code.
    """
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for close", error_code="need_fields")

    resolution = fields.get("resolution", "done")
    archive = fields.get("archive", False)

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    # Validate transition with action="close" (not "update").
    if not _is_valid_transition(ticket.status, resolution, "close"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot close with resolution {resolution!r} (must be 'done' or 'wontfix')"
            + (f" from terminal status {ticket.status!r}" if ticket.status in _TERMINAL_STATUSES else ""),
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Check transition preconditions (e.g., acceptance criteria for → done).
    precondition_error = _check_transition_preconditions(
        ticket.status, resolution, ticket, tickets_dir, fields=fields,
    )
    if precondition_error:
        return EngineResponse(
            state="invalid_transition",
            message=precondition_error,
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change using the canonical frontmatter renderer.
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = resolution
    new_yaml = _render_canonical_frontmatter(data)
    import re

    new_text = re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    ticket_path.write_text(new_text, encoding="utf-8")

    changes = {"frontmatter": {"status": [old_status, resolution]}}

    # Archive if requested.
    if archive:
        closed_dir = tickets_dir / "closed-tickets"
        closed_dir.mkdir(exist_ok=True)
        dst = closed_dir / ticket_path.name
        ticket_path.rename(dst)
        return EngineResponse(
            state="ok_close_archived",
            message=f"Closed and archived {ticket_id} to closed-tickets/",
            ticket_id=ticket_id,
            data={"ticket_path": str(dst), "changes": changes},
        )

    return EngineResponse(
        state="ok_close",
        message=f"Closed {ticket_id} (status: {resolution})",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": changes},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All tests PASS (including all prior tests from 11.1, 11.2, 11.3)

**Step 5: Commit**

```
feat(ticket): implement _execute_close — status transition, archive, precondition checks

Replaces stub. Validates transitions with action='close' (not 'update').
Archiving to closed-tickets/ subdirectory. Acceptance criteria check for → done.
```

### Commit Point: After Task 11.4

Commit all changes. No full checkpoint required — the next full checkpoint at Task 11.6 will verify.

---

## Task 11.5: Execute Subcommand — Execute Reopen

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice replaces the `_execute_reopen` stub with the full implementation and adds reopen-specific tests.

**Step 1: Write failing tests**

Add to `TestEngineExecute` class in `tests/test_engine.py`:

```python
    def test_reopen_ticket(self, tmp_tickets):
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="done")
        resp = engine_execute(
            action="reopen",
            ticket_id="T-20260302-01",
            fields={"reopen_reason": "Bug reoccurred after merge"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"
        content = (tmp_tickets / "2026-03-02-test.md").read_text(encoding="utf-8")
        assert "status: open" in content
        assert "Reopen History" in content
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute::test_reopen_ticket -v`
Expected: NotImplementedError from stub

**Step 3: Replace _execute_reopen stub with full implementation**

Replace the `_execute_reopen` stub in `ticket_engine_core.py` with:

```python
def _execute_reopen(
    ticket_id: str | None,
    fields: dict[str, Any],
    session_id: str,
    request_origin: str,
    tickets_dir: Path,
) -> EngineResponse:
    """Reopen a done/wontfix ticket."""
    if not ticket_id:
        return EngineResponse(state="need_fields", message="ticket_id required for reopen", error_code="need_fields")

    reopen_reason = fields.get("reopen_reason", "")
    if not reopen_reason:
        return EngineResponse(state="need_fields", message="reopen_reason required for reopen", error_code="need_fields")

    from scripts.ticket_read import find_ticket_by_id

    ticket = find_ticket_by_id(tickets_dir, ticket_id)
    if ticket is None:
        return EngineResponse(state="not_found", message=f"No ticket matching {ticket_id}", ticket_id=ticket_id, error_code="not_found")

    if not _is_valid_transition(ticket.status, "open", "reopen"):
        return EngineResponse(
            state="invalid_transition",
            message=f"Cannot reopen ticket with status {ticket.status} (must be done or wontfix)",
            ticket_id=ticket_id,
            error_code="invalid_transition",
        )

    # Write status change directly (not via _execute_update, which would
    # reject done→open since _VALID_TRANSITIONS["done"] is empty for update).
    ticket_path = Path(ticket.path)
    text = ticket_path.read_text(encoding="utf-8")
    yaml_text = extract_fenced_yaml(text)
    if yaml_text is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    data = parse_yaml_block(yaml_text)
    if data is None:
        return EngineResponse(state="escalate", message="Cannot parse ticket YAML", ticket_id=ticket_id, error_code="parse_error")

    old_status = data.get("status", "")
    data["status"] = "open"
    new_yaml = _render_canonical_frontmatter(data)
    import re as _re

    new_text = _re.sub(
        r"^```ya?ml\s*\n.*?^```",
        f"```yaml\n{new_yaml}```",
        text,
        count=1,
        flags=_re.MULTILINE | _re.DOTALL,
    )

    # Append to Reopen History section (newest-last).
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    reopen_entry = f"\n\n## Reopen History\n- **{now}**: {reopen_reason} (by {request_origin})"

    if "## Reopen History" in new_text:
        rh_match = _re.search(r"## Reopen History\n", new_text)
        if rh_match:
            next_heading = _re.search(r"\n## ", new_text[rh_match.end():])
            if next_heading:
                insert_pos = rh_match.end() + next_heading.start()
            else:
                insert_pos = len(new_text)
            entry = f"- **{now}**: {reopen_reason} (by {request_origin})\n"
            new_text = new_text[:insert_pos].rstrip() + "\n" + entry + new_text[insert_pos:]
    else:
        new_text += reopen_entry

    ticket_path.write_text(new_text, encoding="utf-8")

    return EngineResponse(
        state="ok_reopen",
        message=f"Reopened {ticket_id}. Reason: {reopen_reason}",
        ticket_id=ticket_id,
        data={"ticket_path": str(ticket_path), "changes": {"status": [old_status, "open"]}},
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py::TestEngineExecute -v`
Expected: All tests PASS (including all prior tests from 11.1-11.4)

**Step 5: Commit**

```
feat(ticket): implement _execute_reopen — status reset with reopen history

Replaces stub. Validates done/wontfix → open transition.
Appends to Reopen History section with timestamp and reason.
```

### Commit Point: After Task 11.5

Commit all changes. No full checkpoint required — the next full checkpoint at Task 11.6 will verify.

---

## Task 11.6: Execute Subcommand — Execute Dispatcher and Integration Tests

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_core.py`
- Modify: `packages/plugins/ticket/tests/test_engine.py`

This slice finalizes the `engine_execute` dispatcher (already implemented in 11.1 with stubs, now all stubs replaced) and adds integration-level tests that exercise the full create→update→close→reopen lifecycle.

**Step 1: Write integration tests**

The dispatcher was implemented in Task 11.1. All stubs have been replaced in 11.2-11.5. This slice adds integration tests that verify the full lifecycle and edge cases not covered by individual slice tests.

Add to `tests/test_engine.py`:

```python
class TestEngineExecuteIntegration:
    """Integration tests exercising the full engine_execute dispatcher
    across multiple lifecycle operations."""

    def test_full_lifecycle_create_update_close_reopen(self, tmp_tickets):
        """Create → update → close → reopen lifecycle."""
        # Create.
        resp = engine_execute(
            action="create",
            ticket_id=None,
            fields={
                "title": "Lifecycle test",
                "problem": "Integration test problem.",
                "priority": "medium",
                "source": {"type": "ad-hoc", "ref": "", "session": "test-session"},
                "tags": ["test"],
            },
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_create"
        ticket_id = resp.ticket_id
        ticket_path = Path(resp.data["ticket_path"])
        assert ticket_path.exists()

        # Update status to in_progress.
        resp = engine_execute(
            action="update",
            ticket_id=ticket_id,
            fields={"status": "in_progress"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_update"

        # Close with wontfix (avoids acceptance criteria requirement).
        resp = engine_execute(
            action="close",
            ticket_id=ticket_id,
            fields={"resolution": "wontfix"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_close"

        # Reopen.
        resp = engine_execute(
            action="reopen",
            ticket_id=ticket_id,
            fields={"reopen_reason": "Reconsidered — will fix after all"},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "ok_reopen"

        # Verify final state.
        content = ticket_path.read_text(encoding="utf-8")
        assert "status: open" in content
        assert "Reopen History" in content

    def test_unknown_action_escalates(self, tmp_tickets):
        """Dispatcher rejects unknown actions."""
        resp = engine_execute(
            action="merge",
            ticket_id=None,
            fields={},
            session_id="test-session",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert resp.state == "escalate"
        assert resp.error_code == "intent_mismatch"
```

**Step 2: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v`
Expected: All tests PASS (all classes: TestEngineClassify, TestEnginePlan, TestEnginePreflight, TestEngineExecute, TestEngineExecuteIntegration)

**Step 3: Commit**

```
feat(ticket): add execute integration tests — full lifecycle verification

TestEngineExecuteIntegration: create→update→close→reopen lifecycle,
unknown action escalation. All execute stubs replaced, dispatcher complete.
```

### Checkpoint: After Task 11.6

**Required actions (all three must complete):**

1. **Test barrier:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/test_engine.py -v
   ```
   All tests must pass.

2. **Git commit:** Commit all changes with descriptive message.

3. **Invariant ledger** — append to a running ledger comment at the top of `test_engine.py` or in a separate `M4_LEDGER.md`:
   ```
   ## Checkpoint: after Task 11.6 (final M4)
   test_classes: [TestEngineClassify, TestEnginePlan, TestEnginePreflight, TestEngineExecute, TestEngineExecuteIntegration]
   per_class_counts: {TestEngineClassify: 8, TestEnginePlan: 5, TestEnginePreflight: 15, TestEngineExecute: 24, TestEngineExecuteIntegration: 2}
   exports: [EngineResponse, engine_classify, engine_plan, engine_preflight, engine_execute, VALID_ACTIONS, VALID_ORIGINS]
   next_task_depends_on: [engine_classify, engine_plan, engine_preflight, engine_execute, EngineResponse]
   ```

**Monotonic subset enforcement [M]:** Each checkpoint's `test_classes` must be a superset of the previous checkpoint's. Each class's test count must be >= the previous count. The reviewer compares ledger entries between checkpoints.

---

## Gate Exit: M4 → M5

**Gate Type:** Critical (with round-trip probe)

**What the reviewer checks after M4 completes:**

1. **Full test suite:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/ -v
   ```
   All 7 test files must pass (6 upstream + test_engine.py).

2. **Invariant ledger verification:** Compare final ledger entry against all previous entries. Verify monotonic subset property for `test_classes` and `per_class_counts`.

3. **Round-trip gate probe [T]** — 4 operations with adversarial inputs:

   **Vector 1 — Create with adversarial tags:**
   ```python
   tags: ["auth,api", "[wip]", "plain"]
   source: {"type": "ad-hoc", "ref": 'say "hello"', "session": "test"}
   ```
   Assert: `parse_ticket` readback produces identical `tags` list and `source` dict (field-level equality).

   **Vector 2 — Update:**
   Change `status: open → in-progress`, add tag `"colon: value"`.
   Assert: all prior fields preserved + new tag present in readback.

   **Vector 3 — Close:**
   `status: in-progress → done`.
   Assert: readback `status == "done"`, all fields preserved.

   **Vector 4 — Reopen:**
   `status: done → open`.
   Assert: readback `status == "open"`, all fields preserved.

   **Pass/fail:** All 4 readbacks must produce field-level equality. Any mismatch = FAIL → triggers Failure Recovery step 3.

**Gate Card Template:**
```
## Gate Card: M4 → M5
evaluated_sha: <sha>
handoff_sha: <sha>
commands_to_run: ["cd packages/plugins/ticket && uv run pytest tests/ -v"]
must_pass_files: [tests/test_parse.py, tests/test_migration.py, tests/test_id.py, tests/test_render.py, tests/test_read.py, tests/test_dedup.py, tests/test_engine.py]
api_surface_expected:
  - scripts.ticket_engine_core: [engine_classify, engine_plan, engine_preflight, engine_execute]
verdict: PASS | FAIL
warnings: []
probe_evidence:
  - command: "round-trip probe vector 1 (create with adversarial tags)"
    result: "<field-level comparison output>"
  - command: "round-trip probe vector 2 (update with colon tag)"
    result: "<field-level comparison output>"
  - command: "round-trip probe vector 3 (close)"
    result: "<field-level comparison output>"
  - command: "round-trip probe vector 4 (reopen)"
    result: "<field-level comparison output>"
```
