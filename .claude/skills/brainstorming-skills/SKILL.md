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
- Problem understood through discussion with user
- Understanding converged (two consecutive low-yield question rounds)
- Success criteria captured ("what should happen instead")
- Skill type identified
- Risk tier assessed
- Compliance risks identified (what might cause agents to rationalize around this?)
- Writing guide read and checklist verified
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

**Convergence tracking:**

Track whether each question round surfaces new information or just confirms existing understanding.

*A question round yields if it surfaces:*
- New requirement or constraint
- Correction to existing understanding
- New edge case or failure mode
- New compliance risk
- Priority change to existing concern

*A question round does NOT yield if it only:*
- Confirms existing understanding ("yes, that's right")
- Adds detail without changing conclusions
- Rephrases what's already known

**Convergence rule:** Understanding has converged when two consecutive question rounds yield nothing new. Do not proceed to checkpoint until converged.

**Dimensions to cover:**

Before claiming convergence, verify these dimensions have been explored:

| Dimension | Explored? |
|-----------|-----------|
| Problem statement | What's broken/missing? |
| Trigger conditions | When should the skill activate? |
| Success criteria | What should happen instead? |
| Constraints | What can't the skill do? |
| Edge cases | What could go wrong? |
| Compliance risks | What would make Claude ignore this? |
| Conflicts | Does this clash with existing skills/CLAUDE.md? |

Not all dimensions apply to every skill — mark inapplicable ones as such and move on.

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with recommendation and reasoning
- Lead with the recommended option and explain why

## Skill-specific Classification

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

**This is a mandatory checkpoint, not optional preparation.**

Before drafting, complete this checkpoint. Use TodoWrite to track. Provide **visible output for each item** — do not skip silently.

**Summary (present to user):**
- [ ] Problem statement — what's broken/missing?
- [ ] Success criteria — what should happen instead?
- [ ] Core behavior — what should the skill do?
- [ ] Skill type — process, quality, capability, etc.?
- [ ] Risk tier — low/medium/high?

**Adversarial lens (visible output for each):**

*Understanding:*
- [ ] Similar skills? — Check search results. State what you found.
- [ ] Conflicts? — Does this conflict with CLAUDE.md or existing skills?

*Design:*
- [ ] Compliance risks? — What would make an agent ignore or rationalize around this?
- [ ] Simplest version? — What's the minimum that would still be valuable?

*Testability:*
- [ ] How would we test this? — What does failure look like without the skill?

**Loop decision:**

After completing the adversarial lens, decide whether to loop back or proceed:

| Finding | Action |
|---------|--------|
| Adversarial check revealed unexplored dimension | → Loop back to understanding |
| Assumption was invalidated | → Revisit affected understanding |
| Neither | → Proceed to presenting |

**Red flag — rushing past the loop decision:**
> "The adversarial check is done, now I'll draft"

If the adversarial lens surfaced anything new, that's a signal to loop back — not to note it and continue. The checkpoint exists to catch what was missed; catching something means there's more to explore.

**Before presenting:**
- [ ] Present summary AND adversarial findings to user
- [ ] Ask: "Does this match your intent?"
- [ ] WAIT for user confirmation — do not present draft until user responds

**Red flag — user pushes to skip ahead:**
> "Just write it" / "Now make the skill" / "Stop asking questions"

This is when the checkpoint matters MOST. Acknowledge the impatience, then complete the checkpoint anyway:

> "I hear you — before I draft, let me confirm my understanding and flag any concerns: [summary + adversarial findings]. Does this match your intent?"

## Presenting the Design

**Before drafting, read the writing guide:**

YOU MUST read [references/skill-writing-guide.md](references/skill-writing-guide.md) before drafting any SKILL.md content. This is not optional. The guide contains essential principles that determine whether the skill will actually work.

**Presenting the draft SKILL.md:**

- Present one section at a time (e.g., frontmatter, overview, when to use, etc.)
- Ask after each section whether it looks right so far
- Be ready to go back and clarify if something doesn't make sense
- YAGNI — avoid over-engineering

**Red flag — user asks for "the rest" or "everything":**
> "Give me the rest" / "Just show me everything" / "Skip to the end"

Present ONE more section, then ask again. Incremental presentation catches errors early — dumping everything means errors compound and require larger rewrites.

> "Here's the next section: [section name]. Does this look right?"

**Draft SKILL.md requirements:**

- `name`: kebab-case, ≤64 chars, gerund form (e.g., `processing-pdfs`, `writing-tests`)
  - ❌ `code-comments` (noun) → ✅ `commenting-code` (gerund)
  - ❌ `error-handler` (noun) → ✅ `handling-errors` (gerund)
- `description`: ≤1024 chars, trigger conditions ONLY, third person
  - Why: Claude may follow the description instead of reading the skill body. A description summarizing workflow causes incomplete execution.
- Body: under 500 lines
- Heavy content split to reference files (one level deep from SKILL.md)

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

### Problem Statement
> [What's broken/missing? From user discussion]

### Success Criteria
> [What should happen instead? From user discussion]

### Compliance Risks
- <What would make an agent rationalize around this?>

### Rejected Approaches
- <approach>: <why rejected>

### Design Decisions
- <decision>: <rationale>
```

## After the Design

- Commit draft SKILL.md and design context to git
- Confirm design context includes: problem statement, success criteria, compliance risks
- Ask: "Ready to test this skill? Use testing-skills to validate it works."

## References

**Required reading before drafting:**
- [references/skill-writing-guide.md](references/skill-writing-guide.md) — Essential principles for effective skills (consolidates best practices, compliance techniques, quality dimensions)

**Structure and spec:**
- [assets/skill-template.md](assets/skill-template.md) — Starting structure for draft SKILL.md
- [references/anthropic-skill-documentation.md](references/anthropic-skill-documentation.md) — Official skill spec and metadata fields

**Deep dives (if needed):**
- [references/skills-best-practices.md](references/skills-best-practices.md) — Full authoring guide with extended examples
- [references/persuasion-principles.md](references/persuasion-principles.md) — Psychology research behind compliance techniques
- [references/semantic-quality.md](references/semantic-quality.md) — Detailed quality dimension explanations

**Type-specific examples** (load based on identified skill type):
- [references/type-example-process-workflow.md](references/type-example-process-workflow.md)
- [references/type-example-quality-enhancement.md](references/type-example-quality-enhancement.md)
- [references/type-example-capability.md](references/type-example-capability.md)
- [references/type-example-solution-development.md](references/type-example-solution-development.md)
- [references/type-example-meta-cognitive.md](references/type-example-meta-cognitive.md)
- [references/type-example-recovery-resilience.md](references/type-example-recovery-resilience.md)
- [references/type-example-orchestration.md](references/type-example-orchestration.md)
- [references/type-example-template-generation.md](references/type-example-template-generation.md)
