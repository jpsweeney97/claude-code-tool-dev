---
id: agents-builtin
topic: Built-in Agent Types
category: agents
tags: [builtin, general-purpose, plan, explore]
requires: [agents-overview]
related_to: [agents-task-tool]
official_docs: https://code.claude.com/en/sub-agents
---

# Built-in Agent Types

Claude Code includes three built-in agent types for common use cases.

## Agent Types

| Type | Model | Tools | Use Case |
|------|-------|-------|----------|
| `general-purpose` | Inherits | All | Multi-step modification tasks |
| `Plan` | Inherits | Read, Glob, Grep, Bash | Plan mode architecture |
| `Explore` | Haiku | Glob, Grep, Read, Bash (read-only) | Codebase exploration |

## general-purpose

Default agent type for complex multi-step tasks:
- Full tool access
- Inherits model from main conversation
- Good for implementation tasks

## Plan

Architecture and planning agent used during plan mode:
- Read-only tools plus Bash
- Inherits model from main conversation
- Prevents infinite nesting (agents cannot spawn agents)

## Explore

Fast codebase exploration:
- Read-only operations
- Uses Haiku for speed
- Thoroughness levels: **quick** (targeted), **medium** (balanced), **very thorough** (comprehensive)

## Disabling Built-ins

Add to permissions deny array in settings:

```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(Plan)"]
  }
}
```

Or use the CLI flag:

```bash
claude --disallowedTools "Task(Explore)"
```

## Key Points

- Three built-in types: general-purpose, Plan, Explore
- general-purpose and Plan inherit model; Explore uses Haiku
- Explore supports three thoroughness levels
- Plan prevents infinite nesting during plan mode
- Disable via permissions deny array or `--disallowedTools` CLI flag
