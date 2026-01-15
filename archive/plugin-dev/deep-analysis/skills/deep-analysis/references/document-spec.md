# Analysis Document Specification

The output format for deep analysis documents, optimized for Claude's future retrieval and human readability.

---

## File Naming

**Pattern:** `YYYY-MM-DD-slug.md`

**Examples:**
- `2025-01-15-microservices-migration.md`
- `2025-02-03-auth-provider-selection.md`
- `2024-11-20-database-sharding-strategy.md`

**Slug rules:**
- Lowercase
- Hyphens between words
- 3-5 words describing the decision
- No special characters

---

## Document Structure

### YAML Frontmatter

```yaml
---
type: deep-analysis
date: 2025-01-15
problem: microservices-migration
builds-on: [2024-11-03-monolith-pain-points]  # Optional
domain: [architecture, infrastructure]
decision: strangler-fig-pattern              # Required for accepted, omit for draft
status: accepted
keywords: [microservices, migration, strangler-fig, distributed-systems]
---
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Always `deep-analysis` |
| `date` | Yes | YYYY-MM-DD format |
| `problem` | Yes | Slug identifier matching filename |
| `status` | Yes | `draft`, `accepted`, or `superseded` |
| `decision` | Conditional | Required when `status: accepted` |
| `builds-on` | No | Array of prior analysis slugs |
| `domain` | No | Array of domain tags |
| `keywords` | No | Array of searchable terms |

### Status Values

- **draft** — Analysis in progress, decision not yet made
- **accepted** — Decision made and rationale documented
- **superseded** — Replaced by a newer analysis (link to replacement in body)

---

## Document Sections

### Problem

Clear, searchable statement of the decision being made. Use a blockquote for the core question.

```markdown
# Problem

Clear, searchable statement of what was being decided.

> Should we migrate our request-response API to event-driven
> architecture to reduce coupling between services?
```

**Guidelines:**
- One or two sentences framing the decision
- Blockquote contains the core question
- Searchable: include key terms someone might use to find this

### Context

Constraints and conditions at decision time. This section helps Claude judge whether this analysis applies to future similar situations.

```markdown
# Context

- Team: 4 engineers, limited async experience
- Timeline: Q2 delivery target
- Existing: Monolith with synchronous REST between modules
- Pain: Cascading failures when downstream services slow
- Budget: No additional headcount approved
- Dependencies: Must maintain backwards compatibility with mobile apps
```

**Guidelines:**
- Bullet points for scannability
- Include team composition, timeline, existing state
- Note constraints that influenced the decision
- Be specific enough that future-you can assess applicability

### Analysis

Document insights from each analytical framework. Skip frameworks that didn't reveal significant insights, but note that they were applied.

```markdown
# Analysis

## First Principles

- Core need: Services must communicate without tight coupling
- Challenged assumption: "All communication must be synchronous"
- Insight: 80% of our calls are fire-and-forget; only 20% need responses

## Systems Thinking

- Feedback loop identified: Slow service → timeouts → retries → more load → slower service
- Breaking the loop requires: Circuit breakers OR async decoupling

## Inversion

What would guarantee failure:
- Big-bang migration with no rollback
- Assuming team can learn Kafka in two weeks
- No observability into message flow

## Second-Order Effects

If we adopt event-driven:
1. First order: Services decouple
2. Second order: Debugging becomes harder (distributed tracing needed)
3. Third order: Team needs new skills → hiring criteria change

## Trade-off Analysis

| Dimension | Event-Driven | Request-Response |
|-----------|--------------|------------------|
| Coupling | Low | High |
| Debuggability | Harder | Easier |
| Complexity | Higher | Lower |
| Resilience | Better | Worse |

## Pre-mortem

Imagined failure modes:
1. Message ordering issues cause data corruption
2. Team burns out learning too many new things
3. Monitoring gaps lead to silent failures
```

**Guidelines:**
- Use framework names as section headers
- Include specific insights, not generic observations
- Tables for comparative analysis
- Bullet points for lists

### Options Considered

Document each option that was seriously considered.

```markdown
# Options Considered

## Option 1: Full Event-Driven Migration

**Approach:** Replace all synchronous calls with message queues (Kafka/RabbitMQ)

**Pros:**
- Maximum decoupling
- Excellent scalability
- Industry-standard patterns

**Cons:**
- Steep learning curve
- Debugging complexity
- Operational overhead (message broker)

**Verdict:** Rejected — Too much change at once for team size

## Option 2: Strangler Fig Pattern

**Approach:** Gradually replace synchronous calls with events, starting with highest-pain endpoints

**Pros:**
- Incremental learning
- Reversible at each step
- Quick wins visible early

**Cons:**
- Longer timeline to full migration
- Temporary complexity of hybrid system

**Verdict:** Accepted — Balances progress with manageable risk

## Option 3: Keep Request-Response, Add Circuit Breakers

**Approach:** Keep sync architecture but add resilience patterns

**Pros:**
- Minimal change
- Quick to implement
- Team already knows patterns

**Cons:**
- Doesn't solve coupling
- Still vulnerable to cascade failures
- Treats symptoms, not cause

**Verdict:** Rejected — Kicks the can, doesn't solve root problem
```

**Guidelines:**
- 2-5 options typically
- Consistent structure: Approach, Pros, Cons, Verdict
- Verdict includes reasoning
- Rejected options are valuable documentation

### Decision

Clear statement of the choice with rationale.

```markdown
# Decision

Adopt the **Strangler Fig Pattern** for gradual migration to event-driven architecture.

**Rationale:**
- Matches team's learning capacity
- Provides early wins to build momentum
- Each step is reversible if issues emerge
- Reduces risk compared to big-bang migration

**Starting point:** The order notification pipeline (highest pain, lowest risk)

**Success metric:** 50% of inter-service communication async by end of Q3
```

**Guidelines:**
- Bold the chosen option
- 3-5 bullet points for rationale
- Include starting point if applicable
- Define success metric when possible

### Risks Accepted

Document known risks that were accepted as part of the decision.

```markdown
# Risks Accepted

| Risk | Likelihood | Severity | Mitigation |
|------|------------|----------|------------|
| Message ordering issues | Medium | High | Design idempotent consumers, add sequence numbers |
| Team burnout during learning curve | Low | Medium | Timebox learning sprints, celebrate wins |
| Debugging distributed flows | High | Medium | Invest in distributed tracing (Jaeger) |
| Vendor lock-in to message broker | Low | Low | Abstract message layer, use standard protocols |
```

**Guidelines:**
- Table format for scannability
- Likelihood: Low/Medium/High
- Severity: Low/Medium/High/Critical
- Every risk needs a mitigation (even if "accept and monitor")

### Lessons (Post-Implementation)

Added after the decision is implemented. This section turns analysis documents into institutional memory.

```markdown
# Lessons

*Added 2025-04-01 after Q1 implementation*

## What Worked

- Strangler approach gave team confidence
- Starting with order pipeline was right choice (high visibility win)
- Distributed tracing investment paid off immediately

## What We'd Do Differently

- Would have set up dead letter queues earlier
- Underestimated schema evolution complexity
- Should have done more load testing before first production migration

## Gotchas for Future Reference

- Kafka consumer group rebalancing causes brief duplicates — consumers MUST be idempotent
- Our specific Kafka version has a known issue with exactly-once semantics
- The strangler proxy added 2ms latency — acceptable but notable
```

**Guidelines:**
- Add this section after implementation
- Date when lessons were added
- Be specific about what worked and what didn't
- Gotchas section prevents others from hitting same issues

---

## Complete Template

```markdown
---
type: deep-analysis
date: YYYY-MM-DD
problem: slug-description
builds-on: []
domain: []
decision: chosen-option-slug
status: draft | accepted | superseded
keywords: []
---

# Problem

Clear, searchable statement of what was being decided.

> The core question in blockquote form?

# Context

- Constraint 1
- Constraint 2
- Current state
- Pain points

# Analysis

## First Principles

[Insights from challenging assumptions]

## Systems Thinking

[Insights from mapping interactions]

## Inversion

[Insights from imagining failure]

## Second-Order Effects

[Insights from tracing consequences]

## Trade-off Analysis

[Insights from identifying tensions]

## Pre-mortem

[Insights from assuming failure]

# Options Considered

## Option 1: Name

**Approach:** Description

**Pros:**
- Pro 1
- Pro 2

**Cons:**
- Con 1
- Con 2

**Verdict:** Accepted | Rejected — because...

## Option 2: Name

[Same structure]

# Decision

**Chosen option** statement.

**Rationale:**
- Reason 1
- Reason 2
- Reason 3

# Risks Accepted

| Risk | Likelihood | Severity | Mitigation |
|------|------------|----------|------------|
| Risk 1 | Low/Medium/High | Low/Medium/High/Critical | How to handle |

# Lessons

*Added YYYY-MM-DD after implementation*

## What Worked

- Learning 1
- Learning 2

## What We'd Do Differently

- Change 1
- Change 2

## Gotchas for Future Reference

- Gotcha 1
- Gotcha 2
```

---

## Search Optimization

To make documents findable by semantic search:

1. **Problem section:** Use natural language someone would use to search
2. **Keywords field:** Include synonyms and related terms
3. **Domain field:** Use consistent taxonomy across analyses
4. **Context:** Include technology names, patterns, and constraints

**Example keywords for a caching decision:**
```yaml
keywords: [caching, redis, memcached, performance, latency, ttl, cache-invalidation]
```

---

## Linking Analyses

When an analysis builds on or supersedes another:

### Building On

```yaml
builds-on: [2024-11-03-monolith-pain-points, 2024-12-15-service-boundaries]
```

In the body, reference why:
> This analysis builds on our earlier pain points assessment and service boundary mapping.

### Superseding

```yaml
status: superseded
```

In the body, link to replacement:
> **Superseded by:** [2025-06-01-revised-migration-strategy](./2025-06-01-revised-migration-strategy.md)
>
> This analysis was superseded after Q1 learnings revealed issues with our timeline assumptions.
