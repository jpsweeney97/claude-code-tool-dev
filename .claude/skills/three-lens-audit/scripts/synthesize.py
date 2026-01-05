#!/usr/bin/env python3
"""
synthesize.py - Synthesize findings from multiple lens outputs

Part of the three-lens-audit skill.

Takes outputs from 3 parallel lens agents and generates a unified
synthesis report with convergent findings, lens-specific insights,
and prioritized recommendations.

Usage:
    python synthesize.py <adversarial.md> <pragmatic.md> <cost-benefit.md>
    python synthesize.py --design <robustness.md> <minimalist.md> <capability.md>
    python synthesize.py outputs/*.md --auto-detect

Exit Codes:
    0  - Success
    1  - General failure
    2  - Invalid arguments
    3  - File not found
    10 - Validation failed (not enough valid outputs)
"""

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional


# ===========================================================================
# RESULT TYPES
# ===========================================================================

@dataclass
class Finding:
    """A single finding from a lens."""
    text: str
    lens: str
    severity: Optional[str] = None
    keywords: Set[str] = field(default_factory=set)

    def __hash__(self):
        return hash(self.text)


@dataclass
class ConvergentFinding:
    """A finding that appears across multiple lenses."""
    description: str
    lenses: Dict[str, str]  # lens_name -> evidence from that lens
    confidence: float  # 0.0-1.0 based on keyword overlap
    keywords: Set[str] = field(default_factory=set)


@dataclass
class SynthesisResult:
    """Complete synthesis output."""
    target: str
    convergent_3: List[ConvergentFinding]  # All 3 lenses
    convergent_2: List[ConvergentFinding]  # 2 lenses
    unique: Dict[str, List[Finding]]  # lens -> unique findings
    recommendations: List[Dict]
    lens_outputs: Dict[str, str]  # raw outputs for reference
    warnings: List[str] = field(default_factory=list)


# ===========================================================================
# TEXT PROCESSING
# ===========================================================================

# Common stop words to ignore in keyword extraction
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
    'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
    'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
    'about', 'against', 'between', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
    'it', 'its', 'they', 'them', 'their', 'we', 'us', 'our', 'you', 'your',
    'he', 'him', 'his', 'she', 'her', 'i', 'me', 'my', 'mine',
}


def extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text."""
    # Lowercase and extract words
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())

    # Filter stop words
    keywords = {w for w in words if w not in STOP_WORDS}

    return keywords


def extract_table_rows(content: str) -> List[Dict[str, str]]:
    """Extract data rows from markdown tables."""
    rows = []
    lines = content.split('\n')
    current_table_headers = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            cells = [c.strip() for c in stripped.split('|')[1:-1]]

            if re.match(r'^[\s\-:|]+$', stripped.replace('|', '')):
                # Separator row - previous row was headers
                in_table = True
            elif not in_table and cells:
                # This might be header row
                current_table_headers = cells
            elif in_table and cells:
                # Data row
                if len(cells) == len(current_table_headers):
                    row = dict(zip(current_table_headers, cells))
                    rows.append(row)
                else:
                    rows.append({'raw': ' | '.join(cells)})
        else:
            if stripped and not stripped.startswith('#'):
                in_table = False

    return rows


def extract_sections(content: str) -> Dict[str, str]:
    """Extract section content from markdown."""
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        # Check for header
        header_match = re.match(r'^#+\s+(.+)$', line)
        bold_match = re.match(r'^\*\*(.+?)\*\*:?\s*$', line)

        if header_match or bold_match:
            # Save previous section
            if current_section:
                sections[current_section.lower()] = '\n'.join(current_content).strip()

            current_section = (header_match or bold_match).group(1)
            current_content = []
        elif current_section:
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section.lower()] = '\n'.join(current_content).strip()

    return sections


def extract_findings(content: str, lens: str) -> List[Finding]:
    """Extract individual findings from lens output."""
    findings = []

    # Extract from tables
    for row in extract_table_rows(content):
        # Get the main content (first non-trivial column)
        text_parts = []
        severity = None

        for key, value in row.items():
            key_lower = key.lower()
            if 'severity' in key_lower or 'priority' in key_lower:
                severity = value
            elif value and len(value) > 10:
                text_parts.append(value)

        if text_parts:
            text = ' | '.join(text_parts)
            keywords = extract_keywords(text)
            findings.append(Finding(
                text=text,
                lens=lens,
                severity=severity,
                keywords=keywords
            ))

    # Extract from sections (for pragmatic lens especially)
    sections = extract_sections(content)
    for section_name, section_content in sections.items():
        # Extract bullet points
        for line in section_content.split('\n'):
            if line.strip().startswith('-') or line.strip().startswith('*'):
                text = line.strip().lstrip('-*').strip()
                if len(text) > 20:
                    keywords = extract_keywords(text)
                    findings.append(Finding(
                        text=text,
                        lens=lens,
                        keywords=keywords
                    ))

    return findings


def calculate_overlap(keywords1: Set[str], keywords2: Set[str]) -> float:
    """Calculate Jaccard similarity between two keyword sets."""
    if not keywords1 or not keywords2:
        return 0.0
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    return len(intersection) / len(union)


def find_convergent_findings(
    findings_by_lens: Dict[str, List[Finding]],
    threshold: float = 0.3
) -> Tuple[List[ConvergentFinding], List[ConvergentFinding]]:
    """
    Find findings that appear across multiple lenses.

    Returns:
        Tuple of (3-lens convergent, 2-lens convergent)
    """
    convergent_3 = []
    convergent_2 = []

    lenses = list(findings_by_lens.keys())
    if len(lenses) < 2:
        return [], []

    # Compare all pairs
    matches = []  # (lens1, finding1, lens2, finding2, overlap)

    for i, lens1 in enumerate(lenses):
        for lens2 in lenses[i + 1:]:
            for f1 in findings_by_lens[lens1]:
                for f2 in findings_by_lens[lens2]:
                    overlap = calculate_overlap(f1.keywords, f2.keywords)
                    if overlap >= threshold:
                        matches.append((lens1, f1, lens2, f2, overlap))

    # Group matches to find 3-lens convergence
    # A finding is 3-lens convergent if lens1-lens2 and lens2-lens3 both match
    if len(lenses) >= 3:
        for lens1, f1, lens2, f2, overlap12 in matches:
            for lens3 in lenses:
                if lens3 in (lens1, lens2):
                    continue
                for f3 in findings_by_lens[lens3]:
                    overlap13 = calculate_overlap(f1.keywords, f3.keywords)
                    overlap23 = calculate_overlap(f2.keywords, f3.keywords)
                    if overlap13 >= threshold and overlap23 >= threshold:
                        # 3-lens convergence
                        avg_overlap = (overlap12 + overlap13 + overlap23) / 3
                        all_keywords = f1.keywords | f2.keywords | f3.keywords
                        convergent = ConvergentFinding(
                            description=f1.text[:100],  # Use first finding as description
                            lenses={
                                lens1: f1.text,
                                lens2: f2.text,
                                lens3: f3.text
                            },
                            confidence=avg_overlap,
                            keywords=all_keywords
                        )
                        # Avoid duplicates
                        if not any(c.keywords == all_keywords for c in convergent_3):
                            convergent_3.append(convergent)

    # 2-lens convergent (not already in 3-lens)
    three_lens_keywords = {frozenset(c.keywords) for c in convergent_3}

    for lens1, f1, lens2, f2, overlap in matches:
        combined_keywords = f1.keywords | f2.keywords
        if frozenset(combined_keywords) not in three_lens_keywords:
            convergent = ConvergentFinding(
                description=f1.text[:100],
                lenses={lens1: f1.text, lens2: f2.text},
                confidence=overlap,
                keywords=combined_keywords
            )
            if not any(c.keywords == combined_keywords for c in convergent_2):
                convergent_2.append(convergent)

    # Sort by confidence
    convergent_3.sort(key=lambda c: -c.confidence)
    convergent_2.sort(key=lambda c: -c.confidence)

    return convergent_3, convergent_2


def identify_unique_findings(
    findings_by_lens: Dict[str, List[Finding]],
    convergent_3: List[ConvergentFinding],
    convergent_2: List[ConvergentFinding],
    threshold: float = 0.3
) -> Dict[str, List[Finding]]:
    """Identify findings unique to each lens (not convergent)."""
    # Collect all keywords from convergent findings
    convergent_keywords = set()
    for c in convergent_3 + convergent_2:
        convergent_keywords.update(c.keywords)

    unique = {}
    for lens, findings in findings_by_lens.items():
        lens_unique = []
        for finding in findings:
            overlap = calculate_overlap(finding.keywords, convergent_keywords)
            if overlap < threshold:
                lens_unique.append(finding)
        unique[lens] = lens_unique

    return unique


# ===========================================================================
# SYNTHESIS GENERATION
# ===========================================================================

def generate_synthesis_markdown(result: SynthesisResult) -> str:
    """Generate the synthesis report in markdown format."""
    lines = [
        f"## Three-Lens Audit: {result.target}",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        ""
    ]

    # Convergent findings (3 lenses)
    if result.convergent_3:
        lines.extend([
            "### Convergent Findings (All 3 Lenses)",
            "",
            "| Finding | " + " | ".join(result.convergent_3[0].lenses.keys()) + " |",
            "|---------|" + "|".join(["----------" for _ in result.convergent_3[0].lenses]) + "|"
        ])
        for c in result.convergent_3:
            cols = [c.description[:50] + "..."] + [v[:50] + "..." for v in c.lenses.values()]
            lines.append("| " + " | ".join(cols) + " |")
        lines.append("")
        lines.append("**Assessment:** [Convergence indicates high-priority issues requiring immediate attention]")
        lines.append("")
    else:
        lines.extend([
            "### Convergent Findings (All 3 Lenses)",
            "",
            "> **Warning:** No findings flagged by all 3 lenses. This is unusual and may indicate:",
            "> - Agent outputs used different terminology for the same issues",
            "> - Target artifact has no cross-cutting concerns",
            "> - Manual synthesis review is strongly recommended",
            "",
            "*Automated keyword matching (Jaccard similarity >= 0.3) may miss semantically related findings stated differently.*",
            ""
        ])

    # Convergent findings (2 lenses)
    if result.convergent_2:
        lines.extend([
            "### Convergent Findings (2 Lenses)",
            "",
            "| Finding | Lenses | Confidence |",
            "|---------|--------|------------|"
        ])
        for c in result.convergent_2[:5]:  # Top 5
            lens_names = ", ".join(c.lenses.keys())
            confidence = f"{c.confidence:.0%}"
            lines.append(f"| {c.description[:60]}... | {lens_names} | {confidence} |")
        lines.append("")

    # Lens-specific insights
    lines.extend([
        "### Lens-Specific Insights",
        ""
    ])

    for lens, findings in result.unique.items():
        lines.append(f"**{lens.title()} Only:**")
        if findings:
            for f in findings[:3]:  # Top 3
                lines.append(f"- {f.text[:100]}...")
        else:
            lines.append("- (No unique findings not covered by convergent issues)")
        lines.append("")

    # Prioritized recommendations
    lines.extend([
        "### Prioritized Recommendations",
        "",
        "| Priority | Issue | Fix | Effort | Convergence |",
        "|----------|-------|-----|--------|-------------|"
    ])

    priority = 1
    # Add 3-lens convergent as P1
    for c in result.convergent_3[:3]:
        lines.append(f"| {priority} | {c.description[:40]}... | [TODO: Fix] | [TODO] | All 3 |")
        priority += 1

    # Add 2-lens convergent as P2-P3
    for c in result.convergent_2[:2]:
        lens_count = len(c.lenses)
        lines.append(f"| {priority} | {c.description[:40]}... | [TODO: Fix] | [TODO] | {lens_count} lenses |")
        priority += 1

    lines.append("")

    # Summary
    lines.extend([
        "### Summary",
        "",
        f"**Overall assessment:** [TODO: 1 sentence verdict based on convergent findings]",
        "",
        f"**Critical path:** [TODO: What MUST be fixed based on {len(result.convergent_3)} all-3 convergent findings]",
        "",
        f"**Optional improvements:** [TODO: Based on {len(result.convergent_2)} 2-lens findings]",
        ""
    ])

    # Warnings
    if result.warnings:
        lines.extend([
            "---",
            "",
            "**Synthesis Warnings:**"
        ])
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines)


# ===========================================================================
# MAIN LOGIC
# ===========================================================================

def synthesize(
    lens_files: Dict[str, Path],
    target: str = "Unknown Target",
    threshold: float = 0.3
) -> SynthesisResult:
    """
    Synthesize findings from multiple lens outputs.

    Args:
        lens_files: Dict mapping lens name to file path
        target: Name of the audit target
        threshold: Keyword overlap threshold for convergence detection (default: 0.3)

    Returns:
        SynthesisResult with all findings organized
    """
    warnings = []
    lens_outputs = {}
    findings_by_lens = {}

    # Load and validate each lens output
    for lens, path in lens_files.items():
        if not path.exists():
            warnings.append(f"File not found for {lens}: {path}")
            continue

        content = path.read_text()
        lens_outputs[lens] = content

        # Extract findings
        findings = extract_findings(content, lens)
        if not findings:
            warnings.append(f"No findings extracted from {lens} output")
        findings_by_lens[lens] = findings

    if len(findings_by_lens) < 2:
        warnings.append("Insufficient lens outputs for synthesis (need at least 2)")
        return SynthesisResult(
            target=target,
            convergent_3=[],
            convergent_2=[],
            unique={},
            recommendations=[],
            lens_outputs=lens_outputs,
            warnings=warnings
        )

    # Find convergent findings
    convergent_3, convergent_2 = find_convergent_findings(findings_by_lens, threshold=threshold)

    # Warn if no 3-lens convergence found
    if len(findings_by_lens) >= 3 and not convergent_3:
        warnings.append("No 3-lens convergent findings detected. Manual synthesis review recommended.")

    # Identify unique findings
    unique = identify_unique_findings(findings_by_lens, convergent_3, convergent_2)

    return SynthesisResult(
        target=target,
        convergent_3=convergent_3,
        convergent_2=convergent_2,
        unique=unique,
        recommendations=[],  # Populated by markdown generation
        lens_outputs=lens_outputs,
        warnings=warnings
    )


# ===========================================================================
# CLI INTERFACE
# ===========================================================================

def detect_lens_from_content(content: str) -> Optional[str]:
    """Attempt to detect lens type from content."""
    content_lower = content.lower()

    # Look for role declarations
    if 'adversarial auditor' in content_lower or 'attack vectors' in content_lower:
        return 'adversarial'
    elif 'pragmatic practitioner' in content_lower or 'what works' in content_lower:
        return 'pragmatic'
    elif 'cost/benefit' in content_lower or 'effort' in content_lower and 'benefit' in content_lower:
        return 'cost-benefit'
    elif 'robustness advocate' in content_lower:
        return 'robustness'
    elif 'minimalist advocate' in content_lower:
        return 'minimalist'
    elif 'capability realist' in content_lower:
        return 'capability'
    elif 'arbiter' in content_lower and 'critical path' in content_lower:
        return 'arbiter'

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Synthesize three-lens-audit findings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s adversarial.md pragmatic.md cost-benefit.md
  %(prog)s --target "CLAUDE.md" adversarial.md pragmatic.md cost-benefit.md
  %(prog)s --design robustness.md minimalist.md capability.md
  %(prog)s outputs/*.md --auto-detect

Output:
  Generates synthesis markdown to stdout. Redirect to save:
  %(prog)s *.md > synthesis.md
        """
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Agent output files (in lens order, or use --auto-detect)"
    )

    parser.add_argument(
        "--target", "-t",
        default="[Audit Target]",
        help="Name of the audit target for the report"
    )

    parser.add_argument(
        "--design",
        action="store_true",
        help="Use design lenses (robustness/minimalist/capability) instead of default"
    )

    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect lens type from file content"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw synthesis data as JSON instead of markdown"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Keyword overlap threshold for convergence detection (default: 0.3)"
    )

    args = parser.parse_args()

    # Determine lens order
    if args.design:
        default_lenses = ['robustness', 'minimalist', 'capability']
    else:
        default_lenses = ['adversarial', 'pragmatic', 'cost-benefit']

    # Map files to lenses
    lens_files = {}

    if args.auto_detect:
        for path in args.files:
            if not path.exists():
                print(f"Warning: File not found: {path}", file=sys.stderr)
                continue
            content = path.read_text()
            lens = detect_lens_from_content(content)
            if lens:
                lens_files[lens] = path
            else:
                print(f"Warning: Could not detect lens type for: {path}", file=sys.stderr)
    else:
        if len(args.files) != len(default_lenses):
            print(f"Error: Expected {len(default_lenses)} files for lenses: {', '.join(default_lenses)}", file=sys.stderr)
            print("Use --auto-detect to detect lens types from content", file=sys.stderr)
            sys.exit(2)

        for lens, path in zip(default_lenses, args.files):
            lens_files[lens] = path

    if len(lens_files) < 2:
        print("Error: Need at least 2 lens outputs for synthesis", file=sys.stderr)
        sys.exit(10)

    # Synthesize
    result = synthesize(lens_files, args.target, threshold=args.threshold)

    # Output
    if args.json:
        import json
        output = {
            "target": result.target,
            "convergent_3": [
                {
                    "description": c.description,
                    "lenses": c.lenses,
                    "confidence": c.confidence,
                    "keywords": list(c.keywords)
                }
                for c in result.convergent_3
            ],
            "convergent_2": [
                {
                    "description": c.description,
                    "lenses": c.lenses,
                    "confidence": c.confidence,
                    "keywords": list(c.keywords)
                }
                for c in result.convergent_2
            ],
            "unique": {
                lens: [{"text": f.text, "severity": f.severity} for f in findings]
                for lens, findings in result.unique.items()
            },
            "warnings": result.warnings
        }
        print(json.dumps(output, indent=2))
    else:
        print(generate_synthesis_markdown(result))

    # Exit code based on whether we found convergent findings
    if result.warnings:
        print("\n---\nWarnings encountered. Review synthesis carefully.", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
