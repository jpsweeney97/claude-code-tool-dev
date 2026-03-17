"""Tests for retrieve_learnings module."""

from __future__ import annotations

from pathlib import Path

from scripts.retrieve_learnings import (
    LearningEntry,
    filter_by_relevance,
    format_for_briefing,
    parse_learnings,
    retrieve_learnings,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LEARNINGS = """\
# Learnings

Project insights captured from consultations.

### 2026-02-17 [codex, workflow]

When designing validation criteria, separate habit-formation from causal efficacy.
Pre-register rubrics and thresholds before starting.

### 2026-02-18 [security, hooks]

PreToolUse hooks are mechanically fail-open. When enforcement is critical,
explicitly catch all errors and return a block decision.
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Gotchas"} -->

### 2026-02-19 [architecture, codex]

When deploying parallel agents, structural independence matters more than
tool diversity. The falsifier pattern assigns different orientations.
"""

SINGLE_ENTRY = """\
# Learnings

### 2026-03-01 [testing, pattern]

Test the bypass paths, not just the working paths.
"""

EMPTY_FILE = """\
# Learnings

Project insights captured from consultations.
"""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


class TestParseLearnings:
    """Parse learnings.md into LearningEntry objects."""

    def test_parses_multiple_entries(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert len(entries) == 3

    def test_extracts_date(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert entries[0].date == "2026-02-17"

    def test_extracts_tags(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert entries[0].tags == ["codex", "workflow"]

    def test_extracts_content(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert "habit-formation" in entries[0].content
        assert "Pre-register rubrics" in entries[0].content

    def test_detects_promoted_entry(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert entries[1].promoted is True

    def test_detects_unpromoted_entry(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert entries[0].promoted is False
        assert entries[2].promoted is False

    def test_strips_promote_meta_from_content(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        assert "promote-meta" not in entries[1].content

    def test_empty_file_returns_empty_list(self) -> None:
        entries = parse_learnings(EMPTY_FILE)
        assert entries == []

    def test_single_entry(self) -> None:
        entries = parse_learnings(SINGLE_ENTRY)
        assert len(entries) == 1
        assert entries[0].tags == ["testing", "pattern"]


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


class TestFilterByRelevance:
    """Filter entries by tag/keyword overlap with query."""

    def test_matches_by_tag(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        filtered = filter_by_relevance(entries, "codex consultation")
        tags_found = {tag for e in filtered for tag in e.tags}
        assert "codex" in tags_found

    def test_matches_by_content_keyword(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        filtered = filter_by_relevance(entries, "falsifier pattern")
        assert any("falsifier" in e.content for e in filtered)

    def test_no_matches_returns_empty(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        filtered = filter_by_relevance(entries, "quantum computing blockchain")
        assert filtered == []

    def test_case_insensitive(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        filtered = filter_by_relevance(entries, "SECURITY hooks")
        assert len(filtered) > 0


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


class TestFormatForBriefing:
    """Format selected entries as markdown for briefing injection."""

    def test_formats_entries_as_markdown(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        result = format_for_briefing(entries[:2])
        assert "2026-02-17" in result
        assert "habit-formation" in result

    def test_respects_max_entries(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        result = format_for_briefing(entries, max_entries=1)
        # Only one entry's date should appear
        assert result.count("### 2026-") == 1

    def test_empty_list_returns_empty_string(self) -> None:
        result = format_for_briefing([])
        assert result == ""

    def test_includes_tags(self) -> None:
        entries = parse_learnings(SAMPLE_LEARNINGS)
        result = format_for_briefing(entries[:1])
        assert "[codex, workflow]" in result

    def test_includes_injection_marker(self) -> None:
        """Observability marker for analytics."""
        entries = parse_learnings(SAMPLE_LEARNINGS)
        result = format_for_briefing(entries[:2])
        assert "<!-- learnings-injected: 2 -->" in result


# ---------------------------------------------------------------------------
# End-to-end
# ---------------------------------------------------------------------------


class TestRetrieveLearnings:
    """End-to-end: read file, filter, format."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = retrieve_learnings("codex", path=tmp_path / "nonexistent.md")
        assert result == ""

    def test_end_to_end(self, tmp_path: Path) -> None:
        learnings_file = tmp_path / "learnings.md"
        learnings_file.write_text(SAMPLE_LEARNINGS)
        result = retrieve_learnings("security hooks", path=learnings_file)
        assert "fail-open" in result
        assert "<!-- learnings-injected:" in result

    def test_respects_max_entries(self, tmp_path: Path) -> None:
        learnings_file = tmp_path / "learnings.md"
        learnings_file.write_text(SAMPLE_LEARNINGS)
        result = retrieve_learnings(
            "codex architecture security", path=learnings_file, max_entries=2,
        )
        assert result.count("### 2026-") <= 2

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        learnings_file = tmp_path / "learnings.md"
        learnings_file.write_text(EMPTY_FILE)
        result = retrieve_learnings("anything", path=learnings_file)
        assert result == ""
