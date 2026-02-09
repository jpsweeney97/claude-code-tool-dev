# Pivot: Rubric Scoring → Behavioral Markers

**Date:** 2026-02-08
**Trigger:** Discriminability experiment verdict — under the current rubric and prompt difficulty, rubric scoring cannot detect skill effects (runs 2–3 delta = 0; run-1 delta = +1, plausibly evaluator-session drift)
**Analysis:** `docs/benchmarks/runs/2026-02-08_v1-discriminability-102/discriminability-analysis.md`

## Why Rubric Scoring Failed

Rubric scoring measures **outcome correctness** (are labels right? citations accurate? confidences calibrated?). Skills change **process** (explicit counting, verification sections, structured confidence downgrades). On the tasks tested — all within Claude's baseline capability range — Claude produces correct outcomes with or without process structure, so the rubric hits a ceiling at 20/20 for both conditions. This is a task-difficulty problem, not evidence that process changes never affect outcomes.

The evaluator saw the behavioral differences — described them in rationale text — but had no rubric mechanism to score them differently. Both conditions satisfy every criterion at the maximum level.

## What Behavioral Markers Are

Binary or countable signals in the output text that indicate specific skill-induced behaviors. Unlike rubric scores (which aggregate multiple quality dimensions into a single ordinal scale), behavioral markers are:

- **Binary:** present or absent — no subjective 0-4 judgment
- **Greppable:** detectable by pattern matching, not evaluator judgment
- **Process-focused:** measure how Claude worked, not whether it got the right answer
- **Cheap to evaluate:** no blinded evaluator session needed — a script or a single grep pass suffices

## Validated Markers for Scenario 102

From 6 run records (3 baseline, 3 target), these markers consistently distinguish conditions:

| Marker | Description | Target (3/3) | Baseline (3/3) | Detection method |
|--------|-------------|:------------:|:--------------:|------------------|
| **M1: Explicit row counting** | Output contains numbered enumeration of rows followed by a count confirmation (e.g., "1, 2, 3, 4, 5. Exactly 5 rows.") | 3/3 present | 0/3 present | Regex: `/\d+\.\s.*Exactly \d+ rows/s` or `/1,\s*2,\s*3,\s*4,\s*5/` |
| **M2: Confidence threshold verification** | Output contains explicit check that conflicted-claim confidences are ≤ 0.6 (e.g., "0.5 <= 0.6. Confirmed.") | 3/3 present | 0/3 present | Regex: `/<=?\s*0\.6.*[Cc]onfirmed/` or section heading match |
| **M3: Confidence downgrade summary** | Output contains a dedicated section or inline block summarizing all confidence downgrades with rationale | 2/3 present (run-2: standalone section; run-3: inline) | 0/3 present | Section heading match or structured downgrade block detection |

**Discriminability:** All three markers show perfect separation (3/3 vs 0/3) across N=3. This is the signal the rubric could not capture.

### Marker Variation Notes

- M1 and M2 are highly consistent across target runs (same pattern, minor wording variation)
- M3 varies in form: run-1 and run-2 have a standalone "Summary of Confidence Downgrades (Visibility Requirement)" section; run-3 embeds downgrades inline. A robust detector should check for both forms.
- No false positives in baselines — baselines handle confidence correctly but don't include explicit verification artifacts

## Measurement Approach

### Level 1: Binary Detection (Immediate)

For each run, detect presence/absence of each marker. Report as a feature vector:

```
run-1-target:  [M1=1, M2=1, M3=1]  → 3/3 markers
run-1-baseline: [M1=0, M2=0, M3=0]  → 0/3 markers
```

**Discriminability metric:** Proportion of markers that perfectly separate conditions. Currently 3/3 = 100%.

**Advantages:** Zero evaluator judgment. Fully automatable. Can run at any N without additional cost.

### Level 2: Marker Counting (Next)

For markers that can appear multiple times (e.g., M2 fires once per conflicted claim), count occurrences. This provides a richer signal than binary presence.

Example: M2 fires 3 times in a target run (once per conflicted claim) and 0 times in a baseline. The count captures thoroughness, not just presence.

### Level 3: Novel Marker Discovery (Future)

Run a diff-analysis between target and baseline outputs to discover markers not predicted by the skill body. This would reveal unexpected skill effects — behaviors the skill induces that weren't explicitly instructed.

## What This Measures (and Doesn't)

**Measures:** Whether the skill consistently changes Claude's observable process.
- "Does the skill make Claude count explicitly?" → Yes/No, with perfect separation.
- "Does the skill make Claude verify confidence thresholds?" → Yes/No, with perfect separation.

**Does not measure:** Whether those process changes improve output quality.
- The rubric experiment showed that output quality (correctness, calibration, citation precision) is the same with or without the skill on these tasks.
- Process changes may improve quality on harder tasks, or improve reliability/consistency — but that's a separate experiment.

**Honest framing:** Behavioral markers answer "does the skill change behavior?" not "does the skill help?" These are different questions. The first is a prerequisite for the second, and we now have a tool that can answer it.

## Risks and Mitigations

### R1: Overfitting markers to the observed sample

M1–M3 were derived from the same 6 run records they're validated against. Perfect separation on the derivation set doesn't guarantee separation on held-out data — the markers may be tuned to incidental patterns in these specific runs.

**Mitigation:** Pre-register markers before testing on new data.

**Artifact:** Write pre-registration to `docs/benchmarks/markers/prereg/<date>_<scenario>.md`. Each prereg file must contain: marker IDs, regex/detection definitions, expected separation (present in target / absent in baseline, or vice versa), and the git commit hash at time of freeze. The prereg is immutable after the freeze commit — revisions require a new file with a `_rev<N>` suffix and a note explaining why the original definitions didn't hold.

**Protocol:**
1. Define markers from scenario 102 data (done — M1, M2, M3 above; freeze point is the commit that adds this plan).
2. Before running detection on scenarios 101/103, write the prereg file with marker definitions and expected separation *first*, commit it, then test. If markers need revision after seeing new data, document the revision in a `_rev1` file and re-validate on a fresh run.
3. When generating new runs for any scenario, the prereg must already be committed — no post-hoc marker adjustment.

### R2: Goodharting (surface compliance without substance)

A model can emit "Exactly 5 rows. Confirmed." without actually counting, or print a confidence-threshold check section while applying thresholds to the wrong claims. Surface-pattern markers detect text, not correctness.

**Mitigation:** Include a small set of "non-trivial" markers that require internal consistency:
- **M1-strict:** The explicit count stated must match the actual number of rows in the output table. ("Exactly 5 rows" is only valid if the table has 5 rows.)
- **M2-strict:** Each threshold check must reference a claim that actually has conflicting evidence, and the stated confidence value must match the value in the claim table.
- **M3-strict:** The downgrade summary must cover all claims with conflicting evidence — not a subset.

These consistency checks turn marker detection from pure text matching into lightweight semantic verification. They're still automatable (parse the table, compare counts) but catch hollow compliance.

### R3: Contamination scan false positives

If naive text scans (e.g., `rg "baseline|target"`) are used to detect blinding leaks, scenario content can trigger false positives. Scenario 102's evidence set legitimately contains words like "target" (e.g., "Phase 2 target"). Contamination scans should use context-aware patterns that distinguish experimental labels from scenario content.

## Scope of This Pivot

### In scope
- Define behavioral markers for existing scenarios (102 first, then 101 and 103)
- Build detection scripts (grep/regex-based, no LLM needed)
- Run detection on existing run data (6 pilot outputs + 4 discriminability outputs = 10 outputs across all scenarios)
- Establish baseline separation rates

### Out of scope (for now)
- New scenario design
- Skill body modifications
- Quality-focused measurement (the rubric approach is parked, not abandoned — it may work on harder tasks)
- Statistical significance testing (with binary markers and perfect separation, N=3 is sufficient to establish the pattern; formal testing is needed if separation is imperfect)

## Next Steps

1. **Write detection scripts** for M1, M2, M3 (including strict variants) — regex + lightweight table parsing, operating on markdown run-record files
2. **Run on all existing 102 data** (pilot N=1 + discriminability N=2 new pairs = 3 pairs, 6 outputs)
3. **Pre-register markers for scenarios 101 and 103** — define markers and expected separation *before* running detection (per R1 mitigation)
4. **Run on pilot 101/103 data** — test pre-registered markers; document any revisions needed
5. **Decide whether marker-based measurement is sufficient** or whether harder tasks are needed to test quality effects

## Relationship to Prior Work

| Phase | Approach | Result | Learning |
|-------|----------|--------|----------|
| v0 (51 runs, 8 scenarios) | Rubric scoring, automated | INCONCLUSIVE | Ceiling effects, tool-usage confounders |
| v1 pilot (6 runs, 3 scenarios) | Rubric scoring, blinded human eval | FAIL (0/3 improvement) | Dimension coupling (101), ceiling (102/103) |
| Discriminability (6 runs, 1 scenario) | Rubric scoring, blinded isolated eval | CAN'T DETECT (mean delta +0.33) | Rubric can't detect differences at ceiling; task difficulty too low for outcome measurement |
| **Behavioral markers (this)** | **Binary/count detection, automated** | **Pending** | **Expected: perfect separation on 102** |

The progression shows: skills change process detectably, and outcome differences are undetectable on easy tasks. Whether process changes affect outcomes on harder tasks (where baseline Claude makes errors) is an open question — the experiments never tested it. Behavioral markers measure the process change that does occur.
