"""Call 2 execution pipeline: read executor, evidence wrappers, integration.

Build order:
- Task 1 (D2b): read_file_excerpt, ReadExcerpt, BinaryFileError
- Task 2 (D2b): evidence wrapper builders, budget computation
- Task 3 (D2b): execute_read (read -> classify -> redact -> truncate -> wrap)
- Task 4 (D2b): execute_scout (top-level dispatch)
- Task 13-14 (D4): grep executor, grep post-processing
"""

from __future__ import annotations

from dataclasses import dataclass

from context_injection.types import ReadSpec

_BINARY_CHECK_SIZE: int = 8192
"""Check first 8KB for NUL bytes to detect binary files."""


class BinaryFileError(Exception):
    """File contains NUL bytes in the first 8192 bytes."""


@dataclass(frozen=True)
class ReadExcerpt:
    """Result of reading and excerpting a file.

    text: Selected lines joined with newlines (empty string for empty files).
    total_lines: Total line count in the file (via splitlines()).
    excerpt_range: [start_line, end_line] 1-indexed, or None for empty files.
    """

    text: str
    total_lines: int
    excerpt_range: list[int] | None


def read_file_excerpt(spec: ReadSpec) -> ReadExcerpt:
    """Read a file and select an excerpt based on strategy.

    Binary detection: NUL byte in first 8192 bytes -> BinaryFileError.
    Encoding: UTF-8 only, no fallback.
    Excerpt strategies: first_n (first N lines), centered (window around center_line).
    Line joining: selected lines joined with '\\n' + trailing '\\n'.

    Raises:
        FileNotFoundError: file does not exist
        BinaryFileError: NUL byte in first 8192 bytes
        UnicodeDecodeError: file is not valid UTF-8
    """
    path = spec.resolved_path

    # Binary detection (before full read to avoid decoding binary data)
    with open(path, "rb") as f:
        head = f.read(_BINARY_CHECK_SIZE)
    if b"\x00" in head:
        raise BinaryFileError(path)

    # Full read as UTF-8
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    total_lines = len(lines)

    if total_lines == 0:
        return ReadExcerpt(text="", total_lines=0, excerpt_range=None)

    # Excerpt selection
    if spec.strategy == "first_n":
        selected = lines[: spec.max_lines]
        start = 1
        end = len(selected)
    else:
        # centered: window around center_line (1-indexed)
        assert spec.center_line is not None, "centered strategy requires center_line"
        context = (spec.max_lines - 1) // 2
        center_idx = spec.center_line - 1
        start_idx = max(0, center_idx - context)
        end_idx = min(total_lines, start_idx + spec.max_lines)
        # Re-adjust start if clipped at file end
        start_idx = max(0, end_idx - spec.max_lines)
        selected = lines[start_idx:end_idx]
        start = start_idx + 1
        end = start_idx + len(selected)

    if not selected:
        return ReadExcerpt(text="", total_lines=total_lines, excerpt_range=None)

    text = "\n".join(selected) + "\n"
    return ReadExcerpt(text=text, total_lines=total_lines, excerpt_range=[start, end])
