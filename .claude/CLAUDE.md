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
├── rules/        # Methodology and design guidance — READ BEFORE CREATING
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

Quality standards to adhere to across all work lives in `.claude/rules/methodology`. **Read the relevant rule before starting ANY work**:

- @~/Projects/active/claude-code-tool-dev/.claude/rules/methodology/rigor.md
- @~/Projects/active/claude-code-tool-dev/.claude/rules/methodology/tenets.md

### Branch Protection

A hook blocks Edit/Write on `main`, `master`, `develop`. Create a working branch first.

**Exceptions (edits allowed on protected branches):**
- `docs/plans/*.md`, `docs/audits/*.md`
- `CHANGELOG.md`, `README.md`, `settings.json`
- `*/.claude/handoffs/*`, `*/.claude/notes/*`
- Gitignored paths (no commit anyway)

Full details: @~/Projects/active/claude-code-tool-dev/.claude/rules/workflow/gitflow.md

### Extensions

Detailed guidance for each extension type lives in `.claude/rules/extensions`. **Read the relevant rule before starting work on a new extension**:

| Working on... | Read first                                                                      |
| ------------- | ------------------------------------------------------------------------------- |
| Skills        | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/skills.md      |
| Hooks         | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/hooks.md       |
| Commands      | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/commands.md    |
| Agents        | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/agents.md      |
| Plugins       | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/plugins.md     |
| MCP Servers   | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/mcp-servers.md |
| Settings      | ~/Projects/active/claude-code-tool-dev/.claude/rules/extensions/settings.md    |

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`
