# CLAUDE.md

## Project Overview

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

- Important specific guidance lives in `.claude/rules/`.

## How This Repo Works

- Extensions are developed in `.claude/` and `packages/`
- When extensions are ready, they are then promoted to `~/.claude/` for production use.
- The most common extensions that are developed in this repo are **Skills** and **Subagents**

## Directory Structure

```
.claude/
├── skills/       # Skills (SKILL.md required)
├── hooks/        # Hooks
├── commands/     # Slash commands
├── agents/       # Subagents
└── rules/        # Extension and methodology guidance

packages/
├── plugins/      # Plugin packages
└── mcp-servers/  # MCP servers

scripts/          # Utility scripts
docs/
├── frameworks/   # Full methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, task-list guidance
├── plans/        # Implementation plans and design documents
└── audits/       # Quality audits
```

### Extensions

Detailed guidance for each extension type lives in `.claude/rules/`. **YOU MUST read the relevant rule before starting work on a new extension**:

| Working on... | Read first                     |
| ------------- | ------------------------------ |
| Skills        | `.claude/rules/skills.md`      |
| Hooks         | `.claude/rules/hooks.md`       |
| Subagents     | `.claude/rules/subagents.md`   |
| Plugins       | `.claude/rules/plugins.md`     |
| MCP Servers   | `.claude/rules/mcp-servers.md` |
| Configuration | `.claude/rules/settings.md`    |

- Before creating or editing any `SKILL.md` file, read `.claude/rules/skills.md`
- Before creating or editing a Hook, read `.claude/rules/hooks.md`
- Before creating or editing a Subagent, read `.claude/rules/subagents.md`
- Before creating or editing a Plugin or a Marketplace, read `.claude/rules/plugins.md`
- Before creating or editing an MCP Server, read `.claude/rules/mcp-servers.md`
- Before any work involving configuring Claude Code, read `.claude/rules/settings.md`

## Workflow

### Creating Extensions

| Extension  | Create in                        | Test with           |
| ---------- | -------------------------------- | ------------------- |
| Skill      | `.claude/skills/<name>/SKILL.md` | `/<name>`           |
| Command    | `.claude/commands/<name>.md`     | `/<name>`           |
| Hook       | `.claude/hooks/<name>.py`        | After sync-settings |
| Agent      | `.claude/agents/<name>.md`       | Task tool           |
| Plugin     | `packages/plugins/<name>/`       | Marketplace install |
| MCP Server | `packages/mcp-servers/<name>/`   | After build         |

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

## Rules

### Methodology

Read `.claude/rules/methodology/frameworks.md` for guidance on when to use which framework. Full frameworks with templates and worked examples live in `docs/frameworks/`.

### Branch Protection

A hook blocks Edit/Write on `main`, `master`, `develop`. Create a working branch first.

**Exceptions (edits allowed on protected branches):**

- `docs/plans/*.md`, `docs/audits/*.md`
- `CHANGELOG.md`, `README.md`, `settings.json`
- `*/.claude/handoffs/*`, `*/.claude/notes/*`
- Gitignored paths (no commit anyway)

Full details: `.claude/rules/workflow/git.md`

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`
