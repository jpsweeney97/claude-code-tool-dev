# Claude Code Extension Development

This monorepo is the single source of truth for developing Claude Code extensions.

## Quick Reference

| Extension | Create in | Test with | Promote with |
|-----------|-----------|-----------|--------------|
| Skill | `.claude/skills/<name>/SKILL.md` | `/<name>` | `uv run scripts/promote skill <name>` |
| Command | `.claude/commands/<name>.md` | `/<name>` | `uv run scripts/promote command <name>` |
| Agent | `.claude/agents/<name>.md` | Task tool | `uv run scripts/promote agent <name>` |
| Hook | `.claude/hooks/<name>.py` | After sync-settings | `uv run scripts/promote hook <name>` |
| MCP Server | `packages/mcp-servers/<name>/` | After build | `uv run scripts/promote mcp-server <name>` |

## Workflow

```
CREATE in .claude/  →  TEST locally  →  PROMOTE to ~/.claude/
```

**Why this works:**
- Project-local `.claude/` is auto-discovered by Claude Code
- Sandbox testing requires no setup
- Promotion is explicit with validation

## Scripts

| Script | Purpose |
|--------|---------|
| `uv run scripts/inventory` | Scan sources, generate migration YAML |
| `uv run scripts/migrate` | Process inventory, copy to monorepo |
| `uv run scripts/promote <type> <name>` | Validate and deploy to ~/.claude/ |
| `uv run scripts/sync-settings` | Rebuild settings.json from hook frontmatter |

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
├── commands/     # Slash commands
├── agents/       # Subagents
├── skills/       # Skills
├── hooks/        # Hook scripts
├── rules/        # Path-specific context (auto-discovered)
└── settings.json # Hook wiring + config

packages/
├── mcp-servers/  # TypeScript MCP servers
└── plugins/      # Plugin packages

scripts/          # Python utility scripts (PEP 723)
```
