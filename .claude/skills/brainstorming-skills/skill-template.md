# Skill Template

A menu of sections for skill assembly. Not all sections apply to every skill — select based on skill type and needs.
Sections marked required MUST be included in EVERY skill. Sections marked optional SHOULD be included in skills ONLY when they provide meaningful value.

```yaml
---
name: <skill-name>
description: <trigger conditions ONLY — when to activate, not what the skill does>
---
```

**Note:** Description frontmatter field should contain:

- Contextual conditions that should activate this skill
- Literal phrases users might say to invoke this skill

---

## Overview (required)

<!-- What is this? Core principle in 1-2 sentences. -->

## Process/Instructions (required)

<!-- How the skill operates. Choose the appropriate form:

**Numbered steps** — Use for strict sequences where order matters and skipping is failure
  Example: Debugging methodology, deployment checklist, processes with dependencies

**Adaptive phases** — Use for dynamic flows where Claude responds to context
  Example: Brainstorming, collaborative dialogue, exploration

**Criteria/framework** — Use for applying standards or patterns
  Example: writing style, coding patterns


Match the form to the skill's nature. Forcing numbered steps on a brainstorming skill makes it worse.

**Task tracking** — For multi-step workflows (>7 steps) or processes that span multiple passes:
- Guide agents to use TaskCreate for each step/dimension (persists across context compaction)
- Include activeForm for meaningful spinner text (e.g., "Checking trigger clarity")
- Include TaskGet guidance for context recovery after compaction
- See skill-writing-guide.md → Task Tracking for Complex Skills -->

## Decision Points (optional)

<!-- Key decision moments and how to handle them:

**Branching logic** — If X, then Y, otherwise Z
  Example: If tests fail, stop and fix before proceeding

**Judgment calls** — When X, weigh Y vs Z based on [criteria]
  Example: When user pushes back, assess whether resistance is valid concern or scope creep

**Escalation triggers** — When to pause and involve the user
  Example: When confidence drops below threshold, flag uncertainty before proceeding -->

## Outputs (optional)

<!-- What the skill produces. May include:
- Artifacts: Files, reports, documents, commands
- Behavior changes: How Claude acts differently
- Decisions: Choices made, recommendations given
- Improved content: Enhanced version of input -->

## Examples (optional)

**Scenario:** <!-- Concrete situation where this skill applies -->

### ❌ BAD: <!-- Brief label for the failure mode -->

<!-- What Claude does/produces without this skill -->

**Why it's bad:**

<!-- Specific reasons this fails — what's missing, wrong, or harmful -->

### ✅ GOOD: <!-- Brief label for the correct behavior -->

<!-- What Claude does/produces with this skill -->

**Why it's good:**

<!-- Specific reasons this works — what the skill ensures -->

## Verification (optional)

How to confirm the skill worked correctly.

**Quick check:**

<!-- Concrete check with expected result -->

## Troubleshooting (optional)

**Symptom:** <!-- What user observes -->
**Cause:** <!-- Specific cause -->
**Next steps:** <!-- Actionable steps -->

<!-- Add multiple symptom/cause/next-steps blocks as needed -->

## Anti-Patterns (required)

**Required.** Common misuses and how to avoid them.

<!-- Pattern: What happens when skill is misused -->
<!-- Why it fails: Why this is wrong -->
<!-- Fix: Correct approach -->

## Rationalizations to Watch For (optional)

**For discipline-enforcing skills only.** Preempt common excuses agents use to skip steps.

| Excuse                          | Reality                 |
| ------------------------------- | ----------------------- |
| <!-- Common rationalization --> | <!-- Why it's wrong --> |

<!-- End with: "**All of these mean: Complete the process. No shortcuts.**" -->
<!-- See skill-writing-guide.md → Persuasion Principles → Rationalization Tables -->

---

# Reference Sections

> **Note:** These sections are scaffolding for drafting. For authoritative quality guidance, read [skill-writing-guide.md](skill-writing-guide.md). Remove everything below before finalizing the skill.

---

## Writing the Description

The description enables skill discovery. It answers **"when should this skill activate?"** — not "what does this skill do?"

### The Rule

**Describe trigger conditions only. Never summarize the skill's process or workflow.**

### Why

When a description summarizes workflow, Claude follows the description instead of reading the full skill.

**Example failure:** A description saying "code review between tasks" caused Claude to perform ONE review. The actual skill required TWO reviews (spec compliance, then code quality). Claude treated the summary as the instruction.

### Good vs Bad

| Good (triggers only)                                                                            | Bad (summarizes workflow)                                                                   |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| "Use when completing a task, before committing, or when code review is requested"               | "Performs two-phase code review checking spec compliance then code quality"                 |
| "Use when Python imports fail, ModuleNotFoundError appears, or circular dependencies suspected" | "Diagnoses import errors by checking sys.path, virtual environments, and dependency graphs" |
| "Use when starting feature work that needs isolation"                                           | "Creates git worktrees with smart directory selection and safety verification"              |

### Include

- Scenarios that trigger activation
- User phrases that should invoke the skill
- Error messages or symptoms
- Keywords for discoverability

### Exclude

- What the skill does internally
- Steps, phases, or workflow
- How it accomplishes its purpose
- Outputs or artifacts produced

---

## Validation Checklist

<!-- Check before finalizing, then remove this section -->

**Essential:**

- [ ] Required sections present: Overview, Triggers OR When to Use, Process, Examples, Anti-Patterns, Troubleshooting, Decision Points
- [ ] Description contains trigger conditions only (no workflow summary)
- [ ] Examples show concrete Before/After — not abstract descriptions
- [ ] Anti-Patterns show pattern + why it fails + fix
- [ ] Troubleshooting has symptom → cause → next steps (not just "if X, do Y")

**Type fit:**

- [ ] Consulted type-example-[your-type].md for type-specific guidance
- [ ] Skill addresses the "Core Question" for its type (see Examples dispatch table)
