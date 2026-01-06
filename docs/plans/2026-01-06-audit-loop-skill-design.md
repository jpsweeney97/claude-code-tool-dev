# Audit Loop Skill Design

**Date:** 2026-01-06
**Status:** Ready for implementation

## Overview

A skill for executing the Audit → Design Loop workflow pattern with guided prompts and state persistence. Combines orchestration (tracking loop state across sessions) with guidance (walking through Framework for Rigor interactively).

**References:**
- `~/.claude/references/audit-design-loop.md` — The workflow pattern
- `~/.claude/references/framework-for-rigor.md` — Audit methodology

## Goals

1. **Reduce friction** in applying Framework for Rigor (300+ lines → guided prompts)
2. **Prevent state loss** across sessions (cycle, phase, findings tracked)
3. **Enforce completeness** by prompting for each framework element
4. **Enable iteration** with clear Ship/Iterate decision points

## Non-Goals

- Automating audit findings (human judgment required)
- Replacing brainstorming skill (delegates design phase)
- Supporting parallel audits on same artifact

---

## Entry Point

**Invocation:** `/audit-loop <artifact-path>` or `/audit-loop`

**Behavior:**
1. If artifact path provided → check for existing `.audit.json`
   - State exists → "Found audit in progress. Resume or restart?"
   - No state → Begin new audit
2. If no path → ask "What artifact are you auditing?"

**Resume options:**
```
Found in-progress audit (Cycle 1, Phase 2: Execution)

[A] Resume — continue from Phase 2
[B] Restart — discard progress and begin fresh audit
```

---

## State Management

### State File Location

Artifact-adjacent with timestamp on completion:

```
# During audit
docs/plans/feature-x.audit.json              # Active state

# After Ship
docs/plans/feature-x.audit.2026-01-06.json   # Archived state
docs/plans/feature-x.audit-report.2026-01-06.md  # Final report
```

### State Schema

```json
{
  "version": "1.0",
  "artifact": "docs/plans/feature-x.md",
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
    "goal": "Validate feature-x design before implementation",
    "scope": ["architecture", "error handling", "data flow"],
    "excluded": ["performance optimization", "UI details"],
    "excluded_rationale": "Deferred to implementation phase",
    "assumptions": ["API contracts are stable", "Team has React experience"],
    "done_criteria": "No High-priority findings remain"
  },

  "findings": [
    {
      "id": "F1",
      "description": "No error recovery strategy specified",
      "confidence": "certain",
      "priority": "high",
      "evidence": "Lines 45-52 describe happy path only",
      "status": "open"
    },
    {
      "id": "F2",
      "description": "Assumes API always available",
      "confidence": "probable",
      "priority": "medium",
      "evidence": "No offline handling mentioned",
      "status": "addressed",
      "resolution": "Added retry logic in design cycle 1"
    }
  ],

  "verification": {
    "counter_conclusion": "Design is comprehensive for MVP scope",
    "limitations": ["Did not audit performance", "Security review deferred"]
  },

  "history": [
    { "timestamp": "...", "event": "audit_started", "calibration": "medium" },
    { "timestamp": "...", "event": "phase_1_complete" },
    { "timestamp": "...", "event": "findings_complete", "count": 4 },
    { "timestamp": "...", "event": "triage_complete", "high": 2, "medium": 1, "low": 1 },
    { "timestamp": "...", "event": "design_handoff", "findings": ["F1", "F2"] },
    { "timestamp": "...", "event": "verify_complete" }
  ]
}
```

### State Checkpoints

State saved automatically at:
- After stakes assessment (calibration determined)
- After Phase 1: Definition
- After Phase 2: Execution (findings captured)
- After Phase 3: Verification
- After Triage (priorities assigned)
- Before Design handoff
- After Verify phase
- On Ship (archived with timestamp)

---

## Workflow

### Stakes Assessment

Determines calibration level before Phase 1.

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

**Scoring:** 4-6 = Light | 7-9 = Medium | 10-12 = Deep

---

### Phase 1: Definition

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Goal | Brief | Full | Full |
| Scope | Key boundaries | Complete | Exhaustive + justified |
| Done criteria | Implicit OK | Explicit | Explicit + verified |
| Assumptions | Key only | All | All + tested |
| Simple path | Yes | Yes | Yes + documented |

**Prompts:**

```
Phase 1: Definition

1. AUDIT GOAL — What outcome do you want from this audit?
   (Not the artifact's purpose — YOUR investigation goal)
   Example: "Confidence the design is implementable without major rework"

2. SCOPE — What aspects will you examine?
   [A] Architecture & structure
   [B] Error handling & edge cases
   [C] Data flow & state
   [D] Dependencies & integrations
   [E] Security implications
   [F] Other: ___

   What are you EXCLUDING, and why?
   [Red flag check: Are excluded areas actually harder to audit?]

3. ASSUMPTIONS — What are you taking for granted?
   [Medium+: List all]
   [Deep: How would you test each?]

4. DONE CRITERIA — How will you know the audit is complete?
   [Light: Can be implicit]
   [Medium+: Must be explicit]

5. SIMPLE PATH — Is there an obvious conclusion already?
   If so, why isn't it sufficient?
   [Deep: Document this reasoning]
```

---

### Phase 2: Execution

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Evidence collected | Key sources | Multiple sources | Exhaustive |
| Evidence levels noted | — | Yes | Yes |
| Disconfirmation | Brief | Systematic | Adversarial |
| Negative findings | — | Documented | Documented |
| Coverage tracked | List | Matrix | Matrix + verified |
| Methodology recorded | Brief | Full | Timestamped |

**Prompts:**

```
Phase 2: Execution

For each scope area, we'll:
1. Collect evidence (cite specific lines/sections)
2. Note evidence level (Primary/Secondary/Tertiary)
3. Seek DISCONFIRMATION — what would prove this area is fine?
4. Document negatives — what did you look for but NOT find?

Coverage Matrix:
| Area | Examined | Evidence Level | Findings | Gaps |
|------|----------|----------------|----------|------|
| [scope item 1] | | | | |
| [scope item 2] | | | | |

[Medium+: Record methodology — what tools/process did you use?]

[Red flag check: Are you only finding confirming evidence?]
```

**Evidence Hierarchy:**
- **Primary:** Direct observation (read file, run code, see output)
- **Secondary:** Documentation (README says, comments state)
- **Tertiary:** Inference (pattern suggests, absence implies)

**Finding format:**
```
Finding [ID]: [description]
Evidence: [specific citation]
Evidence level: [Primary/Secondary/Tertiary]
Confidence: [Certain/Probable/Possible/Unknown]
```

---

### Phase 3: Verification

| Check | Light | Medium | Deep |
|-------|-------|--------|------|
| Coverage verified | Quick check | Full check | Independent check |
| Reasoning verified | Self-check | Self-check | Peer check |
| Limitations stated | Key | Full | Comprehensive |
| Counter-conclusion | — | Yes | Adversarial |
| Confidence labeled | Yes | Yes | Yes |

**Prompts:**

```
Phase 3: Verification

1. COVERAGE CHECK — Review matrix. Any gaps?
   [Deep: Independent verification]

2. REASONING CHECK — For each finding:
   Does evidence actually support this conclusion?
   [Deep: Peer review]

3. COUNTER-CONCLUSION — Best argument this artifact is FINE?
   [Light: Skip]
   [Medium: Yes]
   [Deep: Adversarial — steelman the opposite view]

4. CONFIDENCE LABELS — For each finding:
   Certain / Probable / Possible / Unknown

5. LIMITATIONS — What did this audit NOT examine?
   What should readers know about blind spots?
```

---

### Triage

After findings are captured, assign priorities.

```
Triage: Prioritizing Findings

You have [N] findings. Let's prioritize.

Priority levels:
- HIGH — Blocks proceeding. Must address before implementation.
- MEDIUM — Should fix. Address if time permits.
- LOW — Nice to have. Document for future.

[Present each finding]

Finding F1: "No error recovery strategy"
Confidence: Certain
Evidence: Lines 45-52 describe happy path only

Priority? [High / Medium / Low]
Brief rationale?

[After all prioritized]

Summary:
- High: [N] findings (must address)
- Medium: [N] findings (should address)
- Low: [N] findings (defer)

Which findings will you address this cycle?
[Default: All High, optionally Medium]
```

---

### Design Handoff

Delegates to `superpowers:brainstorming` with context.

**State before handoff:**
```json
{
  "phase": "verify",
  "pending_verification": ["F1", "F2"],
  "design_context": {
    "artifact": "docs/plans/feature-x.md",
    "findings_to_address": [
      { "id": "F1", "description": "No error recovery strategy" },
      { "id": "F2", "description": "Assumes API always available" }
    ]
  }
}
```

**Handoff prompt:**
```
Design Phase

Handing off to brainstorming skill.

Context being passed:
- ARTIFACT: docs/plans/feature-x.md
- AUDIT CYCLE: 1
- FINDINGS TO ADDRESS:
  F1: No error recovery strategy [High]
  F2: Assumes API always available [High]

Constraint: Design solutions that resolve these specific findings.

[Invoke superpowers:brainstorming]

After brainstorming completes, continue to Verify phase.
```

**After brainstorming:**
- Design doc written to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Continue to Verify phase

---

### Verify Phase

After design, verify findings were addressed.

```
Verify Phase

Design complete. Now verifying findings were addressed.

Reading design output: [path from brainstorming]

---

Finding F1: "No error recovery strategy"
Original evidence: Lines 45-52 describe happy path only

Scanning design doc for relevant sections...

Found in design doc (lines 23-31):
> "[quote from design]"

This appears to address F1.

Does this adequately resolve the finding?
[A] Yes — fully addressed
[B] Partially — some aspects missing
[C] No — not addressed
[D] Let me review the design doc first

[If B or C: What's missing?]

---

[Repeat for each finding]

---

New Gaps Check

The design introduced new elements. Quick review:
- Do any of these introduce new concerns?
- Anything feel underspecified?

[A] No new concerns
[B] Found new issue: [describe]

[If B: Add as new finding for next cycle]
```

**State update:**
- Update finding statuses (addressed/partial/open)
- Capture resolutions
- Add any new findings from design

---

### Iterate/Ship Decision

```
Iterate or Ship?

Cycle [N] complete.

Results:
- High findings: [X] addressed, [Y] remaining
- Medium findings: [X] addressed, [Y] remaining
- Low findings: [X] addressed, [Y] deferred

Exit criteria (calibration: [level]):
[✓/○] No High findings remain
[✓/○] No Medium findings remain (Deep only)

Options:
[A] Ship — Resolved findings meet exit criteria. Document remaining.
[B] Iterate — Start Cycle [N+1] to address remaining findings.
[C] Expand — Re-audit with new scope (design introduced concerns).

Recommendation based on calibration:
→ [recommendation with rationale]

Your choice?
```

**If Ship:**
1. Generate final report
2. Archive state file with timestamp
3. Mark audit complete

**If Iterate:**
1. Increment cycle
2. Return to Phase 2 (Definition already established)
3. Focus on remaining/new findings

**If Expand:**
1. Return to Phase 1 to redefine scope
2. Incorporate new concerns from design

---

## Final Report

Generated on Ship. Template:

```markdown
# Audit Report: [artifact name]

**Completed:** [date]
**Calibration:** [level] (score [N])
**Cycles:** [N]

## Summary

[1-2 sentence overview of audit outcome]

## Scope

**Examined:**
- [scope item 1]
- [scope item 2]

**Excluded:**
- [excluded item] — [rationale]

## Findings

| ID | Description | Priority | Status | Resolution |
|----|-------------|----------|--------|------------|
| F1 | ... | High | Addressed | ... |
| F2 | ... | Medium | Deferred | ... |

## Limitations

- [What this audit did NOT cover]
- [Blind spots readers should know about]

## Counter-Conclusion

[Best argument that the artifact was fine as-is]

## Design Artifacts

- [path to design doc from brainstorming]

## Audit Trail

- Cycle 1: [N] findings, [X] addressed
- Cycle 2: [N] findings, [X] addressed
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Artifact doesn't exist | "Artifact not found: [path]. Check the path and try again." |
| State file corrupted | "State file invalid. [A] Start fresh [B] Show raw state for recovery" |
| Brainstorming not available | Provide inline design guidance (simplified) |

---

## File Structure

```
.claude/skills/audit-loop/
├── SKILL.md                    # Main skill
└── templates/
    └── report.md               # Final report template
```

**SKILL.md estimated length:** ~400-500 lines

**Dependencies:**
- `superpowers:brainstorming` — Design phase delegation
- `~/.claude/references/framework-for-rigor.md` — Referenced but not required

---

## Future Considerations (v1.1+)

- **Export/import state** — Share audits across team
- **Audit templates** — Pre-configured scopes for common artifact types
- **Integration with deep-* skills** — Use deep-exploration for complex codebases
- **Metrics** — Track audit velocity, finding patterns over time
