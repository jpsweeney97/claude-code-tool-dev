"""Tests for learning retrieval."""

from __future__ import annotations

from pathlib import Path
from server.retrieve_learnings import (
    LearningEntry,
    filter_by_relevance,
    format_for_briefing,
    parse_learnings,
    retrieve_learnings,
)


class TestParseLearnings:
    def test_parses_single_entry(self) -> None:
        text = "### 2026-03-15 [safety, scanning]\n\nCredential scanning uses tiered enforcement.\n"
        entries = parse_learnings(text)
        assert len(entries) == 1
        assert entries[0].date == "2026-03-15"
        assert entries[0].tags == ["safety", "scanning"]
        assert "tiered enforcement" in entries[0].content

    def test_parses_multiple_entries(self) -> None:
        text = (
            "### 2026-03-15 [safety]\n\nFirst entry.\n\n"
            "### 2026-03-16 [profiles]\n\nSecond entry.\n"
        )
        entries = parse_learnings(text)
        assert len(entries) == 2
        assert entries[0].date == "2026-03-15"
        assert entries[1].date == "2026-03-16"

    def test_empty_text_returns_empty(self) -> None:
        assert parse_learnings("") == []

    def test_detects_promote_meta(self) -> None:
        text = "### 2026-03-15 [tag]\n<!-- promote-meta status=promoted -->\nContent.\n"
        entries = parse_learnings(text)
        assert entries[0].promoted is True


class TestFilterByRelevance:
    def test_tag_match_scores_higher(self) -> None:
        entries = [
            LearningEntry(date="2026-01-01", tags=["safety"], content="unrelated"),
            LearningEntry(date="2026-01-02", tags=["other"], content="safety note"),
        ]
        filtered = filter_by_relevance(entries, "safety")
        assert filtered[0].date == "2026-01-01"  # tag match = 2 pts

    def test_zero_score_filtered_out(self) -> None:
        entries = [
            LearningEntry(
                date="2026-01-01", tags=["profiles"], content="profile config"
            ),
        ]
        filtered = filter_by_relevance(entries, "safety")
        assert filtered == []


class TestFormatForBriefing:
    def test_formats_entries_as_markdown(self) -> None:
        entries = [
            LearningEntry(date="2026-03-15", tags=["safety"], content="Content here."),
        ]
        result = format_for_briefing(entries, max_entries=5)
        assert "### 2026-03-15 [safety]" in result
        assert "Content here." in result
        assert "learnings-injected: 1" in result

    def test_respects_max_entries(self) -> None:
        entries = [
            LearningEntry(date=f"2026-01-0{i}", tags=["t"], content=f"e{i}")
            for i in range(1, 6)
        ]
        result = format_for_briefing(entries, max_entries=2)
        assert "learnings-injected: 2" in result

    def test_empty_entries_returns_empty(self) -> None:
        assert format_for_briefing([]) == ""


class TestRetrieveLearnings:
    def test_resolves_path_from_repo_root(self, tmp_path: Path) -> None:
        """repo_root determines the learnings file location, not cwd."""
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_text(
            "### 2026-03-15 [safety]\n\nTest learning.\n"
        )
        result = retrieve_learnings("safety", repo_root=tmp_path)
        assert "Test learning" in result

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Fail-soft when learnings file does not exist."""
        result = retrieve_learnings("anything", repo_root=tmp_path)
        assert result == ""

    def test_invalid_utf8_returns_empty(self, tmp_path: Path) -> None:
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_bytes(b"\xff\xfe\xfd")
        result = retrieve_learnings("anything", repo_root=tmp_path)
        assert result == ""

    def test_cwd_does_not_affect_resolution(self, tmp_path: Path, monkeypatch) -> None:
        """Prove that cwd is irrelevant — only repo_root matters."""
        learnings_dir = tmp_path / "docs" / "learnings"
        learnings_dir.mkdir(parents=True)
        (learnings_dir / "learnings.md").write_text(
            "### 2026-03-15 [test]\n\nContent.\n"
        )
        # Change cwd to a directory with no learnings
        monkeypatch.chdir(tmp_path / "docs")
        result = retrieve_learnings("test", repo_root=tmp_path)
        assert "Content" in result
