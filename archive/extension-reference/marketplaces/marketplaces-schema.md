---
id: marketplaces-schema
topic: Marketplace Schema
category: marketplaces
tags: [schema, marketplace-json, configuration]
requires: [marketplaces-overview]
related_to: [marketplaces-sources, marketplaces-examples]
official_docs: https://code.claude.com/en/plugin-marketplaces
---

# Marketplace Schema

The marketplace file `.claude-plugin/marketplace.json` defines the plugin catalog.

## Full Schema

```json
{
  "name": "company-tools",
  "owner": {
    "name": "DevTools Team",
    "email": "devtools@example.com"
  },
  "metadata": {
    "description": "Internal development tools",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-formatter",
      "source": "./plugins/formatter",
      "description": "Automatic code formatting",
      "version": "2.1.0"
    }
  ]
}
```

## Marketplace-Level Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace identifier (kebab-case). Users see this when installing: `/plugin install tool@marketplace-name` |
| `owner` | object | Marketplace maintainer information (see Owner Fields below) |
| `plugins` | array | List of available plugins |

### Owner Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the maintainer or team |
| `email` | string | No | Contact email for the maintainer |

### Optional Metadata

| Field | Type | Description |
|-------|------|-------------|
| `metadata.description` | string | Brief marketplace description |
| `metadata.version` | string | Marketplace version |
| `metadata.pluginRoot` | string | Base directory prepended to relative plugin source paths. Example: `"./plugins"` lets you write `"source": "formatter"` instead of `"source": "./plugins/formatter"` |

## Plugin Entry Fields

Each plugin entry in the `plugins` array describes a plugin and where to find it. Plugin entries can include any field from the plugin manifest schema. The marketplace-specific fields (`source`, `category`, `tags`, `strict`) are additions to that base schema.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (kebab-case). Users see this when installing: `/plugin install plugin-name@marketplace` |
| `source` | string/object | Where to fetch the plugin from. See [marketplaces-sources](marketplaces-sources.md) |

### Standard Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief plugin description |
| `version` | string | Semver version string |
| `author` | object | Plugin author information (`name` required, `email` optional) |
| `homepage` | string | Plugin homepage or documentation URL |
| `repository` | string | Source code repository URL |
| `license` | string | SPDX license identifier (e.g., MIT, Apache-2.0) |
| `keywords` | array | Tags for plugin discovery and categorization |
| `category` | string | Plugin category for organization |
| `tags` | array | Tags for searchability |
| `strict` | boolean | When `true` (default), plugin source must contain `plugin.json`. When `false`, marketplace entry defines everything about the plugin |

### Component Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `commands` | string/array | Custom paths to command files or directories |
| `agents` | string/array | Custom paths to agent files |
| `hooks` | string/object | Custom hooks configuration or path to hooks file |
| `mcpServers` | string/object | MCP server configurations or path to MCP config |
| `lspServers` | string/object | LSP server configurations or path to LSP config |

**Example with component paths:**

```json
{
  "name": "enterprise-tools",
  "source": "./plugins/enterprise",
  "strict": false,
  "commands": ["./commands/core/", "./commands/admin/"],
  "agents": ["./agents/security-reviewer.md"],
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
      }]
    }]
  },
  "mcpServers": {
    "db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server"
    }
  }
}
```

**Key points about this example:**

- **Multiple paths:** `commands` and `agents` accept arrays with directories and individual files
- **`${CLAUDE_PLUGIN_ROOT}`:** Required in hooks and MCP configs—resolves to the plugin's installed cache location
- **`strict: false`:** Marketplace entry defines everything; plugin doesn't need its own `plugin.json`

## Key Points

- Only `name` and `source` are required per plugin
- `strict: false` allows inline plugin definition without separate `plugin.json`
- Marketplace metadata is optional but recommended
- Use `${CLAUDE_PLUGIN_ROOT}` in hooks/MCP configs for installed plugin paths
