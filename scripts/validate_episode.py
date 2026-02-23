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
            Note: ID sequence check deferred to Phase 1b. Parameter
            retained for CLI/API stability.
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
