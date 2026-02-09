# Discriminability Analysis — Scenario 102, N=3

**Run ID:** `2026-02-08_v1-discriminability-102`
**Date:** 2026-02-08
**Branch:** `experiment/v1-discriminability-102`
**Scenario:** v1-rubric-evidence-ledger-102

## Purpose

Test whether rubric scoring can detect skill effects on the scenario with the most obvious behavioral differences. This is a measurement validation experiment, not a skill effectiveness test.

**Motivation:** Two benchmark cycles (v0: 51 runs, v1 pilot: 6 runs) produced no clear positive signal. Before investing in rubric redesign, we need to know if rubric-based scoring can detect skill effects at all.

**Decision record:** `docs/plans/2026-02-08-benchmark-next-steps-decision.md`

## Design

- **Scenario:** 102 (evidence ledger) — chosen because target runs produce visible behavioral differences (explicit counting, verification sections, structured confidence downgrades)
- **Conditions:** baseline (no skill) vs. target (skill loaded)
- **N:** 3 per condition (run-1 reused from pilot, runs 2-3 new)
- **Blinding:** Randomized A/B labels per replicate, scored in isolated `/tmp/` session with no project context
- **Randomization:** SHA-256 hash of `{run_id}:{scenario}:{replicate}`, first nibble determines A/B assignment

## Data Sources

| Run | Source | Evaluator session |
|-----|--------|-------------------|
| Run-1 | v1 pilot (`2026-02-08_benchmark-v1_pilot-01/blinded_scores.md`) | Separate blinded session |
| Run-2 | This experiment (`blinded_scores.md`) | Isolated `/tmp/blinded-eval-102/` session |
| Run-3 | This experiment (`blinded_scores.md`) | Same isolated session as run-2 |

## Unmasked Scores

### Mapping

| Replicate | Label | Condition | Source |
|-----------|-------|-----------|--------|
| Run-1 | CANDIDATE_A | target | Pilot mapping |
| Run-1 | CANDIDATE_B | baseline | Pilot mapping |
| Run-2 | CANDIDATE_A | baseline | `blinded_eval_mapping_private.md` (nibble `3`) |
| Run-2 | CANDIDATE_B | target | `blinded_eval_mapping_private.md` |
| Run-3 | CANDIDATE_A | target | `blinded_eval_mapping_private.md` (nibble `8`) |
| Run-3 | CANDIDATE_B | baseline | `blinded_eval_mapping_private.md` |

### Scores by Condition

| Run | Condition | D1 | D2 | D3 | D4 | D5 | Total |
|-----|-----------|----|----|----|----|-----|-------|
| 1 | target | 4 | 4 | 4 | 4 | 4 | 20 |
| 1 | baseline | 4 | 4 | 3 | 4 | 4 | 19 |
| 2 | target | 4 | 4 | 4 | 4 | 4 | 20 |
| 2 | baseline | 4 | 4 | 4 | 4 | 4 | 20 |
| 3 | target | 4 | 4 | 4 | 4 | 4 | 20 |
| 3 | baseline | 4 | 4 | 4 | 4 | 4 | 20 |

### Per-Run Deltas (target − baseline)

| Run | Target total | Baseline total | Delta |
|-----|-------------|----------------|-------|
| 1 | 20 | 19 | **+1** |
| 2 | 20 | 20 | **0** |
| 3 | 20 | 20 | **0** |
| **Mean** | **20.0** | **19.7** | **+0.33** |

### Per-Dimension Deltas

| Dimension | Run-1 | Run-2 | Run-3 | Mean |
|-----------|-------|-------|-------|------|
| D1 (Evidence typing) | 0 | 0 | 0 | 0 |
| D2 (Citation precision) | 0 | 0 | 0 | 0 |
| D3 (Conflict calibration) | +1 | 0 | 0 | +0.33 |
| D4 (Unsupported-claim discipline) | 0 | 0 | 0 | 0 |
| D5 (Investigation quality) | 0 | 0 | 0 | 0 |

All signal (such as it is) comes from D3. In the pilot, the baseline's D3 was docked one point for a borderline confidence violation (Claim 1 at 0.8 despite counter-evidence). In runs 2-3, both conditions scored 4/4 on D3.

## Verdict

**Under the current rubric and prompt difficulty, rubric scoring cannot detect skill effects on scenario 102.**

### Primary analysis: Runs 2–3 (same evaluator session)

Runs 2 and 3 were scored in the same isolated evaluator session, eliminating inter-session evaluator variance. Both runs show delta = **0** (20/20 vs 20/20). The rubric produces no separation whatsoever.

### Supporting context: Run-1 (different evaluator session)

Run-1 was scored in a separate blinded session (the v1 pilot evaluator). It shows delta = **+1** (20/20 vs 19/20), with the baseline docked on D3 for a borderline confidence violation. This 1-point difference could reflect a real condition effect or evaluator-session drift — with ceilings this tight, inter-session scoring variation is a plausible confounder.

### Combined (with caveat)

| Metric | Runs 2–3 only | All three runs |
|--------|---------------|----------------|
| Mean delta | **0.0** | **+0.33** |
| Range | 0 to 0 | 0 to +1 |

Per the decision record's interpretation criteria:
- Consistent deltas ≥ +2 → rubric CAN detect → proceed to redesign. **Not met.**
- Consistent deltas ~+1 → rubric CAN'T detect → pivot or stop. **Met (runs 2–3 show zero delta; run-1's +1 is within plausible evaluator variance).**
- Mixed signals → add more runs. **Not applicable (primary analysis shows no signal).**

## Diagnosis: Ceiling Effect

The rubric's 0-4 scale per dimension has a hard ceiling at 20/20. Both baseline and target Claude consistently hit this ceiling.

**The evaluator saw the differences but couldn't score them.** Direct evidence from the blinded evaluation rationale:

1. **Run-2, CANDIDATE_B (target):** Evaluator noted "Includes a dedicated 'Summary of Confidence Downgrades' section" and "Includes row-count and confidence-threshold verification" — features absent from the baseline. Score: 4/4.

2. **Run-2, CANDIDATE_A (baseline):** No mention of these features. Score: 4/4.

Both conditions satisfy every rubric criterion at the maximum level. The rubric asks "did the output do X correctly?" and both answer "yes" — the rubric has no mechanism to reward *how thoroughly* or *how structured* the output's approach was.

### Why behavioral differences don't produce score differences

The skill adds process structure (explicit counting, verification sections, confidence downgrade summaries). The rubric measures outcome correctness (are labels right? are citations accurate? are confidences calibrated?). Claude produces correct outcomes with or without the process structure. The skill changes *how* Claude arrives at answers, not *whether* it gets them right — and the rubric only measures the latter.

This is not a rubric design flaw in the narrow sense (the rubric accurately measures what it claims to measure). It's a measurement-target mismatch: rubric scoring measures output quality, but skill effects manifest as process changes that don't affect output quality on tasks within Claude's capability range.

### Falsifier

The ceiling-effect diagnosis predicts: if we introduce a harder evidence set with forced tradeoffs that reliably induces baseline mistakes in D3/D4 (e.g., an evidence set where correct confidence calibration requires noticing a subtle conflict that baselines miss), rubric deltas should reappear. If rubric deltas remain near zero even when baselines make observable errors, the measurement-target mismatch hypothesis strengthens further.

## Implications

1. **Correctness-focused rubric redesign will not fix this at the current difficulty level.** The ceiling effect is not about rubric granularity (e.g., switching to a 0-10 scale). It's about what the rubric measures relative to the task difficulty. Any rubric that measures "correctness of the output" will hit the same ceiling on tasks where Claude produces correct outputs regardless of skill presence. However, a rubric that explicitly measures *process structure* (essentially encoding the behavioral markers as rubric dimensions) could detect effects — but at that point the rubric is measuring behavior, not quality.

2. **Behavioral markers can detect skill effects.** The evaluator's own rationale text proves that target-specific behaviors (counting verification, confidence downgrade summaries) are consistently present in target runs and absent from baselines. A measurement approach that detects presence/absence of these behaviors will have discriminating power.

3. **The benchmark question needs reframing.** "Do skills improve output quality?" → not measurably at this task difficulty, because Claude's baseline quality is already high. "Do skills change Claude's process in consistent, verifiable ways?" → yes, demonstrably. Whether process changes have value beyond these scenarios (e.g., on harder tasks where process structure prevents errors, or for reliability/consistency) is a separate question.

## Recommendation

Pivot to behavioral markers. See `docs/plans/2026-02-08-behavioral-markers-pivot.md`.
