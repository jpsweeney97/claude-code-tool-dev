# Benchmark v0 Report — Run 2026-02-06_benchmark-v0_initial

**Run ID:** 2026-02-06_benchmark-v0_initial
**Framework:** `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
**Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
**Verdict:** TBD (anchor scenarios complete; rubric scenarios not yet executed)

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

Run record stubs have been scaffolded for all 5 rubric scenarios, but **no rubric runs have been executed**. All rubric run-record files contain only placeholder templates (empty Output, Tool Trace, and Oracle Results sections).

| scenario_id | Planned (per suite matrix) | Stubs Scaffolded | Runs Executed | Status |
|---|---|--:|--:|---|
| v0-rubric-scenario-spec-004 | baseline×3, placebo×1, harmful_brevity×1, proxy_gaming×1 | 9 (incl. 3 target stubs marked "no TARGET per suite") | 0 | **not started** |
| v0-rubric-report-005 | baseline×3, target×3, proxy_gaming×1 | 7 | 0 | **not started** |
| v0-rubric-controls-006 | baseline×3, harmful_brevity×1 | 7 (incl. 3 target stubs marked "no TARGET per suite") | 0 | **not started** |
| v0-rubric-exact-three-options-007 | baseline×3, target×3 | 6 | 0 | **not started** |
| v0-rubric-reference-008 | baseline×3, target×3 | 6 | 0 | **not started** |

**Executed runs total: 22 (anchor only). Rubric runs: 0 executed, 35 stubs scaffolded.**

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
- target run-3: `'creating SKILL.md file directory'`

These are essentially the same query with minor token variation. The convergence is stronger than frontmatter-002's (which at least varied the field name).

#### Confounders

**Baseline run-3 anti-convergence steering** (recorded in `…golden-queries-003__baseline__run-3.md`):
- After baseline runs 1–2 converged on identical category (`skills`) with near-identical queries, the orchestrator added "Do not target the 'skills' category" to run-3's prompt.
- This produced a `troubleshooting` selection, breaking convergence and providing variance data.
- The run is tagged with `prompt_deviation` confounder. It is valid for task execution quality but **not** for inferring "what baseline would independently choose." Strictly, the unsteered baseline distribution is 2/2 `skills` (100%), not 2/3 `skills` + 1/3 `troubleshooting`.

**No other confounders recorded** across the 6 runs. No web usage detected in any run (consistent with `no_web` expectation per `docs/benchmarks/target-skills_v0.1.0.md`).

#### Ceiling Effect

This is the clearest ceiling effect in the benchmark. Every run across both conditions:
- Added exactly 1 line (1 array entry)
- Changed 0 production code files
- Changed 0 mock corpus content
- Passed all 254 tests

The `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill's guidance ("identify the smallest change," "keep the diff minimal") describes exactly what the task already requires. There is no opportunity for the skill to produce a measurably different outcome.

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
| rubric_blinded | 5 | 0 (stubs only) | **not executed** | **not executed** |

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

| Control | Expected Behavior | Observed | Assessment |
|---|---|---|---|
| placebo | Neutral delta (no effect) | PASS, indistinguishable from baseline | Confirmed (1 scenario) |
| irrelevant | Neutral delta (ignored or no effect) | PASS, skill non-compliance (formatting instructions overridden by task) | Confirmed via different mechanism than expected (1 scenario) |
| harmful_no_tools | Negative delta (task degradation) | No-op, task_completion FAIL | **Confirmed — strongest signal** (2 scenarios) |

**Did any control "win" unexpectedly?** No. Placebo and irrelevant did not outperform baseline. harmful_no_tools performed strictly worse. No expansion to N=3 required for controls.

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

## Final Verdict + Justification

**Verdict for anchor scenarios: INCONCLUSIVE (pending rubric scenarios)**

**What the anchor data supports:**
1. **Architecture validity (mechanical):** YES — 22/22 runs executed without infrastructure failure. Skill injection, oracle execution, and cleanup all work reliably.
2. **Degradation detection:** YES — harmful_no_tools control produces reliable, detectable task failures (2/2).
3. **Improvement detection (target vs baseline):** **NOT DEMONSTRATED** — zero delta across all 3 anchor scenarios, 9 baseline runs, 9 target runs. The binary oracle + task completion oracle cannot distinguish target from baseline.

**Why INCONCLUSIVE rather than NO:**
- The binary oracle's inability to detect target improvement is a known limitation of anchor scenarios with ceiling effects, not necessarily a failure of the architecture.
- Rubric scenarios (5 planned, 0 executed) are designed to test the architecture's ability to detect subtler quality differences using blinded evaluation — precisely the case where binary oracles plateau.
- The framework's decision threshold (Section 9.3 of `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`) requires target improvement on ≥70% of scenarios — this cannot be assessed until rubric runs are executed and scored.

**Blocking items for final verdict:**
1. Execute all 5 rubric scenarios (run record stubs are scaffolded; no runs completed yet)
2. Blinded evaluation and rubric scoring for all rubric runs
3. Rubric scores added to `scores.md`
4. Re-evaluation against Section 9.3 thresholds with full data
