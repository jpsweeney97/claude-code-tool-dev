"""Tests for truncation: read excerpts and grep evidence blocks."""

from __future__ import annotations

import pytest

from context_injection.enums import TruncationReason
from context_injection.truncate import (
    EvidenceBlock,
    TruncateBlocksResult,
    TruncateResult,
    truncate_blocks,
    truncate_excerpt,
)


# --- Type tests ---


class TestTruncateResult:
    def test_construction(self) -> None:
        r = TruncateResult(
            text="abc", truncated=False, reason=None,
            original_chars=3, original_lines=1,
        )
        assert r.text == "abc"
        assert r.truncated is False
        assert r.reason is None

    def test_frozen(self) -> None:
        r = TruncateResult(text="x", truncated=False, reason=None, original_chars=1, original_lines=1)
        with pytest.raises(AttributeError):
            r.text = "y"


class TestEvidenceBlock:
    def test_construction(self) -> None:
        b = EvidenceBlock(text="line1\nline2\n", start_line=10, path="src/app.py", end_line=11)
        assert b.text == "line1\nline2\n"
        assert b.start_line == 10
        assert b.path == "src/app.py"
        assert b.end_line == 11

    def test_nullable_fields(self) -> None:
        b = EvidenceBlock(text="x", start_line=None, path=None, end_line=None)
        assert b.start_line is None

    def test_all_or_nothing_rejects_partial(self) -> None:
        with pytest.raises(ValueError, match="all-None or all-present"):
            EvidenceBlock(text="x", start_line=1, path=None)
        with pytest.raises(ValueError, match="all-None or all-present"):
            EvidenceBlock(text="x", start_line=None, path="f.py", end_line=5)
        with pytest.raises(ValueError, match="all-None or all-present"):
            EvidenceBlock(text="x", start_line=1, path="f.py")

    def test_end_line_gte_start_line(self) -> None:
        with pytest.raises(ValueError, match="end_line must be >= start_line"):
            EvidenceBlock(text="x", start_line=5, path="f.py", end_line=3)


class TestTruncateBlocksResult:
    def test_construction(self) -> None:
        r = TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)
        assert r.blocks == ()
        assert r.dropped_blocks == 0

    def test_frozen(self) -> None:
        r = TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)
        with pytest.raises(AttributeError):
            r.truncated = True


# --- truncate_excerpt ---


class TestTruncateExcerpt:
    def test_no_truncation(self) -> None:
        result = truncate_excerpt(text="a\nb\n", max_chars=100, max_lines=10)
        assert result.text == "a\nb\n"
        assert result.truncated is False
        assert result.reason is None

    def test_empty_input(self) -> None:
        result = truncate_excerpt(text="", max_chars=100, max_lines=10)
        assert result.text == ""
        assert result.truncated is False

    def test_line_cap_hit(self) -> None:
        result = truncate_excerpt(text="a\nb\nc\n", max_chars=1000, max_lines=2)
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_LINES
        assert "a\n" in result.text
        assert "b\n" in result.text
        assert "[truncated]\n" in result.text
        assert "c\n" not in result.text.replace("[truncated]\n", "")

    def test_char_cap_hit(self) -> None:
        text = "abcdefghij\n" * 5  # 55 chars
        result = truncate_excerpt(text=text, max_chars=35, max_lines=100)
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_CHARS
        assert "[truncated]\n" in result.text

    def test_both_caps_reports_line_first(self) -> None:
        """max_lines checked first -> reason=MAX_LINES even if char cap also binds."""
        text = "a" * 50 + "\n" + "b" * 50 + "\n" + "c" * 50 + "\n"
        result = truncate_excerpt(text=text, max_chars=80, max_lines=1)
        assert result.reason == TruncationReason.MAX_LINES

    def test_marker_preserved(self) -> None:
        """[REDACTED:value] on last kept line is not split."""
        text = "line1\nKEY=[REDACTED:value]\nline3\n"
        result = truncate_excerpt(text=text, max_chars=1000, max_lines=2)
        assert "[REDACTED:value]" in result.text

    def test_single_char_over(self) -> None:
        """Text barely exceeds budget -> truncation."""
        text = "abcdef\n"  # 7 chars
        # Budget: 18 - 12 = 6 chars. "abcdef\n" = 7 chars. Exceeds by 1.
        result = truncate_excerpt(text=text, max_chars=18, max_lines=100)
        assert result.truncated is True

    def test_trailing_newline_two_lines(self) -> None:
        """'a\\nb\\n' = 2 lines via splitlines()."""
        result = truncate_excerpt(text="a\nb\n", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_crlf_line_endings(self) -> None:
        """\\r\\n treated as single line break by splitlines()."""
        result = truncate_excerpt(text="a\r\nb\r\n", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_no_trailing_newline(self) -> None:
        result = truncate_excerpt(text="a\nb", max_chars=1000, max_lines=2)
        assert result.truncated is False
        assert result.original_lines == 2

    def test_max_lines_zero(self) -> None:
        result = truncate_excerpt(text="content\n", max_chars=100, max_lines=0)
        assert result.text == ""
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_LINES

    def test_max_chars_below_indicator(self) -> None:
        result = truncate_excerpt(text="content\n", max_chars=5, max_lines=100)
        assert result.text == ""
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_CHARS

    @pytest.mark.parametrize("max_chars", [12, 13, 14, 15, 16, 17, 18, 19, 20])
    def test_small_char_budgets(self, max_chars: int) -> None:
        """Various small budgets: output must not exceed max_chars."""
        result = truncate_excerpt(text="abcdefghij\nklmnopqrst\n", max_chars=max_chars, max_lines=100)
        assert len(result.text) <= max_chars

    def test_indicator_char_reservation(self) -> None:
        """Content + indicator must fit within max_chars."""
        text = "short\n"  # 6 chars content
        # Budget: 18 - 12 = 6. "short\n" = 6 chars. Fits exactly -> no truncation.
        result = truncate_excerpt(text=text, max_chars=18, max_lines=100)
        assert result.truncated is False

    def test_originals_reported(self) -> None:
        result = truncate_excerpt(text="abc\ndef\nghi\n", max_chars=1000, max_lines=2)
        assert result.original_lines == 3
        assert result.original_chars == 12


# --- truncate_blocks ---


class TestTruncateBlocks:
    def _block(self, text: str, start: int = 1, path: str = "f.py", end: int = 1) -> EvidenceBlock:
        return EvidenceBlock(text=text, start_line=start, path=path, end_line=end)

    def test_no_truncation(self) -> None:
        blocks = [self._block("a\n"), self._block("b\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=100)
        assert len(result.blocks) == 2
        assert result.truncated is False
        assert result.dropped_blocks == 0

    def test_empty_input(self) -> None:
        result = truncate_blocks(blocks=[], max_ranges=10, max_chars=1000, max_lines=100)
        assert result.blocks == ()
        assert result.truncated is False

    def test_max_ranges_exceeded(self) -> None:
        blocks = [self._block("a\n"), self._block("b\n"), self._block("c\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=2, max_chars=1000, max_lines=100)
        assert len(result.blocks) == 2
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_RANGES
        assert result.dropped_blocks == 1

    def test_max_lines_exceeded(self) -> None:
        blocks = [self._block("a\nb\n"), self._block("c\nd\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=3)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_LINES
        assert result.dropped_blocks == 1

    def test_max_chars_exceeded(self) -> None:
        blocks = [self._block("ab\n"), self._block("cd\n")]
        # budget = 16 - 12 = 4. block1 "ab\n" = 3 chars. block2 "cd\n" = 3. cumulative 6 > 4.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=16, max_lines=100)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_CHARS

    def test_block_atomicity(self) -> None:
        """Partial block dropped entirely."""
        blocks = [self._block("a\n"), self._block("bcdefghij\n")]  # 10 chars
        # budget = 20 - 12 = 8. block1 = 2, block2 = 10. 2 + 10 > 8.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=20, max_lines=100)
        assert len(result.blocks) == 1

    def test_single_oversized_block(self) -> None:
        blocks = [self._block("a" * 100 + "\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=50, max_lines=100)
        assert len(result.blocks) == 0
        assert result.truncated is True
        assert result.dropped_blocks == 1

    def test_ranges_ok_but_chars_forces_drop(self) -> None:
        blocks = [self._block("ab\n"), self._block("cd\n"), self._block("ef\n")]
        # budget = 19 - 12 = 7. blocks: 3, 3, 3. cumulative: 3, 6, 9 > 7.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=19, max_lines=100)
        assert len(result.blocks) == 2
        assert result.reason == TruncationReason.MAX_CHARS

    def test_lines_force_drop_not_chars(self) -> None:
        blocks = [self._block("a\nb\n"), self._block("c\n")]
        # block1 = 2 lines, block2 = 1 line. 2 + 1 = 3 > max_lines=2.
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=1000, max_lines=2)
        assert len(result.blocks) == 1
        assert result.reason == TruncationReason.MAX_LINES

    def test_max_chars_below_indicator(self) -> None:
        """max_chars < indicator length drops all blocks immediately."""
        blocks = [self._block("ab\n")]
        result = truncate_blocks(blocks=blocks, max_ranges=10, max_chars=5, max_lines=100)
        assert len(result.blocks) == 0
        assert result.truncated is True
        assert result.reason == TruncationReason.MAX_CHARS
        assert result.dropped_blocks == 1

    def test_dropped_blocks_count(self) -> None:
        blocks = [self._block("a\n")] * 5
        result = truncate_blocks(blocks=blocks, max_ranges=2, max_chars=1000, max_lines=100)
        assert result.dropped_blocks == 3
