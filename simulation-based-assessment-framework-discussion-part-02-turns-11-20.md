## Turn 11: Claude

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

## Turn 13: Claude

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

## Turn 15: Claude

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

## Turn 17: Claude

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

## Turn 19: Claude

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

