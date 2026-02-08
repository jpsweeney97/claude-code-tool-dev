# Discussion: Blinded Scoring Session — Benchmark v0

**Date:** 2026-02-07
**Session type:** Blinded evaluation of rubric scenarios
**Run ID:** `2026-02-06_benchmark-v0_initial`
**Evaluator:** Separate Claude Code session (blinded per suite policy)
**Artifact produced:** `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`

---

## Context

This session continued the Simulation-Based Skill Assessment work (see `DISCUSSION-MAP-simulation-based-assessment.md` for full history). After Phases 1-14 established the architecture, validated it through stress testing, and designed the Benchmark v0 framework, a benchmark run was executed (`2026-02-06_benchmark-v0_initial`). This session performed the **blinded evaluation** step — scoring the rubric scenario outputs without using condition labels in scoring judgments.

### What was being evaluated

The benchmark tests whether the simulation-based assessment architecture can measure functional skill effectiveness. It uses 8 scenarios: 3 anchor (objective oracle = tests/build) and 5 rubric (blinded scoring). This session scored the 5 rubric scenarios:

| Scenario | Task | Skill type tested |
|---|---|---|
| `v0-rubric-scenario-spec-004` | Write an anchor scenario definition | pattern |
| `v0-rubric-report-005` | Write a benchmark report template | pattern |
| `v0-rubric-controls-006` | Draft control skill bodies | discipline |
| `v0-rubric-exact-three-options-007` | Choose a search tool approach (exactly 3 options) | discipline |
| `v0-rubric-reference-008` | Answer repo questions with exact citations | reference |

---

## Procedure

### Blinding protocol

1. Did NOT read `handoff.md` or `handoff_codex.md` (contain condition planning)
2. Did NOT use condition labels (`baseline`/`target`/`placebo`/etc.) in scoring — used only output content
3. Scored each run record independently — no cross-condition comparison during scoring
4. Used only the filename as identifier in the output

### Rubric applied

6 dimensions, each scored 0-2 (total 0-12):

| Dimension | What it measures |
|---|---|
| Correctness | Meets task requirements |
| Completeness | Covers required parts |
| Constraint adherence | Follows explicit constraints |
| Reasoning quality | Decisions justified and traceable |
| Efficiency | Proportionate approach |
| Side effects | Regressions/risks/overfitting avoided |

Scenario-specific overrides from the suite matrix:
- **spec-004:** All Section 5.1 required fields present; success criteria checkable
- **exact-three-options-007:** Exact count compliance is PRIMARY; quality checks secondary
- **reference-008:** Emphasis on citation specificity and observation/inference distinction

---

## Discovery 1: The Benchmark Is Mostly Incomplete

### The numbers

| Scenario | Total runs | With output | Empty stubs | Scorable % |
|---|---:|---:|---:|---:|
| `v0-rubric-scenario-spec-004` | 9 | 6 | 3 | 67% |
| `v0-rubric-report-005` | 7 | 0 | 7 | 0% |
| `v0-rubric-controls-006` | 7 | 0 | 7 | 0% |
| `v0-rubric-exact-three-options-007` | 6 | 3 | 3 | 50% |
| `v0-rubric-reference-008` | 6 | 6 | 0 | 100% |
| **Total** | **35** | **15** | **20** | **43%** |

**57% of run records were empty stubs** with no runner output. Two entire scenarios (report-005, controls-006) were never executed at all.

### Why this matters

The benchmark's core measurement is the delta between baseline and target conditions. For most scenarios, either baseline or target (or both) are missing:

| Scenario | Baseline exists? | Target exists? | Delta computable? |
|---|---|---|---|
| spec-004 | Yes (N=3, scored 12/12) | No (empty stubs; no TARGET per suite — by design) | No |
| report-005 | No | No | No |
| controls-006 | No | No | No |
| exact-three-options-007 | No (empty stubs) | Yes (N=3, scored 12/12/11) | No |
| reference-008 | Yes (N=3, all 12/12) | Yes (N=3, all 12/12) | Yes — but delta = 0 |

**Only reference-008 allows delta computation**, and it shows zero measurable delta.

---

## Discovery 2: Controls Produce Expected Signals

The most encouraging finding comes from spec-004's control conditions (the only scenario where both baselines and controls were executed):

| Condition | File | Score | Expected profile |
|---|---|---:|---|
| Baseline run-1 | `...spec-004__baseline__run-1.md` | 12 | Strong output |
| Baseline run-2 | `...spec-004__baseline__run-2.md` | 12 | Strong output |
| Baseline run-3 | `...spec-004__baseline__run-3.md` | 12 | Strong output |
| Placebo | `...spec-004__placebo__run-1.md` | 12 | ~Zero degradation |
| Proxy gaming | `...spec-004__proxy_gaming__run-1.md` | 11 | Minor quality dip |
| Harmful brevity | `...spec-004__harmful_brevity_60w__run-1.md` | 7 | Clear degradation |

**This is textbook control behavior:**
- Placebo does not degrade (12 = baselines) — no priming/bias signal
- Proxy gaming causes subtle degradation (11) — structural compliance without full substance
- Harmful brevity causes clear degradation (7) — the constraint worked (fewer criteria, non-standard fields, ID collision, less precise references)
- **Delta from baseline to harmful: -5 points** — the largest observed delta

### What the harmful brevity run got wrong

The 7/12 score is not arbitrary. Specific quality issues:
1. Only 3 success criteria (vs 5-6 in baselines)
2. Only 3 failure modes (vs 5-6 in baselines)
3. Non-standard `confounders` YAML field (not in Section 5.1 schema)
4. Scenario ID `v0-anchor-build-regression-002` collides with existing `v0-anchor-frontmatter-002`
5. `files` field uses directories instead of specific files
6. More complex task design (MCP tool addition vs simple function addition)
7. Missing `difficulty` optional field (present in all other runs)

The brevity control was supposed to limit output to 60 words. It didn't achieve that (the YAML artifact is ~250 words — the task demand overrode the compression instruction). But it DID reduce thoroughness across every quality dimension.

### Proxy gaming behavioral signal

The proxy gaming run (11/12) showed partial structural compliance with the control body's required headings (Scope, Preconditions, Self-check, Output). The runner used 2 of 4 headings (Self-check, Output) and included a verification claim in the Self-check section. The scenario content was still good, but the "Self-check" assertion lacked supporting evidence — it was assertion-only rather than demonstrating actual verification.

---

## Discovery 3: Reference-008 Shows Zero Measurable Delta

All 6 reference-008 runs (3 baseline, 3 with injected body) scored 12/12. Two likely explanations:

### Ceiling effect

The task has clear, objectively verifiable right answers:
1. Two specific files (`control-bodies_v0.1.0.md` and `bench-skill-bodies_v0.1.0.md`)
2. One specific heading (`## Loaded Skill` defined in `simulation-assessment-context-official.md`)

Any competent runner — with or without a reference skill — answers correctly with proper citations. The skill has nothing to improve when the task is straightforward file lookup.

### Rubric granularity too coarse

Real qualitative differences exist between runs but don't resolve into point separations at the 0-2 scale:

| Quality signal | Which runs? | Point difference? |
|---|---|---|
| Quoted source text vs paraphrased | baseline run-2 quoted; run-1 paraphrased | No (both score 2/2 on completeness) |
| Primary vs reference distinction | baseline runs 2-3 and all targets distinguished; run-1 listed flatly | No (both score 2/2 on reasoning) |
| Explicit inference labeling | Only target run-3 used "Inference" label | No (both score 2/2 on constraint adherence) |
| Authority self-declaration quoted | Target runs 1-2 quoted lines 102-103; baselines didn't | No (both score 2/2 on completeness) |

Target run-3's explicit inference label was the most notable quality signal. The runner identified that "standardized injection slot" is a descriptive phrase in derivative files, not a term in the authoritative source — and correctly labeled this reasoning as inference rather than observation. This is the deepest citation discipline observed across all 6 runs, but it doesn't create a point separation.

---

## Discovery 4: Exact-Three-Options-007 Target Runs Are Strong but Baselines Are Missing

The 3 target runs all produced structurally compliant output (exactly 3 options, each with strengths/weaknesses, single recommendation). Scores: 12, 12, 11.

The 11/12 run (target run-3) met the exact minimum for strengths/weaknesses (1 each per option) where runs 1-2 provided 3-4 strengths and 2-3 weaknesses per option. This is technically compliant but provides less decision-making information.

**The problem:** No baselines were executed for this scenario. Without baselines, we cannot determine whether the injected discipline skill (`BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0`) actually caused the structural compliance, or whether the model naturally produces 3 options for this prompt. Prior stress tests (Phase 14, Discussion Map Phase 12-13) suggest the model does NOT naturally constrain to exactly 3 options — but this specific prompt was not tested in those stress tests.

---

## Discovery 5: Spec-004 Attractor Pattern

5 of 6 executed spec-004 runs converged on the same target module (`error-messages.ts`) for their proposed scenario, despite being independently forked runs. This suggests strong attractor patterns in the scenario task:

| Run | Target module | Task framing |
|---|---|---|
| Baseline run-1 | `error-messages.ts` | Add new function |
| Baseline run-2 | `error-messages.ts` | Add `formatLoadError` |
| Baseline run-3 | `error-messages.ts` | Add `formatLoadError` |
| Placebo | `error-messages.ts` | Fix existing function (debugging) |
| Proxy gaming | `error-messages.ts` | Add `formatLoadError` |
| Harmful brevity | MCP server (new tool) | Add `list_categories` |

The harmful brevity run was the only one to break the attractor — it targeted the MCP server instead. Whether this is because the brevity constraint caused less thorough exploration (and thus a different "first plausible" choice) or random variance is unclear with N=1.

The placebo run is notable for being the only run to frame the task as `task_type: debugging` (fix existing function) rather than `code-change` (add new function). This novel framing adds scenario diversity but is qualitatively different.

---

## Interpretation: What This All Means

### For the benchmark verdict

**The overall verdict must be `INCONCLUSIVE`** — not because the architecture is broken, but because there isn't enough executed data:
- 57% empty stubs
- 2 entire scenarios never executed
- Only 1 scenario allows baseline-vs-target delta computation, and it shows no delta

### For the measurement architecture

The news is cautiously positive:
1. **Controls work as expected.** Harmful degrades (-5), proxy gaming slightly degrades (-1), placebo doesn't degrade (0). This is exactly the control profile described in the framework (Section 4.2).
2. **The rubric discriminates.** The 0-12 scale separates genuinely degraded output (7) from strong output (12). It can detect quality differences.
3. **But the rubric has a ceiling.** When outputs are all high-quality (reference-008), the 0-2 per-dimension granularity can't separate them. A 0-4 scale would help.

### For next steps

To complete the benchmark:
1. **Execute all empty-stub runs.** report-005 (all 7), controls-006 (all 7), exact-three-options-007 baselines (3), spec-004 targets (already marked "none" per suite — these may be intentionally empty).
2. **Re-score with finer granularity.** Consider 0-4 per dimension for reference-008 and other high-ceiling scenarios.
3. **Expand controls.** The spec-004 control data is the strongest signal in the entire benchmark. Running controls on more scenarios would strengthen the verdict.
4. **Address the attractor pattern.** Consider whether spec-004's open-ended task is too narrowly funneling (5/6 runs converge on same module), reducing the sensitivity of baseline-vs-target comparisons.

---

## Score Summary Table

### Executed runs only

| File | Scenario | Score | Key observation |
|---|---|---:|---|
| `...spec-004__baseline__run-1.md` | spec-004 | 12 | All fields, 5 criteria, 6 failure modes, identified gap |
| `...spec-004__baseline__run-2.md` | spec-004 | 12 | 6 criteria (most), named function + param, wrote to disk |
| `...spec-004__baseline__run-3.md` | spec-004 | 12 | Exact output format, ran oracle commands, broadest exploration |
| `...spec-004__placebo__run-1.md` | spec-004 | 12 | Novel debugging framing, creative deficiency identification |
| `...spec-004__proxy_gaming__run-1.md` | spec-004 | 11 | Broader scope constraint, assertion-only self-check |
| `...spec-004__harmful_brevity_60w__run-1.md` | spec-004 | 7 | Fewer criteria, non-standard field, ID collision, less precise |
| `...exact-three-options-007__target__run-1.md` | exact-three-options-007 | 12 | 3 options, 3-4/2-3 strengths/weaknesses, rec: SQLite FTS5 |
| `...exact-three-options-007__target__run-2.md` | exact-three-options-007 | 12 | 3 options, novel Orama entrant, rec: Orama |
| `...exact-three-options-007__target__run-3.md` | exact-three-options-007 | 11 | 3 options, minimum 1/1 strengths/weaknesses, rec: SQLite FTS5 |
| `...reference-008__baseline__run-1.md` | reference-008 | 12 | Correct, 9 tools, 6 files cited, cross-verified consistency |
| `...reference-008__baseline__run-2.md` | reference-008 | 12 | Correct, quoted source text, primary vs reference distinction |
| `...reference-008__baseline__run-3.md` | reference-008 | 12 | Correct, Grep-first strategy, three-source triangulation |
| `...reference-008__target__run-1.md` | reference-008 | 12 | Correct, quoted authority self-declaration, clear hierarchy |
| `...reference-008__target__run-2.md` | reference-008 | 12 | Correct, quoted authority, absolute paths, supporting evidence |
| `...reference-008__target__run-3.md` | reference-008 | 12 | Correct, explicit "Inference" label (unique), deepest citation discipline |

### Distribution

| Score | Count | % of executed |
|---:|---:|---:|
| 12 | 12 | 80% |
| 11 | 2 | 13% |
| 7 | 1 | 7% |

---

## Relationship to Prior Discussion

This session extends the discussion map timeline:

| Phase | Session | Topic |
|---|---|---|
| 1-7 | Original discussion | Problem identification through framework spec |
| 8-9 | Continuation | Gap analysis and spike design |
| 10 | Continuation | Spike execution (all 6 experiments pass) |
| 11 | 2026-02-04 Session 2 | Implementation begin (false start, correction) |
| 12-13 | 2026-02-04 Session 3 | End-to-end validation + edge case testing |
| 14 | 2026-02-05 | Architecture stress testing (A/B/C categories + Phase 1.2) |
| 15 | 2026-02-06 | Benchmark v0 execution (run records produced) |
| **16** | **2026-02-07 (this session)** | **Blinded scoring of rubric scenarios** |

### Key insight additions to the discussion map

| # | Insight | Source |
|---|---|---|
| 37 | Controls produce expected signals: placebo=0, proxy gaming=-1, harmful=-5 | Blinded scoring |
| 38 | The 0-2 rubric granularity has a ceiling effect — all high-quality outputs score 12/12 with real differences invisible | Reference-008 scoring |
| 39 | 57% empty stubs means the benchmark cannot produce a verdict yet — INCONCLUSIVE for insufficient data, not architectural failure | Coverage analysis |
| 40 | Open-ended tasks create attractor patterns (5/6 runs converge on same module) that reduce baseline-vs-target sensitivity | Spec-004 analysis |
| 41 | Harmful brevity control was overridden by structured-output task demands (couldn't compress YAML to 60 words) but still degraded thoroughness | Harmful brevity analysis |
| 42 | Empty stubs reveal the benchmark run was incomplete — execution gaps, not scoring gaps, are the bottleneck | Cross-scenario analysis |

---

## Open Items (Updated)

| Item | Priority | Status |
|---|---|---|
| Execute report-005 runs (all 7) | **High** | Not started |
| Execute controls-006 runs (all 7) | **High** | Not started |
| Execute exact-three-options-007 baseline runs (3) | **High** | Not started |
| Re-score reference-008 with finer granularity (0-4) | Medium | Not started |
| Address spec-004 attractor pattern | Low | Identified — may need prompt redesign |
| Compile final benchmark report | High | Blocked on execution gaps |
| Update DISCUSSION-MAP with Phase 16 | Low | This document serves as record |

---

*Last updated: 2026-02-07*
*Session duration: Single evaluation session*
*Primary artifact: `docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`*
