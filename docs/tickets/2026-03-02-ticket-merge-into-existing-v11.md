# T-20260302-02: merge_into_existing UX flows (v1.1)

```yaml
id: T-20260302-02
date: "2026-03-02"
status: open
priority: low
effort: M (2-4 sessions)
blocked_by: []
blocks: []
related: [T-20260302-01]
tags: [ticket-plugin, ux, dedup, v1.1]
```

## Problem

The `merge_into_existing` machine state is reserved in v1.0 — the engine returns `escalate` instead. For v1.1, the merge algorithm and field conflict resolution need to be designed and implemented so that when a duplicate is detected, the user can merge the new content into the existing ticket rather than creating a new one or aborting.

## Context

The design doc (line ~220) marks `merge_into_existing` as reserved:
> **Reserved — not emitted in v1.0.** Merge algorithm and field conflict resolution deferred. If conditions would produce this state, engine returns `escalate` instead.

The `duplicate_candidate` state offers only two options in v1.0: (a) create anyway, (b) abort. Merge was the original third option but had no engine logic backing it.

## Prior Investigation

- 5-agent team review (UX reviewer) identified the dead-end when `duplicate_candidate` abort was the only non-create option
- Deeper review Codex dialogue agreed merge should not be offered without engine logic — reserved with escalate fallback
- No existing merge logic in the codebase (handoff plugin has no dedup)

## Approach

Design the merge algorithm:
1. **Field conflict resolution:** When merging ticket B into existing ticket A, define per-field merge rules (append, replace, union, skip)
2. **Section merge:** Problem sections might complement each other; Approach sections might conflict. Define merge semantics per section type.
3. **Preview UX:** Show a merged preview with diff highlighting what came from each source
4. **Confirmation:** User confirms the merged result before write

### Decisions Made
- Deferred to v1.1 — v1.0 ships without merge capability
- `escalate` is the fallback in v1.0 (explains why merge isn't available, suggests manual action)

## Acceptance Criteria
- [ ] Per-field merge rules defined (frontmatter fields)
- [ ] Per-section merge semantics defined (content sections)
- [ ] Merged preview rendering implemented in ticket_render.py
- [ ] Engine `merge_into_existing` state emitted when appropriate
- [ ] UX flow integrated into ticket-ops skill

## Key Files
| File | Role | Look For |
|------|------|----------|
| `docs/plans/2026-03-02-ticket-plugin-design.md:220` | Reserved state | `merge_into_existing` machine state |
| (future) `ticket/scripts/ticket_engine_core.py` | Engine logic | `plan` subcommand dedup handling |
| (future) `ticket/scripts/ticket_render.py` | Preview rendering | Merged preview with diff |
