# Type Example: Process/Workflow Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Process/Workflow.

## Core Question

**Did Claude follow the steps?**

Process/Workflow skills enforce a specific sequence. The failure mode is skipping steps, reordering steps, or taking shortcuts under pressure.

## Type Indicators

Your skill is Process/Workflow if it:
- Has numbered steps or phases that must happen in order
- Has compliance rules that could be violated
- Would fail if steps were skipped or reordered
- Says things like "first... then... finally..."

## Section Guidance

### Process Section

**Use numbered steps.** Order matters. Each step should be:
- Atomic (one action per step)
- Verifiable (you can tell if it happened)
- Sequential (depends on prior steps)

**Example (debugging methodology):**

```markdown
## Process

1. **Reproduce** — Confirm you can trigger the bug consistently
2. **Isolate** — Narrow down to the smallest failing case
3. **Hypothesize** — Form a specific, testable theory about the cause
4. **Test** — Verify the hypothesis with targeted investigation
5. **Fix** — Implement the minimal change that addresses root cause
6. **Verify** — Confirm the fix works and doesn't break other things
```

**Anti-pattern:** Vague steps like "Debug the issue" or "Fix the problem" — these aren't verifiable.

### Decision Points Section

Focus on **what happens when steps are challenged**:
- What if a step fails?
- What if there's pressure to skip?
- What if earlier steps invalidate later ones?

**Example:**

```markdown
## Decision Points

**Step fails:**
- If Reproduce fails → Stop. You can't debug what you can't see. Ask for more information.
- If Hypothesize produces no theory → Return to Isolate. The scope isn't narrow enough.

**Pressure to skip:**
- If urged to "just fix it" → Explain that skipping Isolate/Hypothesize leads to wrong fixes. Cite past failures.
- If "we know what's wrong" → Still verify with Test step. Confidence isn't proof.

**New information:**
- If Fix reveals the hypothesis was wrong → Return to Hypothesize, don't patch over.
```

### Examples Section

Show **step completion comparison**:
- Before: Steps skipped or reordered
- After: All steps completed in order

**Example:**

```markdown
## Examples

**Scenario:** Payment processing fails intermittently. Error: "Transaction timeout."

**Before** (without skill):
Claude sees the error, guesses it's a database connection issue, and immediately suggests adding retry logic to the payment handler. The actual cause (a downstream service rate limit) is never identified. The retry logic makes the rate limiting worse.

**After** (with skill):
1. Reproduce: Triggered timeout by running 10 transactions in 30 seconds
2. Isolate: Timeout only occurs when payment gateway is called, not DB
3. Hypothesize: Gateway has rate limiting we're hitting
4. Test: Checked gateway logs — confirmed 429 responses
5. Fix: Added backoff logic specific to gateway calls
6. Verify: 100 transactions processed without timeout
```

### Anti-Patterns Section

Focus on **shortcuts and rationalizations**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Jumping to Fix after Reproduce
**Why it fails:** Without Isolate/Hypothesize, you're guessing. Guesses are often wrong, and wrong fixes create new bugs.
**Fix:** Complete all steps. The time "saved" by skipping is lost to debugging the wrong fix.

**Pattern:** Skipping Verify because "it obviously works"
**Why it fails:** Fixes often have side effects. "Obviously works" is the mindset that ships regressions.
**Fix:** Always verify. If verify feels redundant, make it fast, but do it.

**Pattern:** Treating pressure as permission to skip
**Why it fails:** "The user said hurry" doesn't change what good debugging requires. Fast wrong fixes are slower than methodical right fixes.
**Fix:** Acknowledge the pressure, explain the cost of skipping, proceed with the process.
```

### Troubleshooting Section

Address **process failures**, not just skill activation failures:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude skipped steps 2-4 and went straight to Fix
**Cause:** High confidence in the diagnosis ("I know what this is")
**Next steps:** Remind Claude that confidence isn't proof. The process exists because confident guesses are often wrong. Return to step 2.

**Symptom:** Claude completed all steps but the fix didn't work
**Cause:** Hypothesis in step 3 was wrong, but wasn't invalidated
**Next steps:** The process worked — it surfaced that the theory was wrong. Return to step 3 with new information from the failed fix.

**Symptom:** User interrupted the process demanding immediate action
**Cause:** External pressure (deadline, frustration, authority)
**Next steps:** Acknowledge the pressure. Explain that skipping steps risks making things worse. Offer a realistic time estimate for completing the process.
```

## Testing This Type

Process/Workflow skills need **pressure scenarios** to verify step adherence:

1. **Baseline test:** Task without skill — observe which steps get skipped
2. **Pressure test:** Task with skill + time pressure — does Claude resist shortcuts?
3. **Metrics:** Step completion rate, step order adherence, rationalization frequency

See `type-specific-testing.md` → Type 1: Process/Workflow Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Steps too vague | Can't verify completion | Make each step atomic and observable |
| No Decision Points for failures | Claude doesn't know what to do when stuck | Add explicit guidance for each failure mode |
| Anti-Patterns don't address pressure | Real failures come from shortcuts | Include time pressure and authority pressure scenarios |
| Examples show happy path only | Doesn't demonstrate value of process | Show Before (skipped steps, bad outcome) vs After (all steps, good outcome) |
