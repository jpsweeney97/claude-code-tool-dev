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

### Other observed differences (not promoted to markers)

**Arithmetic self-correction:** Both conditions caught and corrected arithmetic errors in their weighted score tables. Target labeled it "Calculation verification:" while baseline said "let me recompute." Both produced corrected tables. This is a ceiling effect — Claude self-corrects arithmetic regardless of the skill — so the correction behavior is not a distinguishing marker. The labeling difference is too weak for a binary marker at N=1.

**Process Report section:** Target included a distinct "## Process Report" section with numbered "Decisions made" and "Tools used" subsections. Baseline had no such section. However, the skill body does not instruct a process report — this may be a runner artifact rather than a skill-induced behavior. Not promoted without evidence of skill causation.

**Tool usage:** Target used Glob to search for references; baseline used no tools. Already noted as a confounder in the run record. Tool usage is runner-specific, not skill-induced.

## Scenario 103 (Verdict Gating): No Robust Binary Markers Observed (N=1)

### Why markers are hard here

The scenario prompt already requires:
- Evidence + Interpretation + Confidence + Decision Triggers sections,
- explicit computed metrics,
- a structured confidence downgrade (base + reasons + final),
- exactly 3 decision trigger bullets,
- no extra sections.

The injected body overlaps heavily with those same requirements (step-by-step arithmetic, threshold-first logic, structured downgrade, decision triggers). In the pilot, both conditions converge on the same visible structure.

### Feature-by-feature comparison (N=1)

| Feature | Target | Baseline | Separated? |
|---------|--------|----------|:----------:|
| Evidence/Interpretation separation | Yes (distinct `##` sections) | Yes (distinct `##` sections) | No |
| Step-by-step arithmetic | Yes ("2 / 6 = 33.3%") | Yes ("2 / 6 = 33.3%") | No |
| Threshold rule citation | Yes (explicit threshold comparisons) | Yes (explicit threshold comparisons) | No |
| Confidence downgrade structure | Yes (base → factor 1 → factor 2 → final) | Yes (base → reason 1 → reason 2 → final) | No |
| Decision triggers (3 bullets) | Yes | Yes | No |
| Pass/fail per gate | Yes ("threshold NOT met") | Yes ("Result: **FAILS**") | No |

### Prompt–skill overlap (why no markers exist)

| Skill Instruction | Also In Prompt? | Result |
|-------------------|:---------------:|--------|
| Show intermediate calculations | Yes ("explicit computed metrics") | Both conditions show arithmetic |
| Apply threshold rules directly | Yes ("using these rules: YES requires...") | Both conditions cite rules |
| Separate Evidence and Interpretation | Yes ("Section 'Evidence'... Section 'Interpretation'") | Both conditions use separate sections |
| Structured confidence downgrade | Yes ("base confidence... downgrade reason(s)... final confidence") | Both conditions use the structure |
| Concrete decision triggers | Yes ("Section 'Decision Triggers' with exactly 3 bullet points") | Both conditions provide 3 triggers |

### Observed differences (likely non-generalizable)

The target output includes a more procedural framing (“rule application, in order”), while the baseline uses more narrative framing (“three reasons…”).

This is not a robust marker candidate at N=1:
- It is stylistic rather than a clear “skill-induced” artifact.
- It is not required by the injected body text.
- It could appear in either condition under minimal prompting variance.

**Conclusion:** No binary markers are claimed for scenario 103 from this pilot pair.

## Cross-Scenario Hypothesis: Marker Separation Correlates with Prompt–Skill Orthogonality

| Scenario | Prompt–skill orthogonality | Markers found | Exploratory separation |
|----------|:--------------------------:|:-------------:|:----------------------:|
| 101 | **High** — skill adds verification instruction not in prompt | 1 (M101-1) | 1/1 vs 0/1 |
| 102 | **High** — skill adds counting, threshold, and downgrade instructions not in prompt | 3 (M1, M2, M3) | 3/3 vs 0/3 |
| 103 | **Low** — skill reinforces structure already specified in prompt | 0 | N/A |

Hypothesis (to be validated on fresh runs):
- Markers are most likely to appear when the injected body contains **procedural requirements not already demanded by the scenario prompt**.
- When the prompt already specifies the same structure/steps, the skill is largely redundant and produces little to no additional detectable artifacts.

If true, this provides a design heuristic:
- For marker-based Tier A evaluation, ensure skills introduce at least one orthogonal, testable behavior.
- Avoid prompts that already fully force the skill's behavior (or accept that the skill may be indistinguishable from baseline).

### Falsifiers

This pattern would be falsified by:
1. Finding binary markers in 103 on a larger sample (N=1 may have missed a difference that appears at N=3+).
2. Finding a scenario where prompt–skill overlap is high yet markers still emerge (suggesting the correlation is coincidental).
3. Finding a scenario where prompt–skill orthogonality is high yet markers don't emerge (suggesting other factors dominate).

## All Markers Summary

| Marker | Scenario | Definition | Exploratory Separation | Confidence |
|--------|----------|------------|:----------------------:|:----------:|
| M101-1 | 101 | Explicit score–recommendation verification step | 1/1 vs 0/1 | Low (N=1, post-hoc) |
| M1 | 102 | Explicit row counting | 3/3 vs 0/3 | Medium (N=3, post-hoc) |
| M2 | 102 | Confidence threshold verification | 3/3 vs 0/3 | Medium (N=3, post-hoc) |
| M3 | 102 | Confidence downgrade summary | 3/3 vs 0/3 | Medium (N=3, post-hoc) |
| (none) | 103 | No binary markers found | N/A | N/A |

**Total:** 4 markers across 2 scenarios. 1 scenario (103) has no detectable markers under this method.

## Next Steps (Method Discipline)

1. Treat this document as **exploratory marker discovery** only.
2. If pursuing Tier A closure:
   - Pre-register marker definitions (including strict variants) **before** generating any fresh runs used for validation.
   - Validate markers on **fresh 101/103 runs** (or on a scenario/output set not previously inspected by the prereg author).
3. Document “non-finding” for scenario 103 as an expected outcome under prompt–skill overlap, not as a failure.

