---
id: settings-permissions
topic: Settings Permissions
category: settings
tags: [permissions, allow, deny, patterns]
requires: [settings-overview, settings-scopes]
related_to: [settings-sandbox, settings-tools, security-managed]
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

## Excluding Sensitive Files

Prevent Claude Code from accessing sensitive files using deny rules:

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)"
    ]
  }
}
```

Files matching deny patterns are completely invisible to Claude Code.

**Note:** This replaces the deprecated `ignorePatterns` configuration.

## Default Mode

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

Options: `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions`

## Managed Restrictions

### disableBypassPermissionsMode

Prevent `bypassPermissions` mode from being activated. Set in managed settings only.

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable"
  }
}
```

This disables the `--dangerously-skip-permissions` command-line flag.

### additionalDirectories

Add directories outside the project that Claude can access:

```json
{
  "permissions": {
    "additionalDirectories": ["../docs/", "/shared/config/"]
  }
}
```

## Key Points

- Deny always wins over allow
- Use `:*` suffix for prefix matching
- `**` for recursive directory matching
- `//` prefix for absolute paths
