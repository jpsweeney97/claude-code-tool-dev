# Design Context: reviewing-designs

**Type:** Process/Workflow
**Risk:** Low (read-only analysis; doesn't modify files)

## Problem Statement

The existing `gap-analysis` and `validating-designs` skills were created before current best practices were established and before the Framework for Thoroughness was polished. They had several issues:

- **gap-analysis:** Fixed 7-pass architecture with no iteration, no Entry/Exit gates, no Evidence/Confidence tracking, no convergence detection
- **validating-designs:** Two-phase approach without framework integration, different severity terminology (Blocking/Significant/Minor vs P0/P1/P2)
- Both skills had overlapping concerns but inconsistent approaches

## Success Criteria

A unified skill that:
1. Integrates fully with Framework for Thoroughness (Entry Gate, iterative loop, Yield%, Exit Gate)
2. Covers both source coverage ("did we capture everything?") and implementation readiness ("can we build from this?")
3. Uses framework-native vocabulary (P0/P1/P2, Evidence levels, Confidence levels)
4. Iterates until convergence (Yield% below threshold)
5. Includes both systematic review and adversarial challenge
6. Prevents rationalization through bright-line rules and observable checkpoints

## Compliance Risks

Identified risks and mitigations:

| Risk | Mitigation |
|------|------------|
| "Documents are simple, don't need all passes" | Mandatory Entry Gate; Pass 1 always 100% yield |
| "Already see the main gaps" | Disconfirmation required for P0s; adversarial pass mandatory |
| "Taking too long, probably converged" | Yield% is calculated, not felt; observable iteration log |
| "No new dimensions to discover" | "Apply ≥3 DISCOVER techniques" — bright-line rule |
| Marking dimensions N/A to skip work | Mandatory categories (D12-D19); skeptical reviewer test; self-check |

## Rejected Approaches

| Approach | Why Rejected |
|----------|--------------|
| Keep skills separate with handoff guidance | Overlapping concerns led to inconsistency; unified skill is cleaner |
| Vocabulary-only framework integration | User wanted full protocol including iterative loop |
| Built-in remediation loop | Remediation is a different activity; mixing blurs scope |
| Sign-off ritual | Skill's scope is reviewing and reporting; workflow control is user's domain |
| Explicit handoffs to other skills | Passive approach chosen; user owns workflow decisions |

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Merge gap-analysis + validating-designs | Both check designs; many dimensions overlap; unified approach is consistent |
| Name: `reviewing-designs` | Broad enough to encompass both source comparison and implementation readiness |
| Full framework protocol | User explicitly wanted iterative loop + tracking infrastructure |
| 19 seed dimensions across 5 categories | Covers both original skills' concerns without redundancy |
| Document Quality always mandatory | Most commonly skipped but catches real implementation problems |
| Framework disconfirmation in VERIFY + dedicated adversarial pass | Finding-level vs design-level challenges are complementary |
| Remediation outside scope | Clean separation: skill reviews, user fixes, re-run if needed |
| Default Rigorous thoroughness | Most design reviews warrant moderate rigor; user can override |
| Artifact/chat output split | Prevents overwhelming chat with full report; P0s are unmissable |

## Dimensions Added During Design

The Document Quality dimensions (D13-D19) were added during brainstorming based on user input:

| Dimension | Question | Catches |
|-----------|----------|---------|
| D13: Implicit concepts | Are all terms defined? | Undefined jargon, assumed knowledge |
| D14: Precision | Is language precise? | Vague wording, loopholes, wiggle room |
| D15: Examples | Is abstract guidance illustrated? | Theory without concrete application |
| D16: Internal consistency | Do parts agree? | Contradictions between sections |
| D17: Redundancy | Is anything said twice differently? | Duplication that may drift |
| D18: Verifiability | Can compliance be verified? | Unverifiable requirements |
| D19: Actionability | Is it clear what to do? | Ambiguous instructions |

Check order: D13-D15 (surface) → D16-D17 (cross-section) → D18-D19 (holistic)

## Migration Notes

This skill replaces:
- `.claude/skills/gap-analysis/SKILL.md`
- `.claude/skills/validating-designs/SKILL.md`

After testing confirms the new skill works correctly:
1. Delete or archive the old skill directories
2. Update any references in CLAUDE.md or other documentation
3. Update the Skill tool's available skills list if manually maintained
