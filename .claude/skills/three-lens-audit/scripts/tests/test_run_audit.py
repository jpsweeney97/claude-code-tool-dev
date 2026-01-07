"""Tests for run_audit.py."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from run_audit import (
    PRESETS,
    COST_ESTIMATES,
    load_prompts_from_reference,
    estimate_cost,
    generate_prompts,
    validate_outputs,
    PrepareResult,
    ValidationSummary,
)


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_default_preset_has_three_agents(self):
        """Default preset uses 3 agents."""
        cost = estimate_cost("default")
        assert cost["agents"] == 3

    def test_quick_preset_has_two_agents(self):
        """Quick preset uses 2 agents."""
        cost = estimate_cost("quick")
        assert cost["agents"] == 2

    def test_adds_target_tokens_to_input(self):
        """Target tokens are added to input estimate."""
        cost_no_target = estimate_cost("default", target_tokens=0)
        cost_with_target = estimate_cost("default", target_tokens=1000)
        # With 3 agents, 1000 target tokens adds 3000 to total
        assert cost_with_target["input_tokens"] == cost_no_target["input_tokens"] + 3000

    def test_unknown_preset_uses_default(self):
        """Unknown preset falls back to default estimates."""
        cost_unknown = estimate_cost("unknown_preset")
        cost_default = estimate_cost("default")
        assert cost_unknown["agents"] == cost_default["agents"]

    def test_total_cost_is_sum(self):
        """Total cost equals input + output costs."""
        cost = estimate_cost("default")
        assert abs(cost["total_cost"] - (cost["input_cost"] + cost["output_cost"])) < 0.001


class TestLoadPromptsFromReference:
    """Tests for load_prompts_from_reference function."""

    def test_returns_dict(self):
        """Returns a dictionary of prompts."""
        prompts = load_prompts_from_reference()
        assert isinstance(prompts, dict)

    def test_contains_default_lenses(self):
        """Contains prompts for default lenses."""
        prompts = load_prompts_from_reference()
        default_lenses = {"adversarial", "pragmatic", "cost-benefit"}
        assert default_lenses <= set(prompts.keys())

    def test_prompts_are_non_empty(self):
        """Prompts have content."""
        prompts = load_prompts_from_reference()
        for lens, prompt in prompts.items():
            assert len(prompt) > 100, f"{lens} prompt too short"


class TestGeneratePrompts:
    """Tests for generate_prompts function."""

    def test_generates_for_all_preset_lenses(self):
        """Generates one prompt per lens in preset."""
        prompts = generate_prompts("target.md", "default")
        expected_lenses = PRESETS["default"]["lenses"]
        assert set(prompts.keys()) == set(expected_lenses)

    def test_fills_target_placeholder(self):
        """Target is inserted into prompts."""
        prompts = generate_prompts("my_target.md", "default")
        for lens, prompt in prompts.items():
            assert "my_target.md" in prompt


class TestValidateOutputs:
    """Tests for validate_outputs function."""

    def test_handles_missing_file(self, tmp_path):
        """Reports missing file as failed."""
        missing_file = tmp_path / "nonexistent.md"
        files = {"adversarial": missing_file}
        result = validate_outputs(files)
        assert not result.all_passed

    def test_validates_valid_adversarial(self, tmp_path):
        """Validates correct adversarial output."""
        adv_file = tmp_path / "adversarial.md"
        adv_file.write_text("""# Adversarial Lens Analysis

| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Test vuln | Line 1 | Attacker does X | Major |
""")
        files = {"adversarial": adv_file}
        result = validate_outputs(files)
        passed, _ = result.results["adversarial"]
        assert passed
