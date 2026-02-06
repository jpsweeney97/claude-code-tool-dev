# Run Record: v0-anchor-vitest-001 / target / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `target`
- **replicate:** 1
- **injected_body:** BENCH_TECHNIQUE_RUN_TESTS_AND_MIN_DIFF_v0.1.0 (`docs/benchmarks/bench-skill-bodies_v0.1.0.md`)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
  - `npm -w packages/mcp-servers/claude-code-docs run build`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-vitest-001/SKILL.md` (test template from Section 4.2, with `## Loaded Skill` section)

## Output

### Change Made

Replaced two weak type-level assertions with three precise value-checks in an existing test case in `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test modified:** `describe('parseFrontmatter warnings') > it('returns warnings in result instead of global state')`

**Assertions replaced:**
- Removed: `expect(warnings).toBeDefined();` and `expect(Array.isArray(warnings)).toBe(true);` (type-checks only)
- Added: `expect(warnings).toHaveLength(1);` (exact count)
- Added: `expect(warnings[0]).toEqual({ file: 'test.md', issue: 'Invalid category type: expected string, got object' });` (exact content match)
- Added: `expect(frontmatter.category).toBeUndefined();` (verifies invalid category rejected)

**Rationale (as reported by runner):** The original test would pass even if the function returned an empty array or an array of wrong objects. The new assertions verify exact count, exact content, and the side effect (invalid category not included in parsed frontmatter). The runner read the production source (`frontmatter.ts`) to confirm the expected warning message text.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..9fc523e 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -243,10 +243,15 @@ describe('parseFrontmatter - requires and related_to', () => {
 describe('parseFrontmatter warnings', () => {
   it('returns warnings in result instead of global state', () => {
     const content = '---\ncategory: [invalid]\n---\nBody';
-    const { warnings } = parseFrontmatter(content, 'test.md');
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');

-    expect(warnings).toBeDefined();
-    expect(Array.isArray(warnings)).toBe(true);
+    expect(warnings).toHaveLength(1);
+    expect(warnings[0]).toEqual({
+      file: 'test.md',
+      issue: 'Invalid category type: expected string, got object',
+    });
+    // Invalid category should not appear in parsed frontmatter
+    expect(frontmatter.category).toBeUndefined();
   });

   it('isolates warnings between calls', () => {
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines removed:** 2
**Lines added:** 7
**Net change:** +5 lines
**Production code changes:** 0

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Listed package structure (`ls`, `Glob` on tests/ and src/)
2. Read 6 test files: `chunk-helpers.test.ts`, `fence-tracker.test.ts`, `url-helpers.test.ts`, `frontmatter.test.ts`, `tokenizer.test.ts`, `bm25.test.ts`
3. Read production source: `frontmatter.ts` to understand warning generation logic
4. Identified `frontmatter.test.ts` line 244 `'returns warnings in result instead of global state'` as having the weakest assertions
5. Edited the test: replaced 2 weak type-checks with 3 precise value-checks
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (253 passed)
7. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs run build` — PASS (no errors)
8. Read edited file to verify final state

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package
- No unrelated files modified
- Runner ran both oracle commands as pre-checks (same commands used by orchestrator for oracle of record)
- Runner explicitly followed injected skill's process: identified smallest change, read source to confirm, verified with oracle commands, kept diff minimal

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 2.55s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation). Runner used the same tool set as baseline runs (Read, Edit, Bash for test/build).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`. The `description` field says "test" but this is in the YAML frontmatter, which the runner may or may not attend to. Noted as minor potential bias.
- **Test/build execution frequency:** Runner ran both test and build commands once each as pre-checks. Baseline runners also ran both commands once each. No difference in oracle execution frequency between conditions.
- **Exploration breadth:** Runner read 6 test files before choosing (comparable to baseline run-2's 7 files). Not a confounder.
- **Cross-run state:** Clean starting state confirmed — baseline run-3 code changes were reverted before this run.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-vitest-001

# 2. Revert code changes to restore clean starting state
git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-vitest-001` no longer exists.

## Notes

- **Qualitative difference from baselines:** The target runner replaced existing weak assertions rather than just adding new ones. Baselines added 1–3 lines; target replaced 2 lines with 7 (net +5). The change is arguably "stronger" — it catches a broader class of regressions (wrong count, wrong content, wrong side effect) vs baselines that only added one additional check.
- **Skill adherence signal:** The runner explicitly reported following the injected skill's process ("identify smallest change," "verify with oracle commands," "keep diff minimal"). Baseline runners also ran oracle commands but did not articulate a structured process.
- **Same oracle outcome:** PASS/PASS, same as all 3 baselines. For this anchor scenario, the delta is in *change quality* rather than *pass/fail*, since the task is designed to be achievable by baseline too.
- **Observation for scoring:** The anchor oracle (pass/fail) cannot distinguish change quality — it only confirms the change didn't break anything. Quality differences would need a supplementary rubric dimension if desired.
