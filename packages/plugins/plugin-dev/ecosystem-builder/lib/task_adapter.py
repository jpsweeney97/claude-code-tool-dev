"""Adapter for Claude Code Task tool invocation.

This module provides the interface between ecosystem-builder
and Claude Code's Task tool for subagent-based skill generation.

In production, this would be invoked by Claude Code itself.
The adapter pattern allows testing with mocks while maintaining
the same interface for production use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class SubagentConfig:
    """Configuration for subagent invocation."""

    subagent_type: str = "general-purpose"
    model: str = "sonnet"
    timeout_ms: int = 60000
    description: str = "Generate skill from gap"

    def __post_init__(self) -> None:
        if self.timeout_ms < 1000:
            raise ValueError(f"SubagentConfig.timeout_ms must be >= 1000. Got: {self.timeout_ms!r}")
        if self.timeout_ms > 600000:
            raise ValueError(f"SubagentConfig.timeout_ms must be <= 600000 (10 min). Got: {self.timeout_ms!r}")


def create_subagent_callable(
    config: SubagentConfig | None = None,
) -> Callable[[str], str]:
    """Create a callable that invokes the Task tool.

    In production, this would be wired to Claude Code's Task tool.
    For testing, use mock callables directly on SkillBuilder.

    Returns:
        A callable that takes a prompt string and returns generated content.
        In test environments, this returns a placeholder.
    """
    if config is None:
        config = SubagentConfig()

    def invoke_task(prompt: str) -> str:
        """Invoke Task tool with the given prompt.

        This is a placeholder implementation. In production,
        Claude Code provides the actual Task tool invocation.
        """
        # Production implementation would be:
        # - Claude Code intercepts this call
        # - Invokes Task tool with subagent_type, prompt, model
        # - Returns the agent's response

        # For now, return error indicating production wiring needed
        raise RuntimeError(
            "Task tool not available. "
            "This function should be overridden in production "
            "with Claude Code's Task tool adapter."
        )

    return invoke_task


def create_mock_callable(response: str) -> Callable[[str], str]:
    """Create a mock callable for testing.

    Args:
        response: The skill content to return.

    Returns:
        A callable that returns the given response.
    """

    def mock_invoke(prompt: str) -> str:
        return response

    return mock_invoke


def create_dynamic_mock_callable() -> Callable[[str], str]:
    """Create a dynamic mock that generates contextual skill content.

    Extracts skill name from the prompt and generates appropriate content.
    """

    def dynamic_mock(prompt: str) -> str:
        name = _extract_skill_name(prompt)
        title = " ".join(word.capitalize() for word in name.split("-"))

        return f'''---
name: {name}
description: Use when working with "{title.lower()}" patterns or workflows.
---

# {title}

## Overview

This skill provides guidance for {title.lower()} patterns.

## When to Use

- Working with {title.lower()} patterns
- Need guidance on {title.lower()} workflows

## Process

1. Analyze requirements
2. Apply patterns
3. Validate results
'''

    return dynamic_mock


def _extract_skill_name(prompt: str) -> str:
    """Extract skill name from generation prompt."""
    patterns = [
        r'\*\*Title:\*\*\s*(\S+)',  # Match **Title:** format from prompts.py
        r'Title:\s*(\S+)',  # Plain Title: format
        r'for:\s*(\S+)',
        r'["\']([\w-]+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            name = match.group(1)
            return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return "generated-skill"
