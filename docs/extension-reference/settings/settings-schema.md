---
id: settings-schema
topic: Full Settings Schema
category: settings
tags: [schema, reference, complete]
requires: [settings-overview, settings-permissions, settings-sandbox]
related_to: [settings-examples, settings-authentication, settings-attribution, settings-file-suggestion, settings-plugins-advanced, settings-environment-variables, settings-tools]
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
  "allowedMcpServers": [],
  "deniedMcpServers": [],
  "enabledPlugins": { },
  "extraKnownMarketplaces": { },
  "strictKnownMarketplaces": [],
  "outputStyle": "Explanatory",
  "statusLine": { },
  "fileSuggestion": { },
  "respectGitignore": true,
  "env": { },
  "attribution": { },
  "apiKeyHelper": "",
  "otelHeadersHelper": "",
  "forceLoginMethod": "",
  "forceLoginOrgUUID": "",
  "awsAuthRefresh": "",
  "awsCredentialExport": "",
  "companyAnnouncements": [],
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
| `allowManagedHooksOnly` | boolean | Only run managed hooks (managed settings only) |

#### Hook Configuration (Managed Only)

When `allowManagedHooksOnly` is `true`:
- Managed hooks and SDK hooks are loaded
- User hooks, project hooks, and plugin hooks are blocked

### MCP

| Field | Type | Description |
|-------|------|-------------|
| `enableAllProjectMcpServers` | boolean | Enable project .mcp.json |
| `enabledMcpjsonServers` | array | Enabled MCP servers |
| `disabledMcpjsonServers` | array | Disabled MCP servers |
| `allowedMcpServers` | array | MCP server allowlist (managed only) |
| `deniedMcpServers` | array | MCP server denylist (managed only) |

### Plugins

| Field | Type | Description |
|-------|------|-------------|
| `enabledPlugins` | object | Plugin enable/disable map |
| `extraKnownMarketplaces` | object | Additional marketplaces |
| `strictKnownMarketplaces` | array | Marketplace allowlist (managed only) |

See [settings-plugins-advanced](settings-plugins-advanced.md) for details.

### Authentication

| Field | Type | Description |
|-------|------|-------------|
| `apiKeyHelper` | string | Script to generate auth value |
| `otelHeadersHelper` | string | Script for OTEL headers |
| `forceLoginMethod` | string | Restrict login method |
| `forceLoginOrgUUID` | string | Auto-select organization |
| `awsAuthRefresh` | string | AWS auth refresh script |
| `awsCredentialExport` | string | AWS credential export script |

See [settings-authentication](settings-authentication.md) for details.

### Display

| Field | Type | Description |
|-------|------|-------------|
| `outputStyle` | string | Output verbosity |
| `statusLine` | object | Status line config |
| `fileSuggestion` | object | Custom file autocomplete |
| `respectGitignore` | boolean | Filter `.gitignore` in picker |
| `language` | string | Response language |
| `alwaysThinkingEnabled` | boolean | Enable extended thinking |

See [settings-file-suggestion](settings-file-suggestion.md) for fileSuggestion details.

### Other

| Field | Type | Description |
|-------|------|-------------|
| `env` | object | Environment variables for sessions |
| `attribution` | object | Git commit/PR attribution |
| `companyAnnouncements` | array | Startup announcements. Multiple announcements cycle randomly. |
| `cleanupPeriodDays` | number | Session cleanup period. Set to `0` to delete all sessions immediately. (default: 30) |

See [settings-attribution](settings-attribution.md) for attribution details.

### Deprecated Settings

| Field | Replacement |
|-------|-------------|
| `includeCoAuthoredBy` | Use `attribution` instead. See [settings-attribution](settings-attribution.md). |

## Key Points

- All fields are optional
- Fields merge across scopes
- Use specific field groups as needed
