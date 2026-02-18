from __future__ import annotations

import importlib.util
from pathlib import Path

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_consultation_contract.py"
)
SPEC = importlib.util.spec_from_file_location("validate_consultation_contract", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        f"test import failed: unable to load module spec. Got: {str(MODULE_PATH)!r}"
    )
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "packages/plugins/cross-model/references/consultation-contract.md"

# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_validate_passes_on_current_codebase() -> None:
    """validate() returns no errors against the actual codebase."""
    errors = MODULE.validate(repo_root=REPO_ROOT)
    assert errors == [], f"expected no errors, got:\n" + "\n".join(f"  - {e}" for e in errors)


# ---------------------------------------------------------------------------
# Stub reference checks
# ---------------------------------------------------------------------------


def test_broken_stub_reference_is_caught() -> None:
    """A stub referencing a non-existent §99 is flagged."""
    contract_sections = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
    skill_text_with_bad_ref = "See consultation-contract.md § Fake Section (§99)."
    errors = MODULE.check_stub_references("SKILL.md", skill_text_with_bad_ref, contract_sections)
    assert len(errors) == 1
    assert "§[99]" in errors[0]
    assert "SKILL.md" in errors[0]


def test_valid_stub_references_pass() -> None:
    """Text with only resolvable §N references produces no errors."""
    contract_sections = {5, 7, 9, 10, 11}
    skill_text = "See §5 (§5), §7 (§7), and §11 (§11) in the contract."
    errors = MODULE.check_stub_references("SKILL.md", skill_text, contract_sections)
    assert errors == []


def test_multiple_broken_refs_caught_together() -> None:
    """Multiple unresolved stub references are all reported in a single error."""
    contract_sections = {5, 7}
    text = "see (§99) and (§42) for details"
    errors = MODULE.check_stub_references("SKILL.md", text, contract_sections)
    assert len(errors) == 1
    assert "42" in errors[0]
    assert "99" in errors[0]


# ---------------------------------------------------------------------------
# Section count checks
# ---------------------------------------------------------------------------


def test_missing_contract_section_is_caught() -> None:
    """check_section_count flags when a section number is absent."""
    # Contract has §1-§16; simulate §6 missing
    sections_missing_6 = set(range(1, 17)) - {6}
    errors = MODULE.check_section_count(sections_missing_6)
    assert len(errors) == 1
    assert "6" in errors[0]
    assert "missing" in errors[0]


def test_extra_contract_section_is_caught() -> None:
    """check_section_count flags when an unexpected section number is present."""
    sections_with_extra = set(range(1, 17)) | {17}
    errors = MODULE.check_section_count(sections_with_extra)
    assert len(errors) == 1
    assert "17" in errors[0]
    assert "unexpected" in errors[0]


def test_complete_16_sections_pass() -> None:
    """check_section_count passes when all 16 sections are present."""
    all_sections = set(range(1, 17))
    errors = MODULE.check_section_count(all_sections)
    assert errors == []


# ---------------------------------------------------------------------------
# Governance rule count checks
# ---------------------------------------------------------------------------


def test_governance_rule_count_mismatch_is_caught() -> None:
    """Mismatch between SKILL.md and contract governance rule counts is flagged."""
    # Contract has 7 rules; SKILL.md has only 6
    skill_with_6_rules = "\n".join(
        [
            "## Governance",
            "",
            "1. **Rule one:** text",
            "2. **Rule two:** text",
            "3. **Rule three:** text",
            "4. **Rule four:** text",
            "5. **Rule five:** text",
            "6. **Rule six:** text",
        ]
    )
    contract_with_7_rules = "\n".join(
        [
            "## 15. Governance Locks",
            "",
            "1. **Rule one:** text",
            "2. **Rule two:** text",
            "3. **Rule three:** text",
            "4. **Rule four:** text",
            "5. **Rule five:** text",
            "6. **Rule six:** text",
            "7. **Rule seven:** text",
        ]
    )
    errors = MODULE.check_governance_rule_count(skill_with_6_rules, contract_with_7_rules)
    assert len(errors) == 1
    assert "6" in errors[0]
    assert "7" in errors[0]
    assert "mismatch" in errors[0]


def test_governance_rule_count_matches_passes() -> None:
    """Equal governance rule counts produce no errors."""
    rules_7 = "\n".join(f"{i}. **Rule {i}:** text" for i in range(1, 8))
    skill_text = f"## Governance\n\n{rules_7}\n\n## Next Section\n"
    contract_text = f"## 15. Governance Locks\n\n{rules_7}\n\n## 16. Next\n"
    errors = MODULE.check_governance_rule_count(skill_text, contract_text)
    assert errors == []


def test_governance_section_missing_in_skill_is_caught() -> None:
    """Missing Governance section in SKILL.md is flagged."""
    skill_without_governance = "## Troubleshooting\n\nsome content\n"
    contract_text = "## 15. Governance Locks\n\n1. **Rule one:** text\n"
    errors = MODULE.check_governance_rule_count(skill_without_governance, contract_text)
    assert len(errors) == 1
    assert "Governance section not found" in errors[0]


# ---------------------------------------------------------------------------
# Direct contract sync: sanitizer_status values
# ---------------------------------------------------------------------------


def test_sanitizer_status_values_defined_in_contract() -> None:
    """§7 in the contract defines the sanitizer_status values referenced in SKILL.md.

    SKILL.md references fail_unresolved_match (failure table) and pass_redacted
    (governance rule 6). Both must appear in §7's sanitizer_status field definition.
    """
    contract_text = CONTRACT_PATH.read_text()

    # Extract the §7 Safety Pipeline section
    section_7 = MODULE.extract_section_text(contract_text, "## 7. Safety Pipeline")
    assert section_7 is not None, "§7 Safety Pipeline section not found in contract"

    # Find the sanitizer_status row in the pre-dispatch record table
    sanitizer_row = next(
        (line for line in section_7.splitlines() if "sanitizer_status" in line),
        None,
    )
    assert sanitizer_row is not None, "sanitizer_status row not found in §7"

    # Values that SKILL.md references — both must appear in the contract definition
    required_values = ["fail_unresolved_match", "pass_redacted", "pass_clean", "fail_not_run"]
    for value in required_values:
        assert value in sanitizer_row, (
            f"sanitizer_status value '{value}' not found in §7 definition. "
            f"Got: {sanitizer_row!r:.200}"
        )


def test_extract_contract_sections_returns_correct_numbers() -> None:
    """extract_contract_sections correctly parses ## N. headers."""
    text = "## 1. Purpose\n\nsome text\n\n## 7. Safety\n\nmore text\n\n## 16. Checklist\n"
    sections = MODULE.extract_contract_sections(text)
    assert sections == {1, 7, 16}


def test_extract_stub_refs_returns_correct_numbers() -> None:
    """extract_stub_refs correctly parses (§N) patterns."""
    text = "See §5 (§5), §7 (§7), and §11 (§11). Also (§9) here."
    refs = MODULE.extract_stub_refs(text)
    assert refs == {5, 7, 9, 11}
