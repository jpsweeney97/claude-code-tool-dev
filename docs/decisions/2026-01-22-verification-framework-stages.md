# Verification Framework Stage Structure

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: Designing the Framework for Verification; need to choose stage structure
- Time pressure: None

## Entry Gate
- Stakes level: adequate (easy to revise, moderate blast radius, medium cost of error)
- Time budget: 30 minutes
- Iteration cap: 2
- Evidence bar: Structure must map to failure modes and remain domain-agnostic
- Allowed skips: Deep stakeholder analysis; sensitivity analysis
- Escalation trigger: If structure choice blocks framework design progress

## Frame

### Decision Statement
What stage structure should the Framework for Verification use?

### Constraints
- Must be domain-agnostic (work for code, analysis, decisions, documents)
- Must align with existing framework patterns (Entry Gate, loop, Exit Gate)
- Must address all three failure modes (completion theater, shallow validation, scope confusion)

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| Failure mode coverage | 5 | Does each stage prevent a specific failure? |
| Domain agnosticism | 5 | Works across code, analysis, documents, etc.? |
| Clarity | 4 | Is it obvious what happens in each stage? |
| Parsimony | 3 | No unnecessary stages; no missing essential ones |

### Stakeholders
| Stakeholder | What they value | Priority |
|-------------|-----------------|----------|
| Framework author | Coherent design that complements existing frameworks | High |
| Claude (executor) | Clear, actionable stages | High |
| End users | Verified outputs, not verification theater | High |

### Assumptions
- A1: Stage names should be verbs/actions (consistent with thoroughness framework) [verified]
- A2: Stakes-based depth can handle "overhead for simple cases" concern [unverified]

### Reversibility
Easy — we're designing, not implementing. Can revise structure before finalizing framework.

## Options Considered

### Option A: DEFINE → DESIGN → EXECUTE → EVALUATE (4 stages)
- Description: Four distinct stages, each addressing a specific phase of verification
- Trade-offs: Complete coverage of failure modes; DESIGN and EXECUTE might blur in practice

### Option B: DEFINE → EXECUTE → EVALUATE (3 stages)
- Description: Merge DESIGN into EXECUTE for simplicity
- Trade-offs: Simpler to remember; loses explicit "choose your method" step — risks shallow method selection

### Option C: SPECIFY → VERIFY → JUDGE (3 stages, different framing)
- Description: Alternative naming with fewer stages
- Trade-offs: Cleaner names; but "VERIFY" as a stage name inside a verification framework is confusing

### Option D: DEFINE → DESIGN → EXECUTE → EVALUATE → ITERATE (5 stages)
- Description: Make iteration an explicit stage
- Trade-offs: Makes iteration explicit; but other frameworks handle iteration via loop structure, not a stage

### Option E: Null (defer)
- Description: Gather more input before deciding
- Trade-offs: No risk of wrong choice now; but we have enough context to decide

## Evaluation

### Criteria Scores
| Option | Failure Coverage (5) | Domain Agnostic (5) | Clarity (4) | Parsimony (3) | Total |
|--------|---------------------|---------------------|-------------|---------------|-------|
| A (4 stages) | 5 | 5 | 4 | 4 | 77 |
| B (3 stages) | 3 | 5 | 5 | 5 | 73 |
| C (renamed) | 4 | 5 | 3 | 4 | 68 |
| D (5 stages) | 5 | 5 | 4 | 2 | 71 |
| E (defer) | 0 | 5 | 5 | 5 | 55 |

### Information Gaps
- Will DESIGN feel redundant for simple verifications? (Mitigated by stakes-based depth)

### Bias Check
- Anchoring risk: I proposed Option A first. Mitigated by scoring all options.
- Familiarity: 4-stage structure mirrors existing patterns. This is appropriate alignment, not bias.

## Pressure Test

### Arguments Against Frontrunner
1. **DESIGN and EXECUTE blur together**
   - Response: The separation is the point. DESIGN forces "what tests?" before "run tests." Without it, Claude jumps to the first method that comes to mind. This prevents shallow validation.

2. **Pre-mortem: People treat DESIGN as a formality**
   - Response: Real risk. Countermeasure: DESIGN must output a verification plan with specific methods and expected results. Can't be hand-waved.

### Disconfirmation Attempts
- Sought: Evidence that simpler 3-stage models work well in similar contexts
- Found: Testing frameworks (Arrange-Act-Assert) use 3 stages, but they don't address method selection — they assume you already know what to test

## Decision

**Choice:** Option A — DEFINE → DESIGN → EXECUTE → EVALUATE

**Trade-offs Accepted:**
- Slightly more complex than 3-stage model
- DESIGN requires non-trivial output to avoid becoming a formality

**Confidence:** High

**Caveats:**
- If DESIGN consistently feels like overhead in practice, consider merging with EXECUTE at "adequate" stakes level only
- Watch for checkbox behavior in DESIGN stage

## Downstream Impact
- Enables: Clear mapping of stages to failure modes in the framework
- Precludes: Ultra-simple 3-stage structure
- Next decisions: What activities belong in each stage? What are the failure modes per stage?

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | (initial) | Option A | Pressure test survived; DESIGN stage prevents shallow validation |

## Exit Gate
- [x] Minimum passes met (1 for adequate)
- [x] Frame complete (O1-O4 required for adequate)
- [x] Evaluation complete (3+ options, trade-offs, scoring)
- [x] Convergence met (frontrunner stable, trade-offs stated)
- [x] Trade-offs explicitly documented
- [x] Iteration log complete
- [x] Transition tree passed (clear frontrunner → pressure-tested → converged → EXIT)
