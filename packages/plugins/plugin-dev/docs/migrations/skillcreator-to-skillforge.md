# SkillCreator to SkillForge Migration

## What Changed

The upstream repository `tripleyak/skill-creator-and-improver` has been replaced by `tripleyak/SkillForge`.

### Version Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Skill name** | `skillcreator` | `skillforge` |
| **Version** | 3.2.0 | 4.0.0 |
| **Phases** | 4-phase | 5-phase (new Phase 0) |
| **Upstream repo** | `tripleyak/skill-creator-and-improver` | `tripleyak/SkillForge` |

### New Phase 0: Triage

SkillForge v4.0 adds a **triage phase** that runs BEFORE analysis. This prevents ecosystem bloat by checking if an existing skill already serves the purpose.

**Triage Outcomes:**

| Outcome | Condition | Action |
|---------|-----------|--------|
| `USE_EXISTING` | Existing skill covers the need (≥80% match) | Point to existing skill |
| `IMPROVE_EXISTING` | Close match exists (50-79% match) | Enhance existing skill |
| `CREATE_NEW` | Genuinely novel need (<50% match) | Full 4-phase creation |
| `COMPOSE` | Multiple skills combine | Orchestration pattern |
| `CLARIFY` | Request ambiguous | Ask clarifying questions |

### New Scripts

| Script | Purpose |
|--------|---------|
| `triage_skill_request.py` | Phase 0 triage logic and domain matching |
| `discover_skills.py` | Skill indexing and ecosystem discovery |

## What to Update

### If You Reference `skillcreator` Directly

```diff
- Use the `skillcreator` skill
+ Use the `skillforge` skill
```

### If You Have Custom Scripts Calling Validation

```diff
- python skills/skillcreator/scripts/quick_validate.py
+ python skills/skillforge/scripts/quick_validate.py
```

### Workflow Changes

The `/plugin-dev:create-skill` command now:

1. **Triages first** - May suggest existing skill instead of creating new
2. **Same quality** - Still uses 11 thinking lenses, evolution scoring, synthesis panel
3. **Anti-duplication** - Actively prevents ecosystem bloat

## Backwards Compatibility

The skill functionality is identical. The triage phase is additive - it makes the skill SMARTER about when to create new skills vs. use existing ones.

Users who always want new skill creation can skip triage by being explicit:

```
SkillForge: create a NEW skill for X (confirm this is novel, no existing skill covers this)
```

## Sync Workflow

The sync workflow (`.github/workflows/sync-skillforge.yml`) continues to:

- Poll upstream every 48 hours
- Create PRs for updates
- Run validation before merging

To manually trigger a sync:

```bash
gh workflow run sync-skillforge.yml --field force_sync=true
```
