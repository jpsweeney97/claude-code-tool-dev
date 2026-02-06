# Run Record: v0-anchor-frontmatter-002 / baseline / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-frontmatter-002`
- **condition:** `baseline`
- **replicate:** 2
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
- **TARGET mapping:** `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` (not used for baseline)
- **Control mapping:** none (baseline condition)
- **Scenario definition:** `docs/benchmarks/scenarios/SCENARIO-v0-anchor-frontmatter-002.md`

## Clean-Start Verification

```bash
git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Result:** Empty (clean state confirmed).

## Output

### Change Made

Added 1 new test case to `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test added:** `it('warns on non-string related_to items and omits field when all items invalid')`

**What it tests:** The `parseStringArrayField` helper function's behavior when applied to `related_to` with all non-string items (e.g., `[456, 789]`). The source code (`frontmatter.ts` lines 60–72) validates each array item and produces warnings for non-string items. When all items fail validation, the function returns `undefined`. This code path was previously tested only via the `requires` field, not `related_to`.

**Assertions:**
1. `expect(warnings).toContainEqual({ file: 'test.md', issue: 'Invalid related_to item type: expected string, got number' })` — verifies warning for non-string items
2. `expect(frontmatter.related_to).toBeUndefined()` — verifies the field is omitted when all items are invalid

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..a91668b 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -223,6 +223,17 @@ describe('parseFrontmatter - requires and related_to', () => {
     });
   });

+  it('warns on non-string related_to items and omits field when all items invalid', () => {
+    const content = '---\nrelated_to: [456, 789]\n---\nBody';
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');
+    expect(warnings).toContainEqual({
+      file: 'test.md',
+      issue: 'Invalid related_to item type: expected string, got number',
+    });
+    // When all items are non-string, parseStringArrayField returns undefined
+    expect(frontmatter.related_to).toBeUndefined();
+  });
+
   it('parses id field', () => {
     const content = '---\nid: hooks-exit-codes\n---\nBody';
     const { frontmatter } = parseFrontmatter(content, 'test.md');
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines added:** 11 (1 test case with 2 assertions + 1 comment)
**Production code changes:** 0
**Test count change:** 253 → 254 (1 new test case; frontmatter.test.ts: 33 → 34)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read existing test file: `frontmatter.test.ts` to understand current coverage
2. Globbed source tree to find related source files
3. Read production source: `frontmatter.ts` to understand all code paths
4. Identified coverage gap: `parseStringArrayField` applied to `related_to` with all-invalid items was untested (only tested via `requires`)
5. Added 1 new test case at line 226, within the `parseFrontmatter - requires and related_to` describe block
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 passed)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (source + test files)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.51s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `frontmatter.test.ts` now shows 34 tests (was 33), confirming the new test was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-frontmatter-002`. Description field is neutral (`Scenario run for frontmatter — neutral naming`) — no condition label.
- **Cross-run state:** This is replicate 2. Replicate 1 was fully cleaned up (diff verified empty after run-1). No residual state.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-frontmatter-002

# 2. Revert code changes to restore clean starting state
git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-frontmatter-002` no longer exists.

## Notes

- **Different coverage gap than run-1.** Run-1 targeted the `else if (yaml.tags !== undefined)` branch (invalid tags type). Run-2 targeted `parseStringArrayField` applied to `related_to` with all-invalid array items. This divergence is a positive signal — the scenario surface area is rich enough to produce varied outputs across replicates, unlike vitest-001 where 4 of 9 runs converged on the same change.
- **Structural similarity to run-1.** Both runs: read source first, identified an untested code path, wrote a test with 2 meaningful assertions, placed the test logically near related existing tests. The process pattern is consistent even though the specific gap found differs.
- **Test placement:** Inserted within the `parseFrontmatter - requires and related_to` describe block (line 226), logically grouped with existing `requires`/`related_to` validation tests.
- **Comment in test code.** The runner added a comment (`// When all items are non-string, parseStringArrayField returns undefined`). Run-1 did not include comments. Minor behavioral difference, not a confounder.
- **No build oracle for this scenario.** Consistent with scenario definition and suite matrix.
