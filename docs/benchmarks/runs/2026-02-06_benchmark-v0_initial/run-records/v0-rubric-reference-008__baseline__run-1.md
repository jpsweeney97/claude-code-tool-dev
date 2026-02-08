# Run Record: v0-rubric-reference-008 / baseline / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-reference-008`
- **condition:** `baseline`
- **replicate:** `run-1`
- **injected_body:** none
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** A (self-report)
- **invocation_mechanism:** Skill tool (`Skill(skill: "scenario-repo-lookup-bmv")`)
- **skill_file:** `.claude/skills/scenario-repo-lookup-bmv/SKILL.md`

### Canonical References

- Framework: `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
- Suite matrix: `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
- Bench skill bodies: `docs/benchmarks/bench-skill-bodies_v0.1.0.md`
- Target roster: `docs/benchmarks/target-skills_v0.1.0.md`
- Control bodies: `docs/benchmarks/control-bodies_v0.1.0.md`
- Official context: `docs/simulation-assessment-context-official.md`

## Preflight

```bash
$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean start confirmed)
```

## Output

The runner answered both questions using local repository files, citing exact paths with line numbers. Full raw output below.

---

**Process section (runner self-report):**

The runner used 9 tool invocations: Glob on `docs/benchmarks/**/*.md` and `docs/frameworks/**/*.md`, Grep for "control bod(y|ies)" and "synthetic.*skill.*bod(y|ies)", then Read on 5 files to confirm roles and find the injection slot heading definition.

**Answer 1: Two canonical files for control bodies and synthetic benchmark skill bodies**

- **Control bodies:** `docs/benchmarks/control-bodies_v0.1.0.md` — self-describes as "Control Bodies v0.1.0 (Benchmark Instruments)"; defines CONTROL_PLACEBO, CONTROL_IRRELEVANT_FOR_CODE, CONTROL_HARMFUL_NO_TOOLS, CONTROL_HARMFUL_BREVITY_60W, CONTROL_PROXY_GAMING.
- **Synthetic benchmark skill bodies:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md` — self-describes as "Synthetic Benchmark Skill Bodies v0.1.0 (BENCH_*)"; defines BENCH_DISCIPLINE_EXACT_THREE_OPTIONS, BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF, BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE, BENCH_TOOL_SENSITIVITY_WEB_SEARCH_PUSH, BENCH_REFERENCE_LOCAL_CITATIONS_ONLY.

Runner cited `docs/benchmarks/target-skills_v0.1.0.md` (lines 62-68) as confirming both files are canonical, and `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` (lines 82-93) as referencing both in Quickstart sections.

Runner labeled both answers as "Observation" (directly stated in cited files).

**Answer 2: Standardized injection slot heading**

- **Heading text:** `## Loaded Skill`
- **Defined in:** `docs/simulation-assessment-context-official.md` (line 139, Section 4.2 canonical test template).
- Runner cited this as authoritative per the document's own source-of-truth policy (line 8).
- Runner confirmed consistency across 4 additional canonical files: `docs/benchmarks/control-bodies_v0.1.0.md` (line 9), `docs/benchmarks/bench-skill-bodies_v0.1.0.md` (line 7), `docs/benchmarks/target-skills_v0.1.0.md` (line 25), and `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` (Section 4.2).

Runner labeled this answer as "Observation."

---

## Tool Trace

**Mode A (self-report).** The runner reported 9 tool invocations:

| # | Tool | Target | Purpose |
|---|------|--------|---------|
| 1 | Glob | `docs/benchmarks/**/*.md` | Discover benchmark documentation files |
| 2 | Glob | `docs/frameworks/**/*.md` | Discover framework specification files |
| 3 | Grep | `control bod(y\|ies)` | Find files discussing "control bodies" |
| 4 | Grep | `synthetic.*skill.*bod(y\|ies)` | Find files discussing "synthetic benchmark skill bodies" |
| 5 | Read | `docs/benchmarks/control-bodies_v0.1.0.md` | Confirm role as canonical control body file |
| 6 | Read | `docs/benchmarks/bench-skill-bodies_v0.1.0.md` | Confirm role as canonical synthetic benchmark skill body file |
| 7 | Read | `docs/benchmarks/target-skills_v0.1.0.md` | Find where files are formally designated |
| 8 | Read | `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` | Find framework-level definition of injection slot heading |
| 9 | Read | `docs/simulation-assessment-context-official.md` | Find authoritative template definitions |

**Notable:** This is the first scenario in Benchmark v0 with non-zero tool usage. All prior rubric scenario runs (004, 005, 006, 007) had zero tool usage in baselines. The reference scenario inherently requires file lookup.

## Oracle Results

**Scoring mode: `rubric_blinded` — DO NOT self-score.**

Scoring deferred to blinded evaluator per `rubric_blinded` protocol.

### Blinding Record

- **Evaluator:** Deferred (requires separate session or human)
- **A/B randomization method:** Deferred (to be determined at scoring time)
- **Unmasking timing:** Deferred (must occur after scoring)

## Confounders

- **Tool usage — inherent to scenario:** The runner used 9 tool invocations (Glob, Grep, Read) to look up files. This is expected and inherent to the reference scenario design (`task_type: research`). Unlike writing/decision scenarios, this scenario cannot be answered without file access. Tool usage differentials between baseline and target should be evaluated relative to this baseline level.
- **Runner read canonical execution context:** The runner read `docs/simulation-assessment-context-official.md` (canonical execution context), which contains experiment methodology. This is inherent to the scenario — the questions ask about benchmark infrastructure — but the runner's exposure to assessment methodology could influence behavior on subsequent tasks in the same session. Since this runs in a forked context, the exposure is session-isolated.
- **Naming bias:** Skill name `scenario-repo-lookup-bmv` is neutral. No bias detected.
- **Citation depth:** The runner cited 6 files with specific line numbers. If target runs cite fewer or more files, that's a potential signal of the injected skill's effect on citation discipline.

## Cleanup

```bash
$ trash .claude/skills/scenario-repo-lookup-bmv
# (skill directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
# (scoped revert — NOT git checkout -- .)

$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean confirmed)
```

## Notes

- **Answer correctness (factual check, not rubric scoring):** Both answers appear factually correct based on repo content. The two canonical files are indeed `control-bodies_v0.1.0.md` and `bench-skill-bodies_v0.1.0.md`. The injection slot heading is indeed `## Loaded Skill` defined in `simulation-assessment-context-official.md` Section 4.2.
- **Observation vs inference discipline:** The runner labeled all answers as "Observation" with direct file citations. No inferences were declared. This is appropriate since both answers are directly stated in the cited files.
- **Cross-file consistency check:** The runner went beyond the minimum by verifying the injection slot heading across 5 additional files. This thoroughness is a baseline behavior signal — if target runs show more or less cross-referencing, that's evaluable.
- **No web usage:** Consistent with `allowed_tools_expectation: no_web`.
- **First reference scenario:** This is the first run of v0-rubric-reference-008 and establishes the baseline tool usage pattern for comparison with target runs.
