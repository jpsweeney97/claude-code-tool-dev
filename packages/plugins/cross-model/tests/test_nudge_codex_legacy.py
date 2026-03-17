"""Legacy tests for nudge_codex.py — PostToolUseFailure nudge hook.

Migrated from repo root tests/test_nudge_codex.py. Uses MODULE alias to
preserve original test bodies unchanged.
"""

from __future__ import annotations

import json  # noqa: F401
from io import StringIO  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest

import scripts.nudge_codex as MODULE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event(tool: str = "Bash", session_id: str = "test-session") -> dict:
    return {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": tool,
        "session_id": session_id,
    }


def _run_main(
    monkeypatch,
    event: dict,
    *,
    env_nudge: str | None = "1",
    state_dir: Path | None = None,
) -> None:
    """Run nudge_codex.main() with controlled stdin and env.

    Raises SystemExit when main() calls sys.exit().
    """
    monkeypatch.setattr("sys.stdin", StringIO(json.dumps(event)))
    if env_nudge is not None:
        monkeypatch.setenv("CROSS_MODEL_NUDGE", env_nudge)
    else:
        monkeypatch.delenv("CROSS_MODEL_NUDGE", raising=False)
    if state_dir is not None:
        monkeypatch.setattr(
            MODULE, "state_path", lambda sid: state_dir / f"claude-nudge-{sid}"
        )
    MODULE.main()


# ---------------------------------------------------------------------------
# Env gate tests
# ---------------------------------------------------------------------------


class TestEnvGate:
    def test_env_gate_off_exits_zero(self, monkeypatch, tmp_path) -> None:
        """No CROSS_MODEL_NUDGE env var → immediate exit(0), no state file."""
        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), env_nudge=None, state_dir=tmp_path)
        assert exc_info.value.code == 0
        assert not list(tmp_path.glob("claude-nudge-*"))

    def test_env_gate_wrong_value_exits_zero(self, monkeypatch, tmp_path) -> None:
        """CROSS_MODEL_NUDGE=true (not '1') → immediate exit(0)."""
        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), env_nudge="true", state_dir=tmp_path)
        assert exc_info.value.code == 0
        assert not list(tmp_path.glob("claude-nudge-*"))


# ---------------------------------------------------------------------------
# Tool filter tests
# ---------------------------------------------------------------------------


class TestToolFilter:
    def test_non_bash_tool_exits_zero(self, monkeypatch, tmp_path) -> None:
        """Non-Bash tool name → exit(0), no counter increment."""
        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(tool="Read"), state_dir=tmp_path)
        assert exc_info.value.code == 0
        assert not list(tmp_path.glob("claude-nudge-*"))


# ---------------------------------------------------------------------------
# Counter logic tests
# ---------------------------------------------------------------------------


class TestCounter:
    def test_counter_increments_below_threshold(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        """First failure → count=1, no stdout output."""
        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out == ""
        state_file = tmp_path / "claude-nudge-test-session"
        assert state_file.read_text() == "1"

    def test_counter_reaches_threshold_nudges(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        """3rd failure → additionalContext JSON on stdout, counter resets to 0."""
        state_file = tmp_path / "claude-nudge-test-session"
        state_file.write_text("2")  # simulate 2 prior failures

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "/codex" in output["hookSpecificOutput"]["additionalContext"]

        assert state_file.read_text() == "0"

    def test_counter_resets_after_nudge(self, monkeypatch, tmp_path, capsys) -> None:
        """After nudge (counter reset to 0), next failure → count=1, no output."""
        state_file = tmp_path / "claude-nudge-test-session"
        state_file.write_text("0")  # just reset after a nudge

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert captured.out == ""
        assert state_file.read_text() == "1"

    def test_two_failures_no_output(self, monkeypatch, tmp_path, capsys) -> None:
        """2nd failure → count=2, still no output."""
        state_file = tmp_path / "claude-nudge-test-session"
        state_file.write_text("1")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert captured.out == ""
        assert state_file.read_text() == "2"


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_corrupt_state_file_resets_to_one(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        """Non-integer state file content → count defaults to 1, stderr warning."""
        state_file = tmp_path / "claude-nudge-test-session"
        state_file.write_text("not-a-number")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert captured.out == ""  # count=1 < threshold, no nudge
        assert "state file error" in captured.err


# ---------------------------------------------------------------------------
# Output structure tests
# ---------------------------------------------------------------------------


class TestOutputStructure:
    def test_output_json_structure(self, monkeypatch, tmp_path, capsys) -> None:
        """Verify exact hookSpecificOutput.additionalContext shape."""
        state_file = tmp_path / "claude-nudge-test-session"
        state_file.write_text("2")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, _event(), state_dir=tmp_path)
        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    "You've hit several failures. "
                    "Consider running /codex to get a second opinion from another model. "
                    "It can help spot assumptions you might be stuck on."
                ),
            }
        }


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_missing_session_id_uses_unknown(self, monkeypatch, tmp_path) -> None:
        """Event without session_id → state file uses 'unknown'."""
        event = {"hook_event_name": "PostToolUseFailure", "tool_name": "Bash"}

        with pytest.raises(SystemExit) as exc_info:
            _run_main(monkeypatch, event, state_dir=tmp_path)
        assert exc_info.value.code == 0

        state_file = tmp_path / "claude-nudge-unknown"
        assert state_file.exists()
        assert state_file.read_text() == "1"
