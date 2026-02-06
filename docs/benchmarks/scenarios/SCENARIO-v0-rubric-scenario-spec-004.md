# v0-rubric-scenario-spec-004: Write a high-signal scenario spec (YAML-in-Markdown)

```yaml
id: v0-rubric-scenario-spec-004
title: Write a high-signal scenario spec (YAML-in-Markdown)
skill_target: Produce a scenario with clear oracle, success criteria, confounders
skill_type: pattern
task_type: writing
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Scenario includes all required fields from Section 5.1
  - Success criteria are checkable and not vague
failure_modes_to_watch:
  - Proxy gaming (adds fields but no real measurability)
inputs:
  prompt: |
    Draft ONE new benchmark scenario definition (YAML-in-Markdown) for this repo that would be a strong
    anchor scenario (objective oracle) and has clear success criteria and confounder notes.
```
