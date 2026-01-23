# Verification Framework Failure Modes

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: Brainstorming failure modes for Framework for Verification
- Time pressure: None

## Entry Gate
- Stakes level: adequate
- Time budget: 20 minutes
- Iteration cap: 2
- Evidence bar: Gap analysis against stages and known failure patterns
- Allowed skips: Deep stakeholder analysis; sensitivity analysis
- Escalation trigger: If we can't agree on failure mode coverage

## Frame

### Decision Statement
Does the proposed failure mode table adequately capture verification failures?

### Constraints
- Must be domain-agnostic
- Must map to the 4-stage structure (DEFINE, DESIGN, EXECUTE, EVALUATE)
- Each failure mode needs a clear countermeasure

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Coverage | 5 | Captures the failures we've observed |
| Actionability | 4 | Each countermeasure is concrete |
| Parsimony | 3 | No redundant entries |
| Clarity | 3 | Each failure mode is distinct |

## Options Considered

### Option A: Table is complete enough
- Trade-offs: Can proceed; may have blind spots

### Option B: Missing something
- Trade-offs: More complete; requires identifying gaps

### Option C: Too granular
- Trade-offs: Simpler; might lose distinctions

### Option D: Wrong framing
- Trade-offs: Better structure; requires rethinking

### Option E: Null (defer)
- Trade-offs: Gather more input; delays progress

## Evaluation

### Gap Analysis

Original table had 11 entries. Analyzed for missing failure modes:

| Potential Gap | Analysis |
|---------------|----------|
| Verification of wrong thing | Covered by "Missing criteria" + "Method-criteria mismatch" |
| Giving up too early | NOT covered → add |
| Over-verification | Handled by stakes calibration, not a failure mode |
| Environment mismatch | NOT covered → add |
| Timing/staleness | NOT covered → add |

### Gaps Found

| Stage | Missing Failure Mode | Signal | Countermeasure |
|-------|---------------------|--------|----------------|
| EXECUTE | Premature abandonment | "Ran out of time" | Iteration cap + minimum depth by stakes |
| EXECUTE | Environment mismatch | Verified in wrong context | Require environment spec in DESIGN |
| EVALUATE | Stale verification | Verified earlier, conditions changed | Timestamp verdicts; re-verify after changes |

## Pressure Test

### Arguments Against Frontrunner
1. **14 failure modes is too many**
   - Response: Table is reference material, not runtime checklist. Skills can surface relevant subset.

2. **Some entries overlap**
   - Response: "Completion theater" (no evidence) vs "Selective execution" (skipped hard parts) are distinct with different signals and countermeasures.

## Decision

**Choice:** Option B — original table plus 3 additions

**Additions:**
1. Premature abandonment (EXECUTE)
2. Environment mismatch (EXECUTE)
3. Stale verification (EVALUATE)

**Trade-offs Accepted:** Table grows from 11 to 14 entries

**Confidence:** High

**Caveats:** Domain-specific uses may surface additional failure modes; framework should allow extension

## Complete Failure Mode Table

| Stage | Failure Mode | Signal | Countermeasure |
|-------|--------------|--------|----------------|
| DEFINE | Vague criteria | "It should work correctly" | Require specific, testable conditions |
| DEFINE | Missing criteria | Only checked happy path | Require edge cases, error conditions |
| DEFINE | Wrong oracle type | "I'll know it when I see it" | Require named oracle type |
| DESIGN | Shallow method | "Run the tests" without specifics | Require verification plan with exact steps |
| DESIGN | Method-criteria mismatch | Method doesn't test the criterion | Map each criterion to its method |
| EXECUTE | Completion theater | "I verified it" without evidence | Evidence artifacts required |
| EXECUTE | Selective execution | Skipped hard checks | Pre-registered plan; all steps traced |
| EXECUTE | Misread results | Saw green, wrong test | Pre-registered expectations; explicit comparison |
| EXECUTE | Premature abandonment | "Ran out of time" | Iteration cap + minimum depth by stakes |
| EXECUTE | Environment mismatch | Verified in wrong context | Require environment spec in DESIGN |
| EVALUATE | False positive | "Pass" with weak evidence | Evidence-verdict alignment rule |
| EVALUATE | Unmarked gaps | Didn't test X, didn't say so | Explicit "not verified" category |
| EVALUATE | Ignored disconfirmation | Failure evidence overlooked | Disconfirmation check before claiming pass |
| EVALUATE | Stale verification | Conditions changed since verification | Timestamp verdicts; re-verify after changes |

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | (initial) | Option B | Found 3 gaps via systematic analysis |

## Exit Gate
- [x] Minimum passes met (1 for adequate)
- [x] Frame complete
- [x] Evaluation complete (gap analysis performed)
- [x] Convergence met
- [x] Trade-offs documented
- [x] Iteration log complete
- [x] Transition tree passed
