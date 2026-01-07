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
