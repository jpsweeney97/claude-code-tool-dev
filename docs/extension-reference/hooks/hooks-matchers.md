---
id: hooks-matchers
topic: Hook Matcher Patterns
category: hooks
tags: [matchers, patterns, regex, glob]
requires: [hooks-overview, hooks-configuration]
related_to: [hooks-events]
official_docs: https://code.claude.com/en/hooks
---

# Hook Matcher Patterns

Matchers determine which tools or events trigger hooks.

## Pattern Syntax

Matchers are **case-sensitive** and support:

| Syntax | Description | Example |
|--------|-------------|---------|
| Simple string | Exact tool name match | `Write` matches Write only |
| Regex | Regular expression pattern | `Edit\|Write` or `Notebook.*` |
| `*` | Match all tools | Wildcard for any tool |
| `""` or omitted | Match all tools | Same as `*` |

## Examples

### Match Specific Tool

```json
{
  "matcher": "Bash"
}
```

### Match Multiple Tools (Regex OR)

```json
{
  "matcher": "Write|Edit|NotebookEdit"
}
```

### Match Pattern (Regex)

```json
{
  "matcher": "Notebook.*"
}
```

### Match All Tools

```json
{
  "matcher": "*"
}
```

### No Matcher (Match All)

```json
{
  "hooks": [{
    "type": "command",
    "command": "./hook.sh"
  }]
}
```

## Event-Specific Matchers

Some events use matchers for non-tool values:

| Event | Matcher Values |
|-------|---------------|
| `SessionStart` | `startup`, `resume`, `clear`, `compact` |
| `PreCompact` | `manual`, `auto` |
| `Notification` | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` |

## Key Points

- Matchers are case-sensitive (`Bash` not `bash`)
- Use `|` for OR matching (regex syntax)
- Use `.*` for wildcard matching (regex syntax)
- Omit matcher or use `*` to match all
- Only applies to PreToolUse, PostToolUse, PermissionRequest, and some other events
