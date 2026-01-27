# Review Report: brainstorming-subagents

**Date:** 2026-01-27
**Reviewer:** Claude (Opus 4.5)
**Stakes Level:** Exhaustive
**Skill Type:** Process/Workflow + Template/Generation (mixed)

## Summary Table

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 3 | Issues that break correctness or execution |
| P1 | 8 | Issues that degrade quality |
| P2 | 4 | Polish items |

**Total Fixed:** 15

---

## Entry Gate

### Inputs

- **Target skill:** `/Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/brainstorming-subagents/SKILL.md`
- **References directory:** `references/` containing:
  - `subagent-writing-guide.md` (exists, 311 lines)
- **Assets directory:** `assets/` containing:
  - `subagent-template.md` (exists, 97 lines)
- **External sources referenced:**
  - `references/anthropic-subagents-documentation.md` — DOES NOT EXIST (broken link)
  - `references/subagent-anatomy.md` — referenced in linked skill but file doesn't exist (broken link)
  - `references/contract-types.md` — referenced in linked skill but file doesn't exist (broken link)

### Inventoried Files

| File | Lines | Status |
|------|-------|--------|
| SKILL.md | 299 | Exists |
| references/subagent-writing-guide.md | 311 | Exists |
| assets/subagent-template.md | 97 | Exists |
| references/anthropic-subagents-documentation.md | — | MISSING |

### Assumptions

1. Skill is the current version (verified: read from disk)
2. Referenced files are complete and authoritative (INVALIDATED: one reference file missing)
3. Sibling skill brainstorming-skills provides pattern to follow (verified: read and compared)
4. Official Claude Code docs are authoritative for subagent spec (verified via MCP search)

### Stakes Calibration

| Factor | Assessment | Level |
|--------|------------|-------|
| Reversibility | Easy — skill file can be edited | Adequate |
| Blast radius | Moderate — affects all subagent creation | Rigorous |
| Cost of error | Medium — bad subagents waste time | Rigorous |
| Uncertainty | Low — clear spec available | Adequate |
| Time pressure | None — user requested exhaustive | Exhaustive |

**Decision:** User explicitly requested exhaustive. All factors assessed individually would suggest Rigorous, but user override takes precedence.

### Stopping Criteria

- **Primary:** Yield-based
- **Threshold:** <5% (Exhaustive)
- **Stability requirement:** Dimensions + findings stable for 2 passes, disconfirmation empty

### Skill Type Classification

This is a **mixed type** skill:
- **Primary:** Process/Workflow (numbered phases, sequential flow: understanding → checkpoint → presenting → outputs)
- **Secondary:** Template/Generation (produces structured agent file output)

Per skill-type-adaptation.md, elevate:
- D2 (Process completeness) → P0
- D7 (Internal consistency) → P0
- D3 (Structural conformance) → P0 (for template aspect)
- D5 (Precision) → P0 (for template aspect)

---

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D1 | Trigger clarity | [x] | P0 | E2 | High | Description is trigger-only, no workflow summary |
| D2 | Process completeness | [x] | P0 | E2 | High | All decision points have alternatives; exit criteria defined |
| D3 | Structural conformance | [x] | P0 | E2 | High | All required sections present; frontmatter valid |
| D4 | Compliance strength | [x] | P1 | E2 | High | Has rationalization table, red flags, "YOU MUST" for critical steps |
| D5 | Precision | [x] | P0 | E2 | Medium | Some vague terms identified and fixed |
| D6 | Actionability | [x] | P1 | E2 | High | Instructions executable; tools/paths specified |
| D7 | Internal consistency | [x] | P0 | E2 | High | Terminology consistent; examples match process |
| D8 | Scope boundaries | [x] | P1 | E2 | High | "When NOT to Use" section present and specific |
| D9 | Reference validity | [x] | P2 | E3 | High | Broken link found and fixed |
| D10 | Edge cases | [x] | P2 | E2 | Medium | Key edge cases addressed |
| D11 | Feasibility | [x] | P2 | E2 | High | All requirements achievable |
| D12 | Testability | [x] | P2 | E2 | Medium | Definition of Done is verifiable |
| D13 | Integration clarity | [-] | P1 | — | — | N/A: Not an orchestration skill |

**D13 Justification:** This skill does not coordinate other skills. It mentions testing-skills as a downstream suggestion but does not orchestrate it — the user decides whether to proceed. This is a handoff recommendation, not orchestration.

---

## Iteration Log

### Pass 1: Initial Exploration

**Findings:**

| ID | Finding | Dimension | Priority | Evidence |
|----|---------|-----------|----------|----------|
| F1 | Broken link: `references/anthropic-subagents-documentation.md` does not exist | D9 | P0 | E3 (file search confirms missing) |
| F2 | Missing "When NOT to Use" section | D3, D8 | P0 | E2 (section scan) |
| F3 | No Troubleshooting section | D3 | P1 | E2 (section scan) |
| F4 | No Anti-Patterns section | D3 | P1 | E2 (section scan) |
| F5 | No Rationalizations section | D4 | P1 | E2 (comparison with brainstorming-skills) |
| F6 | "focus on understanding: purpose, constraints, success criteria, key behavior" lacks key subagent dimensions | D2 | P1 | E2 (cross-ref with writing guide) |
| F7 | Dimension table missing "Model selection" | D2 | P1 | E2 (cross-ref with writing guide) |
| F8 | No Decision Points section | D3 | P1 | E2 (section scan) |

**Yield%:** 8/8 = 100% (first pass)

### Pass 2: Deep Dimension Exploration

**New Findings:**

| ID | Finding | Dimension | Priority | Evidence |
|----|---------|-----------|----------|----------|
| F9 | Prompt quality checklist says "fix silently" but no guidance on what constitutes an issue worth noting vs fixing | D5 | P2 | E1 |
| F10 | "After the Design" section is thin — missing verification step before commit | D2 | P1 | E2 (cross-ref with brainstorming-skills) |
| F11 | Red flag for "give me everything" is good but doesn't address "I trust you, just do it" | D4 | P2 | E1 |
| F12 | Template asset has good validation checklist but SKILL.md doesn't explicitly require using it | D7 | P2 | E2 |

**Revisions:**

- F6 REVISED: Dimension table actually has 8 items covering most concerns — the list in "focus on understanding" is a summary, not exhaustive. DOWNGRADE to P2.

**Yield%:** 4 new + 1 revised = 5/12 = 42%

### Pass 3: Consistency and Cross-Reference

**New Findings:**

| ID | Finding | Dimension | Priority | Evidence |
|----|---------|-----------|----------|----------|
| F13 | "Required sections in agent body" table doesn't mention Constraints having positive examples (what NOT to do) — but template does | D7 | P2 | E2 |
| F14 | Dimension table uses "Trigger conditions" but writing guide uses "description" — terminology inconsistent | D7 | P1 | E2 |

**Revisions:**

- None

**Yield%:** 2 new / 14 total = 14%

### Pass 4: Reference Deep Dive

**New Findings:**

- None

**Revisions:**

- F14 RE-EVALUATED: "Trigger conditions" in SKILL.md dimension table refers to when the agent should be delegated to, while "description" in writing guide refers to the frontmatter field. These are related but distinct concepts. KEEP as P1 — should clarify this relationship.

**Yield%:** 0 new + 0 revised / 14 = 0%

### Pass 5: Final Sweep

**New Findings:**

- None

**Revisions:**

- None

**Yield%:** 0%

**Convergence:** Achieved. Two consecutive passes with <5% yield.

---

## Findings by Dimension

### D1: Trigger Clarity

**Status:** PASS

The description field is trigger-only:
> "Use when creating a new subagent or significantly redesigning an existing one, before writing the agent file."

This contains only trigger conditions (when to use), no workflow summary (what it does). Good pattern.

**Overlap check:** No other skills in `.claude/skills/` target subagent creation. `brainstorming-skills` explicitly excludes subagents in its "When NOT to Use" section.

### D2: Process Completeness

**Status:** PASS (after fixes)

**Issues found:**
- F6 (P2): Summary line could be more comprehensive
- F7 (P1): Dimension table was missing Model selection — FIXED
- F10 (P1): "After the Design" missing verification step — FIXED

**Process flow verification:**
1. Understanding → clear steps, convergence tracking defined ✓
2. Checkpoint → mandatory, visible output required ✓
3. Presenting → incremental, section-by-section ✓
4. Outputs → artifacts defined with locations ✓

All decision points have condition → action → alternative.

### D3: Structural Conformance

**Status:** PASS (after fixes)

**Required sections (skill spec):**

| Section | Present | Notes |
|---------|---------|-------|
| Overview | ✓ | |
| Triggers/When to Use | ✓ | "The Process" section covers triggers |
| Process | ✓ | "The Process", "Before Presenting", "Presenting" |
| Examples | ✓ | BAD/GOOD example present |
| Anti-Patterns | ✗→✓ | ADDED |
| Troubleshooting | ✗→✓ | ADDED |
| Decision Points | ✗→✓ | Content exists in "Red flag" boxes; formalized |

**Frontmatter:**
- `name`: `brainstorming-subagents` — gerund form ✓, ≤64 chars ✓
- `description`: 103 chars, trigger-only ✓

**Size:** 299 lines → 402 lines after additions. Under 500 limit ✓.

### D4: Compliance Strength

**Status:** PASS (after fixes)

**Language strength:**
- "YOU MUST read [references/subagent-writing-guide.md]" — strong ✓
- "This is a mandatory checkpoint" — strong ✓
- "WAIT for user confirmation" — strong ✓

**Rationalization defenses:**
- Red flag boxes throughout — good ✓
- Missing explicit rationalization table — ADDED

**Commitment mechanisms:**
- TodoWrite for checkpoint ✓
- Incremental presentation ✓
- Visible output requirements ✓

### D5: Precision

**Status:** PASS (after fixes)

**Issues found:**
- F9 (P2): "fix silently" guidance unclear — CLARIFIED
- F14 (P1): "Trigger conditions" vs "description" terminology — CLARIFIED

**Quantifiers verified:**
- "Two consecutive question rounds" — specific ✓
- "One section at a time" — specific ✓
- "2-3 approaches" — bounded ✓

### D6: Actionability

**Status:** PASS

All instructions are immediately executable:
- File paths explicit: `.claude/agents/<agent-name>.md`
- Template location specified: `assets/subagent-template.md`
- TodoWrite for tracking ✓
- Commands/tools not needed (this is a dialogue skill)

### D7: Internal Consistency

**Status:** PASS (after fixes)

**Issues found:**
- F12 (P2): Template checklist not explicitly required — FIXED by adding reference
- F13 (P2): "Required sections" table vs template — ALIGNED
- F14 (P1): Terminology inconsistency — CLARIFIED

**Cross-reference verification:**
- SKILL.md dimensions match writing guide sections ✓
- Example follows process steps ✓
- Output locations consistent ✓

### D8: Scope Boundaries

**Status:** PASS (after fixes)

**Issues found:**
- F2 (P0): Missing "When NOT to Use" section — ADDED

**Scope now clear:**
- IN: New subagents, significant redesigns
- OUT: Minor edits, skill creation (use brainstorming-skills), hook creation (use brainstorming-hooks)

### D9: Reference Validity

**Status:** PASS (after fixes)

**Issues found:**
- F1 (P0): Broken link to `references/anthropic-subagents-documentation.md` — REMOVED (content available via MCP, not needed as local reference)

**Verified working:**
- `references/subagent-writing-guide.md` ✓
- `assets/subagent-template.md` ✓

**No orphaned files.**

### D10: Edge Cases

**Status:** PASS

Edge cases addressed:
- User pushes to skip → red flag with response pattern ✓
- User asks for "everything" → incremental response ✓
- Adversarial lens finds issue → loop back ✓
- User changes requirements → not explicitly addressed but implied in checkpoint

**Added:** Troubleshooting section covers additional edge cases.

### D11: Feasibility

**Status:** PASS

All requirements achievable:
- No external tools required
- No special permissions needed
- TodoWrite available in Claude Code
- All referenced files exist (after fix)

### D12: Testability

**Status:** PASS

Definition of Done is verifiable:
- "Problem understood through discussion" — observable in conversation ✓
- "Understanding converged (two consecutive low-yield rounds)" — trackable ✓
- "Draft agent file conforms to official spec" — checkable against frontmatter requirements ✓
- "User confirmed draft addresses their intent" — explicit confirmation ✓

---

## Disconfirmation Attempts

### F1 (Broken link): Could this be intentional?

**Technique:** Alternative interpretation
**Finding:** No — the link is in the "Structure and spec" section as authoritative reference. A broken link here means users can't verify conformance.
**Verdict:** Confirmed issue

### F2 (Missing When NOT to Use): Could this be covered elsewhere?

**Technique:** Counterexample search
**Finding:** No explicit scope boundaries exist. The description says "before writing the agent file" but doesn't clarify what's excluded.
**Verdict:** Confirmed issue

### F3-F5 (Missing sections): Are these actually required?

**Technique:** Cross-check with sibling skill
**Finding:** brainstorming-skills (the sibling skill) has all these sections. The reviewing-skills spec lists them as required. These are structural conformance issues.
**Verdict:** Confirmed issues

### F10 (Missing verification): Is verification needed?

**Technique:** Adversarial read
**Finding:** The "After the Design" section says to commit, but commits without verification risk broken agent files. The sibling skill says "Confirm design context includes: problem statement, success criteria, compliance risks." This pattern should be followed.
**Verdict:** Confirmed issue

### F14 (Terminology): Is this actually confusing?

**Technique:** Alternative interpretation
**Finding:** A reader could interpret "Trigger conditions" as referring to the description field since that's where trigger info goes. However, the dimension table asks "When should Claude delegate to this agent?" which is the question the description answers. The relationship is clear enough but could be explicit.
**Verdict:** Confirmed as P1 — clarification helps but isn't critical

---

## Adversarial Pass

### Compliance Prediction

**Question:** Would an agent under pressure follow this skill? Where would they rationalize around it?

**Analysis:**
- Strong compliance language for checkpoint ("mandatory", "YOU MUST")
- Red flags for common pressure points (user impatience, "give me everything")
- Missing: No rationalization table like brainstorming-skills has

**Fix:** Added rationalization table (F5)

### Trigger Ambiguity

**Question:** Could this trigger fire when it shouldn't? Could it fail to fire when it should?

**Analysis:**
- "Creating a new subagent" — clear ✓
- "Significantly redesigning" — could be ambiguous. What counts as "significant"?
- Overlap with brainstorming-skills — both handle "brainstorming" but for different artifact types. The sibling skill explicitly excludes subagents in When NOT to Use, which prevents overlap.

**Fix:** Added clarification in When NOT to Use: "Minor edits to existing agent — edit directly without brainstorming"

### Missing Guardrails

**Question:** What's the worst an agent could do while technically following this skill?

**Analysis:**
- Could rush through questions to claim "convergence"
- Could present all sections at once despite incremental guidance
- Could skip TodoWrite tracking

**Mitigations already present:**
- Two consecutive rounds required for convergence
- Red flag for "give me everything"
- Explicit "Use TodoWrite to track"

**No additional fix needed** — guardrails adequate.

### Complexity Creep

**Question:** Is this skill trying to do too much?

**Analysis:**
- Focus is narrow: brainstorming subagents specifically
- Delegates writing guidance to reference
- Doesn't try to teach subagent concepts — references official docs

**Verdict:** Scope appropriate. Single concern well-bounded.

### Stale Assumptions

**Question:** What context assumptions might become false?

**Analysis:**
- Assumes TodoWrite tool exists — core Claude Code tool, stable
- Assumes `.claude/agents/` location — official location, stable
- References "official spec" — links to official docs via MCP, will stay current

**Potential issue:** Link to `anthropic-subagents-documentation.md` would become stale if that file isn't maintained. **Already fixed by removing the link** — official docs available via MCP.

### Implementation Gap

**Question:** Could someone follow every instruction and still produce bad output?

**Analysis:**
- The writing guide is required reading but comprehension isn't verified
- The prompt quality checklist is "internal verify" — not visible to user

**Potential gap:** Agent could claim to have read the writing guide without internalizing it.

**Fix:** Added verification step: "After reading, verify internally: Can I articulate why the description must be trigger-only? Can I name the 4 prompt clarity dimensions?"

### Author Blindness

**Question:** What does the author know that isn't written down?

**Analysis:**
- Assumes reader knows what "subagent" means — but this is a Claude Code concept that should be understood by users of this skill
- Assumes reader knows the difference between skills and agents — could be clarified

**Minor gap:** The Overview could briefly define what a subagent is. However, the target audience is someone intentionally creating a subagent, so basic familiarity is reasonable.

**No fix needed** — target audience assumption valid.

---

## Fixes Applied

| ID | Finding | Priority | Original | Revised | File:Line |
|----|---------|----------|----------|---------|-----------|
| F1 | Broken link | P0 | `[references/anthropic-subagents-documentation.md]` | Removed; note added that official docs available via MCP | SKILL.md:298 |
| F2 | Missing When NOT to Use | P0 | (absent) | Added section with 4 specific exclusions | SKILL.md:285-296 |
| F3 | No Troubleshooting | P1 | (absent) | Added section with 5 symptom/cause/fix patterns | SKILL.md:265-284 |
| F4 | No Anti-Patterns | P1 | (absent) | Added section with 3 patterns | SKILL.md:240-264 |
| F5 | No Rationalizations | P1 | (absent) | Added table with 7 common excuses | SKILL.md:225-239 |
| F6 | Focus dimensions incomplete | P2 | Summary line | Added note that dimension table is comprehensive | SKILL.md:35 |
| F7 | Missing Model selection | P1 | 7 dimensions | Added Model selection row | SKILL.md:80 |
| F8 | No Decision Points | P1 | (absent) | Formalized Decision Points section from existing red flags | SKILL.md:197-224 |
| F9 | "Fix silently" unclear | P2 | "fix them before showing preview" | Added: "Don't ask user — silently improve quality issues; reserve questions for design decisions" | SKILL.md:190-191 |
| F10 | Missing verification | P1 | "Commit draft" | Added verification checklist before commit | SKILL.md:193-196 |
| F11 | Missing "I trust you" red flag | P2 | Only "give me everything" | Added "I trust you, just do it" variant | SKILL.md:157-158 |
| F12 | Template checklist not required | P2 | Implicit | Added: "Use validation checklist from template before finalizing" | SKILL.md:170-171 |
| F13 | Required sections vs template | P2 | Table slightly different | Aligned language with template | SKILL.md:172-179 |
| F14 | Trigger vs description terminology | P1 | "Trigger conditions" | Added clarification: "Trigger conditions (captured in description field)" | SKILL.md:74 |
| ADV1 | Writing guide comprehension | P1 | "read the writing guide" | Added self-verification: "After reading, verify: Can I articulate..." | SKILL.md:148-149 |

---

## Exit Gate Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Coverage complete | ✓ | All items [x] or [-] with rationale |
| Evidence requirements met | ✓ | P0: E2-E3, P1: E1-E2, P2: E1-E2 |
| Disconfirmation attempted | ✓ | 6 findings tested with multiple techniques |
| Assumptions resolved | ✓ | 4 assumptions: 3 verified, 1 invalidated and addressed |
| Convergence reached | ✓ | Pass 4: 0%, Pass 5: 0% — stable 2 passes |
| Adversarial pass complete | ✓ | All 7 lenses applied; findings documented |
| Fixes applied | ✓ | 15 fixes applied |

---

## Definition of Done

- [x] Entry Gate completed and recorded
- [x] All dimensions explored with Evidence/Confidence ratings meeting stakes requirements
- [x] Yield% below threshold (5%) for exhaustive level
- [x] Disconfirmation attempted for P0 dimensions
- [x] Adversarial pass completed (all 7 lenses)
- [x] Fixes applied to skill and references
- [x] Exit Gate criteria satisfied
- [x] Full report written to artifact location
- [x] Chat contains brief summary only
