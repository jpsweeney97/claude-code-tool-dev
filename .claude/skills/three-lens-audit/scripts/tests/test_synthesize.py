"""Tests for synthesize.py."""
import sys
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from synthesize import (
    STOP_WORDS,
    Finding,
    calculate_overlap,
    extract_keywords,
    extract_sections,
    extract_table_rows,
)


class TestStopWords:
    """Tests for STOP_WORDS set."""

    def test_contains_common_words(self):
        """Stop words include common English words."""
        common_words = {"the", "a", "an", "is", "are", "to", "of", "in", "for", "and"}
        assert common_words <= STOP_WORDS

    def test_is_a_set(self):
        """STOP_WORDS is a set for O(1) lookups."""
        assert isinstance(STOP_WORDS, set)


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_removes_stop_words(self):
        """Keywords extraction removes common stop words."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extract_keywords(text)
        assert "the" not in keywords
        assert "over" not in keywords
        assert "quick" in keywords
        assert "brown" in keywords

    def test_lowercases_text(self):
        """Keywords are lowercased."""
        text = "UPPERCASE Mixed and lowercase"
        keywords = extract_keywords(text)
        assert "uppercase" in keywords
        assert "UPPERCASE" not in keywords
        assert "mixed" in keywords

    def test_excludes_short_words(self):
        """Words shorter than 3 characters are excluded."""
        text = "I am a cat on the mat"
        keywords = extract_keywords(text)
        # "cat" and "mat" are 3 chars, should be included
        assert "cat" in keywords
        assert "mat" in keywords
        # "am" is 2 chars, should be excluded
        assert "am" not in keywords

    def test_returns_set(self):
        """Returns a set of unique keywords."""
        text = "validation validation error error input"
        keywords = extract_keywords(text)
        assert isinstance(keywords, set)
        assert "validation" in keywords
        assert "error" in keywords


class TestCalculateOverlap:
    """Tests for calculate_overlap function (Jaccard similarity)."""

    def test_identical_sets_return_one(self):
        """Identical keyword sets have overlap of 1.0."""
        kw1 = {"validation", "error", "input"}
        kw2 = {"validation", "error", "input"}
        assert calculate_overlap(kw1, kw2) == 1.0

    def test_disjoint_sets_return_zero(self):
        """Disjoint keyword sets have overlap of 0.0."""
        kw1 = {"validation", "error", "input"}
        kw2 = {"network", "timeout", "retry"}
        assert calculate_overlap(kw1, kw2) == 0.0

    def test_partial_overlap(self):
        """Partial overlap returns correct Jaccard similarity."""
        kw1 = {"a", "b", "c"}  # 3 elements
        kw2 = {"b", "c", "d"}  # 3 elements, 2 shared
        # intersection = {b, c} = 2
        # union = {a, b, c, d} = 4
        # Jaccard = 2/4 = 0.5
        assert calculate_overlap(kw1, kw2) == 0.5

    def test_empty_set_returns_zero(self):
        """Empty set returns 0.0 overlap."""
        assert calculate_overlap(set(), {"a", "b"}) == 0.0
        assert calculate_overlap({"a", "b"}, set()) == 0.0

    def test_both_empty_returns_zero(self):
        """Two empty sets return 0.0 overlap."""
        assert calculate_overlap(set(), set()) == 0.0

    def test_single_element_overlap(self):
        """Single shared element calculates correctly."""
        kw1 = {"shared", "unique1"}
        kw2 = {"shared", "unique2"}
        # intersection = {shared} = 1
        # union = {shared, unique1, unique2} = 3
        # Jaccard = 1/3 = 0.333...
        assert abs(calculate_overlap(kw1, kw2) - 1 / 3) < 0.01


class TestExtractTableRows:
    """Tests for extract_table_rows function."""

    def test_extracts_data_rows(self):
        """Extracts data rows from a markdown table."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| value1  | value2  |
| value3  | value4  |
"""
        rows = extract_table_rows(content)
        assert len(rows) == 2
        assert rows[0]["Header1"] == "value1"
        assert rows[0]["Header2"] == "value2"

    def test_handles_no_table(self):
        """Returns empty list when no table present."""
        content = "Just some text without any tables."
        rows = extract_table_rows(content)
        assert rows == []


class TestExtractSections:
    """Tests for extract_sections function."""

    def test_extracts_header_sections(self):
        """Extracts sections marked with ## headers."""
        content = """\
## First Section
Content for first section.

## Second Section
Content for second section.
"""
        sections = extract_sections(content)
        assert "first section" in sections
        assert "second section" in sections
        assert "Content for first section." in sections["first section"]

    def test_extracts_bold_sections(self):
        """Extracts sections marked with **bold**."""
        content = """\
**Important Note**
This is the content.
"""
        sections = extract_sections(content)
        assert "important note" in sections


class TestFinding:
    """Tests for Finding dataclass."""

    def test_finding_is_hashable(self):
        """Findings can be used in sets."""
        f1 = Finding(text="test finding", lens="adversarial")
        f2 = Finding(text="test finding", lens="pragmatic")
        f3 = Finding(text="different finding", lens="adversarial")

        # Same text = same hash
        assert hash(f1) == hash(f2)

        # Can add to set
        findings_set = {f1, f3}
        assert len(findings_set) == 2

    def test_finding_has_keywords(self):
        """Findings can store keyword sets."""
        keywords = {"validation", "error"}
        f = Finding(text="test", lens="test", keywords=keywords)
        assert f.keywords == keywords
