# Handoff Search/Query Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/handoff:search <query>` — section-aware search across handoff history with structured JSON results.

**Architecture:** Python search script parses handoff markdown into section trees, searches within sections, outputs JSON. Skill wrapper invokes script and formats results. Project utility functions (`get_project_name`, `get_handoffs_dir`) are inlined in `search.py` (duplicated from `cleanup.py`). No shared modules — avoids `sys.path` issues with direct script execution.

**Tech Stack:** Python 3.11+, pytest, dataclasses, re, json, argparse

**Design doc:** `docs/plans/2026-02-26-handoff-search-design.md`

**Amendments:** This plan was revised after an adversarial Codex review (5 turns, 9 findings) and a subsequent evaluative deep review (6 turns, 11 resolved). Key changes from adversarial review: dropped `lib/` extraction (P1a: breaks hook execution), added code-fence tracking (P2a), fixed mock patch targets (P0), added `UnicodeDecodeError` handling (P1b). Key changes from deep review: fixed skill CWD bug (A6: P0), fixed heading duplication (A7), added unterminated fence test (A8), added `__main__` subprocess test (A9).

---

## Pre-flight

Before starting, verify:
- Branch: `feature/handoff-search` (create from `main`)
- Working directory: `packages/plugins/handoff/`
- Tests pass: `cd packages/plugins/handoff && uv run pytest -v` (26 cleanup tests)

---

## Dependency Graph

```
Task 1 (parser) ──► Task 2 (search logic) ──► Task 3 (CLI) ──► Task 4 (skill) ──► Task 5 (version bump)
```

All tasks are sequential. `scripts/cleanup.py` and `tests/test_cleanup.py` are NOT modified.

---

### Task 1: Markdown Parser with Tests

**Files:**
- Create: `scripts/search.py` (parser portion only — no CLI yet)
- Create: `tests/test_search.py` (parser tests)

**Data model (dataclasses):**

```python
from dataclasses import dataclass


@dataclass
class Section:
    heading: str
    level: int
    content: str
    line_start: int


@dataclass
class HandoffFile:
    path: str
    frontmatter: dict[str, str]
    sections: list[Section]
```

**Step 1: Write parser tests in `tests/test_search.py`**

```python
"""Tests for search.py — handoff search script."""

from pathlib import Path

from scripts.search import HandoffFile, Section, parse_handoff


class TestParseHandoff:
    """Tests for parse_handoff — markdown parsing."""

    def test_extracts_frontmatter(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\n"
            'title: "My Handoff"\n'
            "date: 2026-02-25\n"
            "type: handoff\n"
            "---\n"
            "\n"
            "# My Handoff\n"
            "\n"
            "## Goal\n"
            "\n"
            "Do something.\n"
        )
        result = parse_handoff(handoff)
        assert result.frontmatter["title"] == "My Handoff"
        assert result.frontmatter["date"] == "2026-02-25"
        assert result.frontmatter["type"] == "handoff"

    def test_splits_sections(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\n---\n"
            "\n"
            "## Goal\n"
            "\n"
            "The goal.\n"
            "\n"
            "## Decisions\n"
            "\n"
            "### Decision A\n"
            "\n"
            "We chose A.\n"
            "\n"
            "### Decision B\n"
            "\n"
            "We chose B.\n"
            "\n"
            "## Next Steps\n"
            "\n"
            "Do more.\n"
        )
        result = parse_handoff(handoff)
        assert len(result.sections) == 3
        assert result.sections[0].heading == "## Goal"
        assert "The goal." in result.sections[0].content
        assert result.sections[1].heading == "## Decisions"
        assert "Decision A" in result.sections[1].content
        assert "Decision B" in result.sections[1].content
        assert result.sections[2].heading == "## Next Steps"

    def test_no_sections(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text("---\ntitle: Minimal\n---\n\nJust some text.\n")
        result = parse_handoff(handoff)
        assert result.sections == []
        assert result.frontmatter["title"] == "Minimal"

    def test_no_frontmatter(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text("## Goal\n\nDo something.\n")
        result = parse_handoff(handoff)
        assert result.frontmatter == {}
        assert len(result.sections) == 1
        assert result.sections[0].heading == "## Goal"

    def test_path_stored(self, tmp_path: Path) -> None:
        handoff = tmp_path / "2026-02-25_22-34_test.md"
        handoff.write_text("---\ntitle: Test\n---\n")
        result = parse_handoff(handoff)
        assert result.path == str(handoff)

    def test_headings_inside_code_fences_ignored(self, tmp_path: Path) -> None:
        """A3: ## lines inside fenced code blocks must not create sections."""
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\n---\n"
            "\n"
            "## Real Section\n"
            "\n"
            "Some content.\n"
            "\n"
            "```markdown\n"
            "## Fake Section Inside Fence\n"
            "\n"
            "This should not be a section.\n"
            "```\n"
            "\n"
            "More content in real section.\n"
        )
        result = parse_handoff(handoff)
        assert len(result.sections) == 1
        assert result.sections[0].heading == "## Real Section"
        assert "Fake Section Inside Fence" in result.sections[0].content

    def test_unterminated_fence_does_not_crash(self, tmp_path: Path) -> None:
        """A8: Unterminated fence suppresses subsequent sections (graceful degradation)."""
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\n---\n"
            "\n"
            "## Before Fence\n"
            "\n"
            "Content before.\n"
            "\n"
            "```python\n"
            "# unclosed fence\n"
            "\n"
            "## Suppressed Section\n"
            "\n"
            "This section is invisible.\n"
        )
        result = parse_handoff(handoff)
        # Only the section before the unterminated fence is found.
        # The suppressed section is absorbed — graceful degradation, not crash.
        assert len(result.sections) == 1
        assert result.sections[0].heading == "## Before Fence"
```

**Step 2: Run tests to verify they fail**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py -v
```

Expected: FAIL — `scripts.search` module doesn't exist yet.

**Step 3: Write `parse_handoff` in `scripts/search.py`**

```python
#!/usr/bin/env python3
"""search.py - Search handoff history for decisions, learnings, and context.

Parses handoff markdown files into section trees, searches within sections,
and outputs structured JSON results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Section:
    heading: str
    level: int
    content: str
    line_start: int


@dataclass
class HandoffFile:
    path: str
    frontmatter: dict[str, str]
    sections: list[Section]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter from markdown text.

    Returns (frontmatter_dict, remaining_text). Handles simple key: value
    pairs and quoted strings. Does not depend on PyYAML.

    Multiline YAML values (e.g., files: lists) are silently skipped —
    only single-line key: value pairs are extracted. This is sufficient
    for search (which uses title, date, type).
    """
    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[4:end]  # Skip opening ---\n
    remaining = text[end + 4:]  # Skip closing ---\n

    frontmatter: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Strip surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            frontmatter[key] = value

    return frontmatter, remaining


def parse_sections(text: str) -> list[Section]:
    """Split markdown text into ## sections.

    Each section includes everything from its ## heading until the next
    ## heading or EOF. ### subsections are included within their parent.
    Code-fenced regions are tracked to avoid treating ## lines inside
    fences as section boundaries. The heading line itself is NOT included
    in section.content to avoid duplication when displaying heading + content.
    """
    sections: list[Section] = []
    lines = text.splitlines(keepends=True)
    current_heading = ""
    current_lines: list[str] = []
    current_start = 0
    inside_fence = False

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.startswith("```"):
            inside_fence = not inside_fence
        if not inside_fence and line.startswith("## "):
            # Save previous section if any
            if current_heading:
                content = "".join(current_lines).strip()
                sections.append(Section(
                    heading=current_heading,
                    level=2,
                    content=content,
                    line_start=current_start,
                ))
            current_heading = line.strip()
            current_lines = []
            current_start = i + 1  # 1-indexed
        elif current_heading:
            current_lines.append(line)

    # Save last section
    if current_heading:
        content = "".join(current_lines).strip()
        sections.append(Section(
            heading=current_heading,
            level=2,
            content=content,
            line_start=current_start,
        ))

    return sections


def parse_handoff(path: Path) -> HandoffFile:
    """Parse a handoff markdown file into structured data."""
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    sections = parse_sections(body)
    return HandoffFile(path=str(path), frontmatter=frontmatter, sections=sections)
```

**Step 4: Run parser tests**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py -v
```

Expected: 7 tests pass (6 parser + 1 unterminated fence).

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/search.py packages/plugins/handoff/tests/test_search.py
git commit -m "feat(handoff): add markdown parser for handoff files"
```

---

### Task 2: Search Logic with Tests

**Files:**
- Modify: `scripts/search.py` (add `search_handoffs` function)
- Modify: `tests/test_search.py` (add search tests)

**Step 1: Write search tests**

Add to `tests/test_search.py`:

```python
import json
from unittest.mock import patch

from scripts.search import search_handoffs


def _make_handoff(path: Path, title: str, date: str, content: str) -> Path:
    """Helper: create a synthetic handoff file."""
    handoff = path / f"{date}_00-00_{title.lower().replace(' ', '-')}.md"
    handoff.write_text(
        f"---\n"
        f'title: "{title}"\n'
        f"date: {date}\n"
        f"type: handoff\n"
        f"---\n\n"
        f"{content}"
    )
    return handoff


class TestSearchHandoffs:
    """Tests for search_handoffs — search logic."""

    def test_literal_match_case_insensitive(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Test", "2026-02-25",
            "## Decisions\n\nWe chose Regular Merge.\n"
        )
        results = search_handoffs(tmp_path, "regular merge")
        assert len(results) == 1
        assert results[0]["section_heading"] == "## Decisions"
        assert "Regular Merge" in results[0]["section_content"]

    def test_regex_match(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Test", "2026-02-25",
            "## Decisions\n\nChose option A over B.\n"
        )
        results = search_handoffs(tmp_path, r"option [AB]", regex=True)
        assert len(results) == 1

    def test_no_matches_returns_empty(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Test", "2026-02-25",
            "## Goal\n\nBuild something.\n"
        )
        results = search_handoffs(tmp_path, "nonexistent_xyz")
        assert results == []

    def test_match_in_heading(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Test", "2026-02-25",
            "## Codebase Knowledge\n\nSome details.\n"
        )
        results = search_handoffs(tmp_path, "codebase knowledge")
        assert len(results) == 1
        assert results[0]["section_heading"] == "## Codebase Knowledge"

    def test_multiple_files_sorted_by_date_descending(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Old", "2026-01-01",
            "## Decisions\n\nDecision about merging.\n"
        )
        _make_handoff(
            tmp_path, "New", "2026-02-25",
            "## Decisions\n\nDecision about merging.\n"
        )
        results = search_handoffs(tmp_path, "merging")
        assert len(results) == 2
        assert results[0]["date"] == "2026-02-25"
        assert results[1]["date"] == "2026-01-01"

    def test_multiple_sections_in_same_file(self, tmp_path: Path) -> None:
        _make_handoff(
            tmp_path, "Test", "2026-02-25",
            "## Goal\n\nSearch feature.\n\n## Learnings\n\nSearch is useful.\n"
        )
        results = search_handoffs(tmp_path, "search")
        assert len(results) == 2

    def test_searches_archive_subdirectory(self, tmp_path: Path) -> None:
        archive = tmp_path / ".archive"
        archive.mkdir()
        _make_handoff(
            archive, "Archived", "2026-01-15",
            "## Decisions\n\nOld decision about caching.\n"
        )
        results = search_handoffs(tmp_path, "caching")
        assert len(results) == 1
        assert results[0]["archived"] is True

    def test_skips_non_md_files(self, tmp_path: Path) -> None:
        txt = tmp_path / "notes.txt"
        txt.write_text("## Decisions\n\nSomething about merging.\n")
        results = search_handoffs(tmp_path, "merging")
        assert results == []

    def test_missing_directory_returns_empty(self, tmp_path: Path) -> None:
        results = search_handoffs(tmp_path / "nonexistent", "anything")
        assert results == []
```

**Step 2: Run tests to verify they fail**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py::TestSearchHandoffs -v
```

Expected: FAIL — `search_handoffs` not defined.

**Step 3: Implement `search_handoffs` in `scripts/search.py`**

Add to `scripts/search.py`:

```python
def search_handoffs(
    handoffs_dir: Path,
    query: str,
    *,
    regex: bool = False,
) -> list[dict]:
    """Search handoff files for matching sections.

    Args:
        handoffs_dir: Directory containing handoff .md files (with optional .archive/ subdirectory)
        query: Search string or regex pattern
        regex: If True, treat query as regex. If False, literal case-insensitive match.

    Returns:
        List of result dicts sorted by date descending. Each dict contains:
        file, title, date, type, archived, section_heading, section_content
    """
    if not handoffs_dir.exists():
        return []

    # Compile search pattern
    flags = 0 if regex else re.IGNORECASE
    if not regex:
        query = re.escape(query)
    pattern = re.compile(query, flags)

    results: list[dict] = []

    # Collect .md files from top-level and .archive/
    md_files: list[tuple[Path, bool]] = []
    for f in handoffs_dir.glob("*.md"):
        md_files.append((f, False))
    archive_dir = handoffs_dir / ".archive"
    if archive_dir.exists():
        for f in archive_dir.glob("*.md"):
            md_files.append((f, True))

    for path, archived in md_files:
        try:
            handoff = parse_handoff(path)
        except (OSError, UnicodeDecodeError):
            continue  # Skip unreadable or malformed files

        for section in handoff.sections:
            search_text = f"{section.heading}\n{section.content}"
            if pattern.search(search_text):
                results.append({
                    "file": path.name,
                    "title": handoff.frontmatter.get("title", path.stem),
                    "date": handoff.frontmatter.get("date", ""),
                    "type": handoff.frontmatter.get("type", "handoff"),
                    "archived": archived,
                    "section_heading": section.heading,
                    "section_content": section.content,
                })

    # Sort by date descending
    results.sort(key=lambda r: r["date"], reverse=True)
    return results
```

**Step 4: Run search tests**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py::TestSearchHandoffs -v
```

Expected: 9 tests pass.

**Step 5: Run all search tests together**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py -v
```

Expected: 16 tests pass (7 parser + 9 search).

**Step 6: Commit**

```bash
git add packages/plugins/handoff/scripts/search.py packages/plugins/handoff/tests/test_search.py
git commit -m "feat(handoff): add section-aware search across handoff files"
```

---

### Task 3: CLI Entry Point with Integration Test

**Files:**
- Modify: `scripts/search.py` (add `get_project_name`, `get_handoffs_dir`, `main()`, argparse)
- Modify: `tests/test_search.py` (add CLI/integration test)

**Step 1: Write integration test**

Add to `tests/test_search.py`:

```python
from scripts.search import main as search_main


class TestSearchCLI:
    """Integration tests for the CLI entry point."""

    def test_end_to_end_json_output(self, tmp_path: Path) -> None:
        """Full pipeline: create handoffs, run search, verify JSON."""
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        _make_handoff(
            handoffs_dir, "Session One", "2026-02-20",
            "## Decisions\n\n### Chose Python\n\nPython over Rust for speed of dev.\n"
        )
        archive = handoffs_dir / ".archive"
        archive.mkdir()
        _make_handoff(
            archive, "Old Session", "2026-01-15",
            "## Learnings\n\nPython parsing is fast enough.\n"
        )

        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main(["Python"])

        result = json.loads(output)
        assert result["query"] == "Python"
        assert result["total_matches"] == 2
        assert result["results"][0]["date"] == "2026-02-20"
        assert result["results"][1]["archived"] is True
        assert result["error"] is None

    def test_no_results(self, tmp_path: Path) -> None:
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()

        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main(["nonexistent_query"])

        result = json.loads(output)
        assert result["total_matches"] == 0
        assert result["results"] == []

    def test_invalid_regex_returns_error(self, tmp_path: Path) -> None:
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()

        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main(["[invalid", "--regex"])

        result = json.loads(output)
        assert result["error"] is not None
        assert "Invalid regex" in result["error"]

    def test_regex_flag(self, tmp_path: Path) -> None:
        handoffs_dir = tmp_path / "handoffs"
        handoffs_dir.mkdir()
        _make_handoff(
            handoffs_dir, "Test", "2026-02-25",
            "## Decisions\n\nChose option-A over option-B.\n"
        )

        with patch("scripts.search.get_handoffs_dir", return_value=handoffs_dir):
            output = search_main([r"option-[AB]", "--regex"])

        result = json.loads(output)
        assert result["total_matches"] == 1

    def test_direct_execution_via_subprocess(self) -> None:
        """A9: Verify __main__ path works under direct script execution."""
        import subprocess

        script = Path(__file__).parent.parent / "scripts" / "search.py"
        result = subprocess.run(
            ["python3", str(script), "nonexistent_query_xyz"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "total_matches" in output
        assert output["error"] is None
```

**Note:** Mock target is `scripts.search.get_handoffs_dir` (the lookup site), NOT `lib.project.get_handoffs_dir`. Python's `from` import creates a new binding in the importing module's namespace — patching the original doesn't affect the already-bound name.

**Step 2: Run to verify failure**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py::TestSearchCLI -v
```

Expected: FAIL — `main` not defined in `scripts.search`.

**Step 3: Add project utilities and CLI to `scripts/search.py`**

Add to `scripts/search.py` (before `main`), inlined from `cleanup.py`:

```python
import json
import subprocess
import sys


def get_project_name() -> str:
    """Get project name from git root directory, falling back to current directory name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return Path.cwd().name


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    return Path.home() / ".claude" / "handoffs" / get_project_name()


def main(argv: list[str] | None = None) -> str:
    """CLI entry point. Returns JSON string.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None).

    Returns:
        JSON string with search results.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Search handoff history")
    parser.add_argument("query", help="Search query (text or regex)")
    parser.add_argument("--regex", action="store_true", help="Treat query as regex")
    args = parser.parse_args(argv)

    # Validate regex before searching
    if args.regex:
        try:
            re.compile(args.query)
        except re.error as e:
            return json.dumps({"query": args.query, "total_matches": 0, "results": [], "error": f"Invalid regex: {e}"})

    handoffs_dir = get_handoffs_dir()
    results = search_handoffs(handoffs_dir, args.query, regex=args.regex)

    return json.dumps({
        "query": args.query,
        "total_matches": len(results),
        "results": results,
        "error": None,
    })


if __name__ == "__main__":
    print(main())
    sys.exit(0)
```

**Step 4: Run CLI tests**

```bash
cd packages/plugins/handoff && uv run pytest tests/test_search.py::TestSearchCLI -v
```

Expected: 5 tests pass (4 mock-based + 1 subprocess).

**Step 5: Run full test suite**

```bash
cd packages/plugins/handoff && uv run pytest -v
```

Expected: 47 tests pass (26 cleanup + 21 search: 7 parser + 9 search + 5 CLI).

**Step 6: Lint**

```bash
cd packages/plugins/handoff && uv run ruff check scripts/search.py tests/test_search.py
```

Expected: Clean.

**Step 7: Commit**

```bash
git add packages/plugins/handoff/scripts/search.py packages/plugins/handoff/tests/test_search.py
git commit -m "feat(handoff): add CLI entry point for search script"
```

---

### Task 4: Skill (`skills/searching-handoffs/SKILL.md`)

**Files:**
- Create: `skills/searching-handoffs/SKILL.md`

**Step 1: Create skill directory**

```bash
mkdir -p packages/plugins/handoff/skills/searching-handoffs
```

**Step 2: Write SKILL.md**

```markdown
---
name: searching-handoffs
description: Search across handoff history for decisions, learnings, and context. Use when user says "search handoffs", "find in handoffs", "what did we decide about", or runs /handoff:search.
argument-hint: "<query> [--regex]"
---

# Search Handoffs

Search active and archived handoffs for the current project. Returns full matching sections.

## Procedure

When user runs `/handoff:search <query>`:

1. **Run the search script:**

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/search.py" "<query>"
   ```

   If user passed `--regex`, append `--regex` to the command.

   If `${CLAUDE_PLUGIN_ROOT}` is not set (e.g., running from the development repo), use:
   ```bash
   python3 "$(git rev-parse --show-toplevel)/packages/plugins/handoff/scripts/search.py" "<query>"
   ```

   **Important:** Do NOT `cd` into the plugin directory before running. `get_project_name()` resolves the project from the current working directory — changing CWD to the plugin directory would resolve to the plugin's repo name instead of the user's project.

2. **Parse JSON output** from stdout.

3. **Handle errors:**
   - If `error` is non-null: display the error message and stop.
   - If `total_matches` is 0: "No handoffs matched `<query>`."

4. **Present results:**
   - **1-5 results:** For each result, show:
     ```
     **<title>** (<date>, <type>) — <section_heading>
     <section_content>
     ```
   - **6+ results:** Show summary table of all matches:
     ```
     | Date | Title | Section | Archived |
     ```
     Then show the 3 most recent results in full.
     Offer: "Want to see the rest?"

## Examples

**User:** `/handoff:search merge strategy`

**Result (1 match):**
> **PR #26 reviewed, merged** (2026-02-25, handoff) — ## Decisions
>
> ### Regular merge over squash merge for PR #26
>
> **Choice:** Regular merge preserving all 22 commits.
> ...

**User:** `/handoff:search --regex "option-[AB]"`

Searches using regex pattern.

**User:** `/handoff:search nonexistent_thing`

> No handoffs matched `nonexistent_thing`.
```

**Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/searching-handoffs/
git commit -m "feat(handoff): add searching-handoffs skill"
```

---

### Task 5: Version Bump and Final Verification

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Bump versions**

Change `"version": "1.1.1"` to `"version": "1.2.0"` in `.claude-plugin/plugin.json`.
Change `version = "1.1.0"` to `version = "1.2.0"` in `pyproject.toml`.

**Step 2: Add superseded banner to design doc**

Add a banner at the top of `docs/plans/2026-02-26-handoff-search-design.md` (after the YAML block) and update the stale sections:

- Change `status: approved` to `status: superseded-by-implementation-plan` in the YAML block
- Add after the YAML block: `> **Superseded:** The architecture described here was amended during Codex review. The implementation plan (`docs/plans/2026-02-26-handoff-search-implementation.md`) is the authoritative reference. Key changes: `lib/project.py` extraction was dropped (P1a), invocation changed from `uv run` to `python3` direct execution (A6).`
- In the "Key Decisions" table (line 24): change `Extract to lib/project.py` to `Inline in search.py (amended: lib/ extraction dropped — see implementation plan)`
- In the "Shared Module" section (lines 142-146): replace content with `> Superseded: shared module was dropped. Functions are inlined in `search.py`. See implementation plan Amendment A1.`

**Step 3: Run full test suite**

```bash
cd packages/plugins/handoff && uv run pytest -v
```

Expected: 47 tests pass (26 cleanup + 21 search).

**Step 4: Lint all modified files**

```bash
cd packages/plugins/handoff && uv run ruff check scripts/ tests/
```

Expected: Clean.

**Step 5: Manual smoke test**

```bash
cd packages/plugins/handoff && python3 scripts/search.py "merge" | python3 -m json.tool
```

Expected: JSON output with results from real handoff files. Uses `python3` direct execution (not `uv run`) to verify the `__main__` path.

**Step 6: Commit**

```bash
git add packages/plugins/handoff/.claude-plugin/plugin.json packages/plugins/handoff/pyproject.toml docs/plans/2026-02-26-handoff-search-design.md
git commit -m "chore(handoff): bump version to 1.2.0, mark design doc superseded"
```

---

## Verification Checklist

After all tasks complete:

- [ ] `uv run pytest -v` — 47 tests pass (26 cleanup + 21 search)
- [ ] `uv run ruff check scripts/ tests/` — clean
- [ ] `python3 scripts/search.py "merge"` — returns valid JSON (direct execution)
- [ ] `python3 scripts/search.py "[invalid" --regex` — returns error JSON
- [ ] `python3 scripts/cleanup.py` — still works (untouched)
- [ ] Skill file exists at `skills/searching-handoffs/SKILL.md`
- [ ] Skill does NOT `cd` into plugin directory (uses `python3` with absolute path)
- [ ] `scripts/cleanup.py` is NOT modified (no import changes)
- [ ] `plugin.json` version is `1.2.0`
- [ ] `pyproject.toml` version is `1.2.0`
- [ ] Design doc `status` is `superseded-by-implementation-plan`

---

## Codex Review Amendments

### Round 1: Adversarial Review (5/10 turns, 9 resolved)

| ID | Severity | Finding | Amendment |
|----|----------|---------|-----------|
| A1 | P1a (Critical) | `lib/` extraction breaks cleanup hook — direct script execution sets `sys.path[0]` to `scripts/`, not package root. `cleanup.main()` swallows the `ModuleNotFoundError` silently. | Dropped `lib/` extraction entirely. Inlined `get_project_name`/`get_handoffs_dir` in `search.py`. |
| A2 | P0 (Bug) | CLI tests patch `lib.project.get_handoffs_dir` but Python `from` imports create a separate binding — mock doesn't reach `main()`. | Changed mock target to `scripts.search.get_handoffs_dir`. |
| A3 | P2a | `parse_sections` splits on `## ` with no code-fence tracking — creates ghost sections from code blocks. | Added `inside_fence` toggle in `parse_sections`. Added fence test. Removed redundant `### ` guard. |
| A4 | P1b | `UnicodeDecodeError` is a `ValueError`, not `OSError` — one malformed file crashes entire search. | Changed `except OSError` to `except (OSError, UnicodeDecodeError)`. |
| A5 | Cleanup | `not line.startswith("### ")` guard is dead code — `"### "` never starts with `"## "`. | Removed (folded into A3). |

### Round 2: Evaluative Deep Review (6/8 turns, 11 resolved)

| ID | Severity | Finding | Amendment |
|----|----------|---------|-----------|
| A6 | P0 (Blocking) | Skill's `cd ${CLAUDE_PLUGIN_ROOT}` changes CWD to plugin directory, causing `get_project_name()` to resolve to the plugin's repo name instead of the user's project. Search returns wrong/empty results silently. | Changed skill invocation to `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/search.py"` (no `cd`). Matches `hooks.json` pattern. |
| A7 | P2 (UX) | `current_lines = [line]` includes heading in `section.content`. When skill displays `heading + content`, heading appears twice. | Changed `current_lines = [line]` to `current_lines = []`. Heading stored in `section.heading` only. |
| A8 | P2 | Unterminated code fence leaves `inside_fence = True` for rest of file, silently suppressing all subsequent `## ` sections. No test coverage. | Added `test_unterminated_fence_does_not_crash` to parser tests. Graceful degradation is acceptable (controlled authoring environment). |
| A9 | P2 | `if __name__ == "__main__"` path is only manual-smoke-tested. Direct execution was the critical A1 concern but has no automated test. | Added `test_direct_execution_via_subprocess` using `subprocess.run(["python3", ...])`. |
| — | Docs | Design doc (`docs/plans/2026-02-26-handoff-search-design.md`) still shows `lib/project.py` architecture with `status: approved`. Actively misleading since plan links to it. | Added superseded banner. Updated stale sections. Changed status to `superseded-by-implementation-plan`. |
| — | Chore | `pyproject.toml` version (`1.1.0`) out of sync with `plugin.json` (`1.1.1`). Plan only bumped `plugin.json`. | Added `pyproject.toml` version bump to Task 5. |

### Deferred (P3 — not blocking)

| Finding | Rationale for deferral |
|---------|----------------------|
| BOM (`\ufeff`) corrupts frontmatter parsing | `cleanup.py` has same gap. Handoffs are written by plugin (no BOMs). Revisit if Windows contributors appear. |
| Tilde fences (`~~~`) not tracked | Valid CommonMark but not used in any handoff file. Revisit if format changes. |
| Shell-escaping of queries with double quotes | Claude Code provides quoting; failure is visible (syntax error), not silent. Revisit if user reports. |
| Import staging across Task 1 and Task 3 | Implementer can concatenate snippets. Plan is clear enough. |
