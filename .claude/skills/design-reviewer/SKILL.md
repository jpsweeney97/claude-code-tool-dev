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

## Evaluation Checklist

Use this checklist to identify findings. Each unchecked item is a potential finding.

### Completeness
- [ ] Has clear purpose/goal statement
- [ ] Lists components or modules involved
- [ ] Describes data flow between components
- [ ] Addresses error handling and failure modes
- [ ] Includes testing strategy or verification approach

### Clarity
- [ ] No undefined terms or acronyms without explanation
- [ ] No "TBD", "TODO", or placeholder sections
- [ ] Complex concepts have examples
- [ ] Could be implemented without asking clarifying questions

### Feasibility
- [ ] All referenced dependencies exist
- [ ] No "assume X works" without justification
- [ ] Performance/scale claims have basis (benchmarks, estimates, precedent)
- [ ] Resource requirements stated (memory, storage, external services)

### Architecture
- [ ] Simpler alternative was considered (or justified why not applicable)
- [ ] Trade-offs explicitly stated
- [ ] Consistent with existing codebase patterns (or explains deviation)
- [ ] No unnecessary abstraction layers

### Edge Cases
- [ ] Empty/null inputs handled
- [ ] Boundary conditions addressed
- [ ] Concurrent access considered (if applicable)
- [ ] Failure/retry behavior defined

### Security (if applicable)
- [ ] Authentication mechanism specified
- [ ] Authorization checks defined
- [ ] Sensitive data handling addressed
- [ ] Input validation approach stated

### Testability
- [ ] Testing approach described
- [ ] Success criteria are verifiable
- [ ] Key behaviors are observable/measurable
