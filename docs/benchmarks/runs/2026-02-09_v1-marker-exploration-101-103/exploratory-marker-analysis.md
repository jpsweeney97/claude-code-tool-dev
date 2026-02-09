# Exploratory Marker Analysis — Scenarios 101 & 103 (Pilot run-1)

**Analysis ID:** `2026-02-09_v1-marker-exploration-101-103`  
**Date:** 2026-02-09  
**Source run:** `2026-02-08_benchmark-v1_pilot-01` (existing pilot outputs; no new execution)  
**Purpose:** Hypothesis generation for behavioral markers on scenarios 101 and 103.

## Status: Exploratory (Not Pre-Registered)

This analysis is **post-hoc**: it is derived by reading pilot outputs and proposing marker definitions based on what is observed.

Because the pilot outputs for scenarios 101/103 were likely read in prior benchmark sessions, **true pre-registration discipline cannot be established retroactively** for those same outputs.

**Claim boundary:** This document proposes candidate markers and detection patterns. It does **not** claim outcome-quality improvement.

## Inputs / Artifacts Reviewed

### Scenario definitions

- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-constraint-ledger-101.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-verdict-gating-103.md`

### Canonical injected bodies (target condition)

- `docs/benchmarks/bench-skill-bodies_v1.0.0.md`
  - `BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0` (scenario 101)
  - `BENCH_PATTERN_VERDICT_GATING_v1.0.0` (scenario 103)

### Pilot run records (run-1)

- `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-constraint-ledger-101__baseline__run-1.md`
- `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-constraint-ledger-101__target__run-1.md`
- `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-verdict-gating-103__baseline__run-1.md`
- `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-verdict-gating-103__target__run-1.md`

## Scenario 101 (Constraint Ledger): Candidate Marker Found

### Why a marker exists here

The injected body for scenario 101 includes an extra procedural instruction not present in the scenario prompt:

- *Verify that the recommended option is the highest-scoring option in the score table; if not, revise.*

In the pilot:
- **Target** includes an explicit “verification step” artifact.
- **Baseline** includes a recommendation that aligns with the score table, but does not explicitly report having performed a verification step.

### Candidate marker: M101-1 (Score–Recommendation Verification Artifact)

**Marker ID:** `M101-1`  
**Intent:** Detect a **reported verification step** that cross-checks “recommended option == highest weighted score.”

**Soft definition (behavioral artifact):**
- Output contains an explicit statement that the runner **verified/confirmed** the recommended option is the highest-scoring option in the weighted score table.

**Suggested detection (regex, case-insensitive):**

- Primary (more specific):
  - `(?i)\\bverification step\\b.*\\b(highest|top)[- ]scor(?:ing|e)\\b`
- Alternative (more general; higher false-positive risk):
  - `(?i)\\b(confirm(?:ed)?|verif(?:y|ied|ies))\\b.*\\brecommended option\\b.*\\b(highest|top)[- ]scor(?:ing|e)\\b`

**Strict variant (internal-consistency check):**
- Parse the weighted score table and compute weighted totals.
- Parse the recommendation’s chosen option.
- Require: recommended option’s weighted total == max(total across options).
- Additionally require: presence of the verification-statement artifact (soft definition).

**Notes:**
- The strict variant is designed to reduce “compliance theater” (printing a verification claim without it being true).
- On this N=1 pilot sample, this marker separates baseline vs target; that separation is not yet validated on held-out runs.

## Scenario 103 (Verdict Gating): No Robust Binary Markers Observed (N=1)

### Why markers are hard here

The scenario prompt already requires:
- Evidence + Interpretation + Confidence + Decision Triggers sections,
- explicit computed metrics,
- a structured confidence downgrade (base + reasons + final),
- exactly 3 decision trigger bullets,
- no extra sections.

The injected body overlaps heavily with those same requirements (step-by-step arithmetic, threshold-first logic, structured downgrade, decision triggers). In the pilot, both conditions converge on the same visible structure.

### Observed differences (likely non-generalizable)

The target output includes a more procedural framing (“rule application, in order”), while the baseline uses more narrative framing (“three reasons…”).

This is not a robust marker candidate at N=1:
- It is stylistic rather than a clear “skill-induced” artifact.
- It is not required by the injected body text.
- It could appear in either condition under minimal prompting variance.

**Conclusion:** No binary markers are claimed for scenario 103 from this pilot pair.

## Cross-Scenario Hypothesis: Marker Separation Correlates with Prompt–Skill Orthogonality

Hypothesis (to be validated on fresh runs):
- Markers are most likely to appear when the injected body contains **procedural requirements not already demanded by the scenario prompt**.
- When the prompt already specifies the same structure/steps, the skill is largely redundant and produces little to no additional detectable artifacts.

If true, this provides a design heuristic:
- For marker-based Tier A evaluation, ensure skills introduce at least one orthogonal, testable behavior.
- Avoid prompts that already fully force the skill’s behavior (or accept that the skill may be indistinguishable from baseline).

## Next Steps (Method Discipline)

1. Treat this document as **exploratory marker discovery** only.
2. If pursuing Tier A closure:
   - Pre-register marker definitions (including strict variants) **before** generating any fresh runs used for validation.
   - Validate markers on **fresh 101/103 runs** (or on a scenario/output set not previously inspected by the prereg author).
3. Document “non-finding” for scenario 103 as an expected outcome under prompt–skill overlap, not as a failure.

