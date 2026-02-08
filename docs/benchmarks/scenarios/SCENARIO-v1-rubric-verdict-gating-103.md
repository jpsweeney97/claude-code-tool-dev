# v1-rubric-verdict-gating-103: Threshold-based verdict with confounder-adjusted confidence

```yaml
id: v1-rubric-verdict-gating-103
title: Threshold-based verdict with confounder-adjusted confidence
skill_target: Apply explicit benchmark thresholds and confidence downgrade logic without overclaiming
skill_type: pattern
task_type: reporting
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Correctly computes improvement coverage from supplied scenario outcomes
  - Applies stated threshold rules to select YES/NO/INCONCLUSIVE
  - Separates Evidence from Interpretation as distinct sections
  - Includes explicit confidence downgrade based on confounder severity
  - Provides concrete "what would change the verdict" conditions
failure_modes_to_watch:
  - Mathematical mistakes in coverage or deltas
  - Verdict chosen without threshold logic
  - Confounders only mentioned narratively with no confidence impact
inputs:
  prompt: |
    You are scoring a benchmark run using these rules:
    - YES requires target improvement on >=70% of targeted scenarios, no high-severity regressions.
    - If discriminability is weak due to ceiling effects, verdict should be INCONCLUSIVE.
    - If placebo/irrelevant systematically outperform target on task-native outcomes, verdict should be NO or INCONCLUSIVE.

    Scenario summary:
    - 6 targeted scenarios total
    - target improved in 2 scenarios
    - no regressions >=2 points
    - 3 scenarios show ceiling effects (all conditions scored at max)
    - one proxy-gaming condition outperformed baseline in structural compliance but not in correctness
    - confounders: medium tool-usage divergence in 2 scenarios

    Output requirements:
    1) Section "Evidence" with explicit computed metrics.
    2) Section "Interpretation" with verdict and rationale.
    3) Section "Confidence" with:
       - base confidence (high/med/low)
       - downgrade reason(s)
       - final confidence (high/med/low)
    4) Section "Decision Triggers" with exactly 3 bullet points describing what new evidence would change the verdict.

    No extra sections.
notes:
  - This scenario targets v0 report limitations: over-coarse confidence handling and advisory confounder treatment.
  - Structural separation is required but insufficient without correct threshold math.
discriminability:
  estimate: medium
  criteria_analysis:
    - criterion: "Correctly computes improvement coverage from supplied scenario outcomes"
      baseline_likelihood: uncertain
      evidence: "Baseline typically performs simple arithmetic correctly, but mistakes increase when multiple threshold and confounder facts are integrated."
    - criterion: "Applies stated threshold rules to select YES/NO/INCONCLUSIVE"
      baseline_likelihood: unlikely
      evidence: "v0 reporting behavior showed tendency toward narrative framing over strict threshold gating; explicit rule application was not always enforced structurally."
    - criterion: "Separates Evidence from Interpretation as distinct sections"
      baseline_likelihood: likely
      evidence: "Baseline often follows section-heading instructions for report formatting."
    - criterion: "Includes explicit confidence downgrade based on confounder severity"
      baseline_likelihood: uncertain
      evidence: "v0 findings showed confounders were usually noted, but confidence demotion was inconsistent and often advisory rather than formal."
    - criterion: "Provides concrete 'what would change verdict' conditions"
      baseline_likelihood: uncertain
      evidence: "Baseline can provide next actions, but precise counterfactual trigger conditions are less consistently operationalized."
  redesign_needed: false
  redesign_notes: null
```
