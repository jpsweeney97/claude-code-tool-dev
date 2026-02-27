# Handoff Plugin

Session handoff and resume skills for context continuity between Claude Code sessions.

## Installation

```bash
claude plugin marketplace add ./packages/plugins/handoff
claude plugin install handoff@handoff-dev
```

## Skills

### `/save [title]`

Create a handoff document capturing session context:
- Decisions made and their rationale
- Files changed and why
- Next steps for continuation
- Gotchas and learnings discovered

Includes a synthesis process to ensure thorough context capture.

### `/load [path]`

Resume from the most recent handoff:
- Loads handoff content into context
- Archives the handoff to prevent stale reuse
- Records chain for `resumed_from` tracking

Lightweight — does not load the synthesis guide.

### `/quicksave [title]`

Fast checkpoint for context-pressure session cycling:
- Captures current task, in-progress state, and next action
- 22-55 line documents — minimum needed to resume
- Guardrail warns after 2 consecutive quicksaves without a full `/save`

### `/search <query> [--regex]`

Search active and archived handoffs for decisions, learnings, and context.

### `/list-handoffs`

List available handoffs for the current project (part of `load` skill).

## Storage

Handoffs are stored at `~/.claude/handoffs/<project>/` with 30-day retention.
Archived handoffs (after resume) are kept for 90 days in `.archive/`.

## Hooks

- **SessionStart**: Prunes old handoffs silently (no prompts, no auto-inject)

## Context Reduction

This plugin splits what was a monolithic skill (758 lines) into focused skills:

| Operation | Lines Loaded |
|-----------|-------------|
| `/save` | ~570 (skill + synthesis guide) |
| `/load` | ~220 (skill only) |
| `/quicksave` | ~120 (skill + contract) |
| `/search` | ~75 (skill only) |

Resume operations load 71% less context than before.
