---
id: hooks-input-schema
topic: Hook Input Schemas
category: hooks
tags: [input, schema, json, stdin]
requires: [hooks-overview, hooks-events]
related_to: [hooks-exit-codes, hooks-environment]
official_docs: https://code.claude.com/en/hooks
---

# Hook Input Schemas

Hooks receive JSON data via stdin. Each event type has specific fields.

## Common Fields

All hook inputs include these fields:

```typescript
{
  session_id: string        // Unique session identifier
  transcript_path: string   // Path to conversation JSON file
  cwd: string               // Current working directory
  permission_mode: string   // "default", "plan", "acceptEdits", "dontAsk", "bypassPermissions"
  hook_event_name: string   // Event type that triggered this hook
}
```

## PreToolUse Input

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

## PostToolUse Input

Includes `tool_response` with the tool's output:

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

## Notification Input

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "notification_type": "permission_prompt"
}
```

## UserPromptSubmit Input

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate factorial"
}
```

## Stop / SubagentStop Input

Includes `stop_hook_active` to prevent infinite loops:

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

**Important**: Check `stop_hook_active` to prevent Claude from running indefinitely when blocking stop.

## PreCompact Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```

- `trigger`: `"manual"` (from `/compact`) or `"auto"` (context full)
- `custom_instructions`: User text from `/compact` (empty for auto)

## SessionStart Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionStart",
  "source": "startup"
}
```

- `source`: `"startup"`, `"resume"`, `"clear"`, or `"compact"`

## SessionEnd Input

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "SessionEnd",
  "reason": "prompt_input_exit"
}
```

**Valid `reason` values:**
- `clear` - Session cleared with /clear command
- `logout` - User logged out
- `prompt_input_exit` - User exited while prompt input was visible
- `other` - Other exit reasons

## PermissionRequest Input

Same structure as PreToolUse:

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

## Reading Input in Scripts

```bash
#!/bin/bash
# Read JSON from stdin
input=$(cat)

# Parse with jq
tool_name=$(echo "$input" | jq -r '.tool_name')
file_path=$(echo "$input" | jq -r '.tool_input.file_path')
```

```python
#!/usr/bin/env python3
import json
import sys

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
```

## Key Points

- All input is JSON via stdin
- Common fields present in all events
- `tool_input` schema varies by tool
- Check `stop_hook_active` to prevent infinite loops
- Use `jq` in bash or `json.load()` in Python
