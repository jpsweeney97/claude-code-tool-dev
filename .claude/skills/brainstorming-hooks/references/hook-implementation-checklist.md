# Hook Implementation Checklist

Quick reference for implementing hooks. Use during Phase 5 (Implement).

## Table of Contents

1. [Script Hook Template](#script-hook-template)
2. [Prompt Hook Template](#prompt-hook-template)
3. [Component-Scoped Hook Template](#component-scoped-hook-template)
4. [Exit Code Reference](#exit-code-reference)
5. [JSON Output Templates](#json-output-templates)
6. [Common Mistakes](#common-mistakes)
7. [Testing Commands](#testing-commands)

---

## Script Hook Template

Create at `.claude/hooks/<name>.py`:

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60
# ///

import json
import sys

def main():
    # Read event data from stdin
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract relevant fields
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Your logic here
    # ...

    # Exit codes:
    # 0 = success/allow
    # 2 = block (stderr shown to Claude)
    # other = non-blocking error

    sys.exit(0)

if __name__ == "__main__":
    main()
```

**After creating:**
```bash
chmod +x .claude/hooks/<name>.py
uv run scripts/sync-settings
```

### Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `event` | Yes | string | Event type (PreToolUse, PostToolUse, etc.) |
| `matcher` | No | string | Tool/event filter pattern |
| `timeout` | No | integer | Seconds (default 60 for command, 30 for prompt) |

---

## Prompt Hook Template

Add directly to settings.json (no script needed):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if Claude should stop. Context: $ARGUMENTS. Check if all tasks are complete. Respond with JSON: {\"ok\": true} to allow stopping, or {\"ok\": false, \"reason\": \"explanation\"} to continue.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Prompt Hook Response Schema

The LLM must respond with:
```json
{
  "ok": true | false,
  "reason": "Required when ok is false"
}
```

---

## Component-Scoped Hook Template

Add to skill/command/agent frontmatter:

```yaml
---
name: my-skill
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "./scripts/validate.sh"
          once: true  # Skills/commands only, NOT agents
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/format.sh"
  Stop:
    - hooks:
        - type: command
          command: "./scripts/cleanup.sh"
---
```

**Supported events:** PreToolUse, PostToolUse, Stop only

**Note:** `once: true` runs hook only once per session (skills/commands only).

---

## Exit Code Reference

| Code | Meaning | stdout | stderr |
|------|---------|--------|--------|
| **0** | Success | JSON processed or shown in verbose | Ignored |
| **2** | Block | Ignored | Shown to Claude as error |
| **1** | Non-blocking error | Ignored | Shown in verbose mode |
| **Other** | Non-blocking error | Ignored | Shown in verbose mode |

### Common Pattern: Block with Message

```python
# WRONG - exit 1 doesn't block!
print("Error: dangerous command", file=sys.stderr)
sys.exit(1)  # Operation proceeds!

# CORRECT - exit 2 blocks
print("Error: dangerous command", file=sys.stderr)
sys.exit(2)  # Operation blocked
```

### Common Pattern: Allow with Context

```python
# Add context without blocking
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": "Note: This modifies production files."
    }
}
print(json.dumps(output))
sys.exit(0)  # Operation proceeds with context
```

---

## JSON Output Templates

### PreToolUse: Auto-Approve

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "Auto-approved by policy"
    }
}
print(json.dumps(output))
sys.exit(0)
```

### PreToolUse: Deny with Reason

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Cannot modify protected files"
    }
}
print(json.dumps(output))
sys.exit(0)
```

### PreToolUse: Modify Input

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {
            "command": original_command + " --dry-run"
        }
    }
}
print(json.dumps(output))
sys.exit(0)
```

### PreToolUse: Inject Context

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": "Remember: Test all changes before committing."
    }
}
print(json.dumps(output))
sys.exit(0)
```

### UserPromptSubmit: Add Context

```python
# Simple: just print text
print(f"Current time: {datetime.now().isoformat()}")
sys.exit(0)

# Or use JSON
output = {
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "Context here"
    }
}
print(json.dumps(output))
sys.exit(0)
```

### UserPromptSubmit: Block Prompt

```python
output = {
    "decision": "block",
    "reason": "Prompt contains sensitive information"
}
print(json.dumps(output))
sys.exit(0)
```

### Stop: Prevent Completion

```python
# Check stop_hook_active to prevent infinite loop!
if event.get("stop_hook_active"):
    sys.exit(0)  # Don't block again

output = {
    "decision": "block",
    "reason": "Tests have not been run. Please run tests before completing."
}
print(json.dumps(output))
sys.exit(0)
```

### SessionStart: Inject Context

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "Project context here..."
    }
}
print(json.dumps(output))
sys.exit(0)
```

### PermissionRequest: Auto-Allow

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
            "behavior": "allow"
        }
    }
}
print(json.dumps(output))
sys.exit(0)
```

### PermissionRequest: Deny with Message

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {
            "behavior": "deny",
            "message": "Cannot modify production files"
        }
    }
}
print(json.dumps(output))
sys.exit(0)
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `sys.exit(1)` to block | Doesn't block, operation proceeds | Use `sys.exit(2)` |
| Error to stdout on exit 2 | stdout ignored on exit 2 | Use `file=sys.stderr` |
| JSON on exit 2 | JSON ignored on exit 2 | JSON only on exit 0 |
| Broad matcher on slow hook | Every tool call slows | Narrow the matcher |
| Not reading stdin | Miss event data | Always `json.load(sys.stdin)` |
| Case-sensitive matcher | `bash` ≠ `Bash` | Match exact case |
| Not checking `stop_hook_active` | Infinite loop in Stop hooks | Check and skip if true |
| Script not executable | Hook doesn't run | `chmod +x` |
| Settings not synced | Hook not registered | `uv run scripts/sync-settings` |
| Network calls without timeout | Hook hangs | Add timeout to all network calls |

---

## Testing Commands

### Manual Test with Mock Input

```bash
# Test PreToolUse hook
echo '{"tool_name": "Bash", "tool_input": {"command": "ls -la"}, "session_id": "test"}' | python .claude/hooks/my-hook.py
echo "Exit code: $?"
```

### Verify Hook Registration

```
/hooks
```

### Debug Mode

```bash
claude --debug
```

### Verbose Mode (in session)

Press `Ctrl+O` to toggle verbose mode and see hook output.

### Check Settings

```bash
cat .claude/settings.json | jq '.hooks'
```

### Sync Settings

```bash
uv run scripts/sync-settings
```

---

## Deployment Checklist

Before declaring done:

- [ ] Script is executable (`chmod +x`)
- [ ] Frontmatter has correct `event` type
- [ ] Matcher is specific (not `*` on slow hooks)
- [ ] Exit codes are correct (2 for block)
- [ ] stderr used for block messages
- [ ] JSON output only on exit 0
- [ ] `stop_hook_active` checked (Stop hooks)
- [ ] Settings synced (`uv run scripts/sync-settings`)
- [ ] Tested with mock input
- [ ] Verified in `/hooks` menu
- [ ] Tested in actual session
