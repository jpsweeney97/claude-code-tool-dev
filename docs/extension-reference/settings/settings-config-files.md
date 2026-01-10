---
id: settings-config-files
topic: Configuration Files
category: settings
tags: [config, files, claude.json, scopes]
requires: [settings-overview, settings-scopes]
related_to: [settings-schema, mcp-overview, agents-overview]
official_docs: https://code.claude.com/en/settings
---

# Configuration Files

Claude Code uses multiple configuration files across different scopes.

## File Locations by Feature

| Feature | User | Project | Local |
|---------|------|---------|-------|
| Settings | `~/.claude/settings.json` | `.claude/settings.json` | `.claude/settings.local.json` |
| Subagents | `~/.claude/agents/` | `.claude/agents/` | — |
| MCP servers | `~/.claude.json` | `.mcp.json` | `~/.claude.json` (per-project) |
| Plugins | `~/.claude/settings.json` | `.claude/settings.json` | `.claude/settings.local.json` |
| CLAUDE.md | `~/.claude/CLAUDE.md` | `CLAUDE.md` or `.claude/CLAUDE.md` | `CLAUDE.local.md` |

## ~/.claude.json

The `~/.claude.json` file stores runtime state and user-scoped MCP configuration.

**Contents:**
- Preferences (theme, notification settings, editor mode)
- OAuth session
- MCP server configurations for user and local scopes
- Per-project state (allowed tools, trust settings)
- Various caches

**Note:** This file is managed by Claude Code. Edit `~/.claude/settings.json` for persistent configuration.

## Subagent Locations

Custom subagents are stored as Markdown files with YAML frontmatter:

| Scope | Location | Shared |
|-------|----------|--------|
| User | `~/.claude/agents/` | No |
| Project | `.claude/agents/` | Yes (git) |

See [agents documentation](/en/sub-agents) for details on creating subagents.

## Key Points

- Settings files use JSON, memory files use Markdown
- `~/.claude.json` is runtime state, not configuration
- Subagents follow same scope pattern as settings
- Project files are shared via git; local files are not
