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

## When to Use

- Creating skills that enforce discipline (TDD, verification, process compliance)
- High-risk skills: security, agentic workflows, data operations
- Skills where behavior change must be verified, not assumed
- Skills with complex requirements needing dialogue to surface
- Skills that will be maintained long-term (audit trail valuable)
- When you need traceability: requirement → test → behavior change

**Symptoms that suggest this skill:**
- "I need to make sure agents actually follow this"
- "This is important enough to test properly"
- "I want to know it works, not hope it works"
- "Multiple stakeholders need to agree on requirements"

## When NOT to Use

- Simple technique documentation (use skillosophy instead)
- Low-risk, read-only skills
- One-off internal tools with clear requirements
- Time-constrained situations where speed trumps rigor
- Skills where structure matters more than behavior (use skillosophy instead)
- Modifying rigorous-skill-creation itself (circular dependency)