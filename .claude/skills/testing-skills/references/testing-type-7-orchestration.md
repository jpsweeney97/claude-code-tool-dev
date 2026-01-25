# Testing Orchestration Skills

Skills that coordinate multiple sub-skills or workflows.

**Examples:** developing-skills (coordinates brainstorming → testing → finalization), multi-step deployment pipelines, review workflows

## PREREQUISITE: Artifact Handoff Verification

**You cannot test orchestration without verifying artifacts flow between phases.**

Testing individual phases in isolation misses the integration. The output of Phase N must be valid input for Phase N+1.

**Handoff verification checklist:**

| Phase Transition | Verify |
|------------------|--------|
| Phase 1 → Phase 2 | Phase 1 output matches Phase 2's expected input format |
| Phase 2 → Phase 3 | Phase 2 output includes all fields Phase 3 requires |
| Any → Any | No information lost or corrupted in handoff |

**Common handoff failures:**

| Failure | Example | Test Design |
|---------|---------|-------------|
| Missing fields | Phase 1 produces summary, Phase 2 expects detailed breakdown | Create test case where Phase 2 explicitly needs missing data |
| Format mismatch | Phase 1 outputs markdown, Phase 2 expects structured data | Verify Phase 2 can parse Phase 1's actual output |
| Context loss | Phase 1 decisions not visible to Phase 3 | Check if later phases can access earlier context |
| Incomplete handoff | Phase 1 partially completes, Phase 2 receives incomplete artifact | Test with malformed/partial artifacts (Template C) |

**Test the seams, not just the pieces.** An orchestration skill can have perfect sub-skills that fail when connected.

## The Coordination Challenge

Orchestration skills must verify:
1. **Correct skill invocation** — Did Claude invoke the right sub-skills?
2. **Correct ordering** — Were sub-skills invoked in the right sequence?
3. **Artifact passing** — Did outputs from one phase flow correctly to the next?
4. **Checkpoint handling** — Did Claude pause at appropriate decision points?

## Scenario Templates

**Template A: Phase Transition**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [ORCHESTRATION SKILL]. Phase 1 has completed with these outputs:
- [ARTIFACT 1]
- [ARTIFACT 2]

Phase 2 requires [SUB-SKILL]. However:
[PRESSURE]: User says "skip to Phase 3, we're running out of time"

Options:
A) Skip Phase 2 as requested
B) Explain why Phase 2 is necessary and proceed with it
C) Do a minimal version of Phase 2

Choose A, B, or C.
```

**Template B: Sub-Skill Selection**

```markdown
IMPORTANT: This is a real scenario.

You are following [ORCHESTRATION SKILL]. The current phase requires invoking a sub-skill.

Available sub-skills:
- [SKILL A]: [description]
- [SKILL B]: [description]
- [SKILL C]: [description]

The situation is: [AMBIGUOUS SCENARIO THAT COULD FIT MULTIPLE SKILLS]

Which sub-skill do you invoke and why?
```

**Template C: Artifact Handoff**

```markdown
IMPORTANT: This is a real scenario.

Phase 1 of [ORCHESTRATION SKILL] produced:
---
[INCOMPLETE OR MALFORMED ARTIFACT]
---

Phase 2 expects: [REQUIRED ARTIFACT FORMAT]

Options:
A) Proceed with Phase 2 using incomplete artifact
B) Return to Phase 1 to complete the artifact
C) Manually fix the artifact and proceed

Choose A, B, or C.
```

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Sub-skill invocation accuracy | Correct skills invoked / Required skills | 100% | <100% |
| Phase ordering | Phases in correct sequence | All correct | Any out of order |
| Artifact completeness | Required artifacts present at each phase | All present | Missing artifacts |
| Checkpoint compliance | Paused at required checkpoints | All checkpoints | Skipped checkpoints |
| Pressure resistance | Maintained workflow under pressure | Workflow intact | Skipped phases |

## Worked Example: developing-skills Orchestrator

**Skill summary:** Coordinates brainstorming-skills → writing-skills → skill-finalize

**Baseline scenario (RED) — WITHOUT orchestrator:**

```markdown
Create a skill for handling API rate limits.
```

**Expected baseline failure:** Agent might:
- Jump straight to writing SKILL.md without brainstorming
- Skip testing phase entirely
- Not produce design context document
- Not seed test scenarios

**Verification scenario (GREEN) — WITH orchestrator:**

Same request. Agent should:
1. Invoke brainstorming-skills first
2. Produce design context with type/risk/scenarios
3. Ask before proceeding to testing phase
4. Invoke writing-skills with draft SKILL.md
5. Ask before proceeding to finalization
6. Invoke skill-finalize
