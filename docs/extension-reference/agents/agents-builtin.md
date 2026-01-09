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
| `general-purpose` | sonnet | All | Multi-step modification tasks |
| `Plan` | sonnet | Read, Glob, Grep, Bash | Plan mode architecture |
| `Explore` | haiku | Glob, Grep, Read, Bash (read-only) | Codebase exploration |

## general-purpose

Default agent type for complex multi-step tasks:
- Full tool access
- Uses sonnet model
- Good for implementation tasks

## Plan

Architecture and planning agent:
- Read-only tools plus Bash
- Uses sonnet for quality
- No file modifications

## Explore

Fast codebase exploration:
- Read-only operations
- Uses haiku for speed
- Best for finding patterns

## Disabling Built-ins

Add to permissions deny array:

```json
{
  "permissions": {
    "deny": ["Task(Explore)", "Task(Plan)"]
  }
}
```

## Key Points

- Three built-in types: general-purpose, Plan, Explore
- Each has different model and tool configuration
- Can be disabled via permissions deny rules
- Custom agents extend these patterns
