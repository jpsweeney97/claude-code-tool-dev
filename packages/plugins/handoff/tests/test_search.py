"""Tests for search.py — handoff search script."""

import json
from pathlib import Path
from unittest.mock import patch

from scripts.search import HandoffFile, Section, parse_handoff, search_handoffs


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
