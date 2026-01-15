---
description: Systematically optimize a plugin through 6 analytical lenses, producing a prioritized design document
argument-hint: "<plugin-path>"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - TodoWrite
  - AskUserQuestion
  - Skill
---

# Optimize Plugin Command

Invoke the optimizing-plugins skill to systematically improve a Claude Code plugin from "good" to "great."

## Arguments

- `$1` - Plugin path (required)

## Process

1. **Validate plugin path**
   - Verify path exists
   - Verify `.claude-plugin/plugin.json` exists
   - If invalid, report error and exit

2. **Invoke the skill**
   - Use the Skill tool to invoke `plugin-dev:optimizing-plugins`
   - Pass the plugin path as context

## Relationship to Audit

- **Audit** (`/plugin-dev:audit-plugin`) finds problems — "broken to working"
- **Optimize** (`/plugin-dev:optimize`) improves quality — "good to great"

Run audit first if unsure whether the plugin has structural issues.

## Example

```
/plugin-dev:optimize plugins/superpowers
```
