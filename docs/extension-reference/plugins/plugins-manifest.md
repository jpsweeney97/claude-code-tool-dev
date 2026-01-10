---
id: plugins-manifest
topic: Plugin Manifest Schema
category: plugins
tags: [manifest, plugin-json, schema, configuration]
requires: [plugins-overview]
related_to: [plugins-components, plugins-paths]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Manifest Schema

The plugin manifest `.claude-plugin/plugin.json` defines plugin metadata and component locations.

## Full Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",

  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/yourname"
  },
  "license": "MIT",
  "keywords": ["code-review", "testing"],
  "homepage": "https://github.com/you/my-plugin",
  "repository": "https://github.com/you/my-plugin",

  "commands": "./commands/",
  "skills": "./skills/",
  "agents": ["./agents/reviewer.md"],
  "hooks": "./hooks/hooks.json",
  "mcpServers": "./.mcp.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique plugin identifier |
| `version` | string | No | Semver version string |
| `description` | string | No | Plugin purpose |
| `author` | object | No | Author info: `name` (required), `email` (optional), `url` (optional) |
| `license` | string | No | License type |
| `keywords` | array | No | Searchable keywords |
| `homepage` | string | No | Project homepage URL |
| `repository` | string | No | Source repository URL |
| `commands` | string/array | No | Command files/directory |
| `skills` | string/array | No | Skill directories |
| `agents` | array | No | Agent file paths |
| `hooks` | string/object | No | Hook config file or inline |
| `mcpServers` | string/object | No | MCP config file or inline |
| `lspServers` | string/object | No | LSP config file or inline |
| `outputStyles` | string/array | No | Output style files/directories |

## Key Points

- Only `name` is required
- Component paths use `./` prefix
- Can use directory (string) or explicit files (array)
- Hooks, MCP, LSP can be inline objects or file references
