---
id: settings-schema
topic: Full Settings Schema
category: settings
tags: [schema, reference, complete]
requires: [settings-overview, settings-permissions, settings-sandbox]
related_to: [settings-examples]
official_docs: https://code.claude.com/en/settings
---

# Full Settings Schema

Complete reference for settings.json structure.

## Schema Overview

```json
{
  "permissions": { },
  "model": "claude-sonnet-4-5-20250929",
  "hooks": { },
  "disableAllHooks": false,
  "allowManagedHooksOnly": true,
  "sandbox": { },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": [],
  "disabledMcpjsonServers": [],
  "enabledPlugins": { },
  "extraKnownMarketplaces": { },
  "outputStyle": "Explanatory",
  "statusLine": { },
  "env": { },
  "attribution": { },
  "cleanupPeriodDays": 30,
  "language": "japanese",
  "alwaysThinkingEnabled": true
}
```

## Field Groups

### Permissions

| Field | Type | Description |
|-------|------|-------------|
| `permissions.allow` | array | Auto-allowed patterns |
| `permissions.ask` | array | Prompt-required patterns |
| `permissions.deny` | array | Blocked patterns |
| `permissions.defaultMode` | string | Default permission mode |
| `permissions.additionalDirectories` | array | Extra allowed directories |

### Hooks

| Field | Type | Description |
|-------|------|-------------|
| `hooks` | object | Hook configurations |
| `disableAllHooks` | boolean | Disable all hooks |
| `allowManagedHooksOnly` | boolean | Only run managed hooks |

### MCP

| Field | Type | Description |
|-------|------|-------------|
| `enableAllProjectMcpServers` | boolean | Enable project .mcp.json |
| `enabledMcpjsonServers` | array | Enabled MCP servers |
| `disabledMcpjsonServers` | array | Disabled MCP servers |

### Display

| Field | Type | Description |
|-------|------|-------------|
| `outputStyle` | string | Output verbosity |
| `statusLine` | object | Status line config |
| `language` | string | UI language |
| `alwaysThinkingEnabled` | boolean | Show thinking |

## Key Points

- All fields are optional
- Fields merge across scopes
- Use specific field groups as needed
