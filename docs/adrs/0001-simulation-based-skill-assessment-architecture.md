# ADR-0001: Simulation-Based Skill Assessment Architecture

**Date:** 2026-02-04
**Status:** Accepted
**Deciders:** JP (via spike validation)
**Supersedes:** None

---

## Summary

Use dynamic skills with `context: fork` pointing to a static `assessment-runner` subagent for simulation-based skill assessment. This architecture enables empirical validation of skill effectiveness through controlled A/B testing with subagents.

---

## Context

### The Problem

The `improving-skills` skill fails at its core purpose. It assesses **structural compliance** (does the skill follow `skills-guide.md`?) rather than **functional effectiveness** (does the skill actually work?).

| Current Approach | Limitation |
|------------------|------------|
| "Does it have trigger phrases?" | Binary, verifiable — but doesn't predict effectiveness |
| "Does it use blocking language?" | Binary, verifiable — but doesn't ensure enforcement |
| "Is it under 500 lines?" | Binary, verifiable — but says nothing about quality |

A skill can pass all structural checks and still fail completely at its stated purpose. This was demonstrated when `improving-skills` was assessed using its own methodology — it scored well while actively failing.

### The Root Cause

**Structural compliance is checkable; functional effectiveness requires observation.**

To know whether a skill works, you must:
1. Run a task WITHOUT the skill (baseline)
2. Run the same task WITH the skill (test)
3. Compare the difference (delta)

This is empirical validation — simulation-based assessment.

### The Challenge

Claude Code's subagent system has constraints that affect how simulation can be implemented:

| Component | Hot-Reload Mid-Session? | Dynamic Creation Works? |
|-----------|------------------------|------------------------|
| **Skills** | ✅ Yes | ✅ Immediately available |
| **Subagents** | ❌ No | ❌ Requires session restart |

This asymmetry is critical: we cannot create subagent files and use them in the same session, but we CAN create skill files and invoke them immediately.

---

## Decision

### Architecture: Static Subagent + Dynamic Skills

```
┌─────────────────────────────────────────────────────────────────┐
│  STATIC COMPONENT (checked into repo)                           │
│                                                                 │
│  .claude/agents/assessment-runner.md                            │
│  - Defines execution environment                                │
│  - Tools: Read, Grep, Glob, Bash, Write, Edit                  │
│  - permissionMode: acceptEdits                                  │
│  - model: inherit                                               │
│  - System prompt: "Execute task, report full process"          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ agent: assessment-runner
                              │
┌─────────────────────────────────────────────────────────────────┐
│  DYNAMIC COMPONENTS (created per-scenario, cleaned up after)    │
│                                                                 │
│  .claude/skills/assessment-baseline-{id}/SKILL.md              │
│  - context: fork                                                │
│  - agent: assessment-runner                                     │
│  - Content: Scenario task only                                  │
│                                                                 │
│  .claude/skills/assessment-test-{id}/SKILL.md                  │
│  - context: fork                                                │
│  - agent: assessment-runner                                     │
│  - Content: Target skill + scenario task                        │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Baseline Run:** Create a skill with `context: fork` containing only the scenario task. Invoke it. The assessment-runner executes without the target skill.

2. **Test Run:** Create a skill with `context: fork` containing the target skill's content PLUS the scenario task. Invoke it. The assessment-runner executes with the target skill injected.

3. **Delta Evaluation:** Compare outputs to identify where the skill helped, failed, or hurt.

4. **Cleanup:** Delete temporary skill directories after assessment.

### Skill File Templates

**Baseline Skill:**
```yaml
# .claude/skills/assessment-baseline-{scenario-id}/SKILL.md
---
name: assessment-baseline-{scenario-id}
description: Baseline assessment for scenario {id}
context: fork
agent: assessment-runner
---
## Scenario

{scenario setup and context}

## Task

{scenario trigger / user message}

## Instructions

Execute this task using your standard capabilities. Do not use any special
skills or guidelines beyond your base training.

Report your complete process and final output.
```

**Test Skill (with target skill injected):**
```yaml
# .claude/skills/assessment-test-{scenario-id}/SKILL.md
---
name: assessment-test-{scenario-id}
description: Test assessment for scenario {id} with target skill
context: fork
agent: assessment-runner
---
## Loaded Skill

You have the following skill loaded. Follow its instructions throughout this task:

---
{target skill content - full SKILL.md minus frontmatter}
---

## Scenario

{scenario setup and context}

## Task

{scenario trigger / user message}

## Instructions

Execute this task while following the loaded skill above.

Report your complete process and final output.
```

### Assessment-Runner Subagent

```yaml
# .claude/agents/assessment-runner.md
---
name: assessment-runner
description: Executes assessment scenarios with full tool access
tools: Read, Grep, Glob, Bash, Write, Edit
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

---

## Alternatives Considered

### Alternative 1: Task Tool with Manual Prompt Injection

**Approach:** Use the Task tool directly, injecting skill content into the prompt string.

```python
Task(
  subagent_type: "general-purpose",
  prompt: """
    You have this skill loaded. Follow its instructions:
    ---
    {skill content}
    ---

    Scenario: {task description}
  """,
  run_in_background: true
)
```

**Verdict:** ✅ Works, but relegated to fallback.

| Factor | Assessment |
|--------|------------|
| Validated | ✅ Experiments 1-6 confirm it works |
| Official mechanism | ⚠️ Workaround, not designed for this |
| Separation of concerns | ❌ Task + skill mixed in prompt |
| Subagent configuration | ⚠️ Limited to built-in subagent types |
| Maintainability | ❌ Harder to debug, no clear structure |

**Use When:** Skill file creation is impractical or fails.

### Alternative 2: Dynamic Subagent with `skills` Field

**Approach:** Create subagent files mid-session with the `skills` field to preload target skills.

```yaml
# .claude/agents/test-skill-injection.md
---
name: test-skill-injection
description: Test subagent with target skill loaded
skills:
  - target-skill-name
tools: Read, Grep, Glob
model: haiku
---
Execute the scenario task...
```

**Verdict:** ❌ Does not work.

| Test | Result |
|------|--------|
| Invoke immediately after file creation | ❌ Agent not found |
| Invoke after `/agents` reload | ❌ Agent not found |
| Simpler agent without `skills` field | ❌ Agent not found |
| Pre-existing agents (created before session) | ✅ Available |

**Root Cause:** Subagents are loaded at session start. `/agents` does not reload from disk mid-session despite documentation suggesting it should. Only session restart makes new subagents available.

**Implication:** This approach requires breaking the workflow into multiple sessions, which is impractical for iterative assessment.

### Alternative 3: Pre-Configured Subagents

**Approach:** Create all assessment subagents before the session starts.

**Verdict:** ⚠️ Would work but impractical.

| Factor | Assessment |
|--------|------------|
| Works technically | ✅ Pre-existing subagents are available |
| Supports dynamic scenarios | ❌ Can't create new scenarios mid-session |
| Iteration support | ❌ Each iteration requires session restart |
| Workflow integration | ❌ Breaks continuous improvement loop |

**Use When:** Assessment scenarios are known in advance and won't change.

---

## Consequences

### Positive

1. **Mid-session dynamic assessment:** Skills hot-reload, enabling iterative improvement within a single session.

2. **Clean separation:** Skills define the task; subagent defines the execution environment.

3. **Full configurability:** The static subagent can specify tools, permissions, and model once.

4. **Official mechanism:** `context: fork` is designed for this use case.

5. **Observability:** The assessment-runner's system prompt requests full process traces.

### Negative

1. **File management overhead:** Temporary skill directories must be created and cleaned up.

2. **Disk writes per scenario:** Each baseline + test pair creates 2 skill directories.

3. **Cleanup responsibility:** Assessment must reliably delete temp files to avoid clutter.

### Neutral

1. **Skill content extraction:** Target skill content must be read and stripped of frontmatter before injection.

2. **Self-reporting observability:** Full tool call details require either background execution with file parsing OR relying on the subagent's self-reported process trace.

---

## Constraints Discovered

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Task prompts are task-framed, not system-framed | Skills framed as "you must X" are ignored | Reframe as "follow this process" |
| Synchronous Task returns summaries | Can't see tool call details | Use background execution OR self-reporting |
| Prohibitions override format requirements | Conflict resolution favors negatives | Avoid conflicting instructions |
| `skills` field requires literal names | Can't parameterize at runtime | Inject skill content into dynamic skill files |
| Subagents don't hot-reload | Dynamic subagent creation requires session restart | Use skills with `context: fork` instead |
| `/agents` reload ineffective | New agents not available after `/agents` | Use skills (which do hot-reload) |
| **Skills DO hot-reload** | ✅ Enabler | Use dynamic skill files with `context: fork` |

---

## Validation

All experiments passed during the feasibility spike:

| # | Experiment | Question | Result |
|---|------------|----------|--------|
| 1 | Prompt Injection Baseline | Can instructions influence subagent behavior? | ✅ Pass (task-framing required) |
| 2 | Skill Content Injection | Can multi-section skill content be followed? | ✅ Pass |
| 3 | Output Capture Fidelity | What detail can be captured? | ✅ Pass (background or self-reporting) |
| 4 | Controlled Conditions | Can baseline/test be identical except skill? | ✅ Pass |
| 5 | Cost Boundaries | What are token/time limits? | ✅ Pass (~675K tokens/full assessment) |
| 6 | Skill Activation Simulation | Does injected skill behave like native skill? | ✅ Pass |

### Key Validation: Skill Hot-Reload with `context: fork`

Created skill mid-session:
```yaml
# .claude/skills/temp-fork-test/SKILL.md
---
name: temp-fork-test
description: Test skill hot-reload with context fork
context: fork
agent: general-purpose
---
Answer this question: What is 2+2?

Your response MUST begin with "FORKED-SKILL-RESPONSE: " followed by your answer.
```

Immediately invoked via Skill tool (no reload, no restart).

**Result:** ✅ Complete success
```
Skill "temp-fork-test" completed (forked execution).

Result:
FORKED-SKILL-RESPONSE: 4
```

### End-to-End Architecture Validation (2026-02-04)

Validated the complete A/B testing workflow using a simple "three options" discipline skill.

**Test Design:**

| Component | Implementation |
|-----------|----------------|
| Target skill | "Present exactly 3 options before recommending" |
| Scenario | "What's the best way to handle errors in a CLI tool?" |
| Baseline | Skill with `context: fork` + `agent: assessment-runner`, scenario only |
| Test | Skill with `context: fork` + `agent: assessment-runner`, target skill + scenario |
| Success criteria | Countable difference in output structure |

**Results:**

| Metric | Baseline | Test |
|--------|----------|------|
| Options presented | 0 | **3 (A, B, C)** |
| Format | Direct recommendation | Options → Recommendation |
| Trade-offs per option | N/A | 2 each (strength + weakness) |
| Skill acknowledgment | None | Explicit |

**Baseline output:** Direct 8-point recommendation on CLI error handling.

**Test output:** Three labeled options (Exit Codes, Exception Hierarchy, Result Types) with trade-offs, followed by recommendation.

**Conclusion:** ✅ Architecture validated. The delta is:
- **Unmistakable** — 0 options vs 3 options
- **Attributable** — Test explicitly acknowledged the skill
- **Observable** — Process traces show structural difference

This confirms the core hypothesis: skill injection via `context: fork` produces measurable behavioral change that can be compared against baseline.

### Edge Case Testing (2026-02-04)

Tested three edge cases to refine framework understanding.

**Methodology refinement:** Initial skill names included "test" and "baseline" which could bias subagent behavior (observer effect). Renamed to neutral identifiers (e.g., `scenario-typescript-9m`, `scenario-typescript-2p`) with meaningless suffixes.

#### Test 1: Partial Compliance

**Hypothesis:** A skill with 3 distinct requirements might be partially followed.

**Skill requirements:**
1. Start with "ANALYSIS:" header
2. Include exactly 2 code examples
3. End with "VERDICT:" section

**Result:** Full compliance (3/3 requirements met). The skill was clear enough that all requirements were followed.

**Finding:** Well-designed skills with unambiguous, countable requirements tend to achieve full compliance. To observe partial compliance, we'd need ambiguous or conflicting requirements.

#### Test 2: Baseline Similarity

**Hypothesis:** Some scenarios produce "natural" behavior that matches what a skill would request, resulting in zero delta.

**Skill:** "Use bullet points to organize benefits"
**Scenario:** "What are the benefits of TypeScript?"

**Result:** Clear delta observed. Without skill: numbered headers with code examples. With skill: concise bullet points.

**Finding:** Don't assume what "natural" behavior looks like. The hypothesis that Claude naturally uses bullet points for "benefits" questions was wrong. Always run the baseline.

#### Test 3: Negative Delta

**Hypothesis:** A harmful skill (15-word limit on complex architecture question) produces detectably worse output.

**Result:** Confirmed.
- Without skill: ~2,000 words with diagrams, phases, trade-offs
- With skill: Exactly 15 words ("Use event-driven design, API gateway, service mesh...")

**Finding:** Negative delta is detectable. The framework can identify skills that harm response quality.

#### Variance Analysis

**Question raised:** Is one baseline run sufficient to establish "natural" behavior?

**Test:** Ran `scenario-typescript-2p` 5 times to measure variance.

**Results:**

| Dimension | Variance |
|-----------|----------|
| Structure (numbered headers, code examples, trade-offs section) | **0%** — all 5 runs identical |
| Content (specific points, wording, examples) | Moderate variation |

**Conclusion:** Variance is dimension-dependent.
- **Format comparisons:** Low variance for constrained scenarios; 1 run may suffice
- **Content comparisons:** Higher variance; multiple runs needed
- **Recommendation:** Specify what dimension is being compared and choose run count accordingly

#### Edge Case Summary

| Test | Hypothesis | Result | Insight |
|------|------------|--------|---------|
| Partial compliance | Skill partially followed | ❌ Full compliance | Clear skills get full compliance |
| Baseline similarity | No delta | ❌ Clear delta | Don't assume natural behavior |
| Negative delta | Skill hurts quality | ✅ Confirmed | Harmful skills are detectable |
| Variance | N=1 insufficient | ⚠️ Depends | Variance is dimension-dependent |

### Architecture Stress Testing (2026-02-05)

Tested whether ambiguous or conflicting skill instructions would break the A/B comparison mechanism. If variance is high, comparisons become unreliable.

**Methodology:**
- 5 runs per test condition
- Neutral skill naming (`scenario-{topic}-{suffix}`) to prevent observer effect
- `context: fork` + `agent: assessment-runner` execution

#### Category A1: Ambiguous Instructions

Tested whether vague/undefined terms cause high variance.

| Test | Instruction | Finding | Variance |
|------|-------------|---------|----------|
| A1a | "several" (quantifier) | ~19 examples consistently | LOW |
| A1b | "concise" vs "thorough" | Asymmetric effect (-55%/+24%) | LOW |
| A1c | "appropriate caveats" | 8-9 caveats consistently | LOW |
| A1d | "better" (code) | 4 core changes consistent | LOW |
| A1e | "optimize" | Identical algorithm all 5 runs | **ZERO** |
| A1f | "improve" (recommendations) | Same pattern across runs | LOW |
| A1g | "professional" | Near-identical outputs | VERY LOW |

**Key Finding: Ambiguity ≠ Variance.** The model has stable defaults for ambiguous terms. Domain-specific terms ("optimize") have stronger defaults than general terms ("better").

**Implication:** Ambiguous skill instructions don't break A/B comparisons. The variance comes from what the model *decides* terms mean, not randomness.

#### Category A2: Conflicting Requirements

Tested what happens when skill instructions genuinely conflict.

| Test | Conflict | Resolution | Consistency |
|------|----------|------------|-------------|
| A2a | 200-word limit vs comprehensive coverage | Content wins | 100% |
| A2b | Exactly 3 options vs all viable approaches | Quantity wins (revised) | 80% quantity / 20% coverage (N=10) |
| A2c | Beginner-friendly vs expert depth | Both (progressive disclosure) | 100% |

**Key Findings:**

1. **Content completeness is highest priority.** Format constraints (word limits) are systematically overridden when they conflict with comprehensiveness.

2. **Quantity constraints show minor variance, mitigable by framing.** "Exactly N options" showed ~80/20 compliance across 10 runs (revised from 60/40 on initial 5). A2b deep-dive found that reframing to "the 3 most common options" eliminates variance entirely (100% compliance, 5/5) — selection criteria remove the perceived arbitrariness that triggers the helpfulness override.

3. **Framing changes the answer, not just structure.** "Exactly 3" selects for diversity (relational, document, embedded); "3 most common" selects for popularity (PostgreSQL, MongoDB, MySQL). Skill authors should choose framing deliberately.

4. **Reconcilable conflicts get reconciled.** When structural solutions exist (like progressive disclosure for tone vs depth), the model finds them rather than choosing one requirement over another.

5. **Conflict acknowledgment is rare.** The model silently resolves tensions rather than explicitly noting the conflict.

#### Stress Test Summary

| Category | Question | Answer |
|----------|----------|--------|
| A1 (Ambiguity) | Do vague terms cause variance? | No — stable defaults exist |
| A2a (Format vs Content) | Which wins when conflicting? | Content, 100% of the time |
| A2b (Quantity vs Coverage) | Which wins when conflicting? | ~80/20 quantity wins; mitigated by selection-criteria framing |
| A2c (Tone vs Depth) | Which wins when conflicting? | Both — reconciled via layering |

**Conclusion:** The A/B comparison mechanism remains reliable. Skill instructions produce consistent, predictable behavior even when ambiguous or conflicting. The only notable variance — quantity constraints ("exactly N") — was found to be minor (~80/20 across 10 runs) and fully mitigable by providing selection criteria (e.g., "the 3 most common" instead of "exactly 3").

#### Implications for Skill Design

| Finding | Skill Design Guideline |
|---------|------------------------|
| Ambiguity has stable defaults | Vague terms are OK — but specify if you need non-default interpretation |
| Content > Format | Hard limits (word counts) will be overridden for comprehensiveness |
| Quantity constraints need selection criteria | "Exactly N" is fragile; "the N most common/important" eliminates variance |
| Reconcilable conflicts get both | Tone + depth can coexist via progressive disclosure |
| Helpfulness > Compliance | Model biases toward helpful output over strict instruction following |

#### Category B: Scenario Variance (2026-02-05)

Tested whether the A/B comparison mechanism is robust to scenario variation. If baseline behavior varies based on phrasing, domain, or complexity, skill effects become harder to attribute.

**B1: Phrasing Variance**

Same scenario (REST API error handling) with three phrasings: formal (explicit structure), casual (conversational), minimal (topic only).

| Finding | Implication |
|---------|-------------|
| Core content stable across phrasings | Skills affecting content won't be confounded by phrasing |
| Presentation adapts to input style | Skills affecting format should control for phrasing |
| Minimal phrasing triggered web search | Phrasing can affect tool usage, not just output |

**Variance: LOW for content, MODERATE for presentation.**

**B2: Domain Variance**

Same "three options" skill across three domains: web dev, data science, DevOps.

| Criterion | Web Dev | Data Science | DevOps |
|-----------|---------|--------------|--------|
| Exactly 3 options | ✅ | ✅ | ✅ |
| Strengths/weaknesses | ✅ | ✅ | ✅ |
| Recommendation | ✅ | ✅ | ✅ |

**Compliance: 100% across all domains.** Domain doesn't affect skill compliance.

**B3: Complexity Variance**

Same "three options" skill across complexity levels: simple (editor choice), medium (React state management with constraints), complex (enterprise migration with 7 constraints).

| Criterion | Simple | Medium | Complex |
|-----------|--------|--------|---------|
| Exactly 3 options | ✅ | ✅ | ✅ |
| Strengths/weaknesses | ✅ | ✅ | ✅ |
| Recommendation | ✅ | ✅ | ✅ |

**Compliance: 100% across all complexity levels.** The model scales depth to match complexity while maintaining structural compliance.

#### Category B Summary

| Test | Question | Finding |
|------|----------|---------|
| B1 (Phrasing) | Does phrasing affect baseline? | Content stable; presentation adapts |
| B2 (Domain) | Does domain affect compliance? | No — 100% compliance across domains |
| B3 (Complexity) | Does complexity affect compliance? | No — 100% compliance across complexity |

**Conclusion:** The A/B comparison mechanism is robust to scenario variation. Phrasing, domain, and complexity do not introduce variance that would confound skill assessment.

#### Category C: Skill Structure Variance (2026-02-05)

Tested whether skill structure (number of requirements, instruction length, instruction density) affects compliance rates.

**C1: Simple vs Compound Skills**

Same scenario (Python GIL explanation) with increasing requirements: 1, 3, and 5 requirements.

| Condition | Requirements | Compliance |
|-----------|--------------|------------|
| Simple | 1 | 100% |
| Compound-3 | 3 | 100% |
| Compound-5 | 5 | 100% |

**Finding:** Number of requirements does not affect compliance when requirements are clear and countable.

**C2: Skill Length Effects**

Same requirements (3 advantages, 3 disadvantages, recommendation) with short (~25 words) vs long (~170 words) instructions.

| Condition | Compliance | Output Effect |
|-----------|------------|---------------|
| Short | 100% | Standard output |
| Long | 100% | More nuanced recommendation |

**Finding:** Instruction length doesn't affect compliance. Longer instructions can add depth to specific sections.

**C3: Instruction Density**

Same requirements with sparse (bullet points only) vs dense (with rationale and examples) guidance.

| Condition | Compliance | Output Words |
|-----------|------------|--------------|
| Sparse | 100% | ~450 |
| Dense | 100% | ~1100 |

**Finding:** Density affects output depth, not compliance. Model adapts presentation to match instruction style.

#### Category C Summary

| Test | Question | Finding |
|------|----------|---------|
| C1 | Does # of requirements affect compliance? | No — 100% at 1, 3, and 5 requirements |
| C2 | Does instruction length affect compliance? | No — 100% for short and long |
| C3 | Does instruction density affect compliance? | No — 100% for sparse and dense |

**Implication for skill authors:** Skill structure is a tool for controlling output style, not a risk factor for compliance. Use multiple requirements freely; control verbosity through instruction density.

#### Combined A+B+C Implications

| Dimension | Variance | Implication for Framework |
|-----------|----------|---------------------------|
| Skill ambiguity (A1) | Low | Vague skill instructions are interpreted consistently |
| Skill conflicts (A2) | Low (mitigable) | Content > format; quantity constraints need selection criteria |
| Scenario phrasing (B1) | Low (content) | Scenario phrasing doesn't confound content-focused skills |
| Scenario domain (B2) | Zero | Skills work consistently across technical domains |
| Scenario complexity (B3) | Zero | Skills work consistently across complexity levels |
| Skill requirement count (C1) | Zero | Multiple requirements don't degrade compliance |
| Skill instruction length (C2) | Zero | Length affects depth, not compliance |
| Skill instruction density (C3) | Zero | Density controls output verbosity |

#### Phase 1.2: Pattern Skill Testing (2026-02-05)

Tested whether the A/B comparison framework generalizes from discipline skills (countable requirements) to pattern skills (qualitative, diffuse differences). All prior tests used skills with binary/countable success criteria; this test validates measurement via proxies.

**Target Skill:** `writing-principles` — 14 writing principles for instruction documents.
**Scenario:** Write a SKILL.md for `commit-message-guide`. 5 baseline + 5 test runs.
**Method:** Define 7 measurement proxies from the skill's principles, score all 10 outputs.

| Proxy | Baseline Mean | Test Mean | Delta | Signal |
|-------|---------------|-----------|-------|--------|
| Vague terms (P1) | 2.4 | 0.8 | -67% | Moderate |
| Scope section (P5) | 0/5 | 5/5 | 0%→100% | **Strong** |
| Example count (P3) | 9.2 | 10.4 | +13% | Weak |
| Failure modes (P6) | 6.2 | 6.0 | ≈0% | None |
| Preconditions (P8) | 0/5 | 4.5/5 | 0%→90% | **Strong** |
| Success criteria (P13) | 0.2 | 0.6 | +0.4 | Moderate |
| Filler phrases (P14) | 0.5 | 0 | -0.5 | Weak |

**Result: 6 of 7 proxies show expected direction.** Framework generalizes to pattern skills.

**Key Findings:**

1. **Boolean proxies (section presence) are the strongest signal.** Scope and Preconditions went from 0% to 90-100% — unmistakable categorical shifts.

2. **Count proxies show moderate signal.** Vague term reduction (-67%) is clear; example count increase (+13%) is real but modest due to ceiling effects.

3. **Some proxies fail when baseline is already good.** Failure modes showed no delta because the model naturally produces this content for SKILL.md tasks. Proxy selection must account for baseline quality.

4. **Self-check workflow is an unplanned powerful proxy.** All 5 test runs performed explicit self-check passes (writing-principles workflow); 0 baseline runs did. This behavioral difference is the most dramatic and directly attributable signal.

5. **The skill was purely additive.** No proxy showed test worse than baseline.

**Implication for framework:** Pattern skills are assessable through measurement proxies. Boolean structural proxies and behavioral workflow proxies are most reliable. The framework is validated for both discipline and pattern skill types.

**Framework validation status:** All blocking stress tests complete. A (ambiguity, conflicts + A2b deep-dive), B (scenario variance + 5-run expansions), C (skill structure + 5-run expansions), and Phase 1.2 (pattern skill testing) all validated. A/B comparison mechanism works across skill instruction variance, scenario variance, skill structure variance, and skill type variance (discipline + pattern). Adversarial tests (Phase 2.1) remain pending but are non-blocking.

---

## Implementation Path

### Phase 2: Skill Architecture Design

1. ✅ **Create assessment-runner subagent** — Minimal design (16 lines), checked into repo
2. ✅ **Validate architecture** — End-to-end test with "three options" skill
3. ✅ **Edge case testing** — Partial compliance, baseline similarity, negative delta, variance
4. **Implement skill file generation** — Templates for baseline and test skills
5. **Implement skill content extraction** — Read target skill, strip frontmatter
6. **Implement 8-step scenario generation** — From framework spec
7. **Implement skill invocation** — Use Skill tool for forked execution
8. **Implement cleanup** — Remove temporary skill directories

### Open Design Questions

| Question | Options | Recommendation | Status |
|----------|---------|----------------|--------|
| Observability approach | Background execution + file parse vs. self-reporting | Start with self-reporting; add background parsing if needed | Open |
| Skill directory location | `.claude/skills/assessment-*/` vs. temp directory | `.claude/skills/` for hot-reload; cleanup after | Open |
| Scenario ID format | UUID vs. incrementing vs. hash | Short hash of scenario content for reproducibility | Open |
| Cleanup timing | After each scenario vs. after full assessment | After full assessment (enables debugging) | Open |
| Runs per scenario | 1 vs. 3-5 vs. 10+ | **5 runs validated** — shows variance patterns clearly; format comparisons may need fewer | ✅ Validated |
| Skill naming | Descriptive vs. neutral IDs | **Neutral IDs confirmed** — `scenario-{topic}-{suffix}` prevents observer effect | ✅ Validated |

---

## References

- **Spike results:** `docs/spikes/simulation-feasibility-spike_2026-02-04.md`
- **Stress test results:** `docs/plans/2026-02-05-architecture-stress-test-results.md`
- **Framework specification:** `docs/frameworks/simulation-based-skill-assessment_v0.2.0.md`
- **Discussion consolidation:** `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md`
- **Skills/subagents relationship:** `docs/discussions/skills-subagents-relationship.md`

---

## Appendix: Full Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  1. SCENARIO GENERATION (8-step framework)                      │
│     Input: Target skill                                         │
│     Output: 5-7 prioritized scenarios                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. FOR EACH SCENARIO:                                          │
│                                                                 │
│     a. Create baseline skill file                               │
│        - context: fork                                          │
│        - agent: assessment-runner                               │
│        - Scenario task (no target skill)                        │
│                                                                 │
│     b. Invoke baseline skill                                    │
│        Skill(skill: "assessment-baseline-{id}")                 │
│                                                                 │
│     c. Create test skill file                                   │
│        - context: fork                                          │
│        - agent: assessment-runner                               │
│        - Target skill content + scenario task                   │
│                                                                 │
│     d. Invoke test skill                                        │
│        Skill(skill: "assessment-test-{id}")                     │
│                                                                 │
│     e. Evaluate delta between baseline and test                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. GAP ANALYSIS                                                │
│     Compare baseline vs test across all scenarios               │
│     Identify where skill helped / failed / hurt                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. ITERATION                                                   │
│     Fix identified gaps, re-run scenarios                       │
│     Repeat until threshold met                                  │
│     Cleanup temporary skill directories                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-04 | Initial ADR created from spike findings |
| 2026-02-04 | Added end-to-end validation test results; updated implementation path |
| 2026-02-04 | Added edge case testing results (partial compliance, baseline similarity, negative delta, variance); added observer effect mitigation guidance |
| 2026-02-05 | Added architecture stress testing results (A1 ambiguity, A2 conflicts); confirmed A/B comparison reliability; added skill design implications |
| 2026-02-05 | Added Category B results (scenario variance: phrasing, domain, complexity); framework validation status updated |
| 2026-02-05 | Added Category C results (skill structure: requirement count, length, density); all stress tests complete; framework ready for Phase 4 |
| 2026-02-05 | A2b deep-dive: revised variance from 60/40 to 80/20 (N=10); reframing with selection criteria eliminates variance (100%, N=5); updated skill design guidelines |
| 2026-02-05 | Phase 1.2: Pattern skill testing complete. writing-principles tested with 7 measurement proxies across 10 runs (5 baseline + 5 test). 6/7 proxies show expected direction. Framework generalizes to pattern skills. |
