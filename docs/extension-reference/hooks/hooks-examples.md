---
id: hooks-examples
topic: Hook Examples
category: hooks
tags: [examples, templates, patterns]
requires: [hooks-overview, hooks-configuration, hooks-exit-codes]
official_docs: https://code.claude.com/en/hooks
---

# Hook Examples

Complete working hook examples.

## PreToolUse Validation

Block dangerous Bash commands:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/validate-bash.sh"
      }]
    }]
  }
}
```

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

## SessionStart Environment

Set up environment on session start:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "hooks": [{
        "type": "command",
        "command": "echo 'source ~/.venv/bin/activate' >> \"$CLAUDE_ENV_FILE\""
      }]
    }]
  }
}
```

## PostToolUse Logging

Log file modifications:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "echo \"$(date): Modified $TOOL_INPUT\" >> ~/.claude/edit-log.txt"
      }]
    }]
  }
}
```

## Prompt Hook for Completion Check

LLM-based verification on Stop:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Verify all requested tasks are complete. Check for: 1) All files created, 2) Tests passing, 3) No TODOs left. Respond with approve or block."
      }]
    }]
  }
}
```

## Key Points

- PreToolUse for validation and blocking
- SessionStart for environment setup
- PostToolUse for logging (cannot block)
- Prompt hooks for LLM verification
