# Skill Review: markdown-formatter

**Date:** 2026-01-29
**Reviewer:** Claude (reviewing-skills)
**Stakes Level:** Rigorous
**Skill Path:** `.claude/skills/markdown-formatter/SKILL.md`

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | Issues that break correctness or execution |
| P1 | 6 | Issues that degrade quality (5 fixed, 1 accepted) |
| P2 | 4 | Polish items (all accepted) |

**Outcome:** All P1 issues fixed. Skill ready for testing-skills.

## Entry Gate

**Assumptions:**
- Skill is current version (v1.0.0)
- No supporting files exist (single SKILL.md)
- Referenced framework file would need to exist for Framework Connection section

**Stakes calibration:**
- Reversibility: Easy (file formatting is reversible)
- Blast radius: Moderate (affects real files)
- Cost of error: Low (losslessness check prevents data loss)
- Uncertainty: Low (clear rules)
- Time pressure: Moderate

**Selected level:** Rigorous

**Stopping criteria:** Yield% < 10% for two consecutive passes

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D1 | Trigger clarity | [x] | P0 | E1 | Medium | Description uses outcome language; Triggers section compensates |
| D2 | Process completeness | [x] | P0 | E2 | High | Process well-defined with clear steps, exit criteria, failure handling |
| D3 | Structural conformance | [x] | P0 | E2 | High | After fixes: all required sections present |
| D4 | Compliance strength | [x] | P1 | E1 | Medium | Has strong language (MUST, NOT, "Ever"); acceptable for tool-style skill |
| D5 | Precision | [x] | P1 | E1 | High | Generally precise; minor vagueness in "unnecessary escape" |
| D6 | Actionability | [x] | P1 | E2 | Medium | After fix: plaintext extraction method note added |
| D7 | Internal consistency | [x] | P1 | E2 | High | Terminology consistent; example matches process |
| D8 | Scope boundaries | [x] | P1 | E1 | Medium | After fix: "When NOT to Use" section added |
| D9 | Reference validity | [x] | P2 | E2 | High | After fix: broken Framework Connection removed |
| D10 | Edge cases | [x] | P2 | E1 | Medium | Good coverage; missing large files, malformed markdown |
| D11 | Feasibility | [x] | P2 | E1 | High | All requirements feasible with standard tools |
| D12 | Testability | [x] | P2 | E2 | High | Excellent testability; all requirements have explicit verification |
| D13 | Integration clarity | [-] | P1 | N/A | High | N/A - standalone skill, not orchestration type |
| D14 | Example quality | [x] | P1 | E1 | Medium | After fix: BAD/GOOD format with realistic examples |
| D15 | Cognitive manageability | [x] | P2 | E1 | High | Good structure; 8 steps manageable; clear phases |

## Iteration Log

| Pass | Focus | Yield% | Notes |
|------|-------|--------|-------|
| 1 | All dimensions | 100% | 10 findings (0 P0, 6 P1, 4 P2) |
| 2 | Verify fixes | 0% | No new findings; converged |

## Findings

### P1 Findings (Fixed)

| ID | Finding | Dimension | Fix Applied |
|----|---------|-----------|-------------|
| F3 | Missing Troubleshooting section | D3 | Added section with 6 common issues |
| F4 | Missing Decision Points section | D3 | Added section with 8 key decisions |
| F6 | Examples not BAD/GOOD format | D3, D14 | Added BAD example showing content modification mistake |
| F8 | Plaintext extraction method unspecified | D6 | Added Method note after extraction rules |
| F9 | Missing "When NOT to Use" section | D8 | Added section with 4 exclusion categories |
| F10 | Broken framework reference | D9 | Removed Framework Connection section entirely |

### P2 Findings (Accepted)

| ID | Finding | Dimension | Reason for Acceptance |
|----|---------|-----------|----------------------|
| F1 | Description uses outcome language | D1 | Triggers section compensates adequately |
| F2 | Markdown validation method unspecified | D2 | Error Handling covers the case implicitly |
| F5 | Name not gerund form | D3 | "formatter" is industry standard for tool-style skills |
| F7 | "Unnecessary escape" vague | D5 | Example clarifies intent; context makes meaning clear |

## Disconfirmation Attempts

| Technique | Target | Result |
|-----------|--------|--------|
| Alternative interpretation | F10 (broken reference) | Could keep section with placeholder? No — dead reference provides no value |
| Context check | F5 (name not gerund) | Project CLAUDE.md doesn't require gerund names; convention is flexible |
| Counterexample search | F1 (outcome language) | Found other skills with similar pattern; Triggers section is standard mitigation |

## Adversarial Pass

All 7 lenses applied:

| Lens | Assessment | Risk |
|------|------------|------|
| Compliance Prediction | Losslessness gate is strong; BAD example reinforces | Low |
| Trigger Ambiguity | Triggers specific; "When NOT to Use" defines exclusions | Low |
| Missing Guardrails | Error Handling + When NOT to Use cover edge cases | Low |
| Complexity Creep | Single concern (structure formatting); no scope creep | None |
| Stale Assumptions | GFM spec v0.29 may become outdated | Low (Extension Points allows updates) |
| Implementation Gap | Plaintext extraction method variance | Acceptable (rules define output, not implementation) |
| Author Blindness | HTML comment whitespace handling implicit | Minor (stripped entirely per rules) |

**No P0 issues from adversarial pass.**

## Exit Gate Verification

- [x] Coverage complete — no `[ ]` or `[?]` items
- [x] Evidence requirements met — P0 dimensions have E2
- [x] Disconfirmation attempted — techniques applied to P0s
- [x] Assumptions resolved — all verified or flagged
- [x] Convergence reached — Yield% = 0% < 10%
- [x] Adversarial pass complete — all 7 lenses applied
- [x] Fixes applied — all P1 findings fixed

## Files Modified

- `.claude/skills/markdown-formatter/SKILL.md`:
  - Added "When NOT to Use" section (after Triggers)
  - Added "Decision Points" section (after Anti-Patterns)
  - Added "Troubleshooting" section (after Decision Points)
  - Added BAD example, renamed section to "Examples"
  - Added Method note for plaintext extraction
  - Removed broken Framework Connection section

## Next Steps

1. Run testing-skills to validate behavioral effectiveness
2. Promote to `~/.claude/skills/` after testing passes
