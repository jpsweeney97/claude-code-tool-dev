---
id: agents-frontmatter
topic: Agent Frontmatter Schema
category: agents
tags: [frontmatter, yaml, schema, configuration]
requires: [agents-overview]
related_to: [agents-permissions, agents-task-tool]
official_docs: https://code.claude.com/en/sub-agents
---

# Agent Frontmatter Schema

YAML frontmatter configures agent behavior, tools, and permissions.

## Full Schema

```yaml
---
# Required
description: What this agent does (shown in Task tool)

# Agent behavior
prompt: |
  You are a specialized agent for...

  Your responsibilities:
  - Task 1
  - Task 2

# Tool access
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit

# Model selection
model: sonnet  # sonnet, opus, or haiku

# Skills to auto-load
skills:
  - sql-analysis
  - chart-generation

# Permission behavior
permissionMode: acceptEdits  # See permission modes

# Component-scoped hooks (no `once: true` support)
hooks:
  PostToolUse:
    - matcher: Write|Edit
      hooks:
        - type: command
          command: ./validate-output.sh
---

Additional context and instructions for the agent...
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | Yes | Shown in Task tool |
| `prompt` | string | No | System prompt for agent |
| `tools` | array | No | Available tools |
| `model` | string | No | sonnet, opus, or haiku |
| `skills` | array | No | Skills to auto-load |
| `permissionMode` | string | No | Permission handling mode |
| `hooks` | object | No | Component-scoped hooks |

## Key Points

- Only `description` is required
- `prompt` defines agent's role and behavior
- `tools` restricts available capabilities
- Component-scoped hooks run during agent execution
- Note: `once: true` not supported in agent hooks
