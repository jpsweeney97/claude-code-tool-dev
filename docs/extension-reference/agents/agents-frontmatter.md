---
id: agents-frontmatter
topic: Agent Frontmatter Schema
category: agents
tags: [frontmatter, yaml, schema, configuration]
requires: [agents-overview]
related_to: [agents-permissions, agents-task-tool, agents-builtin]
official_docs: https://code.claude.com/en/sub-agents
---

# Agent Frontmatter Schema

YAML frontmatter configures agent behavior, tools, and permissions.

## Full Schema

```yaml
---
# Required
name: my-agent  # Unique identifier (lowercase, hyphens)
description: What this agent does (shown in Task tool)

# Tool access (allowlist)
tools: Read, Glob, Grep, Bash, Write, Edit

# Tool denylist (removed from inherited/specified tools)
disallowedTools: Write, Edit

# Model selection
model: sonnet  # sonnet, opus, haiku, or inherit

# Skills to auto-load
skills: sql-analysis, chart-generation

# Permission behavior
permissionMode: acceptEdits  # See permission modes

# Component-scoped hooks (no `once: true` support)
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./validate-command.sh
  PostToolUse:
    - matcher: Write|Edit
      hooks:
        - type: command
          command: ./validate-output.sh
  Stop:  # Runs when agent finishes (converted to SubagentStop)
    - hooks:
        - type: command
          command: ./cleanup.sh
---

Additional context and instructions for the agent...
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier (lowercase, hyphens) |
| `description` | string | Yes | Shown in Task tool |
| `tools` | string | No | Comma-separated allowlist of tools |
| `disallowedTools` | string | No | Comma-separated denylist (removed from inherited/specified) |
| `model` | string | No | sonnet (default), opus, haiku, or inherit |
| `skills` | string | No | Comma-separated skills to inject at startup |
| `permissionMode` | string | No | Permission handling mode |
| `hooks` | object | No | PreToolUse, PostToolUse, Stop events |

### Model Selection Guide

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Doc lookup, simple queries | haiku | Fast, economical |
| Standard development | sonnet | Balanced |
| Complex architecture, planning | opus | Highest capability |

## Hook Lifecycle

Hooks defined in agent frontmatter:
- Run only while that specific agent is active
- Are automatically cleaned up when the agent finishes
- `Stop` hooks are converted to `SubagentStop` events internally

## Hook Environment Variables

Hook commands receive context via environment variables:

| Variable | Description |
|----------|-------------|
| `$TOOL_INPUT` | JSON string of the tool's input parameters |

Example validation script:

```bash
#!/bin/bash
# Block write queries in db-reader agent
if echo "$TOOL_INPUT" | grep -qiE '(INSERT|UPDATE|DELETE|DROP)'; then
  echo "Write operations not allowed" >&2
  exit 2  # Block the tool call
fi
exit 0
```

## Context Isolation

Agents receive only:
- Their system prompt (markdown body after frontmatter)
- Basic environment details (working directory, platform)

Agents do **not** receive the full Claude Code system prompt. This isolation makes agents predictable and focused on their specific task.

## Skills Behavior

When you list skills in the `skills` field:
- Full skill content is **injected** into the agent's context at startup
- Skills are not just "made available for invocation" — their content becomes part of the agent's prompt
- Agents **do not inherit** skills from the parent conversation

```yaml
skills: sql-analysis, chart-generation  # Full skill content injected
```

## Project-Level Agent Hooks

Beyond hooks in agent frontmatter, you can define hooks in `settings.json` that respond to agent lifecycle events:

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "db-agent",
        "hooks": [{ "type": "command", "command": "./scripts/setup-db.sh" }]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "db-agent",
        "hooks": [{ "type": "command", "command": "./scripts/cleanup-db.sh" }]
      }
    ]
  }
}
```

| Event | Matcher Input | When |
|-------|---------------|------|
| `SubagentStart` | Agent name | Agent begins execution |
| `SubagentStop` | Agent name | Agent completes |

Use `matcher` to target specific agents by name. Omit matcher to run for all agents.

## Key Points

- `name` and `description` are required
- Markdown body after frontmatter defines agent's role and behavior
- `tools` allowlist, `disallowedTools` denylist (both comma-separated strings)
- `inherit` model uses parent conversation's model
- Agents receive only their system prompt + env details, not full Claude Code system prompt
- Skills are injected (not just made available); agents don't inherit parent skills
- Component-scoped hooks: PreToolUse, PostToolUse, Stop
- Project-level hooks: SubagentStart, SubagentStop in settings.json
- Note: `once: true` not supported in agent hooks
