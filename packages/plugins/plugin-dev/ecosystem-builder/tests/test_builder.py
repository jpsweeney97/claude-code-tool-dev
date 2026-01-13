"""Tests for SkillBuilder."""

from pathlib import Path

from lib.builder import SkillBuilder
from lib.state import Gap, GapType, BuildResult


class TestSkillBuilder:
    """Tests for SkillBuilder class."""

    def test_classify_simple_gap(self) -> None:
        """MISSING_SKILL with clear title is simple."""
        builder = SkillBuilder()
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="testing",
            description="Add testing skill",
            source_agent="catalog",
            confidence=0.8,
            priority=2,
        )

        assert builder._classify_complexity(gap) == "simple"

    def test_classify_complex_gap(self) -> None:
        """WORKFLOW_HOLE or low confidence is complex."""
        builder = SkillBuilder()
        gap = Gap(
            gap_id="gap-2",
            gap_type=GapType.WORKFLOW_HOLE,
            title="ci-cd-integration",
            description="Complex workflow for CI/CD",
            source_agent="workflow",
            confidence=0.5,
            priority=1,
        )

        assert builder._classify_complexity(gap) == "complex"

    def test_build_simple_direct_generation(self) -> None:
        """Simple gaps use direct template generation."""
        builder = SkillBuilder()
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="testing",
            description="Add testing skill for pytest patterns",
            source_agent="catalog",
            confidence=0.9,
            priority=2,
        )

        result = builder.build(gap.to_dict())

        assert result.success is True
        assert result.method == "direct"
        assert "---" in result.content  # Has frontmatter
        assert "name:" in result.content
        assert "description:" in result.content


class TestDirectGeneration:
    """Tests for direct skill generation."""

    def test_generates_valid_frontmatter(self) -> None:
        """Direct generation creates valid YAML frontmatter."""
        builder = SkillBuilder()
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="code-review",
            description="Skill for reviewing code quality",
            source_agent="catalog",
            confidence=0.85,
            priority=2,
        )

        result = builder.build(gap.to_dict())
        content = result.content

        # Parse frontmatter
        lines = content.split("\n")
        assert lines[0] == "---"
        yaml_end = lines.index("---", 1)
        frontmatter = "\n".join(lines[1:yaml_end])

        import yaml
        metadata = yaml.safe_load(frontmatter)
        assert "name" in metadata
        assert "description" in metadata
        assert metadata["name"] == "code-review"

    def test_generates_body_structure(self) -> None:
        """Direct generation creates proper skill body."""
        builder = SkillBuilder()
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="documentation",
            description="Skill for documentation patterns",
            source_agent="catalog",
            confidence=0.85,
            priority=2,
        )

        result = builder.build(gap.to_dict())
        content = result.content

        # Should have expected sections
        assert "# " in content  # Has heading
        assert "## " in content or "When to Use" in content


class TestSubagentGeneration:
    """Tests for subagent-based skill generation."""

    def test_complex_gap_uses_subagent(self) -> None:
        """Complex gaps route to subagent generation."""
        mock_response = """---
name: ci-cd-integration
description: Use when setting up "CI/CD" workflows.
---

# CI/CD Integration

## Overview

Complex CI/CD workflow skill.

## When to Use

- CI/CD pipeline setup
- Continuous deployment integration

## Process

1. Configure pipeline
2. Deploy
"""

        builder = SkillBuilder(
            subagent_callable=lambda prompt: mock_response
        )
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="ci-cd-integration",
            description="Complex CI/CD workflow",
            source_agent="workflow",
            confidence=0.5,
            priority=1,
        )

        result = builder.build(gap.to_dict())

        assert result.success is True
        assert result.method == "subagent"
        assert "ci-cd-integration" in result.content

    def test_subagent_failure_returns_error(self) -> None:
        """Subagent failure returns BuildResult with error."""
        def failing_subagent(prompt: str) -> str:
            raise RuntimeError("Agent unavailable")

        builder = SkillBuilder(subagent_callable=failing_subagent)
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="test",
            description="Test",
            source_agent="test",
            confidence=0.5,
            priority=1,
        )

        result = builder.build(gap.to_dict())

        assert result.success is False
        assert result.method == "subagent"
        assert "unavailable" in result.error.lower()
