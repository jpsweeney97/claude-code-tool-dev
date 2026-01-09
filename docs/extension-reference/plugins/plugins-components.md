---
id: plugins-components
topic: Plugin Component Types
category: plugins
tags: [components, commands, skills, agents, hooks, mcp, lsp]
requires: [plugins-overview, plugins-manifest]
related_to: [plugins-paths]
official_docs: https://code.claude.com/en/plugins
---

# Plugin Component Types

Plugins can bundle 6 types of components.

## Component Reference

| Component | Manifest Key | Location | Notes |
|-----------|--------------|----------|-------|
| Commands | `commands` | `commands/` | Markdown files |
| Skills | `skills` | `skills/` | Directories with SKILL.md |
| Agents | `agents` | `agents/` | Markdown files |
| Hooks | `hooks` | `hooks/` or inline | JSON configuration |
| MCP Servers | `mcpServers` | `.mcp.json` or inline | Server definitions |
| LSP Servers | `lspServers` | `.lsp.json` or inline | Language servers |

## Commands

Standard command markdown files:

```json
{
  "commands": "./commands/"
}
```

Or explicit list:

```json
{
  "commands": ["./commands/review.md", "./commands/test.md"]
}
```

## Skills

Skill directories containing SKILL.md:

```json
{
  "skills": "./skills/"
}
```

## Agents

Agent definition files:

```json
{
  "agents": ["./agents/reviewer.md", "./agents/analyzer.md"]
}
```

## Hooks

File reference or inline:

```json
{
  "hooks": "./hooks/hooks.json"
}
```

Or inline:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "./validate.sh"}]
    }]
  }
}
```

**Plugin-only hook type**: Plugins support `type: "agent"` hooks.

## MCP Servers

```json
{
  "mcpServers": {
    "database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

## LSP Servers

```json
{
  "lspServers": "./.lsp.json"
}
```

## Key Points

- All 6 component types are optional
- Use directory paths for auto-discovery
- Use array for explicit file lists
- Hooks, MCP, LSP support inline definitions
