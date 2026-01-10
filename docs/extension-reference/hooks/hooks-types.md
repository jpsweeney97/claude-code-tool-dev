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

**Prompt fields:**
- `$ARGUMENTS`: Placeholder for hook input JSON (appended if not present)
- `timeout`: Optional, defaults to 30 seconds

**LLM response schema:**

```json
{
  "ok": true,                      // true allows, false blocks
  "reason": "Explanation here"     // Required when ok is false
}
```

**Best use cases:**
- `Stop`: Intelligently decide if Claude should continue
- `SubagentStop`: Evaluate if subagent completed its task
- `UserPromptSubmit`: Validate user prompts with LLM
- `PreToolUse`: Context-aware permission decisions
- `PermissionRequest`: Intelligent allow/deny

**Example: SubagentStop with custom logic:**

```json
{
  "hooks": {
    "SubagentStop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Evaluate if this subagent should stop. Input: $ARGUMENTS\n\nCheck if:\n- The subagent completed its assigned task\n- Any errors occurred that need fixing\n- Additional context gathering is needed\n\nReturn: {\"ok\": true} to allow stopping, or {\"ok\": false, \"reason\": \"explanation\"} to continue."
      }]
    }]
  }
}
```

**Comparison with command hooks:**

| Aspect | Command Hooks | Prompt Hooks |
|--------|--------------|--------------|
| Execution | Runs bash script | Queries LLM |
| Setup | Requires script file | Just configure prompt |
| Context | Limited to script logic | Natural language understanding |
| Performance | Fast (local) | Slower (API call) |
| Use case | Deterministic rules | Context-aware decisions |

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

## Prompt Hook Best Practices

- **Be specific in prompts**: Clearly state what you want the LLM to evaluate
- **Include decision criteria**: List the factors the LLM should consider
- **Test your prompts**: Verify the LLM makes correct decisions for your use cases
- **Set appropriate timeouts**: Default is 30 seconds, adjust if needed
- **Use for complex decisions**: Bash hooks are better for simple, deterministic rules

## Example: Intelligent Stop Hook

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "You are evaluating whether Claude should stop working. Context: $ARGUMENTS\n\nAnalyze the conversation and determine if:\n1. All user-requested tasks are complete\n2. Any errors need to be addressed\n3. Follow-up work is needed\n\nRespond with JSON: {\"ok\": true} to allow stopping, or {\"ok\": false, \"reason\": \"your explanation\"} to continue working.",
        "timeout": 30
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
