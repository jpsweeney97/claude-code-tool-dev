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

## Inputs

**Required:**

- **Design document path** — Path to design doc (typically `docs/plans/YYYY-MM-DD-<topic>-design.md`)

**Optional:**

- **Focus areas** — Specific aspects to emphasize (e.g., "security", "error handling")
- **Context** — Additional background not in the design doc

**Constraints:**

- Design document must exist at the specified path
- Document must have minimal structure (see Decision Points for structural check)

## Outputs

**Artifacts:**

- **Review report** — Written to `docs/plans/YYYY-MM-DD-<topic>-design-review.md` (same directory as design doc, with `-review` suffix)
- Only written after user confirmation

**Report structure:**

```markdown
# Design Review: <topic>

**Design doc:** <path>
**Reviewed:** <date>
**Verdict:** PASS | PASS WITH CONCERNS | NEEDS REVISION
**Score:** <total> (Critical: N×10, Important: N×3, Minor: N×1)

## Summary
<2-3 sentence overall assessment>

## Findings

### Critical (10 points each — must fix)
- <finding with rationale>

### Important (3 points each — should address)
- <finding with rationale>

### Minor (1 point each — consider)
- <finding with rationale>

## Recommendations
<Prioritized next steps>
```

**Definition of Done:**

- [ ] Review report file exists at confirmed path
- [ ] Report contains verdict (PASS, PASS WITH CONCERNS, or NEEDS REVISION)
- [ ] Report contains score breakdown
- [ ] All Critical/Important findings include rationale
- [ ] User confirmed before file was written
