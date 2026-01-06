#!/usr/bin/env python3
"""
Extract verifiable claims from a markdown document.

Scans for technical assertions that can be verified against official documentation.
Uses conservative pattern matching by default; --verbose for aggressive extraction.

Exit codes:
    0: Claims extracted successfully
    1: Input error (file not found, parse error)
    10: No claims found

Usage:
    python extract_claims.py /path/to/document.md
    python extract_claims.py document.md --verbose        # Aggressive extraction
    python extract_claims.py document.md --json           # JSON output
    python extract_claims.py document.md --by-section     # Group by document section
    python extract_claims.py document.md --limit 50       # Limit output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


# =============================================================================
# CLAIM DETECTION PATTERNS
# =============================================================================

# Topic keywords for clustering extracted claims
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Hooks": [
        "hook", "hooks", "pretooluse", "posttooluse", "sessionstart",
        "exit code", "matcher", "timeout", "blocking", "event",
    ],
    "Skills": [
        "skill", "skills", "skill.md", "frontmatter", "allowed-tools",
        "trigger", "precedence",
    ],
    "Commands": [
        "command", "commands", "slash", "$arguments", "positional",
        "argument-hint", "!`", "@",
    ],
    "MCP": [
        "mcp", "server", "servers", ".mcp.json", "scope", "token",
        "mcp__", "tool",
    ],
    "Agents": [
        "agent", "agents", "subagent", "task tool", "delegation",
        "orchestrat",
    ],
    "Settings": [
        "settings.json", "config", "permission", "keyboard", "shortcut",
    ],
    "CLI": [
        "cli", "flag", "claude ", "--", "terminal", "environment variable",
    ],
}

# Conservative patterns: high-confidence claim indicators
CONSERVATIVE_PATTERNS: list[re.Pattern] = [
    # Bold-label patterns: **Label:** value (common in documentation)
    re.compile(r"\*\*([^*]+):\*\*\s*(.+)", re.I),

    # "X is Y" definitional (with specific values)
    re.compile(r"(?:default|timeout|limit|max|min)\s+(?:is|are|of)\s+(\d+)", re.I),
    re.compile(r"(?:is|are)\s+(\d+)\s*(?:seconds?|minutes?|tokens?|characters?|lines?)", re.I),
    re.compile(r"(\d+)(?:s|ms)?\s+(?:default|timeout|limit)", re.I),

    # Exit codes and return values
    re.compile(r"exit\s+code\s+(\d+)\s*(?::|means|indicates|is|—)", re.I),
    re.compile(r"(?:returns?|exit(?:s)?)\s+(?:with\s+)?(?:code\s+)?(\d+)", re.I),
    re.compile(r"code\s+(\d+)[:—]\s*\w+", re.I),

    # Required/optional field assertions
    re.compile(r"`(\w+)`\s+(?:field\s+)?(?:is\s+)?(?:required|optional|mandatory)", re.I),
    re.compile(r"(?:requires?|must\s+have|must\s+include)\s+(?:a\s+)?`(\w+)`", re.I),

    # Format/structure assertions
    re.compile(r"(?:uses?|requires?|configured?\s+(?:in|via|using))\s+(?:YAML|JSON|markdown)", re.I),
    re.compile(r"\.(?:json|yaml|yml|md)\s+(?:file|format|configuration)", re.I),
    re.compile(r"(?:stored?|configured?|defined?)\s+in\s+[`~./][\w./]+", re.I),

    # Capability assertions
    re.compile(r"(?:supports?|can|cannot|does\s+not)\s+(?:\w+\s+){0,3}(?:parallel|background|concurrent)", re.I),
    re.compile(r"(?:run(?:s)?|execute(?:s)?)\s+(?:in\s+)?(?:parallel|sequentially|background)", re.I),
    re.compile(r"all\s+(?:matching\s+)?(?:hooks?|agents?|commands?)\s+run\s+in\s+parallel", re.I),

    # Scope/precedence assertions
    re.compile(r"(?:takes?\s+)?precedence\s+(?:over|above)", re.I),
    re.compile(r"(?:overrides?|override(?:s)?)\s+(?:project|user|personal|local)", re.I),

    # Location/path assertions
    re.compile(r"(?:stored?|located?|found|saved?)\s+(?:in|at|to)\s+[`~]", re.I),
]

# Verbose patterns: additional candidates (higher recall, more noise)
VERBOSE_PATTERNS: list[re.Pattern] = [
    # General "X is Y" patterns
    re.compile(r"(?:^|\.\s+)([A-Z][^.]*?\s+(?:is|are)\s+[^.]+\.)", re.M),

    # "X supports Y" patterns
    re.compile(r"(?:supports?|provides?|enables?|allows?)\s+(\w+(?:\s+\w+){0,3})", re.I),

    # Default value patterns
    re.compile(r"default(?:s)?\s+(?:to|is|are|value)\s+[^.]+", re.I),

    # Configuration patterns
    re.compile(r"configure(?:d)?\s+(?:in|via|using|with)\s+[^.]+", re.I),

    # Location patterns
    re.compile(r"(?:stored?|located?|found)\s+(?:in|at)\s+[`~./][^.]+", re.I),
]

# Patterns to SKIP (false positives)
SKIP_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\s*#", re.M),  # Headers
    re.compile(r"^\s*\|", re.M),  # Table rows (handled separately)
    re.compile(r"^\s*```", re.M),  # Code blocks
    re.compile(r"for\s+example", re.I),  # Examples
    re.compile(r"(?:might|could|may|should)\s+(?:be|have|use)", re.I),  # Uncertainty
    re.compile(r"consider\s+(?:using|adding)", re.I),  # Advice
    re.compile(r"^\s*>", re.M),  # Blockquotes (often notes/warnings)
]
# Note: List items (- *) are NOT skipped - they often contain claims with **bold:** labels


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ExtractedClaim:
    """A claim extracted from a document."""
    text: str
    line_number: int
    section: str | None = None
    topic: str | None = None
    confidence: str = "medium"  # high, medium, low
    context: str | None = None  # surrounding text for disambiguation


@dataclass
class ExtractionResult:
    """Result of claim extraction from a document."""
    document_path: str
    total_lines: int
    claims: list[ExtractedClaim] = field(default_factory=list)
    sections_found: list[str] = field(default_factory=list)
    mode: str = "conservative"


# =============================================================================
# EXTRACTION ENGINE
# =============================================================================

def detect_topic(text: str) -> str | None:
    """Detect the topic cluster for a claim based on keywords."""
    text_lower = text.lower()

    # Score each topic by keyword matches
    scores: dict[str, int] = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score

    if not scores:
        return None

    # Return topic with highest score
    return max(scores, key=scores.get)


def extract_section_header(line: str) -> str | None:
    """Extract section name from a markdown header line."""
    match = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
    if match:
        return match.group(2).strip()
    return None


def is_skippable(text: str) -> bool:
    """Check if text should be skipped (not a claim)."""
    for pattern in SKIP_PATTERNS:
        if pattern.search(text):
            return True
    return False


def extract_table_claims(lines: list[str], start_idx: int) -> list[tuple[int, str]]:
    """
    Extract claims from a markdown table.

    Returns list of (line_number, claim_text) tuples.
    """
    claims: list[tuple[int, str]] = []

    # Skip header and separator rows
    i = start_idx
    if i < len(lines) and lines[i].strip().startswith("|"):
        i += 1  # Skip header
    if i < len(lines) and re.match(r"^\s*\|[-:|]+\|", lines[i]):
        i += 1  # Skip separator

    # Process data rows
    while i < len(lines) and lines[i].strip().startswith("|"):
        line = lines[i]
        cells = [c.strip() for c in line.split("|")[1:-1]]

        # Look for claim-worthy content in cells
        for cell in cells:
            # Skip empty or short cells
            if len(cell) < 10:
                continue

            # Check if cell contains technical assertion
            has_number = bool(re.search(r"\d+", cell))
            has_keyword = any(
                kw in cell.lower()
                for kws in TOPIC_KEYWORDS.values()
                for kw in kws
            )

            if has_number or has_keyword:
                # Reconstruct claim from row context
                claim_text = " | ".join(c for c in cells if c and len(c) > 3)
                if claim_text and len(claim_text) > 15:
                    claims.append((i + 1, claim_text))
                break

        i += 1

    return claims


def extract_claims_from_document(
    content: str,
    path: str,
    verbose: bool = False,
) -> ExtractionResult:
    """
    Extract verifiable claims from markdown content.

    Args:
        content: Markdown document content
        path: Document path (for reporting)
        verbose: If True, use aggressive extraction patterns

    Returns:
        ExtractionResult with extracted claims
    """
    lines = content.splitlines()
    result = ExtractionResult(
        document_path=path,
        total_lines=len(lines),
        mode="verbose" if verbose else "conservative",
    )

    current_section: str | None = None
    seen_claims: set[str] = set()  # Deduplicate
    in_code_block = False

    # Select patterns based on mode
    patterns = CONSERVATIVE_PATTERNS.copy()
    if verbose:
        patterns.extend(VERBOSE_PATTERNS)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        # Track section headers
        section = extract_section_header(line)
        if section:
            current_section = section
            if section not in result.sections_found:
                result.sections_found.append(section)
            i += 1
            continue

        # Handle tables
        if line.strip().startswith("|") and not line.strip().startswith("|--"):
            table_claims = extract_table_claims(lines, i)
            for line_num, claim_text in table_claims:
                claim_normalized = claim_text.lower().strip()
                if claim_normalized not in seen_claims:
                    seen_claims.add(claim_normalized)
                    result.claims.append(ExtractedClaim(
                        text=claim_text,
                        line_number=line_num,
                        section=current_section,
                        topic=detect_topic(claim_text),
                        confidence="medium",
                    ))
            # Skip past table
            while i < len(lines) and lines[i].strip().startswith("|"):
                i += 1
            continue

        # Skip obvious non-claims
        if is_skippable(line):
            i += 1
            continue

        # Apply extraction patterns
        for pattern in patterns:
            matches = pattern.finditer(line)
            for match in matches:
                # Get full sentence containing match
                claim_text = line.strip()

                # Clean up claim text
                claim_text = re.sub(r"^\s*[-*]\s*", "", claim_text)  # Remove list markers
                claim_text = claim_text.strip()

                if len(claim_text) < 15 or len(claim_text) > 500:
                    continue

                claim_normalized = claim_text.lower()
                if claim_normalized in seen_claims:
                    continue

                seen_claims.add(claim_normalized)

                # Determine confidence based on pattern type
                confidence = "high" if pattern in CONSERVATIVE_PATTERNS else "low"

                result.claims.append(ExtractedClaim(
                    text=claim_text,
                    line_number=i + 1,
                    section=current_section,
                    topic=detect_topic(claim_text),
                    confidence=confidence,
                ))

        i += 1

    return result


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract verifiable claims from a markdown document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
    default (conservative): High-confidence technical assertions only
    --verbose:              Aggressive extraction (more candidates, more noise)

Output formats:
    default: Human-readable summary
    --json:  Structured JSON for pipeline integration

Examples:
    # Conservative extraction
    python extract_claims.py /path/to/guide.md

    # Aggressive extraction
    python extract_claims.py guide.md --verbose

    # JSON output for verification pipeline
    python extract_claims.py guide.md --json

    # Group by document section
    python extract_claims.py guide.md --by-section

    # Limit to first N claims
    python extract_claims.py guide.md --limit 20
        """,
    )
    parser.add_argument("document", type=Path, help="Path to markdown document")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Aggressive extraction (more candidates)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--by-section",
        action="store_true",
        help="Group claims by document section",
    )
    parser.add_argument(
        "--by-topic",
        action="store_true",
        help="Group claims by detected topic (Hooks, Skills, etc.)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Limit output to first N claims",
    )
    parser.add_argument(
        "--min-confidence",
        choices=["high", "medium", "low"],
        default=None,
        help="Filter by minimum confidence level",
    )
    args = parser.parse_args()

    # Validate input
    if not args.document.exists():
        print(f"Error: File not found: {args.document}", file=sys.stderr)
        return 1

    # Read and extract
    try:
        content = args.document.read_text()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    result = extract_claims_from_document(
        content,
        str(args.document),
        verbose=args.verbose,
    )

    # Filter by confidence if requested
    if args.min_confidence:
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        min_level = confidence_order[args.min_confidence]
        result.claims = [
            c for c in result.claims
            if confidence_order.get(c.confidence, 0) >= min_level
        ]

    # Apply limit
    if args.limit:
        result.claims = result.claims[:args.limit]

    # Handle no claims found
    if not result.claims:
        if args.json:
            print(json.dumps({"claims": [], "total_lines": result.total_lines}))
        else:
            print(f"No claims found in {args.document}")
            if not args.verbose:
                print("Tip: Try --verbose for aggressive extraction")
        return 10

    # Output
    if args.json:
        output = {
            "document_path": result.document_path,
            "total_lines": result.total_lines,
            "mode": result.mode,
            "sections_found": result.sections_found,
            "claim_count": len(result.claims),
            "claims": [asdict(c) for c in result.claims],
        }
        print(json.dumps(output, indent=2))
    elif args.by_section:
        print(f"Claims from {args.document} ({result.mode} mode)")
        print(f"Total: {len(result.claims)} claims from {result.total_lines} lines\n")

        by_section: dict[str, list[ExtractedClaim]] = {}
        for claim in result.claims:
            section = claim.section or "Unknown"
            if section not in by_section:
                by_section[section] = []
            by_section[section].append(claim)

        for section, claims in by_section.items():
            print(f"## {section} ({len(claims)} claims)")
            for c in claims:
                conf = {"high": "●", "medium": "○", "low": "◌"}[c.confidence]
                print(f"  {conf} L{c.line_number}: {c.text[:80]}{'...' if len(c.text) > 80 else ''}")
            print()
    elif args.by_topic:
        print(f"Claims from {args.document} ({result.mode} mode)")
        print(f"Total: {len(result.claims)} claims from {result.total_lines} lines\n")

        by_topic: dict[str, list[ExtractedClaim]] = {}
        for claim in result.claims:
            topic = claim.topic or "General"
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(claim)

        for topic in sorted(by_topic.keys()):
            claims = by_topic[topic]
            print(f"## {topic} ({len(claims)} claims)")
            for c in claims:
                conf = {"high": "●", "medium": "○", "low": "◌"}[c.confidence]
                print(f"  {conf} L{c.line_number}: {c.text[:80]}{'...' if len(c.text) > 80 else ''}")
            print()
    else:
        # Default: simple list
        print(f"Claims from {args.document} ({result.mode} mode)")
        print(f"Total: {len(result.claims)} claims from {result.total_lines} lines")
        print(f"Sections: {', '.join(result.sections_found[:5])}{'...' if len(result.sections_found) > 5 else ''}")
        print()

        for i, c in enumerate(result.claims, 1):
            conf = {"high": "●", "medium": "○", "low": "◌"}[c.confidence]
            topic_tag = f"[{c.topic}]" if c.topic else ""
            print(f"{i:3}. {conf} L{c.line_number:4} {topic_tag:10} {c.text[:70]}{'...' if len(c.text) > 70 else ''}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
