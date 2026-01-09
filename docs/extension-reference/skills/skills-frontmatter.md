---
id: skills-frontmatter
topic: Skill Frontmatter Schema
category: skills
tags: [frontmatter, yaml, schema, configuration]
requires: [skills-overview]
related_to: [skills-invocation, skills-context-fork]
official_docs: https://code.claude.com/en/skills
---

# Skill Frontmatter Schema

YAML frontmatter configures skill behavior, visibility, and tool access.

## Full Schema

```yaml
---
# Required
name: skill-name                    # Kebab-case identifier
description: One-line description   # Shown in slash menu, used for auto-discovery

# Optional metadata
license: MIT
metadata:
  version: "1.0.0"
  model: claude-opus-4-5-20251101   # Recommended model
  timelessness_score: 8             # Quality indicator 1-10

# Visibility controls
user-invocable: true                # Show in slash menu (default: true)
disable-model-invocation: false     # Prevent Skill tool from invoking (default: false)

# Tool restrictions
allowed-tools: Read, Glob, Grep, Bash, Write, Edit

# Context isolation
context: fork                       # Run in separate subagent context
agent: Explore                      # Which subagent type to use when forked

# Component-scoped hooks
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate.sh
  PostToolUse:
    - matcher: Write|Edit
      hooks:
        - type: command
          command: ./format.sh "$TOOL_INPUT"
---
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Kebab-case identifier |
| `description` | string | Yes | Shown in slash menu, used for auto-discovery |
| `license` | string | No | License type (e.g., MIT) |
| `metadata` | object | No | Version, model, quality indicators |
| `user-invocable` | boolean | No | Show in slash menu (default: true) |
| `disable-model-invocation` | boolean | No | Prevent Skill tool invocation (default: false) |
| `allowed-tools` | string | No | Comma-separated tool whitelist |
| `context` | string | No | Set to `fork` for isolation |
| `agent` | string | No | Subagent type when forked |
| `hooks` | object | No | Component-scoped hook definitions |

## Key Points

- `name` and `description` are required
- `allowed-tools` restricts what tools skill can use
- Component-scoped hooks run only during skill execution
- `context: fork` runs skill in separate subagent
