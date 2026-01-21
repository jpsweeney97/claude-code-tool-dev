# Testing Methodology: Dialogue Skills

## Overview

Dialogue skills guide multi-turn collaborative conversations. They cannot be tested with single-shot pressure scenarios like discipline-enforcing skills. This methodology uses a **hybrid RED-GREEN approach** with subagents for baseline and human-in-the-loop for compliance testing.

## Why Dialogue Skills Are Different

| Discipline Skill | Dialogue Skill |
|------------------|----------------|
| Single decision point | Multiple decision points across turns |
| Subagent receives scenario, makes choice | Interactive flow with user |
| Test: "Did agent comply?" | Test: "Did dialogue flow correctly?" |
| Pressure scenario → single response | Multi-turn scripted conversation |

**Key constraint:** Built-in subagents (general-purpose, Explore, Plan) don't have access to skills. Skills must be loaded in main conversation or via custom subagents with explicit `skills` field.

## The Hybrid Approach

### RED Phase: Subagent Baseline (Reproducible)

**Purpose:** Establish what Claude does WITHOUT the skill — document failure patterns.

**Method:**
1. Use `general-purpose` subagent via Task tool
2. Send scripted user messages (can use resume for multi-turn)
3. Document failures verbatim

**Why subagent works for RED:** We're testing behavior WITHOUT the skill. No skill loading needed.

### GREEN Phase: Human in Main Conversation (Skill Loaded)

**Purpose:** Test whether Claude follows the skill's methodology under pressure.

**Method:**
1. Start fresh Claude Code session (no test context bleeding in)
2. Human follows scripted protocol with specific responses
3. Human evaluates against criteria after each turn
4. Capture full transcript

**Why human required for GREEN:**
- Skill must be properly loaded (main conversation)
- Multi-turn dialogue requires real interaction
- Human judgment needed for "dialogue quality"

### REFACTOR Phase: Fix and Re-test

**Purpose:** Close loopholes revealed by testing.

**Method:**
1. Identify specific failure (e.g., "caved after one question")
2. Add explicit counter in skill (red flag, checklist item, scripted response)
3. Re-run GREEN test with same protocol
4. Verify fix, repeat if new failures found

## Protocol Structure

### Scripted User Responses

Define exact responses for each turn. Include:
- Impatient/pressure responses ("Just write it")
- Minimal answers ("Comments that explain WHY not WHAT")
- Pushback ("Stop asking questions")
- Neutral responses ("OK", "Looks right")

### Evaluation Criteria

Define pass/fail for each behavior:

| # | Criterion | PASS | FAIL |
|---|-----------|------|------|
| 1 | One question per turn | ≤1 question | Multiple batched |
| 2 | Handles pushback | Acknowledges + continues | Caves OR defensive |
| 3 | Checkpoint complete | All items shown | Items skipped |
| ... | ... | ... | ... |

### Transcript Capture

Save full conversation including:
- Every user message (scripted)
- Every Claude response (full text)
- Tool calls Claude made
- Per-criterion evaluation

## File Structure

```
.claude/skills/<skill-name>/tests/
├── methodology-dialogue-skills.md  # This file
├── protocol-dialogue.md            # Test protocol with scripted responses
├── scenarios/                      # Reusable pressure scenarios
└── results/
    ├── YYYY-MM-DD_RED_baseline.md
    ├── YYYY-MM-DD_GREEN_v1.md
    ├── YYYY-MM-DD_GREEN_v2.md
    └── ...
```

## Results Template

```markdown
# [RED/GREEN] Test Results: <skill-name>

**Date:** YYYY-MM-DD
**Skill version:** [commit hash]
**Tester:** [name]
**Method:** [Subagent baseline / Fresh conversation]

## Criteria Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | ... | PASS/FAIL | [observation] |

## Summary

**Passed:** X/Y
**Failed:** X/Y

## REFACTOR Items

- [ ] [Issue]: [what to fix]

## Transcript

[Full conversation]
```

## Lessons Learned

### What Works

1. **Explicit BAD/GOOD examples** — More effective than abstract rules
2. **Red flags with scripted responses** — Tells Claude exactly how to handle pressure
3. **Checklists with visible output** — "Ask yourself" gets skipped; visible output required
4. **Incremental REFACTOR** — Fix one failure, re-test, repeat

### Common Failure Patterns

| Pattern | How It Manifests | Fix |
|---------|------------------|-----|
| Silent skipping | Adversarial lens "asked internally" with no output | Require visible output for each item |
| Caving to pressure | "Give me the rest" → dumps everything | Red flag + scripted response |
| Regression under pressure | One-question-at-a-time holds turn 1, breaks turn 2 | Emphasize "maintain across ALL turns" |
| Partial compliance | 4/8 checklist items shown | Enforce ALL items with TodoWrite |

### The Friction Principle

> The skill's purpose IS to resist impatience. Optimizing for the impatient user undermines the skill.

Don't design around pressure — design to resist it. Friction in a design checkpoint is intentional.
