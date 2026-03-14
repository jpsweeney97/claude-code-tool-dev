"""Tests for event_log shared module."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from unittest.mock import patch

from scripts.event_log import LOG_PATH, ts, append_log, session_id


class TestLogPath:
    def test_points_to_codex_events(self) -> None:
        assert LOG_PATH.name == ".codex-events.jsonl"
        assert ".claude" in str(LOG_PATH)


class TestTs:
    def test_format_utc_z_suffix(self) -> None:
        result = ts()
        assert result.endswith("Z")
        assert "T" in result
        # Second precision — no microseconds
        assert "." not in result

    def test_is_parseable(self) -> None:
        from datetime import datetime
        result = ts()
        dt = datetime.fromisoformat(result.replace("Z", "+00:00"))
        assert dt is not None


class TestAppendLog:
    def test_writes_json_line(self, tmp_path: Path) -> None:
        log_file = tmp_path / ".codex-events.jsonl"
        with patch("scripts.event_log.LOG_PATH", log_file):
            result = append_log({"event": "test", "value": 42})
        assert result is True
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "test"

    def test_returns_false_on_write_error(self, tmp_path: Path) -> None:
        # Patch to a directory that exists but file path is a dir
        dir_as_file = tmp_path / "adir"
        dir_as_file.mkdir()
        with patch("scripts.event_log.LOG_PATH", dir_as_file):
            result = append_log({"event": "test"})
        assert result is False

    def test_appends_not_overwrites(self, tmp_path: Path) -> None:
        log_file = tmp_path / ".codex-events.jsonl"
        with patch("scripts.event_log.LOG_PATH", log_file):
            append_log({"event": "first"})
            append_log({"event": "second"})
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_creates_log_with_private_permissions(self, tmp_path: Path) -> None:
        log_file = tmp_path / ".codex-events.jsonl"
        with patch("scripts.event_log.LOG_PATH", log_file):
            assert append_log({"event": "first"}) is True
        mode = stat.S_IMODE(log_file.stat().st_mode)
        assert mode == 0o600


class TestSessionId:
    def test_returns_value_from_env(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "abc-123"}):
            assert session_id() == "abc-123"

    def test_returns_none_for_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("CLAUDE_SESSION_ID", None)
            assert session_id() is None

    def test_returns_none_for_whitespace(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "   "}):
            assert session_id() is None

    def test_returns_none_for_empty(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": ""}):
            assert session_id() is None
