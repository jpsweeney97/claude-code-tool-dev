#!/usr/bin/env python3
"""
Test the semantic match prompt against the test suite.

This script formats test cases and outputs prompts for evaluation.
Results are parsed and compared against expected outcomes.

Usage:
    python test_semantic_prompt.py --batch 1  # Run batch 1 (tests 1-15)
    python test_semantic_prompt.py --batch 2  # Run batch 2 (tests 16-30)
    python test_semantic_prompt.py --batch 3  # Run batch 3 (tests 31-45)
    python test_semantic_prompt.py --all      # Output all test prompts
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

# ===========================================================================
# TEST CASES
# ===========================================================================

@dataclass
class TestCase:
    """A single test case for semantic matching."""
    id: str
    lens_a: str
    finding_a: str
    lens_b: str
    finding_b: str
    expected_match: bool
    expected_element: Optional[str] = None
    expected_confidence: Optional[str] = None
    rationale: str = ""


# Category 1: True Matches (High Confidence) - Tests 1.1-1.12
TRUE_MATCHES_HIGH = [
    TestCase(
        id="1.1",
        lens_a="adversarial",
        finding_a="`config.yaml` has no schema validation, allowing malformed configurations to crash the system",
        lens_b="pragmatic",
        finding_b="Users get confusing errors when `config.yaml` has typos because there's no helpful validation",
        expected_match=True,
        expected_element="config.yaml validation",
        expected_confidence="high",
        rationale="Both explicitly reference config.yaml and its lack of validation"
    ),
    TestCase(
        id="1.2",
        lens_a="adversarial",
        finding_a="The `auth.py` module stores tokens in plaintext, creating a credential exposure risk",
        lens_b="cost-benefit",
        finding_b="`auth.py` token handling requires ongoing security audits, adding compliance cost",
        expected_match=True,
        expected_element="auth.py token handling",
        expected_confidence="high",
        rationale="Both reference auth.py token handling"
    ),
    TestCase(
        id="1.3",
        lens_a="pragmatic",
        finding_a="The `README.md` is 800 lines and users can't find what they need quickly",
        lens_b="cost-benefit",
        finding_b="`README.md` maintenance costs exceed its value at current length",
        expected_match=True,
        expected_element="README.md length",
        expected_confidence="high",
        rationale="Both reference README.md length as problematic"
    ),
    TestCase(
        id="1.4",
        lens_a="adversarial",
        finding_a="The `parseInput()` function doesn't sanitize quotes, enabling SQL injection",
        lens_b="pragmatic",
        finding_b="`parseInput()` fails silently on malformed data, leaving users confused",
        expected_match=True,
        expected_element="parseInput() function",
        expected_confidence="high",
        rationale="Both reference the same function"
    ),
    TestCase(
        id="1.5",
        lens_a="pragmatic",
        finding_a="The 'Getting Started' section assumes too much prior knowledge",
        lens_b="cost-benefit",
        finding_b="The 'Getting Started' section creates high onboarding cost for new users",
        expected_match=True,
        expected_element="Getting Started section",
        expected_confidence="high",
        rationale="Both reference the same documentation section"
    ),
    TestCase(
        id="1.6",
        lens_a="robustness",
        finding_a="Step 3 has no error handling if the API returns a 500 error",
        lens_b="minimalist",
        finding_b="Step 3 could be eliminated entirely; steps 2 and 4 could be combined",
        expected_match=True,
        expected_element="Step 3",
        expected_confidence="high",
        rationale="Both focus on Step 3, though from opposing perspectives"
    ),
    TestCase(
        id="1.7",
        lens_a="robustness",
        finding_a="The caching layer doesn't invalidate on config changes, leading to stale data",
        lens_b="capability",
        finding_b="The caching layer assumes instant invalidation, which Claude Code can't guarantee",
        expected_match=True,
        expected_element="caching layer invalidation",
        expected_confidence="high",
        rationale="Both reference caching layer invalidation"
    ),
    TestCase(
        id="1.8",
        lens_a="minimalist",
        finding_a="The 5-phase workflow could be reduced to 3 phases without losing core functionality",
        lens_b="capability",
        finding_b="The 5-phase workflow exceeds typical Claude session context limits",
        expected_match=True,
        expected_element="5-phase workflow",
        expected_confidence="high",
        rationale="Both reference the same workflow"
    ),
    TestCase(
        id="1.9",
        lens_a="implementation",
        finding_a="The hook uses exit code 1 instead of exit code 2, so blocking doesn't work",
        lens_b="adversarial",
        finding_b="The hook can be bypassed because it uses the wrong exit code",
        expected_match=True,
        expected_element="hook exit code",
        expected_confidence="high",
        rationale="Both reference the same hook exit code issue"
    ),
    TestCase(
        id="1.10",
        lens_a="implementation",
        finding_a="The skill requires cross-session state, which Claude Code doesn't support natively",
        lens_b="cost-benefit",
        finding_b="Implementing state persistence for this skill adds infrastructure complexity",
        expected_match=True,
        expected_element="skill state persistence",
        expected_confidence="high",
        rationale="Both reference skill state persistence"
    ),
    TestCase(
        id="1.11",
        lens_a="implementation",
        finding_a="SKILL.md exceeds the 500-line recommendation, which may cause truncation",
        lens_b="adversarial",
        finding_b="SKILL.md size creates risk of Claude missing critical instructions at the end",
        expected_match=True,
        expected_element="SKILL.md length",
        expected_confidence="high",
        rationale="Both reference SKILL.md size"
    ),
    TestCase(
        id="1.12",
        lens_a="adversarial",
        finding_a="The plugin.json uses undocumented fields that may break in future versions",
        lens_b="cost-benefit",
        finding_b="Relying on undocumented plugin.json fields creates future migration cost",
        expected_match=True,
        expected_element="plugin.json undocumented fields",
        expected_confidence="high",
        rationale="Both reference plugin.json undocumented fields"
    ),
]

# Category 2: True Matches (Medium Confidence) - Tests 2.1-2.8
TRUE_MATCHES_MEDIUM = [
    TestCase(
        id="2.1",
        lens_a="adversarial",
        finding_a="The priority system (P1-P18) allows subjective interpretation, enabling inconsistent application",
        lens_b="pragmatic",
        finding_b="The numbered principles are hard to remember and I'm never sure which takes precedence",
        expected_match=True,
        expected_element="priority/principle numbering system",
        expected_confidence="medium",
        rationale="Both describe the prioritization system"
    ),
    TestCase(
        id="2.2",
        lens_a="adversarial",
        finding_a="The permission model can be circumvented by creative command construction",
        lens_b="cost-benefit",
        finding_b="The permission model requires constant user vigilance, adding friction to workflows",
        expected_match=True,
        expected_element="permission model",
        expected_confidence="medium",
        rationale="Both reference the permission model"
    ),
    TestCase(
        id="2.3",
        lens_a="pragmatic",
        finding_a="Users don't know when they've succeeded because there's no clear completion indicator",
        lens_b="cost-benefit",
        finding_b="Lack of completion feedback leads to repeated attempts, wasting compute resources",
        expected_match=True,
        expected_element="completion feedback/indicator",
        expected_confidence="medium",
        rationale="Both describe completion feedback absence"
    ),
    TestCase(
        id="2.4",
        lens_a="robustness",
        finding_a="The rollback mechanism doesn't handle partial failures mid-transaction",
        lens_b="minimalist",
        finding_b="The rollback feature adds complexity that most use cases don't need",
        expected_match=True,
        expected_element="rollback mechanism/feature",
        expected_confidence="medium",
        rationale="Both reference the rollback mechanism"
    ),
    TestCase(
        id="2.5",
        lens_a="robustness",
        finding_a="The API retry logic should use exponential backoff, but currently retries immediately",
        lens_b="capability",
        finding_b="The API retry logic assumes idempotency that most APIs don't guarantee",
        expected_match=True,
        expected_element="API retry logic",
        expected_confidence="medium",
        rationale="Both reference API retry logic"
    ),
    TestCase(
        id="2.6",
        lens_a="implementation",
        finding_a="Claude can't reliably maintain state across tool calls in a single turn",
        lens_b="cost-benefit",
        finding_b="Multi-step workflows that assume state continuity fail unpredictably",
        expected_match=True,
        expected_element="state continuity across tool calls",
        expected_confidence="medium",
        rationale="Both describe state continuity issues"
    ),
    TestCase(
        id="2.7",
        lens_a="adversarial",
        finding_a="The external dependency creates supply chain risk if upstream is compromised",
        lens_b="pragmatic",
        finding_b="Updating the external library requires careful testing each time",
        expected_match=True,
        expected_element="external dependency/library",
        expected_confidence="medium",
        rationale="Both reference external dependency management"
    ),
    TestCase(
        id="2.8",
        lens_a="minimalist",
        finding_a="The validation layer is overkill for the actual input variance we see",
        lens_b="capability",
        finding_b="The validation layer assumes input patterns that Claude rarely produces",
        expected_match=True,
        expected_element="validation layer",
        expected_confidence="medium",
        rationale="Both reference the validation layer"
    ),
]

# Category 3: False Matches - Tests 3.1-3.15
FALSE_MATCHES = [
    TestCase(
        id="3.1",
        lens_a="adversarial",
        finding_a="`README.md` contains outdated security recommendations in the deployment section",
        lens_b="pragmatic",
        finding_b="`README.md` installation instructions assume Linux and don't work on Windows",
        expected_match=False,
        rationale="Same file but completely different sections/issues"
    ),
    TestCase(
        id="3.2",
        lens_a="adversarial",
        finding_a="The `SKILL.md` frontmatter uses undocumented fields",
        lens_b="pragmatic",
        finding_b="The `SKILL.md` examples section is too abstract to follow",
        expected_match=False,
        rationale="Same file but different parts (frontmatter vs examples)"
    ),
    TestCase(
        id="3.3",
        lens_a="adversarial",
        finding_a="In `auth.py`, the `login()` function is vulnerable to timing attacks",
        lens_b="cost-benefit",
        finding_b="In `auth.py`, the `logout()` function has unnecessary database calls",
        expected_match=False,
        rationale="Same file but different functions"
    ),
    TestCase(
        id="3.4",
        lens_a="adversarial",
        finding_a="Missing input validation in the API endpoint",
        lens_b="pragmatic",
        finding_b="Missing form validation feedback in the UI",
        expected_match=False,
        rationale="Both about validation but API backend vs UI frontend"
    ),
    TestCase(
        id="3.5",
        lens_a="pragmatic",
        finding_a="The API documentation lacks examples",
        lens_b="cost-benefit",
        finding_b="The internal architecture docs are expensive to maintain",
        expected_match=False,
        rationale="Different documentation (API docs vs architecture docs)"
    ),
    TestCase(
        id="3.6",
        lens_a="adversarial",
        finding_a="The caching layer can be DoS'd by cache-busting patterns",
        lens_b="cost-benefit",
        finding_b="Database queries are slow and need optimization",
        expected_match=False,
        rationale="Different components (caching vs database)"
    ),
    TestCase(
        id="3.7",
        lens_a="robustness",
        finding_a="Missing error handling for network timeouts",
        lens_b="pragmatic",
        finding_b="Missing examples in the quick start guide",
        expected_match=False,
        rationale="Completely different missing things"
    ),
    TestCase(
        id="3.8",
        lens_a="minimalist",
        finding_a="The state machine has too many states for the actual use cases",
        lens_b="capability",
        finding_b="The prompt template is too complex for Claude to follow reliably",
        expected_match=False,
        rationale="Different sources of complexity"
    ),
    TestCase(
        id="3.9",
        lens_a="adversarial",
        finding_a="Some edge cases aren't handled properly",
        lens_b="pragmatic",
        finding_b="Some parts of the documentation could be clearer",
        expected_match=False,
        rationale="Too vague to determine if same element"
    ),
    TestCase(
        id="3.10",
        lens_a="adversarial",
        finding_a="The `parseConfig()` function doesn't validate nested objects",
        lens_b="pragmatic",
        finding_b="The error messages could be more helpful",
        expected_match=False,
        rationale="Can't confirm vague error messages refers to parseConfig"
    ),
    TestCase(
        id="3.11",
        lens_a="adversarial",
        finding_a="The system can be abused if users know the internal structure",
        lens_b="cost-benefit",
        finding_b="The system requires too much maintenance overhead",
        expected_match=False,
        rationale="'The system' is too generic"
    ),
    TestCase(
        id="3.12",
        lens_a="pragmatic",
        finding_a="The README is too long at 500 lines",
        lens_b="cost-benefit",
        finding_b="The build process takes too long at 10 minutes",
        expected_match=False,
        rationale="Different things are 'too long'"
    ),
    TestCase(
        id="3.13",
        lens_a="pragmatic",
        finding_a="The folder structure is confusing",
        lens_b="adversarial",
        finding_b="The error codes are confusing and could mask security issues",
        expected_match=False,
        rationale="Different things are confusing"
    ),
    TestCase(
        id="3.14",
        lens_a="robustness",
        finding_a="Missing graceful degradation when database is unavailable",
        lens_b="minimalist",
        finding_b="Missing justification for why this feature is needed at all",
        expected_match=False,
        rationale="Different 'missing' things"
    ),
    TestCase(
        id="3.15",
        lens_a="adversarial",
        finding_a="The rate limit of 100 requests/minute can be bypassed",
        lens_b="cost-benefit",
        finding_b="The 100-line config file is expensive to maintain",
        expected_match=False,
        rationale="'100' refers to different things"
    ),
]

# Category 4: Edge Cases - Tests 4.1-4.10
EDGE_CASES = [
    TestCase(
        id="4.1",
        lens_a="adversarial",
        finding_a="In `utils.py`, the `sanitize()` function doesn't escape backticks",
        lens_b="pragmatic",
        finding_b="The `sanitize()` helper is hard to use correctly",
        expected_match=True,
        expected_element="sanitize() function",
        expected_confidence="high",
        rationale="Same function referenced with and without file context"
    ),
    TestCase(
        id="4.2",
        lens_a="adversarial",
        finding_a="In `CLAUDE.md`, the 'Security' section has gaps",
        lens_b="pragmatic",
        finding_b="In `CLAUDE.md`, the 'Quick Start' section is confusing",
        expected_match=False,
        rationale="Same file but different sections"
    ),
    TestCase(
        id="4.3",
        lens_a="adversarial",
        finding_a="The user authentication flow has no 2FA support",
        lens_b="pragmatic",
        finding_b="The user profile page is hard to navigate",
        expected_match=False,
        rationale="Both mention 'user' but different features"
    ),
    TestCase(
        id="4.4",
        lens_a="robustness",
        finding_a="The HTTP client doesn't handle redirects properly",
        lens_b="capability",
        finding_b="Network calls may fail in Claude Code's sandboxed environment",
        expected_match=False,
        rationale="HTTP client is subset of network calls but issues differ"
    ),
    TestCase(
        id="4.5",
        lens_a="adversarial",
        finding_a="The cache is vulnerable to poisoning during high load",
        lens_b="cost-benefit",
        finding_b="The cache provides diminishing returns after 1000 entries",
        expected_match=True,
        expected_element="cache",
        expected_confidence="medium",
        rationale="Same cache, different conditions"
    ),
    TestCase(
        id="4.6",
        lens_a="adversarial",
        finding_a="The API versioning strategy will cause breaking changes",
        lens_b="robustness",
        finding_b="The current API version handling is incomplete",
        expected_match=True,
        expected_element="API versioning",
        expected_confidence="medium",
        rationale="Both about API versioning"
    ),
    TestCase(
        id="4.7",
        lens_a="adversarial",
        finding_a="Secrets are logged in debug mode, violating security policy",
        lens_b="cost-benefit",
        finding_b="Debug logging creates storage costs and compliance overhead",
        expected_match=True,
        expected_element="debug logging",
        expected_confidence="medium",
        rationale="Both reference debug logging"
    ),
    TestCase(
        id="4.8",
        lens_a="adversarial",
        finding_a="The third-party integration has known vulnerabilities",
        lens_b="pragmatic",
        finding_b="Some features don't work as expected",
        expected_match=False,
        rationale="'Some features' is too implicit"
    ),
    TestCase(
        id="4.9",
        lens_a="robustness",
        finding_a="The workflow doesn't specify what happens if step 2 times out",
        lens_b="adversarial",
        finding_b="Step 2 timeout handling can be exploited to hang the system",
        expected_match=True,
        expected_element="step 2 timeout handling",
        expected_confidence="high",
        rationale="Both reference step 2 timeout handling"
    ),
    TestCase(
        id="4.10",
        lens_a="implementation",
        finding_a="The skill assumes tools return instantly, but they may take 30+ seconds",
        lens_b="pragmatic",
        finding_b="Users get frustrated waiting for tool results with no progress indicator",
        expected_match=True,
        expected_element="tool response time / waiting experience",
        expected_confidence="medium",
        rationale="Both reference tool response latency"
    ),
]

ALL_TESTS = TRUE_MATCHES_HIGH + TRUE_MATCHES_MEDIUM + FALSE_MATCHES + EDGE_CASES


# ===========================================================================
# PROMPT TEMPLATE
# ===========================================================================

PROMPT_TEMPLATE = '''You identify whether audit findings from different perspectives describe the SAME element.

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

**Example 1: Both reference "principles.md"**
- Adversarial: "Token count for `principles.md` is vague, may exceed context limits"
- Pragmatic: "`principles.md` at 8K tokens is too heavy to load casually"
- Element A: principles.md | Element B: principles.md | **MATCH: yes**
- Rationale: Both identify principles.md as problematically large
- Confidence: high (explicit file reference in both)

**Example 2: Both reference the same function**
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

**Example 5: Both about "too long" but different things**
- Pragmatic: "The README is too long at 500 lines"
- Cost/Benefit: "The test suite takes too long to run (10 minutes)"
- Element A: README length | Element B: test duration | **MATCH: no**
- Rationale: Different elements (README vs test suite)

**Example 6: Same file, different sections**
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


# ===========================================================================
# FORMATTING AND PARSING
# ===========================================================================

def format_pairs(tests: List[TestCase]) -> str:
    """Format test cases as finding pairs for the prompt."""
    lines = []
    for i, test in enumerate(tests, 1):
        lines.append(f"### Pair {i} (Test {test.id})")
        lines.append(f"**{test.lens_a.title()}:** \"{test.finding_a}\"")
        lines.append(f"**{test.lens_b.title()}:** \"{test.finding_b}\"")
        lines.append("")
    return "\n".join(lines)


def generate_prompt(tests: List[TestCase]) -> str:
    """Generate the full prompt for a batch of tests."""
    pairs_formatted = format_pairs(tests)
    return PROMPT_TEMPLATE.format(pairs_formatted=pairs_formatted)


@dataclass
class ParsedResponse:
    """Parsed response for a single pair."""
    pair_num: int
    test_id: str
    element_a: str
    element_b: str
    match: bool
    shared_element: str
    rationale: str
    confidence: str


def parse_response(response: str, tests: List[TestCase]) -> List[ParsedResponse]:
    """Parse the model's response into structured results."""
    results = []

    # Pattern for each pair response
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
        pair_num = int(match.group(1))
        if pair_num > len(tests):
            continue

        test = tests[pair_num - 1]
        results.append(ParsedResponse(
            pair_num=pair_num,
            test_id=test.id,
            element_a=match.group(2).strip(),
            element_b=match.group(3).strip(),
            match=match.group(4).lower() == 'yes',
            shared_element=match.group(5).strip(),
            rationale=match.group(6).strip(),
            confidence=match.group(7).lower()
        ))

    return results


def evaluate_results(tests: List[TestCase], responses: List[ParsedResponse]) -> Dict:
    """Evaluate parsed responses against expected results."""
    results = {
        "total": len(tests),
        "parsed": len(responses),
        "correct": 0,
        "incorrect": 0,
        "true_positive": 0,
        "true_negative": 0,
        "false_positive": 0,
        "false_negative": 0,
        "details": []
    }

    response_map = {r.test_id: r for r in responses}

    for test in tests:
        resp = response_map.get(test.id)
        if not resp:
            results["details"].append({
                "test_id": test.id,
                "status": "NOT_PARSED",
                "expected_match": test.expected_match,
                "actual_match": None
            })
            continue

        correct = resp.match == test.expected_match

        if correct:
            results["correct"] += 1
            if test.expected_match:
                results["true_positive"] += 1
            else:
                results["true_negative"] += 1
        else:
            results["incorrect"] += 1
            if resp.match and not test.expected_match:
                results["false_positive"] += 1
            else:
                results["false_negative"] += 1

        results["details"].append({
            "test_id": test.id,
            "status": "CORRECT" if correct else "INCORRECT",
            "expected_match": test.expected_match,
            "actual_match": resp.match,
            "expected_confidence": test.expected_confidence,
            "actual_confidence": resp.confidence,
            "rationale": resp.rationale,
            "expected_rationale": test.rationale
        })

    # Calculate metrics
    if results["parsed"] > 0:
        results["accuracy"] = results["correct"] / results["parsed"]
    else:
        results["accuracy"] = 0

    tp = results["true_positive"]
    fp = results["false_positive"]
    fn = results["false_negative"]
    tn = results["true_negative"]

    results["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
    results["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
    results["false_positive_rate"] = fp / (fp + tn) if (fp + tn) > 0 else 0

    return results


def print_summary(results: Dict):
    """Print evaluation summary."""
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {results['total']}")
    print(f"Parsed responses: {results['parsed']}")
    print(f"Correct: {results['correct']}")
    print(f"Incorrect: {results['incorrect']}")
    print()
    print("Confusion Matrix:")
    print(f"  True Positive:  {results['true_positive']}")
    print(f"  True Negative:  {results['true_negative']}")
    print(f"  False Positive: {results['false_positive']} ← Critical metric")
    print(f"  False Negative: {results['false_negative']}")
    print()
    print("Metrics:")
    print(f"  Accuracy:            {results['accuracy']:.1%}")
    print(f"  Precision:           {results['precision']:.1%}")
    print(f"  Recall:              {results['recall']:.1%}")
    print(f"  False Positive Rate: {results['false_positive_rate']:.1%} (target: <10%)")
    print()

    # Print failures
    failures = [d for d in results['details'] if d['status'] != 'CORRECT']
    if failures:
        print("FAILURES:")
        print("-" * 60)
        for f in failures:
            print(f"Test {f['test_id']}: {f['status']}")
            print(f"  Expected: match={f['expected_match']}")
            print(f"  Actual:   match={f['actual_match']}")
            if f.get('rationale'):
                print(f"  Model rationale: {f['rationale'][:80]}...")
            print()


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description="Test semantic match prompt")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3], help="Run specific batch")
    parser.add_argument("--all", action="store_true", help="Output all test prompts")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--parse", type=str, help="Parse response from file")

    args = parser.parse_args()

    if args.batch == 1:
        tests = ALL_TESTS[:15]
        batch_name = "Batch 1 (Tests 1.1-2.3)"
    elif args.batch == 2:
        tests = ALL_TESTS[15:30]
        batch_name = "Batch 2 (Tests 2.4-3.11)"
    elif args.batch == 3:
        tests = ALL_TESTS[30:]
        batch_name = "Batch 3 (Tests 3.12-4.10)"
    else:
        tests = ALL_TESTS
        batch_name = "All Tests"

    if args.parse:
        # Parse a response file
        with open(args.parse) as f:
            response = f.read()
        responses = parse_response(response, tests)
        results = evaluate_results(tests, responses)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_summary(results)
    else:
        # Generate prompt
        prompt = generate_prompt(tests)

        if args.json:
            output = {
                "batch": batch_name,
                "test_count": len(tests),
                "prompt": prompt,
                "expected": [
                    {
                        "test_id": t.id,
                        "expected_match": t.expected_match,
                        "expected_element": t.expected_element,
                        "expected_confidence": t.expected_confidence
                    }
                    for t in tests
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"# {batch_name}")
            print(f"# {len(tests)} test cases")
            print()
            print(prompt)


if __name__ == "__main__":
    main()
