# Audit Loop v3.0.0 UX Redesign

**Date:** 2026-01-06
**Status:** Ready for implementation

## Overview

Redesign audit-loop interaction model to use chip-based single-question flow, reducing friction and typing. Claude does more work; user confirms decisions.

## Goals

1. **Reduce typing** — chip selection instead of free-form answers
2. **Single-question flow** — one question at a time, not walls of text
3. **Smart recommendations** — Claude recommends options based on context
4. **Claude-driven work** — Claude audits and decides; user confirms

## Non-Goals

- Changing core audit methodology
- Modifying state persistence logic
- Altering report format

---

## Interaction Model by Phase

| Phase | Style | Description |
|-------|-------|-------------|
| Pre-Analysis | Claude works | Analyze artifact, save structured understanding |
| Stakes Assessment | **Chips** | 4 single questions with options |
| Definition | **Chips** | Goal, scope, assumptions with dynamic options |
| Execution | Claude works | Audit artifact, present findings |
| Verification | Claude works | Verify coverage, present gaps |
| Triage | Confirm | Claude assigns priorities, user confirms/adjusts |
| Design | Collaborative | Conversational finding resolution |
| Verify | Confirm | Claude checks findings addressed, user confirms |
| Ship/Iterate | **Chips** | [Ship] [Iterate] [Expand] decision |

---

## Pre-Analysis Phase (New)

Runs after artifact path confirmed, before stakes assessment.

**Purpose:** Extract structured understanding for dynamic option generation.

**Behavior:**

1. Display: "Analyzing artifact..."
2. Read full artifact
3. Extract structured summary:
   - purpose: What is this artifact about?
   - components: Major elements discussed (3-7 items)
   - concerns: Risks/unknowns flagged in artifact
   - assumptions: What artifact takes for granted
   - dependencies: Systems, APIs, teams referenced
   - type: design_doc | api_spec | incident_report | rfc | other
4. Save to `state.artifact_analysis`
5. Display brief summary to user
6. Proceed to Stakes Assessment

**State schema addition:**

```json
{
  "artifact_analysis": {
    "purpose": "string",
    "components": ["string"],
    "concerns": ["string"],
    "assumptions": ["string"],
    "dependencies": ["string"],
    "type": "string"
  }
}
```

---

## Chip-Based Phases

### Pattern

Every question uses AskUserQuestion:
- Single question per interaction
- 3-4 dynamically generated options from artifact_analysis
- Recommended option first with "(Recommended)" label
- multiSelect only for scope areas
- "Other" always available (built into tool)

### Recommendation Logic

Before each question, consider:
1. **Artifact signals** — what does the document discuss?
2. **Prior answers** — patterns in user's choices
3. **Calibration level** — light/medium/deep influences thoroughness

Place most contextually relevant option first.

### Stakes Assessment (4 questions)

| # | Question | Options | Recommendation Signals |
|---|----------|---------|----------------------|
| 1 | If this design is wrong, how hard to fix? | Easy (1) / Moderate (2) / Permanent (3) | "migration" → (3), "rollback" → (1) |
| 2 | Who's affected if it fails? | Just me (1) / Team (2) / Users (3) | "production" → (3), "internal" → (1) |
| 3 | Will this be referenced later? | One-off (1) / Maybe (2) / Sets pattern (3) | "template" → (3), "experiment" → (1) |
| 4 | Who will see this? | Internal (1) / Shared (2) / Public (3) | "api" → (3), "internal" → (1) |

Score 4-12 determines calibration: 4-6 Light, 7-9 Medium, 10-12 Deep.

### Definition (5 questions)

| # | Question | Option Generation | Multi-select |
|---|----------|------------------|--------------|
| 1 | What outcome do you want from this audit? | Based on artifact_analysis.type | No |
| 2 | Which aspects will you examine? | From artifact_analysis.components | Yes |
| 3 | What are you explicitly NOT auditing? | Inverse of selected scope + common exclusions | Yes |
| 4 | What key assumption does this artifact make? | From artifact_analysis.assumptions | Repeat until done |
| 5 | How will you know the audit is complete? | Based on calibration level | No |

### Ship/Iterate Decision

After Verify phase, present status and chips:

```
Cycle [N] Complete

Results:
- High: [X] addressed, [Y] remaining
- Medium: [X] addressed, [Y] remaining
- Low: [X] addressed, [Y] deferred

Exit criteria ([calibration]): [Met/Not met]
```

**Options:** Ship / Iterate / Expand scope

**Recommendation:**
- Exit criteria met → Ship (Recommended)
- High findings remain → Iterate (Recommended)
- Design revealed new concerns → Expand scope (Recommended)

---

## Confirm-Style Phases

### Pattern

Claude makes decision, presents reasoning, user confirms or adjusts.

Use AskUserQuestion with: [Confirm] [Adjust]

If Adjust: follow-up question for specific changes.

### Triage

**Prioritization logic:**

1. Calibration level influences threshold
2. Findings affecting artifact_analysis.concerns → higher priority
3. Findings blocking artifact_analysis.purpose → High
4. Confidence level caps uncertain findings at Medium

**Presentation:**

```
Triage Complete

Based on [calibration] calibration:

| Finding | Priority | Rationale |
|---------|----------|-----------|
| F1: ... | High | Blocks stated goal |
| F2: ... | Medium | Mentioned in concerns |

[Confirm] [Adjust priorities]
```

### Verify

**Verification logic:**

For each finding: search design output, assess addressed/partial/unaddressed, cite evidence.

**Presentation:**

```
Verification Complete

| Finding | Status | Evidence |
|---------|--------|----------|
| F1: ... | Addressed | Lines 23-31 |
| F2: ... | Partial | Missing edge case |

[Confirm] [Adjust]
```

---

## Resume Behavior

### Resume by Phase

| Phase | Behavior |
|-------|----------|
| pre_analysis | Re-run (artifact may have changed) |
| stakes/definition | Show completed answers, continue from next |
| execution/verification | Show progress, continue work |
| triage/verify | Show status, offer Confirm/Adjust |
| design | Present existing resume dialog |
| ship | Present chips again |

### Artifact Change Detection

On resume, compare artifact mtime to state.updated:

```
The artifact has been modified since your last session.

[A] Re-analyze — Update analysis, continue
[B] Continue as-is — Use previous analysis
[C] Restart — Begin fresh
```

---

## Implementation

### Files to Modify

| File | Changes |
|------|---------|
| SKILL.md | Add interaction patterns section, pre-analysis phase, update sequence |
| references/phase-prompts.md | Restructure for single-question + confirm styles |
| references/state-schema.md | Add artifact_analysis field |
| references/methodology.md | Minor updates to reflect new patterns |

### Version

**v3.0.0** — Interaction model is fundamentally different. Users expecting v2.x behavior would be surprised.

### Migration

None required. State schema is backward compatible (artifact_analysis is additive).

---

## Phase Sequence

```
pre_analysis → stakes_assessment → definition → execution →
verification → triage → design → verify → ship
```

---

## Summary

| Change | Description |
|--------|-------------|
| Pre-analysis phase | Extract artifact understanding upfront |
| Dynamic options | Generated from artifact, not hardcoded |
| Single-question flow | Stakes, Definition, Ship use AskUserQuestion |
| Confirm-style | Triage, Verify use Claude-decides-user-confirms |
| Smart recommendations | Artifact + state + calibration aware |
| Resume improvements | Show progress, handle artifact changes |
