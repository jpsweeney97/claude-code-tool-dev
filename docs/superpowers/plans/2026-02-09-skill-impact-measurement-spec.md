# Skill Impact Measurement Spec

**Date:** 2026-02-09
**Status:** Draft
**Purpose:** Quantitative signal on whether a skill improves Claude's output versus baseline
**Builds on:** ADR-0001 (architecture), simulation framework v0.2.0 (methodology), stress test results (empirical calibration)

---

## 1. What This Is

A statistical measurement layer for the simulation-based skill assessment architecture. Produces a **quantitative go/no-go signal** — win rate with Wilson 95% confidence interval and sign test — for any skill.

### What It Adds to Existing Work

| Existing Component | Gap | This Spec Adds |
|---|---|---|
| ADR-0001 (`context: fork` + `assessment-runner`) | Validated architecture, no statistical framework | Statistical tests, sample size requirements, interpretation thresholds |
| Simulation framework v0.2.0 | Comprehensive methodology, qualitative delta evaluation | Quantitative scoring, automated rubric derivation, aggregate metrics |
| Stress test results (100+ runs) | Empirical findings about Claude behavior | Calibration data — which measurement approaches work and which hit ceilings |

### What It Doesn't Replace

- **Scenario generation:** Use the simulation framework's 8-step process (§3). This spec covers what happens *after* scenarios exist.
- **Gap analysis and iteration:** Use the simulation framework's fix cycle (§5). This spec covers *measurement*, not *improvement*.
- **Execution architecture:** Uses ADR-0001's `context: fork` + `assessment-runner`. No API harness.

### Relationship Diagram

```
simulation-framework v0.2.0    ADR-0001           stress-test-results
(methodology)                  (architecture)     (calibration)
     │                              │                    │
     │ scenario generation          │ execution          │ empirical
     │ gap analysis                 │ mechanism          │ constraints
     │ rubric design principles     │                    │
     └──────────────┬───────────────┘                    │
                    │                                    │
                    ▼                                    │
          ┌─────────────────────┐                        │
          │  THIS DOCUMENT      │◄───────────────────────┘
          │  Statistical layer  │
          │  Rubric derivation  │
          │  Interpretation     │
          └─────────────────────┘
```

---

## 2. Architecture

Uses the validated architecture from ADR-0001. No changes.

**Execution unit:** A dynamic skill with `context: fork` + `agent: assessment-runner`.

**Baseline run:** Skill file contains scenario task only.
**Test run:** Skill file contains target skill content + scenario task.
**Control run:** Skill file contains control body + scenario task.

Skill naming: `scenario-{topic}-{random-suffix}` (neutral IDs prevent observer effect; validated in stress tests).

Reference: ADR-0001 "Skill File Templates" for exact YAML structure.

---

## 3. Pre-Flight: Before Running Anything

Two pre-flight steps prevent wasted runs. Both must pass before executing scenarios.

### 3.1 Discriminability Verification

**Problem:** Baseline Claude is already competent. If all success criteria are satisfied without the skill, the measurement produces noise regardless of sample size.

**Evidence:** Benchmark v0 found 5 of 6 comparisons showed zero delta due to ceiling effects (simulation framework §6.6).

**Procedure:**

For each scenario in the task suite:

1. List all success criteria (must_do, must_not_do, rubric dimensions).
2. For each criterion, estimate: "Would baseline Claude satisfy this without the skill?"
   - **likely** (>70%): Baseline naturally does this.
   - **uncertain** (30-70%): Might or might not.
   - **unlikely** (<30%): Baseline would not produce this.
3. Classify scenario discriminability:
   - All criteria likely → **LOW** (ceiling effect expected)
   - ≥1 criterion unlikely → **MEDIUM**
   - ≥2 criteria unlikely AND those criteria map to specific skill instructions → **HIGH**

**Gate:** Suite must contain ≥2 scenarios with MEDIUM or HIGH discriminability. If fewer, redesign scenarios before proceeding.

**Redesign strategies:** See simulation framework §6.6 "Redesign Strategies" table.

### 3.2 Rubric Derivation

**Problem:** Generic quality dimensions (correctness, completeness, structure, specificity, appropriateness) produce identical scores for baseline and treatment because baseline Claude is already good at these.

**Evidence:** Stress test Phase 1.2 — boolean/structural proxies derived from specific skill instructions produced categorical shifts (0%→100%); generic quality proxies showed no delta.

**The Skill-Dimension Alignment Principle:** Rubric dimensions discriminate when they measure the specific behavioral change the skill intends (simulation framework §6.7).

**Rubric derivation procedure:**

For a given target skill:

```
STEP 1: Extract key instructions from the skill
  Read the skill. Identify 3-7 instructions that produce
  observable output differences. Use the simulation framework's
  instruction→behavior mapping (§3.6) if needed.

STEP 2: For each instruction, derive a rubric dimension
  Ask: "What would I observe in the output that indicates
  this instruction was followed?"

  Classify each dimension:
  - Structural: countable, algorithmic (e.g., "exactly 3 options")
  - Behavioral: observable action (e.g., "reads file before editing")
  - Qualitative: judgment-based (e.g., "well-organized")

STEP 3: Ensure ≥1 structural or behavioral dimension
  This is the "discriminability anchor" — the dimension most
  likely to show a delta. Must map to a specific skill instruction
  AND target a criterion where baseline likelihood is "unlikely"
  (from §3.1).

STEP 4: Add 1-2 generic quality dimensions as safety net
  These catch catastrophic failures but are not expected to
  discriminate. Examples: task completion, factual accuracy.

STEP 5: Set scoring scale
  - Structural: 0-2 (absent / partial / full)
  - Behavioral: 0-2 or 0-3
  - Qualitative: 0-3 or 0-4
  - Total range: ≥8 points for meaningful spread
```

**Output:** A per-skill rubric with 4-7 dimensions, each with:
- Name
- Type (structural / behavioral / qualitative)
- Source instruction in the skill
- Scoring levels with concrete descriptions
- Whether it serves as the discriminability anchor

**Anti-patterns:** See simulation framework §6.7 "Anti-Patterns" table.

**Example — rubric for `writing-principles` skill:**

| Dimension | Type | Source Instruction | Scale | Anchor? |
|---|---|---|---|---|
| Scope section present | Structural | P5: State Boundaries | 0-2 | Yes |
| Preconditions declared | Structural | P8: Declare Preconditions | 0-2 | Yes |
| Vague term count | Structural | P1: Be Specific | 0-3 (0=many, 3=none) | No |
| Examples per rule | Structural | P3: Show Examples | 0-2 | No |
| Self-check performed | Behavioral | Self-check procedure | 0-2 | Yes |
| Task completion | Qualitative | (generic) | 0-3 | No |

This rubric was validated in stress test Phase 1.2: the structural/behavioral dimensions produced categorical shifts while generic quality proxies didn't move.

---

## 4. Task Suite Design

### 4.1 Three-Tier Taxonomy

| Tier | Purpose | Proportion (of 17 tasks) | What It Tests |
|---|---|---|---|
| **Tier 1: Core domain** | Tasks the skill was designed for | 9/17 | Does the skill help where it should? |
| **Tier 2: Edge cases** | Ambiguous, underspecified, adversarial | 5/17 | Does the skill degrade gracefully? |
| **Tier 3: Out-of-scope** | Tasks adjacent to but outside the skill's domain | 3/17 | Does the skill cause harm when misapplied? |

### 4.2 Minimum Suite Size

**17 tasks per suite** (9 Tier 1, 5 Tier 2, 3 Tier 3).

**Confirmatory holdout (recommended):** Build two independent suites (A = main, B = held-out confirmatory) during suite construction. Only execute suite B if suite A is suggestive (see §6.5).

Rationale: With up to 17 paired comparisons (N_eff = 17 when there are no ties; ties excluded per §6.1), a one-tailed sign test detects meaningful effects:
- 13+ wins out of 17 → p = 0.025 (significant at 0.05)
- 12 wins out of 17 → p = 0.072 (suggestive)

The bump from 15 to 17 serves two purposes: (a) Tier 3 increases from 2 to 3 tasks, reducing noise on harm detection; (b) the significance boundary shifts from 80% (12/15) to 76.5% (13/17), providing finer granularity in the "suggestive" zone.

Below 15, variance swamps signal. Above 20, diminishing returns unless effect size is small.

### 4.3 Task Construction Rules

1. **Each task must have rubric anchoring.** At minimum, the discriminability anchor dimension must have a clear expected score for both baseline and treatment.

2. **Tasks must vary in complexity.** Include simple (single-step), moderate (multi-step), and complex (multi-constraint) tasks. Stress tests (B3) showed this doesn't affect *compliance* but does affect *output depth*.

3. **Include ≥2 calibration tasks** where you know the expected outcome. These validate the rubric isn't broken.

4. **Tier 2 tasks should draw from the simulation framework's adversarial probe library** (§7.4). For discipline skills: shortcut temptation, rationalization, gate bypass. For pattern skills: template mismatch, anti-pattern overlap.

5. **Tier 3 tasks should be plausibly related but out of scope.** A writing-principles skill's Tier 3 tasks might include "write a Python function" or "debug this error" — tasks where the skill could over-format or add unnecessary structure.

### 4.4 Scenario Generation

Use the simulation framework's 8-step process (§3.1-3.9) for Tier 1 and Tier 2 tasks. For Tier 3, generate tasks in adjacent domains where the skill could plausibly activate but shouldn't help.

---

## 5. Execution Protocol

### 5.1 Per-Task Execution

For each task in the suite, execute 3 runs per condition:

```
FOR EACH task T:
  FOR i IN 1..3:
    baseline_i = execute(scenario=T, skill=none)
    test_i     = execute(scenario=T, skill=target)
    IF include_placebo:
      placebo_i  = execute(scenario=T, skill=placebo)
```

`include_placebo` (and the resulting `primary_comparator`) is determined by the instruction-sensitivity check in §5.2.

Each `execute()` creates a dynamic skill file with `context: fork` + `agent: assessment-runner`, invokes it via the Skill tool, and captures the output.

**Why 3 runs, not 1:** Stress tests showed format/structural variance is near-zero but content variance exists. 3 runs per condition captures the variance while keeping cost bounded. Aggregate to a task-level win/loss via majority vote across run-level comparisons (§5.3).

**Why not 5:** The stress tests used 5 runs to characterize variance distributions. For measurement (not characterization), 3 runs is sufficient — the variance is already known to be low.

### 5.2 Control Conditions

Run controls **before** the full assessment as a calibration gate.

| Control | Body | Expected Result |
|---|---|---|
| **Harmful** | Instruction that degrades task capability (e.g., "Respond in exactly 15 words") | Negative delta vs baseline. If neutral → measurement is broken. |
| **Placebo** | Generic non-specific instruction (e.g., "Be careful and do your best work") | Ideally neutral vs baseline. If positive → **instruction-presence effect**; use placebo as the primary comparator (see instruction-sensitivity check below). |

**Control execution:**
- Select 2 representative Tier 1 tasks for controls (**calibration set; not part of the 17-task suite**)
- Run each control type × each task × 3 replications (same as test/baseline)
- Total: 2 control types × 2 tasks × 3 runs = 12 additional runs
- Run controls first, before committing to the full 17-task suite

**Sensitivity gate:** If the harmful control does NOT produce a negative delta on at least 1 of 2 tasks, stop. The rubric cannot detect known-bad behavior, so it cannot be trusted to detect skill impact. Diagnose and fix before proceeding.

**Instruction-sensitivity check (placebo):** If the placebo control outperforms baseline on either calibration task, do **not** mark the measurement invalid. Instead:
- Mark the evaluation as **instruction-sensitive**
- Include a placebo condition in the full 17-task suite
- Treat **test vs placebo** as the **primary** sign test (baseline becomes descriptive context)

If placebo is neutral vs baseline on both calibration tasks, skip the placebo condition for the full suite and keep **test vs baseline** as the primary comparison.

Reference: Simulation framework §4.5-4.6 for control taxonomy, configuration, and interpretation.

### 5.3 Evaluation

For each task, score all outputs (baseline and test, and placebo if included; all runs) using the per-skill rubric (§3.2).

**Who scores:** The orchestrating Claude instance scores outputs using the rubric. This keeps evaluation in-session where process traces and tool usage are visible, not just final output.

**Blinding protocol:** To reduce confirmation bias, anonymize outputs before scoring:

1. Assign each output a random ID (e.g., `output-7k`, `output-3m`). Do not use IDs that reveal condition (no `baseline-1`, `test-2`, `placebo-3`).
2. Randomize presentation order within each task (shuffle outputs). Record the order.
3. Score each output independently against the rubric. Do not score them side-by-side.
4. After all outputs for a task are scored, de-anonymize and compute the winner.

**Scoring procedure:**

```
FOR EACH task T:
  outputs = collect_and_anonymize(baseline_runs + test_runs + (placebo_runs if include_placebo else []))
  shuffle(outputs)

  FOR EACH output in outputs:
    scores[output.id] = apply_rubric(rubric, output)

  de_anonymize(scores)

  comparator_runs = (placebo_runs if primary_comparator == "placebo" else baseline_runs)

  FOR EACH run pair (comparator_i, test_i):
    winner_i = compare(scores[comparator_i], scores[test_i])

  task_winner = majority_vote(winner_1, winner_2, winner_3)
  # Ties: see §6.1
```

---

## 6. Statistical Analysis

### 6.1 Primary Metric: Win Rate

```
win_rate = (tasks won by treatment) / (tasks won + tasks lost)
```

For the **primary** win rate and sign test, define the comparator as:
- **Baseline** by default
- **Placebo** if the instruction-sensitivity check (§5.2) detects an instruction-presence effect

A task is "won" when the treatment's majority-vote rubric score exceeds the **primary comparator's**. A task is "lost" when the primary comparator exceeds treatment.

**Tie handling:** When treatment and the primary comparator have equal majority-vote scores, the task is a **tie**. Ties are excluded from both numerator and denominator. The effective sample size N_eff = (wins + losses) is used for all statistical tests.

Report ties separately: a high tie rate (>30%) indicates the rubric lacks discriminative power — revisit dimension design (§3.2).

**Confidence interval:** Report Wilson 95% CI on win rate. For reference:

| Outcome | Win Rate | Wilson 95% CI |
|---|---|---|
| 13/17 wins, 0 ties | 76.5% | [52.7%, 90.4%] |
| 12/15 wins, 2 ties | 80.0% | [54.8%, 93.0%] |
| 11/15 wins, 2 ties | 73.3% | [48.0%, 89.1%] |
| 9/15 wins, 2 ties | 60.0% | [35.7%, 80.2%] |

### 6.2 Statistical Test: Sign Test (Directional)

Non-parametric test on paired outcomes. Under null hypothesis (no effect), wins ~ Binomial(N_eff, 0.5).

Report both tails:
- **p_help:** one-tailed p-value for treatment beating the primary comparator
- **p_harm:** one-tailed p-value for treatment being worse than the primary comparator (safety signal)

If you need a single two-sided p-value ("effect in either direction"), report:
```
p_two_sided = min(1, 2 * min(p_help, p_harm))
```

**Threshold note:** If you intend to make symmetric statistical claims in either direction ("clearly helps" *or* "harmful"), use **p_two_sided < 0.05** (equivalently p_help < 0.025 or p_harm < 0.025). This spec treats **p_help** as the primary shipping signal; **p_harm** is a safety signal.

The tables below show **p_help** thresholds for the positive direction.

For N_eff = 17 (no ties):

| Wins | Win Rate | p_help | Interpretation |
|---|---|---|---|
| 13+ | 76.5% | 0.025 | Significant (p < 0.05) |
| 12 | 70.6% | 0.072 | Suggestive |
| 11 | 64.7% | 0.166 | Not significant |

For N_eff = 15 (2 ties excluded):

| Wins | Win Rate | p_help | Interpretation |
|---|---|---|---|
| 12+ | 80.0% | 0.018 | Significant (p < 0.05) |
| 11 | 73.3% | 0.059 | Suggestive |
| 10 | 66.7% | 0.151 | Not significant |

For N_eff = 13 (4 ties excluded):

| Wins | Win Rate | p_help | Interpretation |
|---|---|---|---|
| 10+ | 76.9% | 0.046 | Significant (p < 0.05) |
| 9 | 69.2% | 0.133 | Not significant |

**Rule:** If N_eff < 12, the assessment has insufficient power. Report "inconclusive — too many ties" and redesign the rubric.

### 6.3 Secondary Metrics

**Per-dimension deltas:** For each rubric dimension, compute mean score difference (test - baseline) across all tasks. If the placebo condition is included (§5.2), also compute (test - placebo). This diagnoses *what* the skill is doing.

Example output:
```
Scope section:    +1.8  (0.1 baseline → 1.9 test)  ← skill's primary effect
Preconditions:    +1.5  (0.2 baseline → 1.7 test)  ← strong secondary effect
Vague terms:      +0.8  (1.5 baseline → 2.3 test)  ← moderate improvement
Examples:         +0.2  (2.1 baseline → 2.3 test)  ← ceiling effect
Task completion:  +0.0  (2.8 baseline → 2.8 test)  ← no difference (expected)
```

**Per-tier breakdown:** Win rate computed separately for Tier 1 (9 tasks), Tier 2 (5 tasks), and Tier 3 (3 tasks). Tier-level win rates are descriptive — only the overall sign test has statistical power.

| Pattern | Interpretation |
|---|---|
| Tier 1 high, Tier 3 no losses | Skill is well-scoped — helps its domain, doesn't hurt others |
| Tier 1 high, Tier 3 any losses | Potential scoping problem — inspect losses per §7.2 Tier-3 harm check |
| Tier 1 low, any | Skill is broken at its core purpose |
| Tier 2 low, Tier 1 high | Skill is fragile — works in clean cases, fails on edge cases |

**Per-dimension Wilcoxon signed-rank test:** For dimensions with enough range (≥3 levels), run Wilcoxon on paired score differences. This tests whether a specific dimension's improvement is statistically significant, not just directionally positive.

### 6.4 Failure Mode Categorization

For every task the skill lost (treatment scored lower than the **primary comparator**), manually inspect and categorize:

| Category | Description | Example |
|---|---|---|
| **Over-applied** | Skill instructions followed but inappropriate for this task | Adding scope boundaries to a simple debugging task |
| **Hallucinated structure** | Skill induced structure that doesn't fit | Forcing a 3-options format on a yes/no question |
| **Ignored user intent** | Skill instructions override what was actually asked | Verbose analysis when user asked for a quick fix |
| **Bloat** | Skill added content that dilutes rather than helps | Unnecessary preamble, over-formatting |
| **Misinterpreted** | Skill instruction followed incorrectly | "Be specific" interpreted as "add more words" |

Track failure mode frequency across the suite. If one mode dominates, the skill has a systematic problem addressable through the simulation framework's gap analysis (§5).

### 6.5 Confirmatory Runs (Avoid Optional Stopping)

If you decide to spend more compute based on observed p-values, **do not** simply add more tasks and re-run the same p-value threshold on the pooled dataset. That creates an optional-stopping problem and inflates false positives.

**Recommended approach: screen → confirm using a held-out task suite**

1. During task suite construction (§4), generate **two** independent 17-task suites (A = main, B = holdout) with the same tier proportions and rubric anchoring.
2. Run suite A and compute the primary sign test (vs the primary comparator from §5.2).
3. If suite A is **suggestive** (0.05 ≤ p_help < 0.10) *and* calibration gates pass, run suite B.
4. Make the ship/no-ship call based on suite B **alone** at p_help < 0.05 (same analysis and decision rules). Suite A is reported as screening context.

To control cost, suite B only needs the **primary comparison** conditions (test + primary comparator). Running baseline in suite B is optional descriptive context, not required for the confirmatory decision.

**Rule:** If suite A is "inconclusive — too many ties" (N_eff < 12), do not run suite B; redesign the rubric and tasks first.

---

## 7. Reporting

### 7.1 Assessment Report Structure

```markdown
# Skill Impact Assessment: {skill name}

## Summary
- Win rate: X% (Y wins / Z non-tied tasks), Wilson 95% CI: [lo%, hi%]
- Primary comparison: test vs {baseline|placebo}
- Ties: T/17 tasks (tie rate: T%)
- Sign test: p_help = {value} ({significant|suggestive|not significant|inconclusive}); p_harm = {value} (optional)
- Holdout (if run): win rate = X%; p_help = {value}; p_harm = {value} (optional); verdict = {clearly helps | no incremental value | no effect | harmful | inconclusive}
- Tier 1: X/9 | Tier 2: X/5 | Tier 3: X/3
- Verdict: {clearly helps | suggestive | no incremental value | no effect | harmful | measurement invalid | inconclusive}

## Rubric
{Per-skill rubric with dimensions, types, scales — from §3.2}

## Per-Dimension Deltas
{Table of mean score differences per dimension (test - baseline; and test - placebo if applicable)}

## Per-Tier Breakdown
{Win rates by tier with task-level detail}

## Control Results
- Harmful control: {degraded as expected | DID NOT DEGRADE — results unreliable}
- Placebo control: {neutral as expected | improved baseline — instruction-sensitivity detected}

## Failure Analysis
{For each task lost: which task, which tier, failure mode category, brief explanation}

## Discriminability Notes
{Any tasks that showed zero delta — ceiling effect or genuine no-effect?}

## Raw Data
{Task-by-task scores, all runs, presentation order}
```

### 7.2 Decision Rules

The sign test is the **primary criterion**. Win rate is descriptive context. This avoids threshold-alignment problems where a win rate exceeds a percentage boundary but the sign test doesn't reach significance (e.g., 11/15 = 73% but p = 0.059).

| Verdict | Primary Criterion | Supporting Evidence | Action |
|---|---|---|---|
| **Clearly helps** | Sign test p_help < 0.05 vs the primary comparator; sensitivity gate passes | Win rate typically >75% | Ship the skill |
| **Suggestive** | Sign test 0.05 ≤ p_help < 0.10 vs the primary comparator; sensitivity gate passes | Win rate typically 65-75% | Run a confirmatory held-out suite (§6.5). Do not ship as "clearly helps" until confirmed. |
| **No incremental value** | Primary comparator = placebo, and sign test p_help ≥ 0.10 vs placebo | Treatment may still beat baseline (instruction-presence effect) | Do not ship as a skill improvement; either accept placebo/generic guidance or redesign the skill for incremental impact. |
| **No effect** | Primary comparator = baseline, and sign test p_help ≥ 0.10 vs baseline | Win rate typically 50-65% | Diagnose via failure analysis. Fix or retire. |
| **Harmful** | Sign test p_harm < 0.05 vs the primary comparator | Win rate < 40% | Do not ship. Diagnose and fix via simulation framework §5. |
| **Measurement invalid** | Harmful control didn't degrade (sensitivity gate failed) | N/A | Re-derive rubric. Current results are uninterpretable. |
| **Inconclusive** | N_eff < 12 (too many ties) | Tie rate >30% | Redesign rubric for better discriminative power. |

**Tier-3 harm check (qualitative, not statistical):** With 3 Tier-3 tasks, quantitative thresholds are underpowered. Instead: **any Tier-3 loss requires manual inspection.** Categorize each loss using the failure mode taxonomy (§6.4). If any loss is categorized as "over-applied" or "hallucinated structure," the skill has a scoping problem that must be addressed before shipping — even if the overall verdict is "clearly helps."

### 7.3 Reproducibility Helper

Use `scripts/skill_impact_stats` to compute report-ready statistics from `{wins, losses, ties}`:

```bash
scripts/skill_impact_stats --wins 13 --losses 4 --ties 0
scripts/skill_impact_stats --wins 12 --losses 3 --ties 2 --format json
scripts/skill_impact_stats --wins 13 --losses 4 --ties 0 --report-lines --primary-comparison baseline --tier1-result 8/9 --tier2-result 4/5 --tier3-result 2/3
```

The helper outputs:
- `p_help`, `p_harm`, and `p_two_sided`
- Win rate and Wilson confidence interval
- N_eff-derived sign-test thresholds for significant/suggestive help and harm
- Warning when `N_eff < 12` (inconclusive risk)
- Optional paste-ready `## Summary` bullet lines via `--report-lines` (including comparator, tiers, and inferred verdict)

---

## 8. Cost Model

### Per-Skill Assessment

| Component | Runs | Tokens (est.) |
|---|---|---|
| Control calibration (2 tasks × 2 types × 3 runs) | 12 | ~120K |
| Control baselines (2 tasks × 3 runs) | 6 | ~60K |
| 17 tasks × 3 baseline runs | 51 | ~510K |
| 17 tasks × 3 test runs | 51 | ~510K |
| Scoring (rubric application) | — | ~60K |
| **Total** | 120 runs | **~1.26M tokens** |

ADR-0001 estimated ~675K tokens for a full assessment. This spec's 3-runs-per-condition design with expanded controls roughly doubles that.

**Optional add-ons (calibration-triggered):**
- If the instruction-sensitivity check triggers (§5.2), add full-suite placebo runs: 17 tasks × 3 placebo runs = 51 additional runs (~+510K tokens, plus scoring overhead).
- If you run a confirmatory held-out suite (§6.5), budget an additional 17-task execution of the **primary comparison** (test + primary comparator), plus scoring (~+1M tokens order of magnitude).

### Time

At ~30 seconds per forked skill execution, 120 runs ≈ 60 minutes of execution time. Parallelizable to ~20 minutes using 6 concurrent background runs (Task tool with `run_in_background: true`).

Control calibration runs first (~3 minutes parallelized). If controls fail, the remaining 102 runs are not executed — saving ~85% of the budget on broken rubrics.

---

## 9. Implementation Sequence

| Step | Description | Depends On |
|---|---|---|
| 1 | **Rubric derivation** — Given a target skill, produce a per-skill rubric | Target skill exists |
| 2 | **Task suite construction** — Two independent 17-task suites (A=main, B=held-out confirmatory) across 3 tiers with rubric anchoring | Rubric (step 1), simulation framework §3 for generation |
| 3 | **Discriminability verification** — Estimate and gate on discriminability | Task suite (step 2) |
| 4 | **Control calibration** — Run harmful + placebo controls on 2 calibration tasks; gate on sensitivity and decide the primary comparator | Rubric (step 1), architecture from ADR-0001 |
| 5 | **Execution** — Run baseline and test for all 17 tasks (and placebo if instruction-sensitive) | Calibration gates passed (step 4) |
| 6 | **Scoring** — Apply rubric to all outputs with blinding protocol | Rubric (step 1), outputs (step 5) |
| 7 | **Analysis** — Compute win rate, Wilson CI, sign test, per-dimension deltas, failure modes | Scores (step 6) |
| 8 | **Confirmatory holdout (optional)** — If suite A is suggestive, run held-out suite B for the **primary comparison** (test + primary comparator) per §6.5, then score and analyze | Suggestive result (step 7), holdout suite exists (step 2) |
| 9 | **Report** — Produce assessment report with verdict | Analysis (step 7) and (if run) confirmatory results (step 8) |

Steps 1-3 are pre-flight (no runs consumed). Step 4 is calibration (~18 runs). Steps 5-7 are the main execution and analysis (~102 runs; +51 if placebo is included). Step 8 is optional confirmatory execution (order-of-magnitude +~102 runs). If step 4 fails, steps 5-8 are skipped and the report verdict is "measurement invalid."

Steps 1-3 could be automated as a skill. Steps 4-9 could be orchestrated by the `improving-skills` skill or a dedicated `measure-skill` skill.

---

## 10. Known Limitations

### Inherited from Simulation Framework

| Limitation | Impact | Mitigation |
|---|---|---|
| **Ceiling effects** | Baseline already passes many criteria | Discriminability verification (§3.1) gates on this |
| **Oracle problem** | Claude judges Claude | Skill-aligned rubrics with structural dimensions reduce subjectivity |
| **Single-session** | Can't measure multi-session or cumulative effects | Out of scope; acknowledged |
| **Skill interactions** | Testing in isolation misses co-loading conflicts | Out of scope; acknowledged |

### Specific to This Spec

| Limitation | Impact | Mitigation |
|---|---|---|
| **Rubric derivation is judgment-dependent** | Different rubrics for the same skill could produce different verdicts | Rubric validation checklist (simulation §6.7); calibration tasks catch broken rubrics |
| **3 runs may miss rare variance** | If a behavior occurs in 20% of runs, 3 runs might miss it | Stress tests showed most variance is LOW; 3 runs captures majority-vote reliably. Increase to 5 if results are borderline. |
| **Win rate loses nuance** | 60% win rate could be "marginally better everywhere" or "dramatically better on some, worse on others" | Per-tier and per-dimension breakdowns required alongside win rate |
| **No longitudinal tracking** | Can't detect skill drift over model updates | Future work: re-run assessment after model changes |

### What the Stress Tests Tell Us to Watch For

| Finding | Implication for Measurement |
|---|---|
| Ambiguity ≠ Variance (insight #9) | Don't assume vague skill instructions cause inconsistent results. The model has stable defaults. If you see variance, it's signal — investigate. |
| Content > Format (insight #13) | Skills with format constraints (word limits, section counts) may show lower compliance than skills with content constraints. This is the model's priority hierarchy, not a measurement artifact. |
| Helpfulness > Compliance (insight #16) | If the skill's instructions conflict with helpfulness, the model may override. This reduces treatment win rate but is real behavior, not measurement error. |
| Baseline is already comprehensive (insight #3) | Count-based proxies (example count, caveat count) often show small deltas due to ceiling effects. Boolean proxies (section present/absent) are more reliable. Prefer boolean over count dimensions in rubrics. |
| Instruction density controls verbosity (insight #20) | Skill instruction style affects output style. A densely-written skill will produce longer outputs. Length differences between baseline and treatment are a style effect, not necessarily a quality effect. |

---

## 11. Relationship to Other Documents

| Document | Role | This Spec References |
|---|---|---|
| `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` | Execution architecture | §2 (architecture), §5.1 (execution) |
| `docs/frameworks/simulation-based-skill-assessment_v0.2.0.md` | Methodology | §3.1 (discriminability), §3.2 (rubric design), §4.4 (scenario generation), §5.2 (controls) |
| `docs/plans/2026-02-05-architecture-stress-test-results.md` | Empirical calibration | §3.2 (rubric evidence), §10 (watch-fors) |

This spec does NOT supersede any of the above. It adds a statistical measurement layer on top of the existing methodology and architecture.

---

## Changelog

| Date | Change |
|---|---|
| 2026-02-09 | Initial draft — synthesizes proposed evaluation framework with existing simulation architecture, stress test findings, and ADR-0001 |
| 2026-02-09 | Revision: fixed sign-test math (one-tailed throughout); added tie policy and effective N; added Wilson 95% CI; bumped suite from 15→17 tasks (Tier 3: 2→3); made sign test primary verdict criterion to close threshold gap; strengthened controls (3× replication, 2 tasks each, run-first calibration gate); added blinding protocol for scoring; made Tier-3 harm check qualitative |
| 2026-02-09 | Revision: reframed placebo as an instruction-sensitivity signal and (when triggered) the primary comparator; clarified p_help/p_harm reporting and two-sided mapping; replaced "add more tasks" with a held-out confirmatory suite to avoid optional stopping; updated reporting/cost/sequence accordingly |
| 2026-02-09 | Revision: added `scripts/skill_impact_stats` helper and report integration for reproducible p-values, Wilson CI, and N_eff-specific thresholds from `{wins, losses, ties}` |
| 2026-02-09 | Revision: added `--report-lines` summary mode to `scripts/skill_impact_stats` for paste-ready `## Summary` bullets with comparator, tiers, optional holdout, and inferred verdict |
