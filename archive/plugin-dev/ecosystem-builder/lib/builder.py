"""Skill builder with hybrid generation strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from lib.skill_generator import SkillGeneratorAgent
from lib.state import BuildResult, Gap, GapType, normalize_skill_name


@dataclass
class SkillBuilder:
    """Builds skills using hybrid direct/subagent strategy."""

    confidence_threshold: float = 0.7
    subagent_callable: Callable[[str], str] | None = None

    def build(self, gap_dict: dict[str, Any]) -> BuildResult:
        """Build a skill for the given gap."""
        gap = Gap.from_dict(gap_dict)
        complexity = self._classify_complexity(gap)

        if complexity == "simple":
            return self._build_direct(gap)
        else:
            return self._build_subagent(gap)

    def _classify_complexity(self, gap: Gap) -> str:
        """Classify gap as simple or complex."""
        # Complex: workflow holes, low confidence, or incomplete artifacts
        if gap.gap_type == GapType.WORKFLOW_HOLE:
            return "complex"
        if gap.gap_type == GapType.INCOMPLETE_ARTIFACT:
            return "complex"
        if gap.confidence < self.confidence_threshold:
            return "complex"

        # Simple: missing skills or quality issues with high confidence
        return "simple"

    def _build_direct(self, gap: Gap) -> BuildResult:
        """Generate skill directly from template."""
        name = normalize_skill_name(gap.title)
        description = self._generate_description(gap)
        body = self._generate_body(gap)

        content = f"""---
name: {name}
description: {description}
---

# {self._title_case(gap.title)}

{body}
"""

        return BuildResult(
            name=name,
            gap_id=gap.gap_id,
            content=content,
            method="direct",
        )

    def _build_subagent(self, gap: Gap) -> BuildResult:
        """Build using SkillGeneratorAgent."""
        agent = SkillGeneratorAgent(llm_callable=self.subagent_callable)
        result = agent.generate(gap.to_dict())

        return BuildResult(
            name=result.name,
            gap_id=result.gap_id,
            content=result.content,
            error=result.error,
            method="subagent",
        )

    def _title_case(self, title: str) -> str:
        """Convert to title case."""
        return " ".join(word.capitalize() for word in title.replace("-", " ").split())

    def _generate_description(self, gap: Gap) -> str:
        """Generate description with trigger phrases."""
        base = gap.description
        name = gap.title.replace("-", " ")
        return f'Use when working with "{name}" patterns. {base}'

    def _generate_body(self, gap: Gap) -> str:
        """Generate skill body."""
        name = self._title_case(gap.title)
        return f"""## Overview

Skill for {name.lower()} workflows.

## When to Use

- Working with {name.lower()}
- Need guidance on {name.lower()} patterns
- {gap.description}

## Quick Reference

| Pattern | Description |
|---------|-------------|
| Basic | Standard {name.lower()} workflow |

## Process

1. Identify the task
2. Apply appropriate patterns
3. Verify results
"""
