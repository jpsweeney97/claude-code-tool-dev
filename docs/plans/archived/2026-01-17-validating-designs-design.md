# Validating Designs — Skill Design Document

## Overview

**Skill Name:** `validating-designs`

**Purpose:** A companion skill to `brainstorming` that validates and strengthens design documents before implementation begins. Catches issues that would otherwise surface during implementation when they're expensive to fix.

**Problem it solves:**
- Claude creates shallow or incomplete designs
- Designs seem fine at review time but reveal gaps during implementation
- Symptoms: missing pieces, ambiguous specs, wrong abstractions, shallow exploration

**Relationship to brainstorming:**
- Runs AFTER brainstorming produces a design document
- Brainstorming can auto-trigger this skill as a recommended next step
- Can also be invoked manually on any design document

**Scope:** All design documents, regardless of complexity.

---

## Skill Structure

### Frontmatter

```yaml
---
name: validating-designs
description: Use when a design document exists and implementation hasn't started, after brainstorming completes, or when past designs have led to implementation surprises, missing pieces, or ambiguous specs
---
```

### Triggers

- "validate this design"
- "check the design before we implement"
- "is this design ready?"
- "stress-test the design"
- "review the design document"

### When to Use

- Design document exists but implementation hasn't started
- After brainstorming skill completes
- Past designs have led to implementation surprises
- User wants confidence before committing to implementation

### When NOT to Use

- No design document exists yet (use brainstorming first)
- Implementation is already complete (too late)
- Quick prototype/spike where rigor isn't needed
- Design is for documentation only, not implementation

### Inputs

**Required:**
- Design document (file path or inline content)

**Optional:**
- Specific concerns to focus on
- Prior context from brainstorming session

**Constraints:**
- Design must be readable text (markdown, plain text)
- No network access required

### Outputs

**Artifacts:**
- Updated design document with issues resolved
- Validation report (issues found, resolutions, accepted risks)

**Definition of Done:**
- All 11 systematic dimensions checked
- All 9 adversarial lenses applied
- Zero blocking issues remain
- User has explicitly signed off

---

## Phase 1: Systematic Validation

**Purpose:** Verify the design document is internally consistent, clear, and complete before adversarial review.

### 11-Dimension Checklist

**Cross-validation:**
- Inputs in procedure ⊆ Inputs section
- Outputs in procedure ⊆ Outputs section
- Terminology consistent throughout
- Counts match (e.g., "7 categories" → actually 7)

**Clarity:**
- Could be implemented without asking clarifying questions
- Complex concepts have examples
- No undefined terms or acronyms without explanation
- No vague instructions that could be interpreted multiple ways
- No "TBD", "TODO", or placeholder sections

**Completeness:**
- Has clear purpose/goal statement
- Lists components or modules involved
- Describes data flow between components
- Addresses error handling and failure modes
- Includes testing strategy or verification approach

**Architecture:**
- Simpler alternative was considered (or justified why not applicable)
- Trade-offs explicitly stated
- Consistent with existing codebase patterns (or explains deviation)
- No unnecessary abstraction layers

**Edge Cases:**
- Empty/null inputs handled
- Boundary conditions addressed
- Concurrent access considered (if applicable)
- Failure/retry behavior defined

**Testability:**
- Testing approach described
- Success criteria are verifiable
- Key behaviors are observable/measurable

**Feasibility:**
- All referenced dependencies exist
- No "assume X works" without justification
- Performance/scale claims have basis (benchmarks, estimates, precedent)

**Safety Defaults:**
- Default behavior when uncertain
- Escalation when risk detected
- Rollback/recovery path
- Guard against common failures

**Exit Criteria:**
- Explicit completion criteria
- Termination condition for loops
- Quality bar defined (not just "finished")
- What prevents premature exit

**Decision Rules:**
- All branches specified
- Default case defined
- Ambiguous case handled
- Escalation path when stuck

**Procedural Completeness:**
- Precondition stated
- Action is executable (not vague)
- Postcondition/output defined
- Error handling specified

### Phase 1 Process

1. Work through each dimension systematically
2. Document findings (pass/issue) for each check
3. Issues become inputs to Phase 3 remediation

---

## Phase 2: Adversarial Review

**Purpose:** Aggressively stress-test the design. The goal is to break it before implementation does.

### 9 Adversarial Lenses

| Lens | Attack Vector |
|------|---------------|
| **Assumption Hunting** | What is taken for granted? What if those assumptions are wrong? What unstated dependencies exist? |
| **Scale Stress** | What breaks at 10x? At 100x? Where are the bottlenecks? What happens when limits are hit? |
| **Competing Perspectives** | Security: attack vectors? Performance: where slow? Maintainability: what's hard to change? Operations: what's hard to debug? |
| **Kill the Design** | Find reasons this won't work. What's the strongest argument against it? If this fails, what's the cause? |
| **Pre-mortem** | It's 6 months later and this failed catastrophically. Write the post-mortem. What went wrong? |
| **Steelman Alternatives** | Take the rejected approaches seriously. What would make them better than the chosen design? |
| **Challenge the Framing** | Is this the right problem to solve? Are we solving a symptom instead of the root cause? |
| **Hidden Complexity** | Where is complexity being underestimated? What looks simple but isn't? Where are the dragons? |
| **Motivated Reasoning Check** | Where might this design be rationalizing a preferred approach? What would you do if forced to pick a different solution? |

### Phase 2 Process

1. Apply each lens with genuine adversarial intent — try to break things
2. Document findings with severity:
   - **Blocking:** Halts progress until resolved
   - **Significant:** Goes to Phase 3 remediation
   - **Minor:** Documented but may proceed

---

## Phase 3: Validation Checkpoint

**Purpose:** Ensure all issues are resolved and get explicit user approval before implementation begins.

### Remediation Loop

```
Issues from Phase 1 & 2
         ↓
Present findings to user
(grouped by severity: blocking first)
         ↓
Fix issues in design document
         ↓
Re-validate affected dimensions
(targeted checks, not full re-run)
         ↓
    Issues remain?
     ↓         ↓
    yes        no
     ↓         ↓
  (loop)   Proceed to Sign-off
```

### Sign-off Ritual

Before implementation begins, user must explicitly confirm:

1. **Acknowledge remaining risks** — Any unresolved minor issues or accepted trade-offs
2. **Confirm scope** — "This is what we're building"
3. **Approve implementation** — Explicit "proceed" from user

### Phase 3 Outputs

- Updated design document with issues resolved
- Sign-off record (what was approved, what risks were accepted)
- Clear handoff to implementation (`writing-plans` or direct implementation)

---

## Decision Points

**After Phase 1:**
- If blocking issues found → Cannot proceed to Phase 2 until resolved
- If only significant/minor issues → Proceed to Phase 2, issues carry forward

**After Phase 2:**
- If blocking issues found → Add to remediation queue
- If design fundamentally flawed → Consider returning to brainstorming

**During Remediation:**
- If fix introduces new issues → Re-validate affected dimensions
- If remediation feels endless → Design may need fundamental rethinking

**At Sign-off:**
- If user declines → Document concerns, return to relevant phase
- If user accepts with caveats → Document accepted risks explicitly

---

## Verification

**Quick check:**
- Design document has been updated with fixes
- User has said "proceed" or equivalent approval
- No blocking issues remain open

---

## Troubleshooting

**Symptom:** Too many issues found, remediation feels endless
**Cause:** Design may need fundamental rethinking, not incremental fixes
**Next steps:** Return to brainstorming with findings as input

**Symptom:** User wants to skip phases to "move faster"
**Cause:** Time pressure or perceived overhead
**Next steps:** Explain that skipped issues surface during implementation; offer to focus on highest-severity items

**Symptom:** Adversarial review finds nothing
**Cause:** Either design is solid, or review wasn't genuinely adversarial
**Next steps:** Try harder to kill the design; if still nothing, proceed with confidence

---

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Skipping adversarial review because "checklist passed" | Both phases required — checklist finds gaps, adversarial finds weaknesses |
| Accepting blocking issues to "move faster" | Blocking issues will surface during implementation anyway |
| Validating after implementation started | Run before implementation; post-implementation is a different concern |
| Treating minor issues as blocking | Calibrate severity correctly; minor issues don't halt progress |
| Rubber-stamp sign-off without reading findings | Sign-off must be informed; present findings clearly |

---

## Extension Points

- **Domain-specific checklists:** Security-focused, performance-focused, or compliance-focused variants
- **Integration with gap-analysis:** Feed validated design into cross-document validation
- **Integration with writing-plans:** Hand off validated design to implementation planning
- **Severity customization:** Adjust what counts as blocking for different contexts

---

## Integration with Brainstorming

Update brainstorming's "After the Design" section to include:

```markdown
**Validation (recommended):**
- Before implementation, use validating-designs skill to stress-test the design
- Catches issues that would otherwise surface during implementation
```
