"""Prompt templates for skill generation."""

from __future__ import annotations

from lib.state import Gap, GapType


def build_skill_generation_prompt(gap: Gap) -> str:
    """Build a prompt for generating a skill from a gap.

    The prompt guides an LLM to create a complete SKILL.md file
    appropriate for the gap type and confidence level.
    """
    # Base context
    context_parts = [
        "Generate a complete Claude Code skill to address this ecosystem gap.",
        "",
        "## Gap Analysis",
        f"- **Title:** {gap.title}",
        f"- **Type:** {gap.gap_type.value}",
        f"- **Description:** {gap.description}",
        f"- **Confidence:** {gap.confidence:.0%}",
        f"- **Source:** {gap.source_agent}",
    ]

    # Type-specific guidance
    if gap.gap_type == GapType.WORKFLOW_HOLE:
        context_parts.extend([
            "",
            "## Workflow Gap Guidance",
            "This is a workflow hole - a missing connection between existing capabilities.",
            "Focus on:",
            "- How this skill bridges existing workflows",
            "- Integration points with other skills/tools",
            "- Clear handoff points",
        ])
    elif gap.gap_type == GapType.INCOMPLETE_ARTIFACT:
        context_parts.extend([
            "",
            "## Incomplete Artifact Guidance",
            "An existing artifact needs enhancement.",
            "Focus on:",
            "- What's missing from the current implementation",
            "- Backward compatibility with existing usage",
            "- Incremental improvement over current state",
        ])

    # Low confidence handling
    if gap.confidence < 0.5:
        context_parts.extend([
            "",
            "## Low Confidence Note",
            "This gap has uncertain requirements. The skill should:",
            "- Explore the problem space before prescribing solutions",
            "- Clarify assumptions upfront",
            "- Be flexible and adaptable",
        ])

    # Output format
    context_parts.extend([
        "",
        "## Required Output Format",
        "Generate a complete SKILL.md file with:",
        "",
        "```yaml",
        "---",
        "name: skill-name-here",
        'description: Use when [trigger phrases]. [What it does].',
        "---",
        "```",
        "",
        "Followed by:",
        "- H1 title matching skill name",
        "- Overview section explaining purpose",
        "- When to Use section with bullet points",
        "- Quick Reference table (if applicable)",
        "- Process section with numbered steps",
        "",
        "## Quality Requirements",
        "- Description must include trigger phrases (quoted terms or 'Use when/for')",
        "- Body must be at least 200 characters",
        "- Include 3-5 distinct trigger scenarios",
        "- No placeholder text - every section complete",
    ])

    return "\n".join(context_parts)
