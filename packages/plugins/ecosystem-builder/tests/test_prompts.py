"""Tests for prompt templates."""

from lib.prompts import build_skill_generation_prompt
from lib.state import Gap, GapType


class TestSkillGenerationPrompt:
    """Tests for skill generation prompt."""

    def test_prompt_includes_gap_details(self) -> None:
        """Prompt contains gap title, description, type."""
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.WORKFLOW_HOLE,
            title="ci-cd-integration",
            description="Complex CI/CD workflow",
            source_agent="workflow",
            confidence=0.5,
            priority=1,
        )

        prompt = build_skill_generation_prompt(gap)

        assert "ci-cd-integration" in prompt
        assert "CI/CD workflow" in prompt
        assert "workflow_hole" in prompt.lower() or "WORKFLOW_HOLE" in prompt

    def test_prompt_includes_output_format(self) -> None:
        """Prompt specifies expected output format."""
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="testing",
            description="Testing patterns skill",
            source_agent="catalog",
            confidence=0.6,
            priority=2,
        )

        prompt = build_skill_generation_prompt(gap)

        assert "SKILL.md" in prompt or "frontmatter" in prompt.lower()
        assert "name:" in prompt or "description:" in prompt

    def test_prompt_handles_low_confidence(self) -> None:
        """Low confidence gaps get exploration guidance."""
        gap = Gap(
            gap_id="gap-1",
            gap_type=GapType.MISSING_SKILL,
            title="uncertain-feature",
            description="Feature with unclear requirements",
            source_agent="catalog",
            confidence=0.3,
            priority=2,
        )

        prompt = build_skill_generation_prompt(gap)

        # Should mention exploring or clarifying
        assert "explore" in prompt.lower() or "clarify" in prompt.lower() or "uncertain" in prompt.lower()
