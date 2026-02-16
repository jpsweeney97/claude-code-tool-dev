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
├── hooks/        # Hooks
├── commands/     # Slash commands
├── agents/       # Subagents
└── rules/        # Extension and methodology guidance

packages/
├── plugins/      # Plugin packages
├── mcp-servers/  # MCP servers
└── context-injection/  # Context injection MCP server

scripts/          # Utility scripts (run with uv run scripts/<name>)
docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, task-list guidance
├── plans/        # Implementation plans and design documents
├── tickets/      # Work tickets with fix lists and design decisions
├── audits/       # Quality audits
└── claude-code-documentation/  # Official Claude Code docs (reference)
```

### Extension Rules (Blocking)

Before creating or editing any extension, you MUST:

1. Read the relevant rules file from the table below
2. Confirm you have read it before proceeding

| Extension  | Rules File                     |
| ---------- | ------------------------------ |
| Skill      | `.claude/rules/skills.md`      |
| Hook       | `.claude/rules/hooks.md`       |
| Subagent   | `.claude/rules/subagents.md`   |
| Plugin     | `.claude/rules/plugins.md`     |
| MCP Server | `.claude/rules/mcp-servers.md` |
| Settings   | `.claude/rules/settings.md`    |

Do not proceed with edits until you have read the file. This is non-negotiable.

## Systems

Three systems form the cross-model collaboration stack, each building on the previous.

### Codex Integration

MCP server providing cross-model dialogue with OpenAI Codex. Enables Claude Code to consult an independent model for second opinions on architecture, plans, and decisions. Value: an independent model catches blind spots and challenges assumptions that a single model working alone would miss. The codex-dialogue agent was built on this integration to manage structured multi-turn conversations with a running ledger, convergence detection, and confidence-annotated synthesis.

| Resource  | Location                                        |
| --------- | ----------------------------------------------- |
| MCP tools | `mcp__codex__codex`, `mcp__codex__codex-reply`  |
| Agent     | `.claude/agents/codex-dialogue.md`              |

**Status:** Deployed.

### Context Injection

Mid-conversation evidence gathering for Codex dialogues. When Codex makes a factual claim about the codebase, the agent reads the relevant file and uses the evidence to shape follow-ups — verifying claims in real-time rather than relying entirely on the initial briefing.

| Resource          | Location                                                        |
| ----------------- | --------------------------------------------------------------- |
| MCP server        | `packages/context-injection/`                                   |
| Protocol contract | `docs/references/context-injection-contract.md`                 |
| Design spec       | `docs/plans/2026-02-11-conversation-aware-context-injection.md` |
| MCP tools         | `mcp__context-injection__process_turn`, `mcp__context-injection__execute_scout` |

**Security stance:** Over-redaction is always preferable to under-redaction. When adding format-specific redaction logic, verify that edge cases fail toward over-redaction (safe) not under-redaction (leak). Footgun tests (`test_footgun_*`) verify which pipeline layer catches secrets — check that they still test their stated contract after behavior changes.

**Status:** MCP server complete (739 tests). Agent integration pending — the codex-dialogue agent's 3-step conversation loop needs upgrading to the 7-step scouting loop described in the design spec.

### Cross-Model Learning

Persistent knowledge capture across Codex conversations. Insights from Claude-Codex disagreements and resolutions are captured as learning cards — template-constrained, linted artifacts — and re-injected into future consultations as weak priors. Over time, consultations improve because the shared knowledge base grows from real resolutions.

| Resource    | Location                                                       |
| ----------- | -------------------------------------------------------------- |
| Design spec | `docs/plans/2026-02-10-cross-model-learning-system.md`         |

**Status:** Design complete. Implementation not started.

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

### Scripts

Run with `uv run scripts/<name>`: `inventory`, `migrate`, `promote`, `sync-settings`

## Gotchas

- **Dev vs production**: Edit extensions in `.claude/` (this repo), not `~/.claude/` (production). Promote when ready.
- **Sync after hook changes**: Run `uv run scripts/sync-settings` after modifying hooks — Claude Code reads from `settings.json`, not hook files directly.
- **Package-local testing**: Packages under `packages/` have their own `pyproject.toml` and venv. Run tests from the package directory: `cd packages/<name> && uv run pytest`.
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
