# claude-code-tool-dev

Development monorepo for Claude Code extensions: skills, hooks, agents, commands, plugins, and MCP servers. Extensions are built and tested here, then promoted to `~/.claude/` for production use.

## Package Map

Two workspace systems manage six packages across Python and TypeScript:

### Python Packages (uv workspace)

| Package | Path | Version | Description |
|---------|------|---------|-------------|
| cross-model | `packages/plugins/cross-model/` | 3.0.0 | Cross-model consultation with OpenAI Codex — MCP servers, enforcement hooks, dialogue agents |
| context-injection | `packages/plugins/cross-model/context-injection/` | 0.2.0 | Evidence-gathering MCP server for mid-conversation fact verification (nested inside cross-model) |
| handoff | `packages/plugins/handoff/` | 1.5.0 | Session handoff — save, load, search, defer, and triage work across sessions |
| ticket | `packages/plugins/ticket/` | 1.4.0 | Repo-local ticket management with lifecycle operations |
| context-metrics | `packages/plugins/context-metrics/` | 0.1.0 | Context window usage tracking via JSONL analysis |

### TypeScript Packages (npm workspace)

| Package | Path | Version | Description |
|---------|------|---------|-------------|
| @claude-tools/claude-code-docs | `packages/mcp-servers/claude-code-docs/` | 1.0.0 | BM25-indexed documentation search MCP server for Claude Code docs |

### Plugin Marketplace

The four Python plugins are bundled into a `turbo-mode` marketplace (`.claude-plugin/marketplace.json`) for single-command installation:

```bash
claude plugin marketplace update turbo-mode
claude plugin install cross-model@turbo-mode
```

## Getting Started

### Prerequisites

| Dependency | Minimum Version | Managed By |
|------------|----------------|------------|
| Python | >=3.11 | mise |
| Node.js | >=18 | mise |
| uv | Latest | mise |
| git | Any | System |
| ripgrep (`rg`) | Any | System (runtime dep for context-injection) |

### Clone and Setup

```bash
git clone <repo-url>
cd claude-code-tool-dev

# Python workspace (plugins, hooks, scripts)
uv sync

# Node workspace (MCP servers)
npm ci
```

Both workspaces are independent — you can work on Python packages without Node.js installed, and vice versa.

### Branch Protection

A PreToolUse hook blocks edits on `main` and `master`. Create a working branch before making changes:

```bash
git checkout -b feature/<name>    # or fix/, chore/, hotfix/, etc.
```

See `.claude/rules/workflow/git.md` for the full branch naming convention and environment variable overrides.

## Architecture

Three architectural layers, each building on the previous:

```
Layer 3: Claude Code Extensions (loaded into Claude Code sessions)
  .claude/skills/        15 skills (instruction documents Claude follows)
  .claude/agents/         5 subagent definitions
  .claude/hooks/          7 Python hook scripts (security, branch protection)
  .claude/commands/       1 slash command
  .claude/rules/          Auto-loaded session rules (methodology, git workflow)

Layer 2: Plugin Packages (installed as Claude Code plugins)
  packages/plugins/cross-model/       Codex integration + context injection
  packages/plugins/handoff/           Session handoff and work tracking
  packages/plugins/ticket/            Repo-local ticket management
  packages/plugins/context-metrics/   Context window usage metrics

Layer 1: MCP Servers (standalone processes, stdio transport)
  packages/mcp-servers/claude-code-docs/                  TypeScript, BM25 doc search
  packages/plugins/cross-model/context-injection/         Python, evidence gathering
  (External: codex mcp-server)                            OpenAI Codex integration
```

**Extensions** (Layer 3) are developed in `.claude/` and promoted to `~/.claude/` when ready. **Plugins** (Layer 2) bundle multiple extension types (hooks, skills, agents, scripts) into installable packages. **MCP servers** (Layer 1) are long-running processes that provide tools to Claude Code sessions.

### Cross-Model Collaboration Stack

The most architecturally complex subsystem spans all three layers:

1. **Codex Integration** — MCP server wrapping the OpenAI Codex CLI, providing `codex` and `codex-reply` tools for cross-model dialogue
2. **Context Injection** — Python MCP server that verifies Codex claims against the codebase in real-time using a two-call protocol (process_turn → execute_scout) with HMAC-token security
3. **Cross-Model Learning** — Design complete, implementation not started. Captures insights from Claude-Codex disagreements as reusable learning cards

### Key Design Patterns

| Pattern | Where Used | Description |
|---------|-----------|-------------|
| Sandbox-to-Production Promotion | Skills, hooks, agents, commands | Develop in `.claude/`, promote to `~/.claude/` via `scripts/promote` |
| Two-Call Protocol | context-injection MCP server | Call 1 generates HMAC-authorized scout options; Call 2 executes them. Prevents unauthorized file access |
| Fail-Closed Security Gates | context-injection, hooks | Missing preconditions → deny by default (empty git file set = all files denied) |
| Plugin as Extension Bundle | All 4 plugins | Single package bundles hooks, skills, agents, MCP servers, scripts |
| Instruction Documents as Code | Skills, agents | Markdown prompts treated as first-class artifacts with review, testing, and promotion workflows |
| PreToolUse Hook Guard | 7 repo hooks + plugin hooks | Python scripts intercept tool calls, evaluate policy, return allow/block decisions |

## Common Workflows

### Develop and Promote Extensions

```bash
# 1. Create or edit an extension in .claude/
#    skills → .claude/skills/<name>/SKILL.md
#    hooks  → .claude/hooks/<name>.py
#    agents → .claude/agents/<name>.md

# 2. Test locally (extensions are live in the current session)

# 3. Promote to production
uv run scripts/promote skill <name>      # Validates, diffs, copies to ~/.claude/skills/
uv run scripts/promote hook <name>       # Same for hooks
uv run scripts/promote agent <name>      # Same for agents
```

### Install Plugins

Plugins use the marketplace instead of the promote script:

```bash
claude plugin marketplace update turbo-mode
claude plugin install cross-model@turbo-mode    # Install a specific plugin
```

### Run Tests

```bash
# Python — from any directory
uv run --package context-injection pytest        # 991 tests
uv run --package ticket-plugin pytest
uv run --package handoff-plugin pytest
uv run --package context-metrics-plugin pytest

# Or from the package directory
cd packages/plugins/cross-model/context-injection && uv run pytest

# TypeScript
npm run test --workspace @claude-tools/claude-code-docs   # 386 tests

# Root-level cross-cutting tests
uv run pytest tests/
```

### Sync Hook Configuration

After adding or modifying hooks, rebuild the settings file:

```bash
uv run scripts/sync-settings
```

This reads PEP 723-style frontmatter from hook files (`# /// hook` blocks) and writes the hook registration to `~/.claude/settings.json`.

### Build TypeScript Packages

```bash
npm run build                    # All workspaces
npm run dev                      # Watch mode (claude-code-docs)
npx tsc --noEmit                 # Type check only
```

## Scripts & Tooling

All scripts run via `uv run scripts/<name>` using PEP 723 inline metadata for dependencies.

### Core Scripts

| Script | Usage | Purpose |
|--------|-------|---------|
| `promote` | `uv run scripts/promote <type> <name>` | Validate and deploy extensions from `.claude/` to `~/.claude/` |
| `sync-settings` | `uv run scripts/sync-settings` | Rebuild settings.json hooks section from hook file frontmatter |
| `inventory` | `uv run scripts/inventory` | Scan extension sources and generate migration inventory |
| `migrate` | `uv run scripts/migrate` | Process migration inventory — copy extensions based on decision field |

### Validation Scripts

| Script | Usage | Purpose |
|--------|-------|---------|
| `validate_consultation_contract.py` | `uv run scripts/validate_consultation_contract.py` | Validate cross-model consultation contract (16-section check) |
| `validate_episode.py` | `uv run scripts/validate_episode.py <path>` | Validate learning episode artifacts against schema |

### Evaluation Scripts

| Script | Purpose |
|--------|---------|
| `skill_impact_stats.py` | Compute Wilson confidence intervals for skill behavioral eval data |
| `blinded_eval_packet.py` | Generate blinded evaluation packets for skill benchmarks |
| `benchmark_v0_resume` | Resume interrupted benchmark runs |

## Contributing

### Project Structure

```
.claude/           Extensions under development (skills, hooks, agents, commands, rules)
packages/          Plugin packages and MCP servers
scripts/           Utility scripts (run with uv run)
tests/             Root-level cross-cutting tests
docs/              Plans, audits, frameworks, decisions, tickets, learnings
```

### Development Conventions

- **Branch naming**: `feature/*`, `fix/*`, `chore/*`, `hotfix/*` (enforced by hook)
- **Python testing**: pytest, run via `uv run pytest` or `uv run --package <name> pytest`
- **TypeScript testing**: vitest, run via `npm run test --workspace <name>`
- **Linting**: ruff (Python), TypeScript strict mode (Node.js)
- **Skills and agents**: Follow the 14 writing principles in `docs/references/writing-principles.md`
- **Hook frontmatter**: Use PEP 723-style `# /// hook` blocks; run `sync-settings` after changes

### Extension Types

| Type | Location | File Format | How to Create |
|------|----------|-------------|---------------|
| Skill | `.claude/skills/<name>/SKILL.md` | YAML frontmatter + markdown | Directory with SKILL.md |
| Hook | `.claude/hooks/<name>.py` | Python with PEP 723 frontmatter | Executable Python script |
| Agent | `.claude/agents/<name>.md` | YAML frontmatter + markdown | Markdown file |
| Command | `.claude/commands/<name>.md` | YAML frontmatter + markdown | Markdown file |
| Plugin | `packages/plugins/<name>/` | Package with `.claude-plugin/plugin.json` | Full package structure |
| MCP Server | `packages/mcp-servers/<name>/` | TypeScript or Python package | Full package with MCP SDK |

### CI

GitHub Actions runs on the claude-code-docs MCP server only (test, typecheck, build, audit, smoke tests). Python plugin tests run locally — no CI pipeline.
