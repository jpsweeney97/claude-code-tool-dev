# Simulation Effectiveness Benchmark Framework v0.1.0

A **docs-only operational specification** for answering:

> “Does the Simulation-Based Skill Assessment architecture measure functional effectiveness in general?”

This framework turns the “Level 0 → Level 5” validity outline into a **repeatable benchmark program** that can be run manually in Claude Code **without building new tooling**.

**Primary reader:** Claude Code agents (and humans supervising them).

**Architecture prerequisite:** This framework assumes you are using the validated architecture documented in:
- `docs/simulation-assessment-context-official.md`

For deep background and evidence, see:
- `docs/adrs/0001-simulation-based-skill-assessment-architecture.md`
- `docs/plans/2026-02-05-architecture-stress-test-results.md`
- `docs/discussions/DISCUSSION-MAP-simulation-based-assessment.md`

**Version:** 0.1.0 (pragmatic rigor; manual execution)
**Last updated:** 2026-02-06

---

## Quickstart (Repo-Specific) — Run a Benchmark v0 End-to-End

This section is the fastest path to using this framework **in this repo** (`claude-code-tool-dev`) without additional design work. It defines:
- where to store benchmark artifacts,
- which skills to benchmark first,
- a concrete “Benchmark v0” suite,
- and the exact commands/oracles to use.

### Quickstart Preconditions

- You are in the repo root.
- You can invoke Claude Code skills (dynamic `.claude/skills/*` hot-reload).
- You will follow all hard invariants in `docs/simulation-assessment-context-official.md`.

### Quickstart Storage Layout (standardize this)

Create and use these directories:

- Scenario bank (definitions, stable): `docs/benchmarks/scenarios/`
- Benchmark runs (artifacts by date/run-id): `docs/benchmarks/runs/<run-id>/`
 - Benchmark suite run matrix (canonical): `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`

**Run id format (recommended):** `YYYY-MM-DD_benchmark-v0_<short-slug>`

Each run directory SHOULD contain:
- `suite.md` (which scenarios/skills/conditions were run)
- `run-records/` (one file per scenario × condition × replicate)
- `scores.md` (rubric scores, oracle outcomes, deltas)
- `report.md` (final YES/NO/INCONCLUSIVE + justification)

### Quickstart Oracles for this repo

This repo is primarily TypeScript/Node. Anchor scenarios should use:

- Package tests: `npm -w packages/mcp-servers/claude-code-docs test`
- Package build: `npm -w packages/mcp-servers/claude-code-docs run build`

Notes:
- Some tests are skipped unless `DOCS_PATH` is set; treat that as an explicit precondition for those tests.
- Network is not required for the default test suite because the real-network integration test is skipped by default.

### Quickstart: Skills to benchmark (Benchmark v0)

This framework does not prescribe a default list of “target skills” for Benchmark v0.

**Reason:** hardcoding repo skills into the benchmark can bias results (the benchmark becomes a test of local conventions rather than general measurement validity).

**Requirement:** Before running Benchmark v0, define an explicit, versioned target roster (recommended location):
- `docs/benchmarks/target-skills_v0.1.0.md`

The roster MUST specify:
- Skill identifiers (names)
- Skill type classification (discipline/technique/pattern/reference)
- The subset of scenarios each skill is expected to improve
- Any tool expectations (web allowed/expected) per skill/scenario pairing

### Quickstart: Control bodies (canonical)

Use the canonical control bodies in:
- `docs/benchmarks/control-bodies_v0.1.0.md`

When running a benchmark, record the control file version and the control name (e.g., `CONTROL_HARMFUL_NO_TOOLS_v0.1.0`) in your run record.

### Quickstart: Synthetic benchmark skill bodies (canonical)

If you use the synthetic `BENCH_*` skill roster entries from:
- `docs/benchmarks/target-skills_v0.1.0.md`

Use the canonical benchmark bodies in:
- `docs/benchmarks/bench-skill-bodies_v0.1.0.md`

Record the benchmark body version and name (e.g., `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0`) in your run record.

### Quickstart: Benchmark v0 suite overview

Benchmark v0 is intentionally small but complete:
- 8 scenarios total
  - 3 anchor (objective oracle = build/test)
  - 5 rubric (blinded rubric)
- Replication: N=3 baseline vs target for all scenarios
- Controls coverage: ≥50% of scenarios (4 of 8) include placebo/irrelevant/harmful

If any scenario shows high variance or borderline deltas, expand to N=5 for that scenario.

### Quickstart: How to run Benchmark v0 (step-by-step)

1. Choose a target skill roster (from `docs/benchmarks/target-skills_v0.1.0.md`).
2. Create a new run directory under `docs/benchmarks/runs/<run-id>/`.
3. Copy the 8 scenario definitions from **Section 3A** into `docs/benchmarks/scenarios/` (one file per scenario is fine).
3a. Follow the canonical run matrix in `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` for which scenarios get which controls and replication defaults.
4. For each scenario, run:
   - `BASELINE` (no injected skill)
   - `TARGET` (inject the target skill body)
   - plus controls if the scenario is in the control subset
5. For anchor scenarios:
   - Run the oracle commands exactly as written in the scenario (`npm -w ... test`, `npm -w ... run build`).
   - Record pass/fail and failures.
6. For rubric scenarios:
   - Produce Output A/B.
   - Blind + randomize labels.
   - Score with rubric (Section 7.2).
7. Write `report.md` with the final verdict and justification.

**Important:** if you cannot run anchor oracles due to environment limitations, you can still do rubric scenarios, but your verdict MUST be `INCONCLUSIVE` for “general measurement validity.”

## 0) Definitions (Level 0 Operationalization)

### 0.1 Functional effectiveness (operational definition)

A skill is **functionally effective** on a scenario set if, when injected, it produces a **reliable positive delta** on **task-native success outcomes**, with **no unacceptable side effects**, compared to baseline.

Key properties:
- “Task-native outcomes” means outcomes that matter for the task itself (e.g., tests pass, correct output, correct decision), not merely “followed the format.”
- “Reliable” means the sign of the delta is stable under replication (default N=3; expand to N=5 when variance is observed).

### 0.2 The “measures effectiveness in general” claim (operational)

The architecture “measures effectiveness in general” if, across a representative benchmark suite:

1. Skills expected to help show **positive deltas** on the scenarios they target.
2. Placebo and irrelevant skills show **~zero deltas** (within noise).
3. Known-harmful skills show **negative deltas**.
4. The above remains true under scenario variance (phrasing/domain/complexity) and basic adversarial pressure (proxy gaming attempts).
5. Confounders are tracked and do not plausibly explain the observed deltas.

**Allowed verdicts:** `YES` / `NO` / `INCONCLUSIVE`

---

## Coverage target (Matrix Coverage)

This benchmark uses a **matrix coverage** target: the suite should include at least one skill in each **skill type**:
- `discipline`
- `technique`
- `pattern`
- `reference`

and should exercise each skill type against the available oracle regimes:
- `objective_tests` (anchor)
- `rubric_blinded` (rubric)

If the target roster does not include at least one `reference`-type benchmark skill, you cannot claim full matrix coverage and your overall verdict should be capped at `INCONCLUSIVE` for “general measurement validity.”

---

## 1) Guiding Principles (what makes this credible)

This benchmark is only as strong as its measurement integrity.

### 1.1 Prefer objective oracles

When possible, choose scenarios whose success can be judged by an **external oracle**:
- tests passing (`uv run pytest`)
- golden outputs (diff against expected)
- static checks (typecheck/lint) if strongly relevant

### 1.2 Use controls (negative controls are mandatory)

If placebo/irrelevant skills routinely “improve” scores, your system is not measuring functional effectiveness—it is measuring bias, priming, or gaming.

### 1.3 Use blinding for subjective tasks

If scoring requires judgment, use blinded evaluation. Without blinding, you cannot credibly claim general measurement validity.

### 1.4 Confounder discipline

Tool usage changes (e.g., web search triggered by scenario phrasing) can dominate differences. Treat these as **confounders** and record them explicitly.

---

## 2) Prerequisites (do this before running)

### 2.1 Hard invariants

You MUST comply with the “Claude Code Invariants (Hard Rules)” in:
- `docs/simulation-assessment-context-official.md`

If any invariant is violated, the run is invalid unless explicitly labeled as compromised.

### 2.2 Observability mode

Choose a mode per benchmark run (record the choice in the run report):
- **Mode A (Self-report):** runner reports its tool usage and process trace.
- **Mode B (Artifact-backed):** runs generate durable artifacts (logs/files) used for scoring.

**Rule:** If your oracle depends on tool behavior fidelity (e.g., “did it really read the file?”), use Mode B or downgrade confidence for Mode A.

---

## 3) Benchmark Design (Level 5 Generalization, pragmatically)

### 3.1 Scenario types you must include

To support a “general” claim, the suite must include both:

1. **Anchor scenarios (objective oracles):** code changes + tests, golden outputs, etc.
2. **Rubric scenarios (subjective but structured):** writing/planning/decision tasks with blinded scoring.

### 3.2 Minimum suite size (v0.1.0 defaults)

This framework is pragmatic: it does not require power analysis, but it does require breadth.

Minimum recommended suite:
- **Scenarios:** 12 total
  - 6 anchor (objective)
  - 6 rubric (blinded)
- **Skills under evaluation:** 4 distinct skills across types
  - at least 1 discipline/technique-style skill (countable requirements)
  - at least 1 pattern/workflow skill (qualitative behaviors)
  - at least 1 tool-sensitive skill (tool usage likely to matter)
  - 1 additional (any type)

If you want a stronger claim:
- 24 scenarios (12 anchor + 12 rubric) across 6–10 skills.

### 3.3 Replication policy (N)

Default replication:
- **N=3** runs per condition per scenario.

Expansion triggers:
- If outcomes vary across runs (sign flips or large variance), expand to **N=5** for that scenario/condition.
- If placebo/irrelevant outcomes are unstable, expand controls too.

---

## 3A) Benchmark v0 Suite (Concrete, Repo-Specific)

This suite is a concrete starter set that exercises:
- objective oracles (build/tests),
- blinded rubric scoring,
- controls (placebo/irrelevant/harmful),
- and tool-confounder discipline.

### 3A.1 Benchmark v0: scenario roster (8 scenarios)

#### Anchor scenarios (objective oracles)

**Anchor 1 — Unit tests stay stable under “skill injection”**

```yaml
id: v0-anchor-vitest-001
title: `claude-code-docs` unit tests pass after a targeted change
skill_target: Make a small, correct change without breaking tests
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
  - `npm -w packages/mcp-servers/claude-code-docs run build` passes
failure_modes_to_watch:
  - Unrelated edits across the package
  - Tool confounder (web usage despite no_web)
inputs:
  prompt: |
    In `packages/mcp-servers/claude-code-docs`, make a small, low-risk improvement:
    - Strengthen one existing test assertion OR
    - Add one additional assertion to an existing test case

    Constraints:
    - Do not change production logic in `src/` unless required by a clearly failing test.
    - Keep changes minimal and localized to `tests/` when possible.

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
    - Run: `npm -w packages/mcp-servers/claude-code-docs run build`
  files:
    - packages/mcp-servers/claude-code-docs/tests/
notes:
  - This is an anchor scenario because “pass/fail” is objective. It is not a skill-quality oracle by itself; it tests whether injected skills distort engineering behavior.
```

**Anchor 2 — Parser/frontmatter stability**

```yaml
id: v0-anchor-frontmatter-002
title: Improve frontmatter parsing tests without breaking behavior
skill_target: Make a targeted change in parsing-related tests and keep correctness
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
failure_modes_to_watch:
  - Broad refactor “because style”
  - Introducing flaky tests
inputs:
  prompt: |
    Improve coverage for frontmatter parsing by adding a small new test case in:
    - `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`

    The new test must:
    - Be deterministic (no network, no temp files required unless cleaned up)
    - Assert a specific behavior (not just “does not throw”)

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
  files:
    - packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
```

**Anchor 3 — Golden query stability (search quality)**

```yaml
id: v0-anchor-golden-queries-003
title: Tighten golden query tests without breaking the suite
skill_target: Make a small, correct test improvement in golden queries
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `npm -w packages/mcp-servers/claude-code-docs test` passes
failure_modes_to_watch:
  - Changing mock corpus in a way that invalidates test intent
  - Large edits to production search logic
inputs:
  prompt: |
    In `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`, add one more golden query
    assertion that checks a reasonable mapping from query to expected category, using the existing mocked corpus.

    Constraints:
    - Do not expand the mock corpus unless absolutely necessary.
    - Keep the new query realistic and non-overlapping with existing ones.

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
  files:
    - packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
```

#### Rubric scenarios (blinded)

For rubric scenarios, you MUST use the blinding procedure in Section 7.2.

**Rubric 1 — Write an assessment scenario (quality of scenario spec)**

```yaml
id: v0-rubric-scenario-spec-004
title: Write a high-signal scenario spec (YAML-in-Markdown)
skill_target: Produce a scenario with clear oracle, success criteria, confounders
skill_type: pattern
task_type: writing
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Scenario includes all required fields from Section 5.1
  - Success criteria are checkable and not vague
failure_modes_to_watch:
  - Proxy gaming (adds fields but no real measurability)
inputs:
  prompt: |
    Draft ONE new benchmark scenario definition (YAML-in-Markdown) for this repo that would be a strong
    anchor scenario (objective oracle) and has clear success criteria and confounder notes.
```

**Rubric 2 — Write a benchmark run report (clarity and integrity)**

```yaml
id: v0-rubric-report-005
title: Write a benchmark report that supports YES/NO/INCONCLUSIVE
skill_target: Produce a defensible report structure with confounder discipline
skill_type: pattern
task_type: writing
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Report includes required sections from Section 9.2
  - Explicitly separates evidence vs interpretation
failure_modes_to_watch:
  - Overclaiming beyond evidence
inputs:
  prompt: |
    Produce a benchmark report template (Markdown) that matches Section 9.2 and includes explicit
    prompts for confounder tracking and blinding integrity.
```

**Rubric 4 — Discipline benchmark: exactly three options**

```yaml
id: v0-rubric-exact-three-options-007
title: Provide exactly 3 options with trade-offs and a recommendation
skill_target: Enforce strict countable structure (exactly 3 options) without drifting into extra options
skill_type: discipline
task_type: decision
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Output contains exactly 3 options (no more, no less)
  - Each option has at least 1 strength and 1 weakness
  - A single recommendation is stated after the options
failure_modes_to_watch:
  - “Honorable mentions” (counts as non-compliant)
  - Nested sub-options that create ambiguous counts
inputs:
  prompt: |
    You need to choose an approach for a small internal tool that ingests Markdown docs and provides fast search.
    Constraints:
    - Team has strong TypeScript experience
    - Needs to run locally (no managed search service)
    - Needs to support incremental updates to the index

    Provide options and a recommendation.
notes:
  - This scenario is designed to test the benchmark’s ability to detect strict-count discipline effects separately from correctness.
```

**Rubric 5 — Reference benchmark: constrained lookup and citation discipline**

```yaml
id: v0-rubric-reference-008
title: Answer using only local sources and cite exact file paths
skill_target: Demonstrate reference-skill behavior (source lookup + constrained claims) without web access
skill_type: reference
task_type: research
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Claims about repo content cite the exact file paths used (no invented sources)
  - Distinguishes “observed in files” vs “inference”
  - Does not use web browsing
failure_modes_to_watch:
  - Hallucinated repo facts
  - Vague citations (“the docs say…”) without paths
inputs:
  prompt: |
    Using only local repository files (no web), answer:

    1) What are the two canonical files that define benchmark control bodies and synthetic benchmark skill bodies?
    2) Where is the standardized injection slot heading for injected skills defined, and what is the exact heading text?

    Requirements:
    - Cite exact file paths for each answer.
    - If you infer anything not explicitly stated, label it as inference.
notes:
  - This is a reference-skill benchmark: it tests retrieval discipline and citation specificity, not “writing quality.”
```

**Rubric 3 — Draft a “placebo/irrelevant/harmful” control skill body**

```yaml
id: v0-rubric-controls-006
title: Draft control skill bodies that are safe and non-destructive
skill_target: Produce clear placebo/irrelevant/harmful bodies that cannot be mistaken for “real skills”
skill_type: discipline
task_type: writing
oracle_type: rubric_blinded
allowed_tools_expectation: no_web
success_criteria:
  - Control bodies are clearly defined and safe (no destructive actions)
  - Placebo is intentionally non-methodical
  - Harmful degrades outcomes without safety risk
failure_modes_to_watch:
  - Harmful instructions that could cause destructive actions
inputs:
  prompt: |
    Draft three control skill bodies (no frontmatter needed):
    - PLACEBO
    - IRRELEVANT (for code-change scenarios)
    - HARMFUL (non-destructive)

    Each must be short and clearly labeled.
```

### 3A.2 Conditions for Benchmark v0 (per scenario)

Default conditions:
- For all scenarios: `BASELINE` vs `TARGET`
- For 3 scenarios (recommended: Anchor 1, Rubric 1, Rubric 3): also run `PLACEBO`, `IRRELEVANT`, `HARMFUL`

Replication:
- N=3 for all baseline/target comparisons
- N=1 for each control condition initially (expand if controls show surprising deltas)

### 3A.3 Benchmark v0 acceptance (what counts as “it worked”)

Benchmark v0 is successful if:
- Anchor scenarios are runnable end-to-end with objective oracles (tests/build)
- Rubric scenarios are scored with blinding (document the blinding)
- Controls do not “win” systematically; if they do, report `INCONCLUSIVE` and propose measurement hardening

---

## 4) Conditions & Controls (Level 3 Operationalization)

For each scenario, run at least:
1. **BASELINE:** no injected skill
2. **TARGET:** injected target skill content

For a selected subset (controls coverage), also run:
3. **PLACEBO:** a “be careful/be clear” pseudo-skill without a real method
4. **IRRELEVANT:** a skill unrelated to the scenario’s task type
5. **HARMFUL:** a deliberately harmful constraint (e.g., too-short response, no tools)

### 4.1 Control coverage requirement

To make a “general” claim:
- **Minimum:** controls on **≥30%** of scenarios, stratified across task types.
- **Recommended:** controls on **≥50%** of scenarios for a strong “YES.”

### 4.2 Control skill definitions (canonical)

These are not “real” skills; they are benchmark instruments.

**Canonical source:** `docs/benchmarks/control-bodies_v0.1.0.md`

**Placebo (example body):**
- “Be careful and clear. Double-check your work. Do your best.”
- Avoid procedural requirements that would actually help (no checklists, no specific methods).

**Irrelevant:**
- Choose something plausibly orthogonal.
  - Example: a writing-style skill applied to a code-correctness-with-tests anchor scenario.

**Harmful (example bodies):**
- Hard response limit (e.g., “limit to 15 words”)
- Tool prohibition (e.g., “never use tools”)
- Overconfidence injection (e.g., “never express uncertainty”)

**Safety note:** Do not include harmful instructions that could cause destructive actions in the repo. Keep harm limited to outcome degradation, not safety risk.

---

## 5) Scenario Bank Specification (data model + representation)

This benchmark requires a “scenario bank”: a collection of scenario definitions with consistent metadata.

### 5.1 Required fields

Each scenario MUST define:
- `id`: stable identifier (slug or short hash)
- `title`: human-readable
- `skill_target`: the specific capability being tested (not “the entire skill”)
- `skill_type`: `discipline` | `technique` | `pattern` | `reference` (align with `docs/references/skills-guide.md`)
- `task_type`: `code-change` | `debugging` | `writing` | `planning` | `decision` | `research`
- `oracle_type`: `objective_tests` | `golden_output` | `rubric_blinded`
- `success_criteria`: checkable list (booleans/thresholds where possible)
- `failure_modes_to_watch`: list (baseline contamination, tool confounders, etc.)
- `allowed_tools_expectation`: `no_web` | `web_allowed` | `web_expected`
- `inputs`:
  - scenario prompt (what the runner receives)
  - any file paths, fixtures, or repo state assumptions needed

### 5.2 Optional fields
- `difficulty`: `simple` | `medium` | `complex`
- `domain`: e.g., `web` | `devops` | `data` | `docs`
- `notes`: clarifications, anti-gaming guidance, evaluator notes

### 5.3 Representation format (docs-only)

Use “YAML-in-Markdown” for each scenario definition:

```yaml
id: example-scenario-001
title: Fix failing test in module X
skill_target: Diagnoses + minimal fix without unrelated edits
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - All tests pass (`uv run pytest -q`)
  - Only files under `packages/<x>/` modified
failure_modes_to_watch:
  - Baseline contamination (runner adds discipline behavior)
  - Tool confounder (web search used despite no_web)
inputs:
  prompt: |
    You are in repo <…>. A test is failing. Fix it.
  files:
    - packages/<x>/...
notes:
  - Treat changes outside the target area as regressions.
```

**Guidance:** keep each scenario’s prompt short and tightly tied to the oracle.

---

## 6) Execution Protocol (how to run)

This framework uses the existing architecture:
- dynamic scenario skills with `context: fork`
- static runner: `.claude/agents/assessment-runner.md`

All execution mechanics and invariants are defined in:
- `docs/simulation-assessment-context-official.md`

### 6.1 Per-scenario execution steps (per condition)

For each scenario `S` and condition `C`:
1. Fix scenario ID and neutral naming.
2. Create the scenario skill file under `.claude/skills/.../SKILL.md`:
   - For BASELINE: scenario only
   - For TARGET/PLACEBO/IRRELEVANT/HARMFUL: inject the chosen “skill body” + scenario
3. Invoke the skill (using the `assessment-runner` agent).
4. Capture artifacts:
   - raw output
   - process trace/tool usage (Mode A) or logs/files (Mode B)
5. Cleanup temporary skill dirs with `trash`.

### 6.2 Tool confounder handling (required)

If tool usage differs materially between conditions (e.g., baseline triggers web search, test does not):
- Record it as a **confounder** in the run record.
- If the oracle could be affected (almost always), downgrade confidence OR re-run under a standardized `allowed_tools_expectation`.

---

## 7) Oracles & Scoring (Level 1–2 Operationalization)

### 7.1 Objective anchor oracles (preferred)

For anchor scenarios:
- Primary oracle: `uv run pytest -q` pass/fail and failure count.
- Optional: typecheck/lint pass/fail if relevant to scenario.
- Optional: golden output diff if scenario is deterministic transformation.

**Pass definition (objective_tests):**
- All declared tests/checks pass.
- No disallowed file changes (if specified in success criteria).

### 7.2 Rubric-based oracles (blinded)

For rubric scenarios, you MUST use blinding.

#### Blinding procedure (minimum)
1. Produce Output A and Output B (baseline vs target), but do not label them.
2. Randomize which is shown as A vs B.
3. Evaluator scores A and B independently against rubric dimensions.
4. Only after scoring, reveal which was baseline/test to compute delta.

#### Evaluators (allowed)
- Human evaluator (preferred for high-stakes conclusions)
- Secondary agent evaluator (acceptable for iteration; record as lower confidence)

#### Rubric (default)

Score each output on 0–2 per dimension:
- Correctness: meets task requirements
- Completeness: covers required parts
- Constraint adherence: follows explicit constraints
- Reasoning quality: decisions are justified and traceable
- Efficiency: proportionate approach
- Side effects: regressions/risks/overfitting avoided

Total per output: 0–12.

---

## 8) Adversarial & Proxy-Gaming Subset (Level 4 Operationalization)

To support a “general” measurement claim, include at least 4 adversarial scenarios or adversarial conditions:

1. **Proxy gaming:** looks compliant (adds required sections/counts) but degrades correctness.
2. **Empty section gaming:** includes a required section but with no substance.
3. **Self-check theater:** claims to self-check but misses obvious failures.
4. **Skill-body injection attempt:** injected skill tries to override the benchmark/run framing.
5. **Tool-confounding inducement:** injected instructions attempt to force tool usage changes that distort outcomes.

**Validity requirement:** Adversarial/proxy-gaming skills must not systematically “improve” on task-native oracles; if they do, verdict must be `NO` or `INCONCLUSIVE` unless you strengthen oracles/rubrics.

---

## 9) Run Records & Reporting (Level 5 Operationalization)

### 9.1 Run record template (per run)

Record each run in a consistent structure (markdown is fine):
- Scenario `id`
- Condition `C` (baseline/target/placebo/irrelevant/harmful)
- Run number (`1..N`)
- Observability mode (A/B)
- Raw output (or pointer to it)
- Tool usage summary (as reported or as artifacts)
- Oracle results (tests pass/fail, failures count)
- Rubric scores (if applicable; include evaluator identity + blinded status)
- Confounders observed

### 9.2 Benchmark report template (per benchmark run)

Include:
- Scenario roster + which conditions were run
- Per-scenario deltas
- Aggregates by:
  - oracle_type
  - skill_type
  - task_type
- Controls outcomes summary
- Confounders summary
- Final verdict: `YES` / `NO` / `INCONCLUSIVE` with justification

### 9.3 Default decision thresholds (pragmatic)

For a “YES” claim:
- Target improves on ≥70% of scenarios it targets, with no high-severity regressions.
- Placebo/irrelevant show net ~0 delta (no consistent wins beyond noise).
- Harmful shows negative deltas in most anchor scenarios.
- Adversarial/proxy-gaming attempts do not produce systematic “wins” on task-native outcomes.

If placebo/irrelevant consistently “win,” verdict must be `NO` or `INCONCLUSIVE` (measurement contaminated).

Variance handling:
- Start N=3; expand to N=5 for borderline or high-variance scenarios.

---

## 10) Worked Example (minimal, illustrative)

This section is a template example to show what “complete” looks like. It is not tied to a specific repo test suite; adapt it to a real anchor scenario when executing.

### Example scenario definition (anchor)

```yaml
id: anchor-fix-tests-001
title: Fix failing unit tests in a narrow module
skill_target: Minimal correct fix with no unrelated edits
skill_type: technique
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - `uv run pytest -q` passes
  - Only files in the target module are modified
failure_modes_to_watch:
  - Tool confounding (web usage)
  - Broad refactor to “make tests pass”
inputs:
  prompt: |
    A unit test is failing in the target module. Fix it with the smallest change.
  files:
    - packages/<target>/...
notes:
  - If you touch unrelated files, mark as regression.
```

### Example run record (outline)

- Scenario: `anchor-fix-tests-001`
- Condition: `BASELINE`
- Run: 1/3
- Observability: Mode A
- Output: (captured)
- Oracle: pytest FAIL (2 failing tests)
- Confounders: none

Then repeat for `TARGET`, and for controls where applicable.

---

## 11) Common Pitfalls (quick reference)

- **Mistaking proxy compliance for effectiveness:** countable structure isn’t enough; anchor oracles are.
- **No controls:** without placebo/irrelevant/harmful, you can’t detect evaluator bias.
- **No blinding:** rubric scores without blinding are not credible for “general” claims.
- **Tool confounders ignored:** if phrasing flips web usage, your delta may be mostly tool access, not the skill.
