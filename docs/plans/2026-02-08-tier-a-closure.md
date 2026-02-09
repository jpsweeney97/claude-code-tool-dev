# Tier A Closure: Behavioral Marker Measurement Project

**Date:** 2026-02-08
**Status:** Closed
**Prior decisions:** `docs/plans/2026-02-08-skill-evidence-tiers-decision.md`, `docs/plans/2026-02-08-behavioral-markers-pivot.md`
**Analysis:** `docs/benchmarks/runs/2026-02-09_v1-marker-exploration-101-103/exploratory-marker-analysis.md`

## Verdict

**Tier A is closed.** Skills reliably induce intended behavioral artifacts when the skill adds instructions orthogonal to the prompt. The measurement infrastructure (behavioral markers with binary detection) works. The general benchmark project concludes.

## Evidence Summary

### Scenario 102 (Reference Evidence Calibration) — Validated

3 markers, all with perfect separation on N=3 pairs (post-hoc derivation, same data):

| Marker | Target (3/3) | Baseline (3/3) |
|--------|:------------:|:--------------:|
| M1: Explicit row counting | 3/3 present | 0/3 present |
| M2: Confidence threshold verification | 3/3 present | 0/3 present |
| M3: Confidence downgrade summary | 3/3 present | 0/3 present |

Source: `docs/plans/2026-02-08-behavioral-markers-pivot.md`

### Scenario 101 (Constraint Ledger) — Exploratory

1 marker with separation on N=1 pair (post-hoc, exploratory):

| Marker | Target (1/1) | Baseline (1/1) |
|--------|:------------:|:--------------:|
| M101-1: Score–recommendation verification step | 1/1 present | 0/1 present |

Source: `docs/benchmarks/runs/2026-02-09_v1-marker-exploration-101-103/exploratory-marker-analysis.md`

### Scenario 103 (Verdict Gating) — Non-finding

No binary markers found. Both conditions converge because the prompt already specifies the output structure the skill reinforces. 5/5 skill instructions overlap with prompt requirements.

Source: same analysis document, "Prompt–skill overlap" table.

## Cross-Scenario Finding

Marker separation correlates with **prompt–skill orthogonality**: skills that add procedural requirements not in the prompt produce detectable artifacts; skills that reinforce prompt-specified structure do not. This is a measurement-instrument property, not a skill-quality judgment.

| Scenario | Orthogonality | Markers | Separation |
|----------|:-------------:|:-------:|:----------:|
| 101 | High | 1 | 1/1 vs 0/1 |
| 102 | High | 3 | 3/3 vs 0/3 |
| 103 | Low | 0 | N/A |

## What Was and Wasn't Done

The original Tier A plan (`docs/plans/2026-02-08-skill-evidence-tiers-decision.md`, "What Remains") listed 4 items:

| Item | Status | Notes |
|------|:------:|-------|
| Pre-register markers for 101/103 | Replaced | Prior sessions read outputs, so true pre-registration was impossible. Labeled exploratory instead. |
| Test markers on 101/103 pilot data | Done | M101-1 found for 101; 103 non-finding documented with causal explanation. |
| Build detection scripts with strict variants | Not done | Manual inspection sufficient at current scale (10 outputs). Scripts are warranted if marker detection is needed at higher N or for CI integration. |
| Validate on all existing data | Partially done | All 102 data (6 outputs) validated for M1–M3. 101 data (2 outputs) inspected for M101-1. 103 data (2 outputs) inspected, no markers found. |

**Deviation rationale:** The original plan assumed pre-registration was possible and that automated scripts were needed. Neither turned out to be true at this scale. The core question — "do behavioral markers generalize beyond 102?" — was answered: yes for 101 (with the orthogonality caveat), no for 103 (explained by prompt–skill overlap). Detection scripts would add automation but not new information.

## What This Closes

- **The measurement project.** 60+ runs across 4 phases (v0, v1 pilot, discriminability, behavioral markers) converged on a clear finding: skills change process, not outcomes at this difficulty. Behavioral markers detect the process change. The measurement question is answered.
- **The "do skills work?" question** is reframed with precision: skills induce behavioral compliance when they add orthogonal instructions. Whether that compliance is valuable is a design judgment, not a benchmark finding.
- **Tier A as the default evidence bar.** For future skills, Tier A means: define expected behavioral artifacts, verify they appear in target and not in baseline. No rubric scoring, no blinded evaluation, no elaborate infrastructure needed.

## What Remains Open

- **Tier B is parked, trigger-gated.** Decision triggers from `docs/plans/2026-02-08-skill-evidence-tiers-decision.md` still apply: higher-stakes use, quality claim needed, or compliance theater observed.
- **The orthogonality hypothesis is unvalidated.** It's a post-hoc pattern from 3 scenarios. It's useful as a design heuristic but shouldn't be treated as a law.
- **M101-1 is at N=1.** If scenario 101 marker evidence matters for a future decision, fresh runs would strengthen it.

## Project Trajectory

| Phase | Runs | Approach | Result |
|-------|:----:|----------|--------|
| v0 | 51 | Rubric scoring, automated | INCONCLUSIVE (ceiling, confounders) |
| v1 pilot | 6 | Rubric scoring, blinded human eval | FAIL (0/3 improvement) |
| Discriminability | 6 | Rubric scoring, blinded isolated eval | CAN'T DETECT (delta ≈ 0) |
| Behavioral markers | 0 new | Binary detection on existing outputs | **CLOSED — markers work on 2/3 scenarios** |
