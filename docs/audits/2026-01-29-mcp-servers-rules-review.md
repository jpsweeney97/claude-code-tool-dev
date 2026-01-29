# Document Review: mcp-servers.md

**Date:** 2026-01-29
**Target:** `.claude/rules/mcp-servers.md`
**Source:** `docs/claude-code-documentation/mcp.md` (official Claude Code documentation)
**Stakes:** Rigorous
**Reviewer:** Claude (reviewing-documents skill)

## Summary

| Priority | Count | Fixed | Description |
|----------|-------|-------|-------------|
| P0 | 1 | 1 | Issues that break correctness |
| P1 | 6 | 6 | Issues that degrade quality |
| P2 | 4 | 0 | Polish items |

## Entry Gate

**Inputs:**
- Target: `.claude/rules/mcp-servers.md` (678 lines)
- Source: `docs/claude-code-documentation/mcp.md` (1130 lines)

**Scope:**
- Source Coverage (D1-D3): Checked
- Consistency (D12): Checked
- Document Quality (D13-D19): Checked
- Behavioral Completeness (D4-D6): Skipped (reference doc, not implementation spec)
- Implementation Readiness (D7-D11): Skipped (reference doc)

**Assumptions:**
- Source document is authoritative and current
- Target aims to capture essential MCP knowledge for project developers
- Target is project-specific (TypeScript focus), not exhaustive reference

**Stopping Criteria:** Yield% < 10%

## Coverage Tracker

| ID | Dimension | Status | Priority | Evidence | Confidence |
|----|-----------|--------|----------|----------|------------|
| D1 | Structural coverage | [x] | P0 | E2 | High |
| D2 | Semantic fidelity | [x] | P0 | E2 | High |
| D3 | Procedural completeness | [x] | P1 | E1 | High |
| D12 | Cross-validation | [x] | P1 | E1 | Medium |
| D13 | Implicit concepts | [x] | P1 | E1 | High |
| D14 | Precision | [x] | P1 | E1 | High |
| D15 | Examples | [x] | P2 | E1 | High |
| D16 | Internal consistency | [x] | P1 | E1 | High |
| D17 | Redundancy | [x] | P2 | E1 | High |
| D18 | Verifiability | [x] | P2 | E1 | Medium |
| D19 | Actionability | [x] | P1 | E1 | High |

## Iteration Log

| Pass | Focus | Yield% | Notes |
|------|-------|--------|-------|
| 1 | DISCOVER + EXPLORE all dimensions | 100% | Found F1-F11 |
| 2 | Verify findings, deeper exploration | 12.5% | Added F12, F13 |
| 3 | Final sweep, confirm convergence | 0% | No new findings |

## Findings

### P0 — Critical Gaps

**F1: Missing MCP Tool Search section**
- **Dimension:** D1 (Structural coverage)
- **Evidence:** E2 (verified in both documents)
- **Source:** Lines 808-862
- **Issue:** Significant feature for scaling MCP usage completely absent from target
- **Impact:** Developers with many MCP servers will hit context limits without knowing the solution
- **Fix Applied:** Added comprehensive "MCP Tool Search" section with configuration options

### P1 — Quality Issues

**F2: Missing MCP_TIMEOUT environment variable**
- **Dimension:** D1 (Structural coverage)
- **Evidence:** E1
- **Source:** Line 334
- **Fix Applied:** Added note about `MCP_TIMEOUT` in Output Limits section

**F3: Plugin MCP servers section minimal**
- **Dimension:** D1 (Structural coverage)
- **Evidence:** E1
- **Source:** Lines 350-412
- **Fix Applied:** Added "Plugin-Provided MCP Servers" section with configuration examples

**F5: Missing scope name change note**
- **Dimension:** D2 (Semantic fidelity)
- **Evidence:** E1
- **Source:** Line 332
- **Fix Applied:** Added note about `local` (formerly `project`) and `user` (formerly `global`)

**F7: Missing plugin MCP restart requirement**
- **Dimension:** D2 (Semantic fidelity)
- **Evidence:** E1
- **Source:** Line 393
- **Fix Applied:** Added "Must restart Claude Code" note in plugin section

**F8: Imprecise transport deprecation note**
- **Dimension:** D14 (Precision)
- **Evidence:** E1
- **Source:** Line 263
- **Fix Applied:** Changed from "deprecated" to "deprecated — use HTTP where available"

**F12: Missing import from Claude Desktop platform limitation**
- **Dimension:** D19 (Actionability)
- **Evidence:** E1
- **Source:** Lines 675-676
- **Fix Applied:** Added "(macOS and WSL only)" to command comment

### P2 — Polish Items (Not Fixed)

**F9:** Missing "where available" qualifier for HTTP recommendation
**F11:** Missing `/mcp` authentication flow detail
**F13:** Missing Claude Code executable path troubleshooting for `mcp serve`

## Disconfirmation Attempts

**F1 (MCP Tool Search):**
- Counterexample search: Searched target for "tool search", "MCPSearch", "ENABLE_TOOL_SEARCH" → None found
- Alternative hypothesis: Feature might be too new → Source documents it fully, should be included
- **Verdict:** Confirmed P0

## Adversarial Pass

All 9 lenses applied for Rigorous stakes:

| Lens | Result |
|------|--------|
| Assumption Hunting | No hidden assumptions; TypeScript focus is stated |
| Scale Stress | Tool Search addresses scaling (was missing — F1) |
| Competing Perspectives | Security, ops, maintainability concerns addressed |
| Kill the Document | "Tool Search misconfigured" — captured as F1 |
| Pre-mortem | Main failure mode captured as F1 and F7 |
| Steelman Alternatives | Link-to-docs approach considered; current approach valid |
| Challenge the Framing | Appropriate level for project rule file |
| Hidden Complexity | Tool Search was hidden — captured |
| Motivated Reasoning | No anchoring or bias detected |

## Fixes Applied

| Finding | Original | Revised |
|---------|----------|---------|
| F1 | No Tool Search section | Added 45-line section with config table, examples, model requirements |
| F2 | Only MAX_MCP_OUTPUT_TOKENS | Added MCP_TIMEOUT documentation |
| F3 | Brief plugin mention in See Also | Added 25-line Plugin-Provided MCP Servers section |
| F5 | No historical scope names | Added note about local/project and user/global name changes |
| F7 | No restart requirement | Added "Must restart Claude Code" key behavior |
| F8 | "sse (deprecated)" | "sse (deprecated — use HTTP where available)" |
| F12 | No platform note | Added "(macOS and WSL only)" |

## Exit Gate

- [x] Coverage complete (no `[ ]` or `[?]` items)
- [x] Evidence requirements met (E2 for P0, E1 for P1)
- [x] Disconfirmation attempted for P0
- [x] Assumptions resolved (source is authoritative)
- [x] Convergence reached (Yield% = 0% < 10%)
- [x] Adversarial pass complete (9 lenses)
- [x] P0 and P1 fixes applied
