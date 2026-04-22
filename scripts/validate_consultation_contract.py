#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Validate the consultation contract against skill and agent stub references.

Checks:
1. Contract has all 17 expected sections (## N. Title headers).
2. All (§N) stub references in SKILL.md, dialogue/SKILL.md, and codex-dialogue.md
   resolve to real contract sections.
3. SKILL.md governance rule count matches §15 in the contract (both must be 7).
4. §13 Event Contract references actual event types (dialogue_outcome,
   consultation_outcome).
5. §16 Conformance Checklist structure is valid.

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
EXPECTED_AGENT_GOVERNANCE_COUNT = 7
EXPECTED_GATHERER_GOVERNANCE_COUNT = 3

# Matches (§N) in stub prose — the canonical stub reference format
STUB_REF_PATTERN = re.compile(r"\(§(\d+)\)")

# Matches ## N. in contract — the section definition format
CONTRACT_SECTION_PATTERN = re.compile(r"^## (\d+)\.", re.MULTILINE)

# Matches numbered governance rules with bold headings: "N. **Heading:**"
GOVERNANCE_RULE_PATTERN = re.compile(r"^\d+\. \*\*", re.MULTILINE)


def read_file(path: Path) -> str:
    """Read a file. Raises OSError with descriptive message on failure."""
    try:
        return path.read_text()
    except OSError as e:
        raise OSError(f"cannot read {path} ({type(e).__name__}): {e}") from e


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


def check_agent_governance_count(agent_path: Path, expected_count: int) -> list[str]:
    """Verify an agent file has the expected number of governance rules."""
    try:
        agent_text = read_file(agent_path)
    except OSError as e:
        return [f"check_agent_governance failed: {e}"]

    section_text = extract_section_text(agent_text, "## Governance")
    if section_text is None:
        return [f"{agent_path.name}: Governance section not found"]

    count = count_governance_rules(section_text)
    if count != expected_count:
        return [
            f"{agent_path.name}: governance rule count wrong: "
            f"expected {expected_count}, got {count}"
        ]
    return []


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


def check_event_types_in_contract(contract_text: str) -> list[str]:
    """Verify §13 references the actual event types emitted by emit_analytics.py."""
    section = extract_section_text(contract_text, "## 13.")
    if section is None:
        return ["contract: §13 Event Contract section not found"]
    errors: list[str] = []
    for event_type in ("dialogue_outcome", "consultation_outcome"):
        if event_type not in section:
            errors.append(f"contract §13 missing reference to '{event_type}'")
    return errors


def check_deferred_annotations(contract_text: str) -> list[str]:
    """Verify that unimplemented sections are annotated as deferred in §16.

    §17 (Learning Retrieval) is now active — no deferred check needed.
    Retained as scaffolding for future deferred sections.
    """
    section = extract_section_text(contract_text, "## 16.")
    if section is None:
        return ["contract: §16 Conformance Checklist not found"]
    return []


GOVERNANCE_KEY_PHRASES: dict[int, str] = {
    1: "debug-gated",
    2: "fail-closed",
    3: "auto-escalation",
    4: "direct invocation",
    5: "threadId",
    6: "sanitizer_status",
    7: "re-consent",
}


def check_governance_rule_content(contract_text: str) -> list[str]:
    """Verify each governance rule contains its distinguishing key phrase."""
    section_match = re.search(
        r"## 15\. Governance.*?(?=\n## \d+\.|\Z)", contract_text, re.DOTALL
    )
    if not section_match:
        return ["§15 Governance Locks section not found"]

    section = section_match.group()
    errors: list[str] = []
    for rule_num, phrase in GOVERNANCE_KEY_PHRASES.items():
        if phrase not in section:
            errors.append(f"Governance rule {rule_num} missing key phrase {phrase!r}")
    return errors


def check_cross_contract_invariant_refs(
    contract_text: str, ci_contract_path: Path
) -> list[str]:
    """Verify CI-SEC-* references resolve in context-injection contract."""
    refs = set(re.findall(r"CI-SEC-\d+", contract_text))
    if not refs:
        return []  # no cross-references to check

    try:
        ci_text = ci_contract_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read context-injection contract: {exc}"]

    errors: list[str] = []
    for ref in sorted(refs):
        if ref not in ci_text:
            errors.append(
                f"{ref} referenced in consultation contract but not in context-injection contract"
            )
    return errors


def check_profile_validity(repo_root: Path) -> list[str]:
    """Validate consultation-profiles.yaml against §14 invariants."""
    profiles_path = (
        repo_root
        / "packages"
        / "plugins"
        / "cross-model"
        / "references"
        / "consultation-profiles.yaml"
    )
    try:
        import sys

        # sys.path mutation needed: this CI script lives in scripts/ and must
        # reach into the cross-model package's scripts/ for validate_profiles.
        # Guarded against duplicates; scoped to this process lifetime only.
        scripts_dir = (
            repo_root / "packages" / "plugins" / "cross-model" / "scripts"
        )
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from validate_profiles import validate_profiles_file  # type: ignore[import-not-found]

        return validate_profiles_file(profiles_path)
    except Exception as exc:
        return [f"profile validation failed: {exc}"]


def validate(repo_root: Path | None = None) -> list[str]:
    """Run all checks. Returns list of error strings — empty list means all pass."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    contract_path = (
        repo_root / "packages/plugins/cross-model/references/consultation-contract.md"
    )
    skill_path = repo_root / "packages/plugins/cross-model/skills/codex/SKILL.md"
    dialogue_skill_path = (
        repo_root / "packages/plugins/cross-model/skills/dialogue/SKILL.md"
    )
    agent_path = repo_root / "packages/plugins/cross-model/agents/codex-dialogue.md"
    codex_reviewer_path = (
        repo_root / "packages/plugins/cross-model/agents/codex-reviewer.md"
    )
    gatherer_code_path = (
        repo_root / "packages/plugins/cross-model/agents/context-gatherer-code.md"
    )
    gatherer_falsifier_path = (
        repo_root / "packages/plugins/cross-model/agents/context-gatherer-falsifier.md"
    )

    errors: list[str] = []

    contract_text: str | None = None
    skill_text: str | None = None
    agent_text: str | None = None
    dialogue_skill_text: str | None = None

    try:
        contract_text = read_file(contract_path)
    except OSError as e:
        errors.append(f"validate failed: cannot read contract. Got: {str(e)!r:.100}")

    try:
        skill_text = read_file(skill_path)
    except OSError as e:
        errors.append(f"validate failed: cannot read skill. Got: {str(e)!r:.100}")

    try:
        agent_text = read_file(agent_path)
        if "[RETIRED]" in agent_text:
            agent_text = None
    except OSError as e:
        errors.append(f"validate failed: cannot read agent. Got: {str(e)!r:.100}")

    try:
        dialogue_skill_text = read_file(dialogue_skill_path)
    except OSError as e:
        errors.append(
            f"validate failed: cannot read dialogue skill. Got: {str(e)!r:.100}"
        )

    if contract_text is not None:
        contract_sections = extract_contract_sections(contract_text)
        errors.extend(check_section_count(contract_sections))
        if skill_text is not None:
            errors.extend(
                check_stub_references("SKILL.md", skill_text, contract_sections)
            )
        if dialogue_skill_text is not None:
            errors.extend(
                check_stub_references(
                    "dialogue/SKILL.md", dialogue_skill_text, contract_sections
                )
            )
        if agent_text is not None:
            errors.extend(
                check_stub_references(
                    "codex-dialogue.md", agent_text, contract_sections
                )
            )
        errors.extend(check_event_types_in_contract(contract_text))
        errors.extend(check_deferred_annotations(contract_text))
        errors.extend(check_governance_rule_content(contract_text))
        ci_contract_path = (
            repo_root
            / "packages/plugins/cross-model/references/context-injection-contract.md"
        )
        errors.extend(check_cross_contract_invariant_refs(contract_text, ci_contract_path))

    if skill_text is not None and contract_text is not None:
        errors.extend(check_governance_rule_count(skill_text, contract_text))

    if agent_text is not None:
        errors.extend(
            check_agent_governance_count(agent_path, EXPECTED_AGENT_GOVERNANCE_COUNT)
        )
    errors.extend(
        check_agent_governance_count(
            codex_reviewer_path, EXPECTED_AGENT_GOVERNANCE_COUNT
        )
    )
    errors.extend(
        check_agent_governance_count(
            gatherer_code_path, EXPECTED_GATHERER_GOVERNANCE_COUNT
        )
    )
    errors.extend(
        check_agent_governance_count(
            gatherer_falsifier_path, EXPECTED_GATHERER_GOVERNANCE_COUNT
        )
    )
    errors.extend(check_profile_validity(repo_root))
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
