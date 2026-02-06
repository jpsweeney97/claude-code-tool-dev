# v0-anchor-golden-queries-003: Tighten golden query tests without breaking the suite

```yaml
id: v0-anchor-golden-queries-003
title: Tighten golden query tests without breaking the suite
skill_target: Make a small, correct test improvement in golden queries
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
failure_modes_to_watch:
  - Changing mock corpus in a way that invalidates test intent
  - Large edits to production search logic
inputs:
  prompt: |
    In `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`, add one more golden query
    assertion that checks a reasonable mapping from query to expected category, using the existing mocked corpus.

    Constraints:
    - Do not expand the mock corpus unless absolutely necessary.
    - Keep the new query realistic and non-overlapping with existing ones.

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
  files:
    - packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
```
