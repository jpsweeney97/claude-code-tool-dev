# Review Report: Brainstorming-Skills Redesign Proposal

**Document:** `docs/plans/2026-01-29-brainstorming-skills-redesign.md`
**Reviewed:** 2026-01-29
**Stakes:** Rigorous
**Reviewer:** Claude (reviewing-documents skill)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 10 | Issues that break correctness or execution |
| P1 | 8 | Issues that degrade quality |
| P2 | 2 | Polish items |

**Recommendation:** The redesign has sound principles but significant gaps in actionability. Address P0 findings before implementation.

---

## Entry Gate

**Target:** `docs/plans/2026-01-29-brainstorming-skills-redesign.md`

**Sources:**
- `.claude/skills/brainstorming-skills/SKILL.md` (current skill being replaced)
- `.claude/rules/skills.md` (constraints)
- `.claude/skills/brainstorming-skills/skill-writing-guide.md` (referenced guide)

**Assumptions:**
1. Redesign proposal is current working version
2. Current skill represents baseline to preserve
3. skills.md rules are authoritative

**Stakes:** Rigorous
- Moderate undo cost (skill creates other skills — errors cascade)
- Moderate blast radius (affects skill ecosystem)
- Medium cost of error

**Stopping Criteria:** Yield% <10%

---

## Coverage Tracker

| ID | Dimension | Priority | Status | Evidence | Confidence |
|----|-----------|----------|--------|----------|------------|
| D1 | Structural coverage | P1 | [x] | E2 | High |
| D2 | Semantic fidelity | P0 | [x] | E2 | High |
| D3 | Procedural completeness | P0 | [x] | E2 | High |
| D4 | Decision rules | P0 | [x] | E2 | High |
| D5 | Exit criteria | P0 | [x] | E2 | High |
| D6 | Safety defaults | P1 | [x] | E2 | High |
| D7 | Clarity | P1 | [x] | E1 | Medium |
| D12 | Cross-validation | P0 | [x] | E2 | High |
| D13 | Implicit concepts | P1 | [x] | E1 | Medium |
| D14 | Precision | P1 | [x] | E2 | High |
| D15 | Examples | P2 | [x] | E2 | Medium |
| D16 | Internal consistency | P0 | [x] | E2 | High |
| D17 | Redundancy | P2 | [x] | E1 | High |
| D18 | Verifiability | P1 | [x] | E1 | Medium |
| D19 | Actionability | P0 | [x] | E2 | High |

---

## Iteration Log

| Pass | Entities | Yielding | Yield% | Notes |
|------|----------|----------|--------|-------|
| 1 | 14 | 14 | 100% | Initial findings |
| 2 | 19 | 5 | 26% | Safety, clarity, precision |
| 3 | 21 | 3 | 14% | Verification, cross-checks |
| 4 | 23 | 2 | 8.7% | Final verification, below threshold |

---

## Findings

### P0: Critical (blocks correctness or execution)

**F1: Type-based section guidance not fully migrated**
- **Dimension:** D2 (Semantic fidelity)
- **Location:** Lines 379-384 vs current SKILL.md 242-255
- **Issue:** Proposal eliminates 8-type taxonomy but current skill uses types to guide which sections to emphasize. The mined patterns (lines 499-547) exist but are marked "to inline" — not yet incorporated.
- **Fix:** Incorporate approach patterns from Content Mining Analysis into Phase 3 before implementation.

**F3: Phase 1 exit criteria undefined**
- **Dimension:** D3 (Procedural completeness)
- **Location:** Lines 114-117
- **Issue:** "Problem space understood" is subjective. Current skill has 7 concrete dimensions. What specifically must be known before surfacing approaches?
- **Fix:** Add checklist: "Understood when: (1) problem statement articulated, (2) current failure mode identified, (3) success criteria roughed out."

**F4: Assumption gates lack pass/fail criteria**
- **Dimension:** D3 (Procedural completeness)
- **Location:** Lines 196-205
- **Issue:** Gates are prompts ("looks similar to X?") not checklists. What if no similar pattern exists? What constitutes passing?
- **Fix:** For each gate: (1) when to invoke, (2) specific questions, (3) what constitutes passing/failing.

**F5: Phase 2 decision rules incomplete**
- **Dimension:** D4 (Decision rules)
- **Location:** Lines 136-141
- **Issue:** No guidance for: user defers choice ("you decide"), user's choice seems wrong, user wants more exploration.
- **Fix:** Add decision rules from current skill (lines 308-327) adapted for new flow.

**F8: Scenario verification failure handling undefined**
- **Dimension:** D5 (Exit criteria)
- **Location:** Lines 221-224
- **Issue:** "Return to questions" doesn't specify: what resets, which questions, how to identify wrong understanding.
- **Fix:** Define restart semantics: "Wrong prediction → identify which dimension was misunderstood → re-explore that dimension only → re-run affected scenarios."

**F9: "Approach" terminology inconsistent**
- **Dimension:** D12 (Cross-validation)
- **Location:** Lines 93, 127, 157
- **Issue:** Three different meanings: design dimensions (93), template selection (127), phase-specific dimensions (157).
- **Fix:** Rename line 93 "design dimensions"; reserve "approach" for Reference/Task/Methodology only.

**F11: Missing Rationalizations section contradicts guide**
- **Dimension:** D16 (Internal consistency)
- **Location:** Line 446 vs skill-writing-guide.md 139-159
- **Issue:** Proposal says "Rationalizations table NOT needed" but guide says discipline-enforcing skills SHOULD include it. Brainstorming IS discipline-enforcing.
- **Fix:** Either add Rationalizations section OR justify why this methodology skill is an exception.

**F13: Stress-test questions lack action guidance**
- **Dimension:** D19 (Actionability)
- **Location:** Lines 275-286
- **Issue:** Questions listed but no guidance on: what's a concerning answer, what action to take, how to determine severity.
- **Fix:** For each question: good answer looks like X, concerning answer looks like Y, if concerning → action Z.

**F24: No mechanism ensures approach-specific dimensions are sufficient**
- **Dimension:** Adversarial (Pre-mortem)
- **Issue:** Old skill's 7 universal dimensions ensured coverage. New approach-specific dimensions may miss cross-cutting concerns.
- **Fix:** Add a "cross-cutting sanity check" that applies regardless of approach (e.g., "Have you checked for conflicts with existing skills?").

**F18: "Problem space understood" vague**
- **Dimension:** D14 (Precision)
- **Location:** Lines 62-63, 115
- **Issue:** No definition of what constitutes understanding. "3-5 questions typically" isn't a specification.
- **Fix:** Define minimum: problem statement, failure mode, success criteria (rough).

### P1: Quality Issues

**F2: Question discipline rule weakened without justification**
- **Location:** Lines 186-190 vs current line 37
- **Issue:** Changed from "YOU MUST" to "Default... Exception allowed" without explaining why the exception is safe.
- **Fix:** Add rationale OR preserve absolute rule.

**F6: Iteration severity levels not precisely defined**
- **Location:** Lines 350-355
- **Issue:** Examples given but no decision test to distinguish Minor from Moderate.
- **Fix:** Add decision criteria: "Minor = doesn't change skill structure. Moderate = changes structure but not approach."

**F7: Phase 3 exit criteria mixes process and verification**
- **Location:** Lines 228-233
- **Issue:** Process compliance (dimensions, gates) combined with verification (scenarios, user confirmation).
- **Fix:** Restructure: "Process complete when [1-2]. Verified when [3-4]."

**F12: Implementation depends on content not yet in proposal**
- **Location:** Lines 451-456, 499-556
- **Issue:** Checklist says "inline patterns" but patterns are in analysis section, not proposal body.
- **Fix:** Mark implementation as blocked until patterns are incorporated OR incorporate them now.

**F14: Design context template missing required fields**
- **Location:** Lines 292-319
- **Issue:** Template lacks: verification scenarios, stress-test findings (shown at 305-318 but as prose examples, not template fields).
- **Fix:** Add as required template sections.

**F15: No guidance for contradictory requirements**
- **Location:** Missing (current skill lines 320-323)
- **Issue:** User provides conflicting requirements — no handling.
- **Fix:** Add to Phase 3: "If requirements conflict → surface tension, ask to prioritize, document trade-off."

**F16: Approach dimensions don't distinguish required vs optional**
- **Location:** Lines 160-183
- **Issue:** "Focus on:" suggests emphasis, not requirement. Which are mandatory?
- **Fix:** Mark each dimension Required/Recommended/Optional.

**F20: Pre-draft checklist references file without confirming it's retained**
- **Location:** Lines 243-245
- **Issue:** References skill-writing-guide.md but file disposition unclear from proposal.
- **Fix:** Explicitly list skill-writing-guide.md as "Keep" in implementation checklist.

### P2: Polish

**F10: Template name format inconsistent**
- **Location:** Lines 127-131 vs current 190-193
- **Issue:** Missing `.md` suffix in some references.
- **Fix:** Use `.md` suffix consistently.

**F23: Comparison table is meta-commentary**
- **Location:** Lines 573-583
- **Issue:** "Old vs New" is proposal context, not skill guidance.
- **Fix:** Mark as "proposal-only, remove from SKILL.md".

### Informational (not issues)

**F17:** Scenario types (success/edge/failure) could use selection criteria but this is minor.

**F19:** Scenario verification is harder to audit than "two no-yield rounds" but the trade-off is intentional.

**F21:** Open Questions resolutions could cite verification evidence but resolutions appear sound.

**F22:** No worked example is noted but "Examples NOT needed" is an intentional design choice.

**F25:** Complexity escalation could be added but scenario verification may catch this naturally.

**F26:** Line count concern is speculative; verify after implementation.

---

## Adversarial Pass

### Pre-mortem
> "The redesigned skill failed. What happened?"

Scenario verification passed with narrow scenarios, missing edge cases the old 7-dimension exploration would have caught. → **F24 addresses this.**

### Kill the Document
> "Strongest argument against?"

Optimizes for simple skills; complex skills may suffer without escalation path. The 8-type taxonomy was "overhead" for simple cases but "necessary coverage" for complex ones.

### Competing Perspectives

- **Maintainability:** Inlining patterns reduces file count but increases SKILL.md size. Trade-off seems acceptable if under 500 lines.
- **Operations:** Scenario verification is harder to audit than convergence rounds. Consider requiring documented scenarios.

### Challenge the Framing

The proposal assumes the 8-type taxonomy adds no value. But type-based section guidance (current lines 242-255) DOES affect the process. This is captured in F1.

### Motivated Reasoning

The proposal may be anchored on "simplification is good." The removal of Examples, Anti-Patterns, Troubleshooting, and Rationalizations sections represents significant reduction. For a discipline-enforcing skill, these sections have value. F11 captures the Rationalizations concern.

---

## Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Coverage complete | ✅ | All 15 dimensions checked, no [ ] or [?] |
| Evidence requirements | ✅ | E2 for all P0 dimensions |
| Disconfirmation | ✅ | Attempted for F1, F3, F4, F9 |
| Yield% below threshold | ✅ | 8.7% < 10% |
| Adversarial pass complete | ✅ | 9 lenses applied |

---

## Recommendations

### Before Implementation

1. **Incorporate mined patterns** (F1, F12) — Move approach-specific patterns from Content Mining Analysis into Phase 3 body
2. **Define Phase 1 exit criteria** (F3, F18) — What specifically must be understood?
3. **Specify gate pass/fail criteria** (F4) — Each gate needs trigger, questions, pass condition
4. **Add decision rules** (F5, F15) — Port relevant rules from current skill
5. **Define restart semantics** (F8) — What resets on scenario failure?
6. **Fix terminology** (F9) — "Approach" means one thing only
7. **Resolve Rationalizations contradiction** (F11) — Include section OR justify exception
8. **Add stress-test action guidance** (F13) — What to do with answers?
9. **Add cross-cutting sanity check** (F24) — Ensure approach-specific dimensions don't miss universal concerns

### Consider

- Preserving Examples section with at least one worked example of the new flow
- Keeping Anti-Patterns/Troubleshooting in some form (compressed)
- Documenting scenarios for auditability (F19)

### Implementation Blockers

The proposal cannot be implemented until F1 and F12 are resolved (patterns not yet incorporated).
