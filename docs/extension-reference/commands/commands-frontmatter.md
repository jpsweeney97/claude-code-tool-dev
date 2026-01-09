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
hooks:                               # Component-scoped hooks
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
---
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Shown in slash menu and Skill tool |
| `argument-hint` | string | No | Hint shown for expected arguments |
| `model` | string | No | Override model for this command |
| `allowed-tools` | string | No | Comma-separated tool whitelist |
| `hooks` | object | No | Component-scoped hook definitions |

## Key Points

- Only `description` is required
- `allowed-tools` restricts what tools command can use
- Component-scoped hooks run only during command execution
- Model override useful for complex prompts needing Opus
