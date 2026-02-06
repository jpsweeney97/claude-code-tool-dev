# v0-anchor-frontmatter-002: Improve frontmatter parsing tests without breaking behavior

```yaml
id: v0-anchor-frontmatter-002
title: Improve frontmatter parsing tests without breaking behavior
skill_target: Make a targeted change in parsing-related tests and keep correctness
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
failure_modes_to_watch:
  - Broad refactor "because style"
  - Introducing flaky tests
inputs:
  prompt: |
    Improve coverage for frontmatter parsing by adding a small new test case in:
    - `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`

    The new test must:
    - Be deterministic (no network, no temp files required unless cleaned up)
    - Assert a specific behavior (not just "does not throw")

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
  files:
    - packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
```
