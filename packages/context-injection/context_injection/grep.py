"""Ripgrep subprocess execution and output parsing for grep scouts.

Build order:
- Task 1 (D4): GrepRawMatch, RgNotFoundError, _parse_rg_json_lines, run_grep
- Task 2 (D4): build_context_ranges
- Task 3 (D4): group_matches_by_file, filter_file, read_line_range, build_evidence_blocks
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GrepRawMatch:
    """A single match line from ripgrep JSON output."""

    path: str
    """Repo-relative file path (no leading ./)."""
    line_number: int
    """1-indexed line number."""
    line_text: str
    """Matched line content (trailing newline stripped)."""


class RgNotFoundError(Exception):
    """ripgrep (rg) is not installed or not on PATH."""


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

    Runs ``rg --json --fixed-strings -n --no-heading <pattern>`` from
    repo_root directory. Paths in output are repo-relative.

    Raises:
        RgNotFoundError: rg is not on PATH.
        GrepTimeoutError: rg exceeded timeout (not the same as "no matches").

    Returns:
        List of GrepRawMatch. Empty on no matches or rg error.
    """
    try:
        result = subprocess.run(
            ["rg", "--json", "--fixed-strings", "-n", "--no-heading", pattern],
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
        return []

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
