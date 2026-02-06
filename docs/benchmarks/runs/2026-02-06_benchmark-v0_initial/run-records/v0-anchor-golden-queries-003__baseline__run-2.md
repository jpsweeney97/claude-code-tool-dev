# Run Record: v0-anchor-golden-queries-003 / baseline / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-golden-queries-003`
- **condition:** `baseline`
- **replicate:** run-2
- **injected_body:** none (baseline uses no injected body per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` condition matrix)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-golden-queries-003/SKILL.md` (baseline template from Section 4.1, `docs/simulation-assessment-context-official.md`)
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

**Query added:** `{ query: 'creating SKILL.md in skills directory', expectedTopCategory: 'skills' }`

**What it tests:** The search engine's ability to map a query about creating skill files to the `skills` category. Targets the "Creating skills" subsection in the mock corpus (lines 49–51), which is distinct from the existing `'skill frontmatter'` query that targets the frontmatter metadata subsection.

**Rationale (runner-reported):** The `skills` category was underrepresented with only 1 existing query. The mock corpus has a distinct "Creating skills" subsection with content about creating SKILL.md files. The runner also read `src/bm25.js` to confirm BM25 tokenization would match the query terms.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
index a1d405c..522c451 100644
--- a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
@@ -232,6 +232,7 @@ describe('golden queries (URL-based)', () => {
     { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
     { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
     { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
+    { query: 'creating SKILL.md in skills directory', expectedTopCategory: 'skills' },
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
2. Catalogued coverage by category (hooks: 3, skills: 1, mcp: 1, agents: 1, getting-started: 1, providers: 1, ide: 1, ci-cd: 1, security: 1, troubleshooting: 1)
3. Read `src/bm25.js` to confirm BM25 tokenization behavior
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

 ✓ tests/server.test.ts (23 tests) 25ms
 ✓ tests/bm25.test.ts (23 tests) 7ms
 ✓ tests/frontmatter.test.ts (33 tests) 13ms
 ✓ tests/chunker.test.ts (32 tests) 39ms
 ✓ tests/golden-queries.test.ts (16 tests) 76ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 3ms
 ✓ tests/url-helpers.test.ts (20 tests) 6ms
 ✓ tests/fence-tracker.test.ts (10 tests) 3ms
 ✓ tests/index-cache.test.ts (6 tests) 6ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 486ms
 ✓ tests/categories.test.ts (5 tests) 4ms
 ✓ tests/parser.test.ts (7 tests) 8ms
 ✓ tests/fetcher.test.ts (4 tests) 4ms
 ✓ tests/tokenizer.test.ts (11 tests) 6ms
 ✓ tests/cache.mock.test.ts (1 test) 3ms
 ✓ tests/error-messages.test.ts (3 tests) 2ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2196ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Duration  2.54s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.54s
- **Failures:** 0
- **Skipped:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `golden-queries.test.ts` now shows 16 tests (was 15), confirming the new assertion was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-golden-queries-003`. Description field is neutral — no condition label.
- **Scenario specificity:** This scenario targets a specific file and asks for a specific type of change (add one golden query assertion). Scope is narrow.
- **Cross-run state:** Clean start verified. No contamination from run-1 (run-1 was fully cleaned up before this run).

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

## Notes

- **Strong convergence with run-1.** Run-1 added `'creating SKILL.md .claude/skills directory'` → `skills`; run-2 added `'creating SKILL.md in skills directory'` → `skills`. Both targeted the same "Creating skills" subsection and the same category. The query strings are near-identical (differ only in `.claude/` vs `in`). This confirms the convergence risk flagged in run-1: the `skills` category with its second subsection is a strong attractor.
- **Same analytical path.** Both runs read the test file, catalogued category coverage, identified `skills` as underrepresented, and selected the "Creating skills" subsection. Run-2 additionally read `src/bm25.js` (run-1 read `src/categories.ts`), but both arrived at essentially the same change.
- **No mock corpus expansion needed.** Existing mock content already supports the added query.
- **Canonical docs cited:** `docs/simulation-assessment-context-official.md` (Section 4.1 baseline template), `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` (scenario roster, oracle commands, condition matrix).
