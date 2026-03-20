# Context Injection v0b D4: Grep Execution

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the grep stub in `execute.py` with a full grep execution pipeline — ripgrep subprocess, match processing, redaction, truncation — completing the v0b MCP server.

**Architecture:** New `grep.py` module handles ripgrep subprocess and match processing (run, parse, filter, group, merge ranges, build blocks). `execute.py` gains `execute_grep()` that orchestrates the full pipeline and replaces the stub. The existing classify/redact/truncate pipeline is reused for per-block redaction.

**Tech Stack:** ripgrep (`rg`) subprocess with `--json` output, existing `classify_path()` + `redact_text()` + `truncate_blocks()` pipeline.

**Reference:** `docs/plans/2026-02-11-conversation-aware-context-injection.md` (Sections 3, 7, 10, 11)

**Branch:** Create `feature/context-injection-v0b-d4` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest -q`

**Lint command:** `cd packages/context-injection && uv run ruff check .`

**Dependencies between tasks:**
- Task 1: independent (grep subprocess runner + JSON output parser)
- Task 2: independent (context range building — pure functions, no I/O)
- Task 3: depends on Tasks 1 + 2 (match filtering, block building, file I/O + redaction)
- Task 4: depends on Task 3 (execute_grep pipeline, stub replacement)
- Task 5: depends on Task 4 (end-to-end integration through full Call 1 → Call 2 flow)

**Known limitations:**
- Grep matches in config files (YAML, JSON, TOML) produce partial-file snippets that may trigger format redactor desync → suppression. This is safe (over-redaction), not a bug. Most grep use cases target code files where only generic token redaction applies.
- Each matched file is read from disk per range. For MVP with max 5 ranges per file, this is acceptable. Optimization (read once, extract many) is a post-MVP concern.
- `rg` is assumed available in all Claude Code environments. Tests using real `rg` will fail if it's not installed. No fallback to Python `re`.
- Timeouts are distinct from "no matches": `GrepTimeoutError` produces `ScoutResultFailure(status="timeout")`, not a success with 0 matches. This preserves the "absence is data" contract for genuine no-match scenarios.
- TOCTOU between rg run and file read is handled by catching `FileNotFoundError`, `PermissionError`, and `IsADirectoryError` in `build_evidence_blocks`.

---

### Task 1: Grep subprocess runner and JSON output parser

**Files:**
- Create: `packages/context-injection/context_injection/grep.py`
- Create: `packages/context-injection/tests/test_grep.py`

**What this builds:**
- `GrepRawMatch` frozen dataclass: `path` (repo-relative), `line_number` (1-indexed), `line_text` (str)
- `RgNotFoundError` exception for when ripgrep is not installed
- `GrepTimeoutError` exception for when ripgrep exceeds timeout (distinct from "no matches" — timeout is not absence-is-data)
- `_parse_rg_json_lines(lines: list[str]) -> list[GrepRawMatch]` — parses rg's JSON output format (extracts `type: "match"` records, ignores `begin`/`end`/`summary`)
- `run_grep(pattern, repo_root, *, timeout=5.0) -> list[GrepRawMatch]` — runs rg subprocess, parses JSON-per-line output
- Error handling: `RgNotFoundError` (rg not on PATH), `GrepTimeoutError` (timeout exceeded), decode errors (skips malformed lines)

**Why this sequence:** Subprocess + parsing is self-contained with no codebase dependencies. Tests use mock subprocess (no real rg needed). Foundation for all subsequent tasks.

**rg JSON output format reference** (one JSON object per line):
```
type:"begin"  -> data.path.text = "src/main.py"
type:"match"  -> data.path.text, data.line_number, data.lines.text, data.submatches
type:"end"    -> per-file stats
type:"summary" -> overall stats
```
Only `type:"match"` records contain match data. All other types are ignored.

**Step 1: Write test file skeleton and first test for `_parse_rg_json_lines`**

Create `packages/context-injection/tests/test_grep.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestParseRgJsonLines -v`
Expected: ERRORS — `ModuleNotFoundError: No module named 'context_injection.grep'`

**Step 3: Write `GrepRawMatch` and `_parse_rg_json_lines`**

Create `packages/context-injection/context_injection/grep.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestParseRgJsonLines -v`
Expected: All 8 tests PASS

**Step 5: Write tests for `run_grep`**

Append to `packages/context-injection/tests/test_grep.py`:

```python
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
```

**Step 6: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestRunGrep -v`
Expected: ERRORS — `ImportError: cannot import name 'run_grep' from 'context_injection.grep'`

**Step 7: Write `run_grep`**

Append to `packages/context-injection/context_injection/grep.py` (after `_parse_rg_json_lines`):

```python
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
```

**Step 8: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestRunGrep -v`
Expected: All 6 tests PASS

**Step 9: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -q`
Expected: 675 + 14 = 689 tests PASS (14 new from Task 1)

**Step 10: Commit**

```bash
git add packages/context-injection/context_injection/grep.py packages/context-injection/tests/test_grep.py
git commit -m "feat(context-injection): add grep subprocess runner and JSON output parser (D4 Task 1)"
```

---

### Task 2: Context range building and merging

**Files:**
- Modify: `packages/context-injection/context_injection/grep.py`
- Modify: `packages/context-injection/tests/test_grep.py`

**What this builds:**
- `build_context_ranges(match_lines: list[int], context_lines: int, total_lines: int) -> list[tuple[int, int]]` — builds `[match - context, match + context]` windows (1-indexed, clamped to file bounds), merges overlapping/adjacent ranges
- Pure function, no I/O

**Why this sequence:** Range merging is a pure algorithm with thorough edge case testing. Independent of Task 1.

**Step 1: Write tests for `build_context_ranges`**

Append to `packages/context-injection/tests/test_grep.py` (update import to include `build_context_ranges`):

```python
from context_injection.grep import (
    GrepRawMatch,
    RgNotFoundError,
    _parse_rg_json_lines,
    build_context_ranges,
    run_grep,
)


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
```

**Step 2: Run test to verify it fails**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestBuildContextRanges -v`
Expected: ERRORS — `ImportError: cannot import name 'build_context_ranges'`

**Step 3: Write `build_context_ranges`**

Append to `packages/context-injection/context_injection/grep.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestBuildContextRanges -v`
Expected: All 13 tests PASS

**Step 5: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -q`
Expected: 689 + 13 = 702 tests PASS

**Step 6: Commit**

```bash
git add packages/context-injection/context_injection/grep.py packages/context-injection/tests/test_grep.py
git commit -m "feat(context-injection): add context range building and merging (D4 Task 2)"
```

---

### Task 3: Match filtering, file reading, and block building

**Files:**
- Modify: `packages/context-injection/context_injection/grep.py`
- Modify: `packages/context-injection/tests/test_grep.py`

**What this builds:**
- `group_matches_by_file(matches) -> dict[str, list[int]]` — groups match line numbers by file
- `filter_file(path, git_files) -> bool` — git-tracked + denylist check
- `read_line_range(abs_path, start, end) -> str` — reads specific 1-indexed line range
- `_BinaryFile` exception, `_read_file_lines(abs_path)` private helper
- `build_evidence_blocks(grouped, spec, repo_root, git_files) -> tuple[list[EvidenceBlock], int, list[GrepMatch], int]` — full block building pipeline

**Why this sequence:** Integration layer between grep output (Task 1), range logic (Task 2), and the existing classify/redact pipeline. Needs real tmp_path files for testing.

**Step 1: Write tests for `group_matches_by_file`**

Append to test imports and add test class in `packages/context-injection/tests/test_grep.py`:

```python
from context_injection.grep import (
    GrepRawMatch,
    RgNotFoundError,
    _parse_rg_json_lines,
    build_context_ranges,
    filter_file,
    group_matches_by_file,
    read_line_range,
    run_grep,
)


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
```

**Step 2: Write `group_matches_by_file`**

Append to `packages/context-injection/context_injection/grep.py`:

```python
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
```

**Step 3: Run tests to verify**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestGroupMatchesByFile -v`
Expected: 3 tests PASS

**Step 4: Write tests for `filter_file`**

Append to `packages/context-injection/tests/test_grep.py`:

```python
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
```

**Step 5: Write `filter_file`**

Add import and function to `packages/context-injection/context_injection/grep.py`:

```python
# Add to imports at top of file:
from context_injection.paths import _check_denylist


def filter_file(path: str, git_files: set[str]) -> bool:
    """Check if file should be included in grep results.

    Returns True if file is git-tracked AND not in denylist.
    """
    if path not in git_files:
        return False
    return _check_denylist(path) is None
```

**Step 6: Run tests to verify**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestFilterFile -v`
Expected: 7 tests PASS

**Step 7: Write tests for `read_line_range`**

Append to `packages/context-injection/tests/test_grep.py`:

```python
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
```

**Step 8: Write `_read_file_lines` and `read_line_range`**

Add to `packages/context-injection/context_injection/grep.py`:

```python
_BINARY_CHECK_SIZE: int = 8192
"""Check first 8KB for NUL bytes to detect binary files."""


def _read_file_lines(abs_path: str) -> list[str]:
    """Read a UTF-8 text file and return lines with line endings preserved.

    Raises:
        FileNotFoundError: file does not exist.
        UnicodeDecodeError: file is not valid UTF-8.
        ValueError: binary file (NUL byte in first 8KB).
    """
    with open(abs_path, "rb") as f:
        head = f.read(_BINARY_CHECK_SIZE)
    if b"\x00" in head:
        raise ValueError(f"Binary file: {abs_path}")
    with open(abs_path, "r", encoding="utf-8") as f:
        return f.readlines()


def read_line_range(abs_path: str, start: int, end: int) -> str:
    """Read lines [start, end] (1-indexed, inclusive) from a UTF-8 file.

    Returns selected lines joined as a single string (preserving line endings).

    Raises:
        FileNotFoundError: file does not exist.
        UnicodeDecodeError: file is not valid UTF-8.
        ValueError: binary file (NUL byte in first 8KB).
    """
    all_lines = _read_file_lines(abs_path)
    selected = all_lines[start - 1 : end]
    return "".join(selected)
```

**Step 9: Run tests to verify**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestReadLineRange -v`
Expected: 7 tests PASS

**Step 10: Write test for `build_evidence_blocks` (happy path)**

Append to test imports and add test class in `packages/context-injection/tests/test_grep.py`:

```python
from context_injection.grep import build_evidence_blocks
from context_injection.types import GrepMatch, GrepSpec


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
        if blocks:
            assert "[REDACTED" in blocks[0].text
            assert redactions > 0
```

**Step 11: Write `build_evidence_blocks`**

Add imports and function to `packages/context-injection/context_injection/grep.py`:

```python
# Add to imports at top of file:
import os

from context_injection.classify import classify_path
from context_injection.redact import RedactedText, SuppressedText, redact_text
from context_injection.truncate import EvidenceBlock
from context_injection.types import GrepMatch, GrepSpec


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
        except (FileNotFoundError, UnicodeDecodeError, ValueError,
                PermissionError, IsADirectoryError):
            continue

        total_lines = len(all_lines)
        ranges = build_context_ranges(match_lines, spec.context_lines, total_lines)

        # Build blocks per range, tracking which ranges survive redaction
        file_blocks: list[EvidenceBlock] = []
        surviving_ranges: list[tuple[int, int]] = []
        for start, end in ranges:
            range_text = "".join(all_lines[start - 1 : end])
            classification = classify_path(abs_path)
            redact_outcome = redact_text(
                text=range_text, classification=classification, path=abs_path,
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
                EvidenceBlock(text=block_text, start_line=start, path=path),
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
```

**Step 12: Run tests to verify**

Run: `cd packages/context-injection && uv run pytest tests/test_grep.py::TestBuildEvidenceBlocks -v`
Expected: All ~10 tests PASS

**Step 13: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -q`
Expected: ~730 tests PASS (702 prior + ~28 new from Task 3)

**Step 14: Run lint**

Run: `cd packages/context-injection && uv run ruff check .`
Expected: No errors

**Step 15: Commit**

```bash
git add packages/context-injection/context_injection/grep.py packages/context-injection/tests/test_grep.py
git commit -m "feat(context-injection): add match filtering, file reading, and evidence block building (D4 Task 3)"
```

---

### Task 4: execute_grep pipeline and stub replacement

**Files:**
- Modify: `packages/context-injection/context_injection/execute.py`
- Modify: `packages/context-injection/tests/test_execute.py`

**What this builds:**
- `execute_grep()` function in `execute.py` — full pipeline: run_grep → group → build_evidence_blocks → truncate → format → ScoutResultSuccess
- Stub replacement in `execute_scout()`: grep branch dispatches to `execute_grep()` instead of returning `ScoutResultFailure(timeout)`
- Updated tests replacing the old stub test

**Why this sequence:** Integrates all prior tasks into the Call 2 dispatch. The stub replacement is the delivery milestone.

**Step 1: Add imports to `execute.py`**

Add these imports to `packages/context-injection/context_injection/execute.py` (at the top, with existing imports):

```python
# Add to existing imports:
from context_injection.grep import (
    GrepTimeoutError,
    RgNotFoundError,
    build_evidence_blocks,
    group_matches_by_file,
    run_grep,
)
from context_injection.truncate import truncate_blocks  # add alongside existing truncate_excerpt import
from context_injection.types import GrepResult, GrepSpec  # add GrepResult and GrepSpec to existing types import
```

The full types import line becomes:
```python
from context_injection.types import (
    Budget,
    GrepResult,
    GrepSpec,
    ReadResult,
    ReadSpec,
    ScoutFailureStatus,
    ScoutRequest,
    ScoutResultFailure,
    ScoutResultInvalid,
    ScoutResultSuccess,
    SCHEMA_VERSION,
)
```

The truncate import line becomes:
```python
from context_injection.truncate import truncate_blocks, truncate_excerpt
```

**Step 2: Write `execute_grep` function**

Add to `packages/context-injection/context_injection/execute.py` (after `execute_read`, before `execute_scout`):

```python
# --- Grep pipeline integration (Task 4) ---


def execute_grep(
    scout_option_id: str,
    option: ScoutOptionRecord,
    ctx: AppContext,
    evidence_history_len: int,
) -> ScoutResultSuccess | ScoutResultFailure:
    """Execute a grep scout: run rg -> group -> filter -> read+redact -> truncate -> wrap.

    Returns ScoutResultSuccess (even for 0 matches — absence is data) or
    ScoutResultFailure (rg not found, timeout). Never raises.
    """
    spec = option.spec
    assert isinstance(spec, GrepSpec)

    def _fail(status: ScoutFailureStatus, error_message: str) -> ScoutResultFailure:
        return ScoutResultFailure(
            schema_version=SCHEMA_VERSION,
            scout_option_id=scout_option_id,
            status=status,
            template_id=option.template_id,
            entity_id=option.entity_id,
            entity_key=option.entity_key,
            action="grep",
            error_message=error_message,
            budget=compute_budget(evidence_history_len, success=False),
        )

    # Step 1: Run ripgrep
    try:
        raw_matches = run_grep(spec.pattern, ctx.repo_root)
    except RgNotFoundError:
        return _fail("timeout", "ripgrep (rg) not found on PATH")
    except GrepTimeoutError:
        return _fail("timeout", f"ripgrep timed out searching for {spec.pattern!r}")

    # Step 2: Group and build evidence blocks
    grouped = group_matches_by_file(raw_matches) if raw_matches else {}
    blocks, match_count, grep_matches, redactions = build_evidence_blocks(
        grouped, spec, ctx.repo_root, ctx.git_files,
    )

    # Step 3: No surviving blocks — success with 0 matches
    if not blocks:
        return ScoutResultSuccess(
            schema_version=SCHEMA_VERSION,
            scout_option_id=scout_option_id,
            status="success",
            template_id=option.template_id,
            entity_id=option.entity_id,
            entity_key=option.entity_key,
            action="grep",
            grep_result=GrepResult(excerpt="", match_count=0, matches=[]),
            truncated=False,
            truncation_reason=None,
            redactions_applied=0,
            risk_signal=option.risk_signal,
            evidence_wrapper=build_grep_evidence_wrapper(spec.pattern, 0, 0),
            budget=compute_budget(evidence_history_len, success=True),
        )

    # Step 4: Truncate blocks
    trunc = truncate_blocks(
        blocks=blocks,
        max_ranges=spec.max_ranges,
        max_chars=spec.max_chars,
        max_lines=spec.max_lines,
    )

    # Step 5: Build excerpt from surviving blocks
    excerpt = "\n".join(b.text for b in trunc.blocks)
    if trunc.truncated and excerpt:
        excerpt += "[truncated]\n"

    truncation_reason = trunc.reason.value if trunc.reason else None
    file_count = len(grep_matches)

    return ScoutResultSuccess(
        schema_version=SCHEMA_VERSION,
        scout_option_id=scout_option_id,
        status="success",
        template_id=option.template_id,
        entity_id=option.entity_id,
        entity_key=option.entity_key,
        action="grep",
        grep_result=GrepResult(
            excerpt=excerpt,
            match_count=match_count,
            matches=grep_matches,
        ),
        truncated=trunc.truncated,
        truncation_reason=truncation_reason,
        redactions_applied=redactions,
        risk_signal=option.risk_signal,
        evidence_wrapper=build_grep_evidence_wrapper(
            spec.pattern, match_count, file_count,
        ),
        budget=compute_budget(evidence_history_len, success=True),
    )
```

**Step 3: Replace the grep stub in `execute_scout`**

In `packages/context-injection/context_injection/execute.py`, replace the grep stub (lines 380-391):

OLD (remove):
```python
    # Grep stub -- D4 will replace with real grep execution
    return ScoutResultFailure(
        schema_version=SCHEMA_VERSION,
        scout_option_id=req.scout_option_id,
        status="timeout",
        template_id=option.template_id,
        entity_id=option.entity_id,
        entity_key=option.entity_key,
        action="grep",
        error_message="grep not yet implemented",
        budget=compute_budget(evidence_history_len, success=False),
    )
```

NEW:
```python
    return execute_grep(
        req.scout_option_id, option, ctx, evidence_history_len,
    )
```

Also update the `execute_scout` docstring to remove "Grep action -> stub returning ScoutResultFailure(timeout) until D4." and replace with "Grep action -> execute_grep()."

**Step 4: Write grep execution tests in `test_execute.py`**

Replace the old stub test and add new tests. In `packages/context-injection/tests/test_execute.py`:

Add import at top:
```python
from unittest.mock import patch
from context_injection.grep import GrepRawMatch
```

Replace `test_grep_stub_returns_timeout` with new tests in `TestExecuteScout`:

```python
    def test_grep_happy_path(self, tmp_path) -> None:
        ctx, req = _setup_execute_scout_test(
            tmp_path, action="grep",
            file_content="class MyClass:\n    pass\n",
        )
        ctx.git_files = {"hello.py"}
        mock_matches = [
            GrepRawMatch(path="hello.py", line_number=1, line_text="class MyClass:"),
        ]
        with patch("context_injection.execute.run_grep", return_value=mock_matches):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultSuccess)
        assert result.status == "success"
        assert result.action == "grep"
        assert result.grep_result is not None
        assert result.grep_result.match_count == 1
        assert "class MyClass:" in result.grep_result.excerpt
        assert "# hello.py:" in result.grep_result.excerpt
        assert result.grep_result.matches[0].path_display == "hello.py"
        assert result.evidence_wrapper.startswith("Grep for `MyClass`")
        assert "1 matches in 1 file(s)" in result.evidence_wrapper

    def test_grep_no_matches(self, tmp_path) -> None:
        ctx, req = _setup_execute_scout_test(tmp_path, action="grep")
        with patch("context_injection.execute.run_grep", return_value=[]):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultSuccess)
        assert result.action == "grep"
        assert result.grep_result.match_count == 0
        assert result.grep_result.excerpt == ""
        assert result.grep_result.matches == []
        assert "0 matches" in result.evidence_wrapper

    def test_grep_rg_not_found(self, tmp_path) -> None:
        from context_injection.grep import RgNotFoundError

        ctx, req = _setup_execute_scout_test(tmp_path, action="grep")
        with patch("context_injection.execute.run_grep", side_effect=RgNotFoundError("not found")):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultFailure)
        assert result.status == "timeout"
        assert "rg" in result.error_message

    def test_grep_timeout(self, tmp_path) -> None:
        from context_injection.grep import GrepTimeoutError

        ctx, req = _setup_execute_scout_test(tmp_path, action="grep")
        with patch("context_injection.execute.run_grep", side_effect=GrepTimeoutError("timed out")):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultFailure)
        assert result.status == "timeout"
        assert "timed out" in result.error_message

    def test_grep_all_files_filtered(self, tmp_path) -> None:
        ctx, req = _setup_execute_scout_test(
            tmp_path, action="grep",
            file_content="class MyClass:\n",
        )
        # git_files is empty — all matches will be filtered
        ctx.git_files = set()
        mock_matches = [
            GrepRawMatch(path="hello.py", line_number=1, line_text="class MyClass:"),
        ]
        with patch("context_injection.execute.run_grep", return_value=mock_matches):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultSuccess)
        assert result.grep_result.match_count == 0

    def test_grep_budget_success(self, tmp_path) -> None:
        ctx, req = _setup_execute_scout_test(
            tmp_path, action="grep",
            file_content="class MyClass:\n    pass\n",
            evidence_history=[
                EvidenceRecord(
                    entity_key="symbol:OtherClass",
                    template_id="probe.symbol_repo_fact",
                    turn=0,
                ),
            ],
        )
        ctx.git_files = {"hello.py"}
        mock_matches = [
            GrepRawMatch(path="hello.py", line_number=1, line_text="class MyClass:"),
        ]
        with patch("context_injection.execute.run_grep", return_value=mock_matches):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultSuccess)
        # 1 prior + 1 current = 2
        assert result.budget.evidence_count == 2
        assert result.budget.scout_available is False

    def test_grep_budget_failure(self, tmp_path) -> None:
        from context_injection.grep import RgNotFoundError

        ctx, req = _setup_execute_scout_test(
            tmp_path, action="grep",
            evidence_history=[
                EvidenceRecord(
                    entity_key="symbol:OtherClass",
                    template_id="probe.symbol_repo_fact",
                    turn=0,
                ),
            ],
        )
        with patch("context_injection.execute.run_grep", side_effect=RgNotFoundError("not found")):
            result = execute_scout(ctx, req)

        assert isinstance(result, ScoutResultFailure)
        # Failed scouts are free: 1 prior + 0 = 1
        assert result.budget.evidence_count == 1
```

**Step 5: Run tests to verify**

Run: `cd packages/context-injection && uv run pytest tests/test_execute.py::TestExecuteScout -v`
Expected: All tests PASS (old stub test removed, 7 new grep tests pass)

**Step 6: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -q`
Expected: ~735 tests PASS (730 prior - 1 old stub + 6 new)

**Step 7: Run lint**

Run: `cd packages/context-injection && uv run ruff check .`
Expected: No errors

**Step 8: Commit**

```bash
git add packages/context-injection/context_injection/execute.py packages/context-injection/tests/test_execute.py
git commit -m "feat(context-injection): add execute_grep pipeline and replace grep stub (D4 Task 4)"
```

---

### Task 5: End-to-end integration tests

**Files:**
- Modify: `packages/context-injection/tests/test_integration.py`

**What this builds:**
- `test_grep_call1_call2_round_trip` — full Call 1 → Call 2 flow with real `rg`
- `test_grep_no_matches_returns_success` — symbol not found, verifies success with 0 matches
- `test_grep_denied_file_filtered` — matches in denied file excluded from results

**Why this sequence:** Validates the complete flow from agent input to evidence output. Catches integration issues between pipeline → templates → execute → grep.

**Entity extraction requirement:** Symbol entities require dotted identifiers with 3+ parts (regex: `[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){2,}`). Examples: `os.path.join`, `app.config.load`. Backticked in focus text for high confidence. These get `probe.symbol_repo_fact` template → grep scout option.

**Step 1: Write `test_grep_call1_call2_round_trip`**

Add to `packages/context-injection/tests/test_integration.py`:

```python
import shutil

from context_injection.execute import execute_scout
from context_injection.types import ScoutRequest, ScoutResultSuccess


def test_grep_call1_call2_round_trip(tmp_path) -> None:
    """Full Call 1 -> Call 2 flow for a grep scout.

    Creates a file with a searchable dotted symbol, runs process_turn
    (Call 1) to extract the symbol entity and create a grep scout option,
    then runs execute_scout (Call 2) to grep for the symbol and verify
    the result contains matching evidence.

    Requires ripgrep (rg) on PATH.
    """
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    # Setup: file containing a dotted symbol
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "loader.py").write_text(
        "from app.config.load import get_settings\n"
        "\n"
        "def init():\n"
        "    settings = app.config.load()\n"
        "    return settings\n"
    )

    git_files = {"src/loader.py"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    # Call 1: process_turn with a focus mentioning the dotted symbol
    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_grep_test",
            "focus": {
                "text": "How does `app.config.load` initialize settings?",
                "claims": [
                    {
                        "text": "`app.config.load` reads from YAML files",
                        "status": "new",
                        "turn": 1,
                    },
                ],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    # Find the grep scout option (probe.symbol_repo_fact)
    grep_candidates = [
        tc
        for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1, (
        f"Expected grep candidate but got templates: "
        f"{[tc.template_id for tc in result.template_candidates]}"
    )

    grep_tc = grep_candidates[0]
    assert len(grep_tc.scout_options) == 1
    grep_option = grep_tc.scout_options[0]
    assert grep_option.action == "grep"

    # Call 2: execute_scout with the grep option
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    assert scout_result.action == "grep"
    assert scout_result.grep_result is not None
    assert scout_result.grep_result.match_count > 0
    assert "app.config.load" in scout_result.grep_result.excerpt
    assert scout_result.evidence_wrapper.startswith("Grep for")
    assert scout_result.budget.scout_available is False


def test_grep_no_matches_returns_success(tmp_path) -> None:
    """Grep for a non-existent symbol returns success with 0 matches.

    Absence is data per design spec — the model learns the symbol
    doesn't exist in the repo.
    """
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    (tmp_path / "main.py").write_text("def hello():\n    return 1\n")
    git_files = {"main.py"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_no_match",
            "focus": {
                "text": "How does `nonexistent.symbol.name` work?",
                "claims": [],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    grep_candidates = [
        tc for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1

    grep_option = grep_candidates[0].scout_options[0]
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    assert scout_result.grep_result.match_count == 0
    assert scout_result.grep_result.excerpt == ""
    assert "0 matches" in scout_result.evidence_wrapper


def test_grep_denied_file_filtered(tmp_path) -> None:
    """Matches in denied files (.env) are excluded from grep results."""
    if shutil.which("rg") is None:
        pytest.skip("ripgrep (rg) not installed")

    # The symbol appears ONLY in a .env file (denied)
    (tmp_path / ".env").write_text("app.config.load=true\n")
    git_files = {".env"}
    ctx = AppContext.create(repo_root=str(tmp_path), git_files=git_files)

    request = TurnRequest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "turn_number": 1,
            "conversation_id": "conv_denied",
            "focus": {
                "text": "Where is `app.config.load` used?",
                "claims": [],
                "unresolved": [],
            },
            "posture": "exploratory",
        }
    )

    result = process_turn(request, ctx)
    assert isinstance(result, TurnPacketSuccess)

    grep_candidates = [
        tc for tc in result.template_candidates
        if tc.template_id == "probe.symbol_repo_fact"
    ]
    assert len(grep_candidates) >= 1, (
        f"Expected grep candidate for app.config.load but got templates: "
        f"{[tc.template_id for tc in result.template_candidates]}"
    )

    grep_option = grep_candidates[0].scout_options[0]
    ref = f"{request.conversation_id}:{request.turn_number}"
    scout_req = ScoutRequest(
        schema_version=SCHEMA_VERSION,
        scout_option_id=grep_option.id,
        scout_token=grep_option.scout_token,
        turn_request_ref=ref,
    )
    scout_result = execute_scout(ctx, scout_req)

    assert isinstance(scout_result, ScoutResultSuccess)
    # rg may find the match, but filter_file should exclude .env
    assert scout_result.grep_result.match_count == 0
```

**Step 2: Update imports at top of `test_integration.py`**

```python
"""Integration test: full Call 1 → Call 2 pipeline with contract example input."""

import shutil

import pytest

from context_injection.execute import execute_scout
from context_injection.pipeline import process_turn
from context_injection.state import AppContext
from context_injection.types import (
    SCHEMA_VERSION,
    ScoutRequest,
    ScoutResultSuccess,
    TurnPacketSuccess,
    TurnRequest,
)
```

**Step 3: Run integration tests**

Run: `cd packages/context-injection && uv run pytest tests/test_integration.py -v`
Expected: 4 tests PASS (1 existing + 3 new)

**Step 4: Run full test suite**

Run: `cd packages/context-injection && uv run pytest -q`
Expected: ~738 tests PASS

**Step 5: Run lint**

Run: `cd packages/context-injection && uv run ruff check .`
Expected: No errors

**Step 6: Commit**

```bash
git add packages/context-injection/tests/test_integration.py
git commit -m "feat(context-injection): add end-to-end grep integration tests (D4 Task 5)"
```

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest -q`
Expected: All tests pass (675 existing + ~60-70 new ≈ 735-745 total)

Run: `cd packages/context-injection && uv run ruff check .`
Expected: No errors

Run: `cd packages/context-injection && uv run ruff format --check .`
Expected: No reformatting needed

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `grep.py` | New | `GrepRawMatch`, `RgNotFoundError`, `GrepTimeoutError`, `_parse_rg_json_lines`, `run_grep`, `build_context_ranges`, `group_matches_by_file`, `filter_file`, `_read_file_lines`, `read_line_range`, `build_evidence_blocks` |
| `execute.py` | Modified | `execute_grep()` pipeline function, stub replacement in `execute_scout()`, new imports |
| `test_grep.py` | New | ~40 tests: parsing, subprocess runner, range building, grouping, filtering, line reading, evidence block building |
| `test_execute.py` | Modified | 7 new grep execution tests replacing 1 old stub test |
| `test_integration.py` | Modified | 3 new end-to-end Call 1 → Call 2 grep integration tests |

## Function Reference

### grep.py (new module, ~200 lines)

| Function | Type | Purpose |
|----------|------|---------|
| `GrepRawMatch` | dataclass | Single rg match: path + line_number + line_text |
| `RgNotFoundError` | exception | rg not on PATH |
| `GrepTimeoutError` | exception | rg exceeded timeout (distinct from no-matches) |
| `_parse_rg_json_lines` | private | Parse rg JSON output → GrepRawMatch list |
| `run_grep` | public | Run rg subprocess, return parsed matches |
| `build_context_ranges` | public | Match lines → merged context windows |
| `group_matches_by_file` | public | Group matches by file path |
| `filter_file` | public | Git-tracked + denylist check |
| `_read_file_lines` | private | Read UTF-8 file, binary check |
| `read_line_range` | public | Read specific line range from file |
| `build_evidence_blocks` | public | Full per-file pipeline → EvidenceBlocks |

### execute.py (modified, ~50 lines added)

| Function | Type | Purpose |
|----------|------|---------|
| `execute_grep` | public | Full grep pipeline: run → group → blocks → truncate → result |
