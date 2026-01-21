---
name: testing-skills
description: "Use when validating a draft skill works. Receives draft SKILL.md from brainstorming-skills and validates it through RED-GREEN-REFACTOR testing."
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

Different skill types need different test approaches:

### Discipline-Enforcing Skills

**Examples:** TDD, verification-before-completion, designing-before-coding

**Test with:**
- Academic questions: Do they understand the rules?
- Pressure scenarios: Do they comply under stress?
- Multiple pressures combined: time + sunk cost + exhaustion
- Identify rationalizations and add explicit counters

**Success criteria:** Agent follows rule under maximum pressure

### Technique Skills

**Examples:** condition-based-waiting, root-cause-tracing, defensive-programming

**Test with:**
- Application scenarios: Can they apply the technique correctly?
- Variation scenarios: Do they handle edge cases?
- Missing information tests: Do instructions have gaps?

**Success criteria:** Agent successfully applies technique to new scenario

### Pattern Skills

**Examples:** reducing-complexity, information-hiding concepts

**Test with:**
- Recognition scenarios: Do they recognize when pattern applies?
- Application scenarios: Can they use the mental model?
- Counter-examples: Do they know when NOT to apply?

**Success criteria:** Agent correctly identifies when/how to apply pattern

### Reference Skills

**Examples:** API documentation, command references, library guides

**Test with:**
- Retrieval scenarios: Can they find the right information?
- Application scenarios: Can they use what they found correctly?
- Gap testing: Are common use cases covered?

**Success criteria:** Agent finds and correctly applies reference information

## Pressure Scenario Design

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
- [ ] Design pressure scenarios (3+ combined pressures for discipline skills)
- [ ] Run scenarios WITHOUT skill
- [ ] Document baseline behavior verbatim
- [ ] Identify patterns in rationalizations/failures

### GREEN Phase - Verify Skill Works

- [ ] Run same scenarios WITH skill loaded
- [ ] Verify agent now complies
- [ ] Agent cites skill as justification
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

## Output

After testing, provide one of:

**If skill passes:**
```markdown
## Testing Complete: <skill-name>

**Status:** Ready for deployment

**Tests run:**
- [Scenario 1]: PASS - agent followed skill under [pressures]
- [Scenario 2]: PASS - agent resisted [rationalization]

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

**Detailed testing methodology:**
- [references/testing-skills-with-subagents.md](references/testing-skills-with-subagents.md) — Complete testing methodology with pressure scenario design, meta-testing techniques

**Bulletproofing psychology:**
- [references/persuasion-principles.md](references/persuasion-principles.md) — Research foundation on authority, commitment, scarcity, social proof (Cialdini, 2021; Meincke et al., 2025)

## The Bottom Line

**Testing skills is TDD for process documentation.**

Same Iron Law: No deployment without failing test first.
Same cycle: RED (baseline) → GREEN (verify) → REFACTOR (close loopholes).
Same benefits: Better quality, fewer surprises, bulletproof results.

If brainstorming-skills designed it, testing-skills validates it works.
