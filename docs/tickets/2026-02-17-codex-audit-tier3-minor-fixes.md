# T-006: Codex Audit Tier 3 — Minor Fixes

```yaml
id: T-006
date: 2026-02-17
status: complete
priority: low
branch: chore/codex-audit-tier3
blocked_by: [T-004, T-005]
blocks: []
related: [T-003, T-004, T-005]
```

## Summary

23 Severity C findings from the full Codex integration audit. These are clarity improvements, documentation enhancements, style issues, and defensive coding suggestions. None affect behavior, but resolving them raises the baseline quality of the Codex integration before building cross-model learning on top.

**Scope:** codex-dialogue.md, codex-reviewer.md, codex skill SKILL.md, nudge-codex-consultation.py, context-injection-contract.md.

**Session plan:**
- Session 1: Create implementation plan using writing-plans skill
- Session 2: Execute the implementation plan
- Session 3: Review implementation + clean up

## Prerequisites

Before starting fixes:
1. T-004 (Tier 1) and T-005 (Tier 2) must be complete and merged
2. Create working branch from `main`
3. Verify 969 tests still pass

## Findings

### codex-dialogue Agent (13 findings)

#### C1: `substantive` turn label used without definition

**Location:** `.claude/agents/codex-dialogue.md:389`

**Problem:** Confidence table says "at least one `substantive` turn" but `substantive` is not defined. Delta values are `advancing`, `shifting`, `static` — none called `substantive`.

**Fix:** Replace with concrete reference: "at least one `advancing` turn" or "at least one turn where delta was `advancing` or `shifting`."

#### C2: Pre-flight checklist assumes scouts always executed

**Location:** `.claude/agents/codex-dialogue.md:403, 408`

**Problem:** Evidence statistics item is vacuous for zero-scout conversations. No guidance for `evidence_count == 0`.

**Fix:** Add: "If `evidence_count == 0`, state 'Evidence: none (no scouts executed)' and omit evidence trajectory."

#### C3: Step 4 sub-step numbering confuses inner/outer

**Location:** `.claude/agents/codex-dialogue.md:271-296`

**Problem:** Step 4 (Scout) has its own numbered sub-steps 1-7. "Steps 4-6 below" at line 276 refers to sub-steps, but "Steps 4-7" at line 235 refers to outer loop steps.

**Fix:** Rename sub-steps to 4a-4g, or use bullet points.

#### C4: Closing `</output>` tag artifact at end of file

**Location:** `.claude/agents/codex-dialogue.md:513`

**Problem:** File ends with `</output>` — likely a rendering artifact.

**Fix:** Remove the tag.

#### C5: `manual_legacy` mode forward-references "Step 1 above"

**Location:** `.claude/agents/codex-dialogue.md:131-137`

**Problem:** References "(same as Step 1 above)" but Step 1 hasn't been defined yet at this point in the document.

**Fix:** Move manual_legacy after the 7-step loop, or make the forward reference explicit.

#### C6: `model_reasoning_effort` value "xhigh" has no failure mode

**Location:** `.claude/agents/codex-dialogue.md:89`

**Problem:** Configuration value `"xhigh"` is Codex API-specific. No guidance on what happens if rejected.

**Fix:** Add: "If `model_reasoning_effort` is rejected by the API, omit it and proceed."

#### C7: Token safety pattern list lacks freshness caveat

**Location:** `.claude/agents/codex-dialogue.md:64-75`

**Problem:** Credential patterns list is comprehensive but has no versioning constraint. Creates false sense of exhaustiveness despite the fail-closed rule.

**Fix:** Add after pattern list: "This list is not exhaustive. The fail-closed rule (line 74) takes priority for unrecognized credential formats."

#### C8: "Do not include" section uses only negative framing

**Location:** `.claude/agents/codex-dialogue.md:508-512`

**Problem:** Prohibitions-only section. What should be included instead?

**Assessment:** Acceptable — defense-in-depth per Principle #9, which outranks #14. **No change required** unless other C findings are being addressed in the same section.

#### C9: Phase 3 assembly lacks ordering guarantee

**Location:** `.claude/agents/codex-dialogue.md:375-380`

**Problem:** 6-item assembly numbered but unclear if sequential or independent sections.

**Fix:** Add: "These 6 items are independent output sections. Assemble all 6 from `turn_history`."

#### C10: `threadId` extraction has no failure mode for missing value

**Location:** `.claude/agents/codex-dialogue.md:91`

**Problem:** "Persist `threadId` from the response" with fallback chain, but no handling for when both sources are absent.

**Fix:** Add: "If neither `structuredContent.threadId` nor top-level `threadId` is present, report error and stop."

#### C11: Posture table lacks selection disambiguation

**Location:** `.claude/agents/codex-dialogue.md:44-49`

**Problem:** Overlap between Evaluative and Adversarial for similar tasks (e.g., doc review).

**Fix:** Add: "If the goal includes 'find problems' or 'challenge assumptions,' use Adversarial. If 'assess quality' or 'check coverage,' use Evaluative."

#### C12: De-scoped reframe model paragraph is non-actionable

**Location:** `.claude/agents/codex-dialogue.md:340`

**Problem:** 4 lines of design rationale that consume context without providing instruction. References "Section 12" without a path.

**Fix:** Reduce to one line: "Reframe outcome detection is de-scoped. The target-lock guardrail above is the active constraint."

#### C13: Step 5 "Unknown action" rationale unstated

**Location:** `.claude/agents/codex-dialogue.md:305`

**Problem:** Defense-in-depth fallback exists but rationale not documented. Could be mistaken for dead code.

**Fix:** Add: "(defense-in-depth — server currently returns only `continue_dialogue`, `closing_probe`, or `conclude`)."

### codex-reviewer Agent (3 findings)

#### C14: Vague "project conventions" check

**Location:** `.claude/agents/codex-reviewer.md:41`

**Problem:** Instructs checking "project conventions" without specifying what those are or where to find them.

**Fix:** Reference CLAUDE.md code style section or specify: "conventions from CLAUDE.md and .claude/rules/."

#### C15: No observable success criteria for review output

**Location:** `.claude/agents/codex-reviewer.md` (global)

**Problem:** Missing Principle #13 — no definition of what a successful review looks like.

**Fix:** Add: "A complete review includes: (1) at least one finding per file reviewed or explicit 'no issues found,' (2) severity assigned to every finding, (3) source attribution (Codex/Self/Both)."

#### C16: Step numbering mismatch — 5 in overview, 4 in detail

**Location:** `.claude/agents/codex-reviewer.md`

**Problem:** Overview mentions 5 steps but detailed section has 4. Inconsistent structure.

**Fix:** Align step counts. Either add the missing step or correct the overview.

### codex Skill (2 findings)

#### C17: Governance decision #5 triple-stated

**Location:** `.claude/skills/codex/SKILL.md:224, 168-173, 148-165`

**Problem:** Reply continuity rule (`threadId` canonical, `conversationId` deprecated alias) stated in 3 separate places.

**Fix:** State once in the governance section, reference from others.

#### C18: Mixed voice in failure handling table

**Location:** `.claude/skills/codex/SKILL.md:189-198`

**Problem:** Some rows use imperative ("Report the failure"), others use descriptive ("The model reports").

**Fix:** Align to imperative voice throughout.

### Hook (4 findings)

#### C19: Temp files not cleaned up on session end

**Location:** `.claude/hooks/nudge-codex-consultation.py:28`

**Problem:** Temp files (`/tmp/claude-nudge-{session_id}`) accumulate over time.

**Fix:** Add `SessionEnd` hook for cleanup, or accept OS temp cleanup. Low priority.

#### C20: `session_id` fallback to "unknown" creates shared state

**Location:** `.claude/hooks/nudge-codex-consultation.py:49`

**Problem:** If `session_id` missing, fallback "unknown" means sessions share a counter.

**Assessment:** Negligible — `session_id` is always present. **No change required.**

#### C21: No type annotation on `main()`

**Location:** `.claude/hooks/nudge-codex-consultation.py:42`

**Problem:** `main()` lacks `-> None` return type. Inconsistent with the file's own convention.

**Fix:** Add `-> None`.

#### C22: Counter doesn't distinguish related vs unrelated failures

**Location:** `.claude/hooks/nudge-codex-consultation.py:51-53`

**Problem:** Three unrelated failures trigger the same nudge as three consecutive failures on one problem. Nudge text says "consecutive" but they may not be.

**Fix:** Change text from "several consecutive failures" to "several failures." Accept as-is for behavior.

### Contract (1 finding)

#### C23: Checkpoint five-case policy not documented in contract

**Location:** `docs/references/context-injection-contract.md:698-705`

**Problem:** Contract documents Turn 1 / Turn 2+ behavior but not the five-case policy from `checkpoint.py:172-189`.

**Assessment:** The contract's external-facing docs cover agent-observable behavior adequately. The five cases are implementation detail. **No change required** — noted for completeness.

## Summary Table

| Component | Count | IDs |
|-----------|-------|-----|
| codex-dialogue agent | 13 | C1-C13 |
| codex-reviewer agent | 3 | C14-C16 |
| codex skill | 2 | C17-C18 |
| Hook | 4 | C19-C22 |
| Contract | 1 | C23 |
| **Total** | **23** | |
| No change required | 3 | C8, C20, C23 |
| **Actionable** | **20** | |

## Verification

After all fixes:
1. All tests still pass: `cd packages/context-injection && uv run pytest` (expect 969)
2. No new contradictions introduced in agent files
3. Writing principles spot-check: verify fixes comply with referenced principles
4. All "no change required" items confirmed as intentional (not skipped)

## References

### Files to Modify

| File | Findings |
|------|----------|
| `.claude/agents/codex-dialogue.md` | C1-C13 (C8 no change) |
| `.claude/agents/codex-reviewer.md` | C14-C16 |
| `.claude/skills/codex/SKILL.md` | C17-C18 |
| `.claude/hooks/nudge-codex-consultation.py` | C19-C22 (C20 no change) |
| `docs/references/context-injection-contract.md` | C23 (no change) |

### Related Tickets

| Ticket | Relationship |
|--------|-------------|
| T-004 | Predecessor — Tier 1 critical fixes |
| T-005 | Predecessor — Tier 2 significant fixes |
| T-003 | Related — some C findings overlap with T-003 deferred items (C1/C2/C13 match PR #10 Severity C issues) |
