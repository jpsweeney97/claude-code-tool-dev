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

These principles apply to files Claude reads as instructions:

- **Skills**: `.claude/skills/*/SKILL.md` and supporting files
- **Subagents**: `.claude/agents/*.md`

Claude is the audience. Optimize for machine parsing, not human onboarding.

### Principles

**1. Economy (Signal-to-Noise)**

Omit needless words. If a word does not advance meaning, remove it.

- Delete fillers: "please," "it is important to note," "actually"
- Remove redundant qualifiers: "completely finished" → "finished"
- Goal: Maximum density

**2. Affirmative Direction**

State what _is_, not what _is not_. Use active voice.

| Avoid                                    | Prefer                    |
| ---------------------------------------- | ------------------------- |
| "Do not fail to include..."              | "Include..."              |
| "Errors should be logged by the handler" | "The handler logs errors" |
| "It is not uncommon for..."              | "Often..."                |

**3. Concrete Specificity**

Ambiguity is failure. Prefer specific nouns and verbs to abstract generalizations.

- Replace vague pronouns ("it," "this") with their antecedents
- Replace weak verbs with strong: "went quickly" → "sprinted"
- Name exact files, commands, and values — not "the config file" but `.claude/settings.json`

**4. Logical Proximity**

Physical distance on the page reflects logical distance in thought.

- Keep modifiers next to words they modify
- Group related instructions (bullets, tables for parallel ideas)
- Don't separate a condition from its consequence

**5. Contextual Priming**

Structure for rapid parsing.

- Place reference data _before_ instructions that use it
- Start paragraphs with topic sentences
- Use headers to signal shifts in logic
- Front-load the most important information
