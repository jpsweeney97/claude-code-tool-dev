# Rolling Handoff Packet — Benchmark v0

This file is a standardized resume packet for starting a *fresh* Claude session when context limits require a reset.

## Repo

- `/Users/jp/Projects/active/claude-code-tool-dev`

## Goal

Run Benchmark v0 (Simulation Effectiveness Benchmark) with Claude Code executor to assess functional effectiveness of simulation-based architecture.

## Loop Contract

1) Execute exactly one run at a time (1 scenario × 1 condition × 1 replicate).
2) Use canonical mappings only; do not infer.
3) Write specified run-record file.
4) Return status + concise bullets (NO full-file paste; main session reads run record from disk).

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

## Run-Record Directory

- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/`

## Most Recent Run Record Touched

- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__baseline__run-1.md`
  - Repaired: `replicate` format normalized to `run-1`
  - Added: `## Canonical Mapping Citations`
 - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__baseline__run-2.md`
   - Strong convergence with run-1 on `skills` + “Creating skills” subsection (near-identical query strings)
 - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__baseline__run-3.md`
   - Anti-convergence succeeded by targeting `troubleshooting` instead of `skills`
 - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__target__run-1.md`
   - Target also chose `troubleshooting` (suggests secondary attractor beyond `skills`)
 - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__target__run-2.md`
   - Target diverged to `security` (permission boundaries subsection)
 - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/run-records/v0-anchor-golden-queries-003__target__run-3.md`
   - Converged back to `skills` (“Creating skills”) confirming dominant attractor

## Immediate Next Action

Proceed to scoring + report updates for `2026-02-06_benchmark-v0_initial`.

Write run record:

- No new run record. Next updates typically go to:
  - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/scores.md`
  - `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-06_benchmark-v0_initial/report.md`

Response format:

- First line: `COMPLETED` or `BLOCKED: <reason>`
- Then 5–10 concise bullets with mapping/body, clean-start, change, oracle result, `task_completion_verdict`, cleanup/final diff.
