---
id: extension-types
topic: Extension Types Overview
category: overview
tags: [commands, skills, agents, hooks, mcp, lsp, plugins, comparison]
related_to: [when-to-use, precedence]
official_docs: https://code.claude.com/docs/llms.txt
---

# Extension Types

Claude Code supports 6 extension types plus plugins for bundling.

## Comparison Matrix

| Type | Complexity | Isolation | Invocation | Event-Driven |
|------|------------|-----------|------------|--------------|
| Commands | Lowest | None | `/command` | No |
| Skills | Medium | Optional fork | `/skill` or auto | No |
| Agents | Medium-High | Full context | Task tool | No |
| Hooks | Medium | Process-level | Automatic | Yes |
| MCP Servers | High | Separate process | Tool calls | No |
| LSP Servers | High | Separate process | Automatic | No |

## Extension Purposes

- **Commands**: Simple prompt templates, no logic
- **Skills**: Complex workflows with verification and decision points
- **Agents**: Autonomous background tasks in separate context
- **Hooks**: React to events (validate, log, transform, block)
- **MCP Servers**: Integrate external tools, databases, APIs
- **LSP Servers**: Code intelligence (diagnostics, go-to-definition)
- **Plugins**: Bundle any of the above for distribution

## Design Philosophy

### Composition Over Inheritance

Extensions compose rather than inherit. A plugin bundles commands, skills, and hooks but doesn't create a new extension type.

### Single Responsibility

Each extension type serves one purpose:

| Type | Single Purpose |
|------|----------------|
| Commands | User-invoked actions |
| Skills | Domain knowledge for Claude |
| Hooks | Event-driven automation |
| Agents | Autonomous task execution |
| MCP | External tool integration |
| LSP | Code intelligence |

### Progressive Disclosure

Start simple, add complexity as needed:

1. **Command** — Single action
2. **Skill** — Domain expertise
3. **Hook** — Automation
4. **Agent** — Autonomy
5. **Plugin** — Distribution

## Decision Guide

### "I want Claude to..."

| Goal | Extension |
|------|-----------|
| Run a specific action when I type `/foo` | Command |
| Know how to do X better | Skill |
| React automatically when Y happens | Hook |
| Work independently on complex tasks | Agent |
| Connect to external service Z | MCP Server |
| Share my extensions with others | Plugin |

### Complexity Indicators

| Signal | Suggests |
|--------|----------|
| User explicitly triggers | Command |
| Claude needs domain knowledge | Skill |
| "Whenever X, do Y" | Hook |
| Multiple steps, decisions | Agent |
| External API/database | MCP Server |
| Bundle for distribution | Plugin |

### Migration Path

```
Command → Skill → Plugin
   ↓         ↓
 Hook → Agent → Plugin
```

Extensions naturally evolve: a command becomes a skill when it needs verification steps; a skill becomes a plugin when sharing with others.

## Key Points

- Start simple (commands), grow as needed (skills → plugins)
- Extensions are composable: plugins bundle skills, skills define hooks
- User scope overrides project scope for same-named extensions
