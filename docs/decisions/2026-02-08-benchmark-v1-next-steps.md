> **Status: CLOSED** — Benchmark Tier A closed. See docs/plans/2026-02-08-tier-a-closure.md

# Decision Record: Benchmark v1 Next Steps

**Date:** 2026-02-08
**Status:** Decided
**Stakes:** Rigorous
**Decision:** What should we do next after benchmark v0 concluded as INCONCLUSIVE?

## Entry Gate

- **Stakes level:** Rigorous
- **Rationale:** The next step affects benchmark credibility, time cost (another multi-run cycle), and whether v1 can actually measure skill impact.
- **Iteration cap:** 3 passes
- **Minimum passes:** 2
- **Escalation trigger:** If we cannot define at least 3 discriminative v1 scenarios with clear pass/fail signals, escalate before launching another full run.

## Context

Benchmark v0 is complete (51/51 runs executed), and the architecture works. The final verdict is **INCONCLUSIVE** because improvement was demonstrated in only 1/6 scenarios (16.7%), below the Section 9.3 threshold (70%).

From the v0 report:
- Degradation detection is reliable (harmful/proxy controls are detected).
- Ceiling effects dominate 5/6 baseline-target comparisons.
- The strongest positive signal was scenario 007 (exact-three-options discipline).

## Criteria (Weighted)

1. **Discriminative power improvement** (weight 5)
2. **Time to actionable result** (weight 4)
3. **Risk of repeating inconclusive outcome** (weight 5)
4. **Operational complexity** (weight 3)
5. **Comparability to v0 baseline** (weight 3)

## Options Evaluated

### Option A — Focused v1 Redesign + Pilot + Full Run (Recommended)

Keep the architecture, redesign scenario/rubric content for discrimination, run a small pilot, then run full v1 only if pilot clears quality gates.

**Pros**
- Directly addresses the known failure mode (ceiling effects).
- Preserves v0 architecture investment.
- Reduces risk with pilot gate before full spend.

**Cons**
- Requires upfront rubric/scenario design work.

### Option B — Full Framework Overhaul Before v1

Rework architecture and scoring system broadly before any further benchmark runs.

**Pros**
- Could unlock larger long-term flexibility.

**Cons**
- High complexity and delay.
- Low evidence that architecture is the bottleneck (v0 suggests scenario design is).

### Option C — Publish v0 As-Is and Defer v1 (Null Option)

Stop at v0 and treat this as an architecture-validation-only result.

**Pros**
- Fastest path to closure.
- No additional execution cost.

**Cons**
- Leaves improvement question unresolved.
- Misses chance to validate target skills under better discrimination.

### Option D — Run More Replicates on Current v0 Scenarios

Increase N on existing scenarios without redesigning rubric/scenario shape.

**Pros**
- Minimal design effort.

**Cons**
- High likelihood of reproducing the same ceiling-induced zero deltas.
- Adds cost without fixing root cause.

## Recommendation

Adopt **Option A**.

Primary reason: it fixes the root cause (scenario/rubric discrimination) while preserving the already-validated architecture. It balances rigor and speed better than overhaul or pure replication.

## Proposed Execution Plan

1. **Freeze v0 package** (no new claims, only archival edits).
2. **Design v1 discriminative set**:
   - Expand rubric granularity to 0-3 or 0-4 for relevant dimensions.
   - Add at least 3 new scenarios with explicit measurable target-skill deltas (like 007).
   - Add scenario-specific rubric dimensions where justified.
3. **Pilot gate (small-N)**:
   - Run 1 baseline + 1 target replicate per new scenario.
   - Require at least 2/3 scenarios to show non-zero, interpretable baseline-target separation.
4. **Full v1 execution** only if pilot passes gate.
5. **Decision checkpoint**:
   - If pilot fails, revise scenario/rubric design before any full rerun.

## Trade-offs Accepted

- Slightly slower start due to design/pilot phase.
- Additional up-front rubric work in exchange for a much lower risk of another inconclusive full run.

## Confidence and Caveats

- **Confidence:** Medium-high
- **Caveat:** If constraints force no pilot phase, the risk of another inconclusive cycle increases materially.
