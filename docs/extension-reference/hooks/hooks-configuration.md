---
id: hooks-configuration
topic: Hook Configuration Schema
category: hooks
tags: [configuration, schema, settings, json]
requires: [hooks-overview]
related_to: [hooks-events, hooks-matchers, hooks-types, hooks-environment]
official_docs: https://code.claude.com/en/hooks
---

# Hook Configuration Schema

Complete JSON schema for hook configuration.

## Full Schema

```json
{
  "hooks": {
    "<EventType>": [{
      "matcher": "<pattern>",      // Tool name, glob, or regex
      "once": true,                // Optional: run only once per session
      "hooks": [{
        "type": "command",         // "command", "prompt", or "agent"
        "command": "...",          // For command type
        "prompt": "...",           // For prompt type
        "agent": "...",            // For agent type
        "timeout": 60000           // Optional: milliseconds
      }]
    }]
  }
}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `matcher` | string | No | Pattern to match (default: all) |
| `once` | boolean | No | Run only once per session |
| `hooks[].type` | string | Yes | "command", "prompt", or "agent" |
| `hooks[].command` | string | Conditional | Shell command (command type) |
| `hooks[].prompt` | string | Conditional | LLM prompt (prompt type) |
| `hooks[].agent` | string | Conditional | Agent name (agent type) |
| `hooks[].timeout` | number | No | Timeout in milliseconds |

## Component-Scoped Hooks

Skills, commands, and agents can define their own hooks:

```yaml
---
name: my-skill
description: A skill with scoped hooks
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: ./skill-specific-validator.sh
---
```

## `once: true` Behavior

Run hook only once per session:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "once": true,
      "hooks": [{
        "type": "command",
        "command": "./setup-environment.sh"
      }]
    }]
  }
}
```

## Key Points

- EventType is one of the 10 event types
- Multiple hooks can share one matcher
- `once: true` prevents repeated execution
- Component-scoped hooks override global
