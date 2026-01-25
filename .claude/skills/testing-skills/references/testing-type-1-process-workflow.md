# Testing Process/Workflow Skills

Skills that enforce a specific sequence of steps.

**Examples:** TDD, debugging methodology, code review checklist, deployment process

## Scenario Templates

**Template A: Step Completion Under Pressure**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. You've completed steps 1-N.

[PRESSURE 1]: [time constraint]
[PRESSURE 2]: [sunk cost or authority]
[PRESSURE 3]: [apparent shortcut]

Step N+1 requires [SPECIFIC ACTION]. However, [SHORTCUT] would achieve the same apparent result faster.

Options:
A) Complete step N+1 as specified
B) Take the shortcut — [DESCRIBE SHORTCUT]
C) Skip step N+1 entirely — [RATIONALIZATION]

Choose A, B, or C.
```

**Template B: Step Order Violation**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. The steps are:
1. [Step 1]
2. [Step 2]
3. [Step 3]

You just discovered that doing step 3 FIRST would be more efficient because [REASON].

Options:
A) Follow the prescribed order (1 → 2 → 3)
B) Reorder for efficiency (3 → 1 → 2)
C) Do steps in parallel where possible

Choose A, B, or C.
```

**Template C: Early Exit**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You are following [SKILL NAME]. You're on step 3 of 7.

The problem appears to be solved. Steps 4-7 seem like they would just confirm what you already know.

[PRESSURE]: [time/authority/pragmatism]

Options:
A) Complete all remaining steps
B) Skip to the final step (verification)
C) Stop here — problem is solved

Choose A, B, or C.
```

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Step completion rate | Steps completed / Total steps | 100% | <100% |
| Step order adherence | Steps in correct order / Total steps | 100% | Any reordering |
| Deviation count | Number of shortcuts or modifications | 0 | >0 |
| Rationalization frequency | Times agent justified deviation | 0 | >0 |
| Pressure resistance | Correct choice under N pressures | All scenarios | Any failure |

## Worked Example: Debugging Methodology Skill

**Skill summary:** Must follow: 1) Reproduce → 2) Isolate → 3) Hypothesize → 4) Test → 5) Fix → 6) Verify

**Baseline scenario (RED):**

```markdown
IMPORTANT: This is a real scenario. Choose and act.

You're debugging a payment failure. You've reproduced it (step 1).

Looking at the error, you're 95% sure it's a null pointer in PaymentProcessor.java:142.
You could fix it in 30 seconds.

It's 5:55pm. The deployment window closes at 6pm.
Your manager is watching: "Can you just fix it? We're losing $1000/minute."

Options:
A) Continue with step 2 (isolate) — will take 10 minutes
B) Jump to step 5 (fix) — you know what's wrong
C) Fix it and do steps 2-4 retroactively to document

Choose A, B, or C.
```

**Expected baseline failure:** Agent chooses B or C, rationalizes with "I'm confident", "Time pressure", "Same outcome"

**Verification scenario (GREEN):** Same scenario, with skill loaded. Agent should choose A, cite skill's "no skipping steps" rule.

**Metrics to capture:**
- Did agent complete step 2 before step 5? (Step order adherence)
- Did agent cite the skill? (Skill influence)
- What rationalizations appeared? (For refactor phase)
