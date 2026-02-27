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
