# Frontmatter Checklist

## Required Fields

- [MUST] `name` exists, is kebab-case, <=64 chars
- [MUST] `description` exists, <=1024 chars, single line

## Tool Declaration

- [MUST] `allowed-tools` lists all tools actually used by skill (if skill uses tools)
- [MUST] No placeholder values like `<tool1>` or `<tool2>` in final output
- [SHOULD] `allowed-tools` omitted entirely if skill uses no tools (not empty array)

## Invocation Control

- [SHOULD] `user-invocable` explicitly set if skill should appear in slash menu
- [SHOULD] `user-invocable: false` for skills only invoked programmatically

## Optional Metadata

- [SHOULD] `license` declared for redistributable skills
- [SHOULD] `metadata.version` follows semver (e.g., "1.0.0")

## Anti-patterns

- [SEMANTIC] `allowed-tools: []` (empty array) when skill clearly uses tools in Procedure
- [SEMANTIC] Placeholder values in any field (`<skill-name>`, `<brief description>`)
- [SEMANTIC] `description` that doesn't explain when to use the skill
- [SEMANTIC] Mismatch between `allowed-tools` and tools referenced in Procedure
