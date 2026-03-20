# T-004: Codex Audit Tier 1 Critical Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 Severity A findings from the Codex integration audit so the foundation is production-ready before building the cross-model learning system.

**Architecture:** Four independent fixes across different files. A1 (hook) requires empirical testing before deciding on fix vs. close. A2 and A3 both modify the same file (codex-reviewer.md) so they share a task. A4 is documentation-only.

**Reference:** `docs/tickets/2026-02-17-codex-audit-tier1-critical-fixes.md`

**Branch:** Create `chore/codex-audit-tier1` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest` (expect 969 tests pass)

**Dependencies between tasks:**
- Task 1 (A1 — hook empirical test): independent, must run first because outcome affects T-005 planning
- Task 2 (A2 + A3 — codex-reviewer fixes): independent of Task 1
- Task 3 (A4 — documentation fixes): independent of Tasks 1-2
- Task 4 (final verification + commit): depends on Tasks 1-3

## Research Summary

### A1: Hook `additionalContext` — NOT a bug

Documentation research resolved the core concern. The Claude Code docs **explicitly document** `additionalContext` for `PostToolUseFailure`:

> `PostToolUseFailure` hooks can provide context to Claude after a tool failure. [...] `additionalContext`: Additional context for Claude to consider alongside the error.

The audit finding confused raw stdout behavior ("shown in verbose mode for most events") with structured JSON decision control fields (processed as event-specific behavior). The hook code follows the documented pattern exactly.

**Plan:** Empirical test to confirm behavior. If it works (expected): close A1 with evidence. If it doesn't work despite docs: report as Claude Code bug and redesign using UserPromptSubmit relay pattern.

### A2: Dead `develop` reference — clear fix

Line 36 of codex-reviewer.md: `git merge-base <branch> develop` always fails silently because this project has no `develop` branch. Remove the `develop` reference and simplify to `main`-only with a fallback.

### A3: No large-PR degradation — needs thresholds

Line 42 of codex-reviewer.md: "~500 lines" is vague. No handling for >1000 line known failure. Add concrete thresholds, a multi-strategy degradation path, and a hard cap with explicit failure message.

### A4: Stale docs — two text updates

1. CLAUDE.md line 84: "739 tests" → "969 tests", "pending" → "complete"
2. Contract lines 311, 818, 1046: Remove `over_budget` (implementation uses `Literal["under_budget", "at_budget"]` only)

---

## Task 1: A1 — Empirical test of hook `additionalContext` delivery

**Files:**
- Read: `.claude/hooks/nudge-codex-consultation.py`
- Read: `.claude/settings.json` (verify hook registration)

**Step 1: Verify hook registration in settings.json**

Read `.claude/settings.json` and confirm the `PostToolUseFailure` hook entry exists with `matcher: "Bash"` and the correct command path.

Expected: Entry matches:
```json
{
  "hooks": {
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/nudge-codex-consultation.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Step 2: Clear any existing counter state**

The hook stores its counter in a temp file at `/tmp/claude-nudge-{session_id}`. The session_id comes from the hook event input, so we don't know the exact filename. This is fine — start fresh by noting the expectation that the counter starts at 0 for this session (temp files are per-session, so a new session always starts clean).

**Step 3: Trigger 3 consecutive Bash failures**

Run three Bash commands that will fail:

```bash
false
```

```bash
this_command_does_not_exist_xyz
```

```bash
exit 1
```

After each failure, observe whether the hook fires (the hook should run silently for the first 2 failures, incrementing the counter).

**Step 4: Observe whether the nudge appears after the 3rd failure**

After the 3rd Bash failure, check for the nudge text in the conversation context. The `additionalContext` should appear as a system-reminder containing:

> "You've hit several consecutive failures. Consider running /codex to get a second opinion from another model. It can help spot assumptions you might be stuck on."

**Decision gate:**

- **If nudge appears:** A1 is confirmed working. Document the evidence (the system-reminder text). Close A1. The T-005 findings B12 and B13 are actionable (hook works, so improvements to it are meaningful).
- **If nudge does NOT appear:** The hook's `additionalContext` is not reaching Claude despite being documented. Two sub-options:
  - **Option A (recommended):** File as a Claude Code documentation bug. The hook is correctly implemented per docs but the feature doesn't work. Keep the hook as-is pending upstream fix.
  - **Option B:** Redesign as a two-phase hook: `PostToolUseFailure` writes state to a temp file, `UserPromptSubmit` reads the state file and injects context via `additionalContext` (which IS confirmed working for `UserPromptSubmit`). This adds complexity but guarantees delivery.

**Step 5: Document the result**

Record the empirical test result as a comment at the top of the hook file (if working) or as a note in the T-004 ticket (if not working). Example if working:

Add a line to the hook docstring:
```python
"""
Suggest /codex consultation after repeated Bash failures.

Verified 2026-02-17: PostToolUseFailure additionalContext delivery confirmed working.
...
```

---

## Task 2: A2 + A3 — Fix codex-reviewer base detection and add large-PR handling

**Files:**
- Modify: `.claude/agents/codex-reviewer.md:36` (A2 — base detection)
- Modify: `.claude/agents/codex-reviewer.md:38-43` (A3 — large diff handling)

Before editing: Read `.claude/rules/subagents.md` (blocking requirement per CLAUDE.md).

**Step 1: Fix A2 — Remove dead `develop` branch reference**

In `.claude/agents/codex-reviewer.md`, replace the base detection paragraph at line 36:

Current (line 36):
```
**Detecting the base branch:** Run `git merge-base <branch> develop` and `git merge-base <branch> main`. Use whichever base is closer (more recent commit). If neither ref exists, ask the caller to specify.
```

Replace with:
```
**Detecting the base branch:** Run `git merge-base <branch> main`. If `main` doesn't exist (e.g., the default branch uses a different name), ask the caller to specify the base branch.
```

**Why:** This project only uses `main`. The `develop` reference was cargo-culted from gitflow conventions. `git merge-base <branch> develop` always fails silently because `develop` doesn't exist, making the fallback logic dead code.

**Step 2: Fix A3 — Replace vague ~500 line threshold with concrete degradation strategy**

In `.claude/agents/codex-reviewer.md`, replace the vague guidance at line 42:

Current (line 42):
```
- If the diff exceeds ~500 lines, summarize sections instead of inlining everything
```

Replace with:
```
### Handling large diffs

| Diff size | Strategy |
|-----------|----------|
| ≤500 lines | Include full diff in briefing |
| 501–1500 lines | **Summarize by file.** List all changed files with line counts. Inline only the most critical changes (up to 500 lines total). Prioritize: new files > modified core logic > test changes > config/formatting. Note which files were summarized vs. inlined. |
| >1500 lines | **Stop and report.** Output: "This changeset has {N} lines of changes, which exceeds the 1500-line review limit. Consider splitting into smaller PRs for effective review." Do not attempt the review. |

If the diff is empty and there are no untracked files, report "No changes to review" and stop.
```

**Why:** The ~500 line vague threshold had no upper bound. The agent is known to fail on >1000 line diffs. The 1500-line hard cap provides a clear failure message instead of silent degradation. The 501–1500 range adds a summarization strategy that preserves value for medium-large PRs.

**Step 3: Verify the edit reads cleanly**

Read `.claude/agents/codex-reviewer.md` in full and confirm:
1. The base detection paragraph is clean (no `develop` reference)
2. The large diff handling table is properly formatted
3. No other sections were accidentally modified
4. The "If the diff is empty" line wasn't duplicated (it was part of the original text at line 43 — verify it appears exactly once)

**Step 4: Commit**

```bash
git add .claude/agents/codex-reviewer.md
git commit -m "fix(codex-reviewer): remove dead develop ref, add large-PR thresholds (A2, A3)

- Remove git merge-base develop (branch doesn't exist, always fails silently)
- Replace vague ~500-line threshold with 3-tier strategy:
  ≤500 full, 501-1500 summarize by file, >1500 hard cap
- Addresses T-004 findings A2 and A3

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: A4 — Fix stale documentation

**Files:**
- Modify: `.claude/CLAUDE.md:84`
- Modify: `docs/references/context-injection-contract.md:311,818,1046`

**Step 1: Update CLAUDE.md Context Injection status**

In `.claude/CLAUDE.md`, replace line 84:

Current:
```
**Status:** MCP server complete (739 tests). Agent integration pending — the codex-dialogue agent's 3-step conversation loop needs upgrading to the 7-step scouting loop described in the design spec.
```

Replace with:
```
**Status:** MCP server and agent integration complete (969 tests). The codex-dialogue agent uses the 7-step scouting loop with context injection for mid-conversation evidence gathering.
```

**Why:** Three facts were wrong: test count (739 → 969), status ("pending" → complete since PR #10), and description (upgrade "needs" to happen → already done).

**Step 2: Remove `over_budget` from contract — location 1 (line 311)**

In `docs/references/context-injection-contract.md`, replace line 311:

Current:
```
| `budget.budget_status` | `BudgetStatus` | Yes | `"under_budget"`, `"at_budget"`, or `"over_budget"`. Reports remaining capacity. |
```

Replace with:
```
| `budget.budget_status` | `BudgetStatus` | Yes | `"under_budget"` or `"at_budget"`. Reports remaining capacity. |
```

**Step 3: Remove `over_budget` from contract — location 2 (line 818)**

Current:
```
`under_budget` | `at_budget` | `over_budget`
```

Replace with:
```
`under_budget` | `at_budget`
```

**Step 4: Remove `over_budget` from contract — location 3 (line 1046)**

Current:
```
| `budget.budget_status` | Remaining capacity status (`under_budget`, `at_budget`, `over_budget`). |
```

Replace with:
```
| `budget.budget_status` | Remaining capacity status (`under_budget` or `at_budget`). |
```

**Why (all 3 locations):** `over_budget` was removed from the implementation in T-003 as dead code. The budget computation clamps at `at_budget` — the system never produces `over_budget`. Implementation: `Literal["under_budget", "at_budget"]`. Test at `test_templates.py:142` confirms: "budget_status is 'at_budget' (not 'over_budget') when evidence_count == MAX."

**Step 5: Verify edits**

Read both files and confirm:
1. CLAUDE.md status line says "complete (969 tests)"
2. Contract has no remaining `over_budget` references
3. No other content was modified

Run: `grep -n "over_budget" docs/references/context-injection-contract.md`
Expected: No output (zero matches)

**Step 6: Commit**

```bash
git add .claude/CLAUDE.md docs/references/context-injection-contract.md
git commit -m "docs: update stale context-injection status and remove over_budget (A4)

- CLAUDE.md: 739→969 tests, 'pending'→'complete' (PR #10 done)
- Contract: remove over_budget from BudgetStatus (3 locations)
  Implementation uses Literal['under_budget', 'at_budget'] only;
  over_budget was removed as dead code in T-003

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Final verification and branch completion

**Depends on:** Tasks 1, 2, 3

**Step 1: Run context-injection test suite**

```bash
cd packages/context-injection && uv run pytest
```

Expected: All 969 tests pass. No tests should change in this plan (fixes are to instruction docs and documentation, not implementation code).

**Step 2: Run linter**

```bash
cd packages/context-injection && ruff check .
```

Expected: No errors.

**Step 3: Verify all A findings are addressed**

| Finding | Status | Evidence |
|---------|--------|----------|
| A1 | Confirmed working OR redesign planned | Empirical test result from Task 1 |
| A2 | Fixed | `develop` removed from codex-reviewer.md |
| A3 | Fixed | 3-tier threshold table in codex-reviewer.md |
| A4 | Fixed | CLAUDE.md updated, `over_budget` removed from contract |

**Step 4: Update T-004 ticket status**

Edit `docs/tickets/2026-02-17-codex-audit-tier1-critical-fixes.md`:
- Change `status: open` to `status: complete`
- Add `branch: chore/codex-audit-tier1`

**Step 5: Final commit (ticket status)**

```bash
git add docs/tickets/2026-02-17-codex-audit-tier1-critical-fixes.md
git commit -m "chore: mark T-004 complete

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Step 6: Report completion**

Summarize what was done, what was found (A1 test result), and confirm T-005 is unblocked.

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest`
Expected: All 969 tests pass (no test changes in this plan)

Run: `ruff check packages/context-injection/`
Expected: No errors

Verify: `grep -n "over_budget" docs/references/context-injection-contract.md` returns no matches
Verify: `grep -n "develop" .claude/agents/codex-reviewer.md` returns no matches
Verify: `grep -n "739 tests\|pending" .claude/CLAUDE.md` returns no matches for the old text

## Summary of Deliverables

| Module | New/Modified | What This Plan Adds |
|--------|-------------|---------------------|
| `.claude/agents/codex-reviewer.md` | Modified | Remove dead `develop` ref, add 3-tier large-PR thresholds |
| `.claude/CLAUDE.md` | Modified | Update Context Injection status to current (969 tests, complete) |
| `docs/references/context-injection-contract.md` | Modified | Remove `over_budget` from BudgetStatus (3 locations) |
| `docs/tickets/2026-02-17-codex-audit-tier1-critical-fixes.md` | Modified | Mark T-004 complete |
