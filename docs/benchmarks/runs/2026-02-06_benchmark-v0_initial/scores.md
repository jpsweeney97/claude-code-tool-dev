# Benchmark v0 Scores — Run 2026-02-06_benchmark-v0_initial

**Run ID:** 2026-02-06_benchmark-v0_initial

## Anchor Scenarios (Objective Oracle)

### v0-anchor-vitest-001 — Summary

| Condition | N | Code Change | Oracle (test/build) | Task Completion |
|-----------|--:|-------------|---------------------|-----------------|
| baseline | 3 | 3/3 Yes | 3/3 PASS/PASS | 3/3 PASS |
| target | 3 | 3/3 Yes | 3/3 PASS/PASS | 3/3 PASS |
| placebo | 1 | 1/1 Yes | 1/1 PASS/PASS | 1/1 PASS |
| irrelevant | 1 | 1/1 Yes | 1/1 PASS/PASS | 1/1 PASS |
| harmful_no_tools | 1 | **0/1 No** | 1/1 PASS/PASS (vacuous) | **1/1 FAIL** |

**Binary oracle delta (baseline vs target):** 0. Both conditions PASS/PASS on all replicates. The binary oracle cannot differentiate.

**Task completion delta:** 0 between baseline/target (both complete all runs). harmful_no_tools is the only condition with task failure.

**Convergence attractor:** 4 of 9 runs (baseline-1, target-3, placebo-1, irrelevant-1) produced the identical diff: `expect(message).toContain('unknown')` added to `error-messages.test.ts > formatSearchError > handles non-Error values`. This is a dominant fixed point in the test suite for the "strengthen one assertion" prompt.

**Control findings:**
- **Placebo:** Indistinguishable from baseline (expected).
- **Irrelevant:** Skill completely ignored; runner produced normal code change. PRD formatting instruction overridden by concrete scenario task.
- **Harmful_no_tools:** Full skill compliance; zero tools used; zero code changes. Task not completed. Binary oracle returns PASS/PASS vacuously (no-op can't break tests). Exposes oracle sensitivity gap.

**Oracle limitation:** The binary oracle (tests pass / build passes) is necessary but not sufficient for anchor scenarios. A no-op trivially satisfies it. Recommend supplementing with a task-completion oracle (`git diff` non-empty).

---

### v0-anchor-frontmatter-002 — Summary

| Condition | N | Code Change | Oracle (tests) | Task Completion |
|-----------|--:|-------------|----------------|-----------------|
| baseline | 3 | 3/3 Yes | 3/3 PASS (254 tests) | 3/3 PASS |
| target | 3 | 3/3 Yes | 3/3 PASS (254 tests) | 3/3 PASS |
| harmful_no_tools | 1 | **0/1 No** | 1/1 PASS (253, vacuous) | **1/1 FAIL** |

**Binary oracle delta (baseline vs target):** 0. Both conditions PASS on all replicates. Binary oracle cannot differentiate.

**Task completion delta:** 0 between baseline/target. harmful_no_tools is the only condition with task failure (no-op; runner fully complied with tool prohibition).

#### Per-Run Detail

| Run Record | Condition | Code Path Targeted | Field | Lines | Assertions |
|---|---|---|---|--:|--:|
| `…frontmatter-002__baseline__run-1.md` | baseline | `tags` invalid type branch (L110–115) | tags | 10 | 2 |
| `…frontmatter-002__baseline__run-2.md` | baseline | `parseStringArrayField` empty-result (L72) | related_to | 11 | 2 |
| `…frontmatter-002__baseline__run-3.md` | baseline | `parseStringArrayField` empty-result (L72) | related_to | 13 | 3 |
| `…frontmatter-002__target__run-1.md` | target | `tags` invalid type branch (L110–115) | tags | 10 | 2 |
| `…frontmatter-002__target__run-2.md` | target | `parseStringArrayField` empty-result (L72) | requires | 15 | 4 |
| `…frontmatter-002__target__run-3.md` | target | `parseStringArrayField` empty-result (L72) | requires | 11 | 3 |
| `…frontmatter-002__harmful_no_tools__run-1.md` | harmful_no_tools | N/A (no-op) | N/A | 0 | 0 |

#### Convergence Attractors

**Primary attractor — `tags` invalid type branch:**
- baseline run-1 (`tags: 123` → number) and target run-1 (`tags: true` → boolean) both found the same untested code path.
- Structurally identical tests despite different invalid-type values.

**Secondary attractor — `parseStringArrayField` all-invalid items:**
- 4 of 6 baseline+target runs targeted this code path (baseline runs 2–3 via `related_to`; target runs 2–3 via `requires`).
- All test the `result.length > 0 ? result : undefined` branch at line 72 of `frontmatter.ts`.
- Cross-condition field divergence: baseline chose `related_to`, target chose `requires`. Same function, different field.

**Attractor strength:** Weaker than vitest-001 (which had 4/9 identical diffs). Frontmatter-002 runs converge on code paths but diverge on specific fields and assertion counts, yielding more surface-level variety.

#### Ceiling Effect & Discriminability

The `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill instructs "smallest change" and "keep diff minimal." Baseline runs already produce 10–13-line single-test diffs. Target runs produce 10–15-line single-test diffs. The scenario's inherent constraint (add/strengthen one test) limits output to a single test case regardless of condition. The skill's guidance aligns with default behavior — no measurable delta on diff size or pass rate.

#### Control Effectiveness

**harmful_no_tools (run record: `…frontmatter-002__harmful_no_tools__run-1.md`):**
- Full compliance with control body — zero tools used, zero code changes.
- Runner attempted a best-guess test in text output but guessed wrong API shape (`frontmatter.data.title` vs actual `{ frontmatter, warnings }` return), demonstrating tool access is necessary for correctness.
- Task completion: FAIL. Oracle: PASS (vacuous).
- Consistent with vitest-001 harmful_no_tools result — confirms control reliability across anchor scenarios.

---

### v0-anchor-golden-queries-003 — Summary

| Condition | N | Code Change | Oracle (tests) | Task Completion |
|-----------|--:|-------------|----------------|-----------------|
| baseline | 3 | 3/3 Yes | 3/3 PASS (254 tests) | 3/3 PASS |
| target | 3 | 3/3 Yes | 3/3 PASS (254 tests) | 3/3 PASS |

**Binary oracle delta (baseline vs target):** 0. Both conditions PASS on all replicates.

**Task completion delta:** 0. All 6 runs produced exactly 1-line diffs.

**No controls scheduled** for this scenario (per suite matrix in `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`).

#### Per-Run Detail

| Run Record | Condition | Query Added | Category | Subsection |
|---|---|---|---|---|
| `…golden-queries-003__baseline__run-1.md` | baseline | `'creating SKILL.md .claude/skills directory'` | skills | Creating skills |
| `…golden-queries-003__baseline__run-2.md` | baseline | `'creating SKILL.md in skills directory'` | skills | Creating skills |
| `…golden-queries-003__baseline__run-3.md` | baseline | `'connection errors network firewall proxy'` | troubleshooting | Connection troubleshooting |
| `…golden-queries-003__target__run-1.md` | target | `'connection errors network proxy'` | troubleshooting | Connection troubleshooting |
| `…golden-queries-003__target__run-2.md` | target | `'permission boundaries access control'` | security | Permission boundaries |
| `…golden-queries-003__target__run-3.md` | target | `'creating SKILL.md file directory'` | skills | Creating skills |

#### Convergence Attractors

**Dominant attractor — `skills` → "Creating skills" (3/6 runs):**
- baseline run-1, baseline run-2, target run-3
- Query strings nearly identical across all three (minor token variations: `.claude/skills directory` vs `in skills directory` vs `file directory`)

**Secondary attractor — `troubleshooting` → "Connection troubleshooting" (2/6 runs):**
- baseline run-3 (anti-convergence steered away from skills), target run-1
- Query strings overlap: `'connection errors network firewall proxy'` vs `'connection errors network proxy'`

**Unique selection — `security` → "Permission boundaries" (1/6 runs):**
- target run-2 only

**Universal pattern:** All 6 runs targeted the uncovered second subsection of an already-covered category. No run targeted a category with only 1 mock corpus subsection (e.g., MCP "Building MCP servers", agents "Subagent isolation").

#### Confounders

**Baseline run-3 anti-convergence steering** (recorded in `…golden-queries-003__baseline__run-3.md`):
- Prompt included "Do not target the 'skills' category" constraint to break 2/2 convergence on skills.
- Run is tagged with `prompt_deviation` confounder and is not a fully free baseline.
- Still valid for task execution quality but not for "what would baseline independently choose?"

#### Ceiling Effect & Discriminability

This scenario has the strongest ceiling effect of the three anchor scenarios. The task ("add one golden query assertion") inherently requires exactly 1 array entry addition. All 6 runs produced exactly 1 line, 0 production changes, 0 mock corpus changes. The `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill's "keep diff minimal" instruction is fully redundant — the scenario constrains output to minimal changes regardless of condition.

---

## Rubric Scenarios (Blinded Rubric)

Rubric scenario scores come from a separate blinded evaluator artifact:
`docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`.

**Scoring method:** Candidates were assigned condition-free hex IDs and scored independently by a blinded evaluator with no access to condition labels or run-record filenames. Unblinding was performed after all scores were finalized, using `blinded_eval/blinded_eval_mapping_private.md`.

**Scoring date:** 2026-02-08. **Total rubric candidates scored:** 29 across 5 scenarios.

---

### v0-rubric-scenario-spec-004 — Blinded Rubric Scores

**Task:** Draft one new anchor benchmark scenario definition (YAML-in-Markdown) with objective oracle, clear success criteria, and confounder notes.

| Condition | Run | Score | Confidence |
|---|---|--:|---|
| baseline | run-1 | 12/12 | high |
| baseline | run-2 | 12/12 | high |
| baseline | run-3 | 12/12 | high |
| placebo | run-1 | 12/12 | high |
| proxy_gaming | run-1 | 12/12 | high |
| harmful_brevity_60w | run-1 | 7/12 | med |

**Baseline avg:** 12.0/12. **No target condition** per suite matrix.

**Control findings:**
- **harmful_brevity_60w (7/12):** Missing `difficulty` field, only 3 success criteria, non-standard `confounders` field name, ID collision, broader task scope. Brevity constraint suppressed design rationale and structural specificity.
- **proxy_gaming (12/12):** No degradation detected; delivered all required fields and checkable criteria despite process-wrapper pressure.
- **placebo (12/12):** Indistinguishable from baseline (expected neutral delta).

---

### v0-rubric-report-005 — Blinded Rubric Scores

**Task:** Produce a benchmark report template (Markdown) matching Section 9.2, with explicit prompts for confounder tracking and blinding integrity.

| Condition | Run | Score | Confidence |
|---|---|--:|---|
| baseline | run-1 | 12/12 | high |
| baseline | run-2 | 12/12 | high |
| baseline | run-3 | 12/12 | high |
| target | run-1 | 12/12 | high |
| target | run-2 | 12/12 | high |
| target | run-3 | 12/12 | high |
| proxy_gaming | run-1 | 8/12 | high |

**Baseline avg:** 12.0/12. **Target avg:** 12.0/12. **Delta:** 0.

**Ceiling effect:** All baseline and target runs achieved maximum scores. The rubric's 0-2 granularity cannot discriminate qualitative differences among 12/12 candidates.

**Control finding — proxy_gaming (8/12):** Advisory rather than structural evidence/interpretation separation (D2=1), narrative confounder prompts without per-scenario tables (D3=1), narrative blinding without structured workflows (D4=1), less specific prompt format (D6=1).

---

### v0-rubric-controls-006 — Blinded Rubric Scores

**Task:** Draft three categorized skill bodies (non-methodical, irrelevant for code-change, degrading but non-destructive), each short and clearly labeled.

| Condition | Run | Score | Confidence |
|---|---|--:|---|
| baseline | run-1 | 12/12 | high |
| baseline | run-2 | 12/12 | high |
| baseline | run-3 | 12/12 | high |
| harmful_brevity_60w | run-1 | 10/12 | med |

**Baseline avg:** 12.0/12. **No target condition** per suite matrix.

**Control finding — harmful_brevity_60w (10/12):** Weaker irrelevance (D4=1, formatting rules rather than domain-orthogonal approach) and reduced definitional clarity (D6=1, terse bodies lacking mechanism development). Brevity constraint suppressed meta-commentary and rationale.

---

### v0-rubric-exact-three-options-007 — Blinded Rubric Scores

**Task:** Provide exactly 3 options with trade-offs and a recommendation for a local Markdown search tool (TypeScript team, local-only, incremental updates).

| Condition | Run | Score | Confidence |
|---|---|--:|---|
| baseline | run-1 | 8/12 | high |
| baseline | run-2 | 8/12 | high |
| baseline | run-3 | 8/12 | high |
| target | run-1 | 12/12 | high |
| target | run-2 | 12/12 | high |
| target | run-3 | 12/12 | high |

**Baseline avg:** 8.0/12. **Target avg:** 12.0/12. **Delta: +4.0.**

**This is the only scenario with a non-zero baseline-target delta.** All 3 baseline runs produced 4 options (failing D1 exact count and D5 no extras), while all 3 target runs produced exactly 3 options. The evaluator noted: "Count discipline in 007 is the most binary signal across all scenarios."

---

### v0-rubric-reference-008 — Blinded Rubric Scores

**Task:** Answer two questions about repo content using only local files, citing exact file paths, distinguishing observation from inference.

| Condition | Run | Score | Confidence |
|---|---|--:|---|
| baseline | run-1 | 12/12 | high |
| baseline | run-2 | 12/12 | high |
| baseline | run-3 | 12/12 | high |
| target | run-1 | 12/12 | high |
| target | run-2 | 12/12 | high |
| target | run-3 | 12/12 | high |

**Baseline avg:** 12.0/12. **Target avg:** 12.0/12. **Delta:** 0.

**Ceiling effect:** All 6 candidates achieved 12/12. Qualitative differences exist (target run-3 showed uniquely strong inference labeling) but do not resolve at 0-2 granularity. The evaluator noted: "A finer scale (0-3 or 0-4) would help."

---

## Aggregates

### By oracle_type

| oracle_type | Scenarios | Runs Executed | Baseline-Target Delta | Controls Validated |
|---|--:|--:|---|---|
| objective_tests | 3 (anchor) | 22 | 0 (all PASS) | harmful_no_tools 2/2 FAIL; placebo/irrelevant neutral |
| rubric_blinded | 5 (rubric) | 29 | +4.0 on 007; 0 on 005, 008 (004, 006 have no target) | harmful_brevity degrades (7, 10); proxy_gaming mixed (12, 8); placebo neutral (12) |

**Total runs executed:** 51 (22 anchor + 29 rubric). All planned runs complete.

### Baseline vs Target Deltas (scenarios with both conditions)

| Scenario | oracle_type | Baseline Avg | Target Avg | Delta | Signal |
|---|---|--:|--:|--:|---|
| v0-anchor-vitest-001 | objective_tests | PASS (100%) | PASS (100%) | 0 | Ceiling effect |
| v0-anchor-frontmatter-002 | objective_tests | PASS (100%) | PASS (100%) | 0 | Ceiling effect |
| v0-anchor-golden-queries-003 | objective_tests | PASS (100%) | PASS (100%) | 0 | Ceiling effect |
| v0-rubric-report-005 | rubric_blinded | 12.0/12 | 12.0/12 | 0 | Ceiling effect |
| v0-rubric-exact-three-options-007 | rubric_blinded | 8.0/12 | 12.0/12 | **+4.0** | **Target improvement** |
| v0-rubric-reference-008 | rubric_blinded | 12.0/12 | 12.0/12 | 0 | Ceiling effect |

**Scenarios showing target improvement:** 1/6 (16.7%). Below Section 9.3 threshold of 70%.

### By skill_type (anchor scenarios only)

All three anchor scenarios use `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` (skill_type: `technique`).

| skill_type | Scenarios | Target Delta vs Baseline |
|---|--:|---|
| technique | 3 | 0 (no measurable difference on binary oracle + task completion) |

### By task_type (anchor scenarios only)

All three anchor scenarios are `task_type: code-change`.

| task_type | Scenarios | Target Delta vs Baseline |
|---|--:|---|
| code-change | 3 | 0 |

---

## Controls Summary

### Across Anchor Scenarios

| Control | Scenarios Tested | Code Change | Oracle | Task Completion | Interpretation |
|---|--:|---|---|---|---|
| placebo | 1 (vitest-001) | 1/1 Yes | PASS | PASS | Indistinguishable from baseline (expected) |
| irrelevant | 1 (vitest-001) | 1/1 Yes | PASS | PASS | Skill ignored; concrete task overrides formatting instructions |
| harmful_no_tools | 2 (vitest-001, frontmatter-002) | **0/2 No** | PASS (vacuous) | **2/2 FAIL** | Full compliance; reliable degradation; oracle sensitivity gap exposed |

### Across Rubric Scenarios

| Control | Scenarios Tested | Score | Interpretation |
|---|--:|---|---|
| placebo | 1 (spec-004) | 12/12 | Indistinguishable from baseline (expected neutral delta) |
| proxy_gaming | 2 (spec-004, report-005) | 12/12, 8/12 | Mixed: no effect on constrained task, degradation on enforcement-heavy task |
| harmful_brevity_60w | 2 (spec-004, controls-006) | 7/12, 10/12 | Consistent degradation; brevity suppresses rationale and structural specificity |

**Key control findings (rubric):**
1. **harmful_brevity_60w reliably degrades rubric scores** — 7/12 and 10/12 vs baseline avg of 12.0 in both scenarios.
2. **proxy_gaming shows task-dependent effects** — no degradation on well-constrained tasks (spec-004) but significant degradation on enforcement-heavy tasks (report-005, 8/12).
3. **placebo remains neutral** — 12/12, consistent with anchor findings.

**Key control findings:**
1. **harmful_no_tools is reliably effective** — 2/2 anchor scenarios show full compliance with tool prohibition, producing no-op outcomes. This is the strongest discriminative signal in the anchor set.
2. **Binary oracle alone misses harmful_no_tools failures** — no-op passes tests vacuously. The composite oracle (tests PASS AND non-empty diff) correctly catches it.
3. **Placebo and irrelevant show expected neutral delta** — no artificial inflation of target scores. Measurement is not contaminated by these controls.
