# Run Record: v0-anchor-frontmatter-002 / baseline / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-frontmatter-002`
- **condition:** `baseline`
- **replicate:** 1
- **injected_body:** none
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-frontmatter-002/SKILL.md` (baseline template from Section 4.1)
- **description_field:** `Scenario run for frontmatter — neutral naming` (no condition label)
- **task_completion_verdict:** PASS (non-empty diff)

## Output

### Change Made

Added 1 new test case to `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test added:** `it('warns when tags is an invalid type (not string or array)')`

**What it tests:** The `parseFrontmatter` function's handling of `tags` when the value is neither a string nor an array (e.g., a number). The source code (`frontmatter.ts` lines 110–115) has an `else if (yaml.tags !== undefined)` branch that produces a warning and leaves `tags` as `undefined`. This branch was previously untested.

**Assertions:**
1. `expect(frontmatter.tags).toBeUndefined();` — verifies the invalid tags value is discarded
2. `expect(warnings).toContainEqual({ file: 'test.md', issue: 'Invalid tags type: expected string or array, got number' });` — verifies the exact warning message

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..981898c 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -43,6 +43,16 @@ describe('parseFrontmatter', () => {
     });
   });

+  it('warns when tags is an invalid type (not string or array)', () => {
+    const content = '---\ntags: 123\n---\nBody';
+    const { frontmatter, warnings } = parseFrontmatter(content, 'test.md');
+    expect(frontmatter.tags).toBeUndefined();
+    expect(warnings).toContainEqual({
+      file: 'test.md',
+      issue: 'Invalid tags type: expected string or array, got number',
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
**Test count change:** 253 → 254 (1 new test case)

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read production source: `frontmatter.ts` to understand parsing logic and all code paths
2. Read existing test file: `frontmatter.test.ts` to understand current coverage
3. Identified coverage gap: the `else if (yaml.tags !== undefined)` branch (invalid tags type) had no test
4. Added 1 new test case at line 46, after the existing non-string tag values test
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (254 passed)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package (1 source file, 1 test file)
- No unrelated files modified
- Runner ran the oracle command once as pre-check

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 254 tests passed, 3 skipped, 2 todo (259 total)
- **Duration:** 2.48s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests
- **Notable:** `frontmatter.test.ts` now shows 34 tests (was 33), confirming the new test was added and passed

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-frontmatter-002`. Description field is neutral (`Scenario run for frontmatter — neutral naming`) — no condition label.
- **Scenario specificity:** This scenario targets a specific file (`frontmatter.test.ts`), unlike `v0-anchor-vitest-001` which was open-ended ("any test file"). The narrower scope should reduce convergence-attractor effects and increase variety across replicates.
- **Cross-run state:** This is the first run for this scenario. No prior state to contaminate.

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

- **Higher quality than typical vitest-001 baselines.** This baseline run read the production source first, identified an untested code branch (invalid tags type), and wrote a test with 2 meaningful assertions (state + warning message). The vitest-001 baselines typically added 1 assertion to an existing test. The difference may be because this scenario is more specific ("add a new test case" vs "strengthen one assertion") and targets a richer source file.
- **Test count increased:** 253 → 254. This is a new test case, not just a new assertion in an existing case. The scenario prompt explicitly asked for "a small new test case," and the runner complied.
- **Placement choice:** The runner inserted the new test at line 46, immediately after the existing `'warns on non-string tag values'` test. This is logically grouped — both test tag validation edge cases.
- **No build oracle for this scenario.** The scenario definition only specifies `npm test` as oracle, not `npm run build`. This matches the suite matrix.
