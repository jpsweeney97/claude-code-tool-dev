# Blinded Evaluation Mapping (PRIVATE) — Benchmark v1 Pilot

**Run ID:** `2026-02-08_benchmark-v1_pilot-01`

Do not share this file with blinded evaluators.

## Mapping Table

| scenario_id | candidate_id | condition | run_record_path |
|---|---|---|---|
| `v1-rubric-constraint-ledger-101` | `CANDIDATE_A` | baseline | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-constraint-ledger-101__baseline__run-1.md` |
| `v1-rubric-constraint-ledger-101` | `CANDIDATE_B` | target | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-constraint-ledger-101__target__run-1.md` |
| `v1-rubric-evidence-ledger-102` | `CANDIDATE_A` | target | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-evidence-ledger-102__target__run-1.md` |
| `v1-rubric-evidence-ledger-102` | `CANDIDATE_B` | baseline | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-evidence-ledger-102__baseline__run-1.md` |
| `v1-rubric-verdict-gating-103` | `CANDIDATE_A` | target | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-verdict-gating-103__target__run-1.md` |
| `v1-rubric-verdict-gating-103` | `CANDIDATE_B` | baseline | `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/run-records/v1-rubric-verdict-gating-103__baseline__run-1.md` |

## Randomization Record

- Randomization owner: executor (this session)
- Method: SHA-256 hash of `{run_id}:{scenario_id}`, first hex nibble determines assignment (0-7: A=baseline, 8-f: A=target)
- Seed: `2026-02-08_benchmark-v1_pilot-01`
- Timestamp: 2026-02-08
- Results:
  - Scenario 101: hash prefix `1` → A=baseline, B=target
  - Scenario 102: hash prefix `c` → A=target, B=baseline
  - Scenario 103: hash prefix `9` → A=target, B=baseline
- Notes: Assignments are deterministic and reproducible from the seed+scenario pair.
