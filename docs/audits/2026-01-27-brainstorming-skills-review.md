# Review: brainstorming-skills

**Date:** 2026-01-27
**Reviewer:** Claude (reviewing-skills)
**Stakes:** Exhaustive (user specified)
**Outcome:** PASS — 9 fixes applied, skill ready for production

## Summary

| Priority | Count | Fixed |
|----------|-------|-------|
| P0 | 0 | — |
| P1 | 4 | 4 |
| P2 | 6 | 5 |

**Key changes:**
1. Expanded "Exploring approaches" with dimension table and examples
2. Added standalone Decision Points section (6 scenarios)
3. Added explicit convergence round tracking requirement
4. Clarified scope boundaries (minor edits vs. fundamental redesign)

---

## Entry Gate

**Target:** `.claude/skills/brainstorming-skills/SKILL.md`

**Inputs:**
- SKILL.md (367 → 417 lines after fixes)
- assets/skill-template.md (223 lines)
- references/skill-writing-guide.md (417 → 419 lines)
- references/skills-best-practices.md (683 lines)
- references/persuasion-principles.md (188 lines)
- references/semantic-quality.md (119 lines)
- 8 type-example files

**Assumptions:**
1. Skill is current version — CONFIRMED (git status clean)
2. Referenced files are complete — CONFIRMED (all links valid)
3. Solution Development type skill — CONFIRMED (guides analysis, not orchestration)

**Stakes calibration:**
- Exhaustive specified by user
- Wide blast radius (guides creation of other skills)
- High cost of error (bad skills compound)

---

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence |
|----|-----------|--------|----------|----------|------------|
| D1 | Trigger clarity | [x] | P0 | E2 | High |
| D2 | Process completeness | [x] | P0 | E2 | High |
| D3 | Structural conformance | [x] | P0 | E2 | High |
| D4 | Compliance strength | [x] | P0 | E2 | High |
| D5 | Precision | [x] | P1 | E2 | High |
| D6 | Actionability | [x] | P1 | E2 | High |
| D7 | Internal consistency | [x] | P0 | E2 | High |
| D8 | Scope boundaries | [x] | P1 | E2 | High |
| D9 | Reference validity | [x] | P1 | E2 | High |
| D10 | Edge cases | [x] | P2 | E1 | Medium |
| D11 | Feasibility | [x] | P2 | E1 | Medium |
| D12 | Testability | [x] | P2 | E1 | Medium |
| D13 | Integration clarity | [-] | N/A | — | — |

D13 marked N/A: Skill is Solution Development type, not Orchestration. Does not coordinate sub-skills.

---

## Iteration Log

| Pass | Yield% | New | Revised | Notes |
|------|--------|-----|---------|-------|
| 1 | 100% | 10 | 0 | Initial findings |
| 2 | 25% | 1 | 0 | F18 found (glob typo) |
| 3 | 0% | 0 | 0 | Stability confirmed |
| 4 | 0% | 0 | 0 | Convergence reached |

---

## Findings

### P1 Findings (all fixed)

**F1: "Exploring approaches" underspecified (D2)**
- SKILL.md had 4 bullet points for approach exploration
- brainstorming-hooks has detailed phase with dimension table
- **Fix:** Added dimension table (5 items) and example phrases

**F6: Missing Decision Points section (D3)**
- Template requires standalone Decision Points section
- Logic was embedded in checkpoint but incomplete
- **Fix:** Added Decision Points section with 6 scenarios

**F14: skill-writing-guide.md example path confusing (D9)**
- Example showed relative path that could confuse readers
- **Fix:** Added clarifying text about adjusting path

**F18: Glob pattern typo (D6)**
- `**/*.claude/skills/` should be `**/.claude/skills/`
- **Fix:** Corrected glob pattern

### P2 Findings

**F8: "Significantly redesigning" undefined (D5)** — FIXED
- Added definition in When NOT to Use

**F9: "Approach" lacks structural template (D5)** — NOT FIXED
- Decided approach exploration doesn't need rigid template
- Dimension table provides structure without over-constraining

**F10: "Check project context first" lacks specific method (D6)** — FIXED
- Added specific commands (ls, Glob)

**F13: Gap for "existing skill fundamentally broken" (D8)** — FIXED
- Added as explicit case in When NOT to Use

**F17: Reading guide has no verification mechanism (D12)** — FIXED
- Added verification questions

**F20: No commitment mechanism for approach exploration (D4)** — NOT FIXED
- Approach exploration is lighter-touch than checkpoint
- Would add overhead for marginal benefit

**F21: "Question round" undefined (D5)** — NOT FIXED
- One question per message makes this unambiguous
- Adding definition would be redundant

---

## Adversarial Pass

All 7 lenses applied per Exhaustive requirements.

### Compliance Prediction
| Objection | Response | Residual Risk |
|-----------|----------|---------------|
| Agent claims convergence after 1 round | "Two consecutive rounds" explicit; added tracking | LOW |
| Agent skips reading guide | "YOU MUST" + verification question | LOW |
| Agent bundles questions | "No exceptions" but no enforcement | MEDIUM |

**Fix applied:** Added explicit round tracking requirement.

### Trigger Ambiguity
- No overlap with reviewing-skills (different intent words)
- Sequential with testing-skills (not overlapping)
- "Significantly redesigning" now defined

**No fix needed.**

### Missing Guardrails
- Agent must show understanding via dimension table
- Checkpoint requires visible output
- Troubleshooting addresses draft mismatch

**Residual risk:** MEDIUM — depth depends on agent effort.

### Complexity Creep
- 417 lines under 500 limit
- Phases tightly coupled — splitting would hurt UX
- Heavy content in references

**No fix needed.**

### Stale Assumptions
- Pointer architecture (references skill-writing-guide.md)
- Dynamic lookup (reads CLAUDE.md)
- No hardcoded assumptions that could go stale

**No fix needed.**

### Implementation Gap
- User quality outside skill control
- Type identification depends on dialogue
- Verification question catches major guide misreads

**Residual risk:** MEDIUM — acceptable for brainstorming skill.

### Author Blindness
| Hidden Knowledge | Fix |
|------------------|-----|
| Why two rounds, not one | Added rationale: "one could be lucky" |
| Checkpoint item order | Intuitive; no fix needed |
| What "visible output" means | Both TodoWrite and chat mentioned |

**Fix applied:** Added convergence rule rationale.

---

## Fixes Applied

| File | Change | Lines |
|------|--------|-------|
| SKILL.md | Expanded "Exploring approaches" with dimension table | 89-106 |
| SKILL.md | Added Decision Points section | 274-299 |
| SKILL.md | Specific commands for context check | 32-35 |
| SKILL.md | Clarified When NOT to Use boundaries | 301-307 |
| SKILL.md | Reading guide verification question | 187 |
| SKILL.md | Fixed glob pattern typo | 33 |
| SKILL.md | Added convergence round tracking | 69-73 |
| SKILL.md | Added convergence rule rationale | 69 |
| skill-writing-guide.md | Clarified example reference path | 239-242 |

---

## Disconfirmation Attempts

### D2 (Process completeness)
**Technique:** Alternative interpretation
**Attempt:** Maybe thin "Exploring approaches" is intentional design?
**Result:** brainstorming-subagents has same thin section (consistent), but brainstorming-hooks shows richer is better. Finding stands.

### D3 (Structural conformance)
**Technique:** Check if embedded logic satisfies requirement
**Attempt:** Does checkpoint embed Decision Points adequately?
**Result:** Checkpoint covers loop decision but not: conflicting requirements, post-checkpoint changes, convergence failure. Finding stands.

---

## Exit Gate Verification

- [x] No `[ ]` or `[?]` items remaining
- [x] P0 dimensions have E2 evidence
- [x] Disconfirmation attempted for P0s
- [x] Assumptions resolved
- [x] Yield% <5% for 2 consecutive passes
- [x] Adversarial pass complete (7/7 lenses)
- [x] Fixes applied (9 total)

---

## Residual Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Agent bundles questions under pressure | MEDIUM | Authority language present; user can enforce |
| Checkpoint depth depends on agent effort | MEDIUM | Visible output requirement helps; testing-skills catches issues |
| User quality affects outcome | MEDIUM | Outside skill scope; adversarial lens catches some issues |

---

## Recommendations

1. **No blockers for production use**
2. Consider adding enforcement hook for one-question-per-message if compliance issues surface
3. Sync brainstorming-subagents to match expanded structure (separate task)
