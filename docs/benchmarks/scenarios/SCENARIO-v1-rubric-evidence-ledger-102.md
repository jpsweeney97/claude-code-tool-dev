# v1-rubric-evidence-ledger-102: Evidence ledger with observation/inference calibration

```yaml
id: v1-rubric-evidence-ledger-102
title: Evidence ledger with observation/inference calibration
skill_target: Separate observation from inference and calibrate confidence when evidence conflicts
skill_type: reference
task_type: analysis
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Output includes exactly 5 claims in a claims ledger
  - Each claim is labeled Observation or Inference
  - Each claim cites at least one provided path/snippet
  - Conflicting evidence triggers confidence downgrade (<=0.6) with explanation
  - Final section includes exactly 3 next checks
failure_modes_to_watch:
  - Unlabeled or mis-labeled claims
  - Claims without evidence references
  - Overconfident conclusions despite explicit contradictions
inputs:
  prompt: |
    You are given the following snippets from a repository:

    [A] services/rate_limit.py
    - DEFAULT_LIMIT = 200
    - apply_limit(user) uses DEFAULT_LIMIT unless per-user override exists

    [B] config/prod.env
    - RATE_LIMIT_DEFAULT=150
    - RATE_LIMIT_BURST=20

    [C] docs/ops/rate-limit-rollout.md
    - "Phase 2 lowers default from 200 to 150 after Jan 15"
    - "Rollback restores default to 200"

    [D] incidents/INC-1427-summary.md
    - "Spike observed after Jan 20 deployment"
    - "Unclear whether limiter default changed in deployed artifact"

    Questions:
    1) Where is the effective default likely enforced today?
    2) Is there enough evidence to claim the Jan 20 spike was caused by a default-limit change?

    Output requirements:
    1) Provide a claims ledger with exactly 5 rows and columns:
       Claim | Type (Observation/Inference) | Evidence | Confidence (0.0-1.0) | Counter-evidence
    2) If evidence conflicts, confidence for affected claims must be <=0.6 and explain why.
    3) End with "Unknowns & Next Checks" containing exactly 3 concrete checks.

    Do not use web sources.
notes:
  - This scenario directly targets v0 reference/report ceiling effects by forcing conflict-aware calibration.
  - Confidence downgrade behavior is required, not optional.
```
