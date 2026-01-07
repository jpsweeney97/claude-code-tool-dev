"""Tests for synthesize.py."""
import sys
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from synthesize import (
    STOP_WORDS,
    Finding,
    ConvergentFinding,
    SynthesisResult,
    calculate_overlap,
    extract_keywords,
    extract_sections,
    find_convergent_findings,
    generate_implementation_spec_markdown,
    synthesize,
)
from common import parse_markdown_table


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


class TestFindConvergentFindings:
    """Tests for find_convergent_findings function."""

    def test_no_convergence_with_disjoint_findings(self):
        """No convergent findings when keywords don't overlap."""
        findings = {
            "adversarial": [
                Finding(text="Security vulnerability in auth", lens="adversarial",
                        keywords={"security", "vulnerability", "auth"})
            ],
            "pragmatic": [
                Finding(text="Database performance issues", lens="pragmatic",
                        keywords={"database", "performance", "issues"})
            ],
            "cost-benefit": [
                Finding(text="Marketing budget allocation", lens="cost-benefit",
                        keywords={"marketing", "budget", "allocation"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []

    def test_two_lens_convergence_detected(self):
        """Detects convergence when 2 lenses share keywords."""
        # Jaccard similarity for adversarial/pragmatic:
        # intersection = {input, validation, error} = 3
        # union = {input, validation, error, security, confusing} = 5
        # Jaccard = 3/5 = 0.6 >= 0.3 threshold
        findings = {
            "adversarial": [
                Finding(text="Input validation error causes security risk", lens="adversarial",
                        keywords={"input", "validation", "error", "security"})
            ],
            "pragmatic": [
                Finding(text="Input validation error is confusing", lens="pragmatic",
                        keywords={"input", "validation", "error", "confusing"})
            ],
            "cost-benefit": [
                Finding(text="Completely unrelated topic here", lens="cost-benefit",
                        keywords={"completely", "unrelated", "topic"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert len(conv_2) >= 1
        # Verify the convergent finding involves adversarial and pragmatic
        lenses_found = set()
        for c in conv_2:
            lenses_found.update(c.lenses.keys())
        assert "adversarial" in lenses_found
        assert "pragmatic" in lenses_found

    def test_three_lens_convergence_detected(self):
        """Detects convergence when all 3 lenses share keywords."""
        findings = {
            "adversarial": [
                Finding(text="Authentication system has critical vulnerability", lens="adversarial",
                        keywords={"authentication", "system", "critical", "vulnerability"})
            ],
            "pragmatic": [
                Finding(text="Authentication system is hard to use correctly", lens="pragmatic",
                        keywords={"authentication", "system", "hard", "correctly"})
            ],
            "cost-benefit": [
                Finding(text="Authentication system maintenance is expensive", lens="cost-benefit",
                        keywords={"authentication", "system", "maintenance", "expensive"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert len(conv_3) >= 1
        # 3-lens convergent should have all 3 lenses
        for c in conv_3:
            assert len(c.lenses) == 3

    def test_handles_empty_findings(self):
        """Handles empty findings gracefully."""
        findings = {
            "adversarial": [],
            "pragmatic": [],
            "cost-benefit": []
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []

    def test_handles_single_lens(self):
        """Returns empty when only one lens provided."""
        findings = {
            "adversarial": [
                Finding(text="Some finding", lens="adversarial", keywords={"some", "finding"})
            ]
        }

        conv_3, conv_2 = find_convergent_findings(findings, threshold=0.3)

        assert conv_3 == []
        assert conv_2 == []


class TestParseMarkdownTable:
    """Tests for parse_markdown_table function (from common.py)."""

    def test_extracts_data_rows(self):
        """Extracts data rows from a markdown table."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| value1  | value2  |
| value3  | value4  |
"""
        rows = parse_markdown_table(content)
        assert len(rows) == 2
        assert rows[0]["Header1"] == "value1"
        assert rows[0]["Header2"] == "value2"

    def test_handles_no_table(self):
        """Returns empty list when no table present."""
        content = "Just some text without any tables."
        rows = parse_markdown_table(content)
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


class TestGenerateImplementationSpecMarkdown:
    """Tests for generate_implementation_spec_markdown function."""

    def test_includes_summary_table(self):
        """Output includes priority summary table."""
        result = SynthesisResult(
            target="test.md",
            convergent_3=[],
            convergent_2=[],
            unique={},
            recommendations=[],
            lens_outputs={},
        )
        output = generate_implementation_spec_markdown(result)
        assert "| Priority | Count |" in output
        assert "| P1 |" in output

    def test_p1_tasks_from_convergent_3(self):
        """P1 tasks come from 3-lens convergent findings."""
        result = SynthesisResult(
            target="test.md",
            convergent_3=[
                ConvergentFinding(
                    description="Test issue found by all lenses",
                    lenses={"adversarial": "evidence1", "pragmatic": "evidence2", "cost-benefit": "evidence3"},
                    confidence=0.75,
                )
            ],
            convergent_2=[],
            unique={},
            recommendations=[],
            lens_outputs={},
        )
        output = generate_implementation_spec_markdown(result)
        assert "## P1 Tasks" in output
        assert "Task 1.1" in output
        assert "75%" in output

    def test_p2_tasks_from_convergent_2(self):
        """P2 tasks come from 2-lens convergent findings."""
        result = SynthesisResult(
            target="test.md",
            convergent_3=[],
            convergent_2=[
                ConvergentFinding(
                    description="Two-lens issue",
                    lenses={"adversarial": "ev1", "pragmatic": "ev2"},
                    confidence=0.6,
                )
            ],
            unique={},
            recommendations=[],
            lens_outputs={},
        )
        output = generate_implementation_spec_markdown(result)
        assert "## P2 Tasks" in output
        assert "Task 2.1" in output

    def test_p3_tasks_from_unique_findings(self):
        """P3 tasks come from single-lens unique findings."""
        result = SynthesisResult(
            target="test.md",
            convergent_3=[],
            convergent_2=[],
            unique={
                "adversarial": [Finding(text="Unique adversarial finding", lens="adversarial")]
            },
            recommendations=[],
            lens_outputs={},
        )
        output = generate_implementation_spec_markdown(result)
        assert "## P3 Tasks" in output


class TestSynthesize:
    """Tests for synthesize function."""

    def test_synthesize_returns_synthesis_result(self, tmp_path):
        """Synthesize returns SynthesisResult with valid inputs."""
        # Create minimal valid outputs
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Input validation missing | line 42 | Inject bad data | Major |
""")
        prag = tmp_path / "pragmatic.md"
        prag.write_text("""# Pragmatic
## What Works
- Clear structure
## What's Missing
- Input validation is missing
## Friction Points
- Setup is complex
## Verdict
Needs work.
""")
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("""# Cost/Benefit
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Validation | L | H | Add |
## High-ROI
- Add input validation
## Low-ROI
- Complex features
## Recommendations
- Start with validation
""")

        lens_files = {
            "adversarial": adv,
            "pragmatic": prag,
            "cost-benefit": cb
        }

        result = synthesize(lens_files, target="test.md")

        assert isinstance(result, SynthesisResult)
        assert result.target == "test.md"
        assert "adversarial" in result.lens_outputs
        assert "pragmatic" in result.lens_outputs
        assert "cost-benefit" in result.lens_outputs

    def test_synthesize_warns_on_missing_file(self, tmp_path):
        """Synthesize adds warning for missing files."""
        existing = tmp_path / "adversarial.md"
        existing.write_text("Some content here that is long enough to pass")
        missing = tmp_path / "missing.md"

        lens_files = {
            "adversarial": existing,
            "pragmatic": missing
        }

        result = synthesize(lens_files, target="test.md")

        assert any("not found" in w.lower() for w in result.warnings)

    def test_synthesize_warns_with_single_output(self, tmp_path):
        """Synthesize warns when only one lens output provided."""
        single = tmp_path / "adversarial.md"
        single.write_text("Content that is long enough to be processed by the system")

        lens_files = {"adversarial": single}

        result = synthesize(lens_files, target="test.md")

        assert any("insufficient" in w.lower() for w in result.warnings)
        assert result.convergent_3 == []
        assert result.convergent_2 == []
