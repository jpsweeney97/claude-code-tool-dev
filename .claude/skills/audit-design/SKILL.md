---
name: audit-design
description: Audits Claude Code tool designs (skills, plugins, hooks, commands, agents) for feasibility and risk. Fast single-pass analysis, no subagents.
---

# Audit Design

Audit Claude Code tool designs for feasibility issues (assumptions that don't match Claude's actual behavior) and risk issues (failure modes, edge cases, missing error handling).

## Primary Goal

Identify problems in tool designs **before implementation**. Two analysis dimensions:

1. **Feasibility** — Does this assume Claude can do things it actually can't?
2. **Risk** — What failure modes exist? What edge cases are unhandled?

Output: A written report with actionable findings.

## Non-Goals

- **Spec compliance** — Not checking frontmatter fields, required sections, or format rules. Read the spec docs directly for that.
- **Scope review** — Not judging whether the skill is too ambitious or too narrow. That's a design decision.
- **Implementation review** — Audits designs, not code. Use code review for implementation.
- **Security pentesting** — Looks for design gaps, not runtime vulnerabilities or injection attacks.
- **Style feedback** — Not commenting on writing quality, naming, or organization.

## When to Use

- Before implementing a new skill, hook, or command
- When an existing skill isn't working as expected
- To sanity-check feasibility before investing time
- When reviewing someone else's tool design

## When NOT to Use

- **Just have an idea** — Use brainstorming first. Audit needs a written design.
- **Have code to review** — Use code review skills. This audits designs, not implementations.
- **Want spec compliance** — Read the spec docs directly (skills-content-sections.md, etc.)
- **Need architecture advice** — Use architecture-decisions skill for structural choices.
- **Design is obviously incomplete** — Finish the draft first. Auditing fragments wastes time.

## Inputs

### Required

| Input | Source | Example |
|-------|--------|---------|
| Target path | User provides or current file | `.claude/skills/foo/SKILL.md` |

### Detected

The artifact type is inferred from path and content signals:

| Signal | Detected Type |
|--------|---------------|
| Path contains `/skills/` or file named `SKILL.md` | Skill |
| Path contains `/hooks/` or `.py` with hook patterns | Hook |
| Path contains `/commands/` or frontmatter with `allowed-tools` | Command |
| Path contains `/plugins/` or has `package.json` with claude fields | Plugin |
| Path contains `/agents/` or frontmatter with `agent` fields | Agent |
| None match | Ask user |

## Outputs

### Report Location

```
docs/audits/audit-<filename>-<YYYY-MM-DD>.md
```

Example: `docs/audits/audit-SKILL-2025-01-15.md`

### Report Structure

```markdown
# Audit: <artifact-name>

**Date:** YYYY-MM-DD
**Target:** <path>
**Type:** <skill|hook|command|plugin|agent>
**Verdict:** <Critical Issues | Major Issues | Needs Work | Ready>

## Summary

<2-3 sentence overview of findings>

## Findings

### <Finding Title>

- **What:** <The problem>
- **Why it matters:** <Impact or consequence>
- **Evidence:** "<quoted text from design>"
- **Severity:** Critical | Major | Minor
- **Suggestion:** <Specific fix>

### <Next Finding>
...

## What's Working

- <Strength 1>
- <Strength 2>
- <Strength 3>
```

### Definition of Done

All conditions must be true:

1. Report file exists at `docs/audits/audit-<filename>-<YYYY-MM-DD>.md`
2. Report contains Summary section with Verdict
3. Report contains Findings section (even if "No significant issues found")
4. Each finding has all five required fields: What, Why it matters, Evidence, Severity, Suggestion
5. Report contains What's Working section with at least 2 items

## Procedure

### Step 1: Read Target Document

Read the file at the target path.

- **Success:** File contents loaded. Continue to Step 2.
- **Failure:** File not found or unreadable. **STOP.** Ask user to verify the path.

### Step 2: Detect Artifact Type

Use path and content signals to determine the artifact type.

- **Success:** Type identified (skill, hook, command, plugin, agent). Continue to Step 3.
- **Failure:** Type ambiguous. **Ask user** with options: "Is this a skill, hook, command, plugin, or agent?"

### Step 3: Analyze for Feasibility Issues

Check the design against Claude's actual capabilities:

| Check | Red Flag |
|-------|----------|
| **State assumptions** | Assumes persistent memory across sessions, user-specific preferences, or learning from feedback |
| **Reasoning complexity** | Requires multi-step logical inference without intermediate verification |
| **Tool behavior** | Assumes tools return specific formats, always succeed, or have capabilities they don't |
| **Proactivity expectations** | Expects Claude to autonomously monitor, schedule, or initiate without user prompt |
| **Model fit** | Assumes vision, code execution, or internet access when not available |

For each issue found, note the evidence (quoted text) and why it's problematic.

### Step 4: Analyze for Risk Issues

Check for unhandled failure modes and edge cases:

| Check | Red Flag |
|-------|----------|
| **Error handling** | No guidance for tool failures, invalid inputs, or partial results |
| **Edge cases** | Missing handling for empty inputs, very large inputs, or unusual formats |
| **Recovery paths** | No fallback when primary approach fails |
| **Integration risks** | Depends on external services, specific file structures, or environment state |
| **Underspecification** | Vague instructions that could be interpreted multiple ways |

For each issue found, note the evidence and potential impact.

### Step 5: Identify Strengths

Find 2-3 things the design does well. Examples:
- Clear success criteria
- Good error handling patterns
- Appropriate scope
- Realistic assumptions
- Useful examples

### Step 6: Determine Verdict

| Condition | Verdict |
|-----------|---------|
| Any Critical finding | **Critical Issues** — Do not implement until resolved |
| 2+ Major findings | **Major Issues** — Significant rework needed |
| 1 Major or multiple Minor | **Needs Work** — Address before implementing |
| Only Minor or no findings | **Ready** — Safe to implement |

### Step 7: Write Report

Create the report at `docs/audits/audit-<filename>-<YYYY-MM-DD>.md`.

Ensure the `docs/audits/` directory exists first.

Note: This creates a new file in a dedicated audits directory. The action is reversible (file can be deleted) and non-destructive (doesn't overwrite existing content).

### Step 8: Show Summary

Display in conversation:
- Verdict
- Count of findings by severity
- Top 2-3 most important findings
- Path to full report

## Decision Points

### DP1: File Not Found

**Trigger:** Step 1 fails to read the target file.

**Action:** STOP. Do not proceed with analysis.

**Response:** "I couldn't read the file at `<path>`. Please verify the path exists and try again."

### DP2: Artifact Type Ambiguous

**Trigger:** Step 2 cannot confidently determine artifact type from signals.

**Action:** Ask user before proceeding.

**Response:** "I'm not sure what type of artifact this is. Is this a: (1) Skill, (2) Hook, (3) Command, (4) Plugin, or (5) Agent?"

### DP3: No Findings

**Trigger:** Steps 3-4 produce no feasibility or risk findings.

**Action:** Report "No significant issues found" with Ready verdict. Still complete the report with What's Working section.

**Response:** Include in summary: "No significant feasibility or risk issues found. The design appears ready for implementation."

## Severity Definitions

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | Will definitely fail. Assumes impossible behavior. | "Track user preferences across sessions" (no persistent memory) |
| **Major** | Likely to cause problems in common cases. Missing handling for frequent scenarios. | No error handling when file read fails |
| **Minor** | Could be better. Edge cases or unlikely scenarios. | Doesn't handle empty input gracefully |

## Verification

### Quick Check

```bash
# Verify report exists
ls docs/audits/audit-*.md

# Verify required sections
grep -l "## Summary" docs/audits/audit-*.md
grep -l "## Findings" docs/audits/audit-*.md
grep -l "## What's Working" docs/audits/audit-*.md
```

### Verdict Consistency Check

Verify the verdict matches the findings:

| Verdict | Required Evidence |
|---------|------------------|
| Critical Issues | `grep -c "Severity:** Critical" <report>` returns ≥1 |
| Major Issues | `grep -c "Severity:** Critical" <report>` returns 0 AND `grep -c "Severity:** Major" <report>` returns ≥2 |
| Needs Work | `grep -c "Severity:** Major" <report>` returns 1, OR `grep -c "Severity:** Minor" <report>` returns ≥2 |
| Ready | `grep -c "Severity:** Critical\|Major" <report>` returns 0 |

If verdict doesn't match findings, update the verdict.

### Finding Quality Check (Manual)

For each finding, verify:
- **Evidence** quotes actual text from the design (not paraphrased) — check by searching the original document for the quoted string
- **Suggestion** is actionable (specific enough to implement) — should name a concrete change, not just "fix this"

## Troubleshooting

### Report Not Created

**Symptoms:** Audit completes but no file at `docs/audits/`.

**Causes:**
- Directory doesn't exist
- Write permission issue
- Path construction error

**Fix:** Manually create directory with `mkdir -p docs/audits` and retry Step 7.

### All Findings Seem Generic

**Symptoms:** Findings apply to any design, not specific to this one.

**Causes:**
- Didn't quote specific evidence from the design
- Applying checklist mechanically without context

**Fix:** Re-read the design. Each finding must reference specific text. If you can't quote evidence, it's not a real finding.

### Wrong Artifact Type Detected

**Symptoms:** Analysis uses wrong criteria (e.g., checking hook patterns in a skill).

**Causes:**
- Path signals misleading
- Content signals ambiguous

**Fix:** Explicitly state the intended type: "This is a skill design, please audit it as such."

## Examples

### Invocation

```
Audit this skill design: .claude/skills/my-new-skill/SKILL.md
```

```
Review .claude/hooks/pre-commit.py for feasibility issues
```

```
/audit-design .claude/commands/deploy.md
```

### Sample Finding

```markdown
### Assumes Session Memory

- **What:** Design expects Claude to "remember previous audit results" for comparison.
- **Why it matters:** Claude has no persistent memory across sessions. Each conversation starts fresh.
- **Evidence:** "Compare with previous audit to track improvement over time"
- **Severity:** Critical
- **Suggestion:** Store audit results in files and explicitly load previous reports for comparison.
```
