---
id: index
topic: Claude Code Extension System Reference
category: index
tags: [extensions, reference, navigation]
official_docs: https://code.claude.com/docs/llms.txt
---

# Extension System Reference

Machine-optimized reference for Claude Code extensions. Each file covers one concept.

## Categories

| Category | Files | Description |
|----------|-------|-------------|
| [overview/](./overview/) | 3 | Extension types, decision guidance, precedence |
| [commands/](./commands/) | 4 | Slash command creation |
| [skills/](./skills/) | 6 | Complex workflow skills |
| [agents/](./agents/) | 7 | Autonomous subagents |
| [hooks/](./hooks/) | 8 | Event-driven automation |
| [mcp/](./mcp/) | 7 | Model Context Protocol servers |
| [lsp/](./lsp/) | 3 | Language Server Protocol |
| [plugins/](./plugins/) | 6 | Bundled distribution |
| [marketplaces/](./marketplaces/) | 4 | Plugin distribution |
| [settings/](./settings/) | 6 | Configuration |
| [security/](./security/) | 4 | Managed deployment |

## Frontmatter Schema

All files use:
- `id`: Unique identifier (matches filename)
- `topic`: Display title
- `category`: Parent category
- `tags`: Searchable terms
- `requires`: Prerequisites
- `related_to`: Sibling concepts
- `official_docs`: Anthropic documentation URL

## Source Documents

- Human-readable: `docs/claude-code-extension-system.md`
- Official: `docs/documentation/*.md`
