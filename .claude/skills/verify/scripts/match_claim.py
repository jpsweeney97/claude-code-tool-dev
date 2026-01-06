#!/usr/bin/env python3
"""
Match a claim against known-claims.md using weighted Jaccard similarity.

Algorithm: Weighted token overlap with domain boosting and synonym normalization.
- Domain-specific terms (frontmatter, hook, exit code) weighted higher
- Synonyms normalized ("need" → "required", "licence" → "license")
- Stopwords removed to reduce noise

Exit codes:
    0: Match found (prints JSON result)
    1: Input error (missing args, file not found)
    10: No match found (prints empty result)

Usage:
    python match_claim.py "Skills require a license field"
    python match_claim.py "license field required" --threshold 0.3
    python match_claim.py "exit code 1 blocks" --json
    python match_claim.py "timeout" --top 5
    python match_claim.py "required field" --section Skills
    python match_claim.py "timeout" --check-freshness        # Warn about stale claims
    python match_claim.py "timeout" --max-age 60             # Custom TTL (days)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from pathlib import Path

from _common import parse_verified_date, DEFAULT_MAX_AGE_DAYS, SECTION_ALIASES


# =============================================================================
# STALENESS CONFIGURATION
# =============================================================================


def check_staleness(verified_date: str | None, max_age_days: int = DEFAULT_MAX_AGE_DAYS) -> tuple[int | None, bool]:
    """
    Check if a claim is stale based on its verification date.

    Args:
        verified_date: ISO date string (e.g., "2026-01-05" or "2026-01-05 (v2.0.76)")
        max_age_days: Maximum age before claim is considered stale

    Returns:
        Tuple of (days_since_verified, is_stale).
        Returns (None, False) if date is missing or invalid.
    """
    verified = parse_verified_date(verified_date)
    if not verified:
        return (None, False)

    days_ago = (date.today() - verified).days
    return (days_ago, days_ago > max_age_days)


# =============================================================================
# DOMAIN CONFIGURATION
# =============================================================================

# Weights encode diagnostic strength: higher = stronger match signal
# Tuned from known-claims.md vocabulary
DOMAIN_TERMS: dict[str, float] = {
    # Skills cluster
    "frontmatter": 3.0,
    "skill": 2.5,
    "skills": 2.5,
    "name": 1.5,
    "description": 1.5,
    "license": 2.5,
    "licence": 2.5,
    "allowed": 2.0,
    "tools": 1.5,
    "model": 1.5,
    "metadata": 2.0,
    "filename": 2.0,
    "hyphen": 2.0,
    "case": 1.5,
    "lines": 1.5,
    "characters": 1.5,
    "override": 2.0,
    "precedence": 2.0,
    
    # Hooks cluster
    "hook": 2.5,
    "hooks": 2.5,
    "exit": 2.5,
    "code": 1.5,
    "timeout": 2.5,
    "matcher": 2.5,
    "matchers": 2.5,
    "pretooluse": 3.0,
    "posttooluse": 3.0,
    "blocking": 2.0,
    "parallel": 2.0,
    "sessionstart": 2.5,
    
    # Commands cluster
    "command": 2.0,
    "commands": 2.0,
    "arguments": 2.5,
    "positional": 2.0,
    "slash": 2.0,
    "slashcommand": 2.5,
    "bash": 2.0,
    "budget": 1.5,
    
    # MCP cluster
    "mcp": 3.0,
    "server": 1.5,
    "servers": 1.5,
    "scope": 2.5,
    "scopes": 2.5,
    "local": 2.0,
    "project": 2.0,
    "user": 1.5,
    "tokens": 2.0,
    "environment": 1.5,
    "variables": 1.5,
    "approval": 2.0,
    
    # Agents cluster
    "agent": 2.0,
    "agents": 2.0,
    "task": 2.0,
    "subagent": 2.5,
    
    # Configuration terms (cross-cutting)
    "required": 2.0,
    "optional": 2.0,
    "default": 1.5,
    "yaml": 2.5,
    "json": 2.0,
    "markdown": 2.0,
    "field": 1.5,
    "max": 1.5,
    "limit": 1.5,
    "configurable": 1.5,
    "sensitive": 1.5,
}

DEFAULT_WEIGHT: float = 1.0

STOPWORDS: set[str] = {
    "the", "a", "an", "is", "are", "in", "to", "for", "of", "and", "or",
    "it", "be", "has", "have", "was", "were", "been", "being", "this", "that",
    "with", "as", "at", "by", "on", "from", "can", "only", "all", "uses",
    "use", "using", "support", "supports", "does", "do",
}

# Synonym groups: all terms normalize to first in tuple
SYNONYM_GROUPS: list[tuple[str, ...]] = [
    ("required", "require", "requires", "need", "needs", "must", "mandatory"),
    ("optional", "not required"),
    ("field", "property", "attribute", "key"),
    ("frontmatter", "header", "metadata block"),
    ("skill", "skills"),
    ("hook", "hooks"),
    ("command", "commands"),
    ("license", "licence"),
    ("timeout", "time limit"),
    ("exit", "return"),
    ("block", "blocks", "blocking"),
    ("max", "maximum", "limit"),
    ("config", "configuration", "configure", "configured", "configurable"),
]

def discover_sections(cache_path: Path) -> set[str]:
    """
    Discover valid section names from known-claims.md.

    Sections are identified by ## headers, excluding meta-sections
    like "How to Use" and "Maintenance".
    """
    if not cache_path.exists():
        return set()

    skip_sections = {"How to Use", "Maintenance"}
    sections: set[str] = set()

    for line in cache_path.read_text().splitlines():
        if line.startswith("## "):
            section_name = line[3:].strip()
            if section_name not in skip_sections:
                sections.add(section_name)

    return sections


def normalize_section(section: str, valid_sections: set[str]) -> str | None:
    """
    Normalize a section name to its canonical form.

    Returns:
        Canonical section name if valid/aliased, None if unknown.
    """
    # Exact match (case-sensitive)
    if section in valid_sections:
        return section

    # Check aliases (case-insensitive)
    section_lower = section.lower()
    if section_lower in SECTION_ALIASES:
        canonical = SECTION_ALIASES[section_lower]
        if canonical in valid_sections:
            return canonical

    # Case-insensitive match against valid sections
    for valid in valid_sections:
        if valid.lower() == section_lower:
            return valid

    return None

# Query-focal boost: domain terms in query get this multiplier when they match
# Rationale: "Skills need a license" → "license" is what user is asking about
QUERY_FOCAL_BOOST: float = 2.0

# Penalty for missing focal terms (0.0-1.0): reduces score when key query terms don't match
# Rationale: If user asks about "license" and claim doesn't mention license, penalize
MISSING_FOCAL_PENALTY: float = 0.3

# Tiered threshold defaults
THRESHOLD_HIGH: float = 0.60   # Auto-return with confidence
THRESHOLD_MEDIUM: float = 0.40  # Show candidates for confirmation
THRESHOLD_LOW: float = 0.25     # Minimum to consider a match


# =============================================================================
# SIMILARITY ENGINE
# =============================================================================

def _build_synonym_map(groups: list[tuple[str, ...]]) -> dict[str, str]:
    """Map each synonym → canonical form (first in group)."""
    mapping: dict[str, str] = {}
    for group in groups:
        canonical = group[0]
        for term in group:
            mapping[term] = canonical
    return mapping


_SYNONYM_MAP = _build_synonym_map(SYNONYM_GROUPS)


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into tokens."""
    text = text.lower()
    # Preserve numbers (e.g., "60", "500", "0", "1", "2" for exit codes)
    text = re.sub(r"[`'\"\-_.,;:!?()[\]{}]", " ", text)
    return [t for t in text.split() if t]


def _normalize(token: str) -> str:
    """Apply synonym mapping."""
    return _SYNONYM_MAP.get(token, token)


def _weight(token: str) -> float:
    """Get domain weight for a normalized token."""
    return DOMAIN_TERMS.get(token, DEFAULT_WEIGHT)


def calculate_similarity(query: str, known: str) -> float:
    """
    Calculate weighted Jaccard similarity with query-focal boosting.
    
    Algorithm:
        1. Tokenize both strings (lowercase, strip punctuation)
        2. Remove stopwords
        3. Normalize via synonym mapping
        4. Identify focal terms: domain terms that appear in query
        5. Compute weighted Jaccard with focal boost on intersection
        6. Apply penalty for missing focal terms
    
    Key insight: Domain terms in the query are what the user is asking about.
    "Skills need a license" → "license" is focal (domain term in query).
    - Focal terms get QUERY_FOCAL_BOOST (2x) when they match
    - Missing focal terms apply MISSING_FOCAL_PENALTY to final score
    
    Returns:
        float in [0.0, 1.0] where higher = better match
    """
    query_tokens = _tokenize(query)
    known_tokens = _tokenize(known)
    
    # Normalize and filter stopwords
    query_norm = {_normalize(t) for t in query_tokens if t not in STOPWORDS}
    known_norm = {_normalize(t) for t in known_tokens if t not in STOPWORDS}
    
    if not query_norm or not known_norm:
        return 0.0
    
    # Identify focal terms: domain terms present in query
    focal_terms = {t for t in query_norm if t in DOMAIN_TERMS}
    
    intersection = query_norm & known_norm
    union = query_norm | known_norm
    
    if not union:
        return 0.0
    
    # Focal boost: domain terms from query get extra weight when they match
    def effective_weight(token: str, in_intersection: bool) -> float:
        base = _weight(token)
        if in_intersection and token in focal_terms:
            return base * QUERY_FOCAL_BOOST
        return base
    
    weighted_intersection = sum(effective_weight(t, True) for t in intersection)
    weighted_union = sum(effective_weight(t, t in intersection) for t in union)
    
    base_score = weighted_intersection / weighted_union
    
    # Penalty for missing focal terms
    # If user asks about "license" and claim doesn't contain "license", penalize HARD
    # Missing any focal term caps score below THRESHOLD_HIGH
    if focal_terms:
        matched_focal = focal_terms & intersection
        focal_coverage = len(matched_focal) / len(focal_terms)
        if focal_coverage < 1.0:
            # Missing focal terms: cap score at medium confidence
            # Scale penalty so 0% coverage → 50% reduction, 67% coverage → 15% reduction
            penalty_factor = 1 - (MISSING_FOCAL_PENALTY * (1 - focal_coverage) ** 0.5)
            base_score *= penalty_factor
            # Hard cap: can't reach high confidence with missing focal terms
            base_score = min(base_score, THRESHOLD_HIGH - 0.01)
    
    return base_score


def explain_match(query: str, known: str) -> dict:
    """
    Debug helper: show tokenization, normalization, focal terms, and weights.
    
    Returns dict with:
        - query_tokens: normalized tokens from query
        - known_tokens: normalized tokens from known claim
        - focal_terms: domain terms from query (get boosted)
        - matched_focal: focal terms that appear in intersection
        - focal_coverage: fraction of focal terms matched (0.0-1.0)
        - intersection: overlapping tokens
        - intersection_weights: weight contribution per matching token
        - score: final similarity score (after penalty)
    """
    query_tokens = _tokenize(query)
    known_tokens = _tokenize(known)
    
    query_norm = {_normalize(t) for t in query_tokens if t not in STOPWORDS}
    known_norm = {_normalize(t) for t in known_tokens if t not in STOPWORDS}
    
    focal_terms = {t for t in query_norm if t in DOMAIN_TERMS}
    intersection = query_norm & known_norm
    union = query_norm | known_norm
    matched_focal = focal_terms & intersection
    
    focal_coverage = len(matched_focal) / len(focal_terms) if focal_terms else 1.0
    penalty = (1 - focal_coverage) * MISSING_FOCAL_PENALTY if focal_terms else 0.0
    
    def effective_weight(token: str, in_intersection: bool) -> float:
        base = _weight(token)
        if in_intersection and token in focal_terms:
            return base * QUERY_FOCAL_BOOST
        return base
    
    weighted_intersection = sum(effective_weight(t, True) for t in intersection)
    weighted_union = sum(effective_weight(t, t in intersection) for t in union)
    base_score = weighted_intersection / weighted_union if weighted_union else 0.0
    
    return {
        "query_tokens": sorted(query_norm),
        "known_tokens": sorted(known_norm),
        "focal_terms": sorted(focal_terms),
        "matched_focal": sorted(matched_focal),
        "focal_coverage": focal_coverage,
        "penalty": penalty,
        "intersection": sorted(intersection),
        "intersection_weights": {
            t: effective_weight(t, True) for t in sorted(intersection)
        },
        "weighted_intersection": weighted_intersection,
        "weighted_union": weighted_union,
        "base_score": base_score,
        "score": calculate_similarity(query, known),
    }


# =============================================================================
# CLAIM PARSING AND MATCHING
# =============================================================================

@dataclass
class MatchResult:
    """Result of a single claim match."""

    matched: bool
    claim: str
    known_claim: str | None = None
    verdict: str | None = None
    evidence: str | None = None
    section: str | None = None
    confidence: float = 0.0
    verified_date: str | None = None
    days_since_verified: int | None = None
    is_stale: bool = False
    severity: str | None = None  # CRITICAL, HIGH, LOW
    source_url: str | None = None  # Per-claim documentation URL


@dataclass
class MultiMatchResult:
    """Result containing multiple matches."""

    claim: str
    matches: list[MatchResult] = field(default_factory=list)
    total_checked: int = 0


def parse_severity(verdict: str) -> tuple[str, str | None]:
    """
    Extract severity from verdict string.

    Format: "✓ Verified [CRITICAL]" → ("✓ Verified", "CRITICAL")

    Returns:
        Tuple of (base_verdict, severity or None)
    """
    match = re.search(r'\[(CRITICAL|HIGH|LOW)\]', verdict)
    if match:
        severity = match.group(1)
        base_verdict = verdict.replace(f" [{severity}]", "").strip()
        return (base_verdict, severity)
    return (verdict, None)


def parse_source_url(evidence: str) -> tuple[str, str | None]:
    """
    Extract source URL from evidence string.

    Format: "Evidence text (https://...)" → ("Evidence text", "https://...")

    Returns:
        Tuple of (base_evidence, source_url or None)
    """
    # Match URL at end of evidence in parentheses
    match = re.search(r'\s*\((https?://[^\)]+)\)\s*$', evidence)
    if match:
        source_url = match.group(1)
        base_evidence = evidence[:match.start()].strip()
        return (base_evidence, source_url)
    return (evidence, None)


def parse_known_claims(path: Path) -> list[dict]:
    """Parse known-claims.md into structured entries."""
    content = path.read_text()
    claims: list[dict] = []
    current_section: str | None = None

    for line in content.splitlines():
        # Track section headers (## Skills, ## Hooks, etc.)
        if line.startswith("## ") and not line.startswith("## How") and not line.startswith("## Maintenance"):
            current_section = line[3:].strip()
            continue

        # Parse table rows: | Claim | Verdict | Evidence | Verified |
        if line.startswith("|") and not line.startswith("| Claim") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                raw_verdict = parts[1]
                raw_evidence = parts[2]

                # Extract severity and source
                base_verdict, severity = parse_severity(raw_verdict)
                base_evidence, source_url = parse_source_url(raw_evidence)

                claims.append({
                    "claim": parts[0].strip("`"),
                    "verdict": base_verdict,
                    "evidence": base_evidence,
                    "section": current_section,
                    "verified_date": parts[3] if len(parts) >= 4 else None,
                    "severity": severity,
                    "source_url": source_url,
                })

    return claims


def find_best_match(
    query: str,
    claims: list[dict],
    threshold: float,
    section: str | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> MatchResult:
    """Find the single best matching claim above threshold."""
    best_match: dict | None = None
    best_score: float = 0.0

    for entry in claims:
        # Apply section filter if specified
        if section and entry.get("section") != section:
            continue

        score = calculate_similarity(query, entry["claim"])
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score >= threshold:
        verified_date = best_match.get("verified_date")
        days_since, is_stale = check_staleness(verified_date, max_age_days)
        return MatchResult(
            matched=True,
            claim=query,
            known_claim=best_match["claim"],
            verdict=best_match["verdict"],
            evidence=best_match["evidence"],
            section=best_match["section"],
            confidence=round(best_score, 4),
            verified_date=verified_date,
            days_since_verified=days_since,
            is_stale=is_stale,
            severity=best_match.get("severity"),
            source_url=best_match.get("source_url"),
        )

    return MatchResult(matched=False, claim=query, confidence=round(best_score, 4))


def find_top_matches(
    query: str,
    claims: list[dict],
    top_n: int,
    threshold: float = 0.0,
    section: str | None = None,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> MultiMatchResult:
    """
    Find the top N matching claims, optionally filtered by section.

    Args:
        query: User's claim to match
        claims: Parsed claims from known-claims.md
        top_n: Number of top matches to return
        threshold: Minimum score to include (default 0.0 = include all)
        section: Optional section filter (e.g., "Skills", "Hooks")
        max_age_days: Maximum age before claim is considered stale

    Returns:
        MultiMatchResult with up to top_n matches sorted by confidence descending
    """
    scored: list[tuple[float, dict]] = []

    for entry in claims:
        # Apply section filter if specified
        if section and entry.get("section") != section:
            continue

        score = calculate_similarity(query, entry["claim"])
        if score >= threshold:
            scored.append((score, entry))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    matches = []
    for score, entry in scored[:top_n]:
        verified_date = entry.get("verified_date")
        days_since, is_stale = check_staleness(verified_date, max_age_days)
        matches.append(MatchResult(
            matched=True,
            claim=query,
            known_claim=entry["claim"],
            verdict=entry["verdict"],
            evidence=entry["evidence"],
            section=entry["section"],
            confidence=round(score, 4),
            verified_date=verified_date,
            days_since_verified=days_since,
            is_stale=is_stale,
            severity=entry.get("severity"),
            source_url=entry.get("source_url"),
        ))

    return MultiMatchResult(
        claim=query,
        matches=matches,
        total_checked=len(claims) if not section else sum(1 for c in claims if c.get("section") == section),
    )


def list_sections(claims: list[dict]) -> dict[str, int]:
    """Return section names and claim counts."""
    sections: dict[str, int] = {}
    for c in claims:
        sec = c.get("section") or "Unknown"
        sections[sec] = sections.get(sec, 0) + 1
    return sections


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Match claim against known-claims.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes (--mode):
    auto (default): >=0.60 returns immediately, 0.40-0.59 shows candidates, <0.40 no match
    confirm:        Always show top 3 candidates regardless of score
    search:         Only match if score >= 0.60 (strict mode)

Exit codes:
    0:  High confidence match (or explicit --threshold met)
    1:  Medium confidence - candidates shown for confirmation
    10: No match found

Examples:
    # Default auto mode with tiered response
    python match_claim.py "Skills require a license field"

    # Force confirmation display
    python match_claim.py "required field" --mode confirm

    # Top 5 matches
    python match_claim.py "required field" --top 5

    # Filter by section
    python match_claim.py "timeout" --section Hooks

    # Explicit threshold (overrides mode)
    python match_claim.py "license" --threshold 0.5

    # JSON output for scripting
    python match_claim.py "exit code" --json

    # Debug: show focal terms and weights
    python match_claim.py "license required" --debug

    # List available sections
    python match_claim.py --list-sections

    # Check freshness (show staleness warnings)
    python match_claim.py "timeout" --check-freshness

    # Find stale claims needing refresh
    python match_claim.py "*" --top 100 --stale-only

    # Custom TTL threshold (60 days)
    python match_claim.py "exit code" --check-freshness --max-age 60
        """,
    )
    parser.add_argument("claim", nargs="?", help="Claim text to match")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Minimum similarity score (0.0-1.0). Overrides --mode thresholds.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="auto",
        choices=["auto", "confirm", "search"],
        help="Match mode: auto (>=0.60 returns immediately), confirm (0.40-0.59 shows top 3), search (<0.40 no match). Default: auto",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Return top N matches instead of single best match",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Filter matches to a specific section (discovered from known-claims.md)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--debug", action="store_true", help="Show token breakdown for best match")
    parser.add_argument("--list-sections", action="store_true", help="List available sections and exit")
    parser.add_argument(
        "--check-freshness",
        action="store_true",
        help="Show staleness warnings for matched claims",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        metavar="DAYS",
        help=f"Maximum age in days before claim is stale (default: {DEFAULT_MAX_AGE_DAYS})",
    )
    parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Only return stale claims (use with --top to find claims needing refresh)",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.cache.exists():
        print(f"Error: Cache file not found: {args.cache}", file=sys.stderr)
        return 1

    # Parse claims
    claims = parse_known_claims(args.cache)

    # Discover valid sections dynamically
    valid_sections = discover_sections(args.cache)

    # Validate and normalize --section if provided
    if args.section:
        normalized = normalize_section(args.section, valid_sections)
        if normalized is None:
            print(f"Error: Unknown section '{args.section}'", file=sys.stderr)
            print(f"Available sections: {', '.join(sorted(valid_sections))}", file=sys.stderr)
            return 1
        if normalized != args.section:
            print(f"Note: Normalized '{args.section}' → '{normalized}'", file=sys.stderr)
        args.section = normalized

    # Handle --list-sections
    if args.list_sections:
        sections = list_sections(claims)
        if args.json:
            print(json.dumps(sections, indent=2))
        else:
            print("Available sections:")
            for sec, count in sorted(sections.items()):
                print(f"  {sec}: {count} claims")
        return 0
    
    # Require claim for matching
    if not args.claim:
        parser.error("claim is required unless using --list-sections")

    # Multi-match mode (--top N)
    if args.top is not None:
        if args.top < 1:
            parser.error("--top must be >= 1")

        # Use explicit threshold or default to THRESHOLD_LOW
        top_threshold = args.threshold if args.threshold is not None else THRESHOLD_LOW

        result = find_top_matches(
            args.claim,
            claims,
            top_n=args.top,
            threshold=top_threshold,
            section=args.section,
            max_age_days=args.max_age,
        )

        # Filter to stale-only if requested
        if args.stale_only:
            result.matches = [m for m in result.matches if m.is_stale]

        if args.json:
            output = {
                "claim": result.claim,
                "total_checked": result.total_checked,
                "max_age_days": args.max_age,
                "matches": [asdict(m) for m in result.matches],
            }
            print(json.dumps(output, indent=2))
        else:
            section_note = f" in {args.section}" if args.section else ""
            stale_note = " (stale only)" if args.stale_only else ""
            print(f"Top {args.top} matches for: {result.claim!r}{section_note}{stale_note}")
            print(f"(checked {result.total_checked} claims, threshold: {top_threshold})\n")
            
            if not result.matches:
                print("No matches above threshold.")
            else:
                for i, m in enumerate(result.matches, 1):
                    stale_marker = " ⚠️ STALE" if m.is_stale else ""
                    severity_marker = f" [{m.severity}]" if m.severity else ""
                    print(f"{i}. [{m.confidence:.3f}] {m.verdict}{severity_marker}{stale_marker}")
                    print(f"   Claim: {m.known_claim}")
                    print(f"   Evidence: {m.evidence}")
                    print(f"   Section: {m.section}")
                    if m.source_url:
                        print(f"   Source: {m.source_url}")
                    if args.check_freshness and m.verified_date:
                        age_str = f"{m.days_since_verified}d ago" if m.days_since_verified else "unknown"
                        print(f"   Verified: {m.verified_date} ({age_str})")
                    print()

        return 0 if result.matches else 10

    # Single-match mode (default)
    # Determine effective threshold based on mode
    if args.threshold is not None:
        # Explicit threshold overrides mode
        effective_threshold = args.threshold
        mode_behavior = "threshold"
    else:
        # Use mode-based thresholds
        effective_threshold = THRESHOLD_LOW
        mode_behavior = args.mode
    
    # Get top 3 for tiered decision-making
    top_results = find_top_matches(
        args.claim,
        claims,
        top_n=3,
        threshold=effective_threshold,
        section=args.section,
        max_age_days=args.max_age,
    )
    
    # Determine action based on mode and scores
    best_match = top_results.matches[0] if top_results.matches else None
    best_score = best_match.confidence if best_match else 0.0
    
    # Debug mode: show token breakdown
    if args.debug and best_match:
        breakdown = explain_match(args.claim, best_match.known_claim)
        print(f"Query: {args.claim!r}")
        print(f"Best match: {best_match.known_claim!r}\n")
        print(f"  Query tokens:         {breakdown['query_tokens']}")
        print(f"  Known tokens:         {breakdown['known_tokens']}")
        print(f"  Focal terms:          {breakdown['focal_terms']}")
        print(f"  Matched focal:        {breakdown['matched_focal']}")
        print(f"  Focal coverage:       {breakdown['focal_coverage']:.0%}")
        print(f"  Intersection:         {breakdown['intersection']}")
        print(f"  Intersection weights: {breakdown['intersection_weights']}")
        print(f"  Weighted intersection: {breakdown['weighted_intersection']:.2f}")
        print(f"  Weighted union:        {breakdown['weighted_union']:.2f}")
        print(f"  Base score:            {breakdown['base_score']:.4f}")
        print(f"  Penalty:               {breakdown['penalty']:.4f}")
        print(f"  Final score:           {breakdown['score']:.4f}")
        print()
    
    # Tiered response logic
    if mode_behavior == "threshold":
        # Explicit threshold: simple pass/fail
        result = best_match if best_match and best_score >= effective_threshold else MatchResult(
            matched=False, claim=args.claim, confidence=best_score
        )
        tier = "threshold"
    elif best_score >= THRESHOLD_HIGH:
        # High confidence: return immediately
        result = best_match
        tier = "high"
    elif best_score >= THRESHOLD_MEDIUM:
        # Medium confidence: show candidates for confirmation
        tier = "confirm"
        result = best_match  # Still return best, but flag for confirmation
    else:
        # Low confidence: no match
        result = MatchResult(matched=False, claim=args.claim, confidence=best_score)
        tier = "low"
    
    # Output
    if args.json:
        output = asdict(result) if result.matched else asdict(MatchResult(matched=False, claim=args.claim, confidence=best_score))
        output["tier"] = tier
        output["mode"] = mode_behavior
        output["max_age_days"] = args.max_age
        if tier == "confirm":
            output["candidates"] = [asdict(m) for m in top_results.matches]
        print(json.dumps(output, indent=2))
    else:
        section_note = f" in {args.section}" if args.section else ""

        # Helper for staleness display
        def format_freshness(m: MatchResult) -> str:
            if not args.check_freshness or not m.verified_date:
                return ""
            age = f"{m.days_since_verified}d ago" if m.days_since_verified is not None else "unknown"
            if m.is_stale:
                return f"\n⚠️  STALE: verified {m.verified_date} ({age}) - consider /verify --refresh"
            return f"\n   Verified: {m.verified_date} ({age})"

        if tier == "high":
            # High confidence: return immediately
            stale_marker = " ⚠️ STALE" if result.is_stale else ""
            severity_marker = f" [{result.severity}]" if result.severity else ""
            print(f"✓ HIGH CONFIDENCE ({best_score:.2f}){severity_marker}{stale_marker}")
            print(f"{result.verdict} | {result.known_claim}")
            print(f"Evidence: {result.evidence}")
            if result.source_url:
                print(f"Source: {result.source_url}")
            print(f"Section: {result.section}{format_freshness(result)}")
        elif tier == "confirm":
            # Medium confidence: show candidates
            print(f"? CONFIRM ({best_score:.2f}) - Multiple candidates{section_note}:")
            print()
            for i, m in enumerate(top_results.matches, 1):
                marker = "→" if i == 1 else " "
                stale_marker = " ⚠️ STALE" if m.is_stale else ""
                severity_marker = f" [{m.severity}]" if m.severity else ""
                print(f"  {marker} {i}. [{m.confidence:.3f}] {m.verdict}{severity_marker}{stale_marker}")
                print(f"       {m.known_claim}")
                print(f"       Evidence: {m.evidence}")
                if m.source_url:
                    print(f"       Source: {m.source_url}")
                if args.check_freshness and m.verified_date:
                    age = f"{m.days_since_verified}d ago" if m.days_since_verified else "?"
                    print(f"       Verified: {m.verified_date} ({age})")
                print()
            print("Suggestion: Verify with documentation or select a candidate.")
        elif tier == "threshold" and result.matched:
            # Explicit threshold mode with match
            stale_marker = " ⚠️ STALE" if result.is_stale else ""
            severity_marker = f" [{result.severity}]" if result.severity else ""
            print(f"{result.verdict}{severity_marker} | {result.known_claim}{stale_marker}")
            print(f"Evidence: {result.evidence}")
            if result.source_url:
                print(f"Source: {result.source_url}")
            print(f"Section: {result.section}")
            print(f"Confidence: {result.confidence:.2f}{format_freshness(result)}")
        else:
            # No match
            print(f"✗ NO MATCH{section_note} (best score: {best_score:.2f})")
            if top_results.matches:
                print(f"  Closest: {top_results.matches[0].known_claim}")
    
    # Exit codes: 0=high confidence, 1=confirm needed, 10=no match
    if tier == "high" or (tier == "threshold" and result.matched):
        return 0
    elif tier == "confirm":
        return 1
    else:
        return 10


if __name__ == "__main__":
    sys.exit(main())
