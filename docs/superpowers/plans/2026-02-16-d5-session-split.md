# D5 Agent Rewrite — Session Split

**Parent plan:** `docs/plans/2026-02-15-context-injection-agent-integration-d5-agent-rewrite.md`
**Companion:** `docs/plans/2026-02-16-d5-test-plan.md` (Sessions 28-30)

## Summary

D5 (Task 15) rewrites `.claude/agents/codex-dialogue.md` Phase 2 from a 3-step manual loop to a 7-step server-assisted scouting loop. This document splits execution across 5 sessions with clear boundaries.

The D5 plan provides near-verbatim replacement text for Steps 1-6. The creative/uncertain work is concentrated in testing (Step 7) and fixing issues found.

## Decisions

Three design decisions made during the planning discussion (2026-02-16, session 26 planning).

### DD-D5-1: Retry counter scope — per-category

Checkpoint errors and ledger errors get independent retry budgets. Each category allows maximum 1 retry per turn. Maximum 2 retries total per turn (1 checkpoint + 1 ledger).

**Rationale:** The server pipeline evaluates the dual-claims guard (Step 1b) before checkpoint intake (Step 3). A checkpoint retry (same request, null checkpoint) cannot trigger `ledger_hard_reject`. A ledger retry (corrected extraction, same checkpoint) could theoretically trigger a checkpoint error only if server state changed between calls — near-impossible under the single-agent, single-flight model. Per-category is easier to reason about than a shared pool.

**Instruction impact:** The D5 agent instructions should specify retry budgets per category, not as a single global cap. Add after the existing "Checkpoint retry cap" line in Step 3:

```
Retry budgets are per-category: checkpoint errors and ledger errors track independent retry counts. Maximum 2 retries total per turn (1 checkpoint + 1 ledger).
```

### DD-D5-2: Budget-precedence override applies before error recovery

If `turn_count >= effective_budget` when `process_turn` returns an error, skip error recovery entirely. Proceed to Phase 3 synthesis using `turn_history`.

**Rationale:** The conversation is over regardless — retrying to get a successful response that will be immediately concluded is wasted effort. Simple gate check before any branching reduces ambiguity.

**Instruction impact:** Add a budget gate at the top of Step 3, before the error table:

```
**Budget gate (checked first):** If `turn_count >= effective_budget`, skip all error recovery below. Proceed to Phase 3 (Synthesis) using `turn_history`. The conversation is complete — retrying a failed turn that would be immediately concluded is wasted effort.
```

### DD-D5-3: Evidence artifact — annotated checklist

Testing sessions (28-30) produce an annotated checklist: each verification item gets pass/fail + 1-line observation, written during the session as items are verified.

**Format:** Markdown checklist in the handoff document's "Test Results" section. Items map 1:1 to the test plan's verification items.

## Codex Consultation Findings

From the Codex dialogue on error recovery testing strategy (session 26, thread `019c6985`):

### Testing strategy: Hybrid "Option 1.5"

- **Triggerable paths:** Live-test with targeted runs (see test plan)
- **Hard-to-trigger paths:** Structured instruction review using 12-point checklist (see Session 27)
- **Fault-injection harness:** Deferred as P1 follow-up, not D5 blocker

### Precedence collision risks (verify in Session 27 review)

1. `checkpoint_invalid` accidentally captured by generic `checkpoint_*` pattern (violates no-retry contract)
2. Budget-precedence override bypassed if evaluated after error-table branching (addressed by DD-D5-2)
3. Terminal branches still issuing scout/tool calls if action execution not gated
4. `ledger_hard_reject` and `checkpoint_stale` retry counters colliding if tracked globally (addressed by DD-D5-1)

### 12-point instruction review checklist (for Session 27 reviewers)

1. Trigger match is explicit and unambiguous (no wildcard swallowing)
2. Precedence against global guards is explicit
3. Branch outcome is deterministic (exactly one of: retry, synthesize, fallback)
4. Retry policy is bounded with clear second-failure behavior
5. No hidden loops through generic "continue" logic
6. Tool-call side effects bounded after terminal action
7. Rule text is local enough to follow under context pressure
8. Budget gate checked before error-table branching
9. Per-category retry counters clearly scoped
10. Checkpoint pass-through fields handled on both success and error paths
11. Mode gating (server_assisted vs. manual_legacy) has a single decision point
12. Fallback mode instructions are self-contained (not cross-referencing server-assisted steps)

## Session Index

| Session | Focus | D5 Plan Steps | Reads | Output |
|---------|-------|---------------|-------|--------|
| 26 | Write | 1-6 | D5 plan, current agent file, this addendum | Commit |
| 27 | Review + Fix | — | Modified agent file, D5 plan, this addendum (checklist + collision risks) | Commit (if fixes needed) |
| 28 | Happy-path test | 7 (categories 1-3, 6) | Modified agent file, test plan | Annotated checklist + fixes |
| 29 | Error recovery test | 7 (P0 + P1 live tests) | Modified agent file, test plan | Annotated checklist + fixes |
| 30 | Fallback + close | 7 (fallback tests) + final verification | Modified agent file, test plan | Final commit, D5 complete |

## Session 26: Write

**Goal:** Apply all D5 plan Steps 1-6 to `.claude/agents/codex-dialogue.md`.

**What to read:**
- D5 plan (all of it — this is the primary source)
- This addendum (Decisions section — DD-D5-1, DD-D5-2 affect the text written in Steps 3-4)
- Current agent file (to verify structure before editing)

**Work:**
1. Read and verify current agent file structure matches D5 plan Step 1 expectations
2. Apply Steps 2-6 from the D5 plan. The plan provides near-verbatim replacement text for Steps 2-4. Steps 5-6 provide targeted additions.
3. Apply DD-D5-1 (per-category retry language) and DD-D5-2 (budget gate before error table) as specified in the Decisions section above
4. Commit

**Scope boundary:** Writing only. No testing, no review. Produce a committed artifact for Session 27 to review.

**Context budget:** Moderate. Reads: current agent file (~324 lines) + D5 plan (~496 lines) + this addendum. Writes: one file.

## Session 27: Review + Fix

**Goal:** Two-stage review of the modified agent file, adapted for instruction design. Fix findings.

**What to read:**
- Modified agent file (the review target)
- D5 plan (spec reference for the spec compliance reviewer)
- This addendum (12-point checklist + precedence collision risks for the instruction quality reviewer)

**Work:**
1. Dispatch spec compliance reviewer: does the modified agent file implement all D5 plan Steps 2-6? Are DD-D5-1 and DD-D5-2 incorporated? Any omissions or deviations?
2. Dispatch instruction quality reviewer: use the 12-point instruction review checklist above. Specifically verify the 4 precedence collision risks. Check that error branches are deterministic, retry budgets are bounded, and fallback mode is self-contained.
3. Fix any findings
4. Commit fixes (if any)

**Adaptation from D1-D4b reviews:** The spec compliance review is the same methodology. The instruction quality review replaces "code quality" with "instruction clarity" — checking for ambiguity, loopholes, and precedence conflicts rather than code style, naming, and test coverage.

**Context budget:** Moderate. Subagent dispatches return summaries, not raw analysis.

## Session 28: Happy-Path Live Test

**Goal:** Run the agent and verify the basic conversation flow works.

**What to read:**
- Modified agent file (to know what's being tested)
- Test plan (`docs/plans/2026-02-16-d5-test-plan.md`), Section: Happy-Path Tests

**Work:**
- See test plan for detailed procedures and verification items
- Run 1-2 codex-dialogue invocations with evaluative posture, budget 3
- Verify categories 1-3 + 6 (per-turn loop, scout integration, synthesis, turn_history)
- Record annotated checklist
- Fix issues found; re-run key items if needed

**Context budget:** Variable. Each codex-dialogue invocation returns substantial output (full synthesis). Budget for 1-2 test runs with fixes.

## Session 29: Error Recovery Test

**Goal:** Live-test triggerable error paths (P0 + P1 from test plan).

**What to read:**
- Modified agent file
- Test plan, Section: Error Recovery Tests

**Work:**
- See test plan for the P0/P1 test matrix and trigger procedures
- Run targeted test scenarios for each triggerable error path
- Record annotated checklist
- Fix issues found

**Context budget:** Depends on how many test runs each scenario requires. Some (budget=1 override) are single-run. Others (server restart between turns) may need setup.

## Session 30: Fallback Mode + Close

**Goal:** Test manual_legacy mode, final verification, complete D5.

**What to read:**
- Modified agent file
- Test plan, Section: Fallback Tests

**Work:**
1. Test manual_legacy mode: run codex-dialogue without context injection MCP tools
2. Verify fallback behavior per test plan
3. Final regression: re-run one happy-path conversation to confirm no regressions from Session 28-29 fixes
4. Final review if substantial fixes were made
5. Commit any remaining changes
6. D5 complete — update manifest status

**Context budget:** Light. Fallback is a single conversation run. Final verification is a known-clean re-run.

## Post-D5

After Session 30:
- Branch `feature/context-injection-agent-integration` is complete (D1-D5 all done)
- Push to remote + merge/PR decision
- Cross-model learning system unblocked
