# T-20260302-05: ticket-autocreate foreground-only enforcement

```yaml
id: T-20260302-05
date: "2026-03-02"
status: absorbed
priority: low
effort: XS (< 1 session)
blocked_by: []
blocks: []
related: [T-20260302-04]
tags: [ticket-plugin, agent, safety]
absorbed_into: T-04c
notes: "Foreground-only enforcement will be addressed as part of T-04c (agent infrastructure)."
```

## Problem

The `ticket-autocreate` agent is designed to run foreground-only (the user sees its output in real-time). But Claude Code agents lack a native foreground/background distinction — there is no mechanism to prevent the agent from being launched in the background via the Agent tool's `run_in_background: true` parameter.

## Context

The adversarial Codex review (thread `019caf2e`) identified this as an unresolved item: "ticket-autocreate foreground-only constraint has no enforcement mechanism (agents lack native foreground/background distinction)."

Running the agent in the background is a concern because:
1. In `suggest` mode: the agent returns a preview for user confirmation, but a background agent's output isn't immediately visible — the user might miss it
2. In `auto_audit`/`auto_silent` mode: less critical since the agent creates tickets autonomously anyway, but the notification template may not surface promptly

The risk is Low because: the agent is invoked proactively by Claude, not by user command. Claude's own judgment about foreground vs background is the de facto enforcement. A user explicitly launching it in background via Agent tool is an unusual edge case.

## Prior Investigation

- No Claude Code platform mechanism for enforcing foreground-only on agents
- Agent `description` field can include "foreground only" but this is advisory, not enforced
- The agent's `tools` list already excludes `Write` as a safety measure — foreground enforcement would be a second safety layer

## Approach

Accept the limitation for v1.0. Document in agent instructions:

1. Add explicit instruction in `ticket-autocreate.md`: "This agent MUST run in the foreground. Do not use `run_in_background: true` when launching this agent."
2. If the agent detects it's running in background (heuristic: no user interaction within N seconds of a `suggest` mode response), log a warning to the audit trail
3. For v1.1: investigate whether a PreToolUse hook on the Agent tool can inspect `run_in_background` and block background launches of specific agents

### Decisions Made
- Advisory enforcement for v1.0 (instruction-level, not mechanical)
- The risk is Low — agent is proactively invoked by Claude, not user-commanded

## Acceptance Criteria
- [ ] Agent instructions explicitly state foreground-only requirement
- [ ] Audit trail logs a warning if background execution is detected (heuristic)
- [ ] v1.1 investigation noted for mechanical enforcement via PreToolUse hook

## Key Files
| File | Role | Look For |
|------|------|----------|
| `docs/plans/2026-03-02-ticket-plugin-design.md:636` | Unresolved item | "foreground-only constraint" |
| (future) `ticket/agents/ticket-autocreate.md` | Agent definition | Foreground instruction |
