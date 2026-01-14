---
name: design-reviewer
description: Reviews design documents for quality, completeness, and implementation readiness using weighted scoring. Use after brainstorming completes, before writing-plans.
allowed-tools: Read, Glob, Grep, Write, Bash
user-invocable: true
---

# Design Reviewer

## When to Use

- After brainstorming skill completes and saves a design document
- Before starting implementation with writing-plans skill
- When someone wants an independent assessment of design quality
- User says "review design", "check my design", or "/design-reviewer"

## When NOT to Use

**STOP conditions:**

- **STOP** if no design document exists yet — run brainstorming first
- **STOP** if the document is an implementation plan (contains "Task N:" headers) — this reviews designs, not plans
- **STOP** if user wants to edit/improve the design — this produces a report, it doesn't modify the original

**Non-goals:**

- Does not fix issues in the design (reports them for author to address)
- Does not validate implementation plans — different structure and criteria
- Does not replace human judgment on business/product decisions
- Does not review standalone code files or PRs — use code-review skills for that
