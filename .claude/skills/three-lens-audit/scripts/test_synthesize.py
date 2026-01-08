#!/usr/bin/env python3
"""Tests for semantic review functionality in synthesize.py."""

import pytest
from synthesize import SemanticMatch, SemanticReviewResult, Finding, extract_references


def test_semantic_match_creation():
    """SemanticMatch dataclass should hold match details."""
    f_a = Finding(text="config has no validation", lens="adversarial")
    f_b = Finding(text="config errors are confusing", lens="pragmatic")

    match = SemanticMatch(
        finding_a=f_a,
        finding_b=f_b,
        shared_element="config.yaml validation",
        rationale="Both describe config validation issues",
        confidence="high"
    )

    assert match.finding_a == f_a
    assert match.finding_b == f_b
    assert match.shared_element == "config.yaml validation"
    assert match.confidence == "high"


def test_semantic_review_result_creation():
    """SemanticReviewResult should hold review output."""
    result = SemanticReviewResult(
        matches=[],
        no_matches=[],
        token_usage={"input": 1000, "output": 200},
        model_used="haiku"
    )

    assert result.matches == []
    assert result.model_used == "haiku"
    assert result.token_usage["input"] == 1000


def test_extract_references_finds_file_paths():
    """extract_references should find backtick-wrapped file paths."""
    text = "The `config.yaml` file has issues and `auth.py` is broken"
    refs = extract_references(text)
    assert "config.yaml" in refs
    assert "auth.py" in refs


def test_extract_references_finds_quoted_names():
    """extract_references should find quoted element names."""
    text = 'The "Getting Started" section and "API Reference" need work'
    refs = extract_references(text)
    assert "getting started" in refs
    assert "api reference" in refs


def test_extract_references_finds_section_patterns():
    """extract_references should find 'the X section' patterns."""
    text = "Check the Security section and in Overview section"
    refs = extract_references(text)
    assert "security" in refs
    assert "overview" in refs


def test_extract_references_returns_lowercase():
    """extract_references should normalize to lowercase."""
    text = "`README.md` in the Security Section"
    refs = extract_references(text)
    assert "readme.md" in refs
    assert "security" in refs


# ===========================================================================
# generate_candidate_pairs tests
# ===========================================================================

from synthesize import generate_candidate_pairs


def test_generate_candidate_pairs_excludes_keyword_matches():
    """Pairs that already passed keyword threshold should be excluded."""
    findings = {
        "adversarial": [Finding("tokens too large", "adversarial", keywords={"tokens", "large", "context"})],
        "pragmatic": [Finding("tokens too big", "pragmatic", keywords={"tokens", "big", "context"})]
    }
    # These share "tokens" and "context" so keyword overlap is high
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 0


def test_generate_candidate_pairs_includes_shared_refs():
    """Pairs with shared references should be included even with low keyword overlap."""
    findings = {
        "adversarial": [Finding("`config.yaml` may exceed limits", "adversarial", keywords={"exceed", "limits"})],
        "pragmatic": [Finding("`config.yaml` is confusing to edit", "pragmatic", keywords={"confusing", "edit"})]
    }
    # Different keywords but both reference config.yaml
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 1


def test_generate_candidate_pairs_skips_same_lens():
    """Pairs from the same lens should be excluded."""
    findings = {
        "adversarial": [
            Finding("`config.yaml` issue A", "adversarial", keywords={"config", "issue"}),
            Finding("`config.yaml` issue B", "adversarial", keywords={"config", "problem"})
        ]
    }
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 0


def test_generate_candidate_pairs_respects_max_pairs():
    """Should cap pairs per lens combination."""
    findings = {
        "adversarial": [Finding(f"`file{i}.py` issue", "adversarial", keywords={f"file{i}"}) for i in range(10)],
        "pragmatic": [Finding(f"`file{i}.py` confusing", "pragmatic", keywords={f"conf{i}"}) for i in range(10)]
    }
    # All pairs have zero overlap but same file refs
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3, max_pairs_per_lens_combo=5)
    assert len(candidates) <= 5


# ===========================================================================
# format_pairs_for_prompt tests
# ===========================================================================

from synthesize import format_pairs_for_prompt


def test_format_pairs_for_prompt_includes_lens_labels():
    """format_pairs_for_prompt should include capitalized lens names."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert "**Adversarial:**" in formatted
    assert "**Pragmatic:**" in formatted


def test_format_pairs_for_prompt_numbers_pairs():
    """format_pairs_for_prompt should number pairs sequentially."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic")),
        (Finding("issue C", "cost-benefit"), Finding("issue D", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert "### Pair 1" in formatted
    assert "### Pair 2" in formatted


def test_format_pairs_for_prompt_quotes_finding_text():
    """format_pairs_for_prompt should quote finding text."""
    pairs = [
        (Finding("config has issues", "adversarial"), Finding("config is broken", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert '"config has issues"' in formatted
    assert '"config is broken"' in formatted


# ===========================================================================
# parse_semantic_response tests
# ===========================================================================

from synthesize import parse_semantic_response


def test_parse_semantic_response_extracts_matches():
    """parse_semantic_response should extract yes matches."""
    response = """
PAIR 1:
ELEMENT_A: config.yaml validation
ELEMENT_B: config.yaml errors
MATCH: yes
SHARED_ELEMENT: config.yaml validation
RATIONALE: Both describe config.yaml validation issues
CONFIDENCE: high

PAIR 2:
ELEMENT_A: README security
ELEMENT_B: auth.py tokens
MATCH: no
SHARED_ELEMENT: none
RATIONALE: Different elements entirely
CONFIDENCE: n/a
"""
    pairs = [
        (Finding("config no validation", "adversarial"), Finding("config confusing", "pragmatic")),
        (Finding("README security", "adversarial"), Finding("auth tokens", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    assert len(result.matches) == 1
    assert result.matches[0].shared_element == "config.yaml validation"
    assert result.matches[0].confidence == "high"
    assert len(result.no_matches) == 1


def test_parse_semantic_response_handles_medium_confidence():
    """parse_semantic_response should handle medium confidence matches."""
    response = """
PAIR 1:
ELEMENT_A: caching layer
ELEMENT_B: cache invalidation
MATCH: yes
SHARED_ELEMENT: cache
RATIONALE: Both reference caching
CONFIDENCE: medium
"""
    pairs = [
        (Finding("cache vulnerable", "adversarial"), Finding("cache overhead", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    assert len(result.matches) == 1
    assert result.matches[0].confidence == "medium"


def test_parse_semantic_response_handles_malformed_response():
    """parse_semantic_response should gracefully handle missing fields."""
    response = """
PAIR 1:
MATCH: yes
SHARED_ELEMENT: something
"""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]
    result = parse_semantic_response(response, pairs)

    # Should not crash, may return empty if can't parse
    assert isinstance(result.matches, list)


# ===========================================================================
# run_semantic_review tests
# ===========================================================================

import subprocess
from unittest.mock import patch, MagicMock
from synthesize import run_semantic_review


def test_run_semantic_review_calls_claude_cli():
    """run_semantic_review should call claude CLI with correct arguments."""
    pairs = [
        (Finding("config no validation", "adversarial"), Finding("config confusing", "pragmatic"))
    ]

    mock_response = """
PAIR 1:
ELEMENT_A: config.yaml
ELEMENT_B: config.yaml
MATCH: yes
SHARED_ELEMENT: config.yaml
RATIONALE: Same file
CONFIDENCE: high
"""

    with patch('synthesize.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout=mock_response,
            returncode=0
        )

        result = run_semantic_review(pairs, model="haiku")

        # Verify subprocess was called
        assert mock_run.called
        call_args = mock_run.call_args

        # Should use claude CLI with model flag
        assert "claude" in call_args[0][0]
        assert "--model" in call_args[0][0]

        # Should return parsed result
        assert result.model_used == "haiku"
        assert len(result.matches) == 1


def test_run_semantic_review_handles_empty_pairs():
    """run_semantic_review should handle empty pair list."""
    result = run_semantic_review([], model="haiku")

    assert result.matches == []
    assert result.no_matches == []


def test_run_semantic_review_handles_cli_error():
    """run_semantic_review should handle non-zero exit code."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    with patch('synthesize.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=1
        )

        result = run_semantic_review(pairs, model="haiku")

        # Should return empty result on error
        assert result.matches == []
        assert result.model_used == "haiku"


def test_run_semantic_review_handles_timeout():
    """run_semantic_review should handle subprocess timeout."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    with patch('synthesize.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)

        result = run_semantic_review(pairs, model="haiku")

        # Should return empty result on timeout
        assert result.matches == []
        assert result.model_used == "haiku"


def test_run_semantic_review_handles_missing_cli():
    """run_semantic_review should handle missing claude CLI."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]

    with patch('synthesize.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("claude not found")

        result = run_semantic_review(pairs, model="haiku")

        # Should return empty result when CLI not found
        assert result.matches == []
        assert result.model_used == "haiku"


# ===========================================================================
# merge_semantic_matches tests
# ===========================================================================

from synthesize import merge_semantic_matches, ConvergentFinding


def test_merge_semantic_matches_creates_convergent_finding():
    """merge_semantic_matches should create new ConvergentFinding from match."""
    match = SemanticMatch(
        finding_a=Finding("config no validation", "adversarial", keywords={"config", "validation"}),
        finding_b=Finding("config confusing", "pragmatic", keywords={"config", "confusing"}),
        shared_element="config.yaml",
        rationale="Both about config",
        confidence="high"
    )

    convergent_3 = []
    convergent_2 = []

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should create a 2-lens convergent finding
    assert len(convergent_2) == 1
    assert "adversarial" in convergent_2[0].lenses
    assert "pragmatic" in convergent_2[0].lenses


def test_merge_semantic_matches_extends_to_3_lens():
    """If a 2-match involves a lens already in convergent_2, try to extend to 3."""
    existing = ConvergentFinding(
        description="config issue",
        lenses={"adversarial": "validation", "cost-benefit": "overhead"},
        confidence=0.5,
        keywords={"config"}
    )
    convergent_3 = []
    convergent_2 = [existing]

    # New match involves adversarial and pragmatic
    match = SemanticMatch(
        finding_a=Finding("config no validation", "adversarial", keywords={"config"}),
        finding_b=Finding("config confusing", "pragmatic", keywords={"config"}),
        shared_element="config.yaml",
        rationale="Both about config",
        confidence="high"
    )

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should extend to 3-lens
    assert len(convergent_3) == 1
    assert len(convergent_3[0].lenses) == 3


def test_merge_semantic_matches_avoids_duplicates():
    """merge_semantic_matches should not duplicate existing findings."""
    existing = ConvergentFinding(
        description="config issue",
        lenses={"adversarial": "validation", "pragmatic": "confusing"},
        confidence=0.5,
        keywords={"config", "validation", "confusing"}
    )
    convergent_2 = [existing]
    convergent_3 = []

    # Match with same findings
    match = SemanticMatch(
        finding_a=Finding("validation", "adversarial", keywords={"config", "validation"}),
        finding_b=Finding("confusing", "pragmatic", keywords={"config", "confusing"}),
        shared_element="config",
        rationale="Same",
        confidence="high"
    )

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should not create duplicate
    assert len(convergent_2) == 1


# ===========================================================================
# synthesize() semantic review integration tests
# ===========================================================================

from synthesize import synthesize, SynthesisResult
from pathlib import Path
import tempfile


def test_synthesize_with_semantic_review_flag():
    """synthesize() with semantic_review=True should call semantic review."""
    # Create temp files with lens outputs that have LOW keyword overlap
    # but shared file reference (to generate candidates)
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        # Different keywords (validation vs usability) but same file ref
        adv_path.write_text("""
# Adversarial Audit

| Issue | Severity |
|-------|----------|
| `settings.json` allows injection attacks through unvalidated input | High |
""")
        prag_path.write_text("""
# Pragmatic Audit

| Issue | Impact |
|-------|--------|
| `settings.json` editor experience poor due to cryptic interface | Medium |
""")

        # Mock run_semantic_review to track if it's called
        with patch('synthesize.run_semantic_review') as mock_review:
            mock_review.return_value = SemanticReviewResult(
                matches=[],
                no_matches=[],
                token_usage={},
                model_used="haiku"
            )

            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test",
                semantic_review=True
            )

            # Should have called semantic review
            assert mock_review.called


def test_synthesize_without_semantic_review_flag():
    """synthesize() with semantic_review=False should skip semantic review."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        adv_path.write_text("# Adversarial\n\n| Issue | Severity |\n|-------|----------|\n| issue A | High |")
        prag_path.write_text("# Pragmatic\n\n| Issue | Impact |\n|-------|--------|\n| issue B | Medium |")

        with patch('synthesize.run_semantic_review') as mock_review:
            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test",
                semantic_review=False
            )

            # Should NOT have called semantic review
            assert not mock_review.called


def test_synthesize_semantic_review_default_off():
    """synthesize() should default to semantic_review=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        adv_path.write_text("# Adversarial\n\n| Issue | Severity |\n|-------|----------|\n| issue A | High |")
        prag_path.write_text("# Pragmatic\n\n| Issue | Impact |\n|-------|--------|\n| issue B | Medium |")

        with patch('synthesize.run_semantic_review') as mock_review:
            # Call without semantic_review parameter
            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test"
            )

            # Should NOT have called semantic review (default is off)
            assert not mock_review.called


def test_synthesize_semantic_review_merges_matches():
    """synthesize() should merge semantic matches into convergent findings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        # Create findings that won't match by keyword but will by semantic review
        adv_path.write_text("""
# Adversarial Audit

| Issue | Severity |
|-------|----------|
| `config.yaml` has exploitable validation gaps | High |
""")
        prag_path.write_text("""
# Pragmatic Audit

| Issue | Impact |
|-------|--------|
| `config.yaml` error messages confuse users | Medium |
""")

        with patch('synthesize.run_semantic_review') as mock_review:
            # Simulate finding a semantic match
            mock_review.return_value = SemanticReviewResult(
                matches=[SemanticMatch(
                    finding_a=Finding("`config.yaml` has exploitable validation gaps", "adversarial"),
                    finding_b=Finding("`config.yaml` error messages confuse users", "pragmatic"),
                    shared_element="config.yaml",
                    rationale="Both describe config.yaml issues",
                    confidence="high"
                )],
                no_matches=[],
                token_usage={},
                model_used="haiku"
            )

            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test",
                semantic_review=True
            )

            # Should have warnings about semantic review
            semantic_warnings = [w for w in result.warnings if "Semantic review" in w]
            assert len(semantic_warnings) >= 1


# ===========================================================================
# run_semantic_review error logging tests
# ===========================================================================

import sys
from io import StringIO


class TestRunSemanticReviewErrorLogging:
    """Tests for stderr logging in run_semantic_review failure modes."""

    def test_nonzero_exit_logs_to_stderr(self, monkeypatch):
        """Non-zero exit logs error to stderr."""
        pairs = [
            (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
        ]

        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        with patch('synthesize.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="API error: rate limited",
                returncode=1
            )

            result = run_semantic_review(pairs, model="haiku")

            # Should return empty result
            assert result.matches == []

            # Should log error to stderr
            stderr_output = stderr_capture.getvalue()
            assert "Warning" in stderr_output
            assert "exit" in stderr_output.lower() or "failed" in stderr_output.lower()

    def test_nonzero_exit_includes_stderr_content(self, monkeypatch):
        """Non-zero exit includes stderr content in log message."""
        pairs = [
            (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
        ]

        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        with patch('synthesize.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="API error: invalid model",
                returncode=1
            )

            run_semantic_review(pairs, model="haiku")

            stderr_output = stderr_capture.getvalue()
            # Should include the stderr content from the failed command
            assert "API error" in stderr_output or "invalid model" in stderr_output

    def test_timeout_logs_to_stderr(self, monkeypatch):
        """Timeout logs warning to stderr."""
        pairs = [
            (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
        ]

        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        with patch('synthesize.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)

            result = run_semantic_review(pairs, model="haiku")

            # Should return empty result
            assert result.matches == []

            # Should log timeout to stderr
            stderr_output = stderr_capture.getvalue()
            assert "Warning" in stderr_output
            assert "timeout" in stderr_output.lower() or "timed out" in stderr_output.lower()

    def test_cli_not_found_logs_to_stderr(self, monkeypatch):
        """FileNotFoundError logs helpful message to stderr."""
        pairs = [
            (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
        ]

        stderr_capture = StringIO()
        monkeypatch.setattr(sys, "stderr", stderr_capture)

        with patch('synthesize.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("claude not found")

            result = run_semantic_review(pairs, model="haiku")

            # Should return empty result
            assert result.matches == []

            # Should log helpful message to stderr
            stderr_output = stderr_capture.getvalue()
            assert "Warning" in stderr_output
            assert "claude" in stderr_output.lower() or "not found" in stderr_output.lower()


# ===========================================================================
# Direct execution test
# ===========================================================================


def test_synthesize_direct_execution():
    """Script runnable via python synthesize.py --help."""
    import subprocess as sp
    from pathlib import Path

    script_path = Path(__file__).parent / "synthesize.py"

    # Run script directly with --help from a DIFFERENT directory
    # to test the import path handling
    result = sp.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd="/tmp"  # Run from /tmp, not from the script's directory
    )

    # Should exit successfully with help text
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "synthesize" in result.stdout.lower()
    # Should not have import errors
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
