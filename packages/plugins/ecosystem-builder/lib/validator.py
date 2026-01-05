"""Validation panel for skill artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from lib.state import ValidationCheck, ValidationResult


@dataclass
class ValidationPanel:
    """Three-check validation panel for skills."""

    existing_skills_dir: Path | None = None
    min_body_length: int = 100
    min_description_length: int = 20

    def validate(self, name: str, content: str) -> ValidationResult:
        """Run all validation checks."""
        checks = [
            self._check_structure(content),
            self._check_content_quality(content),
            self._check_integration(name, content),
        ]

        return ValidationResult(
            artifact_name=name,
            checks=checks,
        )

    def _check_structure(self, content: str) -> ValidationCheck:
        """Check structural requirements."""
        issues = []

        # Check frontmatter exists
        if not content.startswith("---"):
            issues.append("Missing YAML frontmatter (must start with ---)")
            return ValidationCheck(name="structure", passed=False, issues=issues)

        # Parse frontmatter
        lines = content.split("\n")
        try:
            yaml_end = lines.index("---", 1)
            frontmatter_text = "\n".join(lines[1:yaml_end])
        except ValueError:
            issues.append("Malformed frontmatter (missing closing ---)")
            return ValidationCheck(name="structure", passed=False, issues=issues)

        # Check required fields
        try:
            metadata = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            issues.append(f"Invalid YAML in frontmatter: {e}")
            return ValidationCheck(name="structure", passed=False, issues=issues)

        if not metadata:
            issues.append("Empty frontmatter")
            return ValidationCheck(name="structure", passed=False, issues=issues)

        if "name" not in metadata:
            issues.append("Missing required field: name")
        if "description" not in metadata:
            issues.append("Missing required field: description")

        return ValidationCheck(
            name="structure",
            passed=len(issues) == 0,
            issues=issues,
        )

    def _check_content_quality(self, content: str) -> ValidationCheck:
        """Check content quality requirements."""
        issues = []

        # Extract body (after frontmatter)
        lines = content.split("\n")
        try:
            yaml_end = lines.index("---", 1)
            body = "\n".join(lines[yaml_end + 1 :]).strip()
        except ValueError:
            body = content

        # Check body length
        if len(body) < self.min_body_length:
            issues.append(
                f"Body too short ({len(body)} chars, minimum {self.min_body_length})"
            )

        # Check description has trigger phrases
        if content.startswith("---"):
            lines = content.split("\n")
            try:
                yaml_end = lines.index("---", 1)
                frontmatter_text = "\n".join(lines[1:yaml_end])
                metadata = yaml.safe_load(frontmatter_text)
                description = metadata.get("description", "")

                # Check for trigger phrase indicators
                has_trigger = (
                    '"' in description
                    or "Use when" in description
                    or "Use for" in description
                )
                if not has_trigger:
                    issues.append(
                        "Description should include trigger phrases "
                        "(quoted terms or 'Use when/for')"
                    )
            except (ValueError, yaml.YAMLError):
                pass  # Structure check will catch this

        return ValidationCheck(
            name="content_quality",
            passed=len(issues) == 0,
            issues=issues,
        )

    def _check_integration(self, name: str, content: str) -> ValidationCheck:
        """Check integration with existing ecosystem."""
        issues = []

        # Check for naming conflicts
        if self.existing_skills_dir and self.existing_skills_dir.exists():
            existing_path = self.existing_skills_dir / name
            if existing_path.exists():
                issues.append(f"Name conflict: skill '{name}' already exists")

        return ValidationCheck(
            name="integration",
            passed=len(issues) == 0,
            issues=issues,
        )
