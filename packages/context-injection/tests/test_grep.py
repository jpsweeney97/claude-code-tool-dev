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
    build_context_ranges,
    build_evidence_blocks,
    filter_file,
    group_matches_by_file,
    read_line_range,
    run_grep,
)
from context_injection.types import GrepSpec


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


class TestBuildContextRanges:
    def test_single_match_with_context(self) -> None:
        result = build_context_ranges([5], context_lines=2, total_lines=10)
        assert result == [(3, 7)]

    def test_clamps_to_file_start(self) -> None:
        result = build_context_ranges([1], context_lines=2, total_lines=10)
        assert result == [(1, 3)]

    def test_clamps_to_file_end(self) -> None:
        result = build_context_ranges([10], context_lines=2, total_lines=10)
        assert result == [(8, 10)]

    def test_merges_overlapping_ranges(self) -> None:
        # [3-2, 3+2]=[1,5] and [5-2, 5+2]=[3,7] overlap -> [1, 7]
        result = build_context_ranges([3, 5], context_lines=2, total_lines=10)
        assert result == [(1, 7)]

    def test_merges_adjacent_ranges(self) -> None:
        # [3-2, 3+2]=[1,5] and [8-2, 8+2]=[6,10] -> adjacent (5+1==6) -> [1, 10]
        result = build_context_ranges([3, 8], context_lines=2, total_lines=20)
        assert result == [(1, 10)]

    def test_separate_ranges(self) -> None:
        # [3-2, 3+2]=[1,5] and [20-2, 20+2]=[18,22] -> not adjacent
        result = build_context_ranges([3, 20], context_lines=2, total_lines=30)
        assert result == [(1, 5), (18, 22)]

    def test_duplicate_match_lines_deduped(self) -> None:
        result = build_context_ranges([5, 5, 5], context_lines=2, total_lines=10)
        assert result == [(3, 7)]

    def test_zero_context(self) -> None:
        result = build_context_ranges([5], context_lines=0, total_lines=10)
        assert result == [(5, 5)]

    def test_empty_match_lines(self) -> None:
        assert build_context_ranges([], context_lines=2, total_lines=10) == []

    def test_zero_total_lines(self) -> None:
        assert build_context_ranges([1], context_lines=2, total_lines=0) == []

    def test_unsorted_input_produces_sorted_output(self) -> None:
        result = build_context_ranges([10, 3], context_lines=2, total_lines=20)
        assert result == [(1, 5), (8, 12)]

    def test_many_matches_merge_into_one(self) -> None:
        result = build_context_ranges([1, 2, 3, 4, 5], context_lines=0, total_lines=10)
        # Each has width 1, adjacent -> all merge into [1, 5]
        assert result == [(1, 5)]

    def test_single_line_file(self) -> None:
        result = build_context_ranges([1], context_lines=5, total_lines=1)
        assert result == [(1, 1)]


class TestGroupMatchesByFile:
    def test_groups_by_path(self) -> None:
        matches = [
            GrepRawMatch(path="a.py", line_number=1, line_text="x"),
            GrepRawMatch(path="b.py", line_number=5, line_text="y"),
            GrepRawMatch(path="a.py", line_number=3, line_text="z"),
        ]
        result = group_matches_by_file(matches)
        assert result == {"a.py": [1, 3], "b.py": [5]}

    def test_empty_input(self) -> None:
        assert group_matches_by_file([]) == {}

    def test_line_numbers_sorted_within_file(self) -> None:
        matches = [
            GrepRawMatch(path="a.py", line_number=10, line_text="x"),
            GrepRawMatch(path="a.py", line_number=2, line_text="y"),
            GrepRawMatch(path="a.py", line_number=5, line_text="z"),
        ]
        result = group_matches_by_file(matches)
        assert result["a.py"] == [2, 5, 10]


class TestFilterFile:
    def test_tracked_and_allowed(self) -> None:
        assert filter_file("src/main.py", {"src/main.py"}) is True

    def test_not_tracked(self) -> None:
        assert filter_file("untracked.py", {"other.py"}) is False

    def test_denied_directory(self) -> None:
        assert filter_file(".git/config", {".git/config"}) is False

    def test_denied_file_pattern(self) -> None:
        assert filter_file(".env", {".env"}) is False

    def test_denied_nested_directory(self) -> None:
        assert filter_file("src/.git/hooks/pre-commit", {"src/.git/hooks/pre-commit"}) is False

    def test_node_modules_denied(self) -> None:
        assert filter_file("node_modules/pkg/index.js", {"node_modules/pkg/index.js"}) is False

    def test_empty_git_files(self) -> None:
        assert filter_file("a.py", set()) is False


class TestReadLineRange:
    def test_reads_full_file(self, tmp_path) -> None:
        f = tmp_path / "a.py"
        f.write_text("line1\nline2\nline3\n")
        result = read_line_range(str(f), 1, 3)
        assert result == "line1\nline2\nline3\n"

    def test_reads_middle_range(self, tmp_path) -> None:
        f = tmp_path / "a.py"
        f.write_text("line1\nline2\nline3\nline4\nline5\n")
        result = read_line_range(str(f), 2, 4)
        assert result == "line2\nline3\nline4\n"

    def test_single_line(self, tmp_path) -> None:
        f = tmp_path / "a.py"
        f.write_text("line1\nline2\nline3\n")
        result = read_line_range(str(f), 2, 2)
        assert result == "line2\n"

    def test_range_beyond_file_returns_available(self, tmp_path) -> None:
        f = tmp_path / "a.py"
        f.write_text("line1\nline2\n")
        result = read_line_range(str(f), 1, 100)
        assert result == "line1\nline2\n"

    def test_file_not_found_raises(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            read_line_range(str(tmp_path / "missing.py"), 1, 1)

    def test_binary_file_raises(self, tmp_path) -> None:
        f = tmp_path / "binary.bin"
        f.write_bytes(b"hello\x00world")
        with pytest.raises(ValueError, match="Binary file"):
            read_line_range(str(f), 1, 1)

    def test_non_utf8_raises(self, tmp_path) -> None:
        f = tmp_path / "latin.txt"
        f.write_bytes(b"caf\xe9\n")
        with pytest.raises(UnicodeDecodeError):
            read_line_range(str(f), 1, 1)


class TestBuildEvidenceBlocks:
    @staticmethod
    def _make_spec(**overrides) -> GrepSpec:
        defaults = {
            "action": "grep",
            "pattern": "MyClass",
            "strategy": "match_context",
            "max_lines": 40,
            "max_chars": 2000,
            "context_lines": 2,
            "max_ranges": 5,
        }
        defaults.update(overrides)
        return GrepSpec(**defaults)

    def test_happy_path_single_file(self, tmp_path) -> None:
        f = tmp_path / "main.py"
        f.write_text("import os\nclass MyClass:\n    pass\ndef foo():\n    return 1\n")
        spec = self._make_spec()
        grouped = {"main.py": [2]}
        git_files = {"main.py"}

        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert len(blocks) == 1
        assert blocks[0].path == "main.py"
        assert blocks[0].start_line == 1  # max(1, 2-2)=1
        assert "# main.py:1-4" in blocks[0].text
        assert "class MyClass:" in blocks[0].text
        assert match_count == 1
        assert len(grep_matches) == 1
        assert grep_matches[0].path_display == "main.py"
        assert grep_matches[0].total_lines == 5
        assert grep_matches[0].ranges == [[1, 4]]

    def test_multi_file(self, tmp_path) -> None:
        (tmp_path / "a.py").write_text("class MyClass:\n    pass\n")
        (tmp_path / "b.py").write_text("# comment\nfrom a import MyClass\n# end\n")
        spec = self._make_spec()
        grouped = {"a.py": [1], "b.py": [2]}
        git_files = {"a.py", "b.py"}

        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert len(blocks) == 2
        assert match_count == 2  # 1 match per file
        assert len(grep_matches) == 2
        # Files processed in sorted order
        assert grep_matches[0].path_display == "a.py"
        assert grep_matches[1].path_display == "b.py"

    def test_untracked_file_filtered(self, tmp_path) -> None:
        (tmp_path / "untracked.py").write_text("class MyClass:\n")
        spec = self._make_spec()
        grouped = {"untracked.py": [1]}
        git_files = set()  # not tracked

        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert blocks == []
        assert match_count == 0
        assert grep_matches == []

    def test_denied_file_filtered(self, tmp_path) -> None:
        (tmp_path / ".env").write_text("SECRET=MyClass\n")
        spec = self._make_spec()
        grouped = {".env": [1]}
        git_files = {".env"}  # tracked but denied

        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert blocks == []
        assert match_count == 0

    def test_binary_file_skipped(self, tmp_path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"class MyClass\x00binary")
        spec = self._make_spec()
        grouped = {"data.bin": [1]}
        git_files = {"data.bin"}

        blocks, match_count, grep_matches, _ = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert blocks == []
        assert match_count == 0

    def test_missing_file_skipped(self, tmp_path) -> None:
        spec = self._make_spec()
        grouped = {"gone.py": [1]}
        git_files = {"gone.py"}  # tracked but deleted (TOCTOU)

        blocks, match_count, grep_matches, _ = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert blocks == []
        assert match_count == 0

    def test_empty_grouped_returns_empty(self, tmp_path) -> None:
        spec = self._make_spec()
        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            {}, spec, str(tmp_path), set(),
        )
        assert blocks == []
        assert match_count == 0
        assert grep_matches == []
        assert redactions == 0

    def test_multiple_ranges_same_file(self, tmp_path) -> None:
        # 20 lines, matches at lines 1 and 20 — separate ranges with context=2
        content = "\n".join(f"line {i}" for i in range(1, 21)) + "\n"
        (tmp_path / "big.py").write_text(content)
        spec = self._make_spec(context_lines=2)
        grouped = {"big.py": [1, 20]}
        git_files = {"big.py"}

        blocks, match_count, grep_matches, _ = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        assert len(blocks) == 2  # Two separate ranges
        assert match_count == 2
        assert grep_matches[0].ranges == [[1, 3], [18, 20]]

    def test_redaction_applied_to_config_file(self, tmp_path) -> None:
        (tmp_path / "config.env").write_text("API_KEY=sk-1234567890abcdef\nMY_VAR=MyClass\n")
        spec = self._make_spec()
        grouped = {"config.env": [2]}
        git_files = {"config.env"}

        blocks, match_count, grep_matches, redactions = build_evidence_blocks(
            grouped, spec, str(tmp_path), git_files,
        )

        # ENV redactor should redact the API_KEY value
        assert len(blocks) >= 1, "Expected blocks for config.env (not suppressed)"
        assert "[REDACTED" in blocks[0].text
        assert redactions > 0
