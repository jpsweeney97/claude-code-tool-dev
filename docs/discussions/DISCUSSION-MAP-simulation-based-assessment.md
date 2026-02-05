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

---

## Artifacts Produced

| Artifact | Location |
|----------|----------|
| Framework Specification v0.1.0 | `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md` |
| Consolidated Discussion Summary | `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md` |
| Feasibility Spike Results | `docs/spikes/simulation-feasibility-spike_2026-02-04.md` |
| Architecture Decision Record | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` |
| Assessment-Runner Subagent | `.claude/agents/assessment-runner.md` |
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
| Implement scenario generation | High | Not started |
| Create worked example | Medium | Partially complete (edge case tests) |
| Implement cleanup mechanism | Medium | Not started |
| Oracle mitigation strategy | Medium | Not started |
| Test partial compliance scenarios | Low | Not started (needs ambiguous skill design) |

---

## Reading Order for New Context

1. **Quick overview:** This document
2. **Full specification:** `simulation-based-skill-assessment_v0.1.0.md`
3. **Architecture decision:** `0001-simulation-based-skill-assessment-architecture.md`
4. **Implementation constraints:** `simulation-feasibility-spike_2026-02-04.md`
5. **Deep context (optional):** Original discussion files

---

*Last updated: 2026-02-04 (Session 3)*
*Total discussion turns: 48 (38 + 10) + implementation session + validation session + edge case testing*
*Key pivot: Discovery that skills hot-reload but subagents don't*
*Architecture validated: End-to-end A/B testing confirmed with "three options" skill*
*Edge cases tested: Partial compliance, baseline similarity, negative delta, variance analysis*
