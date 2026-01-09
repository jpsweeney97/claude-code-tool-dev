---
id: agents-task-tool
topic: Task Tool Invocation
category: agents
tags: [task-tool, invocation, dispatch]
requires: [agents-overview]
related_to: [agents-frontmatter, agents-resumable]
official_docs: https://code.claude.com/en/sub-agents
---

# Task Tool Invocation

Agents are invoked via the Task tool, not slash commands.

## Basic Invocation

```typescript
Task(
  description: "Analyze authentication flow",
  prompt: "Trace the authentication flow from login to session creation...",
  subagent_type: "security-analyzer",  // Custom or built-in
  model: "opus",                        // Optional override
  run_in_background: true              // Optional async execution
)
```

## Task Tool Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `description` | string | Yes | Short description (3-5 words) |
| `prompt` | string | Yes | Task instructions |
| `subagent_type` | string | Yes | Agent type name |
| `model` | string | No | Model override (sonnet, opus, haiku) |
| `run_in_background` | boolean | No | Async execution |
| `resume` | string | No | Agent ID to resume |

## Background Execution

Run agents asynchronously:

```typescript
Task(
  description: "Analyze codebase",
  prompt: "...",
  subagent_type: "analyzer",
  run_in_background: true
)
// Returns immediately with output_file path
// Use Read tool to check progress
```

## Key Points

- Task tool is the only way to invoke agents
- `subagent_type` matches agent name or built-in type
- Background agents run asynchronously
- Model can be overridden per invocation
