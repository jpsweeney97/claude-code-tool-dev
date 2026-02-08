# Benchmark v0 Report — Run 2026-02-06_benchmark-v0_initial

**Run ID:** 2026-02-06_benchmark-v0_initial
**Framework:** `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
**Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
**Verdict:** INCONCLUSIVE — architecture validated; improvement detected in 1/6 baseline-target scenarios (below 70% threshold). All 51 runs executed; blinded scoring complete.

---

## Scenario Roster + Conditions Run

### Anchor Scenarios (objective_tests oracle)

| scenario_id | baseline | target | placebo | irrelevant | harmful_no_tools | Total Runs | Status |
|---|--:|--:|--:|--:|--:|--:|---|
| v0-anchor-vitest-001 | 3 | 3 | 1 | 1 | 1 | 9 | COMPLETE |
| v0-anchor-frontmatter-002 | 3 | 3 | — | — | 1 | 7 | COMPLETE |
| v0-anchor-golden-queries-003 | 3 | 3 | — | — | — | 6 | COMPLETE |
| **Anchor total** | **9** | **9** | **1** | **1** | **2** | **22** | |

### Rubric Scenarios (rubric_blinded oracle)

Rubric scenario scoring uses a separate blinded evaluator artifact:
`docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`.

| scenario_id | Conditions Run | Runs Executed | Status |
|---|---|--:|---|
| v0-rubric-scenario-spec-004 | baseline×3, placebo×1, harmful_brevity×1, proxy_gaming×1 | 6 | COMPLETE |
| v0-rubric-report-005 | baseline×3, target×3, proxy_gaming×1 | 7 | COMPLETE |
| v0-rubric-controls-006 | baseline×3, harmful_brevity×1 | 4 | COMPLETE |
| v0-rubric-exact-three-options-007 | baseline×3, target×3 | 6 | COMPLETE |
| v0-rubric-reference-008 | baseline×3, target×3 | 6 | COMPLETE |

**Executed runs total:** 22 anchor + 29 rubric = **51**.

**Rubric scoring provenance:** All 29 rubric candidates were scored by a blinded evaluator (scoring date: 2026-02-08) using condition-free hex IDs. See `blinded_scores.md` for raw scores and `blinded_eval/blinded_eval_mapping_private.md` for the unblinding key.

---

## Per-Scenario Deltas

### v0-anchor-vitest-001 — Summary

**Scenario:** Add or strengthen one test assertion in `packages/mcp-servers/claude-code-docs/tests/`.
**Oracle:** `npm test` + `npm run build` (binary pass/fail).
**Runs completed:** 9/9 (3 baseline, 3 target, 1 placebo, 1 irrelevant, 1 harmful_no_tools).

**Headline finding:** The binary oracle has zero discriminative power for this scenario. All 9 runs return PASS/PASS, including the harmful_no_tools run that made no code changes at all.

**Convergence attractor.** Four of 9 runs (baseline-1, target-3, placebo-1, irrelevant-1) independently produced the identical 1-line diff: `expect(message).toContain('unknown')` in `error-messages.test.ts > formatSearchError > handles non-Error values`. This suggests the scenario's "strengthen one assertion" prompt has a dominant fixed point — the single most obvious weak assertion in the test suite — that the model gravitates toward regardless of injected instructions. Remaining runs chose different files (baseline-2 → `bm25.test.ts`, baseline-3 → `frontmatter.test.ts`, target-1 → `frontmatter.test.ts`, target-2 → `fence-tracker.test.ts`).

**Irrelevant control: skill non-compliance.** The `CONTROL_IRRELEVANT_FOR_CODE_v0.1.0` body instructed PRD formatting with no code. The runner completely ignored this and produced a normal code change. For anchor scenarios with concrete, tool-backed tasks, irrelevant formatting instructions are simply overridden. The control's neutral-delta expectation holds, but via non-compliance rather than degradation.

**Harmful_no_tools: full skill compliance, task failure.** The `CONTROL_HARMFUL_NO_TOOLS_v0.1.0` body ("do not use any tools") was fully obeyed. The runner used zero tools, read zero files, and made zero code changes. This is the only condition across 9 runs that produced a qualitatively different outcome. The control's expected profile ("lower pass rate") is confirmed — but the binary oracle misses it because a no-op trivially passes tests/build.

**Oracle sensitivity gap.** The binary oracle cannot distinguish "made a change and tests pass" from "made no change and tests trivially pass." For anchor scenarios, a **task-completion oracle** (non-empty `git diff` after runner completes) is required to detect no-op failures. With task completion factored in, the harmful_no_tools condition correctly scores as FAIL.

**What this scenario proved:**
- The measurement architecture (dynamic skill injection via `context: fork` + static assessment-runner) works mechanically — all 9 runs executed without infrastructure failures.
- The harmful_no_tools control successfully induced behavioral differentiation, confirming the architecture can detect when an injected skill degrades outcomes.
- The binary oracle is insufficient alone for anchor scenarios; a composite oracle (tests pass AND non-empty diff) is needed.

**What this scenario did NOT prove:**
- Whether the target skill (`BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0`) measurably improves outcomes — the binary oracle shows no delta and the convergence attractor masks qualitative differences.
- Whether the measurement architecture can detect subtler effects (e.g., skill that improves reasoning quality without changing the pass/fail outcome). This requires rubric scenarios.

---

### v0-anchor-frontmatter-002 — Summary

**Scenario:** Add or strengthen one test assertion in `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.
**Oracle:** `npm -w packages/mcp-servers/claude-code-docs test` (binary pass/fail).
**Runs completed:** 7/7 (3 baseline, 3 target, 1 harmful_no_tools).

**Headline finding:** Binary oracle delta between baseline and target is zero — all 6 runs produce PASS and non-empty diffs. harmful_no_tools again produces a no-op with task_completion FAIL, consistent with vitest-001. The scenario has richer surface area than vitest-001 (more code paths to target), yielding weaker convergence but the same ceiling effect.

#### Convergence Analysis

**Two convergence attractors were observed:**

1. **`tags` invalid type branch** (primary): baseline run-1 and target run-1 both found the same untested code path — the `else if (yaml.tags !== undefined)` branch handling tags that are neither string nor array. Baseline used `tags: 123` (number), target used `tags: true` (boolean). The tests are structurally identical despite different invalid-type values.

2. **`parseStringArrayField` all-invalid items** (secondary): 4 of 6 baseline+target runs targeted this helper function's `result.length > 0 ? result : undefined` branch. Baseline runs 2–3 tested via `related_to`; target runs 2–3 tested via `requires`. Same function, different fields — a notable cross-condition divergence that doesn't appear in vitest-001 or golden-queries-003.

**Attractor strength is weaker than vitest-001.** Where vitest-001 had 4/9 runs produce _identical_ diffs, frontmatter-002 runs converge on code paths but diverge on specific field names, assertion counts (2–4), and diff sizes (10–15 lines). The broader coverage surface of `frontmatter.test.ts` gives the model more degrees of freedom.

#### Ceiling Effect

The `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill instructs "smallest change" and "keep diff minimal." Both baseline and target already produce single-test diffs in the 10–15 line range. The scenario's inherent constraint (add/strengthen one test) limits output to one test case regardless of condition. No measurable delta on diff size, pass rate, or task completion.

#### Control Effectiveness

**harmful_no_tools** (`…frontmatter-002__harmful_no_tools__run-1.md`):
- Full compliance — zero tools, zero code changes, zero file reads.
- Runner attempted a best-guess test as inline text but guessed the wrong return shape for `parseFrontmatter` (`frontmatter.data.title` vs actual `{ frontmatter, warnings }`). This demonstrates tool access is structurally necessary for correctness — the model cannot produce valid test code without reading source.
- Task completion: FAIL. Oracle: PASS (vacuous, 253 tests — no test added).
- Confirms harmful_no_tools reliability: 2/2 anchor scenarios show identical pattern (full compliance → no-op → task failure).

---

### v0-anchor-golden-queries-003 — Summary

**Scenario:** Add one golden query assertion to `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`.
**Oracle:** `npm -w packages/mcp-servers/claude-code-docs test` (binary pass/fail).
**Runs completed:** 6/6 (3 baseline, 3 target). No controls scheduled for this scenario.

**Headline finding:** Binary oracle delta between baseline and target is zero — all 6 runs produce PASS with exactly 1-line diffs. This scenario has the strongest ceiling effect of the three anchors: the task inherently requires exactly one array entry addition, making the `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill's "keep diff minimal" instruction fully redundant.

#### Convergence Analysis

**Three category clusters emerged across 6 runs:**

| Category → Subsection | Runs | Notes |
|---|---|---|
| `skills` → "Creating skills" | baseline run-1, baseline run-2, target run-3 (3/6) | Dominant attractor; near-identical query strings |
| `troubleshooting` → "Connection troubleshooting" | baseline run-3, target run-1 (2/6) | Secondary attractor; baseline run-3 was steered away from skills |
| `security` → "Permission boundaries" | target run-2 (1/6) | Only unique selection |

**Universal "second subsection" strategy:** All 6 runs targeted the uncovered second subsection of an already-covered category. No run targeted a category with only 1 subsection in the mock corpus (e.g., MCP "Building MCP servers", agents "Subagent isolation"). This suggests the model's coverage-gap analysis consistently identifies the "closest uncovered neighbor" rather than exploring further afield.

**Query string near-duplication within the `skills` attractor:**
- baseline run-1: `'creating SKILL.md .claude/skills directory'`
- baseline run-2: `'creating SKILL.md in skills directory'`

---

## Rubric Scenarios — Blinded Evaluation Summary (Unblinded)

Scores from blinded evaluator artifact (`blinded_scores.md`, scoring date 2026-02-08), unblinded using `blinded_eval/blinded_eval_mapping_private.md`. Full per-run scores in `scores.md`.

### v0-rubric-scenario-spec-004

- **29 candidates scored across 5 scenarios.** All 6 runs executed and scored.
- Baseline: 12/12 × 3 (avg 12.0). Controls: placebo 12/12, proxy_gaming 12/12, harmful_brevity 7/12.
- **harmful_brevity degradation:** Missing fields, fewer criteria, non-standard field names, broader task scope. Brevity constraint suppressed rationale.
- No target condition per suite matrix; no baseline-target delta available.

### v0-rubric-report-005

- All 7 runs executed and scored. Baseline: 12/12 × 3. Target: 12/12 × 3. proxy_gaming: 8/12.
- **Baseline-target delta: 0.** Ceiling effect — both conditions produce structurally complete templates.
- **proxy_gaming degradation (8/12):** Advisory rather than structural enforcement of evidence/interpretation separation, confounder tracking, and blinding prompts.

### v0-rubric-controls-006

- All 4 runs executed and scored. Baseline: 12/12 × 3. harmful_brevity: 10/12.
- **harmful_brevity degradation (10/12):** Weaker irrelevance category (formatting vs domain-orthogonal) and reduced definitional clarity.
- No target condition per suite matrix.

### v0-rubric-exact-three-options-007

- All 6 runs executed and scored. Baseline: 8/12 × 3 (avg 8.0). Target: 12/12 × 3 (avg 12.0).
- **Baseline-target delta: +4.0 — the only non-zero delta in the benchmark.**
- All 3 baseline runs produced 4 options (failing "exactly 3" count discipline); all 3 target runs produced exactly 3. The target skill's explicit count instruction was perfectly effective.
- The evaluator noted this as "the most binary signal across all scenarios."

### v0-rubric-reference-008

- All 6 runs executed and scored. Baseline: 12/12 × 3. Target: 12/12 × 3.
- **Baseline-target delta: 0.** Ceiling effect — all criteria are binary-checkable and all candidates met every one.
- Qualitative differences exist (target run-3 showed strongest observation/inference discipline) but do not resolve at 0-2 granularity.

---

## Limitations / Confounders

- **Ceiling effects on 5 of 6 baseline-target scenarios:** Baseline and target both achieved maximum or near-maximum scores on all scenarios except exact-three-options-007. Only that scenario showed discriminative power, limiting the benchmark's ability to broadly assess target skill effectiveness.
- **Rubric granularity (0-2 scale):** The blinded evaluator noted qualitative differences among 12/12 candidates in reference-008 and report-005 that do not resolve at 0-2 granularity. A finer scale (0-3 or 0-4) would increase discrimination.
- **Scenario 008 environment confound:** The reference task asks about benchmark infrastructure while running inside benchmark infrastructure. The always-loaded execution environment can restate benchmark templates/structure, creating a derivative-source confound. The suite's citation policy mitigates this by treating canonical docs as the only evidentiary authority.
- **Convergence attractors in anchor scenarios:** All three anchor scenarios exhibit convergence attractors (dominant solutions the model gravitates toward regardless of condition), reducing discriminability between baseline and target.

---

## Key Findings (Anchor Scenarios)

### 1. The Measurement Architecture Works Mechanically

All 22 anchor runs executed without infrastructure failures. Dynamic skill injection via `context: fork` + static assessment-runner reliably delivers skill content to the runner, and cleanup restores clean state for subsequent runs. This validates the architecture from `docs/simulation-assessment-context-official.md`.

### 2. Binary Oracle + Task Completion Oracle Is Necessary But Not Sufficient

The binary test oracle (PASS/FAIL) cannot discriminate between baseline and target for these anchor scenarios — both achieve 100% PASS across all replicates. The task-completion oracle (`git diff` non-empty) adds value by catching harmful_no_tools no-ops, but still cannot detect quality differences between baseline and target.

For the benchmark's top-level question ("Does the architecture measure functional effectiveness?"), anchor scenarios with binary oracles can confirm:
- The architecture **can detect catastrophic degradation** (harmful_no_tools → task failure)
- The architecture **cannot detect subtle improvement** (target vs baseline → no measurable delta)

This is consistent with the framework's design intent — anchor scenarios provide a floor of validity, while rubric scenarios test discrimination power for subtler effects.

### 3. Convergence Attractors Limit Discriminability

All three anchor scenarios exhibit convergence attractors — dominant solutions that the model gravitates toward regardless of condition:

| Scenario | Strongest Attractor | Runs Converged | Strength |
|---|---|---|---|
| vitest-001 | `error-messages.test.ts` identical diff | 4/9 (44%) | Identical output |
| frontmatter-002 | `parseStringArrayField` all-invalid branch | 4/6 (67%) | Same code path, different fields |
| golden-queries-003 | `skills` → "Creating skills" | 3/6 (50%) | Near-identical query strings |

Convergence reduces the scenario's ability to detect behavioral differences between conditions. When both baseline and target produce the same change, any delta from the injected skill is invisible.

**Implication for scenario design:** Scenarios with narrow solution spaces (e.g., "add one assertion to a test file with one obvious gap") will exhibit strong convergence. More discriminative scenarios need broader solution spaces or constraints that create divergent optimal strategies between conditions.

### 4. harmful_no_tools Is the Strongest Discriminative Signal

Across the 2 anchor scenarios where it was tested (vitest-001 and frontmatter-002), harmful_no_tools produced 2/2 full compliance with tool prohibition, 2/2 no-op outcomes, and 2/2 task_completion FAIL verdicts. This is the clearest behavioral differentiation in the anchor set.

The harmful_no_tools control validates that:
- The runner reads and follows injected skill content (compliance)
- The composite oracle (tests + task completion) detects the degradation
- The architecture can measure the _absence_ of effective behavior

### 5. Placebo and Irrelevant Controls Show Expected Neutral Delta

Placebo (tested on vitest-001) was indistinguishable from baseline — expected. Irrelevant (tested on vitest-001) was also indistinguishable, but via non-compliance (runner ignored formatting instructions in favor of the concrete task). Neither control inflated scores, confirming measurement is not contaminated.

---

## Aggregates

### By oracle_type

| oracle_type | Scenarios | Runs Executed | Baseline-Target Delta | Controls Validated |
|---|--:|--:|---|---|
| objective_tests | 3 | 22 | 0 (all PASS) | harmful_no_tools 2/2 FAIL; placebo/irrelevant neutral |
| rubric_blinded | 5 | 29 | +4.0 on 007; 0 on 005, 008 | harmful_brevity degrades; proxy_gaming mixed; placebo neutral |

**Total runs:** 51 (22 anchor + 29 rubric). All planned runs complete.

### Baseline vs Target Deltas (all scenarios with both conditions)

| Scenario | Baseline | Target | Delta |
|---|---|---|--:|
| v0-anchor-vitest-001 | PASS (3/3) | PASS (3/3) | 0 |
| v0-anchor-frontmatter-002 | PASS (3/3) | PASS (3/3) | 0 |
| v0-anchor-golden-queries-003 | PASS (3/3) | PASS (3/3) | 0 |
| v0-rubric-report-005 | 12.0/12 | 12.0/12 | 0 |
| v0-rubric-exact-three-options-007 | 8.0/12 | 12.0/12 | **+4.0** |
| v0-rubric-reference-008 | 12.0/12 | 12.0/12 | 0 |

**Improvement rate:** 1/6 scenarios (16.7%). Below Section 9.3 threshold of ≥70%.

### By skill_type (anchor only)

| skill_type | TARGET Body | Scenarios | Delta |
|---|---|--:|---|
| technique | `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` | 3 | 0 |

### By task_type (anchor only)

| task_type | Scenarios | Delta |
|---|--:|---|
| code-change | 3 | 0 |

---

## Controls Outcomes

### Anchor Controls

| Control | Expected Behavior | Observed | Assessment |
|---|---|---|---|
| placebo | Neutral delta (no effect) | PASS, indistinguishable from baseline | Confirmed (1 scenario) |
| irrelevant | Neutral delta (ignored or no effect) | PASS, skill non-compliance (formatting instructions overridden by task) | Confirmed via different mechanism than expected (1 scenario) |
| harmful_no_tools | Negative delta (task degradation) | No-op, task_completion FAIL | **Confirmed — strongest signal** (2 scenarios) |

### Rubric Controls

| Control | Expected Behavior | Observed | Assessment |
|---|---|---|---|
| placebo | Neutral delta | 12/12 (spec-004) | Confirmed (1 scenario) |
| proxy_gaming | Process gaming, possible degradation | 12/12 (spec-004), 8/12 (report-005) | **Task-dependent**: no effect on constrained tasks, degradation on enforcement-heavy tasks |
| harmful_brevity_60w | Degradation from brevity constraint | 7/12 (spec-004), 10/12 (controls-006) | **Confirmed — consistent degradation** across both scenarios |

**Did any control "win" unexpectedly?** No. Placebo neutral across all contexts. harmful_no_tools (anchor) and harmful_brevity_60w (rubric) performed strictly worse. proxy_gaming shows task-dependent degradation — expected for a process-wrapper that pressures structural enforcement.

---

## Confounders Summary

| Confounder | Runs Affected | Impact | Mitigation |
|---|---|---|---|
| Anti-convergence steering (baseline run-3 of golden-queries-003) | 1 run | Category choice constrained; not a free baseline | Tagged as `prompt_deviation` in run record; valid for task quality, not for "free baseline" inference |
| Naming bias | 0 runs | All skill files used neutral naming | Verified in every run record |
| Tool confounders (web usage) | 0 runs | All runs matched `no_web` expectation | No web search detected in any anchor run |
| Cross-run contamination | 0 runs | Every run verified clean start (empty diff) and clean cleanup | Git diff checks recorded in every run record |

**Assessment:** Confounder load is minimal. The one recorded confounder (anti-convergence steering) is transparent, documented, and affects inference scope (not validity) for a single run.

---

## Rubric Scoring Status

All 5 rubric scenarios are **COMPLETE** — 29 runs executed and scored by blinded evaluator.

### Key Rubric Findings

1. **exact-three-options-007 is the only scenario with discriminative power.** Baseline avg 8.0/12 vs target avg 12.0/12 (+4.0 delta). The target skill's "exactly 3 options" instruction was perfectly effective — 3/3 compliance vs 0/3 baseline compliance on count discipline.

2. **Ceiling effects dominate.** 5 of 6 baseline-target comparisons show zero delta. Baseline already achieves maximum rubric scores on 4 of 5 rubric scenarios. The 0-2 rubric granularity and well-defined task constraints leave no room for the target skill to demonstrate improvement.

3. **Controls validate the architecture's sensitivity.** harmful_brevity_60w degrades scores in both scenarios tested (7/12 and 10/12 vs baseline 12.0). proxy_gaming degrades on enforcement-heavy tasks (8/12 on report-005). The architecture detects degradation reliably.

4. **Convergence attractors in spec-004.** 5 of 6 candidates converged on `error-messages.ts` module, reducing between-candidate variance and potentially masking condition effects.

---

## Final Verdict + Justification

**Verdict: INCONCLUSIVE**

All 51 runs (22 anchor + 29 rubric) executed. Blinded evaluation scored all 29 rubric candidates. The data is complete.

**What the data supports:**
1. **Architecture validity (mechanical):** YES — 51/51 runs executed without infrastructure failure. Skill injection, oracle execution, blinded scoring, and cleanup all work reliably.
2. **Degradation detection:** YES — harmful_no_tools (anchor), harmful_brevity_60w (rubric), and proxy_gaming (rubric, task-dependent) all produce detectable score reductions.
3. **Improvement detection (target vs baseline):** **DEMONSTRATED ON 1 OF 6 SCENARIOS** — exact-three-options-007 shows +4.0 delta (8.0 → 12.0). The remaining 5 scenarios show zero delta due to ceiling effects.

**Why INCONCLUSIVE rather than YES:**
- The Section 9.3 decision threshold requires target improvement on ≥70% of scenarios. Only 1/6 (16.7%) shows improvement — well below threshold.
- The single positive signal (007) is strong and clean (3/3 baseline fail, 3/3 target pass on count discipline), but one scenario is insufficient for a YES verdict.

**Why INCONCLUSIVE rather than NO:**
- The architecture demonstrably *can* detect improvement when the scenario has discriminative power (007 proves this).
- The 5 zero-delta scenarios are explained by ceiling effects and rubric granularity, not architecture failure.
- The benchmark's scenario design (narrow tasks, coarse rubrics) is the limiting factor, not the measurement architecture.

**Recommendations for v1:**
1. Increase rubric granularity to 0-3 or 0-4 scale to resolve qualitative differences among high-performing candidates.
2. Design scenarios with broader solution spaces to reduce ceiling effects and convergence attractors.
3. Add more scenarios where the target skill addresses a specific, measurable behavioral gap (as 007 did with count discipline).
4. Consider scenario-specific rubric dimensions tuned to the target skill's intended behavioral change.
