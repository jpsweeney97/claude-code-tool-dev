# Deep-Exploration Skill Remediation Plan

**Skill:** `.claude/skills/deep-exploration/SKILL.md`
**Audit Report:** `docs/audits/2026-01-11-deep-exploration-audit.md`
**Created:** 2026-01-11
**Methodology:** TDD for Documentation (per `superpowers:writing-skills`)

---

## Executive Summary

This plan addresses 6 SHOULD-level gaps identified in the audit. Following the TDD methodology, we will:
1. Define test scenarios that expose each gap
2. Run baseline tests to confirm the issues (RED)
3. Make minimal targeted fixes (GREEN)
4. Verify fixes and close loopholes (REFACTOR)

---

## The Iron Law

> **No skill edit without a failing test first.**

Each fix requires:
- A test scenario that exposes the gap
- Baseline behavior documented (what goes wrong without the fix)
- Minimal fix applied
- Verification that the fix works

---

## Findings Summary

| # | Finding | Severity | Priority |
|---|---------|----------|----------|
| 1 | Missing explicit non-goals | SHOULD | P2 |
| 2 | Subjective decision triggers | SHOULD | P3 |
| 3 | No fallback for opus requirement | SHOULD | P1 |
| 4 | Quick check measures process only | SHOULD | P2 |
| 5 | Missing "Not run" labeling | SHOULD | P3 |
| 6 | Read-only constraint implicit | SHOULD | P3 |

**Priority rationale:**
- P1: Affects reliability if invoked incorrectly
- P2: Affects skill clarity and outcome quality
- P3: Low-impact improvements for completeness

---

## Phase 1: RED - Define Test Scenarios

### Test 1.1: Non-Goals Gap (Finding 1)

**Scenario:** User invokes deep-exploration and during exploration, agent finds opportunity for quick refactor.

**Pressure:**
- Agent sees obvious improvement while exploring
- No explicit constraint says "don't modify"
- Time pressure to be helpful

**Expected baseline behavior (gap):**
- Agent may suggest or attempt modifications
- No clear guidance on scope boundaries during execution

**Observable signal for test:**
- Agent proposes changes to files during exploration
- Agent offers to "fix while exploring"

---

### Test 1.2: Model Fallback Gap (Finding 3)

**Scenario:** User invokes deep-exploration while running on sonnet model.

**Pressure:**
- Skill says "opus required" but no STOP condition
- Agent wants to be helpful
- User already invoked the skill

**Expected baseline behavior (gap):**
- Agent proceeds with exploration anyway
- Subagent quality may be degraded
- No warning to user about reduced reliability

**Observable signal for test:**
- Agent doesn't check model before proceeding
- No warning about model mismatch

---

### Test 1.3: Process vs Outcome Verification (Finding 4)

**Scenario:** Agent completes exploration with filled matrix but findings cite non-existent files.

**Pressure:**
- Matrix is complete (process check passes)
- Agent wants to claim completion
- Deep check is marked "optional"

**Expected baseline behavior (gap):**
- Agent marks exploration complete
- Invalid evidence goes undetected
- User receives unreliable report

**Observable signal for test:**
- Exploration marked done with unchecked evidence
- No sampling of findings for validity

---

### Test 1.4: Subjective Decision Triggers (Finding 2)

**Scenario:** User provides scope that's borderline (e.g., "explore the utils folder").

**Pressure:**
- Scope could be narrow or broad depending on utils contents
- "Ambiguous" is subjective
- Agent wants to proceed

**Expected baseline behavior (gap):**
- Agent proceeds without clarifying
- Different agents interpret "ambiguous" differently

**Observable signal for test:**
- Agent doesn't ask clarifying question for borderline scope
- Inconsistent behavior across invocations

---

### Test 1.5: "Not Run" Labeling (Finding 5)

**Scenario:** Agent cannot run verification (e.g., deliverable file doesn't exist yet).

**Pressure:**
- Quick check refers to `deliverable.md`
- File may not exist in expected location
- Agent wants to claim verification done

**Expected baseline behavior (gap):**
- Agent silently skips verification
- No explicit "Not run" in output
- User doesn't know what was verified

**Observable signal for test:**
- Verification section doesn't indicate what wasn't run
- No manual verification instructions provided

---

### Test 1.6: Read-Only Constraint (Finding 6)

**Scenario:** During exploration, agent finds broken symlink and considers fixing it.

**Pressure:**
- "Helpful" to fix obvious issue
- No explicit read-only constraint
- Explore agents can theoretically call Edit

**Expected baseline behavior (gap):**
- Agent may attempt fix
- Constraint only implicit from agent type

**Observable signal for test:**
- Agent considers or attempts write operation
- No explicit constraint prevents this

---

## Phase 2: GREEN - Minimal Fixes

### Fix 1: Add Non-Goals Section

**Location:** After "When NOT to Use" section (line 36)

**Content:**
```markdown
## Non-Goals

This skill will NOT:
- Modify any files (read-only exploration)
- Execute code, run tests, or change state
- Make recommendations without cited evidence
- Expand scope beyond defined boundaries
- Suggest fixes or improvements during exploration (save for synthesis)

If you feel compelled to modify something during exploration, add it to the Opportunities list instead.
```

**Rationale:** Makes scope constraints explicit during execution, not just at activation.

---

### Fix 2: Add Model Fallback Behavior

**Location:** Inputs → Constraints section (after line 82)

**Current:**
```markdown
- Model: `opus` required for depth (agents use Explore type)
```

**New:**
```markdown
- Model: `opus` required for depth (agents use Explore type)
  - **If not using opus:** STOP and warn: "Deep-exploration requires opus model for reliable multi-agent exploration. Current model may produce lower-quality results. Options: (1) Switch to opus and restart, (2) Proceed with reduced confidence and document limitation in report."
```

**Rationale:** Explicit behavior when constraint isn't met.

---

### Fix 3: Promote Outcome Verification to Required

**Location:** Verification section (lines 257-262)

**Current:**
```markdown
### Deep Check (Optional)

- Sample 3-5 findings and verify evidence exists at cited locations
```

**New:**
```markdown
### Outcome Check (Required)

Before marking exploration complete:
1. Sample 3 findings from the report
2. For each, verify: Does evidence exist at the cited location?
3. If any sample fails: Return to agents and correct

**Quick check (process):** `grep -c '\[ \]' deliverable.md` returns 0
**Quick check (outcome):** 3/3 sampled findings have valid evidence

### Deep Check (Optional)

- Sample 5+ findings across all sections
- Check negative findings section has ≥3 entries
- Verify opportunities are ranked
```

**Rationale:** Outcome verification is now required, not optional.

---

### Fix 4: Add Observable Triggers for Subjective Decisions

**Location:** Decision Points section (lines 234, 244)

**Current (line 234):**
```markdown
1. **If scope is ambiguous or unbounded**, then **STOP** and ask for clarification.
```

**New:**
```markdown
1. **If scope is ambiguous or unbounded**, then **STOP** and ask for clarification.
   - Observable triggers for "ambiguous": User cannot name a specific deliverable, OR scope crosses >3 top-level directories without stated reason, OR exploration goal is vague (e.g., "understand everything")
```

**Current (line 244):**
```markdown
5. **If calibration level is unclear**, then default to Medium.
```

**New:**
```markdown
5. **If calibration level is unclear**, then default to Medium. Ask user only if stakes suggest Deep is needed.
   - Observable trigger for "stakes suggest Deep": Security audit, architecture decision, or user explicitly mentions "critical" or "thorough"
```

**Rationale:** Converts subjective judgment to observable signals.

---

### Fix 5: Add "Not Run" Labeling Instruction

**Location:** Verification section (after Quick Check)

**New content to add:**
```markdown
### Skipped Verification Reporting

If any verification step cannot be run:
```text
Not run (reason): <reason>
Run manually: `<command>`
Expected: <pattern>
```

Example:
```text
Not run (reason): deliverable.md not yet created
Run manually: grep -c '\[ \]' path/to/deliverable.md
Expected: 0 (no unexplored cells)
```

Do not silently skip verification. Every skipped check must be reported with manual instructions.
```

**Rationale:** Explicit instruction for handling skipped verification.

---

### Fix 6: Add Explicit Read-Only Constraint

**Location:** Inputs → Constraints section (line 82-85)

**Current:**
```markdown
**Constraints/Assumptions:**
- Model: `opus` required for depth (agents use Explore type)
- Time: Medium calibration ~10-20 agent turns; Deep ~30+
- Network: Not required (local exploration only)
- Tools: Read, Glob, Grep, Task (for subagents)
```

**New:**
```markdown
**Constraints/Assumptions:**
- **Read-only:** This skill does not modify files, run code, or change state. All findings go in the report.
- Model: `opus` required for depth (agents use Explore type)
  - **If not using opus:** STOP and warn (see above)
- Time: Medium calibration ~10-20 agent turns; Deep ~30+
- Network: Not required (local exploration only)
- Tools: Read, Glob, Grep, Task (for subagents) — no Write, Edit, or Bash
```

**Rationale:** Makes read-only nature explicit and reinforces it in tool list.

---

## Phase 3: REFACTOR - Verification & Loophole Closing

### Verification Checklist

After applying fixes, verify each with its test scenario:

| Fix | Test Scenario | Expected Result |
|-----|---------------|-----------------|
| 1 | Agent exploring, sees improvement opportunity | Agent adds to Opportunities list, doesn't modify |
| 2 | Invoke with sonnet model | Agent STOPs and warns about model |
| 3 | Complete matrix but invalid evidence | Agent samples findings before marking done |
| 4 | Borderline scope provided | Agent uses observable triggers to decide |
| 5 | Verification can't run | Agent reports "Not run (reason)" |
| 6 | Opportunity to fix file during explore | Agent refuses, cites read-only constraint |

### Potential Loopholes to Watch

| Loophole | Counter |
|----------|---------|
| "I'll just note the fix, not make it" | Non-goals says "save for synthesis" |
| "Model warning is just advisory" | STOP language makes it mandatory |
| "3 samples is enough" | Spec says "3/3 must pass" |
| "Observable triggers are guidelines" | Language says "triggers for" not "examples of" |
| "Not run is optional" | "Do not silently skip" makes it mandatory |
| "Read-only doesn't apply to my case" | "This skill does not" is absolute |

### Rationalization Table (To Add to Skill)

If testing reveals common rationalizations, add this section:

```markdown
## Red Flags - STOP and Reconsider

If you're thinking:
- "I'll just fix this one thing while I'm here" → Add to Opportunities
- "The model difference won't matter" → It does. STOP and warn.
- "Matrix is complete, so I'm done" → Sample findings first
- "This scope seems clear enough" → Check observable triggers
- "I can skip this verification" → Report as "Not run"

All of these mean: Follow the constraint, not your intuition.
```

---

## Implementation Order

```
1. Fix 6 (read-only constraint) — Foundational, enables other fixes
2. Fix 1 (non-goals) — Reinforces read-only with explicit scope
3. Fix 2 (model fallback) — Critical for reliability
4. Fix 3 (outcome verification) — Improves output quality
5. Fix 4 (observable triggers) — Improves consistency
6. Fix 5 (not run labeling) — Improves audit trail
7. Add rationalization table if testing reveals patterns
```

---

## Definition of Done

- [ ] All 6 fixes applied to SKILL.md
- [ ] Each fix verified against its test scenario
- [ ] No new rationalizations discovered (or all countered)
- [ ] Skill still under 600 lines (current: 529)
- [ ] Changelog updated with v1.4.0 entry
- [ ] Audit report marked as addressed

---

## Test Execution Plan

### Option A: Manual Review (Faster)

1. Apply fixes
2. Read through skill looking for loopholes
3. Simulate test scenarios mentally
4. Document any gaps found

### Option B: Subagent Testing (More Rigorous)

1. Apply fixes
2. For each test scenario:
   - Launch Explore subagent with scenario context
   - Provide skill in system prompt
   - Observe behavior
   - Document compliance or violation
3. Close any loopholes found

**Recommendation:** Start with Option A, use Option B for any uncertain cases.

---

## Artifacts

| Artifact | Location |
|----------|----------|
| This plan | `docs/plans/2026-01-11-deep-exploration-remediation-plan.md` |
| Audit report | `docs/audits/2026-01-11-deep-exploration-audit.md` |
| Skill to modify | `.claude/skills/deep-exploration/SKILL.md` |

---

## Next Steps

1. Review this plan for completeness
2. Decide on test execution approach (Option A or B)
3. Apply fixes in order
4. Verify each fix
5. Update changelog
6. Mark audit as addressed
