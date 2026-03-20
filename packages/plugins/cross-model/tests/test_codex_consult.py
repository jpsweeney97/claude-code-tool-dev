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
