"""Tests for Task tool adapter."""

import pytest

from lib.task_adapter import (
    create_dynamic_mock_callable,
    create_mock_callable,
    create_subagent_callable,
    SubagentConfig,
)


class TestSubagentConfig:
    """Tests for SubagentConfig."""

    def test_default_config(self) -> None:
        """Default config uses general-purpose agent."""
        config = SubagentConfig()

        assert config.subagent_type == "general-purpose"
        assert config.model == "sonnet"
        assert config.timeout_ms == 60000
        assert config.description == "Generate skill from gap"

    def test_custom_config(self) -> None:
        """Config accepts custom values."""
        config = SubagentConfig(
            subagent_type="Explore",
            model="opus",
            timeout_ms=120000,
        )

        assert config.subagent_type == "Explore"
        assert config.model == "opus"
        assert config.timeout_ms == 120000


class TestTaskAdapter:
    """Tests for Task tool adapter."""

    def test_create_callable_returns_function(self) -> None:
        """create_subagent_callable returns a callable."""
        callable_fn = create_subagent_callable()

        assert callable(callable_fn)

    def test_callable_includes_prompt(self) -> None:
        """Callable would pass prompt to Task tool."""
        # This is a structural test - actual Task invocation
        # happens in Claude Code runtime, not in tests
        config = SubagentConfig()
        callable_fn = create_subagent_callable(config)

        # The callable exists but can't actually invoke Task tool in tests
        # We verify the structure is correct
        assert callable_fn is not None

    def test_mock_callable_returns_response(self) -> None:
        """Mock callable returns the given response."""
        mock_callable = create_mock_callable("test response")
        result = mock_callable("any prompt")
        assert result == "test response"


class TestDynamicMockCallable:
    """Tests for dynamic mock callable."""

    def test_dynamic_mock_generates_valid_skill(self) -> None:
        """Dynamic mock produces valid YAML frontmatter."""
        import yaml

        mock_callable = create_dynamic_mock_callable()
        prompt = "Generate skill for: ci-cd-integration"
        result = mock_callable(prompt)

        # Parse frontmatter
        lines = result.split("\n")
        assert lines[0] == "---"
        yaml_end = lines.index("---", 1)
        frontmatter = "\n".join(lines[1:yaml_end])
        metadata = yaml.safe_load(frontmatter)

        assert "name" in metadata
        assert "description" in metadata
        assert metadata["name"] == "ci-cd-integration"

    def test_dynamic_mock_with_markdown_title_format(self) -> None:
        """Dynamic mock extracts name from **Title:** markdown format."""
        import yaml

        mock_callable = create_dynamic_mock_callable()
        # This matches the format from lib/prompts.py line 19
        prompt = """Generate a complete Claude Code skill to address this ecosystem gap.

## Gap Analysis
- **Title:** ci-cd-integration
- **Type:** workflow_hole
- **Description:** Test gap
"""
        result = mock_callable(prompt)

        # Parse frontmatter
        lines = result.split("\n")
        assert lines[0] == "---"
        yaml_end = lines.index("---", 1)
        frontmatter = "\n".join(lines[1:yaml_end])
        metadata = yaml.safe_load(frontmatter)

        assert metadata["name"] == "ci-cd-integration"


class TestSubagentConfigValidation:
    """Tests for SubagentConfig __post_init__ validation."""

    def test_timeout_below_minimum_raises(self) -> None:
        """Timeout below 1000ms should raise ValueError."""
        with pytest.raises(ValueError, match="timeout_ms must be >= 1000"):
            SubagentConfig(timeout_ms=999)

    def test_timeout_above_maximum_raises(self) -> None:
        """Timeout above 600000ms should raise ValueError."""
        with pytest.raises(ValueError, match="timeout_ms must be <= 600000"):
            SubagentConfig(timeout_ms=600001)

    def test_boundary_values_valid(self) -> None:
        """Boundary values should be accepted."""
        # Minimum valid timeout
        config_min = SubagentConfig(timeout_ms=1000)
        assert config_min.timeout_ms == 1000

        # Maximum valid timeout
        config_max = SubagentConfig(timeout_ms=600000)
        assert config_max.timeout_ms == 600000
