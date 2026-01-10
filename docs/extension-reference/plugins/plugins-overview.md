---
id: plugins-overview
topic: Plugins Overview
category: plugins
tags: [plugins, distribution, bundle, packaging]
related_to: [plugins-manifest, plugins-components, marketplaces-overview]
official_docs: https://code.claude.com/en/plugins
---

# Plugins Overview

Plugins bundle multiple extension types for distribution. A single plugin can contain commands, skills, agents, hooks, MCP servers, and LSP servers.

## Purpose

- Bundle multiple extensions together
- Distribute via marketplaces
- Share tools across teams
- Package complete workflows

## When to Use Plugins

- **Bundling related extensions**: Group skills, commands, agents that work together
- **Team distribution**: Share curated tooling via git-based marketplaces
- **Versioned releases**: Semantic versioning with changelog tracking
- **Cross-project reuse**: Install once, use across multiple projects

## When NOT to Use Plugins

- **Single skill/command**: Just create in `.claude/skills/` or `.claude/commands/`
- **Project-specific tooling**: Use local `.claude/` directory
- **Rapid iteration**: Plugin installation adds overhead; develop locally first
- **Simple hooks**: Use `settings.json` hooks directly

## Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest (required)
├── commands/                 # Slash commands
│   └── review.md
├── skills/                   # Skills
│   └── analysis/
│       └── SKILL.md
├── agents/                   # Subagents
│   └── reviewer.md
├── hooks/
│   └── hooks.json           # Hook definitions
├── .mcp.json                # MCP servers
├── .lsp.json                # LSP servers
└── scripts/                 # Supporting scripts
    └── validate.sh
```

## Plugin Components

| Component | Directory/File | Description |
|-----------|---------------|-------------|
| Commands | `commands/` | Slash commands |
| Skills | `skills/` | Skill workflows |
| Agents | `agents/` | Subagent definitions |
| Hooks | `hooks/` or inline | Event handlers |
| MCP | `.mcp.json` | External tool servers |
| LSP | `.lsp.json` | Language servers |

## Key Points

- Plugin manifest in `.claude-plugin/plugin.json`
- Can bundle any combination of components
- Distributed via marketplaces
- Installed to `~/.claude/plugins/cache/`
