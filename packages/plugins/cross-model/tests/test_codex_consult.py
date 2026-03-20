"""Tests for codex_consult consultation adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestParseInput:
    """Phase A: structural parse of input JSON."""

    def test_valid_new_conversation(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "explain this code"}))
        result = _parse_input(f)
        assert result["prompt"] == "explain this code"
        assert result["sandbox"] == "read-only"
        assert result["thread_id"] is None

    def test_valid_resume(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({
            "prompt": "follow up question",
            "thread_id": "thr_abc123",
        }))
        result = _parse_input(f)
        assert result["thread_id"] == "thr_abc123"

    def test_defaults(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test"}))
        result = _parse_input(f)
        assert result["sandbox"] == "read-only"
        assert result["reasoning_effort"] == "xhigh"
        assert result["model"] is None

    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text("not json")
        with pytest.raises(ConsultationError, match="invalid JSON"):
            _parse_input(f)

    def test_missing_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"model": "gpt-5"}))
        with pytest.raises(ConsultationError, match="prompt is required"):
            _parse_input(f)

    def test_non_string_prompt_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": ["not", "a", "string"]}))
        with pytest.raises(ConsultationError, match="prompt must be string"):
            _parse_input(f)

    def test_invalid_reasoning_effort_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        f = tmp_path / "input.json"
        f.write_text(json.dumps({"prompt": "test", "reasoning_effort": "ultra"}))
        with pytest.raises(ConsultationError, match="invalid reasoning_effort"):
            _parse_input(f)

    def test_missing_file_errors(self, tmp_path: Path) -> None:
        from scripts.codex_consult import _parse_input, ConsultationError
        with pytest.raises(ConsultationError, match="input read failed"):
            _parse_input(tmp_path / "missing.json")


import subprocess


class TestBuildCommand:
    """Build codex exec command for new and resume conversations."""

    def test_new_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="explain this", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert cmd[:3] == ["codex", "exec", "--json"]
        assert "-s" in cmd
        idx = cmd.index("-s")
        assert cmd[idx + 1] == "read-only"
        assert "--" in cmd
        assert cmd[-1] == "explain this"

    def test_resume_conversation(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="follow up", thread_id="thr_abc", sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert cmd[:4] == ["codex", "exec", "resume", "thr_abc"]
        assert "--json" in cmd
        assert cmd[-1] == "follow up"

    def test_includes_model_when_set(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model="o3", reasoning_effort="xhigh")
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "o3"

    def test_omits_model_when_none(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        assert "-m" not in cmd

    def test_includes_reasoning_effort(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="test", thread_id=None, sandbox="read-only", model=None, reasoning_effort="high")
        assert "-c" in cmd
        idx = cmd.index("-c")
        assert cmd[idx + 1] == "model_reasoning_effort=high"

    def test_dash_prompt_protected(self) -> None:
        from scripts.codex_consult import _build_command
        cmd = _build_command(prompt="--dangerous-looking", thread_id=None, sandbox="read-only", model=None, reasoning_effort="xhigh")
        dd_idx = cmd.index("--")
        assert cmd[dd_idx + 1] == "--dangerous-looking"


class TestCheckCodexVersion:
    """Version check requires >= 0.111.0."""

    def test_valid_version_passes(self) -> None:
        from scripts.codex_consult import _check_codex_version
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.116.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            _check_codex_version()

    def test_old_version_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch, MagicMock
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0, stdout="codex 0.100.0\n")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="requires codex"):
                _check_codex_version()

    def test_missing_codex_errors(self) -> None:
        from scripts.codex_consult import _check_codex_version, ConsultationError
        from unittest.mock import patch
        with patch("scripts.codex_consult.subprocess") as mock_sub:
            mock_sub.run.side_effect = FileNotFoundError("codex not found")
            mock_sub.TimeoutExpired = subprocess.TimeoutExpired
            with pytest.raises(ConsultationError, match="codex not found"):
                _check_codex_version()


class TestParseJsonl:
    """JSONL parsing extracts continuation_id, response, usage."""

    def _make_jsonl(self, *events: dict) -> str:
        return "\n".join(json.dumps(e) for e in events)

    def test_extracts_thread_id(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.started"}, {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_last_thread_id_wins(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_old"}, {"type": "thread.started", "thread_id": "thr_new"}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_new"

    def test_extracts_agent_message(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "The answer is 42."}}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["response_text"] == "The answer is 42."

    def test_concatenates_multiple_messages(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 1."}}, {"type": "item.completed", "item": {"type": "agent_message", "text": "Part 2."}}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert "Part 1." in result["response_text"]
        assert "Part 2." in result["response_text"]

    def test_extracts_token_usage(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 50}})
        result = _parse_jsonl(stdout)
        assert result["token_usage"] == {"input_tokens": 100, "output_tokens": 50}

    def test_captures_runtime_failures(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "thread.started", "thread_id": "thr_001"}, {"type": "turn.failed", "error": "model overloaded"})
        result = _parse_jsonl(stdout)
        assert "model overloaded" in result["runtime_failures"]

    def test_no_usable_events_errors(self) -> None:
        from scripts.codex_consult import _parse_jsonl, ConsultationError
        with pytest.raises(ConsultationError, match="no usable JSONL events"):
            _parse_jsonl("")

    def test_skips_malformed_lines(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = "not json\n" + json.dumps({"type": "thread.started", "thread_id": "thr_001"}) + "\n" + json.dumps({"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] == "thr_001"

    def test_null_thread_id_on_missing_event(self) -> None:
        from scripts.codex_consult import _parse_jsonl
        stdout = self._make_jsonl({"type": "turn.started"}, {"type": "turn.completed", "usage": {}})
        result = _parse_jsonl(stdout)
        assert result["continuation_id"] is None
