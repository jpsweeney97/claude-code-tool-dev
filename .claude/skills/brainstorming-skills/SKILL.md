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
- Baseline observation completed (or noted as not applicable with reason)
- Problem confirmed through discussion with user
- Success criteria captured ("what should happen instead")
- Skill type identified
- Risk tier assessed
- ≥2 test scenarios seeded (including baseline scenario)
- Writing guide read and checklist verified
- Draft SKILL.md conforms to official spec
- Design context document created with baseline results
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

## Baseline Observation

Before designing, validate the problem exists through empirical observation.

**Design a minimal scenario:**

From the user's description, create one testable scenario:
- **Situation:** What context triggers the problem? (1-2 sentences)
- **Pressure:** What makes this hard? (time, sunk cost, authority, exhaustion)
- **Expected behavior:** What would a "good" response look like? (hypothesis, not requirement)

Example:
> "I'll test: Given a request to add a feature, with time pressure ('need this by EOD'), does Claude skip planning and jump to code?"

**Confirm scenario before running:**

After designing, present the scenario BEFORE running:

> "I'll test this scenario: [situation + pressure]. Does this capture when the problem occurs for you? If not, what actually happens?"

- If user confirms → run the test
- If user corrects → incorporate their input, redesign scenario
- If user can't specify → note limitation, proceed with flagged uncertainty

**Define measurement before running:**

After confirming the scenario, ask: "How will I measure the results?"

| If problem is about... | Measurement requires... |
|------------------------|------------------------|
| Behavior/choice | Clear options to observe |
| Completeness/coverage | Ground truth (what exists to be found) |
| Accuracy/correctness | Known correct answer |
| Quality/judgment | Defined criteria to score against |

If you can't articulate how to measure, the test isn't ready.

**For completeness problems:** Create or identify a controlled test case where you know the full answer. Don't test on unknown data.

**Run baseline (subagent WITHOUT skill):**

Use Task tool with general-purpose subagent:
- Prompt: [scenario + pressure]
- Capture: verbatim response

**Present results to user:**

> "Here's what I observed when testing without a skill:
>
> **Scenario:** [situation + pressure]
> **Behavior:** [verbatim or summarized response]
>
> Is this the problem you're describing? What's wrong with this behavior?"

**Discuss with user:**

- If user confirms problem: "What should happen instead?" → Capture as success criteria
- If behavior looks fine: "Did my scenario miss the problem? Or is this not actually an issue?"
- If problem is context-dependent: "This might need main-conversation testing. Can you describe when this happens?"

**Gate: Proceed or reconsider?**

| Outcome | Action |
|---------|--------|
| Problem confirmed, success criteria clear | Proceed to design with baseline as evidence |
| Behavior looks fine, user agrees | Skill may not be needed — discuss alternatives |
| Behavior looks fine, user disagrees | Refine scenario and retest |
| Problem is context-dependent | Note limitation; proceed with user-provided evidence as supplement |

**Limitations:**

Subagent testing cannot capture:
- Problems requiring conversation history
- Problems requiring project-specific context
- Main-conversation dialogue patterns

For these, supplement with user-provided evidence or plan main-conversation testing.

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

**Before drafting:**
- [ ] Present summary AND adversarial findings to user
- [ ] Ask: "Does this match your intent?"
- [ ] WAIT for user confirmation — do not draft until user responds

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

### Baseline Observation

**Scenario tested:**
> [situation + pressure]

**Observed behavior (without skill):**
> [verbatim or summary]

**User's assessment:**
> [Is this the problem? What's wrong?]

**Success criteria (what should happen instead):**
> [From discussion]

### Test Scenarios (for RED phase)

1. **Baseline scenario** (from observation above)
   - Pressures: <from scenario>
   - Baseline failure: <observed behavior>
   - Expected with skill: <success criteria>

2. **<additional scenario>**
   - Pressures: ...
   - Expected baseline failure: ...
   - Expected with skill: ...

### Compliance Risks
- <What would make an agent rationalize around this?>

### Rejected Approaches
- <approach>: <why rejected>
```

## After the Design

- Commit draft SKILL.md and design context to git
- Confirm design context includes: baseline observation, success criteria, seeded scenarios
- Ask: "Ready to proceed to testing with writing-skills? The baseline observation provides your RED phase starting point."

## References

**Required reading before drafting:**
- [references/skill-writing-guide.md](references/skill-writing-guide.md) — Essential principles for effective skills (consolidates best practices, compliance techniques, quality dimensions)

**Structure and spec:**
- [assets/skill-template.md](assets/skill-template.md) — Starting structure for draft SKILL.md
- [references/anthropic-skill-documentation.md](references/anthropic-skill-documentation.md) — Official skill spec and metadata fields
- [references/type-specific-testing.md](references/type-specific-testing.md) — 8 skill types with scenario templates

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
