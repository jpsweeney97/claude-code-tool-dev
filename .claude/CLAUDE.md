# CLAUDE.md

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

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

**Plugin manifest** (`.claude-plugin/plugin.json`):

Required fields:
- `name`, `version`, `description`
- `author`: `{"name": "..."}` (object format)

Optional fields:
- `license`, `keywords`, `homepage`
- `skills`: `"./skills/"` (directory) or `["./skills/one.md"]` (array)
- `commands`: `"./commands/"` (directory)
- `agents`: `["./agents/analyzer.md"]` (array of file paths)
- `mcpServers`: `"./.mcp.json"` (file reference)

All paths use `./` prefix for portability across plugin installations.

### Plugin pyproject.toml

Plugins with Python code use `dependency-groups` (PEP 735) for dev dependencies, NOT `optional-dependencies`:

```toml
# Correct — dev tools hidden from users
[dependency-groups]
dev = ["pytest>=8.0"]

# Wrong — exposes dev tools as installable extras
[project.optional-dependencies]
dev = ["pytest>=8.0"]  # Users can accidentally: pip install plugin[dev]
```

**Why:** When plugins are published, `optional-dependencies` exposes dev tools as user-installable extras. `dependency-groups` keeps dev tools invisible to end users.

**Install dev deps:** `uv sync --group dev` (not `--extra dev`)

### Plugin Installation Internals

Plugin installation is a two-step process:

1. **Cache creation** — Plugin files copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
2. **Registration** — Entry added to `~/.claude/plugins/installed_plugins.json`

| Condition | Result |
|-----------|--------|
| New plugin installed | Restart Claude Code (skills load at session start) |
| Cache exists, no registration | Orphaned cache, plugin won't load |
| Registration exists, no cache | Skill loading errors |

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

## Rules Directory

`.claude/rules/` contains path-scoped context files that Claude Code auto-discovers. Each rule provides guidance when working in specific areas:

| File | Scope |
|------|-------|
| `skills.md` | Skill development conventions |
| `hooks.md` | Hook development conventions |
| `commands.md` | Command development conventions |
| `agents.md` | Agent development conventions |
| `mcp-servers.md` | MCP server development conventions |

Rules are loaded automatically based on file paths being edited.

## Command Format

Commands use YAML frontmatter with `$ARGUMENTS` substitution:

```markdown
---
description: What this command does
argument-hint: <optional hint shown to user>
---

Command instructions here.

User provided: $ARGUMENTS
```

## Directory Structure

```
.claude/
├── skills/       # 14 skills (SKILL.md required)
├── hooks/        # 5 Python hooks
├── rules/        # Path-specific context (auto-discovered)
├── commands/     # 11 slash commands (adr, audit, cli, explore, etc.)
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

**Minimal**: Just `SKILL.md` (e.g., config-optimize, deep-synthesis)

```
.claude/skills/<name>/
└── SKILL.md
```

**Extended**: Additional supporting files as needed

```
.claude/skills/<name>/
├── SKILL.md           # Required
├── references/        # Deep documentation (optional)
├── scripts/           # Automation - stdlib only, no PEP 723 (optional)
├── templates/         # Output templates (optional)
└── assets/            # Images, prompts (optional)
```

**SKILL.md frontmatter** supports these fields:

```yaml
---
name: skill-name
description: One-line description
license: MIT                              # optional
metadata:                                 # optional block
  version: "1.0.0"
  model: claude-opus-4-5-20251101        # recommended model
  timelessness_score: 8                  # quality indicator 1-10
---
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

**Skill-embedded scripts**: Standard library only (skills execute in environments that may lack package managers)

```python
#!/usr/bin/env python3
# Exit codes: 0=success, 1=input error, 2=system error
```

### Why PEP 723 (No Root pyproject.toml)

This is a **federated monorepo** — plugins are independent packages with their own `pyproject.toml`, and top-level scripts are cross-package utilities. PEP 723 inline metadata is intentional:

| Benefit | Explanation |
|---------|-------------|
| Zero-setup execution | `uv run scripts/promote skill foo` works without `uv sync` first |
| Script independence | Each script declares exactly what it needs |
| Portability | Scripts can be copied to other repos and still work |
| No shared state | No root `.venv` to maintain or sync |

**When to reconsider:** If many scripts share the same dependencies, a root `pyproject.toml` with `[dependency-groups] dev` may reduce duplication.

**Plugin packages** use standard `pyproject.toml` with `[dependency-groups] dev` for their own dev tools — this follows the "git repo → project-level deps" rule at the package level.

### Hook Exit Codes

- `0` - Allow/success
- `1` - Error (logged but doesn't block)
- `2` - Block with message to Claude

## Current State

| Component | Status | Action |
|-----------|--------|--------|
| Commands | 11 implemented | Ready to use |
| Plugins | 7 packages | Deploy via `tool-dev` marketplace |
| Hooks | Work, missing frontmatter | Add frontmatter to enable sync-settings |
| Agents | Placeholder | Create in `.claude/agents/` when needed |
| MCP Servers | Placeholder | Create in `packages/mcp-servers/` when needed |
