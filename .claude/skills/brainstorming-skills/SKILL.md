---
name: brainstorming-skills
description: "Use when creating a new skill or significantly redesigning an existing one, before writing SKILL.md."
---

# Brainstorming Skills

## Overview

Turn skill ideas into testable drafts through collaborative dialogue. Preserves brainstorming methodology (one question at a time, 2-3 approaches, incremental validation) while weaving in skill-specific concerns.

**Outputs:**
- Draft SKILL.md at `.claude/skills/<skill-name>/SKILL.md`
- Design context at `docs/plans/YYYY-MM-DD-<skill-name>-design.md`

**Definition of Done:**
- Problem summary confirmed by user
- Skill type identified
- Risk tier assessed
- ≥2 test scenarios seeded
- Draft SKILL.md conforms to official spec
- Design context document created
- User confirmed draft addresses their intent

## The Process

**Understanding the idea:**

- Check project context first (existing skills, patterns, CLAUDE.md)
- Ask questions one at a time to refine the idea
- Prefer multiple choice when possible, open-ended when needed
- Only one question per message — break complex topics into multiple questions
- Focus on understanding: purpose, constraints, success criteria, key behavior

**Assumption traps** — when tempted to skip asking because:
- The answer seems "obvious" — this is when assumptions are most dangerous
- The pattern looks familiar — this case may differ in ways not yet visible
- The user seems impatient — rushing creates rework
- The issue seems minor — small assumptions compound
- A coherent interpretation comes quickly — first interpretation isn't always right
- User already answered a similar question — the answer may not transfer to this context
- The skill resembles one Claude knows — importing assumptions misses what's unique
- Terminology matches something familiar — Claude's definition may differ from user's meaning
- User seems confident about their approach — unexamined confidence creates blind spots

If any of these apply, ask anyway.

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with recommendation and reasoning
- Lead with the recommended option and explain why

**Skill-specific classification:**

During the dialogue, identify (through conversation, not by asking directly unless genuinely ambiguous):

- **Skill type** — which fits best:
  - Process/workflow — enforces step sequence
  - Quality enhancement — makes output "better" along defined dimensions
  - Capability — enables something Claude couldn't do before
  - Solution development — guides problem analysis and solution selection
  - Meta-cognitive — helps recognize own state
  - Recovery/resilience — handles failures gracefully
  - Orchestration — coordinates multiple sub-skills or workflows
  - Template/generation — produces specific output formats
  - Other — note what aspects matter for testing

- **Risk tier:**
  - Low — read-only, reversible, no external deps
  - Medium — writes files, bounded and reversible
  - High — security, data, ops, costly to reverse

## Before Presenting the Design

- Summarize understanding: problem, success criteria, key constraints, skill type, risk tier
- Apply adversarial lens — actively challenge the understanding:
  - What requirement might be misunderstood?
  - What constraint could make this approach unworkable?
  - What's the simplest version that would still be valuable? Is this over-engineered?
  - What similar skill might already exist?
- Surface any concerns explicitly: "I'm uncertain about X" or "I may be assuming Y"
- Ask user to confirm or correct before proceeding

## Presenting the Design

**Presenting the draft SKILL.md:**

- Once understanding is confirmed, present a draft SKILL.md
- Present one section at a time (e.g., frontmatter, overview, when to use, etc.)
- Ask after each section whether it looks right so far
- Be ready to go back and clarify if something doesn't make sense
- YAGNI — avoid over-engineering

**Draft SKILL.md requirements:**

- `name`: kebab-case, ≤64 chars, matches directory
- `description`: ≤1024 chars, triggering conditions only (NOT workflow summary)
  - Why: Claude may follow the description instead of reading the skill body. A description summarizing workflow can cause Claude to execute an incomplete version of the skill.
- Body: under 500 lines, essential instructions
  - See [references/persuasion-principles.md](references/persuasion-principles.md) and [references/semantic-quality.md](references/semantic-quality.md) for writing guidance
- Heavy content identified for reference files

Use [assets/skill-template.md](assets/skill-template.md) as a starting structure, keeping only relevant sections.

**Section relevance by skill type** (guidance, not strict):

| Type | Emphasize |
|------|-----------|
| Process/workflow | Process (numbered steps), Decision Points (step failures) |
| Quality enhancement | Process (criteria/framework), Outputs (quality dimensions) |
| Capability | Process (domain knowledge), Troubleshooting (diagnostic branching) |
| Solution development | Process (analysis framework), Decision Points (tradeoffs) |
| Meta-cognitive | Process (recognition + response), Decision Points (thresholds) |
| Recovery/resilience | Process (failure handling), Decision Points (recovery strategy) |
| Orchestration | Process (phase structure), Decision Points (transitions) |
| Template/generation | Process (format spec), Outputs (field requirements) |

*For meta-cognitive and recovery skills, reframe "Triggers" as recognition patterns or failure signals.

**Required (all types):** Overview, Triggers OR When to Use, Process, Examples, Anti-Patterns, Troubleshooting, Decision Points
**Optional:** Outputs, Verification, Extension Points

See [type-example files](references/) for concrete guidance on filling sections for each type.

**Seeding test scenarios:**

As requirements emerge, capture scenarios for the testing phase:

- For each key behavior: "What would failure look like without this skill?"
- How might an agent rationalize ignoring this guidance?
- At least 2 scenarios that demonstrate the skill's value

See [references/type-specific-testing.md](references/type-specific-testing.md) for type-appropriate scenario templates.

## Outputs

**Artifacts:**

| Artifact | Location |
|----------|----------|
| Draft SKILL.md | `.claude/skills/<skill-name>/SKILL.md` |
| Design context | `docs/plans/YYYY-MM-DD-<skill-name>-design.md` |

**Design context document template:**

```markdown
## Design Context: <skill-name>

**Type:** <one of 8 types>
**Risk:** Low | Medium | High

### Test Scenarios
1. <scenario name>: <what it tests>
2. <scenario name>: <what it tests>

### Rejected Approaches
- <approach>: <why rejected>
```

## After the Design

- Commit draft SKILL.md and design context to git
- Ask: "Ready to proceed to testing with writing-skills?"

## References

- [assets/skill-template.md](assets/skill-template.md) — Starting structure for draft SKILL.md
- [references/anthropic-skill-documentation.md](references/anthropic-skill-documentation.md) — Official skill spec and metadata fields
- [references/type-specific-testing.md](references/type-specific-testing.md) — 8 skill types with scenario templates
- [references/persuasion-principles.md](references/persuasion-principles.md) — For discipline-enforcing skills
- [references/semantic-quality.md](references/semantic-quality.md) — 9 quality dimensions for skill bodies

**Type-specific examples** (load based on identified skill type):
- [references/type-example-process-workflow.md](references/type-example-process-workflow.md)
- [references/type-example-quality-enhancement.md](references/type-example-quality-enhancement.md)
- [references/type-example-capability.md](references/type-example-capability.md)
- [references/type-example-solution-development.md](references/type-example-solution-development.md)
- [references/type-example-meta-cognitive.md](references/type-example-meta-cognitive.md)
- [references/type-example-recovery-resilience.md](references/type-example-recovery-resilience.md)
- [references/type-example-orchestration.md](references/type-example-orchestration.md)
- [references/type-example-template-generation.md](references/type-example-template-generation.md)
