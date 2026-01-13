"""Skill generator agent for complex gaps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from lib.prompts import build_skill_generation_prompt
from lib.state import Gap, normalize_skill_name


@dataclass
class GenerationResult:
    """Result of skill generation."""

    name: str
    gap_id: str
    content: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.content is not None and self.error is None


@dataclass
class SkillGeneratorAgent:
    """Generates skills for complex gaps using enhanced reasoning.

    Accepts an optional llm_callable for testing. In production,
    this would invoke the Task tool with a skill generation agent.
    """

    llm_callable: Callable[[str], str] | None = None

    def generate(self, gap_dict: dict[str, Any]) -> GenerationResult:
        """Generate a skill for the given gap."""
        gap = Gap.from_dict(gap_dict)
        name = normalize_skill_name(gap.title)

        if self.llm_callable is None:
            # No LLM configured - return placeholder
            return GenerationResult(
                name=name,
                gap_id=gap.gap_id,
                content=None,
                error="No LLM callable configured for skill generation",
            )

        # Build prompt and invoke LLM
        prompt = build_skill_generation_prompt(gap)

        try:
            content = self.llm_callable(prompt)
        except Exception as e:
            return GenerationResult(
                name=name,
                gap_id=gap.gap_id,
                content=None,
                error=f"LLM generation failed ({type(e).__name__}): {e}",
            )

        # Validate response has required structure (YAML frontmatter)
        # Must start with --- and have a closing --- delimiter
        if not content or not content.strip().startswith("---"):
            return GenerationResult(
                name=name,
                gap_id=gap.gap_id,
                content=None,
                error="LLM response missing required YAML frontmatter",
            )

        # Check for closing frontmatter delimiter (second ---)
        stripped = content.strip()
        first_delimiter_end = stripped.index("---") + 3
        remaining = stripped[first_delimiter_end:]
        if "---" not in remaining:
            return GenerationResult(
                name=name,
                gap_id=gap.gap_id,
                content=None,
                error="LLM response missing closing YAML frontmatter delimiter",
            )

        return GenerationResult(
            name=name,
            gap_id=gap.gap_id,
            content=content,
        )
