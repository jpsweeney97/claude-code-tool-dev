# Benchmark v0 Suite v0.1.0 (Run Matrix)

This file is the **execution spec** for Benchmark v0. It removes ambiguity by declaring:
- the exact scenario roster,
- the exact condition matrix (baseline/target/controls),
- replication defaults,
- oracle commands and scoring mode,
- and the minimum blinding requirements.

**Framework:** `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`  
**Target roster:** `docs/benchmarks/target-skills_v0.1.0.md`  
**Control bodies:** `docs/benchmarks/control-bodies_v0.1.0.md`  
**Synthetic BENCH bodies:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md`

**Last updated:** 2026-02-06

---

## Storage Layout (required)

- Scenario definitions: `docs/benchmarks/scenarios/`
- Run artifacts: `docs/benchmarks/runs/<run-id>/`

**Run id format:** `YYYY-MM-DD_benchmark-v0_<short-slug>`

---

## Benchmark v0 Scenario Roster (8 scenarios)

All scenario IDs below are defined inline in the framework (Section 3A.1). Copy them into `docs/benchmarks/scenarios/` before running.

### Anchor (objective_tests)

| scenario_id | oracle | commands |
|---|---|---|
| `v0-anchor-vitest-001` | objective_tests | `npm -w packages/mcp-servers/claude-code-docs test`; `npm -w packages/mcp-servers/claude-code-docs run build` |
| `v0-anchor-frontmatter-002` | objective_tests | `npm -w packages/mcp-servers/claude-code-docs test` |
| `v0-anchor-golden-queries-003` | objective_tests | `npm -w packages/mcp-servers/claude-code-docs test` |

### Anchor Task-Completion Oracle (supplementary)

For anchor scenarios, PASS/PASS on tests/build is **necessary but not sufficient**. A run is a **task failure** if `git diff -- packages/mcp-servers/claude-code-docs/` is empty after the runner completes (no-op), even if tests/build pass. A no-op trivially satisfies "tests pass" because nothing was changed.

Record this as `task_completion_verdict: PASS/FAIL` in anchor run records. A run scores:
- `PASS` if the runner produced a non-empty diff (code was changed)
- `FAIL` if the diff is empty (no-op)

This was identified during `v0-anchor-vitest-001` execution, where `CONTROL_HARMFUL_NO_TOOLS_v0.1.0` produced a no-op that the binary oracle scored as PASS/PASS.

### Rubric (rubric_blinded)

| scenario_id | oracle | scoring |
|---|---|---|
| `v0-rubric-scenario-spec-004` | rubric_blinded | blinded rubric (Section 7.2) |
| `v0-rubric-report-005` | rubric_blinded | blinded rubric (Section 7.2) |
| `v0-rubric-controls-006` | rubric_blinded | blinded rubric (Section 7.2); treat as writing-quality task, not “match canonical controls” |
| `v0-rubric-exact-three-options-007` | rubric_blinded | **Exact Count Requirements rubric** (primary) + minimal quality checks |
| `v0-rubric-reference-008` | rubric_blinded | blinded rubric with emphasis on citation specificity + observation vs inference |

---

## Condition Matrix (what to run)

This matrix is the canonical answer to “which scenarios get which controls?”

### Defaults

- For every scenario: run `BASELINE` and `TARGET`.
- Replication: `BASELINE` and `TARGET` run **N=3** each.
- Control conditions start at **N=1** each unless expanded (see expansion rules).

### Deterministic TARGET mapping (no inference allowed)

For Benchmark v0, `TARGET` is scenario-specific and MUST be selected from:
- `docs/benchmarks/bench-skill-bodies_v0.1.0.md` (BENCH_*)
- `docs/benchmarks/control-bodies_v0.1.0.md` (CONTROL_*) when a scenario’s “target” is itself a control-oriented behavior

If no `BENCH_*` skill is intended to improve a scenario, the scenario MUST be run as **baseline-only** (no `TARGET`), and any pre-generated `target` run-record stubs should be treated as invalid.

Canonical TARGET mapping for Benchmark v0:

| scenario_id | TARGET injected body |
|---|---|
| `v0-anchor-vitest-001` | `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` |
| `v0-anchor-frontmatter-002` | `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` |
| `v0-anchor-golden-queries-003` | `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` |
| `v0-rubric-scenario-spec-004` | **none** (baseline + controls only) |
| `v0-rubric-report-005` | `BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE_v0.1.0` |
| `v0-rubric-controls-006` | **none** (baseline + harmful brevity only) |
| `v0-rubric-exact-three-options-007` | `BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0` |
| `v0-rubric-reference-008` | `BENCH_REFERENCE_LOCAL_CITATIONS_ONLY_v0.1.0` |

### Control coverage (≥50%)

Benchmark v0 runs controls on 4 of 8 scenarios:
- 2 anchor scenarios
- 2 rubric scenarios

### Scenario-by-scenario matrix

| scenario_id | baseline | target | placebo | irrelevant | harmful (no tools) | harmful (brevity) | proxy-gaming |
|---|---:|---:|---:|---:|---:|---:|---:|
| `v0-anchor-vitest-001` | N=3 | N=3 | N=1 | N=1 | N=1 | — | — |
| `v0-anchor-frontmatter-002` | N=3 | N=3 | — | — | N=1 | — | — |
| `v0-anchor-golden-queries-003` | N=3 | N=3 | — | — | — | — | — |
| `v0-rubric-scenario-spec-004` | N=3 | — | N=1 | — | — | N=1 | N=1 |
| `v0-rubric-report-005` | N=3 | N=3 | — | — | — | — | N=1 |
| `v0-rubric-controls-006` | N=3 | — | — | — | — | N=1 | — |
| `v0-rubric-exact-three-options-007` | N=3 | N=3 | — | — | — | — | — |
| `v0-rubric-reference-008` | N=3 | N=3 | — | — | — | — | — |

**Control definitions:**
- Placebo: `CONTROL_PLACEBO_v0.1.0`
- Irrelevant (code): `CONTROL_IRRELEVANT_FOR_CODE_v0.1.0`
- Harmful (anchor): `CONTROL_HARMFUL_NO_TOOLS_v0.1.0`
- Harmful (rubric): `CONTROL_HARMFUL_BREVITY_60W_v0.1.0`
- Proxy-gaming: `CONTROL_PROXY_GAMING_v0.1.0`

---

## Blinding Policy (required for rubric scenarios)

### Minimum acceptable blinding (Benchmark v0)

For `rubric_blinded` scenarios, use an evaluator that did **not** generate the outputs being scored.

Acceptable evaluators (in descending preference):
1. Human evaluator (best)
2. Separate Claude Code session (recommended default)
3. Separate Claude Code agent invoked in an isolated context (acceptable for iteration)

Do not allow the same agent instance that produced outputs A/B to score them as “blinded.” If you do, you MUST label the results as lower confidence and cap the final verdict at `INCONCLUSIVE`.

### Required blinding record

Every rubric scenario run MUST record:
- Who evaluated (human / separate session / separate agent)
- How A/B was randomized
- When unmasking occurred (must be after scoring)

---

## Expansion Rules

Expand control replication from N=1 → N=3 if:
- a control condition outperforms baseline/target unexpectedly, or
- there is high variance in baseline/target, or
- proxy-gaming appears to “win” on non-proxy outcomes.

Expand baseline/target from N=3 → N=5 for a scenario if:
- the delta sign flips across runs, or
- results are borderline relative to thresholds.
