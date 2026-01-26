# Design Context: reviewing-code

**Date:** 2026-01-25
**Type:** Process/workflow
**Risk:** Medium (writes files, bounded and reversible)

## Problem Statement

Current code reviews fail in multiple ways:
- **Shallow:** One-pass "looks good" verdicts that miss deeper issues
- **Fragmented:** Multiple tools/agents with overlapping or missing coverage
- **Non-iterative:** No convergence checking, declares "done" prematurely
- **Context-blind:** Reviews code in isolation without understanding the broader system
- **Checklist theater:** Goes through motions without genuine adversarial thinking
- **Missing concerns:** Doesn't check for technical debt, over-engineering, code smells, security, performance, or architecture

## Success Criteria

A successful review:
- Covers 31 dimensions across 9 categories comprehensively
- Understands codebase context before reviewing
- Iterates until findings converge (Yield% below threshold)
- Applies fixes directly with stratified safety
- Produces actionable output (refined code + report + summary)
- Catches issues that shallow reviews miss

## Key Design Decisions

### 31 Dimensions in 9 Categories

Based on research from ISO/IEC 25010, Martin Fowler's code smells, technical debt classification, and gap analysis of existing pr-review-toolkit agents.

**Mandatory categories:** Correctness, Robustness, Maintainability, Code Health
**Conditional categories:** Security, Performance, Architecture, Testing, Type Design

### Context Phase Before Review

Code cannot be reviewed well in isolation. Dedicated exploration phase:
- Reads project configuration (CLAUDE.md, manifests, configs)
- Explores codebase structure
- Identifies patterns and conventions
- Maps target context (dependencies, callers, role in system)

For large scope, multiple Explore agents deployed in parallel.

### Stratified Fix Safety

Unlike documents, code fixes can break functionality:

| Fix Type | Strategy |
|----------|----------|
| Cosmetic | Apply → Run tests |
| Simplification | Apply → Run tests |
| Behavior-changing | Failing test first → Fix → Verify |
| No test coverage | Defer for user approval |

Inspired by TDD skill's principle: "Tests passing immediately prove nothing."

### Coexist with pr-review-toolkit Agents

Decision: Skill is self-contained, doesn't depend on or orchestrate agents.

**Rationale:**
- Agents don't use Yield%/convergence methodology
- Different depth levels: agents for quick targeted checks, this skill for thorough systematic review
- No coupling means independent evolution

Full analysis: `docs/decisions/2026-01-25-reviewing-code-agent-relationship.md`

## Compliance Risks

What would make Claude rationalize around this skill:

| Risk | Countermeasure |
|------|----------------|
| "Code looks fine" | Require minimum 2 passes, Yield% tracking |
| "Simple code" | Mandatory dimensions regardless of perceived simplicity |
| "Know this codebase" | Context phase required even for familiar code |
| "User wants fast" | Minimum rigor level, compress output not process |
| "Fixed obvious issues" | Cannot exit until Yield% below threshold |
| "Dimension doesn't apply" | Mandatory dimensions defined, N/A requires justification |

## Rejected Approaches

### Orchestrate Existing Agents
- **Why rejected:** Agents don't use Yield%/convergence. Mixing methodologies breaks the skill's core promise of iterative thoroughness.

### Replace Agents Entirely
- **Why rejected:** Agents serve a different purpose (quick targeted checks). Coexistence is better than replacement.

### Apply All Fixes Immediately
- **Why rejected:** Behavior-changing fixes without test verification can break working code. Stratified safety is necessary.

## References

- [Dimension Catalog](../.claude/skills/reviewing-code/references/dimension-catalog.md)
- [Agent Relationship Decision](../decisions/2026-01-25-reviewing-code-agent-relationship.md)
- [ISO/IEC 25010](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010)
- [Martin Fowler - Code Smells](https://martinfowler.com/bliki/CodeSmell.html)
- [Technical Debt Classification](https://www.leanware.co/insights/technical-debt-types-categories)
