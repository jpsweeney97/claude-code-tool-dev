---
name: validating-designs
description: Use when a design document exists and implementation hasn't started, after brainstorming completes, or when past designs have led to implementation surprises, missing pieces, or ambiguous specs
---

# Validating Designs

## Triggers

- "validate this design"
- "check the design before we implement"
- "is this design ready?"
- "stress-test the design"
- "review the design document"

## When to Use

- Design document exists but implementation hasn't started
- After brainstorming skill completes
- Past designs have led to implementation surprises
- User wants confidence before committing to implementation

## When NOT to Use

- No design document exists yet (use brainstorming first)
- Implementation is already complete
- Quick prototype/spike where rigor isn't needed
- Design is for documentation only, not implementation

## Inputs

**Required:**
- Design document (file path or inline content)

**Optional:**
- Specific concerns to focus on
- Prior context from brainstorming session

**Constraints:**
- Design must be readable text (markdown, plain text)

## Outputs

**Artifacts:**
- Updated design document with issues resolved
- Validation summary (issues found, resolutions, accepted risks)

**Definition of Done:**
- All 11 systematic dimensions checked
- All 9 adversarial lenses applied
- Zero blocking issues remain
- User has explicitly signed off

## Procedure

### Phase 1: Systematic Validation

Work through each dimension. Document findings as pass/issue for each check.

**1. Cross-validation:**
- [ ] Inputs mentioned in procedure ⊆ Inputs section
- [ ] Outputs mentioned in procedure ⊆ Outputs section
- [ ] Terminology consistent throughout
- [ ] Counts match (e.g., "7 categories" → verify actually 7)

**2. Clarity:**
- [ ] Could be implemented without asking clarifying questions
- [ ] Complex concepts have examples
- [ ] No undefined terms or acronyms without explanation
- [ ] No vague instructions ("handle appropriately", "as needed")
- [ ] No "TBD", "TODO", or placeholder sections

**3. Completeness:**
- [ ] Has clear purpose/goal statement
- [ ] Lists components or modules involved
- [ ] Describes data flow between components
- [ ] Addresses error handling and failure modes
- [ ] Includes testing strategy or verification approach

**4. Architecture:**
- [ ] Simpler alternative was considered (or justified why not applicable)
- [ ] Trade-offs explicitly stated
- [ ] Consistent with existing codebase patterns (or explains deviation)
- [ ] No unnecessary abstraction layers

**5. Edge Cases:**
- [ ] Empty/null inputs handled
- [ ] Boundary conditions addressed
- [ ] Concurrent access considered (if applicable)
- [ ] Failure/retry behavior defined

**6. Testability:**
- [ ] Testing approach described
- [ ] Success criteria are verifiable
- [ ] Key behaviors are observable/measurable

**7. Feasibility:**
- [ ] All referenced dependencies exist
- [ ] No "assume X works" without justification
- [ ] Performance/scale claims have basis (benchmarks, estimates, precedent)

**8. Safety Defaults:**
- [ ] Default behavior when uncertain
- [ ] Escalation when risk detected
- [ ] Rollback/recovery path
- [ ] Guard against common failures

**9. Exit Criteria:**
- [ ] Explicit completion criteria
- [ ] Termination condition for loops/retries
- [ ] Quality bar defined (not just "finished")
- [ ] What prevents premature exit

**10. Decision Rules:**
- [ ] All branches specified
- [ ] Default case defined
- [ ] Ambiguous case handled
- [ ] Escalation path when stuck

**11. Procedural Completeness:**
- [ ] Precondition stated
- [ ] Action is executable (not vague)
- [ ] Postcondition/output defined
- [ ] Error handling specified

### Phase 2: Adversarial Review

Apply each lens with genuine adversarial intent. Try to break the design.

**1. Assumption Hunting**
- List every assumption the design makes (explicit and implicit)
- For each: What if this assumption is wrong?
- Flag unstated dependencies and environmental conditions

**2. Scale Stress**
- What breaks at 10x current expectations?
- What breaks at 100x?
- Where are the bottlenecks?
- What resources are bounded? What happens when limits hit?

**3. Competing Perspectives**
- Security: What attack vectors exist?
- Performance: Where will this be slow?
- Maintainability: What will be hard to change later?
- Operations: What will be hard to debug or monitor?

**4. Kill the Design**
- Find reasons this approach won't work
- What's the strongest argument against this design?
- If this fails in production, what will be the cause?
- Would you bet your job on this design?

**5. Pre-mortem**
- It's 6 months later. This failed catastrophically.
- Write the post-mortem: What went wrong?
- What warning signs were ignored?

**6. Steelman Alternatives**
- What approaches were rejected?
- Take them seriously: What would make them better than the chosen design?
- Is the rejection justified, or was it dismissed too quickly?

**7. Challenge the Framing**
- Is this the right problem to solve?
- Are we solving a symptom instead of the root cause?
- What if the premise is wrong?

**8. Hidden Complexity**
- Where is complexity being underestimated?
- What looks simple but isn't?
- Where are the dragons hiding?
- What will take 10x longer than expected?

**9. Motivated Reasoning Check**
- Where might this design be rationalizing a preferred approach?
- What would you do if forced to pick a completely different solution?
- Is there anchoring to an early idea that should be reconsidered?

### Phase 3: Validation Checkpoint

**Categorize all findings by severity:**
- **Blocking:** Cannot proceed until resolved
- **Significant:** Should fix before implementation
- **Minor:** Document but can proceed

**Produce Summary Report:**

Present a summary table showing all findings:

```markdown
## Summary

| Severity | Count |
|----------|-------|
| Blocking | N |
| Significant | N |
| Minor | N |

### Blocking Issues
| # | Finding | Source Dimensions |
|---|---------|-------------------|
| B1 | [description] | [which checks failed] |

### Significant Issues
| # | Finding | Source Dimensions |
|---|---------|-------------------|
| S1 | [description] | [which checks failed] |

### Minor Issues
| # | Finding | Source Dimensions |
|---|---------|-------------------|
| M1 | [description] | [which checks failed] |
```

**Remediation Loop:**
1. Present findings to user (blocking first)
2. Fix issues in design document
3. Re-validate affected dimensions (targeted, not full re-run)
4. Repeat until no blocking issues remain

**Sign-off Ritual:**
Before proceeding to implementation, user must explicitly confirm:
1. Remaining risks acknowledged
2. Scope confirmed ("this is what we're building")
3. Implementation approved

## Decision Points

**After Phase 1:**
- Blocking issues found → Cannot proceed to Phase 2 until resolved
- Only significant/minor → Proceed to Phase 2, carry issues forward

**After Phase 2:**
- Blocking issues → Add to remediation queue
- Design fundamentally flawed → Consider returning to brainstorming

**During Remediation:**
- Fix introduces new issues → Re-validate affected dimensions
- Remediation feels endless → Design may need fundamental rethinking

**At Sign-off:**
- User declines → Document concerns, return to relevant phase
- User accepts with caveats → Document accepted risks explicitly

## Verification

**Quick check:**
- [ ] Design document updated with fixes
- [ ] User said "proceed" or equivalent
- [ ] No blocking issues remain open
- [ ] Accepted risks documented

## Troubleshooting

**Symptom:** Too many issues, remediation feels endless
**Cause:** Design may need fundamental rethinking
**Next steps:** Return to brainstorming with findings as input

**Symptom:** User wants to skip phases
**Cause:** Time pressure or perceived overhead
**Next steps:** Skipped issues surface during implementation; offer to focus on blocking items only

**Symptom:** Adversarial review finds nothing
**Cause:** Either design is solid, or review wasn't genuinely adversarial
**Next steps:** Try harder to kill the design; apply pre-mortem seriously

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Skipping adversarial review because checklist passed | Both phases required — checklist finds gaps, adversarial finds weaknesses |
| Accepting blocking issues to "move faster" | They surface during implementation anyway |
| Validating after implementation started | Run before; post-implementation is different |
| Rubber-stamp sign-off | Present findings clearly; sign-off must be informed |
| Softball adversarial review | Genuinely try to break it; pre-mortem must feel uncomfortable |

## Extension Points

- Domain-specific checklists (security, performance, compliance)
- Integration with gap-analysis for cross-document validation
- Integration with writing-plans for implementation handoff
