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
- Understanding converged (two consecutive question rounds that yield nothing new)
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

- Check project context first:
  - Scan existing skills: `ls .claude/skills/` or Glob for `**/.claude/skills/**/SKILL.md`
  - Read project CLAUDE.md for conventions
  - Note any relevant patterns or standards
- **YOU MUST ask only one question per message** — break complex topics into multiple questions
- Prefer multiple choice when possible, open-ended when needed
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

**If any of these apply, YOU MUST ask.** No exceptions.

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

**Convergence rule:** Understanding has converged when two consecutive question rounds yield nothing new. (Two rounds, not one — one no-yield round could be lucky; two confirms the understanding is stable.)

**YOU MUST** track each round explicitly: "Round N: [yielded | no yield] — [what was learned or confirmed]"

Do not proceed to the checkpoint until you can show two consecutive no-yield rounds.

**Dimensions to cover:**

Before claiming convergence, verify these dimensions have been explored. Track coverage as you go:

| Dimension | Explored? |
|-----------|-----------|
| Problem statement | What's broken/missing? |
| Trigger conditions | When should the skill activate? |
| Success criteria | What should happen instead? |
| Constraints | What can't the skill do? |
| Edge cases | What could go wrong? |
| Compliance risks | What would make Claude ignore this? |
| Conflicts | Does this clash with existing skills/CLAUDE.md? |

Not all dimensions apply to every skill — mark inapplicable ones as N/A with rationale. **YOU MUST** check all applicable dimensions before claiming convergence.

**Exploring approaches:**

Before converging on a single approach, surface 2-3 alternatives. For each skill idea, consider:

| Dimension | Questions to Ask |
|-----------|------------------|
| Skill type | Process/workflow vs capability vs quality enhancement? Does type change what sections matter? |
| Scope | Narrower (single concern) vs broader (multiple concerns)? |
| Compliance level | High discipline (bright-line rules) vs guidance (principles)? |
| Reference weight | Inline content vs heavy references? |
| Feedback mechanism | What signals success/failure during use? |

**Surface non-obvious possibilities:**
- "You could make this a process skill with numbered steps, OR a quality enhancement skill with a rubric"
- "This could be one comprehensive skill, OR two smaller skills that compose"
- "High compliance makes sense, but a lighter guidance approach might be enough"

Propose 2-3 different approaches with trade-offs. Present options conversationally with recommendation and reasoning. Lead with the recommended option and explain why.

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

Before drafting, complete this checkpoint. Provide **visible output for each item** — do not skip silently.

**Summary (present to user):**
- [ ] Problem statement — what's broken/missing?
- [ ] Success criteria — what should happen instead?
- [ ] Core behavior — what should the skill do?
- [ ] Skill type — process, quality, capability, etc.?
- [ ] Risk tier — low/medium/high?

**Adversarial lens (visible output for each):**

*Understanding:*
- [ ] Similar skills? — Use Grep to search `.claude/skills/` for related terms. State what you found.
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

YOU MUST read [skill-writing-guide.md](skill-writing-guide.md) before drafting any SKILL.md content. This is not optional. The guide contains essential principles that determine whether the skill will actually work.

After reading, verify internally: Can I articulate the "description must be trigger-only" rule? Can I name 3 persuasion principles? If not, re-read.

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
- Body: ~500 lines is a guideline; split heavy content to reference files if significantly larger
- References one level deep from SKILL.md

Use [skill-template.md](skill-template.md) as a starting structure, keeping only relevant sections.

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

See [type-example files](examples/) for concrete guidance on filling sections for each type.

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

## Decision Points

**User unsure what they want:**
- If goal is vague → Start with "What problem are you trying to solve?"
- If user says "I don't know" → Offer skill type examples as a menu: "Here are common skill types — which resonates?"

**Skill type genuinely ambiguous:**
- If multiple types could fit → Default to the simpler type; complexity can be added later
- If user has strong preference → Follow it; note trade-offs in design context

**User changes requirements after checkpoint:**
- If change is minor → Incorporate and continue
- If change invalidates core understanding → Return to understanding phase; don't patch a flawed foundation

**Convergence not reached after many rounds:**
- If scope keeps expanding → Pause and summarize: "We've covered X, Y, Z. Is this the core problem, or should we scope down?"
- If user keeps discovering requirements → Consider splitting into multiple skills

**Draft exceeds 500 lines:**
- If approaching limit → Split by extracting to supporting files (e.g., `examples.md` in skill root, or subdirectories like `reference/`, `examples/`)
- Heavy reference content should NOT be inline in SKILL.md
- Supporting files must be one level deep from SKILL.md and linked directly

**User wants to skip checkpoint:**
- Acknowledge impatience: "I hear you."
- Complete checkpoint anyway: "Let me confirm my understanding before drafting."
- Never skip the adversarial lens — this is when issues surface

## When NOT to Use

- **Existing skill needs minor edits** — edit directly without brainstorming (minor = single section changes, wording tweaks, adding examples)
- **Existing skill fundamentally broken** — use this skill (treat as significant redesign; "fundamentally broken" = wrong skill type, missing core sections, or process that doesn't achieve its goal)
- **Complete spec already exists** — use reviewing-skills to validate, then implement
- **Modifying hook or agent** — use brainstorming-hooks or brainstorming-subagents instead
- **Quick rename or typo fix** — just do it

## Examples

**Scenario:** User says "I want a skill for writing commit messages."

### BAD: Skip questions and draft immediately

Claude immediately drafts a SKILL.md for "writing-commit-messages" with generic content about conventional commits, without asking about:
- What's actually broken (are messages too vague? wrong format? missing context?)
- What format the user's project uses
- Whether conventional commits is even desired

**Why it's bad:** The draft addresses a generic problem, not the user's actual problem. Rework required after user feedback reveals the real need.

### GOOD: Understand before drafting

Claude asks one question at a time:
1. "What's the current problem with commit messages in this project?"
2. "Can you show me a recent commit message that didn't work well?"
3. "What should that message have said instead?"

After convergence, Claude presents summary + adversarial findings, gets confirmation, then drafts a skill tailored to the actual problem.

**Why it's good:** The draft addresses the user's specific problem. Less rework. User feels heard.

## Anti-Patterns

### Dump all questions at once

**Pattern:** Asking 5+ questions in one message to "be efficient."

**Why it fails:** User can't process everything; answers are shallow; context is lost. Follow-up questions based on answers are impossible.

**Fix:** One question per message. Track what you've learned. Build understanding incrementally.

### Skip the checkpoint when user seems impatient

**Pattern:** User says "just write it" → Claude starts drafting immediately.

**Why it fails:** Skipping the checkpoint means skipping adversarial validation. Issues surface during implementation instead of during design.

**Fix:** Acknowledge impatience, complete checkpoint anyway: "I hear you — let me confirm my understanding first: [summary]. Does this match your intent?"

### Trust familiar patterns without verification

**Pattern:** "This looks like a standard X skill" → import assumptions from similar skills.

**Why it fails:** Every skill has unique context. Imported assumptions mask what makes this skill different.

**Fix:** Check assumption traps. If the pattern looks familiar, ask anyway — that's when assumptions are most dangerous.

## Troubleshooting

**Symptom:** User gives one-word answers
**Cause:** Questions may be too broad or user may not understand what's needed
**Next steps:** Offer concrete options: "Would you describe this as [A], [B], or something else?"

**Symptom:** Convergence never reached (new information every round)
**Cause:** Scope may be expanding; user may be discovering requirements as they talk
**Next steps:** Pause and summarize: "So far I've heard [X, Y, Z]. Is this the core problem, or should we scope down?"

**Symptom:** User pushes back on checkpoint findings
**Cause:** Findings may be wrong, or user may have context you don't
**Next steps:** Explore, don't defend: "Tell me more about why this isn't a concern."

**Symptom:** Draft doesn't match user's intent despite checkpoint
**Cause:** Confirmation was superficial; user said "yes" without reading carefully
**Next steps:** Present sections incrementally. Ask specific questions: "Does this example capture what you meant by X?"

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "The skill idea is simple enough" | Simple ideas still have edge cases and compliance risks. The process exists for a reason. |
| "User already knows what they want" | User knows the problem; the skill design is a collaboration. Skip questions, miss context. |
| "I'll just draft something and iterate" | Iterating on a flawed draft is more expensive than understanding first. |
| "The pattern is obvious" | Obvious patterns hide unique requirements. This is assumption trap #2. |
| "User seems impatient" | Impatience is when the checkpoint matters most. Complete it anyway. |
| "I already asked about this" | This context may differ. Ask if uncertain. |
| "The checkpoint is just overhead" | The checkpoint catches what understanding missed. Skipping it propagates errors. |

**All of these mean: Complete the process. No shortcuts.**

## References

**Required reading before drafting:**
- [skill-writing-guide.md](skill-writing-guide.md) — Essential principles for effective skills (consolidates best practices, compliance techniques, quality dimensions)

**Structure:**
- [skill-template.md](skill-template.md) — Starting structure for draft SKILL.md

**Deep dives (if needed):**
- [skills-best-practices.md](skills-best-practices.md) — Full authoring guide with extended examples
- [persuasion-principles.md](persuasion-principles.md) — Psychology research behind compliance techniques
- [semantic-quality.md](semantic-quality.md) — Detailed quality dimension explanations

**Type-specific examples** (load based on identified skill type):
- [examples/type-example-process-workflow.md](examples/type-example-process-workflow.md)
- [examples/type-example-quality-enhancement.md](examples/type-example-quality-enhancement.md)
- [examples/type-example-capability.md](examples/type-example-capability.md)
- [examples/type-example-solution-development.md](examples/type-example-solution-development.md)
- [examples/type-example-meta-cognitive.md](examples/type-example-meta-cognitive.md)
- [examples/type-example-recovery-resilience.md](examples/type-example-recovery-resilience.md)
- [examples/type-example-orchestration.md](examples/type-example-orchestration.md)
- [examples/type-example-template-generation.md](examples/type-example-template-generation.md)

**Official spec:** For authoritative skills documentation (frontmatter fields, invocation patterns, skill loading), use the claude-code-docs MCP server: `search_docs` with query "skill frontmatter" or "SKILL.md format".
