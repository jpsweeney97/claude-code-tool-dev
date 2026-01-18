---
id: commands-frontmatter
topic: Command Frontmatter Schema
category: commands
tags: [frontmatter, yaml, schema, configuration]
requires: [commands-overview]
related_to: [commands-arguments]
official_docs: https://code.claude.com/en/slash-commands
---

# Command Frontmatter Schema

YAML frontmatter configures command behavior.

## Full Schema

```yaml
---
description: Brief description shown in slash menu (required)
argument-hint: <file> [options]     # Hint for expected arguments
model: claude-sonnet-4-20250514     # Model override
allowed-tools: Read, Glob, Grep     # Restrict available tools
disable-model-invocation: false     # Prevent Skill tool from calling this command
hooks:                               # Component-scoped hooks
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
          once: true                 # Run only once per session
---
```

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `description` | string | No | First line of prompt | Shown in slash menu and Skill tool |
| `argument-hint` | string | No | None | Hint shown for expected arguments (supports alternatives: `add [id] \| remove [id] \| list`) |
| `model` | string | No | Inherits from conversation | Override model for this command (see [Models overview](https://docs.claude.com/en/docs/about-claude/models/overview)) |
| `allowed-tools` | string | No | Inherits from conversation | Comma-separated tool whitelist |
| `disable-model-invocation` | boolean | No | `false` | Prevent Skill tool from invoking this command |
| `hooks` | object | No | None | Component-scoped hook definitions |

## Hook Options

When defining hooks in commands, these options are available:

| Option | Type | Description |
|--------|------|-------------|
| `once` | boolean | Run hook only once per session, then remove it |

Hooks defined in commands are **automatically cleaned up** when the command finishes executing.

See [hooks-overview](../hooks/hooks-overview.md) for complete hook configuration format.

## Positional Arguments Example

```markdown
---
argument-hint: [pr-number] [priority] [assignee]
description: Review pull request
---

Review PR #$1 with priority $2 and assign to $3.
Focus on security, performance, and code style.
```

## Key Points

- No fields are strictly required; `description` defaults to first line of prompt
- `allowed-tools` restricts what tools command can use
- Component-scoped hooks run only during command execution
- Model override useful for complex prompts needing Opus
