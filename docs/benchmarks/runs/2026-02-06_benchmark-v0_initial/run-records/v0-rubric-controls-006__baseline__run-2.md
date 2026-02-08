# Run Record: v0-rubric-controls-006 / baseline / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-controls-006`
- **condition:** `baseline`
- **replicate:** run-2
- **injected_body:** none (baseline)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **allowed_tools_expectation:** no_web
- **skill_file:** `.claude/skills/rubric-006-runner/SKILL.md` (cleaned up after run)
- **invocation_method:** Skill tool (`Skill(skill: "rubric-006-runner")`) → `context: fork` → `assessment-runner`

## Preflight

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start)
```

## Output

The runner produced three control skill bodies as requested. Full output below.

### PLACEBO

```md
---
Take your time and think things through. Aim for quality in your work. Remember that attention to detail matters, and your effort is valued.
---
```

**Runner's design rationale:** Three sentences of generic encouragement. No method, no procedure, no structure. "Take your time" and "aim for quality" provide no actionable technique — described by the runner as "the instructional equivalent of a motivational poster." Expected delta: near-zero versus baseline.

### IRRELEVANT (for code-change scenarios)

```md
---
Structure your response using the RACI framework: identify who is Responsible, Accountable, Consulted, and Informed for this change. Begin with a stakeholder impact summary. Conclude with a rollout communication plan addressed to non-technical leadership. Do not include raw code diffs or terminal output in your response.
---
```

**Runner's design rationale:** Imposes a professional-looking organizational framework (RACI) entirely orthogonal to code correctness. Forces the runner to produce stakeholder roles and communication plans instead of code changes. The "do not include raw code diffs" instruction actively suppresses useful output for code-change tasks. Expected delta: neutral-to-negative on code tasks.

### HARMFUL (non-destructive)

```md
---
Do not read or examine any existing source files before making changes. Make all edits in a single attempt with no iterating -- your first version is your final version. Do not run any verification commands (tests, builds, linters) after making changes. If uncertain about any detail, choose the simplest assumption and move on.
---
```

**Runner's design rationale:** Three compounding constraints that degrade code-change quality: (1) prohibiting file reads prevents understanding context/dependencies; (2) single-attempt/no-iteration removes self-correction; (3) prohibiting verification means errors go undetected. A fourth instruction ("choose the simplest assumption") promotes shallow reasoning. All constraints are safe — no destructive actions. Expected delta: negative.

### Runner's Distinguishability Analysis

| Property | Real skill (BENCH_*) | Control |
|---|---|---|
| Actionable procedure | Yes — specific steps, numbered processes | No (placebo) or orthogonal (irrelevant) or anti-procedural (harmful) |
| Domain relevance | Matched to task type | Absent (placebo), mismatched (irrelevant), or inverted (harmful) |
| Expected outcome | Improves task-native metrics | Neutral, orthogonal, or degrading |
| Verification integration | Encourages oracle use | Silent (placebo), suppresses (irrelevant/harmful) |

## Tool Trace

Mode A self-report from runner:

1. Read `.claude/skills/rubric-006-runner/SKILL.md` (scenario skill file)
2. Read `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` (suite matrix — naming conventions and control usage)
3. Read `docs/benchmarks/control-bodies_v0.1.0.md` (existing canonical controls — format and tone reference)
4. Read `docs/benchmarks/bench-skill-bodies_v0.1.0.md` (target skill bodies — contrast point for distinguishability)
5. Runner also mentioned reading a scenario file; however, no file under `docs/benchmarks/runs/` was read
6. No web search or web browsing performed

**Files read:** 4 (skill file + 3 canonical docs)
**Web usage:** none
**Disallowed reads:** none

## Oracle Results

Rubric scoring deferred to blinded evaluation per `rubric_blinded` oracle type.

DO NOT self-score. Scores will be assigned by a separate evaluator in a blinded session.

### Blinding Record

- **Evaluator:** To be determined (separate session or human)
- **A/B randomization method:** To be determined at scoring time
- **Unmasking timing:** Must occur after scoring is complete

## Confounders

- **Runner read existing canonical controls and bench skill bodies:** The runner read both `docs/benchmarks/control-bodies_v0.1.0.md` and `docs/benchmarks/bench-skill-bodies_v0.1.0.md` — legitimate canonical docs, but their content could anchor the runner's output toward variations of existing controls. Low-severity confounder: the scenario context already describes what controls are, and seeing examples could either help (better calibration) or hinder (anchoring). The runner also read bench skill bodies for explicit "distinguishability" analysis — a behavior beyond what the scenario prompt required.
- **Runner produced distinguishability analysis not requested by prompt:** The runner included a comparative table analyzing how the three controls differ from real BENCH_* skills. This is additional unrequested output — it does not contaminate the control bodies themselves but adds context that a blinded evaluator would see. Low-severity for scoring purposes.
- **No tool confounders observed.** No web usage, no unexpected tool patterns.

## Cleanup

```
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/rubric-006-runner
(success — no output)

$ git checkout -- packages/mcp-servers/claude-code-docs/
(success — no output)

$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean state confirmed)
```

**Confirmation:** Did NOT run `git checkout -- .` (only targeted `packages/mcp-servers/claude-code-docs/`).

## Notes

- **Run status:** COMPLETED
- Runner produced all three required control bodies (PLACEBO, IRRELEVANT, HARMFUL) with design rationale and a distinguishability analysis table.
- All three bodies are short (3-4 sentences each), clearly labeled, contain no YAML frontmatter, and are safety-preserving.
- Compared to run-1: PLACEBO uses slightly different wording ("take your time" vs run-1's "confidence and professionalism") but same vacuous pattern. IRRELEVANT uses RACI framework (vs run-1's Change Impact Brief) — different organizational structure, same orthogonality. HARMFUL uses similar triple-mechanism (no reads + no iteration + no verification) with an added fourth constraint ("choose simplest assumption") — similar approach to run-1 but with an additional degradation vector.
- Runner read 4 files (1 more than run-1 — added bench-skill-bodies for contrast analysis). This between-run tool usage variance is minor but recorded.
- No disallowed files were read. No leakage detected.

## Canonical References

1. `docs/simulation-assessment-context-official.md`
2. `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
3. `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
4. `docs/benchmarks/target-skills_v0.1.0.md`
5. `docs/benchmarks/control-bodies_v0.1.0.md`
6. `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
