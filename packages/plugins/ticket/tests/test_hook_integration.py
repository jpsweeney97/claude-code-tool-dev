"""Integration tests — hook subprocess → engine subprocess → audit trail.

Exercises the full production flow: the PreToolUse hook validates and injects
trust fields into a payload file, then the user entrypoint subprocess reads
that payload and runs the engine, which writes an audit trail.

Both the hook and entrypoint are invoked via subprocess.run with
sys.executable, matching how Claude Code invokes them in production.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

PLUGIN_ROOT = str(Path(__file__).parent.parent)
HOOK_SCRIPT = str(Path(__file__).parent.parent / "hooks" / "ticket_engine_guard.py")
USER_ENTRYPOINT = str(Path(__file__).parent.parent / "scripts" / "ticket_engine_user.py")


def run_hook(command: str, session_id: str = "integration-sess", cwd: str = "/") -> dict:
    """Run the hook with a Bash command and return parsed output."""
    hook_input = {
        "session_id": session_id,
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": cwd,
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_use_id": "toolu_integration",
    }
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT}
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=json.dumps(hook_input),
        capture_output=True, text=True, env=env, timeout=10,
    )
    assert result.returncode == 0, f"Hook crashed: {result.stderr}"
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


class TestFullCreateFlow:
    """Full flow: hook → user entrypoint → create → audit trail."""

    def test_full_create_flow(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()

        # Create payload file with create action and required fields.
        payload = {
            "action": "create",
            "fields": {
                "title": "Integration test ticket",
                "problem": "Testing the full hook-engine-audit flow.",
                "priority": "medium",
            },
            "tickets_dir": str(tickets_dir),
        }
        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        # Step 1: Run hook — verify allow + payload injected.
        command = f"python3 {PLUGIN_ROOT}/scripts/ticket_engine_user.py execute {payload_file}"
        hook_output = run_hook(command, session_id="integration-sess", cwd=str(tmp_path))
        assert hook_output != {}, "Hook should return a decision for ticket_engine commands"
        decision = hook_output["hookSpecificOutput"]["permissionDecision"]
        assert decision == "allow"

        # Verify hook injected trust fields into the payload file.
        injected = json.loads(payload_file.read_text(encoding="utf-8"))
        assert injected["hook_injected"] is True
        assert injected["session_id"] == "integration-sess"
        assert injected["hook_request_origin"] == "user"

        # Step 2: Run user entrypoint subprocess — verify ok_create.
        result = subprocess.run(
            [sys.executable, USER_ENTRYPOINT, "execute", str(payload_file)],
            capture_output=True, text=True, cwd=str(tmp_path), timeout=10,
        )
        assert result.returncode == 0, f"Entrypoint failed: {result.stderr}"
        resp = json.loads(result.stdout)
        assert resp["state"] == "ok_create"

        # Step 3: Read audit file — verify 2 entries (attempt_started + ok_create).
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = tickets_dir / ".audit" / date_dir / "integration-sess.jsonl"
        assert audit_file.exists(), f"Audit file not found at {audit_file}"

        lines = [json.loads(line) for line in audit_file.read_text().strip().split("\n")]
        assert len(lines) == 2
        assert lines[0]["action"] == "attempt_started"
        assert lines[1]["action"] == "create"
        assert lines[1]["result"] == "ok_create"

        # Step 4: Verify session_id in audit matches what hook injected.
        assert lines[0]["session_id"] == "integration-sess"
        assert lines[1]["session_id"] == "integration-sess"


class TestHookDenyPreventsExecution:
    """Denied commands don't reach the engine."""

    def test_hook_deny_prevents_execution(self, tmp_path: Path) -> None:
        payload = {"action": "create"}
        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        # Command with extra args after payload path triggers deny.
        command = (
            f"python3 {PLUGIN_ROOT}/scripts/ticket_engine_user.py execute "
            f"{payload_file} --verbose"
        )
        hook_output = run_hook(command, cwd=str(tmp_path))

        # Verify deny.
        decision = hook_output["hookSpecificOutput"]["permissionDecision"]
        assert decision == "deny"

        # Verify payload NOT modified (no hook_injected field).
        raw = json.loads(payload_file.read_text(encoding="utf-8"))
        assert "hook_injected" not in raw


class TestHookSessionIdPropagatesToAudit:
    """Session ID propagates end-to-end: hook → payload → engine → audit."""

    def test_hook_session_id_propagates_to_audit(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / "tickets"
        tickets_dir.mkdir()

        unique_session = "unique-sess-xyz"
        payload = {
            "action": "create",
            "fields": {
                "title": "Session propagation test",
                "problem": "Verify session_id flows through entire pipeline.",
                "priority": "low",
            },
            "tickets_dir": str(tickets_dir),
        }
        payload_file = tmp_path / "payload.json"
        payload_file.write_text(json.dumps(payload), encoding="utf-8")

        # Step 1: Run hook with specific session_id.
        command = f"python3 {PLUGIN_ROOT}/scripts/ticket_engine_user.py execute {payload_file}"
        hook_output = run_hook(command, session_id=unique_session, cwd=str(tmp_path))
        assert hook_output["hookSpecificOutput"]["permissionDecision"] == "allow"

        # Step 2: Run entrypoint.
        result = subprocess.run(
            [sys.executable, USER_ENTRYPOINT, "execute", str(payload_file)],
            capture_output=True, text=True, cwd=str(tmp_path), timeout=10,
        )
        assert result.returncode == 0, f"Entrypoint failed: {result.stderr}"

        # Step 3: Verify audit file exists at path with that session_id.
        date_dir = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = tickets_dir / ".audit" / date_dir / f"{unique_session}.jsonl"
        assert audit_file.exists(), f"Audit file not found at {audit_file}"

        # Step 4: Verify session_id in audit entries matches.
        lines = [json.loads(line) for line in audit_file.read_text().strip().split("\n")]
        assert len(lines) >= 2
        for entry in lines:
            assert entry["session_id"] == unique_session
