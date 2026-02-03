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
└── mcp-servers/  # MCP servers

scripts/          # Utility scripts (run with uv run scripts/<name>)
docs/
├── frameworks/   # Methodology frameworks (thoroughness, decision-making, verification)
├── references/   # Skill patterns, guides, task-list guidance
├── plans/        # Implementation plans and design documents
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

## Gotchas

- **Dev vs production**: Edit extensions in `.claude/` (this repo), not `~/.claude/` (production). Promote when ready.
- **Sync after hook changes**: Run `uv run scripts/sync-settings` after modifying hooks — Claude Code reads from `settings.json`, not hook files directly.

## Writing Extensions

Applies to instruction documents: skills (`.claude/skills/*/SKILL.md`) and subagents (`.claude/agents/*.md`).

Audience is Claude. Optimize for machine parsing.

Full guidance: `docs/references/writing-principles.md`

### Quick Reference

| #   | Principle             | Core Rule                                                       | Red Flag                                                  |
| --- | --------------------- | --------------------------------------------------------------- | --------------------------------------------------------- |
| 1   | Be Specific           | Replace vague language with concrete values                     | Vague pronouns, hedge words, unspecified quantities       |
| 2   | Define Terms          | Explain jargon and acronyms on first use                        | Unexplained acronyms, assumed project knowledge           |
| 3   | Show Examples         | Illustrate rules with concrete instances                        | Rules without demonstration, abstract patterns            |
| 4   | Verify Interpretation | Include confirmation checkpoints for high-risk instructions     | No verification for ambiguous scope, irreversible actions |
| 5   | State Boundaries      | Explicitly declare scope and mutability                         | Implicit "obvious" scope, unstated read-only              |
| 6   | Specify Failure Modes | Define behavior when preconditions fail                         | Happy-path-only instructions, vague error handling        |
| 7   | Specify Defaults      | State behavior when no instruction applies                      | Implicit defaults, unhandled case improvisation           |
| 8   | Declare Preconditions | State requirements and verification before execution            | Assumed working directory, tools, or state                |
| 9   | Close Loopholes       | Anticipate and block creative misinterpretations                | Rules without rationale, unaddressed edge cases           |
| 10  | Front-Load            | Put critical information first                                  | Commands buried after context                             |
| 11  | Group Related         | Keep conditions near consequences                               | Cross-references, scattered related content               |
| 12  | Keep Parallel         | Match structure across similar content                          | Mixed voice in lists, inconsistent hierarchy              |
| 13  | Specify Outcomes      | Define observable success criteria                              | "Ensure it works," process without verification           |
| 14  | Economy               | Remove words that don't advance meaning; use active voice       | Filler phrases, passive voice, double negatives           |

Lower numbers = higher priority in conflicts. See full document for priority hierarchy, self-check procedure, and document-type notes.
