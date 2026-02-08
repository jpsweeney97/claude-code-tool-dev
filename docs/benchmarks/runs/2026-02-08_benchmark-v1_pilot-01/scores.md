# Benchmark v1 Pilot Scores — Run 2026-02-08_benchmark-v1_pilot-01

## Pilot Summary

- Scenarios scored: 3
- Candidate outputs scored: 6
- Improvement signals detected: 0/3
- Pilot gate status: **FAIL**

---

## Per-Scenario Baseline vs Target Summary

| scenario_id | baseline_total | target_total | delta | baseline_pass_fail | target_pass_fail | improvement_signal |
|---|---:|---:|---:|---|---|---|
| `v1-rubric-constraint-ledger-101` | 20 | 16 | -4 | PASS | PASS | false |
| `v1-rubric-evidence-ledger-102` | 19 | 20 | +1 | PASS | PASS | false |
| `v1-rubric-verdict-gating-103` | 19 | 20 | +1 | PASS | PASS | false |

---

## Pilot Gate Evaluation

Gate criteria:
1. At least 2/3 scenarios show improvement signal.
2. No scenario has target regression >=2 points.
3. Blinding contamination checks are clean.

- Criterion 1: FAIL (0/3 improvement signals)
- Criterion 2: FAIL (`v1-rubric-constraint-ledger-101` delta = -4)
- Criterion 3: PASS (no contamination scan matches in `blinded_scores.md`)

**Pilot Decision:** **FAIL**

## Notes

- Improvement signal definition (per suite draft): `target_total - baseline_total >= 2` AND target PASS AND at least one critical dimension improves by >=1.
- This pilot decision is a replication authorization gate only (N=1); it does not support general effectiveness claims.
