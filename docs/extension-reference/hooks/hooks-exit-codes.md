---
id: hooks-exit-codes
topic: Hook Exit Codes
category: hooks
tags: [exit-codes, blocking, allow, deny]
requires: [hooks-overview]
related_to: [hooks-events, hooks-types]
official_docs: https://code.claude.com/en/hooks
---

# Hook Exit Codes

Exit codes determine hook behavior and whether operations proceed.

## Exit Code Reference

| Code | Meaning | Behavior |
|------|---------|----------|
| `0` | Success/Allow | Proceed; stdout shown in verbose mode (Ctrl+O) |
| `1` | Error (non-blocking) | Log error, proceed anyway |
| `2` | Block | Stop operation, show message |

**Non-blocking error format:** For exit codes other than 0 or 2, stderr is shown to the user in verbose mode (Ctrl+O) with format: `Failed with non-blocking status code: {stderr}`. If stderr is empty, shows `No stderr output`.

**Important:** Claude Code does not see stdout if exit code is 0, except for `UserPromptSubmit` and `SessionStart` where stdout is added as context.

## Critical: Exit Code 1 Does NOT Block

```bash
#!/bin/bash
# This does NOT block - just logs and proceeds
echo "Warning: something wrong" >&2
exit 1
```

```bash
#!/bin/bash
# This DOES block
echo "BLOCKED: dangerous operation" >&2
exit 2
```

## Blocking Example

```bash
#!/bin/bash
# ~/.claude/hooks/validate-bash.sh

# Block dangerous commands
if echo "$TOOL_INPUT" | grep -qE "(rm -rf|sudo|chmod 777)"; then
  echo "BLOCKED: Dangerous command detected" >&2
  exit 2
fi

# Allow
exit 0
```

## Allow with Modification

PreToolUse hooks can modify tool inputs by outputting JSON:

```bash
#!/bin/bash
cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": "npm run lint -- --fix"
    }
  }
}
EOF
```

## Exit Code 2 Behavior by Event

| Event | Exit Code 2 Behavior |
|-------|---------------------|
| `PreToolUse` | Blocks tool call, stderr shown to Claude |
| `PermissionRequest` | Denies permission, stderr shown to Claude |
| `PostToolUse` | Stderr shown to Claude (tool already ran) |
| `Notification` | Stderr shown to user only |
| `UserPromptSubmit` | Blocks prompt, erases it, stderr shown to user |
| `Stop` | Blocks stoppage, stderr shown to Claude |
| `SubagentStop` | Blocks stoppage, stderr shown to subagent |
| `PreCompact` | Stderr shown to user only |
| `SessionStart` | Stderr shown to user only |
| `SessionEnd` | Stderr shown to user only |

## JSON Output (Advanced)

Exit code 0 with JSON stdout enables structured control.

**Warning:** JSON output is only processed when exit code is 0. If exit code is 2, stderr text is used directly and any JSON in stdout is ignored.

### Common JSON Fields

```json
{
  "continue": true,           // false stops Claude entirely
  "stopReason": "string",     // Shown when continue is false
  "suppressOutput": true,     // Hide from transcript mode
  "systemMessage": "string"   // Warning shown to user
}
```

**Precedence:** `continue: false` takes precedence over any `decision: "block"` output.

### `continue: false` Behavior by Event

When `continue` is false, Claude stops processing. This differs from `decision: "block"`:

| Event | `continue: false` | `decision: "block"` |
|-------|-------------------|---------------------|
| PreToolUse | Stops Claude entirely | Blocks only this tool call |
| PostToolUse | Stops Claude entirely | Provides feedback to Claude |
| UserPromptSubmit | Prevents prompt processing | Same effect |
| Stop/SubagentStop | Takes precedence | Prevents stopping |

### PreToolUse Decision Control

**`updatedInput` behavior:**
- Modifies tool input parameters before execution
- Combine with `"allow"` to modify and auto-approve
- Combine with `"ask"` to modify and show for user confirmation

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Auto-approved by hook",
    "updatedInput": {
      "command": "modified command"
    }
  }
}
```

| Decision | Effect |
|----------|--------|
| `"allow"` | Bypass permission, execute immediately |
| `"deny"` | Block tool call, reason shown to Claude |
| `"ask"` | Show permission dialog to user |

**Deprecated fields:** The `decision` and `reason` fields are deprecated for PreToolUse hooks. Use `hookSpecificOutput.permissionDecision` and `hookSpecificOutput.permissionDecisionReason` instead. The deprecated `"approve"` and `"block"` values map to `"allow"` and `"deny"` respectively.

### PermissionRequest Decision Control

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": {"command": "npm run lint"}
    }
  }
}
```

**Allow options:**
- `updatedInput`: Modify tool input parameters before execution

**Deny options:**
- `message`: String explaining why denied (shown to Claude)
- `interrupt`: Boolean; if `true`, stops Claude entirely after denial

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "deny",
      "message": "This operation is not permitted",
      "interrupt": true
    }
  }
}
```

### PostToolUse Decision Control

```json
{
  "decision": "block",
  "reason": "Code style violation detected",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional info for Claude"
  }
}
```

### UserPromptSubmit Decision Control

**Two ways to add context (exit code 0):**
1. **Plain text stdout** (simpler): Non-JSON text is added as context
2. **JSON with `additionalContext`** (structured): More control

**Blocking with JSON:** Exit code 2 only uses stderr. To block with a custom reason via JSON, use `"decision": "block"` with exit code 0.

```json
{
  "decision": "block",
  "reason": "Prompt contains sensitive data",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Context to add if allowed"
  }
}
```

**Note:** JSON format isn't required for simple use cases. To add context, print plain text to stdout with exit code 0. Use JSON when you need to block prompts or want structured control.

### Stop/SubagentStop Decision Control

```json
{
  "decision": "block",
  "reason": "Tasks incomplete - please verify tests pass"
}
```

### SessionStart Output

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Context loaded from hook"
  }
}
```

### SessionEnd Decision Control

SessionEnd hooks cannot block session termination but can perform cleanup tasks. No decision control is available.

## Key Points

- Exit 0: Allow operation
- Exit 1: Error but proceed (fail open)
- Exit 2: Block operation
- JSON output only processed on exit code 0
- Only blocking events respect exit code 2
- Stderr output shown when blocking
