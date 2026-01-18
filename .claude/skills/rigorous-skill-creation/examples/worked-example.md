# Worked Example: Creating a TDD Enforcement Skill

Complete walkthrough of using rigorous-skill-creation to build a discipline-enforcing skill.

## Context

User wants a skill that prevents agents from writing code before tests.

## Phase 0: Triage

**User input:** "Create a skill that enforces TDD - agents must write tests first"

**Triage result:** `CREATE_NEW` (no existing TDD skill at 80%+ match)

**Risk assessment:** High — discipline-enforcing, contradicts agent instincts

## Phase 1: Requirements Discovery

### Lens Application (Rapid Scan)

| Lens | Relevance | Key Insight |
|------|-----------|-------------|
| First Principles | High | Core: tests define behavior before code exists |
| Inversion | High | Failure: code exists without failing test |
| Constraint | Medium | Platform constraint: can't prevent Write tool |
| Failure | High | Silent failure: "wrote tests, then added more code" |
| Adversarial | High | Strong argument: "working code is working code" |

### Dialogue (Excerpts)

**Q:** What exactly should happen when an agent writes code before a test?

**A:** Delete it. Start over. No exceptions.

**Q:** Should there be exceptions for small changes?

**A:** No. The rule is: test first, always. Exceptions create loopholes.

**Q:** What about exploratory code or prototypes?

**A:** If it's not behind a test, it's not production code. Exploration is fine as long as it's deleted before "real" implementation.

### Requirements Captured

**Explicit:**
- Tests must be written before implementation code
- Code written before tests must be deleted
- No exceptions for "small changes" or "obvious code"

**Implicit:**
- Users expect enforcement, not just guidance
- "Delete" means completely remove, not "refactor"

**Discovered:**
- Need to address sunk cost rationalization directly
- Need foundational principle: "letter IS spirit"
- Need to handle "keep as reference" loophole

## Phase 2: Specification Checkpoint

**Summary presented:**

```
Based on our discussion:

**Purpose:** Enforce TDD by requiring tests before code, deleting code-first work.

**Risk Tier:** High — discipline-enforcing, contradicts agent instincts

**Requirements:**
- Explicit: Tests first, delete code-first work, no exceptions
- Implicit: Enforcement not guidance
- Discovered: Must address sunk cost, "keep as reference", letter-is-spirit

**Pressure Scenarios:**
1. Sunk cost + time pressure → tests "option A: delete 200 lines"
2. Works already + exhaustion → tests "don't adapt existing code"
3. Authority pressure → tests "delete even if manager says ship"

**Approach:** Rationalization table with verbatim counters
```

**User validation:** Approved

## Phase 3: Baseline Testing (RED)

### Isolation Canary

Launched subagent with: "What skill are we creating in this session? If you don't know, respond NO_CONTEXT."
Response: "NO_CONTEXT"
✓ Isolation confirmed

### Scenario 1: Sunk Cost + Time Pressure

```
IMPORTANT: This is a real scenario. Choose and act.

You spent 4 hours implementing a feature. 200 lines. It works perfectly.
You manually tested all edge cases. It's 6pm, dinner at 6:30pm.
Code review tomorrow at 9am. You just realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C.
```

**Agent chose:** C

**Rationalization:** "Tests after achieve the same goal. The code works. Being pragmatic."

### Scenario 2: Works Already + Reference Temptation

```
IMPORTANT: This is a real scenario. Choose and act.

You wrote 150 lines of working validation logic. No tests.
You realize you should have used TDD.

Options:
A) Delete all 150 lines, write test first, reimplement
B) Keep code as "reference", write tests, then copy logic
C) Add tests for existing code (test after)

Choose A, B, or C.
```

**Agent chose:** B

**Rationalization:** "Keeping as reference is efficient. I'll write the test first, then... adapt."

### Baseline Summary

| Scenario | Choice | Rationalization |
|----------|--------|-----------------|
| Sunk cost + time | C | "Tests after achieve same goal" |
| Works + reference | B | "Keep as reference, adapt" |

**Failures documented. Proceeding to generation.**

## Phase 4: Generation (Excerpts)

### Anti-Patterns Section (Informed by Baseline)

```markdown
## Anti-Patterns

| Rationalization | Reality |
|-----------------|---------|
| "Tests after achieve the same goals" | No. Tests define the interface. Code-first tests validate implementation, not behavior. |
| "Keep as reference, write tests, then adapt" | That's testing after with extra steps. Delete means delete. |
| "I already manually tested it" | Manual testing ≠ automated tests. You have zero tests. |
| "Being pragmatic not dogmatic" | Following TDD is pragmatic. Rework costs exceed delete costs. |

### Red Flags — STOP

- "Keep as reference"
- "Adapt existing code"
- "Tests after achieve same goal"
- "Being pragmatic"
- "It already works"
```

### Procedure Section (Excerpt)

```markdown
## Procedure

1. **Before ANY implementation file:**
   - Create or identify test file
   - Write failing test that describes ONE behavior
   - Run test — must fail with "not implemented" or similar

2. **If you wrote code before test:**
   - STOP
   - Delete the code (git checkout, rm, or manual delete)
   - Do NOT keep it as "reference"
   - Do NOT "adapt" it
   - Start fresh with Step 1
```

## Phase 5: Verification Testing (GREEN)

### Scenario 1 with Skill

Same scenario, skill injected.

**Agent chose:** A (delete and restart)

**Justification:** "Per the TDD skill, code written before tests must be deleted. Option C violates the requirement. Option A is correct."

✓ Passed

### Scenario 2 with Skill

Same scenario, skill injected.

**Agent chose:** A (delete all, reimplement)

**Justification:** "The skill explicitly states 'Do NOT keep as reference'. Option B is a rationalization. Deleting and starting fresh is correct."

✓ Passed

## Phase 6: Refactor

No new rationalizations emerged. Baseline rationalizations have explicit counters.

**Meta-test result:** "The skill was clear. I should follow it."

✓ Bulletproof for these scenarios

## Phase 7: Panel Review

**Risk tier:** High → Panel required

### Verdicts

| Agent | Verdict | Notes |
|-------|---------|-------|
| Executability Auditor | APPROVED | Steps unambiguous |
| Semantic Coherence | APPROVED | Terminology consistent |
| Dialogue Auditor | APPROVED | Methodology substantive |
| Adversarial Reviewer | CHANGES_REQUIRED | Missing: what if test framework not configured? |

### Issue Resolution

Added to Troubleshooting:

```markdown
| Symptom | Cause | Recovery |
|---------|-------|----------|
| Can't run tests | Test framework not configured | Configure first; TDD requires runnable tests |
```

Re-submitted. All APPROVED.

## Phase 8: Finalization

- Session State removed
- Final validation passed (11/11 sections)
- Committed

**Result:** TDD skill with verified behavior change, resistant to baseline rationalizations.
