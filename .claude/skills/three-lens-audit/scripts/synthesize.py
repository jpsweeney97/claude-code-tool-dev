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
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Ensure common module is importable when running directly from different directories
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from common import parse_markdown_table


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


@dataclass
class SemanticMatch:
    """A potential semantic match between findings from different lenses."""
    finding_a: Finding
    finding_b: Finding
    shared_element: str
    rationale: str
    confidence: str  # "high", "medium", or "low"


@dataclass
class SemanticReviewResult:
    """Result of LLM semantic review."""
    matches: List[SemanticMatch]
    no_matches: List[Tuple[Finding, Finding]]
    token_usage: Dict[str, int]
    model_used: str


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


def extract_references(text: str) -> Set[str]:
    """Extract file paths, section names, and element names from text.

    Looks for:
    - Backtick-wrapped paths: `config.yaml`, `auth.py`
    - Quoted names: "Getting Started", "API Reference"
    - Section patterns: "the X section", "in X section"

    Returns lowercase set for case-insensitive matching.
    """
    refs = set()

    # Backtick-wrapped file paths (with common extensions)
    for match in re.findall(r'`([^`]+\.(?:md|py|json|yaml|yml|ts|js|toml))`', text):
        refs.add(match.lower())

    # Backtick-wrapped function/element names
    for match in re.findall(r'`([^`]+\(\))`', text):
        refs.add(match.lower())

    # Quoted element names
    for match in re.findall(r'"([^"]+)"', text):
        refs.add(match.lower())

    # Section patterns: "the X section" or "in X section"
    # Match single capitalized word before "section" (e.g., "the Security section")
    for match in re.findall(r'(?:the|in)\s+([A-Za-z]+)\s+[Ss]ection', text):
        refs.add(match.lower())

    return refs


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
    for row in parse_markdown_table(content):
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


def generate_candidate_pairs(
    findings_by_lens: Dict[str, List[Finding]],
    keyword_threshold: float = 0.3,
    max_pairs_per_lens_combo: int = 10
) -> List[Tuple[Finding, Finding]]:
    """
    Generate finding pairs that might be semantically equivalent
    but failed keyword matching.

    Filtering heuristics:
    1. Skip pairs that already passed keyword threshold
    2. Skip pairs from the same lens
    3. Skip pairs with 0 keyword overlap AND no shared references
    4. Prioritize pairs that reference the same file/section/element

    Args:
        findings_by_lens: Dict mapping lens name to list of findings
        keyword_threshold: Pairs above this overlap are already matched
        max_pairs_per_lens_combo: Cap per lens combination (cost control)

    Returns:
        List of (finding_a, finding_b) tuples to review semantically
    """
    candidates = []

    lenses = list(findings_by_lens.keys())

    for i, lens_a in enumerate(lenses):
        for lens_b in lenses[i + 1:]:  # Avoid duplicates and same-lens
            pairs_for_combo = []

            for f_a in findings_by_lens[lens_a]:
                for f_b in findings_by_lens[lens_b]:
                    # Calculate keyword overlap
                    overlap = calculate_overlap(f_a.keywords, f_b.keywords)

                    # Skip if already convergent
                    if overlap >= keyword_threshold:
                        continue

                    # Check for shared references
                    refs_a = extract_references(f_a.text)
                    refs_b = extract_references(f_b.text)
                    shared_refs = refs_a & refs_b

                    # Skip if completely unrelated (no overlap AND no shared refs)
                    if overlap == 0 and not shared_refs:
                        continue

                    # Score by potential relatedness
                    score = overlap + (0.3 if shared_refs else 0)
                    pairs_for_combo.append((f_a, f_b, score))

            # Sort by score descending, take top N
            pairs_for_combo.sort(key=lambda x: -x[2])
            candidates.extend([(a, b) for a, b, _ in pairs_for_combo[:max_pairs_per_lens_combo]])

    return candidates


def format_pairs_for_prompt(pairs: List[Tuple[Finding, Finding]]) -> str:
    """Format finding pairs for the semantic match prompt.

    Args:
        pairs: List of (finding_a, finding_b) tuples

    Returns:
        Formatted markdown string for prompt insertion
    """
    lines = []
    for i, (f_a, f_b) in enumerate(pairs, 1):
        lines.append(f"### Pair {i}")
        lines.append(f'**{f_a.lens.title().replace("-", "/")}:** "{f_a.text}"')
        lines.append(f'**{f_b.lens.title().replace("-", "/")}:** "{f_b.text}"')
        lines.append("")
    return "\n".join(lines)


SEMANTIC_MATCH_PROMPT = '''You identify whether audit findings from different perspectives describe the SAME element.

## Background

Three auditors reviewed a document from opposing perspectives:
- **Adversarial**: Finds vulnerabilities, exploits, gaps (wants completeness)
- **Pragmatic**: Finds usability issues, friction, confusion (wants simplicity)
- **Cost/Benefit**: Finds inefficiencies, low ROI, waste (wants efficiency)
- **Robustness**: Finds gaps, edge cases, incomplete handling (wants durability)
- **Minimalist**: Finds unnecessary complexity, bloat (wants simplicity)
- **Capability**: Finds unrealistic assumptions about system behavior (wants realism)
- **Implementation**: Finds technical feasibility issues (wants correctness)

These perspectives are deliberately opposed. When they agree something is problematic, it's significant.

## Your Task

For each pair of findings below, determine if they describe THE SAME ELEMENT (file, section, feature, concept).

**Key distinction:**
- SAME element, different perspectives → MATCH
- SAME problem type, different elements → NOT A MATCH

## Decision Process

For each pair, follow these steps:

1. **Extract elements**: What specific thing does each finding reference?
2. **Compare elements**: Are they the same file/section/feature/concept?
3. **Assess confidence**: How certain are you they're the same element?

## Examples

### TRUE MATCHES (same element, different lenses)

**Example 1: Both reference same file**
- Adversarial: "Token count for `principles.md` is vague, may exceed context limits"
- Pragmatic: "`principles.md` at 8K tokens is too heavy to load casually"
- Element A: principles.md | Element B: principles.md | **MATCH: yes**
- Rationale: Both identify principles.md as problematically large
- Confidence: high (explicit file reference in both)

**Example 2: Both reference same function**
- Adversarial: "The `validateInput()` function has no sanitization, allowing injection"
- Pragmatic: "Users get cryptic errors when `validateInput()` receives bad data"
- Element A: validateInput() | Element B: validateInput() | **MATCH: yes**
- Rationale: Both describe input handling issues in the same function
- Confidence: high (explicit function reference in both)

**Example 3: Same concept, different vocabulary**
- Adversarial: "Priority ordering (P2 vs P7) is subjective, can justify contradictory edits"
- Cost/Benefit: "Conflict resolution section has high cognitive overhead for unclear benefit"
- Element A: priority/conflict resolution | Element B: conflict resolution | **MATCH: yes**
- Rationale: Both describe the priority/conflict system as problematic
- Confidence: medium (same concept, different terms)

### FALSE MATCHES (same category, different elements)

**Example 4: Both about "missing X" but different X**
- Adversarial: "Missing input validation in the auth module"
- Pragmatic: "Missing examples in the tutorial section"
- Element A: auth module validation | Element B: tutorial examples | **MATCH: no**
- Rationale: Different elements entirely (auth vs tutorial)

**Example 5: Same file, different sections**
- Adversarial: "`README.md` has outdated security warnings"
- Pragmatic: "`README.md` installation instructions are unclear"
- Element A: README.md security section | Element B: README.md installation section
- **MATCH: no** — Same file but different sections/concerns

## Confidence Calibration

| Confidence | Criteria |
|------------|----------|
| **high** | Same element explicitly named in both (file, function, section) |
| **medium** | Same element implied but named differently, OR same concept described |
| **low** | Possibly the same element, but significant ambiguity remains |

**When in doubt, say NO.** False positives (claiming match when none exists) are worse than false negatives.

## Finding Pairs to Review

{pairs_formatted}

## Output Format

For EACH pair, respond EXACTLY in this format:

```
PAIR N:
ELEMENT_A: [element from first finding]
ELEMENT_B: [element from second finding]
MATCH: yes|no
SHARED_ELEMENT: [the common element, or "none"]
RATIONALE: [1 sentence explaining your decision]
CONFIDENCE: high|medium|low
```

Where N is the pair number (1, 2, 3, etc.). Respond for all pairs in order.'''


def parse_semantic_response(
    response: str,
    pairs: List[Tuple[Finding, Finding]]
) -> SemanticReviewResult:
    """Parse LLM response into structured matches.

    Args:
        response: Raw LLM response text
        pairs: Original pairs that were reviewed

    Returns:
        SemanticReviewResult with matches and no_matches populated
    """
    matches = []
    no_matches = []

    # Pattern for structured output - flexible whitespace handling
    pattern = re.compile(
        r'PAIR\s*(\d+).*?'
        r'ELEMENT_A:\s*(.+?)\s*'
        r'ELEMENT_B:\s*(.+?)\s*'
        r'MATCH:\s*(yes|no)\s*'
        r'SHARED_ELEMENT:\s*(.+?)\s*'
        r'RATIONALE:\s*(.+?)\s*'
        r'CONFIDENCE:\s*(high|medium|low|n/?a|-)',
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(response):
        pair_num = int(match.group(1)) - 1  # Convert to 0-indexed

        if pair_num >= len(pairs) or pair_num < 0:
            continue

        f_a, f_b = pairs[pair_num]
        is_match = match.group(4).lower() == 'yes'

        if is_match:
            matches.append(SemanticMatch(
                finding_a=f_a,
                finding_b=f_b,
                shared_element=match.group(5).strip(),
                rationale=match.group(6).strip(),
                confidence=match.group(7).lower().replace('/', '')
            ))
        else:
            no_matches.append((f_a, f_b))

    return SemanticReviewResult(
        matches=matches,
        no_matches=no_matches,
        token_usage={},  # Filled by caller
        model_used=""    # Filled by caller
    )


def run_semantic_review(
    pairs: List[Tuple[Finding, Finding]],
    model: str = "haiku"
) -> SemanticReviewResult:
    """Run semantic review on finding pairs using Claude CLI.

    Args:
        pairs: List of (finding_a, finding_b) tuples to review
        model: Model to use (haiku, sonnet, opus)

    Returns:
        SemanticReviewResult with matches and metadata
    """
    if not pairs:
        return SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used=model
        )

    # Format the prompt
    pairs_formatted = format_pairs_for_prompt(pairs)
    full_prompt = SEMANTIC_MATCH_PROMPT.format(pairs_formatted=pairs_formatted)

    # Call Claude CLI
    # Using print mode (-p) for non-interactive output
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", model, full_prompt],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            print(f"Warning: Claude CLI failed (exit {result.returncode})", file=sys.stderr)
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}", file=sys.stderr)
            return SemanticReviewResult(
                matches=[],
                no_matches=[],
                token_usage={},
                model_used=model
            )

        response = result.stdout

    except subprocess.TimeoutExpired:
        print("Warning: Claude CLI timed out after 120s", file=sys.stderr)
        return SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used=model
        )
    except FileNotFoundError:
        print("Warning: 'claude' CLI not found - semantic review skipped", file=sys.stderr)
        return SemanticReviewResult(
            matches=[],
            no_matches=[],
            token_usage={},
            model_used=model
        )

    # Parse response
    semantic_result = parse_semantic_response(response, pairs)
    semantic_result.model_used = model

    return semantic_result


def merge_semantic_matches(
    matches: List[SemanticMatch],
    convergent_3: List[ConvergentFinding],
    convergent_2: List[ConvergentFinding]
) -> None:
    """Merge semantic matches into convergent findings (mutates lists in place).

    Strategy:
    1. For each semantic match, check if either finding is already in a 2-lens convergent
    2. If so, try to extend to 3-lens convergent
    3. Otherwise, create new 2-lens convergent

    Args:
        matches: List of semantic matches to merge
        convergent_3: Existing 3-lens convergent findings (mutated)
        convergent_2: Existing 2-lens convergent findings (mutated)
    """
    for match in matches:
        lens_a = match.finding_a.lens
        lens_b = match.finding_b.lens
        combined_keywords = match.finding_a.keywords | match.finding_b.keywords

        # Check for extension to 3-lens
        extended = False
        for c2 in convergent_2[:]:  # Iterate over copy since we may modify
            # Check if one lens from the match is in this convergent finding
            if lens_a in c2.lenses and lens_b not in c2.lenses:
                # Extend with lens_b
                new_lenses = dict(c2.lenses)
                new_lenses[lens_b] = match.finding_b.text
                new_keywords = c2.keywords | combined_keywords

                convergent_3.append(ConvergentFinding(
                    description=c2.description,
                    lenses=new_lenses,
                    confidence=c2.confidence * 0.9,  # Slightly lower confidence
                    keywords=new_keywords
                ))
                convergent_2.remove(c2)
                extended = True
                break

            elif lens_b in c2.lenses and lens_a not in c2.lenses:
                # Extend with lens_a
                new_lenses = dict(c2.lenses)
                new_lenses[lens_a] = match.finding_a.text
                new_keywords = c2.keywords | combined_keywords

                convergent_3.append(ConvergentFinding(
                    description=c2.description,
                    lenses=new_lenses,
                    confidence=c2.confidence * 0.9,
                    keywords=new_keywords
                ))
                convergent_2.remove(c2)
                extended = True
                break

        if extended:
            continue

        # Check for duplicate before creating new convergent
        is_duplicate = False
        for c2 in convergent_2:
            if lens_a in c2.lenses and lens_b in c2.lenses:
                # Already have this lens combination
                keyword_overlap = calculate_overlap(combined_keywords, c2.keywords)
                if keyword_overlap > 0.5:
                    is_duplicate = True
                    break

        if is_duplicate:
            continue

        # Create new 2-lens convergent
        convergent_2.append(ConvergentFinding(
            description=match.shared_element,
            lenses={
                lens_a: match.finding_a.text,
                lens_b: match.finding_b.text
            },
            confidence=0.8 if match.confidence == "high" else 0.6 if match.confidence == "medium" else 0.4,
            keywords=combined_keywords
        ))


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
            "> **⚠️ No automated 3-lens convergence detected.**",
            ">",
            "> Keyword matching (Jaccard similarity ≥ 0.3) often misses semantically equivalent findings.",
            ">",
            "> **Action required:** Manually scan each lens output for:",
            "> - Same element described with different terminology",
            "> - Same root cause surfaced through different perspectives",
            "> - Issues that Adversarial calls \"exploitable\", Pragmatic calls \"confusing\", Cost/Benefit calls \"high-effort\"",
            ">",
            "> See `references/agent-prompts.md#synthesis-template` for semantic equivalence examples.",
            "",
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


def generate_implementation_spec_markdown(result: SynthesisResult) -> str:
    """Generate implementation spec format for Claude Code execution.

    Maps synthesis findings to priority levels:
    - P1: All 3 lenses convergent (detailed implementation steps)
    - P2: 2 lenses convergent (high-level action + done criteria)
    - P3: Single lens unique (brief description)

    Args:
        result: SynthesisResult from synthesize()

    Returns:
        Markdown string in implementation spec format
    """
    lines = [
        f"# Implementation Spec: {result.target}",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Summary",
        "",
        "| Priority | Count | Convergence | Detail Level |",
        "|----------|-------|-------------|--------------|",
    ]

    p3_count = sum(len(findings) for findings in result.unique.values())

    lines.append(f"| P1 | {len(result.convergent_3)} | All 3 lenses | Detailed |")
    lines.append(f"| P2 | {len(result.convergent_2)} | 2 lenses | High-level |")
    lines.append(f"| P3 | {p3_count} | Single lens | Brief |")
    lines.append("")

    # P1 Tasks (Detailed)
    if result.convergent_3:
        lines.extend([
            "## P1 Tasks (Detailed)",
            "",
            "*These issues were flagged by all 3 lenses -- highest priority.*",
            ""
        ])

        for i, c in enumerate(result.convergent_3, 1):
            lines.extend([
                f"### Task 1.{i}: {c.description}",
                "",
                f"**File:** `{result.target}`",
                f"**Convergence:** All 3 lenses (confidence: {c.confidence:.0%})",
                "",
                "**Rationale:**",
            ])
            for lens_name, evidence in c.lenses.items():
                truncated = evidence[:80] + "..." if len(evidence) > 80 else evidence
                lines.append(f"- {lens_name.title()}: \"{truncated}\"")

            lines.extend([
                "",
                "**Implementation:**",
                "1. Locate the relevant section in the target file",
                "2. Address the issue identified by all three perspectives",
                "3. Verify the fix satisfies each lens's concern",
                "",
                "**Done Criteria:**",
                "- [ ] Issue no longer flagged by adversarial review",
                "- [ ] Pragmatic usability improved",
                "- [ ] Cost/benefit ratio justified",
                "",
            ])

    # P2 Tasks (High-Level)
    if result.convergent_2:
        lines.extend([
            "## P2 Tasks (High-Level)",
            "",
            "*These issues were flagged by 2 lenses.*",
            ""
        ])

        for i, c in enumerate(result.convergent_2, 1):
            lens_names = ", ".join(c.lenses.keys())
            lines.extend([
                f"### Task 2.{i}: {c.description}",
                "",
                f"**Lenses:** {lens_names} (confidence: {c.confidence:.0%})",
                f"**Action:** Address the concern shared by both perspectives",
                f"**Done Criteria:** Issue no longer flagged by either lens",
                "",
            ])

    # P3 Tasks (Optional)
    if p3_count > 0:
        lines.extend([
            "## P3 Tasks (Optional)",
            "",
            "*Single-lens findings -- consider if time permits.*",
            ""
        ])

        task_num = 1
        for lens, findings in result.unique.items():
            for f in findings[:3]:  # Top 3 per lens
                truncated = f.text[:60] + "..." if len(f.text) > 60 else f.text
                lines.extend([
                    f"### Task 3.{task_num}: {truncated}",
                    "",
                    f"**Lens:** {lens.title()}",
                    f"**Action:** {f.text[:100]}",
                    "",
                ])
                task_num += 1

    return "\n".join(lines)


# ===========================================================================
# MAIN LOGIC
# ===========================================================================

def synthesize(
    lens_files: Dict[str, Path],
    target: str = "Unknown Target",
    threshold: float = 0.3,
    semantic_review: bool = False,
    semantic_model: str = "haiku",
    max_semantic_pairs: int = 20
) -> SynthesisResult:
    """
    Synthesize findings from multiple lens outputs.

    Args:
        lens_files: Dict mapping lens name to file path
        target: Name of the audit target
        threshold: Keyword overlap threshold for convergence detection (default: 0.3)
        semantic_review: Enable LLM-assisted semantic review for additional matches
        semantic_model: Model for semantic review (haiku, sonnet, opus)
        max_semantic_pairs: Maximum pairs to review semantically (cost control)

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

    # Semantic review for additional matches
    if semantic_review and len(findings_by_lens) >= 2:
        # Generate candidate pairs (findings that failed keyword matching)
        candidates = generate_candidate_pairs(
            findings_by_lens,
            keyword_threshold=threshold,
            max_pairs_per_lens_combo=max_semantic_pairs // max(1, len(findings_by_lens) - 1)
        )

        if candidates:
            # Run LLM semantic review
            semantic_result = run_semantic_review(candidates, model=semantic_model)

            if semantic_result.matches:
                # Merge matches into convergent findings
                merge_semantic_matches(semantic_result.matches, convergent_3, convergent_2)

                # Note the enhancement in warnings
                warnings.append(f"Semantic review found {len(semantic_result.matches)} additional matches using {semantic_model}")

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
