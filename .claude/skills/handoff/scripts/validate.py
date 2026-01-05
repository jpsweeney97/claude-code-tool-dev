#!/usr/bin/env python3
"""
validate.py - Validate synthesized handoff structure.

Part of the handoff skill.

Responsibilities:
- Check for required sections (frontmatter, title, Summary, Next Steps)
- Validate content quality (decisions have reasoning, etc.)
- Return JSON result for skill workflow

Usage:
    echo "handoff content" | python validate.py
    python validate.py --file handoff.md

Output:
    JSON: {"valid": true} or {"valid": false, "issues": [...]}

Exit Codes:
    0  - Valid (or --help)
    1  - Invalid (issues found)
    2  - Input error
"""

import argparse
import json
import re
import sys
from typing import List


def extract_section(content: str, section_name: str) -> str:
    """Extract content of a markdown section."""
    pattern = rf"^## {re.escape(section_name)}\s*$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return ""

    start = match.end()

    # Find next section or end
    next_section = re.search(r"^## ", content[start:], re.MULTILINE)
    if next_section:
        end = start + next_section.start()
    else:
        end = len(content)

    return content[start:end].strip()


def validate_handoff(content: str) -> List[str]:
    """
    Validate handoff content structure.

    Returns list of issues found, empty if valid.
    """
    issues = []

    # 1. Structure checks
    if not content.strip():
        issues.append("Empty content")
        return issues

    if not content.startswith("---"):
        issues.append("Missing YAML frontmatter (must start with ---)")

    if "# Handoff:" not in content:
        issues.append("Missing title (expected '# Handoff: ...')")

    if "## Summary" not in content:
        issues.append("Missing Summary section")

    if "## Next Steps" not in content:
        issues.append("Missing Next Steps section")

    # 2. Content quality checks
    if "## Decisions" in content:
        decisions_section = extract_section(content, "Decisions")
        # Check if decisions have reasoning
        if "**Choice:**" in decisions_section:
            if "**Reasoning:**" not in decisions_section:
                issues.append("Decision found with Choice but missing Reasoning")

    # 3. Artifact checks
    if "## Artifacts" in content:
        artifacts_section = extract_section(content, "Artifacts")
        # Artifacts should contain code blocks if section has content
        if artifacts_section.strip() and "```" not in artifacts_section:
            issues.append("Artifacts section has content but no code blocks (artifacts should be preserved verbatim)")

    # 4. Frontmatter validation
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            required_fields = ["date", "repository"]
            for field in required_fields:
                if f"{field}:" not in frontmatter:
                    issues.append(f"Frontmatter missing required field: {field}")

    # 5. Next Steps validation
    next_steps_section = extract_section(content, "Next Steps")
    if next_steps_section:
        # Should have numbered items
        if not re.search(r"^\d+\.", next_steps_section, re.MULTILINE):
            issues.append("Next Steps should have numbered items (1. 2. 3.)")

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Validate synthesized handoff structure",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--file", "-f",
        help="Read from file instead of stdin"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )

    args = parser.parse_args()

    # Read content
    try:
        if args.file:
            with open(args.file) as f:
                content = f.read()
        else:
            content = sys.stdin.read()
    except Exception as e:
        print(json.dumps({
            "valid": False,
            "issues": [f"Failed to read input: {e}"]
        }))
        sys.exit(2)

    # Validate
    issues = validate_handoff(content)

    # Output result
    result = {
        "valid": len(issues) == 0,
        "issues": issues
    }

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
