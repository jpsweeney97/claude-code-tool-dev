---
id: hooks-events
topic: Hook Event Types
category: hooks
tags: [events, pretooluse, posttooluse, sessionstart]
requires: [hooks-overview]
related_to: [hooks-types, hooks-matchers]
official_docs: https://code.claude.com/en/hooks
---

# Hook Event Types

Claude Code supports 11 hook event types.

## Event Reference

| Event | Trigger | Can Block | Key Use Cases |
|-------|---------|-----------|---------------|
| `PreToolUse` | Before tool execution | Yes | Validate commands, modify inputs |
| `PostToolUse` | After tool execution | No | Log results, capture outputs |
| `UserPromptSubmit` | User sends message | Yes | Inject context, validate requests |
| `Stop` | Claude stops responding (not on user interrupt) | Yes | Final checks, cleanup |
| `SubagentStop` | Subagent completes | Yes | Validate agent output |
| `SubagentStart` | Subagent begins | Yes | Initialize agent environment |
| `SessionStart` | Session begins | No | Initialize state, set env vars |
| `SessionEnd` | Session ends | No | Persist state, cleanup |
| `PreCompact` | Before context compression | No | Preserve critical info |
| `Notification` | Notification shown | No | External integrations |
| `PermissionRequest` | Permission prompt | Yes | Auto-approve/deny patterns |

## Event Matchers

### PreToolUse / PostToolUse / PermissionRequest

Common tool matchers:

| Matcher | Tool |
|---------|------|
| `Task` | Subagent tasks |
| `Bash` | Shell commands |
| `Glob` | File pattern matching |
| `Grep` | Content search |
| `Read` | File reading |
| `Edit` | File editing |
| `Write` | File writing |
| `WebFetch` | Web fetch |
| `WebSearch` | Web search |

### Notification

| Matcher | Trigger |
|---------|---------|
| `permission_prompt` | Permission requests |
| `idle_prompt` | Claude idle 60+ seconds |
| `auth_success` | Authentication success |
| `elicitation_dialog` | MCP tool input needed |

### PreCompact

| Matcher | Trigger |
|---------|---------|
| `manual` | From `/compact` command |
| `auto` | Context window full |

### SessionStart

| Matcher | Trigger |
|---------|---------|
| `startup` | Fresh session start |
| `resume` | `--resume`, `--continue`, or `/resume` |
| `clear` | `/clear` command |
| `compact` | After auto/manual compact |

**Use cases:** Loading development context (issues, recent changes), installing dependencies, setting environment variables.

**Note:** Resume operations start a new session under the hood.

## Blocking Events

Only these events can block operations:
- `PreToolUse` - Block tool execution
- `UserPromptSubmit` - Block user message
- `Stop` - Prevent stop
- `SubagentStop` - Block subagent completion
- `SubagentStart` - Block subagent initialization
- `PermissionRequest` - Auto-deny permission

## Non-Blocking Events

These events cannot block operations. Exit code 2 behavior:
- `PostToolUse` - Exit code ignored
- `SessionStart` - Exit code ignored, stderr shown to user
- `SessionEnd` - Exit code ignored, stderr shown to user
- `PreCompact` - Exit code ignored, stderr shown to user
- `Notification` - Exit code ignored, stderr shown to user

## Key Points

- 11 events, 6 can block operations
- Blocking requires exit code 2
- Non-blocking events ignore exit codes
- PreToolUse is most commonly used
