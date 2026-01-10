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

## Foreground vs Background Execution

Agents can run in **foreground** (blocking) or **background** (concurrent).

### Foreground Agents

- Block the main conversation until complete
- Permission prompts and `AskUserQuestion` pass through to user
- Inherit all tools from main conversation, **including MCP tools**

### Background Agents

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

| Aspect | Behavior |
|--------|----------|
| Permissions | Inherit parent permissions; auto-deny anything not pre-approved |
| MCP tools | Not available in background agents |
| Questions | `AskUserQuestion` fails (agent continues) |
| Recovery | Resume in foreground to retry with prompts |

### Switching Execution Mode

- Ask Claude to "run this in the background"
- Press **Ctrl+B** to send a running foreground task to background

## Key Points

- Task tool is the only way to invoke agents
- `subagent_type` matches agent name or built-in type
- Foreground agents pass through prompts and inherit MCP tools
- Background agents auto-deny and skip MCP tools
- Ctrl+B or "run in background" switches execution mode
- Model can be overridden per invocation
