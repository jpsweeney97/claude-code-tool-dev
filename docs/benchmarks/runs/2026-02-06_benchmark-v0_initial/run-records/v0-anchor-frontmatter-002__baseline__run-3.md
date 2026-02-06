# Run Record: v0-anchor-frontmatter-002 / baseline / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-frontmatter-002`
- **condition:** `baseline`
- **replicate:** run-3
- **injected_body:** none
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-frontmatter-002/SKILL.md` (baseline template from Section 4.1)
- **description_field:** `Scenario run for frontmatter — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)

## Canonical Mapping Citations

- **Suite matrix:** `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` — row `v0-anchor-frontmatter-002`, column `baseline`, N=3
- **TARGET mapping:** `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` (not used for baseline) — from `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` Deterministic TARGET mapping table
- **Control mapping:** none (baseline condition) — from `docs/benchmarks/suites/benchmark-v0_v0.1.0.md` Scenario-by-scenario matrix
- **Scenario definition:** `docs/benchmarks/scenarios/SCENARIO-v0-anchor-frontmatter-002.md`
- **Invariants:** `docs/simulation-assessment-context-official.md` Section 2

## Clean-Start Verification

```bash
$ git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Output:** (empty — no output)

**Result:** Clean state confirmed.

## Output

### Change Made

Added 1 new test case to `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test added:** `it('returns undefined related_to when all items are non-string')`

**What it tests:** The `parseStringArrayField` helper function's behavior when applied to `related_to` with all non-string items (e.g., `[123, 456]`). The source code (`frontmatter.ts` line 72) returns `undefined` when `result.length > 0` is false after filtering out all invalid items. This code path was previously tested only via the `requires` field, not `related_to`.

**Assertions:**
1. `expect(frontmatter.related_to).toBeUndefined()` — verifies the field is `undefined` (not an empty array) when all items are invalid
2. `expect(warnings).toHaveLength(2)` — verifies each invalid item generates its own warning
3. `expect(warnings).toContainEqual({ file: 'test.md', issue: 'Invalid related_to item type: expected string, got number' })` — verifies the exact warning message format

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..15b2060 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -238,6 +238,19 @@ describe('parseFrontmatter - requires and related_to', () => {
       issue: 'Invalid id type: expected string, got number',
     });
   });
+
+  it('returns undefined related_to when all items are non-string', () => {
+    const content = '---\nrelated_to: [123, 456]\n---\nBody';
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');
+    // When every item is invalid, the field should be undefined (not an empty array)
+    expect(frontmatter.related_to).toBeUndefined();
+    // Each invalid item should produce a warning
+    expect(warnings).toHaveLength(2);
+    expect(warnings).toContainEqual({
+      file: 'test.md',
+      issue: 'Invalid related_to item type: expected string, got number',
+    });
+  });
 });

 describe('parseFrontmatter warnings', () => {
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines added:** 13 (1 test case with 3 assertions + 2 comments)
**Production code changes:** 0
**Test count change:** 253 → 254 (1 new test case; frontmatter.test.ts: 33 → 34)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read existing test file: `frontmatter.test.ts` to understand current coverage
2. Globbed source tree to find related source files
3. Read production source: `frontmatter.ts` to understand all code paths
4. Identified coverage gap: `parseStringArrayField` applied to `related_to` with all-invalid items — specifically the `result.length > 0 ? result : undefined` branch at line 72
5. Added 1 new test case at line 242, at the end of the `parseFrontmatter - requires and related_to` describe block
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 passed)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (source + test files)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

```
$ npm -w packages/mcp-servers/claude-code-docs test

 RUN  v2.1.9 /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs

 ✓ tests/server.test.ts (23 tests) 21ms
 ✓ tests/bm25.test.ts (23 tests) 7ms
 ✓ tests/frontmatter.test.ts (34 tests) 48ms
 ✓ tests/golden-queries.test.ts (15 tests) 47ms
 ✓ tests/chunker.test.ts (32 tests) 41ms
 ✓ tests/url-helpers.test.ts (20 tests) 8ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 6ms
 ✓ tests/fence-tracker.test.ts (10 tests) 4ms
 ✓ tests/index-cache.test.ts (6 tests) 6ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 460ms
 ✓ tests/categories.test.ts (5 tests) 3ms
 ✓ tests/parser.test.ts (7 tests) 6ms
 ✓ tests/fetcher.test.ts (4 tests) 8ms
 ✓ tests/cache.mock.test.ts (1 test) 4ms
 ✓ tests/tokenizer.test.ts (11 tests) 5ms
 ✓ tests/error-messages.test.ts (3 tests) 3ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2110ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Start at  13:03:35
   Duration  2.49s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.49s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `frontmatter.test.ts` now shows 34 tests (was 33), confirming the new test was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-frontmatter-002`. Description field is neutral (`Scenario run for frontmatter — neutral naming`) — no condition label.
- **Cross-run state:** This is replicate run-3. Replicates run-1 and run-2 were fully cleaned up (diff verified empty after each). No residual state.

## Cleanup (post-run)

```bash
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-frontmatter-002
$ git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
$ git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Post-cleanup diff output:** (empty — no output)

**Verification:** Clean state confirmed. `.claude/skills/scenario-frontmatter-002` no longer exists.

## Notes

- **Near-convergence with run-2.** Run-3 targeted the same code path as run-2: `parseStringArrayField` applied to `related_to` with all-invalid items. The test name differs (`returns undefined related_to when all items are non-string` vs run-2's `warns on non-string related_to items and omits field when all items invalid`) and run-3 added a third assertion (`toHaveLength(2)`) that run-2 did not. Despite the same gap being found, the test is not identical — different placement (line 242 at end of describe block vs run-2's line 226 mid-block), different assertion count (3 vs 2), and includes inline comments.
- **Divergence from run-1.** Run-1 targeted a completely different code path (`else if (yaml.tags !== undefined)` — invalid tags type). Run-3 and run-2 both found `related_to` with all-invalid items. This suggests `related_to` all-invalid is the next most salient gap after the `tags` type branch, creating a secondary attractor — weaker than vitest-001's dominant attractor but still present.
- **3 assertions vs 2.** Run-3 includes `toHaveLength(2)` to verify warning count, which run-2 did not. This is a qualitative difference: run-3 tests the per-item warning generation behavior more precisely.
- **Test placement:** Inserted at line 242, at the end of the `parseFrontmatter - requires and related_to` describe block (after the `id` test), unlike run-2 which placed it mid-block after the `requires` invalid-type test.
- **No build oracle for this scenario.** Consistent with scenario definition and suite matrix.
