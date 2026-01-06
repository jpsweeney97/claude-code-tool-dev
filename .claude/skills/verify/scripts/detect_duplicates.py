#!/usr/bin/env python3
"""
Detect duplicate or near-duplicate claims in known-claims.md.

Uses fuzzy matching to find claims that are semantically similar,
which may indicate redundancy or inconsistency.

Exit codes:
    0 - No duplicates found
    1 - Input error
    2 - Duplicates found
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import from sibling modules
from match_claim import parse_known_claims


# =============================================================================
# SIMILARITY CALCULATION
# =============================================================================

# Stopwords to ignore in similarity calculation
STOPWORDS: set[str] = {
    "the", "a", "an", "is", "are", "in", "to", "for", "of", "and", "or",
    "it", "be", "has", "have", "was", "were", "been", "being", "this", "that",
    "with", "as", "at", "by", "on", "from", "can", "only", "all", "uses",
    "use", "using", "support", "supports", "does", "do", "means", "indicates",
}


def calculate_duplicate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two strings using word overlap.

    Uses Jaccard similarity on normalized word sets.
    Simpler than match_claim's weighted algorithm since we're comparing
    claims to each other, not queries to claims.
    """
    # Normalize: lowercase, split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Remove stopwords
    words1 -= STOPWORDS
    words2 -= STOPWORDS

    if not words1 or not words2:
        return 0.0

    # Jaccard similarity: intersection / union
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union else 0.0


# =============================================================================
# DUPLICATE DETECTION
# =============================================================================

def find_duplicate_groups(
    known_path: Path,
    threshold: float = 0.7,
    same_section_only: bool = False,
) -> list[dict]:
    """
    Find groups of similar claims.

    Args:
        known_path: Path to known-claims.md
        threshold: Minimum similarity (0.0-1.0) to consider duplicate
        same_section_only: Only compare within same section

    Returns:
        List of duplicate groups, each with:
        - claims: list of claim dicts
        - similarity: highest similarity score in group
        - section: section name if same_section_only, else None
    """
    if not known_path.exists():
        return []

    claims = parse_known_claims(known_path)
    if len(claims) < 2:
        return []

    # Track which claims are already in a group
    grouped: set[int] = set()
    groups: list[dict] = []

    for i, claim1 in enumerate(claims):
        if i in grouped:
            continue

        group_claims = [claim1]
        group_indices = {i}
        best_similarity = 0.0

        for j, claim2 in enumerate(claims[i + 1:], start=i + 1):
            if j in grouped:
                continue

            # Skip cross-section if requested
            if same_section_only and claim1.get("section") != claim2.get("section"):
                continue

            similarity = calculate_duplicate_similarity(
                claim1["claim"],
                claim2["claim"]
            )

            if similarity >= threshold:
                group_claims.append(claim2)
                group_indices.add(j)
                best_similarity = max(best_similarity, similarity)

        # Only create group if we found duplicates
        if len(group_claims) > 1:
            grouped.update(group_indices)
            groups.append({
                "claims": group_claims,
                "similarity": best_similarity,
                "section": claim1.get("section") if same_section_only else None,
            })

    # Sort by similarity (highest first)
    groups.sort(key=lambda g: -g["similarity"])

    return groups


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="Detect duplicate claims in cache")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Similarity threshold (0.0-1.0, default: 0.7)",
    )
    parser.add_argument(
        "--same-section",
        action="store_true",
        help="Only compare claims within the same section",
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

    groups = find_duplicate_groups(
        args.known_claims,
        threshold=args.threshold,
        same_section_only=args.same_section,
    )

    if args.json:
        import json
        output = [
            {
                "similarity": g["similarity"],
                "section": g["section"],
                "claims": [
                    {"claim": c["claim"], "section": c["section"], "verdict": c["verdict"]}
                    for c in g["claims"]
                ],
            }
            for g in groups
        ]
        print(json.dumps(output, indent=2))
    else:
        if not groups:
            print("No duplicate claims found.")
            return 0

        print(f"Found {len(groups)} group(s) of similar claims:\n")

        for i, group in enumerate(groups, 1):
            print(f"Group {i} (similarity: {group['similarity']:.2f}):")
            for claim in group["claims"]:
                print(f"  [{claim['section']}] {claim['claim']}")
                print(f"    Verdict: {claim['verdict']}")
            print()

        print("Consider consolidating or removing redundant claims.")

    return 2 if groups else 0


if __name__ == "__main__":
    sys.exit(main())
