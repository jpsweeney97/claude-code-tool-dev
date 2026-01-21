# Handoff Plugin

Session handoff and resume skills for context continuity between Claude Code sessions.

## Installation

```bash
claude plugin marketplace update tool-dev
claude plugin install handoff@tool-dev
```

## Skills

### `/handoff:creating-handoffs [title]`

Create a handoff document capturing session context:
- Decisions made and their rationale
- Files changed and why
- Next steps for continuation
- Gotchas and learnings discovered

Includes a synthesis process to ensure thorough context capture.

### `/handoff:resuming-handoffs [path]`

Resume from the most recent handoff:
- Loads handoff content into context
- Archives the handoff to prevent stale reuse
- Records chain for `resumed_from` tracking

Lightweight — does not load the synthesis guide.

### `/list-handoffs`

List available handoffs for the current project (part of `resuming-handoffs` skill).

## Storage

Handoffs are stored at `~/.claude/handoffs/<project>/` with 30-day retention.
Archived handoffs (after resume) are kept for 90 days in `.archive/`.

## Hooks

- **SessionStart**: Prunes old handoffs silently (no prompts, no auto-inject)

## Context Reduction

This plugin splits what was a monolithic skill (758 lines) into focused skills:

| Operation | Lines Loaded |
|-----------|-------------|
| `/handoff:creating-handoffs` | ~570 (skill + synthesis guide) |
| `/handoff:resuming-handoffs` | ~220 (skill only) |

Resume operations load 71% less context than before.
