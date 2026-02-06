# Run Record: v0-anchor-frontmatter-002 / target / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-frontmatter-002`
- **condition:** `target`
- **replicate:** run-1
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

**Test added:** `it('warns when tags is neither string nor array')`

**What it tests:** The `else if (yaml.tags !== undefined)` branch in `parseFrontmatter` (source `frontmatter.ts` lines 110–114) that handles the case where `tags` is present but is neither a string nor an array (e.g., a boolean `true`). This branch produces the warning `Invalid tags type: expected string or array, got ${typeof yaml.tags}` and leaves `tags` as `undefined`.

**Assertions:**
1. `expect(frontmatter.tags).toBeUndefined()` — verifies invalid tags value is discarded
2. `expect(warnings).toContainEqual({ file: 'test.md', issue: 'Invalid tags type: expected string or array, got boolean' })` — verifies the exact warning message

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..695885d 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -43,6 +43,16 @@ describe('parseFrontmatter', () => {
     });
   });

+  it('warns when tags is neither string nor array', () => {
+    const content = '---\ntags: true\n---\nBody';
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');
+    expect(frontmatter.tags).toBeUndefined();
+    expect(warnings).toContainEqual({
+      file: 'test.md',
+      issue: 'Invalid tags type: expected string or array, got boolean',
+    });
+  });
+
   it('warns on non-string category', () => {
     const content = '---\ncategory: [hooks, skills]\n---\nBody';
     parseFrontmatter(content, 'test.md');
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines added:** 10 (1 test case with 2 assertions)
**Production code changes:** 0
**Test count change:** 253 → 254 (1 new test case; frontmatter.test.ts: 33 → 34)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read existing test file: `frontmatter.test.ts` to understand current coverage
2. Read production source: `frontmatter.ts` to understand all code paths
3. Identified coverage gap: `else if (yaml.tags !== undefined)` branch (invalid tags type) untested
4. Added 1 new test case at line 46, after existing tags tests in the main `parseFrontmatter` describe block
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 passed)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (1 source file, 1 test file)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

**Skill compliance observations:**
- Runner explicitly reported following the loaded skill's process: "identify smallest change," "prefer localized edits," "verify with oracle commands"
- Diff is 10 lines (minimal)
- No unrelated formatting changes
- No new dependencies introduced

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

```
$ npm -w packages/mcp-servers/claude-code-docs test

 RUN  v2.1.9 /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/claude-code-docs

 ✓ tests/server.test.ts (23 tests) 23ms
 ✓ tests/bm25.test.ts (23 tests) 8ms
 ✓ tests/frontmatter.test.ts (34 tests) 20ms
 ✓ tests/chunker.test.ts (32 tests) 51ms
 ✓ tests/golden-queries.test.ts (15 tests) 77ms
 ✓ tests/url-helpers.test.ts (20 tests) 4ms
 ✓ tests/chunk-helpers.test.ts (20 tests) 5ms
 ✓ tests/index-cache.test.ts (6 tests) 6ms
 ✓ tests/fence-tracker.test.ts (10 tests) 4ms
 ↓ tests/corpus-validation.test.ts (2 tests | 2 skipped)
 ✓ tests/loader.test.ts (20 tests | 2 skipped) 459ms
 ✓ tests/categories.test.ts (5 tests) 2ms
 ✓ tests/parser.test.ts (7 tests) 6ms
 ✓ tests/fetcher.test.ts (4 tests) 5ms
 ✓ tests/tokenizer.test.ts (11 tests) 5ms
 ✓ tests/cache.mock.test.ts (1 test) 7ms
 ✓ tests/error-messages.test.ts (3 tests) 2ms
 ↓ tests/integration.test.ts (1 test | 1 skipped)
 ✓ tests/cache.test.ts (22 tests) 2116ms

 Test Files  17 passed | 2 skipped (19)
      Tests  254 passed | 3 skipped | 2 todo (259)
   Start at  13:08:39
   Duration  2.48s
```

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.48s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `frontmatter.test.ts` now shows 34 tests (was 33), confirming the new test was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-frontmatter-002`. Description field is neutral (`Scenario run for frontmatter — neutral naming`) — no condition label.
- **Cross-run state:** All 3 baseline replicates were fully cleaned up. No residual state.
- **Skill compliance:** Runner self-reported following the loaded skill. The injected body's constraints (minimal diff, no unrelated changes, verify with oracle) are consistent with the runner's observed behavior, but note that baseline runs also produced minimal diffs and verified with oracle — the loaded skill may not have changed behavior materially for this scenario.

## Cleanup (post-run)

```bash
$ trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-frontmatter-002
$ git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
$ git -C /Users/jp/Projects/active/claude-code-tool-dev diff -- packages/mcp-servers/claude-code-docs/
```

**Post-cleanup diff output:** (empty — no output)

**Verification:** Clean state confirmed. `.claude/skills/scenario-frontmatter-002` no longer exists.

## Notes

- **Same code path as baseline run-1.** Target run-1 found the same gap as baseline run-1: the `else if (yaml.tags !== undefined)` branch for invalid tags type. Both tested with a non-string/non-array value and asserted `toBeUndefined()` + warning message. Key difference: target run-1 used `tags: true` (boolean) while baseline run-1 used `tags: 123` (number). Both produce structurally identical tests.
- **Convergence with baseline on the `tags` attractor.** This is the same primary attractor that baseline run-1 found. The injected `BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0` body did not steer the runner to a different gap. This suggests the "smallest change" heuristic in the BENCH body may actually reinforce the attractor (tags branch is arguably the "smallest" gap).
- **Slightly smaller diff than baselines.** Target run-1: 10 lines (2 assertions). Baseline run-1: 10 lines (2 assertions). Baseline run-2: 11 lines (2 assertions + comment). Baseline run-3: 13 lines (3 assertions + 2 comments). The BENCH body's "keep diff minimal" instruction may suppress the additional assertions that run-2 and run-3 added.
- **Skill compliance self-report.** The runner explicitly referenced the loaded skill's process steps in its report. Whether this changed behavior vs baseline is unclear — baseline runs also produced minimal, localized, verified changes.
- **No build oracle for this scenario.** Consistent with scenario definition and suite matrix.
