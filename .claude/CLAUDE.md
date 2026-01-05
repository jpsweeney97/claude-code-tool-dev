# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This monorepo is the single source of truth for developing Claude Code extensions.

## Quick Reference

| Extension  | Create in                        | Test with                | Deploy with                             |
| ---------- | -------------------------------- | ------------------------ | --------------------------------------- |
| Skill      | `.claude/skills/<name>/SKILL.md` | `/<name>`                | `uv run scripts/promote skill <name>`   |
| Command    | `.claude/commands/<name>.md`     | `/<name>`                | `uv run scripts/promote command <name>` |
| Agent      | `.claude/agents/<name>.md`       | Task tool                | `uv run scripts/promote agent <name>`   |
| Hook       | `.claude/hooks/<name>.py`        | After sync-settings      | `uv run scripts/promote hook <name>`    |
| Plugin     | `packages/plugins/<name>/`       | After marketplace update | `claude plugin install <name>@tool-dev` |
| MCP Server | `packages/mcp-servers/<name>/`   | After build              | Manual: `claude mcp add`                |

## Workflow

```
CREATE in .claude/  →  TEST locally  →  PROMOTE to ~/.claude/
```

**Why this works:**

- Project-local `.claude/` is auto-discovered by Claude Code
- Sandbox testing requires no setup
- Promotion is explicit with validation

## Plugin Workflow

Plugins use the marketplace system instead of the promote script.

**This repo is registered as the `tool-dev` marketplace:**

```
.claude-plugin/marketplace.json  →  indexes packages/plugins/*
```

**Development cycle:**

1. Edit plugin in `packages/plugins/<name>/`
2. Update version in `.claude-plugin/plugin.json`
3. Refresh: `claude plugin marketplace update tool-dev`
4. Reinstall: `claude plugin install <name>@tool-dev`
5. Restart Claude Code

**Available plugins:** deep-analysis, doc-auditor, docs-kb, ecosystem-builder, persistent-tasks, plugin-dev, session-log

**Plugin manifest requirements** (`.claude-plugin/plugin.json`):

- `author` must be object: `{"name": "..."}` not string
- Paths must start with `./`: `"./skills/"` not `"skills/"`
- Use `mcpServers` not `mcp` for MCP config

### Plugin Installation Internals

Plugin installation is a two-step process:

1. **Cache creation** — Plugin files copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
2. **Registration** — Entry added to `~/.claude/plugins/installed_plugins.json`

**Important behaviors:**

- Skills are loaded at session start — new installs require Claude Code restart
- Cache can exist without registration (orphaned cache)
- Registration without cache causes skill loading errors

**Troubleshooting plugin issues:**

```bash
# Check if plugin is registered
cat ~/.claude/plugins/installed_plugins.json | jq '.["<plugin>@<marketplace>"]'

# Check if cache exists
ls ~/.claude/plugins/cache/<marketplace>/<plugin>/

# Fix: reinstall to sync cache and registration
claude plugin install <plugin>@<marketplace>
```

**Common failure mode:** Plugin appears installed (cache exists) but skills don't load because registration is missing. Always verify both cache AND registration exist.

## Scripts

| Script                                 | Purpose                                     |
| -------------------------------------- | ------------------------------------------- |
| `uv run scripts/inventory`             | Scan sources, generate migration YAML       |
| `uv run scripts/migrate`               | Process inventory, copy to monorepo         |
| `uv run scripts/promote <type> <name>` | Validate and deploy to ~/.claude/           |
| `uv run scripts/sync-settings`         | Rebuild settings.json from hook frontmatter |

## Skill Precedence

Personal (`~/.claude/skills/`) overrides project (`.claude/skills/`).

**Testing changes to existing skills:**

1. Create `.claude/skills/<name>-dev/SKILL.md`
2. Test with `/<name>-dev`
3. When ready, promote (overwrites production)

## Hook Frontmatter

Hooks require frontmatter for sync-settings to work:

```python
#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Bash
# timeout: 60000
# ///
```

## Directory Structure

```
.claude/
├── skills/       # 14 skills (SKILL.md required)
├── hooks/        # 5 Python hooks
├── rules/        # Path-specific context (auto-discovered)
├── commands/     # Slash commands (placeholder)
└── agents/       # Subagents (placeholder)

packages/
├── plugins/      # 7 plugin packages (deep-analysis, doc-auditor, etc.)
└── mcp-servers/  # TypeScript MCP servers (placeholder)

scripts/          # Python utility scripts (PEP 723)
old-repos/        # Archived source repos (gitignored)
```

## Architecture

### Skill Structures

Skills follow two patterns:

**Minimal** (4 skills): Just `SKILL.md` with basic frontmatter

```
.claude/skills/<name>/
└── SKILL.md
```

**Full** (10 skills): Extended structure with references and scripts

```
.claude/skills/<name>/
├── SKILL.md           # Required
├── references/        # Deep documentation
├── scripts/           # Automation (stdlib only, no PEP 723)
├── templates/         # Output templates
└── assets/            # Images, prompts
```

### Script Conventions

**Top-level scripts** (`scripts/`): Use PEP 723 metadata, external deps allowed

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "rich"]
# ///
```

**Skill-embedded scripts**: Standard library only, no PEP 723

```python
#!/usr/bin/env python3
# Exit codes: 0=success, 1=input error, 2=system error
```

### Hook Exit Codes

- `0` - Allow/success
- `1` - Error (logged but doesn't block)
- `2` - Block with message to Claude

## Current State

- **Commands/Agents/MCP Servers**: Placeholders only, workflow documented but not populated
- **Hooks**: Exist and work, but missing PEP 723 frontmatter (sync-settings won't detect them)
- **Plugins**: 7 plugins in `packages/plugins/`, deployed via `tool-dev` marketplace
