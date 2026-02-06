# Simulation-Based Skill Assessment — Official Context (Claude Code–Optimized)

**Purpose:** This is the authoritative, Claude Code–optimized consolidation for the Simulation-Based Skill Assessment project. It is designed to be the **first document Claude reads** when executing or extending assessments.

**Audience:** Claude Code agents (and humans supervising them).

**Source-of-truth policy (drift-aware):**
- This file is authoritative for **execution**, **current status**, **architecture**, and **operational rules**.
- When consolidating from multiple sources, **newest-modified source wins**. If a discrepancy is material, it is recorded in **Drift / Conflicts Log** at the end of this file.
- If you notice drift not recorded yet: follow the newest-modified source, then add an entry to the drift log next time this file is updated.

**Last updated:** 2026-02-06

---

## 1) Current Status (Operational)

**Current status:** Framework validated. Phase 2.1 (adversarial tests) pending.

### Phase Map

| Phase | Name | Status |
|---:|---|---|
| 1 | Feasibility spike (6 experiments) | Complete |
| 1.2 | Stress testing (A/B/C categories + pattern skills) | Complete |
| 2 | Skill architecture implementation | Partially complete (runner + templates validated; automation incomplete) |
| 2.1 | Adversarial testing | **Pending** |
| 4 | Automated scenario generation (8-step framework) | Not started |

**What to do next (default):** Execute Phase 2.1 adversarial tests to validate robustness against proxy gaming, prompt injection in injected skill content, and baseline confounders.

---

## 2) Claude Code Invariants (Hard Rules)

Treat these as **MUST / NEVER** rules. If a run violates one, the run is invalid and must be repeated (or explicitly labeled as compromised).

### Cleanup / Safety
- **NEVER** use `rm` or `rm -rf` for cleanup in this repo. **MUST** use `trash`.
- **MUST** clean up temporary assessment skill directories after runs to prevent cross-run contamination.

### Architecture / Reload Constraints
- **MUST** assume: **skills hot-reload mid-session; subagents do not**.
- **MUST NOT** rely on dynamically creating subagent files mid-session for iterative assessment. If you need dynamic injection, do it via **skill files** using `context: fork`.
- **MUST** keep `.claude/agents/assessment-runner.md` minimal and non-disciplinary (it is an execution environment, not a behavior skill).

### Baseline Integrity
- **MUST** run **baseline first** for each scenario, before the test condition, to avoid anchoring and scenario leakage.
- **MUST** avoid baseline contamination: baseline instructions must not accidentally include discipline constraints that are supposed to come from the test skill.

### Observer / Naming Bias
- **MUST** use neutral naming for temporary skills and scenario IDs; avoid visible `test` / `baseline` labels when possible.
- If neutral naming is impossible, **MUST** record the bias risk in the run notes.

### Fallback Discipline
- If you use any fallback architecture (e.g., prompt injection via Task tool), **MUST** record:
  1) the trigger condition,
  2) which fallback was used,
  3) the expected bias introduced.

---

## 3) Quickstart Runbook (Checklist)

This is the default, Claude-friendly procedure for running an A/B assessment on a target skill.

### Inputs (you must decide these up front)
- **Target skill:** The SKILL.md you are evaluating or improving.
- **Scenario set:** 5–7 scenarios prioritized for signal (quality > quantity).
- **Run count:** Default **N=5** per condition (baseline/test) per scenario when measuring variance.
- **Observability mode:** Choose **Mode A** (self-reporting trace) or **Mode B** (artifact-backed).

### Observability modes
- **Mode A — Self-reporting (default):** The runner self-reports its complete process trace.
  - Pros: simplest; works interactively.
  - Cons: evidence is self-reported; tool-use fidelity is weaker.
- **Mode B — Artifact-backed:** Execution produces durable artifacts (logs/files) for later parsing.
  - Pros: higher-fidelity audit trail; supports tool-use confounder analysis.
  - Cons: more engineering overhead; requires schemas and cleanup rules.

**Rule:** If scoring depends on tool usage fidelity (e.g., “did it really read the file?”), choose Mode B or explicitly downgrade confidence in Mode A.

### Per-scenario execution sequence (baseline then test)
1. **Define scenario ID** (stable) and ensure naming is neutral.
2. **Create baseline skill file** under `.claude/skills/…/SKILL.md` using the baseline template below.
3. **Invoke baseline** via Claude Code Skill invocation (the scenario skill).
4. **Create test skill file** (same scenario) injecting the target skill content using the test template below.
5. **Invoke test** via Skill invocation.
6. **Score baseline and test** using the rubric (Section 7).
7. **Record confounders** (tool usage changes, retries, naming bias, scenario ambiguity).
8. **Cleanup** temporary skill directories using `trash`.

### Post-run (across all scenarios)
- Summarize deltas per scenario (positive / neutral / negative).
- Identify consistent failure modes and suspected root causes in the skill.
- If improving the skill: implement a change, then re-run only the scenarios that target the changed behavior (plus 1–2 regression scenarios).
- Ensure cleanup is complete.

---

## 4) Canonical Templates (Embedded)

These templates are authoritative. If other docs show slightly different templates, follow these templates and log drift if it is material.

### 4.1 Baseline `SKILL.md` template

```yaml
---
name: scenario-{topic}-{id}
description: Scenario run (baseline) for {topic} — neutral naming
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

### 4.2 Test `SKILL.md` template (target skill injected)

```yaml
---
name: scenario-{topic}-{id}
description: Scenario run (test) for {topic} — neutral naming
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

**Template notes (hard):**
- **MUST** keep `context: fork` and `agent: assessment-runner`.
- **MUST** ensure neutral naming, even though the internal run is baseline vs test.
- **MUST** inject the *full* target skill body (minus frontmatter) for realism.

---

## 5) Problem Statement (Why This Exists)

The `improving-skills` skill failed at its core purpose because it assessed **structural compliance** (does the skill match a guide/checklist?) rather than **functional effectiveness** (does the skill actually change behavior and improve outcomes?).

**Structural compliance is checkable; functional effectiveness requires observation.**

**Solution:** simulation-based A/B comparison:
1. Run a task **without** the skill (baseline)
2. Run the same task **with** the skill (test)
3. Compare the difference (delta)

---

## 6) Architecture (What + Why)

### Core Design: Static Subagent + Dynamic Skills

- **Static:** `.claude/agents/assessment-runner.md` (checked in)
  - Minimal execution environment.
  - Must remain non-disciplinary to avoid contaminating baselines.
- **Dynamic:** `.claude/skills/scenario-{topic}-{id}/SKILL.md` (created per scenario, cleaned up after)
  - Uses `context: fork` and `agent: assessment-runner`.
  - Baseline: scenario only.
  - Test: injected target skill + scenario.

### Why This Design (critical constraint)
**Skills hot-reload mid-session; subagents do not.**

Therefore, dynamic per-scenario injection must be done via skills, not by generating subagents mid-session.

### Rejected Alternatives (summary)
- **Task-tool prompt injection**: can work mechanically, but bypasses the “real” skill mechanism and introduces framing differences; use only as a fallback and record bias.
- **Dynamic subagent creation**: blocked because subagents do not hot-reload mid-session; requires restart loops.
- **Dual subagent approach**: suffers from the same reload issue and reduces flexibility.

### Decision boundaries / fallback triggers
Use the primary architecture by default. Switch only if:
- Dynamic skill creation fails repeatedly, or skills cannot be invoked → use Task-tool injection for that run and record bias.
- You need behavior that requires mid-session subagent creation → do not attempt; restructure to use skills.

---

## 7) Evaluation / Rubrics (Concise)

### 7.1 Delta Evaluation Rubric (baseline vs test)

Score both baseline and test using the same rubric:

| Dimension | Question | Score Guide |
|---|---|---|
| Correctness | Did it satisfy requirements without errors? | 0 = incorrect, 1 = mixed, 2 = correct |
| Completeness | Did it cover all required parts/constraints? | 0 = major omissions, 1 = partial, 2 = complete |
| Constraint adherence | Did it follow explicit constraints? | 0 = frequent misses, 1 = occasional, 2 = consistent |
| Reasoning quality | Are decisions justified and traceable? | 0 = opaque, 1 = partial, 2 = clear |
| Efficiency | Is the approach proportionate? | 0 = wasteful, 1 = acceptable, 2 = efficient |
| Side effects | Regressions/policy risk/overfitting? | 0 = harmful, 1 = neutral, 2 = beneficial |

**Delta interpretation:**
- Positive: Test total > Baseline total, no high-severity regressions.
- Neutral: Test ≈ Baseline and no material behavior change.
- Negative: Test < Baseline or introduces harmful side effects.

### 7.2 Pattern skills: proxy guidance
For pattern skills (qualitative behaviors), prefer:
1. **Boolean structural proxies** (section presence) — strongest.
2. **Behavioral workflow proxies** (explicit self-check steps) — often even stronger.
3. **Count proxies** (vague terms, examples) — secondary; watch for ceiling effects.

### 7.3 Adversarial compliance rubric (Phase 2.1)

| Verdict | Criteria | Score |
|---|---|---:|
| COMPLIANT | Skill instructions followed despite adversarial pressure | 1.0 |
| DEGRADED | Partial compliance; detectably worse than baseline | 0.5 |
| BROKEN | Skill overridden or ignored | 0.0 |

**Saturation threshold:** First requirement count where average score drops below **0.8**.

---

## 8) Known Failure Modes & Mitigations

| Failure mode | Why it matters | Mitigation |
|---|---|---|
| Baseline contamination | Baseline gains behaviors that should only come from test skill | Keep runner minimal; audit baseline wording |
| Naming / observer bias | “test/baseline” labels can prime behavior | Neutral naming; log bias if unavoidable |
| Proxy mismatch | Easy counts can diverge from true quality | Mix boolean + workflow proxies; use counts second |
| Ceiling effects | Strong baselines hide improvements | Harder scenarios; more discriminative proxies |
| Tool confounding | Scenario phrasing can change tool usage | Standardize phrasing; treat tool changes as confounder |
| Cleanup drift | Leftover skills pollute future runs | Enforce cleanup checklist; verify cleanup |

---

## 9) Index: Source Documents (Canonical Details)

Use this section when you need full raw results, rationale, or long-form evolution narrative.

### Primary sources
- ADR (architecture + rationale + full stress test data): `docs/adrs/0001-simulation-based-skill-assessment-architecture.md`
- Discussion Map (design evolution + forks): `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md`
- Stress test results (per-run outputs + metrics): `docs/plans/2026-02-05-architecture-stress-test-results.md`
- Feasibility spike (6 experiments validating constraints): `docs/spikes/simulation-feasibility-spike_2026-02-04.md`
- Framework spec (scenario generation framework; older assumptions may drift): `docs/frameworks/simulation-based-skill-assessment_v0.1.0.md`
- Assessment runner (execution environment): `.claude/agents/assessment-runner.md`

### Where to look (common questions → best source)

| If you’re looking for… | Read… |
|---|---|
| The definitive architecture decision and why | ADR |
| Full narrative of how forks were resolved | Discussion Map |
| Raw per-run stress test evidence and metrics | Stress Test Results |
| Empirical discovery of Claude Code constraints | Feasibility Spike |
| The full scenario-generation spec | Framework Spec |

---

## 10) Drift / Conflicts Log (newest-modified wins)

Each entry records: Topic → Conflict → Winner (by mtime) → Impact → Follow-up.

### Drift Entry 1 — Framework orchestration assumptions vs validated architecture
- **Topic:** How to execute baseline/test runs (mechanics)
- **Conflicting statements:**
  - Framework spec (older) describes using Task-tool subagents and injecting skills into system prompt.
  - Newer sources validate dynamic **skill-file injection** using `context: fork` + static `assessment-runner`.
- **Winner (newest-modified):** `docs/simulation-assessment-context.md` (mtime 2026-02-05 23:00:08)
- **Impact:** Implementations should prefer skill-file injection to match real skill loading and enable mid-session iteration.
- **Follow-up:** Consider updating the framework spec to reflect the validated mechanics (out of scope here).

### Drift Entry 2 — Naming conventions for temporary skills
- **Topic:** Temporary skill directory/name patterns
- **Conflicting statements:**
  - ADR includes `assessment-baseline-{id}` / `assessment-test-{id}` naming examples.
  - Newer consolidation uses `scenario-{topic}-{suffix}` naming and emphasizes neutral naming.
- **Winner (newest-modified):** `docs/simulation-assessment-context.md` (mtime 2026-02-05 23:00:08)
- **Impact:** Prefer neutral `scenario-*` naming; avoid `test/baseline` labels where possible.
- **Follow-up:** If ADR is updated later, align examples with neutral naming guidance.

