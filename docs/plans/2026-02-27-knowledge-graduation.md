# Knowledge Graduation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a `/distill` skill that extracts durable knowledge from handoffs into Phase 0 learnings format, with provenance tracking and three-layer deduplication.

**Architecture:** Hybrid script+skill design. `distill.py` handles deterministic work (parsing, subsection extraction, provenance, exact dedup, JSON output). The `distill` skill handles semantic work (synthesizing raw markdown into Phase 0 paragraphs, semantic dedup, confirmation UX, appending to learnings.md). A shared parsing module (`handoff_parsing.py`) is extracted as a prerequisite to avoid a 4th parser copy.

**Tech Stack:** Python 3.11+, pytest, hashlib (SHA-256), JSON stdio contract

**Source:** Codex dialogue (2026-02-27, 5 turns, collaborative, all 5 design questions resolved)

**Review:** Adversarial Codex dialogue (2026-02-27, 5 turns, 11 amendments). Evaluative Codex dialogue (2026-02-27, 5 turns, 14 amendments + 3 from design dialogue). Final evaluative Codex dialogue (2026-02-27, 6 turns, 5 fixes: B1 session_id fixtures, test count 57→55, call site count, Path import clarification, C1 cross-row dedup documentation). Stress-test adversarial Codex dialogue (2026-02-27, 5/12 turns, early convergence, 22 amendments: 6A+11B+5C — A1 dict key fix, A2 sequential 4→5, A3 parse_handoff error handling, A4 --include-section CLI, A5 missing import, A6 tautology rewrite; B1 preamble merge, B2 UPDATED_SOURCE lookup, B3 dependency graph, B4 learnings warning, B5 test descriptions, +9 net-new tests, test count 55→64). Design: heading_ix with canonical JSON hashing (Task 5), session_id-only identity (Task 5), 4-state dedup with UPDATED_SOURCE (Tasks 5/7).

---

## Prerequisites

Before starting, verify:
- On a feature branch (not `main`) — create `feature/knowledge-graduation`
- In the plugin directory: `packages/plugins/handoff/`
- Tests run: `cd packages/plugins/handoff && uv run pytest` (expect 129 pass)

---

## Task 1: Extract shared parsing module

**Files:**
- Create: `packages/plugins/handoff/scripts/handoff_parsing.py`
- Create: `packages/plugins/handoff/tests/test_handoff_parsing.py`

**Context:** `search.py` and `quality_check.py` each have independent `parse_frontmatter` and `parse_sections` implementations. A 3rd copy for `distill.py` guarantees drift. Extract the `search.py` versions (which return typed dataclasses) into a shared module. Defer migrating `quality_check.py` — it has different heading normalization (strips `## ` prefix to bare names like `"Decisions"`).

**Step 1: Write the failing tests**

```python
# tests/test_handoff_parsing.py
"""Tests for handoff_parsing.py — shared parsing module."""

from pathlib import Path

from scripts.handoff_parsing import (
    HandoffFile,
    Section,
    parse_frontmatter,
    parse_handoff,
    parse_sections,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter."""

    def test_extracts_key_value_pairs(self) -> None:
        text = '---\ntitle: "My Title"\ndate: 2026-02-27\n---\nBody text.'
        fm, remaining = parse_frontmatter(text)
        assert fm["title"] == "My Title"
        assert fm["date"] == "2026-02-27"
        assert remaining.strip() == "Body text."

    def test_strips_surrounding_quotes(self) -> None:
        text = "---\ntitle: \"Quoted\"\ntime: '12:30'\n---\n"
        fm, _ = parse_frontmatter(text)
        assert fm["title"] == "Quoted"
        assert fm["time"] == "12:30"

    def test_no_frontmatter_returns_empty(self) -> None:
        text = "No frontmatter here.\n## Section\nContent."
        fm, remaining = parse_frontmatter(text)
        assert fm == {}
        assert remaining == text

    def test_unclosed_frontmatter_returns_empty(self) -> None:
        text = "---\ntitle: Broken\nno closing\n## Section\n"
        fm, remaining = parse_frontmatter(text)
        assert fm == {}
        assert remaining == text

    def test_skips_multiline_yaml(self) -> None:
        text = "---\ntitle: Test\nfiles:\n  - a.py\n  - b.py\ndate: 2026-01-01\n---\n"
        fm, _ = parse_frontmatter(text)
        assert fm["title"] == "Test"
        assert fm["date"] == "2026-01-01"
        assert "files" not in fm


class TestParseSections:
    """Tests for parse_sections."""

    def test_splits_on_level2_headings(self) -> None:
        text = "## Goal\n\nThe goal.\n\n## Decisions\n\nWe chose A.\n"
        sections = parse_sections(text)
        assert len(sections) == 2
        assert sections[0].heading == "## Goal"
        assert "The goal." in sections[0].content
        assert sections[1].heading == "## Decisions"

    def test_subsections_included_in_parent(self) -> None:
        text = "## Decisions\n\n### Decision A\n\nChose A.\n\n### Decision B\n\nChose B.\n"
        sections = parse_sections(text)
        assert len(sections) == 1
        assert "Decision A" in sections[0].content
        assert "Decision B" in sections[0].content

    def test_backtick_fences_prevent_false_headings(self) -> None:
        text = "## Real\n\nContent.\n\n```\n## Fake\n```\n\nMore content.\n"
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].heading == "## Real"

    def test_tilde_fences_prevent_false_headings(self) -> None:
        text = "## Real\n\nContent.\n\n~~~\n## Fake\n~~~\n\nMore content.\n"
        sections = parse_sections(text)
        assert len(sections) == 1
        assert sections[0].heading == "## Real"

    def test_mixed_fences(self) -> None:
        text = "## A\n\n~~~\n```\n## Fake\n```\n~~~\n\n## B\n\nReal.\n"
        sections = parse_sections(text)
        assert len(sections) == 2

    def test_fence_parity_close_on_same_type_only(self) -> None:
        """~~~ fence is NOT closed by ``` — only same marker type closes."""
        text = "## A\n\n~~~\n```\n## Fake\n```\n## Also Fake\n~~~\n\n## B\n\nReal.\n"
        sections = parse_sections(text)
        assert len(sections) == 2
        assert sections[0].heading == "## A"
        assert sections[1].heading == "## B"

    def test_empty_text_returns_empty(self) -> None:
        assert parse_sections("") == []


class TestParseHandoff:
    """Tests for parse_handoff — full pipeline."""

    def test_parses_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Goal\n\nDo something.\n\n## Decisions\n\nChose A.\n"
        )
        result = parse_handoff(f)
        assert isinstance(result, HandoffFile)
        assert result.frontmatter["title"] == "Test"
        assert len(result.sections) == 2
        assert result.path == str(f)
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_handoff_parsing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.handoff_parsing'`

**Step 3: Write the shared module**

```python
# scripts/handoff_parsing.py
"""Shared handoff parsing utilities.

Provides frontmatter extraction, section splitting, and full handoff
parsing. Used by search.py and distill.py. quality_check.py has its
own implementation (different heading normalization).
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
    only single-line key: value pairs are extracted.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[4:end]
    remaining = text[end + 4:]

    frontmatter: dict[str, str] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
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
    Code-fenced regions (both backtick ``` and tilde ~~~) are tracked to
    avoid treating ## lines inside fences as section boundaries. The
    heading line itself is NOT included in section.content to avoid
    duplication.
    """
    sections: list[Section] = []
    lines = text.splitlines(keepends=True)
    current_heading = ""
    current_lines: list[str] = []
    inside_fence = False
    fence_marker = ""  # Track which fence type opened (``` or ~~~)

    for line in lines:
        stripped = line.rstrip()
        if not inside_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            inside_fence = True
            fence_marker = stripped[:3]
        elif inside_fence and stripped.startswith(fence_marker):
            inside_fence = False
            fence_marker = ""
        if not inside_fence and line.startswith("## "):
            if current_heading:
                content = "".join(current_lines).strip()
                sections.append(Section(
                    heading=current_heading,
                    level=2,
                    content=content,
                ))
            current_heading = line.strip()
            current_lines = []
        elif current_heading:
            current_lines.append(line)

    if current_heading:
        content = "".join(current_lines).strip()
        sections.append(Section(
            heading=current_heading,
            level=2,
            content=content,
        ))

    return sections


def parse_handoff(path: Path) -> HandoffFile:
    """Parse a handoff markdown file into structured data."""
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    sections = parse_sections(body)
    return HandoffFile(path=str(path), frontmatter=frontmatter, sections=sections)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_handoff_parsing.py -v`
Expected: All 13 tests PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/handoff_parsing.py packages/plugins/handoff/tests/test_handoff_parsing.py
git commit -m "feat(handoff): extract shared parsing module handoff_parsing.py"
```

---

## Task 2: Extract shared project_paths module

**Files:**
- Create: `packages/plugins/handoff/scripts/project_paths.py`
- Create: `packages/plugins/handoff/tests/test_project_paths.py`

**Context:** `search.py` has `get_project_name()` and `get_handoffs_dir()`. These are needed by `distill.py` too. Extract to shared module.

**Step 1: Write the failing tests**

```python
# tests/test_project_paths.py
"""Tests for project_paths.py — shared path utilities."""

from pathlib import Path
from unittest.mock import patch

from scripts.project_paths import get_handoffs_dir, get_project_name


class TestGetProjectName:
    """Tests for get_project_name."""

    def test_returns_git_root_name(self) -> None:
        with patch("scripts.project_paths.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "/Users/jp/Projects/myproject\n"
            name, source = get_project_name()
        assert name == "myproject"
        assert source == "git"

    def test_falls_back_to_cwd(self) -> None:
        with patch("scripts.project_paths.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            name, source = get_project_name()
        assert source == "cwd"


class TestGetHandoffsDir:
    """Tests for get_handoffs_dir."""

    def test_returns_handoffs_path(self) -> None:
        with patch("scripts.project_paths.get_project_name", return_value=("myproject", "git")):
            result = get_handoffs_dir()
        assert result == Path.home() / ".claude" / "handoffs" / "myproject"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_project_paths.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.project_paths'`

**Step 3: Write the module**

```python
# scripts/project_paths.py
"""Shared path utilities for handoff plugin scripts.

Provides project name detection and handoffs directory resolution.
Used by search.py and distill.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_project_name() -> tuple[str, str]:
    """Get project name from git root directory, falling back to cwd.

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
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return Path.cwd().name, "cwd"


def get_handoffs_dir() -> Path:
    """Get handoffs directory: ~/.claude/handoffs/<project>/"""
    name, _ = get_project_name()
    return Path.home() / ".claude" / "handoffs" / name
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_project_paths.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/project_paths.py packages/plugins/handoff/tests/test_project_paths.py
git commit -m "feat(handoff): extract shared project_paths module"
```

---

## Task 3: Migrate search.py to shared modules

**Files:**
- Modify: `packages/plugins/handoff/scripts/search.py`

**Context:** Replace the inline implementations of `parse_frontmatter`, `parse_sections`, `Section`, `HandoffFile`, `parse_handoff`, `get_project_name`, and `get_handoffs_dir` with imports from the shared modules. The 29 existing search tests must all pass unchanged — they validate behavior, not implementation.

**Import contract (from review):** After migration, `parse_handoff` remains importable from `scripts.search` via Python's implicit re-export (it's imported at module level). This is intentional — add a comment documenting the re-export and a regression test to protect it from accidental removal during future refactors.

**Step 1: Rewrite search.py imports**

Replace the inline dataclasses, `parse_frontmatter`, `parse_sections`, `parse_handoff`, `get_project_name`, and `get_handoffs_dir` with imports. Keep `search_handoffs` and `main` in search.py (search-specific logic).

The resulting `search.py` should be:
```python
#!/usr/bin/env python3
"""search.py - Search handoff history for decisions, learnings, and context.

Searches within parsed handoff sections and outputs structured JSON results.
Parsing is provided by handoff_parsing.py; paths by project_paths.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Re-exported for backward compatibility — test_search.py imports these from
# scripts.search. Do not remove without updating downstream imports.
from scripts.handoff_parsing import HandoffFile, Section, parse_handoff
from scripts.project_paths import get_handoffs_dir, get_project_name


def search_handoffs(
    handoffs_dir: Path,
    query: str,
    *,
    regex: bool = False,
    skipped: list[dict] | None = None,
) -> list[dict]:
    # ... (unchanged from current implementation, lines 155-217)


def main(argv: list[str] | None = None) -> str:
    # ... (unchanged from current implementation, lines 220-269)


if __name__ == "__main__":
    print(main())
    sys.exit(0)
```

Remove from search.py: `Section` class, `HandoffFile` class, `parse_frontmatter` function, `parse_sections` function, `parse_handoff` function, `get_project_name` function, `get_handoffs_dir` function, and the `subprocess` and `dataclasses` imports.

**Step 2: Add re-export regression test**

Add to `tests/test_search.py` (or `tests/test_handoff_parsing.py`):

```python
def test_search_module_reexports_parse_handoff() -> None:
    """Verify parse_handoff is importable from scripts.search (backward compat)."""
    from scripts.search import parse_handoff  # noqa: F811
    assert callable(parse_handoff)
```

**Step 2b: Add fence regression tests**

Add to the search test class in `tests/test_search.py`:

```python
    def test_backtick_fence_prevents_section_split(self, tmp_path: Path) -> None:
        """Fence regression: backtick fences must not create false sections."""
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Real Section\n\nContent.\n\n"
            "```\n## Fake Section\n```\n\nMore content.\n"
        )
        results = search_handoffs(tmp_path, "content")
        sections_found = {r["section_heading"] for r in results}
        assert "## Fake Section" not in sections_found

    def test_unterminated_fence_behavior(self, tmp_path: Path) -> None:
        """Fence regression: unterminated fence suppresses subsequent sections."""
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Before\n\nContent.\n\n"
            "```\n## Suppressed\n\nStill suppressed.\n"
        )
        results = search_handoffs(tmp_path, "content")
        sections_found = {r["section_heading"] for r in results}
        assert "## Suppressed" not in sections_found
```

> Note: These tests document backtick fence behavior after migration to `handoff_parsing.py`. Tilde fence handling and same-type-only fence parity are new behaviors introduced by the shared module — not regressions from `search.py`'s toggle-based fence logic. The `test_fence_parity_close_on_same_type_only` test in `test_handoff_parsing.py` covers the new fence parity behavior.

**Step 3: Run ALL existing tests to verify no regressions**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_search.py -v`
Expected: All 32 tests PASS (29 existing + 1 re-export + 2 fence regression)

Also run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All 130+ tests PASS (search + quality_check + cleanup + handoff_parsing + project_paths)

**Step 4: Commit**

```bash
git add packages/plugins/handoff/scripts/search.py packages/plugins/handoff/tests/test_search.py
git commit -m "refactor(handoff): migrate search.py to shared parsing modules"
```

---

## Task 4: Build distill.py — subsection parser and durability hints

**Files:**
- Create: `packages/plugins/handoff/scripts/distill.py`
- Create: `packages/plugins/handoff/tests/test_distill.py`

**Context:** The `parse_sections` shared module splits on `##` only — `###` subsections are embedded in `section.content` as raw text. The distill script needs to split those into individual extraction units. Each `###` subsection in Decisions/Learnings becomes one candidate. Codebase Knowledge subsections get a durability hint.

**Step 1: Write the failing tests**

```python
# tests/test_distill.py
"""Tests for distill.py — knowledge graduation extraction."""

from scripts.distill import Subsection, classify_durability, parse_subsections


class TestParseSubsections:
    """Tests for parse_subsections — ### splitting within a ## section."""

    def test_splits_on_level3_headings(self) -> None:
        content = (
            "### Decision A\n\n"
            "**Choice:** Chose A.\n\n"
            "**Driver:** Speed.\n\n"
            "### Decision B\n\n"
            "**Choice:** Chose B.\n\n"
            "**Driver:** Cost.\n"
        )
        subs = parse_subsections(content)
        assert len(subs) == 2
        assert subs[0].heading == "Decision A"
        assert "**Choice:** Chose A." in subs[0].raw_markdown
        assert subs[1].heading == "Decision B"
        assert "**Choice:** Chose B." in subs[1].raw_markdown

    def test_no_subsections_returns_whole_content(self) -> None:
        content = "Just a paragraph of text with no ### headings."
        subs = parse_subsections(content)
        assert len(subs) == 1
        assert subs[0].heading == ""
        assert subs[0].raw_markdown == content

    def test_leading_text_before_first_subsection(self) -> None:
        content = (
            "Some intro text.\n\n"
            "### Sub A\n\n"
            "Content A.\n"
        )
        subs = parse_subsections(content)
        assert len(subs) == 2
        assert subs[0].heading == ""
        assert "Some intro text." in subs[0].raw_markdown
        assert subs[1].heading == "Sub A"

    def test_backtick_fences_do_not_split(self) -> None:
        content = (
            "### Real\n\n"
            "```\n### Fake\n```\n\n"
            "More content.\n"
        )
        subs = parse_subsections(content)
        assert len(subs) == 1
        assert subs[0].heading == "Real"
        assert "### Fake" in subs[0].raw_markdown

    def test_tilde_fences_do_not_split(self) -> None:
        content = (
            "### Real\n\n"
            "~~~\n### Fake\n~~~\n\n"
            "More content.\n"
        )
        subs = parse_subsections(content)
        assert len(subs) == 1
        assert subs[0].heading == "Real"
        assert "### Fake" in subs[0].raw_markdown

    def test_level4_headings_stay_in_parent(self) -> None:
        """#### headings are NOT split — they remain inside the ### parent.

        Extraction granularity is ### only. #### is typically file-inventory
        or sub-detail content that belongs with its parent subsection.
        """
        content = (
            "### Decision A\n\n"
            "**Choice:** Chose A.\n\n"
            "#### Supporting detail\n\n"
            "Some detail.\n\n"
            "#### Another detail\n\n"
            "More detail.\n\n"
            "### Decision B\n\n"
            "**Choice:** Chose B.\n"
        )
        subs = parse_subsections(content)
        assert len(subs) == 2
        assert subs[0].heading == "Decision A"
        assert "#### Supporting detail" in subs[0].raw_markdown
        assert "#### Another detail" in subs[0].raw_markdown
        assert subs[1].heading == "Decision B"

    def test_empty_content_returns_empty(self) -> None:
        subs = parse_subsections("")
        assert len(subs) == 1
        assert subs[0].heading == ""
        assert subs[0].raw_markdown == ""


class TestClassifyDurability:
    """Tests for classify_durability — keyword heuristic for Codebase Knowledge."""

    def test_pattern_is_likely_durable(self) -> None:
        assert classify_durability("Plugin hook naming pattern", "") == "likely_durable"

    def test_convention_is_likely_durable(self) -> None:
        assert classify_durability("Test file naming convention", "") == "likely_durable"

    def test_gotcha_is_likely_durable(self) -> None:
        assert classify_durability("Heredoc gotcha in zsh", "") == "likely_durable"

    def test_architecture_is_likely_ephemeral(self) -> None:
        assert classify_durability("Plugin architecture overview", "") == "likely_ephemeral"

    def test_key_locations_is_likely_ephemeral(self) -> None:
        assert classify_durability("Key code locations", "") == "likely_ephemeral"

    def test_unknown_heading(self) -> None:
        assert classify_durability("Miscellaneous notes", "") == "unknown"

    def test_content_keywords_override_heading(self) -> None:
        """Content with 'pattern' or 'convention' can upgrade unknown heading."""
        hint = classify_durability(
            "Something else",
            "This is a recurring pattern across all scripts.",
        )
        assert hint == "likely_durable"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py::TestParseSubsections -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Implement subsection parser and durability hints**

```python
# scripts/distill.py (initial — subsection parsing + durability)
"""distill.py — Extract durable knowledge from handoffs.

Deterministic extraction pipeline: parses handoff sections into
subsection-level candidates, classifies durability, computes provenance
hashes, checks exact deduplication, and outputs JSON for the distill
skill to synthesize into Phase 0 learning entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Subsection:
    """A ### subsection extracted from a ## section's content."""

    heading: str  # Bare heading text (no ### prefix). Empty if no heading.
    raw_markdown: str  # Full markdown content of this subsection.


# Durability classification keywords
_DURABLE_KEYWORDS: tuple[str, ...] = (
    "pattern",
    "convention",
    "gotcha",
    "invariant",
    "constraint",
    "rule",
    "principle",
    "anti-pattern",
    "antipattern",
    "workaround",
)

_EPHEMERAL_KEYWORDS: tuple[str, ...] = (
    "architecture",
    "structure",
    "overview",
    "layout",
    "key locations",
    "key code locations",
    "file:line",
    "dependency",
    "version",
    "current state",
)


def parse_subsections(content: str) -> list[Subsection]:
    """Split a ## section's content into ### subsections.

    Returns one Subsection per ### heading. If content has no ###
    headings, returns a single Subsection with empty heading containing
    the full content. Leading text before the first ### heading is
    returned as a Subsection with empty heading.

    Code fences (both backtick ``` and tilde ~~~) are tracked to avoid
    false splits on ### inside fences. #### headings are NOT split —
    extraction granularity is ### only.
    """
    if not content:
        return [Subsection(heading="", raw_markdown="")]

    lines = content.splitlines(keepends=True)
    subsections: list[Subsection] = []
    current_heading = ""
    current_lines: list[str] = []
    inside_fence = False
    fence_marker = ""  # Track which fence type opened (``` or ~~~)

    for line in lines:
        stripped = line.rstrip()
        if not inside_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            inside_fence = True
            fence_marker = stripped[:3]
        elif inside_fence and stripped.startswith(fence_marker):
            inside_fence = False
            fence_marker = ""

        if not inside_fence and line.startswith("### "):
            # Save previous subsection
            text = "".join(current_lines).strip()
            if current_heading or text:
                subsections.append(Subsection(
                    heading=current_heading,
                    raw_markdown=text,
                ))
            current_heading = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last subsection
    text = "".join(current_lines).strip()
    if current_heading or text or not subsections:
        subsections.append(Subsection(
            heading=current_heading,
            raw_markdown=text,
        ))

    return subsections


def classify_durability(heading: str, content: str) -> str:
    """Classify a Codebase Knowledge subsection's durability.

    Returns "likely_durable", "likely_ephemeral", or "unknown".
    Uses keyword matching on heading and content. The distill skill
    makes the final inclusion decision — this is directional only.
    """
    heading_lower = heading.lower()
    content_lower = content.lower()

    # Check heading for durable keywords first
    for keyword in _DURABLE_KEYWORDS:
        if keyword in heading_lower:
            return "likely_durable"

    # Check heading for ephemeral keywords
    for keyword in _EPHEMERAL_KEYWORDS:
        if keyword in heading_lower:
            return "likely_ephemeral"

    # Fall back to content keywords (can upgrade unknown to durable)
    for keyword in _DURABLE_KEYWORDS:
        if keyword in content_lower:
            return "likely_durable"

    return "unknown"
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py -v`
Expected: All 14 tests PASS

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/distill.py packages/plugins/handoff/tests/test_distill.py
git commit -m "feat(handoff): add subsection parser and durability hints for distill"
```

---

## Task 5: Build distill.py — provenance and exact dedup

**Files:**
- Modify: `packages/plugins/handoff/scripts/distill.py`
- Modify: `packages/plugins/handoff/tests/test_distill.py`

**Context:** Each distilled entry gets an HTML comment `<!-- distill-meta {...} -->` for provenance tracking. The script checks learnings.md for exact duplicates by source UID (same handoff + section + subsection) and content hash (same text regardless of source). Both use SHA-256.

**Step 1: Write the failing tests**

Append to `tests/test_distill.py`:

```python
from scripts.distill import (
    check_exact_dup_content,
    check_exact_dup_source,
    compute_content_hash,
    compute_source_uid,
    make_distill_meta,
)


class TestProvenance:
    """Tests for provenance computation."""

    def test_source_uid_deterministic(self) -> None:
        uid1 = compute_source_uid("session-abc-123", "Decisions", "Token bucket", heading_ix=0)
        uid2 = compute_source_uid("session-abc-123", "Decisions", "Token bucket", heading_ix=0)
        assert uid1 == uid2
        assert uid1.startswith("sha256:")

    def test_source_uid_differs_by_section(self) -> None:
        uid1 = compute_source_uid("session-abc-123", "Decisions", "Sub A", heading_ix=0)
        uid2 = compute_source_uid("session-abc-123", "Learnings", "Sub A", heading_ix=0)
        assert uid1 != uid2

    def test_source_uid_uses_identity_not_path(self) -> None:
        """source_uid is driven by document_identity, not filesystem path.

        Verified by showing: same identity → same UID, different identity →
        different UID. The integration test (Task 6) exercises this with
        actual handoff files at different paths.
        """
        uid1 = compute_source_uid("session-abc-123", "Decisions", "Sub A", heading_ix=0)
        uid2 = compute_source_uid("session-abc-123", "Decisions", "Sub A", heading_ix=0)
        uid_different = compute_source_uid("different-session", "Decisions", "Sub A", heading_ix=0)
        assert uid1 == uid2  # Same identity = same UID
        assert uid1 != uid_different  # Different identity = different UID

    def test_content_hash_deterministic(self) -> None:
        h1 = compute_content_hash("Some content here.")
        h2 = compute_content_hash("Some content here.")
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_content_hash_normalizes_whitespace(self) -> None:
        h1 = compute_content_hash("  content  \n\n  here  ")
        h2 = compute_content_hash("content here")
        assert h1 == h2

    def test_source_uid_disambiguates_duplicate_headings(self) -> None:
        uid0 = compute_source_uid("session-abc", "Decisions", "Sub A", heading_ix=0)
        uid1 = compute_source_uid("session-abc", "Decisions", "Sub A", heading_ix=1)
        assert uid0 != uid1

    def test_source_uid_canonical_json_is_deterministic(self) -> None:
        """Verify UID is deterministic (canonical JSON guarantees field order)."""
        uid1 = compute_source_uid("sess-1", "Decisions", "Sub A", heading_ix=0)
        uid2 = compute_source_uid("sess-1", "Decisions", "Sub A", heading_ix=0)
        assert uid1 == uid2
        assert uid1.startswith("sha256:")

    def test_distill_meta_format(self) -> None:
        meta = make_distill_meta(
            source_uid="sha256:abc123",
            source_anchor="handoff.md#decisions/token-bucket",
            content_sha256="sha256:def456",
        )
        assert meta.startswith("<!-- distill-meta ")
        assert meta.endswith(" -->")
        assert '"v": 1' in meta
        assert '"source_uid": "sha256:abc123"' in meta


class TestDocumentIdentity:
    """Tests for _document_identity — session_id enforcement."""

    def test_returns_session_id(self) -> None:
        from scripts.distill import _document_identity
        assert _document_identity({"session_id": "abc-123"}) == "abc-123"

    def test_strips_whitespace(self) -> None:
        from scripts.distill import _document_identity
        assert _document_identity({"session_id": "  abc-123  "}) == "abc-123"

    def test_rejects_missing_session_id(self) -> None:
        from scripts.distill import _document_identity
        import pytest
        with pytest.raises(ValueError, match="No session_id"):
            _document_identity({})

    def test_rejects_blank_session_id(self) -> None:
        from scripts.distill import _document_identity
        import pytest
        with pytest.raises(ValueError, match="No session_id"):
            _document_identity({"session_id": "  "})


class TestExactDedup:
    """Tests for exact deduplication checks."""

    def test_source_dup_detected(self) -> None:
        uid = "sha256:abc123"
        learnings = (
            "### 2026-02-27 [test]\n\n"
            "Some learning.\n"
            f'<!-- distill-meta {{"v": 1, "source_uid": "{uid}"}} -->\n'
        )
        assert check_exact_dup_source(uid, learnings) is True

    def test_source_no_dup(self) -> None:
        learnings = (
            "### 2026-02-27 [test]\n\n"
            "Some learning.\n"
            '<!-- distill-meta {"v": 1, "source_uid": "sha256:other"} -->\n'
        )
        assert check_exact_dup_source("sha256:abc123", learnings) is False

    def test_content_dup_detected(self) -> None:
        h = "sha256:def456"
        learnings = (
            "### 2026-02-27 [test]\n\n"
            "Some learning.\n"
            f'<!-- distill-meta {{"v": 1, "content_sha256": "{h}"}} -->\n'
        )
        assert check_exact_dup_content(h, learnings) is True

    def test_content_no_dup(self) -> None:
        learnings = "### 2026-02-27 [test]\n\nSome learning.\n"
        assert check_exact_dup_content("sha256:def456", learnings) is False

    def test_empty_learnings(self) -> None:
        assert check_exact_dup_source("sha256:abc", "") is False
        assert check_exact_dup_content("sha256:abc", "") is False

    def test_prose_containing_json_not_false_positive(self) -> None:
        """Prose that contains JSON key-value patterns should not match.

        Only content inside <!-- distill-meta ... --> comments counts.
        """
        learnings = (
            "### 2026-02-27 [test]\n\n"
            'The check uses `"source_uid": "sha256:abc123"` for matching.\n'
        )
        assert check_exact_dup_source("sha256:abc123", learnings) is False

    def test_prefix_uid_not_false_positive(self) -> None:
        """A source_uid that is a prefix of another should not match."""
        learnings = (
            "### 2026-02-27 [test]\n\n"
            "Some learning.\n"
            '<!-- distill-meta {"v": 1, "source_uid": "sha256:abc123full"} -->\n'
        )
        assert check_exact_dup_source("sha256:abc123", learnings) is False
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py::TestProvenance -v`
Expected: FAIL with `ImportError`

**Step 3: Implement provenance and dedup**

Add to `distill.py` imports:

```python
import hashlib
import json as json_mod  # avoid shadowing
from pathlib import Path

def _document_identity(frontmatter: dict[str, str]) -> str:
    """Extract session_id from frontmatter as document identity.

    Requires session_id — raises ValueError if absent or blank.
    The quality_check hook reports missing session_id but cannot prevent
    a handoff from being written without it (PostToolUse hooks always
    exit 0). This function enforces the invariant.
    """
    session_id = frontmatter.get("session_id", "").strip()
    if not session_id:
        raise ValueError(
            "No session_id in frontmatter. Cannot compute stable "
            "document identity. Handoff may pre-date session_id requirement."
        )
    return session_id


def compute_source_uid(
    document_identity: str,
    section_name: str,
    subsection_heading: str,
    heading_ix: int,
) -> str:
    """Compute deterministic source UID from location identity.

    Uses heading_ix (0-based occurrence count of this heading within the
    section) to disambiguate duplicate ### headings. Always included —
    conditional disambiguation causes multiplicity churn when headings
    change between unique and duplicated.

    Uses canonical JSON hashing for unambiguous key composition (avoids
    delimiter collision if components contain ':'). Format: sha256:<hex>.
    """
    payload = json_mod.dumps({
        "v": 1,
        "doc": document_identity,
        "section": section_name,
        "heading": subsection_heading,
        "heading_ix": heading_ix,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def compute_content_hash(content: str) -> str:
    """Compute normalized content hash.

    Normalizes whitespace (collapse runs, strip) before hashing so that
    formatting-only changes don't create false non-duplicates.
    """
    normalized = re.sub(r'\s+', ' ', content).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_distill_meta(
    source_uid: str,
    source_anchor: str,
    content_sha256: str,
    distilled_at: str = "",
) -> str:
    """Create a distill-meta HTML comment for provenance tracking.

    Format: <!-- distill-meta {"v": 1, "source_uid": "...", ...} -->

    The skill MUST pass a non-empty distilled_at (ISO date) at append time.
    The script produces candidates with distilled_at="" as a placeholder;
    the skill fills it before writing to learnings.md.
    """
    meta = {
        "v": 1,
        "source_uid": source_uid,
        "source_anchor": source_anchor,
        "content_sha256": content_sha256,
        "distilled_at": distilled_at,
    }
    return f"<!-- distill-meta {json_mod.dumps(meta, sort_keys=True)} -->"


_DISTILL_META_RE = re.compile(r'<!--\s*distill-meta\s+(\{.*?\})\s*-->')


def _extract_distill_metas(learnings_content: str) -> list[dict]:
    """Extract all distill-meta JSON payloads from HTML comments.

    Only searches inside <!-- distill-meta ... --> comments to avoid
    false positives from prose that happens to contain JSON key-value
    patterns.
    """
    metas: list[dict] = []
    for match in _DISTILL_META_RE.finditer(learnings_content):
        try:
            metas.append(json_mod.loads(match.group(1)))
        except (json_mod.JSONDecodeError, ValueError):
            continue
    return metas


def check_exact_dup_source(source_uid: str, learnings_content: str) -> bool:
    """Check if source_uid already exists in learnings.md distill-meta comments."""
    return any(
        m.get("source_uid") == source_uid
        for m in _extract_distill_metas(learnings_content)
    )


def check_exact_dup_content(content_hash: str, learnings_content: str) -> bool:
    """Check if content_hash already exists in learnings.md distill-meta comments."""
    return any(
        m.get("content_sha256") == content_hash
        for m in _extract_distill_metas(learnings_content)
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py -v`
Expected: All 33 tests PASS (14 prior + 19 new — `test_source_uid_uses_identity_not_path` replaces tautological `test_source_uid_stable_across_paths`)

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/distill.py packages/plugins/handoff/tests/test_distill.py
git commit -m "feat(handoff): add provenance tracking and exact dedup to distill"
```

---

## Task 6: Build distill.py — signal extraction and main pipeline

**Files:**
- Modify: `packages/plugins/handoff/scripts/distill.py`
- Modify: `packages/plugins/handoff/tests/test_distill.py`

**Context:** The main pipeline reads a handoff, extracts candidates from Decisions, Learnings, Codebase Knowledge, and Gotchas sections, adds signals (confidence, reversibility) from bold-labeled fields, checks exact dedup against learnings.md, and outputs JSON. This is the CLI entry point.

**Step 1: Write the failing tests**

Append to `tests/test_distill.py`:

```python
import json
from pathlib import Path
from unittest.mock import patch

from scripts.distill import extract_signals, extract_candidates, make_distill_meta, main as distill_main


class TestExtractSignals:
    """Tests for extract_signals — best-effort field extraction."""

    def test_extracts_confidence(self) -> None:
        md = "**Choice:** Chose A.\n\n**Confidence:** High (E2) — prototyped all three."
        signals = extract_signals(md)
        assert signals["confidence"] == "High (E2) — prototyped all three."

    def test_extracts_reversibility(self) -> None:
        md = "**Choice:** Chose A.\n\n**Reversibility:** Medium — can swap module."
        signals = extract_signals(md)
        assert signals["reversibility"] == "Medium — can swap module."

    def test_missing_fields_omitted(self) -> None:
        md = "**Choice:** Chose A.\n\n**Driver:** Speed."
        signals = extract_signals(md)
        assert signals == {}

    def test_multiline_value_takes_first_line(self) -> None:
        md = "**Confidence:** High (E2) — verified by tests.\nMore detail on next line."
        signals = extract_signals(md)
        assert signals["confidence"] == "High (E2) — verified by tests."


class TestExtractCandidates:
    """Tests for extract_candidates — full extraction pipeline."""

    def test_extracts_decisions_and_learnings(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Decisions\n\n"
            "### Chose Python\n\n"
            "**Choice:** Python over Rust.\n\n"
            "**Confidence:** High (E1).\n\n"
            "## Learnings\n\n"
            "### Token bucket smooths bursts\n\n"
            "**Mechanism:** Tokens refill at constant rate.\n\n"
            "**Evidence:** Prototype comparison.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        assert result["handoff_date"] == "2026-02-27"
        assert len(result["candidates"]) == 2
        assert result["candidates"][0]["source_section"] == "Decisions"
        assert result["candidates"][0]["subsection_heading"] == "Chose Python"
        assert result["candidates"][0]["dedup_status"] == "NEW"
        assert result["candidates"][1]["source_section"] == "Learnings"

    def test_codebase_knowledge_gets_durability_hint(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Codebase Knowledge\n\n"
            "### Plugin hook naming pattern\n\n"
            "Hooks use `mcp__plugin_<name>__<tool>` format.\n\n"
            "### Current plugin architecture\n\n"
            "The plugin has 3 scripts.\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 2
        assert result["candidates"][0]["durability_hint"] == "likely_durable"
        assert result["candidates"][1]["durability_hint"] == "likely_ephemeral"

    def test_exact_dup_detected(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-session-123\n---\n\n"
            "## Decisions\n\n"
            "### Chose Python\n\n"
            "**Choice:** Python.\n\n"
        )
        # Compute what the source UID would be (using document identity, not path)
        from scripts.distill import compute_source_uid
        uid = compute_source_uid("test-session-123", "Decisions", "Chose Python", heading_ix=0)
        learnings = f'<!-- distill-meta {{"v": 1, "source_uid": "{uid}"}} -->\n'

        result = extract_candidates(str(handoff), learnings)
        assert result["candidates"][0]["dedup_status"] == "EXACT_DUP_SOURCE"

    def test_empty_sections_produce_no_candidates(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Decisions\n\n"
            "## Learnings\n\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 0


class TestRoundTripIdempotence:
    """Extract → write meta → re-extract must produce EXACT_DUP_SOURCE."""

    def test_extract_write_reextract_is_exact_dup(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: round-trip-1\n---\n\n"
            "## Decisions\n\n### Chose Python\n\n**Choice:** Python.\n\n"
        )
        result1 = extract_candidates(str(handoff), "")
        candidate = result1["candidates"][0]
        assert candidate["dedup_status"] == "NEW"

        meta = make_distill_meta(
            source_uid=candidate["source_uid"],
            source_anchor=candidate["source_anchor"],
            content_sha256=candidate["content_sha256"],
            distilled_at="2026-02-27",
        )
        learnings = f"### 2026-02-27 [architecture]\n\nSynthesized.\n{meta}\n"

        result2 = extract_candidates(str(handoff), learnings)
        assert result2["candidates"][0]["dedup_status"] == "EXACT_DUP_SOURCE"


class TestOutputContract:
    """Verify the script/skill interface contract."""

    def test_required_top_level_keys(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: contract-1\n---\n\n"
            "## Decisions\n\n### Sub\n\n**Choice:** A.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        required = {"handoff_path", "handoff_date", "handoff_title",
                     "candidates", "error", "output_version", "error_code"}
        assert required.issubset(result.keys())
        assert result["output_version"] == 1

    def test_candidate_required_keys(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: contract-2\n---\n\n"
            "## Decisions\n\n### Sub\n\n**Choice:** A.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        candidate = result["candidates"][0]
        required = {"source_section", "subsection_heading", "raw_markdown", "signals",
                     "source_uid", "content_sha256", "source_anchor", "dedup_status"}
        assert required.issubset(candidate.keys())

    def test_dedup_status_is_known_enum(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: contract-3\n---\n\n"
            "## Decisions\n\n### Sub\n\n**Choice:** A.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        allowed = {"NEW", "EXACT_DUP_SOURCE", "EXACT_DUP_CONTENT", "UPDATED_SOURCE"}
        for c in result["candidates"]:
            assert c["dedup_status"] in allowed


class TestDistillCLI:
    """Integration tests for the CLI entry point."""

    def test_json_output(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Decisions\n\n"
            "### Chose A\n\n"
            "**Choice:** A over B.\n\n"
        )
        output = distill_main([str(handoff)])
        result = json.loads(output)
        assert result["handoff_path"] == str(handoff)
        assert len(result["candidates"]) == 1

    def test_with_learnings_file(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Learnings\n\n"
            "### Important thing\n\n"
            "**Mechanism:** Works like this.\n\n"
        )
        learnings = tmp_path / "learnings.md"
        learnings.write_text("# Learnings\n\nNo distill-meta comments.\n")
        output = distill_main([str(handoff), "--learnings", str(learnings)])
        result = json.loads(output)
        assert result["candidates"][0]["dedup_status"] == "NEW"

    def test_missing_handoff_returns_error(self) -> None:
        output = distill_main(["/nonexistent/path.md"])
        result = json.loads(output)
        assert result["error"] is not None

    def test_unreadable_learnings_returns_error(self, tmp_path: Path) -> None:
        """OSError reading learnings must return structured error, not silently disable dedup.

        Note: chmod(0o000) does not block root. This test is fragile on CI
        systems that run as root. If flaky on CI, guard with:
        @pytest.mark.skipif(os.getuid() == 0, reason="chmod ineffective as root")
        """
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Decisions\n\n### Chose A\n\n**Choice:** A.\n\n"
        )
        learnings = tmp_path / "learnings.md"
        learnings.write_text("content")
        learnings.chmod(0o000)
        try:
            output = distill_main([str(handoff), "--learnings", str(learnings)])
            result = json.loads(output)
            assert result["error"] is not None
            assert "Failed to read" in result["error"]
        finally:
            learnings.chmod(0o644)


class TestEdgeCases:
    """Edge case tests from evaluative review."""

    def test_no_heading_subsection_is_candidate(self, tmp_path: Path) -> None:
        """Section with no ### headings: the whole body is one candidate."""
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: edge-1\n---\n\n"
            "## Learnings\n\nStandalone learning without a ### heading.\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["subsection_heading"] == ""

    def test_malformed_distill_meta_does_not_crash(self) -> None:
        """Bad JSON in distill-meta comments must be silently skipped."""
        from scripts.distill import _extract_distill_metas
        learnings = (
            '<!-- distill-meta {broken json here -->\n'
            '<!-- distill-meta {"v": 1, "source_uid": "sha256:good"} -->\n'
            '<!-- distill-meta not-even-braces -->\n'
        )
        metas = _extract_distill_metas(learnings)
        assert len(metas) == 1
        assert metas[0]["source_uid"] == "sha256:good"


class TestNoAutodropInvariant:
    """Dedup status is a LABEL, not a filter. All candidates are returned."""

    def test_exact_dup_source_still_in_output(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: abc-123\n---\n\n"
            "## Decisions\n\n### Chose Python\n\n**Choice:** Python.\n\n"
        )
        from scripts.distill import compute_source_uid
        uid = compute_source_uid("abc-123", "Decisions", "Chose Python", heading_ix=0)
        learnings = f'<!-- distill-meta {{"v": 1, "source_uid": "{uid}"}} -->\n'
        result = extract_candidates(str(handoff), learnings)
        # Candidate is present with EXACT_DUP_SOURCE status — NOT filtered out
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["dedup_status"] == "EXACT_DUP_SOURCE"

    def test_exact_dup_content_still_in_output(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Decisions\n\n### Chose Python\n\n**Choice:** Python.\n\n"
        )
        from scripts.distill import compute_content_hash
        h = compute_content_hash("**Choice:** Python.")
        learnings = f'<!-- distill-meta {{"v": 1, "content_sha256": "{h}"}} -->\n'
        result = extract_candidates(str(handoff), learnings)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["dedup_status"] == "EXACT_DUP_CONTENT"


class TestUpdatedSource:
    """UPDATED_SOURCE: same source_uid, different content_sha256."""

    def test_updated_source_detected(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: update-test\n---\n\n"
            "## Decisions\n\n### Chose Python\n\n**Choice:** Python for speed.\n\n"
        )
        from scripts.distill import compute_source_uid
        uid = compute_source_uid("update-test", "Decisions", "Chose Python", heading_ix=0)
        # Learnings has same source_uid but different content hash
        learnings = f'<!-- distill-meta {{"v": 1, "source_uid": "{uid}", "content_sha256": "sha256:old_hash"}} -->\n'
        result = extract_candidates(str(handoff), learnings)
        assert result["candidates"][0]["dedup_status"] == "UPDATED_SOURCE"


class TestGotchasExtraction:
    """Gotchas section should be extracted as candidates."""

    def test_gotchas_extracted(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: test-sess\n---\n\n"
            "## Gotchas\n\n"
            "### Heredoc substitution unreliable\n\n"
            "zsh heredoc fails silently.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["source_section"] == "Gotchas"


class TestPreambleMerge:
    """Preamble (leading text before first ###) is merged into first headed subsection."""

    def test_preamble_merged_into_first_subsection(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: preamble-1\n---\n\n"
            "## Decisions\n\n"
            "Some introductory context about decisions.\n\n"
            "### Chose A\n\n**Choice:** A over B.\n\n"
            "### Chose C\n\n**Choice:** C over D.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 2
        # Preamble merged into first candidate, not dropped
        assert "Some introductory context" in result["candidates"][0]["raw_markdown"]
        assert result["candidates"][0]["subsection_heading"] == "Chose A"

    def test_no_preamble_no_change(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: preamble-2\n---\n\n"
            "## Decisions\n\n"
            "### Chose A\n\n**Choice:** A.\n\n"
        )
        result = extract_candidates(str(handoff), "")
        assert len(result["candidates"]) == 1
        assert "Some introductory" not in result["candidates"][0]["raw_markdown"]


class TestIncludeSection:
    """--include-section adds extra sections to extraction scope."""

    def test_context_section_extracted_when_included(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: context-1\n---\n\n"
            "## Context\n\n### Environment setup\n\nRun on Python 3.11.\n\n"
            "## Decisions\n\n### Chose A\n\n**Choice:** A.\n\n"
        )
        # Without --include-section: Context not extracted
        result_default = extract_candidates(str(handoff), "")
        sections = {c["source_section"] for c in result_default["candidates"]}
        assert "Context" not in sections

        # With --include-section Context: Context extracted
        result_include = extract_candidates(str(handoff), "", extra_sections=("Context",))
        sections = {c["source_section"] for c in result_include["candidates"]}
        assert "Context" in sections
        assert len(result_include["candidates"]) == 2

    def test_include_section_cli(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: context-2\n---\n\n"
            "## Context\n\n### Setup\n\nDetails.\n\n"
        )
        output = distill_main([str(handoff), "--include-section", "Context"])
        result = json.loads(output)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["source_section"] == "Context"


class TestHandoffReadError:
    """extract_candidates handles OSError/UnicodeDecodeError from parse_handoff."""

    def test_unreadable_handoff_returns_error(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text("content")
        handoff.chmod(0o000)
        try:
            result = extract_candidates(str(handoff), "")
            assert result["error"] is not None
            assert result["error_code"] == "HANDOFF_UNREADABLE"
        finally:
            handoff.chmod(0o644)

    def test_binary_handoff_returns_error(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_bytes(b'\x80\x81\x82\xff' * 100)
        result = extract_candidates(str(handoff), "")
        # Binary file may raise UnicodeDecodeError or produce garbage —
        # either an error result or a no-candidates result is acceptable
        assert result["error"] is not None or len(result["candidates"]) == 0


class TestLearningsWarning:
    """--learnings with nonexistent path warns instead of silent dedup disable."""

    def test_nonexistent_learnings_still_runs(self, tmp_path: Path) -> None:
        handoff = tmp_path / "test.md"
        handoff.write_text(
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: warn-1\n---\n\n"
            "## Decisions\n\n### Chose A\n\n**Choice:** A.\n\n"
        )
        output = distill_main([str(handoff), "--learnings", "/nonexistent/path.md"])
        result = json.loads(output)
        # Should still produce candidates (dedup disabled with warning)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["dedup_status"] == "NEW"


class TestPathIndependence:
    """Integration test: source_uid is stable across filesystem paths."""

    def test_same_handoff_different_paths_same_uid(self, tmp_path: Path) -> None:
        """source_uid uses session_id, not filesystem path.

        Same handoff content at two different paths (simulating move to
        .archive/) must produce identical source_uid values.
        """
        content = (
            "---\ntitle: Test\ndate: 2026-02-27\ntype: handoff\nsession_id: stable-uid-test\n---\n\n"
            "## Decisions\n\n### Chose A\n\n**Choice:** A.\n\n"
        )
        path_a = tmp_path / "handoff.md"
        path_b = tmp_path / ".archive" / "handoff.md"
        path_b.parent.mkdir()
        path_a.write_text(content)
        path_b.write_text(content)
        result_a = extract_candidates(str(path_a), "")
        result_b = extract_candidates(str(path_b), "")
        assert result_a["candidates"][0]["source_uid"] == result_b["candidates"][0]["source_uid"]


class TestMakeAnchorEdgeCases:
    """Edge cases for _make_anchor."""

    def test_empty_heading_produces_valid_anchor(self) -> None:
        from scripts.distill import _make_anchor
        anchor = _make_anchor("handoff.md", "Decisions", "")
        # Empty heading → empty slug → anchor is "handoff.md#decisions/"
        assert anchor == "handoff.md#decisions/"
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py::TestExtractSignals -v`
Expected: FAIL with `ImportError`

**Step 3: Implement signal extraction and main pipeline**

Add to `distill.py`:

```python
import argparse
import sys

from scripts.handoff_parsing import parse_handoff

# Sections to extract candidates from (Gotchas added per review — contains
# durable workaround/pattern knowledge. Context excluded by default; opt-in
# via --include-section Context)
_DISTILL_SECTIONS: tuple[str, ...] = ("Decisions", "Learnings", "Codebase Knowledge", "Gotchas")


def extract_signals(raw_markdown: str) -> dict[str, str]:
    """Extract confidence and reversibility signals from bold-labeled fields.

    Best-effort: returns only the fields that are found. Takes the first
    line of the value (stops at next bold label or blank line).
    """
    signals: dict[str, str] = {}
    for field in ("Confidence", "Reversibility"):
        pattern = rf'\*\*{field}:\*\*\s*(.+)'
        match = re.search(pattern, raw_markdown)
        if match:
            signals[field.lower()] = match.group(1).strip()
    return signals


def _section_name(heading: str) -> str:
    """Extract bare section name from ## heading.

    '## Decisions' -> 'Decisions', '## Codebase Knowledge' -> 'Codebase Knowledge'.
    """
    if heading.startswith("## "):
        return heading[3:].strip()
    return heading.strip()


def _make_anchor(handoff_filename: str, section_name: str, subsection_heading: str) -> str:
    """Create a source anchor for provenance.

    Format: <filename>#<section>/<subsection-slug>
    """
    slug = re.sub(r'[^a-z0-9]+', '-', subsection_heading.lower()).strip('-')
    return f"{handoff_filename}#{section_name.lower()}/{slug}"


def extract_candidates(
    handoff_path: str,
    learnings_content: str,
    extra_sections: tuple[str, ...] = (),
) -> dict:
    """Extract distill candidates from a handoff file.

    Returns a dict with handoff metadata and a list of candidates, each
    containing raw_markdown, signals, provenance hashes, and dedup status.

    extra_sections: additional section names to extract (e.g., ("Context",)
    when --include-section Context is passed). Merged with _DISTILL_SECTIONS.
    """
    active_sections = _DISTILL_SECTIONS + extra_sections
    path = Path(handoff_path)
    try:
        handoff = parse_handoff(path)
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": f"Failed to read handoff file: {exc}",
            "error_code": "HANDOFF_UNREADABLE",
        }
    try:
        doc_id = _document_identity(handoff.frontmatter)
    except ValueError as exc:
        return {
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": str(exc),
            "error_code": "NO_DOCUMENT_IDENTITY",
        }

    candidates: list[dict] = []

    for section in handoff.sections:
        name = _section_name(section.heading)
        if name not in active_sections:
            continue

        subsections = parse_subsections(section.content)
        heading_counts: dict[str, int] = {}

        for sub in subsections:
            # Skip empty or heading-only subsections
            if not sub.raw_markdown.strip():
                continue
            # Merge preamble (leading text before first ###) into first
            # headed subsection to avoid silent information loss.
            # Preamble often contains introductory context that belongs
            # with the first subsection rather than being dropped.
            if not sub.heading and any(s.heading for s in subsections):
                # Find first headed subsection and prepend preamble
                for other in subsections:
                    if other.heading:
                        other.raw_markdown = sub.raw_markdown.strip() + "\n\n" + other.raw_markdown
                        break
                continue

            ix = heading_counts.get(sub.heading, 0)
            heading_counts[sub.heading] = ix + 1
            source_uid = compute_source_uid(doc_id, name, sub.heading, heading_ix=ix)
            content_hash = compute_content_hash(sub.raw_markdown)

            # Determine dedup status (4-state matrix)
            # NOTE: source_match and content_match are checked independently
            # across ALL distill-meta entries. If source_uid matches row A and
            # content_sha256 coincidentally matches row B (different row), this
            # classifies as EXACT_DUP_SOURCE when it should be UPDATED_SOURCE.
            # This cross-row misclassification does not self-heal (no row written).
            # Known limitation for V1 — V1.1 should use row-aware matching:
            # compare content within the row that matched source_uid first.
            source_match = check_exact_dup_source(source_uid, learnings_content)
            content_match = check_exact_dup_content(content_hash, learnings_content)
            if source_match and content_match:
                dedup_status = "EXACT_DUP_SOURCE"
            elif source_match and not content_match:
                dedup_status = "UPDATED_SOURCE"
            elif not source_match and content_match:
                dedup_status = "EXACT_DUP_CONTENT"
            else:
                dedup_status = "NEW"

            candidate: dict = {
                "source_section": name,
                "subsection_heading": sub.heading,
                "raw_markdown": sub.raw_markdown,
                "signals": extract_signals(sub.raw_markdown),
                "source_uid": source_uid,
                "content_sha256": content_hash,
                "source_anchor": _make_anchor(path.name, name, sub.heading),
                "dedup_status": dedup_status,
            }

            # Add durability hint for Codebase Knowledge and Gotchas
            if name in ("Codebase Knowledge", "Gotchas"):
                candidate["durability_hint"] = classify_durability(
                    sub.heading, sub.raw_markdown
                )

            candidates.append(candidate)

    return {
        "handoff_path": handoff_path,
        "handoff_date": handoff.frontmatter.get("date", ""),
        "handoff_title": handoff.frontmatter.get("title", path.stem),
        "candidates": candidates,
        "output_version": 1,
        "error": None,
        "error_code": None,
    }


def main(argv: list[str] | None = None) -> str:
    """CLI entry point. Returns JSON string."""
    parser = argparse.ArgumentParser(description="Extract knowledge candidates from a handoff")
    parser.add_argument("handoff", help="Path to handoff markdown file")
    parser.add_argument("--learnings", help="Path to learnings.md for dedup checking", default="")
    parser.add_argument(
        "--include-section",
        action="append",
        default=[],
        help="Additional section names to extract (e.g., Context). May be repeated.",
    )
    args = parser.parse_args(argv)

    handoff_path = args.handoff
    if not Path(handoff_path).exists():
        return json_mod.dumps({
            "handoff_path": handoff_path,
            "handoff_date": "",
            "handoff_title": "",
            "candidates": [],
            "output_version": 1,
            "error": f"Handoff file not found: {handoff_path}",
            "error_code": "HANDOFF_NOT_FOUND",
        })

    learnings_content = ""
    if args.learnings:
        learnings_path = Path(args.learnings)
        if not learnings_path.exists():
            import sys as _sys
            print(
                f"Warning: learnings file not found: {args.learnings}. "
                "Dedup checking disabled.",
                file=_sys.stderr,
            )
        else:
            try:
                learnings_content = learnings_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return json_mod.dumps({
                    "handoff_path": handoff_path,
                    "handoff_date": "",
                    "handoff_title": "",
                    "candidates": [],
                    "output_version": 1,
                    "error": f"Failed to read learnings file: {exc}",
                    "error_code": "LEARNINGS_UNREADABLE",
                })

    result = extract_candidates(
        handoff_path, learnings_content,
        extra_sections=tuple(args.include_section),
    )
    return json_mod.dumps(result, indent=2)


if __name__ == "__main__":
    print(main())
    sys.exit(0)
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_distill.py -v`
Expected: All 64 tests PASS (33 prior + 22 original + 9 net-new from review 4)

Run full suite: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests PASS (129 existing + 64 new distill tests)

**Step 5: Commit**

```bash
git add packages/plugins/handoff/scripts/distill.py packages/plugins/handoff/tests/test_distill.py
git commit -m "feat(handoff): add signal extraction and main pipeline to distill.py"
```

---

## Task 7: Build distill skill

**Files:**
- Create: `packages/plugins/handoff/skills/distill/SKILL.md`

**Context:** The skill handles semantic work: synthesizing raw_markdown into Phase 0 paragraphs, semantic dedup (comparing candidates against existing learnings entries), confirmation UX (showing candidates with status), and appending confirmed entries to learnings.md. The script provides candidates as JSON; the skill provides judgment.

**Step 1: Create the skill**

Create `packages/plugins/handoff/skills/distill/SKILL.md` with the full content below. This was expanded from an intent list per adversarial review — the SKILL.md must be complete and machine-parseable, matching the quality standard of Tasks 1-6.

The SKILL.md must contain these sections with complete content:

**Frontmatter:**
- `name: distill`
- `description:` with trigger phrases (`/distill`, "distill handoff", "extract knowledge", "graduate knowledge")

**Inputs:**
- `/distill` — most recent handoff (use shell glob on handoffs dir, skip `.archive/`)
- `/distill <path>` — specific handoff file
- Optional `--include-section Context` — add Context section to extraction scope

**Procedure (numbered steps):**

1. **Locate handoff:** If path provided, validate it exists. If no path, find most recent handoff via `ls ~/.claude/handoffs/<project>/*.md`.
2. **Run distill.py:** Execute `python3 {plugin_root}/scripts/distill.py <handoff_path> --learnings <learnings_path>`. If user passed `--include-section`, add `--include-section <name>` to the command (may be repeated). Parse JSON output. If `error` is non-null, display error and stop.
3. **Group candidates by script status.** Display summary table with 4 states:
   - `EXACT_DUP_SOURCE` — same source, same content → terminal (auto-skip)
   - `EXACT_DUP_CONTENT` — different source, same content → terminal (auto-skip)
   - `UPDATED_SOURCE` — same source, content changed → prompt user
   - `NEW` — never distilled → synthesize
   For terminal states: display one-line summary (section/heading + 'already distilled' or 'content-identical'). No synthesis, no confirmation.
4. **For each NEW candidate — synthesize:** Convert `raw_markdown` into a Phase 0 paragraph following format mapping (below). Target 6-8 sentences, maximum 10. Preserve the reasoning chain — a decision's "why" must stay with its "what."
5. **For each NEW candidate — semantic dedup:** Compare the synthesized paragraph against existing entries in `docs/learnings/learnings.md`. If the candidate covers the same insight as an existing entry (same concept, different wording), annotate as `LIKELY_DUPLICATE` and show the matched existing entry. Semantic dedup is advisory — the user decides.
6. **Present candidates:** Show each candidate with:
   - Source: `{section}/{subsection_heading}` from handoff
   - Status: NEW or LIKELY_DUPLICATE (with matched entry if duplicate)
   - Durability hint (for Codebase Knowledge/Gotchas only)
   - If `subsection_heading` is empty, display as `(section body)` in the source line
   - Proposed Phase 0 text (the synthesized paragraph)
   - Tags (inferred from section type and content)
7. **User confirmation** — varies by state:
   - **UPDATED_SOURCE**: locate the existing entry in `learnings.md` by scanning for a `<!-- distill-meta` comment whose `source_uid` matches the candidate's `source_uid`. Extract the text between the `###` heading and the `<!-- distill-meta` comment as old content. Show diff (old vs new content). Options: `replace | keep both | skip`. Default: `replace`. To perform a replace: delete the old `###` entry (heading through `<!-- distill-meta` comment inclusive) and append the new entry at the end of the file.
   - **UNIQUE_NEW** (NEW after semantic dedup finds no match): `append | skip`
   - **LIKELY_DUPLICATE** (NEW but semantically similar to existing): `merge | replace | keep both | skip`
   - EXACT_DUP_SOURCE and EXACT_DUP_CONTENT are NOT shown (terminal at step 3).
8. **Append confirmed entries:** For each confirmed entry, append to `docs/learnings/learnings.md`:
   ```
   ### YYYY-MM-DD [tag1, tag2]

   <synthesized paragraph>
   <!-- distill-meta {"v": 1, "source_uid": "...", "source_anchor": "...", "content_sha256": "...", "distilled_at": "YYYY-MM-DD"} -->
   ```
   **MUST populate `distilled_at` with today's ISO date (YYYY-MM-DD).** Never leave it empty.

**Format mapping guidance (embed in SKILL.md):**

| Source section | Source fields | Target in paragraph |
|---------------|-------------|-------------------|
| Decisions | `**Choice:**` | What was decided |
| Decisions | `**Driver:**` | Why — the evidence or reasoning |
| Decisions | `**Alternatives considered:**` | Context (what else was evaluated, briefly) |
| Decisions | `**Trade-offs accepted:**` | Limitations acknowledged |
| Decisions | `**Confidence:**` | Certainty level |
| Learnings | `**Mechanism:**` | What/how it works |
| Learnings | `**Evidence:**` | Proof it's true |
| Learnings | `**Implication:**` | Takeaway for future work |
| Learnings | `**Watch for:**` | Caveat or edge case |
| Codebase Knowledge | (raw markdown) | Pattern or convention described |
| Gotchas | (raw markdown) | Workaround or pitfall described |

> Note: `extract_signals` returns lowercase keys (`confidence`, `reversibility`). The table above references source markdown labels (`**Confidence:**`, `**Reversibility:**`) — the key names in the signals dict are the lowercase equivalents.

**Tag mapping:**
- Decisions → `[architecture]` or `[workflow]` by default; infer from content
- Learnings → infer from content (common: `[debugging]`, `[testing]`, `[pattern]`, `[workflow]`)
- Codebase Knowledge → `[pattern]` or `[architecture]`
- Gotchas → `[debugging]` or `[workflow]`

**Failure modes (embed in SKILL.md):**

| Failure | Recovery |
|---------|----------|
| distill.py returns error JSON | Display error message, stop |
| No NEW candidates | Report "All candidates already distilled or content-identical" |
| learnings.md not found | Create with header `# Learnings\n\nProject insights captured from consultations.` |
| Handoff has no extractable sections | Report "No Decisions, Learnings, Codebase Knowledge, or Gotchas sections found" |

**Step 2: Verify skill loads**

Run `/distill` in Claude Code and verify the skill content is loaded (the SKILL.md renders). The script won't exist in the plugin cache yet, but the skill itself should parse.

**Step 3: Commit**

```bash
git add packages/plugins/handoff/skills/distill/SKILL.md
git commit -m "feat(handoff): add distill skill for knowledge graduation"
```

---

## Task 8: Version bump, README update, plugin.json

**Files:**
- Modify: `packages/plugins/handoff/.claude-plugin/plugin.json`
- Modify: `packages/plugins/handoff/pyproject.toml`
- Modify: `packages/plugins/handoff/README.md`

**Step 1: Bump version to 1.4.0**

In `plugin.json`: change `"version": "1.3.0"` to `"version": "1.4.0"`.
In `pyproject.toml`: change `version = "1.3.0"` to `version = "1.4.0"`.

**Step 2: Add distill section to README.md**

Add a `/distill` section after the `/search` section, documenting:
- What it does (extracts durable knowledge from handoffs into Phase 0 learnings)
- Invocation: `/distill` (most recent) or `/distill <path>` (specific handoff)
- What it extracts: Decisions, Learnings, Codebase Knowledge (with durability filtering)
- Output: Phase 0 entries appended to `docs/learnings/learnings.md`
- Dedup: exact (source + content hash) and semantic (Claude comparison)

Add `/distill` to the context reduction table.

**Step 3: Run full test suite**

Run: `cd packages/plugins/handoff && uv run pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add packages/plugins/handoff/.claude-plugin/plugin.json packages/plugins/handoff/pyproject.toml packages/plugins/handoff/README.md
git commit -m "chore(handoff): bump to 1.4.0 and add distill to README"
```

---

## Task 9: Update ticket status

**Files:**
- Modify: `docs/tickets/handoff-distill.md`

**Step 1: Update ticket**

Change `status: planning` to `status: implemented`. Fill in the Design Space section with the resolved decisions from the Codex dialogue. Update Files Affected to reflect the actual files created (skill name is `distill`, not `distilling-handoffs`; no commands directory; new scripts `distill.py`, `handoff_parsing.py`, `project_paths.py`).

**Step 2: Commit**

```bash
git add docs/tickets/handoff-distill.md
git commit -m "docs: update knowledge graduation ticket status"
```

---

## Dependency Graph

```
Task 1 (shared parsing)
  ├─> Task 3 (migrate search.py)
  │    └─> Task 6 (distill main pipeline)
  └─> Task 6 (distill main pipeline)  [direct: extract_candidates imports parse_handoff]

Task 2 (shared paths)
  └─> Task 3 (migrate search.py)

Task 4 (subsections + durability) ──> Task 5 (provenance + dedup) ──> Task 6 (distill main pipeline)

Task 6 (distill pipeline) ──> Task 7 (skill)
Task 7 (skill) ──> Task 8 (version bump)
Task 8 (version bump) ──> Task 9 (ticket update)
```

Tasks 1+2 can run in parallel. Tasks 4 and 5 are **sequential** — both modify `distill.py` and `test_distill.py`, so parallel execution would create merge conflicts. Task 3 requires Tasks 1+2. Task 6 requires Tasks 3+4+5 and also has a direct dependency on Task 1 (`extract_candidates` imports `parse_handoff` from `handoff_parsing.py`). Tasks 7-9 are sequential.

---

## Post-Implementation

After all tasks complete:

1. Run full test suite: `cd packages/plugins/handoff && uv run pytest -v`
2. Grep for stray old function references: `rg "from scripts.search import.*parse_frontmatter" packages/plugins/handoff/`
3. Verify re-export contract: `cd packages/plugins/handoff && uv run pytest tests/test_search.py::test_search_module_reexports_parse_handoff -v`
4. Test the full flow: run `/distill` on a real handoff from `.archive/`
5. Verify Gotchas extraction: ensure a handoff with Gotchas section produces candidates
6. Code review via `/superpowers:requesting-code-review`
7. Merge to main and update plugin cache
