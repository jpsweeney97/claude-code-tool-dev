#!/usr/bin/env python3
"""
validate_output.py - Validate agent outputs before synthesis

Part of the three-lens-audit skill.

Validates that agent outputs are well-formed and contain required
structure before attempting synthesis. Catches malformed outputs
that would produce unreliable synthesis results.

Usage:
    python validate_output.py <lens> <output_file>
    python validate_output.py adversarial agent1_output.md
    cat output.md | python validate_output.py pragmatic -

Exit Codes:
    0  - Valid output
    1  - General failure
    2  - Invalid arguments
    10 - Validation failed (output malformed)
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:
    from common import count_table_rows
except ImportError:
    from .common import count_table_rows


# ===========================================================================
# RESULT TYPES
# ===========================================================================

@dataclass
class ValidationResult:
    """Result object for validation with detailed check tracking."""
    passed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def check(self, name: str, condition: bool, message: str, warning_only: bool = False):
        """Record a validation check result."""
        if condition:
            self.passed.append(f"[PASS] {name}: {message}")
        elif warning_only:
            self.warnings.append(f"[WARN] {name}: {message}")
        else:
            self.errors.append(f"[FAIL] {name}: {message}")

    @property
    def is_valid(self) -> bool:
        """True if no errors (warnings are OK)."""
        return len(self.errors) == 0

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        total = len(self.passed) + len(self.warnings) + len(self.errors)
        return f"{len(self.passed)}/{total} checks passed, {len(self.warnings)} warnings, {len(self.errors)} errors"

    def format_report(self, title: str = "Validation Report") -> str:
        """Generate formatted report."""
        lines = [
            "=" * 60,
            title.center(60),
            "=" * 60,
            "",
            f"Summary: {self.summary}",
            ""
        ]

        if self.errors:
            lines.append("ERRORS:")
            lines.extend(f"  {e}" for e in self.errors)
            lines.append("")

        if self.warnings:
            lines.append("WARNINGS:")
            lines.extend(f"  {w}" for w in self.warnings)
            lines.append("")

        if self.passed:
            lines.append("PASSED:")
            lines.extend(f"  {p}" for p in self.passed)

        lines.append("=" * 60)
        return "\n".join(lines)


# ===========================================================================
# VALIDATION LOGIC
# ===========================================================================

# Lens validation requirements from agent-prompts.md
LENS_REQUIREMENTS = {
    "adversarial": {
        "table_columns": ["vulnerability", "evidence", "attack scenario", "severity"],
        "min_rows": 1,
        "sections": [],
        "description": "Adversarial Auditor"
    },
    "pragmatic": {
        "table_columns": [],
        "min_rows": 0,
        "sections": ["what works", "what's missing", "friction points", "verdict"],
        "description": "Pragmatic Practitioner"
    },
    "cost-benefit": {
        "table_columns": ["element", "effort", "benefit", "verdict"],
        "min_rows": 1,
        "sections": ["high-roi", "low-roi", "recommendations"],
        "description": "Cost/Benefit Analyst"
    },
    "robustness": {
        "table_columns": ["gap", "evidence", "risk scenario", "severity"],
        "min_rows": 1,
        "sections": [],
        "description": "Robustness Advocate"
    },
    "minimalist": {
        "table_columns": ["element", "keep/cut/simplify", "rationale", "effort saved"],
        "min_rows": 1,
        "sections": ["minimum viable"],
        "description": "Minimalist Advocate"
    },
    "capability": {
        "table_columns": [],
        "min_rows": 0,
        "sections": ["assumption", "reality", "evidence", "mitigation"],
        "description": "Capability Realist"
    },
    "implementation": {
        "table_columns": ["assumption", "reality", "evidence", "severity"],
        "min_rows": 1,
        "sections": ["artifact type", "works today", "behavioral risks", "state assumptions", "verdict"],
        "description": "Implementation Realist"
    },
    "arbiter": {
        "table_columns": [],
        "min_rows": 0,
        "sections": ["critical path", "quick wins", "defer", "verdict"],
        "description": "Arbiter"
    }
}


def check_table_columns(content: str, required_columns: List[str]) -> tuple[bool, List[str]]:
    """Check if table contains required columns (case-insensitive)."""
    content_lower = content.lower()
    found = []
    missing = []

    for col in required_columns:
        # Look for column in table header (within | ... |)
        # Allow for variations like "Attack Scenario" matching "attack scenario"
        col_lower = col.lower()
        if col_lower in content_lower:
            found.append(col)
        else:
            # Try without spaces
            col_compact = col_lower.replace(" ", "")
            if col_compact in content_lower.replace(" ", ""):
                found.append(col)
            else:
                missing.append(col)

    return len(missing) == 0, missing


def check_sections(content: str, required_sections: List[str]) -> tuple[bool, List[str]]:
    """Check if content contains required sections (case-insensitive)."""
    content_lower = content.lower()
    found = []
    missing = []

    for section in required_sections:
        section_lower = section.lower()
        # Look for section as header (## Section) or bold (**Section**)
        patterns = [
            f"## {section_lower}",
            f"**{section_lower}**",
            f"### {section_lower}",
            f"- **{section_lower}",
            f"**{section_lower}:",
        ]

        section_found = any(p in content_lower for p in patterns)

        # Also check for just the text if it's a label like "Verdict:"
        if not section_found and f"{section_lower}:" in content_lower:
            section_found = True

        if section_found:
            found.append(section)
        else:
            missing.append(section)

    return len(missing) == 0, missing


def validate_output(lens: str, content: str) -> ValidationResult:
    """Validate agent output for a specific lens type."""
    result = ValidationResult()

    # Handle unknown lens types with minimal validation (for custom lenses)
    if lens not in LENS_REQUIREMENTS:
        result.warnings.append(f"Unknown lens type '{lens}' - using minimal validation")

        # Minimal validation: check for non-trivial content
        content_len = len(content.strip())
        result.check(
            "content_length",
            content_len >= 100,
            f"Content has {content_len} characters (minimum: 100)"
        )

        # Check for table presence (expected but not required)
        has_table = "|" in content and "---" in content
        result.check(
            "table_presence",
            has_table,
            "Contains markdown table" if has_table else "No markdown table found",
            warning_only=True
        )

        return result

    reqs = LENS_REQUIREMENTS[lens]

    # Check content is not empty
    result.check(
        "non_empty",
        len(content.strip()) > 50,
        f"Content has {len(content)} characters"
    )

    # Check for required table columns
    if reqs["table_columns"]:
        has_columns, missing = check_table_columns(content, reqs["table_columns"])
        result.check(
            "table_columns",
            has_columns,
            f"Table has required columns" if has_columns else f"Missing columns: {', '.join(missing)}"
        )

    # Check for minimum table rows
    if reqs["min_rows"] > 0:
        row_count = count_table_rows(content)
        result.check(
            "table_rows",
            row_count >= reqs["min_rows"],
            f"Table has {row_count} data rows (minimum: {reqs['min_rows']})"
        )

    # Check for required sections
    if reqs["sections"]:
        has_sections, missing = check_sections(content, reqs["sections"])
        if not has_sections:
            # For some lenses, sections are critical; for others, they're nice-to-have
            if lens in ["pragmatic", "arbiter"]:
                result.check(
                    "sections",
                    has_sections,
                    f"Missing required sections: {', '.join(missing)}"
                )
            else:
                result.check(
                    "sections",
                    has_sections,
                    f"Missing sections: {', '.join(missing)}",
                    warning_only=True
                )
        else:
            result.check(
                "sections",
                True,
                "All required sections present"
            )

    # Lens-specific checks
    if lens == "adversarial":
        # Check for severity ratings
        has_severity = any(s in content.lower() for s in ["critical", "major", "minor"])
        result.check(
            "severity_ratings",
            has_severity,
            "Contains severity ratings (Critical/Major/Minor)",
            warning_only=True
        )

    elif lens == "cost-benefit":
        # Check for effort/benefit ratings
        has_ratings = any(r in content.upper() for r in ["H", "M", "L", "HIGH", "MEDIUM", "LOW"])
        result.check(
            "effort_benefit_ratings",
            has_ratings,
            "Contains effort/benefit ratings (H/M/L or High/Medium/Low)",
            warning_only=True
        )

    elif lens == "capability":
        # Check for assumption-reality pairs
        has_pairs = "assumption" in content.lower() and "reality" in content.lower()
        result.check(
            "assumption_reality_pairs",
            has_pairs,
            "Contains Assumption/Reality analysis pairs"
        )

    elif lens == "implementation":
        # Check for artifact type identification (Claude Code audit)
        artifact_types = ["skill", "hook", "plugin", "mcp server", "mcp", "command", "subagent", "feature proposal", "feature"]
        has_artifact_type = any(t in content.lower() for t in artifact_types)
        result.check(
            "artifact_type_identified",
            has_artifact_type,
            "Artifact type identified (Skill/Hook/Plugin/MCP/Command/Subagent/Feature)",
            warning_only=True
        )

        # Check for source citations (official docs)
        has_source = "source:" in content.lower() or "official" in content.lower() or "documentation" in content.lower()
        result.check(
            "official_source_cited",
            has_source,
            "References official documentation (required for verified claims)",
            warning_only=True
        )

    return result


# ===========================================================================
# CLI INTERFACE
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate three-lens-audit agent outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Lens Types:
  adversarial    - Requires table with Vulnerability/Evidence/Attack Scenario/Severity
  pragmatic      - Requires What Works/What's Missing/Friction Points/Verdict sections
  cost-benefit   - Requires Element/Effort/Benefit/Verdict table + ROI sections
  robustness     - Requires Gap/Evidence/Risk Scenario/Severity table
  minimalist     - Requires Element/Keep-Cut-Simplify/Rationale/Effort Saved table
  capability     - Requires Assumption/Reality/Evidence/Mitigation format
  implementation - Requires Artifact Type + Works Today/Behavioral Risks/Verdict (Claude Code)
  arbiter        - Requires Critical Path/Quick Wins/Defer tables + Verdict

Examples:
  %(prog)s adversarial agent1.md
  %(prog)s pragmatic agent2.md --json
  cat output.md | %(prog)s cost-benefit -
        """
    )

    parser.add_argument(
        "lens",
        type=str,
        help="Lens type to validate against (built-in or custom)"
    )

    parser.add_argument(
        "file",
        type=str,
        help="Path to output file, or '-' for stdin"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output errors"
    )

    args = parser.parse_args()

    # Read input
    if args.file == "-":
        content = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(2)
        content = path.read_text()

    # Validate
    result = validate_output(args.lens, content)

    # Output
    if args.json:
        import json
        output = {
            "valid": result.is_valid,
            "lens": args.lens,
            "summary": result.summary,
            "errors": result.errors,
            "warnings": result.warnings,
            "passed": result.passed
        }
        print(json.dumps(output, indent=2))
    elif args.quiet:
        if not result.is_valid:
            for error in result.errors:
                print(error, file=sys.stderr)
    else:
        # Handle custom lenses that aren't in LENS_REQUIREMENTS
        if args.lens in LENS_REQUIREMENTS:
            title = f"{LENS_REQUIREMENTS[args.lens]['description']} Output Validation"
        else:
            title = f"Custom Lens '{args.lens}' Output Validation"
        print(result.format_report(title))

    sys.exit(0 if result.is_valid else 10)


if __name__ == "__main__":
    main()
