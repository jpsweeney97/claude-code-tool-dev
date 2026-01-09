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
| `0` | Success/Allow | Proceed with operation |
| `1` | Error (non-blocking) | Log error, proceed anyway |
| `2` | Block | Stop operation, show message |

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

## Key Points

- Exit 0: Allow operation
- Exit 1: Error but proceed (fail open)
- Exit 2: Block operation
- Only blocking events respect exit code 2
- Stderr output shown when blocking
