---
id: plugins-examples
topic: Plugin Examples
category: plugins
tags: [examples, templates, patterns]
requires: [plugins-overview, plugins-manifest, plugins-components]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Examples

Complete working plugin configurations.

## Minimal Plugin

```json
{
  "name": "my-simple-plugin"
}
```

With directory structure:
```
my-simple-plugin/
├── .claude-plugin/
│   └── plugin.json
└── commands/
    └── hello.md
```

## Full-Featured Plugin

```json
{
  "name": "enterprise-tools",
  "version": "2.1.0",
  "description": "Enterprise workflow automation",
  "author": {
    "name": "Enterprise Team",
    "email": "enterprise@example.com"
  },
  "license": "MIT",
  "keywords": ["enterprise", "workflow"],
  "commands": "./commands/",
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
    "enterprise-db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

## Plugin with All Components

```
full-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── review.md
│   └── test.md
├── skills/
│   └── analysis/
│       └── SKILL.md
├── agents/
│   └── reviewer.md
├── hooks/
│   └── hooks.json
├── .mcp.json
├── .lsp.json
└── scripts/
    └── validate.sh
```

## Enterprise Plugin Layout

A complete plugin for production use:

```
enterprise-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── status.md
│   └── logs.md
├── skills/
│   ├── code-reviewer/
│   │   └── SKILL.md
│   └── pdf-processor/
│       ├── SKILL.md
│       └── scripts/
├── agents/
│   ├── security-reviewer.md
│   ├── performance-tester.md
│   └── compliance-checker.md
├── hooks/
│   ├── hooks.json
│   └── security-hooks.json
├── .mcp.json
├── .lsp.json
├── scripts/
│   ├── security-scan.sh
│   ├── format-code.py
│   └── deploy.js
├── LICENSE
└── CHANGELOG.md
```

Note: Only `plugin.json` belongs in `.claude-plugin/`. All component directories go at the plugin root.

## File Locations Reference

| Component | Default Location | Purpose |
|-----------|------------------|---------|
| **Manifest** | `.claude-plugin/plugin.json` | Required metadata file |
| **Commands** | `commands/` | Slash command Markdown files |
| **Agents** | `agents/` | Subagent Markdown files |
| **Skills** | `skills/` | Agent Skills with SKILL.md files |
| **Hooks** | `hooks/hooks.json` | Hook configuration |
| **MCP servers** | `.mcp.json` | MCP server definitions |
| **LSP servers** | `.lsp.json` | Language server configurations |

## External Dependencies

Plugins cannot reference files outside their directory (path traversal doesn't work). Two options:

**Option 1: Use symlinks**

Create symbolic links to external files. Symlinks are copied during installation:

```bash
# Inside your plugin directory
ln -s /path/to/shared-utils ./shared-utils
```

**Option 2: Restructure marketplace**

Set plugin path to a parent directory containing all required files:

```json
{
  "name": "my-plugin",
  "source": "./",
  "description": "Plugin that needs root-level access",
  "commands": ["./plugins/my-plugin/commands/"],
  "agents": ["./plugins/my-plugin/agents/"],
  "strict": false
}
```

The `strict: false` field allows the marketplace entry to override the plugin's own manifest. This copies the entire marketplace root, giving access to sibling directories.

## Key Points

- Start minimal, add components as needed
- Use inline hooks for simple cases
- Reference files for complex configurations
- Bundle supporting scripts in plugin
- Use symlinks for external dependencies
