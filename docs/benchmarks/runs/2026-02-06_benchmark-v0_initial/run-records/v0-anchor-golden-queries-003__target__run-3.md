# Run Record: v0-anchor-golden-queries-003 / target / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-golden-queries-003`
- **condition:** `target`
- **replicate:** run-3
- **injected_body:** `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` (from `docs/benchmarks/bench-skill-bodies_v0.1.0.md`; mapping from `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` deterministic TARGET mapping table)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-golden-queries-003/SKILL.md` (target template from Section 4.2, `docs/simulation-assessment-context-official.md`)
- **description_field:** `Scenario run for golden queries — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)

## Clean Start Verification

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start confirmed)
```

## Output

### Change Made

Added 1 new golden query assertion to `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`.

**Query added:** `{ query: 'creating SKILL.md file directory', expectedTopCategory: 'skills' }`

**What it tests:** The search engine's ability to map a skill creation query to the `skills` category. Targets the "Creating skills" subsection in the mock corpus containing terms "Create a SKILL.md file" and ".claude/skills directory." Non-overlapping with the existing `'skill frontmatter'` query which targets the "Skill frontmatter" subsection.

**Rationale (runner-reported):** Analysed existing 12 golden queries and their category coverage. The `skills` category had only 1 existing assertion (`skill frontmatter`) while the mock corpus has two distinct subsections — "Skill frontmatter" and "Creating skills." Selected the uncovered "Creating skills" subsection. Query uses terms directly from that section for high-confidence matching.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
index a1d405c..a1b304a 100644
--- a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
@@ -232,6 +232,7 @@ describe('golden queries (URL-based)', () => {
     { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
     { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
     { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
+    { query: 'creating SKILL.md file directory', expectedTopCategory: 'skills' },
   ];
```

**Files changed:** 1 (`tests/golden-queries.test.ts`)
**Lines added:** 1 (1 new golden query assertion in the array)
**Production code changes:** 0
**Mock corpus changes:** 0
**Test count change:** 15 → 16 golden query assertions in the parametric test

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read test file: `golden-queries.test.ts` to understand mock corpus and existing 12 assertions
2. Analysed coverage gaps — identified `skills` category with only 1 assertion and an uncovered "Creating skills" subsection
3. Selected "Creating skills" subsection as target (second skills subsection)
4. Added 1 assertion at line 235 in the `goldenQueries` array
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 tests)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (test file only based on runner report)
- No unrelated files modified
- Runner ran the oracle command once as pre-check
- Runner explicitly described identifying the "smallest change" and keeping diff minimal, consistent with loaded skill

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

```
$ npm -w packages/mcp-servers/claude-code-docs test

 RUN  v2.1.9

 ✓ tests/server.test.ts (23 tests) 21ms
 ✓ tests/bm25.test.ts (23 tests) 10ms
 ✓ tests/frontmatter.test.ts (33 tests) 16ms
 ✓ tests/chunker.test.ts (32 tests) 45ms
 ✓ tests/golden-queries.test.ts (16 tests) 115ms
 ✓ tests/url-helpers.test.ts (20 tests) 10ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 6ms
 ✓ tests/fence-tracker.test.ts (10 tests) 6ms
 ✓ tests/index-cache.test.ts (6 tests) 6ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 611ms
 ✓ tests/categories.test.ts (5 tests) 6ms
 ✓ tests/parser.test.ts (7 tests) 7ms
 ✓ tests/fetcher.test.ts (4 tests) 9ms
 ✓ tests/tokenizer.test.ts (11 tests) 3ms
 ✓ tests/cache.mock.test.ts (1 test) 4ms
 ✓ tests/error-messages.test.ts (3 tests) 2ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2175ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Duration  2.60s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.60s
- **Failures:** 0
- **Skipped:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `golden-queries.test.ts` now shows 16 tests (was 15), confirming the new assertion was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation per `docs/benchmarks/target-skills_v0.1.0.md`).
- **Naming bias:** Skill file used neutral name `scenario-golden-queries-003`. Description field is neutral — no condition label.
- **Skill compliance signal:** Runner mentioned analysing coverage gaps, choosing the "smallest change," and keeping the diff minimal — consistent with the injected `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` body. However, baseline runs also produce minimal 1-line changes (ceiling effect persists).
- **Cross-run state:** Clean start verified. No contamination from prior runs.
- **Convergence with baseline runs 1–2:** Target run-3 chose `skills` → "Creating skills" — the same category and subsection as baseline run-1 (`'creating SKILL.md .claude/skills directory'`) and baseline run-2 (`'creating SKILL.md in skills directory'`). The query string differs but targets the same content.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-golden-queries-003
(success — no output)

# 2. Revert code changes to restore clean starting state
$ git checkout -- packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
(success — no output)

# 3. Verify clean state
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean state confirmed)

# 4. Verify skill directory removed
$ ls .claude/skills/scenario-golden-queries-003
ls: No such file or directory
```

## Canonical Mapping Citations

- **Condition → body mapping:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` deterministic TARGET mapping table: `v0-anchor-golden-queries-003` → `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0`
- **Body content:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md` § `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0`
- **Target template:** `docs/simulation-assessment-context-official.md` Section 4.2
- **Tool expectation:** `docs/benchmarks/target-skills_v0.1.0.md` (`no_web`)

## Notes

- **Target run-3 converged on `skills` → "Creating skills" — same as baseline run-1 and run-2.** Query strings differ (`'creating SKILL.md file directory'` vs `'creating SKILL.md .claude/skills directory'` vs `'creating SKILL.md in skills directory'`), but all three target the same mock corpus subsection. This is a strong convergence signal: the "Creating skills" subsection is the dominant attractor for this scenario.
- **Cross-condition convergence summary for golden-queries-003:**
  - `skills` → "Creating skills": baseline run-1, baseline run-2, **target run-3** (3/6 runs)
  - `troubleshooting` → "Connection troubleshooting": baseline run-3 (steered), target run-1 (2/6 runs)
  - `security` → "Permission boundaries": target run-2 (1/6 runs)
- **Ceiling effect confirmed across all 6 runs.** Every run produced exactly 1 line added. The `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` skill's "keep diff minimal" guidance is indistinguishable from default behavior on this scenario. The scenario does not discriminate between baseline and target on output structure, diff size, or task completion quality.
- **Scenario v0-anchor-golden-queries-003 is now COMPLETE (6/6 runs).** All runs: oracle PASS, task_completion_verdict PASS.
