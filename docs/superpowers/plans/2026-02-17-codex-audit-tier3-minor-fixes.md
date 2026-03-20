# T-006: Codex Audit Tier 3 Minor Fixes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve 19 actionable Severity C findings from the Codex integration audit, raising baseline quality before cross-model learning implementation.

**Architecture:** Text edits to markdown instruction files and one Python hook. All changes are documentation/clarity improvements — no behavioral changes to the context-injection system. Group by file, edit bottom-to-top within each file to avoid line drift.

**Reference:** `docs/tickets/2026-02-17-codex-audit-tier3-minor-fixes.md`

**Branch:** Create `chore/codex-audit-tier3` from `main`.

**Test command:** `cd packages/context-injection && uv run pytest` (expect 969 tests)

**No change required (4 findings):**
- **C4:** `</output>` tag does not exist in current file — already resolved or never present
- **C8:** Negative-only framing acceptable (defense-in-depth per Principle #9)
- **C20:** `session_id` fallback to "unknown" is negligible risk — always present
- **C23:** Five-case checkpoint policy is implementation detail — contract covers agent-observable behavior

**Dependencies between tasks:**
- Tasks 1-4: independent (each targets a different file)
- Task 5: depends on Tasks 1-4 (cross-file verification + test suite)

---

## Task 1: codex-dialogue Agent (C1-C3, C5-C7, C9-C13) — 11 findings

**Precondition:** Read `.claude/rules/subagents.md` before editing.

**Files:**
- Modify: `.claude/agents/codex-dialogue.md`

All edits are bottom-to-top within the file to avoid line drift.

### Step 1: C2 — Pre-flight checklist zero-scout guidance

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
- [ ] Evidence statistics: scouts executed, entities scouted, impacts on conversation
```

new:
```
- [ ] Evidence statistics: scouts executed, entities scouted, impacts on conversation. If `evidence_count == 0`, state "Evidence: none (no scouts executed)" and omit evidence trajectory
```

### Step 2: C1 — Replace undefined "substantive" with delta terms

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
| **Medium** | One side proposed, the other agreed with reasoning (at least one `substantive` turn) |
```

new:
```
| **Medium** | One side proposed, the other agreed with reasoning (at least one turn where delta was `advancing` or `shifting`) |
```

### Step 3: C9 — Phase 3 assembly independence note

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
### Assembly process

1. **Convergence → Areas of Agreement:**
```

new:
```
### Assembly process

These 6 items are independent output sections. Assemble all 6 from `turn_history`.

1. **Convergence → Areas of Agreement:**
```

### Step 4: C12 — Condense de-scoped reframe paragraph

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
**De-scoped: Reframe model.** The design spec (Section 12) flags reframe outcome detection as an unsolved problem at medium priority. Unreliable classification (focus answered / premise falsified / enrichment) in dense agent instructions creates more harm than benefit. The target-lock guardrail above provides the necessary constraint without classification. **Future path:** Server-side `reframe_outcome` field (deterministic classification with cross-turn state) if explicit outcome routing proves necessary.
```

new:
```
**De-scoped: Reframe model.** Reframe outcome detection is de-scoped. The target-lock guardrail above is the active constraint.
```

### Step 5: C13 — Add rationale to Unknown action row

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
| Unknown action | Treat as `conclude` and log a warning: `"Unknown action '<action>' from process_turn — treating as conclude."` |
```

new:
```
| Unknown action | Treat as `conclude` and log a warning: `"Unknown action '<action>' from process_turn — treating as conclude."` (defense-in-depth — server currently returns only `continue_dialogue`, `closing_probe`, or `conclude`) |
```

### Step 6: C3 — Rename Step 4 sub-steps from 1-7 to 4a-4g

Three edits for sub-step renumbering:

**Edit 6a** `.claude/agents/codex-dialogue.md` — items 1-5 (before code block):

old:
```
1. Select the highest-ranked candidate (lowest `rank` value)
2. **Clarifier check:** If the top candidate has `scout_options: []` (empty list), this is a clarifier — skip scouting for this turn. Instead, use the clarifier's question text in Step 6 follow-up composition (treat it as a high-priority unresolved item). Continue to Step 5. (Clarifiers do not consume evidence budget, so this check runs even when `budget.scout_available` is `false`.)
3. **Budget gate:** If `budget.scout_available` is `false`, skip scout execution (steps 4-6 below). Continue to Step 5.
4. Select its first `scout_option`
5. Call `mcp__context-injection__execute_scout`:
```

new:
```
4a. Select the highest-ranked candidate (lowest `rank` value)
4b. **Clarifier check:** If the top candidate has `scout_options: []` (empty list), this is a clarifier — skip scouting for this turn. Instead, use the clarifier's question text in Step 6 follow-up composition (treat it as a high-priority unresolved item). Continue to Step 5. (Clarifiers do not consume evidence budget, so this check runs even when `budget.scout_available` is `false`.)
4c. **Budget gate:** If `budget.scout_available` is `false`, skip scout execution (steps 4d-4f below). Continue to Step 5.
4d. Select its first `scout_option`
4e. Call `mcp__context-injection__execute_scout`:
```

**Edit 6b** `.claude/agents/codex-dialogue.md` — item 6:

old:
```
6. On success:
```

new:
```
4f. On success:
```

**Edit 6c** `.claude/agents/codex-dialogue.md` — item 7:

old:
```
7. On error: continue without evidence. Do not retry.
```

new:
```
4g. On error: continue without evidence. Do not retry.
```

### Step 7: C11 — Posture table disambiguation note

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
| **Evaluative** | Doc review, quality assessment | Probe specifics, verify claims, check coverage |

### Assemble initial briefing
```

new:
```
| **Evaluative** | Doc review, quality assessment | Probe specifics, verify claims, check coverage |

**Disambiguation:** If the goal includes "find problems" or "challenge assumptions," use Adversarial. If "assess quality" or "check coverage," use Evaluative.

### Assemble initial briefing
```

### Step 8: C10 — threadId extraction failure mode

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
Persist `threadId` from the response (prefer `structuredContent.threadId`, fall back to top-level `threadId`).
```

new:
```
Persist `threadId` from the response (prefer `structuredContent.threadId`, fall back to top-level `threadId`). If neither source is present, report error and stop — the conversation cannot continue without a thread identifier.
```

### Step 9: C6 — model_reasoning_effort rejection fallback

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
| `config` | `{"model_reasoning_effort": "xhigh"}` |

Persist `threadId`
```

new:
```
| `config` | `{"model_reasoning_effort": "xhigh"}` |

If `model_reasoning_effort` is rejected by the API, omit it and proceed.

Persist `threadId`
```

### Step 10: C7 — Token safety freshness caveat

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
   - Base64 strings longer than 40 characters adjacent to authentication variable names
   If any match is detected,
```

new:
```
   - Base64 strings longer than 40 characters adjacent to authentication variable names
   This list is not exhaustive. The fail-closed rule below takes priority for unrecognized credential formats.
   If any match is detected,
```

### Step 11: C5 — Fix manual_legacy forward reference

**Edit** `.claude/agents/codex-dialogue.md`:

old:
```
(same as Step 1 above)
```

new:
```
(same as Step 1 of the per-turn loop below)
```

### Step 12: Verify Task 1

Run:
```bash
rg "substantive" .claude/agents/codex-dialogue.md
```
Expected: 0 matches (C1 — removed)

Run:
```bash
rg "Step 1 above" .claude/agents/codex-dialogue.md
```
Expected: 0 matches (C5 — replaced with "per-turn loop below")

Run:
```bash
rg "Section 12" .claude/agents/codex-dialogue.md
```
Expected: 0 matches (C12 — removed)

Run:
```bash
rg "4a\." .claude/agents/codex-dialogue.md
```
Expected: 1 match (C3 — sub-step renumbering)

Run:
```bash
rg "not exhaustive" .claude/agents/codex-dialogue.md
```
Expected: 1 match (C7 — freshness caveat)

Run:
```bash
rg "evidence_count == 0" .claude/agents/codex-dialogue.md
```
Expected: 1 match (C2 — zero-scout guidance)

Run:
```bash
rg "De-scoped" .claude/agents/codex-dialogue.md
```
Expected: 1 match, single line (C12 — condensed)

### Step 13: Commit

```bash
git add .claude/agents/codex-dialogue.md
git commit -m "fix(codex-dialogue): resolve C1-C3, C5-C7, C9-C13 — clarity and disambiguation

C1: replace undefined 'substantive' with delta terms
C2: add zero-scout guidance to pre-flight checklist
C3: rename Step 4 sub-steps 1-7 to 4a-4g
C5: fix manual_legacy forward reference to per-turn loop
C6: add model_reasoning_effort rejection fallback
C7: add freshness caveat to token safety pattern list
C9: add independence note to Phase 3 assembly
C10: add threadId extraction failure mode
C11: add posture table disambiguation note
C12: condense de-scoped reframe to one line
C13: add defense-in-depth rationale to Unknown action

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: codex-reviewer Agent (C14-C16) — 3 findings

**Precondition:** Read `.claude/rules/subagents.md` before editing.

**Files:**
- Modify: `.claude/agents/codex-reviewer.md`

### Step 1: C15 — Add success criteria for review output

**Edit** `.claude/agents/codex-reviewer.md`:

old:
```
## Output Format

### Summary
```

new:
```
## Output Format

**Complete review criteria:** (1) at least one finding per file reviewed or explicit "no issues found," (2) severity assigned to every finding, (3) source attribution (Codex/Self/Both) on every finding.

### Summary
```

### Step 2: C16 — Align step counts (5 in overview → 4)

**Edit** `.claude/agents/codex-reviewer.md`:

old:
```
1. **Gather changes** from git diff
2. **Read surrounding code** for context
3. **Assemble a review briefing** for Codex
4. **Consult Codex** via MCP (1-2 turns)
5. **Synthesize findings** — critically assess Codex's response, add your own observations
```

new:
```
1. **Gather changes** from git diff and read surrounding code for context
2. **Assemble a review briefing** for Codex
3. **Consult Codex** via MCP (1-2 turns)
4. **Synthesize findings** — critically assess Codex's response, add your own observations
```

### Step 3: C14 — Specify "project conventions" source

**Edit** `.claude/agents/codex-reviewer.md`:

old:
```
- Check for project conventions: CLAUDE.md, lint configs, test patterns
```

new:
```
- Check for project conventions from CLAUDE.md and `.claude/rules/`: lint configs, test patterns, code style
```

### Step 4: Verify Task 2

Run:
```bash
rg "^## Step" .claude/agents/codex-reviewer.md
```
Expected: 4 matches (Steps 1-4, C16 aligned)

Run:
```bash
rg "Complete review criteria" .claude/agents/codex-reviewer.md
```
Expected: 1 match (C15)

Run:
```bash
rg "CLAUDE.md and" .claude/agents/codex-reviewer.md
```
Expected: 1 match (C14)

### Step 5: Commit

```bash
git add .claude/agents/codex-reviewer.md
git commit -m "fix(codex-reviewer): resolve C14-C16 — structure, success criteria, specificity

C14: specify project conventions source (CLAUDE.md + .claude/rules/)
C15: add complete review criteria to Output Format
C16: align overview to 4 steps matching detailed sections

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: codex Skill (C17-C18) — 2 findings

**Precondition:** Read `.claude/rules/skills.md` before editing.

**Files:**
- Modify: `.claude/skills/codex/SKILL.md`

### Step 1: C18 — Align failure handling table to imperative voice

**Edit** `.claude/skills/codex/SKILL.md`:

old:
```
| Timeout | Tool timeout | Do not auto-retry. Warn that upstream may have processed the request and retry could create duplicates. Let the user opt into retry |
```

new:
```
| Timeout | Tool timeout | Do not auto-retry. Report that upstream may have processed the request; retrying could create duplicates. Prompt the user to confirm before retrying |
```

### Step 2: C17 — Consolidate reply continuity rule (location 1)

Remove redundant annotations from the continue-conversation parameter list, reference governance.

**Edit** `.claude/skills/codex/SKILL.md`:

old:
```
- at least one continuity identifier:
  - `threadId` (canonical)
  - `conversationId` (deprecated compatibility alias)
```

new:
```
- at least one continuity identifier: `threadId` or `conversationId` (see [Governance](#governance-decision-locked) rule #5)
```

### Step 3: C17 — Consolidate reply continuity rule (location 2)

Remove redundant "canonical" language from the continuity state section. Keep implementation detail (where to find threadId).

**Edit** `.claude/skills/codex/SKILL.md`:

old:
```
### Continuity state (canonical)

After a successful Codex tool call:
- Treat `structuredContent.threadId` as the canonical continuity source.
- Treat `content` as compatibility output only.
- Persist canonical `threadId` for follow-up turns. If `structuredContent.threadId` is missing, fall back to the top-level `threadId` field (when present).
```

new:
```
### Continuity state

After a successful Codex tool call, persist `threadId` for follow-up turns:
- Prefer `structuredContent.threadId` (primary source).
- Fall back to the top-level `threadId` field (when present).
- Treat `content` as compatibility output only.
```

Location 3 (Governance rule #5, line 256) is the authoritative definition — no change needed.

### Step 4: Verify Task 3

Run:
```bash
rg "deprecated compatibility alias" .claude/skills/codex/SKILL.md
```
Expected: 0 matches (C17 — removed from locations 1 and 2; Governance rule #5 uses different phrasing)

Run:
```bash
rg "Let the user" .claude/skills/codex/SKILL.md
```
Expected: 0 matches (C18 — replaced)

Run:
```bash
rg "canonical" .claude/skills/codex/SKILL.md
```
Expected: reduced count — only in Governance rule #5 ("threadId is canonical") and nearby references

### Step 5: Commit

```bash
git add .claude/skills/codex/SKILL.md
git commit -m "fix(codex-skill): resolve C17-C18 — DRY and voice consistency

C17: consolidate reply continuity rule to single governance definition
C18: align failure handling table to imperative voice

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Hook (C19, C21, C22) — 3 findings

**Precondition:** Read `.claude/rules/hooks.md` before editing.

**Files:**
- Modify: `.claude/hooks/nudge-codex-consultation.py`

### Step 1: C22 — Remove "consecutive" from nudge text

**Edit** `.claude/hooks/nudge-codex-consultation.py`:

old:
```
                    "You've hit several consecutive failures. "
```

new:
```
                    "You've hit several failures. "
```

### Step 2: C21 — Add return type to main()

**Edit** `.claude/hooks/nudge-codex-consultation.py`:

old:
```
def main():
```

new:
```
def main() -> None:
```

### Step 3: C19 — Document temp file lifecycle

**Edit** `.claude/hooks/nudge-codex-consultation.py`:

old:
```
def state_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"claude-nudge-{session_id}"
```

new:
```
def state_path(session_id: str) -> Path:
    # Temp files accumulate over sessions; OS /tmp cleanup handles removal.
    return Path(tempfile.gettempdir()) / f"claude-nudge-{session_id}"
```

### Step 4: Verify Task 4

Run:
```bash
rg "consecutive" .claude/hooks/nudge-codex-consultation.py
```
Expected: 0 matches (C22)

Run:
```bash
rg "\-> None" .claude/hooks/nudge-codex-consultation.py
```
Expected: 1 match (C21)

Run:
```bash
ruff check .claude/hooks/nudge-codex-consultation.py
```
Expected: clean

### Step 5: Commit

```bash
git add .claude/hooks/nudge-codex-consultation.py
git commit -m "fix(hook): resolve C19, C21, C22 — type annotation, text fix, documentation

C19: document temp file lifecycle (OS cleanup)
C21: add -> None return type to main()
C22: remove 'consecutive' from nudge text (counter tracks all failures)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Cross-File Verification + Ticket Update

**Depends on:** Tasks 1-4

### Step 1: Run test suite

Run:
```bash
cd packages/context-injection && uv run pytest
```
Expected: 969 tests passed

### Step 2: Cross-file grep verification

**Removed text (all should be 0 matches):**

| Pattern | File | Finding |
|---------|------|---------|
| `substantive` | codex-dialogue.md | C1 |
| `Step 1 above` | codex-dialogue.md | C5 |
| `Section 12` | codex-dialogue.md | C12 |
| `deprecated compatibility alias` | codex SKILL.md | C17 |
| `Let the user` | codex SKILL.md | C18 |
| `consecutive` | hook .py | C22 |

**Added text (all should be 1+ matches):**

| Pattern | File | Finding |
|---------|------|---------|
| `advancing.*shifting` | codex-dialogue.md | C1 |
| `evidence_count == 0` | codex-dialogue.md | C2 |
| `4a\.` | codex-dialogue.md | C3 |
| `per-turn loop below` | codex-dialogue.md | C5 |
| `rejected by the API` | codex-dialogue.md | C6 |
| `not exhaustive` | codex-dialogue.md | C7 |
| `independent output sections` | codex-dialogue.md | C9 |
| `neither source is present` | codex-dialogue.md | C10 |
| `Disambiguation` | codex-dialogue.md | C11 |
| `De-scoped.*active constraint` | codex-dialogue.md | C12 |
| `defense-in-depth.*server currently` | codex-dialogue.md | C13 |
| `CLAUDE.md and` | codex-reviewer.md | C14 |
| `Complete review criteria` | codex-reviewer.md | C15 |
| `Governance.*rule #5` | codex SKILL.md | C17 |
| `Prompt the user to confirm` | codex SKILL.md | C18 |
| `OS /tmp cleanup` | hook .py | C19 |
| `-> None` | hook .py | C21 |

### Step 3: Lint check

Run:
```bash
ruff check .claude/hooks/nudge-codex-consultation.py
```
Expected: clean

### Step 4: Update ticket status

**Edit** `docs/tickets/2026-02-17-codex-audit-tier3-minor-fixes.md`:

old:
```
status: open
```

new:
```
status: complete
```

old:
```
branch: null
```

new:
```
branch: chore/codex-audit-tier3
```

### Step 5: Commit

```bash
git add docs/tickets/2026-02-17-codex-audit-tier3-minor-fixes.md
git commit -m "chore: mark T-006 complete, update plan

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Final Verification

Run: `cd packages/context-injection && uv run pytest`
Expected: All 969 tests pass (no regressions — changes are to markdown and one Python hook)

Run: `ruff check .claude/hooks/nudge-codex-consultation.py`
Expected: No errors

## Summary of Deliverables

| File | New/Modified | What This Plan Changes |
|------|-------------|----------------------|
| `.claude/agents/codex-dialogue.md` | Modified | 11 clarity fixes: disambiguation, failure modes, condensed prose, sub-step renumbering |
| `.claude/agents/codex-reviewer.md` | Modified | 3 structural fixes: step count alignment, success criteria, convention source |
| `.claude/skills/codex/SKILL.md` | Modified | 2 DRY/consistency fixes: consolidated reply continuity, imperative voice |
| `.claude/hooks/nudge-codex-consultation.py` | Modified | 3 minor fixes: type annotation, text accuracy, lifecycle documentation |
| `docs/tickets/...tier3...md` | Modified | Status update: open → complete |

## Plan-Level Decisions

### D1: C4 — No change required (tag doesn't exist)

The ticket reports a `</output>` tag at line 513 of codex-dialogue.md. The file currently ends at line 517 with a standard markdown bullet list — no XML tags present. Marked as no-change-required alongside C8, C20, C23.

### D2: C3 — Use lettered sub-steps (4a-4g) not bullet points

The ticket suggests either "Rename sub-steps to 4a-4g, or use bullet points." Lettered sub-steps preserve the explicit ordering and sequence that numbered steps communicate, while disambiguating from outer loop Steps 4-7. Bullet points would lose ordering semantics.

### D3: C19 — Document lifecycle, don't add SessionEnd hook

The ticket suggests either a SessionEnd hook or accepting OS cleanup. Adding a second hook file for temp file cleanup is over-engineering: the files are small (a few bytes each), accumulate slowly (one per session), and OS temp cleanup handles removal. A comment documenting this decision is sufficient.

### D4: C17 — Keep implementation detail in location 2, remove only duplication

Location 2 (Continuity state section) contains WHERE to find threadId (structuredContent vs top-level). This is implementation detail not duplicated elsewhere. Only the "canonical" / "deprecated" annotations duplicate Governance rule #5. Fix removes the annotations, keeps the implementation detail.

### D5: C12 — Aggressive condensation (4 lines → 1 line)

The original paragraph contains design rationale, problem analysis, and future path — none of which are actionable instructions. The one-line replacement states the decision and the active constraint. Design rationale belongs in the design spec, not in agent instructions.

### D6: C5 — Fix reference direction, don't move section

The ticket suggests either moving manual_legacy after the per-turn loop or fixing the forward reference. Moving the section would change document structure and potentially affect how the agent parses mode-gating flow. Fixing "above" → "of the per-turn loop below" is minimal and precise.
