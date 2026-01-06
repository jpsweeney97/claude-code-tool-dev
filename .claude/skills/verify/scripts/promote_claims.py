#!/usr/bin/env python3
"""
Promote claims from pending-claims.md to known-claims.md.

Moves verified claims from the pending queue to the permanent cache,
inserting them into the appropriate section.

Exit codes:
    0: Success (≥1 claim promoted)
    1: Input error (file missing, parse error, invalid section)
    10: No claims to promote

Usage:
    python promote_claims.py                    # Promote all pending claims
    python promote_claims.py --dry-run          # Preview without writing
    python promote_claims.py --interactive      # Confirm each claim
    python promote_claims.py --json             # JSON output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PendingClaim:
    """A claim awaiting promotion."""
    claim: str
    verdict: str
    evidence: str
    section: str
    date: str


@dataclass
class PromotionResult:
    """Result of the promotion operation."""
    promoted: list[PendingClaim] = field(default_factory=list)
    skipped_duplicates: list[PendingClaim] = field(default_factory=list)
    skipped_invalid_section: list[PendingClaim] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


VALID_SECTIONS = {"Skills", "Hooks", "Commands", "MCP", "Agents"}


# =============================================================================
# PARSING
# =============================================================================

def parse_pending_claims(path: Path) -> list[PendingClaim]:
    """Parse pending-claims.md into structured entries."""
    if not path.exists():
        return []

    content = path.read_text()
    claims: list[PendingClaim] = []

    for line in content.splitlines():
        # Parse table rows: | Claim | Verdict | Evidence | Section | Date |
        if line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                claims.append(PendingClaim(
                    claim=parts[0],
                    verdict=parts[1],
                    evidence=parts[2],
                    section=parts[3],
                    date=parts[4],
                ))

    return claims


def parse_known_claims_structure(path: Path) -> dict[str, list[str]]:
    """
    Parse known-claims.md to find existing claims per section.

    Returns:
        dict mapping section name → list of claim texts (for duplicate detection)
    """
    if not path.exists():
        return {}

    content = path.read_text()
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in content.splitlines():
        # Track section headers
        if line.startswith("## ") and not line.startswith("## How") and not line.startswith("## Maintenance"):
            section_name = line[3:].strip()
            if section_name in VALID_SECTIONS:
                current_section = section_name
                sections[current_section] = []
            continue

        # Parse table rows to extract claim text
        if current_section and line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if parts:
                # Normalize claim text for comparison
                claim_text = parts[0].strip("`").lower()
                sections[current_section].append(claim_text)

    return sections


def find_section_insert_point(content: str, section: str) -> int | None:
    """
    Find the line number where a new claim should be inserted for a section.

    Returns the line index of the last table row in the section (insert after this).
    Returns None if section not found.
    """
    lines = content.splitlines()
    in_section = False
    last_table_row = None

    for i, line in enumerate(lines):
        # Check for section header
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name == section:
                in_section = True
            elif in_section:
                # We've moved to a new section, stop
                break

        # Track last table row in section
        if in_section and line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            last_table_row = i

    return last_table_row


# =============================================================================
# PROMOTION LOGIC
# =============================================================================

def format_known_claim_row(claim: PendingClaim) -> str:
    """Format a pending claim as a known-claims.md table row."""
    return f"| {claim.claim} | {claim.verdict} | {claim.evidence} |"


def promote_claims(
    pending_path: Path,
    known_path: Path,
    dry_run: bool = False,
    interactive: bool = False,
) -> PromotionResult:
    """
    Promote pending claims to known-claims.md.

    Args:
        pending_path: Path to pending-claims.md
        known_path: Path to known-claims.md
        dry_run: If True, don't write changes
        interactive: If True, prompt for each claim

    Returns:
        PromotionResult with promoted/skipped claims and any errors
    """
    result = PromotionResult()

    # Parse pending claims
    pending = parse_pending_claims(pending_path)
    if not pending:
        return result

    # Parse known claims for duplicate detection
    known_structure = parse_known_claims_structure(known_path)

    # Read known-claims.md content for modification
    known_content = known_path.read_text()

    # Group pending claims by section for efficient insertion
    by_section: dict[str, list[PendingClaim]] = {}

    for claim in pending:
        # Validate section
        if claim.section not in VALID_SECTIONS:
            result.skipped_invalid_section.append(claim)
            continue

        # Check for duplicates
        claim_normalized = claim.claim.strip("`").lower()
        existing = known_structure.get(claim.section, [])
        if claim_normalized in existing:
            result.skipped_duplicates.append(claim)
            continue

        # Interactive mode: ask for confirmation
        if interactive and not dry_run:
            print(f"\nClaim: {claim.claim}")
            print(f"  Verdict: {claim.verdict}")
            print(f"  Section: {claim.section}")
            response = input("Promote? [Y/n] ").strip().lower()
            if response and response != "y":
                continue

        # Group for insertion
        if claim.section not in by_section:
            by_section[claim.section] = []
        by_section[claim.section].append(claim)

    # Insert claims into known-claims.md content
    lines = known_content.splitlines()

    # Process sections in reverse order of line numbers to avoid offset issues
    insertions: list[tuple[int, str]] = []

    for section, claims in by_section.items():
        insert_point = find_section_insert_point(known_content, section)
        if insert_point is None:
            for claim in claims:
                result.errors.append(f"Section '{section}' not found in known-claims.md")
                result.skipped_invalid_section.append(claim)
            continue

        # Add all claims for this section
        for claim in claims:
            row = format_known_claim_row(claim)
            insertions.append((insert_point, row))
            result.promoted.append(claim)

    # Sort insertions by line number descending (insert from bottom up)
    insertions.sort(key=lambda x: x[0], reverse=True)

    for insert_after, row in insertions:
        lines.insert(insert_after + 1, row)

    # Update "Last verified" date
    for i, line in enumerate(lines):
        if line.startswith("**Last verified:**"):
            lines[i] = f"**Last verified:** {date.today().isoformat()}"
            break

    # Write changes
    if not dry_run and result.promoted:
        # Write updated known-claims.md
        known_path.write_text("\n".join(lines) + "\n")

        # Clear pending-claims.md (keep header)
        pending_header = """# Pending Claims

Claims verified but not yet promoted to `known-claims.md`. Review during next `/verify` invocation.

| Claim | Verdict | Evidence | Section | Date |
|-------|---------|----------|---------|------|
"""
        pending_path.write_text(pending_header)

    return result


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote claims from pending-claims.md to known-claims.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Promote all pending claims
    python promote_claims.py

    # Preview without writing
    python promote_claims.py --dry-run

    # Confirm each claim
    python promote_claims.py --interactive

    # JSON output
    python promote_claims.py --json
        """,
    )
    parser.add_argument(
        "--pending",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "pending-claims.md",
        help="Path to pending-claims.md",
    )
    parser.add_argument(
        "--known",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for confirmation on each claim",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.pending.exists():
        print(f"Error: Pending file not found: {args.pending}", file=sys.stderr)
        return 1

    if not args.known.exists():
        print(f"Error: Known file not found: {args.known}", file=sys.stderr)
        return 1

    # Run promotion
    result = promote_claims(
        args.pending,
        args.known,
        dry_run=args.dry_run,
        interactive=args.interactive,
    )

    # Output
    if args.json:
        output = {
            "promoted": [asdict(c) for c in result.promoted],
            "skipped_duplicates": [asdict(c) for c in result.skipped_duplicates],
            "skipped_invalid_section": [asdict(c) for c in result.skipped_invalid_section],
            "errors": result.errors,
            "dry_run": args.dry_run,
        }
        print(json.dumps(output, indent=2))
    else:
        mode = "[DRY RUN] " if args.dry_run else ""

        if result.promoted:
            print(f"{mode}Promoted {len(result.promoted)} claim(s):")
            for claim in result.promoted:
                print(f"  ✓ [{claim.section}] {claim.claim}")

        if result.skipped_duplicates:
            print(f"\nSkipped {len(result.skipped_duplicates)} duplicate(s):")
            for claim in result.skipped_duplicates:
                print(f"  ⊘ [{claim.section}] {claim.claim}")

        if result.skipped_invalid_section:
            print(f"\nSkipped {len(result.skipped_invalid_section)} with invalid section:")
            for claim in result.skipped_invalid_section:
                print(f"  ✗ [{claim.section}] {claim.claim}")

        if result.errors:
            print(f"\nErrors:")
            for error in result.errors:
                print(f"  ! {error}")

        if not result.promoted and not result.skipped_duplicates and not result.skipped_invalid_section:
            print("No pending claims to promote.")

    # Exit code
    if result.promoted:
        return 0
    elif result.skipped_duplicates or result.skipped_invalid_section:
        return 0  # Still success if we processed something
    else:
        return 10  # No claims to promote


if __name__ == "__main__":
    sys.exit(main())
