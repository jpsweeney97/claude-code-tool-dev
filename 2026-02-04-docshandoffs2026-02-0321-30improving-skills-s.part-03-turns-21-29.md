## Turn 21: Claude

I'll deploy 3 subagents with different review perspectives to get comprehensive coverage.

[Tool #4: Task — Adversarial review of scenario framework]
[Tool #5: Task — Implementation feasibility review]
[Tool #6: Task — Theoretical completeness review]

## Turn 22: Claude

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

## Turn 24: Claude

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

## Turn 26: Claude

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

## Turn 28: Claude

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

