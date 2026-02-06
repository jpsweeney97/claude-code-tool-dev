# v0-rubric-controls-006: Draft control skill bodies that are safe and non-destructive

```yaml
id: v0-rubric-controls-006
title: Draft control skill bodies that are safe and non-destructive
skill_target: Produce clear placebo/irrelevant/harmful bodies that cannot be mistaken for "real skills"
skill_type: discipline
task_type: writing
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Control bodies are clearly defined and safe (no destructive actions)
  - Placebo is intentionally non-methodical
  - Harmful degrades outcomes without safety risk
failure_modes_to_watch:
  - Harmful instructions that could cause destructive actions
inputs:
  prompt: |
    Draft three control skill bodies (no frontmatter needed):
    - PLACEBO
    - IRRELEVANT (for code-change scenarios)
    - HARMFUL (non-destructive)

    Each must be short and clearly labeled.
```
