#!/usr/bin/env python3
"""
Validate optimization design document.

Checks that a design document has required sections and valid embedded JSON.

Usage:
    python validate_design.py <design-doc.md>
    python validate_design.py <design-doc.md> --json
    python validate_design.py <design-doc.md> --fix

Exit Codes:
    0  - Valid document
    1  - General failure
    2  - Invalid arguments
    10 - Validation failure (missing sections or invalid JSON)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: str  # "error" | "warning"
    category: str
    message: str
    line: Optional[int] = None


@dataclass
class ValidationResult:
    """Result of design document validation."""
    success: bool
    valid: bool
    document_path: str
    issues: list
    sections_found: list
    sections_missing: list
    json_valid: bool
    json_data: Optional[dict] = None

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i["severity"] == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i["severity"] == "warning")


REQUIRED_SECTIONS = [
    "Summary",
    "Quick Wins",
    "High Value",
]

OPTIONAL_SECTIONS = [
    "Consider",
    "Cross-Cutting Notes",
    "Score Summary",
    "Temporal Analysis",
    "Resolved Conflicts",
    "Extension Points",
]

JSON_PATTERN = re.compile(
    r'<!--\s*OPTIMIZATION_DATA\s*\n(.*?)\n\s*-->',
    re.DOTALL
)


def find_sections(content: str) -> list[str]:
    """Find all H2 sections in the document."""
    pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    return [match.group(1).strip() for match in pattern.finditer(content)]


def extract_json(content: str) -> tuple[Optional[dict], Optional[str]]:
    """Extract and parse embedded JSON from document."""
    match = JSON_PATTERN.search(content)
    if not match:
        return None, "No OPTIMIZATION_DATA JSON block found"

    try:
        data = json.loads(match.group(1))
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"


def validate_json_schema(data: dict) -> list[ValidationIssue]:
    """Validate the structure of the embedded JSON."""
    issues = []

    # Check for required fields
    required_fields = ["plugin", "date", "scores"]
    for field in required_fields:
        if field not in data:
            issues.append(ValidationIssue(
                severity="error",
                category="json_schema",
                message=f"Missing required field: {field}"
            ))

    # Validate scores structure
    if "scores" in data:
        scores = data["scores"]
        if not isinstance(scores, dict):
            issues.append(ValidationIssue(
                severity="error",
                category="json_schema",
                message="'scores' must be an object"
            ))
        else:
            if "before" not in scores:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="json_schema",
                    message="Missing 'scores.before'"
                ))
            if "after" not in scores:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="json_schema",
                    message="Missing 'scores.after'"
                ))

    # Validate suggestions if present
    if "suggestions" in data:
        if not isinstance(data["suggestions"], list):
            issues.append(ValidationIssue(
                severity="error",
                category="json_schema",
                message="'suggestions' must be an array"
            ))
        else:
            for i, suggestion in enumerate(data["suggestions"]):
                if not isinstance(suggestion, dict):
                    issues.append(ValidationIssue(
                        severity="error",
                        category="json_schema",
                        message=f"Suggestion {i} must be an object"
                    ))
                elif "id" not in suggestion:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="json_schema",
                        message=f"Suggestion {i} missing 'id'"
                    ))

    return issues


def validate_document(doc_path: Path) -> ValidationResult:
    """Validate an optimization design document."""

    if not doc_path.exists():
        return ValidationResult(
            success=False,
            valid=False,
            document_path=str(doc_path),
            issues=[asdict(ValidationIssue(
                severity="error",
                category="file",
                message=f"File not found: {doc_path}"
            ))],
            sections_found=[],
            sections_missing=[],
            json_valid=False,
        )

    content = doc_path.read_text()
    issues = []

    # Check sections
    sections_found = find_sections(content)
    sections_missing = [s for s in REQUIRED_SECTIONS if s not in sections_found]

    for section in sections_missing:
        issues.append(ValidationIssue(
            severity="error",
            category="structure",
            message=f"Missing required section: ## {section}"
        ))

    # Check optional sections (warn if missing)
    for section in OPTIONAL_SECTIONS:
        if section not in sections_found:
            issues.append(ValidationIssue(
                severity="warning",
                category="structure",
                message=f"Missing optional section: ## {section}"
            ))

    # Extract and validate JSON
    json_data, json_error = extract_json(content)
    json_valid = json_data is not None

    if json_error:
        issues.append(ValidationIssue(
            severity="warning",  # Warning, not error - JSON is optional
            category="json",
            message=json_error
        ))

    if json_data:
        issues.extend(validate_json_schema(json_data))

    # Check for empty sections
    for section in sections_found:
        pattern = re.compile(
            rf'^## {re.escape(section)}\s*\n(.*?)(?=^## |\Z)',
            re.MULTILINE | re.DOTALL
        )
        match = pattern.search(content)
        if match:
            section_content = match.group(1).strip()
            if len(section_content) < 10:  # Effectively empty
                issues.append(ValidationIssue(
                    severity="warning",
                    category="content",
                    message=f"Section '{section}' appears empty"
                ))

    # Determine validity (no errors)
    error_count = sum(1 for i in issues if i.severity == "error")
    valid = error_count == 0

    return ValidationResult(
        success=True,
        valid=valid,
        document_path=str(doc_path),
        issues=[asdict(i) for i in issues],
        sections_found=sections_found,
        sections_missing=sections_missing,
        json_valid=json_valid,
        json_data=json_data,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Validate optimization design document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("document", type=Path, help="Path to design document")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = validate_document(args.document)

    if args.json:
        # Don't include full json_data in output (too verbose)
        output = asdict(result)
        if output.get("json_data"):
            output["json_data"] = {"present": True, "keys": list(result.json_data.keys())}
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(f"\n{'='*60}")
        print(f"Design Document Validation: {args.document.name}")
        print(f"{'='*60}\n")

        if result.valid:
            print("✓ VALID\n")
        else:
            print("✗ INVALID\n")

        print(f"Sections found: {len(result.sections_found)}")
        print(f"Sections missing: {len(result.sections_missing)}")
        print(f"JSON valid: {'Yes' if result.json_valid else 'No'}")
        print()

        if result.issues:
            errors = [i for i in result.issues if i["severity"] == "error"]
            warnings = [i for i in result.issues if i["severity"] == "warning"]

            if errors:
                print("Errors:")
                for issue in errors:
                    print(f"  ✗ [{issue['category']}] {issue['message']}")
                print()

            if warnings:
                print("Warnings:")
                for issue in warnings:
                    print(f"  ! [{issue['category']}] {issue['message']}")
                print()

        if result.sections_missing:
            print(f"Add these sections: {', '.join(result.sections_missing)}")

    sys.exit(0 if result.valid else 10)


if __name__ == "__main__":
    main()
