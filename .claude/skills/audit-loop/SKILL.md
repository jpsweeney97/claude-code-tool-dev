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

---

### Phase 2: Execution

**Calibration requirements:**

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Evidence collected | Key sources | Multiple sources | Exhaustive |
| Evidence levels noted | — | Yes | Yes |
| Disconfirmation | Brief | Systematic | Adversarial |
| Negative findings | — | Documented | Documented |
| Coverage tracked | List | Matrix | Matrix + verified |
| Methodology recorded | Brief | Full | Timestamped |

**Evidence Hierarchy:**
- **Primary:** Direct observation (read file, run code, see output)
- **Secondary:** Documentation (README says, comments state)
- **Tertiary:** Inference (pattern suggests, absence implies)

**Present this prompt:**

```
Phase 2: Execution

For each scope area, we'll:
1. Collect evidence (cite specific lines/sections)
2. Note evidence level (Primary/Secondary/Tertiary)
3. Seek DISCONFIRMATION — what would prove this area is fine?
4. Document negatives — what did you look for but NOT find?

Let's start with: [first scope item]

Read the artifact and share your observations.
```

**For each scope area, guide the user through:**

```
Coverage for [scope item]:

Evidence collected:
- [user provides]

Evidence level: [Primary/Secondary/Tertiary]

Disconfirmation attempt:
- What would prove this area is correct? [user responds]
- Did you find that proof? [yes/no/partial]

Negative findings:
- What did you look for but NOT find?

Findings from this area:
- [capture any issues discovered]
```

**Finding format:**

```
Finding [ID]: [description]
Evidence: [specific citation with line numbers]
Evidence level: [Primary/Secondary/Tertiary]
Confidence: [Certain/Probable/Possible/Unknown]
```

**After all scope areas examined:**

```
Coverage Matrix

| Area | Examined | Evidence Level | Findings | Gaps |
|------|----------|----------------|----------|------|
[auto-populate from responses]

[Medium+: Methodology — what tools/process did you use?]

⚠️ Red flag check: Are you only finding confirming evidence?
If all findings point one direction, actively seek counterexamples.
```

**After Phase 2:**
1. Save findings to `state.findings`
2. Add history event: `findings_complete` with count
3. Proceed to Phase 3: Verification

---

### Phase 3: Verification

**Calibration requirements:**

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Coverage verified | Quick check | Full check | Independent check |
| Reasoning verified | Self-check | Self-check | Peer check |
| Limitations stated | Key | Full | Comprehensive |
| Counter-conclusion | — | Yes | Adversarial |
| Confidence labeled | Yes | Yes | Yes |

**Present these prompts:**

```
Phase 3: Verification

1. COVERAGE CHECK — Review the coverage matrix. Any gaps?

   [Deep: Would an independent reviewer find the same things?]
```

```
2. REASONING CHECK — For each finding:

   Finding [ID]: [description]
   Evidence: [citation]

   Does the evidence actually support this conclusion?
   [Yes / No / Partially]

   [If No/Partially: Revise finding or demote confidence]
```

For Medium/Deep calibration:

```
3. COUNTER-CONCLUSION — What's the best argument that this artifact is FINE as-is?

   [Medium: State the argument]
   [Deep: Steelman it — make it as strong as possible, then respond]
```

```
4. CONFIDENCE LABELS — Review each finding:

   [List findings]

   For each, assign: Certain / Probable / Possible / Unknown

   Certain = Direct evidence, no alternative explanation
   Probable = Strong evidence, alternatives unlikely
   Possible = Some evidence, alternatives exist
   Unknown = Insufficient evidence to judge
```

```
5. LIMITATIONS — What did this audit NOT examine?

   List blind spots readers should know about:
   - [user provides]
```

**After Phase 3:**
1. Save verification to `state.verification`
2. Update finding confidence levels
3. Add history event: `verification_complete`
4. Proceed to Triage

---

### Triage

**Purpose:** Prioritize findings before design phase.

**Present this prompt:**

```
Triage: Prioritizing Findings

You have [N] findings. Let's prioritize each.

Priority levels:
- HIGH — Blocks proceeding. Must address before implementation.
- MEDIUM — Should fix. Address if time permits.
- LOW — Nice to have. Document for future.
```

**For each finding:**

```
Finding [ID]: "[description]"
Confidence: [level]
Evidence: [citation]

Priority? [High / Medium / Low]
Brief rationale: ___
```

**After all prioritized:**

```
Triage Summary

- High: [N] findings (must address)
- Medium: [N] findings (should address)
- Low: [N] findings (defer)

Which findings will you address this cycle?
[Default: All High, optionally include Medium]
```

**After Triage:**
1. Update `state.findings[].priority`
2. Add history event: `triage_complete` with counts
3. If findings to address → Proceed to Design Handoff
4. If no findings → Skip to Ship decision