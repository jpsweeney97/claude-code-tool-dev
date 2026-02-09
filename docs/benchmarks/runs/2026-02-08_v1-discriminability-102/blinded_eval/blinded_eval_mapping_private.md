# Blinded Evaluation Mapping (PRIVATE) — v1 Discriminability Experiment

**Run ID:** `2026-02-08_v1-discriminability-102`

Do not share this file with blinded evaluators.

## Mapping Table

| replicate | candidate_id | condition | run_record_path |
|---|---|---|---|
| run-2 | `CANDIDATE_A` | baseline | `run-records/v1-rubric-evidence-ledger-102__baseline__run-2.md` |
| run-2 | `CANDIDATE_B` | target | `run-records/v1-rubric-evidence-ledger-102__target__run-2.md` |
| run-3 | `CANDIDATE_A` | target | `run-records/v1-rubric-evidence-ledger-102__target__run-3.md` |
| run-3 | `CANDIDATE_B` | baseline | `run-records/v1-rubric-evidence-ledger-102__baseline__run-3.md` |

## Randomization Record

- Randomization owner: executor (this session)
- Method: SHA-256 hash of `{run_id}:{scenario_id}:{replicate}`, first hex nibble determines assignment (0-7: A=baseline, 8-f: A=target)
- Seed: `2026-02-08_v1-discriminability-102`
- Timestamp: 2026-02-08
- Results:
  - Run-2: hash prefix `3` → A=baseline, B=target
  - Run-3: hash prefix `8` → A=target, B=baseline
- Notes: Assignments are deterministic and reproducible from the seed+scenario+replicate triple.

## Prior Data (from pilot)

Run-1 was already scored in the v1 pilot blinded evaluation:
- Pilot mapping: CANDIDATE_A = target (20/20), CANDIDATE_B = baseline (19/20)
- Delta (run-1): target - baseline = +1
- Source: `docs/benchmarks/runs/2026-02-08_benchmark-v1_pilot-01/blinded_scores.md`

After scoring runs 2 and 3, combine with run-1 data for the full N=3 analysis.
