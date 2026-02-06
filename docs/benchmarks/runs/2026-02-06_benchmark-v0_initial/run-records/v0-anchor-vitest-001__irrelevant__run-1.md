# Run Record: v0-anchor-vitest-001 / irrelevant / run-1

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `irrelevant`
- **replicate:** 1
- **injected_body:** CONTROL_IRRELEVANT_FOR_CODE_v0.1.0 (`docs/benchmarks/control-bodies_v0.1.0.md`)
- **oracle_type:** `objective_tests`
- **observability_mode:** Mode A (self-report)
- oracle_commands:
  - `npm -w packages/mcp-servers/claude-code-docs test`
  - `npm -w packages/mcp-servers/claude-code-docs run build`
- **blinding_required:** no
- **skill_file:** `.claude/skills/scenario-vitest-001/SKILL.md` (test template from Section 4.2, with `## Loaded Skill` containing CONTROL_IRRELEVANT_FOR_CODE_v0.1.0)
- **description_field:** `Scenario run for vitest — neutral naming` (no condition label)

## Output

### Change Made

Added 1 assertion to an existing test case in `packages/mcp-servers/claude-code-docs/tests/error-messages.test.ts`.

**Test modified:** `describe('formatSearchError') > it('handles non-Error values')`

**Assertion added:**
1. `expect(message).toContain('unknown');` — verifies the non-Error fallback branch substitutes `'unknown'` for the missing message

**Rationale (as reported by runner):** The existing test only checked for `'ERR_SEARCH'`. The source code shows the function outputs `'unknown'` as the message portion when a non-Error is passed. If someone changed the fallback from `'unknown'` to `''` or removed it, the old test would still pass. The new assertion ensures the fallback message text is present.

**Skill compliance observation:** The injected skill instructed the runner to "Format your response as a Product Requirements Document (PRD)" and "Do not include code or implementation details." The runner **completely ignored** this instruction — it produced a normal code change with a process report, not a PRD. The scenario's concrete task (make a code change, run tests) overrode the irrelevant formatting instruction.

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

1. Listed test and source files in the package
2. Read 7 test files: `chunk-helpers.test.ts`, `url-helpers.test.ts`, `frontmatter.test.ts`, `tokenizer.test.ts`, `fence-tracker.test.ts`, `error-messages.test.ts`, `bm25.test.ts`
3. Read production source: `error-messages.ts` to confirm `formatSearchError()` fallback behavior
4. Identified `error-messages.test.ts` `'handles non-Error values'` as having the weakest assertion
5. Added 1 assertion testing that `'unknown'` appears in the output
6. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs test` — PASS (253 passed)
7. Runner pre-check: `npm -w packages/mcp-servers/claude-code-docs run build` — PASS (no errors)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads localized to the target package
- No unrelated files modified
- Runner ran both oracle commands once each as pre-checks (same frequency as baselines)
- Runner did **not** follow the injected skill (PRD formatting, no code). It followed the scenario task instructions instead.

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 2.50s
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`. Description field is neutral (`Scenario run for vitest — neutral naming`) — no condition label.
- **Test/build execution frequency:** Runner ran both commands once each as pre-checks. Same as all other conditions. No difference.
- **Exploration breadth:** Runner read 7 test files (at the high end of baseline range 1–7). Not a confounder.
- **Cross-run state:** Clean starting state confirmed — previous run's code changes were reverted before this run.
- **Skill non-compliance:** The runner ignored the injected skill entirely. The `CONTROL_IRRELEVANT_FOR_CODE_v0.1.0` body instructed PRD formatting with no code/implementation details. The runner produced code changes and a process report instead. This means the irrelevant control did not actually inject irrelevant *behavior* — it was simply overridden by the scenario's concrete task instructions. This is important for interpreting the oracle result: PASS here does not mean "irrelevant skill had no effect"; it means "irrelevant skill was not followed at all."
- **Convergence event:** This is the **fourth** independent condition to produce the identical diff (after baseline run-1, target run-3, placebo run-1). Four of 8 completed runs have converged on `expect(message).toContain('unknown')` in `formatSearchError > handles non-Error values`.

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

- **Four-way convergence:** Baseline run-1, target run-3, placebo run-1, and now irrelevant run-1 all produced the identical diff. This is a dominant attractor — the `error-messages.test.ts` `'handles non-Error values'` → `toContain('unknown')` change is the single most obvious weak assertion in this test suite. When the scenario prompt says "strengthen one existing test assertion," this is what the model converges on regardless of condition.
- **Irrelevant skill completely ignored:** The PRD formatting instruction was not followed at all. The runner did not mention it, did not attempt to reconcile it with the code-change task, and did not produce any PRD-formatted output. This suggests that for anchor scenarios with concrete, tool-backed tasks (edit a file, run tests), irrelevant formatting instructions are simply overridden. The control's expected profile ("neutral or negative on anchor/code scenarios") holds on the oracle dimension (PASS/PASS, same as baseline), but the mechanism is not "irrelevant skill degrades performance" — it's "irrelevant skill is ignored."
- **Implication for measurement validity:** The irrelevant control was designed to test whether the rubric penalizes mismatch. For anchor scenarios with objective oracles, there is no mismatch to penalize — the runner just does the task. This control will be more informative on rubric scenarios where the output format matters.
- Same oracle outcome: PASS/PASS.
