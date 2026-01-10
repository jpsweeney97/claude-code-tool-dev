---
id: hooks-plugins
topic: Plugin Hooks
category: hooks
tags: [plugins, hooks, integration, merging]
requires: [hooks-overview, hooks-configuration]
related_to: [hooks-environment, hooks-events]
official_docs: https://code.claude.com/en/hooks
---

# Plugin Hooks

Plugins can provide hooks that integrate with user and project hooks.

## How Plugin Hooks Work

- Plugin hooks defined in `hooks/hooks.json` or custom path via `hooks` field
- When plugin is enabled, hooks are **merged** with user and project hooks
- Multiple hooks from different sources can respond to the same event
- Plugin hooks run **in parallel** with other matching hooks

## Plugin Hook Configuration

```json
{
  "description": "Automatic code formatting",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Plugin-specific fields:**
- `description`: Optional field to explain the hook's purpose
- `${CLAUDE_PLUGIN_ROOT}`: Absolute path to plugin directory

## Environment Variables

| Variable | Description |
|----------|-------------|
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory |
| `${CLAUDE_PROJECT_DIR}` | Project root (same as project hooks) |

## Hook Merging

When multiple sources define hooks:

1. User hooks (`~/.claude/settings.json`)
2. Project hooks (`.claude/settings.json`)
3. Plugin hooks (each enabled plugin)

All matching hooks execute in parallel. No source takes precedence—they all run.

## Key Points

- Plugin hooks in `hooks/hooks.json` or custom path
- Merged with user and project hooks
- All matching hooks run in parallel
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin file paths
- Optional `description` field documents purpose
