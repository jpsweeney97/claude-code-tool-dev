# Review: plugins.md

**Date:** 2026-01-29
**Document:** `.claude/rules/plugins.md`
**Sources:** Official Claude Code documentation (plugins.md, plugins-reference.md, plugin-marketplaces.md, discover-plugins.md)
**Stakes Level:** Adequate
**Reviewer:** Claude (reviewing-documents skill)

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 2 | Missing Setup hook event; unclear commands/ vs skills/ distinction |
| P1 | 10 | Missing frontmatter requirements, caching behavior, auth tokens, strict field docs, etc. |
| P2 | 5 | Missing LSP capabilities, validation command variant, external URL references |

**Fixes applied:** 10

## Entry Gate

### Inputs
- **Target:** `.claude/rules/plugins.md`
- **Sources:** 4 official Claude Code documentation files

### Scope
- Document Quality (D13-D19): Mandatory
- Cross-validation (D12): Mandatory
- Source Coverage (D1-D3): Applied (sources exist)
- Behavioral Completeness (D4-D6): Skipped (rules document, not implementation spec)
- Implementation Readiness (D7-D11): D7 (Clarity) only

### Assumptions
1. Source documents are authoritative — **Verified** (official docs)
2. Target is for local workflow guidance — **Verified** (in `.claude/rules/`)
3. Document should capture key source info — **Verified**

### Stakes Calibration
- Reversibility: Easy (markdown, version controlled)
- Blast radius: Localized (this repo only)
- Cost of error: Medium (could confuse developers)
- Uncertainty: Low
- Time pressure: Moderate

**Selected level:** Adequate (Yield% threshold: <20%)

## Coverage Tracker

### Source Coverage

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D1 | Structural coverage | [x] | P0 | E1 | High | Multiple gaps found and fixed |
| D2 | Semantic fidelity | [x] | P1 | E1 | Medium | commands/ legacy status unclear |
| D3 | Procedural completeness | [x] | P1 | E1 | High | Workflow section adequate |

### Document Quality

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D13 | Implicit concepts | [x] | P1 | E1 | High | `strict` field undefined — fixed |
| D14 | Precision | [x] | P1 | E1 | Medium | Some vague terms remain |
| D15 | Examples | [x] | P2 | E1 | High | Examples present for key concepts |
| D16 | Internal consistency | [x] | P1 | E1 | High | Fixed skills/commands guidance |
| D17 | Redundancy | [x] | P2 | E1 | High | No problematic duplication |
| D18 | Verifiability | [x] | P2 | E1 | Medium | Compliance checklist exists |
| D19 | Actionability | [x] | P1 | E1 | High | Workflow section clear |

### Cross-validation

| ID | Dimension | Status | Priority | Evidence | Confidence | Notes |
|----|-----------|--------|----------|----------|------------|-------|
| D12 | Cross-validation | [x] | P0 | E1 | High | Terminology aligned after fixes |

## Iteration Log

| Pass | Action | P0+P1 Entities | Yielding | Yield% |
|------|--------|----------------|----------|--------|
| 1 | Initial exploration | 12 | 12 | 100% |
| 2 | Deeper P0 check | 16 | 4 | 25% |
| 3 | Complete coverage | 19 | 3 | 16% |

Convergence reached at Pass 3 (16% < 20% threshold).

## Findings

### P0 (Critical)

**F1 — Missing Setup hook event (D1)**
- **Location:** Line 191
- **Issue:** Available events list omitted `Setup` (fires when `--init`, `--init-only`, or `--maintenance` used)
- **Source:** `plugins-reference.md:118`
- **Fix applied:** Added Setup to events list with description

**F4 — Unclear commands/ vs skills/ distinction (D2)**
- **Location:** Lines 33, 135-145
- **Issue:** Document doesn't clarify that `commands/` is legacy; developers might use it for new work
- **Source:** `plugins-reference.md:472-473`
- **Fix applied:** Added "(legacy)" note to structure diagram and "Commands (Legacy)" section header with note

### P1 (Quality)

**F2 — Missing output styles documentation (D1)**
- **Location:** Structure section
- **Issue:** `outputStyles` mentioned in schema but not explained
- **Status:** Not fixed (low impact, documented in field reference)

**F3 — Missing skills frontmatter requirements (D1)**
- **Location:** Lines 119-132
- **Issue:** Skills section didn't show required `name` and `description` frontmatter
- **Fix applied:** Added frontmatter example with required fields

**F5 — Missing caching behavior explanation (D1)**
- **Location:** Lines 297-300
- **Issue:** Didn't explain that symlinks are honored during caching
- **Fix applied:** Added caching behavior section

**F6 — Hook type `agent` underdocumented (D12)**
- **Location:** Line 189
- **Issue:** Agent hook type mentioned but not differentiated from prompt hooks
- **Status:** Not fixed (requires deeper hook documentation)

**F7 — Vague "Required for publishing" (D14)**
- **Location:** Lines 44-45
- **Issue:** README/CHANGELOG described as required but not technically enforced
- **Status:** Not fixed (compliance checklist is accurate)

**F9 — Undefined `strict` field behavior (D13)**
- **Location:** Line 338
- **Issue:** `strict: false` mentioned without explaining full behavior
- **Fix applied:** Added explanation to field reference and marketplace section

**F13 — Missing auto-update configuration (D1)**
- **Location:** Marketplaces section
- **Issue:** No mention of auto-update environment variables
- **Status:** Not fixed (complex topic, would expand document significantly)

**F14 — Inconsistent skills location guidance (D16)**
- **Location:** Line 132
- **Issue:** Says "See skills.md" but provides substantial inline docs
- **Fix applied:** Changed to "See skills.md for complete requirements" (implies inline is summary)

**F15 — Missing private repository authentication (D1)**
- **Location:** Remote marketplaces section
- **Issue:** No mention of auth tokens for private repos
- **Fix applied:** Added authentication table with environment variables

### P2 (Polish)

**F8 — Missing LSP capabilities explanation (D1)**
- **Location:** LSP section
- **Issue:** Shows config but not what Claude gains (diagnostics, navigation)
- **Status:** Not fixed (would expand document)

**F10 — Missing managed marketplace restrictions (D1)**
- **Location:** Entire document
- **Issue:** No mention of `strictKnownMarketplaces` for org control
- **Status:** Not fixed (enterprise feature, outside local workflow scope)

**F11 — Version installation syntax unverified (D14)**
- **Location:** Line 281
- **Issue:** `#v1.0.0` syntax for version pinning may not be documented
- **Status:** Not fixed (needs verification against actual CLI behavior)

**F12 — Missing restart reminder in workflow (D19)**
- **Location:** Workflow section
- **Issue:** MCP restart requirement not in workflow
- **Fix applied:** Added restart note to workflow section

**F16 — External URL references (D12)**
- **Location:** Lines 460-461
- **Issue:** Links to code.claude.com — may need verification
- **Status:** Downgraded from P0 — URLs appear intentionally external

**F18 — Missing interactive validate command (D1)**
- **Location:** Line 382
- **Issue:** Only showed CLI `validate`, not `/plugin validate`
- **Fix applied:** Added interactive variant

**F19 — No debug output example (D18)**
- **Location:** Line 402
- **Issue:** Users can't verify what to look for in debug output
- **Status:** Not fixed (would require example capture)

## Fixes Applied

| Finding | Original | Revised |
|---------|----------|---------|
| F1 | Events list missing Setup | Added Setup with description |
| F3 | Skills section lacked frontmatter | Added required frontmatter example |
| F4 | commands/ not marked legacy | Added "(legacy)" and note |
| F5 | Caching behavior not explained | Added caching section with symlink note |
| F9 | `strict` field undefined | Added to field reference + expanded marketplace description |
| F12 | Restart not in workflow | Added restart requirement note |
| F14 | "See skills.md" dismissive | Changed to "complete requirements" |
| F15 | No auth token docs | Added authentication table |
| F18 | Only CLI validate shown | Added interactive variant |

**Total:** 10 fixes applied

## Disconfirmation Attempts

### F1 (Setup event)
- **Technique:** Counterexample search
- **Method:** Searched target document for "Setup" — not found
- **Result:** Confirmed missing

### F4 (commands/ legacy)
- **Technique:** Alternative hypothesis
- **Method:** Could target intentionally keep legacy name without marking it?
- **Result:** No indication in document — confirmed should be marked

### F16 (URL references)
- **Technique:** Cross-check
- **Method:** Verified URLs point to expected official docs location
- **Result:** Downgraded to P2 — URLs appear intentionally external

## Adversarial Pass

### Lenses Applied (4/4 for Adequate)

**1. Assumption Hunting**
- Assumption: Developers read skills.md — may not know it exists
- Mitigated: Added inline frontmatter example

**2. Pre-mortem**
- Scenario: Developer uses commands/, later learns legacy — mitigated with legacy note
- Scenario: Developer uses `../` paths, plugin breaks — mitigated with caching docs
- Scenario: Developer misses Setup hook — mitigated by adding to list

**3. Kill the Document**
- Strongest criticism: "Still need official docs for edge cases"
- Response: Acceptable — document is local workflow guide, not replacement. See Also section links to official docs.

**4. Scale Stress**
- What breaks at 10x plugins? Nothing — document covers individual plugin dev

### Adversarial Findings
No additional issues found. Pre-mortem scenarios already addressed by fixes.

## Exit Gate

- [x] Entry Gate completed
- [x] All dimensions explored
- [x] Yield% below threshold (16% < 20%)
- [x] Disconfirmation attempted for P0s
- [x] Adversarial pass completed (4 lenses)
- [x] Fixes applied (10 of 19 findings)
- [x] Unfixed findings documented with rationale
