# Verification Framework Relationship Model

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: Defining how verification connects to other frameworks
- Time pressure: None

## Entry Gate
- Stakes level: adequate
- Time budget: 20 minutes
- Iteration cap: 2
- Evidence bar: Model must cover all handoff scenarios
- Allowed skips: Deep sensitivity analysis
- Escalation trigger: If model creates confusion

## Frame

### Decision Statement
Does the proposed relationship model correctly capture how verification connects to the other frameworks?

### Constraints
- Must be consistent with framework designs
- Must handle all verification outcomes
- Must be clear about ownership

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Completeness | 5 | Covers all handoff scenarios |
| Clarity | 4 | Easy to know where to go next |
| Consistency | 4 | Aligns with framework designs |
| Simplicity | 3 | Not over-engineered |

## Options Considered

### Option A: Proposed model is correct
- Trade-offs: Complete; may feel complex

### Option B: Missing a handoff
- Trade-offs: More complete; requires identifying gaps

### Option C: Too complex
- Trade-offs: Easier; might lose distinctions

### Option D: Wrong model
- Trade-offs: Better fit; requires redesign

## Evaluation

### Gap Analysis

| Scenario | Covered? |
|----------|----------|
| Verification passes | ✓ |
| Fails, output wrong | ✓ |
| Fails, criteria unclear | ✓ |
| Fails, approach wrong | ✓ |
| Partial verification | ✓ |
| Mid-work verification | ✗ Not explicit |
| New requirements discovered | ✗ Missing |

### Gaps Found

1. **Mid-work verification:** Pipeline shows end-to-end flow but verification can be invoked at any output point
2. **New requirements discovered:** Different from "unclear criteria" — needs explicit routing

## Pressure Test

1. **Pipeline is too linear**
   - Response: Shows logical flow, not temporal. Arrows indicate where to go, not sequence.

2. **Pre-mortem: People got lost in routing**
   - Response: Handoffs are conceptual mental framework, not workflow engine.

## Decision

**Choice:** Option B — model correct with two clarifications

### Clarifications Added

1. **Mid-work verification:** Pipeline shows full flow, but verification can be invoked at any output point. Each output has its own verification cycle.

2. **New requirements discovered:** Route based on scope impact:
   - → Thoroughness (need to understand)
   - → Decision-making (need to decide inclusion)
   - → Escalate (significant scope change)

### Complete Relationship Model

**Handoff TO verification:**

| From | Trigger | What verification receives |
|------|---------|---------------------------|
| Any work | Output produced | The artifact to verify |
| Thoroughness | Findings complete | Findings with E/C ratings |
| Decision-making | Decision made | Chosen option + expected outcomes |
| Implementation | Deliverable complete | Artifact + acceptance criteria |

**Handoff FROM verification:**

| Verification result | Handoff to | What gets passed |
|--------------------|------------|------------------|
| Verified (pass) | Done / next phase | Verification report |
| Not verified — wrong output | Implementation | What failed + evidence |
| Not verified — unclear criteria | Thoroughness | Need understanding |
| Not verified — wrong approach | Decision-making | Need different approach |
| Partially verified | Depends on gaps | Gap analysis routes |
| New requirement discovered | Thoroughness / Decision-making / Escalate | Based on scope impact |

**Pipeline (logical flow):**

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐     ┌──────────────┐
│ Thoroughness│ ──► │ Decision-making  │ ──► │Implementation │ ──► │ Verification │
│ (understand)│     │ (choose)         │     │ (build)       │     │ (confirm)    │
└─────────────┘     └──────────────────┘     └───────────────┘     └──────────────┘
       ▲                    ▲                        ▲                    │
       │                    │                        │                    │
       └────────────────────┴────────────────────────┴────────────────────┘
                              (verification failures route back)
```

**Note:** Pipeline shows logical flow. Verification can be invoked at any output point; each output has its own verification cycle.

**Trade-offs Accepted:** Slightly more complex routing table

**Confidence:** High

**Caveats:** If "new requirement discovered" proves rare, simplify to just "Escalate"

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | (initial) | Option B | Found 2 gaps via scenario analysis |

## Exit Gate
- [x] Minimum passes met
- [x] Frame complete
- [x] Evaluation complete
- [x] Convergence met
- [x] Trade-offs documented
- [x] Iteration log complete
- [x] Transition tree passed
