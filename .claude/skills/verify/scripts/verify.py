#!/usr/bin/env python3
"""
Unified entry point for the verify skill.

Routes to appropriate verification functionality based on input:
- Claim text → check against cache
- File path → document mode (extract and verify claims)
- Flags → maintenance operations (refresh, promote, health, batch)

Exit codes:
    0: Success / match found
    1: Input error / confirm needed
    2: Version change detected (with --health)
    10: No match / nothing to do

Usage:
    python verify.py "Skills require a license"     # Check single claim
    python verify.py /path/to/doc.md                # Document mode
    python verify.py --quick "exit code"            # Cache-only (no agent)
    python verify.py --health                       # Cache health check
    python verify.py --refresh                      # List stale claims
    python verify.py --promote                      # Promote pending claims
    python verify.py --batch                        # Batch verify pending

Examples:
    # Quick cache check (fastest, no external queries)
    python verify.py --quick "hooks use exit code 2 to block"

    # Full verification with freshness info
    python verify.py "frontmatter required" --check-freshness

    # Health check before starting work
    python verify.py --health

    # Maintenance: find and refresh stale claims
    python verify.py --refresh --section Hooks

    # Promote verified claims to permanent cache
    python verify.py --promote --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import from common utilities
from _common import DEFAULT_MAX_AGE_DAYS

# Import from sibling scripts
from match_claim import (
    parse_known_claims,
    find_best_match,
    find_top_matches,
    discover_sections,
    normalize_section,
    list_sections,
    THRESHOLD_HIGH,
    THRESHOLD_MEDIUM,
    THRESHOLD_LOW,
)
from refresh_claims import (
    parse_claims_with_dates,
    find_stale_claims,
    check_version_status,
    RefreshResult,
)
from promote_claims import (
    parse_pending_claims,
    promote_claims,
    PromotionResult,
)
from validate_sources import validate_sources, ValidationResult
from backup_cache import create_backup, list_backups, restore_backup


# =============================================================================
# QUICK-ADD INFERENCE
# =============================================================================

def infer_section(claim: str) -> str:
    """Infer section from claim keywords."""
    claim_lower = claim.lower()

    # Check for specific keywords
    section_keywords = {
        "Hooks": ["hook", "exit code", "pretooluse", "posttooluse", "timeout", "matcher"],
        "Skills": ["skill", "frontmatter", "allowed-tools", "skill.md"],
        "Commands": ["command", "$arguments", "slash", "argument-hint"],
        "MCP": ["mcp", ".mcp.json", "server", "mcpservers"],
        "Agents": ["agent", "task tool", "subagent", "subagent_type"],
        "Settings": ["setting", "permissions", "settings.json"],
        "CLI": ["cli", "flag", "--", "environment variable"],
    }

    for section, keywords in section_keywords.items():
        if any(kw in claim_lower for kw in keywords):
            return section

    return "General"


def infer_severity(claim: str) -> str:
    """Infer severity from claim keywords."""
    claim_lower = claim.lower()

    # Critical indicators
    if any(kw in claim_lower for kw in ["exit code", "required", "must", "block", "error"]):
        return "CRITICAL"

    # High indicators
    if any(kw in claim_lower for kw in ["default", "limit", "max", "min", "timeout"]):
        return "HIGH"

    return "LOW"


# =============================================================================
# CACHE STATISTICS
# =============================================================================

def calculate_cache_stats(known_path: Path, max_age_days: int = 90) -> dict:
    """
    Calculate comprehensive cache statistics.

    Returns dict with:
        total: int
        by_section: dict[str, int]
        by_verdict: dict[str, int]  # verified, false, partial, unverified
        by_age: dict[str, int]  # fresh (<30d), aging (30-90d), stale (>90d)
        oldest_claim: str | None
        newest_claim: str | None
    """
    from datetime import date as date_module
    from _common import parse_verified_date

    if not known_path.exists():
        return {
            "total": 0,
            "by_section": {},
            "by_verdict": {},
            "by_age": {"fresh": 0, "aging": 0, "stale": 0},
            "oldest_claim": None,
            "newest_claim": None,
        }

    claims = parse_known_claims(known_path)
    today = date_module.today()

    stats = {
        "total": len(claims),
        "by_section": {},
        "by_verdict": {"verified": 0, "false": 0, "partial": 0, "unverified": 0},
        "by_age": {"fresh": 0, "aging": 0, "stale": 0},
        "oldest_claim": None,
        "newest_claim": None,
    }

    oldest_date = None
    newest_date = None

    for claim in claims:
        # Count by section
        section = claim.get("section") or "Unknown"
        stats["by_section"][section] = stats["by_section"].get(section, 0) + 1

        # Count by verdict
        verdict_str = claim.get("verdict", "").lower()
        if "verified" in verdict_str and "unverified" not in verdict_str:
            stats["by_verdict"]["verified"] += 1
        elif "false" in verdict_str or "contradicted" in verdict_str:
            stats["by_verdict"]["false"] += 1
        elif "partial" in verdict_str:
            stats["by_verdict"]["partial"] += 1
        else:
            stats["by_verdict"]["unverified"] += 1

        # Count by age
        verified_date = parse_verified_date(claim.get("verified_date"))
        if verified_date:
            age_days = (today - verified_date).days
            if age_days < 30:
                stats["by_age"]["fresh"] += 1
            elif age_days < max_age_days:
                stats["by_age"]["aging"] += 1
            else:
                stats["by_age"]["stale"] += 1

            # Track oldest/newest
            if oldest_date is None or verified_date < oldest_date:
                oldest_date = verified_date
                stats["oldest_claim"] = claim.get("claim")
            if newest_date is None or verified_date > newest_date:
                newest_date = verified_date
                stats["newest_claim"] = claim.get("claim")

    return stats


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

SKILL_ROOT = Path(__file__).parent.parent
REFERENCES_DIR = SKILL_ROOT / "references"
KNOWN_CLAIMS_PATH = REFERENCES_DIR / "known-claims.md"
PENDING_CLAIMS_PATH = REFERENCES_DIR / "pending-claims.md"


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

def cmd_check(args: argparse.Namespace) -> int:
    """Check a claim against the cache."""
    if not KNOWN_CLAIMS_PATH.exists():
        print(f"Error: Cache not found: {KNOWN_CLAIMS_PATH}", file=sys.stderr)
        return 1

    claims = parse_known_claims(KNOWN_CLAIMS_PATH)
    valid_sections = discover_sections(KNOWN_CLAIMS_PATH)

    # Normalize section if provided
    section = args.section
    if section:
        normalized = normalize_section(section, valid_sections)
        if normalized is None:
            print(f"Error: Unknown section '{section}'", file=sys.stderr)
            print(f"Available: {', '.join(sorted(valid_sections))}", file=sys.stderr)
            return 1
        section = normalized

    # Quick mode: cache-only, return immediately
    if args.quick:
        result = find_best_match(
            args.input,
            claims,
            threshold=THRESHOLD_HIGH,
            section=section,
            max_age_days=args.max_age,
        )
        if result.matched:
            stale = " ⚠️ STALE" if result.is_stale else ""
            severity = f" [{result.severity}]" if result.severity else ""
            print(f"✓ CACHED{stale}: {result.verdict}{severity}")
            print(f"  {result.known_claim}")
            print(f"  Evidence: {result.evidence}")
            if result.source_url:
                print(f"  Source: {result.source_url}")
            if args.check_freshness and result.verified_date:
                age = f"{result.days_since_verified}d ago" if result.days_since_verified else "?"
                print(f"  Verified: {result.verified_date} ({age})")
            return 0
        else:
            print(f"✗ NOT IN CACHE (best score: {result.confidence:.2f})")
            print("  Use without --quick to query documentation.")
            return 10

    # Standard mode: tiered response
    top_results = find_top_matches(
        args.input,
        claims,
        top_n=3,
        threshold=THRESHOLD_LOW,
        section=section,
        max_age_days=args.max_age,
    )

    best = top_results.matches[0] if top_results.matches else None
    score = best.confidence if best else 0.0

    if score >= THRESHOLD_HIGH:
        stale = " ⚠️ STALE" if best.is_stale else ""
        severity = f" [{best.severity}]" if best.severity else ""
        print(f"✓ HIGH CONFIDENCE ({score:.2f}){stale}")
        print(f"  {best.verdict}{severity}: {best.known_claim}")
        print(f"  Evidence: {best.evidence}")
        if best.source_url:
            print(f"  Source: {best.source_url}")
        print(f"  Section: {best.section}")
        if args.check_freshness and best.verified_date:
            age = f"{best.days_since_verified}d ago" if best.days_since_verified else "?"
            print(f"  Verified: {best.verified_date} ({age})")
        return 0

    elif score >= THRESHOLD_MEDIUM:
        print(f"? CONFIRM NEEDED ({score:.2f}) - Multiple candidates:")
        for i, m in enumerate(top_results.matches, 1):
            marker = "→" if i == 1 else " "
            stale = " ⚠️ STALE" if m.is_stale else ""
            severity = f" [{m.severity}]" if m.severity else ""
            print(f"  {marker} {i}. [{m.confidence:.3f}]{stale} {m.verdict}{severity}")
            print(f"       {m.known_claim}")
        print("\n  Query documentation to confirm.")
        return 1

    else:
        print(f"✗ NO MATCH (best: {score:.2f})")
        if top_results.matches:
            print(f"  Closest: {top_results.matches[0].known_claim}")
        print("  Query documentation for verification.")
        return 10


def cmd_health(args: argparse.Namespace) -> int:
    """Check cache health."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found. Nothing to check.")
        return 0

    # Version check
    version_status = check_version_status(KNOWN_CLAIMS_PATH)

    # Staleness check
    claims = parse_claims_with_dates(KNOWN_CLAIMS_PATH)
    stale = find_stale_claims(claims, args.max_age)

    total = len(claims)
    stale_count = len(stale)
    stale_pct = (stale_count / total * 100) if total else 0

    print(f"Cache Health Report (TTL: {args.max_age} days)")
    print()

    # Version status
    vs = version_status
    print("Version:")
    print(f"  Current: {vs.current or 'unknown'}")
    print(f"  Cached:  {vs.stored or 'unknown'}")
    if vs.changed:
        print(f"  ⚠️  {vs.change_type.upper()} version change!")
    else:
        print(f"  ✓ Current")
    print()

    # Claims summary
    print("Claims:")
    print(f"  Total: {total}")
    print(f"  Fresh: {total - stale_count} ({100 - stale_pct:.1f}%)")
    print(f"  Stale: {stale_count} ({stale_pct:.1f}%)")

    if stale:
        print()
        print("Stale by section:")
        by_section: dict[str, int] = {}
        for c in stale:
            by_section[c.section] = by_section.get(c.section, 0) + 1
        for sec, count in sorted(by_section.items(), key=lambda x: -x[1]):
            print(f"  {sec}: {count}")

    # Pending claims
    pending = parse_pending_claims(PENDING_CLAIMS_PATH)
    if pending:
        print()
        print(f"Pending: {len(pending)} claims awaiting promotion")
        print("  Run: python verify.py --promote")

    return 2 if vs.changed else 0


def cmd_refresh(args: argparse.Namespace) -> int:
    """List stale claims."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    claims = parse_claims_with_dates(KNOWN_CLAIMS_PATH)

    # Normalize section if provided
    section = args.section
    if section:
        valid_sections = discover_sections(KNOWN_CLAIMS_PATH)
        normalized = normalize_section(section, valid_sections)
        if normalized is None:
            print(f"Error: Unknown section '{section}'", file=sys.stderr)
            return 1
        section = normalized

    stale = find_stale_claims(claims, args.max_age, section)

    section_note = f" in {section}" if section else ""
    print(f"Stale claims{section_note} (>{args.max_age} days)")
    print(f"Found: {len(stale)} of {len(claims)} total")
    print()

    if not stale:
        print("✓ All claims are fresh!")
        return 0

    for c in stale:
        age = f"{c.days_since_verified}d ago" if c.days_since_verified >= 0 else "unknown"
        print(f"⚠️  [{c.section}] {c.claim}")
        print(f"    {c.verdict} | Last: {c.verified_date} ({age})")
        print()

    print("To refresh: re-verify each claim, then update date with:")
    print("  python scripts/refresh_claims.py --update \"claim text\"")

    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    """Promote pending claims to known cache."""
    if not PENDING_CLAIMS_PATH.exists():
        print("No pending claims file found.")
        return 1

    if not KNOWN_CLAIMS_PATH.exists():
        print("No known claims file found.")
        return 1

    result = promote_claims(
        PENDING_CLAIMS_PATH,
        KNOWN_CLAIMS_PATH,
        dry_run=args.dry_run,
        interactive=args.interactive,
        record_version=not args.no_version,
    )

    mode = "[DRY RUN] " if args.dry_run else ""

    if result.normalized_sections:
        print(f"Normalized {len(result.normalized_sections)} section(s):")
        for orig, norm in result.normalized_sections:
            print(f"  ~ '{orig}' → '{norm}'")
        print()

    if result.promoted:
        print(f"{mode}Promoted {len(result.promoted)} claim(s):")
        for c in result.promoted:
            print(f"  ✓ [{c.section}] {c.claim}")

    if result.skipped_duplicates:
        print(f"\nSkipped {len(result.skipped_duplicates)} duplicate(s):")
        for c in result.skipped_duplicates:
            print(f"  ⊘ [{c.section}] {c.claim}")

    if not result.promoted and not result.skipped_duplicates:
        print("No pending claims to promote.")
        return 10

    return 0


def cmd_sections(args: argparse.Namespace) -> int:
    """List available sections."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    claims = parse_known_claims(KNOWN_CLAIMS_PATH)
    sections = list_sections(claims)

    print("Available sections:")
    for sec, count in sorted(sections.items()):
        print(f"  {sec}: {count} claims")

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Display comprehensive cache statistics."""
    if not KNOWN_CLAIMS_PATH.exists():
        print("No cache file found.")
        return 1

    stats = calculate_cache_stats(KNOWN_CLAIMS_PATH, args.max_age)

    print("Cache Statistics")
    print("=" * 40)
    print()

    # Total
    print(f"Total claims: {stats['total']}")
    print()

    # By verdict
    print("By verdict:")
    for verdict, count in sorted(stats["by_verdict"].items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count / stats["total"] * 100 if stats["total"] else 0
            print(f"  {verdict.capitalize():12} {count:3} ({pct:4.1f}%)")
    print()

    # By section
    print("By section:")
    for section, count in sorted(stats["by_section"].items(), key=lambda x: -x[1]):
        print(f"  {section:12} {count:3}")
    print()

    # By age
    print(f"By age (TTL: {args.max_age}d):")
    labels = {
        "fresh": "Fresh (<30d)",
        "aging": f"Aging (30-{args.max_age}d)",
        "stale": f"Stale (>{args.max_age}d)",
    }
    for age_bucket in ["fresh", "aging", "stale"]:
        count = stats["by_age"][age_bucket]
        pct = count / stats["total"] * 100 if stats["total"] else 0
        print(f"  {labels[age_bucket]:20} {count:3} ({pct:4.1f}%)")

    return 0


def cmd_add(args: argparse.Namespace) -> int:
    """Add a verified claim to pending-claims.md for later promotion."""
    from datetime import date as date_module

    # Validate required args
    if not args.claim:
        print("Error: --claim is required", file=sys.stderr)
        return 1
    if not args.verdict:
        print("Error: --verdict is required", file=sys.stderr)
        return 1
    if not args.evidence:
        print("Error: --evidence is required", file=sys.stderr)
        return 1

    # Handle quick-add: infer missing fields
    if args.quick_add:
        if not args.add_section:
            args.add_section = infer_section(args.claim)
            print(f"Inferred section: {args.add_section}")

        if not args.severity:
            args.severity = infer_severity(args.claim)
            print(f"Inferred severity: {args.severity}")

    # Validate section (now required after potential inference)
    if not args.add_section:
        print("Error: --add-section is required (or use --quick-add)", file=sys.stderr)
        return 1

    # Validate verdict format
    valid_verdicts = {"✓ Verified", "✗ False", "✗ Contradicted", "~ Partial", "? Unverified"}
    verdict_aliases = {
        "verified": "✓ Verified",
        "true": "✓ Verified",
        "false": "✗ False",
        "contradicted": "✗ Contradicted",
        "partial": "~ Partial",
        "unverified": "? Unverified",
    }
    verdict = verdict_aliases.get(args.verdict.lower(), args.verdict)
    if verdict not in valid_verdicts:
        print(f"Error: Invalid verdict '{args.verdict}'", file=sys.stderr)
        print(f"Valid: {', '.join(sorted(valid_verdicts))}", file=sys.stderr)
        return 1

    # Build row
    today = date_module.today().isoformat()
    verdict_col = verdict
    if args.severity:
        verdict_col = f"{verdict} [{args.severity}]"
    evidence_col = args.evidence
    if args.source:
        evidence_col = f"{args.evidence} ({args.source})"
    row = f"| {args.claim} | {verdict_col} | {evidence_col} | {args.add_section} | {today} |"

    # Check for duplicate in pending
    if PENDING_CLAIMS_PATH.exists():
        content = PENDING_CLAIMS_PATH.read_text()
        claim_lower = args.claim.lower()
        for line in content.splitlines():
            if line.startswith("|") and claim_lower in line.lower():
                print(f"⚠️  Similar claim already in pending: {line.strip()}")
                if not args.force:
                    print("Use --force to add anyway.")
                    return 1

    # Append to pending-claims.md
    if args.dry_run:
        print(f"[DRY RUN] Would add to pending-claims.md:")
        print(f"  {row}")
        return 0

    # Read existing content
    if PENDING_CLAIMS_PATH.exists():
        content = PENDING_CLAIMS_PATH.read_text(encoding="utf-8")
    else:
        content = "# Pending Claims\n\n| Claim | Verdict | Evidence | Section | Date |\n|-------|---------|----------|---------|------|\n"

    # Append row and use atomic write
    from _common import atomic_write
    content = content.rstrip() + "\n" + row + "\n"
    atomic_write(PENDING_CLAIMS_PATH, content)

    print(f"✓ Added to pending-claims.md:")
    print(f"  [{args.add_section}] {args.claim}")
    print(f"  Verdict: {verdict}")
    print(f"\nRun: python verify.py --promote")

    return 0


def cmd_validate_urls(args: argparse.Namespace) -> int:
    """Validate source documentation URLs."""
    if not KNOWN_CLAIMS_PATH.exists():
        print(f"Error: Cache not found: {KNOWN_CLAIMS_PATH}", file=sys.stderr)
        return 1

    print("Validating source URLs (this may take a moment)...")
    print()

    result = validate_sources(
        KNOWN_CLAIMS_PATH,
        timeout=10,
        rate_limit=1.0,
        section_filter=args.section,
    )

    # Display results
    section_note = f" for {args.section}" if args.section else ""
    print(f"Source URL Validation{section_note}")
    print("=" * 40)

    if result.valid:
        print(f"\n[ok] Valid ({len(result.valid)}):")
        for r in result.valid:
            print(f"    {r.section}: {r.url}")

    if result.invalid:
        print(f"\n[!] Invalid ({len(result.invalid)}):")
        for r in result.invalid:
            status = r.status or "unreachable"
            print(f"    {r.section}: {r.url}")
            print(f"      -> {status}: {r.error}")

    if result.skipped:
        print(f"\n[-] Skipped ({len(result.skipped)}):")
        for s in result.skipped:
            print(f"    {s}")

    print()
    print(f"Summary: {len(result.valid)} valid, {len(result.invalid)} invalid, {len(result.skipped)} skipped")

    if result.invalid:
        print("\nAction: Review claims in sections with broken URLs")
        return 2

    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    """Create backup of known-claims cache."""
    backup_path = create_backup(KNOWN_CLAIMS_PATH)
    if backup_path:
        print(f"Created backup: {backup_path.name}")
        return 0
    else:
        print("Error: No cache to backup", file=sys.stderr)
        return 1


def cmd_list_backups(args: argparse.Namespace) -> int:
    """List available backups."""
    backups = list_backups()
    if not backups:
        print("No backups found")
        return 0

    print("Available backups:")
    for i, b in enumerate(backups):
        timestamp = b.stem.replace("known-claims_", "")
        size = b.stat().st_size
        marker = " (latest)" if i == 0 else ""
        print(f"  {i+1}. {timestamp} ({size:,} bytes){marker}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    """Restore cache from backup."""
    backups = list_backups()

    if not backups:
        print("No backups available", file=sys.stderr)
        return 10

    if args.restore == "latest":
        backup_path = backups[0]
    else:
        # Find matching backup
        backup_path = None
        for b in backups:
            if args.restore in str(b):
                backup_path = b
                break
        if not backup_path:
            print(f"Backup not found: {args.restore}", file=sys.stderr)
            return 1

    if args.dry_run:
        print(f"[DRY RUN] Would restore from: {backup_path.name}")
        return 0

    if restore_backup(backup_path, KNOWN_CLAIMS_PATH):
        print(f"Restored from: {backup_path.name}")
        return 0
    else:
        print("Restore failed", file=sys.stderr)
        return 1


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified verify skill CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
    verify.py "claim"           Check claim against cache
    verify.py --quick "claim"   Cache-only check (no agent query)
    verify.py --health          Cache health summary
    verify.py --stats           Comprehensive cache statistics
    verify.py --refresh         List stale claims
    verify.py --promote         Promote pending to known cache
    verify.py --sections        List available sections

Examples:
    # Quick cache lookup
    python verify.py --quick "exit code 0 means success"

    # Full check with freshness info
    python verify.py "frontmatter required" --check-freshness

    # Check hooks section only
    python verify.py "timeout" --section Hooks

    # Daily maintenance
    python verify.py --health
    python verify.py --refresh
    python verify.py --promote --dry-run
        """,
    )

    # Input (positional, optional for flag modes)
    parser.add_argument(
        "input",
        nargs="?",
        help="Claim text to verify",
    )

    # Mode flags (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--health",
        action="store_true",
        help="Show cache health summary",
    )
    mode_group.add_argument(
        "--refresh",
        action="store_true",
        help="List stale claims needing re-verification",
    )
    mode_group.add_argument(
        "--promote",
        action="store_true",
        help="Promote pending claims to known cache",
    )
    mode_group.add_argument(
        "--sections",
        action="store_true",
        help="List available sections",
    )
    mode_group.add_argument(
        "--stats",
        action="store_true",
        help="Display comprehensive cache statistics",
    )
    mode_group.add_argument(
        "--add",
        action="store_true",
        help="Add a verified claim to pending-claims.md",
    )
    mode_group.add_argument(
        "--validate-urls",
        action="store_true",
        help="Validate source documentation URLs",
    )
    mode_group.add_argument(
        "--backup",
        action="store_true",
        help="Create backup of known-claims cache",
    )
    mode_group.add_argument(
        "--restore",
        nargs="?",
        const="latest",
        metavar="BACKUP",
        help="Restore cache from backup (latest if no argument)",
    )
    mode_group.add_argument(
        "--list-backups",
        action="store_true",
        help="List available backups",
    )

    # Check options
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Cache-only check (high confidence threshold, no agent)",
    )
    parser.add_argument(
        "--section",
        type=str,
        help="Filter to specific section",
    )
    parser.add_argument(
        "--check-freshness",
        action="store_true",
        help="Show verification dates and staleness",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        metavar="DAYS",
        help=f"Staleness threshold (default: {DEFAULT_MAX_AGE_DAYS})",
    )

    # Promote options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Confirm each claim before promoting",
    )
    parser.add_argument(
        "--no-version",
        action="store_true",
        help="Don't record Claude Code version in dates",
    )

    # Add claim options (for --add mode)
    parser.add_argument(
        "--claim",
        type=str,
        help="Claim text to add (with --add)",
    )
    parser.add_argument(
        "--verdict",
        type=str,
        help="Verdict: verified, false, contradicted, partial, unverified (with --add)",
    )
    parser.add_argument(
        "--evidence",
        type=str,
        help="Evidence/quote supporting the verdict (with --add)",
    )
    parser.add_argument(
        "--add-section",
        type=str,
        help="Section for the claim: Skills, Hooks, Commands, MCP, etc. (with --add)",
    )
    parser.add_argument(
        "--severity",
        type=str,
        choices=["CRITICAL", "HIGH", "LOW"],
        help="Claim severity: CRITICAL (breaks things), HIGH (behavior), LOW (guidance)",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Source URL for the claim (with --add)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force add even if similar claim exists (with --add)",
    )
    parser.add_argument(
        "--quick-add",
        action="store_true",
        help="Quick add with smart defaults (infers section and severity)",
    )

    args = parser.parse_args()

    # Route to appropriate handler
    if args.backup:
        return cmd_backup(args)
    elif args.list_backups:
        return cmd_list_backups(args)
    elif args.restore:
        return cmd_restore(args)
    elif args.validate_urls:
        return cmd_validate_urls(args)
    elif args.health:
        return cmd_health(args)
    elif args.refresh:
        return cmd_refresh(args)
    elif args.promote:
        return cmd_promote(args)
    elif args.sections:
        return cmd_sections(args)
    elif args.stats:
        return cmd_stats(args)
    elif args.add:
        return cmd_add(args)
    elif args.input:
        return cmd_check(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
