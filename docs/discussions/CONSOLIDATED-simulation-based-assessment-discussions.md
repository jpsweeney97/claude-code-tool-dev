# Simulation-Based Skill Assessment: Consolidated Discussion Summary

**Purpose:** Single reference capturing all key decisions, findings, and open items from the design discussions. Read this instead of the 7 source files.

**Source Files:**
- `improving-skills-failure-modes-and-simulation-based-assessment.md` — Root cause analysis
- `simulation-based-assessment-framework-discussion-part-*.md` — Framework design (38 turns)
- `continuation-of-simulation-based-skill-assessment-framework-discussion.md` — Gap analysis and feasibility spike

**Primary Artifact:** `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`

---

## 1. The Problem

The `improving-skills` skill fails because it **conflates form with function**:

| What It Does | What It Should Do |
|--------------|-------------------|
| Assesses structural compliance with skills-guide.md | Assesses whether skill achieves its purpose |
| "Does it have trigger phrases?" (binary, verifiable) | "Does Claude follow this correctly?" (requires observation) |
| Completes checklist without substantive analysis | Identifies functional failures through empirical testing |

**Root Cause:** Structural compliance is checkable; functional effectiveness requires simulation. The skill defaults to what it can check.

**The Discipline Skill Paradox:** If assessment is a checklist, Claude completes the checklist without genuine analysis. The skill enforces process compliance, not substantive thinking.

---

## 2. The Solution: Simulation-Based Assessment

Replace theoretical assessment with empirical measurement using subagents:

```
1. BASELINE  — Subagent WITHOUT skill runs task → observe natural behavior
2. TEST      — Subagent WITH skill runs same task → observe skill-assisted behavior
3. DELTA     — Compare → where does skill help/fail/hurt?
4. ITERATE   — Fix observed failures → re-test until threshold
```

**Assessment Hierarchy:**
- **Primary:** Empirical (simulation-based) — determines whether skill achieves purpose
- **Supporting:** Theoretical (structural analysis) — quick screening, remediation guidance

Neither alone is sufficient. Together they provide comprehensive validation.

---

## 3. The 8-Step Scenario Generation Framework

The framework generates 5-7 test scenarios for any target skill.

| Step | Purpose | Key Method |
|------|---------|------------|
| 1. Purpose Determination | What is skill trying to achieve? | Extract from docs OR infer via Goal Inference Method OR generate hypotheses |
| 2. Skill Type Classification | Discipline/Technique/Pattern/Reference | Match indicators to type definitions |
| 3. Use Case Extraction | Gather scenario seeds | Extract existing use cases OR generate from purpose + type |
| 4. Trigger Condition Analysis | When should/shouldn't it activate? | Parse trigger phrases OR derive from purpose |
| 5. Instruction → Behavior Mapping | Transform instructions into testable behaviors | 5-phase procedure (see below) |
| 6. Expected Behavior Derivation | Type-based predicted behaviors | Cross-reference content with type definitions |
| 7. Adversarial Scenario Generation | Edge cases, boundary conditions | Universal probes + type-specific probes |
| 8. Scenario Assembly | Prioritize and select | 4-dimension scoring → P0/P1/P2 assignment |

### Step 5: The 5-Phase Interpretation Procedure

This is the most complex step — transforms vague instructions into testable behaviors:

| Phase | Action |
|-------|--------|
| A. Decomposition | Extract ACTION, OBJECT, MODIFIER, CONDITION from instruction |
| B. Operationalization | Find observable proxies for subjective terms ("quality" → no errors, passes tests) |
| C. Exemplification | Generate compliant and violation examples |
| D. Boundary Definition | Define minimum, maximum, clear violation |
| E. Output Generation | Produce structured interpretation with confidence level |

### Step 8: Prioritization Scoring

| Dimension | 3 (High) | 2 (Medium) | 1 (Low) |
|-----------|----------|------------|---------|
| Purpose Centrality | Directly tests primary purpose | Tests supporting behavior | Tangential |
| Failure Impact | Skill useless if fails | Partial function | Minor issue |
| Usage Likelihood | Matches primary triggers | Plausible variation | Rare/edge case |
| Coverage Uniqueness | Only scenario testing this | Partial overlap | Redundant |

- **P0:** Score ≥ 10 OR (Centrality=3 AND Impact=3)
- **P1:** Score 7-9 OR (any=3 AND none=1)
- **P2:** Score ≤ 6 OR Likelihood=1

---

## 4. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **5-7 scenarios default** | Quality over quantity; well-chosen scenarios covering behavior landscape |
| **Variance is signal** | If 4 pass and 1 fails, investigate the outlier — reveals where skill behaves differently |
| **Holdout scenarios** | Reserve 1-2 for final validation only; detects overfitting |
| **Root cause fixing** | "Clarified ambiguous section" generalizes; "Added instruction for this case" overfits |
| **Dual-path design** | Each step has extraction (when skill provides) and generation (when it doesn't) paths |
| **Difficulty is diagnostic** | If framework struggles because skill is unclear, Claude will struggle too |

### Overfitting Prevention Strategies

1. **Holdout scenarios** — Development set (3-4) vs holdout (1-2)
2. **Scenario rotation** — Keep types consistent, change specifics between iterations
3. **Adversarial design** — Deliberately try to break the skill
4. **Ground in real usage** — Base on actual past failures
5. **Fix root causes** — Ask "why did this fail?" not "how do I pass this test?"

### Hard-to-Test Skill Categories

| Category | Mitigation |
|----------|------------|
| Long-term/multi-session | Test building blocks; simulate multi-phase |
| Qualitative effects | Define observable markers; comparative judgment |
| Context-dependent | Mine real examples; construct triggering contexts |
| Emergent/interaction | Test common combinations; isolation testing |
| Rare triggers | Mock failure condition; historical examples |
| Negative effects (absence) | Baseline comparison; elicit undesired behavior |
| Meta-cognitive | Examine reasoning traces; test downstream effects |
| High-variance | Test process not outcome; element presence |

**Key insight:** "Untestable" often reveals skill problems, not testing limitations.

---

## 5. Gaps Addressed

| Gap | Resolution |
|-----|------------|
| Step 5 procedure undefined | 5-phase interpretation procedure with proxy discovery method |
| Purpose-unclear handling | Goal inference method + hypothesis generation + handling for "purpose-incoherent" skills |
| Prioritization criteria missing | 4-dimension scoring with operationalized criteria and explicit thresholds |
| Circular reasoning | Reduced but not eliminated — irreducible judgment is structured and traceable |

---

## 6. Critical Gaps Still Open

These were identified in the continuation discussion and block implementation:

| Gap | Description | Severity |
|-----|-------------|----------|
| **Subagent skill injection** | How do you inject skill content into subagent context? Skills have frontmatter, use Skill tool, etc. | Blocking |
| **Oracle problem** | Claude-as-evaluator has same biases as subagent being tested. No mitigation strategy specified. | High |
| **Execution mechanics** | Token/time budget? Timeout handling? How to capture reasoning traces? | Blocking |
| **Delta evaluation** | What if baseline and test take completely different (both valid) approaches? | Medium |
| **Failure protocols** | What happens when steps fail? No step-by-step failure handling. | Medium |
| **Holdout sizing** | 1-2 scenarios too small for statistical confidence | Low |
| **Reference skills** | Ground truth for "correct information" is underspecified | Low |
| **Cost model** | "~31 operations" doesn't translate to actionable tokens/time/money | Low |
| **Calibration** | No procedure for validating scenario difficulty before full assessment | Low |

### The Fundamental Tension

> "If purposes are unclear, the framework tests whether skills match their documentation — which is a sophisticated form of structural compliance, not functional assessment."

The framework pushes the oracle problem up a level rather than solving it completely.

---

## 7. Feasibility Spike

A 6-experiment plan to validate the approach before full design:

| # | Experiment | Question | Result |
|---|------------|----------|--------|
| 1 | Prompt Injection Baseline | Can instructions be injected into subagent context? | ✅ Pass (with constraints) |
| 2 | Skill Content Injection | Can actual skill content (multi-section markdown) be followed? | ✅ Pass |
| 3 | Output Capture Fidelity | What detail can we observe? (final output, tool calls, reasoning?) | ✅ Pass (background required) |
| 4 | Controlled Conditions | Can baseline and test be identical except skill presence? | ✅ Pass |
| 5 | Cost Boundaries | What are token/time limits? Is full assessment affordable? | ✅ Pass (~675K tokens/assessment) |
| 6 | Skill Activation Simulation | Does injected skill behave like natively-loaded skill? | ✅ Pass |

**Key Discoveries:**
- Task framing required (not system-rule framing)
- **Skills hot-reload; subagents don't** — Critical architectural insight
- **`context: fork` is the recommended approach** — Dynamic skills pointing to static subagent
- Subagent `skills` field doesn't work mid-session (`/agents` reload ineffective)
- Task tool injection works as fallback

**Status:** ✅ Complete. All experiments pass. Proceed to Phase 2.

**Full results:** `docs/spikes/simulation-feasibility-spike_2026-02-04.md`

---

## 8. Implementation Roadmap

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Feasibility Spike | ✓ Complete | All experiments pass. See `docs/spikes/simulation-feasibility-spike_2026-02-04.md` |
| 1. Framework Specification | ✓ Complete | `simulation-based-skill-assessment_v0.1.0.md` |
| 2. Skill Architecture Design | ✓ Complete | assessment-runner subagent created; templates validated |
| 3. Architecture Validation | ✓ Complete | End-to-end A/B test with "three options" skill |
| 4. Scenario Generation | **Next** | Implement 8-step framework |
| 5. Worked Example | Not started | Apply framework to real skill |
| 6. Skill Implementation | Not started | Build the new improving-skills |
| 7. Validation | Not started | Test improved skill on itself |

---

## 9. Irreducible Elements

Some judgment cannot be eliminated, only structured:

| Judgment Point | Why Irreducible |
|----------------|-----------------|
| Proxy selection | Requires understanding what subjective term is "about" |
| Goal inference | Requires understanding instruction intent |
| Purpose centrality | Requires understanding what matters most |
| Failure impact | Requires understanding consequences |

The framework makes these decisions explicit, traceable, and auditable — not eliminable.

---

## 10. Key Insights (Synthesized)

1. **Structural compliance ≠ functional effectiveness** — The core failure mode
2. **Simulation-based assessment** — Observe what happens, don't just reason about it
3. **The measurement problem** — What's checkable isn't what matters
4. **Discipline skill paradox** — If assessment is a checklist, Claude just completes it
5. **Quality over quantity** — 5 well-chosen scenarios > 20 arbitrary ones
6. **Variance is signal** — Outliers reveal behavior boundaries
7. **Holdout prevents overfitting** — Development vs validation sets
8. **Root cause > symptom fixing** — Clarifying ambiguity generalizes; adding specific instructions overfits
9. **"Untestable" is diagnostic** — Often reveals vague skill design
10. **Assessment hierarchy** — Empirical primary, theoretical supporting
11. **Irreducible judgment** — Structure it, don't try to eliminate it
12. **Difficulty is diagnostic** — If framework struggles, Claude will too
13. **Countable success criteria** — Unambiguous metrics (0 options vs 3) make delta evaluation conclusive
14. **Observer effect** — Skill names like "test/baseline" can bias subagent behavior; use neutral naming
15. **Don't assume natural behavior** — Always run the baseline to see what actually happens
16. **Variance is dimension-dependent** — Format comparisons (low variance) vs content comparisons (higher variance)

---

## Quick Reference: What To Do Next

**Edge cases tested.** Framework refined with variance and observer effect guidance. Proceed to scenario generation.

**Completed:**
- ✅ assessment-runner subagent (minimal, 16 lines)
- ✅ Skill file templates (baseline + test validated)
- ✅ Architecture validation ("three options" test conclusive)
- ✅ Edge case testing (partial compliance, baseline similarity, negative delta)
- ✅ Variance analysis (dimension-dependent: format vs content)

**Key Methodological Findings:**
- Use neutral skill naming (no "test/baseline" to avoid observer effect)
- Don't assume natural behavior — always run the baseline
- Format comparisons: low variance, 1-3 runs may suffice
- Content comparisons: higher variance, 5+ runs recommended
- Negative delta (harmful skills) is clearly detectable

**Phase 4: Scenario Generation (Next)**
1. Implement 8-step scenario generation framework
2. Create worked example with real skill (e.g., improving-skills)
3. Build the new simulation-based improving-skills

**Recommended Architecture (from spike):**

| Component | Purpose |
|-----------|---------|
| Static subagent (`assessment-runner`) | Defines execution environment — tools, permissions, model |
| Dynamic skills with `context: fork` | Created per-scenario; skill content = task for subagent |
| Skill tool invocation | Hot-reload ensures immediate availability |

**Key insight:** Skills hot-reload; subagents don't. Use dynamic skill files with `context: fork` for mid-session assessment.

**Architecture constraints:**
- Skill content must be framed as task requirements
- Use `context: fork` pointing to `assessment-runner` subagent
- Clean up temporary skill directories after assessment
- Fallback: Task tool with manual prompt injection (validated but less clean)

---

*Last updated: 2026-02-04 (edge case testing complete)*
*Source discussions: 7 files, ~4,500 lines total*
*Spike results: `docs/spikes/simulation-feasibility-spike_2026-02-04.md`*
*Key finding: Skills hot-reload, subagents don't — use `context: fork` for dynamic assessment*
*Architecture validated: "Three options" test shows 0→3 options delta between baseline and test*
*Edge cases tested: Observer effect, variance analysis, negative delta detection*
