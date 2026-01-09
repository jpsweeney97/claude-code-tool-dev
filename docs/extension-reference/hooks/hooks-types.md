---
id: hooks-types
topic: Hook Types
category: hooks
tags: [command, prompt, agent, types]
requires: [hooks-overview]
related_to: [hooks-configuration, hooks-exit-codes]
official_docs: https://code.claude.com/en/hooks
---

# Hook Types

Three types of hooks with different capabilities.

## Command Hooks

Execute shell scripts. Available in all events.

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./validate-bash.sh \"$TOOL_INPUT\""
      }]
    }]
  }
}
```

## Prompt Hooks

LLM-based evaluation using Haiku. Available in all events.

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Evaluate if all tasks are complete based on: $ARGUMENTS"
      }]
    }]
  }
}
```

**LLM response schema:**

```json
{
  "decision": "approve",           // "approve" or "block"
  "reason": "All tasks verified",  // Explanation
  "continue": false,               // Optional: stop Claude entirely
  "stopReason": "Work complete",   // Optional: message when stopping
  "systemMessage": "Note: ..."     // Optional: shown to user
}
```

## Agent Hooks (Plugins Only)

Agentic verifier with tool access. Only available in plugins.

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "agent",
        "agent": "code-quality-checker",
        "prompt": "Verify the changes meet quality standards"
      }]
    }]
  }
}
```

## Key Points

- Command hooks: shell scripts, most flexible
- Prompt hooks: LLM evaluation, no tool access
- Agent hooks: plugins only, full tool access
- All types support timeout configuration
