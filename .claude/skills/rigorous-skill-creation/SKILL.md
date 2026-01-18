---
name: rigorous-skill-creation
description: Use when creating skills that need verified behavior change, especially
  high-risk skills (security, agentic, data operations) or skills that enforce discipline.
hooks:
  PostToolUse:
    - matcher: 'Write|Edit'
      hooks:
        - type: command
          command: '${SKILL_ROOT}/scripts/validate_skill.sh'
          once: true
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
  - TodoWrite
user-invocable: true
metadata:
  version: '0.1.0'
  category: meta-skills
  risk_tier: 'Medium — creates artifacts that affect other workflows'
---

# rigorous-skill-creation

Orchestrated skill creation with structured requirements dialogue, baseline testing, and risk-based panel review. Creates skills with verified behavior change.

## Triggers

- "create a skill rigorously"
- "new skill with testing"
- "rigorous skill creation"
- "skill with pressure testing"
- "create a validated skill"
- "TDD skill creation"
- "skill with verification"
