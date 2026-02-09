# Decision Record: Post–Tier A Next Steps

**Date:** 2026-02-09
**Status:** Decided
**Stakes:** Rigorous
**Decision:** What should we do next now that Tier A is closed and benchmark v1 pilot artifacts are finalized?

## Entry Gate

- **Stakes level:** Rigorous
- **Rationale:** This decision sets the default workflow for future skill work (time/attention allocation, what evidence we consider “enough,” and how we avoid misleading quality claims). It’s reversible, but a wrong default can burn many sessions.
- **Iteration cap:** 3 passes
- **Minimum passes:** 2
- **Escalation trigger:** If we cannot articulate a “default loop” that (a) produces user value and (b) preserves claim integrity, escalate before doing more runs or building more infrastructure.

## Context

We have convergent evidence across multiple phases:

- Rubric-based outcome scoring saturates at current prompt difficulty (ceiling effects; low discriminability).
- Tier A (behavioral marker separation) is sufficient to claim “skill induces intended workflow behaviors,” but does not justify “skill improves outcomes.”
- Tier B (outcome-quality tests) is parked and trigger-gated (only when a quality claim is required or stakes demand it).

Tier A closure is recorded in:
- `docs/plans/2026-02-08-tier-a-closure.md`

## Constraints

1. **Claim integrity is load-bearing:** avoid sliding from “process compliance” into implied “quality improvement.”
2. **Time is scarce:** default path must be cheap and repeatable (avoid ongoing benchmark upkeep).
3. **Measurement contamination is real:** when outputs have been read, treat marker work as exploratory unless validated on fresh runs.
4. **Skills are built for use:** the next phase should put skills into real workflows, not continue synthetic measurement by default.

## Stakeholders

- **Skill author / maintainer:** wants a fast loop to iterate skill bodies without pretending to prove more than we can.
- **Skill user:** cares about usefulness and trustworthiness in real tasks.
- **Future reviewer (you in 3 months):** needs the docs to make the claim boundary obvious and defensible.

## Criteria (Weighted)

1. **Time-to-learning / throughput** (weight 5): move forward quickly without requiring many runs.
2. **Claim defensibility** (weight 5): preserves hard boundary between Tier A and Tier B.
3. **Practical usefulness feedback** (weight 4): helps identify “compliance theater” early.
4. **Up-front engineering cost** (weight 3): avoids heavy infra unless it returns compounding value.
5. **Reversibility** (weight 3): easy to pivot if assumptions are wrong.

## Options

### Option A — Adopt “Ship on Tier A” + field usage loop (Recommended)

Default loop:
1. Define intended behavioral artifacts (Tier A).
2. Quick A/B check for those artifacts (low N; strict variants when feasible).
3. Ship into a real workflow.
4. Watch for Tier B triggers (high stakes, explicit quality claim needed, or compliance theater).

### Option B — Search for a Tier B “difficulty frontier”

Invest in designing harder synthetic scenarios until baseline fails in a way process structure can prevent, then run blinded outcome tests to prove quality improvements.

### Option C — Continue benchmark suite iteration (scenario/rubric redesign + new pilot)

Treat pilot FAIL (e.g., scenario 101 regression) as a signal to keep iterating the benchmark suite until it becomes a stable outcome-measurement instrument.

### Option D — Tooling-first: build marker detection scripts + strict variants now

Build automation (regex + parsing) and run it over all stored outputs; treat scripts as the product, then return to skill building.

### Option E — Null option: park the program

Stop measurement and stop systematic validation; build skills ad hoc without explicit evidence tiers.

## Evaluation (Pass 1)

Scores: 0–5 (5 is best). Weighted total = Σ(score × weight).

| Option | Throughput (5) | Defensibility (5) | Usefulness feedback (4) | Cost (3) | Reversible (3) | Total |
|---|---:|---:|---:|---:|---:|---:|
| A | 5 | 5 | 4 | 4 | 5 | 88 |
| B | 1 | 4 | 2 | 1 | 2 | 41 |
| C | 2 | 4 | 1 | 1 | 3 | 42 |
| D | 3 | 5 | 1 | 2 | 4 | 59 |
| E | 5 | 1 | 3 | 5 | 5 | 67 |

**Frontrunner:** Option A

## Pressure Test (Pass 1 → 2)

**Kill it:** “Tier A shipping can devolve into compliance theater; we might ship skills that look disciplined but aren’t useful.”
- **Response:** Make “usefulness observation” an explicit part of the loop and treat “compliance theater observed” as a Tier B trigger (already in the evidence tiers decision).

**Pre-mortem:** 6 months later we’ve shipped many skills and can’t tell which ones matter.
- **Response:** Require each skill to declare (a) intended artifacts and (b) target workflow. Maintain a lightweight “field notes” log per skill (not a benchmark).

**Steelman Option D:** Automation might pay off if we build many skills.
- **Response:** True, but only if we are routinely re-running detection at scale or integrating into CI. At current scale, D is overhead. We can defer scripts until the first clear need (larger N, CI gating, repeated audits).

No frame changes required.

## Evaluation (Pass 2)

No new information changed the ranking; Option A remains the frontrunner. Option D is a reasonable add-on later if/when scale appears.

## Recommendation

Adopt **Option A**: “Ship on Tier A + field usage loop,” with Tier B reserved for triggers.

## Trade-offs Accepted

- We accept that the default program will not produce general outcome-improvement claims.
- We accept slower progress on automation in exchange for higher immediate skill-building throughput.
- We accept that “usefulness” will be monitored qualitatively unless/until a Tier B test is required.

## Confidence and Caveats

- **Confidence:** Medium-high
- **Caveats / what would change this:**
  1. If we need to make an explicit “quality improved” claim for a specific skill, immediately run a Tier B targeted test (pre-registered + blinded).
  2. If we start validating at higher N or want CI gating, revisit Option D (automation) as a compounding investment.

## Immediate Next Actions

1. Pick one real workflow to target first (incident analysis / architecture recommendations / rubric-like evaluations / code review).
2. For the first skill in that workflow, write down 1–3 intended behavioral artifacts (Tier A) and run a minimal A/B artifact check.
3. Start a small per-skill “field notes” log to detect compliance theater early (no scoring; just observations and triggers).

