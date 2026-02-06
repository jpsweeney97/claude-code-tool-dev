# Run Record: v0-anchor-frontmatter-002 / target / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-frontmatter-002`
- **condition:** `target`
- **replicate:** run-3
- **injected_body:** `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` (from `docs/benchmarks/bench-skill-bodies_v0.1.0.md`)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-frontmatter-002/SKILL.md` (test template from Section 4.2, `docs/simulation-assessment-context-official.md`)
- **description_field:** `Scenario run for frontmatter — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)

## Canonical Mapping Citations

- **Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` — row `v0-anchor-frontmatter-002`, column `target`, N=3
- **TARGET mapping:** `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` — from `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` Deterministic TARGET mapping table
- **Injected body source:** `docs/benchmarks/bench-skill-bodies_v0.1.0.md` — section `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0`
- **Control mapping:** N/A (target condition, not a control)
- **Scenario definition:** `docs/benchmarks/scenarios/SCENARIO-v0-anchor-frontmatter-002.md`
- **Invariants:** `docs/simulation-assessment-context-official.md` Section 2

## Clean-Start Verification

```bash
$ git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Output:** (empty — no output)

**Result:** Clean state confirmed.

## Injected Skill Body

Injected into `## Loaded Skill` section per Section 4.2 template:

```
BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0

When making code changes, follow this process:

1) Identify the smallest change that could satisfy the task.
2) Prefer localized edits. Do not refactor unrelated code.
3) Verify with the scenario's stated oracle commands (tests/build). If you cannot run them, state that explicitly and downgrade confidence.
4) If tests fail, iterate until they pass or you can explain the blocker.

Constraints:
- Avoid unrelated formatting-only changes.
- Avoid introducing new dependencies.
- Keep the diff minimal while still correct.
```

## Output

### Change Made

Added 1 new test case to `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test added:** `it('returns undefined requires when all array items are non-string')`

**What it tests:** The `parseStringArrayField` helper function's `result.length > 0 ? result : undefined` branch (source `frontmatter.ts` line 72) when applied to `requires` with all non-string items (`[123, 456]`). When every item fails string validation, the filtered `result` array is empty, so the function returns `undefined`. This was previously untested for the all-invalid case — existing tests always included at least one valid string item.

**Assertions:**
1. `expect(frontmatter.requires).toBeUndefined()` — verifies field is `undefined` (not empty array) when all items invalid
2. `expect(warnings.length).toBe(2)` — verifies each invalid item generates its own warning
3. `expect(warnings).toContainEqual({ file: 'test.md', issue: 'Invalid requires item type: expected string, got number' })` — verifies warning message format

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..3b38afe 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -213,6 +213,17 @@ describe('parseFrontmatter - requires and related_to', () => {
     });
   });

+  it('returns undefined requires when all array items are non-string', () => {
+    const content = '---\nrequires: [123, 456]\n---\nBody';
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');
+    expect(frontmatter.requires).toBeUndefined();
+    expect(warnings.length).toBe(2);
+    expect(warnings).toContainEqual({
+      file: 'test.md',
+      issue: 'Invalid requires item type: expected string, got number',
+    });
+  });
+
   it('warns on invalid requires type', () => {
     const content = '---\nrequires: 123\n---\nBody';
     parseFrontmatter(content, 'test.md');
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines added:** 11 (1 test case with 3 assertions)
**Production code changes:** 0
**Test count change:** 253 → 254 (1 new test case; frontmatter.test.ts: 33 → 34)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read existing test file: `frontmatter.test.ts` to understand current coverage
2. Read production source: `frontmatter.ts` to understand all code paths
3. Identified coverage gap: `parseStringArrayField` applied to `requires` with all-invalid items — specifically the `result.length > 0 ? result : undefined` branch at line 72
4. Added 1 new test case at line 216, after the existing `related_to` tests and before "warns on invalid requires type" in the `parseFrontmatter - requires and related_to` describe block
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 passed)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (1 source file, 1 test file)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

**Skill compliance observations:**
- Runner self-reported following the loaded skill's process: "identify smallest change," "prefer localized edits," "verify with oracle commands"
- Diff is 11 lines (minimal)
- No unrelated formatting changes
- No new dependencies introduced

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

```
$ npm -w packages/mcp-servers/claude-code-docs test

 RUN  v2.1.9 /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs

 ✓ tests/server.test.ts (23 tests) 24ms
 ✓ tests/bm25.test.ts (23 tests) 6ms
 ✓ tests/frontmatter.test.ts (34 tests) 19ms
 ✓ tests/chunker.test.ts (32 tests) 27ms
 ✓ tests/golden-queries.test.ts (15 tests) 62ms
 ✓ tests/url-helpers.test.ts (20 tests) 7ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 5ms
 ✓ tests/fence-tracker.test.ts (10 tests) 3ms
 ✓ tests/index-cache.test.ts (6 tests) 5ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 432ms
 ✓ tests/categories.test.ts (5 tests) 2ms
 ✓ tests/parser.test.ts (7 tests) 4ms
 ✓ tests/fetcher.test.ts (4 tests) 3ms
 ✓ tests/tokenizer.test.ts (11 tests) 2ms
 ✓ tests/cache.mock.test.ts (1 test) 3ms
 ✓ tests/error-messages.test.ts (3 tests) 1ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2153ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Start at  13:27:23
   Duration  2.53s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.53s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `frontmatter.test.ts` now shows 34 tests (was 33), confirming the new test was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-frontmatter-002`. Description field is neutral (`Scenario run for frontmatter — neutral naming`) — no condition label.
- **Cross-run state:** Target run-2 was fully cleaned up (diff verified empty after). No residual state.
- **Skill compliance:** Runner self-reported following the loaded skill. The injected body's constraints (minimal diff, no unrelated changes, verify with oracle) are consistent with the runner's observed behavior. However, baseline runs also produced minimal, localized, verified changes — the loaded skill may not have materially altered behavior for this scenario.

## Cleanup (post-run)

```bash
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-frontmatter-002
$ git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
$ git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Post-cleanup diff output:** (empty — no output)

**Verification:** Clean state confirmed. `.claude/skills/scenario-frontmatter-002` no longer exists.

## Notes

- **Near-identical to target run-2.** Target run-3 found the same code path (`parseStringArrayField` all-invalid-items via `requires`) and produced a structurally similar test with the same test name: `returns undefined requires when all array items are non-string`. Key differences: run-3 used `[123, 456]` (two numbers) while run-2 used `[123, true]` (number + boolean); run-3 has 3 assertions (11 lines) while run-2 had 4 assertions (15 lines) due to checking two distinct `typeof` values.
- **Strong `requires` all-invalid attractor for target condition.** Both target run-2 and run-3 converged on the same gap (`requires` with all-invalid items), while target run-1 found the `tags` type branch. This mirrors the baseline pattern: baseline run-1 found `tags`, baseline runs 2–3 found `related_to` all-invalid. The `parseStringArrayField` empty-result branch is the dominant secondary attractor across both conditions, but target runs test it via `requires` while baseline runs test it via `related_to`.
- **Smallest diff in the target series.** Target run-3: 11 lines (3 assertions). Target run-2: 15 lines (4 assertions). Target run-1: 10 lines (2 assertions). Run-3's smaller diff vs run-2 is because it used same-type invalid items (`[123, 456]`), requiring only one `toContainEqual` assertion.
- **Test placement.** Inserted at line 216, after existing `related_to` tests and before the "warns on invalid requires type" test — slightly different from run-2's placement at line 226.
- **Convergence summary (all 3 target runs).** Run-1: `tags` type branch (10 lines, 2 assertions). Run-2: `requires` all-invalid with mixed types (15 lines, 4 assertions). Run-3: `requires` all-invalid with same type (11 lines, 3 assertions). The BENCH body's "smallest change" instruction may be reinforcing the `parseStringArrayField` attractor, while baseline's slightly more exploratory behavior found `related_to` instead.
- **No build oracle for this scenario.** Consistent with scenario definition and suite matrix.
