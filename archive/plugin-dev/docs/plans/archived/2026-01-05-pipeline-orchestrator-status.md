# Pipeline Orchestrator Design — Current Status

**File:** `2026-01-05-pipeline-orchestrator-design.md`
**Status:** Draft (814 lines)
**Last Updated:** 2026-01-05

## Document Structure

| Section | Lines | Content |
|---------|-------|---------|
| Problem Statement | 8-40 | Original problems + three-lens audit findings |
| Architecture Overview | 42-82 | Diagram + key principles |
| Complexity Analysis | 84-122 | Signals, escalation triggers, example output |
| **Paths** | 124-169 | **Minimal/Rigorous** (simplified from Quick/Standard/Full) |
| Path Graduation | 171-219 | Detection + graduation options |
| **State Management** | 221-282 | **9-field schema** (simplified from 83 lines) |
| **Skill Invocation** | 284-385 | Subagents + **output contract schema** |
| Entry Points | 387-422 | Command + skill entry |
| **Plugin Manifest** | 424-482 | **Auto-creation** (new section) |
| Error Handling | 484-597 | Architecture, failure classification, session mgmt |
| **Integration Testing** | 599-762 | Scope, scenarios, **grep-based contract surfacing** |
| Deferred Topics | 764-788 | Subagent design, **checkpoint system** |
| Open Questions | 781-788 | 4 remaining questions |
| Appendix | 790-804 | Audit summary |
| Changelog | 806-814 | 4 entries |

## What Changed (Audit Response)

| Before | After |
|--------|-------|
| 3 paths (Quick/Standard/Full) | 2 paths (Minimal/Rigorous) |
| 83-line state schema | 9-field schema |
| Checkpoint system | Deferred to v2 |
| Self-reported contracts | Grep-based extraction |
| No plugin.json creation | Auto-creates manifest |
| Decisions/learnings in schema | Flattened to `notes` field |

## Implementation Status

| Component | Design | Built | Notes |
|-----------|--------|-------|-------|
| Orchestrator skill | ✅ | ❌ | Entry point, routes to subagents |
| pipeline-designer agent | ✅ | ❌ | Needs system prompt |
| pipeline-implementer agent | ✅ | ❌ | Needs system prompt |
| pipeline-optimizer agent | ✅ | ❌ | Needs system prompt |
| State file management | ✅ | ❌ | Read/write/reconcile |
| Plugin.json creation | ✅ | ❌ | Auto-generate manifest |
| create-plugin command | ✅ | ❌ | Replace legacy command |
| Integration tests | ✅ | ❌ | Scenario format defined |

## Roadmap (Prioritized)

1. **Resolve open questions** — Need decisions before implementation
2. **Write subagent definitions** — System prompts for 3 agents
3. **Build orchestrator skill** — Core routing logic
4. **Build state management** — Schema + reconciliation
5. **Build create-plugin command** — Entry point
6. **Integration test** — End-to-end with real plugin

## Deferred to v2

| Item | Rationale |
|------|-----------|
| Checkpoint/recovery | Add if users report lost progress |
| MCP server support | Requires new brainstorming/implementing skills |
| Learning capture | Generic outputs; revisit with better prompts |
| Multi-user editing | Edge case for team plugins |

## Open Questions (Unresolved)

1. **State file location:** `docs/plans/plugin-state.json` vs root-level?
2. **Notes export:** Auto-export to README at publish time?
3. **Parallel component work:** Can multiple components be designed/implemented in parallel?
4. **Validation enforcement:** Gate stage transitions or advisory only?

## Related Documents

- [Pipeline Orchestrator Design](2026-01-05-pipeline-orchestrator-design.md) — Full design document
- [Audit Response Strategy](2026-01-05-audit-response-strategy.md) — Decisions from three-lens audit
- [Audit Simplification Plan](2026-01-05-audit-simplification-plan.md) — Implementation plan (7 tasks)
- [ADR-001](../ADR-001-plugin-development-pipeline.md) — Architecture decision record

## Pipeline Skills

### Triage Stage

| Skill | Path | Purpose |
|-------|------|---------|
| brainstorming-plugins | `skills/brainstorming-plugins/` | Analyze request, determine components needed |

### Design Stage (pipeline-designer subagent)

| Skill | Path | Purpose |
|-------|------|---------|
| brainstorming-skills | `skills/brainstorming-skills/` | Design skill structure and behavior |
| brainstorming-hooks | `skills/brainstorming-hooks/` | Design hook triggers and logic |
| brainstorming-agents | `skills/brainstorming-agents/` | Design agent capabilities |
| brainstorming-commands | `skills/brainstorming-commands/` | Design command interface |

### Implementation Stage (pipeline-implementer subagent)

| Skill | Path | Purpose |
|-------|------|---------|
| implementing-skills | `skills/implementing-skills/` | TDD implementation of skills |
| implementing-hooks | `skills/implementing-hooks/` | TDD implementation of hooks |
| implementing-agents | `skills/implementing-agents/` | TDD implementation of agents |
| implementing-commands | `skills/implementing-commands/` | TDD implementation of commands |

### Optimization Stage (pipeline-optimizer subagent)

| Skill | Path | Purpose |
|-------|------|---------|
| optimizing-plugins | `skills/optimizing-plugins/` | Six-lens optimization review |

### Deployment Stage

| Skill | Path | Purpose |
|-------|------|---------|
| deploying-plugins | `skills/deploying-plugins/` | Marketplace publishing |

### Reference Skills (not invoked by pipeline, structural docs)

| Skill | Path | Purpose |
|-------|------|---------|
| skill-development | `skills/skill-development/` | Skill structure reference |
| hook-development | `skills/hook-development/` | Hook structure reference |
| agent-development | `skills/agent-development/` | Agent structure reference |
| command-development | `skills/command-development/` | Command structure reference |
| skillforge | `skills/skillforge/` | Deep skill analysis (escalation target) |
| plugin-structure | `skills/plugin-structure/` | Plugin manifest reference |
| plugin-settings | `skills/plugin-settings/` | Settings configuration |
| plugin-audit | `skills/plugin-audit/` | Plugin validation |
| mcp-integration | `skills/mcp-integration/` | MCP server integration (v2) |

## Session Log

| Date | Commits | Summary |
|------|---------|---------|
| 2026-01-05 | 9 | Audit response: simplified paths (Minimal/Rigorous), 9-field state schema, grep-based contracts, plugin.json creation, ADR update |

### 2026-01-05 Commits

```
387253e docs(plugin-dev): update ADR-001 for Minimal/Rigorous paths
e75b7d8 feat(plugin-dev): add plugin.json creation to pipeline
47cf277 refactor(plugin-dev): change contract surfacing to post-hoc grep
f3dc9d3 fix(plugin-dev): clarify decisions/learnings storage in notes field
3f51041 refactor(plugin-dev): simplify state schema to 9 fields
5b56d26 fix(plugin-dev): correct YAML extraction regex for multiline
064a97f feat(plugin-dev): define subagent output contract schema
f261d30 refactor(plugin-dev): consolidate paths to Minimal/Rigorous
1c50657 refactor(plugin-dev): remove checkpoint system from orchestrator design
```

## Blockers

(none currently)
