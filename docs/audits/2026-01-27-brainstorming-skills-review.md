# Review Report: brainstorming-skills

**Date:** 2026-01-27
**Target:** `.claude/skills/brainstorming-skills/SKILL.md`
**Stakes:** Rigorous
**Protocol:** reviewing-skills

## Summary

| Priority | Count | Fixed |
|----------|-------|-------|
| P0 | 2 | 2 |
| P1 | 8 | 8 |
| P2 | 3 | 0 (accepted) |

**Key changes:**
- Added missing required sections (Examples, Anti-Patterns, Troubleshooting, When NOT to Use)
- Strengthened compliance language for core discipline (one question per message, assumption traps)
- Added rationalization table
- Removed broken reference link
- Added explicit enforcement for convergence gate and dimension coverage

**Reference updates (consistency fix):**
- Added rationalization table pattern to `references/skill-writing-guide.md` (Persuasion Principles section)
- Added "Rationalizations to Watch For" as optional section in `assets/skill-template.md`

## Entry Gate

**Target:** `.claude/skills/brainstorming-skills/SKILL.md` (278 lines pre-review)

**References inventory:**
| File | Status |
|------|--------|
| skill-writing-guide.md | Present |
| skills-best-practices.md | Present |
| persuasion-principles.md | Present |
| semantic-quality.md | Present |
| type-example-*.md (8 files) | Present |
| anthropic-skill-documentation.md | **Missing** (F4) |
| assets/skill-template.md | Present |

**Assumptions:**
1. Skill is current version — verified
2. Referenced files complete — verified (except F4)
3. Production skill — verified

**Stakes assessment:**
- Reversibility: Easy → Adequate
- Blast radius: Wide (meta-skill) → Exhaustive
- Cost of error: High → Exhaustive
- **Result: Rigorous** (two factors in higher column)

**Stopping criteria:** Yield% <10%

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D1 | Trigger clarity | [x] | P0 | E1 | High | Description follows trigger-only pattern |
| D2 | Process completeness | [x] | P0 | E2 | High | F1, F2 fixed |
| D3 | Structural conformance | [x] | P0 | E2 | High | F3, F10 fixed; F12, F13 accepted |
| D4 | Compliance strength | [x] | P1 | E2 | High | F5, F6, F7 fixed |
| D5 | Precision | [x] | P1 | E1 | High | F8 fixed |
| D6 | Actionability | [x] | P1 | E1 | High | F9 fixed |
| D7 | Internal consistency | [x] | P1 | E1 | High | No issues |
| D8 | Scope boundaries | [x] | P1 | E2 | High | F10 fixed |
| D9 | Reference validity | [x] | P0 | E2 | High | F4 fixed |
| D10 | Edge cases | [~] | P2 | E1 | Medium | F11 accepted as limitation |
| D11 | Feasibility | [x] | P2 | E1 | High | No issues |
| D12 | Testability | [x] | P2 | E1 | High | No issues |
| D13 | Integration clarity | [-] | — | — | — | N/A (not orchestration skill) |

## Iteration Log

| Pass | New Findings | Revised | Fixed | Yield% |
|------|--------------|---------|-------|--------|
| 1 | 11 (F1-F11) | 0 | 0 | 100% |
| 1 FIX | — | — | 10 | — |
| 2 | 2 (F12-F13) | 0 | 0 | 18% |
| 3 | 0 | 0 | 0 | 0% |
| Adversarial | 2 (F14-F15) | 0 | 1 | — |

**Convergence:** Reached at Pass 3 (Yield% = 0% < 10%)

## Findings

### P0 Findings

**F3 (D3): Missing required sections**
- Examples, Anti-Patterns, Troubleshooting, Decision Points (embedded only)
- **Fix:** Added Examples, Anti-Patterns, Troubleshooting sections with concrete content

**F4 (D9): Broken reference link**
- `references/anthropic-skill-documentation.md` does not exist
- **Fix:** Removed reference from References section

### P1 Findings

**F1 (D2): Dimensions table lacks tracking enforcement**
- **Fix:** Added "Use TodoWrite to track" instruction

**F2 (D2): No explicit convergence gate**
- **Fix:** Added "YOU MUST verify convergence before proceeding to the checkpoint"

**F5 (D4): "One question at a time" uses soft language**
- **Fix:** Changed to "**YOU MUST ask only one question per message**"

**F6 (D4): Assumption traps guidance lacks enforcement**
- **Fix:** Changed "ask anyway" to "**YOU MUST ask.** No exceptions."

**F7 (D4): No rationalization table**
- **Fix:** Added "Rationalizations to Watch For" section with 7 entries

**F8 (D5): "low-yield" imprecise**
- **Fix:** Changed to "yield nothing new"

**F9 (D6): "Check search results" vague**
- **Fix:** Changed to "Use Grep to search `.claude/skills/` for related terms"

**F10 (D8): Missing "When NOT to Use" section**
- **Fix:** Added section with 4 exclusions

**F14 (Adversarial): Dimensions table lacks explicit enforcement**
- **Fix:** Added "**YOU MUST** check all applicable dimensions before claiming convergence"

### P2 Findings (Accepted)

**F11 (D10): No guidance for abandoned brainstorms**
- Accepted as limitation; design context document can serve as progress checkpoint

**F12 (D3): Line count increased to 367**
- Informational; still under 500 limit

**F13 (D3): "When NOT to Use" section placement unconventional**
- Accepted; functional where placed

**F15 (Adversarial): No guidance on question quality**
- Accepted as limitation; examples implicitly demonstrate good questions

## Disconfirmation Attempts

### D1 (Trigger clarity)
- **Technique:** Alternative interpretation
- **Result:** Description is unambiguous; "significantly redesigning" could be subjective but "When NOT to Use" clarifies boundary

### D3 (Structural conformance)
- **Technique:** Cross-check with template
- **Result:** Post-fix, skill contains all required sections

### D9 (Reference validity)
- **Technique:** File existence check
- **Result:** All references verified except anthropic-skill-documentation.md (fixed)

## Adversarial Pass

| Lens | Objection | Response | Residual Risk |
|------|-----------|----------|---------------|
| Compliance Prediction | Dimensions table could be skipped | Added explicit enforcement (F14) | Low |
| Trigger Ambiguity | "significantly redesigning" vague | When NOT to Use clarifies | Low |
| Missing Guardrails | Infinite questions possible | Convergence rule addresses | Low |
| Complexity Creep | Could split into phases | Tightly coupled; splitting adds overhead | None |
| Stale Assumptions | Dependencies could change | References section makes explicit | Low |
| Implementation Gap | Question quality not evaluated | Examples demonstrate implicitly (F15 accepted) | Medium |
| Author Blindness | Assumes skill terminology | Linked references provide background | Low |

## Fixes Applied

| Finding | Original | Revised | File:Line |
|---------|----------|---------|-----------|
| F3 | (missing) | Added Examples, Anti-Patterns, Troubleshooting, When NOT to Use | SKILL.md:256-343 |
| F4 | `[references/anthropic-skill-documentation.md]` | Removed | SKILL.md (was 262) |
| F5 | "Ask questions one at a time" | "**YOU MUST ask only one question per message**" | SKILL.md:33 |
| F6 | "If any of these apply, ask anyway." | "**If any of these apply, YOU MUST ask.** No exceptions." | SKILL.md:48 |
| F7 | (missing) | Added "Rationalizations to Watch For" section | SKILL.md:331-343 |
| F8 | "two consecutive low-yield question rounds" | "two consecutive question rounds that yield nothing new" | SKILL.md:18 |
| F9 | "Check search results" | "Use Grep to search `.claude/skills/` for related terms" | SKILL.md:128 |
| F10 | (missing) | Added "When NOT to Use" section | SKILL.md:256-261 |
| F1 | (no tracking mention) | "Use TodoWrite to track:" | SKILL.md:72 |
| F2 | "Do not proceed to checkpoint until converged." | Added "**YOU MUST** verify convergence before proceeding" | SKILL.md:68 |
| F14 | "mark inapplicable ones as such and move on" | Added "**YOU MUST** check all applicable dimensions before claiming convergence" | SKILL.md:84 |

## Exit Gate

| Criterion | Evidence |
|-----------|----------|
| Coverage complete | All dimensions [x] or [~] with documented gaps |
| Evidence requirements met | P0: E2; P1: E1+ |
| Disconfirmation attempted | 3 P0 dimensions disconfirmed |
| Assumptions resolved | anthropic-skill-documentation.md fixed |
| Convergence reached | Pass 3 Yield% = 0% |
| Adversarial pass complete | 7/7 lenses applied |
| Fixes applied | 11/13 findings fixed (2 P2 accepted) |
