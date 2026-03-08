# A-003: Shared Entrypoint Runner — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract duplicated entrypoint boundary logic into a shared runner module, reducing `ticket_engine_user.py` and `ticket_engine_agent.py` to thin wrappers.

**Architecture:** New `ticket_engine_runner.py` exposes `run(request_origin, argv, *, prog) -> int` containing all boundary logic (payload read, origin enforcement, trust triple, project root, tickets_dir, dispatch, exit codes). Entrypoints become ~15-line wrappers that set origin and delegate. Hook guard unchanged.

**Tech Stack:** Python 3.14, dataclasses (existing), pytest.

**Design doc:** `docs/plans/2026-03-08-a003-shared-entrypoint-runner-design.md`

---

### Task 1: Create `ticket_engine_runner.py` with `run()` and `_dispatch()`

**Files:**
- Create: `packages/plugins/ticket/scripts/ticket_engine_runner.py`

**Step 1: Create the runner module**

The runner consolidates all logic from `ticket_engine_user.py:37-185` and `ticket_engine_agent.py:37-185`. The only parameterized value is `request_origin`.

```python
"""Shared entrypoint runner for the ticket engine.

Consolidates boundary logic (payload read, origin enforcement, trust triple,
project root, tickets_dir, dispatch, exit codes) that was previously
duplicated between ticket_engine_user.py and ticket_engine_agent.py.

Entrypoints import and call run() with their hardcoded request_origin.
This module is never invoked directly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from scripts.ticket_engine_core import (
    AutonomyConfig,
    EngineResponse,
    engine_classify,
    engine_execute,
    engine_plan,
    engine_preflight,
)
from scripts.ticket_paths import discover_project_root, resolve_tickets_dir
from scripts.ticket_stage_models import (
    ClassifyInput,
    ExecuteInput,
    PayloadError,
    PlanInput,
    PreflightInput,
)
from scripts.ticket_trust import collect_trust_triple_errors


def run(
    request_origin: str,
    argv: list[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the ticket engine entrypoint.

    Args:
        request_origin: Authoritative origin ("user" or "agent").
        argv: Command-line arguments [subcommand, payload_file].
              Defaults to sys.argv[1:].
        prog: Script name for usage messages.

    Returns:
        Exit code: 0 (success), 1 (engine error), 2 (need_fields).
    """
    args = argv if argv is not None else sys.argv[1:]
    if len(args) < 2:
        print(
            json.dumps({"error": f"Usage: {prog} <subcommand> <payload_file>"}),
            file=sys.stderr,
        )
        return 1

    subcommand = args[0]
    payload_path = Path(args[1])

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps({"error": f"Cannot read payload: {exc}"}),
            file=sys.stderr,
        )
        return 1

    # Normalize origin in payload. request_origin argument is authoritative.
    payload["request_origin"] = request_origin

    # Check for hook-injected origin mismatch (all stages).
    hook_origin = payload.get("hook_request_origin")
    if hook_origin is not None and hook_origin != request_origin:
        resp = EngineResponse(
            state="escalate",
            message=f"origin_mismatch: entrypoint={request_origin}, hook={hook_origin}",
            error_code="origin_mismatch",
        )
        print(resp.to_json())
        return 1

    # Execute requires the full trust triple.
    if subcommand == "execute":
        trust_errors = collect_trust_triple_errors(
            payload.get("hook_injected", False),
            hook_origin,
            payload.get("session_id", ""),
        )
        if trust_errors:
            resp = EngineResponse(
                state="policy_blocked",
                message=f"Execute requires verified hook provenance: {', '.join(trust_errors)}",
                error_code="policy_blocked",
            )
            print(resp.to_json())
            return 1

    project_root = discover_project_root(Path.cwd())
    if project_root is None:
        resp = EngineResponse(
            state="policy_blocked",
            message="Cannot determine project root: no .claude/ or .git/ marker found in ancestors of cwd",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        return 1

    tickets_dir_raw = payload.get("tickets_dir", "docs/tickets")
    tickets_dir, path_error = resolve_tickets_dir(tickets_dir_raw, project_root=project_root)
    if path_error is not None or tickets_dir is None:
        resp = EngineResponse(
            state="policy_blocked",
            message=path_error or "tickets_dir validation failed",
            error_code="policy_blocked",
        )
        print(resp.to_json())
        return 1

    resp = _dispatch(subcommand, payload, tickets_dir, request_origin)
    print(resp.to_json())
    return _exit_code(resp)


def _exit_code(resp: EngineResponse) -> int:
    """Map EngineResponse to exit code. Single-sourced."""
    # Exit codes: 0=success, 1=engine error, 2=validation failure (need_fields).
    if resp.state in ("ok", "ok_create", "ok_update", "ok_close", "ok_close_archived", "ok_reopen"):
        return 0
    if resp.error_code == "need_fields":
        return 2
    return 1


def _dispatch(
    subcommand: str,
    payload: dict[str, Any],
    tickets_dir: Path,
    request_origin: str,
) -> EngineResponse:
    try:
        if subcommand == "classify":
            inp = ClassifyInput.from_payload(payload)
            return engine_classify(
                action=inp.action,
                args=inp.args,
                session_id=inp.session_id,
                request_origin=request_origin,
            )
        elif subcommand == "plan":
            inp = PlanInput.from_payload(payload)
            return engine_plan(
                intent=inp.intent,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=request_origin,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "preflight":
            inp = PreflightInput.from_payload(payload)
            return engine_preflight(
                ticket_id=inp.ticket_id,
                action=inp.action,
                session_id=inp.session_id,
                request_origin=request_origin,
                classify_confidence=inp.classify_confidence,
                classify_intent=inp.classify_intent,
                dedup_fingerprint=inp.dedup_fingerprint,
                target_fingerprint=inp.target_fingerprint,
                fields=inp.fields,
                duplicate_of=inp.duplicate_of,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                hook_injected=inp.hook_injected,
                tickets_dir=tickets_dir,
            )
        elif subcommand == "execute":
            inp = ExecuteInput.from_payload(payload)
            autonomy_config = (
                AutonomyConfig.from_dict(inp.autonomy_config_data)
                if isinstance(inp.autonomy_config_data, dict)
                else None
            )
            return engine_execute(
                action=inp.action,
                ticket_id=inp.ticket_id,
                fields=inp.fields,
                session_id=inp.session_id,
                request_origin=request_origin,
                dedup_override=inp.dedup_override,
                dependency_override=inp.dependency_override,
                tickets_dir=tickets_dir,
                target_fingerprint=inp.target_fingerprint,
                autonomy_config=autonomy_config,
                hook_injected=inp.hook_injected,
                hook_request_origin=inp.hook_request_origin,
                classify_intent=inp.classify_intent,
                classify_confidence=inp.classify_confidence,
                dedup_fingerprint=inp.dedup_fingerprint,
            )
        else:
            return EngineResponse(
                state="escalate",
                message=f"Unknown subcommand: {subcommand!r}",
                error_code="intent_mismatch",
            )
    except PayloadError as exc:
        return EngineResponse(
            state=exc.state,
            message=f"{subcommand} payload validation failed: {exc}",
            error_code=exc.code,
        )
```

**Step 2: Verify the module parses cleanly**

Run: `cd packages/plugins/ticket && python3 -c "import scripts.ticket_engine_runner; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```
git add packages/plugins/ticket/scripts/ticket_engine_runner.py
git commit -m "feat(ticket): add shared entrypoint runner (A-003)"
```

---

### Task 2: Write `test_runner.py` — in-process runner tests

**Files:**
- Create: `packages/plugins/ticket/tests/test_runner.py`

**Step 1: Write the test file**

All tests call `run()` directly with `argv` and capture stdout/stderr via `capsys`. Each test creates a `tmp_path` with a `.git` marker (for project root discovery) and a JSON payload file.

```python
"""Tests for ticket_engine_runner.py — in-process boundary logic tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ticket_engine_runner import run


def _write_payload(tmp_path: Path, payload: dict) -> str:
    """Write payload to a temp file and return the path string."""
    p = tmp_path / "input.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return str(p)


def _ensure_project_root(tmp_path: Path) -> None:
    """Create a .git marker so discover_project_root() succeeds."""
    (tmp_path / ".git").mkdir(exist_ok=True)


class TestUsageErrors:
    def test_missing_args_returns_1(self, capsys, tmp_path):
        code = run("user", [], prog="ticket_engine_user.py")
        assert code == 1
        err = capsys.readouterr().err
        assert "Usage:" in err

    def test_one_arg_returns_1(self, capsys, tmp_path):
        code = run("user", ["classify"], prog="ticket_engine_user.py")
        assert code == 1
        err = capsys.readouterr().err
        assert "Usage:" in err

    def test_prog_appears_in_usage(self, capsys):
        run("user", [], prog="my_custom_prog.py")
        err = capsys.readouterr().err
        assert "my_custom_prog.py" in err


class TestPayloadReadErrors:
    def test_missing_file_returns_1(self, capsys, tmp_path):
        _ensure_project_root(tmp_path)
        code = run(
            "user",
            ["classify", str(tmp_path / "nonexistent.json")],
            prog="ticket_engine_user.py",
        )
        assert code == 1
        err = capsys.readouterr().err
        assert "Cannot read payload" in err

    def test_bad_json_returns_1(self, capsys, tmp_path):
        _ensure_project_root(tmp_path)
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json", encoding="utf-8")
        code = run(
            "user",
            ["classify", str(bad_file)],
            prog="ticket_engine_user.py",
        )
        assert code == 1
        err = capsys.readouterr().err
        assert "Cannot read payload" in err


class TestOriginMismatch:
    def test_user_entrypoint_rejects_agent_hook_origin(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "args": {},
            "session_id": "test",
            "hook_request_origin": "agent",
        })
        code = run("user", ["classify", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "origin_mismatch"

    def test_agent_entrypoint_rejects_user_hook_origin(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "args": {},
            "session_id": "test",
            "hook_request_origin": "user",
        })
        code = run("agent", ["classify", payload_file], prog="ticket_engine_agent.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "origin_mismatch"


class TestTrustTriple:
    def test_execute_without_hook_injected(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "fields": {"title": "t", "problem": "p"},
            "session_id": "test",
        })
        code = run("user", ["execute", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "policy_blocked"

    def test_execute_with_empty_session_id(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "fields": {"title": "t", "problem": "p"},
            "hook_injected": True,
            "hook_request_origin": "user",
            "session_id": "",
        })
        code = run("user", ["execute", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "policy_blocked"

    def test_execute_without_hook_request_origin(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "fields": {"title": "t", "problem": "p"},
            "hook_injected": True,
            "session_id": "test",
        })
        code = run("user", ["execute", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] in ("policy_blocked", "origin_mismatch")


class TestProjectRoot:
    def test_no_project_root_returns_policy_blocked(self, capsys, tmp_path, monkeypatch):
        # tmp_path has NO .git or .claude marker.
        nested = tmp_path / "no" / "markers"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)
        payload_file = _write_payload(nested, {
            "action": "create",
            "args": {},
            "session_id": "test",
        })
        code = run("user", ["classify", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "policy_blocked"
        assert "project root" in out["message"]


class TestTicketsDir:
    def test_tickets_dir_outside_root_returns_policy_blocked(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        outside = tmp_path.parent / "outside-tickets"
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "args": {},
            "session_id": "test",
            "tickets_dir": str(outside),
        })
        code = run("user", ["classify", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "policy_blocked"


class TestSuccessfulDispatch:
    def test_classify_returns_0(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "args": {},
            "session_id": "test",
        })
        code = run("user", ["classify", payload_file], prog="ticket_engine_user.py")
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "ok"

    def test_execute_with_full_trust_triple_returns_0(self, capsys, tmp_path, monkeypatch):
        from scripts.ticket_dedup import dedup_fingerprint as compute_fp

        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        problem = "test problem"
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "fields": {"title": "Test", "problem": problem, "priority": "medium"},
            "hook_injected": True,
            "hook_request_origin": "user",
            "session_id": "test-session",
            "classify_intent": "create",
            "classify_confidence": 0.95,
            "dedup_fingerprint": compute_fp(problem, []),
        })
        code = run("user", ["execute", payload_file], prog="ticket_engine_user.py")
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["state"] == "ok_create"


class TestExitCodes:
    def test_need_fields_returns_2(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        # Plan with empty fields triggers need_fields for create intent.
        payload_file = _write_payload(tmp_path, {
            "intent": "create",
            "fields": {},
            "session_id": "test",
        })
        code = run("user", ["plan", payload_file], prog="ticket_engine_user.py")
        assert code == 2
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "need_fields"

    def test_unknown_subcommand_returns_1(self, capsys, tmp_path, monkeypatch):
        _ensure_project_root(tmp_path)
        monkeypatch.chdir(tmp_path)
        payload_file = _write_payload(tmp_path, {
            "action": "create",
            "args": {},
            "session_id": "test",
        })
        code = run("user", ["bogus", payload_file], prog="ticket_engine_user.py")
        assert code == 1
        out = json.loads(capsys.readouterr().out)
        assert out["error_code"] == "intent_mismatch"
```

**Step 2: Run tests to verify they pass**

Run: `uv run --package ticket-plugin pytest packages/plugins/ticket/tests/test_runner.py -v`
Expected: All 15 tests pass.

**Step 3: Commit**

```
git add packages/plugins/ticket/tests/test_runner.py
git commit -m "test(ticket): add in-process runner tests (A-003)"
```

---

### Task 3: Rewrite entrypoints as thin wrappers

**Files:**
- Modify: `packages/plugins/ticket/scripts/ticket_engine_user.py` (189→15 lines)
- Modify: `packages/plugins/ticket/scripts/ticket_engine_agent.py` (189→15 lines)

**Step 1: Rewrite `ticket_engine_user.py`**

Replace the entire file with:

```python
#!/usr/bin/env python3
"""User entrypoint for the ticket engine.

Hardcodes request_origin="user". Called by ticket-ops skill.
Usage: python3 ticket_engine_user.py <subcommand> <payload_file>
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_runner import run

if __name__ == "__main__":
    raise SystemExit(run("user", prog="ticket_engine_user.py"))
```

**Step 2: Rewrite `ticket_engine_agent.py`**

Replace the entire file with:

```python
#!/usr/bin/env python3
"""Agent entrypoint for the ticket engine.

Hardcodes request_origin="agent". Called by ticket-autocreate agent.
Usage: python3 ticket_engine_agent.py <subcommand> <payload_file>
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ticket_engine_runner import run

if __name__ == "__main__":
    raise SystemExit(run("agent", prog="ticket_engine_agent.py"))
```

**Step 3: Run the full test suite**

Run: `uv run --package ticket-plugin pytest packages/plugins/ticket/ -v`
Expected: All tests pass (runner tests + existing entrypoint subprocess tests + all engine tests). Watch for minor assertion updates in `test_entrypoints.py` if error messages changed slightly.

**Step 4: If any `test_entrypoints.py` tests fail, fix assertions**

The subprocess tests should work as-is because the entrypoints still invoke the same logic. If any assertions break due to minor message changes, update the assertions to match the new (centralized) output. Do not change the runner behavior to match old assertions — the runner is now authoritative.

**Step 5: Commit**

```
git add packages/plugins/ticket/scripts/ticket_engine_user.py packages/plugins/ticket/scripts/ticket_engine_agent.py
git commit -m "refactor(ticket): rewrite entrypoints as thin wrappers (A-003)"
```

If `test_entrypoints.py` needed assertion updates, include those:
```
git add packages/plugins/ticket/tests/test_entrypoints.py
git commit -m "test(ticket): update entrypoint assertions for runner centralization (A-003)"
```

---

### Task 4: Final verification

**Step 1: Run full test suite**

Run: `uv run --package ticket-plugin pytest packages/plugins/ticket/ -v`
Expected: All tests pass.

**Step 2: Verify import direction**

Run: `cd packages/plugins/ticket && python3 -c "from scripts.ticket_engine_runner import run; print('runner OK')" && python3 -c "from scripts.ticket_engine_user import run; print('wrapper import OK')"`
Expected: Both print OK. The wrapper imports the runner; the runner imports ticket modules. No circular imports.

**Step 3: Verify the runner is NOT in hook candidate basenames**

Run: `grep -n 'ticket_engine_runner' packages/plugins/ticket/hooks/ticket_engine_guard.py`
Expected: No output. The runner should not appear in the hook guard.

**Step 4: Verify wrapper line counts**

Run: `wc -l packages/plugins/ticket/scripts/ticket_engine_user.py packages/plugins/ticket/scripts/ticket_engine_agent.py packages/plugins/ticket/scripts/ticket_engine_runner.py`
Expected: Wrappers ~18 lines each, runner ~170 lines.

**Step 5: Commit the full changeset (if not already committed per task)**

All commits should already be made. Verify with: `git log --oneline -5`
