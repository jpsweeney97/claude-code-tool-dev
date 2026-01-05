---
name: brainstorming-skills
description: Use when designing a new skill, "design a skill for X",
  "what should this skill contain", "skill scope", "skill triggers",
  or after brainstorming-plugins identifies a skill is needed.
  Guides collaborative skill design through 6-step process.
---

# Skill Design

Turn skill ideas into design documents through collaborative dialogue.

## Quick Start

```
User: "I need a skill for X"
Claude: Uses skillforge methodology (default)

1. Core purpose (2-3 questions)
2. Trigger design (3-5 phrases)
3. Knowledge scope (in/out boundaries)
4. Structure decisions (SKILL.md, references, scripts)
5. Composition check (related skills)
6. Present design in sections, validate each
7. Write design document → handoff to implementing-skills
```

## Triggers

- `design a skill for {purpose}`
- `what should this skill contain`
- `skill scope` / `skill boundaries`
- `skill triggers` / `when should this skill activate`
- `brainstorm a skill` (after triage)

## Prerequisites

Before using this skill, you should:
- Know you need a skill (from `/brainstorming-plugins` or direct knowledge)
- Understand the problem you're solving

No design document? This skill creates one.

## Pipeline Context

This skill is **Stage 2: Design** in the plugin development pipeline.

| Aspect | Value |
|--------|-------|
| This stage | Design skill from requirements |
| Previous | `/brainstorming-plugins` (or direct request) |
| Next | `/implementing-skills` |

**Full pipeline:** See `references/pipeline-overview.md` in brainstorming-plugins.

## Quick Reference

| Design Area | Key Question | Output |
|-------------|--------------|--------|
| Purpose | What can Claude NOT do without this? | 1-2 sentence statement |
| Triggers | What phrases activate it? | 3-5 distinct phrases |
| Scope | What's in AND out? | Boundary list |
| Structure | What goes where? | SKILL.md outline + reference/script needs |
| Composition | How does it fit the ecosystem? | Related skills, conflicts |

## The Process

**Default:** Use skillforge methodology for all skills. This ensures rigor.

**Announce at start:** "Using skillforge methodology to design this skill."

### Step 1 of 6: Core Purpose

Ask one question at a time:
- What specific knowledge does this skill provide?
- What can Claude NOT do well without this skill?
- Who benefits? (Claude operating better? User getting guidance? Both?)

**Output:** 1-2 sentence purpose statement

Example: "This skill teaches Claude how to write effective git commit messages following conventional commit format, preventing vague or non-standard commits."

### Step 2 of 6: Trigger Design

| Aspect | Questions |
|--------|-----------|
| Activation | What phrases should trigger this skill? |
| Symptoms | What problems indicate this skill is needed? |
| Boundaries | What should NOT trigger it? |

**Target:** 3-5 distinct trigger phrases covering different phrasings of same need.

**Quality check:** Would Claude find this skill when needed? Test mentally against likely user queries.

Example triggers for a git commit skill:
- `write a commit message`
- `commit this change`
- `conventional commit format`
- `git commit best practices`

### Step 3 of 6: Knowledge Scope

| Boundary | Define Explicitly |
|----------|-------------------|
| IN scope | What this skill covers (be specific) |
| OUT of scope | What this skill does NOT cover (equally important) |
| Adjacent | Related skills that handle nearby concerns |

**Why out-of-scope matters:** Unbounded skills bloat and become unfocused. Explicit boundaries prevent scope creep.

Example for git commit skill:
- **IN:** Commit message format, conventional commit types, body vs title
- **OUT:** Git branching strategy, PR descriptions, changelog generation
- **Adjacent:** git-workflow skill (if exists)

### Step 4 of 6: Structure Decisions

| Component | Decision | Size Target |
|-----------|----------|-------------|
| SKILL.md body | Core workflow, must be self-sufficient | 1,500-2,000 words |
| references/ | Deep docs loaded on demand | Unlimited |
| scripts/ | Deterministic/repeated operations | As needed |
| examples/ | Working code to copy/adapt | As needed |

**Key principle:** SKILL.md must be self-sufficient for executing the skill. References answer "tell me more about X," not "what's the next step."

### Step 5 of 6: Composition

- What skills might be used alongside this one?
- Does this skill depend on or reference others?
- Any overlap or conflict with existing skills?

**Check existing skills:** Search for similar triggers before finalizing.

### Step 6 of 6: Present Design

Present in 200-300 word sections:
1. **Purpose & Triggers** — What it does, how it activates
2. **Scope** — In/out boundaries
3. **Structure** — SKILL.md outline, references, scripts
4. **Composition** — Related skills, dependencies

After each section: "Does this look right so far?"

Be ready to revise based on feedback.

## Output

Write validated design to: `docs/plans/YYYY-MM-DD-<skill-name>-design.md`

**Use template:** `references/design-template.md`

**Design document includes:**
- Purpose statement
- Trigger phrases (3-5)
- Scope boundaries (in/out)
- SKILL.md outline
- Reference/script/example needs
- Composition notes
- Open questions (if any)

## Next Step

After saving the design document, run:

```
/implementing-skills docs/plans/YYYY-MM-DD-<skill-name>-design.md
```

Replace the path with your actual design document location.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Skipping scope boundaries | Leads to bloated, unfocused skills | Define OUT as carefully as IN |
| Generic triggers | Skill won't activate when needed | 3-5 specific, varied phrases |
| SKILL.md depends on references | User can't execute without loading more | SKILL.md self-sufficient |
| Designing in isolation | May duplicate existing skills | Check ecosystem early |
| Skipping composition check | Causes conflicts and confusion | Identify related skills |

## Verification

Before completing, confirm:

| Check | Status |
|-------|--------|
| Purpose statement (1-2 sentences) | Defined |
| Why it's specific, not generic | Explained |
| 3-5 trigger phrases | Listed |
| Triggers cover different phrasings | Confirmed |
| IN scope (3+ items) | Listed |
| OUT of scope (3+ items) | Listed |
| SKILL.md outline | Drafted |
| Similar existing skills checked | Done |
| Design document saved | Path confirmed |

## Key Principles

- **One question at a time** — Don't overwhelm
- **Boundaries matter** — OUT of scope prevents bloat
- **Triggers determine discoverability** — Test them mentally
- **Self-sufficient SKILL.md** — References add depth, not steps
- **Check the ecosystem** — Avoid duplicates and conflicts
- **Validate incrementally** — Present in sections, confirm each

## References

- skill-development — Structural reference (file format, directories)
- skillforge — Deep analysis methodology (used by default)
- implementing-skills — TDD implementation workflow (next stage)
- brainstorming-plugins/references/pipeline-overview.md — Full pipeline
