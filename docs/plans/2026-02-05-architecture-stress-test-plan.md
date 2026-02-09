> **Status: CLOSED** — Tests complete. See results companion.

# Architecture Stress Test Plan

**Date:** 2026-02-05
**Purpose:** Comprehensive edge case testing before Phase 4 (scenario generation)
**Approach:** Adaptive — start with high-priority cases, stop when we stop learning

---

## Goals

1. **Stress-test the architecture** — Find scenarios where A/B comparison breaks down
2. **Characterize behavior** — Understand how ambiguity and conflicts affect assessment
3. **Define boundaries** — Establish what can and can't be assessed

---

## Test Suite Overview

| Category | Tests | Initial Runs | Expandable |
|----------|-------|--------------|------------|
| A1: Ambiguous Instructions | 5 | 25 | If high variance |
| A2: Conflicting Requirements | 3 | 3 | +4-12 if interesting |
| **Total** | 8 | 28 | Up to 40 |

**Deferred:** A5 (subjective criteria) — partially covered by A1b

---

## A1: Ambiguous Instructions

Tests whether unclear skill instructions cause variance or unpredictable compliance.

### A1a: Vague Quantifiers

**Hypothesis:** "Several" has no fixed meaning; compliance will vary.

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Skill instruction | "Include several code examples to illustrate your points" | "Mention a few common pitfalls to avoid" |
| Scenario | "Explain how promises work in JavaScript" | "Explain REST API design principles" |
| Measurement | Count code examples | Count pitfalls mentioned |
| Runs | 5 | 5 (if primary shows no variance) |

**Switch condition:** Primary shows <20% variance in example count.

---

### A1b: Undefined Terms (Concise vs Thorough)

**Hypothesis:** "Concise" and "thorough" have no fixed meaning; word count will vary.

**Design:** Three conditions on same scenario to isolate the variable.

| Condition | Skill Instruction | Runs |
|-----------|-------------------|------|
| A1b-base | (none) | 5 |
| A1b-i | "Be concise in your explanation" | 5 |
| A1b-ii | "Be thorough in your explanation" | 5 |

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Scenario | "Explain how database indexing works" | "Explain microservices architecture" |
| Measurement | Word count | Word count |

**Switch condition:** Baseline, concise, and thorough show <15% difference in word count.

**Expected pattern:**
- Baseline: ~X words
- Concise: <X words
- Thorough: >X words

---

### A1c: Implicit Conditions

**Hypothesis:** "When appropriate" is subjective; caveat presence will vary.

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Skill instruction | "Add appropriate caveats and limitations when discussing technical recommendations" | "Note limitations where relevant" |
| Scenario | "Should we use MongoDB for our user data?" | "Should we use GraphQL for our API?" |
| Measurement | Caveat/limitation count; presence/absence | Same |
| Runs | 5 | 5 (if primary shows no variance) |

**Switch condition:** Primary always or never includes caveats (no variance).

---

## A2: Conflicting Requirements

Tests how the framework handles skills with internal contradictions.

**Initial approach:** 1 run each to see resolution pattern, expand if interesting.

### A2a: Format vs Content

**Conflict:** Word limit vs comprehensive coverage.

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Skill instructions | "Keep response under 200 words" + "Cover all common edge cases and failure modes" | Same instructions |
| Scenario | "What should I consider when implementing user authentication?" | "What should I consider when implementing error handling?" |
| Measurement | Word count + edge case count | Same |
| Runs | 1 initial, +4 if interesting | Same |

**Possible outcomes:**
- Word limit respected, edge cases incomplete
- Edge cases complete, word limit exceeded
- Awkward compromise (both partially satisfied)

---

### A2b: Quantity vs Quality

**Conflict:** Fixed count vs comprehensive options.

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Skill instructions | "Provide exactly 3 options, no more, no less" + "Include all viable approaches worth considering" | Same instructions |
| Scenario | "What database should I use for a real-time chat application?" | "What frontend framework should I use for an admin dashboard?" |
| Measurement | Option count; whether viable options omitted | Same |
| Runs | 1 initial, +4 if interesting | Same |

**Possible outcomes:**
- Exactly 3 (potentially omitting viable options)
- More than 3 (ignoring quantity instruction)
- Attempted compromise with notes about omitted options

**Why alternative:** Database choices may naturally be ~3; framework choices are 5+ viable.

---

### A2c: Tone vs Substance

**Conflict:** Beginner accessibility vs expert depth.

| Attribute | Primary | Alternative |
|-----------|---------|-------------|
| Skill instructions | "Explain in simple terms a beginner could understand" + "Include technical implementation details an expert would need" | Same instructions |
| Scenario | "How does HTTPS encryption work?" | "How does garbage collection work?" |
| Measurement | Jargon density + simple analogy count | Same; alt metric: technical term count vs analogy count |
| Runs | 1 initial, +4 if interesting | Same |

**Possible outcomes:**
- Oversimplified (beginner wins)
- Too technical (expert wins)
- Layered explanation (both satisfied)
- Awkward mix (neither satisfied)

---

## Execution Protocol

### Naming Convention

Use neutral names to prevent observer effect:

```
scenario-{topic}-{random-suffix}
```

Examples:
- `scenario-promises-4x` (with skill)
- `scenario-promises-7k` (without skill)

**Do not use:** "test", "baseline", "control", "experiment" in names.

### Run Tracking

For each run, record:
- Skill name (neutral ID)
- Timestamp
- Full output
- Metric values

### Analysis Criteria

| Metric | Low Variance | High Variance |
|--------|--------------|---------------|
| Count (examples, caveats) | σ ≤ 1 | σ > 1 |
| Word count | CV ≤ 15% | CV > 15% |
| Presence (yes/no) | 100% or 0% | Mixed |

(CV = coefficient of variation = σ/μ)

### Expansion Triggers

| Test | Expand If |
|------|-----------|
| A1a, A1c | High variance in count metrics |
| A1b | No difference between conditions |
| A2a-c | Inconsistent resolution across runs OR interesting compromise pattern |

---

## Success Criteria

| Finding | Implication for Framework |
|---------|---------------------------|
| A1 shows high variance | Ambiguous instructions unreliable; flag during assessment |
| A1 shows low variance | Ambiguity interpretable consistently; document patterns |
| A2 resolves consistently | Conflicts have predictable winners; document hierarchy |
| A2 resolves inconsistently | Conflicts are framework limitation; flag during assessment |

---

## Deferred Tests

| Test | Reason Deferred |
|------|-----------------|
| A3: Tool use required | Lower priority; delta in actions vs output |
| A4: Very long skill | Lower priority; instruction following limits |
| A5: Subjective criteria | Partially covered by A1b; revisit if A1b insufficient |
| Category B: Skill types | Depends on A results |
| Category C: Boundaries | Depends on A results |

---

## Next Steps

1. Create feature branch for testing
2. Execute A1 tests (25 runs)
3. Analyze A1 results
4. Execute A2 tests (3 runs)
5. Decide on expansion based on findings
6. Document results in ADR and discussion map
7. Determine if Category B/C testing needed
