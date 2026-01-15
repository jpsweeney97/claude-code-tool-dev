"""Tests for SkillGeneratorAgent."""

from lib.skill_generator import GenerationResult, SkillGeneratorAgent
from lib.state import Gap, GapType


class TestSkillGeneratorAgent:
    """Tests for SkillGeneratorAgent interface."""

    def test_generation_result_success(self) -> None:
        """GenerationResult tracks success state."""
        result = GenerationResult(
            name="test-skill",
            content="---\nname: test\n---\n# Test",
            gap_id="gap-123",
        )

        assert result.success is True
        assert result.error is None

    def test_generation_result_failure(self) -> None:
        """GenerationResult tracks failure state."""
        result = GenerationResult(
            name="test-skill",
            content=None,
            gap_id="gap-123",
            error="Generation failed: timeout",
        )

        assert result.success is False
        assert "timeout" in result.error

    def test_agent_accepts_gap_dict(self) -> None:
        """Agent.generate() accepts gap as dict."""
        agent = SkillGeneratorAgent()
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="ci-cd-integration",
            description="Complex CI/CD workflow integration",
            source_agent="workflow",
            confidence=0.5,
            priority=1,
        )

        # Should not raise
        result = agent.generate(gap.to_dict())

        assert isinstance(result, GenerationResult)
        assert result.gap_id == "gap-1"


class TestSkillGeneration:
    """Tests for actual skill generation."""

    def test_generate_with_mock_llm(self) -> None:
        """Generation works with mock LLM response."""
        mock_response = """---
name: ci-cd-integration
description: Use when setting up "CI/CD pipelines" or integrating continuous deployment.
---

# CI/CD Integration

## Overview

Skill for CI/CD integration workflows.

## When to Use

- Setting up CI/CD pipelines
- Integrating continuous deployment
- Automating build and deploy processes

## Process

1. Analyze current pipeline setup
2. Identify integration points
3. Configure automation
"""

        agent = SkillGeneratorAgent(
            llm_callable=lambda prompt: mock_response
        )
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="ci-cd-integration",
            description="Complex CI/CD workflow integration",
            source_agent="workflow",
            confidence=0.5,
            priority=1,
        )

        result = agent.generate(gap.to_dict())

        assert result.success is True
        assert "ci-cd-integration" in result.content
        assert "---" in result.content

    def test_generate_handles_llm_error(self) -> None:
        """Generation handles LLM errors gracefully."""
        def failing_llm(prompt: str) -> str:
            raise RuntimeError("LLM unavailable")

        agent = SkillGeneratorAgent(llm_callable=failing_llm)
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="test",
            description="Test",
            source_agent="test",
            confidence=0.5,
            priority=1,
        )

        result = agent.generate(gap.to_dict())

        assert result.success is False
        assert "LLM unavailable" in result.error or "unavailable" in result.error.lower()

    def test_generate_handles_invalid_response(self) -> None:
        """Generation handles LLM response without frontmatter."""
        agent = SkillGeneratorAgent(llm_callable=lambda prompt: "No frontmatter here")
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="test",
            description="Test",
            source_agent="test",
            confidence=0.5,
            priority=1,
        )

        result = agent.generate(gap.to_dict())

        assert result.success is False
        assert "frontmatter" in result.error.lower()

    def test_generate_handles_unclosed_frontmatter(self) -> None:
        """Generation handles LLM response with unclosed frontmatter."""
        agent = SkillGeneratorAgent(llm_callable=lambda prompt: "---\nname: test\nNo closing delimiter")
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="test",
            description="Test",
            source_agent="test",
            confidence=0.5,
            priority=1,
        )

        result = agent.generate(gap.to_dict())

        assert result.success is False
        assert "frontmatter" in result.error.lower()

    def test_generate_rejects_embedded_delimiter(self) -> None:
        """Generation rejects content with --- not at start."""
        agent = SkillGeneratorAgent(llm_callable=lambda prompt: "Hello --- world ---")
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="test",
            description="Test",
            source_agent="test",
            confidence=0.5,
            priority=1,
        )

        result = agent.generate(gap.to_dict())

        assert result.success is False
        assert "frontmatter" in result.error.lower()
