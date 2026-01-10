---
id: mcp-plugins
topic: Plugin-Provided MCP Servers
category: mcp
tags: [plugins, bundled, automatic, lifecycle]
requires: [mcp-overview]
related_to: [mcp-transports, plugins-overview]
official_docs: https://code.claude.com/en/mcp
---

# Plugin-Provided MCP Servers

Plugins can bundle MCP servers that start automatically when the plugin is enabled.

## Defining Plugin MCP Servers

### Option 1: `.mcp.json` at Plugin Root

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

### Option 2: Inline in `plugin.json`

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `${CLAUDE_PLUGIN_ROOT}` | Plugin installation directory (for relative paths) |
| `${VAR}` | Any user environment variable |

## Features

| Feature | Behavior |
|---------|----------|
| **Automatic lifecycle** | Servers start when plugin enables |
| **Restart required** | MCP server changes require Claude Code restart |
| **Transport support** | stdio, SSE, HTTP (varies by server) |
| **User environment** | Access to same env vars as manual servers |

## Viewing Plugin Servers

```bash
/mcp
```

Plugin servers appear in the list with indicators showing they come from plugins.

## Benefits

- **Bundled distribution** — Tools and servers packaged together
- **Automatic setup** — No manual MCP configuration needed
- **Team consistency** — Everyone gets same tools when plugin installed

## Key Points

- Define in `.mcp.json` at plugin root or inline in `plugin.json`
- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Servers start automatically but changes require restart
- Plugin servers managed through plugin installation, not `/mcp` commands
