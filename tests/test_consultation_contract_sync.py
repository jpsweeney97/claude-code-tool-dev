from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_consultation_contract.py"
)
SPEC = importlib.util.spec_from_file_location(
    "validate_consultation_contract", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        f"test import failed: unable to load module spec. Got: {str(MODULE_PATH)!r}"
    )
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT / "packages/plugins/cross-model/references/consultation-contract.md"
)

# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_validate_passes_on_current_codebase() -> None:
    """validate() returns no errors against the actual codebase."""
    errors = MODULE.validate(repo_root=REPO_ROOT)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


# ---------------------------------------------------------------------------
# Stub reference checks
# ---------------------------------------------------------------------------


def test_broken_stub_reference_is_caught() -> None:
    """A stub referencing a non-existent §99 is flagged."""
    contract_sections = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16}
    skill_text_with_bad_ref = "See consultation-contract.md § Fake Section (§99)."
    errors = MODULE.check_stub_references(
        "SKILL.md", skill_text_with_bad_ref, contract_sections
    )
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
    sections_missing_6 = set(range(1, 18)) - {6}
    errors = MODULE.check_section_count(sections_missing_6)
    assert len(errors) == 1
    assert "6" in errors[0]
    assert "missing" in errors[0]


def test_extra_contract_section_is_caught() -> None:
    """check_section_count flags when an unexpected section number is present."""
    sections_with_extra = set(range(1, 18)) | {18}
    errors = MODULE.check_section_count(sections_with_extra)
    assert len(errors) == 1
    assert "18" in errors[0]
    assert "unexpected" in errors[0]


def test_complete_17_sections_pass() -> None:
    """check_section_count passes when all 17 sections are present."""
    all_sections = set(range(1, 18))
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
    errors = MODULE.check_governance_rule_count(
        skill_with_6_rules, contract_with_7_rules
    )
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
    required_values = [
        "fail_unresolved_match",
        "pass_redacted",
        "pass_clean",
        "fail_not_run",
    ]
    for value in required_values:
        assert value in sanitizer_row, (
            f"sanitizer_status value '{value}' not found in §7 definition. "
            f"Got: {sanitizer_row!r:.200}"
        )


def test_extract_contract_sections_returns_correct_numbers() -> None:
    """extract_contract_sections correctly parses ## N. headers."""
    text = (
        "## 1. Purpose\n\nsome text\n\n## 7. Safety\n\nmore text\n\n## 16. Checklist\n"
    )
    sections = MODULE.extract_contract_sections(text)
    assert sections == {1, 7, 16}


def test_extract_stub_refs_returns_correct_numbers() -> None:
    """extract_stub_refs correctly parses (§N) patterns."""
    text = "See §5 (§5), §7 (§7), and §11 (§11). Also (§9) here."
    refs = MODULE.extract_stub_refs(text)
    assert refs == {5, 7, 9, 11}


# ---------------------------------------------------------------------------
# Agent governance checks
# ---------------------------------------------------------------------------

AGENTS_DIR = REPO_ROOT / "packages/plugins/cross-model/agents"


def _count_governance_rules(agent_path: Path) -> int:
    """Read an agent file and count governance rules matching the pattern."""
    import re

    pattern = re.compile(r"^\d+\. \*\*", re.MULTILINE)
    text = agent_path.read_text()
    start = text.find("## Governance")
    assert start != -1, f"{agent_path.name}: Governance section not found"
    next_section = text.find("\n## ", start + len("## Governance"))
    section = text[start:next_section] if next_section != -1 else text[start:]
    return len(pattern.findall(section))


def test_codex_dialogue_has_governance_section() -> None:
    """codex-dialogue.md must have a Governance section with 7 rules."""
    count = _count_governance_rules(AGENTS_DIR / "codex-dialogue.md")
    assert count == 7, f"expected 7 governance rules, got {count}"


def test_codex_reviewer_has_governance_section() -> None:
    """codex-reviewer.md must have a Governance section with 7 rules."""
    count = _count_governance_rules(AGENTS_DIR / "codex-reviewer.md")
    assert count == 7, f"expected 7 governance rules, got {count}"


def test_context_gatherer_code_has_governance_section() -> None:
    """context-gatherer-code.md must have a Governance section with 3 rules."""
    count = _count_governance_rules(AGENTS_DIR / "context-gatherer-code.md")
    assert count == 3, f"expected 3 governance rules, got {count}"


def test_context_gatherer_falsifier_has_governance_section() -> None:
    """context-gatherer-falsifier.md must have a Governance section with 3 rules."""
    count = _count_governance_rules(AGENTS_DIR / "context-gatherer-falsifier.md")
    assert count == 3, f"expected 3 governance rules, got {count}"


# ---------------------------------------------------------------------------
# §13 event type checks
# ---------------------------------------------------------------------------

DIALOGUE_SKILL_PATH = (
    REPO_ROOT / "packages/plugins/cross-model/skills/dialogue/SKILL.md"
)


def test_event_types_match_contract() -> None:
    """§13 must reference actual event types from emit_analytics.py."""
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_event_types_in_contract(contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


# ---------------------------------------------------------------------------
# §16 deferred annotation checks
# ---------------------------------------------------------------------------


def test_deferred_sections_annotated() -> None:
    """§16 must annotate unimplemented sections as deferred."""
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_deferred_annotations(contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


# ---------------------------------------------------------------------------
# dialogue/SKILL.md stub reference checks
# ---------------------------------------------------------------------------


def test_missing_event_type_is_caught() -> None:
    """§13 missing 'dialogue_outcome' is flagged."""
    contract_text = "\n".join(
        [
            "## 13. Event Contract",
            "",
            "Events emitted: `consultation_outcome`.",
            "",
            "## 14. Next Section",
        ]
    )
    errors = MODULE.check_event_types_in_contract(contract_text)
    assert len(errors) >= 1
    assert any("dialogue_outcome" in e for e in errors)



def test_agent_governance_count_mismatch_is_caught(tmp_path: Path) -> None:
    """Agent file with 2 governance rules flagged when 7 expected."""
    agent_file = tmp_path / "fake-agent.md"
    agent_file.write_text(
        "\n".join(
            [
                "# Fake Agent",
                "",
                "## Governance",
                "",
                "1. **Rule one:** text",
                "2. **Rule two:** text",
                "",
                "## Next Section",
            ]
        )
    )
    errors = MODULE.check_agent_governance_count(agent_file, 7)
    assert len(errors) == 1
    assert "2" in errors[0]
    assert "7" in errors[0]


def test_dialogue_skill_stub_refs_resolve() -> None:
    """dialogue/SKILL.md stub references must resolve to contract sections."""
    contract_text = CONTRACT_PATH.read_text()
    dialogue_skill_text = DIALOGUE_SKILL_PATH.read_text()
    contract_sections = MODULE.extract_contract_sections(contract_text)
    errors = MODULE.check_stub_references(
        "dialogue/SKILL.md", dialogue_skill_text, contract_sections
    )
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


# ---------------------------------------------------------------------------
# OSError handling (S4)
# ---------------------------------------------------------------------------


def test_read_file_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read_file catches PermissionError (via OSError widening), not just FileNotFoundError."""
    target = tmp_path / "unreadable.md"
    target.write_text("content")

    # Monkeypatch Path.read_text to raise PermissionError
    original_read_text = Path.read_text

    def patched_read_text(self: Path, **kwargs: str | None) -> str:
        if self == target:
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    # Before S4 fix: this raises uncaught PermissionError
    # After S4 fix: this returns a descriptive error string
    errors = MODULE.check_agent_governance_count(target, 7)
    assert len(errors) == 1
    assert "PermissionError" in errors[0]


def test_read_file_preserves_oserror_on_permission_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read_file re-raises as OSError with descriptive message, preserving original via __cause__."""
    target = tmp_path / "unreadable.md"
    target.write_text("content")

    original_read_text = Path.read_text

    def patched_read_text(self: Path, **kwargs: str | None) -> str:
        if self == target:
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    with pytest.raises(OSError, match="cannot read") as exc_info:
        MODULE.read_file(target)
    assert "PermissionError" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, PermissionError)


# ---------------------------------------------------------------------------
# Scope-breach conformance (I7)
# ---------------------------------------------------------------------------


def test_termination_reasons_match_contract() -> None:
    """§13's Valid termination reasons must match event_schema.VALID_TERMINATION_REASONS."""
    import re as re_mod
    import importlib.util as ilu

    # Import from event_schema (leaf module, no sibling imports — importlib-safe)
    schema_path = REPO_ROOT / "packages/plugins/cross-model/scripts/event_schema.py"
    spec = ilu.spec_from_file_location("event_schema", schema_path)
    assert spec is not None and spec.loader is not None
    schema_mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(schema_mod)
    code_reasons = schema_mod.VALID_TERMINATION_REASONS

    # Parse §13's "### Valid termination reasons" subsection
    contract_text = CONTRACT_PATH.read_text()
    section_13 = MODULE.extract_section_text(contract_text, "## 13.")
    assert section_13 is not None, "§13 not found in contract"

    # Find the subsection body after "### Valid termination reasons"
    sub_start = section_13.find("### Valid termination reasons")
    assert sub_start != -1, "§13 missing '### Valid termination reasons' subsection"

    # Extract text until next ### or end
    sub_text = section_13[sub_start:]
    next_sub = sub_text.find("\n### ", len("### Valid termination reasons"))
    if next_sub != -1:
        sub_text = sub_text[:next_sub]

    # Extract backtick-delimited values
    contract_reasons = set(re_mod.findall(r"`([^`]+)`", sub_text))

    assert contract_reasons == code_reasons, (
        f"termination reason mismatch: contract has {sorted(contract_reasons)}, "
        f"code has {sorted(code_reasons)}"
    )


def test_scope_breach_referenced_in_section_6() -> None:
    """§6 must reference termination_reason: scope_breach for scope enforcement."""
    contract_text = CONTRACT_PATH.read_text()
    section_6 = MODULE.extract_section_text(contract_text, "## 6.")
    assert section_6 is not None, "§6 not found in contract"
    assert "scope_breach" in section_6, (
        "§6 must reference 'scope_breach' as a termination reason"
    )


# ---------------------------------------------------------------------------
# Test coverage gaps (round 2)
# ---------------------------------------------------------------------------


def test_agent_governance_missing_file(tmp_path: Path) -> None:
    """check_agent_governance_count returns error for non-existent agent file."""
    missing_path = tmp_path / "nonexistent-agent.md"
    errors = MODULE.check_agent_governance_count(missing_path, 7)
    assert len(errors) == 1
    assert "cannot read" in errors[0] or "check_agent_governance failed" in errors[0]


def test_event_types_missing_section() -> None:
    """check_event_types_in_contract returns error when §13 is absent."""
    contract_without_13 = "\n".join(
        [
            "## 12. Previous Section",
            "",
            "Some content.",
            "",
            "## 14. Next Section",
            "",
            "More content.",
        ]
    )
    errors = MODULE.check_event_types_in_contract(contract_without_13)
    assert len(errors) == 1
    assert "§13" in errors[0]
    assert "not found" in errors[0]


def test_multiple_simultaneous_errors() -> None:
    """validate() accumulates errors from multiple failing checks."""
    # Use a repo root that doesn't exist — all file reads will fail
    fake_root = Path("/nonexistent/repo/root")
    errors = MODULE.validate(repo_root=fake_root)
    # 4 file-read errors + 3 unconditional agent governance checks = 7 minimum
    assert len(errors) >= 7, (
        f"expected at least 7 accumulated errors from missing files, got {len(errors)}:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
    # Verify errors are accumulated, not just the first one
    error_text = "\n".join(errors)
    assert "contract" in error_text.lower()
    assert "skill" in error_text.lower()


def test_validate_catches_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """validate() catches PermissionError (OSError subclass) during file reads."""
    original_read_file = MODULE.read_file

    def patched_read_file(path: Path) -> str:
        if "consultation-contract" in path.name:
            raise PermissionError(f"Permission denied: {path}")
        return original_read_file(path)

    monkeypatch.setattr(MODULE, "read_file", patched_read_file)
    errors = MODULE.validate(repo_root=tmp_path)
    permission_errors = [
        e for e in errors if "PermissionError" in e or "Permission denied" in e
    ]
    assert len(permission_errors) >= 1, (
        "expected PermissionError in accumulated errors, got:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )
