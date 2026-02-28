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

### `/distill [path]`

Extract durable knowledge from handoffs into Phase 0 learnings.

- `/distill` — distills the most recent handoff
- `/distill <path>` — distills a specific handoff

**What it extracts:** Decisions, Learnings, Codebase Knowledge, and Gotchas that pass durability filtering (session-specific details are excluded).

**Output:** Phase 0 entries appended to `docs/learnings/learnings.md`.

**Dedup:** Exact (source + content hash) and semantic (Claude comparison) deduplication prevents redundant entries.

### `/defer [filter]`

Extract deferred work items from conversation and create tracking tickets:
- Analyzes conversation for open questions, risks, explicit deferrals, TODOs
- Presents candidates with evidence anchors for user confirmation
- Creates structured tickets in `docs/tickets/` with provenance tracking

### `/triage`

Review open tickets and detect orphaned handoff items:
- Lists open tickets grouped by priority and age
- Scans handoffs for untracked items (Open Questions, Risks)
- Matches items to tickets via session correlation and ID references
- Reports match counts for observability

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
| `/distill` | ~210 (skill only) |

Resume operations load 71% less context than before.
