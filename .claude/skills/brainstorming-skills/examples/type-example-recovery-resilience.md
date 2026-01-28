# Type Example: Recovery/Resilience Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Recovery/Resilience.

## Core Question

**Did Claude recover appropriately?**

Recovery/Resilience skills help Claude handle failures, errors, and unexpected situations gracefully. The failure mode isn't "couldn't do the task" — it's "made things worse when something went wrong."

## Type Indicators

Your skill is Recovery/Resilience if it:
- Says "handle", "recover", "when X fails", "gracefully"
- Involves error handling or fallback strategies
- Helps Claude respond to unexpected situations
- Prevents Claude from making problems worse

## The Recovery Test

Recovery skills are tested by injecting failures:
- Can Claude recognize the failure?
- Does Claude attempt appropriate recovery?
- Does Claude avoid making things worse?
- Does Claude communicate clearly about what happened?

## Section Guidance

### Process Section

**Use failure recognition + recovery strategy structure:**

**Example (handle tool failures):**

```markdown
## Process

**Step 1: Recognize the Failure**

Identify failure type from output:
- **Explicit error:** Error message, non-zero exit code, exception
- **Silent failure:** Command succeeded but output is unexpected
- **Partial success:** Some parts worked, others didn't
- **Timeout:** No response within expected time

**Step 2: Assess Impact**

Before attempting recovery:
- What state is the system in now?
- What was partially completed?
- Is the situation stable or degrading?
- Can we safely retry, or would that make things worse?

**Step 3: Choose Recovery Strategy**

| Failure Type | Safe Retries? | Recovery Approach |
|--------------|---------------|-------------------|
| Transient (network, timeout) | Yes (with backoff) | Retry 2-3 times with exponential backoff |
| State conflict (merge conflict, lock) | No | Diagnose state, resolve conflict, then proceed |
| Permission/auth | No | Don't retry; escalate to user |
| Data corruption | No | Stop immediately; don't write anything else |
| Unknown | No | Don't guess; diagnose first |

**Step 4: Communicate**

Always tell the user:
- What failed
- What you tried for recovery
- Current state
- What you need (if escalating)
```

**Anti-pattern:** Immediately retrying without understanding the failure type.

### Decision Points Section

Focus on **recovery strategy selection and escalation triggers**:

**Example:**

```markdown
## Decision Points

**Retry or not:**
- Transient network error → Retry with backoff (max 3 attempts)
- Authentication failure → Don't retry. Credentials won't magically work.
- Conflict/lock → Don't retry blindly. Diagnose the conflict first.
- Unknown error → Don't retry. You might make it worse.

**Escalate or continue:**
- If you've retried twice without success → Escalate. More retries won't help.
- If error message suggests user action needed → Escalate immediately.
- If you're not sure what's wrong → Escalate. Don't guess.

**How much to explain:**
- For simple, recovered failures → Brief: "Network hiccup, retried successfully."
- For failures requiring user action → Detailed: What failed, what state we're in, what's needed.
- For cascading failures → Very detailed: Full timeline of what happened.

**Damage control:**
- If recovery attempt failed → Stop. Don't try another approach without thinking.
- If you made things worse → Acknowledge immediately. Don't hide it.
- If rollback is possible → Prefer rollback over forward-fix when uncertain.
```

### Examples Section

Show **recovery comparison**:
- Before: Failure made worse or poorly communicated
- After: Appropriate recovery, clear communication

**Example:**

```markdown
## Examples

**Scenario:** Git push fails due to remote changes

```
error: failed to push some refs to 'origin'
hint: Updates were rejected because the remote contains work that you do not have locally.
```

**Before** (without skill):
Claude suggests: "Try `git push --force` to override the remote changes."

Problems:
- Destructive action without understanding the situation
- Could overwrite someone else's work
- Didn't diagnose what the remote changes were

**After** (with skill):

**Step 1: Recognize** — Push rejected, not a transient error. Remote has commits we don't have.

**Step 2: Assess** — This is a state conflict, not a transient failure. Our local commits are fine, but we need to integrate remote changes.

**Step 3: Recover** — This is NOT a retry situation. We need to:
```bash
# Fetch to see what's on remote
git fetch origin

# See what changed
git log HEAD..origin/main --oneline

# Integrate (rebase or merge depending on workflow)
git pull --rebase origin main
# OR
git merge origin/main
```

**Step 4: Communicate:**
"The push failed because the remote has commits you don't have locally. This happens when someone else pushed while you were working.

I fetched the remote changes. Here's what was added: [list commits]

Before pushing, you need to integrate these changes. Would you like me to:
- Rebase your commits on top (cleaner history)
- Merge (preserves exact commit history)

I recommend rebase unless these are shared/published commits."
```

### Anti-Patterns Section

Focus on **recovery mistakes**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Retrying without understanding the failure
**Why it fails:** Transient failures can be retried. State conflicts, auth failures, and data issues cannot. Blind retry can make things worse.
**Fix:** Always identify failure type before choosing recovery strategy.

**Pattern:** Force/override as first response
**Why it fails:** --force flags exist for a reason, but they're destructive. Using them reflexively loses data.
**Fix:** Force flags are last resort, require user consent, and need clear warning about consequences.

**Pattern:** Hiding that something went wrong
**Why it fails:** User doesn't know the true state. They make decisions based on false assumptions.
**Fix:** Always communicate failures, even if you recovered. "There was an issue, I handled it" is better than silence.

**Pattern:** Cascading fixes
**Why it fails:** Fix A broke B, so you fix B, which broke C... Each fix adds risk and complexity.
**Fix:** After first failed fix, stop. Assess the full situation. Consider rollback instead of forward-fixing.

**Pattern:** Guessing when uncertain
**Why it fails:** "Maybe it's X, let me try Y" can make things worse if it wasn't X.
**Fix:** If uncertain, diagnose more. Or escalate: "I'm not sure what's wrong. Here's what I see: [details]"
```

### Troubleshooting Section

Address **recovery process failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude made the problem worse while trying to fix it
**Cause:** Didn't properly assess before attempting recovery
**Next steps:** Rollback if possible. Then diagnose from the new (worse) state. Don't compound with more guessing.

**Symptom:** Claude keeps retrying something that won't work
**Cause:** Misidentified failure as transient when it's persistent
**Next steps:** Stop retrying. Diagnose the actual failure type. Is it auth? Config? State conflict?

**Symptom:** User is surprised by the current state
**Cause:** Claude didn't communicate the failure or partial recovery
**Next steps:** Full status report: what was attempted, what succeeded, what failed, current state.

**Symptom:** Claude escalated too quickly without trying anything
**Cause:** Over-cautious, treating everything as dangerous
**Next steps:** Calibrate: some failures (network, timeout) can safely be retried. Not everything needs escalation.
```

## Testing This Type

Recovery/Resilience skills need **failure injection**:

1. **Recognition test:** Inject failures — does Claude identify them correctly?
2. **Strategy test:** Does Claude choose appropriate recovery (retry vs diagnose vs escalate)?
3. **Damage test:** Did recovery make things worse?
4. **Communication test:** Was user informed clearly?
5. **Pressure test:** Add urgency — does Claude still avoid risky shortcuts?

See `type-specific-testing.md` → Type 6: Recovery/Resilience Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Blind retry | Makes transient/persistent distinction ignored | Always identify failure type first |
| Force flags reflexively | Destructive action without consent | Force is last resort, requires user approval |
| Silent recovery | User doesn't know true state | Always communicate, even on successful recovery |
| Cascading fixes | Each fix creates new problems | Stop after first failed fix, assess fully |
