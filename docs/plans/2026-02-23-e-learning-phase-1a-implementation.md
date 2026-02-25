# E-LEARNING Phase 1a Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured episode logging to the `/learn` skill — `/learn log` creates machine-validated episodes for the cross-model learning system.

**Architecture:** `/learn log` routes through SKILL.md to create YAML-frontmatter markdown files in `docs/learnings/episodes/`. A standalone validator script (`scripts/validate_episode.py`) checks structural constraints (13 checks) at generation time. The episode schema reference file (`.claude/skills/learn/references/episode-schema.md`) is the authoritative source for field definitions, enum tables, and inference guidance. Phase 0's unstructured `/learn` path remains unchanged.

**Tech Stack:** Python 3.12+ (stdlib only for validator), YAML frontmatter, markdown, pytest

**Source plan:** `/Users/jp/.claude/plans/generic-hatching-cat.md` (296 lines, 6 Codex reviews)

---

## Task 1: Create Feature Branch and Episode Directory

**Files:**
- Create: `docs/learnings/episodes/.gitkeep`

**Step 1: Create feature branch**

```bash
git checkout -b feature/e-learning-phase-1a main
```

**Step 2: Create episode directory with .gitkeep**

Create the file `docs/learnings/episodes/.gitkeep` — empty file, just ensures git tracks the directory.

**Step 3: Commit**

```bash
git add docs/learnings/episodes/.gitkeep
git commit -m "chore: add episode directory for structured learning"
```

---

## Task 2: Create Episode Validator — Test Scaffolding

**Files:**
- Create: `scripts/validate_episode.py` (stub with module structure)
- Create: `tests/test_validate_episode.py`

**Step 1: Write validator stub**

Create `scripts/validate_episode.py` with the module structure and empty `validate()` function. This follows the `validate_consultation_contract.py` pattern: stdlib only, importable as module, callable as CLI.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate an episode file against the Phase 1a schema.

Checks structural constraints: required fields, enum membership, conditional
body sections, ID/date format, and extension namespace. Does NOT check
semantic correctness of classification — that is handled by user confirmation.

Usage:
    uv run scripts/validate_episode.py docs/learnings/episodes/EP-0001.md
    uv run scripts/validate_episode.py --skip-id-sequence path/to/episode.md

Exit codes: 0 = valid, 1 = one or more errors.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TASK_TYPES: set[str] = {
    "code-change",
    "debugging",
    "testing",
    "code-review",
    "design",
    "planning",
    "research",
    "operations",
    "writing",
    "decision",
}

VALID_SOURCE_TYPES: set[str] = {"dialogue", "solo"}

VALID_DECISIONS: set[str] = {"applied", "rejected", "deferred"}

VALID_DECIDED_BY: set[str] = {"user"}  # Phase 1a: only "user"

REQUIRED_FIELDS: set[str] = {
    "id",
    "date",
    "title",
    "source_type",
    "domain",
    "task_type",
    "keywords",
    "decision",
    "decided_by",
    "safety",
    "schema_version",
}

# Regex patterns
ID_PATTERN = re.compile(r"^EP-\d{4}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECTION_HEADER_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse YAML frontmatter and body from episode text.

    Returns (frontmatter_dict, body_text). Raises ValueError on parse failure.
    Uses a simple line-by-line parser — no PyYAML dependency.
    """
    lines = text.strip().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("episode missing opening '---' frontmatter delimiter")

    end_idx: int | None = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("episode missing closing '---' frontmatter delimiter")

    fm: dict[str, object] = {}
    for line in lines[1:end_idx]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Parse booleans
        if value.lower() == "true":
            fm[key] = True
        elif value.lower() == "false":
            fm[key] = False
        # Parse integers
        elif value.isdigit():
            fm[key] = int(value)
        # Parse lists: [item1, item2, ...]
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                fm[key] = []
            else:
                fm[key] = [item.strip().strip("'\"") for item in inner.split(",")]
        # Parse quoted strings
        elif (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            fm[key] = value[1:-1]
        # Plain string
        else:
            fm[key] = value

    body = "\n".join(lines[end_idx + 1 :])
    return fm, body


def extract_body_sections(body: str) -> dict[str, str]:
    """Extract ## sections from body text. Returns {header: content}."""
    sections: dict[str, str] = {}
    matches = list(SECTION_HEADER_PATTERN.finditer(body))
    for i, match in enumerate(matches):
        header = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections[header] = content
    return sections


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def validate(filepath: Path, *, skip_id_sequence: bool = False) -> list[str]:
    """Validate an episode file. Returns list of error strings (empty = valid).

    Args:
        filepath: Path to the episode .md file.
        skip_id_sequence: If True, skip ID sequence check (useful for testing
            individual files without the full episode directory).
    """
    errors: list[str] = []

    try:
        text = filepath.read_text()
    except OSError as e:
        return [f"read failed: {e}"]

    # Parse frontmatter
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        return [f"parse failed: {e}"]

    # Check 1: Required fields
    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        errors.append(f"missing required fields: {sorted(missing)}")

    # Check 2: Enum validation
    if "task_type" in fm and fm["task_type"] not in VALID_TASK_TYPES:
        errors.append(
            f"invalid task_type: {fm['task_type']!r}. "
            f"Valid: {sorted(VALID_TASK_TYPES)}"
        )
    if "source_type" in fm and fm["source_type"] not in VALID_SOURCE_TYPES:
        errors.append(
            f"invalid source_type: {fm['source_type']!r}. "
            f"Valid: {sorted(VALID_SOURCE_TYPES)}"
        )
    if "decision" in fm and fm["decision"] not in VALID_DECISIONS:
        errors.append(
            f"invalid decision: {fm['decision']!r}. "
            f"Valid: {sorted(VALID_DECISIONS)}"
        )
    if "decided_by" in fm and fm["decided_by"] not in VALID_DECIDED_BY:
        errors.append(
            f"invalid decided_by: {fm['decided_by']!r}. "
            f"Phase 1a accepts: {sorted(VALID_DECIDED_BY)}"
        )

    # Check 3: Boolean type for safety
    if "safety" in fm and not isinstance(fm["safety"], bool):
        errors.append(
            f"safety must be boolean, got {type(fm['safety']).__name__}: {fm['safety']!r}"
        )

    # Check 4: ID format
    if "id" in fm:
        id_val = str(fm["id"])
        if not ID_PATTERN.match(id_val):
            errors.append(f"invalid id format: {id_val!r}. Expected: EP-NNNN")

    # Check 5: Date format
    if "date" in fm:
        date_val = str(fm["date"])
        if not DATE_PATTERN.match(date_val):
            errors.append(f"invalid date format: {date_val!r}. Expected: YYYY-MM-DD")

    # Check 6: schema_version exact match
    if "schema_version" in fm and fm["schema_version"] != 1:
        errors.append(
            f"invalid schema_version: {fm['schema_version']!r}. "
            f"Phase 1a requires exactly 1"
        )

    # Check 7: Unknown keys (reject unless x_* prefix)
    known_fields = REQUIRED_FIELDS | {"languages", "frameworks"}
    unknown = {k for k in fm if k not in known_fields and not k.startswith("x_")}
    if unknown:
        errors.append(
            f"unknown fields: {sorted(unknown)}. "
            f"Use x_* prefix for extensions"
        )

    # Check 8: Keyword count (1-5 entries)
    if "keywords" in fm:
        kw = fm["keywords"]
        if not isinstance(kw, list):
            errors.append(f"keywords must be a list, got {type(kw).__name__}")
        elif len(kw) < 1 or len(kw) > 5:
            errors.append(
                f"keywords must have 1-5 entries, got {len(kw)}"
            )

    # Parse body sections
    sections = extract_body_sections(body)

    # Check 9: Conditional body sections based on source_type
    source_type = fm.get("source_type")
    if source_type == "dialogue":
        for required in ("Claude Position", "Codex Position"):
            if required not in sections:
                errors.append(
                    f"source_type 'dialogue' requires '## {required}' section"
                )
            elif not sections[required]:
                errors.append(
                    f"'## {required}' section is present but empty"
                )
    elif source_type == "solo":
        for forbidden in ("Claude Position", "Codex Position"):
            if forbidden in sections:
                errors.append(
                    f"source_type 'solo' must not have '## {forbidden}' section"
                )

    # Check 10: Body presence — Summary and Evidence non-empty
    for required_section in ("Summary", "Evidence"):
        if required_section not in sections:
            errors.append(f"missing required section: '## {required_section}'")
        elif not sections[required_section]:
            errors.append(f"'## {required_section}' section is present but empty")

    # Check 11: Resolution conditionality
    decision = fm.get("decision")
    if decision in ("applied", "rejected"):
        if "Resolution" not in sections:
            errors.append(
                f"decision '{decision}' requires '## Resolution' section"
            )
        elif not sections["Resolution"]:
            errors.append(
                "'## Resolution' section is present but empty"
            )
    # deferred: Resolution is optional (either present or absent is fine)

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Run validation on a single episode file."""
    if os.environ.get("EPISODE_SKIP_VALIDATION") == "1":
        print('{"status": "skipped"}')
        return 0

    if len(sys.argv) < 2:
        print("Usage: validate_episode.py <path-to-episode.md>", file=sys.stderr)
        return 1

    filepath = Path(sys.argv[1])
    skip_id = "--skip-id-sequence" in sys.argv

    errors = validate(filepath, skip_id_sequence=skip_id)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "ok"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Write test file with imports and first test**

Create `tests/test_validate_episode.py` — start with the import pattern from `test_consultation_contract_sync.py` and the first happy-path test.

```python
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
```

**Step 3: Run tests to verify they pass**

Run: `uv run pytest tests/test_validate_episode.py -v`
Expected: ALL PASS (36 tests)

**Step 4: Commit**

```bash
git add scripts/validate_episode.py tests/test_validate_episode.py
git commit -m "feat: add episode validator with 36 tests

Validates Phase 1a episode schema: 13 structural checks covering
required fields, enum membership, conditional body sections, ID/date
format, keyword count, and extension namespace. Follows
validate_consultation_contract.py pattern (stdlib only, module + CLI)."
```

---

## Task 3: Create Episode Schema Reference

**Files:**
- Create: `.claude/skills/learn/references/episode-schema.md`

**Step 1: Create the references directory**

```bash
mkdir -p .claude/skills/learn/references
```

**Step 2: Write the schema reference file**

Create `.claude/skills/learn/references/episode-schema.md` (~120 lines). This is the authoritative source for field definitions, enum tables, inference guidance, and bias documentation. The SKILL.md references this file for details.

```markdown
# Episode Schema Reference

Authoritative field definitions for Phase 1a structured episodes. SKILL.md references this file for enum tables, inference guidance, and bias documentation.

**Schema version:** 1
**Validator:** `scripts/validate_episode.py`
**Storage:** `docs/learnings/episodes/EP-NNNN.md`

## Schema

```yaml
---
id: EP-NNNN              # Auto-incremented (glob highest existing + 1, zero-pad to 4)
date: YYYY-MM-DD          # Date of episode creation
title: string             # 1-line summary, max ~80 chars
source_type: dialogue|solo # Controls conditional body sections
domain: string            # Free-form: architecture, security, performance, etc.
task_type: <enum>         # See task_type table below
languages: []             # Optional: [python, typescript, ...]
frameworks: []            # Optional: [playwright, django, ...]
keywords: [list]          # Free-form searchable tags, 1-5 entries
decision: applied|rejected|deferred
decided_by: user          # Phase 1a: always "user"
safety: false             # true if touches auth/credentials/secrets
schema_version: 1         # Exact match required
---
```

### Required Fields

All fields above are required except `languages` and `frameworks` (default to `[]`).

### ID Generation

1. Glob `docs/learnings/episodes/EP-*.md`
2. Parse highest existing number (or 0 if none)
3. Increment by 1
4. Zero-pad to 4 digits: `EP-0001`, `EP-0002`, ...

### Conditional Body Sections

| source_type | Required sections | Forbidden sections |
|-------------|-------------------|--------------------|
| `dialogue` | Summary, Claude Position, Codex Position, Evidence, Resolution* | — |
| `solo` | Summary, Evidence, Resolution* | Claude Position, Codex Position |

*Resolution required when `decision` is `applied` or `rejected`. Optional when `deferred`.

### Immutability

`decision` is the only mutable field (`deferred` → `applied`/`rejected`). All other fields are immutable after creation. Decision updates are manual file edits in Phase 1a.

## task_type Enum (10 values)

| Value | Description |
|-------|-------------|
| `code-change` | Writing or modifying code |
| `debugging` | Finding and fixing bugs |
| `testing` | Writing or running tests |
| `code-review` | Reviewing code or PRs |
| `design` | Architectural or system design |
| `planning` | Project planning, scoping, estimation |
| `research` | Exploring, reading docs, investigating |
| `operations` | CI/CD, deployment, infrastructure |
| `writing` | Documentation, specs, proposals |
| `decision` | Making or recording a choice between options |

## Inference Guidance

### Rules (normative — SKILL.md references these)

1. **Signals are suggestive, not deterministic.** Never auto-assign a value without user confirmation.
2. **Suggestion threshold:** ≥1 strong signal OR ≥2 weak signals from different families.
   - Strong signal: direct task intent or object (e.g., "review PR #42", "deploy rollback", "wrote failing test").
   - Weak signal: indirect contextual hint (e.g., "quality pass", "investigate", "looks good").
3. **Low confidence:** sparse, conflicting, or split signals → present options via AskUserQuestion. Do not guess.
4. **User override:** explicit user statement always overrides inference.

### Signal Table

| Value | Signal families (non-exhaustive) | Bias watch |
|-------|----------------------------------|------------|
| `code-change` | "wrote", "implemented", "refactored", "added function" | B1 (compression with debugging) |
| `debugging` | "root cause", "fixed bug", "stack trace", "bisected" | B1 (compression with code-change) |
| `testing` | "test suite", "coverage", "assertion", "TDD" | B1 (compression with code-change) |
| `code-review` | "PR review", "LGTM", "requested changes", "approved" | B5 (over-attribution if Codex involved) |
| `design` | "architecture", "trade-offs", "component boundaries" | B5 (over-attribution to dialogue) |
| `planning` | "roadmap", "sprint", "estimate", "scope", "phase" | — |
| `research` | "explored", "investigated", "docs say", "RFC" | B4 (recency — last doc read ≠ session topic) |
| `operations` | "deployed", "CI pipeline", "infrastructure", "Docker" | — |
| `writing` | "spec", "documentation", "proposal", "wrote up" | B1 (compression with design) |
| `decision` | "chose between", "decided", "trade-off accepted" | B2 (outcome optimism — toward applied) |
| `dialogue` (source_type) | Codex disagreement, cross-model resolution, contested claim | B5 (any /codex usage ≠ dialogue) |
| `solo` (source_type) | No Codex involvement in the insight | — |
| `applied` (decision) | "we went with", "implemented the fix", positive evidence | B2 (optimism), B6 (deferred underproduction) |
| `rejected` (decision) | "ruled out", "won't do", no "do later" language | B2 (optimism) |
| `deferred` (decision) | "revisit later", "postponed", "parking this" | B6 (underproduction — models avoid deferred) |

### Negative-Space Guards on `decision`

- `applied`: requires positive evidence AND no postponement language
- `rejected`: requires no "do later" or "revisit" markers
- `deferred`: requires explicit postpone/revisit marker
- Inconclusive (no clear signal, mixed markers): → AskUserQuestion

## Inference Biases

Six LLM-as-operator biases to watch for when generating episodes:

| # | Bias | Description | Mitigation |
|---|------|-------------|------------|
| B1 | Label compression | Multi-part sessions forced to one `task_type` | Multi-signal match → present options via AskUserQuestion |
| B2 | Outcome optimism | `applied` over-assigned vs `deferred` | Present `decision` for explicit user confirmation with negative-space guards |
| B3 | Authority leakage | Codex recommendation treated as user decision | `decided_by` is always `user` in Phase 1a |
| B4 | Recency artifact | `languages`/`frameworks` from last file, not session scope | Scan full conversation, not just recent context |
| B5 | Dialogue over-attribution | Any `/codex` usage triggers `dialogue` | `source_type` based on whether insight came from disagreement, not tool presence |
| B6 | Deferred underproduction | Models avoid `deferred` (feels incomplete) | Explicitly present `deferred` as valid option |

## Examples

### Solo Episode

```yaml
---
id: EP-0001
date: 2026-02-23
title: Heredoc substitution unreliable in zsh Bash tool
source_type: solo
domain: workflow
task_type: debugging
languages: [bash]
frameworks: []
keywords: [zsh, heredoc, bash-tool]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
The `$(cat <<'EOF' ... EOF)` heredoc pattern produces zsh temp file errors in Claude Code's Bash tool.

## Resolution
Switched to inline multiline strings for git commit messages and gh pr create bodies.

## Evidence
Error observed: `(eval):1: can't create temp file for here document`. Commands still succeeded but behavior is unreliable. Documented in CLAUDE.md as a known issue.
```

### Dialogue Episode

```yaml
---
id: EP-0002
date: 2026-02-23
title: Dual-version validator windows over-engineered for single-developer scale
source_type: dialogue
domain: architecture
task_type: design
languages: [python]
frameworks: []
keywords: [schema-migration, scale, codex]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
Schema version transitions should use atomic cutover, not dual-version acceptance windows.

## Claude Position
Dual-version validator modes (strict/transition) are over-engineered for single-developer scale with 5-20 episode files. Atomic cutover with migration script is sufficient.

## Codex Position
Initially proposed flag-based validator modes for backward compatibility during transitions. Conceded after scale argument — operational context (single developer, small file volume) doesn't justify the complexity.

## Resolution
Adopted atomic cutover: migration script (idempotent, --dry-run), one-pass migration, then switch validator to strict v2-only.

## Evidence
Planning dialogue converged in 5 turns. validate_consultation_contract.py has no version-range logic (validates exact structural invariants), confirming the pattern.
```
```

**Step 3: Commit**

```bash
git add .claude/skills/learn/references/episode-schema.md
git commit -m "feat: add episode schema reference with inference guidance

Authoritative source for field definitions, 10-value task_type enum,
signal table, 4 inference rules, negative-space guards, and 6 bias
descriptions. ~120 lines within budget."
```

---

## Task 4: Rewrite `/learn` SKILL.md

**Files:**
- Modify: `.claude/skills/learn/SKILL.md`

This is the largest task — rewriting the skill to add `/learn log` routing while preserving Phase 0 behavior. The skill lives in the dev repo at `.claude/skills/learn/SKILL.md` and will later be promoted to `~/.claude/skills/learn/SKILL.md`.

**Step 1: Write the updated SKILL.md**

The complete rewritten skill follows. Key changes from the existing skill:
- Updated `description` and `argument-hint` in frontmatter
- Added `$ARGUMENTS` routing section (log → Episode, promote → reject, else → Phase 0)
- Added Episode Logging flow with signal-based inference and two-step confirmation
- Renamed existing instructions to "Unstructured Capture"
- References schema reference file for details

```markdown
---
name: learn
description: >-
  Capture project insights. Two modes: `/learn log` creates a structured,
  machine-validated episode (cross-model learning system). `/learn` (no
  subcommand) appends an unstructured insight to the learnings file (Phase 0).
  Use when user says "/learn", "capture this insight", "log this learning".
argument-hint: "[log [hint] | hint]"
---

# Learn

Capture project insights for re-injection in future sessions.

## Routing

Extract the first token from `$ARGUMENTS` (case-insensitive, split on whitespace):

| First token | Route | Remaining tokens |
|-------------|-------|------------------|
| `log` | Episode Logging (below) | Passed as hint context |
| `promote` | Reject: "Not yet available. `/learn promote` is Phase 1b." | — |
| *(anything else)* | Unstructured Capture (below) | Full `$ARGUMENTS` used as hint |
| *(empty)* | Unstructured Capture (below) | No hint |

**Routing rules:** Exact first-token match only. No prefix matching. Case-insensitive comparison (`Log`, `LOG`, `log` all route to Episode Logging).

---

## Episode Logging (`/learn log`)

Create a structured, machine-validated episode file in `docs/learnings/episodes/`.

**Reference:** `.claude/skills/learn/references/episode-schema.md` is authoritative for field definitions, enum tables, inference rules, and bias documentation. Read it before generating an episode.

### Procedure

#### 1. Determine next episode ID

- Glob `docs/learnings/episodes/EP-*.md`
- Parse the highest existing number (0 if none exist)
- Next ID = highest + 1, zero-padded to 4 digits (`EP-0001`, `EP-0002`, ...)

#### 2. Determine `source_type`

Review the conversation for Codex involvement:

- If the insight came from a **Codex disagreement, cross-model resolution, or contested claim** → suggest `dialogue`
- If the insight is from **solo work with no Codex contribution** → suggest `solo`

**Bias watch (B5):** The presence of any `/codex` tool usage does NOT automatically mean `dialogue`. Only use `dialogue` when the *insight itself* came from the cross-model interaction, not just because Codex was consulted during the session.

Present the suggested value and confirm with the user via AskUserQuestion:
- Options: `dialogue`, `solo`
- Default: the suggested value

#### 3. Infer `task_type` and `decision`

For each field, scan the conversation for relevant signals. Consult the signal table and inference rules in the schema reference.

**Inference rules (from schema reference — authoritative):**

1. Signals are suggestive, not deterministic. Never auto-assign.
2. Suggest when ≥1 strong signal OR ≥2 weak signals from different families.
3. Sparse, conflicting, or split signals → mark low confidence, ask user.
4. Explicit user statement overrides inference.

**For `decision`, apply negative-space guards:**
- `applied`: requires positive evidence AND no postponement language
- `rejected`: requires no "do later" markers
- `deferred`: requires explicit postpone/revisit marker
- Inconclusive → AskUserQuestion with all three options

**Bias watch:**
- B1 (label compression): If the session spans multiple task types, present the top 2-3 candidates and let the user choose.
- B2 (outcome optimism): Do not default to `applied`. Check for postponement language before suggesting it.
- B6 (deferred underproduction): Explicitly include `deferred` as an option — do not omit it.

Present each inferred value with a brief rationale. Confirm via AskUserQuestion:
- For `task_type`: show the suggested value and 1-2 alternatives
- For `decision`: show the suggested value with the signal rationale

#### 4. Collect remaining fields

- `title`: Draft a 1-line summary (~80 chars). Present for confirmation.
- `domain`: Infer from conversation topic. Present for confirmation.
- `keywords`: Suggest 1-5 tags. Present for confirmation. Reuse tags from existing episodes and learnings where possible.
- `languages` / `frameworks`: Scan conversation for languages and frameworks mentioned in context. Default to `[]` if none relevant.
- `safety`: Set to `true` if the episode touches auth, credentials, or secrets. Default `false`.

**Bias watch (B4):** For `languages`/`frameworks`, scan the full conversation, not just recent context. The last file touched is not necessarily representative of the session scope.

#### 5. Two-step confirmation

**Step A — Compact metadata summary:**

Present all frontmatter fields as a compact block:

```
Episode draft:

  id: EP-0003
  date: 2026-02-23
  title: Atomic cutover replaces dual-version transition windows
  source_type: dialogue
  domain: architecture
  task_type: design
  languages: [python]
  frameworks: []
  keywords: [schema-migration, scale]
  decision: applied
  decided_by: user
  safety: false
  schema_version: 1

Confirm, edit, or cancel?
```

**Step B — Handle response:**

- **Confirm:** proceed to draft body sections
- **Edit:** Accept `field=value` directives (e.g., `task_type=planning, keywords=[a,b,c]`). Any frontmatter field accepted. Invalid enum/field → show error with valid options. Multiple edits comma-separated. Re-display summary after edits.
- **Cancel:** abort episode creation

#### 6. Draft body sections

Based on `source_type` and `decision`, draft the appropriate sections:

- **Summary:** One sentence summarizing the episode. Self-contained — a future session should understand without the original conversation.
- **Claude Position** (dialogue only): Claude's argument or recommendation.
- **Codex Position** (dialogue only): Codex's counter-argument or alternative.
- **Resolution** (required when `decision != deferred`): What was decided and why.
- **Evidence:** Supporting data — test results, patterns, code references.

If the user provided a hint (e.g., `/learn log the thing about scale`), focus the body content on that topic.

#### 7. Validate and write

1. Assemble the full episode file (frontmatter + body)
2. Write to a temp file
3. Run: `uv run scripts/validate_episode.py <temp-file>`
4. **On success (exit 0):** Move to `docs/learnings/episodes/EP-NNNN.md`
5. **On failure (exit 1):** Show validation errors. Fix the issue and retry from step 2. Do not write an invalid episode.

#### 8. Confirm

One-line summary: the EP ID, title, and file path.

```
Logged EP-0003: "Atomic cutover replaces dual-version transition windows" → docs/learnings/episodes/EP-0003.md
```

### Phase 0 hint

When running in Unstructured Capture mode (below), if the conversation shows signs of a Codex dialogue — cross-model disagreement, contested claims, position convergence — add a one-line suggestion after the capture:

> Tip: This insight came from a Codex dialogue. Consider `/learn log` for a structured episode.

This is a suggestion only. Do not block or redirect the Phase 0 flow.

---

## Unstructured Capture (`/learn`)

Extract an insight from the current conversation and append it to the project's learnings file for re-injection in future sessions. This is the Phase 0 path — quick, low-ceremony, append-only.

### Procedure

1. **Identify the insight.** Review the current conversation and extract the most notable insight.

   - If the user provided a hint (e.g., `/learn the thing about Codex infrastructure`), focus on that topic.
   - If no hint, identify the insight that would be most valuable in a future session — patterns discovered, mistakes caught, techniques that worked, architectural decisions and their reasoning.
   - Prefer specific, actionable insights over general observations.

2. **Select tags** from the table below. Pick 1-3 tags that fit. Create a new tag if none fit.

3. **Draft the entry** and present it to the user for confirmation:

   ```
   Draft learning:

   ### YYYY-MM-DD [tag1, tag2]

   One paragraph capturing the insight — specific enough to be actionable
   when re-read in a future session without the original context.

   Append to docs/learnings/learnings.md?
   ```

   Write the insight as a single paragraph. It should be self-contained — a future Claude session reading this entry should understand the insight without access to the original conversation.

4. **On confirmation, append the entry** to `docs/learnings/learnings.md`.

   If the file does not exist, create it with this header first:

   ```markdown
   # Learnings

   Project insights captured from consultations. Curate manually: delete stale entries, merge duplicates.
   ```

   Append using this exact format (preserve the blank line before the heading):

   ```markdown

   ### YYYY-MM-DD [tag1, tag2]

   The insight paragraph.
   ```

5. **Confirm** with a one-line summary: the date, tags, and first ~10 words of the insight.

### Example Tags

| Tag | Use for |
|-----|---------|
| `codex` | Insights from Codex dialogues |
| `architecture` | Architectural decisions and patterns |
| `debugging` | Debugging techniques and root causes |
| `workflow` | Process and workflow improvements |
| `testing` | Testing strategies and patterns |
| `security` | Security considerations |
| `pattern` | Reusable code or design patterns |
| `performance` | Performance optimization |
| `skill-design` | Skill authoring insights |
| `review` | Code review and feedback patterns |

These are examples, not a closed set. Create new tags when none fit.
```

**Step 2: Run existing tests to verify nothing broken**

Run: `uv run pytest tests/ -v`
Expected: All existing tests PASS

**Step 3: Commit**

```bash
git add .claude/skills/learn/SKILL.md
git commit -m "feat: rewrite /learn skill with episode logging route

Adds /learn log subcommand for structured episode creation with
signal-based inference, two-step confirmation, and inline validation.
Preserves Phase 0 /learn path unchanged. References episode-schema.md
for field definitions and inference rules."
```

---

## Task 5: Update Rules File

**Files:**
- Modify: `.claude/rules/learnings.md`

**Step 1: Read current file and add episode reference**

Current content (5 lines):

```markdown
# Learnings

At session start, read `docs/learnings/learnings.md` for accumulated project insights from prior consultations. Use these as context for current work — they capture patterns, mistakes, and decisions that recur across sessions.

If the file does not exist or is empty, skip silently.
```

Add one line noting episode files. Updated content:

```markdown
# Learnings

At session start, read `docs/learnings/learnings.md` for accumulated project insights from prior consultations. Use these as context for current work — they capture patterns, mistakes, and decisions that recur across sessions.

Structured episodes in `docs/learnings/episodes/` contain machine-validated insights with metadata (task type, decision, evidence). These are created via `/learn log` and are used by the cross-model learning pipeline.

If the file does not exist or is empty, skip silently.
```

**Step 2: Commit**

```bash
git add .claude/rules/learnings.md
git commit -m "chore: add episode directory reference to learnings rule"
```

---

## Task 6: Amend Spec with A9

**Files:**
- Modify: `docs/plans/2026-02-10-cross-model-learning-system.md`

**Step 1: Read the end of the spec to find insertion point**

The spec ends at A8 (line ~1396). A9 goes after A8.

**Step 2: Append A9 amendment**

Add the following after the A8 section:

```markdown

### A9. Phase 1a Implementation (forward-reference)

**Date:** 2026-02-23
**Source:** 6 Codex dialogues (32 turns, 59 resolved items) reviewing the Phase 1a implementation plan.

Phase 1a implementation establishes structured episode logging. This amendment documents forward-references from the plan to the spec, and records where 1a implementation detail supersedes spec-level descriptions.

#### 1. Generation-time validation gate

`scripts/validate_episode.py` performs 13 structural checks at episode creation time. This is distinct from the Gate 1 card linter described in §5 (which operates at promotion time in Phase 1b). The generation-time validator checks syntactic structural validity only — well-formed YAML, valid enum members, required sections present and non-empty. Semantic correctness is handled by mandatory user confirmation.

#### 2. `/learn` routing table

| First token | Route |
|-------------|-------|
| `log` | Episode Logging (structured, validated) |
| `promote` | Reject: "Not yet available" (Phase 1b) |
| *(else)* | Phase 0 Unstructured Capture |

#### 3. Authoritative schema location

The episode schema is defined in `.claude/skills/learn/references/episode-schema.md`. The episode sub-schema in §4 is superseded for field-level detail (enum values, conditional body rules, inference guidance). The card schema in §4 remains authoritative and is not affected by this amendment.

#### 4. `decided_by` Phase 1a restriction

Phase 1a accepts only `decided_by: user`. The values `auto-verify` and `debate` are deferred to Phase 1b when the calibration pipeline can assess automated decisions.

#### 5. Deferred harmonization

The following are implemented in 1a but formally documented in a 1b amendment: `source_type` conditional body rules, `task_type` 10-value enum alignment with `applies_to.task_types`, and the `concepts` field (deferred entirely — not in 1a schema).

#### 6. Upgrade choreography (atomic cutover)

Schema version transitions use atomic cutover, not dual-version acceptance windows. Protocol for 1b:

1. Open 1b A-series amendment entry (schema delta + migration scope)
2. Perform A9 supersession scope review as explicit decision
3. Update episode schema reference to v2 (**prerequisite gate** — validator changes cannot begin until complete)
4. Add `scripts/migrate_episodes.py` (idempotent, `--dry-run`, summary counts: total/migrated/unchanged/failed; fail-fast on first error)
5. Run migration dry-run; resolve blockers
6. Run migration in one pass (atomic cutover; interrupted migration requires rerun-to-clean before validator switch)
7. Switch validator to strict v2-only (`schema_version == 2`, exact match)
8. Full corpus validation + CI; completion criteria: zero v1 episodes, all pass v2
9. Record cutover outcome in 1b notes (before/after counts, failed=0, timestamp)
```

**Step 3: Commit**

```bash
git add docs/plans/2026-02-10-cross-model-learning-system.md
git commit -m "docs: add A9 amendment — Phase 1a forward-reference

Documents generation-time validation gate, /learn routing table,
authoritative schema location, decided_by restriction, deferred
harmonization, and atomic cutover upgrade choreography."
```

---

## Task 7: Integration Testing

**Files:**
- No new files — manual verification

Run through the verification cases from the plan to confirm the system works end-to-end.

**Step 1: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: ALL PASS (existing tests + new episode validator tests)

**Step 2: CLI smoke test**

Run: `uv run scripts/validate_episode.py --help 2>&1 || uv run scripts/validate_episode.py 2>&1`
Expected: Usage message or error about missing file argument

**Step 3: Verify validator on schema reference examples**

Create a temp valid episode and validate it:

```bash
cat > /tmp/test-ep.md << 'EPISODE'
---
id: EP-0001
date: 2026-02-23
title: Test episode
source_type: solo
domain: testing
task_type: debugging
languages: [python]
frameworks: []
keywords: [test]
decision: applied
decided_by: user
safety: false
schema_version: 1
---

## Summary
A test episode.

## Resolution
Test resolution.

## Evidence
Test evidence.
EPISODE
uv run scripts/validate_episode.py /tmp/test-ep.md
```

Expected: `{"status": "ok"}`

**Step 4: Verify validator catches errors**

```bash
cat > /tmp/test-ep-bad.md << 'EPISODE'
---
id: EP-1
date: 02-23-2026
title: Bad episode
source_type: group
domain: testing
task_type: hacking
keywords: []
decision: maybe
decided_by: debate
safety: "false"
schema_version: 2
---

## Summary
Bad episode.
EPISODE
uv run scripts/validate_episode.py /tmp/test-ep-bad.md
```

Expected: Exit 1, multiple ERROR lines to stderr

**Step 5: Verify file structure**

```bash
ls -la docs/learnings/episodes/
ls -la .claude/skills/learn/references/
ls -la scripts/validate_episode.py
```

Expected: All files exist

---

## Task 8: Promote to Production

**Files:**
- Promotes `.claude/skills/learn/` → `~/.claude/skills/learn/`

**Step 1: Run promote script**

```bash
uv run scripts/promote skill learn
```

Expected: Success message, files copied to `~/.claude/skills/learn/`

**Step 2: Verify production files**

```bash
ls -la ~/.claude/skills/learn/
ls -la ~/.claude/skills/learn/references/
```

Expected: SKILL.md and references/episode-schema.md present

**Step 3: Final commit (if promote modifies anything)**

Only commit if the promote script modifies tracked files. It typically only copies to the global directory.

---

## Verification Checklist

Map to the 36 verification cases from the plan:

| # | Case | Covered by |
|---|------|------------|
| 1-5 | Routing | Task 4 SKILL.md routing table (manual test) |
| 6-8 | Episode creation | Task 4 SKILL.md procedure (manual test) |
| 9-15 | Validation checks | Task 2 tests (automated) |
| 16-18 | UX | Task 4 SKILL.md procedure (manual test) |
| 19-20 | CLI | Task 2 CLI tests (automated) |
| 21-36 | Deep-review + adversarial cases | Task 2 tests (automated) |

---

## Summary

| Task | Files | Tests | Commit message |
|------|-------|-------|----------------|
| 1 | `docs/learnings/episodes/.gitkeep` | — | `chore: add episode directory` |
| 2 | `scripts/validate_episode.py`, `tests/test_validate_episode.py` | 36 | `feat: add episode validator with 36 tests` |
| 3 | `.claude/skills/learn/references/episode-schema.md` | — | `feat: add episode schema reference` |
| 4 | `.claude/skills/learn/SKILL.md` | — | `feat: rewrite /learn skill with episode logging` |
| 5 | `.claude/rules/learnings.md` | — | `chore: add episode directory reference` |
| 6 | `docs/plans/2026-02-10-cross-model-learning-system.md` | — | `docs: add A9 amendment` |
| 7 | — | smoke tests | — |
| 8 | promote to `~/.claude/` | — | — |
