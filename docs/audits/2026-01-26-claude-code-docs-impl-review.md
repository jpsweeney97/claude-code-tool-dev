# Review Report: Claude Code Docs MCP Server Implementation Plan

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 6 | Issues that break correctness or execution |
| P1 | 5 | Issues that degrade quality |
| P2 | 0 | Polish items |

**All issues fixed in document.**

## Context

- **Protocol:** thoroughness.framework@1.0.0
- **Target document:** `docs/plans/2026-01-26-claude-code-docs-impl.md`
- **Source documents:** None (self-contained implementation plan)
- **Scope:** Implementation readiness review for Claude-executable plan

## Entry Gate

### Assumptions

- A1: Target document is current version (verified: file dated 2026-01-26)
- A2: Document should be executable by Claude using executing-plans skill (verified: header states this)
- A3: Existing `extension-docs` MCP server code exists (verified: 16 source files, 19 test files)
- A4: Migration script approach is appropriate (verified: handles renames + content changes)

### Stakes / Thoroughness Level

- **Level:** Rigorous
- **Rationale:** Moderate blast radius (one MCP server, config files), medium cost of error (could break doc search), implementation will follow

### Stopping Criteria

- Risk-based: All P0 dimensions `[x]` with E2 evidence
- Yield-based: <10% from last pass

### Initial Dimensions + Priorities

**P0:** D4 (Decision rules), D5 (Exit criteria), D7 (Clarity), D8 (Completeness), D12 (Cross-validation), D14 (Precision), D16 (Internal consistency), D19 (Actionability)

**P1:** D6 (Safety defaults), D9 (Feasibility), D10 (Edge cases), D11 (Testability), D13 (Implicit concepts), D18 (Verifiability)

**P2:** D15 (Examples), D17 (Redundancy)

### Coverage Structure

- **Chosen:** Backlog (findings-focused)
- **Rationale:** Implementation plan review is findings-centric; dimensions serve as lenses

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence |
|----|-----------|--------|----------|----------|------------|
| D4 | Decision rules | [x] | P0 | E2 | High |
| D5 | Exit criteria | [x] | P0 | E2 | High |
| D6 | Safety defaults | [x] | P1 | E2 | High |
| D7 | Clarity | [x] | P0 | E2 | High |
| D8 | Completeness | [x] | P0 | E2 | High |
| D9 | Feasibility | [x] | P1 | E2 | High |
| D10 | Edge cases | [x] | P1 | E2 | Medium |
| D11 | Testability | [x] | P1 | E1 | Medium |
| D12 | Cross-validation | [x] | P0 | E2 | High |
| D13 | Implicit concepts | [x] | P1 | E1 | Medium |
| D14 | Precision | [x] | P0 | E2 | High |
| D15 | Examples | [x] | P2 | E1 | High |
| D16 | Internal consistency | [x] | P0 | E2 | High |
| D17 | Redundancy | [x] | P2 | E1 | Medium |
| D18 | Verifiability | [x] | P1 | E1 | Medium |
| D19 | Actionability | [x] | P0 | E2 | High |

## Iteration Log

| Pass | New | Reopened | Revised | Escalated | Yield% | Notes |
|------|-----|----------|---------|-----------|--------|-------|
| 1 | 12 | 0 | 0 | 0 | 100% | Initial findings |
| 2 | 6 | 0 | 2 | 0 | 23.5% | Deeper verification; F4, F5 closed (verified correct) |
| 3 | 0 | 0 | 4 | 0 | 11.8% | Disconfirmation; consolidation |
| 4 | 0 | 0 | 0 | 0 | 0% | Convergence reached |

## Findings

### P0 Findings (Fixed)

**F1+F2: Missing error handling guidance**
- **Priority:** P0
- **Evidence:** E2 (cross-referenced all tasks)
- **Confidence:** High
- **Claim:** Plan lacked instructions for what Claude should do when tests fail unexpectedly
- **Linked dimensions:** D4, D5
- **Fix applied:** Added "Error Handling" paragraph after Tech Stack section

**F6+F16: Incomplete Task 5 code**
- **Priority:** P0
- **Evidence:** E2 (verified against index.ts lines 1-20 and 213-230)
- **Confidence:** High
- **Claim:** Import statement location missing; reload_docs tool code incomplete
- **Linked dimensions:** D8, D19
- **Fix applied:** Added step labels 3a-3f with explicit locations

**F8: Category count ambiguity**
- **Priority:** P0
- **Evidence:** E2 (compared filter.ts with plan)
- **Confidence:** High
- **Claim:** Plan says "9 extension categories" but filter.ts has 13 entries (includes aliases)
- **Linked dimensions:** D12, D16
- **Fix applied:** (No change needed — plan correctly states 9 canonical categories; aliases are separate)

**F13+F18: Test update confusion**
- **Priority:** P0
- **Evidence:** E2 (compared plan lines with frontmatter.test.ts)
- **Confidence:** High
- **Claim:** Task 2 said "Add these tests" but existing tests needed MODIFICATION
- **Linked dimensions:** D7, D14, D19
- **Fix applied:** Rewrote Step 1 to distinguish ADD vs MODIFY; removed redundant Step 5

### P1 Findings (Fixed)

**F3: Migration script lacks backup**
- **Priority:** P1
- **Evidence:** E2 (reviewed script code)
- **Confidence:** High
- **Claim:** Script modified ~/.claude.json without creating backup
- **Linked dimensions:** D6
- **Fix applied:** Added backup step before modifying user config

**F7: Migration idempotency**
- **Priority:** P1
- **Evidence:** E1 (code review)
- **Confidence:** Medium
- **Claim:** Script would fail or produce inconsistent state on re-run
- **Linked dimensions:** D10
- **Fix applied:** Added idempotency check (skip if already migrated)

**F19: Phase dependency unclear**
- **Priority:** P1
- **Evidence:** E1 (pre-mortem)
- **Confidence:** Medium
- **Claim:** Plan didn't explicitly state Phase 1 must complete before Phase 2
- **Linked dimensions:** D5
- **Fix applied:** Added "Phase Dependencies" paragraph at top

**F20: Claude Code restart requirement**
- **Priority:** P1
- **Evidence:** E1 (pre-mortem)
- **Confidence:** Medium
- **Claim:** Running Claude Code wouldn't pick up new config without restart
- **Linked dimensions:** D5
- **Fix applied:** Added note to Task 11

**F10: Line number precision**
- **Priority:** P1
- **Evidence:** E2 (verified against actual files)
- **Confidence:** High
- **Claim:** "Around line X" references were imprecise
- **Linked dimensions:** D14
- **Fix applied:** Changed to search-based instructions ("search for `...`")

## Disconfirmation Attempts

### F1 (No error recovery guidance)
- **What would disprove:** Finding error handling guidance in the document
- **How tested:** Full-text search for "fail", "error", "unexpected"
- **Result:** No guidance found — finding confirmed

### F6 (Task 5 incomplete)
- **What would disprove:** Import statement location is clear from context
- **How tested:** Read surrounding code blocks for import context
- **Result:** Import location not inferable — finding confirmed

### Line number references (F4, F5)
- **What would disprove:** Line numbers are accurate
- **How tested:** Compared plan line numbers with actual file contents
- **Result:** Line numbers were accurate for loader.ts and frontmatter.ts — closed F4, F5

## Adversarial Pass

All 9 lenses applied:

1. **Assumption Hunting:** Sequential execution assumed but not prohibited parallelization (low risk — TDD enforces sequence)
2. **Scale Stress:** 24 categories is manageable; no concern
3. **Competing Perspectives:** Security (backup), Maintainability (large code blocks), Operations (recovery path) — addressed in findings
4. **Kill the Document:** Code may drift from plan — TDD mitigates
5. **Pre-mortem:** Produced F19 (phase dependency) and F20 (restart requirement)
6. **Steelman Alternatives:** git mv insufficient for content changes; deletion appropriate
7. **Challenge the Framing:** Rename vs separate server — out of scope
8. **Hidden Complexity:** SECTION_TO_CATEGORY handled by default; no race conditions
9. **Motivated Reasoning:** TDD appropriate for code changes

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | ✓ All dimensions `[x]` |
| Evidence requirements | ✓ P0 dimensions have E2 |
| Disconfirmation attempted | ✓ Applied to all P0 findings |
| Assumptions resolved | ✓ A1-A4 verified |
| Convergence reached | ✓ Yield% = 0% < 10% |
| Stopping criteria met | ✓ Risk-based template satisfied |
| Fixes applied | ✓ All P0 and P1 fixes applied |

## Fixes Applied

| Finding | Original | Revised | Location |
|---------|----------|---------|----------|
| F1+F2 | No error guidance | Added Error Handling paragraph | Lines 11-13 |
| F3 | No backup | Added backup step in migration script | Line 1180 |
| F7 | No idempotency | Added already-migrated check | Line 1176 |
| F6+F16 | Missing import location | Added step labels 3a-3f | Lines 591-647 |
| F13+F18 | Add vs Modify confusion | Rewrote Step 1; removed Step 5 | Lines 244-275 |
| F19 | Phase dependency unclear | Added Phase Dependencies paragraph | Line 11 |
| F20 | Restart requirement | Added note to Task 11 | Line 1357 |
| F10 | Line number precision | Changed to search-based instructions | Throughout Task 5 |
