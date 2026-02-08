# Benchmark v1 Pilot Report — 2026-02-08_benchmark-v1_pilot-01

## 1) Scope

This pilot evaluates rubric discriminability improvements for v1 draft scenarios:
- `v1-rubric-constraint-ledger-101`
- `v1-rubric-evidence-ledger-102`
- `v1-rubric-verdict-gating-103`

Conditions:
- baseline N=1
- target N=1

## 2) Execution Status

- Run execution completeness: COMPLETE (6/6 tuples executed; 6/6 tuples ACCEPTED)
- Blinded packet completeness: COMPLETE (`blinded_eval/blinded_eval_packet.md` populated; mapping file populated)
- Blinded scoring completeness: COMPLETE (`blinded_scores.md` populated; unmasking completed)

## 3) Evidence

- Per-scenario totals and deltas (see `scores.md`):
  - `v1-rubric-constraint-ledger-101`: 20 → 16 (delta -4)
  - `v1-rubric-evidence-ledger-102`: 19 → 20 (delta +1)
  - `v1-rubric-verdict-gating-103`: 19 → 20 (delta +1)
- Improvement signal count: 0/3 (suite rule requires delta >= +2 plus critical-dimension lift)
- Confounders observed: recorded in run records (e.g., differential tool usage noted in `v1-rubric-constraint-ledger-101__target__run-1`)

## 4) Interpretation

- Pilot gate verdict: **FAIL**
- Confidence level: High (deterministic gate rules applied to recorded totals)
- Key rationale:
  - Regression criterion violated: `v1-rubric-constraint-ledger-101` target regressed by 4 points (>=2).
  - No scenario met the improvement-signal rule (no deltas >= +2).

## 5) Next Action

- If gate PASS: expand to full v1 replication (baseline N=3, target N=3).
- If gate FAIL: revise scenario/rubric design before full execution.
- Immediate next step: revise Scenario 101 discriminability/rubric coupling and re-run a new pilot (new `RUN_ID`) before attempting full replication.

## 6) References

- `docs/benchmarks/suites/benchmark-v1-draft_v0.1.0.md`
- `docs/benchmarks/operations/benchmark-v1_pilot_checklist_v0.1.0.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-constraint-ledger-101.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-evidence-ledger-102.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-verdict-gating-103.md`
