# T-20260302-01: auto_audit notification UX flows

```yaml
id: T-20260302-01
date: "2026-03-02"
status: deferred
priority: medium
effort: S (1-2 sessions)
blocked_by: []
blocks: []
related: [T-20260302-02, T-20260302-03, T-04c]
tags: [ticket-plugin, ux, autonomy, auto-audit-rollout]
notes: "Deferred — target reference.md doesn't exist yet. Part of auto_audit rollout alongside T-04c (agent infrastructure)."
```

## Problem

The `auto_audit` autonomy mode in the ticket plugin design specifies a notification template but lacks detailed UX flows for confirmation handling and undo. When the engine creates a ticket in `auto_audit` mode, the user sees a one-line notification — but the design doesn't specify what happens when the user wants to review, modify, or undo the auto-created ticket.

## Context

The notification template is defined in the design doc (lines ~397-401):
```
[auto] Created T-YYYYMMDD-NN: <title summary>
  Path: docs/tickets/YYYY-MM-DD-<slug>.md
  Review: /ticket query T-YYYYMMDD-NN
```

What's missing: the interaction flow after the notification. Does the user just run `/ticket query`? Can they inline-edit? Is there an undo window? How does confirmation differ between `auto_audit` (notification shown) and `auto_silent` (notification deferred to triage digest)?

## Prior Investigation

- Design doc specifies the template but not the interaction flow
- `auto_silent` guardrail 4 now uses durable audit summary + skill-owned visible digest — the UX for surfacing this digest is also unspecified
- The handoff plugin has no comparable interaction (defer.py creates silently with no confirmation)

## Approach

Define the UX flows for:
1. **Post-notification review:** User can run `/ticket query T-...` or `/ticket update T-...` to review/modify
2. **Undo:** `/ticket close T-... --reason "auto-created in error"` with `wontfix` status — no special undo mechanism needed (standard close flow)
3. **Digest surfacing:** When `ticket-triage` fires proactively, it reports recent auto-created tickets from the audit trail

### Decisions Made
- No special "undo" mechanism — standard ticket close covers this case
- Digest is surfaced by ticket-triage, not a custom mechanism

## Acceptance Criteria
- [ ] UX flow documented for post-notification review
- [ ] UX flow documented for undo/reject of auto-created ticket
- [ ] UX flow documented for triage digest surfacing (auto_silent)
- [ ] Flows integrated into ticket-ops skill reference.md

## Key Files
| File | Role | Look For |
|------|------|----------|
| `docs/plans/2026-03-02-ticket-plugin-design.md:397` | Notification template | `auto_audit` template definition |
| `docs/plans/2026-03-02-ticket-plugin-design.md:388` | Guardrails | 6 hard constraints for auto_silent |
| (future) `ticket/skills/ticket-ops/reference.md` | Implementation target | Per-operation detailed guides |
