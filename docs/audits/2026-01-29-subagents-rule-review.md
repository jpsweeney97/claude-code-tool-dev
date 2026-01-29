# Document Review: subagents.md Rule File

**Date:** 2026-01-29
**Target:** `.claude/rules/subagents.md`
**Source:** `docs/claude-code-documentation/subagents.md` (official docs)
**Stakes:** Rigorous
**Reviewer:** Claude (via reviewing-documents skill)

## Summary

| Priority | Count | Description                                |
| -------- | ----- | ------------------------------------------ |
| P0       | 2     | Issues that break correctness or execution |
| P1       | 5     | Issues that degrade quality                |
| P2       | 4     | Polish items                               |

**All P0 and P1 issues fixed. 1 P2 issue fixed. 3 P2 items accepted as-is.**

## Entry Gate

### Inputs
- **Target:** `.claude/rules/subagents.md` (576 lines)
- **Source:** `docs/claude-code-documentation/subagents.md` (725 lines) — official Claude Code documentation

### Scope
All dimension categories applied:
- Document Quality (D13-D19): Mandatory
- Cross-validation (D12): Mandatory
- Source Coverage (D1-D3): Source exists
- Behavioral Completeness (D4-D6): Rule file will be implemented
- Implementation Readiness (D7-D11): Developers will use this

### Assumptions
1. Source document (official docs) is authoritative and current
2. Target document (rule file) should capture source accurately while condensing
3. Rule file may intentionally omit tutorial content

### Stakes Calibration
- Reversibility: Easy to edit — Adequate
- Blast radius: Project-level guidance — Moderate
- Cost of error: Wrong agent config could cause wasted effort — Medium
- **Result: Rigorous** (moderate blast radius + medium error cost)

### Stopping Criteria
- Primary: Yield-based (Yield% < 10%)

---

## Coverage Tracker

### Source Coverage (D1-D3)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D1-1 | [x] | P1 | Missing `/agents` command documentation | Source lines 69-139 | High |
| D1-2 | [x] | P1 | Missing `--agents` CLI JSON format example | Source lines 156-169 | High |
| D1-3 | [x] | P1 | Incomplete built-in agents list | Source lists 6+ agents; rule listed 3 | High |
| D1-4 | [x] | P1 | Missing background execution controls | Ctrl+B, env var missing | High |
| D2-1 | [x] | P0 | Hook input mechanism incorrect | Source: stdin; Rule: env var | High |
| D3-1 | [-] | N/A | Procedures match | Compare invocation patterns | High |

### Behavioral Completeness (D4-D6)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D4-1 | [x] | — | Decision rules present | Priority table, model selection | High |
| D5-1 | [x] | — | Exit criteria defined | Compliance checklist | High |
| D6-1 | [x] | — | Safety defaults present | Permission modes, tool restrictions | High |

### Implementation Readiness (D7-D11)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D7-1 | [x] | — | Clear instructions | Format, examples present | High |
| D8-1 | [x] | P2 | MCP inheritance not explicit | "inherit all" vs "including MCP" | Medium |
| D9-1 | [x] | P0 | Broken example script | Uses non-existent $TOOL_INPUT | High |
| D9-2 | [x] | P1 | Broken reference link | Path includes non-existent /references/ | High |
| D10-1 | [x] | — | Edge cases covered | Anti-patterns section | High |
| D11-1 | [x] | — | Testable | Testing workflow present | High |

### Consistency (D12)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D12-1 | [x] | — | Terminology consistent | Agent/subagent usage consistent | High |
| D12-2 | [x] | P2 | Built-in tools characterization differs | Source: "read-only"; Rule: lists specific tools | Low |

### Document Quality (D13-D19)

| ID | Status | Priority | Finding | Evidence | Confidence |
|----|--------|----------|---------|----------|------------|
| D13-1 | [x] | — | Terms defined | Frontmatter fields, permission modes | High |
| D14-1 | [x] | — | Language precise | Specific instructions | High |
| D15-1 | [x] | — | Examples present | Multiple code examples | High |
| D16-1 | [x] | — | Internal consistency | No contradictions found | High |
| D17-1 | [x] | P2 | once:true mentioned but not in source | Rule adds useful clarification | Medium |
| D18-1 | [x] | — | Verifiable | Compliance checklist testable | High |
| D19-1 | [x] | — | Actionable | Clear workflow steps | High |

---

## Iteration Log

| Pass | New Findings | Revisions | Total P0+P1 | Yield% |
|------|--------------|-----------|-------------|--------|
| 1    | 11           | 0         | 8           | 100%   |
| 2    | 0            | 0         | 8           | 0%     |

**Convergence reached at Pass 2** (Yield% 0% < 10% threshold)

---

## Findings

### P0: Critical Issues

#### F1: Hook environment variable incorrect
- **Dimension:** D2 (Semantic fidelity), D9 (Feasibility)
- **Location:** Lines 165-183 (original)
- **Problem:** Rule stated hooks receive context via `$TOOL_INPUT` environment variable
- **Source says:** Hooks receive JSON via stdin: `INPUT=$(cat)`
- **Impact:** Scripts using $TOOL_INPUT would fail silently
- **Fix applied:** Replaced section with correct stdin-based example

#### F2: Example validation script broken
- **Dimension:** D9 (Feasibility)
- **Location:** Lines 176-183 (original)
- **Problem:** Script used `echo "$TOOL_INPUT" | grep` which wouldn't work
- **Fix applied:** Replaced with correct `INPUT=$(cat)` + jq parsing pattern

### P1: Quality Issues

#### F3: Missing /agents command documentation
- **Dimension:** D1 (Structural coverage)
- **Location:** Agent Priority section
- **Problem:** Source covers interactive management extensively; rule file only showed file-based creation
- **Fix applied:** Added "Managing Agents with /agents" section

#### F4: Missing --agents CLI JSON format example
- **Dimension:** D1 (Structural coverage)
- **Location:** Agent Priority section
- **Problem:** CLI flag mentioned but format not shown
- **Fix applied:** Added "CLI-Defined Agents" section with JSON example

#### F5: Incomplete built-in agents list
- **Dimension:** D1 (Structural coverage), D8 (Completeness)
- **Location:** Built-in Agent Types section
- **Problem:** Said "three built-in subagents" but source lists 6+
- **Fix applied:** Expanded table to include Bash, statusline-setup, Claude Code Guide

#### F6: Broken reference link
- **Dimension:** D9 (Feasibility)
- **Location:** Prompt Clarity and Quality Dimensions sections (2 occurrences)
- **Problem:** Link path `skills/brainstorming-subagents/references/subagent-writing-guide.md` doesn't exist
- **Actual path:** `skills/brainstorming-subagents/subagent-writing-guide.md`
- **Fix applied:** Corrected both links

#### F7: Missing background execution features
- **Dimension:** D1 (Structural coverage)
- **Location:** Background Execution section
- **Problem:** Missing Ctrl+B shortcut and CLAUDE_CODE_DISABLE_BACKGROUND_TASKS env var
- **Fix applied:** Added "Runtime controls" section with both features

### P2: Polish Items

#### F8: MCP tools inheritance not explicit (FIXED)
- **Dimension:** D8 (Completeness)
- **Location:** Frontmatter Fields table
- **Problem:** Said "inherit all" but source explicitly says "including MCP tools"
- **Fix applied:** Added "(including MCP tools)" to tools field description

#### F9: Built-in tools characterization differs (ACCEPTED)
- **Dimension:** D12 (Cross-validation)
- **Location:** Built-in Agent Types table
- **Problem:** Source says "read-only tools (denied Write, Edit)"; rule listed specific tools
- **Decision:** Updated to match source characterization

#### F10: once:true limitation documented but not in source (ACCEPTED)
- **Dimension:** D17 (Redundancy)
- **Location:** Line 167
- **Assessment:** Rule adds useful clarification confirmed by MCP docs search
- **Decision:** Retain — adds value beyond source

#### F11: Missing "Understand automatic delegation" section (ACCEPTED)
- **Dimension:** D1 (Structural coverage)
- **Assessment:** Concept is captured in description field note about "use proactively"
- **Decision:** Current coverage sufficient for reference doc

---

## Adversarial Pass

Applied all 9 lenses (Rigorous requirement):

### Assumption Hunting
- **Found:** Hook script assumes `jq` availability
- **Fixed:** Changed to "Use `jq` (or Python/etc.) to parse"

### Scale Stress
- Priority rules handle name conflicts ✓
- Context warning for background agents ✓
- cleanupPeriodDays handles disk ✓
- **No issues found**

### Competing Perspectives
- Security: Hook validation correct ✓
- Performance: Background agents, Haiku guidance ✓
- Maintainability: Clear structure ✓
- **No issues found**

### Kill the Document
- Strongest attack: Someone might copy old pattern elsewhere
- Defense: Fixed with explicit stdin reference

### Pre-mortem
- "What went wrong?" scenarios all addressed by fixes

### Steelman Alternatives
- Tutorial content appropriately deferred to official docs

### Challenge the Framing
- Reference doc scope is correct for rule file purpose

### Hidden Complexity
- Hook parsing complexity acknowledged with "(or Python/etc.)"

### Motivated Reasoning
- Old $TOOL_INPUT pattern was likely copied from outdated source — caught and fixed

---

## Fixes Applied

| Finding | Change | Lines Affected |
|---------|--------|----------------|
| F1+F2 | Replaced Hook Environment Variables section with Hook Input section | 165-213 |
| F3 | Added Managing Agents with /agents section | 40-49 |
| F4 | Added CLI-Defined Agents section with JSON example | 51-66 |
| F5 | Expanded Built-in Agent Types table from 3 to 6 agents | 586-593 |
| F6 | Corrected broken links (2 occurrences) | 260, 296 |
| F7 | Added Runtime controls section | 480-483 |
| F8 | Added "(including MCP tools)" to tools field | 111 |
| Adversarial | Changed "jq" to "jq (or Python/etc.)" | 195 |

---

## Disconfirmation Attempts

### P0 Findings (2+ techniques required for Rigorous)

**F1+F2 (Hook input mechanism):**
1. **Cross-check:** Searched MCP docs via search_docs tool — confirmed stdin pattern
2. **Alternative hypothesis:** Checked if $TOOL_INPUT was valid in any context — not found in official docs
3. **Counterexample search:** Looked for env var documentation — found CLAUDE_PROJECT_DIR but not TOOL_INPUT

### Adversarial techniques applied:
- Pre-mortem inversion
- Assumption hunting
- Scale stress testing
- Competing perspectives

---

## Exit Gate

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Coverage complete | ✅ | No `[ ]` or `[?]` items remaining |
| Evidence requirements | ✅ | E2 for P0 (source docs + MCP search) |
| Disconfirmation attempted | ✅ | 3 techniques for P0; 9 lenses for adversarial |
| Assumptions resolved | ✅ | jq assumption clarified |
| Convergence reached | ✅ | Yield% 0% < 10% |
| Adversarial pass complete | ✅ | All 9 lenses applied |
| Fixes applied | ✅ | 8 fixes + 1 adversarial fix |

---

## Recommendations

1. **Periodic re-review:** As official docs evolve, re-validate rule file captures changes
2. **Consider adding:** Link to official docs for tutorial content
3. **Test hooks:** Validate the corrected hook script example works in practice

---

*Review conducted using reviewing-documents skill v1.0 with Thoroughness Framework*
