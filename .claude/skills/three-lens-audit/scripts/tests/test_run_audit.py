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
    finalize,
    PrepareResult,
    ValidationSummary,
    FinalizeResult,
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


class TestFinalize:
    """Tests for finalize function."""

    def test_successful_finalize_with_valid_outputs(self, tmp_path):
        """Finalize succeeds when all outputs are valid."""
        # Create valid adversarial output with extractable findings
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Authentication bypass vulnerability | Missing token validation on line 42 | Attacker sends requests without valid tokens | Major |
| SQL injection risk | User input not sanitized | Attacker injects malicious queries | Critical |
""")
        # Create valid pragmatic output with extractable findings
        prag = tmp_path / "pragmatic.md"
        prag.write_text("""# Pragmatic
## What Works
- Authentication system provides reasonable security baseline
- Token validation flow is conceptually correct
## What's Missing
- Input sanitization is incomplete for user-provided data
- Error handling for authentication failures needs improvement
## Friction Points
- Token validation logic is scattered across multiple files
## Verdict
Acceptable with improvements needed.
""")
        # Create valid cost-benefit output with extractable findings
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("""# Cost/Benefit
| Element | Effort | Benefit | Verdict |
|---------|--------|---------|---------|
| Token validation refactor | M | H | Keep |
| Input sanitization layer | L | H | Keep |

## High-ROI
- Adding input sanitization is low effort high benefit
## Low-ROI
- Major authentication overhaul would be expensive
## Recommendations
- Prioritize input sanitization before token changes
""")

        result = finalize([adv, prag, cb], target="test.md")

        assert result.validation.all_passed
        assert result.synthesis_result is not None
        # Validation warnings are empty (synthesis may still warn about convergence)
        assert all("Validation failed" not in w for w in result.warnings)

    def test_finalize_with_insufficient_outputs_returns_no_synthesis(self, tmp_path):
        """Finalize returns no synthesis when < 2 outputs pass validation."""
        # Create one valid file
        adv = tmp_path / "adversarial.md"
        adv.write_text("""# Adversarial
| Vulnerability | Evidence | Attack Scenario | Severity |
|---------------|----------|-----------------|----------|
| Issue | Proof | Attack | Major |
""")
        # Create one invalid file (too short)
        prag = tmp_path / "pragmatic.md"
        prag.write_text("too short")

        # Create another invalid file
        cb = tmp_path / "cost-benefit.md"
        cb.write_text("also too short")

        result = finalize([adv, prag, cb], target="test.md")

        assert not result.validation.all_passed
        assert result.synthesis_result is None
        assert any("Insufficient" in w for w in result.warnings)

    def test_finalize_handles_missing_files(self, tmp_path):
        """Finalize handles missing files gracefully."""
        missing1 = tmp_path / "nonexistent1.md"
        missing2 = tmp_path / "nonexistent2.md"
        missing3 = tmp_path / "nonexistent3.md"

        result = finalize([missing1, missing2, missing3], target="test.md")

        assert not result.validation.all_passed
        assert result.synthesis_result is None
