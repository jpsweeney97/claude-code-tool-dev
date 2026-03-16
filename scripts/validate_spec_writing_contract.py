#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the spec-writing contract: SKILL.md inlined blocks must match shared-contract.md.

Checks:
1. Claims Enum table matches between SKILL.md and shared-contract.md.
2. Claim-to-Role Derivation Table matches between SKILL.md and shared-contract.md.
3. spec.yaml Schema block matches between SKILL.md and shared-contract.md.
4. Producer Failure Model table matches between SKILL.md and shared-contract.md.
5. All 4 SYNC comment markers are present in SKILL.md.
6. Claims Enum has exactly 8 entries.
7. Derivation Table has exactly 6 roles.

Usage:
    uv run scripts/validate_spec_writing_contract.py
    uv run scripts/validate_spec_writing_contract.py --repo-root /path/to/repo

Exit codes: 0 = all checks pass, 1 = one or more failures.
"""

import argparse
import re
import sys
from pathlib import Path

EXPECTED_CLAIM_COUNT = 8
EXPECTED_ROLE_COUNT = 6

SYNC_MARKERS = [
    "docs/references/shared-contract.md#claims-enum",
    "docs/references/shared-contract.md#derivation-table",
    "docs/references/shared-contract.md#spec-yaml-schema",
    "docs/references/shared-contract.md#failure-model",
]

# Anchor → heading text in shared-contract.md
ANCHOR_TO_HEADING: dict[str, str] = {
    "claims-enum": "## Claims Enum",
    "derivation-table": "## Claim-to-Role Derivation Table",
    "spec-yaml-schema": "## spec.yaml",
    "failure-model": "## Failure Model",
}


def read_file(path: Path) -> str:
    """Read a file. Raises OSError with descriptive message on failure."""
    try:
        return path.read_text()
    except OSError as e:
        raise OSError(f"cannot read {path} ({type(e).__name__}): {e}") from e


def extract_table_rows(text: str) -> list[str]:
    """Extract non-separator table rows from text (lines starting with |).

    Ignores separator rows (lines like |---|---|).
    Returns stripped row strings.
    """
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Skip separator rows: |---|---| or |:---|:---:|
        if re.match(r"^\|[-|: ]+\|$", stripped):
            continue
        rows.append(stripped)
    return rows


def extract_fenced_block(text: str) -> str | None:
    """Extract the first fenced code block (``` ... ```) from text.

    Returns the content between the fences (stripping the fence lines themselves),
    or None if no fenced block is found.
    """
    lines = text.splitlines()
    inside = False
    block_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not inside and stripped.startswith("```"):
            inside = True
            continue
        if inside and stripped.startswith("```"):
            inside = False
            break
        if inside:
            block_lines.append(line)
    return "\n".join(block_lines) if block_lines else None


def extract_section_after_marker(text: str, marker: str) -> str:
    """Extract text from the SYNC marker's own ## heading until the next ## heading or SYNC marker.

    The SYNC marker immediately precedes the ## heading for that section.
    We include the heading itself and extract until the next ## heading or SYNC marker.

    Returns empty string if marker not found.
    """
    marker_line = f"<!-- SYNC: {marker} -->"
    pos = text.find(marker_line)
    if pos == -1:
        return ""

    # Text from the marker onward (includes the heading that follows)
    after_marker = text[pos + len(marker_line):]

    # The first ## heading in after_marker is the section heading for this block.
    # We want everything from that heading until the next ## heading or SYNC marker.
    first_heading = re.search(r"\n## ", after_marker)
    if first_heading is None:
        return ""

    # Content starts at the first heading
    section_start = first_heading.start()
    section_text = after_marker[section_start:]

    # Find the end: the next ## heading after the first, or next SYNC marker
    # Search past the first "## " (skip 4 chars: "\n## ")
    next_heading = re.search(r"\n## ", section_text[4:])
    next_sync = section_text.find("<!-- SYNC:")

    end = len(section_text)
    if next_heading is not None:
        end = min(end, next_heading.start() + 4)
    if next_sync != -1:
        end = min(end, next_sync)

    return section_text[:end]


def extract_section_from_contract(text: str, anchor: str) -> str:
    """Extract a section from the shared contract by its heading anchor.

    Finds the heading matching ANCHOR_TO_HEADING[anchor] and returns
    text from that heading until the next ## heading or EOF.
    """
    heading = ANCHOR_TO_HEADING.get(anchor)
    if heading is None:
        return ""

    pos = text.find(heading)
    if pos == -1:
        return ""

    # Start from the heading
    after_heading = text[pos:]

    # Find the next ## heading (but not the one we matched)
    next_heading = re.search(r"\n## ", after_heading[2:])  # skip past current ##
    if next_heading is not None:
        # +2 because we sliced off 2 chars above
        return after_heading[: next_heading.start() + 2]
    return after_heading


def normalize_table_rows(rows: list[str]) -> list[str]:
    """Normalize table rows: collapse multiple spaces within cells to single space."""
    normalized = []
    for row in rows:
        # Collapse runs of spaces to single space within the row content
        norm = re.sub(r"  +", " ", row)
        normalized.append(norm)
    return normalized


def check_sync_markers(skill_text: str) -> list[str]:
    """Verify all 4 SYNC comment markers are present in SKILL.md."""
    errors: list[str] = []
    for marker in SYNC_MARKERS:
        marker_line = f"<!-- SYNC: {marker} -->"
        if marker_line not in skill_text:
            errors.append(f"SKILL.md: missing SYNC marker: {marker_line!r}")
    return errors


def check_claims_enum(skill_text: str, contract_text: str) -> list[str]:
    """Verify the Claims Enum table in SKILL.md matches shared-contract.md."""
    errors: list[str] = []

    skill_section = extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#claims-enum"
    )
    contract_section = extract_section_from_contract(contract_text, "claims-enum")

    if not skill_section:
        errors.append("SKILL.md: Claims Enum section not found after SYNC marker")
        return errors
    if not contract_section:
        errors.append("shared-contract.md: Claims Enum section not found")
        return errors

    skill_rows = normalize_table_rows(extract_table_rows(skill_section))
    contract_rows = normalize_table_rows(extract_table_rows(contract_section))

    # Check count (excluding header row)
    skill_data_rows = skill_rows[1:] if len(skill_rows) > 1 else skill_rows
    if len(skill_data_rows) != EXPECTED_CLAIM_COUNT:
        errors.append(
            f"SKILL.md: Claims Enum has {len(skill_data_rows)} data rows, "
            f"expected {EXPECTED_CLAIM_COUNT}"
        )

    # Check set equality (order-insensitive for data rows; header must match)
    if skill_rows and contract_rows:
        skill_header = skill_rows[0] if skill_rows else ""
        contract_header = contract_rows[0] if contract_rows else ""
        if skill_header != contract_header:
            errors.append(
                f"Claims Enum header mismatch:\n"
                f"  SKILL.md:         {skill_header!r}\n"
                f"  shared-contract:  {contract_header!r}"
            )

        skill_data = set(skill_rows[1:])
        contract_data = set(contract_rows[1:])
        only_in_skill = skill_data - contract_data
        only_in_contract = contract_data - skill_data
        if only_in_skill:
            errors.append(
                f"Claims Enum: rows in SKILL.md not in shared-contract: {sorted(only_in_skill)}"
            )
        if only_in_contract:
            errors.append(
                f"Claims Enum: rows in shared-contract not in SKILL.md: {sorted(only_in_contract)}"
            )

    return errors


def check_derivation_table(skill_text: str, contract_text: str) -> list[str]:
    """Verify the Derivation Table in SKILL.md matches shared-contract.md."""
    errors: list[str] = []

    skill_section = extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#derivation-table"
    )
    contract_section = extract_section_from_contract(contract_text, "derivation-table")

    if not skill_section:
        errors.append(
            "SKILL.md: Derivation Table section not found after SYNC marker"
        )
        return errors
    if not contract_section:
        errors.append("shared-contract.md: Derivation Table section not found")
        return errors

    skill_rows = normalize_table_rows(extract_table_rows(skill_section))
    contract_rows = normalize_table_rows(extract_table_rows(contract_section))

    # Check role count (excluding header row)
    skill_data_rows = skill_rows[1:] if len(skill_rows) > 1 else skill_rows
    if len(skill_data_rows) != EXPECTED_ROLE_COUNT:
        errors.append(
            f"SKILL.md: Derivation Table has {len(skill_data_rows)} data rows, "
            f"expected {EXPECTED_ROLE_COUNT}"
        )

    if skill_rows and contract_rows:
        skill_header = skill_rows[0] if skill_rows else ""
        contract_header = contract_rows[0] if contract_rows else ""
        if skill_header != contract_header:
            errors.append(
                f"Derivation Table header mismatch:\n"
                f"  SKILL.md:         {skill_header!r}\n"
                f"  shared-contract:  {contract_header!r}"
            )

        skill_data = set(skill_rows[1:])
        contract_data = set(contract_rows[1:])
        only_in_skill = skill_data - contract_data
        only_in_contract = contract_data - skill_data
        if only_in_skill:
            errors.append(
                f"Derivation Table: rows in SKILL.md not in shared-contract: "
                f"{sorted(only_in_skill)}"
            )
        if only_in_contract:
            errors.append(
                f"Derivation Table: rows in shared-contract not in SKILL.md: "
                f"{sorted(only_in_contract)}"
            )

    return errors


def check_spec_yaml_schema(skill_text: str, contract_text: str) -> list[str]:
    """Verify the spec.yaml Schema fenced block in SKILL.md matches shared-contract.md."""
    errors: list[str] = []

    skill_section = extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#spec-yaml-schema"
    )
    contract_section = extract_section_from_contract(contract_text, "spec-yaml-schema")

    if not skill_section:
        errors.append("SKILL.md: spec.yaml Schema section not found after SYNC marker")
        return errors
    if not contract_section:
        errors.append("shared-contract.md: spec.yaml Schema section not found")
        return errors

    skill_block = extract_fenced_block(skill_section)
    contract_block = extract_fenced_block(contract_section)

    if skill_block is None:
        errors.append("SKILL.md: spec.yaml Schema has no fenced code block")
        return errors
    if contract_block is None:
        errors.append("shared-contract.md: spec.yaml Schema has no fenced code block")
        return errors

    # Normalize: strip trailing whitespace from each line, ignore blank-line differences
    def normalize_block(block: str) -> list[str]:
        lines = [line.rstrip() for line in block.splitlines()]
        # Remove trailing empty lines
        while lines and not lines[-1]:
            lines.pop()
        return lines

    skill_lines = normalize_block(skill_block)
    contract_lines = normalize_block(contract_block)

    if skill_lines != contract_lines:
        # Find first differing line for a helpful error
        for i, (sl, cl) in enumerate(zip(skill_lines, contract_lines)):
            if sl != cl:
                errors.append(
                    f"spec.yaml Schema block mismatch at line {i + 1}:\n"
                    f"  SKILL.md:         {sl!r}\n"
                    f"  shared-contract:  {cl!r}"
                )
                break
        else:
            # One is longer than the other
            errors.append(
                f"spec.yaml Schema block length mismatch: "
                f"SKILL.md has {len(skill_lines)} lines, "
                f"shared-contract has {len(contract_lines)} lines"
            )

    return errors


def check_failure_model(skill_text: str, contract_text: str) -> list[str]:
    """Verify the Producer Failure Model table in SKILL.md matches shared-contract.md."""
    errors: list[str] = []

    skill_section = extract_section_after_marker(
        skill_text, "docs/references/shared-contract.md#failure-model"
    )
    # Contract has a subsection "### Producer Failures" under "## Failure Model"
    contract_full_section = extract_section_from_contract(contract_text, "failure-model")

    if not skill_section:
        errors.append("SKILL.md: Failure Model section not found after SYNC marker")
        return errors
    if not contract_full_section:
        errors.append("shared-contract.md: Failure Model section not found")
        return errors

    # Extract producer failures subsection from contract
    producer_start = contract_full_section.find("### Producer Failures")
    if producer_start == -1:
        errors.append(
            "shared-contract.md: '### Producer Failures' subsection not found"
        )
        return errors

    producer_section = contract_full_section[producer_start:]
    # Stop at next ### or ## heading
    next_sub = re.search(r"\n### ", producer_section[len("### Producer Failures"):])
    next_h2 = re.search(r"\n## ", producer_section)
    end = len(producer_section)
    if next_sub is not None:
        end = min(end, next_sub.start() + len("### Producer Failures"))
    if next_h2 is not None:
        end = min(end, next_h2.start())
    producer_section = producer_section[:end]

    skill_rows = normalize_table_rows(extract_table_rows(skill_section))
    contract_rows = normalize_table_rows(extract_table_rows(producer_section))

    if not skill_rows:
        errors.append("SKILL.md: Failure Model section has no table rows")
        return errors
    if not contract_rows:
        errors.append("shared-contract.md: Producer Failures has no table rows")
        return errors

    if skill_rows and contract_rows:
        skill_header = skill_rows[0]
        contract_header = contract_rows[0]
        if skill_header != contract_header:
            errors.append(
                f"Failure Model header mismatch:\n"
                f"  SKILL.md:         {skill_header!r}\n"
                f"  shared-contract:  {contract_header!r}"
            )

        skill_data = set(skill_rows[1:])
        contract_data = set(contract_rows[1:])
        only_in_skill = skill_data - contract_data
        only_in_contract = contract_data - skill_data
        if only_in_skill:
            errors.append(
                f"Failure Model: rows in SKILL.md not in shared-contract: "
                f"{sorted(only_in_skill)}"
            )
        if only_in_contract:
            errors.append(
                f"Failure Model: rows in shared-contract not in SKILL.md: "
                f"{sorted(only_in_contract)}"
            )

    return errors


def validate(repo_root: Path | None = None) -> list[str]:
    """Run all checks. Returns list of error strings — empty list means all pass."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    skill_path = repo_root / ".claude/skills/spec-writer/SKILL.md"
    contract_path = repo_root / "docs/references/shared-contract.md"

    errors: list[str] = []

    skill_text: str | None = None
    contract_text: str | None = None

    try:
        skill_text = read_file(skill_path)
    except OSError as e:
        errors.append(f"validate failed: cannot read SKILL.md. Got: {str(e)!r:.100}")

    try:
        contract_text = read_file(contract_path)
    except OSError as e:
        errors.append(
            f"validate failed: cannot read shared-contract.md. Got: {str(e)!r:.100}"
        )

    if skill_text is not None:
        errors.extend(check_sync_markers(skill_text))

    if skill_text is not None and contract_text is not None:
        errors.extend(check_claims_enum(skill_text, contract_text))
        errors.extend(check_derivation_table(skill_text, contract_text))
        errors.extend(check_spec_yaml_schema(skill_text, contract_text))
        errors.extend(check_failure_model(skill_text, contract_text))

    return errors


def main() -> int:
    """Run validation, print results, return exit code."""
    parser = argparse.ArgumentParser(
        description="Validate the spec-writing contract: SKILL.md vs shared-contract.md."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of this script's directory)",
    )
    args = parser.parse_args()

    print("validate_spec_writing_contract: running checks...")
    errors = validate(repo_root=args.repo_root)

    if errors:
        print(f"FAIL: {len(errors)} error(s) found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"PASS: all checks passed "
        f"({EXPECTED_CLAIM_COUNT} claims, "
        f"{EXPECTED_ROLE_COUNT} derivation roles, "
        f"{len(SYNC_MARKERS)} sync markers verified)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
