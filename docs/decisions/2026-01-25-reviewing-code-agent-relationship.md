# Decision Record: reviewing-code Skill Relationship to Existing Agents

**Date:** 2026-01-25
**Status:** Decided
**Stakes:** Rigorous

## Decision Statement

How should the new reviewing-code skill relate to the existing pr-review-toolkit agents (silent-failure-hunter, type-design-analyzer, pr-test-analyzer, comment-analyzer, code-reviewer, code-simplifier)?

## Context

We're designing a "state-of-the-art" code review skill with:
- 31 dimensions in 9 categories
- Iterative convergence methodology (Yield%)
- Fixes applied directly (like reviewing-documents)

The pr-review-toolkit plugin has 6 specialized agents that cover some of the same concerns (error handling, test coverage, comments, types).

## Constraints

- Must achieve comprehensive 31-dimension coverage
- Must use iterative convergence methodology throughout
- Skill should be self-contained and usable without plugin dependencies
- Existing agents are in a separate plugin

## Criteria (Weighted)

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Comprehensiveness | 5 | Must cover all 31 dimensions |
| Methodology consistency | 5 | Must use Yield%/convergence throughout |
| Maintainability | 4 | Changes to one component shouldn't break others |
| Reuse of proven logic | 3 | Don't reinvent what works |
| Simplicity | 3 | Fewer moving parts = fewer failure modes |

## Options Considered

### Option 1: Replace
Skill handles all 31 dimensions directly. Existing agents become obsolete.

### Option 2: Orchestrate
Skill dispatches to existing agents for dimensions they cover, handles rest directly.

### Option 3: Coexist (Selected)
Skill is self-contained with full methodology. Agents remain as independent tools for quick targeted checks.

### Option 4: Hybrid
Skill handles all dimensions directly, optionally invokes agents as "second opinion."

### Option 5: Null
Defer decision, build skill without considering agents.

## Evaluation

| Option | Comp. (5) | Method. (5) | Maint. (4) | Reuse (3) | Simple (3) | Total |
|--------|-----------|-------------|------------|-----------|------------|-------|
| Replace | 5 | 5 | 4 | 1 | 4 | 78 |
| Orchestrate | 5 | 2 | 2 | 5 | 2 | 60 |
| **Coexist** | **5** | **5** | **5** | **2** | **5** | **86** |
| Hybrid | 5 | 5 | 3 | 3 | 3 | 76 |
| Null | 3 | 5 | 4 | 1 | 5 | 70 |

## Decision

**Coexist independently.**

The reviewing-code skill will be fully self-contained, handling all 31 dimensions with the iterative convergence methodology. It does not depend on or dispatch to pr-review-toolkit agents.

Existing agents remain useful as separate tools for quick, targeted checks when users don't need full systematic review.

## Rationale

1. **Methodology consistency**: Agents don't use Yield%/convergence. Orchestrating them would break the skill's core promise of iterative thoroughness.

2. **Not duplication**: Different tools for different needs:
   - reviewing-code: thorough, iterative, 31 dimensions, convergence-based
   - Agents: quick, single-pass, narrow focus

   Like having both a comprehensive health checkup and a quick blood pressure check.

3. **Maintainability**: No coupling means changes to agents don't break the skill and vice versa.

4. **Self-contained**: Skill works without pr-review-toolkit installed.

## Trade-offs Accepted

- **Lower reuse score**: We're implementing error handling, test coverage, type design checks ourselves rather than calling existing agents. This means more code to maintain in the skill.

- **Potential user confusion**: Users must understand when to use the skill vs agents. Mitigation: clear documentation in skill's "When to Use" section.

## Risks

- Users may not understand the distinction → Document clearly
- Agents evolve with better logic we don't inherit → Accept; methodology consistency is worth more than marginal logic improvements

## What Would Change This

- If agents adopted Yield%/convergence methodology, orchestration would become viable
- If maintaining dimension logic in the skill proves too burdensome, reconsider hybrid approach

## Iteration Log

| Pass | Frontrunner | Key Finding |
|------|-------------|-------------|
| 1 | Coexist (86) | Orchestrate breaks methodology; Replace scores lower on maintainability |
| 2 | Coexist (86) | Confirmed: "coexist" means different depth levels, not duplication |

## Stakeholder Perspectives

- **User**: Gets comprehensive reviews from skill, quick checks from agents — clear value proposition for each
- **Skill maintainer**: No external dependencies to break
- **Agent maintainer**: Agents remain independent, can evolve freely
