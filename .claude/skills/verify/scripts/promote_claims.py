#!/usr/bin/env python3
"""
Promote claims from pending-claims.md to known-claims.md.

Moves verified claims from the pending queue to the permanent cache,
inserting them into the appropriate section with their verification date.

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
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path


# =============================================================================
# VERSION DETECTION
# =============================================================================

def get_claude_code_version() -> str | None:
    """Get current Claude Code version."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


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
    normalized_sections: list[tuple[str, str]] = field(default_factory=list)  # (original, normalized)
    errors: list[str] = field(default_factory=list)


# Section normalization: map common variants to canonical names
# Keys are lowercase for case-insensitive matching
SECTION_ALIASES: dict[str, str] = {
    "feature": "Features",
    "setting": "Settings",
    "hook": "Hooks",
    "command": "Commands",
    "skill": "Skills",
    "agent": "Agents",
}

# Source URLs for known documentation sections
# Used when creating new sections to provide traceable evidence
SECTION_SOURCES: dict[str, str] = {
    # Core extension types
    "Skills": "https://code.claude.com/docs/en/skills.md",
    "Hooks": "https://code.claude.com/docs/en/hooks.md",
    "Commands": "https://code.claude.com/docs/en/slash-commands.md",
    "MCP": "https://code.claude.com/docs/en/mcp.md",
    "Agents": "https://code.claude.com/docs/en/agents.md",

    # Configuration and settings
    "Settings": "https://code.claude.com/docs/en/interactive-mode.md",
    "Permissions": "https://code.claude.com/docs/en/permissions.md",
    "Configuration": "https://code.claude.com/docs/en/configuration.md",

    # Features and capabilities
    "CLI": "https://code.claude.com/docs/en/cli.md",
    "Features": "https://code.claude.com/docs/en/overview.md",
    "Memory": "https://code.claude.com/docs/en/memory.md",
    "Context": "https://code.claude.com/docs/en/context.md",

    # Integrations
    "IDE": "https://code.claude.com/docs/en/ide-integrations.md",
    "GitHub": "https://code.claude.com/docs/en/github.md",
    "Git": "https://code.claude.com/docs/en/git.md",

    # Advanced topics
    "Plugins": "https://code.claude.com/docs/en/plugins.md",
    "SDK": "https://code.claude.com/docs/en/sdk.md",
    "API": "https://code.claude.com/docs/en/api.md",
    "Security": "https://code.claude.com/docs/en/security.md",
    "Bedrock": "https://code.claude.com/docs/en/bedrock.md",
    "Vertex": "https://code.claude.com/docs/en/vertex.md",

    # Troubleshooting
    "Troubleshooting": "https://code.claude.com/docs/en/troubleshooting.md",
    "Debugging": "https://code.claude.com/docs/en/debugging.md",
}


def normalize_section(section: str, valid_sections: set[str]) -> tuple[str, bool]:
    """
    Normalize a section name to its canonical form.

    Args:
        section: The section name to normalize
        valid_sections: Set of existing section names in known-claims.md

    Returns:
        Tuple of (normalized_name, was_normalized).
        If section is unknown and not aliased, returns (section, False) for new section creation.
    """
    # Exact match (case-sensitive)
    if section in valid_sections:
        return (section, False)

    # Check aliases (case-insensitive)
    section_lower = section.lower()
    if section_lower in SECTION_ALIASES:
        canonical = SECTION_ALIASES[section_lower]
        if canonical in valid_sections:
            return (canonical, True)
        # Alias exists but section doesn't - use canonical form for new section
        return (canonical, True)

    # Case-insensitive match against valid sections
    for valid in valid_sections:
        if valid.lower() == section_lower:
            return (valid, True)

    # Unknown section - will create new one
    return (section, False)


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

    # Sections to skip (not claim containers)
    skip_sections = {"How to Use", "Maintenance"}

    for line in content.splitlines():
        # Track section headers - discover sections dynamically
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name not in skip_sections:
                current_section = section_name
                sections[current_section] = []
            else:
                current_section = None
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


def find_maintenance_section_line(content: str) -> int | None:
    """Find the line number of the Maintenance section header."""
    for i, line in enumerate(content.splitlines()):
        if line.startswith("## Maintenance"):
            return i
    return None


def infer_source_url(section: str) -> str:
    """
    Infer the documentation source URL for a section.

    Returns the known URL for recognized sections, or a placeholder for unknown sections.
    """
    return SECTION_SOURCES.get(section, "(pending verification)")


def create_new_section(section: str) -> str:
    """
    Generate a new section block for known-claims.md.

    The section is created with an inferred source URL (or placeholder for unknown sections).
    """
    source_url = infer_source_url(section)
    return f"""---

## {section}

**Source:** {source_url}

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|"""


# =============================================================================
# PROMOTION LOGIC
# =============================================================================

def format_known_claim_row(claim: PendingClaim, version: str | None = None) -> str:
    """Format a pending claim as a known-claims.md table row.

    If version is provided, appends it to the date for traceability.
    Format: "2026-01-06 (v2.0.76)" or just "2026-01-06" if no version.
    """
    date_col = claim.date
    if version:
        date_col = f"{claim.date} (v{version})"
    return f"| {claim.claim} | {claim.verdict} | {claim.evidence} | {date_col} |"


def promote_claims(
    pending_path: Path,
    known_path: Path,
    dry_run: bool = False,
    interactive: bool = False,
    record_version: bool = True,
) -> PromotionResult:
    """
    Promote pending claims to known-claims.md.

    Args:
        pending_path: Path to pending-claims.md
        known_path: Path to known-claims.md
        dry_run: If True, don't write changes
        interactive: If True, prompt for each claim
        record_version: If True, append Claude Code version to verification date

    Returns:
        PromotionResult with promoted/skipped claims and any errors
    """
    # Get version for recording (if requested)
    version = get_claude_code_version() if record_version else None
    result = PromotionResult()

    # Parse pending claims
    pending = parse_pending_claims(pending_path)
    if not pending:
        return result

    # Parse known claims for duplicate detection
    known_structure = parse_known_claims_structure(known_path)

    # Get valid sections for normalization
    valid_sections = set(known_structure.keys())

    # Read known-claims.md content for modification
    known_content = known_path.read_text()

    # Group pending claims by section for efficient insertion
    by_section: dict[str, list[PendingClaim]] = {}

    for claim in pending:
        # Normalize section name
        original_section = claim.section
        normalized_section, was_normalized = normalize_section(original_section, valid_sections)
        if was_normalized:
            result.normalized_sections.append((original_section, normalized_section))
            claim.section = normalized_section

        # Check for duplicates (using normalized section)
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

    # Track sections that need to be created
    sections_to_create: set[str] = set()

    # Process sections in reverse order of line numbers to avoid offset issues
    insertions: list[tuple[int, str]] = []

    for section, claims in by_section.items():
        insert_point = find_section_insert_point(known_content, section)

        if insert_point is None:
            # Section doesn't exist - mark for creation
            sections_to_create.add(section)
            # Claims will be added after section creation
            for claim in claims:
                result.promoted.append(claim)
        else:
            # Add all claims for this section
            for claim in claims:
                row = format_known_claim_row(claim, version)
                insertions.append((insert_point, row))
                result.promoted.append(claim)

    # Sort insertions by line number descending (insert from bottom up)
    insertions.sort(key=lambda x: x[0], reverse=True)

    for insert_after, row in insertions:
        lines.insert(insert_after + 1, row)

    # Create new sections before Maintenance (at end of file if no Maintenance)
    if sections_to_create:
        # Re-read lines after insertions
        current_content = "\n".join(lines)
        maintenance_line = find_maintenance_section_line(current_content)

        # Sort sections alphabetically for consistent ordering
        for section in sorted(sections_to_create, reverse=True):
            section_block = create_new_section(section)
            section_lines = section_block.splitlines()

            # Add claims to the new section
            claims_for_section = by_section[section]
            for claim in claims_for_section:
                section_lines.append(format_known_claim_row(claim, version))

            if maintenance_line is not None:
                # Insert before Maintenance, with blank line before ---
                insert_idx = maintenance_line
                # Find the --- separator before Maintenance
                for i in range(maintenance_line - 1, -1, -1):
                    if lines[i].strip() == "---":
                        insert_idx = i
                        break
                lines = lines[:insert_idx] + section_lines + [""] + lines[insert_idx:]
            else:
                # Append at end
                lines.extend([""] + section_lines)

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
    parser.add_argument(
        "--no-version",
        action="store_true",
        help="Don't record Claude Code version in verification date",
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
        record_version=not args.no_version,
    )

    # Output
    if args.json:
        output = {
            "promoted": [asdict(c) for c in result.promoted],
            "skipped_duplicates": [asdict(c) for c in result.skipped_duplicates],
            "skipped_invalid_section": [asdict(c) for c in result.skipped_invalid_section],
            "normalized_sections": result.normalized_sections,
            "errors": result.errors,
            "dry_run": args.dry_run,
        }
        print(json.dumps(output, indent=2))
    else:
        mode = "[DRY RUN] " if args.dry_run else ""

        if result.normalized_sections:
            print(f"Normalized {len(result.normalized_sections)} section name(s):")
            for original, normalized in result.normalized_sections:
                print(f"  ~ '{original}' → '{normalized}'")
            print()

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
