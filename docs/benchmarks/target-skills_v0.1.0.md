# Target Skills v0.1.0 (Benchmark Roster)

This file defines the **versioned roster** of target skills used by the Simulation Effectiveness Benchmark.

**Framework:** `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`

## Purpose

The benchmark requires an explicit skill roster to avoid implicit selection bias and to make results reproducible. The roster is the authoritative answer to:

> “What exact target skills should I benchmark?”

## How to Use

1. Select a roster (this file version) before running a benchmark.
2. Record the roster version in your benchmark run’s `suite.md` and `report.md`.
3. For each scenario, run BASELINE vs TARGET for the skill(s) specified here.

## Roster: Synthetic Benchmark Skills v0.1.0 (Recommended)

This roster defines a set of **synthetic benchmark “skills”** intended to support the primary objective:

> Validate whether the assessment architecture measures functional effectiveness in general.

These are not required to exist as real `.claude/skills/*` directories. They are designed to be injected as bodies into the scenario skill’s `## Loaded Skill` section (see `docs/simulation-assessment-context-official.md`).

**Why synthetic:** They have deliberately controlled intent, expected effects, and failure modes. This makes placebo/irrelevant/harmful/adversarial behaviors interpretable and reduces selection bias.

### Required fields per skill

- `skill_name`: identifier you will inject (or reference) consistently
- `skill_type`: `discipline` | `technique` | `pattern` | `reference`
- `intended_effect`: what “effectiveness” means for this skill (task-native outcomes)
- `scenario_ids`: which scenario IDs this skill is expected to improve
- `tool_expectation`: `no_web` | `web_allowed` | `web_expected` (default for this skill in its scenarios)

### Skill roster table

| skill_name | skill_type | intended_effect | scenario_ids | tool_expectation |
|---|---|---|---|---|
| BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0 | discipline | Enforce a strictly countable output structure (“exactly 3 options with pros/cons + recommendation”) without claiming to improve correctness. | v0-rubric-exact-three-options-007 | no_web |
| BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0 | technique | Improve objective success on code-change tasks by requiring: (a) run test/build oracles, (b) keep diffs minimal, (c) avoid unrelated refactors. | v0-anchor-vitest-001, v0-anchor-frontmatter-002, v0-anchor-golden-queries-003 | no_web |
| BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE_v0.1.0 | pattern | Improve reporting integrity by separating evidence vs interpretation and enforcing blinding documentation in rubric scenarios. | v0-rubric-report-005 | no_web |
| BENCH_REFERENCE_LOCAL_CITATIONS_ONLY_v0.1.0 | reference | Improve source discipline: make claims grounded in repo files with exact path citations; distinguish observation vs inference; no web. | v0-rubric-reference-008 | no_web |
| BENCH_TOOL_SENSITIVITY_WEB_SEARCH_PUSH_v0.1.0 | technique | Deliberately increase tool-use confounding by encouraging web search even when not needed (used to test confounder detection, not to “help”). Expected to be neutral/negative on anchor outcomes. | v0-anchor-vitest-001 | web_expected |
| CONTROL_PLACEBO_v0.1.0 | discipline | Neutral “be careful” priming; should not systematically improve outcomes. | v0-anchor-vitest-001, v0-rubric-scenario-spec-004 | no_web |
| CONTROL_IRRELEVANT_FOR_CODE_v0.1.0 | pattern | Force PRD formatting and prohibit code/implementation details; should not improve objective oracles for code-change tasks. | v0-anchor-vitest-001 | no_web |
| CONTROL_HARMFUL_NO_TOOLS_v0.1.0 | discipline | Degrade anchor task success by prohibiting tools/tests/builds (safe negative control). | v0-anchor-vitest-001, v0-anchor-frontmatter-002 | no_web |
| CONTROL_HARMFUL_BREVITY_60W_v0.1.0 | discipline | Degrade rubric task scores by forcing harmful compression (safe negative control). | v0-rubric-scenario-spec-004, v0-rubric-controls-006 | no_web |
| CONTROL_PROXY_GAMING_v0.1.0 | discipline | Demonstrate proxy gaming: include proxy artifacts (sections/self-check) while reducing substance; should not improve task-native outcomes. | v0-rubric-scenario-spec-004, v0-rubric-report-005 | no_web |

## Scoring notes (to prevent over-crediting structure)

Some benchmark skills intentionally improve **structure** without necessarily improving **correctness**. To avoid mistaking structure for functional effectiveness:

- For `BENCH_DISCIPLINE_EXACT_THREE_OPTIONS_v0.1.0` on `v0-rubric-exact-three-options-007`:
  - Score compliance primarily with the **Exact Count Requirements** rubric (COMPLIANT/PARTIAL/NON-COMPLIANT).
  - Treat “more words,” “more reasoning,” or “more elaboration” as neutral unless the scenario explicitly requires it.

If the discipline benchmark “wins” overall by inflating non-structural rubric dimensions, treat that as a measurement design failure (rubric confounded by verbosity/structure).

## Canonical control body source

The control bodies in this roster are defined canonically in:
- `docs/benchmarks/control-bodies_v0.1.0.md`

For synthetic non-control benchmark skills (the `BENCH_*` entries), create a dedicated canonical file before running Benchmark v0:
- `docs/benchmarks/bench-skill-bodies_v0.1.0.md`

Until that file exists, do not assume the “BENCH_*” bodies are stable or identical across runs.

## Selection guidance (non-binding)

To support a “general measurement validity” claim, prefer a roster that includes:
- at least one discipline/technique style skill with countable requirements
- at least one qualitative pattern/workflow skill
- at least one tool-sensitive skill (where tool usage could be a confounder)
- at least one “hard” skill where success is not purely structural

Do not include skills that are tightly coupled to this repo’s conventions unless you explicitly want to test “local effectiveness” rather than “general measurement validity.”
