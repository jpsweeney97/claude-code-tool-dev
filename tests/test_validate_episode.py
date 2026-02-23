from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import (same pattern as test_consultation_contract_sync.py)
# ---------------------------------------------------------------------------

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_episode.py"
)
SPEC = importlib.util.spec_from_file_location("validate_episode", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(
        f"test import failed: unable to load module spec. Got: {str(MODULE_PATH)!r}"
    )
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

VALID_SOLO_EPISODE = """\
---
id: EP-0001
date: 2026-02-23
title: Test episode for validation
source_type: solo
domain: testing
task_type: debugging
languages: [python]
frameworks: []
keywords: [validation, testing]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
A test episode to verify validator behavior.

## Resolution
Decided to use the approach described above.

## Evidence
Test results confirmed the behavior.
"""

VALID_DIALOGUE_EPISODE = """\
---
id: EP-0002
date: 2026-02-23
title: Dialogue episode for validation
source_type: dialogue
domain: architecture
task_type: design
languages: [python, typescript]
frameworks: []
keywords: [cross-model, architecture]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
A dialogue episode to verify conditional sections.

## Claude Position
Claude argued for approach A because of X.

## Codex Position
Codex argued for approach B because of Y.

## Resolution
Approach A was chosen with modifications from B.

## Evidence
Both approaches were tested; A performed better on metric Z.
"""


def _write_episode(tmp_path: Path, content: str, name: str = "EP-0001.md") -> Path:
    """Write episode content to a temp file and return the path."""
    path = tmp_path / name
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Happy path (Verification cases 9, 29, 32)
# ---------------------------------------------------------------------------


def test_valid_solo_episode_passes(tmp_path: Path) -> None:
    """A well-formed solo episode produces no validation errors."""
    path = _write_episode(tmp_path, VALID_SOLO_EPISODE)
    errors = MODULE.validate(path)
    assert errors == [], f"expected no errors, got: {errors}"


def test_valid_dialogue_episode_passes(tmp_path: Path) -> None:
    """A well-formed dialogue episode produces no validation errors."""
    path = _write_episode(tmp_path, VALID_DIALOGUE_EPISODE)
    errors = MODULE.validate(path)
    assert errors == [], f"expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# Check 1: Required fields (Verification case 9)
# ---------------------------------------------------------------------------


def test_missing_required_field(tmp_path: Path) -> None:
    """Missing a required field produces a validation error."""
    content = VALID_SOLO_EPISODE.replace("domain: testing\n", "")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("missing required fields" in e and "domain" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 2: Enum validation (Verification cases 10, 11)
# ---------------------------------------------------------------------------


def test_invalid_task_type(tmp_path: Path) -> None:
    """Invalid task_type value is rejected."""
    content = VALID_SOLO_EPISODE.replace("task_type: debugging", "task_type: hacking")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid task_type" in e for e in errors)


def test_invalid_decision(tmp_path: Path) -> None:
    """Invalid decision value is rejected."""
    content = VALID_SOLO_EPISODE.replace("decision: applied", "decision: maybe")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid decision" in e for e in errors)


def test_invalid_source_type(tmp_path: Path) -> None:
    """Invalid source_type value is rejected."""
    content = VALID_SOLO_EPISODE.replace("source_type: solo", "source_type: group")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid source_type" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 3: Boolean type (Verification case 12)
# ---------------------------------------------------------------------------


def test_safety_string_not_boolean(tmp_path: Path) -> None:
    """safety as quoted string 'false' is rejected (must be boolean)."""
    content = VALID_SOLO_EPISODE.replace('safety: false', 'safety: "false"')
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("safety must be boolean" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 4: ID format (Verification case 30)
# ---------------------------------------------------------------------------


def test_id_missing_zero_padding(tmp_path: Path) -> None:
    """ID without zero-padding (EP-1) is rejected."""
    content = VALID_SOLO_EPISODE.replace("id: EP-0001", "id: EP-1")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid id format" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 5: Date format (Verification case 31)
# ---------------------------------------------------------------------------


def test_date_wrong_format(tmp_path: Path) -> None:
    """Date in MM-DD-YYYY format is rejected."""
    content = VALID_SOLO_EPISODE.replace("date: 2026-02-23", "date: 02-23-2026")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid date format" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 6: schema_version (Verification cases 28, 29)
# ---------------------------------------------------------------------------


def test_schema_version_2_rejected(tmp_path: Path) -> None:
    """schema_version: 2 is rejected in Phase 1a."""
    content = VALID_SOLO_EPISODE.replace("schema_version: 1", "schema_version: 2")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid schema_version" in e for e in errors)


def test_schema_version_1_passes(tmp_path: Path) -> None:
    """schema_version: 1 passes (positive path — ensures not always-reject)."""
    path = _write_episode(tmp_path, VALID_SOLO_EPISODE)
    errors = MODULE.validate(path)
    assert not any("schema_version" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 7: Unknown keys (Verification cases 14, 32)
# ---------------------------------------------------------------------------


def test_unknown_key_rejected(tmp_path: Path) -> None:
    """Unknown frontmatter key without x_ prefix is rejected."""
    content = VALID_SOLO_EPISODE.replace(
        "schema_version: 1",
        "schema_version: 1\ncustom_field: value",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("unknown fields" in e and "custom_field" in e for e in errors)


def test_extension_key_accepted(tmp_path: Path) -> None:
    """x_* extension namespace keys pass validation."""
    content = VALID_SOLO_EPISODE.replace(
        "schema_version: 1",
        "schema_version: 1\nx_custom: value",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert not any("unknown fields" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 8: Keyword count
# ---------------------------------------------------------------------------


def test_keywords_empty_rejected(tmp_path: Path) -> None:
    """Empty keywords list is rejected (minimum 1)."""
    content = VALID_SOLO_EPISODE.replace(
        "keywords: [validation, testing]", "keywords: []"
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("keywords must have 1-5" in e for e in errors)


def test_keywords_six_rejected(tmp_path: Path) -> None:
    """Keywords list with 6 entries is rejected (maximum 5)."""
    content = VALID_SOLO_EPISODE.replace(
        "keywords: [validation, testing]",
        "keywords: [a, b, c, d, e, f]",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("keywords must have 1-5" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 9: Conditional body sections (Verification cases 6, 7, 15, 21, 33)
# ---------------------------------------------------------------------------


def test_dialogue_missing_claude_position(tmp_path: Path) -> None:
    """Dialogue episode missing Claude Position is rejected."""
    content = VALID_DIALOGUE_EPISODE.replace(
        "## Claude Position\nClaude argued for approach A because of X.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Claude Position" in e for e in errors)


def test_dialogue_missing_codex_position(tmp_path: Path) -> None:
    """Dialogue episode missing Codex Position is rejected."""
    content = VALID_DIALOGUE_EPISODE.replace(
        "## Codex Position\nCodex argued for approach B because of Y.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Codex Position" in e for e in errors)


def test_solo_with_claude_position_rejected(tmp_path: Path) -> None:
    """Solo episode with Claude Position section is rejected."""
    content = VALID_SOLO_EPISODE.replace(
        "## Resolution",
        "## Claude Position\nShouldn't be here.\n\n## Resolution",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("solo" in e.lower() and "Claude Position" in e for e in errors)


def test_solo_with_quoted_header_in_evidence(tmp_path: Path) -> None:
    """Solo episode quoting '## Claude Position' in Evidence text passes.

    Line-start anchored header matching prevents false positives from
    body text that quotes section headers.
    """
    content = VALID_SOLO_EPISODE.replace(
        "Test results confirmed the behavior.",
        'Test results confirmed the behavior.\nThe `## Claude Position` header was discussed.',
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    # The backtick-quoted header should NOT be parsed as a section
    assert not any("Claude Position" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 10: Body presence — Summary and Evidence (Verification case 13)
# ---------------------------------------------------------------------------


def test_missing_summary_section(tmp_path: Path) -> None:
    """Episode missing Summary section is rejected."""
    content = VALID_SOLO_EPISODE.replace(
        "## Summary\nA test episode to verify validator behavior.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Summary" in e for e in errors)


def test_missing_evidence_section(tmp_path: Path) -> None:
    """Episode missing Evidence section is rejected."""
    content = VALID_SOLO_EPISODE.replace(
        "## Evidence\nTest results confirmed the behavior.\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Evidence" in e for e in errors)


# ---------------------------------------------------------------------------
# Check 11: Resolution conditionality (Verification cases 22-25, 35-36)
# ---------------------------------------------------------------------------


def test_applied_without_resolution_rejected(tmp_path: Path) -> None:
    """decision: applied without Resolution section is rejected."""
    content = VALID_SOLO_EPISODE.replace(
        "## Resolution\nDecided to use the approach described above.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Resolution" in e for e in errors)


def test_rejected_without_resolution_rejected(tmp_path: Path) -> None:
    """decision: rejected without Resolution section is rejected."""
    content = VALID_SOLO_EPISODE.replace("decision: applied", "decision: rejected")
    content = content.replace(
        "## Resolution\nDecided to use the approach described above.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Resolution" in e for e in errors)


def test_deferred_without_resolution_passes(tmp_path: Path) -> None:
    """decision: deferred without Resolution section passes."""
    content = VALID_SOLO_EPISODE.replace("decision: applied", "decision: deferred")
    content = content.replace(
        "## Resolution\nDecided to use the approach described above.\n\n", ""
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert not any("Resolution" in e for e in errors)


def test_deferred_with_resolution_passes(tmp_path: Path) -> None:
    """decision: deferred WITH Resolution section also passes."""
    content = VALID_SOLO_EPISODE.replace("decision: applied", "decision: deferred")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert not any("Resolution" in e for e in errors)


def test_resolution_present_but_empty_rejected(tmp_path: Path) -> None:
    """Resolution section present but with no content is rejected when decision != deferred."""
    content = VALID_SOLO_EPISODE.replace(
        "## Resolution\nDecided to use the approach described above.",
        "## Resolution\n",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Resolution" in e and "empty" in e for e in errors)


def test_dialogue_position_present_but_empty_rejected(tmp_path: Path) -> None:
    """Claude Position header present but empty content is rejected."""
    content = VALID_DIALOGUE_EPISODE.replace(
        "## Claude Position\nClaude argued for approach A because of X.",
        "## Claude Position\n",
    )
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("Claude Position" in e and "empty" in e for e in errors)


# ---------------------------------------------------------------------------
# decided_by restriction (Verification cases 26, 27)
# ---------------------------------------------------------------------------


def test_decided_by_debate_rejected(tmp_path: Path) -> None:
    """decided_by: debate is rejected in Phase 1a."""
    content = VALID_SOLO_EPISODE.replace("decided_by: user", "decided_by: debate")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid decided_by" in e for e in errors)


def test_decided_by_auto_verify_rejected(tmp_path: Path) -> None:
    """decided_by: auto-verify is rejected in Phase 1a."""
    content = VALID_SOLO_EPISODE.replace("decided_by: user", "decided_by: auto-verify")
    path = _write_episode(tmp_path, content)
    errors = MODULE.validate(path)
    assert any("invalid decided_by" in e for e in errors)


# ---------------------------------------------------------------------------
# Frontmatter parsing edge cases
# ---------------------------------------------------------------------------


def test_missing_frontmatter_delimiter(tmp_path: Path) -> None:
    """File without opening --- is rejected."""
    path = _write_episode(tmp_path, "no frontmatter here\n## Summary\ntext\n")
    errors = MODULE.validate(path)
    assert any("parse failed" in e for e in errors)


def test_unreadable_file(tmp_path: Path) -> None:
    """Non-existent file returns a read error."""
    path = tmp_path / "nonexistent.md"
    errors = MODULE.validate(path)
    assert any("read failed" in e for e in errors)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_valid_episode(tmp_path: Path) -> None:
    """CLI returns 0 for a valid episode."""
    path = _write_episode(tmp_path, VALID_SOLO_EPISODE)
    # Test via module's main() by patching sys.argv
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["validate_episode.py", str(path)]
        exit_code = MODULE.main()
    finally:
        sys.argv = original_argv
    assert exit_code == 0


def test_cli_invalid_episode(tmp_path: Path) -> None:
    """CLI returns 1 for an invalid episode."""
    content = VALID_SOLO_EPISODE.replace("task_type: debugging", "task_type: invalid")
    path = _write_episode(tmp_path, content)
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["validate_episode.py", str(path)]
        exit_code = MODULE.main()
    finally:
        sys.argv = original_argv
    assert exit_code == 1
