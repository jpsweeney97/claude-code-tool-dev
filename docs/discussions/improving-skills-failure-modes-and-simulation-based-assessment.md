# Discussion: Improving-Skills Failure Modes and Simulation-Based Assessment

**Date:** 2026-02-03
**Participants:** JP, Claude (Opus 4.5)
**Subject:** Root cause analysis of improving-skills execution failures and exploration of simulation-based assessment as a solution

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Observed Failure Modes](#observed-failure-modes)
- [Root Cause Analysis](#root-cause-analysis)
- [Proposed Solution: Simulation-Based Assessment](#proposed-solution-simulation-based-assessment)
- [Design Questions](#design-questions)
  - [Question 1: How Many Scenarios Are Enough?](#question-1-how-many-scenarios-are-enough)
  - [Question 2: How Do You Avoid Overfitting to Test Scenarios?](#question-2-how-do-you-avoid-overfitting-to-test-scenarios)
  - [Question 3: What About Skills That Are Hard to Test?](#question-3-what-about-skills-that-are-hard-to-test)
  - [Question 4: What's the Cost/Benefit?](#question-4-whats-the-costbenefit)
- [Next Steps](#next-steps)

---

## Problem Statement

The `improving-skills` skill frequently fails to achieve its primary objective of improving skills. A root cause analysis was required to determine why execution fails so frequently.

The failures observed were in **how Claude executes the skill**, not in the skill's structural design per se.

---

## Observed Failure Modes

Two specific failure modes were identified:

1. **Claude produced low-quality findings, despite completing the assessment**
   - Claude went through the motions procedurally without achieving the substance of what those steps were meant to produce
   - The assessment was completed but hollow

2. **Claude based skill quality assessment only on level of adherence to `skills-guide.md`, not on how conducive the skill was to its primary objective**
   - Assessment focused on structural compliance rather than functional effectiveness
   - A skill could score well on the assessment while completely failing at its stated purpose

---

## Root Cause Analysis

### The Pattern: Form vs. Function Conflation

Both failures stem from the same root: **the skill assesses how a skill is written rather than whether it achieves its purpose**. Completing the assessment produces low-quality findings because the assessment criteria themselves are misaligned with what matters.

### Evidence from the Skill's Architecture

The skill's assessment steps prioritize structural compliance:

- **Step 2** directs Claude to note "How it compares to skills-guide.md standards"
- **Step 3** defines strengths as "Elements that follow skills-guide.md recommendations" and weaknesses as "Deviations from skills-guide.md standards"
- **Step 4** lists strength sources like "Follows standards" and "Type-appropriate"

The skill does include a "Center Claude's Actual Needs" section with questions like:
- "Does this content help Claude succeed at something it would otherwise struggle with?"
- "Does Claude actually exhibit the failure modes these anti-patterns address?"

But this framing is **positioned as a lens, not integrated into the assessment steps**. By Step 3, Claude is back to checking structural compliance. The effectiveness question gets lost.

### Why the Skill Optimizes for Form Over Function

**The measurement problem.** Structural compliance is checkable:
- "Does it have trigger phrases?" → Binary, verifiable
- "Does it use blocking language?" → Binary, verifiable
- "Is it under 500 lines?" → Binary, verifiable

Functional effectiveness is not:
- "Will Claude follow this correctly?" → Requires simulation
- "Does this prevent the failure modes it claims to prevent?" → Requires empirical evidence
- "Is this content genuinely useful to Claude?" → Requires understanding Claude's actual capabilities

The skill defaults to what can be checked. This is a rational response to an ill-defined problem, but it produces the wrong outcomes.

### The "Center Claude's Actual Needs" Section is Aspirational, Not Operational

It poses the right questions but provides **no method for answering them**. How would Claude determine if it "actually exhibits" a failure mode? That requires either:
1. Empirical evidence from past executions
2. Adversarial self-simulation ("If I followed this, where would I go wrong?")

Neither is specified. So Claude reads the section, nods, and proceeds to the structural checklist it can complete.

### The Discipline Skill Paradox

Discipline skills exist because Claude shortcuts processes. But if the assessment of discipline skills is itself a checklist, Claude can shortcut the assessment by completing the checklist without genuine analysis.

The skill enforces **process compliance**, not **substantive thinking**. Claude can satisfy every step and gate while producing hollow output.

### The Self-Referential Proof

If you assessed `improving-skills` using its own methodology:
- **Structure:** ✓ Has phases, gates, rationalization tables, anti-patterns
- **Type-appropriate:** ✓ Uses discipline skill techniques correctly
- **Follows skills-guide.md:** ✓ Under 500 lines, has trigger phrases, etc.

It would score well. Yet it fails at its stated purpose. This demonstrates that **structural compliance ≠ functional effectiveness**.

### What Functional Assessment Would Require

To assess whether a skill works, Claude would need to:

1. **Understand the skill's purpose** — not its structure, its intent
2. **Simulate execution** — "If I were Claude following this, where would I misinterpret or shortcut?"
3. **Identify failure modes specific to this skill** — not generic anti-patterns, but this skill's vulnerabilities
4. **Reason adversarially** — actively try to find ways the skill could fail

This is qualitatively different from comparing against a reference document.

---

## Proposed Solution: Simulation-Based Assessment

### The Repair vs. Radical Simplification Choice

Before proceeding with a specific approach, a key choice point was identified: **repair within a new methodology, or radically simplify?**

The question posed: At 663 lines, is a discipline skill of this complexity inherently fragile? Maybe the problem isn't just *what* the skill assesses, but that discipline skills of this complexity are hard to execute reliably regardless of methodology.

A minimal version was considered:
1. What is this skill trying to do?
2. Simulate execution — where would you fail?
3. Those are the weaknesses. Fix them.

**Decision:** Explore repair via simulation-based assessment rather than radical simplification. The simulation-based approach directly addresses the identified root cause (assessing form over function) and provides a testable methodology. If simulation-based assessment proves too complex in practice, radical simplification remains an option.

### The Paradigm Shift

Replace **theoretical assessment** with **empirical measurement**.

| Current Approach | Proposed Approach |
|------------------|-------------------|
| Read the skill, reason about what would happen | Run the skill, observe what actually happens |
| Compare against standards document | Compare against baseline behavior |
| Assessment = expert judgment | Assessment = experimental evidence |
| "This should work because..." | "This does/doesn't work because we observed..." |

This treats skill improvement as **empirical science**, not **code review**.

### The Mechanism

**Step 1: Establish baseline**

Deploy a subagent *without* the skill. Give it a task that the skill is designed to help with. Observe:
- What approach does it take?
- Where does it struggle?
- What shortcuts does it take?
- What quality does it produce?

This is the control group. It answers: "What does Claude do naturally, without this skill's guidance?"

**Step 2: Measure skill-assisted behavior**

Deploy a subagent *with* the skill. Same task, same conditions. Observe across multiple dimensions:
- **Delta from baseline:** Did behavior change? In what direction?
- **Instruction compliance:** What did the subagent do at each instruction?
- **Shortcut patterns:** Where was it tempted to skip steps? Did it?
- **Misinterpretation:** Where did it understand instructions differently than intended?
- **Assumption failures:** Where did the skill assume something that wasn't true?

**Step 3: The delta is the assessment**

The comparison between baseline and skill-assisted behavior reveals:
- Where the skill helps (behavior improved)
- Where the skill fails to help (no change from baseline)
- Where the skill might hurt (behavior worse or confused)
- Where the skill is ignored (instructions present but not followed)

This is functional assessment. Not "does it follow the guide" but "does it change behavior in the intended direction."

**Step 4: Findings inform improvement**

The observed failures become the improvement targets:
- Instruction ignored → Make it more salient or enforceable
- Instruction misinterpreted → Clarify or restructure
- Assumption failed → Remove assumption or add precondition check
- No delta from baseline → The skill isn't providing value here; why?

**Step 5: Iterate until threshold**

Improve, re-run, compare. The cycle continues until:
- Skill-assisted behavior matches intended behavior on key dimensions
- Critical failure modes no longer occur
- Delta from baseline demonstrates the skill's value

### Why Subagents Enable This

Subagents run in their own context window with:
- Custom system prompt
- Specific tool access
- Independent permissions
- Isolated context (no contamination from the parent conversation)

This allows controlled experiments:
- Baseline subagent truly doesn't have the skill
- Test subagent truly does have the skill
- Same task, same conditions, different skill presence

### Integration with Purpose-First Framing

The two approaches work together:

| Purpose-First | Simulation-Based |
|---------------|------------------|
| Defines what should happen | Measures what actually happens |
| "This skill should cause Claude to assess before editing" | "Did the subagent assess before editing?" |
| Establishes success criteria | Tests against those criteria |

Purpose-First Framing sets the target. Simulation-Based Assessment measures against it. The gap between target and observed behavior = the work.

### Implications for Skill Architecture

If this approach is adopted, the `improving-skills` skill transforms substantially:

**Current structure:** Assessment phase → Recommendations phase → Dialogue phase → Implementation

**New structure:**
1. **Purpose extraction:** What is this skill trying to achieve? What behavior change does it intend?
2. **Scenario design:** What tasks would reveal whether it achieves that?
3. **Baseline measurement:** Run subagent without skill
4. **Skill-assisted measurement:** Run subagent with skill
5. **Delta analysis:** Compare, identify failures
6. **Improvement:** Address observed failures
7. **Re-test:** Run again, verify improvement
8. **Iterate:** Until threshold met

The skills-guide.md becomes a *remediation reference* — once you know what's wrong, it helps you fix it — rather than the assessment lens.

---

## Design Questions

Four key questions were identified for working through:

1. How many scenarios are enough?
2. How do you avoid overfitting to test scenarios?
3. What about skills that are hard to test?
4. What's the cost/benefit?

---

### Question 1: How Many Scenarios Are Enough?

**Initial position:** 5 scenarios as a default.

**Conclusion:** 5 is a reasonable default, but **the quality of scenario design matters more than the count**.

#### Factors That Influence Scenario Count

- **Coverage of purpose:** Scenarios need to exercise the skill's intended scope
- **Edge cases vs. typical usage:** Need both happy path and boundary conditions
- **Diminishing returns:** Each additional scenario adds cost
- **Signal vs. noise:** Enough scenarios to distinguish pattern from variance

#### What 5 Well-Chosen Scenarios Might Look Like

For `improving-skills`:

1. **Clear issues:** A skill with obvious structural problems. Can it diagnose them?
2. **Subtle issues:** A skill that looks fine structurally but doesn't achieve its purpose. Can it see past form to function?
3. **User-reported problem:** "This skill isn't working" — Can it diagnose from symptoms?
4. **Nearly perfect skill:** A skill that's actually good. Does it recognize this, or invent problems?
5. **Deeply broken skill:** A skill that needs complete rewrite. Does it hand off correctly?

#### Calibration Guidance

| Count | When to Use |
|-------|-------------|
| Fewer (3) | Skill has narrow, well-defined purpose with limited modes |
| Default (5) | Skill has typical scope |
| More (7-10) | Skill has broad scope, multiple distinct modes, or high stakes |

#### Key Insight: Scenario Variance Is Informative

If 4 scenarios show one pattern and 1 shows another, that's signal, not noise. The outlier reveals where the skill behaves differently. Investigate variance rather than averaging it out.

#### Criteria for Well-Chosen Scenarios

- Covers each distinct mode/use case of the skill
- Includes at least one happy-path scenario
- Includes at least one edge case that could reveal fragility
- Includes at least one scenario that tests the skill's boundaries

---

### Question 2: How Do You Avoid Overfitting to Test Scenarios?

**Initial position:** Ensure wide variety of test scenarios including edge cases.

**Conclusion:** Wide variety is necessary but not sufficient. Multiple mitigation strategies are needed.

#### Why Overfitting Occurs

- **Teaching to the test:** Same scenarios used across iterations; improvements address those specific cases
- **Scenario author bias:** Designer's mental model has blind spots
- **Root cause vs. symptom fixing:** Fixing specific cases rather than underlying issues
- **Missing modes:** Real-world failures come from unanticipated contexts

#### Mitigation Strategies

**1. Holdout scenarios**

| Set | Count | Purpose |
|-----|-------|---------|
| Development | 3-4 | Used during iterative improvement |
| Holdout | 1-2 | Only used for final validation |

If skill performs well on development but fails on holdout, that's evidence of overfitting.

**2. Scenario rotation**

Don't use exactly the same scenarios on every iteration:
- Keep scenario types consistent (happy path, edge case, etc.)
- Change specifics between iterations

**3. Adversarial scenario design**

Deliberately design scenarios that try to break the skill:
- What would a user do that wasn't anticipated?
- Where are the boundary conditions?

**4. Ground scenarios in real usage**

Base scenarios on actual past failures or observed usage patterns, not just theoretical edge cases.

**5. Fix root causes, not symptoms**

When a scenario reveals a failure, ask:
- Why did this fail? (root cause)
- Does the fix address the root cause, or just this specific case?

#### Key Insight: Generalization Is About Explanation

After improving, test not just "does it pass?" but "does the explanation suggest generalization?"

| Signal | Interpretation |
|--------|----------------|
| "It passes because we added instruction for this case" | Likely overfit |
| "It passes because we clarified the ambiguous section that caused multiple failures" | Likely generalizes |

---

### Question 3: What About Skills That Are Hard to Test?

**Initial position:** This is genuinely complex and requires deep thinking.

**Conclusion:** Different categories of difficulty require different mitigations. "Untestable" often reveals something about the skill itself.

#### Categories of Difficulty

**Category 1: Long-term or multi-session effects**

*Example:* Skills about building understanding over time.

*Why hard:* Subagents are isolated; can't observe multi-session accumulation.

*Mitigations:*
- Test building blocks that would lead to long-term effects
- Simulate multi-phase within one run
- Accept partial coverage; monitor in production

**Category 2: Subtle or qualitative effects**

*Example:* Skills about writing style or explanation quality.

*Why hard:* Success is qualitative; different observers judge differently.

*Mitigations:*
- Define observable markers for qualitative changes
- Use comparative judgment (better than baseline?)
- Accept some evaluator subjectivity with explicit criteria

**Category 3: Context-dependent effects**

*Example:* Skills that only matter in specific triggering contexts.

*Why hard:* Need to construct scenarios with the right context.

*Mitigations:*
- Mine real examples where context occurred
- Explicitly construct triggering conditions
- Verify trigger recognition (when it applies and when it doesn't)

**Category 4: Emergent or interaction effects**

*Example:* Skills that conflict with other skills when co-loaded.

*Why hard:* Combinatorial explosion of skill combinations.

*Mitigations:*
- Test common combinations
- Isolation testing (alone vs. with others)
- Accept some discovery in production

**Category 5: Rare trigger conditions**

*Example:* Skills about recovering from tool failures.

*Why hard:* Can't easily make tools fail on demand.

*Mitigations:*
- Mock the failure condition
- Use historical examples
- Verify skill doesn't break when condition doesn't occur

**Category 6: Negative effects (absence of behavior)**

*Example:* Skills that prevent undesirable behavior.

*Why hard:* Testing "doesn't do X" requires knowing Claude would otherwise do X.

*Mitigations:*
- Explicit baseline comparison
- Construct scenarios designed to elicit undesired behavior
- Look for reasoning evidence of skill influence

**Category 7: Meta-cognitive effects**

*Example:* Skills that change how Claude thinks, not just outputs.

*Why hard:* Internal reasoning isn't fully visible.

*Mitigations:*
- Examine reasoning traces
- Test downstream effects where thinking change should be visible
- Look for process markers (does Claude invoke the skill's concepts?)

**Category 8: High-variance domains**

*Example:* Skills for creative work with no single "right" answer.

*Why hard:* Can't define crisp success criteria.

*Mitigations:*
- Test process, not outcome
- Define success as element presence, not target matching
- Use relative evaluation (more likely to include desired elements?)

#### Higher-Level Strategies

**Strategy A: Decompose into testable components**

Test the mechanism even when you can't test the ultimate outcome:
- Does Claude invoke the sub-steps?
- Does Claude ask the prescribed questions?
- Does Claude structure approach correctly?

**Strategy B: Use proxy metrics**

Find measurable proxies for hard-to-measure effects:
- Instead of "is code robust," test "does it handle these error cases"
- Proxies are imperfect but provide signal

**Strategy C: Comparative over absolute**

If absolute success is undefined, relative improvement still matters:
- Is skill-assisted better than baseline?
- On what dimensions? By how much?

**Strategy D: Design for testability**

When creating or improving skills, ask: How would we test this?
- If no testable effects, question whether skill provides value
- Sometimes "hard to test" reveals "vaguely defined"

#### The Hard Question: Fundamentally Untestable Skills

Resist accepting "untestable" too quickly. Often it means:
- Haven't defined observable markers for the effect
- Haven't constructed the right triggering context
- The effect is vague or illusory

**Key insight:** If a skill's core purpose is untestable, how do we know it provides value? "Untestability" might reveal something about the skill, not just a testing limitation.

#### Proposed Stance for Improving-Skills

When a skill has hard-to-test aspects:

1. **Categorize the difficulty:** Which category? Different causes need different approaches.
2. **Apply relevant mitigations:** Use strategies appropriate to that category.
3. **Test what you can:** Partial coverage is better than no coverage.
4. **Flag what you can't:** Explicitly acknowledge which aspects weren't validated.
5. **Question untestable core purposes:** If the skill's primary effect can't be tested, push back and reconsider.

---

### Question 4: What's the Cost/Benefit?

**Initial position:** Running multiple subagents is always worth it.

**Conclusion:** Empirical assessment is always worth it because the comparison isn't "expensive empirical vs. cheap theoretical" — it's "expensive empirical vs. cheap theoretical that doesn't work in isolation."

**User's formulation:** "Empirical assessment should be the primary basis for evaluating quality and effectiveness. Theoretical analysis serves as a complementary, supporting assessment. In combination, they ensure comprehensive validation of skills."

#### The Costs

- **Token cost:** Multiple subagent runs consume tokens
- **Time cost:** Sequential runs take wall-clock time
- **Complexity cost:** More moving parts in the assessment process
- **Cognitive cost:** Synthesizing results across multiple runs

#### The Benefits

- **Ground truth:** Observe what actually happens, not what might happen
- **Actionable findings:** Observed failures point directly to what needs fixing
- **Confidence in improvements:** Evidence, not belief
- **Catches the unforeseen:** Reveals failure modes you wouldn't anticipate

#### Why "Always Worth It" Holds

The alternative (theoretical assessment alone) has a documented failure rate. If theoretical assessment produces low-quality findings and misses functional issues, its effective value is low regardless of its low cost.

The comparison isn't:
> Expensive empirical assessment vs. cheap theoretical assessment

It's:
> Expensive empirical assessment vs. cheap theoretical assessment that doesn't work in isolation

#### The Assessment Hierarchy

| Layer | Method | Role |
|-------|--------|------|
| **Primary** | Empirical (simulation-based) | Determines whether the skill achieves its purpose |
| **Supporting** | Theoretical (structural analysis) | Quick screening, remediation guidance, sanity checks |

Neither alone is sufficient:
- Empirical without theoretical misses obvious structural issues and lacks remediation vocabulary
- Theoretical without empirical produces the failure mode we started with — compliance without effectiveness

**Together:** Theoretical analysis catches surface issues and guides fixes. Empirical assessment validates that fixes actually work.

#### Calibration by Stakes

Even with "always empirical," investment can scale:

| Situation | Approach |
|-----------|----------|
| Minor refinement to well-tested skill | Fewer iterations, lighter validation |
| Major changes to important skill | Full scenario suite, multiple iterations |
| New skill with uncertain design | More exploratory scenarios |
| Skill with known failure history | Scenarios targeting past failures |

---

## Next Steps

- Complete discussion of Question 4 (cost/benefit)
- Design the new skill architecture incorporating simulation-based assessment
- Define specific scenario templates
- Define success thresholds
- Implement and test the revised skill

---

## Key Insights Summary

1. **Form vs. Function Conflation:** The current skill assesses structural compliance rather than functional effectiveness. A skill can score well and still fail at its purpose.

2. **The Measurement Problem:** Structural compliance is checkable; functional effectiveness requires empirical observation. The skill defaults to what it can check.

3. **Aspirational vs. Operational:** The skill asks the right questions about effectiveness but provides no method for answering them.

4. **The Discipline Skill Paradox:** If assessment is a checklist, Claude can complete the checklist without substantive analysis.

5. **Simulation-Based Assessment:** Replace theoretical assessment with empirical measurement using subagents to observe actual behavior.

6. **Quality Over Quantity for Scenarios:** 5 well-chosen scenarios that cover the behavior landscape matter more than volume.

7. **Avoiding Overfitting:** Holdout scenarios, rotation, adversarial design, and root-cause fixing all contribute to generalization.

8. **Hard-to-Test Skills:** Different categories require different mitigations. "Untestable" often reveals something about the skill itself.

9. **Purpose-First + Simulation-Based:** Purpose defines success criteria; simulation measures against them. The gap is the work.

10. **Assessment Hierarchy:** Empirical assessment is primary (determines effectiveness); theoretical analysis is supporting (screening, remediation, sanity checks). Neither alone is sufficient; together they provide comprehensive validation.
