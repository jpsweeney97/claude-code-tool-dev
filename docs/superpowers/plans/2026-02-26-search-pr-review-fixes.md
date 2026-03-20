# Search PR Review Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 12 findings from the 4-agent PR #27 review — silent failures, missing error reporting, double compilation, undocumented behavior, test gaps, and dead code.

**Architecture:** All changes are in `packages/plugins/handoff/`. The JSON output envelope gains two new fields (`skipped`, `project_source`). `search_handoffs` gains a `skipped` parameter for error reporting. `get_project_name` returns a tuple with resolution source. Regex compilation moves to a single site.

**Tech Stack:** Python 3, pytest, no new dependencies.

**Files:**
- `scripts/search.py` — main implementation (252 lines)
- `tests/test_search.py` — tests (307 lines)
- `skills/searching-handoffs/SKILL.md` — skill instructions (69 lines)

**Working directory:** `packages/plugins/handoff/`

**Test command:** `uv run pytest tests/test_search.py -v`

---

## Finding-to-Task Map

| Finding | Description | Task |
|---------|-------------|------|
| #1 | Silent file skip, no feedback | 2 |
| #2 | Missing directory indistinguishable from no results | 3 |
| #3 | `get_project_name` swallows errors, no fallback indicator | 4 |
| #4 | Regex compiled twice (main + search_handoffs) | 5 |
| #5 | Regex case sensitivity undocumented in SKILL.md | 6 |
| #7 | Regex case sensitivity untested | 1 |
| #8 | Unreadable file skipping untested | 2 |
| #9 | Unclosed frontmatter delimiter untested | 1 |
| #10 | Regex metacharacters in literal mode untested | 1 |
| #11 | Docstring omits regex is case-sensitive | 6 |
| #12 | Test labels reference unknown external doc | 7 |
| #13 | `Section.line_start` computed but unused | 7 |

---

### Task 1: Tests for existing correct behavior (#7, #9, #10)

Three new tests that verify behavior already working correctly. All should pass immediately against the current code — no implementation changes.

**Files:**
- Modify: `tests/test_search.py`

**Step 1: Add test for regex case sensitivity (#7)**

Add to `TestSearchHandoffs`:

```python
def test_regex_is_case_sensitive(self, tmp_path: Path) -> None:
    """Regex mode is case-sensitive (flags=0), unlike literal mode."""
    _make_handoff(
        tmp_path, "Test", "2026-02-25",
        "## Decisions\n\nChose Regular Merge.\n"
    )
    # Literal: case-insensitive — matches
    assert len(search_handoffs(tmp_path, "regular merge")) == 1
    # Regex: case-sensitive — lowercase doesn't match titlecase
    assert len(search_handoffs(tmp_path, "regular merge", regex=True)) == 0
    # Regex: exact case — matches
    assert len(search_handoffs(tmp_path, "Regular Merge", regex=True)) == 1
```

**Step 2: Add test for unclosed frontmatter (#9)**

Add to `TestParseHandoff`:

```python
def test_unclosed_frontmatter_treated_as_no_frontmatter(self, tmp_path: Path) -> None:
    """Opening --- with no closing --- is treated as no frontmatter."""
    handoff = tmp_path / "test.md"
    handoff.write_text(
        "---\n"
        "title: Broken\n"
        "no closing delimiter\n"
        "\n"
        "## Goal\n"
        "\n"
        "Do something.\n"
    )
    result = parse_handoff(handoff)
    assert result.frontmatter == {}
    assert len(result.sections) == 1
    assert result.sections[0].heading == "## Goal"
```

**Step 3: Add test for regex metacharacters in literal mode (#10)**

Add to `TestSearchHandoffs`:

```python
def test_literal_escapes_regex_metacharacters(self, tmp_path: Path) -> None:
    """Literal search escapes regex metacharacters via re.escape()."""
    _make_handoff(
        tmp_path, "Test", "2026-02-25",
        "## Decisions\n\nChose option (A) over option (B).\n"
    )
    results = search_handoffs(tmp_path, "option (A)")
    assert len(results) == 1
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 24 tests pass (21 existing + 3 new).

**Step 5: Commit**

```
git add tests/test_search.py
git commit -m "test(handoff): add tests for regex case sensitivity, unclosed frontmatter, literal escaping"
```

---

### Task 2: Skipped files tracking (#1, #8)

TDD: add `skipped` parameter to `search_handoffs` so callers can receive information about files that failed to parse. Update `main()` to include `skipped` in JSON output.

**Files:**
- Modify: `scripts/search.py`
- Modify: `tests/test_search.py`

**Step 1: Write the failing test**

Add to `TestSearchHandoffs`:

```python
def test_unreadable_file_reported_in_skipped(self, tmp_path: Path) -> None:
    """Unreadable files are reported via skipped parameter, not silently dropped."""
    _make_handoff(
        tmp_path, "Good", "2026-02-25",
        "## Goal\n\nSearchable content.\n"
    )
    bad_file = tmp_path / "2026-02-24_00-00_bad.md"
    bad_file.write_bytes(b"---\ntitle: Bad\n---\n\n## Goal\n\n\xff\xfe invalid\n")

    skipped: list[dict] = []
    results = search_handoffs(tmp_path, "content", skipped=skipped)
    assert len(results) == 1
    assert len(skipped) == 1
    assert "bad.md" in skipped[0]["file"]
    assert skipped[0]["reason"]  # Non-empty reason string
```

Add to `TestSearchCLI`:

```python
def test_skipped_files_in_json_output(self, tmp_path: Path) -> None:
    """JSON output includes skipped field."""
    handoffs_dir = tmp_path / "handoffs"
    handoffs_dir.mkdir()

    with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
        output = search_main(["anything"])

    result = json.loads(output)
    assert "skipped" in result
    assert result["skipped"] == []
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_search.py::TestSearchHandoffs::test_unreadable_file_reported_in_skipped tests/test_search.py::TestSearchCLI::test_skipped_files_in_json_output -v`

Expected: FAIL — `search_handoffs` doesn't accept `skipped` parameter; JSON output has no `skipped` field.

**Step 3: Implement skipped tracking in `search_handoffs`**

In `scripts/search.py`, change the `search_handoffs` signature:

```python
def search_handoffs(
    handoffs_dir: Path,
    query: str,
    *,
    regex: bool = False,
    skipped: list[dict] | None = None,
) -> list[dict]:
```

Change the except block (currently lines 195-196):

```python
        except (OSError, UnicodeDecodeError) as e:
            if skipped is not None:
                skipped.append({"file": path.name, "reason": str(e)})
            continue  # Skip unreadable or malformed files
```

**Step 4: Add skipped to `main()` JSON output**

In `main()`, replace the search call and JSON output (currently lines 239-247):

```python
    handoffs_dir = get_handoffs_dir()
    skipped_files: list[dict] = []
    results = search_handoffs(handoffs_dir, args.query, regex=args.regex, skipped=skipped_files)

    return json.dumps({
        "query": args.query,
        "total_matches": len(results),
        "results": results,
        "skipped": skipped_files,
        "error": None,
    })
```

Also update the regex error JSON path (currently line 237) to include `"skipped": []`.

**Step 5: Run all tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 26 tests pass (24 + 2 new).

**Step 6: Commit**

```
git add scripts/search.py tests/test_search.py
git commit -m "fix(handoff): report skipped files in search results instead of silent drop"
```

---

### Task 3: Missing directory error (#2)

TDD: when the handoffs directory doesn't exist, report an error in JSON instead of returning `total_matches: 0, error: null`.

**Files:**
- Modify: `scripts/search.py`
- Modify: `tests/test_search.py`

**Step 1: Write the failing test**

Add to `TestSearchCLI`:

```python
def test_missing_directory_reports_error(self, tmp_path: Path) -> None:
    """Missing handoffs directory reports error, not silent empty results."""
    nonexistent = tmp_path / "nonexistent"

    with patch("scripts.search.get_handoffs_dir", return_value=nonexistent):
        output = search_main(["anything"])

    result = json.loads(output)
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert str(nonexistent) in result["error"]
    assert result["total_matches"] == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search.py::TestSearchCLI::test_missing_directory_reports_error -v`

Expected: FAIL — `result["error"]` is `None`.

**Step 3: Add directory check in `main()`**

In `main()`, after `handoffs_dir = get_handoffs_dir()` and before calling `search_handoffs`, add:

```python
    if not handoffs_dir.exists():
        return json.dumps({
            "query": args.query,
            "total_matches": 0,
            "results": [],
            "skipped": [],
            "error": f"Handoffs directory not found: {handoffs_dir}",
        })
```

**Step 4: Run all tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 27 tests pass (26 + 1 new).

Note: `TestSearchHandoffs::test_missing_directory_returns_empty` still passes — it tests `search_handoffs()` directly, not `main()`. The library function still returns `[]` for missing directories (defensive).

**Step 5: Commit**

```
git add scripts/search.py tests/test_search.py
git commit -m "fix(handoff): report error when handoffs directory not found"
```

---

### Task 4: Project source indicator (#3)

TDD: `get_project_name()` returns `(name, source)` so callers know whether the name came from git or cwd fallback. `main()` includes `project_source` in JSON output.

**Files:**
- Modify: `scripts/search.py`
- Modify: `tests/test_search.py`

**Step 1: Write the failing tests**

Add to `TestSearchCLI`:

```python
def test_project_source_git(self, tmp_path: Path) -> None:
    """JSON output includes project_source when resolved via git."""
    handoffs_dir = tmp_path / "handoffs"
    handoffs_dir.mkdir()

    with patch("scripts.search.get_project_name", return_value=("test", "git")):
        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main(["anything"])

    result = json.loads(output)
    assert result["project_source"] == "git"

def test_project_source_cwd_fallback(self, tmp_path: Path) -> None:
    """JSON output shows project_source='cwd' when git fails."""
    handoffs_dir = tmp_path / "handoffs"
    handoffs_dir.mkdir()

    with patch("scripts.search.get_project_name", return_value=("test", "cwd")):
        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main(["anything"])

    result = json.loads(output)
    assert result["project_source"] == "cwd"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_search.py::TestSearchCLI::test_project_source_git tests/test_search.py::TestSearchCLI::test_project_source_cwd_fallback -v`

Expected: FAIL — `project_source` not in JSON; `get_project_name` returns string not tuple.

**Step 3: Change `get_project_name` to return tuple**

```python
def get_project_name() -> tuple[str, str]:
    """Get project name from git root directory, falling back to current directory name.

    Returns:
        (project_name, source) where source is "git" or "cwd".
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name, "git"
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return Path.cwd().name, "cwd"
```

**Step 4: Update `get_handoffs_dir` to unpack**

```python
def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    name, _ = get_project_name()
    return Path.home() / ".claude" / "handoffs" / name
```

**Step 5: Add `project_source` to `main()` JSON output**

At the top of `main()`, after `args = parser.parse_args(argv)`, add:

```python
    _, project_source = get_project_name()
```

Then add `"project_source": project_source` to all three JSON output paths in `main()`:
1. The directory-not-found error path
2. The regex error path (added in Task 5)
3. The success path

**Step 6: Run all tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 29 tests pass (27 + 2 new).

**Step 7: Commit**

```
git add scripts/search.py tests/test_search.py
git commit -m "fix(handoff): include project_source in search output to surface fallback"
```

---

### Task 5: Compile regex once (#4)

Refactor: remove duplicate regex validation from `main()`. The pattern is compiled once inside `search_handoffs`; `main()` catches `re.error` from the call.

**Files:**
- Modify: `scripts/search.py`

**Step 1: Remove pre-validation from `main()`**

Delete the regex validation block (currently lines 232-237):

```python
    # DELETE THIS BLOCK:
    if args.regex:
        try:
            re.compile(args.query)
        except re.error as e:
            return json.dumps({"query": args.query, "total_matches": 0, "results": [], "error": f"Invalid regex: {e}"})
```

**Step 2: Wrap `search_handoffs` call in try/except**

Replace the existing search call with:

```python
    skipped_files: list[dict] = []
    try:
        results = search_handoffs(handoffs_dir, args.query, regex=args.regex, skipped=skipped_files)
    except re.error as e:
        return json.dumps({
            "query": args.query,
            "total_matches": 0,
            "results": [],
            "skipped": skipped_files,
            "project_source": project_source,
            "error": f"Invalid regex: {e}",
        })
```

**Step 3: Run all tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 29 tests pass. `test_invalid_regex_returns_error` still passes — the error is now caught at a different site but produces the same JSON output.

**Step 4: Commit**

```
git add scripts/search.py
git commit -m "refactor(handoff): compile regex once in search_handoffs, remove duplicate validation"
```

---

### Task 6: Documentation (#5, #11)

Update docstring and SKILL.md to document regex case sensitivity and skipped file handling.

**Files:**
- Modify: `scripts/search.py`
- Modify: `skills/searching-handoffs/SKILL.md`

**Step 1: Update `search_handoffs` docstring (#11)**

Change the `regex` parameter doc (line 166):

From:
```python
        regex: If True, treat query as regex. If False, literal case-insensitive match.
```

To:
```python
        regex: If True, treat query as regex (case-sensitive). If False, literal case-insensitive match.
            Users can embed (?i) in their regex for case-insensitive regex search.
```

**Step 2: Add regex case sensitivity note to SKILL.md (#5)**

After the `--regex` line in the Procedure section, add:

```markdown
   **Note:** Literal search is case-insensitive. Regex search is case-sensitive by default — users can add `(?i)` to their pattern for case-insensitive regex (e.g., `(?i)merge.*strategy`).
```

**Step 3: Add skipped files handling to SKILL.md**

In the "Handle errors" section, after the `total_matches` check, add:

```markdown
   - If `skipped` is non-empty: mention "N files could not be read" after results.
   - If `project_source` is `"cwd"`: mention "Note: project name resolved from directory name (git not available)."
```

**Step 4: Run tests (sanity check)**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 29 tests pass. (No logic changes in this task.)

**Step 5: Commit**

```
git add scripts/search.py skills/searching-handoffs/SKILL.md
git commit -m "docs(handoff): document regex case sensitivity and skipped file reporting"
```

---

### Task 7: Cleanup (#12, #13)

Update test labels to reference their source document. Remove unused `line_start` field from `Section` dataclass.

**Files:**
- Modify: `scripts/search.py`
- Modify: `tests/test_search.py`

**Step 1: Update test docstrings with document reference (#12)**

In `tests/test_search.py`, update the three test docstrings that use opaque labels:

```python
# test_headings_inside_code_fences_ignored (line 87):
"""A3 (handoff-search-implementation): ## lines inside fenced code blocks must not create sections."""

# test_unterminated_fence_does_not_crash (line 110):
"""A8 (handoff-search-implementation): Unterminated fence suppresses subsequent sections (graceful degradation)."""

# test_direct_execution_via_subprocess (line 294):
"""A9 (handoff-search-implementation): Verify __main__ path works under direct script execution."""
```

**Step 2: Remove `line_start` from `Section` dataclass (#13)**

In `scripts/search.py`, change the `Section` dataclass:

```python
@dataclass
class Section:
    heading: str
    level: int
    content: str
```

Remove `line_start=current_start` from both `Section()` constructor calls in `parse_sections` (currently lines 101 and 116). Also remove the `current_start = 0` initialization (line 86) and the `current_start = i + 1` assignment (line 105).

**Step 3: Run all tests**

Run: `uv run pytest tests/test_search.py -v`

Expected: All 29 tests pass. No test asserts on `line_start`.

**Step 4: Commit**

```
git add scripts/search.py tests/test_search.py
git commit -m "chore(handoff): add doc refs to test labels, remove unused Section.line_start"
```

---

## Final Verification

After all 7 tasks:

1. Run full test suite: `uv run pytest tests/ -v` — expect 29+ tests pass
2. Run linter: `uv run ruff check scripts/ tests/` — expect clean
3. Verify JSON output manually: `python3 scripts/search.py "test"` — expect `skipped`, `project_source`, `error` fields present
4. Push and verify PR #27 is updated

## Expected Final State

**JSON output envelope (after all fixes):**

```json
{
  "query": "search term",
  "total_matches": 2,
  "results": [...],
  "skipped": [{"file": "bad.md", "reason": "..."}],
  "project_source": "git",
  "error": null
}
```

**Test count:** 29 (21 original + 3 existing-behavior + 2 skipped + 1 missing-dir + 2 project-source)

**Commits:** 7 (one per task)
