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

| Question | Options | Recommendation |
|----------|---------|----------------|
| Observability approach | Background execution + file parse vs. self-reporting | Start with self-reporting; add background parsing if needed |
| Skill directory location | `.claude/skills/assessment-*/` vs. temp directory | `.claude/skills/` for hot-reload; cleanup after |
| Scenario ID format | UUID vs. incrementing vs. hash | Short hash of scenario content for reproducibility |
| Cleanup timing | After each scenario vs. after full assessment | After full assessment (enables debugging) |
| Runs per scenario | 1 vs. 3-5 vs. 10+ | Depends on comparison dimension: format (1-3), content (5+) |
| Skill naming | Descriptive vs. neutral IDs | Neutral IDs (e.g., `scenario-xyz-7x`) to prevent observer effect |

---

## References

- **Spike results:** `docs/spikes/simulation-feasibility-spike_2026-02-04.md`
- **Framework specification:** `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`
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
