#!/usr/bin/env python3
"""
Validate the verify skill structure and components.

Self-verification script that ensures all skill components are properly
configured and functional. Run this after making changes to the skill.

Exit codes:
    0: All validations pass
    1: Input error (skill directory not found)
    10: Validation failures detected

Usage:
    python validate_skill.py                # Validate from script location
    python validate_skill.py /path/to/skill # Validate specific skill directory
    python validate_skill.py --json         # JSON output for automation
    python validate_skill.py --fix          # Attempt to fix simple issues
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ValidationIssue:
    """A validation issue found during checks."""
    severity: str  # error, warning, info
    component: str
    message: str
    fixable: bool = False


@dataclass
class ValidationResult:
    """Result of skill validation."""
    skill_path: str
    issues: list[ValidationIssue] = field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0

    @property
    def success(self) -> bool:
        return all(i.severity != "error" for i in self.issues)


# =============================================================================
# VALIDATORS
# =============================================================================

def validate_skill_md(skill_dir: Path, result: ValidationResult) -> None:
    """Validate SKILL.md structure and content."""
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        result.issues.append(ValidationIssue(
            severity="error",
            component="SKILL.md",
            message="SKILL.md not found",
        ))
        result.checks_failed += 1
        return

    content = skill_md.read_text()
    lines = content.splitlines()

    # Check frontmatter
    if not lines or not lines[0].strip() == "---":
        result.issues.append(ValidationIssue(
            severity="error",
            component="SKILL.md",
            message="Frontmatter must start on line 1",
        ))
        result.checks_failed += 1
    else:
        result.checks_passed += 1

    # Check required frontmatter fields
    frontmatter_end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            frontmatter_end = i
            break

    if frontmatter_end == -1:
        result.issues.append(ValidationIssue(
            severity="error",
            component="SKILL.md",
            message="Frontmatter not properly closed",
        ))
        result.checks_failed += 1
        return

    frontmatter = "\n".join(lines[1:frontmatter_end])

    if "name:" not in frontmatter:
        result.issues.append(ValidationIssue(
            severity="error",
            component="SKILL.md",
            message="Missing required 'name' field in frontmatter",
        ))
        result.checks_failed += 1
    else:
        result.checks_passed += 1

    if "description:" not in frontmatter:
        result.issues.append(ValidationIssue(
            severity="error",
            component="SKILL.md",
            message="Missing required 'description' field in frontmatter",
        ))
        result.checks_failed += 1
    else:
        result.checks_passed += 1

    # Check version in metadata
    if "version:" not in frontmatter:
        result.issues.append(ValidationIssue(
            severity="warning",
            component="SKILL.md",
            message="No version in metadata (recommended)",
        ))

    # Check line count
    line_count = len(lines)
    if line_count > 500:
        result.issues.append(ValidationIssue(
            severity="warning",
            component="SKILL.md",
            message=f"SKILL.md has {line_count} lines (recommended: ≤500)",
        ))
    else:
        result.checks_passed += 1

    # Check description length
    desc_match = re.search(r"description:\s*(.+)", frontmatter)
    if desc_match:
        desc = desc_match.group(1).strip()
        if len(desc) > 1024:
            result.issues.append(ValidationIssue(
                severity="error",
                component="SKILL.md",
                message=f"Description exceeds 1024 chars ({len(desc)})",
            ))
            result.checks_failed += 1
        elif "<" in desc or ">" in desc:
            result.issues.append(ValidationIssue(
                severity="error",
                component="SKILL.md",
                message="Description contains angle brackets",
            ))
            result.checks_failed += 1
        else:
            result.checks_passed += 1


def validate_scripts(skill_dir: Path, result: ValidationResult) -> None:
    """Validate scripts in the scripts/ directory."""
    scripts_dir = skill_dir / "scripts"

    if not scripts_dir.exists():
        result.issues.append(ValidationIssue(
            severity="info",
            component="scripts/",
            message="No scripts directory",
        ))
        return

    expected_scripts = [
        "match_claim.py",
        "promote_claims.py",
        "extract_claims.py",
        "refresh_claims.py",
        "check_version.py",
        "batch_verify.py",
        "validate_skill.py",
    ]

    for script_name in expected_scripts:
        script_path = scripts_dir / script_name
        if not script_path.exists():
            result.issues.append(ValidationIssue(
                severity="warning",
                component=f"scripts/{script_name}",
                message="Expected script not found",
            ))
            continue

        content = script_path.read_text()

        # Check shebang
        if not content.startswith("#!/usr/bin/env python3"):
            result.issues.append(ValidationIssue(
                severity="warning",
                component=f"scripts/{script_name}",
                message="Missing or incorrect shebang",
                fixable=True,
            ))
        else:
            result.checks_passed += 1

        # Check docstring
        if '"""' not in content[:500]:
            result.issues.append(ValidationIssue(
                severity="warning",
                component=f"scripts/{script_name}",
                message="Missing module docstring",
            ))
        else:
            result.checks_passed += 1

        # Check exit codes documentation
        if "Exit codes:" not in content:
            result.issues.append(ValidationIssue(
                severity="warning",
                component=f"scripts/{script_name}",
                message="Exit codes not documented in docstring",
            ))
        else:
            result.checks_passed += 1

        # Check for argparse (CLI interface)
        if "argparse" not in content:
            result.issues.append(ValidationIssue(
                severity="info",
                component=f"scripts/{script_name}",
                message="No argparse (no CLI interface)",
            ))


def validate_references(skill_dir: Path, result: ValidationResult) -> None:
    """Validate references/ directory."""
    refs_dir = skill_dir / "references"

    if not refs_dir.exists():
        result.issues.append(ValidationIssue(
            severity="info",
            component="references/",
            message="No references directory",
        ))
        return

    expected_refs = [
        "known-claims.md",
        "pending-claims.md",
        "document-mode.md",
        "capture-mode.md",
        "scripts-reference.md",
    ]

    for ref_name in expected_refs:
        ref_path = refs_dir / ref_name
        if not ref_path.exists():
            result.issues.append(ValidationIssue(
                severity="warning",
                component=f"references/{ref_name}",
                message="Expected reference file not found",
            ))
        else:
            result.checks_passed += 1

    # Check known-claims.md structure
    known_claims = refs_dir / "known-claims.md"
    if known_claims.exists():
        content = known_claims.read_text()

        if "**Last verified:**" not in content:
            result.issues.append(ValidationIssue(
                severity="warning",
                component="references/known-claims.md",
                message="Missing 'Last verified' header",
            ))

        if "**Claude Code version:**" not in content:
            result.issues.append(ValidationIssue(
                severity="warning",
                component="references/known-claims.md",
                message="Missing 'Claude Code version' header",
            ))

        # Count claims
        claim_count = content.count("| ✓") + content.count("| ✗") + content.count("| ~") + content.count("| ?")
        if claim_count < 50:
            result.issues.append(ValidationIssue(
                severity="info",
                component="references/known-claims.md",
                message=f"Only {claim_count} claims cached (consider expanding)",
            ))
        else:
            result.checks_passed += 1


def validate_hooks(skill_dir: Path, result: ValidationResult) -> None:
    """Check for associated hooks."""
    # Look in parent .claude/hooks/ for related hooks
    hooks_dir = skill_dir.parent.parent / "hooks"
    hook_file = hooks_dir / "verify-capture-reminder.py"

    if not hook_file.exists():
        result.issues.append(ValidationIssue(
            severity="info",
            component="hooks/",
            message="verify-capture-reminder.py hook not in .claude/hooks/",
        ))
    else:
        result.checks_passed += 1


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate verify skill structure and components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Validation checks:
    - SKILL.md: frontmatter, required fields, line count, description
    - scripts/: shebang, docstring, exit codes, argparse
    - references/: expected files, known-claims.md structure
    - hooks/: associated hooks exist

Examples:
    # Validate from script location
    python validate_skill.py

    # Validate specific skill directory
    python validate_skill.py /path/to/skill

    # JSON output
    python validate_skill.py --json
        """,
    )
    parser.add_argument(
        "skill_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Path to skill directory (default: parent of scripts/)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix simple issues (not implemented)",
    )
    args = parser.parse_args()

    # Determine skill directory
    if args.skill_dir:
        skill_dir = args.skill_dir
    else:
        # Default: parent directory of scripts/
        skill_dir = Path(__file__).parent.parent

    if not skill_dir.exists():
        if args.json:
            print(json.dumps({"error": f"Skill directory not found: {skill_dir}"}))
        else:
            print(f"Error: Skill directory not found: {skill_dir}", file=sys.stderr)
        return 1

    # Run validations
    result = ValidationResult(skill_path=str(skill_dir))

    validate_skill_md(skill_dir, result)
    validate_scripts(skill_dir, result)
    validate_references(skill_dir, result)
    validate_hooks(skill_dir, result)

    # Output
    if args.json:
        output = {
            "skill_path": result.skill_path,
            "success": result.success,
            "checks_passed": result.checks_passed,
            "checks_failed": result.checks_failed,
            "issues": [asdict(i) for i in result.issues],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Skill Validation: {skill_dir.name}")
        print("=" * 50)
        print(f"Checks passed: {result.checks_passed}")
        print(f"Checks failed: {result.checks_failed}")
        print()

        if result.issues:
            # Group by severity
            errors = [i for i in result.issues if i.severity == "error"]
            warnings = [i for i in result.issues if i.severity == "warning"]
            infos = [i for i in result.issues if i.severity == "info"]

            if errors:
                print("❌ Errors:")
                for issue in errors:
                    print(f"  [{issue.component}] {issue.message}")
                print()

            if warnings:
                print("⚠️  Warnings:")
                for issue in warnings:
                    print(f"  [{issue.component}] {issue.message}")
                print()

            if infos:
                print("ℹ️  Info:")
                for issue in infos:
                    print(f"  [{issue.component}] {issue.message}")
                print()

        if result.success:
            print("✓ Skill validation passed")
        else:
            print("✗ Skill validation failed")

    return 0 if result.success else 10


if __name__ == "__main__":
    sys.exit(main())
