# Prompt Briefing Patterns for `codex` and `codex-reply`

**Purpose:** Improve consultation quality by using structured, high-signal prompts.  
**Audience:** Anyone preparing Codex consultation requests.

---

## Why Briefing Quality Matters

Better briefing quality usually produces:

- more precise recommendations
- fewer clarification loops
- better alignment with current constraints

Poor briefings produce generic output and slower iteration.

---

## Canonical Briefing Template

Use this structure for new `codex` calls:

```markdown
## Context
[Current task, constraints, environment, and desired outcome]

## Material
[Key code snippets, file paths, error output, attempted approaches]

## Question
[One concrete, answerable question]
```

---

## Pattern A: Architecture Review

**Use when:** validating design direction and trade-offs.

Include:

1. Current architecture summary.
2. Known constraints (latency, reliability, compliance, timeline).
3. Alternative options already considered.
4. Decision criteria ranked by priority.

Example question:

> Which design best minimizes deployment risk under these constraints, and why?

---

## Pattern B: Debugging Investigation

**Use when:** root cause is unclear.

Include:

1. Exact error message and timing.
2. Steps to reproduce.
3. What was already tried and why it failed.
4. Any recent changes likely related.

Example question:

> What are the top 3 likely root causes, with fastest verification step for each?

---

## Pattern C: Code Review Second Opinion

**Use when:** validating a proposed patch or implementation.

Include:

1. Goal of the change.
2. Patch summary.
3. Critical risk areas (security/perf/correctness).
4. Acceptance criteria.

Example question:

> Identify blocking risks first, then recommend minimal fixes.

---

## Pattern D: Plan Validation

**Use when:** reviewing rollout steps or migration plans.

Include:

1. Rollout sequence and dependencies.
2. Rollback criteria.
3. Monitoring/alert expectations.
4. Operational constraints.

Example question:

> Which step is highest risk, and what pre-flight check would most reduce that risk?

---

## Follow-Up (`codex-reply`) Pattern

For follow-up turns:

1. Reference prior recommendation briefly.
2. Add only new evidence.
3. Ask one refinement question.

Template:

```markdown
New evidence:
- [result 1]
- [result 2]

Given this, refine your recommendation for [specific objective].
```

---

## Anti-Patterns

1. Vague asks (“Thoughts?”).
2. Huge unstructured dumps without prioritization.
3. Missing failure history in debugging contexts.
4. Multiple unrelated questions in one turn.
5. Asking for action without stating constraints.

---

## Briefing Quality Rubric (Quick Score)

Score each 0–2:

1. Context clarity
2. Material relevance
3. Constraint specificity
4. Question precision
5. Follow-up focus

**Interpretation:**

- 8–10: high signal
- 5–7: acceptable, can improve
- 0–4: likely to produce generic/low-value output

