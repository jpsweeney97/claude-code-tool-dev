# Benchmark v1 Draft Spec v0.1.0 (Scenario + Rubric Redesign)

This file is the **draft design spec** for Benchmark v1. It addresses the main v0 limitation:
high ceiling effects with coarse rubric resolution.

Benchmark v0 showed that the architecture works, but only 1/6 baseline-target comparisons produced non-zero signal.
v1 therefore keeps the same execution architecture and upgrades **scenario discriminability + rubric granularity**.

**Status:** Draft (pilot-executable via temporary v1 target bodies; full suite pending canonical v1 body finalization)  
**Last updated:** 2026-02-08  
**Primary objective:** Increase baseline-target separation while preserving blinded scoring discipline.

Execution companion:
- `docs/benchmarks/operations/benchmark-v1_pilot_checklist_v0.1.0.md`

---

## 1) Design Goals (derived from v0 findings)

1. Reduce ceiling effects by moving rubric scoring from 0-2 to **0-4**.
2. Add scenario-specific dimensions, not only generic quality dimensions.
3. Keep at least one strict binary discipline dimension (like v0 scenario 007), but avoid over-narrow task spaces.
4. Require confidence calibration under confounders (explicit downgrade rules).
5. Gate full-scale execution behind a pilot that proves discriminative power.

---

## 2) Scenario Roster (v1 Draft)

| scenario_id | oracle_type | intent | expected discriminative signal |
|---|---|---|---|
| `v1-rubric-constraint-ledger-101` | rubric_blinded | Constraint-accountable recommendation with exact structure + weighted scoring | Count/constraint discipline + coherent trade-off reasoning |
| `v1-rubric-evidence-ledger-102` | rubric_blinded | Observation vs inference on conflicting inputs with confidence downgrades | Citation precision + calibration under ambiguity |
| `v1-rubric-verdict-gating-103` | rubric_blinded | Compute benchmark verdict from supplied metrics + confounders | Threshold logic + confidence gating + anti-overclaiming |

Scenario definitions live in:
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-constraint-ledger-101.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-evidence-ledger-102.md`
- `docs/benchmarks/scenarios/SCENARIO-v1-rubric-verdict-gating-103.md`

---

## 3) v1 Rubric Model (0-4 Scale)

### 3.1 Dimension scale anchors (applies to all scenarios)

| Score | Meaning |
|---|---|
| 0 | Missing or incorrect; directly violates requirement |
| 1 | Attempt present but substantially flawed/incomplete |
| 2 | Partially correct; material omissions or weak justification |
| 3 | Correct and complete for standard expectations |
| 4 | Strong execution with precise, well-supported details |

### 3.2 Scenario scoring shape

- 5 dimensions per scenario
- 0-4 per dimension
- Total per output: 0-20

**Critical dimensions:** each scenario flags 2 critical dimensions.  
Critical dimensions must score **>=3** for the output to be considered fully compliant.

### 3.3 Scenario pass rule

An output is `PASS` if:
- total score >=16/20, and
- both critical dimensions >=3.

Otherwise: `FAIL`.

### 3.4 Improvement signal rule (baseline vs target)

For each scenario, improvement is considered present if all are true:
1. `target_total - baseline_total >= 2`, and
2. target is `PASS`, and
3. at least one critical dimension increases by >=1 point.

This avoids crediting tiny numeric differences with no practical behavioral change.

---

## 4) Scenario-Specific Rubrics

## 4.1 `v1-rubric-constraint-ledger-101`

Critical dimensions: **D1, D2**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Structural compliance | Exactly 3 options; required sections present; no extra options/honorable mentions |
| D2 | Constraint coverage | All prompt constraints represented in option analysis and recommendation rationale |
| D3 | Trade-off quality | Strengths/weaknesses are concrete, non-duplicative, and decision-relevant |
| D4 | Quantitative coherence | Weighted score table is valid (weights sum to 100) and aligns with recommendation |
| D5 | Risk realism | Risk statement + fast-fail experiment are specific and testable |

## 4.2 `v1-rubric-evidence-ledger-102`

Critical dimensions: **D1, D3**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Evidence typing accuracy | Observation vs Inference labels are correct for each claim |
| D2 | Citation precision | Evidence references map precisely to provided snippets/paths |
| D3 | Conflict calibration | Conflicting evidence causes explicit confidence downgrades and rationale |
| D4 | Unsupported-claim control | Avoids assertions not grounded in supplied evidence |
| D5 | Investigation quality | Unknowns + next checks are specific and likely to reduce uncertainty |

## 4.3 `v1-rubric-verdict-gating-103`

Critical dimensions: **D1, D2**

| Dim | Name | What is scored |
|---|---|---|
| D1 | Metric correctness | Derived metrics are numerically correct from provided scenario data |
| D2 | Threshold logic | Verdict logic correctly applies Section 9.3-style thresholds |
| D3 | Evidence/interpretation separation | Structural separation is explicit and respected |
| D4 | Confidence downgrade discipline | Confounders produce explicit confidence adjustment (not merely mentioned) |
| D5 | Decision-actionability | Clear trigger conditions for rerun/redesign/acceptance decisions |

---

## 5) Pilot Matrix (Gate Before Full v1)

Pilot scope decision (2026-02-08):
- **Rubric-only pilot** (no objective anchor scenarios in pilot phase).
- Rationale: maximize signal on rubric discriminability before adding anchor overhead.

Run matrix (minimum):

| scenario_id | baseline | target |
|---|---:|---:|
| `v1-rubric-constraint-ledger-101` | N=1 | N=1 |
| `v1-rubric-evidence-ledger-102` | N=1 | N=1 |
| `v1-rubric-verdict-gating-103` | N=1 | N=1 |

### Pilot acceptance gate

Proceed to full v1 only if:
1. At least 2/3 scenarios show improvement by rule in Section 3.4.
2. No scenario shows target regression (`target_total < baseline_total`) by >=2 points.
3. Blinding contamination checks are clean.

If gate fails: revise scenario prompts and/or rubric dimensions before adding replication.

---

## 6) Full v1 Expansion (after pilot pass)

Recommended default:
- baseline N=3 and target N=3 for each v1 scenario.
- Add at least one adverse control condition on >=1 scenario to verify degradation sensitivity remains intact.

Expand N=3 -> N=5 when:
- score deltas are within +/-1 on average,
- or sign flips occur between replicates,
- or evaluator confidence is low due to confounders.

---

## 7) Planned v1 Skill Mapping (Draft)

These names are placeholders for v1 body authoring:

| scenario_id | baseline | target placeholder |
|---|---|---|
| `v1-rubric-constraint-ledger-101` | no injected benchmark body | `BENCH_DISCIPLINE_CONSTRAINT_LEDGER_v1.0.0` |
| `v1-rubric-evidence-ledger-102` | no injected benchmark body | `BENCH_REFERENCE_EVIDENCE_CALIBRATION_v1.0.0` |
| `v1-rubric-verdict-gating-103` | no injected benchmark body | `BENCH_PATTERN_VERDICT_GATING_v1.0.0` |

Controls can be reused from v0 (`PLACEBO`, `IRRELEVANT`, `HARMFUL_BREVITY`, `PROXY_GAMING`) where appropriate.

---

## 8) Open Questions (must resolve before execution)

1. Which scenario(s) should receive proxy-gaming controls to stress structural compliance without correctness?
2. Should evaluator confidence become a numeric field (e.g., 0.0-1.0) instead of qualitative labels?

Until these are resolved, treat this as a planning spec rather than an executable suite contract.
