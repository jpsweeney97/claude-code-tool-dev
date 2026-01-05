# Plugin Development Pipeline

**Load this reference when:** understanding the full plugin development workflow, planning multi-component plugins, or entering the pipeline at a later stage.

## Stages & Artifacts

| Stage | Skill | Output Artifact |
|-------|-------|-----------------|
| **Triage** | brainstorming-plugins | Component list with rationale |
| **Design** | brainstorming-{component} | Design doc: `docs/plans/YYYY-MM-DD-<name>-design.md` |
| **Implement** | implementing-{component} | Working component + passing tests |
| **Optimize** | optimizing-plugins | Optimization doc + improvements |
| **Deploy** | deploying-plugins | Published plugin |

## Data Flow

```
Component List        Design Document         Working Plugin
    │                      │                       │
    ▼                      ▼                       ▼
┌────────┐  list    ┌────────────┐  doc    ┌──────────────┐
│ Triage │ ──────►  │   Design   │ ──────► │  Implement   │
└────────┘          └────────────┘         └──────────────┘
                                                   │
                    ┌──────────────────────────────┘
                    │ working plugin
                    ▼
             ┌────────────┐  optimized    ┌────────────┐
             │  Optimize  │ ────────────► │   Deploy   │
             └────────────┘               └────────────┘
```

## Entry Points

Users can enter at any stage based on what they already have:

| Starting Point | Prerequisites | First Skill |
|----------------|---------------|-------------|
| "I have an idea" | None | `/brainstorming-plugins` |
| "I know I need a skill" | Component decision made | `/brainstorming-skills` |
| "I have a design" | Design document exists | `/implementing-skills` |
| "I have a working plugin" | Plugin functional | `/optimizing-plugins` |
| "I want to publish" | Plugin ready | `/deploying-plugins` |

## If a Stage Fails

| Stage | Failure Signal | Resolution |
|-------|----------------|------------|
| **Triage** | Can't determine components | Ask more questions; user clarifies problem |
| **Design** | Design doesn't converge | Escalate to `/skillforge` for deep analysis |
| **Design** | Scope too broad | Apply YAGNI; split into multiple components |
| **Implement** | Tests don't pass | Iterate RED-GREEN-REFACTOR; don't skip phases |
| **Implement** | Design was wrong | Return to brainstorming-{component} |
| **Optimize** | Validation panel rejects | Address feedback; re-run affected lenses |
| **Deploy** | Packaging fails | Fix issues per error messages; re-validate |

## Component-Specific Skills

### Skills (Slice 1 - Active)

| Stage | Skill | Status |
|-------|-------|--------|
| Design | `/brainstorming-skills` | Active |
| Implement | `/implementing-skills` | Active |

### Hooks (Slice 2 - Planned)

| Stage | Skill | Status |
|-------|-------|--------|
| Design | `/brainstorming-hooks` | Coming soon |
| Implement | `/implementing-hooks` | Coming soon |

### Agents (Slice 3 - Planned)

| Stage | Skill | Status |
|-------|-------|--------|
| Design | `/brainstorming-agents` | Coming soon |
| Implement | `/implementing-agents` | Coming soon |

### Commands (Slice 4 - Planned)

| Stage | Skill | Status |
|-------|-------|--------|
| Design | `/brainstorming-commands` | Coming soon |
| Implement | `/implementing-commands` | Coming soon |

## Multi-Component Plugins

When triage identifies multiple components (e.g., "Skill + Hook"):

1. **Complete one component at a time** — Don't parallelize design/implement
2. **Order by dependencies** — If Hook references Skill, build Skill first
3. **Track completion** — Note which components are done before moving to Optimize
4. **Optimize once** — Run optimization on complete plugin, not per-component

## Key Principles

- **Vertical slices** — Complete the full pipeline for one component before starting another
- **YAGNI** — Challenge every component; simpler is better
- **TDD for skills** — No skill without failing test first
- **Single source of truth** — This document is the authoritative pipeline reference
