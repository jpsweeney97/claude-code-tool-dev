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
    / "validate_spec_writing_contract.py"
)
SPEC = importlib.util.spec_from_file_location(
    "validate_spec_writing_contract", MODULE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        f"test import failed: unable to load module spec. Got: {str(MODULE_PATH)!r}"
    )
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / ".claude/skills/spec-writer/SKILL.md"
CONTRACT_PATH = REPO_ROOT / "docs/references/shared-contract.md"

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
# SYNC marker checks
# ---------------------------------------------------------------------------


def test_all_sync_markers_present() -> None:
    """SKILL.md contains all 4 SYNC comment markers."""
    skill_text = SKILL_PATH.read_text()
    errors = MODULE.check_sync_markers(skill_text)
    assert errors == [], "expected no missing markers, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


def test_missing_sync_marker_is_caught() -> None:
    """A SKILL.md missing one SYNC marker is flagged."""
    skill_text = "# Spec Writer\n\nSome content without sync markers.\n"
    errors = MODULE.check_sync_markers(skill_text)
    assert len(errors) == 4  # all 4 missing
    assert all("SYNC" in e for e in errors)


def test_one_missing_sync_marker_is_caught() -> None:
    """A SKILL.md missing one specific SYNC marker reports exactly that marker."""
    # Include 3 of 4 markers, omit the derivation-table one
    skill_text = "\n".join(
        [
            "<!-- SYNC: docs/references/shared-contract.md#claims-enum -->",
            "<!-- SYNC: docs/references/shared-contract.md#spec-yaml-schema -->",
            "<!-- SYNC: docs/references/shared-contract.md#failure-model -->",
            "No derivation-table marker here.",
        ]
    )
    errors = MODULE.check_sync_markers(skill_text)
    assert len(errors) == 1
    assert "derivation-table" in errors[0]


# ---------------------------------------------------------------------------
# Claims Enum checks
# ---------------------------------------------------------------------------


def test_claims_enum_matches_contract() -> None:
    """Claims Enum in SKILL.md matches shared-contract.md exactly."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_claims_enum(skill_text, contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


def test_claims_enum_has_8_entries() -> None:
    """Claims Enum section in SKILL.md has exactly 8 data rows."""
    skill_text = SKILL_PATH.read_text()
    section = MODULE.extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#claims-enum"
    )
    rows = MODULE.extract_table_rows(section)
    # First row is header, rest are data
    data_rows = rows[1:] if len(rows) > 1 else rows
    assert len(data_rows) == 8, f"expected 8 claim rows, got {len(data_rows)}"


def test_modified_claim_in_skill_is_caught() -> None:
    """A modified claim row in SKILL.md (drift) is detected."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Corrupt one claim row in SKILL.md
    drifted_skill = skill_text.replace(
        "| `architecture_rule` | Architectural constraints, cross-cutting invariants | — |",
        "| `architecture_rule` | DRIFTED CONTENT | — |",
    )
    errors = MODULE.check_claims_enum(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("SKILL.md" in e and "not in shared-contract" in e for e in errors)


def test_extra_claim_in_skill_is_caught() -> None:
    """A claim present in SKILL.md but not in shared-contract is flagged."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Insert a fake claim row after the SYNC marker section
    extra_row = "| `fake_claim` | Fake content | — |"
    drifted_skill = skill_text.replace(
        "| `verification_strategy` | Test design, coverage plans, regression strategy | — |",
        "| `verification_strategy` | Test design, coverage plans, regression strategy | — |\n"
        + extra_row,
    )
    errors = MODULE.check_claims_enum(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("not in shared-contract" in e for e in errors)


def test_missing_claim_in_skill_is_caught() -> None:
    """A claim in shared-contract but missing from SKILL.md is flagged."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Remove one claim row from SKILL.md
    drifted_skill = skill_text.replace(
        "| `persistence_schema` | Data model, storage constraints, state representation | schema-persistence |",
        "",
    )
    errors = MODULE.check_claims_enum(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("not in SKILL.md" in e for e in errors)


# ---------------------------------------------------------------------------
# Derivation Table checks
# ---------------------------------------------------------------------------


def test_derivation_table_matches_contract() -> None:
    """Derivation Table in SKILL.md matches shared-contract.md exactly."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_derivation_table(skill_text, contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


def test_derivation_table_has_6_roles() -> None:
    """Derivation Table section in SKILL.md has exactly 6 data rows."""
    skill_text = SKILL_PATH.read_text()
    section = MODULE.extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#derivation-table"
    )
    rows = MODULE.extract_table_rows(section)
    data_rows = rows[1:] if len(rows) > 1 else rows
    assert len(data_rows) == 6, f"expected 6 derivation rows, got {len(data_rows)}"


def test_modified_role_in_skill_is_caught() -> None:
    """A modified derivation role row in SKILL.md is detected."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Corrupt one role row
    drifted_skill = skill_text.replace(
        "| `foundation` | `architecture_rule`, `decision_record` | Yes |",
        "| `foundation` | `architecture_rule` | Yes |",
    )
    errors = MODULE.check_derivation_table(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("not in shared-contract" in e for e in errors)


# ---------------------------------------------------------------------------
# spec.yaml Schema checks
# ---------------------------------------------------------------------------


def test_spec_yaml_schema_matches_contract() -> None:
    """spec.yaml Schema block in SKILL.md matches shared-contract.md exactly."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_spec_yaml_schema(skill_text, contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


def test_spec_yaml_schema_drift_is_caught() -> None:
    """A line change in the spec.yaml Schema block is detected."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Corrupt the schema block by changing a field name
    drifted_skill = skill_text.replace(
        "shared_contract_version: 1",
        "shared_contract_version: 2",
        # Only replace in the SKILL.md schema block (the contract version stays as-is)
    )
    errors = MODULE.check_spec_yaml_schema(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("mismatch" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Failure Model checks
# ---------------------------------------------------------------------------


def test_failure_model_matches_contract() -> None:
    """Failure Model table in SKILL.md matches shared-contract.md producer failures."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()
    errors = MODULE.check_failure_model(skill_text, contract_text)
    assert errors == [], "expected no errors, got:\n" + "\n".join(
        f"  - {e}" for e in errors
    )


def test_missing_failure_row_in_skill_is_caught() -> None:
    """A failure model row present in shared-contract but missing from SKILL.md is flagged."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Remove one specific failure row
    drifted_skill = skill_text.replace(
        "| Cross-references don't resolve | Hard failure |",
        "",
    )
    errors = MODULE.check_failure_model(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("not in SKILL.md" in e for e in errors)


def test_extra_failure_row_in_skill_is_caught() -> None:
    """A failure model row in SKILL.md not present in shared-contract is flagged."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Add an invented failure row
    drifted_skill = skill_text.replace(
        "| `spec.yaml` top-level key has wrong type (e.g., `boundary_rules: {}` instead of list, `authorities: []` instead of mapping) | Hard failure |",
        "| `spec.yaml` top-level key has wrong type (e.g., `boundary_rules: {}` instead of list, `authorities: []` instead of mapping) | Hard failure |\n"
        "| Invented new failure condition | Hard failure |",
    )
    errors = MODULE.check_failure_model(drifted_skill, contract_text)
    assert len(errors) >= 1
    assert any("not in shared-contract" in e for e in errors)


# ---------------------------------------------------------------------------
# Edge semantics
# ---------------------------------------------------------------------------


def test_claim_ordering_is_insignificant() -> None:
    """Reordering claim rows in SKILL.md does not produce errors (set comparison)."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Swap two claim rows in the SKILL.md text
    drifted_skill = skill_text.replace(
        "| `architecture_rule` | Architectural constraints, cross-cutting invariants | — |\n"
        "| `decision_record` | Locked design decisions, accepted tradeoffs | — |",
        "| `decision_record` | Locked design decisions, accepted tradeoffs | — |\n"
        "| `architecture_rule` | Architectural constraints, cross-cutting invariants | — |",
    )
    errors = MODULE.check_claims_enum(drifted_skill, contract_text)
    assert errors == [], (
        "reordering rows should not produce errors (set comparison):\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_role_ordering_is_insignificant() -> None:
    """Reordering derivation role rows does not produce errors (set comparison)."""
    skill_text = SKILL_PATH.read_text()
    contract_text = CONTRACT_PATH.read_text()

    # Swap two role rows
    drifted_skill = skill_text.replace(
        "| `foundation` | `architecture_rule`, `decision_record` | Yes |\n"
        "| `behavior` | `behavior_contract`, `interface_contract` | Yes |",
        "| `behavior` | `behavior_contract`, `interface_contract` | Yes |\n"
        "| `foundation` | `architecture_rule`, `decision_record` | Yes |",
    )
    errors = MODULE.check_derivation_table(drifted_skill, contract_text)
    assert errors == [], (
        "reordering rows should not produce errors:\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


# ---------------------------------------------------------------------------
# extract_table_rows edge semantics
# ---------------------------------------------------------------------------


def test_extract_table_rows_ignores_separator_rows() -> None:
    """extract_table_rows skips separator rows (|---|---|)."""
    text = (
        "| Header 1 | Header 2 |\n"
        "|----------|----------|\n"
        "| data1    | data2    |\n"
    )
    rows = MODULE.extract_table_rows(text)
    assert len(rows) == 2
    assert all("---" not in row for row in rows)


def test_extract_table_rows_handles_empty_input() -> None:
    """extract_table_rows returns empty list for text with no table rows."""
    rows = MODULE.extract_table_rows("No table here.\n\nJust prose.")
    assert rows == []


def test_extract_fenced_block_returns_none_for_missing_block() -> None:
    """extract_fenced_block returns None when no fenced block exists."""
    result = MODULE.extract_fenced_block("Just some prose without code blocks.")
    assert result is None


def test_extract_fenced_block_extracts_content() -> None:
    """extract_fenced_block extracts content between ``` fences."""
    text = "Some prose.\n\n```yaml\nkey: value\nother: thing\n```\n\nMore prose."
    result = MODULE.extract_fenced_block(text)
    assert result is not None
    assert "key: value" in result
    assert "other: thing" in result
    assert "```" not in result


# ---------------------------------------------------------------------------
# read_file error handling
# ---------------------------------------------------------------------------


def test_read_file_raises_oserror_for_missing_file(tmp_path: Path) -> None:
    """read_file raises OSError with descriptive message for non-existent file."""
    missing = tmp_path / "nonexistent.md"
    with pytest.raises(OSError, match="cannot read"):
        MODULE.read_file(missing)


def test_read_file_preserves_cause_for_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read_file re-raises as OSError with __cause__ preserved."""
    target = tmp_path / "unreadable.md"
    target.write_text("content")

    original_read_text = Path.read_text

    def patched(self: Path, **kwargs: str | None) -> str:
        if self == target:
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched)

    with pytest.raises(OSError, match="cannot read") as exc_info:
        MODULE.read_file(target)
    assert isinstance(exc_info.value.__cause__, PermissionError)


# ---------------------------------------------------------------------------
# validate() error accumulation
# ---------------------------------------------------------------------------


def test_validate_accumulates_errors_for_missing_files() -> None:
    """validate() accumulates errors when both input files are missing."""
    fake_root = Path("/nonexistent/repo/root")
    errors = MODULE.validate(repo_root=fake_root)
    # Both SKILL.md and shared-contract.md fail to read → 2 errors
    assert len(errors) >= 2
    error_text = "\n".join(errors)
    assert "SKILL.md" in error_text
    assert "shared-contract.md" in error_text


def test_validate_missing_skill_only_reports_skill_error(tmp_path: Path) -> None:
    """validate() reports SKILL.md read error when only SKILL.md is missing."""
    # Copy real contract into tmp_path
    real_contract = CONTRACT_PATH.read_text()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "references").mkdir()
    (tmp_path / "docs" / "references" / "shared-contract.md").write_text(real_contract)

    # No .claude/skills/spec-writer/SKILL.md in tmp_path
    errors = MODULE.validate(repo_root=tmp_path)
    assert any("SKILL.md" in e for e in errors)
    # Contract was readable, so no contract error
    assert not any("shared-contract.md" in e for e in errors)
