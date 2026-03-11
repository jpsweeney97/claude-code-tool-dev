# CLAUDE.md

## Project Overview

Monorepo for developing Claude Code extensions: skills, commands, agents, hooks, plugins, and MCP servers.

## How This Repo Works

- Develop extensions in `.claude/` and `packages/`
- Promote to `~/.claude/` when ready
- Most common: **Skills** and **Subagents**

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

packages/
├── plugins/
│   ├── cross-model/          # Codex MCP + context injection + dialogue agent
│   │   └── context-injection/  # Mid-conversation evidence gathering MCP server
│   ├── handoff/              # Session state persistence
│   ├── ticket/               # Repo-local ticket management
│   └── context-metrics/      # Context window usage tracking
└── mcp-servers/
    └── claude-code-docs/     # BM25-indexed doc search (TypeScript)

scripts/          # Utility scripts (run with uv run scripts/<name>)

docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, style references
├── plans/        # Implementation plans and design documents
├── decisions/    # Architecture Decision Records
├── learnings/    # Cross-model consultation insights
├── tickets/      # Work tickets
└── audits/       # Quality audits

.claude-plugin/   # Plugin marketplace config (turbo-mode bundle)
```

## Packages

| Package | Path | Language | Purpose |
|---------|------|----------|---------|
| cross-model | `packages/plugins/cross-model/` | Python | Codex MCP server + enforcement hooks + dialogue agent |
| context-injection | `packages/plugins/cross-model/context-injection/` | Python | Mid-conversation evidence gathering with redaction (991 tests) |
| handoff | `packages/plugins/handoff/` | Python | Session state persistence (save/load/search) |
| ticket | `packages/plugins/ticket/` | Python | Repo-local ticket lifecycle management |
| context-metrics | `packages/plugins/context-metrics/` | Python | Context window usage analysis |
| claude-code-docs | `packages/mcp-servers/claude-code-docs/` | TypeScript | BM25-indexed Claude Code doc search (397 tests) |

Plugins deploy via `turbo-mode` marketplace. MCP servers and extensions deploy via `uv run scripts/promote`.

## Systems

Three systems form the cross-model collaboration stack:

| System | Status | Key Resources |
|--------|--------|---------------|
| **Codex Integration** — Cross-model dialogue with OpenAI Codex | Deployed | MCP tools: `mcp__plugin_cross-model_codex__codex`, `codex-reply`. Agent: `agents/codex-dialogue.md` |
| **Context Injection** — Mid-conversation evidence gathering for Codex dialogues | Complete | MCP tools: `mcp__plugin_cross-model_context-injection__process_turn`, `execute_scout`. Server: `packages/plugins/cross-model/context-injection/`. Contract: `packages/plugins/cross-model/references/context-injection-contract.md` |
| **Cross-Model Learning** — Persistent knowledge capture from Codex conversations | Phase 0 in progress | Spec: `docs/plans/2026-02-10-cross-model-learning-system.md`. Skill: `.claude/skills/learn/` |

**Context Injection security:** Over-redaction is always preferable to under-redaction. Footgun tests (`test_footgun_*`) verify which pipeline layer catches secrets.

**Codex hook delivery:** `PostToolUseFailure` `additionalContext` confirmed working (verified 2026-02-17).

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
| `promote` | Validate and deploy extensions to `~/.claude/` |
| `sync-settings` | Sync hook config to `settings.json` (run after hook changes) |
| `inventory` | List all extensions and packages |
| `migrate` | Extension schema migrations |
| `validate_consultation_contract.py` | Validate Codex contract + governance rules |
| `validate_episode.py` | Validate learning episode format |

Additional scripts in `scripts/` for benchmarking and analysis. See directory listing for full inventory.

## Rules

### Methodology

Read `.claude/rules/methodology/frameworks.md` for guidance on when to use which framework. Full frameworks with templates and worked examples live in `docs/frameworks/`.

### Thoroughness over cost

Always prefer rigorous, thorough approaches (parallel dialogues, exhaustive analysis) over cheap/fast shortcuts. Do not optimize for token cost or speed at the expense of quality.

### Branch Protection

A hook blocks Edit/Write on `main` and `master`. Create a working branch first.

**Exceptions (edits allowed on protected branches):**

- `docs/plans/*.md`, `docs/audits/*.md`
- `CHANGELOG.md`, `README.md`, `settings.json`
- `*/.claude/handoffs/*`, `*/.claude/notes/*`
- Gitignored paths (no commit anyway)

Full details: `.claude/rules/workflow/git.md`

## Gotchas

- **Dev vs production**: Edit extensions in `.claude/` (this repo), not `~/.claude/` (production). Promote when ready.
- **Sync after hook changes**: Run `uv run scripts/sync-settings` after modifying hooks — Claude Code reads from `settings.json`, not hook files directly.
- **Package-local testing**: A uv workspace (`pyproject.toml` at repo root) links all packages. Run tests from anywhere: `uv run --package <name> pytest`, or from the package directory: `cd packages/<path> && uv run pytest`.
- **Rules file size**: `.claude/rules/` files auto-load into every session. Keep them minimal — move reference material to `docs/` and link to it.

## Writing Extensions

Applies to instruction documents: skills (`.claude/skills/*/SKILL.md`) and subagents (`.claude/agents/*.md`).

Audience is Claude. Optimize for machine parsing.

Full guidance: `docs/references/writing-principles.md`

### Quick Reference

| #   | Principle             | Core Rule                                                   | Red Flag                                                  |
| --- | --------------------- | ----------------------------------------------------------- | --------------------------------------------------------- |
| 1   | Be Specific           | Replace vague language with concrete values                 | Vague pronouns, hedge words, unspecified quantities       |
| 2   | Define Terms          | Explain jargon and acronyms on first use                    | Unexplained acronyms, assumed project knowledge           |
| 3   | Show Examples         | Illustrate rules with concrete instances                    | Rules without demonstration, abstract patterns            |
| 4   | Verify Interpretation | Include confirmation checkpoints for high-risk instructions | No verification for ambiguous scope, irreversible actions |
| 5   | State Boundaries      | Explicitly declare scope and mutability                     | Implicit "obvious" scope, unstated read-only              |
| 6   | Specify Failure Modes | Define behavior when preconditions fail                     | Happy-path-only instructions, vague error handling        |
| 7   | Specify Defaults      | State behavior when no instruction applies                  | Implicit defaults, unhandled case improvisation           |
| 8   | Declare Preconditions | State requirements and verification before execution        | Assumed working directory, tools, or state                |
| 9   | Close Loopholes       | Anticipate and block creative misinterpretations            | Rules without rationale, unaddressed edge cases           |
| 10  | Front-Load            | Put critical information first                              | Commands buried after context                             |
| 11  | Group Related         | Keep conditions near consequences                           | Cross-references, scattered related content               |
| 12  | Keep Parallel         | Match structure across similar content                      | Mixed voice in lists, inconsistent hierarchy              |
| 13  | Specify Outcomes      | Define observable success criteria                          | "Ensure it works," process without verification           |
| 14  | Economy               | Remove words that don't advance meaning; use active voice   | Filler phrases, passive voice, double negatives           |

Lower numbers = higher priority in conflicts. See full document for priority hierarchy, self-check procedure, and document-type notes.
