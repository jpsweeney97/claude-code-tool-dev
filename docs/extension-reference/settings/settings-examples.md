---
id: settings-examples
topic: Settings Examples
category: settings
tags: [examples, templates, patterns]
requires: [settings-overview, settings-permissions, settings-sandbox, settings-schema]
official_docs: https://code.claude.com/en/settings
---

# Settings Examples

Complete working settings configurations.

## Minimal Project Settings

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run:*)",
      "Bash(git status)"
    ]
  }
}
```

## Secure Development Environment

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true
  }
}
```

## Team Configuration

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Bash(npm run build)"
    ],
    "deny": [
      "Bash(npm publish:*)"
    ]
  },
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "./scripts/validate-command.sh"
      }]
    }]
  },
  "model": "claude-sonnet-4-5-20250929"
}
```

## Full Enterprise Settings

```json
{
  "permissions": {
    "allow": ["Bash(npm run:*)", "Read(./src/**)"],
    "deny": ["Bash(curl:*)", "Read(./.env)"],
    "defaultMode": "acceptEdits"
  },
  "sandbox": {
    "enabled": true,
    "excludedCommands": ["docker"]
  },
  "hooks": {
    "SessionStart": [{
      "matcher": "startup",
      "once": true,
      "hooks": [{
        "type": "command",
        "command": "echo 'source ~/.venv/bin/activate' >> \"$CLAUDE_ENV_FILE\""
      }]
    }]
  },
  "enabledPlugins": {
    "formatter@company-tools": true
  },
  "outputStyle": "Explanatory"
}
```

## Key Points

- Start minimal, add restrictions as needed
- Team settings should be committed to git
- Use local scope for testing
- Hooks for validation and automation
