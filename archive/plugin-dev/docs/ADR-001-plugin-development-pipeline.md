# ADR-001: Plugin Development Pipeline Architecture

## Status

Accepted

## Context

The plugin-dev plugin had accumulated skills for plugin development without a clear workflow connecting them. Users faced several problems:

- **Unclear entry points**: Multiple skills existed (skillforge, skill-development, writing-skills) without guidance on which to use when
- **No consistent pattern**: Each component type (skills, hooks, agents, commands) had different development approaches
- **Missing handoffs**: Skills lacked explicit prerequisites and didn't direct users to the next step
- **Scope confusion**: Some skills tried to do too much (triage + design + implementation)

**Forces at play:**

| Force | Tension |
|-------|---------|
| Discoverability | Users must find the right skill quickly |
| Consistency | Same mental model should apply to all component types |
| Completeness | Pipeline should cover full lifecycle (design → deploy) |
| Simplicity | Avoid over-engineering for simple cases |
| Maintainability | Changes to one component type shouldn't require rewriting everything |

## Decision

We will structure plugin-dev around a **staged pipeline** with consistent patterns for each component type.

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────┐
│ TRIAGE: brainstorming-plugins                            │
│                                                          │
│ Output: Component list (e.g., "Skill + Hook")            │
│ Handoff: "Use brainstorming-{type} for each component"  │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ DESIGN: brainstorming-{type}                             │
│ Light: Collaborative dialogue                            │
│ Deep: → skillforge                                       │
│                                                          │
│ Output: Design document                                  │
│ Handoff: "Use implementing-{type} to build it"          │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ IMPLEMENT: implementing-{type}                           │
│ TDD workflow                                             │
│ Iron Law: "Test invocation exhaustively before           │
│           orchestration"                                 │
│                                                          │
│ Output: Working, tested component                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
               ┌────────────────────┐
               │ What's next?       │
               └────────────────────┘
                        │
        ┌───────────────┼───────────────┬─────────────────┐
        │               │               │                 │
        ▼               ▼               ▼                 ▼
  ┌───────────┐  ┌─────────────┐  ┌──────────┐    ┌──────────┐
  │ More      │  │ Polish      │  │ Publish  │    │ Personal │
  │ components│  │             │  │          │    │ use only │
  └───────────┘  └─────────────┘  └──────────┘    └──────────┘
        │               │               │                 │
        │               ▼               │                 │
        │  ┌─────────────────────────┐  │                 │
        │  │ OPTIMIZE:               │  │                 │
        │  │ optimizing-plugins      │  │                 │
        │  │ 6 lenses, validation    │  │                 │
        │  └─────────────────────────┘  │                 │
        │               │               │                 │
        │               ▼               │                 │
        │  ┌─────────────────────────┐  │                 │
        │  │ DEPLOY:                 │◄─┘                 │
        │  │ deploying-plugins       │                    │
        │  └─────────────────────────┘                    │
        │               │                                 │
        ▼               ▼                                 ▼
┌─────────────┐  ┌─────────────┐                   ┌─────────────┐
│ Loop back   │  │ Published   │                   │ Done        │
│ to DESIGN   │  │ plugin      │                   │ (active in  │
│ for next    │  │             │                   │ ~/.claude/) │
│ component   │  │             │                   │             │
└─────────────┘  └─────────────┘                   └─────────────┘
```

**Note:** The pipeline orchestrator offers two paths:
- **Minimal:** Implement → Done (personal use)
- **Rigorous:** Design → Implement → Test → Done (shared use)

Path selection via single question: "Is this plugin for personal use, or will others use it?"

### Component Types

Each component type gets its own brainstorming-X and implementing-X pair:

| Component | Design Skill | Implementation Skill | Reference Skill |
|-----------|--------------|---------------------|-----------------|
| Skills | brainstorming-skills | implementing-skills | skill-development |
| Hooks | brainstorming-hooks | implementing-hooks | hook-development |
| Agents | brainstorming-agents | implementing-agents | agent-development |
| Commands | brainstorming-commands | implementing-commands | command-development |

Reference skills provide structural documentation; brainstorming/implementing skills provide workflow.

### Stages & Artifacts

| Stage | Skill | Output Artifact |
|-------|-------|-----------------|
| **Triage** | brainstorming-plugins | Component list with rationale |
| **Design** | brainstorming-{component} | Design doc: `docs/plans/YYYY-MM-DD-<name>-design.md` |
| **Implement** | implementing-{component} | Working component + passing tests |
| **Optimize** | optimizing-plugins | Optimization doc + improvements |
| **Deploy** | deploying-plugins | Published plugin |

### Failure Handling

| Stage | Failure Signal | Resolution |
|-------|----------------|------------|
| Triage | Can't determine components | Ask more questions; user clarifies problem |
| Design | Design doesn't converge | Escalate to skillforge for deep analysis |
| Design | Scope too broad | Apply YAGNI; split into multiple components |
| Implement | Tests don't pass | Iterate RED-GREEN-REFACTOR; don't skip phases |
| Implement | Design was wrong | Return to brainstorming-{component} |
| Optimize | Validation panel rejects | Address feedback; re-run affected lenses |
| Deploy | Packaging fails | Fix issues per error messages; re-validate |

### Entry Points

Users can enter at any stage based on what they already have:

| Starting Point | Prerequisites | First Skill |
|----------------|---------------|-------------|
| "I have an idea" | None | brainstorming-plugins |
| "I know I need a skill" | Component decision made | brainstorming-skills |
| "I have a design" | Design document exists | implementing-skills |
| "I have a working plugin" | Plugin functional | optimizing-plugins |
| "I want to publish" | Plugin ready | deploying-plugins |

### Implementation Approach

Implemented via vertical slices — complete one component type fully before adding the next:

| Slice | Component | Status |
|-------|-----------|--------|
| 1 | Skills | Implemented |
| 2 | Hooks | Implemented |
| 3 | Agents | Implemented |
| 4 | Commands | Implemented |

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Vertical slices over horizontal batches | Validates architecture early, ships value fast |
| Comprehensive refactor over incremental | Clean architecture compounds; patching accumulates debt |
| Light/deep toggle in design skills | Prevents over-engineering simple skills |
| TDD stays in implementation | Testing IS implementation in TDD; can't separate |
| Pipeline overview in triage skill | Entry point is authoritative source for pipeline |
| Explicit handoff artifacts | Clear contracts between stages |
| Iron Law for implementing-X | "Test invocation exhaustively before orchestration" prevents common failures |
| Two paths (Minimal/Rigorous) | Clear intent: personal vs. shared use |

## Consequences

**Positive:**

- Consistent mental model across all component types
- Clear handoffs with explicit artifacts (design doc → working component)
- Users can enter at any stage based on what they already have
- Reference skills (skill-development, hook-development, etc.) remain for structural details
- Failure handling defined for each stage

**Negative:**

- More skills to maintain (8 new brainstorming/implementing skills)
- Users must learn pipeline stages (overhead for very simple cases)
- Updating one brainstorming-X may require updating all for consistency
- Vertical slices mean some component types were delayed

**Neutral:**

- skillforge remains separate (deep analysis tool, not part of standard flow)
- Existing reference skills unchanged (structural documentation role)

## Updates

- **2026-01-03**: deploying-plugins implemented (was originally deferred for MVP). Full pipeline now complete.
- **2026-01-05**: Three-lens audit identified gaps (no session resume, validation advisory, overhead for simple cases). Pipeline orchestrator design started — see [Pipeline Orchestrator Design](plans/2026-01-05-pipeline-orchestrator-design.md).
- **2026-01-05**: Audit response applied — paths simplified to Minimal/Rigorous, checkpoint system deferred to v2, state schema reduced to 9 fields. See [Audit Response Strategy](plans/2026-01-05-audit-response-strategy.md).
