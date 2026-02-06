# Run Record: v0-anchor-golden-queries-003 / baseline / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-golden-queries-003`
- **condition:** `baseline`
- **replicate:** run-1
- **injected_body:** none
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-golden-queries-003/SKILL.md` (baseline template from Section 4.1, `docs/simulation-assessment-context-official.md`)
- **description_field:** `Scenario run for golden queries — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)

## Canonical Mapping Citations

- **Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` — row `v0-anchor-golden-queries-003`, column `baseline`, N=3
- **Injected body:** none (baseline condition) — per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md`
- **Invariants:** `docs/simulation-assessment-context-official.md`

## Clean Start Verification

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start confirmed)
```

## Output

### Change Made

Added 1 new golden query assertion to `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`.

**Query added:** `{ query: 'creating SKILL.md .claude/skills directory', expectedTopCategory: 'skills' }`

**What it tests:** The search engine's ability to map a query about creating skill files to the `skills` category. The existing skills query (`'skill frontmatter'`) targets frontmatter metadata; the new query targets the distinct "Creating skills" subsection in the mock corpus containing content about creating SKILL.md files.

**Rationale:** Non-overlapping with existing 12 golden queries (the `skills` category had 1 existing query for frontmatter; this adds a second for a different subsection). Realistic user query — a developer looking for how to create a skill file.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
index a1d405c..ad5dd8e 100644
--- a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
@@ -232,6 +232,7 @@ describe('golden queries (URL-based)', () => {
     { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
     { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
     { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
+    { query: 'creating SKILL.md .claude/skills directory', expectedTopCategory: 'skills' },
   ];
```

**Files changed:** 1 (`tests/golden-queries.test.ts`)
**Lines added:** 1 (1 new golden query assertion in the array)
**Production code changes:** 0
**Mock corpus changes:** 0
**Test count change:** 15 → 16 golden query assertions in the parametric test (254 total tests unchanged — the new assertion is a data-driven iteration, not a new `it()` block)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read test file: `golden-queries.test.ts` to understand mock corpus and existing assertions
2. Read categories file: `src/categories.ts` to confirm URL-to-category mappings
3. Analyzed 12 existing golden queries and identified coverage by category
4. Selected "Creating skills" subsection as target (non-overlapping with existing `'skill frontmatter'` query)
5. Added 1 assertion at line 235 in the `goldenQueries` array
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 tests)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (1 test file, 1 source file)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

```
$ npm -w packages/mcp-servers/claude-code-docs test

 RUN  v2.1.9

 ✓ tests/server.test.ts (23 tests) 18ms
 ✓ tests/bm25.test.ts (23 tests) 8ms
 ✓ tests/frontmatter.test.ts (33 tests) 12ms
 ✓ tests/chunker.test.ts (32 tests) 29ms
 ✓ tests/golden-queries.test.ts (16 tests) 63ms
 ✓ tests/url-helpers.test.ts (20 tests) 4ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 6ms
 ✓ tests/index-cache.test.ts (6 tests) 4ms
 ✓ tests/fence-tracker.test.ts (10 tests) 4ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 400ms
 ✓ tests/categories.test.ts (5 tests) 3ms
 ✓ tests/parser.test.ts (7 tests) 4ms
 ✓ tests/fetcher.test.ts (4 tests) 3ms
 ✓ tests/tokenizer.test.ts (11 tests) 5ms
 ✓ tests/cache.mock.test.ts (1 test) 7ms
 ✓ tests/error-messages.test.ts (3 tests) 3ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2112ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Duration  2.47s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.47s
- **Failures:** 0
- **Skipped:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `golden-queries.test.ts` now shows 16 tests (was 15), confirming the new assertion was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-golden-queries-003`. Description field is neutral — no condition label.
- **Scenario specificity:** This scenario targets a specific file (`golden-queries.test.ts`) and asks for a specific type of change (add one golden query assertion). Scope is narrow.
- **Cross-run state:** This is the first executed run for this scenario. No prior state to contaminate.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash .claude/skills/scenario-golden-queries-003

# 2. Revert code changes to restore clean starting state
git checkout -- packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-golden-queries-003` no longer exists.

## Notes

- **Minimal, well-targeted change.** The runner added exactly 1 golden query assertion (1 line), targeting a second subsection of the `skills` category that was non-overlapping with the existing `'skill frontmatter'` query. No mock corpus expansion was needed.
- **Category coverage:** After this change, `skills` is the only category with 2 golden queries. All other categories have exactly 1 each. This is a reasonable choice given the mock corpus has two distinct skills subsections.
- **Convergence risk for replicates:** The `skills` category has the most remaining subsection surface (2 subsections in mock), which makes it a likely convergence attractor. Replicates may choose the same or a similar query. Other categories with only 1 subsection in the mock (e.g., `getting-started`) leave less room for non-overlapping additions.
- **Canonical docs cited:** `docs/simulation-assessment-context-official.md` (baseline template, invariants), `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` (scenario roster, oracle commands, condition matrix).
