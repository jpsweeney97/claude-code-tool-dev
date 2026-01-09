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

Claude Code supports 10 hook event types.

## Event Reference

| Event | Trigger | Can Block | Key Use Cases |
|-------|---------|-----------|---------------|
| `PreToolUse` | Before tool execution | Yes | Validate commands, modify inputs |
| `PostToolUse` | After tool execution | No | Log results, capture outputs |
| `UserPromptSubmit` | User sends message | Yes | Inject context, validate requests |
| `Stop` | Claude stops responding | Yes | Final checks, cleanup |
| `SubagentStop` | Subagent completes | Yes | Validate agent output |
| `SessionStart` | Session begins | No | Initialize state, set env vars |
| `SessionEnd` | Session ends | No | Persist state, cleanup |
| `PreCompact` | Before context compression | No | Preserve critical info |
| `Notification` | Notification shown | No | External integrations |
| `PermissionRequest` | Permission prompt | Yes | Auto-approve/deny patterns |

## Blocking Events

Only these events can block operations:
- `PreToolUse` - Block tool execution
- `UserPromptSubmit` - Block user message
- `Stop` - Prevent stop
- `SubagentStop` - Block subagent completion
- `PermissionRequest` - Auto-deny permission

## Non-Blocking Events

These events cannot block (exit code 2 is ignored):
- `PostToolUse`
- `SessionStart`
- `SessionEnd`
- `PreCompact`
- `Notification`

## Key Points

- 10 events, 5 can block operations
- Blocking requires exit code 2
- Non-blocking events ignore exit codes
- PreToolUse is most commonly used
