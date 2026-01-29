# Decision Record: Skill Template Structure

**Date:** 2026-01-29
**Status:** Decided
**Stakes:** Rigorous
**Decision:** How to structure the three skill templates (reference, task, methodology)

## Context

The current `skill-template.md` has 7+ required sections, but:
- Official `api-conventions` example is 5 lines total
- Skill types table says Reference skills need "Clarity only" and should avoid all persuasion
- Audit of brainstorming-subagents revealed "concerns over structure" principle

Need to design three type-specific templates that reduce friction while preventing failure modes.

## Decision Questions

1. **Placeholder content vs structure-only:** How much guidance to include in templates?
2. **Section header prescriptiveness:** Mandate headers or just concerns?
3. **Handling hybrid skills:** How to address skills that span types?

## Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Alignment with official docs | 5 | Templates shouldn't require more than official examples show is valid |
| Friction reduction | 4 | Creating a skill should feel lightweight for simple skills |
| Failure prevention | 4 | Templates should guide toward quality, prevent common mistakes |
| Learnability | 3 | New users should understand what each template is for |
| Flexibility | 3 | Templates shouldn't over-constrain valid approaches |

## Decisions

### Q1: Placeholder Content vs Structure-Only

**Decision:** Hybrid approach

**Options evaluated:**
| Option | Score | Notes |
|--------|-------|-------|
| Rich placeholders | 55 | Over-constrains, encourages fill-in-blank mentality |
| Structure-only | 68 | Misses opportunity to guide required concerns |
| **Hybrid** | **69** | Required concerns get brief guidance; optional sections are headers only |
| Null (single template) | 37 | Doesn't solve the friction problem |

**Trade-offs accepted:**
- Slightly more complex than structure-only
- Requires maintaining guidance per type

**Why:** Different skill types have genuinely different needs. Reference skills need almost no guidance, methodology skills need guardrails. Hybrid matches this reality.

### Q2: Section Header Prescriptiveness

**Decision:** Required concerns, suggested headers

**Options evaluated:**
| Option | Score | Notes |
|--------|-------|-------|
| Required headers | 47 | Over-constrains; conflicts with official examples |
| **Required concerns** | **72** | Specifies what must be addressed, flexible on how |
| Fully flexible | 59 | Insufficient guidance; skills may miss critical content |
| Type-specific headers | 66 | Adds learning cost (three different systems) |

**Trade-offs accepted:**
- Less consistency in skill structure
- Validation harder (check concerns, not headers)

**Why:** The subagent audit showed official examples work without formal headers. Prescribing headers creates friction without improving quality. "Address these concerns" is simpler to teach than "use these exact headers."

### Q3: Handling Skills That Span Types

**Decision:** Guidance in brainstorming-skills SKILL.md, not a fourth template

**Options evaluated:**
| Option | Score | Notes |
|--------|-------|-------|
| Primary type + additions | 69 | Reasonable but adds complexity to templates |
| Composite template | 51 | Fourth template for rare case; adds learning cost |
| **Guidance in SKILL.md** | **72** | Appropriate place for edge case handling |
| Null | 51 | Leaves creators without guidance |

**Trade-offs accepted:**
- Edge case handling requires reading SKILL.md, not just template
- Brainstorming-skills bears responsibility for type selection guidance

**Why:** Hybrid skills are rare. A fourth template adds complexity for an edge case. Guidance like "If your skill has both reference content AND a process, start with task template" is clearer and keeps templates simple.

## Implementation

### Template Structure

| Template | Concerns | Guidance Level |
|----------|----------|----------------|
| `template-reference.md` | Name, description, content | Minimal — just frontmatter + content |
| `template-task.md` | Name, description, when to use, steps, verification | Moderate — brief guidance on required concerns |
| `template-methodology.md` | Current full template | Full — detailed guidance, all sections |

### Validation Approach

Instead of checking for headers, validation checks for concerns addressed:
- Reference: Does it provide the knowledge?
- Task: Are steps clear? Is invocation context specified?
- Methodology: Are failure modes addressed? Anti-patterns? Troubleshooting?

### Anti-Creep Measures

Include in minimal templates:
```markdown
<!-- DO NOT ADD: Process, Decision Points, Examples, Anti-Patterns, Troubleshooting, Rationalizations -->
<!-- Reference skills are knowledge, not workflows. If you need these sections, use template-task or template-methodology. -->
```

## Iteration Log

| Pass | Frame Changes | Frontrunners | Key Findings |
|------|---------------|--------------|--------------|
| 1 | Initial | C (Hybrid), B (Concerns), C (SKILL.md guidance) | Scored against criteria |
| 2 | None | Same | Integration check passed; frontrunners consistent |

## Caveats

- If users consistently struggle with concerns-based validation, may need to add suggested headers
- If hybrid skills become common, may need to revisit fourth template decision
