# Rolling Handoff Packet — Benchmark v0

This file is a standardized resume packet for starting a *fresh* Claude session when context limits require a reset.
Executor-facing document only. Orchestrator actions belong in `handoff_codex.md`.

## Repo

- `/Users/jp/Projects/active/claude-code-tool-dev`

## Goal

Run Benchmark v0 (Simulation Effectiveness Benchmark) with Claude Code executor to assess functional effectiveness of simulation-based architecture.

## Loop Contract

1) Execute exactly one run at a time (1 scenario × 1 condition × 1 replicate).
2) Use canonical mappings only; do not infer.
3) Write specified run-record file.
4) Return status + concise bullets (NO full-file paste; main session reads run record from disk).
5) Do NOT select the next run or run orchestration/resume scripts (that is orchestrator-only).

## Canonical Docs (Authoritative)

Use **ONLY** these for mapping and citations:

1) `/Users/jp/Projects/active/claude-code-tool-dev/docs/simulation-assessment-context-official.md`
2) `/Users/jp/Projects/active/claude-code-tool-dev/docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3) `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4) `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/target-skills_v0.1.0.md`
5) `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/control-bodies_v0.1.0.md`
6) `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/bench-skill-bodies_v0.1.0.md`

## Hard Invariants (Every Run)

- Never use `rm`; use `trash`.
- Skills hot-reload; do not rely on subagents.
- Neutral skill metadata naming (no baseline/test/control/placebo labels).
- Runner is pre-check only; main session anchor oracle is oracle of record.
- Must verify clean start:
  - `git diff -- packages/mcp-servers/claude-code-docs/` must be empty before run.
- Must cleanup after run:
  - `trash` temp skill dir + revert code changes + verify diff empty.
- Anchor rule:
  - include `task_completion_verdict` PASS/FAIL.
  - Empty diff => FAIL even if tests pass.
- Run record must include raw output blocks for clean-start/oracle/cleanup verification.
- Replicate must be recorded as string `run-1`/`run-2`/`run-3` (NOT numeric).
- Citation rule:
  - use the six canonical docs only (do not cite `docs/benchmarks/scenarios/SCENARIO-*`).
- Rubric scenarios (`rubric_blinded`):
  - no self-scoring
  - no rubric score table (even empty/em-dash scaffold tables)
- Leakage rule (strict, orchestrator-enforced):
  - do NOT read `scores.md`, `report.md`, or other run records for the same run_id.
  - any disallowed read => run is **REPAIR required** (not acceptable for baseline/condition accounting).

## Current Benchmark Run ID

- `2026-02-06_benchmark-v0_initial`

## Progress Snapshot

- `v0-anchor-vitest-001`: COMPLETE (9/9)
- `v0-anchor-frontmatter-002`: COMPLETE (7/7)
  - baseline run-1/run-2/run-3 complete
  - target run-1/run-2/run-3 complete
  - harmful_no_tools run-1 complete (expected no-op; `task_completion_verdict: FAIL`)
  - placebo correctly BLOCKED (not scheduled in suite matrix)
- `v0-anchor-golden-queries-003`:
  - baseline run-1 COMPLETE (run record repaired: replicate now `run-1` + canonical mapping citations added)
  - baseline run-2 COMPLETE
  - baseline run-3 COMPLETE (note: anti-convergence steering used; see run record Confounders)
  - target run-1 COMPLETE
  - target run-2 COMPLETE
  - target run-3 COMPLETE

- `v0-rubric-scenario-spec-004`: COMPLETE (6/6)
  - baseline run-1/run-2/run-3 COMPLETE
  - placebo run-1 COMPLETE
  - proxy_gaming run-1 COMPLETE
  - harmful_brevity_60w run-1 COMPLETE

- `v0-rubric-report-005`: COMPLETE (7/7)
  - baseline run-1/run-2/run-3 COMPLETE (run-3 accepted via REPAIR re-execution)
  - target run-1/run-2/run-3 COMPLETE
  - proxy_gaming run-1 COMPLETE

- `v0-rubric-controls-006`: COMPLETE (4/4)
  - baseline run-1/run-2/run-3 COMPLETE
  - harmful_brevity_60w run-1 COMPLETE

- `v0-rubric-exact-three-options-007`: COMPLETE (6/6)
  - baseline run-1/run-2/run-3 COMPLETE
  - target run-1/run-2/run-3 COMPLETE

- `v0-rubric-reference-008`: COMPLETE (6/6)
  - baseline run-1/run-2/run-3 COMPLETE
  - target run-1/run-2/run-3 COMPLETE

## Run-Record Directory

- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/`

## Most Recent Run Record Touched

This section distinguishes:
- **Most recently modified on disk:** the run-record file(s) most recently edited in the repo (including repairs).
- **Most recently accepted run:** the last run record that passed invariant validation (i.e., accepted as a completed benchmark run record).

- **Most recently modified on disk:**
  - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-rubric-exact-three-options-007__baseline__run-3.md`

- **Most recently accepted run:**
  - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-rubric-exact-three-options-007__baseline__run-3.md`
    - Accepted; strict leakage gate satisfied, plus rubric_blinded + zero-mention invariants verified.

## Immediate Next Action

Benchmark v0 run execution is COMPLETE (`planned_runs=51`, `executed_runs=51`).

Blinded evaluator scoring is COMPLETE:
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/blinded_scores.md`

Post-eval refresh is COMPLETE:
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/scores.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/report.md`

Blinding gate status:
- `rg` checks on `blinded_scores.md` for condition labels and injected-body tokens returned empty (clean).

Benchmark v0 status:
- **COMPLETE** (execution + blinded scoring + score/report refresh)
- Final verdict in report: **INCONCLUSIVE** (16.7% scenario improvement vs 70% threshold)
- No remaining run tuples.

## Next Claude Prompt (Copy/Paste)

```text
N/A — Benchmark v0 loop is complete.
No further executor/evaluator prompt is required for this run_id.
```

## Repo State Notes

- Benchmark artifacts under `docs/benchmarks/` are now tracked in git (use `git diff` for verification).
- Two unrelated plan docs remain untracked:
  - `docs/plans/codex-tool-dev-repo-skeleton.md`
  - `docs/plans/codex-tool-dev-repo-spec.md`

Response format:

- First line: `COMPLETED` or `BLOCKED: <reason>`
- Then 5–10 concise bullets with final artifact pointers and any proposed follow-up.
