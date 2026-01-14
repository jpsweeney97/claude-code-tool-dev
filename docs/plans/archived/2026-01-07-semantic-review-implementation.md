# Semantic Review Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add LLM-assisted semantic review to three-lens-audit synthesis to catch semantically equivalent findings that keyword matching misses.

**Architecture:** Extend `synthesize.py` with candidate pair generation, LLM semantic matching via Claude API subprocess call, and result merging. Add CLI flags to `run_audit.py finalize` for user control. Cost-effective: uses Haiku by default (~$0.002-0.01 per synthesis).

**Tech Stack:** Python 3.12, subprocess (for `claude` CLI), dataclasses, argparse, re

---

## Task 1: Add SemanticMatch and SemanticReviewResult dataclasses

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:42-73` (after existing dataclasses)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py` (create)

**Step 1: Write the failing test**

Create test file:

```python
#!/usr/bin/env python3
"""Tests for semantic review functionality in synthesize.py."""

import pytest
from synthesize import SemanticMatch, SemanticReviewResult, Finding


def test_semantic_match_creation():
    """SemanticMatch dataclass should hold match details."""
    f_a = Finding(text="config has no validation", lens="adversarial")
    f_b = Finding(text="config errors are confusing", lens="pragmatic")

    match = SemanticMatch(
        finding_a=f_a,
        finding_b=f_b,
        shared_element="config.yaml validation",
        rationale="Both describe config validation issues",
        confidence="high"
    )

    assert match.finding_a == f_a
    assert match.finding_b == f_b
    assert match.shared_element == "config.yaml validation"
    assert match.confidence == "high"


def test_semantic_review_result_creation():
    """SemanticReviewResult should hold review output."""
    result = SemanticReviewResult(
        matches=[],
        no_matches=[],
        token_usage={"input": 1000, "output": 200},
        model_used="haiku"
    )

    assert result.matches == []
    assert result.model_used == "haiku"
    assert result.token_usage["input"] == 1000
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_semantic_match_creation -v`
Expected: FAIL with "cannot import name 'SemanticMatch' from 'synthesize'"

**Step 3: Write minimal implementation**

Add after line 73 in `synthesize.py`:

```python
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
```

Also add `Tuple` to the typing imports on line 31:
```python
from typing import List, Dict, Set, Tuple, Optional, Literal
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add SemanticMatch and SemanticReviewResult dataclasses"
```

---

## Task 2: Implement extract_references() helper

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:100-110` (after extract_keywords)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from synthesize import extract_references


def test_extract_references_finds_file_paths():
    """extract_references should find backtick-wrapped file paths."""
    text = "The `config.yaml` file has issues and `auth.py` is broken"
    refs = extract_references(text)
    assert "config.yaml" in refs
    assert "auth.py" in refs


def test_extract_references_finds_quoted_names():
    """extract_references should find quoted element names."""
    text = 'The "Getting Started" section and "API Reference" need work'
    refs = extract_references(text)
    assert "getting started" in refs
    assert "api reference" in refs


def test_extract_references_finds_section_patterns():
    """extract_references should find 'the X section' patterns."""
    text = "Check the Security section and in Overview section"
    refs = extract_references(text)
    assert "security" in refs
    assert "overview" in refs


def test_extract_references_returns_lowercase():
    """extract_references should normalize to lowercase."""
    text = "`README.md` in the Security Section"
    refs = extract_references(text)
    assert "readme.md" in refs
    assert "security" in refs
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_extract_references_finds_file_paths -v`
Expected: FAIL with "cannot import name 'extract_references'"

**Step 3: Write minimal implementation**

Add after `extract_keywords()` function (around line 110):

```python
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
    for match in re.findall(r'(?:the|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+section', text, re.IGNORECASE):
        refs.add(match.lower())

    return refs
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_extract_references_finds_file_paths test_synthesize.py::test_extract_references_finds_quoted_names test_synthesize.py::test_extract_references_finds_section_patterns test_synthesize.py::test_extract_references_returns_lowercase -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add extract_references() helper for semantic review"
```

---

## Task 3: Implement generate_candidate_pairs()

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:270-300` (after find_convergent_findings)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from synthesize import generate_candidate_pairs, Finding


def test_generate_candidate_pairs_excludes_keyword_matches():
    """Pairs that already passed keyword threshold should be excluded."""
    findings = {
        "adversarial": [Finding("tokens too large", "adversarial", keywords={"tokens", "large", "context"})],
        "pragmatic": [Finding("tokens too big", "pragmatic", keywords={"tokens", "big", "context"})]
    }
    # These share "tokens" and "context" so keyword overlap is high
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 0


def test_generate_candidate_pairs_includes_shared_refs():
    """Pairs with shared references should be included even with low keyword overlap."""
    findings = {
        "adversarial": [Finding("`config.yaml` may exceed limits", "adversarial", keywords={"exceed", "limits"})],
        "pragmatic": [Finding("`config.yaml` is confusing to edit", "pragmatic", keywords={"confusing", "edit"})]
    }
    # Different keywords but both reference config.yaml
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 1


def test_generate_candidate_pairs_skips_same_lens():
    """Pairs from the same lens should be excluded."""
    findings = {
        "adversarial": [
            Finding("`config.yaml` issue A", "adversarial", keywords={"config", "issue"}),
            Finding("`config.yaml` issue B", "adversarial", keywords={"config", "problem"})
        ]
    }
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3)
    assert len(candidates) == 0


def test_generate_candidate_pairs_respects_max_pairs():
    """Should cap pairs per lens combination."""
    findings = {
        "adversarial": [Finding(f"`file{i}.py` issue", "adversarial", keywords={f"file{i}"}) for i in range(10)],
        "pragmatic": [Finding(f"`file{i}.py` confusing", "pragmatic", keywords={f"conf{i}"}) for i in range(10)]
    }
    # All pairs have zero overlap but same file refs
    candidates = generate_candidate_pairs(findings, keyword_threshold=0.3, max_pairs_per_lens_combo=5)
    assert len(candidates) <= 5
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_generate_candidate_pairs_excludes_keyword_matches -v`
Expected: FAIL with "cannot import name 'generate_candidate_pairs'"

**Step 3: Write minimal implementation**

Add after `find_convergent_findings()` (around line 270):

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_generate_candidate_pairs_excludes_keyword_matches test_synthesize.py::test_generate_candidate_pairs_includes_shared_refs test_synthesize.py::test_generate_candidate_pairs_skips_same_lens test_synthesize.py::test_generate_candidate_pairs_respects_max_pairs -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add generate_candidate_pairs() for semantic review"
```

---

## Task 4: Implement format_pairs_for_prompt()

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py` (after generate_candidate_pairs)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from synthesize import format_pairs_for_prompt, Finding


def test_format_pairs_for_prompt_includes_lens_labels():
    """format_pairs_for_prompt should include capitalized lens names."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert "**Adversarial:**" in formatted
    assert "**Pragmatic:**" in formatted


def test_format_pairs_for_prompt_numbers_pairs():
    """format_pairs_for_prompt should number pairs sequentially."""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic")),
        (Finding("issue C", "cost-benefit"), Finding("issue D", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert "### Pair 1" in formatted
    assert "### Pair 2" in formatted


def test_format_pairs_for_prompt_quotes_finding_text():
    """format_pairs_for_prompt should quote finding text."""
    pairs = [
        (Finding("config has issues", "adversarial"), Finding("config is broken", "pragmatic"))
    ]
    formatted = format_pairs_for_prompt(pairs)
    assert '"config has issues"' in formatted
    assert '"config is broken"' in formatted
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_format_pairs_for_prompt_includes_lens_labels -v`
Expected: FAIL with "cannot import name 'format_pairs_for_prompt'"

**Step 3: Write minimal implementation**

Add after `generate_candidate_pairs()`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_format_pairs_for_prompt_includes_lens_labels test_synthesize.py::test_format_pairs_for_prompt_numbers_pairs test_synthesize.py::test_format_pairs_for_prompt_quotes_finding_text -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add format_pairs_for_prompt() for semantic review"
```

---

## Task 5: Add SEMANTIC_MATCH_PROMPT constant

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py` (after format_pairs_for_prompt)
- No test needed (constant string)

**Step 1: Add the prompt constant**

Add after `format_pairs_for_prompt()`:

```python
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
```

**Step 2: Verify syntax is correct**

Run: `cd .claude/skills/three-lens-audit/scripts && python -c "from synthesize import SEMANTIC_MATCH_PROMPT; print(len(SEMANTIC_MATCH_PROMPT))"`
Expected: Prints number ~3000-4000 (no syntax error)

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py
git commit -m "feat(three-lens-audit): add SEMANTIC_MATCH_PROMPT constant"
```

---

## Task 6: Implement parse_semantic_response()

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py` (after SEMANTIC_MATCH_PROMPT)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from synthesize import parse_semantic_response, Finding, SemanticMatch


def test_parse_semantic_response_extracts_matches():
    """parse_semantic_response should extract yes matches."""
    response = """
PAIR 1:
ELEMENT_A: config.yaml validation
ELEMENT_B: config.yaml errors
MATCH: yes
SHARED_ELEMENT: config.yaml validation
RATIONALE: Both describe config.yaml validation issues
CONFIDENCE: high

PAIR 2:
ELEMENT_A: README security
ELEMENT_B: auth.py tokens
MATCH: no
SHARED_ELEMENT: none
RATIONALE: Different elements entirely
CONFIDENCE: n/a
"""
    pairs = [
        (Finding("config no validation", "adversarial"), Finding("config confusing", "pragmatic")),
        (Finding("README security", "adversarial"), Finding("auth tokens", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    assert len(result.matches) == 1
    assert result.matches[0].shared_element == "config.yaml validation"
    assert result.matches[0].confidence == "high"
    assert len(result.no_matches) == 1


def test_parse_semantic_response_handles_medium_confidence():
    """parse_semantic_response should handle medium confidence matches."""
    response = """
PAIR 1:
ELEMENT_A: caching layer
ELEMENT_B: cache invalidation
MATCH: yes
SHARED_ELEMENT: cache
RATIONALE: Both reference caching
CONFIDENCE: medium
"""
    pairs = [
        (Finding("cache vulnerable", "adversarial"), Finding("cache overhead", "cost-benefit"))
    ]
    result = parse_semantic_response(response, pairs)

    assert len(result.matches) == 1
    assert result.matches[0].confidence == "medium"


def test_parse_semantic_response_handles_malformed_response():
    """parse_semantic_response should gracefully handle missing fields."""
    response = """
PAIR 1:
MATCH: yes
SHARED_ELEMENT: something
"""
    pairs = [
        (Finding("issue A", "adversarial"), Finding("issue B", "pragmatic"))
    ]
    result = parse_semantic_response(response, pairs)

    # Should not crash, may return empty if can't parse
    assert isinstance(result.matches, list)
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_parse_semantic_response_extracts_matches -v`
Expected: FAIL with "cannot import name 'parse_semantic_response'"

**Step 3: Write minimal implementation**

Add after `SEMANTIC_MATCH_PROMPT`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_parse_semantic_response_extracts_matches test_synthesize.py::test_parse_semantic_response_handles_medium_confidence test_synthesize.py::test_parse_semantic_response_handles_malformed_response -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add parse_semantic_response() for LLM output"
```

---

## Task 7: Implement run_semantic_review() with Claude CLI subprocess

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test (integration-style, with mock)**

Add to test file:

```python
import subprocess
from unittest.mock import patch, MagicMock
from synthesize import run_semantic_review, Finding


def test_run_semantic_review_calls_claude_cli():
    """run_semantic_review should call claude CLI with correct arguments."""
    pairs = [
        (Finding("config no validation", "adversarial"), Finding("config confusing", "pragmatic"))
    ]

    mock_response = """
PAIR 1:
ELEMENT_A: config.yaml
ELEMENT_B: config.yaml
MATCH: yes
SHARED_ELEMENT: config.yaml
RATIONALE: Same file
CONFIDENCE: high
"""

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            stdout=mock_response,
            returncode=0
        )

        result = run_semantic_review(pairs, model="haiku")

        # Verify subprocess was called
        assert mock_run.called
        call_args = mock_run.call_args

        # Should use claude CLI with model flag
        assert "claude" in call_args[0][0]
        assert "--model" in call_args[0][0]

        # Should return parsed result
        assert result.model_used == "haiku"
        assert len(result.matches) == 1


def test_run_semantic_review_handles_empty_pairs():
    """run_semantic_review should handle empty pair list."""
    result = run_semantic_review([], model="haiku")

    assert result.matches == []
    assert result.no_matches == []
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_run_semantic_review_calls_claude_cli -v`
Expected: FAIL with "cannot import name 'run_semantic_review'"

**Step 3: Write minimal implementation**

Add `import subprocess` at top of file, then add after `parse_semantic_response()`:

```python
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
            # Return empty result on error
            return SemanticReviewResult(
                matches=[],
                no_matches=[],
                token_usage={},
                model_used=model
            )

        response = result.stdout

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # Claude CLI not available or timed out
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_run_semantic_review_calls_claude_cli test_synthesize.py::test_run_semantic_review_handles_empty_pairs -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add run_semantic_review() with Claude CLI integration"
```

---

## Task 8: Implement merge_semantic_matches()

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py`
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from synthesize import merge_semantic_matches, SemanticMatch, ConvergentFinding, Finding


def test_merge_semantic_matches_creates_convergent_finding():
    """merge_semantic_matches should create new ConvergentFinding from match."""
    match = SemanticMatch(
        finding_a=Finding("config no validation", "adversarial", keywords={"config", "validation"}),
        finding_b=Finding("config confusing", "pragmatic", keywords={"config", "confusing"}),
        shared_element="config.yaml",
        rationale="Both about config",
        confidence="high"
    )

    convergent_3 = []
    convergent_2 = []

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should create a 2-lens convergent finding
    assert len(convergent_2) == 1
    assert "adversarial" in convergent_2[0].lenses
    assert "pragmatic" in convergent_2[0].lenses


def test_merge_semantic_matches_extends_to_3_lens():
    """If a 2-match involves a lens already in convergent_2, try to extend to 3."""
    existing = ConvergentFinding(
        description="config issue",
        lenses={"adversarial": "validation", "cost-benefit": "overhead"},
        confidence=0.5,
        keywords={"config"}
    )
    convergent_3 = []
    convergent_2 = [existing]

    # New match involves adversarial and pragmatic
    match = SemanticMatch(
        finding_a=Finding("config no validation", "adversarial", keywords={"config"}),
        finding_b=Finding("config confusing", "pragmatic", keywords={"config"}),
        shared_element="config.yaml",
        rationale="Both about config",
        confidence="high"
    )

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should extend to 3-lens
    assert len(convergent_3) == 1
    assert len(convergent_3[0].lenses) == 3


def test_merge_semantic_matches_avoids_duplicates():
    """merge_semantic_matches should not duplicate existing findings."""
    existing = ConvergentFinding(
        description="config issue",
        lenses={"adversarial": "validation", "pragmatic": "confusing"},
        confidence=0.5,
        keywords={"config", "validation", "confusing"}
    )
    convergent_2 = [existing]
    convergent_3 = []

    # Match with same findings
    match = SemanticMatch(
        finding_a=Finding("validation", "adversarial", keywords={"config", "validation"}),
        finding_b=Finding("confusing", "pragmatic", keywords={"config", "confusing"}),
        shared_element="config",
        rationale="Same",
        confidence="high"
    )

    merge_semantic_matches([match], convergent_3, convergent_2)

    # Should not create duplicate
    assert len(convergent_2) == 1
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_merge_semantic_matches_creates_convergent_finding -v`
Expected: FAIL with "cannot import name 'merge_semantic_matches'"

**Step 3: Write minimal implementation**

Add after `run_semantic_review()`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_merge_semantic_matches_creates_convergent_finding test_synthesize.py::test_merge_semantic_matches_extends_to_3_lens test_synthesize.py::test_merge_semantic_matches_avoids_duplicates -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): add merge_semantic_matches() for convergent finding extension"
```

---

## Task 9: Update synthesize() to use semantic review

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/synthesize.py:534-599` (synthesize function)
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Write the failing test**

Add to test file:

```python
from unittest.mock import patch
from synthesize import synthesize
from pathlib import Path
import tempfile


def test_synthesize_with_semantic_review_flag():
    """synthesize() with semantic_review=True should call semantic review."""
    # Create temp files with lens outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        adv_path.write_text("""
# Adversarial Audit

| Issue | Severity |
|-------|----------|
| `config.yaml` has no validation | High |
""")
        prag_path.write_text("""
# Pragmatic Audit

| Issue | Impact |
|-------|--------|
| `config.yaml` errors are confusing | Medium |
""")

        # Mock run_semantic_review to track if it's called
        with patch('synthesize.run_semantic_review') as mock_review:
            mock_review.return_value = SemanticReviewResult(
                matches=[],
                no_matches=[],
                token_usage={},
                model_used="haiku"
            )

            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test",
                semantic_review=True
            )

            # Should have called semantic review
            assert mock_review.called


def test_synthesize_without_semantic_review_flag():
    """synthesize() with semantic_review=False should skip semantic review."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adv_path = Path(tmpdir) / "adversarial.md"
        prag_path = Path(tmpdir) / "pragmatic.md"

        adv_path.write_text("# Adversarial\n\n| Issue | Severity |\n|-------|----------|\n| issue A | High |")
        prag_path.write_text("# Pragmatic\n\n| Issue | Impact |\n|-------|--------|\n| issue B | Medium |")

        with patch('synthesize.run_semantic_review') as mock_review:
            result = synthesize(
                {"adversarial": adv_path, "pragmatic": prag_path},
                target="test",
                semantic_review=False
            )

            # Should NOT have called semantic review
            assert not mock_review.called
```

**Step 2: Run test to verify it fails**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_synthesize_with_semantic_review_flag -v`
Expected: FAIL (synthesize doesn't accept semantic_review parameter yet)

**Step 3: Update synthesize() function signature and implementation**

Modify the `synthesize()` function (around line 534):

```python
def synthesize(
    lens_files: Dict[str, Path],
    target: str = "Unknown Target",
    threshold: float = 0.3,
    semantic_review: bool = False,  # NEW
    semantic_model: str = "haiku",  # NEW
    max_semantic_pairs: int = 20    # NEW
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

    # Find convergent findings (keyword-based)
    convergent_3, convergent_2 = find_convergent_findings(findings_by_lens, threshold=threshold)

    # NEW: Semantic review for additional matches
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
```

**Step 4: Run test to verify it passes**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py::test_synthesize_with_semantic_review_flag test_synthesize.py::test_synthesize_without_semantic_review_flag -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/synthesize.py .claude/skills/three-lens-audit/scripts/test_synthesize.py
git commit -m "feat(three-lens-audit): integrate semantic review into synthesize()"
```

---

## Task 10: Add CLI flags to run_audit.py finalize

**Files:**
- Modify: `.claude/skills/three-lens-audit/scripts/run_audit.py:538-571` (finalize_parser)
- Test: Manual CLI test

**Step 1: Update finalize function signature**

Modify `finalize()` in run_audit.py (around line 301):

```python
def finalize(
    output_files: List[Path],
    target: str = "[Audit Target]",
    preset: str = "default",
    auto_detect: bool = False,
    threshold: float = 0.3,
    semantic_review: bool = False,  # NEW
    semantic_model: str = "haiku",  # NEW
    max_semantic_pairs: int = 20    # NEW
) -> FinalizeResult:
    """Validate outputs and synthesize findings."""
    warnings = []

    # ... existing lens_files detection code ...

    # Validate
    validation = validate_outputs(lens_files)

    if not validation.all_passed:
        failed = [l for l, (p, _) in validation.results.items() if not p]
        warnings.append(f"Validation failed for: {', '.join(failed)}")

        if validation.passed_count < 2:
            return FinalizeResult(
                validation=validation,
                synthesis_result=None,
                warnings=warnings + ["Insufficient valid outputs for synthesis (need ≥2)"]
            )

    # Filter to valid outputs only
    valid_lens_files = {l: p for l, p in lens_files.items()
                        if validation.results.get(l, (False, ""))[0]}

    # Synthesize (with semantic review if enabled)
    result = synthesize(
        valid_lens_files,
        target,
        threshold=threshold,
        semantic_review=semantic_review,  # NEW
        semantic_model=semantic_model,     # NEW
        max_semantic_pairs=max_semantic_pairs  # NEW
    )

    if result.warnings:
        warnings.extend(result.warnings)

    return FinalizeResult(
        validation=validation,
        synthesis_result=result,
        warnings=warnings
    )
```

**Step 2: Add CLI arguments to finalize_parser**

Modify the finalize subparser (around line 556):

```python
    finalize_parser.add_argument(
        "--semantic-review",
        action="store_true",
        help="Enable LLM-assisted semantic review for additional convergent findings"
    )
    finalize_parser.add_argument(
        "--semantic-model",
        choices=["haiku", "sonnet", "opus"],
        default="haiku",
        help="Model for semantic review (default: haiku, cheapest)"
    )
    finalize_parser.add_argument(
        "--max-pairs",
        type=int,
        default=20,
        help="Maximum pairs to review semantically (cost control, default: 20)"
    )
```

**Step 3: Update cmd_finalize to pass new arguments**

Modify `cmd_finalize()` (around line 427):

```python
def cmd_finalize(args):
    """Handle finalize subcommand."""
    output_files = [Path(f) for f in args.files]

    result = finalize(
        output_files,
        target=args.target,
        preset=args.preset,
        auto_detect=args.auto_detect,
        threshold=args.threshold,
        semantic_review=args.semantic_review,  # NEW
        semantic_model=args.semantic_model,     # NEW
        max_semantic_pairs=args.max_pairs       # NEW
    )

    # ... rest of function unchanged ...
```

**Step 4: Test CLI help output**

Run: `cd .claude/skills/three-lens-audit/scripts && python run_audit.py finalize --help`
Expected: Should show `--semantic-review`, `--semantic-model`, `--max-pairs` flags

**Step 5: Commit**

```bash
git add .claude/skills/three-lens-audit/scripts/run_audit.py
git commit -m "feat(three-lens-audit): add --semantic-review CLI flags to finalize command"
```

---

## Task 11: Run all tests and verify integration

**Files:**
- Test: `.claude/skills/three-lens-audit/scripts/test_synthesize.py`

**Step 1: Run full test suite**

Run: `cd .claude/skills/three-lens-audit/scripts && python -m pytest test_synthesize.py -v`
Expected: All tests PASS

**Step 2: Test with real audit outputs (if available)**

Run: `cd .claude/skills/three-lens-audit/scripts && python run_audit.py finalize ../examples/*.md --target "test" --semantic-review --auto-detect 2>&1 | head -50`
Expected: Should run without errors, may show semantic review warnings

**Step 3: Commit if any fixes needed**

```bash
git add .claude/skills/three-lens-audit/scripts/
git commit -m "test(three-lens-audit): verify semantic review integration"
```

---

## Task 12: Update CHANGELOG.md

**Files:**
- Modify: `.claude/skills/three-lens-audit/CHANGELOG.md`

**Step 1: Add v1.18.0 entry**

Add at the top of CHANGELOG.md:

```markdown
## [1.18.0] - 2026-01-07

### Added
- **Semantic Review**: LLM-assisted detection of semantically equivalent findings
  - `--semantic-review` flag enables semantic matching for findings that keyword matching misses
  - `--semantic-model` flag to choose model (haiku default, sonnet, opus)
  - `--max-pairs` flag for cost control
- New functions in `synthesize.py`:
  - `extract_references()` - Extract file/section/element references from text
  - `generate_candidate_pairs()` - Identify pairs for semantic review
  - `format_pairs_for_prompt()` - Format pairs for LLM prompt
  - `parse_semantic_response()` - Parse LLM response into structured matches
  - `run_semantic_review()` - Execute semantic review via Claude CLI
  - `merge_semantic_matches()` - Merge semantic matches into convergent findings
- New dataclasses: `SemanticMatch`, `SemanticReviewResult`

### Changed
- `synthesize()` now accepts `semantic_review`, `semantic_model`, `max_semantic_pairs` parameters
- `finalize()` in `run_audit.py` passes semantic review flags to synthesize

### Cost
- Semantic review adds ~$0.002-0.01 per synthesis using Haiku
- 93.3% accuracy, 0% false positive rate based on 45-test evaluation
```

**Step 2: Update version in SKILL.md frontmatter**

Modify `.claude/skills/three-lens-audit/SKILL.md` frontmatter:

```yaml
metadata:
  version: "1.18.0"
```

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/CHANGELOG.md .claude/skills/three-lens-audit/SKILL.md
git commit -m "docs(three-lens-audit): update CHANGELOG for v1.18.0 semantic review"
```

---

## Task 13: Update documentation references

**Files:**
- Modify: `.claude/skills/three-lens-audit/references/scripts-reference.md`
- Modify: `.claude/skills/three-lens-audit/references/workflow-details.md`

**Step 1: Update scripts-reference.md with new flags**

Add to the `finalize` command section:

```markdown
### Semantic Review Flags

```bash
# Enable semantic review (finds matches keyword matching missed)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review

# Use Sonnet for higher accuracy (more expensive)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review --semantic-model sonnet

# Limit pairs reviewed (cost control)
python scripts/run_audit.py finalize *.md --target "X" --semantic-review --max-pairs 10
```

**Cost:** ~$0.002-0.01 per synthesis with Haiku (default)
```

**Step 2: Add semantic review section to workflow-details.md**

Add new section:

```markdown
## Semantic Review

Keyword-based convergence detection (Jaccard similarity ≥0.3) misses semantically equivalent findings that use different vocabulary.

### When to Use

- When no 3-lens convergence is detected automatically
- When findings describe the same element from different perspectives
- When vocabulary differs across lenses (e.g., "exploitable" vs "confusing" vs "high-maintenance")

### How It Works

1. Generates candidate pairs from findings that failed keyword matching
2. Filters to pairs with shared file/element references
3. Sends pairs to Claude (Haiku by default) for semantic comparison
4. Merges confirmed matches into convergent findings

### Cost

| Scenario | Pairs | Cost (Haiku) |
|----------|-------|--------------|
| Small audit | ~10 | ~$0.002 |
| Medium audit | ~30 | ~$0.006 |
| Large audit | 20 (capped) | ~$0.004 |
```

**Step 3: Commit**

```bash
git add .claude/skills/three-lens-audit/references/
git commit -m "docs(three-lens-audit): add semantic review to reference documentation"
```

---

Plan complete and saved to `docs/plans/2026-01-07-semantic-review-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
