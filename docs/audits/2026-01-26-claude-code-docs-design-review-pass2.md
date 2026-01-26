# Review Report: Claude Code Docs MCP Server Design (Pass 2)

**Document:** `docs/plans/2026-01-24-claude-code-docs-design.md`
**Review Date:** 2026-01-26
**Stakes Level:** Rigorous
**Reviewer:** Claude (reviewing-documents skill)
**Prior Review:** `docs/audits/2026-01-25-claude-code-docs-design-review.md`

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | Issues that break correctness or execution |
| P1 | 1 | Issues that degrade quality |
| P2 | 2 | Polish items |

**All findings have been fixed.**

---

## Entry Gate

### Inputs
- **Target document:** `docs/plans/2026-01-24-claude-code-docs-design.md`
- **Source documents:** None (design derived from existing codebase)
- **Prior review:** `docs/audits/2026-01-25-claude-code-docs-design-review.md` (26 findings, all fixed)

### Scope
| Category | Included | Rationale |
|----------|----------|-----------|
| Document Quality (D13-D19) | Yes | Mandatory |
| Cross-validation (D12) | Yes | Mandatory |
| Source Coverage (D1-D3) | No | No separate source documents |
| Behavioral Completeness (D4-D6) | Yes | Document will be implemented |
| Implementation Readiness (D7-D11) | Yes | Document will be implemented |

### Assumptions
1. Existing codebase at `packages/mcp-servers/extension-docs/` is authoritative for current state
2. Prior review's fixes were applied to the document
3. Official Claude Code docs structure at docs.anthropic.com matches what's described

### Stakes Assessment
- Reversibility: Moderate (migration affects multiple files, user configs)
- Blast radius: Moderate (MCP server, settings, agents, skills)
- Cost of error: Medium (broken search, failed migrations)
- Uncertainty: Low (codebase visible, prior review exists)

**Level:** Rigorous

### Stopping Criteria
- Primary: Yield% < 10%

---

## Coverage Tracker

### Document Quality (Mandatory)

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D13 | Implicit concepts | [x] | — | E1 | High | BM25 now defined |
| D14 | Precision | [x] | P1 | E2 | High | Hook script action imprecise — **Fixed** |
| D15 | Examples | [x] | — | E2 | High | SECTION_TO_CATEGORY complete |
| D16 | Internal consistency | [x] | P2 | E1 | High | "(if exists)" qualifier inconsistent — **Fixed** |
| D17 | Redundancy | [x] | — | E1 | High | No redundancy issues |
| D18 | Verifiability | [x] | — | E1 | Medium | Exit criteria clear |
| D19 | Actionability | [x] | P2 | E1 | High | corpus-validation claim inaccurate — **Fixed** |

### Cross-validation (Mandatory)

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D12 | Cross-validation | [x] | — | E2 | High | Verified against codebase |

### Behavioral Completeness

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D4 | Decision rules | [x] | — | E1 | High | Clear phase structure |
| D5 | Exit criteria | [x] | — | E1 | High | Each phase has exit criterion |
| D6 | Safety defaults | [x] | — | E1 | High | Dry-run default, atomic writes |

### Implementation Readiness

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D7 | Clarity | [x] | — | E2 | High | Clear and specific |
| D8 | Completeness | [x] | — | E2 | High | All files identified |
| D9 | Feasibility | [x] | — | E2 | High | All referenced files exist |
| D10 | Edge cases | [x] | — | E1 | Medium | Addressed in Risks table |
| D11 | Testability | [x] | — | E1 | Medium | Verification steps in Phase 3 |

---

## Iteration Log

| Pass | Focus | P0 Found | P1 Found | P2 Found | Yield% |
|------|-------|----------|----------|----------|--------|
| 1 | Cross-validation with codebase | 0 | 1 | 2 | 13% |
| 2 | Post-fix verification | 0 | 0 | 0 | 0% |

**Convergence reached at Pass 2 (Yield% = 0% < 10% threshold)**

---

## Findings

### P1 Findings (Fixed)

**F31: Hook script content update missing from scope**
- Line 265 said "Rename script (if exists)" for `~/.claude/hooks/extension-docs-reminder.sh`
- The script outputs JSON containing old tool names (`search_extension_docs`, `reload_extension_docs`)
- After migration, these tool names become `search_docs` and `reload_docs`
- Missing content update would cause hook to give incorrect instructions post-migration
- **Fix:** Expanded scope entry to include content updates for tool names and server name

### P2 Findings (Fixed)

**F32: Skill entry missing "(if exists)" qualifier**
- Line 263 for `~/.claude/skills/extension-docs/` didn't have "(if exists)" qualifier
- The skill doesn't exist in production yet — only repo-local version exists
- Inconsistent with hook entry (line 265) which had "(if exists)"
- **Fix:** Added "(if exists)" for consistency

**F33: corpus-validation.test.ts update claim inaccurate**
- Line 222 said "Update expected category list" for `corpus-validation.test.ts`
- The test file doesn't contain a category list — it tests chunk size bounds
- **Fix:** Changed to "No category changes needed (tests chunk size bounds, not categories)"

---

## Disconfirmation Attempts

### P1 Dimensions

| Finding | Technique | Result |
|---------|-----------|--------|
| F31 | Read hook script content | Confirmed: script contains old tool names in JSON output |

### Adversarial Pass

| Lens | Applied | Finding |
|------|---------|---------|
| Assumption Hunting | Yes | Key assumptions identified and mitigated |
| Scale Stress | Yes | No issues at 10x/100x scale |
| Competing Perspectives | Yes | Operations concern (config migration) addressed by atomic writes |
| Kill the Document | Yes | Search dilution concern mitigated by category filter |
| Pre-mortem | Yes | Silent failure risk from hook script — now fixed (F31) |
| Steelman Alternatives | Yes | Two-server approach correctly rejected |
| Challenge the Framing | Yes | Expanding to all docs is correct direction |
| Hidden Complexity | Yes | Hook script content complexity — now explicit |
| Motivated Reasoning | Yes | No evidence found |

---

## Fixes Applied

| Finding | Change | Location |
|---------|--------|----------|
| F31 | Expanded hook script scope to include content updates | Migration Scope table, line 265 |
| F32 | Added "(if exists)" qualifier | Migration Scope table, line 263 |
| F33 | Changed corpus-validation.test.ts description | Tests to Update table, line 222 |

---

## Exit Gate Verification

| Criterion | Status |
|-----------|--------|
| Coverage complete | [x] No [ ] or [?] remaining |
| Evidence requirements met | [x] E2 for P0 dimensions, E1+ for P1 |
| Disconfirmation attempted | [x] P1 verified via file read |
| Assumptions resolved | [x] All listed and addressed |
| Convergence reached | [x] Yield% = 0% < 10% |
| Adversarial pass complete | [x] All 9 lenses applied |
| Fixes applied | [x] All findings fixed |

---

## Relationship to Prior Review

This review is a follow-up pass to `docs/audits/2026-01-25-claude-code-docs-design-review.md`.

The prior review found 5 P0, 18 P1, and 3 P2 issues — all reportedly fixed. This review:
1. Verified fixes were applied (spot-checked key findings)
2. Found 3 additional issues missed by prior review
3. Applied fixes for all new findings

The new findings (F31-F33) were not in the prior review's scope because:
- F31: Hook script file wasn't read during prior review
- F32, F33: Minor consistency issues that become visible on re-read

---

## Recommendations

1. **Test hook script after migration** — After running the migration script, verify the hook's JSON output references the new tool names.

2. **Consider adding golden query for hook content** — A test case that verifies the hook script content would catch future drift.
