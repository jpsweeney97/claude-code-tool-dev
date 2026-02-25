# Handoff Enhancement #2: Knowledge Graduation

```yaml
id: handoff-distill
date: 2026-02-24
status: planning
priority: medium
blocked_by: []
blocks: []
related: [handoff-search]
plugin: packages/plugins/handoff/
```

## Problem

Handoffs have 30-day active / 90-day archive retention. But decisions, architecture understanding, and patterns are durable knowledge that outlives any session chain. Today this knowledge gets permanently deleted when handoffs age past retention.

The `/learn` system and `MEMORY.md` exist for persistent knowledge — but are completely disconnected from the handoff system. No extraction path exists.

**Evidence:**
- 90-day archive retention means all knowledge in handoffs from before ~Nov 2025 is gone
- Handoffs contain structured Decisions, Learnings, and Codebase Knowledge sections with durable insights
- `/learn` Phase 0 exists (`docs/learnings/learnings.md`, 19 entries) but is populated manually, not from handoffs
- No overlap between handoff sections and learning entries — these are separate knowledge silos

**Cost:**
- Permanent loss of decisions and their rationale after retention expires
- Manual duplicate effort to capture the same insight in both a handoff and a learning
- Learnings file misses insights that were captured in handoffs but never promoted

## Scope

**In scope:**
- Extract durable knowledge from a specific handoff or most recent handoff
- Format as Phase 0 learning entries (`### YYYY-MM-DD [tags]` + paragraph)
- Append to `docs/learnings/learnings.md` with user confirmation
- Identify which sections contain durable knowledge (Decisions, Learnings, Patterns)

**Out of scope:**
- Automatic extraction (always user-triggered)
- Structured episodes (Phase 1+ of cross-model learning system)
- Cross-project knowledge transfer
- Modifying the handoff after extraction
- Replacing `/learn` — this complements it

## Design Space

*To be filled during brainstorming. Key questions:*

1. **Invocation**: `/handoff:distill [path]` vs integration with `/learn`?
2. **Selection**: Extract from specific handoff, most recent, or batch?
3. **What to extract**: All durable sections? User-selected sections? Auto-detected?
4. **Format mapping**: How do handoff sections map to learning entries?
5. **Deduplication**: How to avoid extracting the same insight twice from chained handoffs?
6. **Confirmation UX**: Show proposed entries and confirm before appending?
7. **Should this run at archive time?** Offer distill when `/resume` archives a handoff?

## Files Affected

| File | Change |
|------|--------|
| `skills/distilling-handoffs/SKILL.md` | **New** — distill skill |
| `commands/distill.md` | **New** — command wrapper |
| `.claude-plugin/plugin.json` | Version bump |

## Acceptance Criteria

- [ ] `/handoff:distill` extracts durable knowledge from a handoff
- [ ] Produces Phase 0 format learning entries
- [ ] Shows proposed entries to user before appending
- [ ] Appends confirmed entries to `docs/learnings/learnings.md`
- [ ] Does not modify the source handoff
- [ ] Handles handoffs with no extractable knowledge gracefully
