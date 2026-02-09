# Evaluate `making-recommendations` Skill

## Context

- Protocol: `decision-making.framework@1.0.0`
- Stakes level: Rigorous
- Decision trigger: User asked “what if we evaluated the making-recommendations skill?”
- Time pressure: No constraint
- Skill under evaluation: `/Users/jp/.codex/skills/making-recommendations/SKILL.md`

## Entry Gate

- Stakes level: Rigorous
- Time budget: 1–2 hours to define markers + setup; 2–3 weeks of lightweight field notes during normal work
- Iteration cap: 3 passes
- Evidence bar: Tier A (behavioral/process artifacts) + field usefulness loop; Tier B only on triggers
- Allowed skips: Skip I13 sensitivity analysis unless options are within ~10% in totals
- Escalation trigger: If we cannot define a Tier A/Tier B boundary that avoids circularity and preserves claim integrity, do not run outcome-quality tests

## Frame

### Decision Statement

What evaluation approach for `making-recommendations` gives sufficient evidence it is valuable *for its intended claim* (process-shaping), without recreating low-discriminability “quality benchmarking”?

### Constraints

- C1: Tier A is about behavioral/process compliance, not outcome-quality improvement
- C2: Evaluating “decision quality” is subjective and easy to overfit without strong blinding/discriminability
- C3: Baseline-vs-target comparisons can be contaminated once the evaluator has read the skill
- C4: The default path must be low-overhead and repeatable

### Criteria

| Criterion | Weight | Definition |
|---|---:|---|
| Claim defensibility | 5 | Supports a precise claim without implying “better outcomes” |
| Discriminability | 5 | Produces observable separation between “skill loaded” and “not loaded” |
| Cost / overhead | 4 | Ongoing maintenance and time overhead |
| Usefulness signal | 4 | Detects compliance theater and encourages corrective action |
| Reversibility | 3 | Ease of changing approach later |

### Stakeholders

| Stakeholder | What they value | Priority |
|---|---|---:|
| You (operator) | Faster, more defensible decisions | High |
| Future reviewers | Clear claim boundaries | High |
| Skill authors | Actionable feedback loops | Medium |

### Assumptions

- A1: The skill is primarily process-shaping (Tier A is meaningful). Status: unverified (reasonable prior)
- A2: Tier B tests should be rare and hypothesis-driven. Status: verified (existing evidence-tiers decision)

### Scope

- In bounds: Tier A artifact detection; lightweight strict checks; field usefulness notes as trigger detection
- Out of bounds: Default outcome-quality benchmarking for “better decisions”
- Related decisions: `docs/plans/2026-02-08-skill-evidence-tiers-decision.md`

### Reversibility

High. We can start with Tier A + field notes and add Tier B only when needed.

### Dependencies

- Depends on: Tier A/Tier B framework docs and closure notes
  - `docs/plans/2026-02-08-skill-evidence-tiers-decision.md`
  - `docs/plans/2026-02-08-tier-a-closure.md`
- Blocks: none

### Downstream Impact

- Enables: a repeatable evaluation template for meta-skills (frameworks/checklists)
- Precludes: claiming “better decisions” by default without Tier B evidence

## Options Considered

### Option A: Tier A-only (artifact compliance check)

- Description: Define behavioral markers and check baseline vs skill-loaded outputs for separation.
- Trade-offs: Gains low cost + defensibility; sacrifices usefulness signal beyond compliance.

### Option B: Tier A + field usefulness loop (Recommended)

- Description: Option A plus lightweight field notes during real work; treat compliance theater as Tier B trigger.
- Trade-offs: Gains usefulness signal without heavy infra; sacrifices some objectivity (field notes are subjective).

### Option C: Tier B outcome tests (score “decision quality”)

- Description: Build an evaluation rubric for recommendation quality and run blinded comparisons.
- Trade-offs: Gains outcome-centric evidence; sacrifices cost, discriminability, and risks overfitting.

### Option D: Tooling-first (enforce template via scripts)

- Description: Build lint-like checks that decision records contain required sections.
- Trade-offs: Gains enforcement and consistency; sacrifices usefulness signal and may be premature at small scale.

### Option E: Null (do not evaluate; use as-is)

- Description: Treat the skill as valuable by design judgment alone.
- Trade-offs: Gains speed; sacrifices defensibility and early detection of failure modes.

## Evaluation

### Criteria Scores

Scores 0–5 (5 best). Weighted total = Σ(score × weight).

| Option | Claim defensibility (5) | Discriminability (5) | Cost / overhead (4) | Usefulness signal (4) | Reversibility (3) | Total |
|---|---:|---:|---:|---:|---:|---:|
| A | 5 | 4 | 5 | 1 | 5 | 79 |
| B | 5 | 4 | 4 | 4 | 5 | 91 |
| C | 3 | 2 | 1 | 3 | 2 | 45 |
| D | 4 | 5 | 2 | 1 | 4 | 66 |
| E | 1 | 0 | 5 | 0 | 5 | 36 |

### Risks per Option

| Option | Key Risks | Mitigation |
|---|---|---|
| A | “Passes” even if useless (compliance theater) | Add field loop or Tier B trigger discipline |
| B | Subjective field notes; could rationalize | Treat as trigger detection only; prereg Tier B hypotheses when triggered |
| C | Low discriminability; expensive; subjective | Only do when a specific quality claim is required |
| D | Premature infra; enforces form over substance | Defer until scale/CI gating is needed |
| E | No defensible evidence; drift risk | Adopt at least Tier A markers |

### Information Gaps

- How often will we need to justify a “quality improvement” claim (Tier B trigger frequency)?
- How often will field notes indicate compliance theater in practice?

### Bias Check

- Familiarity bias: risk of preferring “structured docs” because they feel safer → countered by explicitly scoring usefulness signal and requiring field loop
- Sunk cost: we’ve already invested in Tier A framing → countered by including null option and considering Tier B
- Anchoring: Option B resembles current direction → pressure-tested against Option D (automation) and Option C (quality tests)

## Perspectives

| Stakeholder | View of Options | Concerns |
|---|---|---|
| You (operator) | Wants Option B (fast + useful) | Avoids analysis paralysis; wants minimal overhead |
| Future reviewers | Prefer A or B with strong claim boundary | Strongly oppose “quality” claims without Tier B |
| Skill authors | Prefer B or D (actionable + enforceable) | Want signal that maps to concrete improvements |

## Pressure Test

### Arguments Against Frontrunner (Option B)

1. Field notes are subjective; could confirm prior beliefs.
   - Response: Use field notes only to detect triggers (compliance theater / stakes / claim needs). If triggered, move to Tier B with pre-registration + blinding.
2. The skill could create overhead and slow down decisions.
   - Response: Enforce stakes calibration and allow “adequate” decisions; track time/verbosity as an explicit field-note dimension.
3. We might end up needing automation anyway.
   - Response: True; defer Option D until (a) scale appears or (b) CI gating is desired.

### Disconfirmation Attempts

- Sought: A reason to prefer a “quality benchmarking” default (Option C) or a tooling-first default (Option D).
- Found: Both have high overhead and weak discriminability at this stage; they are better as triggered or scaling responses.

## Decision

**Choice:** Option B — Tier A artifact evaluation + field usefulness loop

**Trade-offs Accepted:**
- Default evidence remains process-claim (Tier A), not outcome-quality.
- Field notes are used for trigger detection, not as “proof.”
- Automation is deferred until it has compounding returns.

**Confidence:** Medium-high

**Caveats:**
- If we must claim “better decisions,” run a Tier B targeted test (pre-registered hypothesis + blinded review).
- If contamination makes baseline indistinguishable, use fresh sessions/analysts or novel prompts for Tier A discrimination.

## Downstream Impact

- This enables: a cheap, defensible evaluation loop for meta-skills
- This precludes: implying outcome improvements by default
- Next decisions triggered: when to invest in Option D automation (scale/CI) or Tier B tests (triggered)

## Iteration Log

| Pass | Frame Changes | Frontrunner | Key Findings |
|---|---|---|---|
| 1 | Initial frame and scoring | Option B | Best balance of defensibility, discriminability, and usefulness |
| 2 | No changes | Option B | Survived pressure test; alternatives are better as triggered/scaling responses |

## Exit Gate

- [x] All outer loop activities complete
- [x] All inner loop activities complete (rigorous-level depth)
- [x] Convergence indicators met (frontrunner stable across 2 passes; objections addressed; perspectives checked; bias check completed)
- [x] Trade-offs explicitly documented
- [x] Decision defensible under scrutiny

