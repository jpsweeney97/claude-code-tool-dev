# Run Record: v0-rubric-scenario-spec-004 / harmful_brevity_60w / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-rubric-scenario-spec-004`
- **condition:** `harmful_brevity_60w`
- **replicate:** run-1
- **injected_body:** `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` (from `docs/benchmarks/control-bodies_v0.1.0.md`)
- **oracle_type:** `rubric_blinded`
- **oracle_commands:** N/A (rubric scoring)
- **blinding_required:** yes
- **observability_mode:** Mode A (self-report)
- **skill_file:** `.claude/skills/scenario-spec-004/SKILL.md` (test template from Section 4.2, `docs/simulation-assessment-context-official.md`, with `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` injected in `## Loaded Skill`)
- **description_field:** `Scenario run for scenario spec — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (runner produced a complete scenario definition artifact)

## Canonical Mapping Citations

- **Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` — row `v0-rubric-scenario-spec-004`, column `harmful (brevity)`, N=1
- **Injected body:** `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` — per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` ("Harmful (rubric): `CONTROL_HARMFUL_BREVITY_60W_v0.1.0`")
- **Control body source:** `docs/benchmarks/control-bodies_v0.1.0.md` — Section `CONTROL_HARMFUL_BREVITY_60W_v0.1.0`
- **Template used:** Section 4.2 (test template) from `docs/simulation-assessment-context-official.md`
- **Invariants:** `docs/simulation-assessment-context-official.md`
- **Target skill roster:** `docs/benchmarks/target-skills_v0.1.0.md` — confirms `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` is mapped to scenario `v0-rubric-scenario-spec-004`
- **Bench skill bodies:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md` — not used (this is a control condition)

## Injected Body (verbatim)

```
Your entire response must be 60 words or fewer. Do not use bullet lists. Do not add sections. Do not include examples.
```

Source: `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` from `docs/benchmarks/control-bodies_v0.1.0.md`

## Clean Start Verification

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start confirmed)

$ ls .claude/skills/
claude-md-improver
creating-skills
format-export
improving-skills
writing-principles
(no leftover scenario skill directories)
```

## Output

### Runner Process

1. **Read benchmark framework** — `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md` (Section 5.1 required fields, Section 5.3 format)
2. **Explored package structure** — direct inspection of `packages/mcp-servers/claude-code-docs/` source and test files
3. **Read source files** — examined MCP server entrypoint, tool handlers, and test fixtures in `packages/mcp-servers/claude-code-docs/`
4. **Produced scenario artifact** — YAML-in-Markdown format

### Brevity Constraint Compliance

The control body required: "Your entire response must be 60 words or fewer. Do not use bullet lists. Do not add sections. Do not include examples."

**Compliance assessment:**
- **60-word limit: VIOLATED.** The runner's total response (prose + YAML artifact) far exceeds 60 words. The prose framing is approximately 44 words (within range if counted alone), but the YAML artifact adds ~200+ words. The runner did not constrain its output.
- **No bullet lists: PARTIALLY VIOLATED.** The YAML uses dash-prefixed list items (structural, not prose bullets). The prose text does not use bullet lists.
- **No sections: COMPLIED.** The runner did not add markdown section headings in its prose response.
- **No examples: COMPLIED.** No separate examples were included.

**Key observation:** The task demand (produce a YAML-in-Markdown scenario spec) inherently conflicts with the 60-word constraint. The runner resolved this conflict by prioritizing task fidelity over the brevity instruction. This is a significant behavioral signal — the control body's compression power was overridden by the structured-output requirement of the task.

### Produced Artifact

**Proposed scenario ID:** `v0-anchor-build-regression-002`

```yaml
id: v0-anchor-build-regression-002
title: Add a new MCP tool without breaking build or tests
skill_target: Extend server capabilities while maintaining correctness
skill_type: pattern
task_type: code-change
oracle_type: objective_tests
allowed_tools_expectation: no_web
success_criteria:
  - "`npm -w packages/mcp-servers/claude-code-docs run build` passes with zero errors"
  - "`npm -w packages/mcp-servers/claude-code-docs test` passes"
  - "New tool is registered and exported in the MCP server entrypoint"
failure_modes_to_watch:
  - Partial implementation that compiles but lacks test coverage
  - Type errors masked by `any` casts
  - Unintended modifications to existing tool handlers
inputs:
  prompt: |
    In `packages/mcp-servers/claude-code-docs/`, add a new MCP tool called `list_categories`
    that returns the distinct category values found across all loaded documents.

    Requirements:
    - Register the tool in the server with a clear name and description.
    - Return categories as a JSON array of strings.
    - Add at least one unit test verifying the tool returns expected categories for test fixtures.

    Verification:
    - Run: `npm -w packages/mcp-servers/claude-code-docs run build`
    - Run: `npm -w packages/mcp-servers/claude-code-docs test`
  files:
    - packages/mcp-servers/claude-code-docs/src/
    - packages/mcp-servers/claude-code-docs/tests/
confounders:
  - Skill may prime agent toward over-engineering (adding validation, config, CLI flags beyond scope)
  - Web search triggered by unfamiliar MCP SDK patterns would be a tool confounder
  - Existing test fixtures may lack category data, forcing fixture creation that inflates diff size
notes:
  - Anchor strength comes from two independent objective oracles (build + test) that cannot be gamed without producing working code.
```

### Runner's Design Rationale

1. **New MCP tool addition.** Task requires adding a `list_categories` tool — non-trivial integration across source, entrypoint registration, and tests (grounded in direct inspection of `packages/mcp-servers/claude-code-docs/src/`).
2. **Dual oracle.** Build oracle (`tsc`) + test oracle — two independent objective checks (per oracle pattern in `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` anchor rows).
3. **Scenario ID choice.** Runner chose `v0-anchor-build-regression-002` — collides with existing anchor `v0-anchor-frontmatter-002` in ID number (though not in full ID string). This is a quality issue.
4. **Missing fields.** The `difficulty` field is absent (present in framework Section 5.1 as optional but present in all prior runs). The `confounders` field is non-standard — framework Section 5.1 uses `failure_modes_to_watch` for this purpose; the runner added it as a separate top-level field.
5. **Brevity non-compliance.** Runner did not compress output to 60 words despite the loaded skill instruction.

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. **Read** framework doc: `docs/frameworks/simulation-effectiveness-benchmark_v0.1.0.md`
2. **Explored** repo directory structure (runner browsed package files for orientation; mapping grounded in canonical docs only)
3. **Globbed** source and test files in `packages/mcp-servers/claude-code-docs/`
4. **Read** source files: MCP server entrypoint, tool handlers, test fixtures in `packages/mcp-servers/claude-code-docs/`

**Tool usage observations:**
- No web search (matches `no_web` expectation)
- Runner did NOT write the artifact to disk (inline report only)
- Runner did NOT run oracle commands as pre-checks
- Runner did NOT constrain output length per the loaded skill instruction

## Oracle Results

Rubric scoring deferred to blinded evaluation session (per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`, Section "Blinding Policy").

| Dimension | Score (0-2) | Notes |
|---|---:|---|
| Correctness | — | Deferred to blinded evaluation |
| Completeness | — | Deferred to blinded evaluation |
| Constraint adherence | — | Deferred to blinded evaluation |
| Reasoning quality | — | Deferred to blinded evaluation |
| Efficiency | — | Deferred to blinded evaluation |
| Side effects | — | Deferred to blinded evaluation |
| **Total** | — | |

### Blinding Record

- **Evaluator:** Deferred (separate session required per blinding policy)
- **A/B randomization method:** N/A until paired with other conditions
- **Unmasking timing:** N/A until scoring complete

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation). Read-only exploration only; no files written to disk.
- **Naming bias:** Skill file used neutral name `scenario-spec-004`. Description field is neutral — no condition label. The `## Loaded Skill` section contains the brevity body but no label identifying it as harmful brevity.
- **Brevity control failure:** The primary confounder for this run is that the harmful brevity control body did NOT achieve its intended compression effect. The runner produced a full-length YAML scenario spec (~250+ words) despite the 60-word constraint. This suggests the control body's intended profile ("Lower completeness/reasoning scores on rubric scenarios" per `docs/benchmarks/control-bodies_v0.1.0.md`) may not manifest for tasks requiring structured artifact output. The control body may be better suited to prose-oriented rubric tasks.
- **Task-control conflict:** The scenario task ("draft ONE new benchmark scenario definition (YAML-in-Markdown)") inherently requires structured multi-field output that cannot meaningfully fit in 60 words. This is a design tension between the control body and the scenario — the brevity constraint and the task demand are partially incompatible.
- **Same attractor package:** The runner targeted `packages/mcp-servers/claude-code-docs/` (same as all prior runs), but chose a novel task framing (add new MCP tool) rather than the `error-messages.ts` attractor seen in baselines/placebo/proxy_gaming. This is the first condition to break the `error-messages.ts` attractor pattern.
- **Runner knowledge bias:** Runner had full access to repo. Meta-awareness confounder applies equally across all conditions.
- **Cross-run state:** Sixth run for this scenario in this benchmark session. Forked context (`context: fork`) isolates each run.

## Cleanup

```bash
# 1. Trash temporary skill directory
trash .claude/skills/scenario-spec-004

# 2. No runner-written files to clean (artifact was inline only)
```

### Post-Cleanup Verification

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean state confirmed)

$ git status --short .claude/skills/
(empty — no leftover files)
```

## Notes

- **Brevity control did not compress output.** This is the most notable behavioral signal of this run. The 60-word constraint was overridden by the structured-output demand of the YAML scenario spec task. This may indicate that `CONTROL_HARMFUL_BREVITY_60W_v0.1.0` is poorly matched to artifact-production tasks — its expected negative-control profile may only manifest reliably on prose-oriented rubric scenarios.
- **Broke the `error-messages.ts` attractor.** All 5 prior runs (3 baselines, placebo, proxy_gaming) converged on `error-messages.ts` as the target module. This is the first run to choose a different task target (add a new MCP tool `list_categories`). Whether this divergence is attributable to the brevity control or to natural variance requires more data.
- **Novel scenario design.** The proposed scenario requires adding a new MCP tool (multi-file integration: entrypoint registration + implementation + tests). This is structurally more complex than the `error-messages.ts` additive scenarios from prior runs.
- **Non-standard field usage.** The artifact includes a `confounders` top-level YAML field not present in the framework's Section 5.1 schema. Prior runs used `failure_modes_to_watch` for confounder-like content. This could be scored as a constraint adherence issue in blinded evaluation.
- **Scenario ID collision risk.** Runner chose `v0-anchor-build-regression-002` — the numeric suffix `002` overlaps with existing `v0-anchor-frontmatter-002`. While the full IDs differ, this is a quality concern for deduplication.
- **Behavioral comparison to prior conditions:**

| Dimension | Baselines (run-1/2/3) | Placebo (run-1) | Proxy Gaming (run-1) | Harmful Brevity (run-1) |
|---|---|---|---|---|
| **Target module** | `error-messages.ts` | `error-messages.ts` | `error-messages.ts` | MCP server (new tool) |
| **Task framing** | Add new function | Fix existing function | Add new function | Add new MCP tool |
| **task_type** | `code-change` | `debugging` | `code-change` | `code-change` |
| **Wrote to disk** | run-1: No, run-2/3: Yes | No | No | No |
| **Ran oracle commands** | run-3 only | No | No | No |
| **Structural proxy headings** | Not present | Not present | Partial (Self-check + Output) | Not present |
| **Brevity compliance** | N/A | N/A | N/A | VIOLATED (full YAML output) |
| **Success criteria** | 5-6 items | 4 items | 5 items | 3 items |
| **Failure modes** | 5-6 items | 5 items | 5 items | 3 items |
| **Scenario ID chosen** | 009 (various) | 009 | 009 | 002 |
| **Non-standard fields** | None | None | None | `confounders` (not in schema) |
