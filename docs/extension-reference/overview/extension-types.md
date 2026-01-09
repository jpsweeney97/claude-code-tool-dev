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

## Key Points

- Start simple (commands), grow as needed (skills → plugins)
- Extensions are composable: plugins bundle skills, skills define hooks
- User scope overrides project scope for same-named extensions
