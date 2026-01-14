# Deep-Exploration Skill Audit Report

**Skill:** `.claude/skills/deep-exploration/SKILL.md`
**Version:** 1.3.0
**Audit Date:** 2026-01-11
**Specifications:**
- `skills-as-prompts-strict-spec.md` (structural requirements)
- `skills-semantic-quality-addendum.md` (semantic quality)

---

## Executive Summary

**Disposition: PASS-WITH-NOTES**

The skill meets all MUST-level structural requirements. It has strong verification, comprehensive troubleshooting, and excellent decision point coverage. However, several SHOULD-level semantic gaps and one borderline structural issue warrant attention.

---

## Structural Compliance (skills-as-prompts-strict-spec.md)

### Required Content Areas (8-section contract)

| Section | Status | Location | Notes |
|---------|--------|----------|-------|
| When to use | ✅ PASS | Lines 19-29 | 6 clear triggers |
| When NOT to use | ✅ PASS | Lines 32-36 | 5 explicit boundaries |
| Inputs | ✅ PASS | Lines 69-88 | Required/Optional/Constraints all present |
| Outputs | ✅ PASS | Lines 92-105 | Artifacts + 5 objective DoD checks |
| Procedure | ⚠️ PASS | Lines 122-203 | Phases with embedded numbered steps |
| Decision points | ✅ PASS | Lines 229-244 | 5 explicit If/then/otherwise |
| Verification | ✅ PASS | Lines 246-263 | Quick check + deep checks |
| Troubleshooting | ✅ PASS | Lines 395-449 | 4 entries with symptoms/causes/next steps |

### Reviewer Checklist Results

| Check ID | Requirement | Status | Evidence |
|----------|-------------|--------|----------|
| CHECK.required-content-areas | All 8 areas findable | ✅ PASS | All sections present within 60s scan |
| CHECK.outputs-have-objective-dod | Artifacts + objective DoD | ✅ PASS | Lines 94-105: 5 checkbox-style objective checks |
| CHECK.procedure-numbered-with-stop-ask | Numbered procedure + STOP/ask | ✅ PASS | Phases numbered; STOP in lines 86-88 |
| CHECK.two-decision-points-or-exception | ≥2 decision points | ✅ PASS | 5 decision points (lines 234-244) |
| CHECK.verification-has-quick-check | Concrete quick check | ✅ PASS | Lines 250-254: grep commands with expected "0" |
| CHECK.troubleshooting-present | ≥1 failure mode | ✅ PASS | 4 comprehensive entries |
| CHECK.assumptions-declared-with-fallback | Assumptions + fallback | ⚠️ PARTIAL | Assumptions declared; fallback incomplete |

### Automatic FAIL Conditions

| Fail Code | Condition | Status |
|-----------|-----------|--------|
| FAIL.missing-content-areas | Required areas absent | ✅ NOT TRIGGERED |
| FAIL.no-objective-dod | No objective DoD | ✅ NOT TRIGGERED |
| FAIL.no-stop-ask | No STOP/ask behavior | ✅ NOT TRIGGERED |
| FAIL.no-quick-check | No concrete quick check | ✅ NOT TRIGGERED |
| FAIL.too-few-decision-points | <2 decision points | ✅ NOT TRIGGERED |
| FAIL.undeclared-assumptions | Assumptions undeclared | ✅ NOT TRIGGERED |
| FAIL.unsafe-default | Destructive without ask-first | ✅ NOT TRIGGERED (read-only skill) |
| FAIL.non-operational-procedure | Not numbered/executable | ✅ NOT TRIGGERED |

---

## Semantic Quality Assessment (skills-semantic-quality-addendum.md)

### Semantic Minimums (NORMATIVE)

| Minimum | Status | Evidence | Gap |
|---------|--------|----------|-----|
| 1) Intent fidelity | ⚠️ PARTIAL | Description exists (lines 3-7, 16-17) | No explicit "Primary goal:" statement; "When NOT to use" lists activation boundaries, not scope non-goals |
| 2) Constraint completeness | ⚠️ PARTIAL | Constraints in lines 82-85 | Missing: explicit read-only constraint; no fallback for opus requirement |
| 3) Observable decision triggers | ⚠️ PARTIAL | Most are observable | "ambiguous" (line 234) and "unclear" (line 244) are subjective |
| 4) Verification validity | ⚠️ PARTIAL | Measures matrix completeness | Measures process compliance, not primary outcome (understanding quality) |
| 5) Calibration honesty | ⚠️ PARTIAL | Confidence levels (lines 218-227) | No "Not run (reason)" instruction |

### Dimension Scoring (0-2 scale, guidance)

| Dimension | Score | Notes |
|-----------|-------|-------|
| A) Intent fidelity | 1 | Has intent, lacks explicit primary goal + non-goals |
| B) Constraint completeness | 1 | Constraints declared; fallbacks incomplete |
| C) Terminology clarity | 2 | Key terms well-defined (lines 218-227, matrix symbols) |
| D) Evidence anchoring | 2 | Strong: every finding requires source citation |
| E) Decision sufficiency | 2 | 5 decision points covering major branches |
| F) Verification validity | 1 | Quick check measures process, not outcome |
| G) Artifact usefulness | 2 | Clear artifact structure and format |
| H) Minimality discipline | 2 | Read-only; no scope creep risk |
| I) Calibration honesty | 1 | Has confidence levels; lacks "Not run" handling |
| J) Offline/restricted handling | 1 | Says "not required" but no fallback guidance |

**Total: 15/20** (Good, but below "Excellent" threshold of 16 with no 0s)

---

## Detailed Findings

### Finding 1: Missing Explicit Non-Goals (SHOULD-level)

**Location:** "When NOT to use" section (lines 32-36)

**Issue:** The section lists *activation boundaries* (when to skip the skill) rather than *scope non-goals* (what the skill will NOT do even when activated).

**Current:**
```markdown
- Quick answer suffices
- Scope is narrow and well-defined
- Time pressure prohibits rigor
...
```

**Expected (per semantic spec section `semantic.minimums.intent-and-non-goals`):**
```markdown
## Non-goals
- Will not modify any files (read-only exploration)
- Will not execute code or run tests
- Will not make recommendations without evidence
- Will not expand scope beyond defined boundaries
```

**Severity:** Low (SHOULD-level gap)

**Recommendation:** Add a "Non-goals" section or append explicit scope constraints to "When NOT to use."

---

### Finding 2: Subjective Decision Triggers (SHOULD-level)

**Location:** Decision Points section (lines 234, 244)

**Issue:** Two decision points rely on subjective judgment rather than observable signals.

**Current:**
- Line 234: "If scope is **ambiguous** or unbounded"
- Line 244: "If calibration level is **unclear**"

**Expected (per `semantic.minimums.observable-decision-points`):**
```markdown
If scope crosses more than 3 top-level directories or the user cannot name a specific deliverable, then STOP...
If the user has not specified calibration and stakes are not obvious from context, then default to Medium.
```

**Severity:** Low (SHOULD-level; current wording is functional)

**Recommendation:** Add concrete observable triggers for "ambiguous" and "unclear."

---

### Finding 3: Missing Fallback for Model Requirement (SHOULD-level)

**Location:** Inputs → Constraints (line 82)

**Issue:** The skill requires `opus` model but provides no fallback or STOP behavior if a different model is active.

**Current:**
```markdown
- Model: `opus` required for depth (agents use Explore type)
```

**Expected (per strict spec `spec.required-content-contract.allowed-omissions` and command mention rule):**
```markdown
- Model: `opus` required for depth. If using a different model, STOP and warn:
  "This skill requires opus for reliable multi-agent exploration.
   Proceed with reduced confidence, or switch models."
```

**Severity:** Medium (affects reliability if invoked with wrong model)

**Recommendation:** Add explicit fallback behavior or STOP condition for non-opus models.

---

### Finding 4: Verification Measures Process, Not Outcome (SHOULD-level)

**Location:** Verification section (lines 250-254)

**Issue:** The quick check verifies matrix completeness (process compliance), not the primary success property (exploration produced useful, accurate findings).

**Current:**
```bash
grep -c '\[ \]' deliverable.md  # Expected: 0
```

**Expected (per `semantic.minimums.verification-validity`):**
```markdown
## Verification

**Quick check (process):** Matrix has no `[ ]` or `[?]` cells.
**Quick check (outcome):** Sample 2 findings and confirm evidence exists at cited locations.
```

The Deep Check section (lines 258-262) does address outcome verification, but it's marked optional.

**Severity:** Low (Deep Check covers this; marking it optional is the issue)

**Recommendation:** Promote "Sample 3-5 findings" from Deep Check to required Quick Check, or add outcome-focused quick check.

---

### Finding 5: Missing "Not Run" Labeling Instruction (SHOULD-level)

**Location:** Throughout procedure and verification

**Issue:** The skill doesn't instruct the agent to label skipped verification with `Not run (reason)`.

**Expected (per `semantic.minimums.calibration`):**
```markdown
If verification was skipped, report:
Not run (reason): <reason>. Run: `<command>` to verify manually.
```

**Severity:** Low (affects audit trail for incomplete explorations)

**Recommendation:** Add "Not run" labeling instruction to Verification section.

---

### Finding 6: Read-Only Constraint Not Explicit (SHOULD-level)

**Location:** Inputs → Constraints (lines 82-85)

**Issue:** The skill is fundamentally read-only (uses Explore agents, no Write operations), but this isn't explicitly stated as a constraint.

**Expected (per `semantic.minimums.constraints`):**
```markdown
**Constraints:**
- **Read-only:** This skill does not modify files, run code, or make changes
- Model: opus required
...
```

**Severity:** Low (implicit from agent type, but explicit is better)

**Recommendation:** Add explicit read-only constraint.

---

### Finding 7: Procedure Structure (Informational)

**Location:** Lines 122-203

**Observation:** The procedure uses a 4-phase structure with embedded numbered steps within Phase 2 and Phase 3. This is unconventional but compliant—the spec allows "equivalent structure" if information is findable.

The Quick Start section (lines 39-54) provides a condensed numbered version that helps.

**Status:** Compliant; no action needed.

---

## Anti-Pattern Check

| Anti-Pattern | Present? | Evidence |
|--------------|----------|----------|
| Over-broad activation | No | Clear When/When NOT sections |
| Implicit assumptions | Partial | Assumes opus without fallback |
| Premature solutioning | No | Inspect-first via Pre-Flight and agents |
| Scope creep | No | Read-only; explicit calibration |
| Verification theater | No | Concrete grep commands |
| Decision-point omission | No | 5 explicit decision points |
| Unsafe default | No | Read-only skill |
| Unrecoverable procedure | No | 4 troubleshooting entries |
| Non-portable instructions | Partial | `grep` is portable; opus requirement isn't |

---

## Category Assessment

**Applicable category:** Auditing & Assessment (`category=auditing-assessment`)

Per the Category Tightening Matrix:
- Inputs: High → ✅ Met (comprehensive inputs section)
- Verification: High → ⚠️ Partial (process check; outcome is optional)
- Decision Points: High → ✅ Met (5 decision points)
- STOP/ask: High → ✅ Met (2 STOP conditions)
- Risk: Medium → ✅ Appropriate (read-only, no destructive actions)

---

## Risk Tier Assessment

**Determined tier:** Low-Medium

**Rationale:**
- Read-only exploration (no mutations)
- No destructive actions possible
- No external service dependencies
- Produces recommendations, doesn't execute them

**Tier minimums check:**
- All 8 sections: ✅
- Quick check: ✅
- Troubleshooting: ✅
- STOP/ask for missing inputs: ✅
- Non-goals against scope creep: ⚠️ Implicit only

---

## Summary of Gaps

| # | Finding | Severity | Spec Reference |
|---|---------|----------|----------------|
| 1 | Missing explicit non-goals | SHOULD | `semantic.minimums.intent-and-non-goals` |
| 2 | Subjective decision triggers | SHOULD | `semantic.minimums.observable-decision-points` |
| 3 | No fallback for opus requirement | SHOULD | `spec.required-content-contract.allowed-omissions` |
| 4 | Quick check measures process only | SHOULD | `semantic.minimums.verification-validity` |
| 5 | Missing "Not run" labeling | SHOULD | `semantic.minimums.calibration` |
| 6 | Read-only constraint implicit | SHOULD | `semantic.minimums.constraints` |

---

## Recommendations (Priority Order)

1. **Add model fallback** (Finding 3): Most impactful—prevents silent degradation if opus isn't available

2. **Add explicit non-goals section** (Finding 1): Prevents scope drift in future uses

3. **Add outcome-focused quick check** (Finding 4): Move sampling from optional Deep Check to required

4. **Add "Not run" instruction** (Finding 5): Improves audit trail

5. **Make observable triggers explicit** (Finding 2): Replace "ambiguous" with concrete test

6. **State read-only constraint** (Finding 6): Explicit is better than implicit

---

## Final Disposition

**PASS-WITH-NOTES**

The skill meets all MUST requirements in the strict spec. It has excellent structure, comprehensive troubleshooting, and strong decision point coverage. The gaps are all SHOULD-level semantic quality improvements that would elevate the skill from "good" to "excellent."
