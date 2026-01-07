"""Tests for common.py shared utilities."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from common import parse_markdown_table, count_table_rows


class TestParseMarkdownTable:
    """Tests for parse_markdown_table function."""

    def test_parses_simple_table(self):
        """Parses a simple markdown table with headers and rows."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| value1  | value2  |
| value3  | value4  |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["Header1"] == "value1"
        assert rows[0]["Header2"] == "value2"
        assert rows[1]["Header1"] == "value3"

    def test_returns_empty_for_no_table(self):
        """Returns empty list when no table present."""
        content = "Just some text without tables."
        rows = parse_markdown_table(content)
        assert rows == []

    def test_handles_table_with_extra_whitespace(self):
        """Handles cells with extra whitespace."""
        content = """\
|   Header1   |   Header2   |
|-------------|-------------|
|   value1    |   value2    |
"""
        rows = parse_markdown_table(content)
        assert rows[0]["Header1"] == "value1"


class TestCountTableRows:
    """Tests for count_table_rows function."""

    def test_counts_data_rows(self):
        """Counts only data rows, not header or separator."""
        content = """\
| Header |
|--------|
| row1   |
| row2   |
| row3   |
"""
        assert count_table_rows(content) == 3

    def test_returns_zero_for_no_table(self):
        """Returns 0 when no table present."""
        assert count_table_rows("No tables here") == 0

    def test_returns_zero_for_header_only(self):
        """Returns 0 when table has only header."""
        content = """\
| Header |
|--------|
"""
        assert count_table_rows(content) == 0
