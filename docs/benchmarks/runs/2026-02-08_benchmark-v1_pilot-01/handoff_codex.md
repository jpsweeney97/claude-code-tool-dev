# Rolling Handoff Packet — Benchmark v1 Pilot (Codex Orchestrator)

Codex-only packet for orchestration + verification in fresh sessions.
Executor prompt text for Claude is maintained in `handoff.md`.

## Repo

- `/Users/jp/Projects/active/claude-code-tool-dev`

## Run ID

- `2026-02-08_benchmark-v1_pilot-01`

## Mission

Run and verify the rubric-only v1 pilot with strict one-tuple cadence:
- 3 scenarios
- conditions: baseline + target
- replicate: run-1
- total tuples: 6

## Interaction Pattern (Must Follow)

1) Read this file + `handoff.md`.
2) Determine the next pending tuple from run-record stubs on disk.
3) Generate one paste-ready Claude executor prompt for that tuple.
4) After Claude response, verify run record from disk (not chat summary).
5) Update `handoff.md` + `handoff_codex.md` with latest accepted state.
6) Repeat until all 6 tuples complete.

## Authoritative References

- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/operations/benchmark-v1_pilot_checklist_v0.1.0.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/bench-skill-bodies_v1.0.0.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-constraint-ledger-101.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-evidence-ledger-102.md`
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/scenarios/SCENARIO-v1-rubric-verdict-gating-103.md`

## Pilot Run Matrix (Canonical)

1. `v1-rubric-constraint-ledger-101__baseline__run-1`
2. `v1-rubric-constraint-ledger-101__target__run-1`
3. `v1-rubric-evidence-ledger-102__baseline__run-1`
4. `v1-rubric-evidence-ledger-102__target__run-1`
5. `v1-rubric-verdict-gating-103__baseline__run-1`
6. `v1-rubric-verdict-gating-103__target__run-1`

Run-record dir:
- `/Users/jp/Projects/active/claude-code-tool-dev/docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/`

## Verification Checklist (Per Tuple)

1) Filename + metadata tuple match:
   - `scenario_id`, `condition`, `replicate=run-1`.
2) `oracle_type` is `rubric_blinded`.
3) No self-scoring table present.
4) Preflight clean-start evidence present.
5) Cleanup block present and shows:
   - temp skill dir removed via `trash`
   - scoped package revert
   - final package diff empty.
6) Explicit confirmation: did not run `git checkout -- .`.
7) Tool trace + confounders sections are populated.
8) For target runs, injected body token/text matches canonical definitions in `bench-skill-bodies_v1.0.0.md`.

If any check fails:
- mark tuple `REPAIR_REQUIRED`
- do not advance progression pointer
- re-run same tuple with corrected prompt.

## Current State Snapshot

All execution complete:
- run records: 6/6 COMPLETED
- blinded packet: READY FOR EVALUATION
- private mapping: POPULATED (with randomized A/B assignments)
- blinded scores: COMPLETE
- scores/report: COMPLETE

## Tuple Acceptance Ledger (Orchestrator)

Acceptance statuses are recorded by Codex after verifying the on-disk run record against the checklist above.

| tuple_id | execution_status | acceptance_status | notes |
|---|---|---|---|
| `v1-rubric-constraint-ledger-101__baseline__run-1` | COMPLETED | **ACCEPTED** | Verified from run record on 2026-02-08 |
| `v1-rubric-constraint-ledger-101__target__run-1` | COMPLETED | **ACCEPTED** | Injected body token matches canonical mapping; run record references canonical body source |
| `v1-rubric-evidence-ledger-102__baseline__run-1` | COMPLETED | **ACCEPTED** | Verified from run record on 2026-02-08 |
| `v1-rubric-evidence-ledger-102__target__run-1` | COMPLETED | **ACCEPTED** | Injected body token matches canonical mapping; run record references canonical body source |
| `v1-rubric-verdict-gating-103__baseline__run-1` | COMPLETED | **ACCEPTED** | Verified from run record on 2026-02-08 |
| `v1-rubric-verdict-gating-103__target__run-1` | COMPLETED | **ACCEPTED** | Injected body token matches canonical mapping; run record references canonical body source |

## Immediate Next Action

All tuples **ACCEPTED**. Evaluator phase complete.

Pilot gate decision (per `scores.md`): **FAIL**

Next action:
1. Revise Scenario 101 discriminability + rubric coupling
2. Re-run a new pilot (new `RUN_ID`) before authorizing full replication

## Claim Boundary (Orchestrator)

- Pilot PASS/FAIL is a gate decision only.
- Do not claim general effectiveness from N=1 pilot results.

## Next Codex Actions

Execution phase complete. Orchestrator should:
1. Launch a new evaluator session with blinded packet
2. Collect scores into `blinded_scores.md`
3. Unmask and compute pilot gate
4. Write final report to `report.md`
