# T-005: Codex Audit Tier 2 — Significant Fixes

```yaml
id: T-005
date: 2026-02-17
status: complete
priority: medium
branch: chore/codex-audit-tier2
blocked_by: [T-004]
blocks: [T-006]
related: [T-003, T-004]
```

## Summary

14 Severity B findings from the full Codex integration audit. These are ambiguous instructions that could cause inconsistent behavior across sessions, missing examples, and calibration gaps. The codex-dialogue agent (the core component cross-model learning invokes) has 4 of these, making it the priority target.

**Scope:** codex-dialogue.md, codex-reviewer.md, codex skill SKILL.md, nudge-codex-consultation.py.

**Session plan:**
- Session 1: Create implementation plan using writing-plans skill
- Session 2: Execute the implementation plan
- Session 3: Review implementation + clean up

## Prerequisites

Before starting fixes:
1. T-004 (Tier 1) must be complete and merged
2. Create working branch from `main`
3. Read each file listed in the findings below

## Findings

### codex-dialogue Agent (4 findings)

#### B1: `focus.claims` scoping instruction contradicts itself

**Found by:** dialogue-auditor

**Location:** `.claude/agents/codex-dialogue.md:222-224`

**Problem:** Line 223 says "Build `claims` list once from ledger extraction. Assign to BOTH `focus.claims` and top-level `claims` fields." Then immediately says "On subsequent turns, `focus.claims` contains claims relevant to the current focus scope (not the full conversation history)." The first sentence says assign the same list to both fields; the second says `focus.claims` should be a subset.

**Impact:** Agent may always send identical lists (defeating scope-filtering) or attempt to filter without criteria.

**Fix:** Separate turn-1 and turn-N behavior explicitly. Clarify that both channels should carry the same list (which is what the server expects based on the dual-claims guard — mismatched lists trigger `ledger_hard_reject`).

**Writing principles violated:** #1 (Be Specific), #9 (Close Loopholes)

#### B2: "Weakest claim" derivation uses undefined "importance"

**Found by:** dialogue-auditor

**Location:** `.claude/agents/codex-dialogue.md:323-324`

**Problem:** "the weakest claim is the one with fewest `reinforced` statuses relative to its importance" — "importance" is undefined. No rubric for assessing importance.

**Impact:** Two agents would derive different "weakest claims." This directly affects follow-up composition priority (Step 6, priority item 4).

**Fix:** Define importance concretely (e.g., claims appearing in `unresolved` items or tagged `new` with no subsequent `reinforced`) or simplify to "the claim with the fewest `reinforced` statuses across all turns."

**Writing principles violated:** #1 (Be Specific), #7 (Specify Defaults)

#### B3: `turn_count` naming ambiguous — "completed" vs "current"

**Found by:** dialogue-auditor

**Location:** `.claude/agents/codex-dialogue.md:105, 203, 235, 357, 361-366`

**Problem:** `turn_count` described as "Turns completed" with initial value `1`, but represents current turn number. With `turn_count=1` and `effective_budget=1`, the budget gate fires at Step 3 of the FIRST turn — correct behavior but confusing naming.

**Impact:** Agent might mis-implement the budget gate for edge cases (budget=1, budget=2).

**Fix:** Rename to `current_turn` with initial value `1` and description "Current turn number (1-indexed)." Or keep name and change description to "Current turn number."

**Writing principles violated:** #2 (Define Terms), #1 (Be Specific)

#### B4: No document-wide default behavior statement

**Found by:** dialogue-auditor

**Location:** `.claude/agents/codex-dialogue.md` (global)

**Problem:** No catch-all default for situations not explicitly covered. Many specific defaults exist but no fallback for uncovered situations (e.g., Codex returns empty response, `process_turn` returns unexpected fields).

**Impact:** Agent must improvise for uncovered situations.

**Fix:** Add near the top: "Default: when no instruction covers the current situation, log a warning and proceed to the next step. If the current step cannot be skipped, synthesize from `turn_history` (proceed to Phase 3)."

**Writing principle violated:** #7 (Specify Defaults)

### codex-reviewer Agent (4 findings)

#### B5: Severity system undefined

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:128`

**Problem:** Uses Critical/High/Medium/Low severity but never calibrates them. Agent and Codex may assign severity using different criteria, making the output inconsistent.

**Fix:** Add a severity calibration table defining what each level means with examples.

#### B6: Redaction marker inconsistent with skill

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:78` vs `.claude/skills/codex/SKILL.md:132`

**Problem:** Agent uses `[REDACTED: credential material]`, skill uses `[REDACTED: sensitive credential material]`. Different marker text could cause pattern-matching issues.

**Fix:** Align to a single marker format across both components.

#### B7: Vague "surrounding code" guidance

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:40`

**Problem:** "Read modified files for surrounding context" doesn't specify how much context to read (whole file? function? 50 lines?).

**Fix:** Specify: "Read the full file for files under 300 lines. For larger files, read the modified functions plus 20 lines of surrounding context."

#### B8: No default for ambiguous prompt scope

**Found by:** reviewer-auditor

**Location:** `.claude/agents/codex-reviewer.md:27-34`

**Problem:** Four prompt patterns listed but no default for prompts that don't match any pattern.

**Fix:** Add a default: "For prompts that don't match the patterns above, treat as a general code review of the current branch's changes against the base branch."

### codex Skill (3 findings)

#### B9: No subagent delegation example

**Found by:** reviewer-auditor

**Location:** `.claude/skills/codex/SKILL.md:111-123`

**Problem:** Direct invocation has 3 examples; the delegated path (3+ turns via codex-dialogue subagent) has zero examples. This is a Principle #3 (Show Examples) violation.

**Fix:** Add 1-2 examples showing when and how delegation to codex-dialogue occurs, including what the briefing looks like and what the synthesized output contains.

#### B10: `-t` flag lacks case-sensitivity and version documentation

**Found by:** reviewer-auditor

**Location:** `.claude/skills/codex/SKILL.md:50`

**Problem:** No statement on whether the `-t` (reasoning effort) flag values are case-sensitive. No upstream version constraint documenting which Codex API versions support this parameter.

**Fix:** State case-sensitivity explicitly (e.g., "Values are case-insensitive: `high`, `HIGH`, and `High` are equivalent"). Add a note about API version support if relevant.

#### B11: Diagnostics section buried after workflow

**Found by:** reviewer-auditor

**Location:** `.claude/skills/codex/SKILL.md:204-215`

**Problem:** Diagnostics (timestamp, strategy chosen, threadId, success/failure) appear after the workflow section. Agent may complete review without capturing diagnostics.

**Fix:** Move diagnostics to an "Always" section that fires regardless of success/failure, or reference it from within the workflow steps.

### Hook (2 findings)

#### B12: `PostToolUseFailure` may not respect `matcher: Bash`

**Found by:** integration-auditor

**Location:** `.claude/hooks/nudge-codex-consultation.py:4`, `.claude/settings.json:8`

**Problem:** The official hooks reference states matchers are "only applicable for PreToolUse, PermissionRequest, and PostToolUse." `PostToolUseFailure` is not listed. If matchers are silently ignored, the hook fires for ALL tool failures.

**Impact:** Threshold reached faster than intended (3 failures of any tool type, not just Bash).

**Fix:** Depends on A1 resolution. If hook is redesigned, add explicit `tool_name` filtering in code. If hook works as-is, test matcher support empirically and add filtering if needed.

**Note:** This finding is contingent on T-004 A1 resolution.

#### B13: Temp file race condition

**Found by:** integration-auditor

**Location:** `.claude/hooks/nudge-codex-consultation.py:31-39,51-67`

**Problem:** Non-atomic read-modify-write cycle on counter file. Concurrent `PostToolUseFailure` hooks could lose counts.

**Impact:** Low in practice — failures would need to overlap within milliseconds. Consequence is just a missed count.

**Fix:** Use file locking (`fcntl.flock`) or atomic rename. Nice-to-have rather than urgent.

### Cross-Component (1 finding)

#### B14: `$ARGUMENTS` variable never defined in skill

**Found by:** reviewer-auditor

**Location:** `.claude/skills/codex/SKILL.md:43`

**Problem:** References `$ARGUMENTS` without defining what it represents or where it comes from.

**Fix:** Define: "`$ARGUMENTS` is the text after `/codex` in the user's command (e.g., for `/codex review this PR`, `$ARGUMENTS` is `review this PR`)."

**Writing principle violated:** #2 (Define Terms)

## Verification

After all fixes:
1. All tests still pass: `cd packages/context-injection && uv run pytest` (expect 969)
2. codex-dialogue agent: all 4 B findings resolved, no contradictions introduced
3. codex-reviewer agent: severity calibrated, large-PR guidance improved (from T-004 A3), redaction markers aligned
4. codex skill: delegation example added, diagnostics accessible during workflow
5. Hook findings resolved per T-004 A1 outcome

## References

### Files to Modify

| File | Findings |
|------|----------|
| `.claude/agents/codex-dialogue.md` | B1, B2, B3, B4 |
| `.claude/agents/codex-reviewer.md` | B5, B6, B7, B8 |
| `.claude/skills/codex/SKILL.md` | B9, B10, B11, B14 |
| `.claude/hooks/nudge-codex-consultation.py` | B12, B13 (contingent on T-004 A1) |

### Related Tickets

| Ticket | Relationship |
|--------|-------------|
| T-004 | Predecessor — T-004 fixes critical issues; T-005 addresses significant quality gaps |
| T-006 | Blocked by T-005 — Tier 3 minor fixes |
| T-003 | Related — T-003 fixed context-injection findings; some Severity C issues from T-003 overlap with B2, B3 |
