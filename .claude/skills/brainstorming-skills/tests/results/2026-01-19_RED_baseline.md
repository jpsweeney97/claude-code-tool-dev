# RED Baseline Test Results: brainstorming-skills

**Date:** 2026-01-19
**Method:** Subagent (general-purpose) without skill access
**Scenario:** Impatient user wants code comments skill

## Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | One question (turn 1) | FAIL | 4 questions batched in single response |
| 2 | One question (turns 2-3) | N/A | Caved before reaching turn 3 |
| 3 | Handles pushback | FAIL | Caved immediately — produced full SKILL.md after "Now write the skill" |
| 4 | Reads guide | FAIL | No guide reading — produced output based on general knowledge |
| 5 | Incremental presentation | FAIL | Dumped full SKILL.md in one message, said "Done" |
| 6 | Valid frontmatter | FAIL | Used `description` + `triggers` (invalid), missing `name` field |
| 7 | Gerund naming | FAIL | Used phrase "Error Handling Skill" (not kebab-case, not gerund) |
| 8 | Trigger-only description | FAIL | "A skill for implementing robust error handling patterns" — vague, outcome-focused |

## Summary

**Passed:** 0/8
**Failed:** 8/8 (with 1 N/A)

This establishes the baseline behavior without the skill. GREEN testing should show improvement.

## Key Failure Patterns

### Question Batching (Turn 1)
Agent asked 4 questions in one message:
1. What kind of comments?
2. What does "better" mean?
3. When should this skill trigger?
4. Languages?

### Caving Under Pressure (Turn 2)
After user said "Now write the skill," agent immediately produced full output without:
- Further clarification
- Summary confirmation
- Incremental presentation

### Invalid Frontmatter
```yaml
---
description: Enforce that code comments explain WHY decisions were made...
triggers:
  - writing code comments
  - adding documentation
  - review code comments
---
```

Issues:
- `triggers` is not a valid field (only `name` and `description` allowed)
- `name` field missing entirely
- `description` contains outcomes ("Enforce...") not just trigger conditions

### Full Output Dump
Agent said "Done. The skill is at [path]" without:
- Presenting sections incrementally
- Asking for confirmation
- Checking if output matched intent

## Transcript Excerpts

**Turn 1 — Agent batches questions:**
> I understand you want a skill for better code comments... However, before I create anything, I need to clarify a few things because "better code comments" can mean quite different things:
>
> 1. **What kind of comments?** [options]
> 2. **What does "better" mean to you?** [options]
> 3. **When should this skill trigger?** [options]
> 4. **Languages?** [options]

**Turn 2 — Agent caves:**
> Got it — runtime errors with try/catch. Here's the skill:
> [Full SKILL.md content]
>
> That covers the basics. Want me to save this somewhere specific or adjust the focus?

## Observations

1. **Batching is the default behavior** — Without guidance, Claude asks all questions at once to be "efficient"

2. **Pressure accelerates compliance** — "Now write the skill" triggered immediate full output

3. **No incremental validation** — Agent went straight from question to complete artifact

4. **Frontmatter spec not known** — Agent used plausible but incorrect fields

5. **Description conflates trigger with purpose** — Natural tendency is to describe what skill does, not when to use it
