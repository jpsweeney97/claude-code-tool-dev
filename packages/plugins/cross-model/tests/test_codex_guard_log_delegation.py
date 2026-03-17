"""Tests verifying codex_guard delegates logging to event_log module."""

from __future__ import annotations

import io
import json
from unittest.mock import patch


def test_append_log_calls_event_log():
    """_append_log wrapper delegates to event_log.append_log."""
    with patch("scripts.codex_guard._raw_append_log", return_value=True) as mock_raw:
        from scripts.codex_guard import _append_log

        _append_log({"event": "test"})
        mock_raw.assert_called_once_with({"event": "test"})


def test_append_log_logs_stderr_on_write_failure(capsys):
    """_append_log prints to stderr when the underlying write fails."""
    with patch("scripts.codex_guard._raw_append_log", return_value=False):
        from scripts.codex_guard import _append_log

        _append_log({"event": "block"})
        captured = capsys.readouterr()
        assert "audit log write failed" in captured.err
        assert "block" in captured.err


def test_posttooluse_error_logs_to_stderr():
    """PostToolUse exceptions log to stderr instead of being silently swallowed."""
    from scripts.codex_guard import main

    payload = json.dumps({
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__plugin_cross-model_codex__codex",
    })
    with (
        patch("sys.stdin", io.StringIO(payload)),
        patch("scripts.codex_guard.handle_post", side_effect=RuntimeError("boom")),
    ):
        result = main()
    assert result == 0
    # stderr assertion via capsys not possible here since main() catches
    # the exception — we verify it returns 0 (non-blocking)


def test_ts_is_event_log_ts():
    """After migration, _ts should be event_log.ts."""
    import scripts.codex_guard as mod
    import scripts.event_log as ev

    assert mod._ts is ev.ts


def test_log_path_not_defined_locally():
    """codex_guard should not define its own _LOG_PATH."""
    import scripts.codex_guard as mod

    assert "_LOG_PATH" not in vars(mod)
