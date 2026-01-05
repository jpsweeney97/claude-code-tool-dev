---
name: brainstorming-plugins
description: Use when starting plugin development, "build a plugin", "create a plugin for X", or unsure which components are needed. Identifies which components your plugin needs, then hands off to component-specific design skills.
---

# Plugin Component Triage

Identify which components your plugin needs, then hand off to component-specific design skills.

## Fast Path

If user request explicitly mentions component type, skip triage:

| User Says | Skip To |
|-----------|---------|
| "I want to build a skill for X" | `/brainstorming-skills` |
| "I need a hook that Y" | `/brainstorming-hooks` |
| "Create a command for Z" | `/brainstorming-commands` |
| "Build an agent that W" | `/brainstorming-agents` |

**Only use triage when:** User is unsure what components they need, or describes a problem without specifying component type.

## Prerequisites

None — this is the entry point.

## The Process

### 1. Understand the Problem

Ask one question at a time:
- What problem does this solve?
- Who uses it? (User explicitly? Claude automatically? Both?)
- When should it activate? (Explicit command? Automatic trigger? Event-driven?)

### 2. Distribution & Scope

Before selecting components, understand the context:
- Who uses this? (Personal, team, community?)
- Installation scope: user, project, or managed?
- Does it need marketplace distribution?

This affects complexity decisions — a personal tool can be simpler.

### 3. Component Selection

Use decision matrix:

| Need | Component | Why |
|------|-----------|-----|
| "Claude needs knowledge about X" | Skill | On-demand guidance |
| "User runs action X explicitly" | Command | User-initiated action |
| "Delegate complex work" | Agent | Isolated execution |
| "X must ALWAYS happen on event Y" | Hook | Guaranteed automation |
| "Connect to external service X" | MCP Server | External API tools |

Present your recommendation with rationale for each component.

### 4. Simplicity Check (YAGNI)

Before confirming:
- What's the minimum that solves the problem?
- Can one component type handle it, or are multiple truly needed?
- What can we remove and still succeed?

Challenge your own recommendations. Simpler is better.

### 5. Confirm & Handoff

Present final recommendation: "For this plugin, I recommend:
- Skill for [reason]
- Hook for [reason]"

Get user confirmation before handoff.

## Next Step

Run the command for your first component:

| Component | Command |
|-----------|---------|
| Skill | `/brainstorming-skills` |
| Hook | `/brainstorming-hooks` |
| Agent | `/brainstorming-agents` |
| Command | `/brainstorming-commands` |

Copy-paste the command above to continue.

## Pipeline Context

This skill is **Stage 1: Triage** in the plugin development pipeline.

For the full pipeline overview including stages, data flow, entry points, and failure handling, see:
- [references/pipeline-overview.md](references/pipeline-overview.md)

| Aspect | Value |
|--------|-------|
| This stage | Identify components needed |
| Prerequisite | None (this is the entry point) |
| Hands off to | `/brainstorming-{component}` |

## Key Principles

- **One question at a time** — Don't overwhelm
- **Prefer multiple choice** — Easier to answer when possible
- **Explain WHY each component** — Not just what
- **YAGNI ruthlessly** — Challenge every component
- **User confirms before handoff** — No surprises

## What This Skill Does NOT Do

- Detailed component design (→ brainstorming-{component})
- Implementation guidance (→ implementing-{component})
- Optimization (→ optimizing-plugins)
- Deployment (→ deploying-plugins)

## References

- [references/pipeline-overview.md](references/pipeline-overview.md) — Full pipeline stages and data flow
- [references/component-decision-guide.md](references/component-decision-guide.md) — Detailed component selection criteria
