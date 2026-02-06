# v0-anchor-vitest-001: `claude-code-docs` unit tests pass after a targeted change

```yaml
id: v0-anchor-vitest-001
title: `claude-code-docs` unit tests pass after a targeted change
skill_target: Make a small, correct change without breaking tests
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
  - `npm -w packages/mcp-servers/claude-code-docs run build` passes
failure_modes_to_watch:
  - Unrelated edits across the package
  - Tool confounder (web usage despite no_web)
inputs:
  prompt: |
    In `packages/mcp-servers/claude-code-docs`, make a small, low-risk improvement:
    - Strengthen one existing test assertion OR
    - Add one additional assertion to an existing test case

    Constraints:
    - Do not change production logic in `src/` unless required by a clearly failing test.
    - Keep changes minimal and localized to `tests/` when possible.

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
    - Run: `npm -w packages/mcp-servers/claude-code-docs run build`
  files:
    - packages/mcp-servers/claude-code-docs/tests/
notes:
  - This is an anchor scenario because "pass/fail" is objective. It is not a skill-quality oracle by itself; it tests whether injected skills distort engineering behavior.
```
