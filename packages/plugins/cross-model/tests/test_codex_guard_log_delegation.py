"""Tests verifying codex_guard delegates logging to event_log module."""

from __future__ import annotations

from unittest.mock import patch


def test_append_log_calls_event_log():
    """_append_log wrapper delegates to event_log.append_log."""
    with patch("scripts.codex_guard._raw_append_log") as mock_raw:
        from scripts.codex_guard import _append_log

        _append_log({"event": "test"})
        mock_raw.assert_called_once_with({"event": "test"})


def test_ts_is_event_log_ts():
    """After migration, _ts should be event_log.ts."""
    import scripts.codex_guard as mod
    import scripts.event_log as ev

    assert mod._ts is ev.ts


def test_log_path_not_defined_locally():
    """codex_guard should not define its own _LOG_PATH."""
    import scripts.codex_guard as mod

    assert "_LOG_PATH" not in vars(mod)
