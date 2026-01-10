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

## Notification with Multiple Matchers

Different hooks for different notification types:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [{"type": "command", "command": "/path/to/permission-alert.sh"}]
      },
      {
        "matcher": "idle_prompt",
        "hooks": [{"type": "command", "command": "/path/to/idle-notification.sh"}]
      }
    ]
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

## Python: Bash Command Validation

```python
#!/usr/bin/env python3
import json
import re
import sys

VALIDATION_RULES = [
    (r"\bgrep\b(?!.*\|)", "Use 'rg' (ripgrep) instead of 'grep'"),
    (r"\bfind\s+\S+\s+-name\b", "Use 'rg --files' instead of 'find -name'"),
]

def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(0)

issues = validate_command(command)
if issues:
    for message in issues:
        print(f"* {message}", file=sys.stderr)
    sys.exit(2)
```

## Python: UserPromptSubmit with Security Check

```python
#!/usr/bin/env python3
import json
import sys
import re

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)

prompt = input_data.get("prompt", "")

# Block prompts with sensitive patterns
sensitive = [
    (r"(?i)\b(password|secret|key|token)\s*[:=]", "Contains potential secrets"),
]

for pattern, message in sensitive:
    if re.search(pattern, prompt):
        output = {
            "decision": "block",
            "reason": f"Security: {message}. Rephrase without sensitive data."
        }
        print(json.dumps(output))
        sys.exit(0)

# Add context for allowed prompts
print(f"Session time: {__import__('datetime').datetime.now()}")
sys.exit(0)
```

## Python: PreToolUse Auto-Approval

```python
#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Auto-approve reading documentation files
if tool_name == "Read":
    file_path = tool_input.get("file_path", "")
    if file_path.endswith((".md", ".mdx", ".txt", ".json")):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Documentation auto-approved"
            },
            "suppressOutput": True
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

## Key Points

- PreToolUse for validation and blocking
- SessionStart for environment setup
- PostToolUse for logging (cannot block)
- Prompt hooks for LLM verification
- Python hooks: read stdin, write stdout/stderr
