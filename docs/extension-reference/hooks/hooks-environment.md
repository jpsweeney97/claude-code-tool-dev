---
id: hooks-environment
topic: Hook Environment Variables
category: hooks
tags: [environment, variables, context]
requires: [hooks-overview]
related_to: [hooks-types, hooks-exit-codes]
official_docs: https://code.claude.com/en/hooks
---

# Hook Environment Variables

Environment variables available in hook commands.

## Variable Reference

| Variable | Description | Available In |
|----------|-------------|--------------|
| `CLAUDE_PROJECT_DIR` | Project root directory | All events |
| `CLAUDE_CODE_REMOTE` | `"true"` if running remotely | All events |
| `TOOL_INPUT` | Tool input JSON | PreToolUse, PostToolUse |
| `TOOL_OUTPUT` | Tool output | PostToolUse only |
| `CLAUDE_ENV_FILE` | Path for env persistence | SessionStart |

## Using TOOL_INPUT

```bash
#!/bin/bash
# Access tool input in PreToolUse

# Parse command from Bash tool input
command=$(echo "$TOOL_INPUT" | jq -r '.command')

if [[ "$command" == *"rm -rf"* ]]; then
  echo "BLOCKED: Destructive command" >&2
  exit 2
fi
```

## Using CLAUDE_ENV_FILE

SessionStart hooks can persist environment variables:

```bash
#!/bin/bash
# Activate virtual environment for session

echo 'source ~/.venv/bin/activate' >> "$CLAUDE_ENV_FILE"
echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
```

## Using TOOL_OUTPUT

```bash
#!/bin/bash
# Log file modifications in PostToolUse

echo "$(date): Modified $TOOL_INPUT" >> ~/.claude/edit-log.txt
echo "Output: $TOOL_OUTPUT" >> ~/.claude/edit-log.txt
```

## Key Points

- `TOOL_INPUT` is JSON, use `jq` to parse
- `CLAUDE_ENV_FILE` persists env for session
- `TOOL_OUTPUT` only available in PostToolUse
- All vars are strings, quote appropriately
