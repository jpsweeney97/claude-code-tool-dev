# Review Report: Claude Code Docs MCP Server Design (Pass 3)

**Document:** `docs/plans/2026-01-24-claude-code-docs-design.md`
**Review Date:** 2026-01-26
**Stakes Level:** Rigorous
**Reviewer:** Claude (reviewing-documents skill)
**Prior Reviews:**
- `docs/audits/2026-01-25-claude-code-docs-design-review.md` (26 findings)
- `docs/audits/2026-01-26-claude-code-docs-design-review-pass2.md` (3 findings)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 0 | Issues that break correctness or execution |
| P1 | 1 | Issues that degrade quality |
| P2 | 1 | Polish items |

**All findings have been fixed.**

---

## Entry Gate

### Inputs
- **Target document:** `docs/plans/2026-01-24-claude-code-docs-design.md`
- **Source documents:** Existing codebase at `packages/mcp-servers/extension-docs/`
- **Prior reviews:** 2 passes, 29 total findings, all reportedly fixed

### Scope
| Category | Included | Rationale |
|----------|----------|-----------|
| Document Quality (D13-D19) | Yes | Mandatory |
| Cross-validation (D12) | Yes | Mandatory — verify prior fixes and find missed issues |
| Source Coverage (D1-D3) | No | No separate source documents |
| Behavioral Completeness (D4-D6) | Yes | Document will be implemented |
| Implementation Readiness (D7-D11) | Yes | Document will be implemented |

### Assumptions
1. Existing codebase at `packages/mcp-servers/extension-docs/` is authoritative for current state
2. Prior review fixes were applied to the document
3. Official Claude Code docs structure at docs.anthropic.com matches what's described

### Stakes Assessment
- Reversibility: Moderate (migration affects multiple files, user configs)
- Blast radius: Moderate (MCP server, settings, agents, skills)
- Cost of error: Medium (broken search, failed migrations)
- Uncertainty: Low (codebase visible, two prior reviews exist)

**Level:** Rigorous

### Stopping Criteria
- Primary: Yield% < 10%

---

## Coverage Tracker

### Document Quality (Mandatory)

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D13 | Implicit concepts | [x] | — | E1 | High | BM25 defined after categories table |
| D14 | Precision | [x] | P1 | E2 | High | Skill prose refs incomplete — **Fixed** |
| D15 | Examples | [x] | — | E2 | High | SECTION_TO_CATEGORY complete |
| D16 | Internal consistency | [x] | — | E1 | High | Consistent style |
| D17 | Redundancy | [x] | — | E1 | High | No redundancy issues |
| D18 | Verifiability | [x] | — | E1 | Medium | Exit criteria clear |
| D19 | Actionability | [x] | P2 | E1 | High | settings.local.json clarification — **Fixed** |

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
| 1 | Cross-validation with codebase | 0 | 1 | 1 | 9% |
| 2 | Post-fix verification | 0 | 0 | 0 | 0% |

**Convergence reached at Pass 2 (Yield% = 0% < 10% threshold)**

---

## Findings

### P1 Findings (Fixed)

**F34: Skill prose references not in migration scope**
- Line 260 said "update name, tool references, and description" for `.claude/skills/extension-docs/`
- The skill file has prose references to "extension-docs MCP server" at lines 37 and 92
- Migration script wouldn't know to update prose without explicit instruction
- **Fix:** Expanded scope entry to include prose references in troubleshooting section

### P2 Findings (Fixed)

**F35: settings.local.json scope imprecise**
- Line 261 mentioned updating `mcp__extension-docs__search_extension_docs` permission
- Actual file only has `search_extension_docs` in permissions, not `reload_extension_docs`
- This is correct behavior but could confuse implementer who expects both
- **Fix:** Added note clarifying only `search_extension_docs` requires update

---

## Disconfirmation Attempts

### P1 Dimensions

| Finding | Technique | Result |
|---------|-----------|--------|
| F34 | Read skill file content | Confirmed: lines 37, 92 contain "extension-docs MCP server" |

### Adversarial Pass

| Lens | Applied | Finding |
|------|---------|---------|
| Assumption Hunting | Yes | Key assumptions remain valid |
| Scale Stress | Yes | No issues at 10x/100x scale |
| Competing Perspectives | Yes | No new issues |
| Kill the Document | Yes | Prior concerns adequately addressed |
| Pre-mortem | Yes | Skill prose refs would cause user confusion — fixed (F34) |
| Steelman Alternatives | Yes | Two-server approach correctly rejected |
| Challenge the Framing | Yes | Expanding to all docs remains correct direction |
| Hidden Complexity | Yes | Prose ref complexity now explicit |
| Motivated Reasoning | Yes | No evidence found |

---

## Fixes Applied

| Finding | Change | Location |
|---------|--------|----------|
| F34 | Expanded skill scope to include prose refs | Migration Scope table, line 260 |
| F35 | Added clarification about which permission needs update | Migration Scope table, line 261 |

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

## Relationship to Prior Reviews

This is the third review pass of this document:

| Pass | Date | Findings | Status |
|------|------|----------|--------|
| 1 | 2026-01-25 | 26 (5 P0, 18 P1, 3 P2) | All fixed |
| 2 | 2026-01-26 | 3 (0 P0, 1 P1, 2 P2) | All fixed |
| 3 | 2026-01-26 | 2 (0 P0, 1 P1, 1 P2) | All fixed |

**Total findings across all passes:** 31

The new findings (F34-F35) were not in prior reviews because:
- F34: Prior review checked agent file for prose refs but not skill file's troubleshooting section
- F35: Minor clarification that becomes relevant when implementing

---

## Verification Evidence

### Skill file prose references (F34 evidence)

```
.claude/skills/extension-docs/SKILL.md:37:- Requires extension-docs MCP server to be running
.claude/skills/extension-docs/SKILL.md:92:**Cause:** extension-docs MCP server not running or not configured
```

### settings.local.json content (F35 evidence)

```json
{
  "permissions": {
    "allow": [
      "mcp__extension-docs__search_extension_docs",
      "Bash(ls:*)"
    ]
  }
}
```

Note: Only `search_extension_docs` is in permissions, not `reload_extension_docs`.

---

## Recommendations

1. **Document is now implementation-ready** — After 31 findings across 3 passes, the design is comprehensive and accurate.

2. **Consider full grep after migration** — Run `grep -r "extension-docs" .` after applying migration to catch any straggler references.
