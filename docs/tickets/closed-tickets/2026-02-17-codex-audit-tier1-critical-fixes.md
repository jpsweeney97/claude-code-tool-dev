# T-004: Codex Audit Tier 1 — Critical Fixes

```yaml
id: T-004
date: 2026-02-17
status: complete
priority: high
branch: chore/codex-audit-tier1
blocked_by: []
blocks: [T-005, T-006]
related: [T-003]
```

## Summary

4 Severity A findings from the full Codex integration audit (4 parallel reviewers, 25+ files, 41 total findings). These are factually incorrect documentation, dead code in a production agent, and a potentially non-functional hook. Must be resolved before building cross-model learning system on this foundation.

**Scope:** CLAUDE.md, context-injection-contract.md, codex-reviewer.md, nudge-codex-consultation.py.

**Reviewers:** dialogue-auditor (codex-dialogue agent), reviewer-auditor (codex-reviewer + skill), integration-auditor (hook + MCP config), docs-auditor (documentation accuracy).

**Session plan:**
- Session 1: Create implementation plan using writing-plans skill
- Session 2: Execute the implementation plan
- Session 3: Review implementation + clean up

## Prerequisites

Before starting fixes:
1. Create working branch from `main` (at `34c8a0f`, 969 tests)
2. Run `cd packages/context-injection && uv run pytest` to confirm 969 tests pass
3. Read each file listed in the findings below

## Findings

### A1: Hook `additionalContext` may not reach Claude for `PostToolUseFailure`

**Found by:** integration-auditor

**Location:** `.claude/hooks/nudge-codex-consultation.py:55-64`

**Problem:** The hook outputs `hookSpecificOutput.additionalContext` JSON on stdout at exit 0. The Claude Code hooks reference documents `additionalContext` for `PostToolUse`, `PreToolUse`, `UserPromptSubmit`, `SessionStart`, and `Setup` — but there is no `PostToolUseFailure` JSON output control section. The hook's entire value proposition depends on `additionalContext` being visible to Claude, but the docs suggest stdout for this event type is only shown in verbose mode.

**Impact:** If `PostToolUseFailure` doesn't process `hookSpecificOutput.additionalContext`, the nudge is invisible to Claude — the hook is silently non-functional. The counter still increments and resets, but the suggestion never reaches the model.

**Fix options:**
- **Option A (test first):** Empirically test whether Claude receives the `additionalContext` for `PostToolUseFailure` hooks. If it works, document the finding.
- **Option B (redesign):** Restructure as `PostToolUseFailure` writes state + `UserPromptSubmit` reads state and injects context on the next prompt.
- **Option C (remove):** If the hook is non-functional and not worth redesigning, remove it cleanly.

**Files:** `.claude/hooks/nudge-codex-consultation.py`, `.claude/settings.json`

**Related finding (B-severity, may inform fix):** `PostToolUseFailure` may not respect `matcher: Bash` — if matchers are ignored for this event type, the hook fires for ALL tool failures, not just Bash failures. If redesigning, consider adding explicit `tool_name` filtering in the hook code.

### A2: Dead `develop` branch reference in codex-reviewer

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:36`

**Problem:** Base branch detection runs `git merge-base <branch> develop` but this project has no `develop` branch. The command always fails silently, falling through to whatever fallback exists.

**Impact:** Diff detection is unreliable. The agent may not correctly determine the base branch for review, leading to incomplete or incorrect change sets.

**Fix:** Remove `develop` from the branch detection list. Use only `main` (the project's actual default branch).

**Files:** `.claude/agents/codex-reviewer.md`

### A3: No large-PR degradation path in codex-reviewer

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:42`

**Problem:** The ~500-line summarization threshold is vague. There is no guidance for the known >1000 line failure mode. No hard upper bound, no caller warning, no graceful stop.

**Impact:** The agent fails silently on large PRs. This is a known production issue (documented in MEMORY.md as "Code review skill Agent 1 fails on large PRs (>1000 lines)").

**Fix (multi-part):**
1. Define a concrete threshold (e.g., 500 lines for summarization, 1500 lines hard cap)
2. Add a summarization strategy for large diffs (e.g., review by file, prioritize changed functions)
3. Add a hard upper bound with an explicit failure message: "This PR exceeds the review size limit. Consider splitting into smaller PRs."

**Files:** `.claude/agents/codex-reviewer.md`

### A4: Stale documentation — CLAUDE.md + contract `over_budget`

**Found by:** docs-auditor

**Location (CLAUDE.md):** `.claude/CLAUDE.md:84`

**Current text:** "MCP server complete (739 tests). Agent integration pending — the codex-dialogue agent's 3-step conversation loop needs upgrading to the 7-step scouting loop described in the design spec."

**Should be:** "MCP server and agent integration complete (969 tests). See `.claude/agents/codex-dialogue.md` for the integrated 7-step scouting loop."

**Wrong on 3 counts:**
1. Test count: says 739, actual is 969
2. Status: says "agent integration pending", but PR #10 completed it
3. Says the upgrade "needs" to happen, but it was done

**Location (contract):** `docs/references/context-injection-contract.md:311`, `:818`, `:1046`

**Problem:** BudgetStatus documented as `under_budget | at_budget | over_budget` (three variants). Implementation is `Literal["under_budget", "at_budget"]` (two variants). The `over_budget` variant was removed in T-003 as dead code — the contract was not updated.

**Fix:**
1. Update CLAUDE.md Context Injection status line
2. Remove `over_budget` from all 3 locations in the contract

**Files:** `.claude/CLAUDE.md`, `docs/references/context-injection-contract.md`

## Verification

After all fixes:
1. All tests still pass: `cd packages/context-injection && uv run pytest` (expect 969)
2. CLAUDE.md reflects current state
3. Contract matches implementation types
4. Hook either works (with evidence) or is redesigned/removed
5. codex-reviewer handles large PRs gracefully

## References

### Files to Modify

| File | Finding |
|------|---------|
| `.claude/hooks/nudge-codex-consultation.py` | A1 |
| `.claude/settings.json` | A1 (if hook removed/restructured) |
| `.claude/agents/codex-reviewer.md` | A2, A3 |
| `.claude/CLAUDE.md` | A4 |
| `docs/references/context-injection-contract.md` | A4 |

### Related Tickets

| Ticket | Relationship |
|--------|-------------|
| T-003 | Predecessor — T-003 fixed context-injection findings, T-004 fixes remaining Codex integration issues |
| T-005 | Blocked by T-004 — Tier 2 significant fixes |
| T-006 | Blocked by T-004 — Tier 3 minor fixes |

### Audit Source

Full audit conducted by 4 parallel agents:
- **dialogue-auditor:** codex-dialogue.md — 17 findings (0A, 4B, 13C)
- **reviewer-auditor:** codex-reviewer.md + codex skill — 14 findings (2A, 7B, 5C)
- **integration-auditor:** hook + MCP config — 8 findings (1A, 3B, 4C)
- **docs-auditor:** CLAUDE.md + docs/codex-mcp/ + contract — 2 findings (1A, 0B, 1C)
