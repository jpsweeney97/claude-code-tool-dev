#!/usr/bin/env python3
"""
Analyze documentation coverage in known-claims.md.

Identifies sections with few or no claims, helping prioritize
verification efforts.

Exit codes:
    0 - Good coverage (all sections meet threshold)
    1 - Input error
    2 - Sparse coverage detected
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from match_claim import parse_known_claims, discover_sections


# Known documentation sections that should have claims
KNOWN_SECTIONS = [
    "Skills",
    "Hooks",
    "Commands",
    "MCP",
    "Agents",
    "Settings",
    "CLI",
    "IDE",
    "Permissions",
    "Memory",
]


def analyze_coverage(
    known_path: Path,
    min_claims: int = 3,
) -> dict:
    """
    Analyze claim coverage across documentation sections.

    Args:
        known_path: Path to known-claims.md
        min_claims: Minimum claims for "adequate" coverage

    Returns:
        Dict with:
            total_claims: int
            sections: dict[str, {count, sparse, source_url}]
            missing_sections: list[str]
            coverage_score: float (0-1)
    """
    if not known_path.exists():
        return {
            "total_claims": 0,
            "sections": {},
            "missing_sections": KNOWN_SECTIONS.copy(),
            "coverage_score": 0.0,
        }

    claims = parse_known_claims(known_path)
    existing_sections = discover_sections(known_path)

    # Count claims per section
    section_counts: dict[str, int] = {}
    for claim in claims:
        section = claim["section"]
        section_counts[section] = section_counts.get(section, 0) + 1

    # Build section analysis
    sections = {}
    for section in existing_sections:
        count = section_counts.get(section, 0)
        sections[section] = {
            "count": count,
            "sparse": count < min_claims,
            "source_url": None,  # Could extract from file
        }

    # Find missing known sections
    missing = [s for s in KNOWN_SECTIONS if s not in existing_sections]

    # Calculate coverage score
    # Score = (sections with adequate claims) / (total known sections)
    adequate_sections = sum(1 for s in sections.values() if not s["sparse"])
    total_expected = len(KNOWN_SECTIONS)
    coverage_score = adequate_sections / total_expected if total_expected else 0.0

    return {
        "total_claims": len(claims),
        "sections": sections,
        "missing_sections": missing,
        "coverage_score": coverage_score,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze claim coverage")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        default=3,
        help="Minimum claims for adequate coverage (default: 3)",
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

    result = analyze_coverage(args.known_claims, args.min_claims)

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Coverage Analysis")
        print("=" * 40)
        print()
        print(f"Total claims: {result['total_claims']}")
        print(f"Coverage score: {result['coverage_score']:.0%}")
        print()

        # Sections with claims
        print(f"Sections (min {args.min_claims} claims for adequate):")
        for section, data in sorted(result["sections"].items(), key=lambda x: -x[1]["count"]):
            status = "SPARSE" if data["sparse"] else "ok"
            print(f"  [{status:6}] {section}: {data['count']} claims")

        # Missing sections
        if result["missing_sections"]:
            print()
            print("Missing sections (no claims):")
            for section in result["missing_sections"]:
                print(f"  [MISSING] {section}")

        print()
        if result["coverage_score"] < 0.7:
            print("Action: Add claims for sparse/missing sections")

    return 2 if result["coverage_score"] < 0.7 else 0


if __name__ == "__main__":
    sys.exit(main())
