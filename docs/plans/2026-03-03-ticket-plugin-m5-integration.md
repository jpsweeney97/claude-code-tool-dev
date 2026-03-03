# Ticket Plugin Phase 1 — Module 5: Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the two entrypoint scripts (`ticket_engine_user.py`, `ticket_engine_agent.py`), run integration tests for the full pipeline, and perform the final suite run with cleanup.

**Architecture:** Hybrid adapter pattern (Architecture E). Two entrypoints hardcode `request_origin` ("user" or "agent") and delegate to `ticket_engine_core.py`. `ticket_engine_agent.py` always gets `policy_blocked` in Phase 1 (agent hard-block). Integration tests exercise the full create->update->close->reopen lifecycle through the user entrypoint. Entrypoints use `subprocess.run()`, not Python imports — they are standalone scripts.

**Tech Stack:** Python 3.11+, PyYAML, pytest

**References (read-only — do not modify these files):**
- Canonical plan: `docs/plans/2026-03-02-ticket-plugin-phase1-plan.md`
- Modularization design: `docs/plans/2026-03-02-ticket-plugin-plan-modularization.md`
- Design doc: `docs/plans/2026-03-02-ticket-plugin-design.md` (canonical spec)

**Scope:** Module 5 of 5 (final module). Creates `scripts/ticket_engine_user.py`, `scripts/ticket_engine_agent.py`, `tests/test_entrypoints.py`, `tests/test_integration.py`. Task 15 runs the full suite and cleans up.

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

**From Module 1:** Plugin scaffold, conftest.py.

**From Module 2:** `scripts/ticket_parse.py` (ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block).

**From Module 3 — all utility modules:**
- `scripts/ticket_id.py`: `allocate_id`, `build_filename`
- `scripts/ticket_render.py`: `render_ticket`
- `scripts/ticket_read.py`: `find_ticket_by_id`, `list_tickets`
- `scripts/ticket_dedup.py`: `dedup_fingerprint`, `normalize`, `target_fingerprint`

**From Module 4:** `scripts/ticket_engine_core.py` (from Module 4, already implemented):
- `engine_classify(request) -> dict`
- `engine_plan(request) -> dict`
- `engine_preflight(request) -> dict`
- `engine_execute(request) -> dict`

**Cumulative test files (all passing):** test_parse.py, test_migration.py, test_id.py, test_render.py, test_read.py, test_dedup.py, test_engine.py

**M4->M5 gate passed:** Critical gate with round-trip probe — all 4 probe vectors produced field-level equality.

**Important:** Task 12 entrypoints use `subprocess.run()` to invoke engine scripts, NOT Python imports. This is why M4->M5 doesn't have Standard+ import sentinels — the round-trip probe covers the critical contract instead.

## Gate Entry: M4 -> M5

Verify before starting:
```bash
cd packages/plugins/ticket && uv run pytest tests/ -v
```
All 7 test files must pass. The M4->M5 gate card should confirm round-trip probe success.

---

## Task 12: Entrypoints — ticket_engine_user.py and ticket_engine_agent.py

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_engine_user.py`
- Create: `packages/plugins/ticket/scripts/ticket_engine_agent.py`
- Create: `packages/plugins/ticket/tests/test_entrypoints.py`

**Context:** Read design doc: "Trust Model" (lines ~359-406). Entrypoints are thin wrappers that hardcode `request_origin` and delegate to core (from Module 4, already implemented). They read JSON input from a file path (payload-by-file pattern).

**Step 1: Write failing tests**

```python
"""Tests for engine entrypoints — ticket_engine_user.py and ticket_engine_agent.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Path to scripts directory.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def run_entrypoint(script: str, subcommand: str, payload: dict, tmp_path: Path) -> dict:
    """Run an entrypoint script as a subprocess and return parsed JSON output."""
    payload_file = tmp_path / "input.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script), subcommand, str(payload_file)],
        capture_output=True,
        text=True,
        cwd=str(SCRIPTS_DIR.parent),
    )
    assert result.returncode in (0, 1, 2), f"Unexpected exit code: {result.returncode}\nstderr: {result.stderr}"
    return json.loads(result.stdout)


class TestUserEntrypoint:
    def test_classify_create(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_user.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"
        assert output["data"]["intent"] == "create"

    def test_origin_is_user(self, tmp_path):
        """The user entrypoint always sets request_origin=user."""
        output = run_entrypoint(
            "ticket_engine_user.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "request_origin": "agent",  # Caller tries to override — ignored.
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        # Should succeed because origin is forced to "user".
        assert output["state"] == "ok"


class TestAgentEntrypoint:
    def test_classify_create(self, tmp_path):
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"
        assert output["data"]["intent"] == "create"

    def test_origin_is_agent(self, tmp_path):
        """The agent entrypoint always sets request_origin=agent."""
        # Agent classify succeeds, but preflight would block in suggest mode.
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "classify",
            {
                "action": "create",
                "args": {},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "ok"


class TestEntrypointErrors:
    def test_missing_subcommand(self, tmp_path):
        payload_file = tmp_path / "input.json"
        payload_file.write_text("{}", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "ticket_engine_user.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_invalid_json(self, tmp_path):
        payload_file = tmp_path / "input.json"
        payload_file.write_text("not json", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "ticket_engine_user.py"), "classify", str(payload_file)],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR.parent),
        )
        assert result.returncode != 0
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v`
Expected: FileNotFoundError (scripts don't exist)

**Step 3: Write ticket_engine_user.py**

```python
#!/usr/bin/env python3
"""User entrypoint for the ticket engine.

Hardcodes request_origin="user". Called by ticket-ops skill.
Usage: python3 ticket_engine_user.py <subcommand> <payload_file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)

REQUEST_ORIGIN = "user"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_user.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "user" regardless of what caller passed.
    payload["request_origin"] = REQUEST_ORIGIN

    # Check for hook-injected origin mismatch.
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != REQUEST_ORIGIN:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={REQUEST_ORIGIN}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        sys.exit(1)

    tickets_dir = Path(payload.get("tickets_dir", "docs/tickets"))

    resp = _dispatch(subcommand, payload, tickets_dir)
    print(resp.to_json())
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        sys.exit(0)
    elif resp.error_code == "need_fields":
        sys.exit(2)
    else:
        sys.exit(1)


def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    elif subcommand == "plan":
        return engine_plan(
            intent=payload.get("intent", payload.get("action", "")),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            tickets_dir=tickets_dir,
        )
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            tickets_dir=tickets_dir,
        )
    elif subcommand == "execute":
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
        )
    else:
        return EngineResponse(state="escalate", message=f"Unknown subcommand: {subcommand!r}", error_code="intent_mismatch")


if __name__ == "__main__":
    main()
```

**Step 4: Write ticket_engine_agent.py**

```python
#!/usr/bin/env python3
"""Agent entrypoint for the ticket engine.

Hardcodes request_origin="agent". Called by ticket-autocreate agent.
Usage: python3 ticket_engine_agent.py <subcommand> <payload_file>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_core import (
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)

REQUEST_ORIGIN = "agent"


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: ticket_engine_agent.py <subcommand> <payload_file>"}), file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    payload_path = Path(sys.argv[2])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"error": f"Cannot read payload: {exc}"}), file=sys.stderr)
        sys.exit(1)

    # Force request_origin to "agent" regardless of what caller passed.
    payload["request_origin"] = REQUEST_ORIGIN

    # Check for hook-injected origin mismatch.
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != REQUEST_ORIGIN:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={REQUEST_ORIGIN}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        sys.exit(1)

    tickets_dir = Path(payload.get("tickets_dir", "docs/tickets"))

    resp = _dispatch(subcommand, payload, tickets_dir)
    print(resp.to_json())
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        sys.exit(0)
    elif resp.error_code == "need_fields":
        sys.exit(2)
    else:
        sys.exit(1)


def _dispatch(subcommand: str, payload: dict, tickets_dir: Path) -> EngineResponse:
    if subcommand == "classify":
        return engine_classify(
            action=payload.get("action", ""),
            args=payload.get("args", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
        )
    elif subcommand == "plan":
        return engine_plan(
            intent=payload.get("intent", payload.get("action", "")),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            tickets_dir=tickets_dir,
        )
    elif subcommand == "preflight":
        return engine_preflight(
            ticket_id=payload.get("ticket_id"),
            action=payload.get("action", ""),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            classify_confidence=payload.get("classify_confidence", 0.0),
            classify_intent=payload.get("classify_intent", ""),
            dedup_fingerprint=payload.get("dedup_fingerprint"),
            target_fingerprint=payload.get("target_fingerprint"),
            duplicate_of=payload.get("duplicate_of"),
            dedup_override=payload.get("dedup_override", False),
            tickets_dir=tickets_dir,
        )
    elif subcommand == "execute":
        return engine_execute(
            action=payload.get("action", ""),
            ticket_id=payload.get("ticket_id"),
            fields=payload.get("fields", {}),
            session_id=payload.get("session_id", ""),
            request_origin=REQUEST_ORIGIN,
            dedup_override=payload.get("dedup_override", False),
            dependency_override=payload.get("dependency_override", False),
            tickets_dir=tickets_dir,
        )
    else:
        return EngineResponse(state="escalate", message=f"Unknown subcommand: {subcommand!r}", error_code="intent_mismatch")


if __name__ == "__main__":
    main()
```

**Step 5: Run tests to verify they pass**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_entrypoints.py -v`
Expected: All tests PASS

**Step 6: Commit**

```
feat(ticket): add user and agent entrypoints with origin enforcement

Payload-by-file pattern, hardcoded request_origin, hook origin
mismatch detection. Both delegate to engine_core.
```

---

## Task 13: Integration Test — Full Pipeline

**Files:**
- Create: `packages/plugins/ticket/tests/test_integration.py`

**Context:** End-to-end test of the classify -> plan -> preflight -> execute pipeline. Uses `engine_classify`, `engine_plan`, `engine_preflight`, `engine_execute` from `ticket_engine_core.py` (from Module 4, already implemented).

**Step 1: Write integration tests**

```python
"""Integration tests — full engine pipeline end-to-end."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ticket_engine_core import (
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)


class TestFullCreatePipeline:
    def test_user_create_end_to_end(self, tmp_tickets):
        """classify -> plan -> preflight -> execute for user create."""
        # Step 1: classify
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="integration-test",
            request_origin="user",
        )
        assert classify_resp.state == "ok"

        # Step 2: plan
        fields = {
            "title": "Integration test ticket",
            "problem": "This is an integration test.",
            "priority": "medium",
            "key_files": [],
        }
        plan_resp = engine_plan(
            intent=classify_resp.data["intent"],
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "ok"

        # Step 3: preflight
        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="integration-test",
            request_origin="user",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=plan_resp.data["dedup_fingerprint"],
            target_fingerprint=plan_resp.data["target_fingerprint"],
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "ok"

        # Step 4: execute
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="integration-test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"
        assert Path(execute_resp.data["ticket_path"]).exists()

    def test_agent_blocked_phase1_fail_closed(self, tmp_tickets):
        """Agent create is hard-blocked by Phase 1 fail-closed policy."""
        classify_resp = engine_classify(
            action="create",
            args={},
            session_id="agent-test",
            request_origin="agent",
        )
        assert classify_resp.state == "ok"

        preflight_resp = engine_preflight(
            ticket_id=None,
            action="create",
            session_id="agent-test",
            request_origin="agent",
            classify_confidence=classify_resp.data["confidence"],
            classify_intent=classify_resp.data["intent"],
            dedup_fingerprint=None,
            target_fingerprint=None,
            tickets_dir=tmp_tickets,
        )
        assert preflight_resp.state == "policy_blocked"

    def test_update_then_close_pipeline(self, tmp_tickets):
        """Create -> update to in_progress -> close."""
        from tests.conftest import make_ticket

        make_ticket(tmp_tickets, "2026-03-02-test.md", id="T-20260302-01", status="open")

        # Update to in_progress.
        update_resp = engine_execute(
            action="update",
            ticket_id="T-20260302-01",
            fields={"status": "in_progress"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert update_resp.state == "ok_update"

        # Close.
        close_resp = engine_execute(
            action="close",
            ticket_id="T-20260302-01",
            fields={"resolution": "done"},
            session_id="test",
            request_origin="user",
            dedup_override=False,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert close_resp.state == "ok_close"

    def test_dedup_then_override(self, tmp_tickets):
        """Create duplicate detected -> override -> create succeeds."""
        from tests.conftest import make_ticket

        make_ticket(
            tmp_tickets,
            "2026-03-02-existing.md",
            id="T-20260302-01",
            problem="Auth times out.",
        )

        fields = {
            "title": "Same auth bug",
            "problem": "Auth times out.",
            "priority": "high",
            "key_files": [],
        }

        plan_resp = engine_plan(
            intent="create",
            fields=fields,
            session_id="test",
            request_origin="user",
            tickets_dir=tmp_tickets,
        )
        assert plan_resp.state == "duplicate_candidate"

        # Override and create anyway.
        execute_resp = engine_execute(
            action="create",
            ticket_id=None,
            fields=fields,
            session_id="test",
            request_origin="user",
            dedup_override=True,
            dependency_override=False,
            tickets_dir=tmp_tickets,
        )
        assert execute_resp.state == "ok_create"
```

**Step 2: Run tests**

Run: `cd packages/plugins/ticket && uv run pytest tests/test_integration.py -v`
Expected: All tests PASS

**Step 3: Run full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```
feat(ticket): add integration tests for full engine pipeline

End-to-end: user create, agent suggest-mode block, update->close,
dedup detection with override.
```

---

## Task 15: Final — Run Full Suite, Clean Up, Commit

**Step 1: Run the full test suite**

Run: `cd packages/plugins/ticket && uv run pytest -v --tb=short`
Expected: All tests PASS

**Step 2: Check test count**

Run: `cd packages/plugins/ticket && uv run pytest --co -q | tail -1`
Expected: ~104+ tests collected

**Step 3: Delete .gitkeep files if directories have content**

```bash
# Only remove .gitkeep if the directory has other files.
for dir in scripts skills agents references; do
    if [ "$(ls -A packages/plugins/ticket/$dir/ 2>/dev/null | grep -v .gitkeep)" ]; then
        trash packages/plugins/ticket/$dir/.gitkeep
    fi
done
```

**Step 4: Final commit**

```
chore(ticket): phase 1 complete — engine + contract + utilities

15 tasks: scaffold, contract, parse, ID, render, read, dedup,
engine (classify, plan, preflight, execute), entrypoints,
integration tests, migration golden tests.
```

---

## Gate Exit: Final Gate

**Gate Type:** Final (no next module)

**What the reviewer checks after M5 completes:**

1. **Full suite run:**
   ```bash
   cd packages/plugins/ticket && uv run pytest tests/ -v
   ```
   All 9 test files must pass: test_parse.py, test_migration.py, test_id.py, test_render.py, test_read.py, test_dedup.py, test_engine.py, test_entrypoints.py, test_integration.py

2. **Entrypoint smoke test:**
   ```bash
   cd packages/plugins/ticket
   # User entrypoint should be executable
   python scripts/ticket_engine_user.py --help 2>&1 || true
   # Agent entrypoint should exist
   python scripts/ticket_engine_agent.py --help 2>&1 || true
   ```

3. **Agent hard-block verification:**
   Verify that `ticket_engine_agent.py` returns `policy_blocked` for any mutation request (Phase 1 policy).

4. **Clean state:** No temporary files, no debug prints, no TODO comments in committed code.

**Final Gate Card Template:**
```
## Final Gate Card: M5 Complete
evaluated_sha: <executor's final commit SHA>
commands_to_run: ["cd packages/plugins/ticket && uv run pytest tests/ -v"]
must_pass_files: [tests/test_parse.py, tests/test_migration.py, tests/test_id.py, tests/test_render.py, tests/test_read.py, tests/test_dedup.py, tests/test_engine.py, tests/test_entrypoints.py, tests/test_integration.py]
total_tests: ~128
api_surface:
  - scripts.ticket_engine_user: [user_create, user_update, user_close, user_reopen]
  - scripts.ticket_engine_agent: [agent_create, agent_update, agent_close, agent_reopen]
  - scripts.ticket_engine_core: [engine_classify, engine_plan, engine_preflight, engine_execute]
  - scripts.ticket_parse: [ParsedTicket, parse_ticket, extract_fenced_yaml, parse_yaml_block]
  - scripts.ticket_id: [allocate_id, build_filename]
  - scripts.ticket_render: [render_ticket]
  - scripts.ticket_read: [find_ticket_by_id, list_tickets]
  - scripts.ticket_dedup: [dedup_fingerprint, normalize, target_fingerprint]
verdict: PASS | FAIL
phase1_complete: true
```
