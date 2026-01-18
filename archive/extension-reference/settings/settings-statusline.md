---
id: settings-statusline
topic: Status Line Settings
category: settings
tags: [statusline, display, custom]
requires: [settings-overview]
related_to: [settings-schema, hooks-overview]
official_docs: https://code.claude.com/en/statusline
---

# Status Line Settings

Configure a custom status line to display context.

## Configuration

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh"
  }
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Must be `"command"` |
| `command` | string | Script path to execute |

## Script Requirements

- Output a single line of text to stdout
- Runs with same environment as hooks (includes `CLAUDE_PROJECT_DIR`)
- Output displayed in status area of UI

## Example Script

```bash
#!/bin/bash
echo "$(git branch --show-current 2>/dev/null || echo 'no-git') | $(hostname -s)"
```

## Key Points

- Custom script for dynamic context display
- Useful for showing branch, environment, hostname
- Runs on UI refresh
