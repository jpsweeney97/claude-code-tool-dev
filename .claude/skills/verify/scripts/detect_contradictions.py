#!/usr/bin/env python3
"""
Detect contradictory claims in known-claims.md.

Finds claims that logically conflict with each other:
- Same subject with opposite verdicts
- Antonym pairs (required/optional, blocks/non-blocking)
- Same claim text with different verdicts across sections

Different from duplicate detection (which finds similar claims).

Exit codes:
    0 - No contradictions found
    1 - Input error
    2 - Contradictions found
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from match_claim import parse_known_claims


# Type alias for claim dict
ClaimDict = dict[str, str | None]


# Antonym pairs that indicate contradiction
ANTONYM_PAIRS = [
    ("required", "optional"),
    ("required", "not required"),
    ("blocks", "non-blocking"),
    ("blocks", "does not block"),
    ("blocking", "non-blocking"),
    ("must", "may"),
    ("always", "never"),
    ("enabled", "disabled"),
    ("default", "not default"),
    ("supported", "not supported"),
    ("allowed", "not allowed"),
    ("mandatory", "optional"),
]


@dataclass
class Contradiction:
    """A pair of contradictory claims."""
    claim1: ClaimDict
    claim2: ClaimDict
    reason: str
    severity: str  # HIGH, MEDIUM, LOW


def normalize_claim_text(text: str) -> str:
    """Normalize claim text for comparison."""
    # Lowercase
    text = text.lower()
    # Remove backticks and quotes
    text = re.sub(r"[`'\"]", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def extract_subject(claim: str) -> str | None:
    """
    Extract the subject of a claim.

    Examples:
        "exit code 2 blocks" -> "exit code 2"
        "`name` field is required" -> "name field"
        "description field is optional" -> "description field"
    """
    claim = normalize_claim_text(claim)

    # Pattern: <subject> is/are/means/blocks/...
    patterns = [
        r"^(.+?)\s+(?:is|are|means|blocks|does|must|may|can|cannot|should)\b",
        r"^(.+?)\s+(?:field|option|setting|parameter|flag)\s+(?:is|are)\b",
    ]

    for pattern in patterns:
        match = re.match(pattern, claim)
        if match:
            return match.group(1).strip()

    # Fallback: first few significant words
    words = claim.split()[:4]
    return " ".join(words)


def has_opposite_verdict(verdict1: str, verdict2: str) -> bool:
    """Check if two verdicts are logically opposite."""
    v1 = verdict1.lower()
    v2 = verdict2.lower()

    # Verified vs False/Contradicted
    verified_indicators = ["verified", "✓"]
    false_indicators = ["false", "contradicted", "✗"]

    v1_verified = any(ind in v1 for ind in verified_indicators)
    v1_false = any(ind in v1 for ind in false_indicators)
    v2_verified = any(ind in v2 for ind in verified_indicators)
    v2_false = any(ind in v2 for ind in false_indicators)

    return (v1_verified and v2_false) or (v1_false and v2_verified)


def has_antonym_pair(claim1: str, claim2: str) -> tuple[bool, str | None]:
    """
    Check if two claims contain antonym pairs about the same subject.

    Returns:
        Tuple of (has_antonym, antonym_pair_description)
    """
    c1 = normalize_claim_text(claim1)
    c2 = normalize_claim_text(claim2)

    for word1, word2 in ANTONYM_PAIRS:
        if word1 in c1 and word2 in c2:
            return True, f"{word1} vs {word2}"
        if word2 in c1 and word1 in c2:
            return True, f"{word2} vs {word1}"

    return False, None


def find_contradictions(
    known_path: Path,
    same_section_only: bool = False,
    include_partial: bool = False,
) -> list[Contradiction]:
    """
    Find contradictory claims in the cache.

    Args:
        known_path: Path to known-claims.md
        same_section_only: Only check within same section
        include_partial: Include partial verdict contradictions

    Returns:
        List of Contradiction objects
    """
    if not known_path.exists():
        return []

    claims = parse_known_claims(known_path)
    if len(claims) < 2:
        return []

    contradictions: list[Contradiction] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i, c1 in enumerate(claims):
        for c2 in claims[i + 1:]:
            # Skip if same section restriction and sections differ
            if same_section_only and c1["section"] != c2["section"]:
                continue

            # Create consistent pair key to avoid duplicates
            pair_key = tuple(sorted([c1["claim"], c2["claim"]]))
            if pair_key in seen_pairs:
                continue

            # Extract subjects
            subj1 = extract_subject(c1["claim"])
            subj2 = extract_subject(c2["claim"])

            # Skip if subjects are too different
            if subj1 and subj2:
                # Check for significant subject overlap
                words1 = set(subj1.split())
                words2 = set(subj2.split())
                overlap = len(words1 & words2)
                if overlap < 2 and subj1 != subj2:
                    continue

            contradiction = None

            # Check 1: Same claim text (or very similar), different verdicts
            if normalize_claim_text(c1["claim"]) == normalize_claim_text(c2["claim"]):
                if has_opposite_verdict(c1["verdict"], c2["verdict"]):
                    contradiction = Contradiction(
                        claim1=c1,
                        claim2=c2,
                        reason="Same claim, opposite verdicts",
                        severity="HIGH",
                    )

            # Check 2: Antonym pairs with same/similar subject
            if not contradiction:
                has_antonym, antonym_desc = has_antonym_pair(c1["claim"], c2["claim"])
                if has_antonym:
                    # Both should be verified for this to be a true contradiction
                    v1_verified = "verified" in c1["verdict"].lower() or "✓" in c1["verdict"]
                    v2_verified = "verified" in c2["verdict"].lower() or "✓" in c2["verdict"]

                    if v1_verified and v2_verified:
                        contradiction = Contradiction(
                            claim1=c1,
                            claim2=c2,
                            reason=f"Antonym pair: {antonym_desc}",
                            severity="HIGH" if c1["section"] == c2["section"] else "MEDIUM",
                        )

            # Check 3: Similar subject, one verified, one false
            if not contradiction and subj1 == subj2:
                if has_opposite_verdict(c1["verdict"], c2["verdict"]):
                    contradiction = Contradiction(
                        claim1=c1,
                        claim2=c2,
                        reason="Same subject, opposite verdicts",
                        severity="MEDIUM",
                    )

            if contradiction:
                seen_pairs.add(pair_key)
                contradictions.append(contradiction)

    # Sort by severity (HIGH first)
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    contradictions.sort(key=lambda c: severity_order.get(c.severity, 3))

    return contradictions


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect contradictory claims")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--same-section",
        action="store_true",
        help="Only check within same section",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    contradictions = find_contradictions(
        args.known_claims,
        same_section_only=args.same_section,
    )

    if args.json:
        import json
        output = [
            {
                "severity": c.severity,
                "reason": c.reason,
                "claim1": {
                    "claim": c.claim1["claim"],
                    "section": c.claim1["section"],
                    "verdict": c.claim1["verdict"],
                },
                "claim2": {
                    "claim": c.claim2["claim"],
                    "section": c.claim2["section"],
                    "verdict": c.claim2["verdict"],
                },
            }
            for c in contradictions
        ]
        print(json.dumps(output, indent=2))
    else:
        if not contradictions:
            print("No contradictions found.")
            return 0

        print(f"Found {len(contradictions)} contradiction(s):\n")

        for i, c in enumerate(contradictions, 1):
            severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(c.severity, "⚪")
            print(f"{severity_icon} Contradiction {i}: {c.reason}")
            print(f"   [{c.claim1['section']}] {c.claim1['claim']}")
            print(f"      Verdict: {c.claim1['verdict']}")
            print(f"   [{c.claim2['section']}] {c.claim2['claim']}")
            print(f"      Verdict: {c.claim2['verdict']}")
            print()

        print("Action: Review and resolve conflicting claims")

    return 2 if contradictions else 0


if __name__ == "__main__":
    sys.exit(main())
