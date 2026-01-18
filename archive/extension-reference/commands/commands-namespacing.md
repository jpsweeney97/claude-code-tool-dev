---
id: commands-namespacing
topic: Command Namespacing and Precedence
category: commands
tags: [commands, namespacing, precedence, organization]
requires: [commands-overview]
related_to: [commands-frontmatter]
official_docs: https://code.claude.com/en/slash-commands
---

# Command Namespacing and Precedence

Subdirectories organize commands and affect how conflicts are resolved.

## Subdirectory Organization

Commands in subdirectories show their path in the description:

| File Location | Command | Description |
|---------------|---------|-------------|
| `.claude/commands/test.md` | `/test` | (project) |
| `.claude/commands/frontend/test.md` | `/test` | (project:frontend) |
| `.claude/commands/backend/test.md` | `/test` | (project:backend) |
| `~/.claude/commands/test.md` | `/test` | (user) |

The subdirectory name appears after the scope indicator.

## Precedence Rules

When multiple commands share the same name:

### Project vs User

Project commands override user commands with the same name. The user command is silently ignored.

```
.claude/commands/deploy.md      ← Wins (project)
~/.claude/commands/deploy.md    ← Ignored (user)
```

### Same Scope, Different Subdirectories

Commands in different subdirectories can share names because the subdirectory appears in the description to distinguish them:

```
.claude/commands/frontend/test.md   → /test (project:frontend)
.claude/commands/backend/test.md    → /test (project:backend)
```

Both appear in `/help` with their distinguishing descriptions.

## Autocomplete Behavior

Slash command autocomplete works anywhere in your input, not just at the beginning. Type `/` at any position to see available commands.

When multiple commands match, autocomplete shows all options with their descriptions to help distinguish them.

## Key Points

- Subdirectory creates description suffix, not command prefix
- Project scope always wins over user scope
- Same-name commands differentiated by description
- `/help` shows all available commands with scope indicators
