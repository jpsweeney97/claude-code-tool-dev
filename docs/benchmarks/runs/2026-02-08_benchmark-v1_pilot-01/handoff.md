# Rolling Handoff Packet — Benchmark v1 Pilot

Executor-facing packet for fresh Claude sessions.
Orchestrator procedure belongs in `handoff_codex.md`.

## Repo

- `/Users/jp/Projects/active/claude-code-tool-dev`

## Goal

Execute Benchmark v1 pilot run_id `2026-02-08_benchmark-v1_pilot-01`:
- rubric-only pilot
- 3 scenarios
- baseline + target
- 1 replicate each (6 total runs)

## Authoritative Docs

1. `/Users/jp/Projects/active/claude-code-tool-dev/docs/simulation-assessment-context-official.md`
2. `/Users/jp/Projects/active/claude-code-tool-dev/docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`
4. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/operations/benchmark-v1_pilot_checklist_v0.1.0.md`
5. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/bench-skill-bodies_v1.0.0.md`
6. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-constraint-ledger-101.md`
7. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-evidence-ledger-102.md`
8. `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-verdict-gating-103.md`

## Loop Contract

1) Execute exactly one run tuple at a time.
2) Write/complete only the specified run-record file for that tuple.
3) Do not choose the next run tuple (orchestrator-only).
4) Return concise completion status (no full file paste).
5) For `rubric_blinded`, do not self-score.

## Hard Invariants (Every Run)

- Never use `rm`; use `trash`.
- Do not run `git checkout -- .`.
- Verify clean start:
  - `git diff -- packages/mcp-servers/claude-code-docs/` must be empty before execution.
- Cleanup after run:
  - remove temporary skill dir via `trash`
  - revert package code changes via scoped checkout
  - verify `git diff -- packages/mcp-servers/claude-code-docs/` is empty.
- Replicate must be `run-1` (string).
- `oracle_type` is `rubric_blinded`; no score tables in run records.
- Keep tooling expectation aligned to scenario: `no_web`.
- For target condition runs, injected body text must come from canonical `bench-skill-bodies_v1.0.0.md`.

## Claim Boundary

- This pilot is a discriminability gate at N=1.
- Pilot PASS/FAIL is valid.
- General effectiveness claims are not valid until post-pilot replication.

## Pilot Run ID

- `2026-02-08_benchmark-v1_pilot-01`

## Current Progress Snapshot

All 6 runs COMPLETED. Blinded evaluation materials READY.

- `v1-rubric-constraint-ledger-101__baseline__run-1.md` — COMPLETED
- `v1-rubric-constraint-ledger-101__target__run-1.md` — COMPLETED
- `v1-rubric-evidence-ledger-102__baseline__run-1.md` — COMPLETED
- `v1-rubric-evidence-ledger-102__target__run-1.md` — COMPLETED
- `v1-rubric-verdict-gating-103__baseline__run-1.md` — COMPLETED
- `v1-rubric-verdict-gating-103__target__run-1.md` — COMPLETED
- `blinded_eval/blinded_eval_packet.md` — READY FOR EVALUATION
- `blinded_eval/blinded_eval_mapping_private.md` — POPULATED

## Orchestrator Verification Status

Run records must be verified and marked **ACCEPTED** by the orchestrator (Codex) before blinded scoring/gate computation.

| tuple_id | acceptance_status |
|---|---|
| `v1-rubric-constraint-ledger-101__baseline__run-1` | **ACCEPTED** |
| `v1-rubric-constraint-ledger-101__target__run-1` | **ACCEPTED** |
| `v1-rubric-evidence-ledger-102__baseline__run-1` | **ACCEPTED** |
| `v1-rubric-evidence-ledger-102__target__run-1` | **ACCEPTED** |
| `v1-rubric-verdict-gating-103__baseline__run-1` | **ACCEPTED** |
| `v1-rubric-verdict-gating-103__target__run-1` | **ACCEPTED** |

## Run-Record Directory

- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/`

## Immediate Next Action

All execution complete. Blinded scoring + unmasking complete.

Pilot gate decision (per `scores.md`): **FAIL**

Next step: revise Scenario 101 discriminability/rubric coupling and re-run a new pilot (new `RUN_ID`) before attempting full replication.
