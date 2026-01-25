# Design Context: reviewing-documents

**Type:** Process/Workflow
**Risk:** Medium (writes/modifies files, bounded and reversible)

## Problem Statement

Hard to decide between `reviewing-designs` and `refining-specifications` skills due to significant overlap:

- Document Quality dimensions (D13-D19) in reviewing-designs are literally the same as the 7 lenses in refining-specifications
- Both skills address document clarity and completeness
- Decision friction: unclear when to use which skill

User typically wants:
- Fixes applied (not audit-only)
- Adversarial thinking included
- Source comparison when sources exist
- Implementation readiness checks when document will be built from

## Success Criteria

- Single skill handles both use cases (source comparison and standalone refinement)
- Always applies fixes (not audit-only)
- Uses Yield% convergence with stakes-based thresholds
- Includes adversarial pass
- User has confidence nothing major was missed
- Appropriate rigor for stakes level

## Compliance Risks

What would make an agent rationalize around this skill:

- **"Document is already good"** — rationalizes skipping entirely
- **"Just a minor update"** — exempts small changes that compound
- **Single-pass "looks good"** — declares done too early
- **Time pressure** — skips adversarial pass or Entry Gate
- **"Most dimensions don't apply"** — marks too many dimensions N/A

Mitigations built into skill:
- Document Quality (D13-D19) and Cross-validation (D12) cannot be skipped
- Pass 1 is always 100% yield — cannot exit after one pass
- Explicit iteration cap prevents endless loops
- Adversarial pass is mandatory before Exit Gate

## Rejected Approaches

- **Keep both skills separate:** User decision friction remains; overlap still exists
- **Audit-only mode:** User wants fixes applied, not just reported
- **Simpler "two consecutive clean passes" convergence:** User prefers calculated Yield% approach for rigor

## Design Decisions

- **Unified skill called "reviewing-documents":** General name covers specs, designs, frameworks
- **Always apply fixes:** Removes audit-only mode; user's stated preference
- **Preserve Yield% convergence:** More rigorous than "two clean passes"
- **Preserve adversarial pass:** User values design-level flaw detection
- **Conditional dimension categories:** Source Coverage only when sources exist; Implementation Readiness only when document will be built from
- **Document Quality always mandatory:** D13-D19 cannot be skipped regardless of context

## Skills to Retire

After validating reviewing-documents works:
- `.claude/skills/reviewing-designs/`
- `.claude/skills/refining-specifications/`
