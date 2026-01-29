# Skills Rules Document Review

**Date:** 2026-01-29
**Target:** `.claude/rules/extensions/skills.md`
**Source:** `docs/claude-code-documentation/skills.md` (official Claude Code docs)
**Stakes:** Rigorous
**Reviewer:** Claude Opus 4.5

## Summary

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | 3     | Issues that break correctness or execution |
| P1       | 8     | Issues that degrade quality                |
| P2       | 4     | Polish items                               |

**Fixed:** 8 issues addressed in this review.

---

## Entry Gate

**Assumptions:**
1. Source documentation represents authoritative current state — **Verified** via MCP search
2. Target should serve as operational guidance for this repo — **Verified** by context
3. Target may include project-specific conventions beyond official docs — **Accepted**, but must be clearly marked

**Stakes assessment:** Rigorous
- Reversibility: Moderate (rules propagate to all skills)
- Blast radius: Moderate (all skill development in this repo)
- Cost of error: Medium (incorrect guidance leads to malformed skills)

**Stopping criteria:** Yield% <10%

---

## Coverage Tracker

### Source Coverage (D1-D3)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D1 | [x] | P1 | Missing "Types of skill content" section | Source lines 110-144 vs target | High |
| D1 | [x] | P2 | Missing troubleshooting section | Source lines 635-658 | High |
| D1 | [x] | P2 | Missing visual output example pattern | Source lines 446-631 | High |
| D2 | [x] | P0 | `name` field incorrectly marked as "Required" with "gerund form" | Source: "No" required, no gerund requirement | High |
| D2 | [x] | P0 | `license` and `metadata` frontmatter fields not in official docs | MCP search confirmed | High |
| D2 | [x] | P1 | Missing `$ARGUMENTS[N]` and `$N` indexed argument access | Source lines 183-185 | High |
| D2 | [x] | P2 | Description fallback behavior not mentioned | Source line 166 | Medium |
| D3 | [x] | - | Steps adequately specified | - | - |

### Behavioral Completeness (D4-D6)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D4 | [x] | - | Decision rules adequate | - | - |
| D5 | [x] | - | Exit criteria not applicable (reference doc) | - | - |
| D6 | [x] | - | Safety defaults adequate (permissions section) | - | - |

### Implementation Readiness (D7-D11)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D7 | [x] | P1 | "stdlib only" undefined in Structure table | Target line 41 | High |
| D7 | [x] | P1 | `once` hook attribute shown but not explained | Target line 105 | High |
| D8 | [x] | - | Components adequately covered | - | - |
| D9 | [x] | - | Dependencies exist (Claude Code features) | - | - |
| D10 | [x] | - | Edge cases not applicable (reference doc) | - | - |
| D11 | [x] | - | Testability not applicable | - | - |

### Consistency (D12)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D12 | [x] | - | Terminology consistent | Cross-section review | High |

### Document Quality (D13-D19)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D13 | [x] | P1 | "stdlib only" undefined | Target line 41 | High |
| D14 | [x] | P1 | "significantly exceeds ~500 lines" is vague | Target line 50 | Medium |
| D14 | [x] | P2 | "may be partially read" lacks trigger conditions | Target line 51 | Low |
| D15 | [x] | - | Examples adequate | - | - |
| D16 | [x] | - | Internal consistency adequate | - | - |
| D17 | [x] | - | Minor redundancy acceptable | - | - |
| D18 | [x] | P2 | "keep skills focused" is unverifiable | Target line 48 | Low |
| D19 | [x] | - | Actionability adequate for reference doc | - | - |

---

## Iteration Log

| Pass | Action | Findings | Yield% |
|------|--------|----------|--------|
| 1 | Initial source comparison + document quality | 10 findings (3 P0, 5 P1, 2 P2) | 100% |
| 2 | Deeper source verification via MCP | +4 findings, 1 revised | 27% |
| 3 | Document quality deep dive | +2 findings (P2) | 12% |
| 4 | Final verification | 0 new | 0% |

**Convergence:** Achieved at Pass 4 (Yield% 0%, below 10% threshold)

---

## Findings Detail

### P0 Findings (Fixed)

**F1: `name` field requirement incorrect**
- **Location:** Frontmatter section
- **Issue:** Target said "Required: kebab-case, gerund form (verb-ing)"
- **Source says:** "No" required, "Lowercase letters, numbers, and hyphens only"
- **Fix:** Changed to "Recommended" with gerund marked as project convention (📋)

**F2: Undocumented frontmatter fields**
- **Location:** Frontmatter example
- **Issue:** `license` and `metadata` fields not in official documentation
- **Evidence:** MCP search of skills documentation returned no results for these fields
- **Fix:** Removed both fields from example

**A1: No distinction between official and project conventions**
- **Location:** Throughout document
- **Issue:** Readers cannot distinguish Claude Code requirements from project preferences
- **Fix:** Added header note explaining 📋 marks project conventions

### P1 Findings (Fixed)

**F3: Missing "Types of skill content" section**
- **Location:** After Structure section
- **Issue:** Important design guidance from source not present
- **Fix:** Added "Types of Skill Content" section with reference/task distinction

**F4: Missing indexed argument access**
- **Location:** String Substitutions table
- **Issue:** `$ARGUMENTS[N]` and `$N` not documented
- **Fix:** Added both to table with descriptions

**F6: "stdlib only" undefined**
- **Location:** Structure table
- **Issue:** Term used without definition
- **Fix:** Removed; changed to "Utility scripts Claude can execute"

**F7: Vague line guidance**
- **Location:** Progressive Disclosure
- **Issue:** "significantly exceeds ~500 lines" not actionable
- **Fix:** Changed to "exceeds 500 lines" with concrete threshold

**F12: `once` hook attribute unexplained**
- **Location:** Hooks frontmatter example
- **Issue:** Shown in example but function not explained
- **Fix:** Added inline comment: "(skill hooks only, not agents)"

**A2: Missing reference to official docs**
- **Location:** Document header
- **Issue:** No pointer to complete official documentation
- **Fix:** Added link to https://code.claude.com/docs/en/skills

### P2 Findings (Not Fixed — Lower Priority)

**F8:** Description fallback behavior not mentioned
**F9:** Missing visual output example pattern
**F16:** "may be partially read" lacks trigger conditions
**F17:** "keep skills focused" is unverifiable guidance

---

## Adversarial Pass

### Lenses Applied

| Lens | Finding |
|------|---------|
| Assumption Hunting | Document assumes readers will check official docs — mitigated by adding explicit reference |
| Scale Stress | At 100 skills, line limits become critical — addressed with concrete 500-line threshold |
| Competing Perspectives | Maintainability concern: undocumented fields create confusion — addressed by removing them |
| Kill the Document | Mixed official/project content without distinction — addressed with 📋 marker system |
| Pre-mortem | "Developer thinks gerund naming is required by Claude Code" — addressed by marking as project convention |
| Steelman Alternatives | Separate documents considered; single source preferred with clear labeling |
| Challenge the Framing | Document purpose appropriate for repo |
| Hidden Complexity | Subagent integration is dense but adequate |
| Motivated Reasoning | Gerund preference and metadata fields may be personal style — removed metadata, marked gerund as preference |

---

## Disconfirmation Attempts

| Technique | Target | Result |
|-----------|--------|--------|
| Cross-check via MCP | `license`, `metadata` fields | Confirmed not in official docs |
| Cross-check via MCP | `once` hook attribute | Confirmed official, skill-only |
| Source comparison | Gerund requirement | Confirmed not in official docs |

---

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | ✓ No `[ ]` or `[?]` items |
| Evidence requirements met | ✓ E2 for P0 (source + MCP) |
| Disconfirmation attempted | ✓ 3 techniques on P0 findings |
| Assumptions resolved | ✓ All verified |
| Convergence reached | ✓ Yield% 0% at Pass 4 |
| Adversarial pass complete | ✓ All 9 lenses |
| Fixes applied | ✓ 8 fixes applied |

---

## Fixes Applied

| Finding | Original | Revised |
|---------|----------|---------|
| F1 | `name: skill-name # Required: kebab-case, gerund form (verb-ing), max 64 chars` | `name: skill-name # Recommended: lowercase letters, numbers, hyphens only; max 64 chars; 📋 prefer gerund form (verb-ing)` |
| F2 | Included `license` and `metadata` fields | Removed both fields |
| F3 | No types section | Added "Types of Skill Content" section |
| F4 | Only `$ARGUMENTS` and `${CLAUDE_SESSION_ID}` | Added `$ARGUMENTS[N]` and `$N` |
| F6 | `scripts/          # Automation - stdlib only (optional)` | `scripts/          # Utility scripts Claude can execute (optional)` |
| F7 | "Aim for ~500 lines... significantly larger" | "Keep SKILL.md under 500 lines... exceeds 500 lines" |
| F12 | `once: true # Optional: run only once per session` | `once: true # Optional: run only once per session (skill hooks only, not agents)` |
| A1+A2 | No header note | Added note distinguishing official vs project conventions + link to official docs |
