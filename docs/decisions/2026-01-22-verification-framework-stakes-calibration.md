# Verification Framework Stakes Calibration

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: Defining what varies by stakes level in the verification framework
- Time pressure: None

## Entry Gate
- Stakes level: adequate
- Time budget: 25 minutes
- Iteration cap: 2
- Evidence bar: Calibration must cover failure modes and feel proportionate
- Allowed skips: Deep sensitivity analysis
- Escalation trigger: If calibration doesn't fit verification's unique needs

## Frame

### Decision Statement
What dimensions should vary by stakes level in the verification framework, and how?

### Constraints
- Must align with adequate/rigorous/exhaustive pattern
- Must be verification-specific
- Must prevent under-verification and over-verification

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Failure mode coverage | 5 | Higher stakes = more failure modes countered |
| Proportionality | 4 | Effort scales appropriately |
| Clarity | 4 | Easy to know requirements |
| Consistency | 3 | Aligns with other frameworks |

## Options Considered

### Option A: Mirror thoroughness (evidence levels)
- Vary by E1/E2/E3
- Trade-offs: Consistent; but verification evidence differs from research evidence

### Option B: Vary by criteria coverage only
- Adequate = critical; Rigorous = all; Exhaustive = all + edge cases
- Trade-offs: Simple; doesn't address method depth

### Option C: Multi-dimensional
- Vary 6 dimensions independently
- Trade-offs: Complete; more complex

### Option D: Null (defer)
- Trade-offs: Avoids lock-in; delays progress

## Evaluation

| Option | Failure Coverage (5) | Proportionality (4) | Clarity (4) | Consistency (3) | Total |
|--------|---------------------|---------------------|-------------|-----------------|-------|
| A | 3 | 4 | 5 | 5 | 66 |
| B | 3 | 4 | 5 | 4 | 63 |
| C | 5 | 5 | 3 | 4 | 70 |
| D | 0 | 5 | 5 | 5 | 55 |

## Pressure Test

1. **6 dimensions is complex**
   - Response: Table is reference material; users pick a level, framework tells them what's required

2. **Pre-mortem: People mix levels inconsistently**
   - Response: Each level is a package — no mixing. Upgrade whole level if needed.

3. **Steelman Option A: Just use evidence levels**
   - Response: Verification has unique dimensions (environment, method independence) that evidence levels don't capture

## Decision

**Choice:** Option C — Multi-dimensional with 6 dimensions

### Stakes Calibration Table

| Dimension | Adequate | Rigorous | Exhaustive |
|-----------|----------|----------|------------|
| **Criteria scope** | Critical path only | All stated criteria | All criteria + edge cases + failure modes |
| **Method depth** | Single method per criterion | Primary + backup for critical | Multiple independent methods; triangulation |
| **Evidence bar** | Artifacts required | Artifacts + explicit comparison | Artifacts + comparison + independent confirmation |
| **Disconfirmation** | Quick "what would failure look like?" | Active search for failure evidence | Assume failure, prove otherwise |
| **Iteration cap** | 1-2 passes | 2-3 passes | 3-5 passes |
| **Environment** | Primary environment | Primary + one alternate | All relevant environments |

**Trade-offs Accepted:** More complex than single-dimension; mitigated by package approach

**Confidence:** High

**Caveats:** If 6 dimensions overwhelming, consider collapsing Environment into Method depth

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | (initial) | Option C | Multi-dimensional covers unique verification needs |

## Exit Gate
- [x] Minimum passes met
- [x] Frame complete
- [x] Evaluation complete
- [x] Convergence met
- [x] Trade-offs documented
- [x] Iteration log complete
- [x] Transition tree passed
