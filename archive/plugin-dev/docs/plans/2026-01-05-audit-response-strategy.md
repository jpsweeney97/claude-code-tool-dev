# Audit Response Strategy

**Status:** Approved
**Created:** 2026-01-05
**Source:** Three-lens design audit of pipeline orchestrator design

## Context

A three-lens design audit (`--design` preset: Robustness + Minimalist + Capability) identified 5 convergent findings and 4 two-lens findings in the pipeline orchestrator design.

### Convergent Findings (All 3 Lenses)

| Finding | Problem |
|---------|---------|
| Subagent output contract undefined | Can't build orchestrator without knowing what subagents return |
| State management too complex | 83-line schema invites incomplete updates |
| Checkpoint system overengineered | Industrial recovery for 30-min workflows |
| 3 paths unnecessary | Quick/Standard/Full adds cognitive load without value |
| Contract surfacing unreliable | Expecting Claude to self-report assumptions it won't notice |

### Two-Lens Findings

| Finding | Problem |
|---------|---------|
| plugin.json not created | Pipeline produces components but no installable manifest |
| Learning capture produces platitudes | Generic observations, not actionable insights |
| MCP server support missing | Users building MCP plugins fall off pipeline |
| Resume UX format will vary | No template enforcement |

## Approach

**Strategy:** Moderate simplification via incremental commits

- Address all 5 convergent findings
- Add plugin.json creation (2-lens finding with direct user impact)
- Preserve architectural foundation (state file, subagent delegation, staged pipeline)
- Defer MCP server support, checkpoint system, and learning capture to v2

## Decisions

### Paths: Minimal + Rigorous (replaces Quick/Standard/Full)

| Aspect | Minimal | Rigorous |
|--------|---------|----------|
| Intent | Personal tool, quick iteration | Marketplace quality, shared use |
| Stages | Implement → Done | Design → Implement → Test → Done |
| Design doc | No | Yes, per component |
| Integration test | No | Yes, required before "done" |
| Optimization | On request | On request |
| Deployment | On request | On request |

**Path selection:** Single question to user: "Is this plugin for personal use, or will others use it?"

### Subagents: Keep 3 with Stage Isolation

| Subagent | Skills |
|----------|--------|
| pipeline-designer | brainstorming-plugins, brainstorming-skills, brainstorming-hooks, brainstorming-agents, brainstorming-commands |
| pipeline-implementer | implementing-skills, implementing-hooks, implementing-agents, implementing-commands |
| pipeline-optimizer | optimizing-plugins, deploying-plugins |

**Rationale:** Stage isolation via skill restrictions prevents Claude from blurring stage boundaries.

### Subagent Output Contract: YAML Block

```yaml
---
artifacts:
  - path: skills/my-skill/SKILL.md
    type: skill
    action: created  # created | modified | deleted

decisions:
  - key: trigger_strategy
    value: explicit_command_only
    rationale: "Skill is complex; avoid accidental invocation"

contracts:  # Only for pipeline-implementer
  - description: "Assumes hook:block-etc blocks /etc writes"
    source: skill:path-validator
    target: hook:block-etc

errors:  # Empty array if none
  - stage: implementation
    message: "MCP server not responding"
    recoverable: true
---
```

**Subagent instruction:**
> End your response with a fenced YAML block (using `---` delimiters) containing: artifacts, decisions, contracts, errors.

### State Schema: 9 Fields

```json
{
  "schema_version": "1.0",
  "plugin": "my-plugin",
  "created": "2026-01-05T12:00:00Z",
  "updated": "2026-01-05T14:30:00Z",
  "path": "rigorous",
  "stage": "implementing",
  "components": [
    {
      "type": "skill",
      "name": "my-skill",
      "status": "implemented",
      "design_doc": "docs/plans/2026-01-05-my-skill-design.md"
    }
  ],
  "contracts": [
    "skill:path-validator assumes hook:block-etc blocks /etc writes"
  ],
  "notes": "Exit code 2 shows stderr to Claude, not user."
}
```

**Cut:** analysis block, decisions per-component, learnings taxonomy, integration.results, escalation_triggers, blockers, all checkpoint fields.

### Contract Surfacing: Post-hoc Grep

**Comment convention:**
```python
# CONTRACT: assumes hook:block-etc blocks /etc/* writes
```

**Extraction:**
```bash
grep -rh "# CONTRACT:" skills/ hooks/ agents/ commands/ | \
  sed 's/.*# CONTRACT: //' | sort -u
```

**Subagent instruction:**
> When your implementation assumes behavior from another component, add a comment: `# CONTRACT: assumes {component}:{name} {behavior}`. You do NOT need to include contracts in your YAML output.

### Plugin.json Creation

**When:** After first component reaches "implemented" status

**Template:**
```json
{
  "name": "my-plugin",
  "version": "0.1.0",
  "description": "Created by pipeline orchestrator",
  "author": {
    "name": "User"
  },
  "components": {
    "skills": "./skills/"
  }
}
```

**Orchestrator prompt:** "Created `.claude-plugin/plugin.json`. Update `description` and `author.name` before publishing."

### Checkpoint System: Deferred

**Rationale:** All 3 lenses questioned whether checkpoint complexity is warranted for workflows that complete in one session. Claude Code already has `/save-handoff`. Add in v2 if users complain about lost progress.

## Implementation Plan

### Commit Sequence

```
1. refactor(plugin-dev): remove checkpoint system
   - Delete checkpoint sections from design doc
   - Remove checkpoint-related state fields

2. refactor(plugin-dev): consolidate paths to Minimal/Rigorous
   - Update path descriptions
   - Change path selection from complexity analysis to single question
   - Update state schema path values

3. feat(plugin-dev): define subagent output contract schema
   - Add YAML schema specification
   - Add subagent instructions
   - Define parsing requirements for orchestrator

4. refactor(plugin-dev): simplify state schema to 9 fields
   - Replace 83-line schema with 9-field version
   - Update all state references

5. refactor(plugin-dev): change contract surfacing to post-hoc grep
   - Remove self-report expectation from subagent contract
   - Add CONTRACT comment convention
   - Update integration testing section

6. feat(plugin-dev): add plugin.json creation to pipeline
   - Define creation trigger (first component implemented)
   - Add minimal template
   - Add user prompt for required updates
```

### Files Modified

| File | Changes |
|------|---------|
| `docs/plans/2026-01-05-pipeline-orchestrator-design.md` | All sections updated per commits |
| `docs/ADR-001-plugin-development-pipeline.md` | Update to reflect Minimal/Rigorous paths |

## Deferred to v2

| Item | Rationale |
|------|-----------|
| Checkpoint/recovery system | Add if users report lost progress |
| MCP server component support | Requires new brainstorming/implementing skills |
| Multi-user concurrent editing | Edge case for team plugins |
| Version management | Add when marketplace publishing matures |
| State write failure handling | Low probability, add with checkpoint system |
| Learning capture | Generic outputs; revisit with better prompts |

## Verification

Strategy complete when:
- [ ] All 6 commits applied
- [ ] Design document internally consistent
- [ ] State schema matches subagent output contract
- [ ] Paths map to available skills
- [ ] ADR updated to reflect changes
