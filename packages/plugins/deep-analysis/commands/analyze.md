---
name: analyze
description: Start a structured deep analysis session for complex decisions
argument-hint: problem or question to analyze
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - TodoWrite
  - mcp__deep-analysis__*
---

# Deep Analysis

Conduct a structured analysis for a complex decision.

**Topic:** $ARGUMENTS

## Instructions

1. Invoke the `deep-analysis` skill and follow its process exactly
2. Work through all 5 stages with user checkpoints
3. Apply all 6 analytical frameworks during investigation
4. Save the analysis document when complete (with user permission)

## If No Arguments Provided

Ask the user what they want to analyze:

> What decision or problem would you like to analyze? This works best for:
> - Architectural decisions with multiple valid approaches
> - Strategic trade-offs ("should we X or Y?")
> - Technology or approach evaluation

## Key Reminders

- Search for prior art before starting fresh analysis
- Ask clarifying questions one at a time
- Apply ALL 6 frameworks during investigation
- Get user confirmation at each checkpoint
- Offer to save the analysis when complete
