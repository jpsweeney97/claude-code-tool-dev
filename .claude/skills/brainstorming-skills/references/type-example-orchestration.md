# Type Example: Orchestration Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Orchestration.

## Core Question

**Did Claude coordinate correctly?**

Orchestration skills coordinate multiple sub-skills or workflows. The failure mode is invoking wrong sub-skills, wrong order, or broken handoffs between phases.

## Type Indicators

Your skill is Orchestration if it:
- Invokes other skills via the Skill tool
- Coordinates multiple phases or sub-workflows
- Produces artifacts that feed into subsequent phases
- Acts as a "meta-skill" that sequences other skills

## The Coordination Challenge

Orchestration skills must verify:
1. **Correct sub-skill selection** — Did Claude invoke the right skills?
2. **Correct ordering** — Were phases executed in the right sequence?
3. **Artifact handoff** — Did outputs from one phase flow correctly to the next?
4. **Checkpoint handling** — Did Claude pause at required decision points?

## Section Guidance

### Process Section

**Use phase structure with explicit handoffs:**

**Example (skill development workflow):**

```markdown
## Process

**Phase 1: Brainstorm** (uses: brainstorming-skills)
- Invoke brainstorming-skills for the skill idea
- Outputs: Design context document with type, risk level, test scenarios
- Checkpoint: Review design context with user before proceeding

**Phase 2: Write** (uses: writing-skills)
- Invoke writing-skills with design context as input
- Outputs: Draft SKILL.md following template
- Checkpoint: Review draft with user before testing

**Phase 3: Test** (uses: skill-testing)
- Invoke skill-testing with draft SKILL.md and test scenarios from Phase 1
- Outputs: Test results, identified issues
- Checkpoint: Review issues with user; return to Phase 2 if critical issues

**Phase 4: Finalize** (uses: skill-finalize)
- Invoke skill-finalize for final validation and promotion
- Outputs: Finalized skill, promotion confirmation

**Phase Transitions:**
- Phase 1 → Phase 2: Only after user approves design context
- Phase 2 → Phase 3: Only after user approves draft
- Phase 3 → Phase 4: Only if tests pass or issues are acceptable
- Phase 3 → Phase 2: If tests reveal critical issues
```

**Anti-pattern:** Phases without explicit outputs and checkpoints.

### Decision Points Section

Focus on **phase transitions and sub-skill selection**:

**Example:**

```markdown
## Decision Points

**Sub-skill selection:**
- If skill type is unclear → Stay in Phase 1. Brainstorming-skills must determine type before proceeding.
- If multiple skill types apply → Brainstorm for primary type first. Secondary aspects can be added in Phase 2.

**Phase transitions:**
- If user wants to skip Phase 1 → Warn that skipping brainstorming leads to underdeveloped skills. Proceed only with explicit consent.
- If Phase 3 tests fail → Return to Phase 2. Don't proceed to finalization with failing tests.
- If user wants to skip testing → Strongly discourage. Untested skills fail in production. Proceed only with explicit consent and documented risk.

**Artifact completeness:**
- If Phase 1 produces incomplete design context → Don't proceed. Return to brainstorming to fill gaps.
- If Phase 2 SKILL.md is missing required sections → Don't proceed to testing. Incomplete skills can't be properly tested.

**Checkpoints:**
- All checkpoints require explicit user approval before proceeding
- "Looks good" is sufficient approval
- Silence or ambiguous response → Ask for explicit confirmation
```

### Examples Section

Show **coordination comparison**:
- Before: Wrong order, missing handoffs, skipped checkpoints
- After: Correct phase sequence with proper handoffs

**Example:**

```markdown
## Examples

**Scenario:** User asks to create a new skill for handling API rate limits

**Before** (without orchestration):
Claude immediately starts writing SKILL.md:
- Skips brainstorming entirely
- Doesn't determine skill type
- Doesn't identify test scenarios
- Produces a skill that looks complete but hasn't been validated

Problems:
- No design context → skill may be wrong type for the problem
- No test scenarios → skill will be tested ad-hoc or not at all
- No checkpoints → user has no opportunity to course-correct

**After** (with orchestration):

**Phase 1:** Invokes brainstorming-skills
"Let me start by brainstorming this skill. We need to understand what type of skill this is and identify test scenarios."

Output: Design context document
- Type: Recovery/Resilience (handles rate limit failures)
- Risk: Medium (incorrect handling could cause cascading failures)
- Test scenarios: 429 response, Retry-After header parsing, backoff strategy

Checkpoint: "Here's the design context. Does this capture what you're looking for?"

User: "Yes, looks good."

**Phase 2:** Invokes writing-skills with design context
"Now I'll draft the SKILL.md based on the design context."

Output: Draft SKILL.md with Recovery/Resilience structure

Checkpoint: "Here's the draft. Any changes before we test?"

User: "Add guidance for handling different rate limit windows."

Claude: Updates draft, presents again for approval.

**Phase 3:** Invokes skill-testing with draft and scenarios
"Now let's test the skill against our scenarios."

Output: Test results showing one scenario failing (Retry-After with very long delay)

Checkpoint: "Tests found an issue with long Retry-After values. Should we fix this before finalizing?"

User: "Yes, fix it."

Returns to Phase 2, updates skill, re-tests.

**Phase 4:** Invokes skill-finalize
"Tests passing. Finalizing the skill."

Output: Finalized skill promoted to production location
```

### Anti-Patterns Section

Focus on **orchestration failures**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Skipping phases because "I know what's needed"
**Why it fails:** Each phase produces artifacts the next phase needs. Skipping brainstorming means no design context for writing. Skipping testing means shipping untested skills.
**Fix:** All phases are mandatory. Shortcuts create quality debt.

**Pattern:** Not waiting for checkpoint approval
**Why it fails:** User can't course-correct if you don't pause. You might build extensively on a flawed foundation.
**Fix:** Checkpoints require explicit user response. Ask if unclear.

**Pattern:** Invoking wrong sub-skill for the phase
**Why it fails:** Sub-skills have specific purposes. Using writing-skills for brainstorming produces wrong outputs.
**Fix:** Each phase specifies exactly which sub-skill to use. Follow the mapping.

**Pattern:** Broken artifact handoff
**Why it fails:** Phase 2 needs Phase 1's output. If you don't pass the design context to writing-skills, the draft won't reflect the brainstorming.
**Fix:** Explicitly reference prior phase outputs when invoking next phase.

**Pattern:** Proceeding despite failed tests
**Why it fails:** Tests exist to catch problems. Ignoring them ships known issues.
**Fix:** Failed tests → return to earlier phase. Only proceed to finalization with passing tests or explicit user acceptance of known issues.
```

### Troubleshooting Section

Address **orchestration failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude invoked a sub-skill but it didn't have needed context
**Cause:** Artifact from previous phase wasn't passed to sub-skill
**Next steps:** Re-invoke sub-skill with explicit reference to prior phase output.

**Symptom:** User is confused about where we are in the process
**Cause:** Phase transitions not communicated clearly
**Next steps:** State current phase explicitly: "We're now in Phase 2 (writing). Phase 1 (brainstorming) is complete."

**Symptom:** Final skill is missing elements from brainstorming
**Cause:** Design context wasn't properly incorporated in writing phase
**Next steps:** Compare final skill against design context. Fill gaps, return to testing.

**Symptom:** User wants to restart from an earlier phase
**Cause:** Later phase revealed issues with earlier phase output
**Next steps:** This is fine — orchestration supports backtracking. Return to specified phase, preserve what's still valid.
```

## Testing This Type

Orchestration skills need **phase transition testing**:

1. **Sequence test:** Does Claude invoke sub-skills in correct order?
2. **Handoff test:** Do artifacts flow correctly between phases?
3. **Checkpoint test:** Does Claude wait for user approval at checkpoints?
4. **Pressure test:** If urged to skip phases, does Claude resist appropriately?
5. **Backtrack test:** Can Claude return to earlier phases cleanly?

See `type-specific-testing.md` → Type 7: Orchestration Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Implicit phase transitions | User doesn't know where we are | State phase explicitly at each transition |
| Missing checkpoints | No opportunity to course-correct | Every phase ends with user approval checkpoint |
| Artifacts not passed | Sub-skills lack needed context | Explicitly reference prior phase outputs |
| No backtrack path | Can't fix issues found in later phases | Design phases to support returning to earlier phases |
