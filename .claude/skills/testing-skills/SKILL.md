---
name: testing-skills
description: Use when validating a draft skill works.
---

# Testing Skills

## Overview

**Testing skills IS Test-Driven Development applied to skill documentation.**

You run test scenarios (pressure scenarios with subagents), watch them fail without the skill (baseline behavior), run them with the skill (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**Input:** Draft SKILL.md + design context from brainstorming-skills

## Input from brainstorming-skills

Testing-skills expects:

| Input | Location | Purpose |
|-------|----------|---------|
| Draft SKILL.md | `.claude/skills/<skill-name>/SKILL.md` | The skill to test |
| Design context | `docs/plans/YYYY-MM-DD-<skill-name>-design.md` | Problem, success criteria, compliance risks |

**Design context provides:**
- **Problem statement** — what's broken/missing (informs scenario design)
- **Success criteria** — what should happen instead (defines GREEN)
- **Compliance risks** — what might cause agents to rationalize (informs pressure scenarios)

## TDD Mapping for Skills

| TDD Concept             | Skill Testing                                    |
| ----------------------- | ------------------------------------------------ |
| **Test case**           | Pressure scenario with subagent                  |
| **Production code**     | Skill document (SKILL.md)                        |
| **Test fails (RED)**    | Agent violates rule without skill (baseline)     |
| **Test passes (GREEN)** | Agent complies with skill present                |
| **Refactor**            | Close loopholes while maintaining compliance     |
| **Write test first**    | Run baseline scenario BEFORE evaluating skill    |
| **Watch it fail**       | Document exact rationalizations agent uses       |
| **Minimal code**        | Suggest edits addressing those specific violations |
| **Watch it pass**       | Verify agent now complies                        |
| **Refactor cycle**      | Find new rationalizations → plug → re-verify     |

## The Iron Law

```
NO SKILL DEPLOYMENT WITHOUT A FAILING TEST FIRST
```

Test skill before deploying? Required.
Skip testing because "it's obviously clear"? Violation.

**No exceptions:**

- Not for "simple skills"
- Not for "just documentation"
- Not for "reference material"

## The Testing Cycle

```
         ┌────────────────────────────────┐
         │                                │
         ▼                                │
       RED ──► GREEN ──► REFACTOR? ───────┘
    (baseline)  (verify)   (loopholes     │
                            found?)       │
                               │          │
                          EXIT if no ─────┘
```

### RED Phase: Baseline Testing

Run pressure scenarios with subagent WITHOUT the skill loaded. Document exact behavior:

1. **Design scenarios from design context:**
   - Use problem statement to create realistic situations
   - Use compliance risks to add pressure
   - Combine 3+ pressures for discipline-enforcing skills

2. **Run baseline test:**
   ```
   Task tool → general-purpose subagent
   Prompt: [scenario + pressure]
   Skill: NOT loaded
   ```

3. **Capture verbatim:**
   - What choices did the agent make?
   - What rationalizations did they use (exact words)?
   - Which pressures triggered violations?

**Output:** Documented baseline failures and rationalizations

**If baseline doesn't fail:**

The agent performed well without the skill. This could mean:

| Situation | Action |
|-----------|--------|
| Scenario too easy | Add more pressure, make task harder |
| Testing description not execution | Give agent actual work to do (see "Execution, Not Description") |
| Skill teaches what agents already do | Skill may not add value — consider if it's needed |
| Agent got lucky on this scenario | Try different scenarios targeting other compliance risks |

Before concluding "skill not needed," verify you're testing actual execution under realistic pressure with materials that have known flaws at multiple difficulty levels.

### GREEN Phase: Verify Skill Works

Run same scenarios WITH the skill loaded. Agent should now comply.

1. **Run test with skill:**
   ```
   Task tool → general-purpose subagent
   Prompt: [same scenario + pressure]
   Skill: Loaded via @skill-name or inline
   ```

2. **Verify compliance:**
   - Does agent follow the skill's guidance?
   - Does agent cite the skill as justification?
   - Does agent resist the pressure?

**If agent still fails:** Skill needs revision. Note specific gaps and loop back to brainstorming-skills with feedback.

**Output:** Confirmed compliance or feedback for revision

### REFACTOR Phase: Close Loopholes

Agent found new rationalization during GREEN? Add explicit counter.

1. **Capture new rationalizations verbatim**
2. **Suggest additions to skill:**
   - Explicit counters in rules
   - Entries in rationalization table
   - Red flags list updates
3. **Re-test until bulletproof**

**Bulletproof = no new rationalizations under maximum pressure**

## Testing by Skill Type

Different skill types need different test approaches. Identify your type, then design scenarios accordingly.

| Type | Core Question | Test With |
|------|---------------|-----------|
| Process/Workflow | Did Claude follow the steps? | Pressure on step completion/order |
| Quality Enhancement | Is output measurably better? | Before/after comparison + adversarial |
| Capability | Can Claude do the thing? | Success rate delta (with/without skill) |
| Solution Development | Did Claude find the best approach? | Alternatives explored + adversarial |
| Meta-cognitive | Did Claude notice what it should? | Recognition rate + calibration |
| Recovery/Resilience | Did Claude recover appropriately? | Failure injection scenarios |
| Orchestration | Right skills invoked in right order? | Phase transition + artifact handoff |
| Template/Generation | Does output match required format? | Structure validation + edge cases |

**Not sure which type?** See [type-specific-testing.md](references/type-specific-testing.md) for decision trees, scenario templates, and worked examples.

## Pressure Scenario Design

### Execution, Not Description

**Critical:** Test scenarios must have the agent **actually perform** the skill's task — not describe how they would perform it.

| Wrong | Right |
|-------|-------|
| "How would you review this design?" | "Here's a design document. Review it." |
| "What's your approach to debugging?" | "Here's a failing test. Debug it." |
| "Describe your TDD process" | "Write tests for this function." |

**Why this matters:**
- Describing a process tests *knowledge* — agent can articulate correct steps
- Performing a task tests *behavior* — agent actually follows the steps under pressure

An agent can perfectly describe a process while skipping critical steps when actually doing the work. Only execution-based tests catch this gap.

**For each skill type:**
- Reviewing skill → give them a document to review
- Debugging skill → give them a bug to debug
- TDD skill → give them code to write tests for
- Decision skill → give them a decision to make

Pressure scenarios and decision points occur *during* execution. The "Choose A, B, or C" templates test specific decision points mid-task — they assume the agent is already doing the work.

### Test Materials with Known Flaws

For skills that process input (review, analyze, debug, etc.), create test materials with **known defects at varying difficulty levels**.

**Why this matters:**
- You can't measure skill effectiveness without knowing the right answer
- Pass/fail is less informative than "found 42% baseline → 75% with skill"
- Layered difficulty shows where the skill adds value

**Structure:**

```
Test Material (e.g., design document, code with bugs, spec to review)
├── Obvious flaws (3-5) — should catch in first pass
├── Medium flaws (3-5) — requires cross-referencing or careful reading
├── Subtle flaws (3-5) — requires adversarial thinking or deep analysis
└── Answer key (separate file) — documents all flaws with locations
```

**Answer key format:**

```markdown
| ID | Flaw | Difficulty | Location | Why it matters |
|----|------|------------|----------|----------------|
| O1 | Missing error handling | Obvious | Section 3 | Crashes on invalid input |
| M1 | Inconsistent terminology | Medium | Section 2 vs 5 | Confuses implementers |
| H1 | Race condition under load | Subtle | Section 4 | Only surfaces at scale |
```

**Measurement:**

| Metric | Baseline | With Skill | Delta |
|--------|----------|------------|-------|
| Obvious flaws found | X/N | Y/N | |
| Medium flaws found | X/N | Y/N | |
| Subtle flaws found | X/N | Y/N | |
| Process steps followed | list | list | |

The skill adds value if with-skill finds more issues, especially subtle ones that require the skill's methodology (e.g., adversarial pass, systematic iteration).

### Pressure Types

| Pressure | Example |
|----------|---------|
| **Time** | Emergency, deadline, deploy window closing |
| **Sunk cost** | Hours of work, "waste" to delete |
| **Authority** | Senior says skip it, manager overrides |
| **Economic** | Job, promotion, company survival |
| **Exhaustion** | End of day, already tired |
| **Social** | Looking dogmatic, seeming inflexible |
| **Pragmatic** | "Being pragmatic vs dogmatic" |

### Scenario Template

```markdown
IMPORTANT: This is a real scenario. Choose and act.

[Situation that triggers the problem from design context]

[Pressure 1: e.g., time constraint]
[Pressure 2: e.g., sunk cost]
[Pressure 3: e.g., authority/social]

Options:
A) [Correct behavior per skill]
B) [Common violation]
C) [Another violation variant]

Choose and explain your reasoning.
```

### Combining Pressures

**Bad scenario (no pressure):** Too academic, agent just recites the skill

**Good scenario (single pressure):** Time + consequences

**Great scenario (multiple pressures):** Sunk cost + time + exhaustion + consequences

**Best tests combine 3+ pressures.**

## Bulletproofing Against Rationalization

### Signs Skill is Bulletproof

1. Agent chooses correct option under maximum pressure
2. Agent cites skill sections as justification
3. Agent acknowledges temptation but follows rule anyway
4. Meta-testing reveals "skill was clear, I should follow it"

### Signs Skill Needs Work

- Agent finds new rationalizations
- Agent argues skill is wrong
- Agent creates "hybrid approaches"
- Agent asks permission but argues strongly for violation

### Building Rationalization Table

Capture rationalizations from baseline testing. Every excuse agents make goes in the table:

```markdown
| Excuse                           | Reality                                                                 |
| -------------------------------- | ----------------------------------------------------------------------- |
| "Too simple to test"             | Simple code breaks. Test takes 30 seconds.                              |
| "I'll test after"                | Tests passing immediately prove nothing.                                |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
```

### Red Flags List

Make it easy for agents to self-check when rationalizing:

```markdown
## Red Flags - STOP and Reconsider

- [Specific rationalization 1]
- [Specific rationalization 2]
- "This is different because..."
- "I'm following the spirit not the letter"

**All of these mean: Follow the skill. No exceptions.**
```

## Common Rationalizations for Skipping Testing

| Excuse                         | Reality                                                          |
| ------------------------------ | ---------------------------------------------------------------- |
| "Skill is obviously clear"     | Clear to you ≠ clear to other agents. Test it.                   |
| "It's just a reference"        | References can have gaps, unclear sections. Test retrieval.      |
| "Testing is overkill"          | Untested skills have issues. Always. 15 min testing saves hours. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE deploying.        |
| "Too tedious to test"          | Testing is less tedious than debugging bad skill in production.  |
| "I'm confident it's good"      | Overconfidence guarantees issues. Test anyway.                   |
| "Academic review is enough"    | Reading ≠ using. Test application scenarios.                     |
| "No time to test"              | Deploying untested skill wastes more time fixing it later.       |

**All of these mean: Test before deploying. No exceptions.**

## Testing Checklist

**IMPORTANT: Use TodoWrite to create todos for EACH checklist item.**

### RED Phase - Baseline Testing

- [ ] Read design context (problem statement, success criteria, compliance risks)
- [ ] **Verify execution-based testing:** agent performs the task, not describes it (see "Execution, Not Description")
- [ ] Create test materials with known flaws (obvious/medium/subtle) and answer key
- [ ] Design pressure scenarios (3+ combined pressures for discipline skills)
- [ ] Run scenarios WITHOUT skill — agent must actually perform the task
- [ ] Document baseline behavior verbatim
- [ ] Score: what flaws did baseline find? What process steps did they follow?
- [ ] If baseline doesn't fail: verify you're testing execution, not description

### GREEN Phase - Verify Skill Works

- [ ] Run same scenarios WITH skill loaded
- [ ] Verify agent follows the skill's process (not just good outcomes)
- [ ] Agent cites skill as justification
- [ ] Score: what flaws did with-skill find? Compare to baseline
- [ ] Measure process compliance: Entry Gate? Iteration? Required steps?
- [ ] If fails: document gaps, provide feedback for revision

### REFACTOR Phase - Close Loopholes

- [ ] Identify NEW rationalizations from testing
- [ ] Suggest explicit counters for skill
- [ ] Build rationalization table entries
- [ ] Create red flags list entries
- [ ] Re-test until bulletproof

### Exit Criteria

- [ ] Agent follows skill under maximum pressure
- [ ] No new rationalizations in last test round
- [ ] Skill ready for deployment OR feedback provided to brainstorming-skills

## Anti-Patterns

### ❌ Testing Without Pressure

Running "does the agent understand the skill?" instead of "does the agent follow the skill under pressure?"

**Fix:** Always combine 3+ pressures in scenarios

### ❌ Accepting First Pass

Agent complied once → "testing complete"

**Fix:** Try different pressure combinations, look for loopholes

### ❌ Vague Failure Documentation

"Agent didn't follow the skill"

**Fix:** Capture exact rationalizations verbatim for targeted fixes

### ❌ Testing Your Own Skill Immediately

You just wrote it, you'll unconsciously confirm it works

**Fix:** Let time pass, or have different session test it

### ❌ Skipping Baseline

"I know what agents do without the skill"

**Fix:** Always run baseline. Document actual behavior, not assumptions.

### ❌ Testing Description Instead of Execution

Asking "How would you approach this?" instead of giving the agent actual work to do.

**Fix:** Give the agent the actual task. For a review skill, provide a document to review. For a debugging skill, provide a bug to debug. Watch them *do* the work, not *describe* the work.

## Output

After testing, provide one of:

**If skill passes:**
```markdown
## Testing Complete: <skill-name>

**Status:** Ready for deployment

**Coverage (if test materials with known flaws used):**

| Category | Baseline | With Skill | Delta |
|----------|----------|------------|-------|
| Obvious  | X/N      | Y/N        | +Z    |
| Medium   | X/N      | Y/N        | +Z    |
| Subtle   | X/N      | Y/N        | +Z    |

**Process compliance:**

| Requirement | Baseline | With Skill |
|-------------|----------|------------|
| [Step 1]    | No       | Yes        |
| [Step 2]    | Partial  | Yes        |

**Rationalizations captured:** [N] added to skill's table

**Recommendation:** Deploy to ~/.claude/skills/
```

**If skill needs revision:**
```markdown
## Testing Feedback: <skill-name>

**Status:** Needs revision

**Failures:**
- [Scenario]: Agent rationalized with "[exact quote]"
- Gap identified: [what's missing from skill]

**Suggested additions:**
1. Add to rules section: [specific text]
2. Add to rationalization table: [excuse] → [reality]
3. Add red flag: [specific phrase to watch for]

**Next step:** Return to brainstorming-skills with this feedback
```

## References

**Testing methodology:**
- [references/testing-skills-with-subagents.md](references/testing-skills-with-subagents.md) — Subagent execution details, meta-testing techniques, worked examples
- [references/type-specific-testing.md](references/type-specific-testing.md) — 8 skill types × scenario templates × metrics frameworks
- [references/methodology-dialogue-skills.md](references/methodology-dialogue-skills.md) — Testing multi-turn dialogue skills (hybrid RED-GREEN)

**Bulletproofing psychology:**
- [references/persuasion-principles.md](references/persuasion-principles.md) — Research foundation on authority, commitment, scarcity, social proof (Cialdini, 2021; Meincke et al., 2025)

## The Bottom Line

**Testing skills is TDD for process documentation.**

Same Iron Law: No deployment without failing test first.
Same cycle: RED (baseline) → GREEN (verify) → REFACTOR (close loopholes).
Same benefits: Better quality, fewer surprises, bulletproof results.

If brainstorming-skills designed it, testing-skills validates it works.
