# Run Record: v0-anchor-vitest-001 / baseline / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `baseline`
- **replicate:** 1
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

Added one assertion to an existing test case in `packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts`.

**Test modified:** `describe('formatSearchError') > it('handles non-Error values')`

**Assertion added:** `expect(message).toContain('unknown');`

**Rationale (as reported by runner):** The existing test only checked for `ERR_SEARCH` in the output. The source code (`src/error-messages.ts` line 2) shows a fallback path: `const message = err instanceof Error ? err.message : 'unknown';`. The new assertion verifies the fallback behavior — that when a non-Error value is passed, `'unknown'` appears in the formatted message.

### Diff

```diff
--- a/packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts
@@ -15,5 +15,6 @@ describe('formatSearchError', () => {
   it('handles non-Error values', () => {
     const message = formatSearchError('oops');
     expect(message).toContain('ERR_SEARCH');
+    expect(message).toContain('unknown');
   });
 });
```

**Files changed:** 1 (`tests/error-messages.test.ts`)
**Lines added:** 1
**Production code changes:** 0

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read test files in `packages/mcp-servers/claude-code-docs/tests/`
2. Read production source `src/error-messages.ts` to understand behavior
3. Identified `error-messages.test.ts` as a candidate for strengthening
4. Added one assertion to the `'handles non-Error values'` test
5. Ran `npm -w packages/mcp-servers/claude-code-docs test` — PASS
6. Ran `npm -w packages/mcp-servers/claude-code-docs run build` — PASS

**Tool usage observations:**
- No web search or external tool usage detected
- File reads were localized to the target package
- No unrelated files modified

## Oracle Results

### Tests (independently verified by orchestrator)
- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 2.65s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)
- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`, but the YAML frontmatter `description` field contained `(baseline)`: `"Scenario run (baseline) for vitest — neutral naming"`. The runner may or may not attend to the description field. Noted as minor potential bias; fixed in subsequent runs by dropping the condition label from the description.
- **Scenario ambiguity:** Low. Task was clear ("strengthen one existing test assertion OR add one additional assertion").
- **Cross-run state:** This is run-1. Code change must be reverted before run-2 to prevent starting-state contamination.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-vitest-001

# 2. Revert code changes to restore clean starting state for next replicate
git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-vitest-001` no longer exists.

## Notes

- The change was minimal (1 line, 1 file) and well-targeted — a reasonable baseline behavior.
- The runner read production source to understand the code path before adding the assertion, which is good engineering practice.
- Test count remained at 253 (no new test cases added, just a new assertion in an existing case).
- Code revert between replicates is not explicitly prescribed by the framework but is required by the "cross-run contamination" invariant — each replicate of a code-change scenario must start from an identical codebase state.
