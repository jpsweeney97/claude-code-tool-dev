# Run Record: v0-rubric-reference-008 / target / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-reference-008`
- **condition:** `target`
- **replicate:** `run-1`
- **injected_body:** `BENCH_REFERENCE_LOCAL_CITATIONS_ONLY_v0.1.0` (`docs/benchmarks/bench-skill-bodies_v0.1.0.md`)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** A (self-report)
- **invocation_mechanism:** Skill tool (`Skill(skill: "scenario-repo-lookup-jnr")`)
- **skill_file:** (omitted)

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

The runner answered both questions using local repository files, citing exact paths with line numbers and explicitly labeling all claims as "Observation." Full raw output below.

---

**Process section (runner self-report):**

5-step process: (1) Glob search for files containing "control", "synthetic", "benchmark", and "skill-bod" patterns under `docs/`, identifying two candidate canonical files, (2) Read both candidate files in full to confirm their purpose and content, (3) Grep for "injection slot", "injected skill", and "Loaded Skill" across `docs/` to locate where the injection heading is defined, (4) Read `simulation-effectiveness-benchmark_v0.1.0.md` around the scenario definition, (5) Read `simulation-assessment-context-official.md` Sections 4.1 and 4.2 to confirm the authoritative template definition.

**Answer 1: Two canonical files for control bodies and synthetic benchmark skill bodies**

- **Control bodies:** `docs/benchmarks/control-bodies_v0.1.0.md` — line 1 states "Control Bodies v0.1.0 (Benchmark Instruments)"; line 3 states: "This file defines canonical control 'skill bodies' used by the Simulation Effectiveness Benchmark to validate measurement integrity." Contains: CONTROL_PLACEBO, CONTROL_IRRELEVANT_FOR_CODE, CONTROL_HARMFUL_NO_TOOLS, CONTROL_HARMFUL_BREVITY_60W, CONTROL_PROXY_GAMING.
- **Synthetic benchmark skill bodies:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md` — line 1 states "Synthetic Benchmark Skill Bodies v0.1.0 (BENCH_*)"; lines 3-4 state: "This file defines canonical instruction bodies for synthetic benchmark skills referenced by: `docs/benchmarks/target-skills_v0.1.0.md`". Contains: BENCH_DISCIPLINE_EXACT_THREE_OPTIONS, BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF, BENCH_PATTERN_BLINDED_EVAL_DISCIPLINE, BENCH_TOOL_SENSITIVITY_WEB_SEARCH_PUSH, BENCH_REFERENCE_LOCAL_CITATIONS_ONLY.

Runner labeled both as "Observation."

**Answer 2: Standardized injection slot heading**

- **Heading text:** `## Loaded Skill`
- **Primary definition:** `docs/simulation-assessment-context-official.md`, Section 4.2, line 139. Runner cited the file's self-declaration as authoritative (lines 102-103): "These templates are authoritative. If other docs show slightly different templates, follow these templates and log drift if it is material."
- **Supporting citations (referenced, not independently defined):**
  - `docs/benchmarks/control-bodies_v0.1.0.md` (lines 9-10: "Heading: `## Loaded Skill`" and delimiter wrapping instructions)
  - `docs/benchmarks/bench-skill-bodies_v0.1.0.md` (lines 7-8: "Heading: `## Loaded Skill`" and delimiter wrapping instructions)
  - (omitted: non-canonical rules file reference)

Runner labeled answer as "Observation" and noted all other files are consistent with the authoritative source.

---

## Tool Trace

**Mode A (self-report).** The runner reported the following tool invocations:

| # | Tool | Target | Purpose |
|---|------|--------|---------|
| 1 | Glob | Files under `docs/` with benchmark/control/skill patterns | Discover candidate canonical files |
| 2 | Read | `docs/benchmarks/control-bodies_v0.1.0.md` | Confirm role and content |
| 3 | Read | `docs/benchmarks/bench-skill-bodies_v0.1.0.md` | Confirm role and content |
| 4 | Grep | "injection slot", "injected skill", "Loaded Skill" in `docs/` | Locate injection heading definition |
| 5 | Read | `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` | Read scenario definition context |
| 6 | Read | `docs/simulation-assessment-context-official.md` | Confirm authoritative template definition |

**Comparison to baselines:** Baselines used 8-9 tool invocations (Glob/Grep + Read). Target run-1 used ~6 invocations — slightly fewer.

## Oracle Results

**Scoring mode: `rubric_blinded` — DO NOT self-score.**

Scoring deferred to blinded evaluator per `rubric_blinded` protocol.

### Blinding Record

- **Evaluator:** Deferred (requires separate session or human)
- **A/B randomization method:** Deferred (to be determined at scoring time)
- **Unmasking timing:** Deferred (must occur after scoring)

## Confounders

- **Tool usage — inherent to scenario:** ~6 tool invocations (Glob, Grep, Read). Expected and inherent to `task_type: research`. Slightly lower count than baselines (8-9). The difference is minor and may reflect efficiency rather than a meaningful behavioral shift.
- **Runner read canonical execution context:** Runner read `docs/simulation-assessment-context-official.md`, which contains experiment methodology. Same as baselines. Session-isolated via forked context.
- **Rules file citation (differential):** Omitted (non-canonical rules file reference).
- **Naming bias:** Skill name `scenario-repo-lookup-jnr` is neutral. No bias detected.
- **Citation depth:** Runner cited 5 files with specific line numbers (including the rules file). Baselines cited 5-6 files. Comparable depth.
- **Authoritative source hierarchy:** Runner explicitly quoted the self-declaration of authority from `simulation-assessment-context-official.md` (lines 102-103). Baselines noted authority but did not quote the self-declaration passage. This is a qualitative difference in citation precision.

## Cleanup

```bash
$ trash .claude/skills/<neutral_name>
# (skill directory removed)

$ git checkout -- packages/mcp-servers/claude-code-docs/
# (scoped revert — NOT git checkout -- .)

$ git diff -- packages/mcp-servers/claude-code-docs/
# (empty — clean confirmed)
```

## Notes

- **Answer correctness (factual check, not rubric scoring):** Both answers factually correct. Same canonical files and heading identified as in all three baselines.
- **Observation vs inference discipline:** Runner explicitly labeled all claims as "Observation." No inferences declared. Same pattern as baselines. The injected skill instructs labeling — baselines also labeled without this instruction, so the skill reinforces existing baseline behavior rather than introducing new behavior.
- **Authority citation (potential skill effect):** The runner quoted the self-declaration of authority from `simulation-assessment-context-official.md` ("These templates are authoritative..."). Baselines mentioned authority but did not quote the specific passage. The injected skill's instruction to "cite exact file paths for each key claim" may have prompted more precise authority attribution.
- **Rules file as additional source:** Omitted (non-canonical rules file reference).
- **No web usage:** Consistent with `allowed_tools_expectation: no_web`.
- **First target run for scenario 008.** Establishes the target tool usage pattern for comparison with target runs 2 and 3.
