# CLAUDE.md

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

Extensions are developed in `.claude/` and `packages/`, tested locally, then promoted to `~/.claude/` for production use. Important specific guidance lives in `.claude/rules/`.

## Directory Structure

```
.claude/
├── skills/       # Skill definitions (SKILL.md required)
├── hooks/        # Python event hooks
├── commands/     # Slash command definitions
├── agents/       # Subagent definitions
└── rules/        # Extension and methodology guidance — READ BEFORE CREATING

packages/
├── plugins/      # Plugin packages (marketplace: tool-dev)
└── mcp-servers/  # TypeScript MCP servers

scripts/          # Utility scripts (inventory, migrate, promote, sync-settings)
docs/
├── frameworks/   # Full methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, task-list guidance
├── plans/        # Implementation plans
└── audits/       # Quality audits
```

## Workflow

```
CREATE in .claude/ or packages/  →  TEST locally  →  PROMOTE to ~/.claude/
```

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

### Extensions

Detailed guidance for each extension type lives in `.claude/rules/`. **Read the relevant rule before starting work on a new extension**:

| Working on... | Read first                       |
| ------------- | -------------------------------- |
| Skills        | `.claude/rules/skills.md`        |
| Hooks         | `.claude/rules/hooks.md`         |
| Commands      | `.claude/rules/commands.md`      |
| Subagents     | `.claude/rules/subagents.md`     |
| Plugins       | `.claude/rules/plugins.md`       |
| MCP Servers   | `.claude/rules/mcp-servers.md`   |
| Settings      | `.claude/rules/settings.md`      |

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`
