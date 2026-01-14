# CLAUDE.md Redesign

**Date:** 2026-01-10
**Status:** Proposed

## Summary

Redesign CLAUDE.md to follow context engineering best practices: reduce from 278 lines to ~82 lines by deferring component-specific guidance to path-scoped rules files.

## Rationale

Based on guidance from:
- `/Users/jp/Documents/writing-a-good-CLAUDE.md.md` — Less is more, progressive disclosure, <300 lines
- `docs/documentation/claude.md-reference.md` — Path-scoped rules, @import syntax

Key insights:
1. Rules in `.claude/rules/` load automatically when working with matching files
2. Current CLAUDE.md duplicates content that exists in rules files (2,732 lines total)
3. Component counts drift (claimed 14 skills, actual 19)
4. @imports enable progressive disclosure without bloating context

## Design Principles

| Principle | Application |
|-----------|-------------|
| Universal applicability | Only content relevant to every task |
| Progressive disclosure | Point to rules/, don't duplicate |
| No drifting content | Remove counts, lists that need maintenance |
| File boundaries | Show structure, not exhaustive inventory |

## Proposed CLAUDE.md

```markdown
# CLAUDE.md

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

Extensions are developed in `.claude/` and `packages/`, tested locally, then promoted to `~/.claude/` for production use. Component-specific guidance lives in `.claude/rules/` and loads automatically when working with matching files.

## Directory Structure

```
.claude/
├── skills/       # Skill definitions (SKILL.md required)
├── hooks/        # Python event hooks
├── commands/     # Slash command definitions
├── agents/       # Subagent definitions
├── rules/        # Path-scoped guidance — READ BEFORE CREATING
├── handoffs/     # Session continuity documents
└── references/   # Framework documentation

packages/
├── plugins/      # Plugin packages (marketplace: tool-dev)
└── mcp-servers/  # TypeScript MCP servers

scripts/          # Utility scripts (inventory, migrate, promote, sync-settings)
docs/             # Reference documentation and plans
```

## Workflow

```
CREATE in .claude/ or packages/  →  TEST locally  →  PROMOTE to ~/.claude/
```

### Creating Extensions

| Extension | Create in | Test with |
|-----------|-----------|-----------|
| Skill | `.claude/skills/<name>/SKILL.md` | `/<name>` |
| Command | `.claude/commands/<name>.md` | `/<name>` |
| Hook | `.claude/hooks/<name>.py` | After sync-settings |
| Agent | `.claude/agents/<name>.md` | Task tool |
| Plugin | `packages/plugins/<name>/` | Marketplace install |
| MCP Server | `packages/mcp-servers/<name>/` | After build |

### Promoting to Production

```bash
uv run scripts/promote <type> <name>   # Validate and deploy to ~/.claude/
```

### Plugin Development

Plugins use the `tool-dev` marketplace instead of the promote script:

```bash
claude plugin marketplace update tool-dev
claude plugin install <name>@tool-dev
```

## References

### Rules (Path-Scoped)

Detailed guidance for each extension type lives in `.claude/rules/`. These files load automatically when you work with matching files, but **read the relevant rule before starting work on a new extension**:

| Working on... | Read first |
|---------------|------------|
| Skills | @.claude/rules/skills.md |
| Hooks | @.claude/rules/hooks.md |
| Commands | @.claude/rules/commands.md |
| Agents | @.claude/rules/agents.md |
| Plugins | @.claude/rules/plugins.md |
| MCP Servers | @.claude/rules/mcp-servers.md |
| Settings | @.claude/rules/settings.md |

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`
```

## Comparison

| Metric | Current | Proposed |
|--------|---------|----------|
| Lines | 278 | 82 |
| Reduction | — | 70% |
| Component-specific detail | Duplicated | Deferred to rules/ |
| Drifting counts | Yes | None |
| @imports | None | 7 |

## What Was Removed

| Content | Reason | New Location |
|---------|--------|--------------|
| Component counts (14 skills, etc.) | Drifts, not actionable | Discoverable via filesystem |
| Plugin workflow details | Component-specific | @.claude/rules/plugins.md |
| Hook frontmatter example | Component-specific | @.claude/rules/hooks.md |
| Plugin manifest fields | Component-specific | @.claude/rules/plugins.md |
| Script descriptions table | Low value | Inline in Scripts section |
| Architecture section | Component-specific | Individual rules files |
| Current state table | Drifts | Discoverable |

## Implementation

1. Back up current `.claude/CLAUDE.md`
2. Replace with proposed content
3. Verify @imports resolve correctly
4. Test with fresh Claude Code session
