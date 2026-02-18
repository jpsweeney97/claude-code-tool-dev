"""Ripgrep subprocess execution and output parsing for grep scouts.

Layers:
- Subprocess runner: run_grep, _parse_rg_json_lines, exception types
- Range building: build_context_ranges (match lines → merged windows)
- Evidence building: group_matches_by_file, filter_file, build_evidence_blocks
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass

from context_injection.classify import classify_path
from context_injection.paths import check_denylist
from context_injection.redact import RedactedText, SuppressedText, redact_text
from context_injection.truncate import EvidenceBlock
from context_injection.types import GrepMatch, GrepSpec

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GrepRawMatch:
    """A single match line from ripgrep JSON output."""

    path: str
    """Repo-relative file path (no leading ./)."""
    line_number: int
    """1-indexed line number."""
    line_text: str
    """Matched line content (trailing newline stripped)."""

    def __post_init__(self) -> None:
        if self.line_number < 1:
            raise ValueError(
                f"line_number must be >= 1. Got: {self.line_number}"
            )


class RgNotFoundError(Exception):
    """ripgrep (rg) is not installed or not on PATH."""


class RgExecutionError(Exception):
    """ripgrep exited with an error (exit code >= 2)."""


class GrepTimeoutError(Exception):
    """ripgrep subprocess exceeded its timeout."""


def _parse_rg_json_lines(lines: list[str]) -> list[GrepRawMatch]:
    """Parse rg --json output lines into GrepRawMatch objects.

    Processes only type=="match" records. Skips begin/end/summary/context.
    Silently skips malformed JSON lines and records with missing fields.
    """
    matches: list[GrepRawMatch] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "match":
            continue
        data = record.get("data", {})
        path_obj = data.get("path")
        if not isinstance(path_obj, dict):
            continue
        path_text = path_obj.get("text")
        line_number = data.get("line_number")
        lines_obj = data.get("lines", {})
        lines_text = lines_obj.get("text", "") if isinstance(lines_obj, dict) else ""
        if path_text is None or line_number is None:
            continue
        matches.append(
            GrepRawMatch(
                path=path_text.removeprefix("./"),
                line_number=line_number,
                line_text=lines_text.rstrip("\n"),
            )
        )
    return matches


def run_grep(
    pattern: str,
    repo_root: str,
    *,
    timeout: float = 5.0,
) -> list[GrepRawMatch]:
    """Run ripgrep and return parsed match results.

    Runs rg from repo_root with these flags:
    - ``--json``: structured JSON output for parsing
    - ``--fixed-strings``: literal pattern match (no regex)
    - ``-n --no-heading``: line numbers, no file headers
    - ``--hidden``: search hidden directories (.github/, .husky/, etc.)
    - ``--no-ignore``: ignore .gitignore rules (we filter post-hoc)
    - ``--glob=!.git/``: exclude .git internals (wasteful I/O)

    Post-hoc filtering rationale: ``filter_file()`` handles git-tracked +
    denylist filtering. rg's built-in filtering is redundant and too
    aggressive (misses hidden/ignored files the pipeline needs to see).

    Raises:
        RgNotFoundError: rg is not on PATH.
        GrepTimeoutError: rg exceeded timeout (not the same as "no matches").
        RgExecutionError: rg exited with error (exit code >= 2).

    Returns:
        List of GrepRawMatch. Empty list means no matches (exit code 1).
    """
    try:
        result = subprocess.run(
            [
                "rg", "--json", "--fixed-strings", "-n", "--no-heading",
                "--hidden", "--no-ignore", "--glob=!.git/",
                pattern,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=repo_root,
        )
    except FileNotFoundError:
        raise RgNotFoundError("ripgrep (rg) not found on PATH") from None
    except subprocess.TimeoutExpired:
        raise GrepTimeoutError(
            f"ripgrep timed out after {timeout}s searching for {pattern!r}"
        ) from None

    # rg exit codes: 0=matches found, 1=no matches, 2+=error
    if result.returncode not in (0, 1):
        raise RgExecutionError(
            f"rg exited with code {result.returncode}: {result.stderr.strip()}"
        )

    return _parse_rg_json_lines(result.stdout.splitlines())


def build_context_ranges(
    match_lines: list[int],
    context_lines: int,
    total_lines: int,
) -> list[tuple[int, int]]:
    """Build merged context ranges around match lines.

    Each match gets a window of [match - context_lines, match + context_lines],
    clamped to [1, total_lines]. Overlapping and adjacent ranges are merged.

    Args:
        match_lines: 1-indexed line numbers of matches (need not be sorted).
        context_lines: lines of context before and after each match.
        total_lines: total line count of the file.

    Returns:
        List of (start, end) tuples, 1-indexed, sorted by start.
        Empty list if match_lines is empty or total_lines is 0.
    """
    if not match_lines or total_lines == 0:
        return []

    # Build raw windows (deduplicate and sort)
    windows: list[tuple[int, int]] = []
    for line in sorted(set(match_lines)):
        start = max(1, line - context_lines)
        end = min(total_lines, line + context_lines)
        windows.append((start, end))

    # Merge overlapping/adjacent ranges
    merged: list[tuple[int, int]] = [windows[0]]
    for start, end in windows[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged


def group_matches_by_file(
    matches: list[GrepRawMatch],
) -> dict[str, list[int]]:
    """Group match line numbers by file path.

    Returns dict mapping repo-relative path to sorted list of
    1-indexed line numbers.
    """
    grouped: dict[str, list[int]] = {}
    for m in matches:
        grouped.setdefault(m.path, []).append(m.line_number)
    for line_numbers in grouped.values():
        line_numbers.sort()
    return grouped


def filter_file(path: str, git_files: set[str]) -> bool:
    """Check if file should be included in grep results.

    Returns True if file is git-tracked AND not in denylist.
    """
    if path not in git_files:
        return False
    return check_denylist(path) is None


_BINARY_CHECK_SIZE: int = 8192
"""Check first 8KB for NUL bytes to detect binary files."""


def _read_file_lines(abs_path: str) -> list[str]:
    """Read a UTF-8 text file and return lines with line endings preserved.

    Single read: opens once in binary mode, checks first 8KB for NUL bytes,
    decodes full content as UTF-8. Eliminates TOCTOU between binary check
    and content read.

    Raises:
        FileNotFoundError: file does not exist.
        UnicodeDecodeError: file is not valid UTF-8.
        ValueError: binary file (NUL byte in first 8KB).
    """
    with open(abs_path, "rb") as f:
        raw = f.read()
    if b"\x00" in raw[:_BINARY_CHECK_SIZE]:
        raise ValueError(f"Binary file: {abs_path}")
    return raw.decode("utf-8").splitlines(keepends=True)



def build_evidence_blocks(
    grouped: dict[str, list[int]],
    spec: GrepSpec,
    repo_root: str,
    git_files: set[str],
) -> tuple[list[EvidenceBlock], int, list[GrepMatch], int]:
    """Build evidence blocks from grouped match data.

    For each file: filter -> read -> build ranges -> redact per range -> blocks.
    Files with errors (binary, decode, not found, permission, replaced-by-dir)
    or full suppression are skipped.

    Returns:
        (blocks, match_count, grep_matches, redactions_applied)
        - blocks: one EvidenceBlock per surviving range
        - match_count: total match lines across files with surviving blocks,
          counting only lines whose ranges survived redaction
        - grep_matches: one GrepMatch per file with surviving blocks
        - redactions_applied: total redactions across all blocks
    """
    all_blocks: list[EvidenceBlock] = []
    match_count = 0
    grep_matches: list[GrepMatch] = []
    redactions_applied = 0

    for path in sorted(grouped):
        match_lines = grouped[path]

        if not filter_file(path, git_files):
            continue

        abs_path = os.path.join(repo_root, path)

        # Read file once — catch TOCTOU errors (file deleted, replaced by dir,
        # permission changed between rg run and our read)
        try:
            all_lines = _read_file_lines(abs_path)
        except FileNotFoundError:
            logger.debug("File vanished between rg run and read: %s", path)
            continue
        except UnicodeDecodeError:
            logger.debug("UTF-8 decode failed, skipping: %s", path)
            continue
        except ValueError:
            logger.debug("Binary file detected, skipping: %s", path)
            continue
        except PermissionError:
            logger.info("Permission denied reading: %s", path)
            continue
        except IsADirectoryError:
            logger.info("Path replaced by directory between rg run and read: %s", path)
            continue

        total_lines = len(all_lines)
        ranges = build_context_ranges(match_lines, spec.context_lines, total_lines)

        # Build blocks per range, tracking which ranges survive redaction
        file_blocks: list[EvidenceBlock] = []
        surviving_ranges: list[tuple[int, int]] = []
        # Resolve symlinks before classification — prevents symlink bypass
        # (e.g., code.py -> secret.cfg would classify as CODE, not CONFIG_INI).
        # Matches execute_read which uses realpath at execute.py:259-260.
        real_abs_path = os.path.realpath(abs_path)
        classification = classify_path(real_abs_path)
        for start, end in ranges:
            range_text = "".join(all_lines[start - 1 : end])
            redact_outcome = redact_text(
                text=range_text, classification=classification, path=real_abs_path,
            )

            if isinstance(redact_outcome, SuppressedText):
                continue

            assert isinstance(redact_outcome, RedactedText)
            redactions_applied += (
                redact_outcome.stats.format_redactions
                + redact_outcome.stats.token_redactions
            )
            block_text = f"# {path}:{start}-{end}\n{redact_outcome.text}"
            file_blocks.append(
                EvidenceBlock(
                    text=block_text, start_line=start, path=path, end_line=end,
                ),
            )
            surviving_ranges.append((start, end))

        if file_blocks:
            all_blocks.extend(file_blocks)
            # Count only match lines within surviving ranges
            file_match_count = sum(
                1 for line in match_lines
                if any(s <= line <= e for s, e in surviving_ranges)
            )
            match_count += file_match_count
            grep_matches.append(
                GrepMatch(
                    path_display=path,
                    total_lines=total_lines,
                    ranges=[[s, e] for s, e in surviving_ranges],
                ),
            )

    return all_blocks, match_count, grep_matches, redactions_applied
