"""Truncation for read excerpts and grep evidence blocks.

Dual-cap truncation: max_lines then max_chars, at line boundaries only.
Marker-safe: never splits [REDACTED:*] markers. Block atomicity for grep.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from context_injection.enums import TruncationReason

_TRUNCATED_INDICATOR = "[truncated]\n"
_INDICATOR_LEN = len(_TRUNCATED_INDICATOR)


@dataclass(frozen=True)
class TruncateResult:
    """Result of truncate_excerpt()."""

    text: str
    truncated: bool
    reason: TruncationReason | None
    original_chars: int
    original_lines: int


@dataclass(frozen=True)
class EvidenceBlock:
    """A single grep evidence block (atomic unit for truncation).

    Location fields (path, start_line, end_line) are all-or-nothing:
    either all three are present (specific file range) or all three are None
    (no file location). ``__post_init__`` enforces this invariant.
    """

    text: str
    start_line: int | None
    path: str | None
    end_line: int | None = None

    def __post_init__(self) -> None:
        location = (self.path, self.start_line, self.end_line)
        present = sum(v is not None for v in location)
        if present not in (0, 3):
            raise ValueError(
                f"EvidenceBlock location fields must be all-None or all-present. "
                f"Got: path={self.path!r}, start_line={self.start_line!r}, "
                f"end_line={self.end_line!r}"
            )
        if self.start_line is not None and self.end_line is not None:
            if self.end_line < self.start_line:
                raise ValueError(
                    f"end_line must be >= start_line. "
                    f"Got: start_line={self.start_line}, end_line={self.end_line}"
                )


@dataclass(frozen=True)
class TruncateBlocksResult:
    """Result of truncate_blocks()."""

    blocks: tuple[EvidenceBlock, ...]
    truncated: bool
    reason: TruncationReason | None
    dropped_blocks: int


def truncate_excerpt(
    *, text: str, max_chars: int, max_lines: int,
) -> TruncateResult:
    """Truncate a read excerpt. No partial source lines. Marker-safe.

    Marker safety: achieved by whole-line truncation. Since lines are atomic
    units (never cut mid-line), [REDACTED:value] markers within a line cannot
    be split. No explicit marker detection needed.

    Appends '[truncated]\\n' if truncated. Indicator doesn't count against
    max_lines but DOES count against max_chars (reserve _INDICATOR_LEN chars).
    Indicator space is always reserved from max_chars, even on the no-truncation
    fast path, so callers can rely on room for the indicator if they later
    need to append one.
    Precedence: max_lines then max_chars. Reports first cap that removes content.
    Line counting: str.splitlines() — trailing newlines do not consume budget.
    Line endings: splitlines()/join normalizes \\r\\n to \\n in truncated output.
    Non-truncated text is returned verbatim.
    """
    if not text:
        return TruncateResult(
            text="", truncated=False, reason=None,
            original_chars=0, original_lines=0,
        )

    lines = text.splitlines()
    original_lines = len(lines)
    original_chars = len(text)

    # Zero-budget edge cases
    if max_lines <= 0:
        return TruncateResult(
            text="", truncated=True, reason=TruncationReason.MAX_LINES,
            original_chars=original_chars, original_lines=original_lines,
        )
    if max_chars < _INDICATOR_LEN:
        return TruncateResult(
            text="", truncated=True, reason=TruncationReason.MAX_CHARS,
            original_chars=original_chars, original_lines=original_lines,
        )

    # No truncation needed — reserve indicator space so output never exceeds
    # max_chars even if truncation is triggered on the char-cap path below.
    char_budget = max_chars - _INDICATOR_LEN
    if original_lines <= max_lines and original_chars <= char_budget:
        return TruncateResult(
            text=text, truncated=False, reason=None,
            original_chars=original_chars, original_lines=original_lines,
        )

    # Truncation needed
    reason: TruncationReason | None = None

    # Step 1: line cap
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        reason = TruncationReason.MAX_LINES

    # Step 2: char cap (at line boundaries, reuse reserved budget)
    kept: list[str] = []
    cumulative = 0
    for line in lines:
        line_len = len(line) + 1  # +1 for \n
        if cumulative + line_len > char_budget:
            if reason is None:
                reason = TruncationReason.MAX_CHARS
            break
        cumulative += line_len
        kept.append(line)

    # Build output with indicator
    if kept:
        result_text = "\n".join(kept) + "\n" + _TRUNCATED_INDICATOR
    else:
        result_text = _TRUNCATED_INDICATOR

    return TruncateResult(
        text=result_text, truncated=True, reason=reason,
        original_chars=original_chars, original_lines=original_lines,
    )


def truncate_blocks(
    *,
    blocks: Sequence[EvidenceBlock],
    max_ranges: int,
    max_chars: int,
    max_lines: int,
) -> TruncateBlocksResult:
    """Truncate grep evidence blocks. Each block is atomic — never cut inside.

    Prefix-ordered: iterate in order, accumulate counts, stop when any cap exceeded.
    Precedence: max_ranges then max_lines then max_chars.
    Reports first cap that causes a block to be dropped.

    Indicator reservation: _INDICATOR_LEN chars reserved from max_chars budget.
    This function does not append an indicator itself — the caller appends
    '[truncated]' to the formatted output when truncated=True. The reservation
    ensures the caller's indicator fits within the overall char budget.
    """
    if not blocks:
        return TruncateBlocksResult(blocks=(), truncated=False, reason=None, dropped_blocks=0)

    # Budget too small for even the indicator — drop everything immediately.
    if max_chars < _INDICATOR_LEN:
        return TruncateBlocksResult(
            blocks=(), truncated=True, reason=TruncationReason.MAX_CHARS,
            dropped_blocks=len(blocks),
        )

    # Quick check: does everything fit? Reserve indicator space in char budget.
    char_budget = max_chars - _INDICATOR_LEN
    total_lines = sum(len(b.text.splitlines()) for b in blocks)
    total_chars = sum(len(b.text) for b in blocks)
    if len(blocks) <= max_ranges and total_lines <= max_lines and total_chars <= char_budget:
        return TruncateBlocksResult(
            blocks=tuple(blocks), truncated=False, reason=None, dropped_blocks=0,
        )

    # Truncation needed — reuse reserved budget
    kept: list[EvidenceBlock] = []
    cumulative_lines = 0
    cumulative_chars = 0
    reason: TruncationReason | None = None

    for block in blocks:
        # Check max_ranges first
        if len(kept) >= max_ranges:
            reason = reason or TruncationReason.MAX_RANGES
            break

        block_lines = len(block.text.splitlines())
        block_chars = len(block.text)

        # Check max_lines
        if cumulative_lines + block_lines > max_lines:
            reason = reason or TruncationReason.MAX_LINES
            break

        # Check max_chars
        if cumulative_chars + block_chars > char_budget:
            reason = reason or TruncationReason.MAX_CHARS
            break

        kept.append(block)
        cumulative_lines += block_lines
        cumulative_chars += block_chars

    dropped = len(blocks) - len(kept)
    return TruncateBlocksResult(
        blocks=tuple(kept), truncated=dropped > 0,
        reason=reason, dropped_blocks=dropped,
    )
