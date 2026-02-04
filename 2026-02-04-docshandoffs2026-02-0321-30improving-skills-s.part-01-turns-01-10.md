## Turn 1: User

`docs/handoffs/2026-02-03_21-30_improving-skills-simulation-based-assessment.md`

[Tool #1: Read docs/handoffs/2026-02-03_21-30_improving-skills-simulation-based-assessment.md]

## Turn 2: Claude

I see this handoff is about redesigning the improving-skills skill based on a root cause analysis. The handoff explicitly requires reading the discussion document for full context.

Let me read that document first.

[Tool #2: Read discussion document]

## Turn 3: Claude

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

## Turn 5: Claude

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

## Turn 7: Claude

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

## Turn 9: Claude

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

