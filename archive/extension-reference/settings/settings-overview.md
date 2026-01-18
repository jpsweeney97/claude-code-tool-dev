---
id: settings-overview
topic: Settings Overview
category: settings
tags: [settings, configuration, preferences]
related_to: [settings-scopes, settings-permissions, settings-schema, settings-environment-variables, settings-tools]
official_docs: https://code.claude.com/en/settings
---

# Settings Overview

Settings control Claude Code behavior, permissions, hooks, and integrations.

## Purpose

- Configure permissions and restrictions
- Define hooks for automation
- Set model and display preferences
- Configure sandbox and security

## Configuration System

| Component | Format | Purpose |
|-----------|--------|---------|
| Memory files (CLAUDE.md) | Markdown | Instructions and context loaded at startup |
| Settings files | JSON | Permissions, environment variables, tool behavior |
| Slash commands | Markdown | Custom `/command-name` invocations |
| MCP servers | JSON | Additional tools and integrations |

Settings merge across scopes, with more specific settings overriding broader ones.

## Configuration Files

| Scope | File | Purpose |
|-------|------|---------|
| Managed | `managed-settings.json` | IT/enterprise policies |
| User | `~/.claude/settings.json` | Personal defaults |
| Project | `.claude/settings.json` | Team-shared settings |
| Local | `.claude/settings.local.json` | Personal project overrides |

## Precedence (Highest to Lowest)

1. **Managed** — Cannot be overridden
2. **Command line** — Flags passed to `claude`
3. **Local** — Personal project overrides
4. **Project** — Team-shared
5. **User** — Personal defaults

## Key Points

- Settings are JSON files
- Higher scope always wins
- Deny rules override allow rules
- Local for testing before promoting to project
- Claude Code's internal system prompt is not published; use `CLAUDE.md` files or `--append-system-prompt` flag for custom instructions
