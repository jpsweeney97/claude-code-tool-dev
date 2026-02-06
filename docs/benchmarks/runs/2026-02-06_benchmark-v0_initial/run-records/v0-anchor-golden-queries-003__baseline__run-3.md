# Run Record: v0-anchor-golden-queries-003 / baseline / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-golden-queries-003`
- **condition:** `baseline`
- **replicate:** run-3
- **injected_body:** none (baseline uses no injected body per `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` condition matrix)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-golden-queries-003/SKILL.md` (baseline template from Section 4.1, `docs/simulation-assessment-context-official.md`)
- **description_field:** `Scenario run for golden queries — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)
- **prompt_deviation:** Anti-convergence constraint added: "Do not target the 'skills' category — it already has sufficient query coverage. Choose a different category." See Confounders section.

## Clean Start Verification

```
$ git diff -- packages/mcp-servers/claude-code-docs/
(empty — clean start confirmed)
```

## Output

### Change Made

Added 1 new golden query assertion to `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`.

**Query added:** `{ query: 'connection errors network firewall proxy', expectedTopCategory: 'troubleshooting' }`

**What it tests:** The search engine's ability to map a connectivity-related troubleshooting query to the `troubleshooting` category. The existing troubleshooting query (`'troubleshooting debug logging'`) targets the debug logging subsection; the new query targets the distinct "Connection troubleshooting" subsection in the mock corpus containing content about connection errors, network settings, firewall rules, and proxy misconfiguration.

**Rationale (runner-reported):** The `troubleshooting` mock corpus section has two distinct subsections (connection troubleshooting and debug logging). Only debug logging was covered. The new query uses terms drawn directly from the "Connection troubleshooting" subsection for strong BM25 relevance.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
index a1d405c..ca6b4b3 100644
--- a/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
@@ -232,6 +232,7 @@ describe('golden queries (URL-based)', () => {
     { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
     { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
     { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
+    { query: 'connection errors network firewall proxy', expectedTopCategory: 'troubleshooting' },
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
3. Read `src/bm25.ts` to confirm BM25 tokenization and scoring behavior
4. Selected "Connection troubleshooting" subsection as target (non-overlapping with existing `'troubleshooting debug logging'` query)
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

 ✓ tests/server.test.ts (23 tests) 21ms
 ✓ tests/bm25.test.ts (23 tests) 10ms
 ✓ tests/chunker.test.ts (32 tests) 30ms
 ✓ tests/frontmatter.test.ts (33 tests) 42ms
 ✓ tests/golden-queries.test.ts (16 tests) 68ms
 ✓ tests/url-helpers.test.ts (20 tests) 6ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 9ms
 ✓ tests/index-cache.test.ts (6 tests) 4ms
 ✓ tests/fence-tracker.test.ts (10 tests) 8ms
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 396ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/categories.test.ts (5 tests) 3ms
 ✓ tests/parser.test.ts (7 tests) 6ms
 ✓ tests/tokenizer.test.ts (11 tests) 3ms
 ✓ tests/fetcher.test.ts (4 tests) 4ms
 ✓ tests/cache.mock.test.ts (1 test) 4ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/error-messages.test.ts (3 tests) 1ms
 ✓ tests/cache.test.ts (22 tests) 2124ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Duration  2.52s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.52s
- **Failures:** 0
- **Skipped:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `golden-queries.test.ts` now shows 16 tests (was 15), confirming the new assertion was added and passed

## Confounders

- **Prompt deviation (anti-convergence steering):** This replicate's task prompt included an additional constraint: "Do not target the 'skills' category — it already has sufficient query coverage. Choose a different category." This was added because run-1 and run-2 both converged on the same `skills` category and near-identical query strings, reducing baseline variance. The constraint biases category selection away from `skills` but does not prescribe which category to choose or what query to write. **Impact:** The runner's category choice was constrained (not free), so this replicate is not fully comparable to run-1/run-2 in terms of "what does the baseline runner independently choose?" It is still a valid baseline for task execution quality (did it add a correct, passing assertion?).
- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-golden-queries-003`. Description field is neutral — no condition label.
- **Cross-run state:** Clean start verified. No contamination from prior runs.

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

- **Anti-convergence succeeded.** Run-3 targeted `troubleshooting` (connection errors subsection) vs run-1/run-2's `skills` (creating skills subsection). This gives the baseline set meaningful variety: 2 replicates chose `skills`, 1 chose `troubleshooting`.
- **Same structural pattern.** All 3 baseline replicates followed the same analytical path: read test file → catalogue coverage → identify underrepresented category with multiple mock subsections → add 1 assertion. The strategy is identical; only the category selection differed (and only because run-3 was steered).
- **Baseline summary across all 3 replicates:** All PASS on tests and task_completion_verdict. All added exactly 1 line. All targeted a second subsection within an existing category. No production code or mock corpus changes. The baseline is consistent in execution quality.
- **Canonical docs cited:** `docs/simulation-assessment-context-official.md` (Section 4.1 baseline template), `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` (scenario roster, oracle commands, condition matrix).
