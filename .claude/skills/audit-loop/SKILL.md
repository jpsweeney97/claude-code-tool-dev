---
name: audit-loop
description: Execute the Audit → Design Loop workflow with guided prompts and state persistence. Reduces friction in applying Framework for Rigor, prevents state loss across sessions, and enforces completeness.
license: MIT
metadata:
  version: 1.0.0
  model: claude-opus-4-5-20251101
  timelessness_score: 8
---

# Audit Loop

Execute rigorous audits on artifacts (plans, designs, docs) with state persistence and guided prompts.

**Core mechanic:** Walk through Framework for Rigor interactively, persisting state to `.audit.json` for session resumption.

---

## Contents

- [When to Use](#when-to-use)
- [Entry Point](#entry-point)
- [State Management](#state-management)
- [Workflow](#workflow)
- [Prompts Reference](#prompts-reference)

---

## When to Use

| Situation | Why This Skill Helps |
|-----------|---------------------|
| Design doc needs validation | Surfaces assumptions and gaps before implementation |
| High-stakes decision document | Multiple audit-design cycles increase confidence |
| Inherited artifact needs review | Objective assessment with systematic design follow-up |
| Post-incident design revision | Ensures root causes addressed, not just symptoms |

**Don't use when:**
- Artifact is trivial (low stakes, easily reversible)
- You're the author auditing immediately (wait 24h for objectivity)
- Pure exploration without improvement intent

---

## Entry Point

**Invocation:** `/audit-loop <artifact-path>` or `/audit-loop`

**Behavior:**

1. If artifact path provided:
   - Check for existing `.audit.json` adjacent to artifact
   - If state exists → Offer resume or restart
   - If no state → Begin new audit

2. If no path provided:
   - Ask: "What artifact are you auditing? (provide path)"

### Resume Dialog

When existing state is found:

```
Found in-progress audit (Cycle [N], [phase])

[A] Resume — continue from current phase
[B] Restart — discard progress and begin fresh
```

### State File Location

```
# During audit (active state)
docs/plans/feature-x.audit.json

# After Ship (archived)
docs/plans/feature-x.audit.2026-01-06.json       # State archive
docs/plans/feature-x.audit-report.2026-01-06.md  # Final report
```

---

## State Management

### Schema (v1.0)

```json
{
  "version": "1.0",
  "artifact": "path/to/artifact.md",
  "created": "2026-01-06T12:00:00Z",
  "updated": "2026-01-06T14:30:00Z",

  "calibration": {
    "stakes": {
      "reversibility": 2,
      "blast_radius": 2,
      "precedent": 1,
      "visibility": 2
    },
    "score": 7,
    "level": "medium"
  },

  "cycle": 1,
  "phase": "execution",

  "definition": {
    "goal": "string",
    "scope": ["string"],
    "excluded": ["string"],
    "excluded_rationale": "string",
    "assumptions": ["string"],
    "done_criteria": "string"
  },

  "findings": [
    {
      "id": "F1",
      "description": "string",
      "confidence": "certain|probable|possible|unknown",
      "priority": "high|medium|low",
      "evidence": "string",
      "status": "open|addressed|partial",
      "resolution": "string (optional)"
    }
  ],

  "verification": {
    "counter_conclusion": "string",
    "limitations": ["string"]
  },

  "history": [
    { "timestamp": "ISO-8601", "event": "string", "data": {} }
  ]
}
```

### State Checkpoints

State is saved automatically at:
- After stakes assessment (calibration determined)
- After Phase 1: Definition
- After Phase 2: Execution (findings captured)
- After Phase 3: Verification
- After Triage (priorities assigned)
- Before Design handoff
- After Verify phase
- On Ship (archived with timestamp)

### Phase Values

`stakes_assessment` → `definition` → `execution` → `verification` → `triage` → `design` → `verify` → `ship`

---

## Workflow

### Stakes Assessment

**Purpose:** Determine calibration level before auditing.

**Present this prompt:**

```
Stakes Assessment

Reversibility — if this design is wrong, how hard to fix?
  [A] Easy to undo (1)
  [B] Moderate effort (2)
  [C] Permanent/very costly (3)

Blast radius — who's affected if it fails?
  [A] Just you (1)
  [B] Your team (2)
  [C] Users or organization (3)

Precedent — will this be referenced later?
  [A] One-off (1)
  [B] May be referenced (2)
  [C] Sets a pattern (3)

Visibility — who will see this?
  [A] Internal only (1)
  [B] Shared with others (2)
  [C] Public (3)
```

**Scoring:**
- 4-6 = **Light** calibration
- 7-9 = **Medium** calibration
- 10-12 = **Deep** calibration

**After user responds:**
1. Calculate score by summing values
2. Determine calibration level
3. Save to state: `calibration.stakes`, `calibration.score`, `calibration.level`
4. Report: "Calibration: [level] (score [N]). This affects rigor requirements for each phase."
5. Proceed to Phase 1: Definition

---

### Phase 1: Definition

**Calibration requirements:**

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Goal | Brief | Full | Full |
| Scope | Key boundaries | Complete | Exhaustive + justified |
| Done criteria | Implicit OK | Explicit | Explicit + verified |
| Assumptions | Key only | All | All + testable |
| Simple path | Yes | Yes | Yes + documented |

**Present these prompts sequentially:**

```
Phase 1: Definition

1. AUDIT GOAL — What outcome do you want from this audit?
   (Not the artifact's purpose — YOUR investigation goal)
   Example: "Confidence the design is implementable without major rework"
```

After response, continue:

```
2. SCOPE — What aspects will you examine?
   [A] Architecture & structure
   [B] Error handling & edge cases
   [C] Data flow & state
   [D] Dependencies & integrations
   [E] Security implications
   [F] Other: ___

   (Select all that apply)
```

After scope selection:

```
3. EXCLUSIONS — What are you explicitly NOT examining, and why?

   ⚠️ Red flag check: Are excluded areas actually harder to audit?
   If so, reconsider whether they should be in scope.
```

For Medium/Deep calibration:

```
4. ASSUMPTIONS — What are you taking for granted?
   List each assumption.
   [Deep only: How would you test each?]
```

```
5. DONE CRITERIA — How will you know the audit is complete?
   [Light: Can be implicit, but state it]
   [Medium+: Must be explicit and measurable]
```

```
6. SIMPLE PATH — Is there an obvious conclusion already?
   If so, why isn't it sufficient?
   [Deep: Document this reasoning in state]
```

**After all prompts:**
1. Save responses to `state.definition`
2. Add history event: `phase_1_complete`
3. Proceed to Phase 2: Execution