"""Tests for ValidationPanel."""

from pathlib import Path

import pytest

from lib.validator import ValidationPanel
from lib.state import ValidationResult


class TestStructureCheck:
    """Tests for structure validation."""

    def test_valid_structure_passes(self) -> None:
        """Valid frontmatter and structure passes."""
        panel = ValidationPanel()
        content = """---
name: test-skill
description: Use when testing
---

# Test Skill

## Overview

Content here.
"""
        check = panel._check_structure(content)

        assert check.passed is True
        assert len(check.issues) == 0

    def test_missing_frontmatter_fails(self) -> None:
        """Missing frontmatter fails structure check."""
        panel = ValidationPanel()
        content = """# Test Skill

No frontmatter here.
"""
        check = panel._check_structure(content)

        assert check.passed is False
        assert any("frontmatter" in i.lower() for i in check.issues)

    def test_missing_required_fields_fails(self) -> None:
        """Missing name or description fails."""
        panel = ValidationPanel()
        content = """---
name: test-skill
---

# Test
"""
        check = panel._check_structure(content)

        assert check.passed is False
        assert any("description" in i.lower() for i in check.issues)


class TestContentQualityCheck:
    """Tests for content quality validation."""

    def test_good_content_passes(self) -> None:
        """Content with trigger phrases and good length passes."""
        panel = ValidationPanel()
        content = """---
name: test-skill
description: Use when working with "testing patterns" or need test guidance
---

# Test Skill

## Overview

This skill provides guidance for testing patterns.

## When to Use

- Working with unit tests
- Need testing patterns
- Writing integration tests

## Process

Detailed process content here with enough words to meet the minimum length requirement.
More content to ensure we have sufficient body text for the quality check.
"""
        check = panel._check_content_quality(content)

        assert check.passed is True

    def test_short_body_fails(self) -> None:
        """Body under 100 characters fails."""
        panel = ValidationPanel()
        content = """---
name: test
description: Use when testing
---

# Test

Short.
"""
        check = panel._check_content_quality(content)

        assert check.passed is False
        assert any("length" in i.lower() or "short" in i.lower() for i in check.issues)


class TestIntegrationCheck:
    """Tests for integration validation."""

    def test_unique_name_passes(self, tmp_path: Path) -> None:
        """Skill with unique name passes."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        panel = ValidationPanel(existing_skills_dir=skills_dir)
        check = panel._check_integration("new-skill", "content")

        assert check.passed is True

    def test_conflicting_name_fails(self, tmp_path: Path) -> None:
        """Skill with existing name fails."""
        skills_dir = tmp_path / "skills"
        (skills_dir / "existing-skill").mkdir(parents=True)

        panel = ValidationPanel(existing_skills_dir=skills_dir)
        check = panel._check_integration("existing-skill", "content")

        assert check.passed is False
        assert any("conflict" in i.lower() or "exists" in i.lower() for i in check.issues)


class TestValidationPanel:
    """Tests for full validation panel."""

    def test_validate_runs_all_checks(self, tmp_path: Path) -> None:
        """validate() runs structure, content, and integration checks."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        panel = ValidationPanel(existing_skills_dir=skills_dir)
        content = """---
name: test-skill
description: Use when working with "testing" patterns
---

# Test Skill

## Overview

This skill provides testing guidance with enough content to pass quality checks.

## When to Use

- Testing scenarios
- Test patterns needed
- Quality assurance

## Process

Follow these steps for effective testing patterns and workflows.
Additional content here to meet minimum length requirements.
"""
        result = panel.validate("test-skill", content)

        assert isinstance(result, ValidationResult)
        assert len(result.checks) == 3
        assert result.passed is True
