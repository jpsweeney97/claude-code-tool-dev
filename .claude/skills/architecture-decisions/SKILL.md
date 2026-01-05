---
name: architecture-decisions
description: >
  Systematic methodology for making and documenting architecture decisions.
  Provides decision frameworks, constraint clarification, tradeoff analysis, and
  ADR (Architecture Decision Record) output. Use when facing structural choices
  that are costly to reverse: service boundaries, data models, API contracts,
  technology selection, or integration patterns.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 9
---

# Architecture Decisions

Systematic methodology for making structural decisions that are costly to reverse.

## When to Use

Use architecture-decisions when:
- Facing a structural choice (not implementation detail)
- Decision is costly or impossible to reverse
- Multiple viable options exist with different tradeoffs
- Rationale needs to be documented for future maintainers
- Stakes warrant deliberate analysis

Do not use when:
- Choice is easily reversible (just try it)
- Single obvious option exists
- Decision is implementation detail, not structure
- Time pressure prohibits analysis (decide, document later)

**Key insight:** If you can change it in an afternoon without breaking things, it's not architecture.

## Quick Start

```text
1. Clarify   → What's being decided? What constraints apply?
2. Explore   → What options exist? What are their tradeoffs?
3. Decide    → Which option fits best? Why not the others?
```

**Minimum viable decision:**
```markdown
[ ] Decision stated as question (not solution)
[ ] Constraints listed (real vs assumed)
[ ] At least 2 options with tradeoffs
[ ] Rationale documented (WHY this, WHY NOT others)
[ ] ADR produced
```

## Triggers

- "Should we use X or Y?"
- "What's the right architecture for..."
- "Help me decide between..."
- "Architecture decision record"
- "Evaluate architectural options"
- `/architecture-decisions`

## Calibration

Match rigor to stakes. Light calibration done well beats deep calibration done poorly.

### Stakes Assessment

| Factor | Low (1) | Medium (2) | High (3) |
|--------|---------|------------|----------|
| **Reversibility** | Change in hours | Change in days/weeks | Months or impossible |
| **Blast radius** | Single component | Multiple services | System-wide |
| **Precedent** | One-off | May be referenced | Sets pattern for team |
| **Uncertainty** | Clear tradeoffs | Some unknowns | Significant fog |

**Score 4-6:** Light | **Score 7-9:** Medium | **Score 10-12:** Deep

### Calibration Levels

| Level | When | Process |
|-------|------|---------|
| **Light** | Low stakes, clear winner | Quick constraint check, brief tradeoff note, lightweight ADR |
| **Medium** | Moderate stakes, real tradeoffs | Full three phases, documented analysis, complete ADR |
| **Deep** | High stakes, significant uncertainty | Extended exploration, stakeholder input, detailed ADR with reversal plan |

**Default:** Medium. When uncertain, choose more rigor.

---

## The Three Phases

### Phase 1: Clarify

**Purpose:** Understand what's being decided and why it matters.

**Actions:**

1. **State the decision as a question**
   - Bad: "We should use PostgreSQL"
   - Good: "What database should we use for user data?"

2. **Identify the trigger**
   - What prompted this decision?
   - Is it the right time to decide? (Defer if possible)

3. **Clarify constraints**

   | Constraint | Source | Negotiable? |
   |------------|--------|-------------|
   | Must support 10K concurrent users | Product requirements | No |
   | Team knows PostgreSQL | Current skills | Yes (training) |
   | Budget < $500/month | Finance | Partially |

   **For each constraint, ask:**
   - Is this truly non-negotiable, or current preference?
   - Who imposed this? Can they change it?
   - What happens if we violate it?

4. **Assess stakes** (use Stakes Assessment table above)

5. **Set calibration level**

**Phase 1 complete when:** Decision stated clearly, constraints documented, stakes assessed.

### Phase 2: Explore

**Purpose:** Enumerate options with their tradeoffs.

**Actions:**

1. **List viable options** (filtered by real constraints)
   - Don't list options that violate hard constraints
   - Include "do nothing" if applicable
   - Include "defer" if timing is uncertain

2. **For each option, document:**

   | Dimension | Questions |
   |-----------|-----------|
   | **Benefits** | What does this enable? What problems does it solve? |
   | **Costs** | Implementation effort? Operational overhead? Learning curve? |
   | **Risks** | What could go wrong? How likely? How severe? |
   | **Fit** | How well does it match our constraints? |

3. **Identify decision criteria**
   - What would make each option the best choice?
   - Under what circumstances would you pick each?

4. **Check for obvious winner**
   - If one option dominates on all dimensions → proceed to ADR
   - If tradeoffs exist → continue to Phase 3

**Phase 2 complete when:** Options enumerated, tradeoffs documented, criteria clear.

### Phase 3: Decide

**Purpose:** Make and document the decision.

**Actions:**

1. **Apply criteria to options**

   | Option | Scalability | Maintainability | Cost | Risk | Fit |
   |--------|-------------|-----------------|------|------|-----|
   | A | High | Medium | $$ | Low | Good |
   | B | Medium | High | $ | Medium | Good |
   | C | High | Low | $$$ | Low | Partial |

2. **Select the option with strongest overall fit**
   - Not necessarily best on any single dimension
   - Must be acceptable on all critical dimensions

3. **Document rationale**
   - WHY this option (positive case)
   - WHY NOT alternatives (what they lack)
   - What tradeoffs are being accepted

4. **Identify reversal conditions**
   - Under what circumstances would we revisit?
   - What signals would indicate wrong choice?

5. **Produce ADR** (see ADR Template below)

**Phase 3 complete when:** ADR produced with rationale and reversal conditions.

---

## ADR Template

```markdown
# ADR-{number}: {title}

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-X]

## Context
What triggered this decision? What problem are we solving?
What constraints apply? What's the current situation?

## Decision
We will {decision}.

## Rationale
Why this choice:
- {reason 1}
- {reason 2}

Why not {alternative 1}:
- {reason}

Why not {alternative 2}:
- {reason}

## Consequences

### Positive
- {benefit 1}
- {benefit 2}

### Negative
- {cost/risk 1}
- {cost/risk 2}

### Neutral
- {implication}

## Reversal Conditions
We would revisit this decision if:
- {condition 1}
- {condition 2}
```

**ADR Hygiene:**
- Number sequentially (ADR-001, ADR-002, ...)
- Store in `docs/architecture/decisions/` or similar
- Link related ADRs
- Update status when decisions change

---

## Decision Frameworks

### Common Architecture Decisions

| Decision Type | Key Tradeoffs | Critical Questions |
|--------------|---------------|-------------------|
| **Monolith vs Services** | Simplicity vs independence | Team size? Deployment frequency? Scaling needs? |
| **SQL vs NoSQL** | Consistency vs flexibility | Query patterns? Schema stability? Transaction needs? |
| **Sync vs Async** | Simplicity vs resilience | Latency tolerance? Failure handling? Ordering needs? |
| **Build vs Buy** | Control vs speed | Core competency? Maintenance capacity? Customization needs? |
| **REST vs GraphQL** | Simplicity vs flexibility | Client diversity? Query complexity? Caching needs? |

### Monolith vs Services

**Choose monolith when:**
- Team < 10 engineers
- Domain boundaries unclear
- Deployment simplicity matters
- Can't afford operational overhead

**Choose services when:**
- Independent scaling required
- Different tech stacks per domain
- Team structure mirrors service boundaries
- Failure isolation critical

**Hybrid signal:** Start monolith, extract services when boundaries prove stable.

### SQL vs NoSQL

**Choose SQL when:**
- Complex queries with joins
- ACID transactions required
- Schema is stable
- Reporting/analytics needed

**Choose NoSQL when:**
- Schema flexibility required
- Horizontal scaling priority
- Document/graph data models natural
- Eventually consistent acceptable

**Hybrid signal:** Use both for different data types (polyglot persistence).

---

## Anti-Patterns

| Pattern | Problem | Alternative |
|---------|---------|-------------|
| **Architecture Astronaut** | Over-engineering for hypothetical future | Design for current needs with extension points |
| **Cargo Culting** | "Netflix uses it" isn't a reason | Verify YOUR constraints match the pattern's assumptions |
| **Decision Paralysis** | Analyzing forever, never deciding | Set deadline; reversible decisions can change |
| **Undocumented Decisions** | Future maintainers don't know WHY | Always produce ADR, even lightweight |
| **Premature Optimization** | Scaling for load you don't have | Build for current scale with clear scaling path |
| **Resume-Driven Development** | Choosing tech for career, not problem | Optimize for team and problem, not resume |

---

## Framework for Rigor

This skill implements the [Framework for Rigor](~/.claude/references/framework-for-rigor.md).

### How Architecture-Decisions Maps to the Framework

| Framework Phase | Architecture-Decisions Phase | Key Actions |
|-----------------|------------------------------|-------------|
| **Definition** | Clarify | State decision, clarify constraints, assess stakes |
| **Execution** | Explore | Enumerate options, document tradeoffs, identify criteria |
| **Verification** | Decide | Apply criteria, document rationale, produce ADR |

### Seven Principles Applied

| Principle | How Applied |
|-----------|-------------|
| **Appropriate Scope** | Stakes assessment determines calibration |
| **Adequate Evidence** | Options must be evaluated, not assumed |
| **Sound Inference** | Rationale must connect evidence to choice |
| **Full Coverage** | All viable options considered |
| **Documentation** | ADR captures process and rationale |
| **Traceability** | Decision linked to constraints and criteria |
| **Honesty** | Reversal conditions acknowledge uncertainty |

---

## Integration

**Before architecture-decisions:**
- `deep-exploration` — Understand the system before deciding about it

**After architecture-decisions:**
- Implement the decision
- Store ADR in repository
- Communicate to stakeholders

**During architecture-decisions:**
- `episodic-memory:search` — Check for prior related decisions

---

## Completion Criteria

Before claiming decision complete:

| Criterion | Verification |
|-----------|--------------|
| Decision clearly stated | Question form, not solution |
| Constraints documented | Source and negotiability for each |
| Options enumerated | At least 2 with tradeoffs |
| Criteria explicit | What would make each option best? |
| Rationale complete | WHY this, WHY NOT alternatives |
| ADR produced | All sections filled |
| Reversal conditions stated | When to revisit |

**Red flags:**
- "Obviously we should..." (skipped analysis)
- "Everyone uses..." (cargo culting)
- "In case we need..." (architecture astronaut)
- No ADR produced (undocumented decision)

---

## References

- [Framework for Rigor](~/.claude/references/framework-for-rigor.md) — Underlying methodology
- [Decision Frameworks](references/decision-frameworks.md) — Detailed frameworks for common decisions
- [ADR Examples](references/adr-examples.md) — Sample ADRs for reference

---

## Changelog

### v1.0.0
- Initial release
- Three-phase methodology (Clarify, Explore, Decide)
- Stakes-based calibration
- ADR template and hygiene guidelines
- Common decision frameworks (monolith/services, SQL/NoSQL)
- Integration with Framework for Rigor
