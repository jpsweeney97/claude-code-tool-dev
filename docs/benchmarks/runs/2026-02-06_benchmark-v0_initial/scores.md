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

<!-- Rubric scenario scores pending blinded evaluation -->

---

## Aggregates

### By oracle_type

| oracle_type | Scenarios | Baseline PASS Rate | Target PASS Rate | Delta |
|---|--:|---|---|---|
| objective_tests | 3 (anchor) | 9/9 (100%) | 9/9 (100%) | 0 |
| rubric_blinded | 5 (rubric) | — | — | **not executed** (run record stubs scaffolded; no runs completed) |

**Note:** "PASS" for anchor scenarios means oracle PASS AND task_completion PASS. With this composite definition, baseline is 9/9 and target is 9/9 across all three anchor scenarios.

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

**Key control findings:**
1. **harmful_no_tools is reliably effective** — 2/2 anchor scenarios show full compliance with tool prohibition, producing no-op outcomes. This is the strongest discriminative signal in the anchor set.
2. **Binary oracle alone misses harmful_no_tools failures** — no-op passes tests vacuously. The composite oracle (tests PASS AND non-empty diff) correctly catches it.
3. **Placebo and irrelevant show expected neutral delta** — no artificial inflation of target scores. Measurement is not contaminated by these controls.
