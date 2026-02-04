# If we design the testing methodology first, we'll know what we're measuring — and that constrains how the skill should be structured.

Let me build on the foundation from the discussion document and get specific about scenario design.

---

Starting Point: What Scenarios Must Reveal

For improving-skills, the skill's purpose is: assess and improve existing skills through rigorous analysis.

That means scenarios must test:
┌───────────────────┬─────────────────────────────────────────────────────┐
│ Capability │ What We're Testing │
├───────────────────┼─────────────────────────────────────────────────────┤
│ Diagnosis │ Can it accurately identify what's wrong (or right)? │
├───────────────────┼─────────────────────────────────────────────────────┤
│ Treatment │ Can it effectively fix identified issues? │
├───────────────────┼─────────────────────────────────────────────────────┤
│ Restraint │ Does it know when NOT to change things? │
├───────────────────┼─────────────────────────────────────────────────────┤
│ Scope Recognition │ Does it recognize when to hand off vs. proceed? │
└───────────────────┴─────────────────────────────────────────────────────┘
The discussion document sketched 5 scenarios:

1. Clear issues (obvious problems)
2. Subtle issues (form vs. function trap)
3. User-reported problem (symptom-based diagnosis)
4. Nearly perfect skill (test restraint)
5. Deeply broken skill (test handoff recognition)

---

Design Question: What Makes a Scenario Effective?

For simulation-based assessment to work, each scenario needs:

1. Observable success criteria — What should the subagent do/produce if the skill works?
2. Distinguishable baseline — How would behavior differ without the skill?
3. Clear purpose mapping — Which capability is this testing?
4. Known ground truth — We need to know what "correct" looks like to judge

That last point is crucial. If we're testing whether the skill can diagnose issues, we need test skills where we know what the issues are. We're creating controlled
experiments, not exploring unknowns.

---

A Candidate Framework

Scenario structure:
Scenario Name: [descriptive name]
Purpose: [which capability being tested]
Test Skill: [the skill given to the subagent to "improve"]
Known Issues: [ground truth — what's actually wrong/right]
Success Criteria: [observable outcomes if skill works]
Baseline Expectation: [what happens without the skill]

Consolidated Scenario Information from Discussion Document

Direct Scenario Guidance

Lines 249-287: Question 1 — How Many Scenarios Are Enough?
┌───────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────┬─────────┐
│ Topic │ Content │ Lines │
├───────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Default count │ 5 scenarios as default │ 249 │
├───────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Core principle │ "the quality of scenario design matters more than the count" │ 251 │
├───────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Factors influencing count │ Coverage of purpose, edge cases vs typical usage, diminishing returns, signal vs noise │ 255-259 │
└───────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────┴─────────┘
Lines 261-276: Example Scenarios for improving-skills
┌─────┬───────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────┬───────┐
│ # │ Scenario │ What It Tests │ Lines │
├─────┼───────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────┤
│ 1 │ Clear issues │ "A skill with obvious structural problems. Can it diagnose them?" │ 263 │
├─────┼───────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────┤
│ 2 │ Subtle issues │ "A skill that looks fine structurally but doesn't achieve its purpose. Can it see past form to function?" │ 264 │
├─────┼───────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────┤
│ 3 │ User-reported problem │ "'This skill isn't working' — Can it diagnose from symptoms?" │ 265 │
├─────┼───────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────┤
│ 4 │ Nearly perfect skill │ "A skill that's actually good. Does it recognize this, or invent problems?" │ 266 │
├─────┼───────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────┤
│ 5 │ Deeply broken skill │ "A skill that needs complete rewrite. Does it hand off correctly?" │ 267 │
└─────┴───────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────┴───────┘
Lines 269-276: Calibration by Count
┌─────────────┬──────────────────────────────────────────────────────────────────┬───────┐
│ Count │ When to Use │ Lines │
├─────────────┼──────────────────────────────────────────────────────────────────┼───────┤
│ Fewer (3) │ "Skill has narrow, well-defined purpose with limited modes" │ 272 │
├─────────────┼──────────────────────────────────────────────────────────────────┼───────┤
│ Default (5) │ "Skill has typical scope" │ 273 │
├─────────────┼──────────────────────────────────────────────────────────────────┼───────┤
│ More (7-10) │ "Skill has broad scope, multiple distinct modes, or high stakes" │ 274 │
└─────────────┴──────────────────────────────────────────────────────────────────┴───────┘
Lines 278-279: Variance as Signal

"If 4 scenarios show one pattern and 1 shows another, that's signal, not noise. The outlier reveals where the skill behaves differently. Investigate variance rather
than averaging it out."

Lines 281-287: Criteria for Well-Chosen Scenarios

- Covers each distinct mode/use case of the skill
- Includes at least one happy-path scenario
- Includes at least one edge case that could reveal fragility
- Includes at least one scenario that tests the skill's boundaries

---

Overfitting Prevention (Affects Scenario Design)

Lines 289-345: Question 2 — How Do You Avoid Overfitting?
┌────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┬─────────┐
│ Topic │ Content │ Lines │
├────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Why overfitting occurs │ Teaching to test, scenario author bias, symptom vs root cause fixing, missing modes │ 297-301 │
└────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┴─────────┘
Lines 303-329: Mitigation Strategies
┌──────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────┬─────────┐
│ Strategy │ Description │ Lines │
├──────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Holdout scenarios │ Development set (3-4) vs holdout set (1-2); holdout only for final validation │ 305-313 │
├──────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Scenario rotation │ Keep types consistent, change specifics between iterations │ 315-319 │
├──────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Adversarial design │ "What would a user do that wasn't anticipated? Where are the boundary conditions?" │ 321-324 │
├──────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Ground in real usage │ "Base scenarios on actual past failures or observed usage patterns, not just theoretical edge cases" │ 326-329 │
├──────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼─────────┤
│ Fix root causes │ Ask "Why did this fail?" and "Does the fix address root cause or just this case?" │ 331-335 │
└──────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────┴─────────┘
Lines 337-345: Generalization Signals
┌──────────────────────────────────────────────────────────────────────────────────────┬────────────────────┬───────┐
│ Signal │ Interpretation │ Lines │
├──────────────────────────────────────────────────────────────────────────────────────┼────────────────────┼───────┤
│ "It passes because we added instruction for this case" │ Likely overfit │ 342 │
├──────────────────────────────────────────────────────────────────────────────────────┼────────────────────┼───────┤
│ "It passes because we clarified the ambiguous section that caused multiple failures" │ Likely generalizes │ 343 │
└──────────────────────────────────────────────────────────────────────────────────────┴────────────────────┴───────┘

---

Hard-to-Test Scenarios

Lines 347-488: Question 3 — What About Skills That Are Hard to Test?

Lines 355-441: Eight Categories of Testing Difficulty
┌──────────────────────────┬──────────────────────────────────┬────────────────────────────────┬─────────────────────────────────────────────────────────┬─────────┐
│ Category │ Example │ Why Hard │ Mitigations │ Lines │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 1. │ Building understanding over time │ Subagents are isolated │ Test building blocks; simulate multi-phase; accept │ 355-365 │
│ Long-term/multi-session │ │ │ partial coverage │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 2. Subtle/qualitative │ Writing style, explanation │ Success is qualitative │ Define observable markers; use comparative judgment │ 367-377 │
│ │ quality │ │ │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 3. Context-dependent │ Skills that only matter in │ Need to construct right │ Mine real examples; explicitly construct triggers; │ 379-389 │
│ │ specific contexts │ context │ verify trigger recognition │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 4. Emergent/interaction │ Skills that conflict when │ Combinatorial explosion │ Test common combinations; isolation testing │ 391-399 │
│ │ co-loaded │ │ │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 5. Rare triggers │ Recovering from tool failures │ Can't easily make tools fail │ Mock failure; use historical examples; verify doesn't │ 401-409 │
│ │ │ │ break when condition absent │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 6. Negative effects │ Preventing undesirable behavior │ Testing absence requires │ Explicit baseline comparison; construct scenarios to │ 411-420 │
│ │ │ knowing baseline │ elicit undesired behavior │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 7. Meta-cognitive │ Changes how Claude thinks │ Internal reasoning not fully │ Examine reasoning traces; test downstream effects; look │ 422-431 │
│ │ │ visible │ for process markers │ │
├──────────────────────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────┤
│ 8. High-variance │ Creative work, no single right │ Can't define crisp success │ Test process not outcome; element presence not target │ 433-441 │
│ │ answer │ │ matching │ │
└──────────────────────────┴──────────────────────────────────┴────────────────────────────────┴─────────────────────────────────────────────────────────┴─────────┘
Lines 443-467: Higher-Level Strategies
┌───────────────────────────────────────┬───────────────────────────────────────────────────────────────────┬─────────┐
│ Strategy │ Description │ Lines │
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┼─────────┤
│ A. Decompose into testable components │ Test mechanism even if can't test ultimate outcome │ 445-450 │
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┼─────────┤
│ B. Use proxy metrics │ Find measurable proxies for hard-to-measure effects │ 452-456 │
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┼─────────┤
│ C. Comparative over absolute │ If absolute success undefined, relative improvement still matters │ 458-463 │
├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────┼─────────┤
│ D. Design for testability │ Ask "how would we test this?" during skill creation │ 465-467 │
└───────────────────────────────────────┴───────────────────────────────────────────────────────────────────┴─────────┘
Lines 469-477: The Hard Question — Fundamentally Untestable

"Resist accepting 'untestable' too quickly. Often it means: Haven't defined observable markers for the effect, Haven't constructed the right triggering context, The
effect is vague or illusory"

"If a skill's core purpose is untestable, how do we know it provides value? 'Untestability' might reveal something about the skill, not just a testing limitation."
(Lines 476-477)

Lines 479-488: Proposed Stance When Hard to Test

1. Categorize the difficulty
2. Apply relevant mitigations
3. Test what you can
4. Flag what you can't
5. Question untestable core purposes

---

Scenario Role in the Mechanism

Lines 146-189: The Core Mechanism
┌──────────────────┬──────────────────────────────────────────────────────────┬─────────┐
│ Step │ Role of Scenarios │ Lines │
├──────────────────┼──────────────────────────────────────────────────────────┼─────────┤
│ Step 1: Baseline │ "Give it a task that the skill is designed to help with" │ 148-155 │
├──────────────────┼──────────────────────────────────────────────────────────┼─────────┤
│ Step 2: Measure │ "Same task, same conditions" │ 157-165 │
├──────────────────┼──────────────────────────────────────────────────────────┼─────────┤
│ Step 3: Delta │ Comparison reveals where skill helps/fails/hurts │ 167-173 │
└──────────────────┴──────────────────────────────────────────────────────────┴─────────┘
Lines 225-230: New Skill Structure (mentions scenarios)

"Scenario design: What tasks would reveal whether it achieves that?" (Line 227)

---

Cost/Benefit Affecting Scenario Investment

Lines 536-546: Calibration by Stakes
┌───────────────────────────────────────┬──────────────────────────────────────────┬───────┐
│ Situation │ Approach │ Lines │
├───────────────────────────────────────┼──────────────────────────────────────────┼───────┤
│ Minor refinement to well-tested skill │ Fewer iterations, lighter validation │ 541 │
├───────────────────────────────────────┼──────────────────────────────────────────┼───────┤
│ Major changes to important skill │ Full scenario suite, multiple iterations │ 542 │
├───────────────────────────────────────┼──────────────────────────────────────────┼───────┤
│ New skill with uncertain design │ More exploratory scenarios │ 543 │
├───────────────────────────────────────┼──────────────────────────────────────────┼───────┤
│ Skill with known failure history │ Scenarios targeting past failures │ 544 │
└───────────────────────────────────────┴──────────────────────────────────────────┴───────┘

---

Summary: Key Principles Extracted

1. Quality over quantity (Line 251)
2. Variance is signal (Lines 278-279)
3. Holdout scenarios prevent overfitting (Lines 305-313)
4. Ground in real usage, not just theory (Lines 326-329)
5. Root cause fixing generalizes; symptom fixing overfits (Lines 337-345)
6. "Untestable" often reveals skill problems (Lines 476-477)
7. Scale investment to stakes (Lines 536-546)

---

---

Gaps

1. Scenario Construction Method Unspecified

The document assumes scenarios exist but doesn't address how they're created:

- Synthetic test skills — We create skills with known issues, giving us ground truth
- Real existing skills — Authentic complexity, but do we know the "correct" diagnosis?
- Historical failures — Line 326-329 mentions "actual past failures" but doesn't operationalize this

The phrase "Known Issues: [ground truth — what's actually wrong/right]" in my earlier framework assumes we have ground truth. How do we establish it?

2. Baseline Behavior Is Assumed Meaningful

The mechanism (Lines 148-155) says "deploy a subagent without the skill" — but what does Claude do "naturally" when asked to improve a skill?

Possibilities:

- Has some built-in capability (comparison is: skill vs. native ability)
- Does something mediocre (comparison is: skill vs. mediocre)
- Does essentially nothing useful (comparison shows skill does something, not that it's good)

If baseline is near-zero, the delta only proves the skill has an effect, not that the effect is correct.

3. Success Criteria Remain Abstract

Line 263: "Can it diagnose them?" — but what counts as correct diagnosis?
┌───────────────┬───────────────────────────────────────────────┐
│ Dimension │ Not Addressed │
├───────────────┼───────────────────────────────────────────────┤
│ Completeness │ Must identify all issues? Most important? │
├───────────────┼───────────────────────────────────────────────┤
│ Precision │ False positives allowed? How many? │
├───────────────┼───────────────────────────────────────────────┤
│ Priority │ Must rank correctly? │
├───────────────┼───────────────────────────────────────────────┤
│ Actionability │ Must the diagnosis lead to correct treatment? │
└───────────────┴───────────────────────────────────────────────┘ 4. The Evaluator Problem

Who judges whether the subagent's output is correct?

- Human evaluator? (Doesn't scale; introduces subjectivity)
- Another Claude instance? (Could fall into same form-over-function trap)
- Automated checks? (What would these look like?)

The document critiques assessment-by-checklist but doesn't specify what replaces it when judging scenario outcomes.

5. The "Nearly Perfect Skill" Circularity (Scenario 4)

Testing restraint requires a skill that's "actually good." But how do we know it's good?

- If we judge by structure → form-over-function trap
- If we judge by effectiveness → we need prior empirical evidence
- If we don't have either → we're guessing

This scenario's ground truth depends on solving the problem the skill is meant to solve.

6. Iteration Mechanics Unspecified

Line 185-189 says "Iterate until threshold" but:

- Same scenario instances or fresh ones each iteration?
- Same subagent or fresh context?
- How do we prevent tuning to specific instances vs. scenario types?

This connects to the overfitting concern but isn't resolved by holdout alone.

7. Handoff Scenario Complexity (Scenario 5)

Testing "Does it hand off correctly?" requires:

- Defining what "deeply broken" means (threshold)
- The improving-skills subagent having awareness of creating-skills
- Judging whether handoff was appropriate, not just whether it happened

This tests a transition decision, not an outcome. Different evaluation structure needed.

---

Nuances

1. Baseline Comparison vs. Absolute Standard

The document frames everything as delta-from-baseline (Lines 167-173). But:

- Delta positive could mean: skill helps, OR baseline was artificially bad
- Delta neutral could mean: skill useless, OR skill compensates for something baseline already did differently

Do we also need an absolute standard? "Skill-assisted behavior meets these criteria" regardless of baseline?

2. Tension: "Ground in Real Usage" vs. "Holdout Scenarios"

- Line 326-329: Base scenarios on actual past failures
- Lines 305-313: Reserve holdout scenarios for final validation

If real failures go into development set → holdout becomes synthetic (less valid)
If real failures reserved for holdout → development scenarios are theoretical (the problem we're avoiding)

Limited real examples create allocation tension.

3. Variance Interpretation Ambiguity

Lines 278-279: "If 4 scenarios show one pattern and 1 shows another, that's signal"

But variance could indicate:

- Informative — The outlier reveals where skill behaves differently (intended interpretation)
- Problematic — The skill is inconsistent/unreliable (bad sign)

How do we distinguish "reveals different mode" from "skill is flaky"?

4. Scenario Independence vs. Skill Adaptation

Should the skill being tested adapt based on earlier scenarios in a run? Or should each scenario be independent?

- Independent: Cleaner measurement, but doesn't test learning/adaptation
- Sequential: More realistic, but confounds what's being measured

5. Meta-Evaluation Problem

We're designing scenarios to test a skill that assesses skills. But how do we assess whether our scenarios are good?

The same trap applies: scenarios could look right structurally but fail to reveal skill effectiveness. We need scenarios for our scenarios? Or acceptance that this
is where human judgment enters?

6. The "Didn't Test" Negative Space

The document focuses on what scenarios test. What can't scenarios test?

- Behaviors that only emerge in extended real usage
- Interactions with user conversation dynamics
- Adaptation over multiple invocations
- Effects that manifest downstream (skill improves X, but X's effect only visible later)

What's the acknowledged coverage gap?

---

Summary: The Deepest Gap

The document establishes what to compare (baseline vs. skill-assisted) but underspecifies how to judge correctness of the skill-assisted output.

For simulation-based assessment to work, we need an oracle — something that tells us whether the subagent's behavior was right. The document assumes we'll know
correct behavior when we see it, but that's the judgment the current skill fails at.

This suggests: scenario design must include explicit correctness criteria that don't reduce to structural compliance. That's the hard problem the document identifies
but doesn't solve.

Let me trace the dependencies carefully.

---

Dependency Analysis

What we want to test: Does improving-skills make skills better?

To answer that, we need: A way to determine if a skill is "better" after improvement

To determine "better," we need: A way to measure skill effectiveness

To measure effectiveness, we need: To test whether the skill achieves its purpose

To test purpose achievement, we need: Scenarios for the target skill (not improving-skills)

---

The Recursive Structure

Here's what I see:

┌─────────────────────────────────────────────────────────────┐
│ Testing improving-skills │
│ │
│ Scenario: "Here's a skill. Improve it." │
│ │
│ To judge success, we must answer: │
│ "Is the improved skill more effective than before?" │
│ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Testing the target skill (before and after) │ │
│ │ │ │
│ │ Requires: scenarios for the target skill │ │
│ │ Requires: evaluation criteria for target skill │ │
│ │ Requires: baseline vs skill-assisted comparison │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

We cannot test whether improving-skills improves skills without being able to test whether skills work.

This is inescapable. The purpose of improving-skills is to increase effectiveness. "Increased effectiveness" requires measuring effectiveness. Measuring
effectiveness requires testing the skill.

---

The Foundational Dependency

Everything depends on:

A method for testing whether any given skill achieves its purpose.

This is the oracle. This is where ground truth comes from. Without this capability, we're stuck doing form-over-function assessment — just at the meta level instead
of the object level.

The discussion document describes simulation-based assessment as the solution. But it describes it as something improving-skills is tested with, not as something
improving-skills must perform.

---

The Implication

For improving-skills to actually improve skills (not just assess their structure), it must:

1. Extract the target skill's purpose — What behavior change does it intend?
2. Design scenarios for that purpose — What tasks would reveal whether it works?
3. Run baseline measurement — Subagent without skill, observe behavior
4. Run skill-assisted measurement — Subagent with skill, same task
5. Evaluate delta — Did behavior change in the intended direction?
6. Identify gaps — Where did it fail to achieve purpose?
7. Propose fixes — Address the observed failures
8. Re-test — Verify the fixes work

This is the simulation-based methodology applied by improving-skills to target skills.

---

Where to Start

Not: "What scenarios test improving-skills?"

But: "How does improving-skills test target skills?"

The inner loop must be defined before the outer loop. If we don't know how improving-skills determines whether a skill is effective, we can't design scenarios to
test whether improving-skills does this correctly.

---

The Hard Question

This raises a fundamental design choice:

Option A: improving-skills performs simulation-based assessment on target skills

- improving-skills spawns subagents to test the target skill
- It measures baseline vs skill-assisted behavior
- It identifies functional gaps
- It proposes fixes based on observed failures
- It re-tests to verify

This is principled but expensive and complex. It also means improving-skills needs to design scenarios for arbitrary target skills — which is itself a hard problem.

Option B: improving-skills relies on pre-existing effectiveness data

- Target skills come with their own test suites / scenario definitions
- improving-skills uses those to measure before/after
- Reduces the problem: improving-skills doesn't design scenarios, just runs them

This is simpler but requires target skills to already have scenario definitions. What about skills that don't?

Option C: improving-skills uses diagnosis-only (no treatment verification)

- Test only whether improving-skills correctly identifies issues
- Don't test whether proposed fixes actually work
- Ground truth comes from planted issues or human-validated issue lists

This is tractable but incomplete. We test diagnosis accuracy but not treatment effectiveness. We could end up with a skill that correctly identifies problems but
proposes bad fixes.

---

My Assessment

Option A is the principled approach — it's what the discussion document implies. But it requires solving "how to design scenarios for arbitrary skills," which is
hard.

Option C is a valid starting point — we can test diagnosis accuracy with planted issues, establishing whether improving-skills can see past form to function.
Treatment verification can come later.

The question:: Do we need improving-skills to test target skills autonomously (Option A), or is there a scoped version that's tractable now (Option C) while
building toward the full capability?

Option A is the goal. Let me break down what Option A actually requires.

---

Option A: Full Simulation-Based Assessment

improving-skills must perform this loop for each target skill:

1. Extract purpose → What is this skill trying to achieve?
2. Design scenarios → What tasks would reveal whether it achieves that?
3. Run baseline → Subagent without skill, observe behavior
4. Run test → Subagent with skill, same task, observe behavior
5. Evaluate delta → Did behavior change in the intended direction?
6. Identify gaps → Where did it fail? Why?
7. Propose fixes → What changes would address the failures?
8. Re-test → Verify fixes work, iterate until threshold

Let me explore each component.

---

1. Purpose Extraction

What it must do: Determine what the target skill is trying to achieve — not its structure, its intent.

Sources of purpose:

- Skill's stated description/name
- Skill's trigger phrases (when does it activate?)
- Skill's instructions (what does it tell Claude to do?)
- Implicit from skill type (discipline skill vs. knowledge skill vs. workflow skill)

Challenges:
┌───────────────────────────┬──────────────────────────────────────────────────────────┐
│ Challenge │ Why It's Hard │
├───────────────────────────┼──────────────────────────────────────────────────────────┤
│ Purpose not stated │ Many skills assume purpose is obvious │
├───────────────────────────┼──────────────────────────────────────────────────────────┤
│ Multiple purposes │ Primary vs secondary vs emergent │
├───────────────────────────┼──────────────────────────────────────────────────────────┤
│ Purpose vs implementation │ What skill says vs what it actually does │
├───────────────────────────┼──────────────────────────────────────────────────────────┤
│ Abstract purposes │ "Improve code quality" — what does that mean concretely? │
└───────────────────────────┴──────────────────────────────────────────────────────────┘
What needs definition:

- Method for extracting/inferring purpose from skill content
- How to handle unclear or missing purpose statements
- How to operationalize abstract purposes into testable claims

---

2. Scenario Design (The Hard Problem)

What it must do: Create tasks that would reveal whether the skill achieves its purpose.

Requirements for a good scenario:

- Exercises the behavior the skill is meant to influence
- Has distinguishable baseline behavior (skill must make a visible difference)
- Has observable success criteria (we can tell if it worked)
- Represents realistic usage (not artificial edge cases only)

Approaches to scenario generation:
┌────────────────┬──────────────────────────────────────────┬───────────────────────────────────┐
│ Approach │ Method │ Limitation │
├────────────────┼──────────────────────────────────────────┼───────────────────────────────────┤
│ Templated │ Generic templates instantiated per skill │ May be too generic │
├────────────────┼──────────────────────────────────────────┼───────────────────────────────────┤
│ Purpose-driven │ Map purpose types to scenario structures │ Purpose classification is hard │
├────────────────┼──────────────────────────────────────────┼───────────────────────────────────┤
│ Example-seeded │ Derive from skill's own examples │ Not all skills have examples │
├────────────────┼──────────────────────────────────────────┼───────────────────────────────────┤
│ Adversarial │ Try to break the skill │ May not represent realistic usage │
└────────────────┴──────────────────────────────────────────┴───────────────────────────────────┘
The core difficulty:

Designing good scenarios requires understanding:

- The skill's domain
- What tasks would trigger it
- What "success" looks like in that domain
- Where failure modes lurk

This is creative, domain-specific work. Can we make it systematic?

Possible structure:

For any skill, ask:

1. What situation triggers this skill? → Scenario context
2. What should Claude do differently with the skill? → Expected behavior delta
3. What would Claude do without the skill? → Baseline expectation
4. How would we recognize success? → Observable markers

This gives us scenario components, but filling them in still requires judgment.

---

3 & 4. Subagent Runs (Baseline and Test)

What it must do: Run controlled experiments — same task, different skill presence.

Baseline configuration:

- System prompt: Standard Claude behavior
- Tools: Whatever the scenario requires
- Context: The scenario task
- Skill: Absent

Test configuration:

- System prompt: Standard Claude behavior + target skill loaded
- Tools: Same as baseline
- Context: Same scenario task
- Skill: Present

Challenges:
┌───────────────────────┬─────────────────────────────────────────────────────────────┐
│ Challenge │ Description │
├───────────────────────┼─────────────────────────────────────────────────────────────┤
│ Skill injection │ How do we load a skill into a subagent's context? │
├───────────────────────┼─────────────────────────────────────────────────────────────┤
│ Controlled conditions │ Ensuring only skill presence differs │
├───────────────────────┼─────────────────────────────────────────────────────────────┤
│ Observation capture │ What exactly do we record from each run? │
├───────────────────────┼─────────────────────────────────────────────────────────────┤
│ Variance │ Same task might produce different outputs due to randomness │
└───────────────────────┴─────────────────────────────────────────────────────────────┘
What to observe:

- Final output (what did the subagent produce?)
- Process markers (did it mention/follow skill concepts?)
- Reasoning trace (if visible)
- Tool usage patterns
- Where it got stuck or made choices

---

5. Delta Evaluation (The Oracle Problem)

What it must do: Determine whether the skill-assisted behavior is "correct" — whether the delta is in the intended direction.

This is the crux. Without a reliable oracle, we can't judge improvement.

Oracle options:
┌─────────────────────────┬─────────────────────────────────────────────────┬──────────────────────────────────────────────┐
│ Oracle │ Pro │ Con │
├─────────────────────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ Human evaluator │ Can judge qualitative outcomes │ Doesn't scale, subjective │
├─────────────────────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ Claude-as-evaluator │ Scalable │ Could fall into same form-over-function trap │
├─────────────────────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ Automated checks │ Objective, repeatable │ Only works for checkable criteria │
├─────────────────────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ Criteria-based + Claude │ Structured evaluation against explicit criteria │ Criteria could be wrong │
└─────────────────────────┴─────────────────────────────────────────────────┴──────────────────────────────────────────────┘
Proposed approach: Criteria-based evaluation with Claude-as-evaluator

For each scenario, improving-skills defines:

- What the skill-assisted subagent should do (expected behavior)
- Observable markers of success
- Observable markers of failure
- Dimensions to compare (output quality, process adherence, etc.)

A separate evaluator (Claude instance) judges against these criteria.

Risk: improving-skills might define bad criteria (form over function again).

Mitigation: Criteria are explicit and auditable. We can inspect them and challenge whether they actually measure effectiveness.

---

6. Gap Analysis

What it must do: Identify where the skill failed and why.

Gap types:
┌─────────────────────┬────────────────────────────────────────────────────┐
│ Gap │ Description │
├─────────────────────┼────────────────────────────────────────────────────┤
│ No effect │ Skill present but behavior unchanged from baseline │
├─────────────────────┼────────────────────────────────────────────────────┤
│ Wrong effect │ Behavior changed but not in intended direction │
├─────────────────────┼────────────────────────────────────────────────────┤
│ Partial effect │ Some intended changes, others missing │
├─────────────────────┼────────────────────────────────────────────────────┤
│ Negative effect │ Skill made behavior worse │
├─────────────────────┼────────────────────────────────────────────────────┤
│ Inconsistent effect │ Works in some runs, not others │
└─────────────────────┴────────────────────────────────────────────────────┘
Root cause categories:
┌────────────────────────────┬─────────────────────────────────────────────────────────────────┐
│ Cause │ Description │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Instruction ignored │ Subagent didn't follow skill instructions │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Instruction misinterpreted │ Subagent followed instructions but understood them wrong │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Instruction unclear │ Instructions are ambiguous │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Assumption failed │ Skill assumes something that isn't true │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Conflict │ Skill conflicts with other guidance or Claude's defaults │
├────────────────────────────┼─────────────────────────────────────────────────────────────────┤
│ Scope mismatch │ Skill doesn't apply to this scenario (shouldn't have triggered) │
└────────────────────────────┴─────────────────────────────────────────────────────────────────┘
What needs definition:

- How to map observed failures to root causes
- How to distinguish "skill problem" from "scenario problem"
- How to prioritize gaps (which to fix first)

---

7. Fix Generation

What it must do: Propose specific changes to the skill that address observed gaps.

Fix types:
┌─────────────────────────────────────────────────────────────────┐
│ Gap → Fix │
├─────────────────────────────────────────────────────────────────┤
│ Instruction ignored → Make more salient, add enforcement │
├─────────────────────────────────────────────────────────────────┤
│ Instruction misinterpreted → Clarify wording, add examples │
├─────────────────────────────────────────────────────────────────┤
│ Instruction unclear → Restructure, remove ambiguity │
├─────────────────────────────────────────────────────────────────┤
│ Assumption failed → Remove assumption or add precondition check │
├─────────────────────────────────────────────────────────────────┤
│ Conflict → Resolve priority, add exception handling │
├─────────────────────────────────────────────────────────────────┤
│ Scope mismatch → Adjust trigger conditions │
└─────────────────────────────────────────────────────────────────┘
Challenge: Multiple possible fixes for same gap. How to choose?

Approach: Prefer fixes that address root cause, not symptom. (Lines 331-335 from discussion document)

---

8. Re-test and Iteration

What it must do: Verify fixes work, iterate until convergence.

Questions:
┌──────────────────────────────┬───────────────────────────────────────────────────────────┐
│ Question │ Options │
├──────────────────────────────┼───────────────────────────────────────────────────────────┤
│ Same scenarios or different? │ Same risks overfitting; different loses comparability │
├──────────────────────────────┼───────────────────────────────────────────────────────────┤
│ How many iterations? │ Until threshold met, or cap at N │
├──────────────────────────────┼───────────────────────────────────────────────────────────┤
│ What's "good enough"? │ All scenarios pass? X% pass? Key scenarios pass? │
├──────────────────────────────┼───────────────────────────────────────────────────────────┤
│ Regression testing? │ Check that fixes don't break previously passing scenarios │
└──────────────────────────────┴───────────────────────────────────────────────────────────┘
Proposed approach:

- Re-run same scenarios to verify fix effectiveness
- Use holdout scenarios (not used during iteration) for final validation
- Cap iterations (e.g., 3-5) to prevent infinite loops
- Define success threshold based on scenario priority

---

Architecture Question

This is complex. Is it a skill or a system?

A skill: Instructions that guide Claude's behavior in a single context

A system: Orchestrated process with multiple components, potentially multiple agents

Given the complexity, I see improving-skills as: a skill that orchestrates subagents for specific tasks

improving-skills (orchestrator)
│
├── Purpose extraction (could be inline or subagent)
├── Scenario generation (likely subagent - creative task)
├── Baseline runner (subagent by definition)
├── Test runner (subagent by definition)
├── Delta evaluator (likely subagent - judgment task)
├── Gap analyzer (could be inline or subagent)
├── Fix generator (could be inline)
└── Iteration controller (inline - the main loop)

The main skill provides methodology and flow control. Subagents handle tasks requiring isolated context.

---

Cost Reality

For one target skill improvement:
┌─────────────────────┬──────────────────────┐
│ Component │ Runs │
├─────────────────────┼──────────────────────┤
│ Scenario generation │ 1 │
├─────────────────────┼──────────────────────┤
│ Baseline runs │ 5 (one per scenario) │
├─────────────────────┼──────────────────────┤
│ Test runs │ 5 (one per scenario) │
├─────────────────────┼──────────────────────┤
│ Evaluation runs │ 5 (one per scenario) │
├─────────────────────┼──────────────────────┤
│ Per iteration │ 16 │
├─────────────────────┼──────────────────────┤
│ 3 iterations │ ~48 subagent runs │
└─────────────────────┴──────────────────────┘
Plus overhead for gap analysis, fix generation, coordination.

This is expensive. The discussion document argues it's worth it (Lines 493-520): expensive-but-works beats cheap-but-broken.

---

The Bottleneck: Scenario Generation

Looking at all components, scenario generation is the hardest and least specified.

- Purpose extraction is constrained by the skill's content
- Subagent runs are mechanical once scenarios exist
- Evaluation is structured if criteria are defined
- Gap analysis and fix generation are diagnostic

But scenario generation requires:

- Understanding arbitrary skill domains
- Creative construction of revealing tasks
- Defining success criteria for those tasks

This is where the "can we make this work for arbitrary skills" question is sharpest.

---

Question for You

Given this breakdown, where do you want to focus?

Option A1: Dive deeper into scenario generation — how can improving-skills design good scenarios for arbitrary skills?

Option A2: Dive deeper into evaluation — how can we reliably judge whether skill-assisted behavior is "correct"?

Option A3: Dive deeper into the orchestration — how do the components fit together and communicate?

Let me explore scenario generation in depth - this is the bottleneck

---

The Core Challenge

For arbitrary skills, we need to:

1. Understand what the skill is trying to do
2. Imagine situations where that purpose would be tested
3. Define what success looks like in those situations
4. Construct tasks that create those situations

This requires both understanding and creativity. Can we make it systematic?

---

Approach 1: Purpose Classification → Scenario Templates

Hypothesis: Skills have a finite number of "purpose types." If we classify purpose, we can use templates.
┌─────────────────────┬───────────────────────────────────┬─────────────────────────────────────────────────┬──────────────────────┐
│ Purpose Type │ What It Does │ Scenario Structure │ Success Marker │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Prevent X │ Stops Claude from doing something │ Situation where Claude would naturally do X │ X does not occur │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Ensure Y │ Makes Claude do something │ Situation where Y is relevant but not automatic │ Y occurs │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Guide process Z │ Provides methodology │ Task requiring Z │ Process followed │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Provide knowledge K │ Gives information │ Task where K helps │ K used correctly │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Modify style S │ Changes communication │ Task with output │ Output matches S │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Set criteria C │ Guides choices │ Task with multiple valid approaches │ Choice aligns with C │
├─────────────────────┼───────────────────────────────────┼─────────────────────────────────────────────────┼──────────────────────┤
│ Define boundaries B │ Constrains scope │ Task that could cross boundaries │ Boundaries respected │
└─────────────────────┴───────────────────────────────────┴─────────────────────────────────────────────────┴──────────────────────┘
Example derivation:

Skill: "Always run tests before claiming done"

- Purpose type: Ensure Y (Y = run tests)
- Scenario structure: Task where tests exist, completion is possible
- Success marker: Tests executed before "done" claim

Challenge: Most skills combine multiple purpose types.

Mitigation: Decompose into constituent purposes, generate scenarios for each.

---

Approach 2: Instruction-Driven Scenario Generation

Hypothesis: The skill's own instructions tell us what to test.

For each instruction:

- What situation makes this instruction relevant?
- What would happen if followed vs. ignored?

Example:

Instruction: "Before editing any file, read it first."
┌──────────────────────┬───────────────────────────────────┐
│ Element │ Value │
├──────────────────────┼───────────────────────────────────┤
│ Situation │ User asks to edit a file │
├──────────────────────┼───────────────────────────────────┤
│ Baseline expectation │ Claude might edit without reading │
├──────────────────────┼───────────────────────────────────┤
│ Test expectation │ Claude reads before editing │
├──────────────────────┼───────────────────────────────────┤
│ Observable marker │ Read tool called before Edit tool │
└──────────────────────┴───────────────────────────────────┘
Extraction heuristics:
┌────────────────────────┬────────────────────────────────────────────────┐
│ Instruction Pattern │ Scenario Implication │
├────────────────────────┼────────────────────────────────────────────────┤
│ "Always X" │ Scenario where X is optional but should happen │
├────────────────────────┼────────────────────────────────────────────────┤
│ "Never Y" │ Scenario where Y is tempting but forbidden │
├────────────────────────┼────────────────────────────────────────────────┤
│ "When A, do B" │ Scenario where A occurs │
├────────────────────────┼────────────────────────────────────────────────┤
│ "If A, then B, else C" │ Scenarios for both branches │
├────────────────────────┼────────────────────────────────────────────────┤
│ "Prefer X over Y" │ Scenario where both X and Y are viable │
└────────────────────────┴────────────────────────────────────────────────┘
Challenge: Not all instructions are actionable. "Be thorough" doesn't map to a specific scenario.

Mitigation: Filter for instructions with observable behavioral implications.

---

Approach 3: Trigger-Based Scenario Generation

Hypothesis: Skills define when they activate. Triggers define scenario contexts.

Skill trigger: "Use when user asks to improve a skill"
Scenario context: User message "Please improve this skill: [content]"

Skill trigger: "Activates when editing files in .claude/"
Scenario context: Task requiring edits to .claude/ files

This ensures scenarios actually activate the skill.

Challenge: Triggers may be vague. "Use for debugging tasks" — what counts?

Mitigation: Combine with purpose classification. Trigger → context; purpose → structure.

---

Approach 4: Example Extraction and Variation

Hypothesis: Skill examples are scenario seeds. Variations test generalization.

Skill example: "When user says 'fix this bug', use systematic debugging"

Derived scenarios:

- Exact: "Fix this bug"
- Variation: "This is broken, can you help?"
- Synonym: "Debug this issue"
- Symptom: "The login isn't working"

This tests whether the skill generalizes beyond literal triggers.

Challenge: Not all skills have examples. Coverage may be limited.

Mitigation: Supplementary source, not primary.

---

Approach 5: Adversarial Scenario Generation

Hypothesis: Edge cases reveal gaps. Deliberately try to break the skill.

Adversarial questions:
┌────────────────────────────────────────────┬────────────────────────────┐
│ Question │ What It Reveals │
├────────────────────────────────────────────┼────────────────────────────┤
│ What if [precondition] doesn't hold? │ Assumption failures │
├────────────────────────────────────────────┼────────────────────────────┤
│ What if user explicitly contradicts? │ Priority/override handling │
├────────────────────────────────────────────┼────────────────────────────┤
│ What if task is at skill's scope boundary? │ Scope recognition │
├────────────────────────────────────────────┼────────────────────────────┤
│ What if multiple skills conflict? │ Conflict resolution │
├────────────────────────────────────────────┼────────────────────────────┤
│ What if skill's guidance is impossible? │ Failure handling │
└────────────────────────────────────────────┴────────────────────────────┘
Example for "always run tests before done":
┌──────────────────────────────────────┬───────────────────────┐
│ Adversarial Scenario │ What It Tests │
├──────────────────────────────────────┼───────────────────────┤
│ No tests exist │ Precondition failure │
├──────────────────────────────────────┼───────────────────────┤
│ Tests are broken │ Impossible to satisfy │
├──────────────────────────────────────┼───────────────────────┤
│ User says "skip tests" │ Override handling │
├──────────────────────────────────────┼───────────────────────┤
│ Task is exploratory, not "done-able" │ Scope boundary │
└──────────────────────────────────────┴───────────────────────┘
Challenge: Requires creative adversarial thinking.

Mitigation: Template the adversarial questions so they can be applied mechanically.

---

Synthesis: Hybrid Scenario Generation

No single approach is sufficient. Combine them:

Input: Target skill

Step 1: Classify purpose type(s)
→ Purpose categories (prevent, ensure, guide, provide, modify, set, define)

Step 2: Extract actionable instructions
→ Specific behaviors skill requires

Step 3: Analyze trigger conditions
→ Situations where skill should activate

Step 4: Extract and vary examples
→ Example-based scenario seeds

Step 5: Generate adversarial probes
→ Edge case and boundary scenarios

Step 6: Assemble scenario suite
→ Combine, deduplicate, prioritize
→ Target: 5-7 scenarios covering: - At least one happy path - At least one edge case - At least one adversarial case - Coverage of main purposes

---

Success Criteria Derivation

Each scenario needs success criteria. Can these be derived systematically?
┌─────────────────────┬────────────────────────┬────────────────────────┬────────────────────────────────────┐
│ Purpose Type │ Success │ Failure │ Observable │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Prevent X │ X absent │ X present │ Action/output presence │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Ensure Y │ Y present │ Y absent │ Action/output presence │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Guide process Z │ Z followed │ Z ignored │ Action sequence, reasoning markers │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Provide knowledge K │ K used correctly │ K ignored/misused │ Content accuracy │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Modify style S │ Output matches S │ Output doesn't match S │ Style markers │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Set criteria C │ Decision aligns with C │ Decision contradicts C │ Choice + reasoning │
├─────────────────────┼────────────────────────┼────────────────────────┼────────────────────────────────────┤
│ Define boundaries B │ B respected │ B violated │ Scope of actions │
└─────────────────────┴────────────────────────┴────────────────────────┴────────────────────────────────────┘
Key insight: Success criteria can be derived from purpose type + specific skill content.

For "Ensure Y" where Y = "run tests before done":

- Success: Test execution observed before completion claim
- Failure: Completion claimed without test execution
- Observable: Tool call sequence (test tool before "done" message)

---

Worked Example: writing-principles Skill

Let me apply the framework to a real skill from this repo.

Step 1: Purpose classification

- Guide process (writing instruction documents)
- Set criteria (14 numbered principles)
- Define boundaries (applies to specific file paths)

Step 2: Actionable instructions

- Principle 1: Replace vague language with concrete values
- Principle 2: Explain jargon on first use
- Principle 3: Include examples for rules
- ... (principles 4-14)
- Use self-check procedure before finalizing
- Apply priority hierarchy when principles conflict

Step 3: Trigger conditions

- Editing **/skills/**/\*.md
- Editing \*_/agents/_.md
- Editing \*\*/CLAUDE.md

Step 4: Example extraction

- "Vague pronouns, hedge words" as red flag → scenario where these are tempting
- "Rules without demonstration" → scenario needing examples

Step 5: Adversarial probes

- User says "just draft quick notes, don't polish"
- Two principles conflict (specific vs. economy)
- File is instruction-like but outside trigger paths
- Document already follows principles well

Step 6: Assembled suite
┌─────┬──────────────────────┬────────────────────────────────────────┬───────────────────────────┬─────────────────────────────────────┐
│ # │ Type │ Scenario │ Tests │ Success Criteria │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 1 │ Happy path │ "Write SKILL.md for code-review skill" │ Full workflow │ Follows principles, uses self-check │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 2 │ Specific instruction │ Draft contains "do it properly" │ Principle 1 (specificity) │ Flags/fixes vague language │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 3 │ Boundary │ Edit README.md (not in trigger path) │ Scope recognition │ Does NOT apply writing-principles │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 4 │ Adversarial │ User: "Quick draft, don't polish" │ Override handling │ Appropriate adaptation │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 5 │ Conflict │ Verbose specificity vs. economy │ Priority hierarchy │ Resolves per hierarchy │
├─────┼──────────────────────┼────────────────────────────────────────┼───────────────────────────┼─────────────────────────────────────┤
│ 6 │ Already good │ Well-written instruction doc │ Restraint │ Recognizes quality, minimal changes │
└─────┴──────────────────────┴────────────────────────────────────────┴───────────────────────────┴─────────────────────────────────────┘

---

Remaining Hard Problems

1. Compound Purposes

Skills with multiple interacting purposes. How do they combine?

Possible approach: Generate scenarios for each purpose separately, then add scenarios that test interactions.

2. Qualitative Success

"Improve code quality" — how do we operationalize?

Possible approach: Decompose into observable markers. Quality = specific, documented, tested, etc. Test the markers, not the abstraction.

3. Context Dependency

Success varies by situation. "Do the right thing" isn't testable.

Possible approach: Skills with undefined success criteria may be poorly specified. This is signal, not just a testing limitation.

4. Emergent Behavior

Skills that change thinking without direct markers.

Possible approach: Test downstream effects. If skill changes thinking, that should manifest somewhere observable. If it doesn't manifest, how do we know it's
working?

---

The Key Uncertainty

This framework produces scenarios, but does it produce good scenarios?

How do we know if:

- Scenarios actually reveal skill effectiveness (not just activity)?
- Success criteria measure function (not just form)?
- Coverage is adequate (not missing critical cases)?

The meta-evaluation problem surfaces again. We can systematize scenario generation, but judging scenario quality still requires judgment.

---

Questions

Does this hybrid framework address the scenario generation bottleneck? Specifically:

1. Coverage: Do the five approaches (purpose, instruction, trigger, example, adversarial) cover the space adequately? What's missing?
2. Derivation: Does "success criteria from purpose type" avoid the form-over-function trap, or does it recreate it at a different level?
3. Tractability: Is this systematic enough that improving-skills could execute it, or does it require too much judgment?

Does @docs/references/skills-guide.md provide any valuable insights?

Yes. Several insights directly relevant to scenario generation.

---

Insight 1: Well-Designed Skills Define Their Own Scenarios

Lines 259-282: Start with Use Cases

The guide says skills should START with 2-3 concrete use cases:

Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:

1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates
   Result: Fully planned sprint with tasks created

This IS a scenario template. A use case contains:

- Trigger (scenario context)
- Steps (expected behavior)
- Result (success criteria)

Implication: If a skill was properly designed, it comes with scenario seeds built in. If it doesn't have use cases, that's both a design gap AND a signal about the
skill's quality.

---

Insight 2: Skill Types Map to Expected Behaviors

Lines 307-373: Common Skill Types

Each type has defined "Key techniques":
┌────────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
│ Type │ Key Techniques (expected behaviors) │
├────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Discipline │ Phase gates, evidence requirements, anti-pattern tables, red flag lists, blocking language │
├────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Technique │ Step-by-step workflows, decision trees, worked examples, quality criteria, iteration patterns │
├────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Pattern │ Template structures, style guides, anti-patterns, variation catalogs, decision tables │
├────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Reference │ Search integration, query guidance, quick-reference tables, freshness indicators │
└────────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘
Implication: If a skill claims to be type X, we can derive expected behaviors from the type definition. A "Discipline" skill that lacks phase gates or evidence
requirements has a structural gap that predicts functional failure.

This gives us a type-based scenario generator: given skill type, test for presence and effectiveness of type-appropriate techniques.

---

Insight 3: Troubleshooting = Known Failure Modes

Lines 618-753: Troubleshooting Section

The guide documents common skill failures:
┌───────────────────────────┬────────────────────────────────┬─────────┐
│ Failure Mode │ What Goes Wrong │ Lines │
├───────────────────────────┼────────────────────────────────┼─────────┤
│ Doesn't trigger │ Never loads automatically │ 620-632 │
├───────────────────────────┼────────────────────────────────┼─────────┤
│ Triggers too often │ Loads for unrelated queries │ 634-660 │
├───────────────────────────┼────────────────────────────────┼─────────┤
│ MCP connection issues │ Skill loads but calls fail │ 662-685 │
├───────────────────────────┼────────────────────────────────┼─────────┤
│ Instructions not followed │ Skill loads but behavior wrong │ 687-731 │
├───────────────────────────┼────────────────────────────────┼─────────┤
│ Large context issues │ Slow or degraded responses │ 733-753 │
└───────────────────────────┴────────────────────────────────┴─────────┘
Implication: Each failure mode is an adversarial scenario type. We should test:

- Does the skill trigger when it should?
- Does it NOT trigger when it shouldn't?
- Are instructions actually followed?

---

Insight 4: Success Criteria Are Pre-Defined (But Vague)

Lines 283-304: Define Success Criteria

The guide provides success criteria templates:
┌──────────────┬───────────────────────────────────────────────┬──────────────────────────────────┐
│ Metric Type │ Example │ Measurement Approach │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────────────┤
│ Quantitative │ "Triggers on 90% of relevant queries" │ Run 10-20 test queries │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────────────┤
│ Quantitative │ "Completes in X tool calls" │ Compare with/without skill │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────────────┤
│ Qualitative │ "Users don't need to prompt about next steps" │ Note redirections during testing │
├──────────────┼───────────────────────────────────────────────┼──────────────────────────────────┤
│ Qualitative │ "Workflows complete without correction" │ Run 3-5 times, compare outputs │
└──────────────┴───────────────────────────────────────────────┴──────────────────────────────────┘
Critical admission (line 287):
"Aim for rigor but accept that there will be an element of vibes-based assessment."

Implication: The guide acknowledges the oracle problem but doesn't solve it. These criteria are aspirational, not operational.

---

Insight 5: The Guide Itself Is Form-Focused

Lines 100-122: Quality Checklist

The checklist is structural:

- name is kebab-case
- description includes WHAT + WHEN + triggers
- SKILL.md is under 500 lines
- Critical requirements use blocking language

Implication: This confirms the root cause analysis. The guide assesses structure, not function. A skill could pass every checklist item and still not work.

The checklist is necessary but not sufficient. It catches structural errors but not functional failures.

---

Key Synthesis

The skills-guide provides inputs to scenario generation, not a complete method:
┌────────────────────────────┬───────────────────────────────────────────────┐
│ Guide Provides │ What It Enables │
├────────────────────────────┼───────────────────────────────────────────────┤
│ Use case template │ Scenario structure (trigger → steps → result) │
├────────────────────────────┼───────────────────────────────────────────────┤
│ Skill type definitions │ Type-based expected behaviors │
├────────────────────────────┼───────────────────────────────────────────────┤
│ Troubleshooting failures │ Adversarial scenario categories │
├────────────────────────────┼───────────────────────────────────────────────┤
│ Success criteria templates │ Measurement dimensions (but not oracles) │
└────────────────────────────┴───────────────────────────────────────────────┘
The gap: The guide tells you to define success criteria but doesn't tell you how to verify them. "Triggers on 90% of relevant queries" — how do you generate those
queries? "Workflows complete without correction" — how do you measure that?

---

Actionable Insight for Scenario Generation

If a skill follows the guide properly, it self-documents its test scenarios:

1. Use cases → Happy path scenarios (trigger + expected behavior + result)
2. Skill type → Type-appropriate behavior expectations
3. Error handling sections → Error recovery scenarios
4. Troubleshooting patterns → Adversarial scenarios (doesn't trigger, triggers wrong, instructions ignored)

If a skill lacks these, that's diagnostic:

- No use cases → Purpose unclear → Scenario design harder → Skill probably has functional issues
- Wrong type techniques → Structural mismatch → Predicted failure mode

This suggests a two-phase approach:

1. Extract existing scenarios from the skill's own documentation (use cases, examples, error handling)
2. Generate missing scenarios based on skill type, trigger conditions, and adversarial probes

Skills that provide rich material for phase 1 are likely better-designed. Skills that require extensive phase 2 generation may have deeper issues.
