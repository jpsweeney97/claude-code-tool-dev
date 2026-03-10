# T-20260302-04: DeferredWorkEnvelope schema definition

```yaml
id: T-20260302-04
date: "2026-03-02"
status: in_progress
priority: high
effort: M (3-5 sessions)
blocked_by: []
blocks: []
related: [T-20260302-05]
tags: [ticket-plugin, handoff-plugin, migration, integration]
notes: "Split into T-04a/b/c. T-04a (consumer) done in PR #69. T-04b (producer) and T-04c (agent infra) remain."
sub_tickets:
  - id: T-04a
    title: "Envelope consumer (validate, map, read, lifecycle)"
    status: done
    closed_at: "2026-03-10"
    closed_by: "PR #69"
  - id: T-04b
    title: "Handoff-side envelope producer (defer.py → envelope JSON)"
    status: open
  - id: T-04c
    title: "Agent infrastructure (ticket-autocreate envelope ingestion)"
    status: open
    absorbs: T-20260302-05
```

## Problem

The ticket plugin design specifies a `DeferredWorkEnvelope` as the bridge between the handoff plugin's `/save` skill and the ticket plugin's creation flow. The envelope is how unfinished work items get routed from handoff to tickets during the transition period. But the envelope schema (field names, types, required vs optional, versioning) is undefined.

## Context

The design doc (Relationship to Handoff Plugin section) specifies the transition sequence:
1. Ticket plugin ships with envelope support
2. Handoff's `/save` emits envelopes instead of calling `defer.py`
3. After telemetry confirms stability, deprecate `/defer`
4. Remove `defer.py` and `/defer` skill

The envelope must be agreed upon by both plugins. Handoff writes it; ticket plugin reads it. The schema is the integration contract.

Currently, handoff's `defer.py` creates Gen 4 tickets directly (writing markdown files). The envelope replaces this with a neutral intermediate format that the ticket plugin can process through its engine pipeline (including dedup, autonomy enforcement, and audit trail).

## Prior Investigation

- Deeper review Codex dialogue proposed the envelope bridge model (T4 of thread `019caf7f`)
- handoff's `defer.py` (line 39+) creates tickets with: title, problem, source_type, source_ref, provenance dict, suggested sections
- The envelope needs to carry at least this information plus ticket plugin-specific fields

## Approach

Define the `DeferredWorkEnvelope` as a JSON file:

```json
{
  "envelope_version": "1.0",
  "title": "Fix authentication timeout on large payloads",
  "problem": "Authentication handler times out for payloads >10MB...",
  "context": "Found during session abc-123 while working on API refactor",
  "source": {
    "type": "handoff",
    "ref": "session-abc-123",
    "session": "abc-123"
  },
  "suggested_priority": "medium",
  "suggested_tags": ["auth", "api"],
  "sections": {
    "Prior Investigation": "Checked handler.py:45 — timeout hardcoded...",
    "Key Files": "| File | Role |\n|------|------|\n| handler.py:45 | Timeout logic |"
  }
}
```

Storage: `docs/tickets/.envelopes/<timestamp>-<slug>.json` (intermediate, consumed on processing).

### Decisions Made
- JSON format (not markdown) — envelopes are machine-to-machine, not human-readable artifacts
- Envelopes are consumed (moved to `.envelopes/.processed/`) after successful ticket creation
- Schema versioned independently from ticket contract version

## Acceptance Criteria
- [ ] Envelope JSON schema defined with required/optional fields
- [ ] Handoff plugin's `/save` skill can emit envelopes
- [ ] `/ticket create --from-envelope <path>` reads envelope and creates ticket via engine pipeline
- [ ] `ticket-autocreate` agent can process envelopes when autonomy allows
- [ ] Processed envelopes moved to `.processed/` subdirectory
- [ ] Schema documented in both plugins' contracts

## Key Files
| File | Role | Look For |
|------|------|----------|
| `docs/plans/2026-03-02-ticket-plugin-design.md` | Design spec | "DeferredWorkEnvelope" in Handoff section |
| `packages/plugins/handoff/scripts/defer.py` | Current defer impl | Fields written to ticket files |
| `packages/plugins/handoff/skills/defer/SKILL.md` | Current defer skill | How deferred items are gathered |
| (future) `ticket/references/ticket-contract.md` | Ticket contract | Envelope schema definition |
