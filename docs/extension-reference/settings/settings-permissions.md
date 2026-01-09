---
id: settings-permissions
topic: Settings Permissions
category: settings
tags: [permissions, allow, deny, patterns]
requires: [settings-overview, settings-scopes]
related_to: [settings-sandbox]
official_docs: https://code.claude.com/en/settings
---

# Settings Permissions

Control what tools Claude can use without prompting.

## Permission Levels

| Level | Behavior |
|-------|----------|
| `allow` | Execute without prompting |
| `ask` | Prompt on each use (default) |
| `deny` | Block completely |

## Permission Configuration

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "ask": [
      "Bash(git push:*)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  }
}
```

## Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Bash(npm run test)` | Exact command |
| `Bash(npm run:*)` | Commands starting with prefix |
| `Read(./.env)` | Specific file |
| `Read(./secrets/**)` | Directory recursively |
| `Read(//absolute/path)` | Absolute path (note `//`) |
| `mcp__server__tool` | Specific MCP tool |
| `Task(Explore)` | Specific subagent type |

## Default Mode

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

Options: `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions`

## Key Points

- Deny always wins over allow
- Use `:*` suffix for prefix matching
- `**` for recursive directory matching
- `//` prefix for absolute paths
