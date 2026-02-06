# Simulation-Based Skill Assessment: Consolidated Context

**Purpose:** Standalone reference for continuing this work. Contains comprehensive working context extracted from the ADR (762 lines) and Discussion Map (896 lines), with source provenance for key claims. Someone with no prior knowledge of the Simulation-Based Skill Assessment project should gain the context needed to continue implementation and evaluation work. Use this as the primary reference, and consult source docs for full-detail threads.

**Last updated:** 2026-02-05
**Branch:** `feature/architecture-stress-tests`
**Current status:** Framework validated. Phase 2.1 (adversarial tests) pending.

## Index: Source Documents (Start Here for Details)

This document is the *consolidated* view. Use the links below as the canonical "index" into the underlying sources.

### Primary Sources (most referenced)

- ADR (architecture + decision rationale): `docs/adrs/0001-simulation-based-skill-assessment-architecture.md`
- Discussion Map (design evolution + threads): `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md`
- Framework Spec (full 8-step framework): `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`

### Execution Artifacts (what was actually run)

- Feasibility spike (6 experiments): `docs/spikes/simulation-feasibility-spike_2026-02-04.md`
- Stress test plan: `docs/plans/2026-02-05-architecture-stress-test-plan.md`
- Stress test results (per-run outputs + metrics): `docs/plans/2026-02-05-architecture-stress-test-results.md`
- Assessment runner (static agent): `.claude/agents/assessment-runner.md`

### Consolidations / Notes

- Discussion consolidation (earlier summary): `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md`

### Where to Look (common questions → best source)

| If you're looking for… | Read… |
|---|---|
| The “why” + what we decided | ADR |
| The “how we got here” + forks considered | Discussion Map |
| The detailed scenario-generation framework | Framework Spec |
| Empirical validation and constraints discovered | Feasibility Spike |
| Raw stress test runs, deltas, and edge cases | Stress Test Results |

### Phase Map

| Phase | Name | Status |
|-------|------|--------|
| 1 | Feasibility spike (6 experiments) | Complete |
| 1.2 | Stress testing (A/B/C categories + pattern skills) | Complete |
| 2 | Skill architecture implementation | Partially complete (runner + templates validated; file generation, scenario generation, cleanup not automated) |
| 2.1 | Adversarial testing | **Pending** |
| 4 | Automated scenario generation (8-step framework) | Not started |

---

## 1. The Problem

The `improving-skills` skill fails at its core purpose: it checks **structural compliance** (does the skill follow the guide?) rather than **functional effectiveness** (does the skill actually work?).

A skill can pass all structural checks and still fail completely. This was proved when `improving-skills` was assessed using its own methodology — it scored well while actively failing. Structural compliance is checkable; functional effectiveness requires observation.

**Solution:** Simulation-based A/B testing.
1. Run a task WITHOUT the skill (baseline)
2. Run the same task WITH the skill (test)
3. Compare the difference (delta)

### How This Evolved (Meta Thread Summary)

This section exists to capture the reasoning path that led to the current architecture and to prevent re-litigating already-resolved design forks.

**Sequence:**
1. **Problem framing:** The core failure mode is “structural compliance ≠ functional effectiveness” (the checklist passes even when the skill fails).
2. **Method choice:** Shift from theoretical evaluation to empirical A/B simulation (baseline vs test → delta).
3. **Dependency realization:** To improve `improving-skills`, you need a general method to test *arbitrary* skills, which forces scenario generation as a first-class problem.
4. **Framework first:** The 8-step scenario generation framework was developed before mechanics were fully solved; gap analysis then identified blocking “execution mechanics” questions.
5. **Feasibility spike:** A targeted spike validated mechanics and surfaced the key constraint: **skills hot-reload mid-session; subagents do not**.
6. **Architecture lock-in:** The static `assessment-runner` + dynamic `context: fork` skills design was adopted because it is the only approach that supports iterative assessment within a single session without restart loops.

---

## 2. Architecture

### Core Design: Static Subagent + Dynamic Skills

```
STATIC (checked into repo):
  .claude/agents/assessment-runner.md
  - 16-line minimal subagent
  - permissionMode: acceptEdits, model: inherit
  - System prompt: "Execute task, report full process"

DYNAMIC (created per-scenario, cleaned up after):
  .claude/skills/scenario-{topic}-{suffix}/SKILL.md
  - context: fork
  - agent: assessment-runner
  - Baseline: scenario task only
  - Test: target skill content + scenario task
```

### Why This Design

**Critical constraint discovered via spike:** Skills hot-reload mid-session; subagents don't. A subagent file created mid-session won't be available until session restart. Skills with `context: fork` are immediately available. So: use skills as the dynamic injection mechanism, pointing to a static subagent as the execution environment.

### Rejected Alternatives

Three other architectures were tried and rejected during the feasibility spike:

| Alternative | Approach | Why Rejected |
|-------------|----------|--------------|
| Task tool + prompt injection | Inject skill content directly into Task tool prompt string | Works mechanically but bypasses official skill mechanism; no `context: fork` isolation; prompt framing differs from real skill loading |
| Multiple subagent files | Create separate subagent `.md` files per scenario | Subagents don't hot-reload mid-session — files created after session start are invisible until restart. **Blocking.** |
| Dual subagent approach | Pre-create "baseline" and "test" subagents | Same hot-reload problem; also can't dynamically vary skill content per scenario |

The current architecture is the only one that supports dynamic, iterative assessment within a single session.

### Decision Boundaries and Fallback Triggers

Use the primary architecture (static subagent + dynamic `context: fork` skills) by default. Switch only when one of these conditions is true:

| Condition | Trigger | Action |
|-----------|---------|--------|
| Dynamic skill creation unavailable | Skill file creation fails repeatedly, or temporary skill loading cannot be invoked | Use Task-tool prompt injection fallback for that run and log why |
| Session-restart-required behavior blocks iteration | Workflow requires creating new subagents mid-session | Do not use dynamic subagents; continue with static runner + dynamic skills |
| Scenario set fixed in advance | All scenarios known before session and no iteration needed | Pre-configured approach is acceptable, but document reduced flexibility |
| Baseline contamination risk detected | Baseline shows behavior that appears to come from injected discipline constraints | Revert runner prompt to minimal execution/observability instructions |

If fallback is used, record: (1) trigger condition, (2) fallback selected, (3) expected bias introduced.

### The Over-Engineering Trap

The initial assessment-runner had extensive behavioral instructions (constraints on tone, formatting, approach). This caused `writing-principles` to be applied mechanically to every task — the execution environment itself was acting like a discipline skill, biasing the baseline. Reverting to the current minimal 16-line design (observability instructions only, no behavioral constraints) eliminated this contamination.

**Lesson:** The assessment-runner is an execution environment, not a behavioral specification. Adding instructions beyond "execute and report" contaminates the A/B comparison by giving the baseline behaviors that should only come from the test skill.

### Skill File Templates

**Baseline:**
```yaml
---
name: scenario-{topic}-{suffix}
description: Baseline assessment for {topic}
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

**Test (with target skill injected):**
```yaml
---
name: scenario-{topic}-{suffix}
description: Test assessment for {topic} with target skill
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

### Scenario Quality Criteria

Every scenario must satisfy these four requirements (established in Phase 2):

| Requirement | Definition | Example |
|-------------|-----------|---------|
| Observable success criteria | What should the subagent do if the skill works? | "Output contains exactly 3 options with trade-offs" |
| Distinguishable baseline | How would behavior differ without the skill? | Baseline produces 0 structured options; test produces 3 |
| Clear purpose mapping | Which skill capability is this testing? | Tests the "present options" requirement, not the entire skill |
| Known ground truth | We can judge what "correct" looks like | A commit-message-guide SKILL.md should have trigger phrases, examples, scope |

### Full Workflow

```
1. SCENARIO GENERATION (8-step framework, not yet automated)
   Input: Target skill → Output: 5-7 prioritized scenarios

2. FOR EACH SCENARIO (N=5 runs per condition):
   a. Create baseline skill file (scenario only)
   b. Invoke: Skill(skill: "scenario-{topic}-{suffix}")
   c. Create test skill file (target skill + scenario)
   d. Invoke: Skill(skill: "scenario-{topic}-{suffix}")
   e. Evaluate delta between baseline and test

3. GAP ANALYSIS: Compare across all scenarios

4. CLEANUP: Delete temporary skill directories (use trash, never rm)
```

---

## 3. Validation History

### End-to-End Validation (2026-02-04)

**Skill tested:** "Three Options" (present exactly 3 options with trade-offs)
**Result:** Baseline = 0 options; Test = 3 options. Clear, measurable delta. Architecture confirmed sound.

**Related artifacts (read for full details):**
- `docs/plans/2026-02-05-architecture-stress-test-plan.md`
- `docs/plans/2026-02-05-architecture-stress-test-results.md`

### Edge Case Testing (2026-02-04)

| Test | Hypothesis | Actual Result |
|------|-----------|---------------|
| Partial compliance | 3-requirement skill → partial compliance | Full compliance (3/3); no variance |
| Baseline similarity | Scenario where natural behavior matches skill | Clear delta; baseline differs from test (always run baseline) |
| Negative delta | Harmful skill (15-word limit) | Clearly detectable; degradation is measurable |
| Observer bias | Skill names bias behavior | Confirmed; "test/baseline" in names can bias. Mitigated by neutral naming |

### Architecture Stress Tests (2026-02-05)

#### Category A: Skill Instruction Variance

| Test | Condition | Finding |
|------|-----------|---------|
| A1 (7 tests) | Ambiguous terms: "several," "concise," "appropriate," "better," "optimize," "improve," "professional" | Stable defaults; ambiguity does NOT cause variance |
| A2a | 200-word limit + comprehensiveness requirement | Content wins 100% of time; format constraints overridden |
| A2b (N=10 + N=5) | "Exactly 3 options" vs "all viable options" | ~80/20 compliance. Reframing with selection criteria ("the 3 most common") → 100% compliance |
| A2c | Beginner-friendly + expert depth | Both achieved via progressive disclosure; reconcilable conflicts get reconciled |

**A2b deep-dive insight:** Quantity constraints are fragile not because the model can't count, but because "exactly N" without selection criteria feels arbitrary. Adding selection criteria resolves the perceived arbitrariness. Also: framing changes the answer — "exactly 3" picks for diversity; "3 most common" picks for popularity.

#### Category B: Scenario Variance

| Test | Variable | Finding |
|------|----------|---------|
| B1 | Phrasing (formal, casual, minimal) | Content stable; presentation adapts to input style |
| B2 (N=5) | Domain (web dev, data science, DevOps) | 100% compliance across all domains |
| B3 | Complexity (simple, medium, complex) | 100% compliance; depth scales to match complexity |

#### Category C: Skill Structure Variance

| Test | Variable | Finding |
|------|----------|---------|
| C1 (N=5) | Requirement count (1, 3, 5) | 100% compliance at all levels |
| C2 | Instruction length (~25 words vs ~170 words) | 100% compliance; longer = more nuance |
| C3 | Instruction density (sparse vs dense) | 100% compliance; density controls output verbosity |

#### Phase 1.2: Pattern Skill Testing

Prior tests used discipline skills with countable requirements. This test validated that the framework works for pattern skills with qualitative differences.

**Target:** `writing-principles` (14 writing principles for instruction documents)
**Scenario:** Write a SKILL.md for `commit-message-guide`
**Runs:** 5 baseline + 5 test

**Measurement proxies and results:**

| Proxy | Source Principle | Baseline Mean | Test Mean | Delta | Signal |
|-------|-----------------|---------------|-----------|-------|--------|
| Vague terms | P1 (Be Specific) | 2.4 | 0.8 | -67% | Moderate |
| Scope section | P5 (Boundaries) | 0/5 | 5/5 | 0%→100% | **Strong** |
| Example count | P3 (Show Examples) | 9.2 | 10.4 | +13% | Weak |
| Failure modes | P6 (Failure Modes) | 6.2 | 6.0 | ≈0% | None |
| Preconditions | P8 (Preconditions) | 0/5 | 4.5/5 | 0%→90% | **Strong** |
| Success criteria | P13 (Outcomes) | 0.2 | 0.6 | +0.4 | Moderate |
| Filler phrases | P14 (Economy) | 0.5 | 0 | -0.5 | Weak |

**Result:** 6/7 proxies show expected direction. Framework generalizes to pattern skills.

**Proxy effectiveness hierarchy:**

| Category | Signal Strength | Examples | Recommendation |
|----------|----------------|----------|----------------|
| Boolean structural | Strong | Section presence (Scope, Preconditions) | Primary for pattern skills |
| Behavioral workflow | Strong | Self-check passes (0% → 100%) | Unplanned but powerful; include as standard |
| Count reduction | Moderate | Vague terms (-67%) | Good secondary when baseline has room |
| Count increase | Weak | Examples (+13%) | Ceiling effects limit utility |
| Count neutral | None | Failure modes (≈0%) | Baseline already good; proxy selection must account for this |

---

## 4. Architecture Stress Tests (2026-02-05)

This section summarizes the stress-test plan and results as **key takeaways** (not full run tables). For raw metrics, per-run outputs, and full narrative, consult:
- `docs/plans/2026-02-05-architecture-stress-test-plan.md`
- `docs/plans/2026-02-05-architecture-stress-test-results.md`

### 4.1 Purpose and Scope

**Why:** Comprehensive edge-case testing before Phase 4 (scenario generation).

**What it tested:** Whether the A/B comparison mechanism stays reliable when:
- Skill instructions are ambiguous or contradictory (Category A)
- Scenario wording, domain, and complexity vary (Category B)
- Skill structure (length, density, requirement count) varies (Category C)
- Pattern skills are evaluated via proxies rather than simple countable requirements (Phase 1.2)

### 4.2 Protocol (As Executed)

**Naming:** Use neutral skill names to prevent observer effect:
`scenario-{topic}-{random-suffix}`. Avoid "test", "baseline", "control", "experiment".

**Run tracking:** For each run, record the neutral skill name, timestamp, full output, and measured metrics.

**Variance thresholds (decision rules):**
- Count metrics (examples, caveats): low variance if σ ≤ 1
- Word count: low variance if CV ≤ 15%
- Presence/absence: low variance if 100% or 0%; high variance if mixed

**Expansion triggers:** Expand runs when variance is high, resolution strategy is inconsistent, or the outcome is surprising/interesting.

### 4.3 Category A Results: Instruction Variance

**A1 (ambiguous instructions):**
- Result: **Low variance overall.** Ambiguous terms like "several" and "appropriate caveats" were interpreted consistently, typically as "be comprehensive."
- Asymmetry: "Be concise" had a stronger effect than "Be thorough" (baseline behavior already leans thorough).
- Evaluative terms ("better", "optimize", "professional", "improve") had **stable defaults** in context (e.g., "optimize" → time complexity; "professional" → remove filler + add structure).

**A2 (conflicting requirements):**
- A2a (format vs content): **Deterministic outcome.** When a word limit conflicts with comprehensiveness, content wins; the word limit is exceeded consistently and the conflict is rarely acknowledged.
- A2b (exactly N vs all viable): **Observable variance.** The model may comply, refuse ("arbitrary"), or defer (ask for context). Adding explicit selection criteria (e.g., "the 3 most common") largely eliminates variance.
- A2c (beginner-friendly + expert depth): **Consistent progressive disclosure.** The model reliably satisfies both via layered explanation.

**Implication:** Ambiguity is not automatically a variance source; contradiction is more likely to produce strategy variance unless selection criteria resolves perceived arbitrariness.

### 4.4 Category B Results: Scenario Variance

**Finding:** Phrasing, domain, and complexity do not significantly change *content compliance*; they mostly change *presentation* (structure, tone, verbosity).

**Potential confound:** Minimal phrasing can trigger different tool behavior (e.g., web search), which can change output character in ways unrelated to the assessed skill.

**Implication:** Control scenario phrasing when evaluating format-sensitive requirements and treat tool usage changes as a possible confound during delta scoring.

### 4.5 Category C Results: Skill Structure Variance

**Finding:** Requirement count (1/3/5), instruction length, and instruction density did not degrade compliance in these tests.

**Key effect:** Density primarily controls output verbosity/depth, not adherence.

**Implication:** Adding more requirements is usually safe if they’re clear and countable; avoid relying on structure alone to "force" compliance.

### 4.6 Phase 1.2: Pattern Skill Testing (Proxy-Based)

**Finding:** Pattern skills can be assessed by mixing proxy types:
- **Boolean structural proxies** (section presence) are strongest and least ambiguous.
- **Behavioral workflow proxies** (e.g., self-check procedure present/absent) can be an even stronger signal than counts.
- Count proxies can suffer from ceiling effects when baselines are already strong.

**Implication:** Prefer boolean + workflow proxies as primary signals for pattern skills; use counts as secondary indicators.

---

## 4. Key Insights

Numbered insights accumulated across all phases. Starred (★) entries are most relevant to future work.

| # | Insight |
|---|---------|
| 1 | ★ Structural compliance ≠ functional effectiveness |
| 2 | Simulation-based assessment treats skill improvement as empirical science |
| 3 | ★ The measurement problem: what's checkable isn't what matters |
| 4 | Discipline skill paradox: if assessment is a checklist, Claude completes it without analysis |
| 5 | Quality over quantity: 5 well-chosen scenarios > 20 arbitrary ones |
| 6 | Variance is signal: investigate outliers, don't average them out |
| 7 | Difficulty of scenario generation is diagnostic — if framework struggles, Claude will too |
| 8 | "Untestable" often reveals skill problems, not testing limitations |
| 9 | ★ Irreducible judgment can be structured, not eliminated |
| 10 | ★ Framework pushes oracle problem up a level, doesn't solve it |
| 11 | Skills hot-reload; subagents don't |
| 12 | `context: fork` enables mid-session dynamic assessment |
| 13 | ★ Discipline skills are context-dependent; applying them mechanically can be counterproductive |

---

## 5. Delta Evaluation Rubric (Concise)

Use this rubric to evaluate baseline vs test outputs consistently:

| Dimension | Question | Score Guide |
|-----------|----------|-------------|
| Correctness | Did the output satisfy the task requirements without errors? | 0 = incorrect, 1 = mixed, 2 = correct |
| Completeness | Did it cover all required parts and constraints? | 0 = major omissions, 1 = partial, 2 = complete |
| Constraint adherence | Did it follow explicit format/limit/instruction constraints? | 0 = frequent misses, 1 = occasional misses, 2 = consistent |
| Reasoning quality | Were decisions justified and process traceable? | 0 = opaque, 1 = partially clear, 2 = clear and traceable |
| Efficiency | Was the approach proportionate (tools/time/steps) for the task? | 0 = wasteful, 1 = acceptable, 2 = efficient |
| Side effects | Did behavior introduce regressions, policy risk, or overfitting? | 0 = harmful, 1 = neutral, 2 = beneficial |

**Delta interpretation:**
- Positive delta: Test total > Baseline total, with no high-severity regressions.
- Neutral delta: Test total ≈ Baseline total and no material behavior change.
- Negative delta: Test total < Baseline total or introduces harmful side effects.

---

## 6. Known Limitations and Failure Modes

| Limitation / Failure Mode | Why It Matters | Mitigation |
|---------------------------|----------------|------------|
| Baseline contamination | Runner instructions can accidentally add behavior that should come from test skill | Keep runner minimal; audit baseline language periodically |
| Scenario representativeness risk | Narrow scenarios can overstate real-world effectiveness | Use mixed scenario sets (simple/complex, varied domains, varied phrasing) |
| Evaluator bias | Knowing "test" can bias interpretation toward expected gains | Use neutral naming and pre-declared rubric |
| Proxy mismatch | Easy-to-count proxies may not reflect actual quality | Mix structural, behavioral, and qualitative indicators |
| Ceiling effects | Strong baselines can hide improvements on count-based proxies | Add harder scenarios and boolean workflow indicators |
| Tool-behavior confounding | Scenario phrasing can change tool usage (e.g., web search) and alter output in ways unrelated to the assessed skill | Standardize scenario phrasing; predeclare tool expectations; score tool-use changes as potential confounders |
| Tooling/cleanup drift | Temporary artifacts can pollute later runs | Enforce post-run cleanup checklist and artifact audit |

### Implementation Constraints (Discovered)

These constraints were discovered empirically during the feasibility spike and materially affect how assessment runs must be implemented.

| Constraint | Impact | Mitigation |
|------------|--------|------------|
| Task prompts are task-framed, not system-framed | Skills framed as "you must X" are ignored | Reframe as "follow this process" (task instruction, not system rule) |
| Synchronous Task returns summaries | Can't reliably see full tool call details | Use background execution with artifacts for parsing OR rely on self-reporting traces |
| Prohibitions override format requirements | Conflict resolution favors negatives | Avoid conflicting instructions; prefer affirmative constraints with selection criteria |
| `skills` field requires literal names | Can't parameterize at runtime | Inject skill content into dynamic skill files |
| Subagents don't hot-reload | Dynamic subagent creation requires session restart | Use skills with `context: fork` for dynamic mid-session assessment |
| `/agents` reload ineffective | New agents are not available after `/agents` | Avoid dynamic subagent approaches; rely on skills hot-reload |
| **Skills DO hot-reload** | ✅ Enabler | Create `.claude/skills/*` mid-session; invoke immediately |

### Observability: Background Execution vs Self-Reporting

There are two viable observability modes. Choose explicitly before running evaluations, because the choice affects what evidence you can use during delta scoring.

**Mode A — Self-reporting (default):**
- The `assessment-runner` is instructed to report its complete process trace.
- Strengths: simplest workflow; no extra harness; works in interactive runs.
- Weaknesses: evidence is self-reported; may omit details; harder to audit tool behavior.

**Mode B — Background execution + artifact parsing (higher-fidelity):**
- Run execution in a way that produces durable artifacts (e.g., logs, files) that can be parsed after.
- Strengths: more reliable audit trail for tool usage and intermediate state; enables post-hoc scoring from artifacts.
- Weaknesses: more engineering overhead; requires defining artifact schema and storage/cleanup rules.

**Rule:** If your rubric dimension depends on tool usage fidelity (e.g., “Did it actually read the file?”), use Mode B or explicitly downgrade confidence when using Mode A.

---

## 7. Operational Checklist

### Pre-Run
- Confirm target skill version and scenario IDs are fixed.
- Confirm `assessment-runner` prompt remains minimal (no discipline behavior constraints).
- Confirm naming is neutral (avoid `test`/`baseline` labels visible to evaluator when possible).
- Define success criteria and rubric dimensions before execution.

### Run
- Execute baseline first for each scenario.
- Execute test run with injected skill using same scenario and constraints.
- Preserve full process traces for both runs.
- Record any anomalies (tool failures, retries, unexpected branching).

### Post-Run
- Score both runs with the same rubric.
- Classify delta (positive/neutral/negative) and note severity.
- Capture failure modes and suspected confounders.
- Cleanup temporary skills/artifacts and verify cleanup completed.

---

## 8. Coverage and Provenance Appendix

This document is the primary working reference. The table below maps key claims to source anchors in the ADR and Discussion Map for traceability.

| Consolidated Claim | ADR Anchor | Discussion Anchor |
|--------------------|-----------|-------------------|
| Structural compliance does not measure functional effectiveness | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Problem/Motivation) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Core problem framing threads) |
| Simulation A/B delta is the core assessment method | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Decision/How It Works) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Method synthesis and iteration notes) |
| Static subagent + dynamic skills is the chosen architecture | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Architecture Decision) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Spike validation thread) |
| Skills hot-reload mid-session; subagents do not | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Constraints/Alternatives) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Experiment findings) |
| Dynamic-subagent alternatives were rejected | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Alternatives Considered) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Failure analysis threads) |
| Over-engineered runner contaminates baseline | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Consequences/Design notes) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Runner simplification discussion) |
| Pattern-skill assessment is feasible with proxy mix | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` (Validation/Consequences) | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` (Phase 1.2 results) |
| Architecture stress tests validate variance boundaries and conflict-resolution patterns | `docs/plans/2026-02-05-architecture-stress-test-results.md` (A1/A2/B/C summaries) | `docs/plans/2026-02-05-architecture-stress-test-plan.md` (Protocol, thresholds, expansion triggers) |

For complete raw argumentation and full experimental narrative, consult:
- `docs/adrs/0001-simulation-based-skill-assessment-architecture.md`
- `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md`
| 14 | ★ Execution environments should be minimal; behavioral bias contaminates A/B comparisons |
| 15 | Countable, unambiguous success criteria make delta evaluation conclusive |
| 16 | ★ Observer effect: skill names like "test/baseline" can bias subagent behavior |
| 17 | Clear skills with unambiguous requirements tend to achieve full compliance |
| 18 | ★ Don't assume natural behavior — always run baseline to see what actually happens |
| 19 | Negative delta (harmful skills) is clearly detectable through A/B comparison |
| 20 | Variance is dimension-dependent: format (low variance) vs content (higher variance) |
| 21 | Ambiguity ≠ variance: vague terms have stable model defaults |
| 22 | ★ Content completeness is the model's highest priority — format constraints are overridden |
| 23 | Quantity constraints show minor variance (~80/20) mitigable by selection criteria |
| 24 | Reconcilable conflicts get reconciled (e.g., beginner + expert → progressive disclosure) |
| 25 | Scenario phrasing affects presentation, not content compliance |
| 26 | Domain and complexity don't affect skill compliance |
| 27 | Skill structure (requirement count, length, density) doesn't affect compliance |
| 28 | Instruction density controls output verbosity |
| 29 | Observer effect is real: naming skills with descriptive terms can bias behavior |
| 30 | ★ Quantity constraints are fragile due to perceived arbitrariness, not counting inability |
| 31 | Framing changes the answer — "exactly 3" picks diversity; "3 most common" picks popularity |
| 32 | 5-run expansions confirmed single-probe findings |
| 33 | ★ Pattern skills are testable via measurement proxies |
| 34 | ★ Boolean structural proxies are the strongest signal for pattern skills |
| 35 | ★ Self-check workflow behavior is an unplanned but powerful proxy |
| 36 | Some proxies fail when baseline is already good |

---

## 9. Design Rules (Validated)

These rules are empirically validated and should be followed in all future assessment work.

| Rule | Basis | Implication |
|------|-------|-------------|
| Use neutral skill naming: `scenario-{topic}-{suffix}` | Observer effect confirmed (#16, #29) | Never use "test", "baseline", "simple", "complex" in skill names |
| 5 runs per condition (dimension-calibrated) | Validated across all tests (#20, #32) | Format comparisons (e.g., "exactly 3 options") show ~0% inter-run variance → 1-3 runs sufficient. Content comparisons (e.g., quality of explanation) show higher variance → 5 runs standard. Default to 5 unless comparing a purely format dimension. |
| Content > format when they conflict | A2a (100% consistency) (#22) | Don't rely on hard format limits in skills |
| Use selection criteria for quantity constraints | A2b deep-dive (#23, #30) | "The N most common" not "exactly N" |
| Boolean proxies > count proxies for pattern skills | Phase 1.2 (#34) | Prioritize structural presence/absence |
| Include behavioral workflow proxies | Phase 1.2 (#35) | Self-check, explicit processes, risk calibration |
| Minimal execution environment | Over-engineering lesson (#14) | assessment-runner should be 16 lines, not a behavioral spec |
| Cleanup after full assessment, not per-scenario | Enables debugging | Use `trash`, never `rm` |
| Update all three docs together | User preference | Results doc, ADR, and Discussion Map must stay in sync |

---

## 10. Unresolved Questions

### Framework-Level

| Question | Context | Impact |
|----------|---------|--------|
| Oracle problem | Framework tests whether skills achieve their purposes. But if purposes are unclear, it tests documentation match — a sophisticated form of structural compliance (#10). A goal inference method was designed (synthesize implied goal from instructions, score hypotheses, flag incoherent skills) but not yet implemented. | Fundamental limitation; goal inference is the proposed mitigation |
| Proxy selection methodology | Phase 1.2 defined proxies ad hoc from writing-principles' 14 principles. No systematic process for selecting proxies for other skills | Blocks generalized pattern skill testing |
| Observation approach | Self-reporting (current) vs background file parsing | Self-reporting works for now; may need augmentation |
| Baseline quality detection | No method exists to detect when a baseline is pathologically unusual (e.g., model chooses an atypical default due to scenario wording) vs. when a skill genuinely helps | Could produce false positives (skill gets credit for fixing an unusual baseline) or false negatives (unusual baseline already does what the skill does) |

### Implementation-Level

| Question | Options | Current Recommendation |
|----------|---------|----------------------|
| Skill directory location | `.claude/skills/assessment-*/` vs temp dir | `.claude/skills/` for hot-reload; cleanup after |
| Scenario ID format | UUID vs incrementing vs hash | Short hash of scenario content (reproducibility) |

---

## 11. What Phase 2.1 (Adversarial Tests) Should Target

No detailed plan exists yet. These are the identified gaps and vulnerability surfaces from all prior testing:

### Known Gaps (Not Yet Tested)

1. **Oracle failure modes** — Can a skill produce positive delta on measured proxies while actually being unhelpful? Can harmful skills be masked as helpful? (#10)
2. **Proxy gaming** — Can a skill game boolean proxies (e.g., add an empty "Scope" section that satisfies the proxy but adds no value)?
3. **Pathological skill definitions** — Beyond A2 conflicts: impossible constraints, self-contradictory logic, recursive instructions
4. **Scenario generation failure modes** — What happens when the scenario itself is adversarial or broken?
5. **Baseline confounding** — Can uncontrolled variables make a baseline pathologically different, creating false deltas?
6. **Prompt injection via skill content** — Can adversarial content in injected skill definitions escape the assessment framing?

### Adversarial-Adjacent Work Already Done

These prior tests covered some adversarial territory:

| Test | What It Covered | What It Didn't Cover |
|------|----------------|---------------------|
| A1 (ambiguity) | Vague terms → stable defaults | Deliberately deceptive ambiguity |
| A2 (conflicts) | Competing requirements → content wins | Requirements designed to be impossible |
| Edge Case Test 3 (negative delta) | Harmful skill → detectable | Subtly harmful skill that looks helpful |
| Feasibility Spike Exp. 1 | Prompt injection → task framing needed | Sophisticated injection in skill content |
| Observer effect | Naming bias → mitigated | Other forms of priming or anchoring |

---

## 12. User Preferences

- Use `context: fork` + skill files for assessment runs, not Task tool shortcuts
- 5-run expansions for statistical rigor on all test conditions
- Update all three docs (results, ADR, discussion map) together — they must stay in sync
- Neutral skill naming to prevent observer effect
- Use `trash` for deletion, never `rm`
- Subagents for reading documents >5 files or parallel streams
- One question at a time; prefer multiple choice over open-ended

---

## 13. References

| Document | Location | Purpose |
|----------|----------|---------|
| ADR | `docs/adrs/0001-simulation-based-skill-assessment-architecture.md` | Architectural decisions and full stress test data |
| Discussion Map | `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md` | Evolution narrative, 48+ turns of design |
| Framework Spec | `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md` | Full 2,300-line spec (8-step framework, scenario generation) |
| Stress Test Plan | `docs/plans/2026-02-05-architecture-stress-test-plan.md` | Test design for A, B, C categories |
| Stress Test Results | `docs/plans/2026-02-05-architecture-stress-test-results.md` | Detailed per-run results and meta-insights |
| Feasibility Spike | `docs/spikes/simulation-feasibility-spike_2026-02-04.md` | 6 experiments validating architecture |
| Assessment Runner | `.claude/agents/assessment-runner.md` | The 16-line static subagent |
| Discussion Consolidation | `docs/discussions/CONSOLIDATED-simulation-based-assessment-discussions.md` | Earlier discussion summary |
