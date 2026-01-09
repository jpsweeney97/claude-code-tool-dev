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

## Pattern Types

| Pattern | Matches |
|---------|---------|
| `Bash` | All Bash tool uses |
| `Bash(npm run test)` | Exact command match |
| `Bash(npm run:*)` | Commands starting with `npm run` |
| `Write\|Edit` | Either Write or Edit tool |
| `*` | All tools |
| `startup` | SessionStart event |

## Examples

### Match Specific Tool

```json
{
  "matcher": "Bash"
}
```

### Match Exact Command

```json
{
  "matcher": "Bash(rm -rf)"
}
```

### Match Command Prefix

```json
{
  "matcher": "Bash(git:*)"
}
```

### Match Multiple Tools

```json
{
  "matcher": "Write|Edit|NotebookEdit"
}
```

### Match All Tools

```json
{
  "matcher": "*"
}
```

### No Matcher (All)

```json
{
  "hooks": [{
    "type": "command",
    "command": "./hook.sh"
  }]
}
```

## Key Points

- Omit matcher to match all
- Use `|` for OR matching
- Use `:*` suffix for prefix matching
- `startup` is special for SessionStart
