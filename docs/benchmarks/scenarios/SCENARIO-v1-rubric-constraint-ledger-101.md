# v1-rubric-constraint-ledger-101: Constraint-accountable recommendation with weighted scoring

```yaml
id: v1-rubric-constraint-ledger-101
title: Constraint-accountable recommendation with weighted scoring
skill_target: Maintain strict structure while reasoning over multiple explicit constraints
skill_type: discipline
task_type: decision
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Output contains exactly 3 options (no more, no less)
  - Each option includes at least 2 strengths and 2 weaknesses
  - Includes a weighted score table with weights summing to 100
  - Recommendation is consistent with the stated scoring and constraints
failure_modes_to_watch:
  - "Honorable mentions" or a hidden 4th option
  - Score table present but not used in final recommendation
  - Generic trade-offs that ignore prompt constraints
inputs:
  prompt: |
    You are selecting an architecture for a local Markdown search tool.

    Constraints:
    - Must run entirely local (no hosted services)
    - Team: 2 TypeScript engineers
    - MVP delivery window: 2 weeks
    - Must support incremental indexing
    - Must support rollback to previous index format in under 1 day
    - Memory budget: 800 MB at 50k documents

    Output requirements:
    1) Provide exactly 3 options.
    2) For each option, include:
       - short description (max 2 sentences)
       - 2 strengths
       - 2 weaknesses
       - risk level (low/med/high)
    3) Provide a weighted score table using these criteria:
       - latency performance
       - implementation effort
       - operational simplicity
       - rollback simplicity
       Weights must sum to 100.
    4) Recommend one option and justify in 3-5 sentences.
    5) Provide one fast-fail experiment for the recommended option.

    Do not include honorable mentions or extra options.
notes:
  - This is a broader successor to v0 exact-three-options-007.
  - It preserves count discipline while adding quantitative coherence checks.
discriminability:
  estimate: high
  criteria_analysis:
    - criterion: "Output contains exactly 3 options (no more, no less)"
      baseline_likelihood: unlikely
      evidence: "Benchmark v0 exact-three-options-007 baseline runs converged on 4 options (3/3 runs), indicating natural expansion drift without explicit discipline support."
    - criterion: "Each option includes at least 2 strengths and 2 weaknesses"
      baseline_likelihood: likely
      evidence: "Baseline Claude usually provides multi-point pros/cons when prompted for option trade-offs; this is generic quality behavior rather than skill-specific."
    - criterion: "Includes a weighted score table with weights summing to 100"
      baseline_likelihood: uncertain
      evidence: "Baseline often provides weighted tables, but exact arithmetic and consistency are error-prone under multi-constraint prompts."
    - criterion: "Recommendation is consistent with the stated scoring and constraints"
      baseline_likelihood: unlikely
      evidence: "Recommendation/score-table mismatch is a common failure mode when long-form option analysis and explicit constraints are combined."
  redesign_needed: false
  redesign_notes: null
```
