# Subagent Template

A starting structure for subagent files. Adapt based on the agent's purpose.

```yaml
---
name: <agent-name>
description: <when Claude should delegate to this agent — not what it does>
tools: <comma-separated list, or omit to inherit all>
model: <haiku | sonnet | opus | inherit>
---
```

**Note:** Remove placeholder comments and unused optional sections before finalizing.

---

## Purpose Statement

**Required.** Clear, specific description of what this agent does.

<!-- What is this agent's specialty? What domain does it own? -->

## Task Instructions

**Required.** What the agent should do when invoked.

<!--
Methodology or approach:
1. First step (context gathering or immediate action)
2. Core task steps
3. Output/delivery step
-->

## Constraints

**Required.** Explicit boundaries — what NOT to do.

<!--
- What areas are out of scope?
- What actions are forbidden?
- What should the agent skip or ignore?
-->

## Output Format

**Required.** Exact structure of what the agent returns.

<!--
Return:
1. [Primary output]
2. [Supporting details]
3. [Evidence or references]

Do not include:
- [What to omit]
-->

---

# Reference Section

> **Note:** Remove everything below before finalizing.

## Writing the Description

The description enables delegation. It answers **"when should Claude delegate to this agent?"** — not "what does this agent do?"

### Good vs Bad

| Good (delegation trigger) | Bad (describes behavior) |
|---------------------------|--------------------------|
| "Use proactively when reviewing code for security vulnerabilities and error handling issues" | "Analyzes code, generates prioritized findings, and suggests fixes" |
| "Use when debugging test failures or unexpected behavior" | "Uses systematic elimination to find root causes and verify fixes" |
| "Use when exploring codebase to answer architectural questions" | "Reads files, maps dependencies, and returns structured summaries" |

### Include

- "Use when..." or "Use proactively when..." phrasing
- Domain or specialty area
- Types of tasks to delegate
- Keywords for discoverability

### Exclude

- How the agent works internally
- Steps or methodology
- Output format details

## Validation Checklist

- [ ] Required sections present: Purpose, Task Instructions, Constraints, Output Format
- [ ] Description contains delegation trigger only (no methodology)
- [ ] Constraints specify what NOT to do
- [ ] Output format specifies what NOT to return
- [ ] No contradictions between sections
- [ ] Tools match constraints (no Edit if read-only)
