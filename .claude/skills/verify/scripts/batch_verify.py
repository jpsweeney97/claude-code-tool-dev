#!/usr/bin/env python3
"""
Prepare batch verification of pending claims.

Groups pending claims by topic for efficient verification, outputs a verification
plan that Claude can execute via parallel claude-code-guide agents.

Exit codes:
    0: Success (verification plan generated or claims updated)
    1: Input error (file missing, parse error)
    10: No pending claims to verify

Usage:
    python batch_verify.py                    # Generate verification plan
    python batch_verify.py --section Hooks    # Filter to specific section
    python batch_verify.py --dry-run          # Preview plan only
    python batch_verify.py --update-verdict CLAIM VERDICT EVIDENCE  # Update a claim
    python batch_verify.py --interactive      # Review each claim before including
    python batch_verify.py --json             # JSON output for scripting
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path

# Import from common utilities
sys.path.insert(0, str(Path(__file__).parent))
from _common import atomic_write


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PendingClaim:
    """A claim awaiting verification."""
    claim: str
    verdict: str
    evidence: str
    section: str
    date: str
    line_number: int


@dataclass
class VerificationBatch:
    """A batch of claims to verify together."""
    section: str
    claims: list[PendingClaim] = field(default_factory=list)

    @property
    def query_prompt(self) -> str:
        """Generate a query prompt for claude-code-guide agent."""
        claims_list = "\n".join(f"- {c.claim}" for c in self.claims)
        return f"""Verify these {self.section} claims against official Claude Code documentation:

{claims_list}

For each claim, provide:
1. Verdict: ✓ Verified / ✗ Contradicted / ~ Partial / ? Unverified
2. Evidence: Quote from official docs or explanation
3. Source: Documentation URL if available"""


@dataclass
class BatchVerifyResult:
    """Result of batch verification preparation."""
    batches: list[VerificationBatch] = field(default_factory=list)
    total_claims: int = 0
    claims_by_section: dict[str, int] = field(default_factory=dict)
    updated_claims: list[str] = field(default_factory=list)


# =============================================================================
# INTERACTIVE MODE
# =============================================================================

def confirm_claim(claim: PendingClaim, index: int, total: int) -> str:
    """
    Prompt user to confirm, skip, or edit a claim verdict.

    Returns: 'confirm', 'skip', 'edit', or 'quit'
    """
    print(f"\n[{index}/{total}] Claim: {claim.claim}")
    print(f"  Section: {claim.section}")
    print(f"  Current verdict: {claim.verdict}")
    print(f"  Evidence: {claim.evidence[:100]}{'...' if len(claim.evidence) > 100 else ''}")

    while True:
        try:
            response = input("\n[c]onfirm, [s]kip, [e]dit verdict, [q]uit? ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted.")
            return "quit"
        if response in ("c", "confirm", ""):
            return "confirm"
        elif response in ("s", "skip"):
            return "skip"
        elif response in ("e", "edit"):
            return "edit"
        elif response in ("q", "quit"):
            return "quit"
        else:
            print("Invalid response. Use c/s/e/q")


def edit_claim_verdict(claim: PendingClaim) -> PendingClaim:
    """Prompt user to edit claim verdict and evidence."""
    print("\nEdit claim:")
    print("  Current verdict:", claim.verdict)

    try:
        new_verdict = input("  New verdict (verified/false/partial/unverified) [keep]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted. Keeping original values.")
        return claim
    if new_verdict and new_verdict in ("verified", "false", "partial", "unverified", "✓", "✗", "~", "?"):
        # Normalize to symbols
        verdict_map = {
            "verified": "✓ Verified",
            "false": "✗ Contradicted",
            "partial": "~ Partial",
            "unverified": "? Unverified",
        }
        claim.verdict = verdict_map.get(new_verdict, new_verdict)

    print("  Current evidence:", claim.evidence[:50] + "..." if len(claim.evidence) > 50 else claim.evidence)
    try:
        new_evidence = input("  New evidence [keep]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted. Keeping original values.")
        return claim
    if new_evidence:
        claim.evidence = new_evidence

    return claim


# =============================================================================
# PARSING
# =============================================================================

def parse_pending_claims(path: Path) -> list[PendingClaim]:
    """Parse pending-claims.md with line numbers."""
    if not path.exists():
        return []

    content = path.read_text()
    claims: list[PendingClaim] = []

    for i, line in enumerate(content.splitlines()):
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
                    line_number=i,
                ))

    return claims


def group_by_section(claims: list[PendingClaim]) -> list[VerificationBatch]:
    """Group claims into batches by section."""
    by_section: dict[str, list[PendingClaim]] = {}

    for claim in claims:
        section = claim.section or "General"
        if section not in by_section:
            by_section[section] = []
        by_section[section].append(claim)

    return [
        VerificationBatch(section=section, claims=claims)
        for section, claims in sorted(by_section.items())
    ]


# =============================================================================
# UPDATE OPERATIONS
# =============================================================================

def update_claim_verdict(
    path: Path,
    claim_text: str,
    new_verdict: str,
    new_evidence: str,
) -> bool:
    """
    Update verdict and evidence for a pending claim.

    Args:
        path: Path to pending-claims.md
        claim_text: The claim to update
        new_verdict: New verdict (✓ Verified, ✗ Contradicted, etc.)
        new_evidence: New evidence text

    Returns:
        True if claim was found and updated
    """
    if not path.exists():
        return False

    content = path.read_text()
    lines = content.splitlines()
    updated = False
    claim_normalized = claim_text.lower().strip()

    for i, line in enumerate(lines):
        if not line.startswith("|") or line.startswith("| Claim") or line.startswith("|---"):
            continue

        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 5:
            line_claim = parts[0].lower().strip()
            if line_claim == claim_normalized:
                # Update verdict and evidence, keep section and date
                parts[1] = new_verdict
                parts[2] = new_evidence
                parts[4] = date.today().isoformat()  # Update verification date
                lines[i] = "| " + " | ".join(parts) + " |"
                updated = True
                break

    if updated:
        atomic_write(path, "\n".join(lines) + "\n")

    return updated


def filter_unverified_only(claims: list[PendingClaim]) -> list[PendingClaim]:
    """Filter to only claims that need verification (? Captured or similar)."""
    return [c for c in claims if c.verdict.startswith("?")]


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare batch verification of pending claims",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
    1. Run batch_verify.py to generate verification plan
    2. Claude executes parallel claude-code-guide agents per batch
    3. Use --update-verdict to record results
    4. Use promote_claims.py to move verified claims to cache

Examples:
    # Generate verification plan (default)
    python batch_verify.py

    # Filter to specific section
    python batch_verify.py --section Hooks

    # Update a claim's verdict after verification
    python batch_verify.py --update-verdict "Exit code 2 blocks" "✓ Verified" "Official docs confirm"

    # Interactive review of each claim
    python batch_verify.py --interactive

    # JSON output for pipeline
    python batch_verify.py --json
        """,
    )
    parser.add_argument(
        "--pending",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "pending-claims.md",
        help="Path to pending-claims.md",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Filter to a specific section",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview plan without any actions",
    )
    parser.add_argument(
        "--update-verdict",
        nargs=3,
        metavar=("CLAIM", "VERDICT", "EVIDENCE"),
        help="Update verdict for a specific claim",
    )
    parser.add_argument(
        "--unverified-only",
        action="store_true",
        help="Only include claims with '?' verdict (not yet verified)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Confirm each claim interactively before including in batch",
    )
    args = parser.parse_args()

    # Handle update operation
    if args.update_verdict:
        claim, verdict, evidence = args.update_verdict

        if args.dry_run:
            print(f"[DRY RUN] Would update: {claim}")
            print(f"  Verdict: {verdict}")
            print(f"  Evidence: {evidence}")
            return 0

        success = update_claim_verdict(args.pending, claim, verdict, evidence)

        if args.json:
            print(json.dumps({
                "updated": success,
                "claim": claim,
                "verdict": verdict,
            }))
        else:
            if success:
                print(f"✓ Updated: {claim}")
                print(f"  Verdict: {verdict}")
            else:
                print(f"✗ Claim not found: {claim}")

        return 0 if success else 1

    # Validate inputs
    if not args.pending.exists():
        if args.json:
            print(json.dumps({"error": f"File not found: {args.pending}"}))
        else:
            print(f"Error: Pending file not found: {args.pending}", file=sys.stderr)
        return 1

    # Parse and group claims
    claims = parse_pending_claims(args.pending)

    if not claims:
        if args.json:
            print(json.dumps({"batches": [], "total_claims": 0}))
        else:
            print("No pending claims to verify.")
        return 10

    # Apply filters
    if args.section:
        claims = [c for c in claims if c.section == args.section]

    if args.unverified_only:
        claims = filter_unverified_only(claims)

    if not claims:
        if args.json:
            print(json.dumps({"batches": [], "total_claims": 0, "note": "All claims filtered out"}))
        else:
            filter_note = f" (section={args.section})" if args.section else ""
            print(f"No pending claims match filters{filter_note}.")
        return 10

    # Interactive mode: confirm each claim
    if args.interactive:
        if args.json:
            print(json.dumps({"error": "--interactive and --json are mutually exclusive"}))
            return 1

        confirmed_claims: list[PendingClaim] = []
        skipped_claims: list[PendingClaim] = []

        for i, claim in enumerate(claims, 1):
            action = confirm_claim(claim, i, len(claims))

            if action == "quit":
                print(f"\nQuitting. Processed {i-1}/{len(claims)} claims.")
                break
            elif action == "skip":
                skipped_claims.append(claim)
            elif action == "edit":
                edited = edit_claim_verdict(claim)
                confirmed_claims.append(edited)
            else:  # confirm
                confirmed_claims.append(claim)

        claims = confirmed_claims

        print(f"\nInteractive review complete:")
        print(f"  Confirmed: {len(confirmed_claims)}")
        print(f"  Skipped: {len(skipped_claims)}")

        if not claims:
            print("No claims to process after review.")
            return 10

    # Group into batches
    batches = group_by_section(claims)

    result = BatchVerifyResult(
        batches=batches,
        total_claims=len(claims),
        claims_by_section={b.section: len(b.claims) for b in batches},
    )

    # Output
    if args.json:
        output = {
            "total_claims": result.total_claims,
            "claims_by_section": result.claims_by_section,
            "batches": [
                {
                    "section": b.section,
                    "claim_count": len(b.claims),
                    "claims": [c.claim for c in b.claims],
                    "query_prompt": b.query_prompt,
                }
                for b in result.batches
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Batch Verification Plan")
        print(f"=======================")
        print(f"Total claims: {result.total_claims}")
        print(f"Batches: {len(result.batches)}")
        print()

        for batch in result.batches:
            print(f"## {batch.section} ({len(batch.claims)} claims)")
            print()
            for claim in batch.claims:
                print(f"  - {claim.claim}")
            print()
            print("Query for claude-code-guide agent:")
            print("---")
            print(batch.query_prompt)
            print("---")
            print()

        print("Next steps:")
        print("  1. Launch claude-code-guide agents for each batch")
        print("  2. Record results with: --update-verdict CLAIM VERDICT EVIDENCE")
        print("  3. Promote verified claims: python promote_claims.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
