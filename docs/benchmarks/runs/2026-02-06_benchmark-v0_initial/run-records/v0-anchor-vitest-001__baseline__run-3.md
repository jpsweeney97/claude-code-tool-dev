# Run Record: v0-anchor-vitest-001 / baseline / run-3

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `baseline`
- **replicate:** 3
- **injected_body:** none
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
  - `npm -w packages/mcp-servers/claude-code-docs run build`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-vitest-001/SKILL.md` (baseline template from Section 4.1)

## Output

### Change Made

Added one assertion to an existing test case in `packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts`.

**Test modified:** `describe('parseFrontmatter') > it('warns on malformed YAML')`

**Assertion added:** `expect(warnings[0].issue).toContain('Invalid YAML frontmatter');`

**Rationale (as reported by runner):** The existing test verified that a warning existed (`warnings.length > 0`) and that the warning's `file` field was correct (`warnings[0].file === 'test.md'`), but did not verify the warning's `issue` field. The production code (`frontmatter.ts` line 173) produces `Invalid YAML frontmatter: ${err instanceof Error ? err.message : 'unknown error'}`. Without the new assertion, the test would pass even if the warning message were completely wrong.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
index 1e515fa..2c11873 100644
--- a/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
@@ -71,6 +71,7 @@ describe('parseFrontmatter', () => {
     const warnings = getParseWarnings();
     expect(warnings.length).toBeGreaterThan(0);
     expect(warnings[0].file).toBe('test.md');
+    expect(warnings[0].issue).toContain('Invalid YAML frontmatter');
   });

   it('normalizes CRLF line endings', () => {
```

**Files changed:** 1 (`tests/frontmatter.test.ts`)
**Lines added:** 1
**Production code changes:** 0

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read test files and production source in `packages/mcp-servers/claude-code-docs/`
2. Read `src/frontmatter.ts` to understand warning generation behavior
3. Identified `frontmatter.test.ts` `'warns on malformed YAML'` as candidate for strengthening
4. Added 1 assertion to verify the warning's `issue` field content
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs run build` — PASS

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package
- No unrelated files modified

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 2.53s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`, but the YAML frontmatter `description` field contained `(baseline)`: `"Scenario run (baseline) for vitest — neutral naming"`. The runner may or may not attend to the description field. Noted as minor potential bias; fixed in subsequent runs by dropping the condition label from the description.
- **Scenario ambiguity:** Low. Same task as runs 1–2.
- **Cross-run state:** Clean starting state confirmed — run-2 code changes were reverted before this run.

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

- Third distinct file chosen across baselines: `frontmatter.test.ts` (vs `error-messages.test.ts` in run-1, `bm25.test.ts` in run-2).
- All 3 baseline runs: PASS/PASS, 1 file changed, 0 production code changes, 1–3 lines added.
- Consistent pattern: runner reads production source to understand behavior before adding assertion — good engineering practice emerging without injected skill.
- Baseline N=3 complete for this scenario. All 3 runs passed both oracles with no confounders.
