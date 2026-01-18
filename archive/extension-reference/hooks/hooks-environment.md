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
| `CLAUDE_PROJECT_DIR` | Project root directory (absolute path) | All events |
| `CLAUDE_CODE_REMOTE` | `"true"` if remote/web, empty if local CLI | All events |
| `CLAUDE_PLUGIN_ROOT` | Plugin directory (absolute path) | Plugin hooks only |
| `CLAUDE_ENV_FILE` | Path for env persistence | SessionStart only |

**Note**: Hook input is delivered via **stdin** as JSON, not environment variables. See hooks-input-schema for field details.

## Reading Stdin Input

```bash
#!/bin/bash
# Read JSON from stdin, parse with jq
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

if [[ "$command" == *"rm -rf"* ]]; then
  echo "BLOCKED: Destructive command" >&2
  exit 2
fi
```

## Using CLAUDE_ENV_FILE

SessionStart hooks can persist environment variables:

```bash
#!/bin/bash
# Set individual variables
echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
```

### Capture All Environment Changes

When setup modifies environment (e.g., `nvm use`), capture the diff:

```bash
#!/bin/bash
ENV_BEFORE=$(export -p | sort)

# Run setup that modifies environment
source ~/.nvm/nvm.sh
nvm use 20

if [ -n "$CLAUDE_ENV_FILE" ]; then
  ENV_AFTER=$(export -p | sort)
  comm -13 <(echo "$ENV_BEFORE") <(echo "$ENV_AFTER") >> "$CLAUDE_ENV_FILE"
fi
```

**Important:** `CLAUDE_ENV_FILE` is only available for SessionStart hooks. Other hook types do not have access to this variable. Variables written to this file will be available in all subsequent bash commands that Claude Code executes during the session.

## Using CLAUDE_CODE_REMOTE

Detect execution environment:

```bash
#!/bin/bash
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  # Running in web/remote environment
  echo "Remote mode - using cloud paths"
else
  # Running in local CLI
  echo "Local mode - using local paths"
fi
```

## Key Points

- Input via stdin (JSON), not environment variables
- `CLAUDE_ENV_FILE` persists env for session
- `CLAUDE_CODE_REMOTE` detects local vs remote
- `CLAUDE_PLUGIN_ROOT` only in plugin hooks
- Always quote variables in bash
