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

## Settings File Locations

| Scope | Path | Notes |
|-------|------|-------|
| User | `~/.claude/settings.json` | Global settings |
| Project | `.claude/settings.json` | Checked into repo |
| Local | `.claude/settings.local.json` | Not committed |
| Managed | Policy settings | Enterprise managed |

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
        "timeout": 60              // Optional: seconds
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
| `hooks[].timeout` | number | No | Timeout in seconds (default: 60) |

## Events Without Matchers

For events like `UserPromptSubmit`, `Stop`, and `SubagentStop` that don't use matchers, omit the `matcher` field:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/prompt-validator.py"
          }
        ]
      }
    ]
  }
}
```

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

**Agent example:**

```yaml
---
name: code-reviewer
description: Review code changes
hooks:
  PostToolUse:
    - matcher: 'Edit|Write'
      hooks:
        - type: command
          command: './scripts/run-linter.sh'
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

**Note**: `once` is only supported for skills and slash commands, not for agents.

## Component-Scoped Hook Events

When defining hooks in skills, commands, or agents via frontmatter, only these events are supported:
- `PreToolUse`
- `PostToolUse`
- `Stop`

## Key Points

- EventType is one of the 10 event types
- Multiple hooks can share one matcher
- `once: true` prevents repeated execution (skills/commands only)
- Component-scoped hooks support 3 events only
- Settings file locations have precedence order
