# CLAUDE.md

## Project Overview

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

- Develop extensions in `.claude/` and `packages/`
- Promote to `~/.claude/` when ready

## Directory Structure

```
.claude/
├── skills/       # Skills (SKILL.md required)
├── hooks/        # Hooks (Python scripts, synced to settings.json)
├── commands/     # Slash commands
├── agents/       # Subagents
├── rules/        # Auto-loaded session rules (keep minimal)
├── handoffs/     # Session handoff documents (gitignored)
├── sessions/     # Session notes (gitignored)
└── worktrees/    # Git worktree state (gitignored)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Codex consultation insights
├── tickets/      # Work tickets
└── audits/       # Quality audits

.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
```

## Packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
| superspec | `packages/plugins/superspec/` | Shell/Markdown | Spec writing system — write, review, modularize specs with shared contract |
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search |

Plugins deploy via `turbo-mode` marketplace. MCP servers and extensions deploy via `uv run scripts/promote`.

## Gotchas

- **Dev vs production**: Edit extensions in `.claude/` (this repo), not `~/.claude/` (production). Promote when ready.
- **Sync after hook changes**: Run `uv run scripts/sync-settings` after modifying hooks — Claude Code reads from `settings.json`, not hook files directly.
- **Package-local testing**: A uv workspace (`pyproject.toml` at repo root) links all packages. Run tests from anywhere: `uv run --package <name> pytest`, or from the package directory: `cd packages/<path> && uv run pytest`.
- **Rules file size**: `.claude/rules/` files auto-load into every session. Keep them minimal — move reference material to `docs/` and link to it.
- **Hook failure polarity**: PreToolUse hooks are fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds. For critical enforcement, catch all errors and return a block decision.
- **MCP tool naming**: Plugin tools use `mcp__plugin_<plugin>_<server>__<tool>`. Must match across hook matchers, skill `allowed-tools`, and agent `tools` frontmatter. `tools` is a hard allowlist (wrong name = unavailable); `allowed-tools` is auto-approval only (wrong name = permission prompts).
- **Hook payload fields**: PostToolUse uses `tool_response` (not `tool_result`); PreToolUse uses `tool_input`. Plugin `.mcp.json` `env` merges with parent environment. `${VAR:-default}` does NOT expand; safest to inherit rather than set.

## Writing Extensions

Applies to instruction documents: skills (`.claude/skills/*/SKILL.md`) and subagents (`.claude/agents/*.md`).

Audience is Claude. Optimize for machine parsing.

Full guidance: `docs/references/writing-principles.md`

- **Prohibit, don't omit**: When Claude should avoid an action, use active prohibitions ("Do NOT set X", "Never use Y") rather than passive language ("omit X for default", "leave X empty"). Passive instructions don't reliably prevent Claude from filling gaps with training knowledge. The stronger the training prior, the more explicit the prohibition must be.
- **Standalone layers**: When instruction documents layer (skill → agent → contract), each layer must be fully operational standalone. Never use "if available, use X; otherwise fall back" — inline the minimal self-contained version. Other sources are additive, not alternative.

## Workflow

### Promoting Extensions

```bash
uv run scripts/promote <type> <name>   # Validate and deploy to ~/.claude/
```

Types: `skill`, `command`, `agent`, `hook`. Plugins use the marketplace instead (see Packages table).

### Scripts

Run with `uv run scripts/<name>`:

| Script | Purpose |
|--------|---------|
| `sync-settings` | Sync hook config to `settings.json` (run after hook changes) |
| `inventory` | List all extensions and packages |
| `migrate` | Extension schema migrations |
| `validate_episode.py` | Validate learning episode format |
