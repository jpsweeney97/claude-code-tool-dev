"""Tests for distill.py — knowledge graduation extraction."""

import pytest
from scripts.distill import (
    Subsection,
    classify_durability,
    parse_subsections,
    check_exact_dup_content,
    check_exact_dup_source,
    compute_content_hash,
    compute_source_uid,
    make_distill_meta,
)


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
        """source_uid is driven by document_identity, not filesystem path."""
        uid1 = compute_source_uid("session-abc-123", "Decisions", "Sub A", heading_ix=0)
        uid2 = compute_source_uid("session-abc-123", "Decisions", "Sub A", heading_ix=0)
        uid_different = compute_source_uid("different-session", "Decisions", "Sub A", heading_ix=0)
        assert uid1 == uid2
        assert uid1 != uid_different

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
        with pytest.raises(ValueError, match="No session_id"):
            _document_identity({})

    def test_rejects_blank_session_id(self) -> None:
        from scripts.distill import _document_identity
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
        """Only content inside <!-- distill-meta ... --> comments counts."""
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
