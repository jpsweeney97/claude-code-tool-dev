#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the consultation contract against skill and agent stub references.

Checks:
1. Contract has all 17 expected sections (## N. Title headers).
2. All (§N) stub references in SKILL.md and codex-dialogue.md resolve to
   real contract sections.
3. SKILL.md governance rule count matches §15 in the contract (both must be 7).

Usage:
    uv run scripts/validate_consultation_contract.py
    uv run scripts/validate_consultation_contract.py --repo-root /path/to/repo

Exit codes: 0 = all checks pass, 1 = one or more failures.
"""

import argparse
import re
import sys
from pathlib import Path

EXPECTED_SECTION_COUNT = 17
EXPECTED_GOVERNANCE_RULE_COUNT = 7

# Matches (§N) in stub prose — the canonical stub reference format
STUB_REF_PATTERN = re.compile(r'\(§(\d+)\)')

# Matches ## N. in contract — the section definition format
CONTRACT_SECTION_PATTERN = re.compile(r'^## (\d+)\.', re.MULTILINE)

# Matches numbered governance rules with bold headings: "N. **Heading:**"
GOVERNANCE_RULE_PATTERN = re.compile(r'^\d+\. \*\*', re.MULTILINE)


def read_file(path: Path) -> str:
    """Read a file. Raises FileNotFoundError with descriptive message on failure."""
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    return path.read_text()


def extract_contract_sections(contract_text: str) -> set[int]:
    """Return the set of section numbers defined in ## N. headers."""
    return {int(n) for n in CONTRACT_SECTION_PATTERN.findall(contract_text)}


def extract_stub_refs(text: str) -> set[int]:
    """Return the set of section numbers referenced via (§N) in stub text."""
    return {int(n) for n in STUB_REF_PATTERN.findall(text)}


def extract_section_text(text: str, section_header: str) -> str | None:
    """Return the text of a section from its header to the next ## header (or EOF)."""
    start = text.find(section_header)
    if start == -1:
        return None
    next_section = text.find("\n## ", start + len(section_header))
    if next_section == -1:
        return text[start:]
    return text[start:next_section]


def count_governance_rules(section_text: str) -> int:
    """Count numbered governance rules (N. **...) in section text."""
    return len(GOVERNANCE_RULE_PATTERN.findall(section_text))


def check_section_count(contract_sections: set[int]) -> list[str]:
    """Verify the contract has exactly EXPECTED_SECTION_COUNT sections."""
    errors: list[str] = []
    expected = set(range(1, EXPECTED_SECTION_COUNT + 1))
    missing = expected - contract_sections
    extra = contract_sections - expected
    if missing:
        errors.append(f"contract missing section(s): {sorted(missing)}")
    if extra:
        errors.append(f"contract has unexpected section(s): {sorted(extra)}")
    return errors


def check_stub_references(
    filename: str,
    text: str,
    contract_sections: set[int],
) -> list[str]:
    """Verify all (§N) stub references in text resolve to real contract sections."""
    refs = extract_stub_refs(text)
    unresolved = refs - contract_sections
    if not unresolved:
        return []
    return [
        f"{filename}: stub reference(s) §{sorted(unresolved)} not found in contract"
    ]


def check_governance_rule_count(skill_text: str, contract_text: str) -> list[str]:
    """Verify SKILL.md governance rule count matches §15 in the contract."""
    skill_section = extract_section_text(skill_text, "## Governance")
    if skill_section is None:
        return ["SKILL.md: Governance section not found"]
    skill_count = count_governance_rules(skill_section)

    contract_section = extract_section_text(contract_text, "## 15. Governance Locks")
    if contract_section is None:
        return ["contract: §15 Governance Locks section not found"]
    contract_count = count_governance_rules(contract_section)

    if skill_count != contract_count:
        return [
            f"governance rule count mismatch: SKILL.md has {skill_count}, "
            f"contract §15 has {contract_count}"
        ]
    if skill_count != EXPECTED_GOVERNANCE_RULE_COUNT:
        return [
            f"governance rule count wrong: expected {EXPECTED_GOVERNANCE_RULE_COUNT}, "
            f"got {skill_count}"
        ]
    return []


def validate(repo_root: Path | None = None) -> list[str]:
    """Run all checks. Returns list of error strings — empty list means all pass."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    contract_path = repo_root / "packages/plugins/cross-model/references/consultation-contract.md"
    skill_path = repo_root / "packages/plugins/cross-model/skills/codex/SKILL.md"
    agent_path = repo_root / "packages/plugins/cross-model/agents/codex-dialogue.md"

    try:
        contract_text = read_file(contract_path)
    except FileNotFoundError as e:
        return [f"validate failed: cannot read contract. Got: {str(e)!r:.100}"]

    try:
        skill_text = read_file(skill_path)
    except FileNotFoundError as e:
        return [f"validate failed: cannot read skill. Got: {str(e)!r:.100}"]

    try:
        agent_text = read_file(agent_path)
    except FileNotFoundError as e:
        return [f"validate failed: cannot read agent. Got: {str(e)!r:.100}"]

    contract_sections = extract_contract_sections(contract_text)

    errors: list[str] = []
    errors.extend(check_section_count(contract_sections))
    errors.extend(check_stub_references("SKILL.md", skill_text, contract_sections))
    errors.extend(check_stub_references("codex-dialogue.md", agent_text, contract_sections))
    errors.extend(check_governance_rule_count(skill_text, contract_text))
    return errors


def main() -> int:
    """Run validation, print results, return exit code."""
    parser = argparse.ArgumentParser(
        description="Validate the consultation contract against skill and agent stubs."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of this script's directory)",
    )
    args = parser.parse_args()

    print("validate_consultation_contract: running checks...")
    errors = validate(repo_root=args.repo_root)

    if errors:
        print(f"FAIL: {len(errors)} error(s) found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"PASS: all checks passed "
        f"({EXPECTED_SECTION_COUNT} sections, "
        f"{EXPECTED_GOVERNANCE_RULE_COUNT} governance rules, "
        f"stubs resolved)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
