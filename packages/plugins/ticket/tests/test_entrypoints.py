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

    def test_execute_blocked_phase1(self, tmp_path):
        """Agent execute is hard-blocked in Phase 1 (defense-in-depth)."""
        output = run_entrypoint(
            "ticket_engine_agent.py",
            "execute",
            {
                "action": "create",
                "fields": {"title": "test", "problem": "test", "priority": "medium"},
                "session_id": "test",
                "tickets_dir": str(tmp_path),
            },
            tmp_path,
        )
        assert output["state"] == "policy_blocked"


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
