#!/usr/bin/env python3
"""Tests for semantic review functionality in synthesize.py."""

import pytest
from synthesize import SemanticMatch, SemanticReviewResult, Finding


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
