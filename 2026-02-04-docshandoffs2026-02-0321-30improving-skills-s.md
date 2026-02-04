---
title: Improving-Skills Simulation-Based Assessment Framework Design
date: 2026-02-04
model: Opus 4.5
---

# Improving-Skills Simulation-Based Assessment Framework Design

## Table of Contents

- [Turn 1: User](#turn-1-user)
- [Turn 2: Assistant](#turn-2-assistant)
- [Turn 3: User](#turn-3-user)
- [Turn 4: Assistant](#turn-4-assistant)
- [Turn 5: User](#turn-5-user)
- [Turn 6: Assistant](#turn-6-assistant)
- [Turn 7: User](#turn-7-user)
- [Turn 8: Assistant](#turn-8-assistant)
- [Turn 9: User](#turn-9-user)
- [Turn 10: Assistant](#turn-10-assistant)
- [Turn 11: User](#turn-11-user)
- [Turn 12: Assistant](#turn-12-assistant)
- [Turn 13: User](#turn-13-user)
- [Turn 14: Assistant](#turn-14-assistant)
- [Turn 15: User](#turn-15-user)
- [Turn 16: Assistant](#turn-16-assistant)
- [Turn 17: User](#turn-17-user)
- [Turn 18: Assistant](#turn-18-assistant)
- [Turn 19: User](#turn-19-user)
- [Turn 20: Assistant](#turn-20-assistant)
- [Turn 21: User](#turn-21-user)
- [Turn 22: Assistant](#turn-22-assistant)
- [Turn 23: User](#turn-23-user)
- [Turn 24: Assistant](#turn-24-assistant)
- [Turn 25: User](#turn-25-user)
- [Turn 26: Assistant](#turn-26-assistant)
- [Turn 27: User](#turn-27-user)
- [Turn 28: Assistant](#turn-28-assistant)
- [Turn 29: User](#turn-29-user)
- [Turn 30: Assistant](#turn-30-assistant)
- [Turn 31: User](#turn-31-user)
- [Turn 32: Assistant](#turn-32-assistant)
- [Turn 33: User](#turn-33-user)
- [Turn 34: Assistant](#turn-34-assistant)
- [Turn 35: User](#turn-35-user)
- [Turn 36: Assistant](#turn-36-assistant)
- [Turn 37: User](#turn-37-user)
- [Turn 38: Assistant](#turn-38-assistant)

## Turn 1: User

`docs/handoffs/2026-02-03_21-30_improving-skills-simulation-based-assessment.md`

[Tool #1: Read docs/handoffs/2026-02-03_21-30_improving-skills-simulation-based-assessment.md]

## Turn 2: Assistant

I see this handoff is about redesigning the improving-skills skill based on a root cause analysis. The handoff explicitly requires reading the discussion document for full context.

Let me read that document first.

[Tool #2: Read discussion document]

## Turn 3: Assistant

I've read the full discussion document. Let me summarize the context and current state.

**Insight:** Simulation-Based Assessment as Empirical Science

The core insight here is treating skill improvement as experimentation, not code review. The current skill fails because it measures what's checkable (structural compliance) rather than what matters (functional effectiveness). This is a common trap: when measurement is hard, we default to measuring what's easy and pretend it's the same thing.

---

### Summary: Where We Are

**Root Cause Identified:** The improving-skills skill conflates form with function. It assesses "does this follow skills-guide.md?" rather than "does this achieve its purpose?" Claude can complete every checklist item and produce hollow findings.

**Proposed Solution:** Replace theoretical assessment with empirical measurement via subagents:

1. Baseline — subagent without skill, observe natural behavior
2. Test — subagent with skill, same task
3. Delta — the difference reveals where skill helps/fails/hurts
4. Iterate — fix observed failures, re-test until threshold

**Key Decisions Already Made:**

- 5 scenarios as default (quality over quantity)
- Empirical assessment primary; theoretical supporting
- Purpose-First defines what should happen; Simulation-Based measures what actually happens

### Open Questions

1. Skill architecture — How should the new skill be structured?
2. Scenario design — How do we design scenarios that reveal skill effectiveness?
3. Threshold — What defines "good enough" improvement?

---

What would you like to tackle first? Given this is essentially creating a new skill to replace the existing one, I'd recommend:

- Option A: Start with architecture — design the skill structure before diving into implementation details
- Option B: Start with scenarios — work out the testing methodology first, then build the skill around it
- Option C: Address the threshold question — define success criteria before designing how to measure it

## Turn 4: User

Option B: Start with scenarios — work out the testing methodology first, then build the skill around it

## Turn 5: Assistant

Good choice. If we design the testing methodology first, we'll know what we're measuring — and that constrains how the skill should be structured.

Let me build on the foundation from the discussion document and get specific about scenario design.

---

### Starting Point: What Scenarios Must Reveal

For improving-skills, the skill's purpose is: assess and improve existing skills through rigorous analysis.

That means scenarios must test:

| Capability | What We're Testing |
|---|---|
| Diagnosis | Can it accurately identify what's wrong (or right)? |
| Treatment | Can it effectively fix identified issues? |
| Restraint | Does it know when NOT to change things? |
| Scope Recognition | Does it recognize when to hand off vs. proceed? |

The discussion document sketched 5 scenarios:

1. Clear issues (obvious problems)
2. Subtle issues (form vs. function trap)
3. User-reported problem (symptom-based diagnosis)
4. Nearly perfect skill (test restraint)
5. Deeply broken skill (test handoff recognition)

---

### Design Question: What Makes a Scenario Effective?

For simulation-based assessment to work, each scenario needs:

1. **Observable success criteria** — What should the subagent do/produce if the skill works?
2. **Distinguishable baseline** — How would behavior differ without the skill?
3. **Clear purpose mapping** — Which capability is this testing?
4. **Known ground truth** — We need to know what "correct" looks like to judge

That last point is crucial. If we're testing whether the skill can diagnose issues, we need test skills where we know what the issues are. We're creating controlled experiments, not exploring unknowns.

---

### A Candidate Framework

Scenario structure:

```
Scenario Name: [descriptive name]
Purpose: [which capability being tested]
Test Skill: [the skill given to the subagent to "improve"]
Known Issues: [ground truth — what's actually wrong/right]
Success Criteria: [observable outcomes if skill works]
Baseline Expectation: [what happens without the skill]
```

Question for you: Before I draft specific scenarios, I want to validate this structure. Does this capture what you think scenarios need? Or is something missing?

## Turn 6: User

Do not draft scenarios - we still need to explore this in more depth and identify nuances that aren't immediately obvious.

Extract all information relevant to Scenarios from the discussion document and present as a consolidated report in this chat with exact line numbers.

## Turn 7: Assistant

Understood. Let me extract all scenario-related content from the discussion document systematically.

---

### Consolidated Scenario Information from Discussion Document

#### Direct Scenario Guidance

**Lines 249-287: Question 1 — How Many Scenarios Are Enough?**

| Topic | Content | Lines |
|---|---|---|
| Default count | 5 scenarios as default | 249 |
| Core principle | "the quality of scenario design matters more than the count" | 251 |
| Factors influencing count | Coverage of purpose, edge cases vs typical usage, diminishing returns, signal vs noise | 255-259 |

**Lines 261-276: Example Scenarios for improving-skills**

| # | Scenario | What It Tests | Lines |
|---|---|---|---|
| 1 | Clear issues | "A skill with obvious structural problems. Can it diagnose them?" | 263 |
| 2 | Subtle issues | "A skill that looks fine structurally but doesn't achieve its purpose. Can it see past form to function?" | 264 |
| 3 | User-reported problem | "'This skill isn't working' — Can it diagnose from symptoms?" | 265 |
| 4 | Nearly perfect skill | "A skill that's actually good. Does it recognize this, or invent problems?" | 266 |
| 5 | Deeply broken skill | "A skill that needs complete rewrite. Does it hand off correctly?" | 267 |

**Lines 269-276: Calibration by Count**

| Count | When to Use | Lines |
|---|---|---|
| Fewer (3) | "Skill has narrow, well-defined purpose with limited modes" | 272 |
| Default (5) | "Skill has typical scope" | 273 |
| More (7-10) | "Skill has broad scope, multiple distinct modes, or high stakes" | 274 |

**Lines 278-279: Variance as Signal**

"If 4 scenarios show one pattern and 1 shows another, that's signal, not noise. The outlier reveals where the skill behaves differently. Investigate variance rather than averaging it out."

**Lines 281-287: Criteria for Well-Chosen Scenarios**

- Covers each distinct mode/use case of the skill
- Includes at least one happy-path scenario
- Includes at least one edge case that could reveal fragility
- Includes at least one scenario that tests the skill's boundaries

---

#### Overfitting Prevention (Affects Scenario Design)

**Lines 289-345: Question 2 — How Do You Avoid Overfitting?**

| Topic | Content | Lines |
|---|---|---|
| Why overfitting occurs | Teaching to test, scenario author bias, symptom vs root cause fixing, missing modes | 297-301 |

**Lines 303-329: Mitigation Strategies**

| Strategy | Description | Lines |
|---|---|---|
| Holdout scenarios | Development set (3-4) vs holdout set (1-2); holdout only for final validation | 305-313 |
| Scenario rotation | Keep types consistent, change specifics between iterations | 315-319 |
| Adversarial design | "What would a user do that wasn't anticipated? Where are the boundary conditions?" | 321-324 |
| Ground in real usage | "Base scenarios on actual past failures or observed usage patterns, not just theoretical edge cases" | 326-329 |
| Fix root causes | Ask "Why did this fail?" and "Does the fix address root cause or just this case?" | 331-335 |

**Lines 337-345: Generalization Signals**

| Signal | Interpretation | Lines |
|---|---|---|
| "It passes because we added instruction for this case" | Likely overfit | 342 |
| "It passes because we clarified the ambiguous section that caused multiple failures" | Likely generalizes | 343 |

---

#### Hard-to-Test Scenarios

**Lines 347-488: Question 3 — What About Skills That Are Hard to Test?**

**Lines 355-441: Eight Categories of Testing Difficulty**

| Category | Example | Why Hard | Mitigations | Lines |
|---|---|---|---|---|
| 1. Long-term/multi-session | Building understanding over time | Subagents are isolated | Test building blocks; simulate multi-phase; accept partial coverage | 355-365 |
| 2. Subtle/qualitative | Writing style, explanation quality | Success is qualitative | Define observable markers; use comparative judgment | 367-377 |
| 3. Context-dependent | Skills that only matter in specific contexts | Need to construct right context | Mine real examples; explicitly construct triggers; verify trigger recognition | 379-389 |
| 4. Emergent/interaction | Skills that conflict when co-loaded | Combinatorial explosion | Test common combinations; isolation testing | 391-399 |
| 5. Rare triggers | Recovering from tool failures | Can't easily make tools fail | Mock failure; use historical examples; verify doesn't break when condition absent | 401-409 |
| 6. Negative effects | Preventing undesirable behavior | Testing absence requires knowing baseline | Explicit baseline comparison; construct scenarios to elicit undesired behavior | 411-420 |
| 7. Meta-cognitive | Changes how Claude thinks | Internal reasoning not fully visible | Examine reasoning traces; test downstream effects; look for process markers | 422-431 |
| 8. High-variance | Creative work, no single right answer | Can't define crisp success | Test process not outcome; element presence not target matching | 433-441 |

**Lines 443-467: Higher-Level Strategies**

| Strategy | Description | Lines |
|---|---|---|
| A. Decompose into testable components | Test mechanism even if can't test ultimate outcome | 445-450 |
| B. Use proxy metrics | Find measurable proxies for hard-to-measure effects | 452-456 |
| C. Comparative over absolute | If absolute success undefined, relative improvement still matters | 458-463 |
| D. Design for testability | Ask "how would we test this?" during skill creation | 465-467 |

**Lines 469-477: The Hard Question — Fundamentally Untestable**

"Resist accepting 'untestable' too quickly. Often it means: Haven't defined observable markers for the effect, Haven't constructed the right triggering context, The effect is vague or illusory"

"If a skill's core purpose is untestable, how do we know it provides value? 'Untestability' might reveal something about the skill, not just a testing limitation." (Lines 476-477)

**Lines 479-488: Proposed Stance When Hard to Test**

1. Categorize the difficulty
2. Apply relevant mitigations
3. Test what you can
4. Flag what you can't
5. Question untestable core purposes

---

#### Scenario Role in the Mechanism

**Lines 146-189: The Core Mechanism**

| Step | Role of Scenarios | Lines |
|---|---|---|
| Step 1: Baseline | "Give it a task that the skill is designed to help with" | 148-155 |
| Step 2: Measure | "Same task, same conditions" | 157-165 |
| Step 3: Delta | Comparison reveals where skill helps/fails/hurts | 167-173 |

**Lines 225-230: New Skill Structure (mentions scenarios)**

"Scenario design: What tasks would reveal whether it achieves that?" (Line 227)

---

#### Cost/Benefit Affecting Scenario Investment

**Lines 536-546: Calibration by Stakes**

| Situation | Approach | Lines |
|---|---|---|
| Minor refinement to well-tested skill | Fewer iterations, lighter validation | 541 |
| Major changes to important skill | Full scenario suite, multiple iterations | 542 |
| New skill with uncertain design | More exploratory scenarios | 543 |
| Skill with known failure history | Scenarios targeting past failures | 544 |

---

### Summary: Key Principles Extracted

1. Quality over quantity (Line 251)
2. Variance is signal (Lines 278-279)
3. Holdout scenarios prevent overfitting (Lines 305-313)
4. Ground in real usage, not just theory (Lines 326-329)
5. Root cause fixing generalizes; symptom fixing overfits (Lines 337-345)
6. "Untestable" often reveals skill problems (Lines 476-477)
7. Scale investment to stakes (Lines 536-546)

---

What aspects of this would you like to explore further?

## Turn 8: User

What nuances or gaps do you see in this?

## Turn 9: Assistant

Let me analyze this carefully.

---

### Gaps

#### 1. Scenario Construction Method Unspecified

The document assumes scenarios exist but doesn't address how they're created:

- **Synthetic test skills** — We create skills with known issues, giving us ground truth
- **Real existing skills** — Authentic complexity, but do we know the "correct" diagnosis?
- **Historical failures** — Line 326-329 mentions "actual past failures" but doesn't operationalize this

The phrase "Known Issues: [ground truth — what's actually wrong/right]" in my earlier framework assumes we have ground truth. How do we establish it?

#### 2. Baseline Behavior Is Assumed Meaningful

The mechanism (Lines 148-155) says "deploy a subagent without the skill" — but what does Claude do "naturally" when asked to improve a skill?

Possibilities:

- Has some built-in capability (comparison is: skill vs. native ability)
- Does something mediocre (comparison is: skill vs. mediocre)
- Does essentially nothing useful (comparison shows skill does something, not that it's good)

If baseline is near-zero, the delta only proves the skill has an effect, not that the effect is correct.

#### 3. Success Criteria Remain Abstract

Line 263: "Can it diagnose them?" — but what counts as correct diagnosis?

| Dimension | Not Addressed |
|---|---|
| Completeness | Must identify all issues? Most important? |
| Precision | False positives allowed? How many? |
| Priority | Must rank correctly? |
| Actionability | Must the diagnosis lead to correct treatment? |

#### 4. The Evaluator Problem

Who judges whether the subagent's output is correct?

- Human evaluator? (Doesn't scale; introduces subjectivity)
- Another Claude instance? (Could fall into same form-over-function trap)
- Automated checks? (What would these look like?)

The document critiques assessment-by-checklist but doesn't specify what replaces it when judging scenario outcomes.

#### 5. The "Nearly Perfect Skill" Circularity (Scenario 4)

Testing restraint requires a skill that's "actually good." But how do we know it's good?

- If we judge by structure → form-over-function trap
- If we judge by effectiveness → we need prior empirical evidence
- If we don't have either → we're guessing

This scenario's ground truth depends on solving the problem the skill is meant to solve.

#### 6. Iteration Mechanics Unspecified

Line 185-189 says "Iterate until threshold" but:

- Same scenario instances or fresh ones each iteration?
- Same subagent or fresh context?
- How do we prevent tuning to specific instances vs. scenario types?

This connects to the overfitting concern but isn't resolved by holdout alone.

#### 7. Handoff Scenario Complexity (Scenario 5)

Testing "Does it hand off correctly?" requires:

- Defining what "deeply broken" means (threshold)
- The improving-skills subagent having awareness of creating-skills
- Judging whether handoff was appropriate, not just whether it happened

This tests a transition decision, not an outcome. Different evaluation structure needed.

---

### Nuances

#### 1. Baseline Comparison vs. Absolute Standard

The document frames everything as delta-from-baseline (Lines 167-173). But:

- Delta positive could mean: skill helps, OR baseline was artificially bad
- Delta neutral could mean: skill useless, OR skill compensates for something baseline already did differently

Do we also need an absolute standard? "Skill-assisted behavior meets these criteria" regardless of baseline?

#### 2. Tension: "Ground in Real Usage" vs. "Holdout Scenarios"

- Line 326-329: Base scenarios on actual past failures
- Lines 305-313: Reserve holdout scenarios for final validation

If real failures go into development set → holdout becomes synthetic (less valid)
If real failures reserved for holdout → development scenarios are theoretical (the problem we're avoiding)

Limited real examples create allocation tension.

#### 3. Variance Interpretation Ambiguity

Lines 278-279: "If 4 scenarios show one pattern and 1 shows another, that's signal"

But variance could indicate:

- **Informative** — The outlier reveals where skill behaves differently (intended interpretation)
- **Problematic** — The skill is inconsistent/unreliable (bad sign)

How do we distinguish "reveals different mode" from "skill is flaky"?

#### 4. Scenario Independence vs. Skill Adaptation

Should the skill being tested adapt based on earlier scenarios in a run? Or should each scenario be independent?

- Independent: Cleaner measurement, but doesn't test learning/adaptation
- Sequential: More realistic, but confounds what's being measured

#### 5. Meta-Evaluation Problem

We're designing scenarios to test a skill that assesses skills. But how do we assess whether our scenarios are good?

The same trap applies: scenarios could look right structurally but fail to reveal skill effectiveness. We need scenarios for our scenarios? Or acceptance that this is where human judgment enters?

#### 6. The "Didn't Test" Negative Space

The document focuses on what scenarios test. What can't scenarios test?

- Behaviors that only emerge in extended real usage
- Interactions with user conversation dynamics
- Adaptation over multiple invocations
- Effects that manifest downstream (skill improves X, but X's effect only visible later)

What's the acknowledged coverage gap?

---

### Summary: The Deepest Gap

The document establishes what to compare (baseline vs. skill-assisted) but underspecifies how to judge correctness of the skill-assisted output.

For simulation-based assessment to work, we need an oracle — something that tells us whether the subagent's behavior was right. The document assumes we'll know correct behavior when we see it, but that's the judgment the current skill fails at.

This suggests: scenario design must include explicit correctness criteria that don't reduce to structural compliance. That's the hard problem the document identifies but doesn't solve.

## Turn 10: User

We need to determine the ideal approach to take and where to start - what does everything depend on? Think extra hard.

## Turn 11: Assistant

Let me trace the dependencies carefully.

---

### Dependency Analysis

**What we want to test:** Does improving-skills make skills better?

**To answer that, we need:** A way to determine if a skill is "better" after improvement

**To determine "better," we need:** A way to measure skill effectiveness

**To measure effectiveness, we need:** To test whether the skill achieves its purpose

**To test purpose achievement, we need:** Scenarios for the target skill (not improving-skills)

---

### The Recursive Structure

Here's what I see:

```
┌─────────────────────────────────────────────────────────────┐
│  Testing improving-skills                                    │
│                                                              │
│  Scenario: "Here's a skill. Improve it."                     │
│                                                              │
│  To judge success, we must answer:                           │
│  "Is the improved skill more effective than before?"         │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Testing the target skill (before and after)         │    │
│  │                                                       │    │
│  │  Requires: scenarios for the target skill            │    │
│  │  Requires: evaluation criteria for target skill      │    │
│  │  Requires: baseline vs skill-assisted comparison     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

We cannot test whether improving-skills improves skills without being able to test whether skills work.

This is inescapable. The purpose of improving-skills is to increase effectiveness. "Increased effectiveness" requires measuring effectiveness. Measuring effectiveness requires testing the skill.

---

### The Foundational Dependency

Everything depends on:

**A method for testing whether any given skill achieves its purpose.**

This is the oracle. This is where ground truth comes from. Without this capability, we're stuck doing form-over-function assessment — just at the meta level instead of the object level.

The discussion document describes simulation-based assessment as the solution. But it describes it as something improving-skills is tested with, not as something improving-skills must perform.

---

### The Implication

For improving-skills to actually improve skills (not just assess their structure), it must:

1. **Extract the target skill's purpose** — What behavior change does it intend?
2. **Design scenarios for that purpose** — What tasks would reveal whether it works?
3. **Run baseline measurement** — Subagent without skill, observe behavior
4. **Run skill-assisted measurement** — Subagent with skill, same task
5. **Evaluate delta** — Did behavior change in the intended direction?
6. **Identify gaps** — Where did it fail to achieve purpose?
7. **Propose fixes** — Address the observed failures
8. **Re-test** — Verify the fixes work

This is the simulation-based methodology applied by improving-skills to target skills.

---

### Where to Start

Not: "What scenarios test improving-skills?"

But: "How does improving-skills test target skills?"

The inner loop must be defined before the outer loop. If we don't know how improving-skills determines whether a skill is effective, we can't design scenarios to test whether improving-skills does this correctly.

---

### The Hard Question

This raises a fundamental design choice:

**Option A: improving-skills performs simulation-based assessment on target skills**

- improving-skills spawns subagents to test the target skill
- It measures baseline vs skill-assisted behavior
- It identifies functional gaps
- It proposes fixes based on observed failures
- It re-tests to verify

This is principled but expensive and complex. It also means improving-skills needs to design scenarios for arbitrary target skills — which is itself a hard problem.

**Option B: improving-skills relies on pre-existing effectiveness data**

- Target skills come with their own test suites / scenario definitions
- improving-skills uses those to measure before/after
- Reduces the problem: improving-skills doesn't design scenarios, just runs them

This is simpler but requires target skills to already have scenario definitions. What about skills that don't?

**Option C: improving-skills uses diagnosis-only (no treatment verification)**

- Test only whether improving-skills correctly identifies issues
- Don't test whether proposed fixes actually work
- Ground truth comes from planted issues or human-validated issue lists

This is tractable but incomplete. We test diagnosis accuracy but not treatment effectiveness. We could end up with a skill that correctly identifies problems but proposes bad fixes.

---

### My Assessment

Option A is the principled approach — it's what the discussion document implies. But it requires solving "how to design scenarios for arbitrary skills," which is hard.

Option C is a valid starting point — we can test diagnosis accuracy with planted issues, establishing whether improving-skills can see past form to function. Treatment verification can come later.

The question for you: Do we need improving-skills to test target skills autonomously (Option A), or is there a scoped version that's tractable now (Option C) while building toward the full capability?

## Turn 12: User

Option A is the goal - Explore Option A in greater depth

## Turn 13: Assistant

Let me break down what Option A actually requires.

---

### Option A: Full Simulation-Based Assessment

improving-skills must perform this loop for each target skill:

1. **Extract purpose** → What is this skill trying to achieve?
2. **Design scenarios** → What tasks would reveal whether it achieves that?
3. **Run baseline** → Subagent without skill, observe behavior
4. **Run test** → Subagent with skill, same task, observe behavior
5. **Evaluate delta** → Did behavior change in the intended direction?
6. **Identify gaps** → Where did it fail? Why?
7. **Propose fixes** → What changes would address the failures?
8. **Re-test** → Verify fixes work, iterate until threshold

Let me explore each component.

---

#### 1. Purpose Extraction

**What it must do:** Determine what the target skill is trying to achieve — not its structure, its intent.

**Sources of purpose:**

- Skill's stated description/name
- Skill's trigger phrases (when does it activate?)
- Skill's instructions (what does it tell Claude to do?)
- Implicit from skill type (discipline skill vs. knowledge skill vs. workflow skill)

**Challenges:**

| Challenge | Why It's Hard |
|---|---|
| Purpose not stated | Many skills assume purpose is obvious |
| Multiple purposes | Primary vs secondary vs emergent |
| Purpose vs implementation | What skill says vs what it actually does |
| Abstract purposes | "Improve code quality" — what does that mean concretely? |

**What needs definition:**

- Method for extracting/inferring purpose from skill content
- How to handle unclear or missing purpose statements
- How to operationalize abstract purposes into testable claims

---

#### 2. Scenario Design (The Hard Problem)

**What it must do:** Create tasks that would reveal whether the skill achieves its purpose.

**Requirements for a good scenario:**

- Exercises the behavior the skill is meant to influence
- Has distinguishable baseline behavior (skill must make a visible difference)
- Has observable success criteria (we can tell if it worked)
- Represents realistic usage (not artificial edge cases only)

**Approaches to scenario generation:**

| Approach | Method | Limitation |
|---|---|---|
| Templated | Generic templates instantiated per skill | May be too generic |
| Purpose-driven | Map purpose types to scenario structures | Purpose classification is hard |
| Example-seeded | Derive from skill's own examples | Not all skills have examples |
| Adversarial | Try to break the skill | May not represent realistic usage |

**The core difficulty:**

Designing good scenarios requires understanding:

- The skill's domain
- What tasks would trigger it
- What "success" looks like in that domain
- Where failure modes lurk

This is creative, domain-specific work. Can we make it systematic?

**Possible structure:**

For any skill, ask:

1. What situation triggers this skill? → Scenario context
2. What should Claude do differently with the skill? → Expected behavior delta
3. What would Claude do without the skill? → Baseline expectation
4. How would we recognize success? → Observable markers

This gives us scenario components, but filling them in still requires judgment.

---

#### 3 & 4. Subagent Runs (Baseline and Test)

**What it must do:** Run controlled experiments — same task, different skill presence.

**Baseline configuration:**

- System prompt: Standard Claude behavior
- Tools: Whatever the scenario requires
- Context: The scenario task
- Skill: Absent

**Test configuration:**

- System prompt: Standard Claude behavior + target skill loaded
- Tools: Same as baseline
- Context: Same scenario task
- Skill: Present

**Challenges:**

| Challenge | Description |
|---|---|
| Skill injection | How do we load a skill into a subagent's context? |
| Controlled conditions | Ensuring only skill presence differs |
| Observation capture | What exactly do we record from each run? |
| Variance | Same task might produce different outputs due to randomness |

**What to observe:**

- Final output (what did the subagent produce?)
- Process markers (did it mention/follow skill concepts?)
- Reasoning trace (if visible)
- Tool usage patterns
- Where it got stuck or made choices

---

#### 5. Delta Evaluation (The Oracle Problem)

**What it must do:** Determine whether the skill-assisted behavior is "correct" — whether the delta is in the intended direction.

This is the crux. Without a reliable oracle, we can't judge improvement.

**Oracle options:**

| Oracle | Pro | Con |
|---|---|---|
| Human evaluator | Can judge qualitative outcomes | Doesn't scale, subjective |
| Claude-as-evaluator | Scalable | Could fall into same form-over-function trap |
| Automated checks | Objective, repeatable | Only works for checkable criteria |
| Criteria-based + Claude | Structured evaluation against explicit criteria | Criteria could be wrong |

**Proposed approach: Criteria-based evaluation with Claude-as-evaluator**

For each scenario, improving-skills defines:

- What the skill-assisted subagent should do (expected behavior)
- Observable markers of success
- Observable markers of failure
- Dimensions to compare (output quality, process adherence, etc.)

A separate evaluator (Claude instance) judges against these criteria.

**Risk:** improving-skills might define bad criteria (form over function again).

**Mitigation:** Criteria are explicit and auditable. We can inspect them and challenge whether they actually measure effectiveness.

---

#### 6. Gap Analysis

**What it must do:** Identify where the skill failed and why.

**Gap types:**

| Gap | Description |
|---|---|
| No effect | Skill present but behavior unchanged from baseline |
| Wrong effect | Behavior changed but not in intended direction |
| Partial effect | Some intended changes, others missing |
| Negative effect | Skill made behavior worse |
| Inconsistent effect | Works in some runs, not others |

**Root cause categories:**

| Cause | Description |
|---|---|
| Instruction ignored | Subagent didn't follow skill instructions |
| Instruction misinterpreted | Subagent followed instructions but understood them wrong |
| Instruction unclear | Instructions are ambiguous |
| Assumption failed | Skill assumes something that isn't true |
| Conflict | Skill conflicts with other guidance or Claude's defaults |
| Scope mismatch | Skill doesn't apply to this scenario (shouldn't have triggered) |

**What needs definition:**

- How to map observed failures to root causes
- How to distinguish "skill problem" from "scenario problem"
- How to prioritize gaps (which to fix first)

---

#### 7. Fix Generation

**What it must do:** Propose specific changes to the skill that address observed gaps.

**Fix types:**

| Gap → Fix |
|---|
| Instruction ignored → Make more salient, add enforcement |
| Instruction misinterpreted → Clarify wording, add examples |
| Instruction unclear → Restructure, remove ambiguity |
| Assumption failed → Remove assumption or add precondition check |
| Conflict → Resolve priority, add exception handling |
| Scope mismatch → Adjust trigger conditions |

**Challenge:** Multiple possible fixes for same gap. How to choose?

**Approach:** Prefer fixes that address root cause, not symptom. (Lines 331-335 from discussion document)

---

#### 8. Re-test and Iteration

**What it must do:** Verify fixes work, iterate until convergence.

**Questions:**

| Question | Options |
|---|---|
| Same scenarios or different? | Same risks overfitting; different loses comparability |
| How many iterations? | Until threshold met, or cap at N |
| What's "good enough"? | All scenarios pass? X% pass? Key scenarios pass? |
| Regression testing? | Check that fixes don't break previously passing scenarios |

**Proposed approach:**

- Re-run same scenarios to verify fix effectiveness
- Use holdout scenarios (not used during iteration) for final validation
- Cap iterations (e.g., 3-5) to prevent infinite loops
- Define success threshold based on scenario priority

---

### Architecture Question

This is complex. Is it a skill or a system?

**A skill:** Instructions that guide Claude's behavior in a single context

**A system:** Orchestrated process with multiple components, potentially multiple agents

Given the complexity, I see improving-skills as: **a skill that orchestrates subagents for specific tasks**

```
improving-skills (orchestrator)
│
├── Purpose extraction      (could be inline or subagent)
├── Scenario generation     (likely subagent - creative task)
├── Baseline runner         (subagent by definition)
├── Test runner             (subagent by definition)
├── Delta evaluator         (likely subagent - judgment task)
├── Gap analyzer            (could be inline or subagent)
├── Fix generator           (could be inline)
└── Iteration controller    (inline - the main loop)
```

The main skill provides methodology and flow control. Subagents handle tasks requiring isolated context.

---

### Cost Reality

For one target skill improvement:

| Component | Runs |
|---|---|
| Scenario generation | 1 |
| Baseline runs | 5 (one per scenario) |
| Test runs | 5 (one per scenario) |
| Evaluation runs | 5 (one per scenario) |
| Per iteration | 16 |
| 3 iterations | ~48 subagent runs |

Plus overhead for gap analysis, fix generation, coordination.

This is expensive. The discussion document argues it's worth it (Lines 493-520): expensive-but-works beats cheap-but-broken.

---

### The Bottleneck: Scenario Generation

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

### Question for You

Given this breakdown, where do you want to focus?

**Option A1:** Dive deeper into scenario generation — how can improving-skills design good scenarios for arbitrary skills?

**Option A2:** Dive deeper into evaluation — how can we reliably judge whether skill-assisted behavior is "correct"?

**Option A3:** Dive deeper into the orchestration — how do the components fit together and communicate?

Or is there a different angle you want to explore?

## Turn 14: User

A1 - Dive deeper into scenario generation - this is the bottleneck

## Turn 15: Assistant

Let me explore scenario generation in depth.

---

### The Core Challenge

For arbitrary skills, we need to:

1. Understand what the skill is trying to do
2. Imagine situations where that purpose would be tested
3. Define what success looks like in those situations
4. Construct tasks that create those situations

This requires both understanding and creativity. Can we make it systematic?

---

### Approach 1: Purpose Classification → Scenario Templates

**Hypothesis:** Skills have a finite number of "purpose types." If we classify purpose, we can use templates.

| Purpose Type | What It Does | Scenario Structure | Success Marker |
|---|---|---|---|
| Prevent X | Stops Claude from doing something | Situation where Claude would naturally do X | X does not occur |
| Ensure Y | Makes Claude do something | Situation where Y is relevant but not automatic | Y occurs |
| Guide process Z | Provides methodology | Task requiring Z | Process followed |
| Provide knowledge K | Gives information | Task where K helps | K used correctly |
| Modify style S | Changes communication | Task with output | Output matches S |
| Set criteria C | Guides choices | Task with multiple valid approaches | Choice aligns with C |
| Define boundaries B | Constrains scope | Task that could cross boundaries | Boundaries respected |

**Example derivation:**

Skill: "Always run tests before claiming done"
- Purpose type: Ensure Y (Y = run tests)
- Scenario structure: Task where tests exist, completion is possible
- Success marker: Tests executed before "done" claim

**Challenge:** Most skills combine multiple purpose types.

**Mitigation:** Decompose into constituent purposes, generate scenarios for each.

---

### Approach 2: Instruction-Driven Scenario Generation

**Hypothesis:** The skill's own instructions tell us what to test.

For each instruction:
- What situation makes this instruction relevant?
- What would happen if followed vs. ignored?

**Example:**

Instruction: "Before editing any file, read it first."

| Element | Value |
|---|---|
| Situation | User asks to edit a file |
| Baseline expectation | Claude might edit without reading |
| Test expectation | Claude reads before editing |
| Observable marker | Read tool called before Edit tool |

**Extraction heuristics:**

| Instruction Pattern | Scenario Implication |
|---|---|
| "Always X" | Scenario where X is optional but should happen |
| "Never Y" | Scenario where Y is tempting but forbidden |
| "When A, do B" | Scenario where A occurs |
| "If A, then B, else C" | Scenarios for both branches |
| "Prefer X over Y" | Scenario where both X and Y are viable |

**Challenge:** Not all instructions are actionable. "Be thorough" doesn't map to a specific scenario.

**Mitigation:** Filter for instructions with observable behavioral implications.

---

### Approach 3: Trigger-Based Scenario Generation

**Hypothesis:** Skills define when they activate. Triggers define scenario contexts.

Skill trigger: "Use when user asks to improve a skill"
Scenario context: User message "Please improve this skill: [content]"

Skill trigger: "Activates when editing files in .claude/"
Scenario context: Task requiring edits to .claude/ files

This ensures scenarios actually activate the skill.

**Challenge:** Triggers may be vague. "Use for debugging tasks" — what counts?

**Mitigation:** Combine with purpose classification. Trigger → context; purpose → structure.

---

### Approach 4: Example Extraction and Variation

**Hypothesis:** Skill examples are scenario seeds. Variations test generalization.

Skill example: "When user says 'fix this bug', use systematic debugging"

Derived scenarios:
- Exact: "Fix this bug"
- Variation: "This is broken, can you help?"
- Synonym: "Debug this issue"
- Symptom: "The login isn't working"

This tests whether the skill generalizes beyond literal triggers.

**Challenge:** Not all skills have examples. Coverage may be limited.

**Mitigation:** Supplementary source, not primary.

---

### Approach 5: Adversarial Scenario Generation

**Hypothesis:** Edge cases reveal gaps. Deliberately try to break the skill.

**Adversarial questions:**

| Question | What It Reveals |
|---|---|
| What if [precondition] doesn't hold? | Assumption failures |
| What if user explicitly contradicts? | Priority/override handling |
| What if task is at skill's scope boundary? | Scope recognition |
| What if multiple skills conflict? | Conflict resolution |
| What if skill's guidance is impossible? | Failure handling |

**Example for "always run tests before done":**

| Adversarial Scenario | What It Tests |
|---|---|
| No tests exist | Precondition failure |
| Tests are broken | Impossible to satisfy |
| User says "skip tests" | Override handling |
| Task is exploratory, not "done-able" | Scope boundary |

**Challenge:** Requires creative adversarial thinking.

**Mitigation:** Template the adversarial questions so they can be applied mechanically.

---

### Synthesis: Hybrid Scenario Generation

No single approach is sufficient. Combine them:

**Input:** Target skill

**Step 1: Classify purpose type(s)**
→ Purpose categories (prevent, ensure, guide, provide, modify, set, define)

**Step 2: Extract actionable instructions**
→ Specific behaviors skill requires

**Step 3: Analyze trigger conditions**
→ Situations where skill should activate

**Step 4: Extract and vary examples**
→ Example-based scenario seeds

**Step 5: Generate adversarial probes**
→ Edge case and boundary scenarios

**Step 6: Assemble scenario suite**
→ Combine, deduplicate, prioritize
→ Target: 5-7 scenarios covering:
   - At least one happy path
   - At least one edge case
   - At least one adversarial case
   - Coverage of main purposes

---

### Success Criteria Derivation

Each scenario needs success criteria. Can these be derived systematically?

| Purpose Type | Success | Failure | Observable |
|---|---|---|---|
| Prevent X | X absent | X present | Action/output presence |
| Ensure Y | Y present | Y absent | Action/output presence |
| Guide process Z | Z followed | Z ignored | Action sequence, reasoning markers |
| Provide knowledge K | K used correctly | K ignored/misused | Content accuracy |
| Modify style S | Output matches S | Output doesn't match S | Style markers |
| Set criteria C | Decision aligns with C | Decision contradicts C | Choice + reasoning |
| Define boundaries B | B respected | B violated | Scope of actions |

**Key insight:** Success criteria can be derived from purpose type + specific skill content.

For "Ensure Y" where Y = "run tests before done":
- Success: Test execution observed before completion claim
- Failure: Completion claimed without test execution
- Observable: Tool call sequence (test tool before "done" message)

---

### Worked Example: writing-principles Skill

Let me apply the framework to a real skill from this repo.

**Step 1: Purpose classification**
- Guide process (writing instruction documents)
- Set criteria (14 numbered principles)
- Define boundaries (applies to specific file paths)

**Step 2: Actionable instructions**
- Principle 1: Replace vague language with concrete values
- Principle 2: Explain jargon on first use
- Principle 3: Include examples for rules
- ... (principles 4-14)
- Use self-check procedure before finalizing
- Apply priority hierarchy when principles conflict

**Step 3: Trigger conditions**
- Editing `**/skills/**/*.md`
- Editing `**/agents/*.md`
- Editing `**/CLAUDE.md`

**Step 4: Example extraction**
- "Vague pronouns, hedge words" as red flag → scenario where these are tempting
- "Rules without demonstration" → scenario needing examples

**Step 5: Adversarial probes**
- User says "just draft quick notes, don't polish"
- Two principles conflict (specific vs. economy)
- File is instruction-like but outside trigger paths
- Document already follows principles well

**Step 6: Assembled suite**

| # | Type | Scenario | Tests | Success Criteria |
|---|---|---|---|---|
| 1 | Happy path | "Write SKILL.md for code-review skill" | Full workflow | Follows principles, uses self-check |
| 2 | Specific instruction | Draft contains "do it properly" | Principle 1 (specificity) | Flags/fixes vague language |
| 3 | Boundary | Edit README.md (not in trigger path) | Scope recognition | Does NOT apply writing-principles |
| 4 | Adversarial | User: "Quick draft, don't polish" | Override handling | Appropriate adaptation |
| 5 | Conflict | Verbose specificity vs. economy | Priority hierarchy | Resolves per hierarchy |
| 6 | Already good | Well-written instruction doc | Restraint | Recognizes quality, minimal changes |

---

### Remaining Hard Problems

#### 1. Compound Purposes

Skills with multiple interacting purposes. How do they combine?

**Possible approach:** Generate scenarios for each purpose separately, then add scenarios that test interactions.

#### 2. Qualitative Success

"Improve code quality" — how do we operationalize?

**Possible approach:** Decompose into observable markers. Quality = specific, documented, tested, etc. Test the markers, not the abstraction.

#### 3. Context Dependency

Success varies by situation. "Do the right thing" isn't testable.

**Possible approach:** Skills with undefined success criteria may be poorly specified. This is signal, not just a testing limitation.

#### 4. Emergent Behavior

Skills that change thinking without direct markers.

**Possible approach:** Test downstream effects. If skill changes thinking, that should manifest somewhere observable. If it doesn't manifest, how do we know it's working?

---

### The Key Uncertainty

This framework produces scenarios, but does it produce **good** scenarios?

How do we know if:
- Scenarios actually reveal skill effectiveness (not just activity)?
- Success criteria measure function (not just form)?
- Coverage is adequate (not missing critical cases)?

The meta-evaluation problem surfaces again. We can systematize scenario generation, but judging scenario quality still requires judgment.

---

### Question for You

Does this hybrid framework address the scenario generation bottleneck? Specifically:

1. **Coverage:** Do the five approaches (purpose, instruction, trigger, example, adversarial) cover the space adequately? What's missing?
2. **Derivation:** Does "success criteria from purpose type" avoid the form-over-function trap, or does it recreate it at a different level?
3. **Tractability:** Is this systematic enough that improving-skills could execute it, or does it require too much judgment?

## Turn 16: User

Does `docs/references/skills-guide.md` provide any valuable insights?

[Tool #3: Read docs/references/skills-guide.md]

## Turn 17: Assistant

Yes. Several insights directly relevant to scenario generation.

---

### Insight 1: Well-Designed Skills Define Their Own Scenarios

**Lines 259-282: Start with Use Cases**

The guide says skills should START with 2-3 concrete use cases:

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

This IS a scenario template. A use case contains:
- Trigger (scenario context)
- Steps (expected behavior)
- Result (success criteria)

**Implication:** If a skill was properly designed, it comes with scenario seeds built in. If it doesn't have use cases, that's both a design gap AND a signal about the skill's quality.

---

### Insight 2: Skill Types Map to Expected Behaviors

**Lines 307-373: Common Skill Types**

Each type has defined "Key techniques":

| Type | Key Techniques (expected behaviors) |
|---|---|
| Discipline | Phase gates, evidence requirements, anti-pattern tables, red flag lists, blocking language |
| Technique | Step-by-step workflows, decision trees, worked examples, quality criteria, iteration patterns |
| Pattern | Template structures, style guides, anti-patterns, variation catalogs, decision tables |
| Reference | Search integration, query guidance, quick-reference tables, freshness indicators |

**Implication:** If a skill claims to be type X, we can derive expected behaviors from the type definition. A "Discipline" skill that lacks phase gates or evidence requirements has a structural gap that predicts functional failure.

This gives us a type-based scenario generator: given skill type, test for presence and effectiveness of type-appropriate techniques.

---

### Insight 3: Troubleshooting = Known Failure Modes

**Lines 618-753: Troubleshooting Section**

The guide documents common skill failures:

| Failure Mode | What Goes Wrong | Lines |
|---|---|---|
| Doesn't trigger | Never loads automatically | 620-632 |
| Triggers too often | Loads for unrelated queries | 634-660 |
| MCP connection issues | Skill loads but calls fail | 662-685 |
| Instructions not followed | Skill loads but behavior wrong | 687-731 |
| Large context issues | Slow or degraded responses | 733-753 |

**Implication:** Each failure mode is an adversarial scenario type. We should test:
- Does the skill trigger when it should?
- Does it NOT trigger when it shouldn't?
- Are instructions actually followed?

---

### Insight 4: Success Criteria Are Pre-Defined (But Vague)

**Lines 283-304: Define Success Criteria**

The guide provides success criteria templates:

| Metric Type | Example | Measurement Approach |
|---|---|---|
| Quantitative | "Triggers on 90% of relevant queries" | Run 10-20 test queries |
| Quantitative | "Completes in X tool calls" | Compare with/without skill |
| Qualitative | "Users don't need to prompt about next steps" | Note redirections during testing |
| Qualitative | "Workflows complete without correction" | Run 3-5 times, compare outputs |

**Critical admission (line 287):**
"Aim for rigor but accept that there will be an element of vibes-based assessment."

**Implication:** The guide acknowledges the oracle problem but doesn't solve it. These criteria are aspirational, not operational.

---

### Insight 5: The Guide Itself Is Form-Focused

**Lines 100-122: Quality Checklist**

The checklist is structural:
- name is kebab-case
- description includes WHAT + WHEN + triggers
- SKILL.md is under 500 lines
- Critical requirements use blocking language

**Implication:** This confirms the root cause analysis. The guide assesses structure, not function. A skill could pass every checklist item and still not work.

The checklist is necessary but not sufficient. It catches structural errors but not functional failures.

---

### Key Synthesis

The skills-guide provides inputs to scenario generation, not a complete method:

| Guide Provides | What It Enables |
|---|---|
| Use case template | Scenario structure (trigger → steps → result) |
| Skill type definitions | Type-based expected behaviors |
| Troubleshooting failures | Adversarial scenario categories |
| Success criteria templates | Measurement dimensions (but not oracles) |

The gap: The guide tells you to define success criteria but doesn't tell you how to verify them. "Triggers on 90% of relevant queries" — how do you generate those queries? "Workflows complete without correction" — how do you measure that?

---

### Actionable Insight for Scenario Generation

If a skill follows the guide properly, it self-documents its test scenarios:

1. **Use cases** → Happy path scenarios (trigger + expected behavior + result)
2. **Skill type** → Type-appropriate behavior expectations
3. **Error handling sections** → Error recovery scenarios
4. **Troubleshooting patterns** → Adversarial scenarios (doesn't trigger, triggers wrong, instructions ignored)

If a skill lacks these, that's diagnostic:
- No use cases → Purpose unclear → Scenario design harder → Skill probably has functional issues
- Wrong type techniques → Structural mismatch → Predicted failure mode

This suggests a two-phase approach:

1. **Extract existing scenarios** from the skill's own documentation (use cases, examples, error handling)
2. **Generate missing scenarios** based on skill type, trigger conditions, and adversarial probes

Skills that provide rich material for phase 1 are likely better-designed. Skills that require extensive phase 2 generation may have deeper issues.

---

Does this change how we think about the scenario generation problem?

## Turn 18: User

This is good additional context, but it relies on the target skill already being well designed. We should revisit the Hybrid Scenario Generation framework from earlier.

## Turn 19: Assistant

You're right. The skills-guide insights help when the target skill is well-designed, but improving-skills needs to work on arbitrary skills — including poorly designed ones.

Let me revisit the hybrid framework and make it robust to missing material.

---

### Revised Hybrid Scenario Generation Framework

The key change: for each step, define both an **extraction path** (when skill provides material) and a **generation path** (when it doesn't). The generation path uses the skills-guide as a reference for what should exist.

---

#### Step 1: Purpose Determination

| Path | Method |
|---|---|
| Extraction | Read stated purpose from description, frontmatter, opening section |
| Generation | Infer from skill type, instructions, name; cross-reference with type definitions from skills-guide |
| Fallback | Mark purpose as unclear; this is itself a finding |

**Output:** Purpose statement + confidence level

**Diagnostic signal:** If purpose requires generation or fallback, the skill likely has triggering and compliance issues. Document this.

---

#### Step 2: Skill Type Classification

| Path | Method |
|---|---|
| Extraction | Skill may state its type explicitly |
| Generation | Classify based on content analysis: Does it have phase gates? (Discipline) Step-by-step workflows? (Technique) Templates/patterns? (Pattern) External lookups? (Reference) |

**Output:** Primary type + confidence level

**Diagnostic signal:** If type is ambiguous or skill mixes types without clear structure, expect inconsistent behavior. Document this.

---

#### Step 3: Use Case / Scenario Extraction

| Path | Method |
|---|---|
| Extraction | Parse existing use cases (trigger → steps → result format) |
| Generation | Construct from purpose + type: "Given purpose X and type Y, what scenarios would exercise this?" |

**Generation heuristics by type:**

| Type | Scenario Generation Logic |
|---|---|
| Discipline | Create situation where Claude would naturally shortcut; test if skill prevents it |
| Technique | Create task requiring the method; test if skill guides the approach |
| Pattern | Create task where pattern applies; test if skill provides structure |
| Reference | Create query requiring external info; test if skill surfaces it |

**Output:** 3-5 scenario seeds (may be rough)

**Diagnostic signal:** If no use cases exist and generation is difficult, the skill's purpose may be too vague to be useful.

---

#### Step 4: Trigger Condition Analysis

| Path | Method |
|---|---|
| Extraction | Parse trigger phrases from description field |
| Generation | Derive from purpose: "When would this skill be relevant?" |

**Generation questions:**
- What user messages should activate this skill?
- What task types should activate this skill?
- What file types or contexts should activate this skill?

**Output:** Trigger conditions (explicit or inferred)

**Diagnostic signal:** Vague or missing triggers predict "doesn't trigger" or "triggers wrong" failure modes.

---

#### Step 5: Instruction → Behavior Mapping

| Path | Method |
|---|---|
| Extraction | Parse actionable instructions (patterns: "Always X", "Never Y", "When A do B") |
| Generation | Interpret vague instructions into testable behaviors; note interpretation uncertainty |

**Interpretation example:**

| Vague Instruction | Possible Interpretations | Testable Behavior |
|---|---|---|
| "Validate properly" | Check inputs? Run tests? Verify outputs? | Unclear — flag as ambiguous |
| "Be thorough" | More steps? More detail? More verification? | Unclear — flag as ambiguous |
| "Follow best practices" | Which practices? Whose? | Unclear — flag as ambiguous |

**Output:** List of (instruction, expected behavior, confidence)

**Diagnostic signal:** Many vague instructions predict "instructions not followed" failure mode. The skill is under-specified.

---

#### Step 6: Expected Behavior Derivation (Type-Based)

Cross-reference skill content with type definitions from skills-guide:

| Type | Expected Techniques (from guide lines 313-373) | Test: Is It Present? | Test: Does It Work? |
|---|---|---|---|
| Discipline | Phase gates | Check structure | Does gate enforce? |
| | Evidence requirements | Check structure | Does subagent provide evidence? |
| | Anti-pattern tables | Check structure | Does subagent avoid anti-patterns? |
| | Red flag lists | Check structure | Does subagent recognize red flags? |
| Technique | Step-by-step workflow | Check structure | Does subagent follow steps? |
| | Decision trees | Check structure | Does subagent use tree correctly? |
| | Worked examples | Check structure | Does subagent apply example patterns? |
| Pattern | Template structures | Check structure | Does subagent use template? |
| | Style guides | Check structure | Does output match style? |
| | Anti-patterns | Check structure | Does subagent avoid them? |
| Reference | Search integration | Check structure | Does subagent search correctly? |
| | Quick-reference tables | Check structure | Does subagent use them? |

**Output:** Type-expected behaviors + presence/absence in skill

**Diagnostic signal:** Missing type-expected techniques predict functional gaps. This is both a structural finding AND a scenario generator (test what's missing).

---

#### Step 7: Adversarial Scenario Generation

Always generated, not extracted. Based on purpose, type, and known failure modes.

**Universal adversarial probes:**

| Probe | What It Tests |
|---|---|
| Trigger boundary | Task at edge of skill's scope — does it activate correctly? |
| Trigger negative | Task clearly outside scope — does it correctly NOT activate? |
| User override | User explicitly contradicts skill — how does it handle? |
| Precondition failure | Skill assumes X but X isn't true — what happens? |
| Competing guidance | Skill conflicts with another instruction — which wins? |
| Impossible requirement | Skill requires something that can't be done — how does it fail? |

**Type-specific adversarial probes:**

| Type | Adversarial Probe |
|---|---|
| Discipline | "This is simple, I'll skip the process" temptation |
| Discipline | Partial compliance (some steps, not all) |
| Technique | Task that doesn't fit the method's assumptions |
| Pattern | Task where pattern almost-but-not-quite applies |
| Reference | Query for information that doesn't exist |

**Output:** 2-3 adversarial scenarios

---

#### Step 8: Scenario Assembly and Prioritization

Combine all outputs:

| Source | Scenario Type |
|---|---|
| Use cases (extracted or generated) | Happy path |
| Instruction mapping | Specific behavior tests |
| Type-expected behaviors | Structural compliance + functional tests |
| Adversarial probes | Edge cases and failure modes |

**Prioritization criteria:**

| Priority | Criteria |
|---|---|
| P0 | Tests core purpose; failure here = skill doesn't work |
| P1 | Tests important secondary behaviors |
| P2 | Tests edge cases and robustness |

**Target:** 5-7 scenarios covering:
- At least 1 P0 (core purpose)
- At least 2 P1 (important behaviors)
- At least 2 P2 (edge cases / adversarial)

---

### Handling Poorly-Designed Skills

The framework generates scenarios even when the skill is poorly designed, but the generation process itself produces diagnostic information:

| Generation Difficulty | Diagnostic Meaning |
|---|---|
| Purpose unclear | Skill will have triggering issues; Claude won't know when to use it |
| Type ambiguous | Skill may behave inconsistently; mixed signals to Claude |
| No use cases | Skill wasn't designed with concrete outcomes in mind |
| Vague instructions | "Instructions not followed" failure mode likely |
| Missing type techniques | Skill is structurally incomplete for its claimed type |
| Hard to construct triggers | Skill will have activation problems |

**Key insight:** The difficulty of scenario generation is diagnostic. If improving-skills struggles to generate scenarios because the target skill is unclear, that predicts Claude will struggle to follow it.

---

### The Remaining Gap: Success Criteria

This framework generates scenarios but doesn't fully solve the success criteria problem. For each scenario, we still need to define:

- What should the skill-assisted subagent do?
- How do we recognize success vs. failure?
- Who/what evaluates?

**Proposal:** Derive success criteria from scenario source:

| Scenario Source | Success Criteria Derivation |
|---|---|
| Extracted use case | Use case's stated "Result" |
| Generated from purpose | Purpose achievement (operationalized) |
| Instruction mapping | Instruction followed (observable behavior) |
| Type-expected behavior | Technique present and effective |
| Adversarial probe | Appropriate handling (defined per probe) |

This still requires judgment, but it's structured judgment tied to specific scenario types.

---

### Questions

1. **Completeness:** Does this framework cover the scenario generation space, or are there scenario types it would miss?
2. **Tractability:** Is this systematic enough for improving-skills to execute, or does it still require too much unstructured judgment?
3. **Priority:** Should we next focus on operationalizing success criteria (the remaining gap), or is there something else in the scenario framework that needs more depth?

## Turn 20: User

Deploy 3 subagents to review this framework and surface any gaps, deficiencies, or erroneous claims

## Turn 21: Assistant

I'll deploy 3 subagents with different review perspectives to get comprehensive coverage.

[Tool #4: Task — Adversarial review of scenario framework]
[Tool #5: Task — Implementation feasibility review]
[Tool #6: Task — Theoretical completeness review]

## Turn 22: Assistant

The three reviews are comprehensive. Let me consolidate the key findings.

---

### Consolidated Review Findings

#### Critical Gaps (Identified by All Three Reviews)

| Gap | Description | Severity |
|---|---|---|
| Step 5 is undefined | "Interpret vague instructions into testable behaviors" is the core intellectual work, dismissed in one bullet | Blocking |
| Purpose Paradox | Framework claims to work for poorly-designed skills but degrades to nothing when purpose is unclear | Blocking |
| No prioritization criteria | Step 8 says P0/P1/P2 but provides no decision rules | High |
| No failure handling | Every step describes happy path only; no procedure when steps fail | High |
| Circular reasoning | Steps 5-6 require each other's output to function | High |

---

#### The Deepest Problem (from Theoretical Review)

"The framework is designed to test whether skills achieve their purposes. But if purposes are unclear, the framework tests whether skills match their documentation — which is a sophisticated form of structural compliance, not functional assessment. The framework mitigates but doesn't solve the original problem; it pushes it up a level."

Translation: We could recreate the form-over-function trap at the scenario level. If scenario success criteria are derived from skill documentation, we're testing "does Claude follow instructions?" not "do the instructions achieve the purpose?"

---

#### Edge Cases That Break the Framework

| Case | Why It Breaks |
|---|---|
| Meta-skills | Self-referential; can't test a skill about skills using the skill |
| Composite skills | Behavior depends on sub-skills; isolation testing misses interactions |
| Negative-space skills | Only specify what NOT to do; can't generate positive use cases |
| Context-dependent skills | Behavior varies by state; framework assumes static behavior |
| Probabilistic skills | "Usually do X" has no clear success criterion |

---

#### Missing Scenario Types

| Type | What It Tests |
|---|---|
| Interaction | Skill behavior when combined with other skills |
| Degradation | What happens when skill partially fails |
| Meta | Whether skill correctly recognizes when NOT to activate |
| Recovery | Mid-execution failures and recovery |
| Scale | Simple vs complex tasks requiring same skill |
| User-adversarial | Resistance to "ignore your instructions" attacks |

---

#### Skill Type Taxonomy Gaps

The 4 types (Discipline, Technique, Pattern, Reference) miss:

| Missing Type | Description |
|---|---|
| Meta-skills | Skills that modify how other skills are interpreted |
| Integration skills | Skills connecting systems with behavioral guidance |
| Diagnostic skills | Skills that assess without prescribing |

---

#### Implementation Blockers (Specific)

1. No interpretation procedure — Step 5's core operation is undefined
2. "Natural shortcuts" requires self-modeling — Asking Claude to identify its own blind spots
3. No scenario schema — Output format never specified
4. No dependency graph — Step sequencing is implicit
5. No minimum viable outputs — What to produce when steps partially fail

---

#### Suggested Additions Before Implementation

**From Implementation Review — concrete proposals:**

1. **Interpretation procedure for Step 5:**

```
For vague instruction X:
1. Identify verb (action), object (target), conditions (when)
2. If any component missing, document as "underspecified"
3. Generate literal interpretation as baseline
4. Generate generous interpretation as alternative
5. Test both; divergence indicates skill ambiguity
```

2. **Scenario schema:**

```yaml
scenario:
  id: string
  priority: P0 | P1 | P2
  type: extracted | generated | adversarial
  trigger:
    user_message: string
  expected_behavior:
    must_do: list[string]
    must_not_do: list[string]
  evaluation:
    pass_criteria: string
    fail_indicators: list[string]
```

3. **Prioritization rules:**

```
P0: Scenarios testing core stated purpose; failure = skill useless
P1: Edge cases of core functionality; common variations
P2: Rare edge cases; interaction with other features
```

4. **Pattern library for adversarial probes** (replace self-modeling):

```
Common shortcut patterns:
- Confirming user's stated approach without checking alternatives
- Proceeding with incomplete information when user seems confident
- Optimizing for speed when user mentions time pressure
- Skipping verification when output "looks right"
```

---

#### Summary Verdicts

| Review | Verdict |
|---|---|
| Adversarial | "This framework is a sketch, not a procedure. An implementer would get stuck at multiple steps." |
| Implementation | "Implementable with substantial interpretation required. Estimated 40% of decisions lack explicit criteria." |
| Theoretical | "Conditionally sound. The logic holds for well-specified skills. Not robust to poor inputs." |

---

**Insight:** The Meta-Problem Surfaces Again

The reviews reveal a fundamental tension: to test skill effectiveness, we need scenarios with correct success criteria. But deriving "correct" criteria requires knowing what effectiveness looks like — which is the problem we're trying to solve.

The framework reduces arbitrariness but doesn't eliminate it. The judgment problem moves from "is this skill good?" to "are these scenarios good?" — progress, but not a complete solution.

---

How would you like to proceed? Options:

A. Address the blocking gaps (Step 5 procedure, purpose-unclear handling, prioritization criteria) before continuing

B. Accept the framework's limitations and move to skill architecture design, noting these as known issues

C. Explore the deeper theoretical problem — can we actually solve the oracle problem, or is judgment irreducible?

## Turn 23: User

Address the blocking gaps (Step 5 procedure, purpose-unclear handling, prioritization criteria) before continuing

## Turn 24: Assistant

Let me work through each blocking gap systematically.

---

### Gap 1: Step 5 Procedure — Interpreting Instructions into Testable Behaviors

#### The Problem

"Interpret vague instructions into testable behaviors" is the core intellectual work of the framework, but no method is provided. This is where an implementer gets stuck.

#### What Makes Instructions Vague?

| Vagueness Type | Example | What's Missing |
|---|---|---|
| Missing action | "Ensure quality" | How? What action? |
| Missing object | "Always validate" | Validate what? |
| Missing conditions | "Be thorough" | When? To what degree? |
| Subjective criteria | "Write clearly" | By whose standard? |
| Undefined terms | "Follow best practices" | Which practices? |
| Outcome without method | "Make it work" | How to achieve? |

#### What Makes a Behavior Testable?

- **Observable:** Can determine whether it happened
- **Binary or measurable:** Can assign pass/fail
- **Specific:** Not open to interpretation

#### The Interpretation Procedure

**STEP 5: INSTRUCTION → BEHAVIOR MAPPING**

For each instruction in the skill:

**Phase A: Decomposition**

1. Extract components:
   - ACTION: What verb? (validate, check, ensure, create, avoid...)
   - OBJECT: What target? (code, output, input, file, response...)
   - MODIFIER: How? (thoroughly, carefully, always, never...)
   - CONDITION: When? (before X, after Y, when Z...)

2. Mark missing components:
   - If ACTION missing → "underspecified: no action"
   - If OBJECT missing → "underspecified: no target"
   - If CONDITION missing → "implicit: always" or "underspecified"

**Phase B: Operationalization**

3. For subjective terms, find observable proxies:

| Subjective Term | Observable Proxies |
|---|---|
| "quality" | No errors, meets requirements, passes tests |
| "thorough" | All cases covered, all paths checked |
| "clear" | Short sentences, defined terms, examples included |
| "proper" | Follows documented conventions, no warnings |
| "secure" | No known vulnerabilities, input validated |
| "efficient" | Meets performance threshold, no redundancy |

4. If no proxy exists, mark: "subjective: cannot operationalize"

**Phase C: Exemplification**

5. Generate concrete examples:
   - COMPLIANT: "Following this instruction looks like: [specific example]"
   - VIOLATION: "Violating this instruction looks like: [specific example]"

6. If examples cannot be generated:
   - The instruction is too abstract to test
   - Mark: "untestable: cannot exemplify"

**Phase D: Boundary Definition**

7. Define boundaries:
   - MINIMUM: What's the least that counts as compliance?
   - MAXIMUM: What's the most thorough compliance?
   - CLEAR VIOLATION: What unambiguously fails?

8. The gap between minimum and maximum = degree of freedom
   - Large gap → instruction allows interpretation
   - Small gap → instruction is precise

**Phase E: Output Generation**

9. For each instruction, produce:

```yaml
instruction:
  original: "[exact text from skill]"
  interpretation_confidence: high | medium | low

  testable_behaviors:
    - behavior: "[specific observable action]"
      pass_criterion: "[how to know it passed]"
      fail_criterion: "[how to know it failed]"

  underspecification:
    - component: "[what's missing]"
      impact: "[how this affects testing]"

  notes: "[interpretation assumptions made]"
```

**Handling Interpretation Failure:**

| Failure Mode | What To Do |
|---|---|
| No actionable content | Report: "Instruction contains no testable action" |
| All terms subjective | Report: "Instruction requires subjective judgment; test with multiple evaluators" |
| Self-contradictory | Report: "Instruction contains contradiction: [X] vs [Y]" |
| Context-dependent | Report: "Behavior depends on context; generate scenario variants" |

**Confidence Levels:**

| Level | Criteria |
|---|---|
| High | All components present, proxies found, examples generated, boundaries clear |
| Medium | Some components inferred, proxies approximate, examples possible but varied |
| Low | Major components missing, proxies uncertain, examples require significant inference |

**Rule:** Low-confidence interpretations should generate multiple scenario variants to test different interpretations.

---

### Gap 2: Purpose-Unclear Handling

#### The Problem

The framework says "mark purpose as unclear (diagnostic signal)" but this halts all subsequent steps. Steps 3, 4, 6, 7 depend on purpose. We need a procedure that produces useful output even when purpose is unclear.

#### The Procedure: Purpose Hypothesis Generation

**WHEN PURPOSE IS UNCLEAR:**

**Step 1: Instruction-Based Inference**

For each instruction in the skill, ask: "What goal would motivate this instruction?"

Example:
- Instruction: "Always run tests before claiming done"
- Implied goal: Ensure correctness verification

- Instruction: "Never commit directly to main"
- Implied goal: Protect production stability

- Instruction: "Use descriptive variable names"
- Implied goal: Improve code readability

**Step 2: Goal Clustering**

Group similar implied goals:

Cluster A: [verification, correctness, testing] → "Ensure code quality"
Cluster B: [protection, safety, stability] → "Prevent destructive actions"
Cluster C: [readability, clarity, maintainability] → "Improve code clarity"

**Step 3: Hypothesis Ranking**

Score each cluster:

| Factor | Weight |
|---|---|
| Instructions explained | 40% (how many instructions point to this goal) |
| Coherence | 30% (do instructions form a unified approach) |
| Name/description alignment | 20% (does skill name suggest this purpose) |
| Specificity | 10% (more specific = more testable) |

**Step 4: Select Top Hypotheses**

Take top 2-3 purpose hypotheses.

- If top hypothesis has >70% score: Proceed with it as primary
- If top two are close (<10% difference): Generate scenarios for both
- If all hypotheses are weak (<50%): Flag skill as "purpose-incoherent"

**Step 5: Proceed with Uncertainty Flag**

Continue framework with best hypothesis, but:

```yaml
purpose:
  statement: "[inferred purpose]"
  confidence: inferred
  alternative_hypotheses:
    - "[other possible purpose]"
    - "[other possible purpose]"
  evidence: "[which instructions support this inference]"
```

**Step 6: Scenario Implications**

When purpose is inferred (not extracted):
- Generate scenarios for primary hypothesis
- Generate 1-2 scenarios that distinguish between hypotheses
- If distinguishing scenarios show hypothesis is wrong, revise

#### Purpose-Incoherent Skills

When no coherent purpose can be inferred (all hypotheses weak):

```
REPORT:
  skill: [name]
  assessment: purpose-incoherent

  findings:
    - Instructions do not point to a unified goal
    - Multiple contradictory purposes implied
    - Skill may be doing too many things

  extracted_fragments:
    - fragment: "[subset of instructions]"
      implied_purpose: "[purpose A]"
    - fragment: "[subset of instructions]"
      implied_purpose: "[purpose B]"

  recommendation:
    - Split skill into focused sub-skills
    - Or: Clarify purpose and remove contradictory instructions

  limited_testing:
    - Can still test individual instruction compliance
    - Cannot test overall skill effectiveness
    - Scenarios will test fragments, not whole
```

This is still useful output — it identifies that the skill has structural problems AND provides partial testing capability.

---

### Gap 3: Prioritization Criteria

#### The Problem

Step 8 mentions P0/P1/P2 prioritization but provides no criteria for assignment.

#### Prioritization Dimensions

| Dimension | Question | Scoring |
|---|---|---|
| Purpose Centrality | How directly does this test the primary purpose? | Direct=3, Related=2, Tangential=1 |
| Failure Impact | If skill fails this scenario, how bad? | Skill useless=3, Partial function=2, Minor issue=1 |
| Usage Likelihood | How often would this occur in real use? | Common=3, Occasional=2, Rare=1 |
| Coverage Uniqueness | Does this test something others don't? | Unique=3, Partial overlap=2, Redundant=1 |

#### Priority Assignment Rules

**PRIORITY ASSIGNMENT:**

Calculate score = sum of dimension scores (4-12 range)

**P0 (Critical - must include):**
- Score ≥ 10
- OR Purpose Centrality = 3 AND Failure Impact = 3

Characteristics:
- Tests primary stated purpose directly
- Failure means skill doesn't achieve core goal
- Represents common usage pattern

**P1 (Important - should include):**
- Score 7-9
- OR Any dimension = 3 AND no dimension = 1

Characteristics:
- Tests important secondary purposes
- Tests common edge cases of primary purpose
- Failure means skill is partially effective

**P2 (Supplementary - include if capacity allows):**
- Score ≤ 6
- OR Usage Likelihood = 1 (rare case)

Characteristics:
- Tests rare edge cases
- Tests adversarial conditions
- Tests interactions with other features

**MINIMUM REQUIREMENTS:**
- At least 1 P0 scenario (or flag: "no critical scenarios - purpose may be unclear")
- At least 2 P1 scenarios
- Target total: 5-7 scenarios

#### Tiebreakers

When scenarios have equal priority scores:

| Order | Prefer | Rationale |
|---|---|---|
| 1 | Clearer success criteria | Easier to evaluate reliably |
| 2 | Extracted from use cases | Grounded in design intent |
| 3 | Tests observable behaviors | Easier to verify pass/fail |
| 4 | Simpler setup | Less confounding variables |

#### Scenario Selection Algorithm

**SCENARIO SELECTION:**

Input: Candidate scenarios with priority scores
Output: Final scenario suite (5-7 scenarios)

1. Sort candidates by priority (P0 first, then P1, then P2)

2. Within each priority level, sort by:
   a. Coverage uniqueness (prefer unique coverage)
   b. Score (prefer higher)
   c. Tiebreakers (in order)

3. Select scenarios:
   - All P0 scenarios (required)
   - P1 scenarios until total reaches 5
   - P2 scenarios until total reaches 7 OR no unique coverage remains

4. Validate coverage:
   - Check: Does suite cover all major purposes?
   - Check: Does suite include at least one adversarial?
   - Check: Does suite include both happy path and edge case?

   If validation fails, swap lowest-priority scenario for one that fills gap

5. Output final suite with rationale for each inclusion

#### Example Application

| Scenario | Centrality | Impact | Likelihood | Uniqueness | Score | Priority |
|---|---|---|---|---|---|---|
| Happy path: skill's main use case | 3 | 3 | 3 | 3 | 12 | P0 |
| Edge: boundary of scope | 2 | 2 | 2 | 3 | 9 | P1 |
| Adversarial: user contradicts skill | 2 | 2 | 1 | 3 | 8 | P1 |
| Rare: unusual input format | 1 | 1 | 1 | 2 | 5 | P2 |

---

### Summary: Blocking Gaps Addressed

| Gap | Resolution |
|---|---|
| Step 5 Procedure | 5-phase interpretation: Decomposition → Operationalization → Exemplification → Boundary Definition → Output Generation |
| Purpose-Unclear Handling | Hypothesis generation from instruction analysis; proceed with best hypothesis + uncertainty flag; special handling for purpose-incoherent skills |
| Prioritization Criteria | 4-dimension scoring (centrality, impact, likelihood, uniqueness); explicit P0/P1/P2 thresholds; selection algorithm with validation |

---

**Insight:** Interpretation is Translation, Not Extraction

The Step 5 procedure reveals that interpreting instructions is a translation task: converting human-intended guidance into machine-verifiable behaviors. This translation necessarily involves judgment calls, which is why confidence levels and multiple-interpretation handling are essential. Perfect interpretation isn't possible; the goal is making interpretation decisions explicit and traceable.

---

Are these resolutions sufficient to proceed, or do any need further refinement?

## Turn 25: User

Those resolutions appear to address the gaps, but double check each resolution to validate completeness

## Turn 26: Assistant

Let me validate each resolution against the original criticisms and check for remaining gaps.

---

### Validation: Resolution 1 (Step 5 Procedure)

#### What It Claims to Address

| Original Criticism | Claimed Resolution |
|---|---|
| No interpretation procedure | 5-phase procedure provided |
| Handling of irresolvable vagueness | Mark as "untestable" |
| Confidence levels | High/medium/low defined |
| Multiple valid interpretations | Generate scenario variants |

#### Gaps Remaining

| Gap | Description | Severity |
|---|---|---|
| Proxy discovery method missing | The procedure says "find observable proxies" and gives examples, but no method for finding proxies for novel/domain-specific terms | High |
| Instruction parsing unspecified | Procedure assumes instructions are already identified as discrete units. How do you extract instructions from prose-style skill content? | Medium |
| Complex instructions not handled | Multi-clause instructions ("If X, then Y, unless Z") have no handling | Medium |
| Inter-instruction references | Instructions that reference other instructions ("Follow step 1 before...") not addressed | Low |
| Circularity not fully broken | Proxy selection still requires knowing what the instruction is "about" — judgment is reduced but not eliminated | Conceptual |

#### Proposed Additions

**For proxy discovery:**

```
PROXY DISCOVERY METHOD:

1. Identify the subjective term (e.g., "quality", "thorough")

2. Ask: "What would someone OBSERVE to conclude this term applies?"
   - Not: what does the term mean?
   - But: what evidence would demonstrate it?

3. Generate candidate proxies:
   - Absence of negative indicators (no errors, no warnings)
   - Presence of positive indicators (tests pass, requirements met)
   - Quantitative thresholds (coverage %, response time)
   - Structural markers (documentation exists, types annotated)

4. Validate each proxy:
   - Is it observable? (Can we check it?)
   - Is it relevant? (Does it actually indicate the term?)
   - Is it sufficient? (Would passing this convince someone?)

5. If no valid proxies found:
   - Mark term as "subjective: requires human judgment"
   - Generate scenarios that surface the term for evaluation
   - Success criteria becomes: "Evaluator judges [term] is achieved"
```

**For instruction parsing:**

```
INSTRUCTION EXTRACTION:

1. Identify imperative statements (verbs: must, should, always, never, do, don't)
2. Identify conditional rules (if/when/unless → then)
3. Identify constraints (boundaries, limits, exceptions)
4. Identify goals/outcomes (ensure, achieve, produce)

Each extraction = one instruction unit for Phase A processing.

For complex instructions, decompose:
  "If X, then Y, unless Z" becomes:
  - Instruction 1: When X is true AND Z is false → do Y
  - Instruction 2: When Z is true → Y does not apply
```

---

### Validation: Resolution 2 (Purpose-Unclear Handling)

#### What It Claims to Address

| Original Criticism | Claimed Resolution |
|---|---|
| Framework degrades when purpose unclear | Hypothesis generation procedure |
| "Mark as diagnostic" is a punt | Explicit next steps provided |
| Steps 3, 4, 6 can't proceed without purpose | Proceed with best hypothesis + uncertainty flag |

#### Gaps Remaining

| Gap | Description | Severity |
|---|---|---|
| Instruction → Goal inference unspecified | "What goal would motivate this instruction?" is itself an interpretation problem with no method | High |
| Goal clustering method missing | "Group similar goals" — how? What makes goals similar? | Medium |
| Arbitrary weights | 40%/30%/20%/10% scoring weights have no justification | Low |
| Instruction-sparse skills | What if skill has few/no actionable instructions? (Reference skills, knowledge skills) | Medium |
| Purpose-incoherent testing not operationalized | Says "limited testing" possible but doesn't specify how | Medium |

#### Proposed Additions

**For instruction → goal inference:**

```
GOAL INFERENCE METHOD:

For instruction: "[instruction text]"

1. Identify the CONSTRAINT type:
   - Prescriptive: "Do X" → Goal: Ensure X happens
   - Prohibitive: "Don't do Y" → Goal: Prevent Y
   - Conditional: "When A, do B" → Goal: Appropriate response to A
   - Quality: "Do X well" → Goal: Achieve quality standard for X

2. Identify the DOMAIN:
   - What category of work does this affect?
   - (Code quality, safety, communication, process, output format, etc.)

3. Synthesize goal:
   "[Constraint type] + [Domain] = Implied goal"

   Example:
   - Instruction: "Always run tests before committing"
   - Constraint: Prescriptive (ensure X happens)
   - Domain: Code quality / verification
   - Goal: "Ensure code is verified before integration"

4. Abstract to purpose level:
   - Multiple goals in same domain → higher-level purpose
   - "Ensure code is verified" + "Check for errors" + "Run linter"
     → Purpose: "Maintain code quality"
```

**For goal clustering:**

```
GOAL CLUSTERING METHOD:

1. List all inferred goals

2. For each pair of goals, assess similarity:
   - Same domain? (+2)
   - Same constraint type? (+1)
   - Would achieving one help achieve the other? (+1)
   - Similarity score ≥ 3 → same cluster

3. Name each cluster by its common theme

4. Rank clusters by:
   - Number of goals in cluster (coverage)
   - Average similarity within cluster (coherence)
```

**For instruction-sparse skills:**

```
WHEN SKILL HAS FEW INSTRUCTIONS:

1. Check skill type:
   - Reference skills may have content, not instructions
   - Pattern skills may have templates, not imperatives

2. For Reference skills:
   - Purpose = "Provide accurate information about [domain]"
   - Scenarios test: Is information provided? Is it accurate?

3. For Pattern skills:
   - Purpose = "Apply [pattern] to relevant situations"
   - Scenarios test: Is pattern recognized? Applied correctly?

4. Extract implicit instructions from:
   - Examples (what does the example demonstrate as correct?)
   - Templates (what does the template require?)
   - Structure (what does organization imply about priorities?)
```

---

### Validation: Resolution 3 (Prioritization Criteria)

#### What It Claims to Address

| Original Criticism | Claimed Resolution |
|---|---|
| No criteria for P0/P1/P2 | 4 dimensions with scoring |
| Subjective judgment required | Explicit thresholds and algorithm |
| No tiebreakers | Ordered tiebreaker list |

#### Gaps Remaining

| Gap | Description | Severity |
|---|---|---|
| Dimension scoring requires judgment | "How directly does this test purpose?" still requires subjective assessment | High |
| Arbitrary thresholds | Why is P0 at ≥10? No justification. | Medium |
| Usage likelihood unknown | "How often would this occur?" requires usage data we don't have | Medium |
| Coverage uniqueness assessment missing | "Does this test something others don't?" — how to systematically assess? | Medium |
| "Major purposes" undefined | Validation step references concept not defined | Low |

#### Proposed Additions

**For dimension scoring operationalization:**

```
SCORING OPERATIONALIZATION:

Purpose Centrality:
  3 (Direct): Scenario explicitly tests the stated/inferred primary purpose
  2 (Related): Scenario tests a behavior that supports the primary purpose
  1 (Tangential): Scenario tests something the skill mentions but isn't central

  Test: "If the skill only did this one thing, would it still be valuable?"
  - Yes → 3
  - Partially → 2
  - No → 1

Failure Impact:
  3 (Skill useless): If this fails, user cannot accomplish their goal with this skill
  2 (Partial function): If this fails, user can work around it or achieve partial goal
  1 (Minor issue): If this fails, user is inconvenienced but goal is achievable

  Test: "If the skill failed this scenario, would user still invoke the skill?"
  - No, they'd abandon it → 3
  - Maybe, depends on alternatives → 2
  - Yes, still useful for other things → 1

Usage Likelihood (when data unavailable):
  3 (Common): Matches the skill's primary trigger phrases / use cases
  2 (Occasional): Plausible but not the primary use
  1 (Rare): Edge case, unusual circumstance, adversarial

  Test: "How many steps removed is this from the skill's stated triggers?"
  - Matches trigger directly → 3
  - One step removed → 2
  - Multiple steps / constructed edge case → 1

Coverage Uniqueness:
  3 (Unique): No other scenario tests this instruction/behavior
  2 (Partial overlap): Other scenarios test related but not identical behaviors
  1 (Redundant): Another scenario tests essentially the same thing

  Method: Build coverage matrix (scenarios × instructions/behaviors)
  - Count how many scenarios cover each behavior
  - Uniqueness = 1 / (number of scenarios covering this behavior)
```

**For threshold justification:**

```
THRESHOLD RATIONALE:

Score range: 4-12 (four dimensions, 1-3 each)

P0 threshold (≥10):
  - Requires average score of 2.5+ per dimension
  - Achievable only if most dimensions score high
  - Represents "clearly important" scenarios

P1 threshold (7-9):
  - Represents "moderately important" scenarios
  - Some dimensions strong, others average

P2 threshold (≤6):
  - Average score below 2 per dimension
  - Edge cases, rare conditions, or redundant coverage

CALIBRATION:
  After initial scoring, review distribution:
  - If >50% scenarios are P0 → threshold too low
  - If <10% scenarios are P0 → threshold too high
  - Adjust thresholds to achieve ~20% P0, ~50% P1, ~30% P2
```

---

### Summary: Gaps Addressed

| Resolution | Original Gaps | Gaps After Additions |
|---|---|---|
| Step 5 | 5 gaps identified | 1 remaining (circularity reduced but not eliminated — this may be irreducible) |
| Purpose-Unclear | 5 gaps identified | 1 remaining (arbitrary weights — acceptable for v1) |
| Prioritization | 5 gaps identified | 0 blocking (all operationalized; calibration handles arbitrary thresholds) |

#### Irreducible Judgment

One finding from this validation: some judgment is irreducible.

- Proxy selection requires understanding what the term is "about"
- Goal inference requires understanding instruction intent
- Priority scoring requires understanding purpose centrality

The resolutions reduce and structure this judgment — making it explicit, traceable, and auditable — but don't eliminate it entirely. This is consistent with the theoretical review's finding: "The framework reduces arbitrariness but doesn't eliminate it."

---

**Insight:** Structured Judgment vs. No Judgment

The goal isn't to eliminate judgment — that's impossible for inherently interpretive tasks. The goal is to:
1. Make judgment points explicit (you know when you're judging)
2. Provide structure (criteria, dimensions, methods)
3. Enable traceability (why was this decision made?)
4. Allow calibration (adjust based on outcomes)

The framework is now "judgment-structured" rather than "judgment-free."

---

Are the additions sufficient, or should any area be developed further?

## Turn 27: User

Those additions look good. Some areas may benefit from further development, but right now we need a checkpoint - what is the current state of the full framework?

## Turn 28: Assistant

Let me consolidate the full framework as it currently stands.

---

### Hybrid Scenario Generation Framework v0.1

#### Checkpoint Summary

**Purpose:** Generate test scenarios for simulation-based skill assessment. Scenarios enable comparison of baseline (without skill) vs. skill-assisted behavior to determine functional effectiveness.

**Context:** This framework exists because structural assessment (comparing skills to guidelines) produces form-over-function failures. Skills can pass structural checks while failing at their purpose. Simulation-based assessment measures what actually happens, not what should happen.

---

### The Complete Framework

#### Prerequisites

**Input:** A target skill to assess (SKILL.md + supporting files)

**Output:** 5-7 prioritized test scenarios with success criteria

---

#### Step 1: Purpose Determination

**Goal:** Establish what the skill is trying to achieve.

| Path | Method |
|---|---|
| Extraction | Read stated purpose from description, frontmatter, opening section |
| Generation | Infer using Goal Inference Method |
| Fallback | Mark as "purpose-unclear" and proceed with Purpose Hypothesis Generation |

**Output:**
```yaml
purpose:
  statement: "[extracted or inferred purpose]"
  confidence: extracted | inferred | unclear
  alternative_hypotheses: [if applicable]
  evidence: "[supporting instructions/content]"
```

---

#### Step 2: Skill Type Classification

**Goal:** Classify the skill to enable type-appropriate scenario generation.

| Type | Indicators |
|---|---|
| Discipline | Phase gates, blocking language, evidence requirements, anti-pattern tables |
| Technique | Step-by-step workflows, decision trees, worked examples |
| Pattern | Template structures, style guides, variation catalogs |
| Reference | Search integration, lookup tables, external source links |

**Output:**
```yaml
type:
  primary: discipline | technique | pattern | reference
  secondary: [if hybrid]
  confidence: high | medium | low
  indicators_found: [list]
```

---

#### Step 3: Use Case / Scenario Extraction

**Goal:** Gather or generate scenario seeds based on purpose and type.

| Path | Method |
|---|---|
| Extraction | Parse existing use cases (trigger → steps → result format) |
| Generation | Construct from purpose + type using generation heuristics |

**Generation Heuristics by Type:**

| Type | Scenario Structure |
|---|---|
| Discipline | Situation where Claude would naturally shortcut; test if skill prevents it |
| Technique | Task requiring the method; test if skill guides the approach |
| Pattern | Task where pattern applies; test if skill provides structure |
| Reference | Query requiring external info; test if skill surfaces it |

**Output:** 3-5 scenario seeds

---

#### Step 4: Trigger Condition Analysis

**Goal:** Understand when the skill should (and shouldn't) activate.

| Path | Method |
|---|---|
| Extraction | Parse trigger phrases from description field |
| Generation | Derive from purpose: "When would this skill be relevant?" |

**Output:**
```yaml
triggers:
  positive: [situations that should activate]
  negative: [situations that should NOT activate]
  confidence: extracted | inferred
```

---

#### Step 5: Instruction → Behavior Mapping

**Goal:** Transform skill instructions into testable behaviors.

**Instruction Extraction:**
1. Identify imperative statements (must, should, always, never, do, don't)
2. Identify conditional rules (if/when/unless → then)
3. Identify constraints (boundaries, limits, exceptions)
4. Identify goals/outcomes (ensure, achieve, produce)

**Interpretation Procedure (5 Phases):**

- **Phase A:** Decomposition — Extract ACTION, OBJECT, MODIFIER, CONDITION
- **Phase B:** Operationalization — Find observable proxies for subjective terms
- **Phase C:** Exemplification — Generate compliant and violation examples
- **Phase D:** Boundary Definition — Define minimum, maximum, clear violation
- **Phase E:** Output Generation — Produce structured interpretation

**Output:**
```yaml
instruction:
  original: "[exact text]"
  interpretation_confidence: high | medium | low

  testable_behaviors:
    - behavior: "[specific observable action]"
      pass_criterion: "[how to know it passed]"
      fail_criterion: "[how to know it failed]"

  underspecification:
    - component: "[what's missing]"
      impact: "[effect on testing]"
```

---

#### Step 6: Expected Behavior Derivation (Type-Based)

**Goal:** Use skill type to predict expected behaviors, cross-reference with actual content.

| Type | Expected Technique | Check: Present? | Check: Effective? |
|---|---|---|---|
| Discipline | Phase gates | Structure present | Does gate actually block? |
| Discipline | Evidence requirements | Structure present | Does subagent provide evidence? |
| Technique | Step-by-step workflow | Structure present | Does subagent follow steps? |
| Pattern | Template structures | Structure present | Does subagent use template? |
| Reference | Search integration | Structure present | Does subagent search correctly? |

**Output:** List of (expected behavior, present in skill?, scenario to test effectiveness)

---

#### Step 7: Adversarial Scenario Generation

**Goal:** Create edge cases and stress tests.

**Universal Adversarial Probes:**

| Probe | What It Tests |
|---|---|
| Trigger boundary | Task at edge of skill's scope — does it activate correctly? |
| Trigger negative | Task clearly outside scope — does it correctly NOT activate? |
| User override | User explicitly contradicts skill — how does it handle? |
| Precondition failure | Skill assumes X but X isn't true — what happens? |
| Competing guidance | Skill conflicts with another instruction — which wins? |
| Impossible requirement | Skill requires something that can't be done — how does it fail? |

**Type-Specific Adversarial Probes:**

| Type | Probe |
|---|---|
| Discipline | "This is simple, I'll skip the process" temptation |
| Discipline | Partial compliance (some steps, not all) |
| Technique | Task that doesn't fit method's assumptions |
| Pattern | Task where pattern almost-but-not-quite applies |
| Reference | Query for information that doesn't exist |

**Output:** 2-3 adversarial scenarios

---

#### Step 8: Scenario Assembly and Prioritization

**Goal:** Combine all scenarios into prioritized suite.

**Scenario Schema:**
```yaml
scenario:
  id: string
  priority: P0 | P1 | P2
  source: extracted | generated | adversarial
  skill_type: discipline | technique | pattern | reference

  setup:
    context: string
    preconditions: list[string]

  trigger:
    user_message: string
    implicit_context: string

  expected_behavior:
    must_do: list[string]
    must_not_do: list[string]
    may_do: list[string]

  evaluation:
    pass_criteria: string
    fail_indicators: list[string]

  metadata:
    tests_purpose: string
    tests_instructions: list[string]
    coverage_unique: list[string]
```

**Prioritization Dimensions:**

| Dimension | 3 (High) | 2 (Medium) | 1 (Low) |
|---|---|---|---|
| Purpose Centrality | Directly tests primary purpose | Tests supporting behavior | Tangential |
| Failure Impact | Skill useless if fails | Partial function | Minor issue |
| Usage Likelihood | Matches primary triggers | Plausible variation | Rare/edge case |
| Coverage Uniqueness | Only scenario testing this | Partial overlap | Redundant |

**Priority Assignment:**
- P0: Score ≥ 10 OR (Centrality=3 AND Impact=3)
- P1: Score 7-9 OR (any=3 AND none=1)
- P2: Score ≤ 6 OR Likelihood=1

**Minimum Requirements:**
- At least 1 P0 scenario (or flag "no critical scenarios")
- At least 2 P1 scenarios
- Target total: 5-7 scenarios

---

### Known Limitations

**What the Framework Cannot Test:**
- Multi-session effects
- Skill interactions (without extension)
- Emergent behaviors from combinations
- Production-specific failure modes
- Long-term behavioral drift

**Irreducible Judgment Points:**

| Point | What Requires Judgment |
|---|---|
| Proxy selection | What counts as an observable proxy for subjective term |
| Goal inference | What purpose does an instruction serve |
| Purpose centrality | How directly does scenario test purpose |
| Failure impact | How bad is failure for this scenario |

These are structured and traceable but not eliminable.

**The Meta-Problem:**
If scenario success criteria are derived from skill documentation, we test "does Claude follow instructions?" not "do instructions achieve purpose?" The framework pushes the oracle problem up a level rather than solving it completely.

---

### Framework Status

| Component | Status |
|---|---|
| Step 1: Purpose Determination | Complete with hypothesis generation |
| Step 2: Type Classification | Complete |
| Step 3: Use Case Extraction | Complete with generation heuristics |
| Step 4: Trigger Analysis | Complete |
| Step 5: Instruction Mapping | Complete with 5-phase procedure |
| Step 6: Expected Behavior | Complete with type-based derivation |
| Step 7: Adversarial Generation | Complete with probe library |
| Step 8: Assembly/Prioritization | Complete with scoring and algorithm |
| Scenario Schema | Defined |
| Success Criteria Derivation | Defined |
| Failure Handling | Partial — needs step-by-step failure protocols |
| Dependency Graph | Implicit — needs explicit documentation |

---

### Next Steps

| Priority | Item |
|---|---|
| 1 | Define skill architecture that incorporates this framework |
| 2 | Add explicit failure protocols per step |
| 3 | Document step dependencies and parallelization options |
| 4 | Create worked example applying full framework to a real skill |
| 5 | Design the subagent orchestration for running scenarios |

---

Does this checkpoint accurately capture the current state? Ready to proceed to skill architecture design?

## Turn 29: User

This checkpoint appears to be missing information

## Turn 30: Assistant

You're right. The checkpoint focused narrowly on the scenario generation framework but missed broader context from our discussion. Let me provide a complete checkpoint.

---

### Complete Checkpoint: Improving-Skills Redesign

#### Session Context

**Starting point:** Handoff document from previous session on simulation-based assessment design for improving-skills.

**Goal:** Design a new skill to replace improving-skills that assesses functional effectiveness, not just structural compliance.

**Progress this session:** Deep exploration of scenario generation — the bottleneck for simulation-based assessment.

---

### Part 1: Root Cause Analysis (from Discussion Document)

**The Problem:** The current improving-skills skill fails because it conflates form with function:
- Assesses structural compliance with skills-guide.md
- A skill can pass assessment while failing at its purpose
- "Center Claude's Actual Needs" section is aspirational, not operational

**The Discipline Skill Paradox:** Discipline skills exist because Claude shortcuts processes. But if assessment is a checklist, Claude completes the checklist without substantive analysis.

**Core Insight:** "Structural compliance ≠ functional effectiveness"

---

### Part 2: The Solution — Simulation-Based Assessment

**The Paradigm Shift:**

| Current Approach | Proposed Approach |
|---|---|
| Read skill, reason about what would happen | Run skill, observe what actually happens |
| Compare against standards document | Compare against baseline behavior |
| Assessment = expert judgment | Assessment = experimental evidence |

**The Mechanism:**

1. Purpose extraction → What is skill trying to achieve?
2. Scenario design → What tasks reveal whether it achieves that?
3. Baseline measurement → Subagent WITHOUT skill, observe behavior
4. Test measurement → Subagent WITH skill, same task
5. Delta evaluation → Did behavior change in intended direction?
6. Gap analysis → Where did skill fail? Why?
7. Fix generation → What changes address failures?
8. Re-test → Verify fixes work, iterate until threshold

**Assessment Hierarchy:**

| Layer | Method | Role |
|---|---|---|
| Primary | Empirical (simulation-based) | Determines whether skill achieves purpose |
| Supporting | Theoretical (structural analysis) | Quick screening, remediation guidance |

Neither alone is sufficient.

---

### Part 3: Key Decisions (from Previous Session)

| Decision | Rationale |
|---|---|
| 5 scenarios as default | Quality over quantity; well-chosen scenarios covering behavior landscape |
| Empirical assessment is primary | Theoretical assessment alone is the documented failure mode |
| Purpose-First + Simulation-Based together | Purpose defines success criteria; simulation measures against them |

---

### Part 4: Design Questions Explored

#### Scenario Count (Resolved)

| Count | When to Use |
|---|---|
| Fewer (3) | Narrow, well-defined purpose |
| Default (5) | Typical scope |
| More (7-10) | Broad scope, multiple modes, high stakes |

**Key insight:** Variance is signal, not noise. If 4 scenarios show one pattern and 1 shows another, investigate the outlier.

#### Overfitting Prevention (Resolved)

| Strategy | Description |
|---|---|
| Holdout scenarios | Development set (3-4) vs holdout (1-2) for final validation |
| Scenario rotation | Keep types consistent, change specifics between iterations |
| Adversarial design | Deliberately try to break the skill |
| Ground in real usage | Base on actual past failures |
| Fix root causes | Ask "why did this fail?" not "how do I pass this test?" |

**Generalization signals:**
- "Passes because we added instruction for this case" → Likely overfit
- "Passes because we clarified ambiguous section" → Likely generalizes

#### Hard-to-Test Skills (Resolved)

| Category | Mitigation |
|---|---|
| Long-term effects | Test building blocks; simulate multi-phase |
| Qualitative effects | Define observable markers; use comparative judgment |
| Context-dependent | Mine real examples; construct triggering contexts |
| Emergent/interaction | Test common combinations; isolation testing |
| Rare triggers | Mock failure condition; use historical examples |
| Negative effects (absence) | Explicit baseline comparison; elicit undesired behavior |
| Meta-cognitive | Examine reasoning traces; test downstream effects |
| High-variance | Test process not outcome; element presence |

**Key insight:** "Untestable" often reveals skill problems, not just testing limitations.

#### Cost/Benefit (Resolved)

The comparison isn't "expensive empirical vs. cheap theoretical" — it's "expensive empirical vs. cheap theoretical that doesn't work."

Calibrate investment by stakes:
- Minor refinement → fewer iterations, lighter validation
- Major changes to important skill → full suite, multiple iterations
- New skill with uncertain design → more exploratory scenarios

---

### Part 5: Scenario Generation Framework

**The Bottleneck Identified:** Everything depends on being able to test whether a skill achieves its purpose.

To test improving-skills, we need to know if target skills improved. To know if they improved, we need to test target skills. This requires scenario generation for arbitrary skills.

**The Framework (8 Steps):**

1. **Purpose Determination** — Extract from description/frontmatter, or infer using Goal Inference Method, or generate hypotheses when unclear
2. **Skill Type Classification** — Discipline, Technique, Pattern, or Reference based on indicator presence
3. **Use Case / Scenario Extraction** — Extract existing use cases or generate from purpose + type + heuristics
4. **Trigger Condition Analysis** — Parse trigger phrases or derive from purpose
5. **Instruction → Behavior Mapping** — 5-phase procedure: Decomposition → Operationalization → Exemplification → Boundary Definition → Output Generation
6. **Expected Behavior Derivation** — Cross-reference content with type definitions; check technique present and effective
7. **Adversarial Scenario Generation** — Universal probes (trigger boundary, user override, precondition failure, etc.) + Type-specific probes
8. **Scenario Assembly and Prioritization** — Combine all sources, score on 4 dimensions (centrality, impact, likelihood, uniqueness), assign P0/P1/P2, select 5-7 scenarios

---

### Part 6: Gaps Addressed This Session

#### Step 5 Procedure (Was Undefined)

Now includes:
- Instruction extraction method
- 5-phase interpretation procedure
- Proxy discovery method
- Confidence levels
- Handling for unparseable instructions

#### Purpose-Unclear Handling (Was a Punt)

Now includes:
- Goal inference method
- Goal clustering method
- Purpose hypothesis generation
- Handling for "purpose-incoherent" skills

#### Prioritization Criteria (Were Missing)

Now includes:
- 4 scoring dimensions with operationalization
- Explicit P0/P1/P2 thresholds
- Selection algorithm
- Calibration guidance

---

### Part 7: Review Findings (from 3 Subagents)

**Critical Gaps (All Addressed):**

| Gap | Resolution Status |
|---|---|
| Step 5 undefined | Addressed with 5-phase procedure |
| Purpose paradox | Addressed with hypothesis generation |
| Prioritization criteria | Addressed with scoring system |
| Circular reasoning | Reduced but not eliminated (irreducible) |
| No failure handling | Partially addressed — needs step-by-step protocols |

**Edge Cases That Break Framework:**

| Case | Status |
|---|---|
| Meta-skills | Not addressed |
| Composite skills | Not addressed |
| Negative-space skills | Partially addressed |
| Context-dependent skills | Partially addressed |
| Probabilistic skills | Not addressed |

**Missing Scenario Types:**

| Type | Status |
|---|---|
| Interaction (skill combinations) | Not addressed |
| Degradation (partial failure) | Not addressed |
| Meta (when NOT to activate) | Addressed via trigger negative |
| Recovery (mid-execution failure) | Not addressed |
| Scale (simple vs complex) | Not addressed |

**The Fundamental Tension:**
"The framework is designed to test whether skills achieve their purposes. But if purposes are unclear, the framework tests whether skills match their documentation — which is a sophisticated form of structural compliance, not functional assessment."

The framework mitigates but doesn't fully solve the oracle problem.

---

### Part 8: Irreducible Elements

**Judgment Points:**

| Point | Why Irreducible |
|---|---|
| Proxy selection | Requires understanding what term is "about" |
| Goal inference | Requires understanding instruction intent |
| Purpose centrality | Requires understanding what matters |
| Failure impact | Requires understanding consequences |

These are structured and traceable, but not eliminable.

**The Oracle Problem:**
To judge whether skill-assisted behavior is "correct," we need to know what correct looks like. This requires either:
- Pre-existing ground truth (planted issues, known-good skills)
- Human judgment (doesn't scale)
- Another Claude instance (same biases)

The framework uses criteria-based evaluation with Claude-as-evaluator, making criteria explicit and auditable.

---

### Part 9: Open Questions (from Original Handoff)

| Question | Status |
|---|---|
| How should the new skill architecture be structured? | Not yet addressed |
| How should we approach designing scenarios? | Addressed (this session's focus) |
| What threshold defines "good enough" improvement? | Not yet addressed |

---

### Part 10: What's Missing for Implementation

| Item | Priority | Status |
|---|---|---|
| Skill architecture design | High | Not started |
| Subagent orchestration design | High | Not started |
| "Good enough" threshold definition | High | Not started |
| Failure protocols per step | Medium | Not started |
| Step dependency graph | Medium | Not started |
| Worked example (apply to real skill) | Medium | Not started |
| Interaction scenario extension | Low | Not started |
| Edge case handling (meta-skills, etc.) | Low | Not started |

---

### Part 11: Key Insights Summary

1. **Form vs. Function Conflation:** Structural compliance ≠ functional effectiveness
2. **The Measurement Problem:** Structural compliance is checkable; functional effectiveness requires empirical observation
3. **Aspirational vs. Operational:** Skills ask right questions but provide no method for answering them
4. **The Discipline Skill Paradox:** If assessment is a checklist, Claude completes it without substantive analysis
5. **Simulation-Based Assessment:** Replace theoretical with empirical using subagents
6. **Quality Over Quantity:** 5 well-chosen scenarios matter more than volume
7. **Variance is Signal:** Investigate outliers rather than averaging them out
8. **Avoiding Overfitting:** Holdout scenarios, rotation, adversarial design, root-cause fixing
9. **Hard-to-Test ≠ Untestable:** Different categories require different mitigations
10. **Assessment Hierarchy:** Empirical primary, theoretical supporting
11. **Scenario Generation is the Bottleneck:** Can't test improving-skills without testing target skills
12. **Irreducible Judgment:** Some interpretation is structured but not eliminable

---

Does this checkpoint now capture the full state? What would you like to address next?

## Turn 31: User

Create a file at docs/ with the comprehensive framework. This must cover all steps exhaustively and include all components. It is critically important that this file is 100% thorough and all-inclusive. Do not omit any details that are relevant to the framework. This file must be self-contained.

## Turn 32: Assistant

[Tool #7: Write docs/frameworks/simulation-based-skill-assessment_v0.1.0.md]

I've created the comprehensive framework document. Let me verify its completeness.

[Tool #8: Grep for section headers]
[Tool #9: Count lines]

The document is 2,164 lines with comprehensive coverage:

**Structure verified:**

| Section | Content |
|---|---|
| 1. Introduction | Purpose, problem statement, root cause analysis, solution overview |
| 2. Theoretical Foundation | Assessment hierarchy, simulation mechanism, principles, limitations |
| 3. Scenario Generation | All 8 steps with full procedures, schemas, and examples |
| 4. Scenario Execution | Subagent configuration, baseline/test measurement, delta evaluation |
| 5. Gap Analysis | Gap identification, root cause classification, fix generation, iteration |
| 6. Supporting Components | Schema, success criteria, overfitting prevention, hard-to-test, cost |
| 7. Reference Tables | Type indicators, proxy mappings, shortcut patterns, probe library |
| 8. Key Insights | 12 synthesized principles from the framework development |

**Document includes:**
- Complete 5-phase instruction interpretation procedure (Step 5)
- Purpose hypothesis generation for unclear skills
- Full prioritization scoring system with operationalization
- Scenario schema (YAML format)
- All probe libraries (universal + type-specific)
- Subjective term proxy mappings
- Shortcut pattern library
- Cost calibration guidance
- Known limitations and irreducible judgment points

The document is self-contained at `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`.

## Turn 33: User

Review docs/frameworks/simulation-based-skill-assessment_v0.1.0.md for completeness

## Turn 34: Assistant

[Tool #10: Task — Review framework document for completeness]

The review is complete. Here's the summary:

---

### Review Summary

**Overall Completeness: 92%**

#### What's Complete

| Section | Status | Notes |
|---|---|---|
| 1. Introduction | ✓ Complete | Root cause analysis fully captured |
| 2. Theoretical Foundation | ✓ Complete | Hierarchy, mechanism, limitations documented |
| 3. Scenario Generation (8 steps) | 95% | All steps present; Step 3 missing output schema |
| 4. Scenario Execution | ✓ Complete | Subagent config, measurement, delta evaluation |
| 5. Gap Analysis | ✓ Complete | Gap types, root causes, iteration protocol |
| 6. Supporting Components | 95% | Cost/benefit rationale could be expanded |
| 7. Reference Tables | ✓ Complete | All 4 tables with full content |
| 8. Key Insights | ✓ Complete | All 12 insights documented |

**Verified complete:**
- Step 5's 5-phase interpretation procedure (Phases A-F)
- Step 8's prioritization system (scoring, algorithm, thresholds)
- All YAML schemas (except Step 3)

---

#### Gaps Found

| Priority | Gap | Recommendation |
|---|---|---|
| High | No worked example | Add Section 3.10 walking through a real skill |
| High | No subagent orchestration details | Add Section 4.0 or note as out-of-scope |
| High | Step 3 missing output schema | Add YAML schema like other steps |
| Medium | No step failure protocols | Add subsection to 3.1 for failure handling |
| Medium | No step dependency graph | Add visual diagram to 3.1 |

---

#### Inconsistencies Found

| Issue | Location | Fix |
|---|---|---|
| Scenario count: "5" vs "5-7" | Section 2.3 vs 3.9 | Clarify 5 is default, 7 is max |
| Priority labels: P1/P2 in Step 7, P0/P1/P2 in Step 8 | Sections 3.8 and 3.9 | Harmonize or explain promotion |
| Holdout math: 3-4 dev + 1-2 holdout = 4-6, not 5-7 | Section 6.3 | Clarify for different suite sizes |

---

### Verdict

Suitable as v0.1.0 draft. The document successfully operationalizes the simulation-based assessment concept with:
- Clear procedures for all 8 steps
- YAML schemas for structured outputs
- Reference tables for operational use
- Explicit acknowledgment of limitations

For v1.0: Address high-priority gaps (worked example, subagent orchestration, Step 3 schema) and resolve inconsistencies.

---

Would you like me to address any of the high-priority gaps now?

## Turn 35: User

If I started a new session, with no context other than `simulation-based-skill-assessment_v0.1.0.md`, would Claude have a complete understanding of everything that was discussed in this session? Imagine you had no information other than the information present in `simulation-based-skill-assessment_v0.1.0.md` - what questions would you be left with?

## Turn 36: Assistant

Let me put myself in the position of a new Claude instance with only this document.

---

### Questions I'd Be Left With

#### 1. What Is This Framework FOR?

The document describes a methodology but never explicitly states:
- "This is a specification for rebuilding the improving-skills skill"
- "A skill will implement this framework"
- "This is meant to be automated/manual/hybrid"

I'd understand the methodology but not what artifact results from it.

#### 2. Where Is the Current improving-skills Skill?

The document critiques it but never shows it. I can't verify the root cause analysis or understand what's being replaced.

#### 3. Who/What Executes This Framework?

The document reads like instructions, but for whom?
- Is this for a human to follow manually?
- Is this for Claude to follow as a skill?
- Is this for an automated system?

The tone shifts between describing what happens and instructing what to do.

#### 4. How Do Subagents Actually Work?

Section 4 describes configuration but not mechanics:
- How do I "deploy a subagent"?
- How do I inject/exclude skill content from system prompts?
- How do I capture observations?
- What tool or API does this use?

#### 5. What's the Relationship Between This Document and the Skill?

If this becomes a skill:
- Does the skill contain all 2,000+ lines?
- Does it reference this document?
- Is there a condensed operational version?

The document doesn't explain how it will be used.

#### 6. Where Does skills-guide.md Come From?

The document references skill types (Discipline, Technique, Pattern, Reference) and indicators, but doesn't explain these come from an existing guide. A new reader would wonder: "Are these standard definitions or invented here?"

#### 7. What's the Discussion Document?

Referenced multiple times as the source, but:
- Where is it?
- Is this summary complete?
- Do I need to read it for full context?

#### 8. Why These Specific Choices?

| Decision | Document Says | But Why? |
|---|---|---|
| 5-7 scenarios | Target count | Why not 3? Why not 10? |
| 4 skill types | Classification system | Are these exhaustive? Standard? |
| P0/P1/P2 priorities | Scoring thresholds | Why ≥10 for P0? |
| 3 iterations default | Iteration limit | Based on what? |

The document states decisions but doesn't always justify them.

#### 9. What Happens After Framework Execution?

The document ends with scenarios and gap analysis. But:
- How do improvements get applied to the skill?
- How is the improved skill deployed?
- What's the full lifecycle?

#### 10. How Does This Fit Into the Project?

The document is in `docs/frameworks/` but:
- What project is this?
- What other frameworks exist?
- How does this integrate with the skills system?

#### 11. What Are the Open Items Actually Blocking?

The "Open Items" table lists things as "Not started" but doesn't explain:
- Can the framework be used without them?
- What's the minimum viable version?
- What's the priority order?

#### 12. Is This Complete Enough to Implement?

The 92% completeness suggests yes, but a new reader would wonder:
- Can I build a skill from this?
- What's missing that would block me?
- Are the gaps documented or hidden?

---

### Summary: What's Missing for Self-Containment

| Missing Element | Impact |
|---|---|
| Explicit purpose statement | Reader doesn't know what to build |
| The current improving-skills skill | Can't verify root cause claims |
| Subagent mechanics | Can't execute Section 4 |
| Skill architecture design | Framework without container |
| Implementation roadmap | What to do with this document |
| Source references | Discussion document not accessible |
| Decision rationale | Choices seem arbitrary |
| Integration guidance | How this fits the project |

---

### The Core Gap

The document is a complete **methodology** but not a complete **specification**. It answers "how to generate scenarios and evaluate skills" but not:

1. "What artifact am I building?"
2. "How do I build it?"
3. "How do I use this document to build it?"

A new session would understand the framework intellectually but wouldn't know how to proceed to implementation.

---

Would you like me to add a preamble/introduction that addresses these gaps, making the document truly self-contained?

## Turn 37: User

yes, add a preamble to address those gaps.

## Turn 38: Assistant

[Tool #11: Read framework document opening]

[Tool #12: Update — Add preamble to framework document]

[Tool #13: Update — Add preamble to Table of Contents]

[Tool #14: Read updated document opening]

Done. The document now includes a comprehensive preamble (153 additional lines, total now 2,317 lines).

---

### Preamble Contents

The preamble addresses all the gaps identified:

| Gap | Preamble Section |
|---|---|
| What is this framework FOR? | "What This Document Is" — specification for rebuilding improving-skills |
| Who executes it? | "Who Executes This Framework" — Claude, as part of the skill |
| Relationship to the skill | "Relationship to the Skill" — diagram showing skill references framework |
| How do subagents work? | "Subagent Mechanics" — explains Task tool, baseline vs test config |
| Where do source materials live? | "Source Materials" — paths to discussion doc and handoff |
| Why these specific choices? | "Decision Rationale" — table explaining 5-7 scenarios, 4 types, P0/P1/P2, etc. |
| How does this fit the project? | "Project Context" — directory structure showing where everything lives |
| What happens next? | "Implementation Roadmap" — 6-phase plan with status |
| Can this be used now? | "Minimum Viable Usage" — what can be done before full implementation |
| How should I read this? | "Reading Guide" — navigation based on intent |

---

### New Reader Experience

A Claude instance with only this document would now understand:

1. This is a specification for rebuilding improving-skills, not the skill itself
2. Claude executes this as part of the skill, not humans manually
3. The skill will reference this document for detailed procedures
4. Subagents are spawned via Task tool with isolated context
5. Decisions have rationale (5-7 scenarios because of coverage/cost balance, etc.)
6. Phase 1 is complete and there's a clear roadmap for Phases 2-6
7. The framework can be used now for manual assessment or scenario generation

