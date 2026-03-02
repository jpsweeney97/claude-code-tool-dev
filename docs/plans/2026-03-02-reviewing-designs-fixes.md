# Reviewing-Designs Skill: Fix Design

**Date:** 2026-03-02
**Source:** Adversarial Codex dialogue (5-turn, converged)
**Approach:** Surgical edits (Approach A) — fix each finding in-place with minimal structural changes
**Target:** SKILL.md 546→~484 lines (under 500-line cap)

## Findings Summary

| # | Severity | Finding | Fix |
|---|----------|---------|-----|
| 1 | P0 | Broken protocol link at line 17 | Fix filename |
| 2 | P0 | Contradictory dimension logic (D12 mandatory vs. "just review it" excludes it) | Change shortcut to D4-D19 |
| 3 | P0 | Adversarial lenses unindexed (9 lenses, no IDs, no completion schema) | Add A1-A9 IDs |
| 4 | P0 | Anti-shortcut controls placed 300 lines after steps they protect | Inline top-3 guards |
| 5 | Emerged | Metric gaming via priority downgrades enables false convergence | Add downgrade rule |
| 6 | P1 | Line count 546 > 500 limit | Merge Verification into Exit Gate, move example to references |
| 7 | — | Yield% formula differs from framework | Align with framework formula |
| 8 | — | Description missing WHAT capability statement | Add to frontmatter |
| 9 | — | Stakes override conflict unspecified in Extension Points | Add resolution rule |

## Fix Specifications

### Fix 1: Broken protocol link
- **Line 17:** `references/framework-for-thoroughness.md` → `references/framework-for-thoroughness_v1.0.0.md`

### Fix 2: Description missing WHAT
- **Line 3:** Prepend "Iterative design review using the Framework for Thoroughness." before existing trigger phrases

### Fix 3: "Just review it" dimension contradiction
- **Line 343:** Replace "Proceed with Implementation Readiness and Document Quality dimensions only" with "Proceed with D4-D19 (Behavioral Completeness through Document Quality); mark D1-D3 as `[-]` with rationale: no source documents specified"

### Fix 4: Adversarial lens IDs
- **Lines 293-309:** Add A1-A9 IDs to lens name column
- After table, add completion schema: "Record lens ID, objection, response, and residual risk for each applied lens. Verify count matches stakes requirement."

### Fix 5: Anti-shortcut inline guards
- **After EXPLORE (~line 218):** Add two STOP-CHECK guards:
  1. Completeness vs. presence check
  2. N/A dimension justification check
- **After VERIFY (~line 243):** Add one STOP-CHECK guard:
  3. Genuine disconfirmation check

### Fix 6: Metric gaming mitigation
- **In REFINE, after Yield% formula:** Add priority downgrade rule requiring evidence + justification, tracking in iteration log

### Fix 7: Yield% formula alignment
- **Line 258:** Replace `yielding entities / total P0+P1 entities` with `|Y| / max(1, |U|)` where `U = E_prev ∪ E_cur`
- Add note that union denominator prevents denominator shrinkage

### Fix 8: Merge Verification into Exit Gate
- **Lines 470-521:** Remove standalone Verification section
- Merge unique checklist items into Exit Gate as post-completion self-check
- Saves ~45 lines

### Fix 9: Move example to references
- **Lines 386-448:** Move BAD/GOOD example to `references/examples.md`
- Replace with link: "See [Review Examples](references/examples.md) for BAD vs. GOOD comparison."
- Saves ~55 lines

### Fix 10: Stakes override conflict resolution
- **Extension Points section:** Add conflict resolution: state concrete risk delta, record accepted risk, proceed with user's choice

## Implementation Order

1. Fix 9 (move example — creates `references/examples.md`, largest line reduction)
2. Fix 8 (merge Verification into Exit Gate — second largest line reduction)
3. Fix 1 (broken link — 1-line fix)
4. Fix 2 (description — 1-line fix)
5. Fix 3 (dimension contradiction — 1-line fix)
6. Fix 7 (Yield% formula — small edit in REFINE)
7. Fix 6 (metric gaming — add to REFINE after Yield%)
8. Fix 4 (lens IDs — table modification)
9. Fix 5 (inline guards — add after EXPLORE and VERIFY)
10. Fix 10 (stakes override — add to Extension Points)

Order rationale: line-reducing fixes first (to create budget), then content fixes, then additions.

## Verification

After all fixes:
- [ ] SKILL.md under 500 lines
- [ ] All internal links resolve
- [ ] Description includes WHAT + WHEN + trigger phrases
- [ ] No contradictions between dimension applicability rules and decision paths
- [ ] Adversarial lenses have A1-A9 IDs
- [ ] STOP-CHECK guards present after EXPLORE and VERIFY
- [ ] Yield% formula matches framework
- [ ] Metric gaming downgrade rule present
- [ ] Verification section removed (merged into Exit Gate)
- [ ] Example moved to references/examples.md
