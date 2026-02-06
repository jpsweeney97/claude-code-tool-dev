# v0-rubric-exact-three-options-007: Provide exactly 3 options with trade-offs and a recommendation

```yaml
id: v0-rubric-exact-three-options-007
title: Provide exactly 3 options with trade-offs and a recommendation
skill_target: Enforce strict countable structure (exactly 3 options) without drifting into extra options
skill_type: discipline
task_type: decision
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Output contains exactly 3 options (no more, no less)
  - Each option has at least 1 strength and 1 weakness
  - A single recommendation is stated after the options
failure_modes_to_watch:
  - "Honorable mentions" (counts as non-compliant)
  - Nested sub-options that create ambiguous counts
inputs:
  prompt: |
    You need to choose an approach for a small internal tool that ingests Markdown docs and provides fast search.
    Constraints:
    - Team has strong TypeScript experience
    - Needs to run locally (no managed search service)
    - Needs to support incremental updates to the index

    Provide options and a recommendation.
notes:
  - This scenario is designed to test the benchmark's ability to detect strict-count discipline effects separately from correctness.
```
