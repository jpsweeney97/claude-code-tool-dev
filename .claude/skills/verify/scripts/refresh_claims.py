#!/usr/bin/env python3
"""
Find and manage stale claims in known-claims.md.

Identifies claims that exceed the TTL threshold and need re-verification.
Can update verification dates for claims that have been re-verified.
Supports version-aware staleness: when Claude Code version changes, all
claims are flagged for review regardless of age.

Exit codes:
    0: Success (stale claims found or update successful)
    1: Input error (file missing, parse error)
    2: Version changed - all claims need review
    10: No stale claims found

Usage:
    python refresh_claims.py                      # List all stale claims
    python refresh_claims.py --version-aware      # Also check for version changes
    python refresh_claims.py --section Hooks      # Filter by section
    python refresh_claims.py --max-age 60         # Custom TTL (days)
    python refresh_claims.py --update "claim"     # Update verification date for a claim
    python refresh_claims.py --update-all         # Update all claims (after bulk re-verification)
    python refresh_claims.py --json               # JSON output for scripting
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from typing import NamedTuple

from _common import parse_verified_date, get_claude_code_version, DEFAULT_MAX_AGE_DAYS


# =============================================================================
# VERSION CHECKING
# =============================================================================

class Version(NamedTuple):
    """Parsed semantic version."""
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> "Version | None":
        """Parse a version string like '1.2.3'."""
        match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", version_str.strip())
        if not match:
            return None
        return cls(int(match.group(1)), int(match.group(2)), int(match.group(3)))


@dataclass
class VersionStatus:
    """Result of version comparison."""
    current: str | None
    stored: str | None
    changed: bool
    change_type: str  # "none", "patch", "minor", "major", "unknown"


def get_stored_version(path: Path) -> str | None:
    """Get version stored in known-claims.md header."""
    if not path.exists():
        return None
    content = path.read_text()
    match = re.search(r"\*\*Claude Code version:\*\*\s*(\S+)", content)
    return match.group(1) if match else None


def check_version_status(cache_path: Path) -> VersionStatus:
    """Check if Claude Code version has changed since last verification."""
    current = get_claude_code_version()
    stored = get_stored_version(cache_path)

    if not current or not stored:
        return VersionStatus(current, stored, changed=True, change_type="unknown")

    cur_v = Version.parse(current)
    sto_v = Version.parse(stored)

    if not cur_v or not sto_v:
        return VersionStatus(current, stored, changed=True, change_type="unknown")

    if cur_v.major != sto_v.major:
        return VersionStatus(current, stored, changed=True, change_type="major")
    if cur_v.minor != sto_v.minor:
        return VersionStatus(current, stored, changed=True, change_type="minor")
    if cur_v.patch != sto_v.patch:
        return VersionStatus(current, stored, changed=False, change_type="patch")

    return VersionStatus(current, stored, changed=False, change_type="none")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class StaleClaim:
    """A claim that needs re-verification."""
    claim: str
    verdict: str
    evidence: str
    section: str
    verified_date: str
    days_since_verified: int
    line_number: int


@dataclass
class RefreshResult:
    """Result of refresh operation."""
    stale_claims: list[StaleClaim] = field(default_factory=list)
    updated_claims: list[str] = field(default_factory=list)
    total_claims: int = 0
    max_age_days: int = DEFAULT_MAX_AGE_DAYS
    version_status: VersionStatus | None = None


# =============================================================================
# PARSING
# =============================================================================

def parse_claims_with_dates(path: Path) -> list[dict]:
    """Parse known-claims.md with line numbers for updating."""
    content = path.read_text()
    claims: list[dict] = []
    current_section: str | None = None
    skip_sections = {"How to Use", "Maintenance"}

    for i, line in enumerate(content.splitlines()):
        # Track section headers
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name not in skip_sections:
                current_section = section_name
            else:
                current_section = None
            continue

        # Parse table rows: | Claim | Verdict | Evidence | Verified |
        if current_section and line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                claims.append({
                    "claim": parts[0].strip("`"),
                    "verdict": parts[1],
                    "evidence": parts[2],
                    "verified_date": parts[3],
                    "section": current_section,
                    "line_number": i,
                })

    return claims


def find_stale_claims(
    claims: list[dict],
    max_age_days: int,
    section: str | None = None,
) -> list[StaleClaim]:
    """Find claims older than max_age_days."""
    stale: list[StaleClaim] = []
    today = date.today()

    for claim in claims:
        # Apply section filter
        if section and claim.get("section") != section:
            continue

        verified_date = claim.get("verified_date", "")
        if not verified_date:
            continue

        # Use parse_verified_date to handle version-tagged dates like "2026-01-05 (v2.0.76)"
        verified = parse_verified_date(verified_date)
        if verified:
            days_ago = (today - verified).days

            if days_ago > max_age_days:
                stale.append(StaleClaim(
                    claim=claim["claim"],
                    verdict=claim["verdict"],
                    evidence=claim["evidence"],
                    section=claim["section"],
                    verified_date=verified_date,
                    days_since_verified=days_ago,
                    line_number=claim["line_number"],
                ))
        else:
            # Invalid date format, treat as stale
            stale.append(StaleClaim(
                claim=claim["claim"],
                verdict=claim["verdict"],
                evidence=claim["evidence"],
                section=claim["section"],
                verified_date=verified_date,
                days_since_verified=-1,  # Unknown age
                line_number=claim["line_number"],
            ))

    # Sort by age descending (oldest first)
    stale.sort(key=lambda c: c.days_since_verified, reverse=True)
    return stale


def update_claim_date(
    path: Path,
    claim_text: str,
    new_date: str | None = None,
) -> bool:
    """
    Update the verification date for a specific claim.

    Args:
        path: Path to known-claims.md
        claim_text: The claim text to find and update
        new_date: New date (ISO format), defaults to today

    Returns:
        True if claim was found and updated, False otherwise
    """
    if new_date is None:
        new_date = date.today().isoformat()

    content = path.read_text()
    lines = content.splitlines()
    updated = False
    claim_normalized = claim_text.strip("`").lower()

    for i, line in enumerate(lines):
        if not line.startswith("|") or line.startswith("| Claim") or line.startswith("|---"):
            continue

        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 4:
            line_claim = parts[0].strip("`").lower()
            if line_claim == claim_normalized:
                # Update the date column
                parts[3] = new_date
                lines[i] = "| " + " | ".join(parts) + " |"
                updated = True
                break

    if updated:
        path.write_text("\n".join(lines) + "\n")

    return updated


def update_all_claims_date(path: Path, new_date: str | None = None) -> int:
    """
    Update verification date for all claims.

    Use after bulk re-verification to mark all claims as freshly verified.

    Returns:
        Number of claims updated
    """
    if new_date is None:
        new_date = date.today().isoformat()

    content = path.read_text()
    lines = content.splitlines()
    updated_count = 0
    skip_sections = {"How to Use", "Maintenance"}
    current_section: str | None = None

    for i, line in enumerate(lines):
        # Track section headers
        if line.startswith("## "):
            section_name = line[3:].strip()
            current_section = None if section_name in skip_sections else section_name
            continue

        # Update table rows
        if current_section and line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                parts[3] = new_date
                lines[i] = "| " + " | ".join(parts) + " |"
                updated_count += 1

    # Also update header date
    for i, line in enumerate(lines):
        if line.startswith("**Last verified:**"):
            lines[i] = f"**Last verified:** {new_date}"
            break

    path.write_text("\n".join(lines) + "\n")
    return updated_count


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find and manage stale claims in known-claims.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List all stale claims (default TTL: 90 days)
    python refresh_claims.py

    # Filter by section
    python refresh_claims.py --section Hooks

    # Custom TTL threshold
    python refresh_claims.py --max-age 60

    # Update a single claim's date after re-verification
    python refresh_claims.py --update "Exit code 0 means success"

    # Mark all claims as freshly verified (after bulk re-verification)
    python refresh_claims.py --update-all

    # JSON output for pipeline integration
    python refresh_claims.py --json
        """,
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        metavar="DAYS",
        help=f"Maximum age in days before claim is stale (default: {DEFAULT_MAX_AGE_DAYS})",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Filter to a specific section",
    )
    parser.add_argument(
        "--update",
        type=str,
        metavar="CLAIM",
        help="Update verification date for a specific claim",
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="Update verification date for all claims",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics only",
    )
    parser.add_argument(
        "--version-aware",
        action="store_true",
        help="Check Claude Code version; flag all claims if version changed",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.cache.exists():
        print(f"Error: Cache file not found: {args.cache}", file=sys.stderr)
        return 1

    # Handle update operations
    if args.update:
        success = update_claim_date(args.cache, args.update)
        if args.json:
            print(json.dumps({"updated": success, "claim": args.update}))
        else:
            if success:
                print(f"✓ Updated verification date for: {args.update}")
            else:
                print(f"✗ Claim not found: {args.update}")
        return 0 if success else 1

    if args.update_all:
        count = update_all_claims_date(args.cache)
        if args.json:
            print(json.dumps({"updated_count": count}))
        else:
            print(f"✓ Updated verification date for {count} claims")
        return 0

    # Check version if requested
    version_status = None
    if args.version_aware:
        version_status = check_version_status(args.cache)

    # Find stale claims
    claims = parse_claims_with_dates(args.cache)
    stale = find_stale_claims(claims, args.max_age, args.section)

    result = RefreshResult(
        stale_claims=stale,
        total_claims=len(claims),
        max_age_days=args.max_age,
        version_status=version_status,
    )

    # Output
    if args.json:
        output = {
            "total_claims": result.total_claims,
            "stale_count": len(result.stale_claims),
            "max_age_days": result.max_age_days,
            "stale_claims": [asdict(c) for c in result.stale_claims],
        }
        if result.version_status:
            output["version_status"] = asdict(result.version_status)
        print(json.dumps(output, indent=2))
    elif args.summary:
        fresh_count = result.total_claims - len(result.stale_claims)
        stale_pct = (len(result.stale_claims) / result.total_claims * 100) if result.total_claims else 0
        print(f"Cache Health Report (TTL: {result.max_age_days} days)")

        # Version status (if checked)
        if result.version_status:
            vs = result.version_status
            print(f"\n  Version Check:")
            print(f"    Current: {vs.current or 'unknown'}")
            print(f"    Cached:  {vs.stored or 'unknown'}")
            if vs.changed:
                print(f"    ⚠️  {vs.change_type.upper()} version change - all claims need review!")
            else:
                print(f"    ✓ Version current ({vs.change_type})")

        print(f"\n  Claims:")
        print(f"    Total: {result.total_claims}")
        print(f"    Fresh: {fresh_count} ({100-stale_pct:.1f}%)")
        print(f"    Stale: {len(result.stale_claims)} ({stale_pct:.1f}%)")

        if result.stale_claims:
            # Group by section
            by_section: dict[str, int] = {}
            for c in result.stale_claims:
                by_section[c.section] = by_section.get(c.section, 0) + 1
            print("\n  Stale by section:")
            for sec, count in sorted(by_section.items(), key=lambda x: -x[1]):
                print(f"    {sec}: {count}")
    else:
        # Version status header (if checked)
        if result.version_status:
            vs = result.version_status
            print(f"Version: {vs.current or 'unknown'} (cached: {vs.stored or 'unknown'})")
            if vs.changed:
                print(f"⚠️  {vs.change_type.upper()} VERSION CHANGE - all claims need review!\n")
            else:
                print(f"✓ Version current\n")

        section_note = f" in {args.section}" if args.section else ""
        print(f"Stale claims{section_note} (older than {result.max_age_days} days)")
        print(f"Found: {len(result.stale_claims)} of {result.total_claims} total claims\n")

        if not result.stale_claims:
            if result.version_status and result.version_status.changed:
                print("No time-based stale claims, but version changed.")
                print("Consider re-verifying critical claims in affected areas.")
            else:
                print("No stale claims found. Cache is fresh!")
        else:
            for c in result.stale_claims:
                age_str = f"{c.days_since_verified}d ago" if c.days_since_verified >= 0 else "unknown age"
                print(f"⚠️  [{c.section}] {c.claim}")
                print(f"    Verdict: {c.verdict}")
                print(f"    Last verified: {c.verified_date} ({age_str})")
                print()

            print("To refresh these claims:")
            print("  1. Run /verify for each claim to re-verify")
            print("  2. Use --update <claim> to mark as refreshed")
            print("  3. Or use --update-all after bulk re-verification")

    # Exit code: 2 if version changed, 0 otherwise
    if result.version_status and result.version_status.changed:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
