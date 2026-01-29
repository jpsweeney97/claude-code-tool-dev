# Subagents Rules Document Review

## Summary

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | 1     | Skills field format discrepancy (fixed)    |
| P1       | 5     | Missing sections and incomplete tables     |
| P2       | 3     | Polish items                               |

**Fixes applied:** 9 (all P0 and P1)

## Context

- **Protocol:** thoroughness.framework@1.0.0
- **Target:** `.claude/rules/extensions/subagents.md`
- **Source:** `docs/claude-code-documentation/subagents.md`
- **Stakes:** Rigorous
- **Stopping criteria:** Yield% <10%

## Entry Gate

### Assumptions
- A1: Source document is authoritative reference ✓
- A2: Target document is current working version ✓
- A3: Target is development guidance, not feature spec ✓
- A4: Target may exclude user-focused content ✓

### Dimensions Checked

| Category | Dimensions | Status |
|----------|------------|--------|
| Source Coverage | D1-D3 | ✓ |
| Behavioral Completeness | D4-D6 | ✓ |
| Implementation Readiness | D7-D11 | ✓ |
| Cross-validation | D12 | ✓ |
| Document Quality | D13-D19 | ✓ |

## Iteration Log

| Pass | New | Reopened | Revised | Escalated | Yield% |
|------|-----|----------|---------|-----------|--------|
| 1 | 7 | 0 | 0 | 0 | 100% |
| 2 | 2 | 0 | 0 | 0 | 22% |
| 3 | 2 | 0 | 0 | 0 | 18% |
| 4 | 0 | 0 | 0 | 0 | 0% |

Convergence reached at Pass 4.

## Findings

### P0: Critical

**F6: Skills field format discrepancy**
- **Location:** Line 85 (frontmatter table), Line 95-96 (example)
- **Problem:** Target showed comma-separated string (`skills: sql-analysis, chart-generation`), but source uses YAML list format. YAML would parse comma-separated as single string, causing silent skill loading failure.
- **Evidence:** E2 (cross-referenced source example at lines 263-266)
- **Confidence:** High
- **Fix:** Changed type from "string" to "list", updated example to YAML list format

### P1: Should Fix

**F1: Auto-compaction section missing**
- **Location:** Not present in target
- **Problem:** Source (lines 522-538) documents subagent auto-compaction and `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` env var. Developers should know agents support compaction.
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added Auto-Compaction section after Storage section

**F2: Permission modes table incomplete**
- **Location:** Line 84
- **Problem:** Target listed modes but didn't explain each behavior. Source has detailed table (lines 241-248).
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added Permission Modes section with full behavior table

**F7: When-to-use guidance less detailed**
- **Location:** Lines 19-24
- **Problem:** Source provides more nuanced guidance on when to use main conversation vs. subagents.
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added latency and iterative refinement points to "When NOT to Use"

**F8: CLI disallowedTools flag not mentioned**
- **Location:** Line 527
- **Problem:** Source (lines 329-334) mentions both settings deny array AND CLI flag. Target only mentioned settings.
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added CLI alternative

**F11: Context consumption warning missing**
- **Location:** Parallel Execution section
- **Problem:** Source (lines 461-464) warns about context consumption from parallel agent results.
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added warning note about context consumption

### P2: Polish

**F3: Testing section lacks exit criteria**
- **Location:** Lines 459-465
- **Problem:** Testing steps given but no criteria for "agent is ready"
- **Evidence:** E1
- **Confidence:** Medium
- **Status:** Not fixed (low impact)

**F4: MCP unavailability in background not explained**
- **Location:** Background Execution section
- **Problem:** MCP unavailability mentioned but not actionable guidance
- **Evidence:** E1
- **Confidence:** Medium
- **Fix:** Added "design around" emphasis and explicit guidance

**F10: Chaining pattern not explicitly mentioned**
- **Location:** Not present
- **Problem:** Source (lines 465-472) shows chaining pattern for multi-step workflows
- **Evidence:** E2
- **Confidence:** High
- **Fix:** Added Chaining Agents section

## Disconfirmation Attempts

**F6 (Skills format):**
- **Hypothesis:** Both formats might be valid
- **Test:** Analyzed YAML parsing behavior
- **Result:** Comma-separated would be parsed as single string value, not list. Confirmed this is a genuine format error.

## Adversarial Pass

Applied all 9 lenses:

| Lens | Finding |
|------|---------|
| Assumption Hunting | No critical assumptions discovered |
| Scale Stress | Priority/shadowing rules handle many agents |
| Competing Perspectives | Security (hooks), performance (model selection), maintainability (checklist) addressed |
| Kill the Document | Skills format (F6) was the most dangerous gap — silent failure mode |
| Pre-mortem | Confirmed F6 as critical via failure scenario |
| Steelman Alternatives | Linking to source not appropriate for rules doc |
| Challenge the Framing | Document type is appropriate |
| Hidden Complexity | Hook env vars could be more detailed (acceptable at Rigorous) |
| Motivated Reasoning | No signs of anchoring |

## Exit Gate

| Criterion | Status |
|-----------|--------|
| Coverage complete | ✓ |
| Evidence requirements met | ✓ E2 for P0, E1+ for P1 |
| Disconfirmation attempted | ✓ |
| Assumptions resolved | ✓ |
| Convergence reached | ✓ Yield% = 0% < 10% |
| Adversarial pass complete | ✓ All 9 lenses |

## Fixes Applied

1. **Skills field type:** "string" → "list" (line 85)
2. **Skills example:** comma-separated → YAML list format (lines 95-99)
3. **Permission modes table:** Added new section with behavior descriptions
4. **Auto-compaction section:** Added after Storage
5. **Context consumption warning:** Added to Parallel Execution
6. **CLI disallowedTools flag:** Added alternative to settings approach
7. **When-not-to-use:** Added latency and iterative refinement points
8. **Chaining agents section:** Added before Background Execution
9. **MCP foreground guidance:** Added explicit note
