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
