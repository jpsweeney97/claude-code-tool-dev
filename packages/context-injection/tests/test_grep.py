"""Tests for grep subprocess runner and output parsing."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from context_injection.grep import (
    GrepRawMatch,
    GrepTimeoutError,
    RgNotFoundError,
    _parse_rg_json_lines,
    run_grep,
)


class TestParseRgJsonLines:
    def test_extracts_match_records(self) -> None:
        lines = [
            '{"type":"begin","data":{"path":{"text":"src/main.py"}}}',
            '{"type":"match","data":{"path":{"text":"src/main.py"},"lines":{"text":"class MyClass:\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}',
            '{"type":"match","data":{"path":{"text":"src/main.py"},"lines":{"text":"    return MyClass()\\n"},"line_number":5,"absolute_offset":36,"submatches":[]}}',
            '{"type":"end","data":{"path":{"text":"src/main.py"},"binary_offset":null,"stats":{}}}',
            '{"type":"summary","data":{}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert len(result) == 2
        assert result[0] == GrepRawMatch(
            path="src/main.py", line_number=1, line_text="class MyClass:",
        )
        assert result[1] == GrepRawMatch(
            path="src/main.py", line_number=5, line_text="    return MyClass()",
        )

    def test_skips_malformed_json(self) -> None:
        lines = [
            "not json at all",
            '{"type":"match","data":{"path":{"text":"a.py"},"lines":{"text":"x\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert len(result) == 1
        assert result[0].path == "a.py"

    def test_skips_records_with_missing_fields(self) -> None:
        lines = [
            '{"type":"match","data":{"path":{},"lines":{"text":"x\\n"}}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert len(result) == 0

    def test_empty_input(self) -> None:
        assert _parse_rg_json_lines([]) == []

    def test_strips_dot_slash_prefix(self) -> None:
        lines = [
            '{"type":"match","data":{"path":{"text":"./src/a.py"},"lines":{"text":"x\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert result[0].path == "src/a.py"

    def test_strips_trailing_newline_from_line_text(self) -> None:
        lines = [
            '{"type":"match","data":{"path":{"text":"a.py"},"lines":{"text":"hello world\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert result[0].line_text == "hello world"

    def test_multi_file_matches(self) -> None:
        lines = [
            '{"type":"begin","data":{"path":{"text":"a.py"}}}',
            '{"type":"match","data":{"path":{"text":"a.py"},"lines":{"text":"x\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}',
            '{"type":"end","data":{"path":{"text":"a.py"},"binary_offset":null,"stats":{}}}',
            '{"type":"begin","data":{"path":{"text":"b.py"}}}',
            '{"type":"match","data":{"path":{"text":"b.py"},"lines":{"text":"y\\n"},"line_number":3,"absolute_offset":0,"submatches":[]}}',
            '{"type":"end","data":{"path":{"text":"b.py"},"binary_offset":null,"stats":{}}}',
        ]
        result = _parse_rg_json_lines(lines)
        assert len(result) == 2
        assert result[0].path == "a.py"
        assert result[1].path == "b.py"

    def test_skips_blank_lines(self) -> None:
        lines = ["", "  ", '{"type":"match","data":{"path":{"text":"a.py"},"lines":{"text":"x\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}']
        result = _parse_rg_json_lines(lines)
        assert len(result) == 1


class TestRunGrep:
    def test_returns_parsed_matches(self, tmp_path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            '{"type":"match","data":{"path":{"text":"a.py"},"lines":{"text":"class MyClass:\\n"},"line_number":1,"absolute_offset":0,"submatches":[]}}\n'
        )
        with patch("context_injection.grep.subprocess.run", return_value=mock_result) as mock_run:
            result = run_grep("MyClass", str(tmp_path))

        assert len(result) == 1
        assert result[0] == GrepRawMatch(path="a.py", line_number=1, line_text="class MyClass:")
        # Verify rg was called with correct args
        call_args = mock_run.call_args
        assert call_args[0][0] == ["rg", "--json", "--fixed-strings", "-n", "--no-heading", "MyClass"]
        assert call_args[1]["cwd"] == str(tmp_path)
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True

    def test_rg_not_found_raises(self, tmp_path) -> None:
        with patch("context_injection.grep.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RgNotFoundError, match="not found on PATH"):
                run_grep("MyClass", str(tmp_path))

    def test_timeout_raises(self, tmp_path) -> None:
        with patch(
            "context_injection.grep.subprocess.run",
            side_effect=subprocess.TimeoutExpired("rg", 5.0),
        ):
            with pytest.raises(GrepTimeoutError, match="timed out"):
                run_grep("MyClass", str(tmp_path))

    def test_error_exit_code_returns_empty(self, tmp_path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 2  # rg error
        with patch("context_injection.grep.subprocess.run", return_value=mock_result):
            result = run_grep("MyClass", str(tmp_path))
        assert result == []

    def test_no_matches_exit_code_1_returns_empty(self, tmp_path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("context_injection.grep.subprocess.run", return_value=mock_result):
            result = run_grep("MyClass", str(tmp_path))
        assert result == []

    def test_custom_timeout(self, tmp_path) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("context_injection.grep.subprocess.run", return_value=mock_result) as mock_run:
            run_grep("MyClass", str(tmp_path), timeout=10.0)
        assert mock_run.call_args[1]["timeout"] == 10.0
