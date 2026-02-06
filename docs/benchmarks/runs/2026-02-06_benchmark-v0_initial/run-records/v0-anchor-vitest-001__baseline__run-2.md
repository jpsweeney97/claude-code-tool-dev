# Run Record: v0-anchor-vitest-001 / baseline / run-2

**Run ID:** 2026-02-06_benchmark-v0_initial

## Metadata

- **scenario_id:** `v0-anchor-vitest-001`
- **condition:** `baseline`
- **replicate:** 2
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

Added two assertions to an existing test case in `packages/mcp-servers/claude-code-docs/tests/bm25.test.ts`.

**Test modified:** `describe('search') > it('ranks by relevance')`

**Assertions added:**
1. `expect(results).toHaveLength(2);` — verifies both matching chunks are returned
2. `expect(results[1].chunk_id).toBe('b');` — verifies complete ordering, not just top result

**Rationale (as reported by runner):** The existing test only asserted the first result's `chunk_id` was `'a'`. It did not verify that both matching chunks were returned or that the second result was `'b'`. The new assertions catch regressions where the search might incorrectly filter out valid results or return them in a wrong arrangement.

### Diff

```diff
diff --git a/packages/mcp-servers/claude-code-docs/tests/bm25.test.ts b/packages/mcp-servers/claude-code-docs/tests/bm25.test.ts
index 0d5cb7a..4b352fc 100644
--- a/packages/mcp-servers/claude-code-docs/tests/bm25.test.ts
+++ b/packages/mcp-servers/claude-code-docs/tests/bm25.test.ts
@@ -77,8 +77,11 @@ describe('search', () => {
     const index = buildBM25Index(chunks);
     const results = search(index, 'hooks');

+    // Both chunks contain the query term, so both should appear
+    expect(results).toHaveLength(2);
     // Chunk with more occurrences should rank higher
     expect(results[0].chunk_id).toBe('a');
+    expect(results[1].chunk_id).toBe('b');
   });

   it('respects limit parameter', () => {
```

**Files changed:** 1 (`tests/bm25.test.ts`)
**Lines added:** 3 (2 assertions + 1 comment)
**Production code changes:** 0

## Tool Trace

Mode A (self-report from forked assessment-runner context):

1. Listed files in `packages/mcp-servers/claude-code-docs/` (src/ and tests/)
2. Read multiple test files: `bm25.test.ts`, `chunk-helpers.test.ts`, `fence-tracker.test.ts`, `tokenizer.test.ts`, `frontmatter.test.ts`, `url-helpers.test.ts`, `categories.test.ts`
3. Read production source: `src/bm25.ts` and `src/types.ts` to understand `SearchResult` shape and `search()` behavior
4. Identified `bm25.test.ts` `'ranks by relevance'` as candidate for strengthening
5. Added 2 assertions to the existing test case
6. Ran `npm -w packages/mcp-servers/claude-code-docs test` — PASS (runner context)
7. Ran `npm -w packages/mcp-servers/claude-code-docs run build` — PASS (runner context)

**Tool usage observations:**
- No web search or external tool usage detected
- File reads spanned multiple test files (broader exploration than run-1) but edits were localized to one file
- No unrelated files modified

## Oracle Results

**Oracle commands executed by: main session (orchestrator), independently after forked runner completed.**

### Tests (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** 17 test files passed, 2 skipped (19 total); 253 tests passed, 3 skipped, 2 todo (258 total)
- **Duration:** 8.93s (slower than run-1's 2.65s; likely due to system load variance, not a code issue)
- **Failures:** 0
- **Skipped tests:** corpus-validation (DOCS_PATH not set), integration (network), 2 loader tests

### Build (independently verified by orchestrator)

- **Result:** PASS
- **Summary:** `tsc` completed with zero errors

## Confounders

- **Tool confounders:** None detected. No web usage (matches `no_web` expectation).
- **Naming bias:** Skill file used neutral name `scenario-vitest-001`, but the YAML frontmatter `description` field contained `(baseline)`: `"Scenario run (baseline) for vitest — neutral naming"`. The runner may or may not attend to the description field. Noted as minor potential bias; fixed in subsequent runs by dropping the condition label from the description.
- **Scenario ambiguity:** Low. Same task as run-1.
- **Cross-run state:** Clean starting state confirmed — run-1 code changes were reverted before this run.
- **Exploration breadth:** Runner read 7 test files before choosing one (broader than run-1's approach). This is a behavioral variance but not a confounder — the task allows the runner to choose which test to strengthen.

## Cleanup (post-run)

Commands executed after oracle verification and run record capture:

```bash
# 1. Remove temporary skill directory
trash /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/scenario-vitest-001

# 2. Revert code changes to restore clean starting state for next replicate
git -C /Users/jp/Projects/active/claude-code-tool-dev checkout -- packages/mcp-servers/claude-code-docs/tests/bm25.test.ts
```

**Verification:** After cleanup, `git diff -- packages/mcp-servers/claude-code-docs/` returned empty (clean state confirmed) and `.claude/skills/scenario-vitest-001` no longer exists.

## Notes

- Different file chosen than run-1 (`bm25.test.ts` vs `error-messages.test.ts`) — expected variance since the task gives the runner freedom to choose.
- The change was slightly larger than run-1 (3 lines vs 1 line) but still minimal and well-targeted.
- Runner explored more broadly (7 files) before committing — may indicate natural variance in exploration strategy without skills.
- Test count remained at 253 (no new test cases, just new assertions in an existing case).
- Test duration variance (8.93s vs 2.65s in run-1) is attributed to system load, not the code change.
