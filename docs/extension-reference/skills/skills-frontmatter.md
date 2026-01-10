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

# Model override
model: claude-sonnet-4-20250514     # Override conversation model for this skill

# Visibility controls
user-invocable: true                # Show in slash menu (default: true)
disable-model-invocation: false     # Prevent Skill tool from invoking (default: false)

# Tool restrictions (two formats)
allowed-tools: Read, Glob, Grep     # Comma-separated string
# OR YAML list:
allowed-tools:
  - Read
  - Glob
  - Grep

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
          once: true                # Run only once per session, then removed
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
| `name` | string | Yes | Kebab-case identifier (max 64 chars). Should match directory name. |
| `description` | string | Yes | Shown in slash menu, used for auto-discovery (max 1024 chars) |
| `license` | string | No | License type (e.g., MIT) |
| `metadata` | object | No | Version, model, quality indicators |
| `model` | string | No | Model to use when skill is active (overrides conversation model) |
| `user-invocable` | boolean | No | Show in slash menu (default: true) |
| `disable-model-invocation` | boolean | No | Prevent Skill tool invocation (default: false) |
| `allowed-tools` | string/list | No | Tool whitelist (comma-separated string or YAML list). **Claude Code only.** |
| `context` | string | No | Set to `fork` for isolation |
| `agent` | string | No | Subagent type when forked. Defaults to `general-purpose`. Only applicable with `context: fork`. |
| `hooks` | object | No | Component-scoped hook definitions |

See [best practices guide](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices) for complete authoring guidance including validation rules.

### Hook Options

| Option | Type | Description |
|--------|------|-------------|
| `once` | boolean | Run hook only once per session, then remove it (default: false) |

### allowed-tools Behavior

When `allowed-tools` is omitted, the skill doesn't restrict tools. Claude uses its standard permission model and may ask for tool approval.

When specified, useful for:
- **Read-only skills**: Prevent file modifications
- **Limited scope**: e.g., data analysis without file writing
- **Security-sensitive workflows**: Restrict capabilities explicitly

## Key Points

- `name` and `description` are required
- `model` overrides the conversation model when skill is active
- `allowed-tools` accepts comma-separated string or YAML list
- `once: true` on hooks runs them only once per session
- Component-scoped hooks run only during skill execution
- `context: fork` runs skill in separate subagent
