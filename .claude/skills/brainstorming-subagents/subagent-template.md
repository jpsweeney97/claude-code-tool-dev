# Subagent Template

Starting structures for subagent files. Choose the style that fits your agent's domain.

```yaml
---
name: <agent-name>
description: <when Claude should delegate to this agent — not what it does>
tools: <comma-separated list, or omit to inherit all>
model: <haiku | sonnet | opus | inherit>
---
```

---

## Two Valid Structures

The prompt body must address four concerns: **purpose**, **task instructions**, **constraints**, and **output format**. How you organize them is flexible.

### Option A: Formal Sections

Use explicit headers when the agent is complex or when clarity benefits from separation.

```markdown
## Purpose

You are a security specialist focusing on injection vulnerabilities and auth bypasses.

## Task

When invoked:
1. Scan the specified files for security issues
2. Trace data flows from user input to sensitive operations
3. Report findings with evidence

## Constraints

- Do not modify any files
- Do not report style issues — security only
- Skip test files unless explicitly included

## Output

Return findings as:
### [Severity] Issue Title
- **Location**: file:line
- **Problem**: What's wrong
- **Evidence**: Code snippet showing the issue

Do not include: minor issues, suggestions for unrelated improvements.
```

### Option B: Fluid Prose

Use conversational flow when the agent is straightforward or when domain context reads more naturally inline.

```markdown
You are a senior code reviewer ensuring high standards of code quality and security.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is clear and readable
- Proper error handling
- No exposed secrets or API keys
- Input validation implemented

Provide feedback organized by priority:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)

Include specific examples of how to fix issues. Do not report minor style issues or suggest unrelated refactoring.
```

Both examples address all four concerns. The second embeds constraints ("Do not report minor style issues") and output format ("Provide feedback organized by priority") inline rather than in separate sections.

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

Content (all required — structure is flexible):

- [ ] **Purpose** addressed: What is this agent's specialty?
- [ ] **Task instructions** addressed: What should it do when invoked?
- [ ] **Constraints** addressed: What should it NOT do?
- [ ] **Output format** addressed: What should it return (and not return)?

Quality:

- [ ] Description contains delegation trigger only (no methodology)
- [ ] No contradictions between instructions
- [ ] Tools match constraints (no Edit if read-only)
- [ ] Two specialists reading this prompt would work the same way
