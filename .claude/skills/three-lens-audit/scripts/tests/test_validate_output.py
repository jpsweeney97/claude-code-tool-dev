"""Tests for validate_output.py."""
import sys
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from validate_output import (
    LENS_REQUIREMENTS,
    ValidationResult,
    check_sections,
    check_table_columns,
    find_table_rows,
    validate_output,
)


class TestLensRequirements:
    """Tests for LENS_REQUIREMENTS configuration."""

    def test_has_all_documented_lenses(self):
        """All documented lenses have validation requirements."""
        expected_lenses = {
            "adversarial",
            "pragmatic",
            "cost-benefit",
            "robustness",
            "minimalist",
            "capability",
            "implementation",
            "arbiter",
        }
        assert set(LENS_REQUIREMENTS.keys()) == expected_lenses

    def test_each_lens_has_required_fields(self):
        """Each lens configuration has the required structure."""
        required_fields = {"table_columns", "min_rows", "sections", "description"}
        for lens, config in LENS_REQUIREMENTS.items():
            assert required_fields <= set(config.keys()), f"{lens} missing fields"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_is_valid_when_no_errors(self):
        """Result is valid when there are no errors."""
        result = ValidationResult()
        result.passed.append("[PASS] test: passed")
        result.warnings.append("[WARN] test: warning")
        assert result.is_valid is True

    def test_is_invalid_when_has_errors(self):
        """Result is invalid when there are errors."""
        result = ValidationResult()
        result.errors.append("[FAIL] test: failed")
        assert result.is_valid is False

    def test_check_records_pass(self):
        """check() records pass when condition is True."""
        result = ValidationResult()
        result.check("test", True, "passed condition")
        assert len(result.passed) == 1
        assert "[PASS] test: passed condition" in result.passed[0]

    def test_check_records_fail(self):
        """check() records error when condition is False."""
        result = ValidationResult()
        result.check("test", False, "failed condition")
        assert len(result.errors) == 1
        assert "[FAIL] test: failed condition" in result.errors[0]

    def test_check_records_warning_only(self):
        """check() records warning when warning_only=True and condition is False."""
        result = ValidationResult()
        result.check("test", False, "warning condition", warning_only=True)
        assert len(result.warnings) == 1
        assert len(result.errors) == 0


class TestFindTableRows:
    """Tests for find_table_rows function."""

    def test_counts_data_rows(self):
        """Correctly counts data rows in a markdown table."""
        content = """\
| Header1 | Header2 |
|---------|---------|
| row1    | data    |
| row2    | data    |
| row3    | data    |
"""
        assert find_table_rows(content) == 3

    def test_ignores_header_and_separator(self):
        """Does not count header or separator as data rows."""
        content = """\
| Just Header |
|-------------|
"""
        assert find_table_rows(content) == 0

    def test_handles_no_table(self):
        """Returns 0 when there's no table."""
        content = "Just some text without any tables."
        assert find_table_rows(content) == 0


class TestCheckTableColumns:
    """Tests for check_table_columns function."""

    def test_finds_all_columns(self):
        """Returns True when all required columns are present."""
        content = """\
| Vulnerability | Evidence | Attack Scenario | Severity |
|--------------|----------|-----------------|----------|
| Issue 1      | line 42  | inject data     | High     |
"""
        has_all, missing = check_table_columns(
            content, ["vulnerability", "evidence", "attack scenario", "severity"]
        )
        assert has_all is True
        assert missing == []

    def test_reports_missing_columns(self):
        """Returns False and lists missing columns."""
        content = """\
| Issue | Notes |
|-------|-------|
| Something | Something else |
"""
        has_all, missing = check_table_columns(
            content, ["vulnerability", "evidence"]
        )
        assert has_all is False
        assert "vulnerability" in missing
        assert "evidence" in missing

    def test_case_insensitive(self):
        """Column matching is case-insensitive."""
        content = "| VULNERABILITY | Evidence | ATTACK SCENARIO |"
        has_all, missing = check_table_columns(
            content, ["vulnerability", "attack scenario"]
        )
        assert has_all is True


class TestCheckSections:
    """Tests for check_sections function."""

    def test_finds_header_sections(self):
        """Finds sections marked with ## headers."""
        content = """\
## What Works
Some content here.

## What's Missing
More content.
"""
        has_all, missing = check_sections(content, ["what works", "what's missing"])
        assert has_all is True
        assert missing == []

    def test_finds_bold_sections(self):
        """Finds sections marked with **bold**."""
        content = """\
**Verdict:**
The final assessment.
"""
        has_all, missing = check_sections(content, ["verdict"])
        assert has_all is True

    def test_reports_missing_sections(self):
        """Returns False and lists missing sections."""
        content = "## Only One Section"
        has_all, missing = check_sections(content, ["one section", "another section"])
        assert has_all is False
        assert "another section" in missing


class TestValidateOutput:
    """Tests for validate_output function."""

    def test_adversarial_valid_output(self):
        """Valid adversarial output passes validation."""
        content = """\
# Adversarial Lens Output

| Vulnerability | Evidence | Attack Scenario | Severity |
|--------------|----------|-----------------|----------|
| Missing input validation | Line 42 | Inject malformed data | Critical |
| No rate limiting | config.py | DoS attack | Major |
"""
        result = validate_output("adversarial", content)
        assert result.is_valid, f"Validation failed: {result.errors}"

    def test_adversarial_missing_columns(self):
        """Adversarial output missing required columns fails."""
        content = """\
# Adversarial Lens Output

| Issue | Notes |
|-------|-------|
| Something | Something else |
"""
        result = validate_output("adversarial", content)
        assert result.is_valid is False
        assert any("column" in e.lower() for e in result.errors)

    def test_pragmatic_valid_output(self):
        """Valid pragmatic output passes validation."""
        content = """\
# Pragmatic Practitioner Output

## What Works
- Good structure
- Clear documentation

## What's Missing
- Error handling

## Friction Points
- Complex setup

## Verdict
Usable but needs work.
"""
        result = validate_output("pragmatic", content)
        assert result.is_valid, f"Validation failed: {result.errors}"

    def test_pragmatic_missing_sections(self):
        """Pragmatic output missing required sections fails."""
        content = """\
# Pragmatic Practitioner Output

## What Works
- Something good
"""
        result = validate_output("pragmatic", content)
        assert result.is_valid is False
        # Should fail because pragmatic has critical sections

    def test_unknown_lens_with_short_content_fails(self):
        """Unknown lens with insufficient content fails content_length check."""
        result = validate_output("unknown_lens", "some content")
        assert result.is_valid is False
        # Unknown lens type is a warning, not an error
        assert any("unknown lens" in w.lower() for w in result.warnings)
        # Failure is due to content_length check (< 100 chars)
        assert any("content" in e.lower() for e in result.errors)

    def test_empty_content_fails(self):
        """Empty or very short content fails."""
        result = validate_output("adversarial", "too short")
        assert result.is_valid is False

    def test_capability_needs_assumption_reality(self):
        """Capability lens checks for assumption/reality pairs."""
        content = """\
# Capability Realist Output

**Assumption:** The model can do X
**Reality:** Actually it cannot
**Evidence:** Testing showed failures
**Mitigation:** Use alternative approach
"""
        result = validate_output("capability", content)
        assert result.is_valid, f"Validation failed: {result.errors}"
