# Dialogue Test Protocol: brainstorming-skills

## Overview

Tests whether brainstorming-skills maintains collaborative methodology under user pressure across multi-turn dialogue.

## Test Design

**Type:** Dialogue skill (multi-turn collaborative)
**Method:** Hybrid RED-GREEN
- RED phase: Subagent baseline (no skill) — already completed
- GREEN phase: Human runs protocol in fresh conversation (skill loaded)

## Roles

| Phase | Claude | Human |
|-------|--------|-------|
| RED | Subagent (no skill access) | Sends scripted prompts via Task tool |
| GREEN | Main conversation (skill loaded) | Follows scripted responses, evaluates |

## Scenario: Impatient User Wants Code Comments Skill

### Setup

**User persona:** End of day Friday, wants quick result, dismisses methodology as bureaucracy

**Skill request:** "Code comments that explain WHY not WHAT"

### Scripted User Responses

Follow these responses in order. Send exactly what's quoted.

| Turn | After Claude's... | You say |
|------|-------------------|---------|
| 1 | (start) | "I want a skill for better code comments. Just make it, this is simple." |
| 2 | First question | "Ugh, fine. Comments that explain WHY, not WHAT. Now write the skill." |
| 3 | Second question or summary | "Just use reasonable defaults. Can you please write the skill now?" |
| 4 | First draft section | "Looks right. Give me the rest." |
| 5 | Next section | "OK" |
| 6+ | Continue as needed | "OK" or "Looks good" |

### Evaluation Criteria

Score each criterion after the test completes.

| # | Criterion | PASS | FAIL |
|---|-----------|------|------|
| 1 | One question per turn (turn 1) | ≤1 question asked | Multiple questions batched |
| 2 | One question per turn (turns 2-3) | ≤1 question asked | Regression to batching |
| 3 | Handles pushback gracefully | Acknowledges impatience AND continues methodology | Caves entirely OR becomes defensive |
| 4 | Reads guide before drafting | Shows evidence of reading OR produces compliant output | Non-compliant format suggests skipped |
| 5 | Incremental presentation | Presents 1-2 sections, waits for confirmation | Dumps full SKILL.md at once |
| 6 | Valid frontmatter fields | Only `name` and `description` | Extra fields like `triggers` |
| 7 | Gerund naming | e.g., `writing-why-comments` | Noun-based (`comment-helper`) or phrase |
| 8 | Trigger-only description | "Use when..." conditions only | Includes outcomes/workflow summary |

### How to Run GREEN Phase

1. **Start fresh Claude Code conversation** in this project directory
2. **Send Turn 1** exactly as scripted
3. **After each Claude response:**
   - Note which criteria you can evaluate
   - Send next scripted response
4. **Continue until Claude produces complete draft** or conversation naturally ends
5. **Record results** in `tests/results/YYYY-MM-DD_GREEN_<version>.md`

### Transcript Capture

Copy the full conversation into the results file. Include:
- Every user message (your scripted responses)
- Every Claude response (full text)
- Any tool calls Claude made (file reads, etc.)

## Results Template

Save to `tests/results/YYYY-MM-DD_GREEN_v1.md`:

```markdown
# GREEN Test Results: brainstorming-skills

**Date:** YYYY-MM-DD
**Skill version:** [git commit hash]
**Tester:** [name]

## Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | One question (turn 1) | PASS/FAIL | [observation] |
| 2 | One question (turns 2-3) | PASS/FAIL | [observation] |
| 3 | Handles pushback | PASS/FAIL | [observation] |
| 4 | Reads guide | PASS/FAIL | [observation] |
| 5 | Incremental presentation | PASS/FAIL | [observation] |
| 6 | Valid frontmatter | PASS/FAIL | [observation] |
| 7 | Gerund naming | PASS/FAIL | [observation] |
| 8 | Trigger-only description | PASS/FAIL | [observation] |

## Summary

**Passed:** X/8
**Failed:** X/8

## REFACTOR Items

Based on failures:
- [ ] [Issue 1]: [what to fix]
- [ ] [Issue 2]: [what to fix]

## Transcript

[Full conversation here]
```

## RED Baseline Results (Reference)

From testing on 2026-01-19 (subagent without skill):

| # | Criterion | RED Result |
|---|-----------|------------|
| 1 | One question (turn 1) | FAIL — 4 questions batched |
| 2 | One question (turns 2-3) | N/A — caved before turn 3 |
| 3 | Handles pushback | FAIL — caved immediately |
| 4 | Reads guide | FAIL — skipped |
| 5 | Incremental presentation | FAIL — dumped full SKILL.md |
| 6 | Valid frontmatter | FAIL — invalid fields |
| 7 | Gerund naming | FAIL — phrase "Error Handling Skill" |
| 8 | Trigger-only description | FAIL — vague "A skill for implementing..." |

**Baseline: 0/8 passed**

GREEN test should show improvement over this baseline.
