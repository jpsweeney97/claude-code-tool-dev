"""Tests for session_start hook script."""

import json
import tempfile
from pathlib import Path



def test_session_start_records_timestamp():
    """SessionStart hook records start timestamp."""
    from scripts.session_start import handle_session_start

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = {
            "session_id": "test-123",
            "cwd": tmpdir,
            "hook_event_name": "SessionStart",
        }

        result = handle_session_start(input_data, state_dir=Path(tmpdir))

        assert result["success"] is True

        # Check state file was created with session_id in filename
        state_file = Path(tmpdir) / "session_test-123.json"
        assert state_file.exists()

        state = json.loads(state_file.read_text())
        assert "start_time" in state
        assert state["session_id"] == "test-123"


def test_session_start_captures_cwd():
    """SessionStart hook captures working directory."""
    from scripts.session_start import handle_session_start

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = {
            "session_id": "test-456",
            "cwd": tmpdir,
            "hook_event_name": "SessionStart",
        }

        handle_session_start(input_data, state_dir=Path(tmpdir))

        state_file = Path(tmpdir) / "session_test-456.json"
        state = json.loads(state_file.read_text())
        assert state["cwd"] == tmpdir


def test_session_start_captures_git_info():
    """SessionStart hook captures git branch and commit when in git repo."""
    from scripts.session_start import get_git_info

    # Test in the current working directory (which is a git repo)
    git_info = get_git_info(".")
    # May or may not have git info depending on environment
    assert "branch" in git_info
    assert "commit" in git_info


def test_session_start_handles_non_git_directory():
    """SessionStart hook handles non-git directories gracefully."""
    from scripts.session_start import get_git_info

    with tempfile.TemporaryDirectory() as tmpdir:
        git_info = get_git_info(tmpdir)
        assert git_info["branch"] is None
        assert git_info["commit"] is None


def test_session_start_uses_default_state_dir():
    """SessionStart hook uses default state directory when not specified."""
    from scripts.session_start import get_state_dir

    state_dir = get_state_dir()
    expected = Path.home() / ".claude" / "session-log" / "state"
    assert state_dir == expected


def test_session_start_handles_missing_session_id():
    """SessionStart hook handles missing session_id gracefully."""
    from scripts.session_start import handle_session_start

    with tempfile.TemporaryDirectory() as tmpdir:
        input_data = {
            "cwd": tmpdir,
            "hook_event_name": "SessionStart",
        }

        result = handle_session_start(input_data, state_dir=Path(tmpdir))

        assert result["success"] is True

        state_file = Path(tmpdir) / "session_unknown.json"
        state = json.loads(state_file.read_text())
        assert state["session_id"] == "unknown"
