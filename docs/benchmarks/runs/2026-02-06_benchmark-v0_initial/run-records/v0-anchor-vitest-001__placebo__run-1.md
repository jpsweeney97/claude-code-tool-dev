# Run Record: v0-anchor-vitest-001 / placebo / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `placebo`
- **replicate:** 1
- **injected_body:** CONTROL_PLACEBO_v0.1.0 (`docs/benchmarks/control-bodies_v0.1.0.md`)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
  - `npm -w packages/mcp-servers/claude-code-docs run build`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-vitest-001/SKILL.md` (test template from Section 4.2, with `## Loaded Skill` containing CONTROL_PLACEBO_v0.1.0)
- **description_field:** `Scenario run for vitest — neutral naming` (no condition label)

## Output

### Change Made

Added 1 assertion to an existing test case in `packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts`.

**Test modified:** `describe('formatSearchError') > it('handles non-Error values')`

**Assertion added:**
1. `expect(message).toContain('unknown');` — verifies the non-Error fallback branch substitutes `'unknown'` for the missing message

**Rationale (as reported by runner):** The existing test only checked the error code (`ERR_SEARCH`) was present. The source code (`src/error-messages.ts`) falls back to `'unknown'` when a non-Error value is passed. The test was not asserting this behavior. Adding the assertion tests the core branching logic (the `instanceof Error` fallback path) and prevents silent regression if the fallback string is changed.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts b/packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts
index 845248f..5a570f7 100644
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
**Lines added:** 1 (1 assertion)
**Production code changes:** 0

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Read 6 test files: `chunk-helpers.test.ts`, `url-helpers.test.ts`, `frontmatter.test.ts`, `fence-tracker.test.ts`, `tokenizer.test.ts`, `error-messages.test.ts`
2. Read production source: `error-messages.ts` to confirm `formatSearchError()` fallback behavior (`err instanceof Error ? err.message : 'unknown'`)
3. Identified `error-messages.test.ts` `'handles non-Error values'` as having the weakest assertion — only checked `ERR_SEARCH` presence, not the fallback message
4. Added 1 assertion testing that `'unknown'` appears in the output (verifying the non-Error branch)
5. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (253 passed)
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs run build` — PASS (no errors)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package
- No unrelated files modified
- Runner ran both oracle commands once each as pre-checks (same frequency as baselines)

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 2.58s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`. Description field is neutral (`Scenario run for vitest — neutral naming`) — no condition label.
- **Test/build execution frequency:** Runner ran both commands once each as pre-checks. Same as baselines and targets. No difference.
- **Exploration breadth:** Runner read 6 test files (within the baseline range of 1–7). Not a confounder.
- **Cross-run state:** Clean starting state confirmed — previous run's code changes were reverted before this run.
- **Convergence event:** This run produced the **identical diff** to baseline run-1 and target run-3 (same file, same test, same assertion). Three independent conditions converged on the same change. This eliminates any discriminative signal between these three runs and suggests `error-messages.test.ts` `'handles non-Error values'` is a strong attractor — the most obvious weak assertion in the test suite.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-vitest-001

# 2. Revert code changes to restore clean starting state
git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-vitest-001` no longer exists.

## Notes

- **Three-way convergence:** Placebo run-1, baseline run-1, and target run-3 all produced the identical change — same file, same test, same assertion, same diff. This is the third independent condition to land on `expect(message).toContain('unknown')` in `formatSearchError > handles non-Error values`. The convergence strongly suggests this is the single most obvious weak assertion in the test suite, functioning as a "fixed point" that all conditions gravitate toward regardless of injected instructions.
- **Placebo behavior indistinguishable from baseline:** The placebo body (`"Be careful and clear. Try to be helpful..."`) produced no observable difference from the baseline condition. The runner's exploration pattern (read 6 test files + source), rationale (fallback path testing), and output (1-line diff) are all within baseline norms. This is the expected profile for CONTROL_PLACEBO — neutral delta vs baseline.
- **Implication for scenario design:** The convergence pattern across 3 conditions (out of 8 total runs so far) suggests `v0-anchor-vitest-001` has limited assertion-strengthening surface area once the obvious candidates are exhausted. The remaining runs (irrelevant, harmful_no_tools) may also converge here, which would mean the scenario is effectively a single-attractor task for the "strengthen one assertion" prompt variant.
- Same oracle outcome: PASS/PASS.
