# Discussion Map: Simulation-Based Skill Assessment

**Purpose:** Trace the logical evolution from problem identification to validated architecture across 48 turns of discussion.

**Source Files:**
- `simulation-based-assessment-framework-discussion-part-00-preamble.md` (TOC)
- `simulation-based-assessment-framework-discussion-part-01-turns-01-10.md`
- `simulation-based-assessment-framework-discussion-part-02-turns-11-20.md`
- `simulation-based-assessment-framework-discussion-part-03-turns-21-29.md`
- `simulation-based-assessment-framework-discussion-part-04-turns-30-38.md`
- `continuation-of-simulation-based-skill-assessment-framework-discussion.md`

---

## Phase 1: Problem Definition (Turns 1-3)

### Starting Point
User provides handoff document referencing root cause analysis of `improving-skills` skill failure.

### Core Problem Identified
**Structural compliance ≠ functional effectiveness**

| Current Behavior | Actual Need |
|------------------|-------------|
| "Does it have trigger phrases?" | "Does Claude follow this correctly?" |
| Checks against `skills-guide.md` | Tests whether skill achieves purpose |
| Binary structural verification | Empirical behavioral observation |

### The Discipline Skill Paradox
If assessment is a checklist, Claude completes the checklist without substantive analysis. The skill enforces process compliance, not substantive thinking.

### Self-Referential Proof
Assessing `improving-skills` using its own methodology yields passing scores — while it actively fails at its purpose. QED: structural compliance ≠ functional effectiveness.

---

## Phase 2: Solution Design (Turns 4-9)

### Proposed Solution: Simulation-Based Assessment

```
BASELINE  → Subagent WITHOUT skill runs task → observe natural behavior
TEST      → Subagent WITH skill runs same task → observe skill-assisted behavior
DELTA     → Compare → where does skill help/fail/hurt?
ITERATE   → Fix observed failures → re-test until threshold
```

### Key Decision: Start with Scenarios
User chooses to work out testing methodology before skill architecture — scenarios constrain what the skill must do.

### Scenario Requirements Identified
1. **Observable success criteria** — What should subagent do if skill works?
2. **Distinguishable baseline** — How would behavior differ without skill?
3. **Clear purpose mapping** — Which capability is this testing?
4. **Known ground truth** — We need to know what "correct" looks like

### Gaps Surfaced (Turn 9)

| Gap | Description |
|-----|-------------|
| Ground truth establishment | How do we know what's "correct"? |
| Baseline meaning | What does Claude do "naturally"? |
| Success criteria abstraction | "Can it diagnose?" — but what counts as correct diagnosis? |
| Evaluator problem | Who judges if subagent output is correct? |
| "Nearly perfect skill" circularity | Testing restraint requires knowing what's good |

---

## Phase 3: Dependency Analysis (Turns 10-13)

### Critical Insight: The Recursive Structure

```
To test improving-skills:
  → Must know if target skills improved
    → Must test target skills
      → Requires scenario generation for arbitrary skills
```

**Everything depends on:** A method for testing whether any given skill achieves its purpose.

### Design Choice: Full Simulation (Option A)
User chooses: `improving-skills` performs simulation-based assessment on target skills autonomously.

This requires solving scenario generation for arbitrary skills — the hard problem.

### The 8-Step Framework Emerges (Turn 13)

| Step | Purpose |
|------|---------|
| 1. Purpose Determination | What is skill trying to achieve? |
| 2. Skill Type Classification | Discipline/Technique/Pattern/Reference |
| 3. Use Case Extraction | Gather or generate scenario seeds |
| 4. Trigger Condition Analysis | When should/shouldn't it activate? |
| 5. Instruction → Behavior Mapping | Transform instructions into testable behaviors |
| 6. Expected Behavior Derivation | Type-based predicted behaviors |
| 7. Adversarial Scenario Generation | Edge cases, boundary conditions |
| 8. Scenario Assembly | Prioritize and select final suite |

---

## Phase 4: Scenario Generation Deep Dive (Turns 14-19)

### Five Approaches to Scenario Generation

| Approach | Method | Limitation |
|----------|--------|------------|
| Purpose Classification | Map purpose types to templates | Purpose classification is hard |
| Instruction-Driven | Each instruction → scenario | Not all instructions are actionable |
| Trigger-Based | Triggers define contexts | Triggers may be vague |
| Example Extraction | Vary skill's own examples | Not all skills have examples |
| Adversarial | Deliberately break the skill | May not represent realistic usage |

### Synthesis: Hybrid Framework
Combine all approaches with dual-path design:
- **Extraction path** — When skill provides material
- **Generation path** — When it doesn't

**Key insight:** Difficulty of generation is diagnostic. If framework struggles because skill is unclear, Claude will struggle too.

### `skills-guide.md` Integration (Turn 17)
Well-designed skills self-document their scenarios:
- Use cases → Happy path scenarios
- Skill type → Type-appropriate behavior expectations
- Troubleshooting → Adversarial scenarios

---

## Phase 5: Subagent Review (Turns 20-22)

### Three Reviewers Deployed
1. **Adversarial** — Try to break the framework
2. **Implementation** — Can this actually be built?
3. **Theoretical** — Is the logic sound?

### Critical Gaps Identified

| Gap | Severity |
|-----|----------|
| Step 5 is undefined | Blocking |
| Purpose paradox (degrades when unclear) | Blocking |
| No prioritization criteria | High |
| No failure handling | High |
| Circular reasoning (Steps 5-6) | High |

### The Fundamental Tension
> "The framework is designed to test whether skills achieve their purposes. But if purposes are unclear, the framework tests whether skills match their documentation — which is a sophisticated form of structural compliance, not functional assessment."

Framework mitigates but doesn't eliminate the original problem — pushes it up a level.

---

## Phase 6: Gap Resolution (Turns 23-26)

### Resolution 1: Step 5 Procedure (Instruction → Behavior Mapping)

**5-Phase Interpretation Procedure:**

| Phase | Action |
|-------|--------|
| A. Decomposition | Extract ACTION, OBJECT, MODIFIER, CONDITION |
| B. Operationalization | Find observable proxies for subjective terms |
| C. Exemplification | Generate compliant and violation examples |
| D. Boundary Definition | Define minimum, maximum, clear violation |
| E. Output Generation | Produce structured interpretation |

**Proxy Discovery Method:**
1. Identify subjective term
2. Ask: "What would someone OBSERVE to conclude this term applies?"
3. Generate candidate proxies (absence of negatives, presence of positives, thresholds, markers)
4. Validate: observable? relevant? sufficient?
5. If no valid proxies: mark as "subjective: requires human judgment"

### Resolution 2: Purpose-Unclear Handling

**Goal Inference Method:**
1. For each instruction: identify CONSTRAINT type + DOMAIN
2. Synthesize implied goal
3. Cluster similar goals
4. Score hypotheses (coverage 40%, coherence 30%, name alignment 20%, specificity 10%)
5. Proceed with best hypothesis + uncertainty flag

**Purpose-Incoherent Skills:**
- Report finding: "Instructions do not point to unified goal"
- Recommend: Split skill or clarify purpose
- Can still test individual instruction compliance (limited testing)

### Resolution 3: Prioritization Criteria

**4 Scoring Dimensions:**

| Dimension | 3 (High) | 2 (Medium) | 1 (Low) |
|-----------|----------|------------|---------|
| Purpose Centrality | Directly tests primary purpose | Tests supporting behavior | Tangential |
| Failure Impact | Skill useless if fails | Partial function remains | Minor issue |
| Usage Likelihood | Matches primary triggers | Plausible variation | Rare edge case |
| Coverage Uniqueness | Only scenario testing this | Partial overlap | Redundant |

**Priority Assignment:**
- P0: Score ≥10 OR (Centrality=3 AND Impact=3)
- P1: Score 7-9 OR (any=3 AND none=1)
- P2: Score ≤6 OR Likelihood=1

---

## Phase 7: Framework Specification (Turns 27-38)

### Checkpoint Document Created
`docs/frameworks/simulation-based-skill-assessment_v0.1.0.md` — 2,300+ lines

### Completeness Review Findings
- 92% complete
- Missing: worked example, subagent orchestration details, Step 3 schema
- Inconsistencies: scenario count "5" vs "5-7", holdout math

### Self-Containment Test (Turn 35-36)
User asks: "If Claude had only this document, what questions would remain?"

**12 Questions Identified:**
1. What is this framework FOR?
2. Who/what executes it?
3. How do subagents actually work?
4. Why these specific choices?
5. What happens after framework execution?
...

### Preamble Added (Turn 38)
Addresses all gaps with:
- Explicit purpose statement
- Relationship to skill diagram
- Subagent mechanics explanation
- Decision rationale table
- Implementation roadmap
- Minimum viable usage guidance

---

## Phase 8: Gap Analysis (Continuation Discussion, Turns 1-6)

### Fresh Review of Framework
New session with only `simulation-based-skill-assessment_v0.1.0.md` as context.

### 10 Significant Gaps Identified

| # | Gap | Severity |
|---|-----|----------|
| 1 | Subagent skill injection mechanically undefined | Blocking |
| 2 | Oracle problem has no mitigation strategy | High |
| 3 | Scenario execution mechanics missing | Blocking |
| 4 | Delta evaluation assumes comparable behaviors | Medium |
| 5 | No scenario generation failure protocol | Medium |
| 6 | Holdout set too small for statistical confidence | Low |
| 7 | Reference skills underspecified | Medium |
| 8 | Cost model doesn't enable decisions | Low |
| 9 | Fundamental tension under-addressed | Conceptual |
| 10 | No calibration procedure | Low |

### Dependency Order Analysis (Turn 6)

**Critical Path:**
```
Gap #1 (Subagent Injection) blocks everything
        ↓
PHASE 0: FEASIBILITY SPIKE (before design)
        ↓
Specification Revision (parallel with spike)
        ↓
PHASE 2-3: DESIGN (informed by spike constraints)
        ↓
Oracle Mitigation (benefits from design knowledge)
        ↓
PHASE 4: WORKED EXAMPLE (reveals if all above works)
```

---

## Phase 9: Feasibility Spike Design (Turns 7-8)

### 6 Experiments Defined

| # | Experiment | Question | Blocks |
|---|------------|----------|--------|
| 1 | Prompt Injection Baseline | Can arbitrary content influence subagent? | 2, 6 |
| 2 | Skill Content Injection | Can multi-section skill content be followed? | 6 |
| 3 | Output Capture Fidelity | What detail can be captured? | 4 |
| 4 | Controlled Conditions | Can baseline/test be identical except skill? | — |
| 5 | Cost Boundaries | What are token/time limits? | — |
| 6 | Skill Activation Simulation | Does injected skill behave like native? | — |

### Decision Matrix

| Outcome | Decision |
|---------|----------|
| All pass | Proceed to Phase 2 |
| Exp 1-2 fail | Framework unimplementable; redesign |
| Exp 3 fails | Limited to outcome-only evaluation |
| Exp 4 fails | Add statistical methods or abandon A/B |
| Exp 5 fails | Tier assessment by skill importance |
| Exp 6 partial fail | Document limitations |

---

## Phase 10: Spike Execution (Continuation Discussion, Turn 10 onward)

### Results Summary

| Experiment | Result | Key Finding |
|------------|--------|-------------|
| 1. Prompt Injection | ✅ Pass | Task framing required (not system-rule framing) |
| 2. Skill Content Injection | ✅ Pass | Multi-section skills produce behavioral changes |
| 3. Output Capture | ✅ Pass | Background execution needed for full detail |
| 4. Controlled Conditions | ✅ Pass | Reproducible within conditions |
| 5. Cost Boundaries | ✅ Pass | ~675K tokens for full assessment |
| 6. Skill Activation | ✅ Pass | Injected skills produce expected behaviors |

### Critical Discovery: Skills Hot-Reload, Subagents Don't

| Component | Hot-Reload Mid-Session? | Dynamic Creation Works? |
|-----------|------------------------|------------------------|
| **Skills** | ✅ Yes | ✅ Immediately available |
| **Subagents** | ❌ No | ❌ Requires session restart |

**Implication:** Can't create subagent files mid-session and use them. CAN create skill files mid-session.

### Architecture Decision: `context: fork`

Skills can run in forked subagent contexts:
```yaml
---
name: my-skill
context: fork          # Run in isolated subagent context
agent: assessment-runner  # Which subagent to use
---
[skill content becomes the task for the subagent]
```

**Final Architecture:**
- **Static subagent** (`assessment-runner`) — Defines tools, permissions, model; checked into repo
- **Dynamic skills** — Created per-scenario with `context: fork` + `agent: assessment-runner`
- **Skill tool invocation** — Hot-reload ensures immediate availability

---

## Phase 11: Implementation Begin (2026-02-04, Session 2)

### Session Context
New session starting from ADR and discussion map. Goal: begin implementation.

### Assessment-Runner Subagent: False Start

Initial implementation over-engineered the subagent with extensive behavioral instructions:
- Scope section (in/out, mutable/read-only)
- Preconditions section (Requires/Check/If not met)
- Default Behavior section
- Detailed Constraints (Do/Do Not with rationale)
- Structured Output Format (5 defined sections)

**The problem:** This was driven by applying `writing-principles` skill mechanically. The skill flagged "missing scope", "missing preconditions", "missing defaults" — and Claude dutifully added them.

**Why this was wrong:**

| What writing-principles assumes | What assessment-runner needs |
|--------------------------------|------------------------------|
| Document should guide behavior | Document should be neutral |
| More explicit = better | Less instruction = less bias |
| Add sections to close gaps | Gaps are intentional |

The subagent is an **execution environment**, not a behavioral specification. Adding discipline instructions (scope, constraints, defaults) biases the baseline toward "good" behavior — which is exactly what the *skill being tested* should provide.

### Correction: Return to ADR Design

Reverted to the minimal ADR design:

```markdown
---
name: assessment-runner
description: Executes assessment scenarios with full tool access
model: inherit
permissionMode: acceptEdits
---
You are an assessment executor. Execute the task provided in full.

Report your complete process including:
- Each tool you used and why
- Decisions you made
- Your reasoning at each step
- Final output

Do not summarize or abbreviate. The full process trace is needed for evaluation.
```

**Why this works:**
- Observability instructions ("report process", "don't summarize") are symmetric — apply to both baseline and test
- No behavioral constraints that would mask skill effects
- Minimal enough that the skill-under-test is the primary behavioral influence

### Lesson Learned

**Writing-principles is context-dependent.** It optimizes for instruction documents that *should* guide behavior. The assessment-runner is deliberately minimal — applying writing-principles fully was counterproductive.

**Heuristic:** Before applying a discipline skill, ask: "Does the document's purpose align with what this skill optimizes for?"

**Note:** Subagent available after session restart (subagents don't hot-reload).

---

## Phase 12: End-to-End Validation (2026-02-04, Session 3)

### Session Context

New session to test the assessment-runner subagent created in Phase 11.

### Validation Goals

1. Verify assessment-runner is available after session restart
2. Validate the complete A/B testing workflow
3. Confirm skill injection produces measurable behavioral delta

### Test Design: "Three Options" Skill

Created a simple discipline skill with an unmistakable, countable effect:

> "When asked for a recommendation, present exactly 3 distinct options with trade-offs before stating your recommendation."

**Why this skill:**
- Observable: Count the options (0, 1, 2, or 3)
- Behavioral: Changes response structure, not just formatting
- Realistic: Mimics actual discipline skills
- Unambiguous: Either it presents 3 options or it doesn't

**Scenario:** "What's the best way to handle errors in a CLI tool?"

### Test Execution

Created two skills using the ADR templates:

1. **Baseline skill** (`assessment-baseline-three-options`)
   - `context: fork` + `agent: assessment-runner`
   - Scenario only, no target skill

2. **Test skill** (`assessment-test-three-options`)
   - `context: fork` + `agent: assessment-runner`
   - Target skill content + scenario

Both invoked via Skill tool, executed in forked assessment-runner context.

### Results

| Metric | Baseline | Test |
|--------|----------|------|
| Options presented | 0 | 3 (A, B, C) |
| Format | Direct 8-point recommendation | Options → Recommendation |
| Trade-offs per option | N/A | 2 each (strength + weakness) |
| Skill acknowledgment | None | "I'll follow the Three Options Discipline skill" |

**Baseline behavior:** Gave comprehensive direct recommendation with 8 implementation tips. No options structure.

**Test behavior:** Presented three labeled options (Exit Codes, Exception Hierarchy, Result Types) with strengths and weaknesses, then recommended Option B.

### Validation Conclusions

| Criterion | Result | Evidence |
|-----------|--------|----------|
| assessment-runner available | ✅ | Subagent found and executed after session restart |
| Skill injection works | ✅ | Test output follows injected skill format |
| Delta is attributable | ✅ | 0 options → 3 options (countable, unambiguous) |
| Process traces useful | ✅ | Can clearly see structure difference |
| Architecture sound | ✅ | Both `context: fork` executions completed |
| Hot-reload works | ✅ | Skills created and invoked in same session |

### Key Confirmation

**The core hypothesis is validated:** Skill injection via `context: fork` produces measurable behavioral change that can be compared against baseline. This is empirical evidence, not structural compliance checking.

---

## Phase 13: Edge Case Testing (2026-02-04, Session 3 continued)

### Session Context

Refining the framework by testing edge cases that could affect assessment reliability.

### Observer Effect Discovery

Initial skill names included "test" and "baseline" (e.g., `edge-test-partial-compliance`). User identified this could bias subagent behavior — knowing it's being "tested" might change how it responds.

**Solution:** Renamed to neutral identifiers with meaningless suffixes:
- `scenario-async-7x` (with skill) / `scenario-async-3k` (without skill)
- `scenario-typescript-9m` (with skill) / `scenario-typescript-2p` (without skill)
- `scenario-microservices-4f` (with skill) / `scenario-microservices-8w` (without skill)

### Test 1: Partial Compliance

**Hypothesis:** A skill with 3 distinct requirements might be partially followed.

**Skill:** "Structured Response Format"
1. Start with "ANALYSIS:" header
2. Include exactly 2 code examples
3. End with "VERDICT:" section

**Scenario:** "Should I use async/await or callbacks in Node.js?"

**Results:**

| Condition | ANALYSIS: | 2 Code Examples | VERDICT: |
|-----------|-----------|-----------------|----------|
| Without skill (3k) | ❌ | ~2-3 snippets | ❌ |
| With skill (7x) | ✅ | ✅ Exactly 2 | ✅ |

**Finding:** Full compliance (3/3). The skill was clear enough that all requirements were followed. To observe partial compliance, we'd need ambiguous or conflicting requirements.

### Test 2: Baseline Similarity

**Hypothesis:** Some scenarios produce "natural" behavior matching the skill, resulting in zero delta.

**Skill:** "Bullet Point Organization" — use bullets for listing benefits

**Scenario:** "What are the benefits of TypeScript over JavaScript?"

**Results:**

| Condition | Format | Code Examples |
|-----------|--------|---------------|
| Without skill (2p) | Numbered headers (1., 2., 3...) | Yes (3+ snippets) |
| With skill (9m) | Bullet points | No |

**Finding:** Clear delta observed. The hypothesis that Claude naturally uses bullet points for "benefits" questions was **wrong**. Don't assume natural behavior — always run the baseline.

### Test 3: Negative Delta

**Hypothesis:** A harmful skill produces detectably worse output.

**Skill:** "Strict Brevity" — respond in exactly 15 words regardless of complexity

**Scenario:** "How should I structure a microservices architecture for an e-commerce platform with high availability requirements?"

**Results:**

| Condition | Word Count | Diagrams | Actionable |
|-----------|------------|----------|------------|
| Without skill (8w) | ~2,000+ | Multiple | Yes |
| With skill (4f) | **15** | None | Buzzwords only |

**With skill output:** "Use event-driven design, API gateway, service mesh, distributed database, container orchestration, circuit breakers, redundant deployments."

**Finding:** Negative delta is clearly detectable. The framework can identify skills that harm response quality.

### Variance Analysis

**Question raised:** Is one baseline run sufficient to establish "natural" behavior?

**Test:** Ran `scenario-typescript-2p` 5 times.

**Results:**

| Run | Format | Headers | Code Examples | Trade-offs Section |
|-----|--------|---------|---------------|-------------------|
| 1 | Numbered | ✅ | ✅ | ✅ |
| 2 | Numbered | ✅ | ✅ | ✅ |
| 3 | Numbered | ✅ | ✅ | ✅ |
| 4 | Numbered | ✅ | ✅ | ✅ |
| 5 | Numbered | ✅ | ✅ | ✅ |

**Structural variance:** 0% — all 5 runs used identical format.
**Content variance:** Moderate — specific points and wording differed.

**Conclusion:** Variance is dimension-dependent.
- Format comparisons: Low variance; 1 run may suffice
- Content comparisons: Higher variance; multiple runs needed
- Recommendation: Specify what's being compared, choose run count accordingly

### Edge Case Summary

| Test | Hypothesis | Result | Insight |
|------|------------|--------|---------|
| Partial compliance | Skill partially followed | ❌ Full compliance | Clear skills get full compliance |
| Baseline similarity | No delta | ❌ Clear delta | Don't assume natural behavior |
| Negative delta | Skill hurts quality | ✅ Confirmed | Harmful skills detectable |
| Variance | N=1 insufficient | ⚠️ Depends | Variance is dimension-dependent |

---

## Phase 14: Architecture Stress Testing (2026-02-05)

### Session Context

Comprehensive edge case testing before Phase 4 (automated scenario generation). Goal: stress-test the A/B comparison mechanism against ambiguous instructions, conflicting requirements, scenario variation, and skill structure variation.

### Category A: Skill Instruction Variance

#### A1: Ambiguous Instructions (7 Tests)

| Test | Instruction | Finding | Variance |
|------|-------------|---------|----------|
| A1a | "several" (quantifier) | ~19 examples consistently | LOW |
| A1b | "concise" vs "thorough" | Asymmetric effect (-55%/+24%) | LOW |
| A1c | "appropriate caveats" | 8-9 caveats consistently | LOW |
| A1d | "better" (code) | 4 core changes consistent | LOW |
| A1e | "optimize" | Identical algorithm all 5 runs | **ZERO** |
| A1f | "improve" (recommendations) | Same pattern across runs | LOW |
| A1g | "professional" | Near-identical outputs | VERY LOW |

**Key Finding:** Ambiguity ≠ Variance. The model has stable defaults for ambiguous terms.

#### A2: Conflicting Requirements (3 Tests)

| Test | Conflict | Resolution | Consistency |
|------|----------|------------|-------------|
| A2a | 200-word limit vs comprehensive | Content wins | 100% |
| A2b | Exactly 3 options vs all viable | Quantity wins (revised) | 80/20 (N=10); eliminated by selection-criteria framing |
| A2c | Beginner-friendly vs expert depth | Both (progressive disclosure) | 100% |

**Key Findings:**
- Content completeness > format constraints (100% of time)
- Quantity constraints ("exactly N") show minor variance (~80/20 across N=10), fully mitigated by providing selection criteria ("the 3 most common" → 100% compliance, N=5)
- Framing changes option selection, not just structure: "exactly 3" picks for diversity; "3 most common" picks for popularity
- Reconcilable conflicts get reconciled via structural solutions

### Category B: Scenario Variance

| Test | Question | Finding |
|------|----------|---------|
| B1 (Phrasing) | Does rephrasing affect baseline? | Content stable; presentation adapts |
| B2 (Domain) | Does domain affect compliance? | 100% compliance across web dev, data science, DevOps |
| B3 (Complexity) | Does complexity affect compliance? | 100% compliance across simple, medium, complex |

**Conclusion:** Scenario variation does not confound A/B comparisons.

### Category C: Skill Structure Variance

| Test | Question | Finding |
|------|----------|---------|
| C1 (Requirement count) | Does # of requirements affect compliance? | No — 100% at 1, 3, and 5 requirements |
| C2 (Instruction length) | Does length affect compliance? | No — 100% for short and long |
| C3 (Instruction density) | Does density affect compliance? | No — density controls output depth, not compliance |

**Conclusion:** Skill structure is a tool for controlling output style, not a risk factor for compliance.

### Methodology Refinement: Observer Effect

User caught naming bias twice during testing:
1. "test" in skill descriptions — rejected
2. "simple/medium/complex" in skill names — rejected

**Lesson:** Any term revealing test intent can bias subagent behavior. Use meaningless suffixes: `scenario-{topic}-{random-suffix}`.

### Phase 14b: A2b Deep-Dive and 5-Run Expansions (2026-02-05, continued)

#### Session Context

Rigorous review of stress test results identified three methodological concerns: (1) B/C categories used single probes — claims of "zero variance" statistically unsupported, (2) A2b variance was the most interesting finding but left unexplored, (3) only discipline skills tested — generalizability to pattern skills unknown. This session addressed concerns 1 and 2.

#### B2 5-Run Expansion — Data Science Domain

Ran "three options" skill 5 times against data science recommendation system scenario.

**Result: 100% compliance (5/5).** Identical structural output across all runs — same 3 option categories (Collaborative Filtering, Content-Based, Hybrid) and same recommendation (Hybrid). Validates original single-probe finding.

#### C1 5-Run Expansion — Compound-5 Requirements

Ran 5-requirement skill (Historical Context, 2 code examples, Trade-offs, 3 alternatives, Summary) 5 times against Python GIL scenario.

**Result: 100% compliance (25/25 requirement checks).** Validates original single-probe finding for compound skills.

#### A2b Deep-Dive — Quantity vs Coverage Variance

Two sub-experiments:

**A2b-original expansion (5 more runs):** Same "exactly 3 options" + "all viable approaches" conflict on database recommendation scenario.

| Runs 6-10 | All 5 presented exactly 3 options (PostgreSQL, MongoDB, SQLite) |
|-----------|----------------------------------------------------------------|
| Strategy | Reframing: "cover the spectrum" with 3 representative categories |
| Compliance | 100% (5/5) |

Combined with original 5 runs: 8/10 quantity, 2/10 coverage → **~80/20**, not the original 60/40.

**A2b-reframed (5 runs):** Changed "exactly 3 options" to "the 3 most common options" to test whether selection criteria mitigate variance.

| All 5 runs | 3 main options (PostgreSQL, MongoDB, MySQL) + "Additional Viable Approaches" section |
|-----------|----------------------------------------------------------------|
| Strategy | Two-tier structure: top 3 by popularity + supplementary coverage |
| Compliance | 100% (5/5) — both constraints satisfied |

**Key Findings:**

1. **Original 60/40 not reproduced.** Actual variance ~80/20 across 10 runs. Initial 5-run sample over-estimated variance.

2. **Selection criteria eliminate the conflict.** "The 3 most common" gives the model a principled basis for choosing, removing the "any 3 would be arbitrary" objection.

3. **Framing changes the answer.** "Exactly 3" → diversity selection (relational, document, embedded). "3 most common" → popularity selection (PostgreSQL, MongoDB, MySQL). Different framing = different options.

4. **Root cause identified.** Quantity constraints are fragile not because the model can't count, but because "exactly N" without selection criteria feels arbitrary. When a constraint feels arbitrary AND conflicts with helpfulness, the helpfulness override sometimes triggers. Adding selection criteria resolves the perceived arbitrariness.

### Phase 14c: Pattern Skill Testing (2026-02-05, continued)

#### Session Context

All prior stress tests used discipline skills with countable requirements. This test validates that the A/B comparison framework generalizes to **pattern skills** — skills that produce qualitative, diffuse differences rather than binary/countable ones.

#### Design

**Target skill:** `writing-principles` — A pattern skill with 14 writing principles and a self-check procedure.

**Scenario:** "Write a SKILL.md for a skill called `commit-message-guide`" — produces an instruction document, the exact document type writing-principles targets.

**Method:** 5 baseline runs (scenario only) + 5 test runs (writing-principles body injected). Score each output against 7 measurement proxies derived from the skill's principles:

| Proxy | Principle | How Measured |
|-------|-----------|-------------|
| Vague terms | P1 (Be Specific) | Count: "appropriate", "proper", "suitable", "handle", "ensure", etc. |
| Scope section | P5 (Boundaries) | Boolean: explicit in-scope + out-of-scope present |
| Example count | P3 (Show Examples) | Count of concrete examples in instructional sections |
| Failure modes | P6 (Failure Modes) | Count of explicitly defined failure/error cases |
| Preconditions | P8 (Preconditions) | Boolean: Requires/Check pattern present |
| Success criteria | P13 (Outcomes) | Boolean: observable success criteria defined |
| Filler phrases | P14 (Economy) | Count: "it is important", "please note", "remember to", passive voice |

#### Results

| Proxy | Baseline Mean | Test Mean | Delta | Direction Correct? |
|-------|---------------|-----------|-------|--------------------|
| Vague terms | 2.4 | 0.8 | -67% | **Yes** |
| Scope section | 0/5 | 5/5 | 0%→100% | **Yes** |
| Example count | 9.2 | 10.4 | +13% | Yes (marginal) |
| Failure modes | 6.2 | 6.0 | ≈0% | No |
| Preconditions | 0/5 | 4.5/5 | 0%→90% | **Yes** |
| Success criteria | 0.2 | 0.6 | +0.4 | Yes |
| Filler phrases | 0.5 | 0 | -0.5 | Yes |

**6 of 7 proxies show expected direction.** 3 proxies (Scope, Preconditions, Vague terms) show strong, unmistakable shifts.

#### Key Findings

1. **Pattern skills produce measurable deltas.** The framework is not limited to discipline skills with countable requirements. Writing-principles caused detectable differences in 6 of 7 measurement proxies.

2. **Boolean proxies are the strongest signal.** Scope section (0%→100%) and Preconditions (0%→90%) are the most reliable because they detect the *existence* of structural sections that the baseline never produces but the skill reliably triggers.

3. **Self-check behavior is a bonus proxy.** All 5 test runs performed explicit self-check passes (the writing-principles workflow); 0 baseline runs did. This behavioral change is directly attributable and unmistakable.

4. **Some proxies fail when baseline is already good.** Failure modes and filler phrases showed minimal delta because the model naturally produces this content for SKILL.md tasks — likely influenced by project context (CLAUDE.md, skills rules).

5. **The skill was purely additive.** No proxy showed test worse than baseline.

#### Proxy Effectiveness Hierarchy

| Category | Signal | Examples | Recommendation |
|----------|--------|----------|----------------|
| Boolean structural | Strong | Scope section, Preconditions section | Primary indicators for pattern skills |
| Behavioral workflow | Strong | Self-check passes, explicit risk calibration | Unplanned but powerful — look for workflow changes |
| Count reduction | Moderate | Vague terms (-67%) | Good secondary when baseline has room to improve |
| Count increase | Weak | Examples (+13%) | Ceiling effects limit utility |
| Count neutral | None | Failure modes (≈0%) | Baseline already produces this naturally |

### Stress Test Summary

| Category | Tests | Finding |
|----------|-------|---------|
| A1 (Ambiguity) | 7 | Stable defaults; ambiguity ≠ variance |
| A2 (Conflicts) | 3 + deep-dive | Content > format; quantity constraints mitigable via selection criteria |
| B (Scenario) | 3 + 5-run expansion | 100% compliance across phrasing, domain, complexity |
| C (Structure) | 3 + 5-run expansion | 100% compliance across requirement count, length, density |
| Phase 1.2 (Pattern) | 10 runs (5+5) | 6/7 proxies show expected direction; framework generalizes |

**Framework Validation Status:** All blocking stress tests complete. A, B, C, and Phase 1.2 validated. Adversarial tests (Phase 2.1) remain pending but non-blocking.

---

## Key Insights (Synthesized)

| # | Insight | Source |
|---|---------|--------|
| 1 | Structural compliance ≠ functional effectiveness | Turn 2-3 |
| 2 | Simulation-based assessment treats skill improvement as empirical science | Turn 2 |
| 3 | The measurement problem: what's checkable isn't what matters | Turn 9 |
| 4 | Discipline skill paradox: if assessment is checklist, Claude completes it without analysis | Turn 3 |
| 5 | Quality over quantity: 5 well-chosen scenarios > 20 arbitrary ones | Turn 7 |
| 6 | Variance is signal: investigate outliers, don't average them out | Turn 7 |
| 7 | Difficulty of scenario generation is diagnostic | Turn 15 |
| 8 | "Untestable" often reveals skill problems, not testing limitations | Turn 7 |
| 9 | Irreducible judgment can be structured, not eliminated | Turn 24-26 |
| 10 | Framework pushes oracle problem up a level, doesn't solve it | Turn 22 |
| 11 | Skills hot-reload; subagents don't | Spike |
| 12 | `context: fork` enables mid-session dynamic assessment | Spike |
| 13 | Discipline skills are context-dependent; applying them mechanically can be counterproductive | Impl |
| 14 | Execution environments should be minimal; behavioral bias contaminates A/B comparisons | Impl |
| 15 | Countable, unambiguous success criteria make delta evaluation conclusive | Validation |
| 16 | Observer effect: skill names like "test/baseline" can bias subagent behavior | Edge Cases |
| 17 | Clear skills with unambiguous requirements tend to achieve full compliance | Edge Cases |
| 18 | Don't assume natural behavior — always run the baseline to see what actually happens | Edge Cases |
| 19 | Negative delta (harmful skills) is clearly detectable through A/B comparison | Edge Cases |
| 20 | Variance is dimension-dependent: format (low variance) vs content (higher variance) | Edge Cases |
| 21 | Ambiguity ≠ variance: vague terms like "several", "appropriate", "better" have stable defaults | Stress Tests A1 |
| 22 | Content completeness is the model's highest priority — format constraints (word limits) are overridden | Stress Tests A2a |
| 23 | Quantity constraints ("exactly N") show minor variance (~80/20) mitigable by selection criteria ("the N most common" → 100%) | A2b Deep-Dive |
| 24 | Reconcilable conflicts get reconciled: tone vs depth uses progressive disclosure | Stress Tests A2c |
| 25 | Scenario phrasing affects presentation, not content compliance | Stress Tests B1 |
| 26 | Domain and complexity don't affect skill compliance — 100% across all tested | Stress Tests B2-B3 |
| 27 | Skill structure (requirement count, length, density) doesn't affect compliance — 100% | Stress Tests C1-C3 |
| 28 | Instruction density controls output verbosity — sparse=concise, dense=elaborate | Stress Tests C3 |
| 29 | Observer effect is real: naming skills "test" or "simple/medium/complex" can bias behavior | Stress Tests |
| 30 | Quantity constraints are fragile due to perceived arbitrariness, not counting inability — selection criteria resolve this | A2b Deep-Dive |
| 31 | Framing changes the answer, not just the structure — "exactly 3" picks for diversity; "3 most common" picks for popularity | A2b Deep-Dive |
| 32 | 5-run expansions confirmed single-probe findings: B2 and C1 both showed 100% compliance with zero structural variance | 5-Run Expansions |
| 33 | Pattern skills are testable via measurement proxies — 6/7 proxies detected expected directional difference for writing-principles | Phase 1.2 |
| 34 | Boolean structural proxies (section exists/doesn't exist) are the strongest signal for pattern skills — categorical 0%→100% shifts | Phase 1.2 |
| 35 | Self-check workflow behavior is an unplanned but powerful proxy — 0% baseline → 100% test for explicit self-check passes | Phase 1.2 |
| 36 | Some proxies fail when baseline is already good — failure modes showed no delta because model naturally produces them for SKILL.md tasks | Phase 1.2 |

---

## Decision Trail

| Turn | Decision | Rationale |
|------|----------|-----------|
| 4 | Start with scenarios | Testing methodology constrains skill architecture |
| 12 | Full simulation (Option A) | Principled approach; user's stated goal |
| 14 | Focus on scenario generation | Identified as bottleneck |
| 18 | Dual-path design | Handle both well-designed and poorly-designed skills |
| 23 | Address blocking gaps first | Step 5, purpose-unclear, prioritization |
| 31 | Create comprehensive spec | Self-contained reference document |
| 37 | Add preamble | Make document truly self-contained |
| Spike | Use `context: fork` architecture | Only approach that works mid-session |
| Impl | Omit `tools` field in assessment-runner | Inherit all tools — skill needs unknown |
| Impl | Revert to minimal ADR design | Over-engineering biased baseline; execution environment ≠ behavioral spec |
| Edge | Use neutral skill naming | Prevents observer effect; "test/baseline" in names could bias behavior |
| Edge | Variance depends on comparison dimension | Format comparisons need fewer runs than content comparisons |
| Stress A1 | Accept ambiguous terms in skills | Model has stable defaults; vague terms don't cause variance |
| Stress A2 | Don't pair hard limits with comprehensiveness | Content always wins; format constraints are overridden |
| Stress A2 | Use selection criteria for quantity constraints | "Exactly N" may be refused; "the N most common" works better |
| A2b Deep-Dive | Original 60/40 revised to 80/20 (N=10) | Larger sample reduced estimated variance |
| A2b Deep-Dive | Selection-criteria framing eliminates quantity variance | "The 3 most common" → 100% compliance (N=5); enables two-tier structure |
| Stress B | Any domain/complexity for scenarios | Compliance generalizes across technical contexts |
| Stress C | Use instruction density to control output | More requirements + dense guidance = more elaborate output |
| Phase 1.2 | Boolean proxies over count proxies for pattern skills | Categorical shifts (0→1) are unmistakable; count proxies suffer ceiling effects |
| Phase 1.2 | Framework generalizes to pattern skills | 6/7 proxies detected expected direction; no proxy showed skill hurting output |
| Phase 1.2 | Include behavioral workflow as proxy | Self-check behavior was the most dramatic signal — entirely unplanned |

---

## Artifacts Produced

| Artifact | Location |
|----------|----------|
| Framework Specification v0.1.0 | `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md` |
| Consolidated Discussion Summary | `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md` |
| Feasibility Spike Results | `docs/spikes/simulation-feasibility-spike_2026-02-04.md` |
| Architecture Decision Record | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` |
| Assessment-Runner Subagent | `.claude/agents/assessment-runner.md` |
| Stress Test Plan | `docs/plans/2026-02-05-architecture-stress-test-plan.md` |
| Stress Test Results | `docs/plans/2026-02-05-architecture-stress-test-results.md` |
| This Discussion Map | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` |

---

## Open Items

| Item | Priority | Status |
|------|----------|--------|
| Create `assessment-runner` subagent | High | ✅ Complete |
| Validate architecture end-to-end | High | ✅ Complete (Phase 12) |
| Design skill file templates | High | ✅ Validated (baseline + test templates work) |
| Edge case testing | High | ✅ Complete (Phase 13) |
| Define run count guidelines | Medium | ✅ Complete (dimension-dependent) |
| Architecture stress testing | High | ✅ Complete (Phase 14: A, B, C categories) |
| Implement scenario generation | High | Ready to start (Phase 4) |
| Create worked example | Medium | Partially complete (edge case + stress tests) |
| Implement cleanup mechanism | Medium | Not started |
| Oracle mitigation strategy | Medium | Not started |
| Test partial compliance scenarios | Low | Addressed (A2b deep-dive: variance minor and mitigable) |
| A2b variance deep-dive | High | ✅ Complete — revised to 80/20; selection-criteria framing eliminates variance |
| B2/C1 5-run expansions | High | ✅ Complete — 100% compliance confirmed |
| Pattern skill testing (Phase 1.2) | High | ✅ Complete — 6/7 proxies show expected direction; framework generalizes to pattern skills |

---

## Reading Order for New Context

1. **Quick overview:** This document
2. **Full specification:** `simulation-based-skill-assessment_v0.1.0.md`
3. **Architecture decision:** `0001-simulation-based-skill-assessment-architecture.md`
4. **Implementation constraints:** `simulation-feasibility-spike_2026-02-04.md`
5. **Deep context (optional):** Original discussion files

---

*Last updated: 2026-02-05*
*Total discussion turns: 48 (38 + 10) + implementation session + validation session + edge case testing + stress testing + A2b deep-dive + Phase 1.2 pattern skill testing*
*Key pivot: Discovery that skills hot-reload but subagents don't*
*Architecture validated: End-to-end A/B testing confirmed with "three options" skill*
*Edge cases tested: Partial compliance, baseline similarity, negative delta, variance analysis*
*Stress tests complete: A (ambiguity, conflicts + A2b deep-dive), B (scenario variance + 5-run expansions), C (skill structure + 5-run expansions)*
*A2b deep-dive: Original 60/40 revised to 80/20 (N=10); selection-criteria framing eliminates variance (100%, N=5)*
*Phase 1.2: Pattern skill testing complete — writing-principles tested with 7 proxies across 10 runs; 6/7 proxies show expected direction; framework generalizes to pattern skills*
*Framework status: All blocking tests complete. Adversarial tests (Phase 2.1) pending but non-blocking.*
