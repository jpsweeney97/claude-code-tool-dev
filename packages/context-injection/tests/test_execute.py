"""Tests for the read execution pipeline."""

from __future__ import annotations

import pytest

from context_injection.execute import (
    BinaryFileError,
    ReadExcerpt,
    read_file_excerpt,
)
from context_injection.types import ReadSpec


def _read_spec(path: str, **overrides) -> ReadSpec:
    """Create a ReadSpec with defaults, overriding resolved_path."""
    defaults = dict(
        action="read",
        resolved_path=path,
        strategy="first_n",
        max_lines=40,
        max_chars=2000,
    )
    defaults.update(overrides)
    return ReadSpec(**defaults)


# --- ReadExcerpt type ---


class TestReadExcerpt:
    def test_construction(self) -> None:
        r = ReadExcerpt(text="a\n", total_lines=5, excerpt_range=[1, 1])
        assert r.text == "a\n"
        assert r.total_lines == 5
        assert r.excerpt_range == [1, 1]

    def test_frozen(self) -> None:
        r = ReadExcerpt(text="", total_lines=0, excerpt_range=None)
        with pytest.raises(AttributeError):
            r.text = "x"


# --- read_file_excerpt ---


class TestReadFileExcerpt:
    def test_first_n_basic(self, tmp_path) -> None:
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\nline4\nline5\n")
        result = read_file_excerpt(_read_spec(str(f), max_lines=3))
        assert result.text == "line1\nline2\nline3\n"
        assert result.total_lines == 5
        assert result.excerpt_range == [1, 3]

    def test_first_n_whole_file(self, tmp_path) -> None:
        """File shorter than max_lines returns entire file."""
        f = tmp_path / "short.py"
        f.write_text("a\nb\n")
        result = read_file_excerpt(_read_spec(str(f), max_lines=10))
        assert result.text == "a\nb\n"
        assert result.total_lines == 2
        assert result.excerpt_range == [1, 2]

    def test_centered_basic(self, tmp_path) -> None:
        f = tmp_path / "ten.py"
        f.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")
        result = read_file_excerpt(
            _read_spec(str(f), strategy="centered", max_lines=3, center_line=5),
        )
        assert result.excerpt_range == [4, 6]
        assert "line4" in result.text
        assert "line5" in result.text
        assert "line6" in result.text

    def test_centered_start_edge(self, tmp_path) -> None:
        """center_line=1 clamps window to beginning."""
        f = tmp_path / "ten.py"
        f.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")
        result = read_file_excerpt(
            _read_spec(str(f), strategy="centered", max_lines=3, center_line=1),
        )
        assert result.excerpt_range == [1, 3]

    def test_centered_end_edge(self, tmp_path) -> None:
        """center_line near end clamps window to last max_lines lines."""
        f = tmp_path / "ten.py"
        f.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")
        result = read_file_excerpt(
            _read_spec(str(f), strategy="centered", max_lines=3, center_line=10),
        )
        assert result.excerpt_range == [8, 10]

    def test_centered_beyond_end(self, tmp_path) -> None:
        """center_line > total_lines returns last max_lines lines."""
        f = tmp_path / "ten.py"
        f.write_text("\n".join(f"line{i}" for i in range(1, 11)) + "\n")
        result = read_file_excerpt(
            _read_spec(str(f), strategy="centered", max_lines=5, center_line=100),
        )
        assert result.excerpt_range == [6, 10]

    def test_binary_detection(self, tmp_path) -> None:
        """NUL byte in first 8192 bytes raises BinaryFileError."""
        f = tmp_path / "binary.dat"
        f.write_bytes(b"text\x00more")
        with pytest.raises(BinaryFileError):
            read_file_excerpt(_read_spec(str(f)))

    def test_binary_nul_beyond_8192_not_detected(self, tmp_path) -> None:
        """NUL byte beyond first 8192 bytes is not caught."""
        f = tmp_path / "large.txt"
        f.write_bytes(b"x" * 8192 + b"\x00rest\n")
        result = read_file_excerpt(_read_spec(str(f)))
        assert result.total_lines == 1

    def test_encoding_error(self, tmp_path) -> None:
        """Non-UTF-8 bytes raise UnicodeDecodeError."""
        f = tmp_path / "bad.txt"
        f.write_bytes(b"hello\xff\xfeworld\n")
        with pytest.raises(UnicodeDecodeError):
            read_file_excerpt(_read_spec(str(f)))

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            read_file_excerpt(_read_spec("/nonexistent/path.py"))

    def test_empty_file(self, tmp_path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("")
        result = read_file_excerpt(_read_spec(str(f)))
        assert result.text == ""
        assert result.total_lines == 0
        assert result.excerpt_range is None

    def test_no_trailing_newline(self, tmp_path) -> None:
        """File without trailing newline: excerpt adds trailing newline."""
        f = tmp_path / "no_nl.py"
        f.write_text("a\nb")
        result = read_file_excerpt(_read_spec(str(f), max_lines=10))
        assert result.total_lines == 2
        assert result.text == "a\nb\n"
        assert result.excerpt_range == [1, 2]
