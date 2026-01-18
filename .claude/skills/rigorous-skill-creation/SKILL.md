---
name: rigorous-skill-creation
description: Use when creating skills that need verified behavior change, especially high-risk skills (security, agentic, data operations) or skills that enforce discipline.
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
  version: '0.2.0'
  category: meta-skills
  risk_tier: 'Medium — creates artifacts that affect other workflows'
---

# Rigorous Skill Creation

Create skills with verified behavior change through collaborative dialogue, baseline testing, and iterative refinement.

## Overview

Help turn skill ideas into fully-formed, tested skills through natural collaborative dialogue.

Start by understanding what the skill needs to accomplish, then explore approaches together. Once we understand what we're building, test that the skill actually changes behavior — don't assume it works.

## The Process

**Understanding the skill:**

- Ask questions one at a time to understand the skill's purpose
- Prefer multiple choice questions when possible
- Focus on: what behavior should change, when it applies, what failure looks like
- Check for existing skills that might overlap (run triage script if available)

**Exploring the design:**

- Propose 2-3 approaches with trade-offs
- Lead with your recommendation and explain why
- Identify risk tier: Low (read-only), Medium (code generation), High (security/agentic/data)

**Testing behavior change (the core discipline):**

- Before writing the skill: run pressure scenarios WITHOUT the skill to capture baseline failures
- After writing: run same scenarios WITH the skill to verify it actually changes behavior
- If no baseline failure exists, the skill may not be needed

**Presenting the skill:**

- Break into sections of 200-300 words
- Ask after each section whether it looks right
- Cover all 11 required sections (see `references/section-checklists.md`)

## Key Principles

- **One question at a time** — Don't overwhelm with multiple questions
- **Test before trusting** — Baseline failures prove the skill is needed; verification proves it works
- **Capture rationalizations verbatim** — The exact words agents use to bypass rules become anti-patterns
- **Pressure scenarios need teeth** — Combine 3+ pressures, force A/B/C choice, no escape routes

## After Understanding: The Phases

Once we understand what we're building, follow these phases:

1. **Requirements Discovery** — Apply thinking lenses, categorize requirements, assess risk tier
2. **Specification Checkpoint** — Summarize requirements, get user validation before proceeding
3. **Baseline Testing (RED)** — Run scenarios WITHOUT skill, capture failures and rationalizations
4. **Generation** — Write skill sections incrementally, validate each against checklist
5. **Verification (GREEN)** — Run same scenarios WITH skill, verify behavior changed
6. **Refactor** — Close loopholes found in verification, add counters to anti-patterns
7. **Panel Review** — For Medium/High risk: launch 4 parallel review agents
8. **Finalization** — Validate structure, remove session state, confirm completion

Detailed phase procedures: `references/phase-procedures.md`

## Decision Points

| Situation | Action |
|-----------|--------|
| Existing skill ≥80% match | Recommend it; ask to proceed or create anyway |
| Existing skill 50-79% match | Offer MODIFY or CREATE |
| Baseline shows no failures | Strengthen pressures; if still none, reconsider need |
| Agent fails despite skill | Run meta-test: "How could the skill be clearer?" |
| Panel agents contradict | Present both views; user decides |

Risk tier determines panel requirement:
- **Low** (read-only, docs): Skip panel
- **Medium** (code gen, refactoring): Panel required
- **High** (security, agentic, data): Panel required

## Outputs

**Primary:** `SKILL.md` with 11 sections + frontmatter + embedded metadata

**Supporting (as needed):**
- `references/` — Heavy material that would bloat SKILL.md
- `examples/` — Usage examples, worked walkthrough
- `scripts/` — Executable tools the skill needs

**Verification evidence embedded in metadata:**
- Baseline scenarios run and failures observed
- Rationalizations captured verbatim
- Verification pass/fail counts
- Panel status

## When NOT to Use

- Simple technique documentation (use skillosophy)
- Low-risk, read-only skills where verification adds no value
- Time-constrained situations where speed trumps rigor
- Modifying rigorous-skill-creation itself (circular dependency)

## Reference Files

- `references/phase-procedures.md` — Detailed step-by-step for each phase
- `references/section-checklists.md` — Required content per section
- `references/thinking-lenses.md` — 14 lenses for requirements discovery
- `references/testing-methodology.md` — How to construct pressure scenarios
- `references/panel-protocol.md` — How panel review works
- `references/risk-tiers.md` — Risk assessment criteria
- `references/troubleshooting.md` — Common issues and recovery
