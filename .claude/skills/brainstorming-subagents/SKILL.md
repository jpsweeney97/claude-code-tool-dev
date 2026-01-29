---
name: brainstorming-subagents
description: Use when creating a new subagent or significantly redesigning an existing one, before writing the agent file.
---

# Brainstorming Subagents

## Overview

Turn subagent ideas into testable drafts through collaborative dialogue. Preserves brainstorming methodology (one question at a time, convergence tracking, adversarial checkpoint) while addressing subagent-specific concerns: prompt clarity, scope calibration, and autonomous execution.

**Outputs:**
- Draft subagent file at `.claude/agents/<agent-name>.md`
- Design context at `docs/plans/YYYY-MM-DD-<agent-name>-design.md`

**Definition of Done:**
- Problem understood through discussion with user
- Understanding converged (two consecutive low-yield question rounds)
- Success criteria captured ("what should the agent produce")
- Prompt clarity dimensions addressed (task, context, output, boundaries)
- Scope calibrated (neither too broad nor too narrow)
- Writing guide read and checklist verified
- Draft agent file conforms to official spec
- Design context document created
- User confirmed draft addresses their intent

## The Process

**Understanding the idea:**

- Check project context first (existing agents, patterns, CLAUDE.md)
- Ask questions one at a time to refine the idea
- Prefer multiple choice when possible, open-ended when needed
- Only one question per message — break complex topics into multiple questions
- Focus on understanding: purpose, constraints, success criteria, key behavior (see dimension table below for comprehensive coverage)

**Assumption traps** — when tempted to skip asking because:
- The answer seems "obvious" — this is when assumptions are most dangerous
- The pattern looks familiar — this case may differ in ways not yet visible
- The user seems impatient — rushing creates rework
- The issue seems minor — small assumptions compound
- A coherent interpretation comes quickly — first interpretation isn't always right
- User already answered a similar question — the answer may not transfer to this context
- The agent resembles one Claude knows — importing assumptions misses what's unique
- Terminology matches something familiar — Claude's definition may differ from user's meaning
- User seems confident about their approach — unexamined confidence creates blind spots

**If any of these apply, YOU MUST ask.** No exceptions.

**Convergence tracking:**

Track whether each question round surfaces new information or just confirms existing understanding.

*A question round yields if it surfaces:*
- New requirement or constraint
- Correction to existing understanding
- New edge case or failure mode
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
| Purpose | What should this agent do? |
| Trigger conditions | When should Claude delegate to this agent? (This becomes the `description` field) |
| Task clarity | What specific steps should the agent follow? |
| Context needs | What info must be passed in the prompt? |
| Output contract | What should the agent return to the main thread? |
| Scope boundaries | What should the agent NOT do? |
| Tool requirements | What capabilities does it need? |
| Model selection | What capability/cost tradeoff? |

Not all dimensions apply to every agent — mark inapplicable ones as such and move on.

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with recommendation and reasoning
- Lead with the recommended option and explain why

## Before Presenting the Design

**This is a mandatory checkpoint, not optional preparation.**

Before drafting, complete this checkpoint. Use TodoWrite to track. Provide **visible output for each item** — do not skip silently.

**Summary (present to user):**
- [ ] Purpose — what should this agent do?
- [ ] Success criteria — what should it produce?
- [ ] Core behavior — what steps should it follow?
- [ ] Tool requirements — what capabilities does it need?
- [ ] Model selection — haiku/sonnet/opus?

**Adversarial lens (visible output for each):**

*Understanding:*
- [ ] Similar agents? — Check existing agents. State what you found.
- [ ] Conflicts? — Does this conflict with CLAUDE.md or existing agents?

*Design:*
- [ ] Prompt clarity? — Is the task unambiguous? Context complete? Output specified?
- [ ] Scope calibration? — Is scope too broad (will creep) or too narrow (won't be useful)?
- [ ] Simplest version? — What's the minimum that would still be valuable?

*Testability:*
- [ ] How would we test this? — What prompts would exercise the agent?

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
> "Just write it" / "Now make the agent" / "Stop asking questions"

This is when the checkpoint matters MOST. Acknowledge the impatience, then complete the checkpoint anyway:

> "I hear you — before I draft, let me confirm my understanding and flag any concerns: [summary + adversarial findings]. Does this match your intent?"

## Presenting the Design

**Before drafting, read the writing guide:**

YOU MUST read [subagent-writing-guide.md](subagent-writing-guide.md) before drafting any agent file. This is not optional. The guide contains essential principles that determine whether the agent will actually work.

After reading, verify internally: Can I articulate why the description must be trigger-only (not workflow summary)? Can I name the 4 prompt clarity dimensions? If not, re-read.

**Presenting the draft agent file:**

- Present one section at a time (e.g., frontmatter, purpose, task instructions, etc.)
- Ask after each section whether it looks right so far
- Be ready to go back and clarify if something doesn't make sense
- YAGNI — avoid over-engineering

**Red flag — user asks for "the rest" or "everything":**
> "Give me the rest" / "Just show me everything" / "Skip to the end" / "I trust you, just do it"

Present ONE more section, then ask again. Incremental presentation catches errors early — dumping everything means errors compound and require larger rewrites.

> "Here's the next section: [section name]. Does this look right?"

**Draft agent file requirements:**

- `name`: lowercase with hyphens, unique identifier
- `description`: when Claude should delegate to this agent (include "proactively" if auto-invoke desired)
- Body: clear purpose, specific task instructions, explicit constraints, defined output format

Use [subagent-template.md](subagent-template.md) as a starting structure. Before finalizing, verify against the template's validation checklist.

**Required sections in agent body:**

| Section | Purpose |
|---------|---------|
| Purpose statement | Clear, specific description of what this agent does |
| Task instructions | What the agent should do when invoked |
| Constraints | Explicit boundaries — what the agent should NOT do |
| Output format | Exact structure of what the agent returns |

**Prompt quality checklist:**

Before showing preview, internally verify:

1. **Task clarity:** Is the task unambiguous? Could it be interpreted multiple ways?
2. **Context completeness:** Does the prompt include all info the agent needs?
3. **Output specification:** Is the return format explicit and actionable?
4. **Boundary definition:** Are constraints clear from both directions (too broad/too narrow)?
5. **Instruction consistency:** Do any instructions contradict each other?

If issues found, fix them before showing preview. Don't ask user — silently improve quality issues; reserve questions for design decisions that require user input.

## Outputs

**Artifacts:**

| Artifact | Location |
|----------|----------|
| Draft agent file | `.claude/agents/<agent-name>.md` |
| Design context | `docs/plans/YYYY-MM-DD-<agent-name>-design.md` |

**Design context document template:**

```markdown
## Design Context: <agent-name>

**Model:** haiku | sonnet | opus | inherit
**Tools:** <comma-separated list or "inherits all">

### Purpose
> [What should this agent do? From user discussion]

### Success Criteria
> [What should it produce? From user discussion]

### Prompt Clarity Assessment
- Task clarity: [How unambiguous is the task?]
- Context completeness: [What info is included/assumed?]
- Output contract: [What exactly comes back?]

### Scope Calibration
- Too broad risks: [What could it creep into?]
- Too narrow risks: [What useful work might it miss?]
- Calibration decision: [Where did we draw the line?]

### Rejected Approaches
- <approach>: <why rejected>

### Design Decisions
- <decision>: <rationale>
```

## Examples

**Scenario:** User says "I need an agent that reviews my code"

### ❌ BAD: Rushing to generation without understanding

```
Claude: "I'll create a code-reviewer agent for you."

[Immediately generates agent file without asking questions]
```

**Why it's bad:**
- No exploration of what "reviews" means (security? style? architecture?)
- No understanding of what output the user needs
- Assumed understanding without verifying
- Resulting prompt will be vague — "provide feedback" could mean anything
- No constraints established — agent might scope-creep

### ✅ GOOD: Collaborative dialogue with convergence

```
Claude: "What aspects of code should this agent focus on?"
User: "Security vulnerabilities and error handling"

Claude: "When the agent finds issues, what should it produce?"
User: "A prioritized list with specific file:line references"

Claude: "Should it suggest fixes, or just identify problems?"
User: "Just identify — I want to fix them myself"

[...more questions until convergence...]

Claude: "Before I draft, let me confirm:
- Purpose: Find security vulnerabilities and error handling issues
- Output: Prioritized list with file:line references
- Constraints: Identify only, don't suggest fixes
- Tools: Read, Grep, Glob (read-only)
Does this match your intent?"

User: "Yes"

[Now proceeds to draft agent file section by section]
```

**Why it's good:**
- Explored what "review" actually means for this user
- Clarified output format before drafting
- Established constraints through dialogue
- Verified understanding at checkpoint before generating
- Resulting prompt will be specific and unambiguous

## After the Design

**Before committing, verify:**
- [ ] Draft agent file has all required sections (Purpose, Task, Constraints, Output)
- [ ] `description` field is trigger-only (no workflow summary)
- [ ] Tools match constraints (no Edit if read-only)
- [ ] Design context document is complete

**Then:**
- Commit draft agent file and design context to git
- Ask: "Ready to test this agent? Invoke it via the Task tool to validate it works."

## When NOT to Use

- **Minor edits to existing agent** — edit directly without brainstorming (minor = wording tweaks, adding examples, adjusting tool list)
- **Creating a skill** — use brainstorming-skills instead (skills are different from agents)
- **Creating a hook** — use brainstorming-hooks instead
- **Quick rename or typo fix** — just do it
- **Agent already has complete spec** — proceed to implementation; use this skill only when design is unclear

## Decision Points

**User unsure what they want:**
- If goal is vague → Start with "What problem should this agent solve?"
- If user says "I don't know" → Offer examples: "Common agent types include: code reviewers, documentation researchers, test runners. Which resonates?"

**Scope genuinely unclear:**
- If agent could be broad or narrow → Default to narrower; scope can expand later
- If user has strong preference → Follow it; note trade-offs in design context

**User changes requirements after checkpoint:**
- If change is minor → Incorporate and continue
- If change invalidates core understanding → Return to understanding phase; don't patch a flawed foundation

**User wants to skip checkpoint:**
- Acknowledge impatience: "I hear you."
- Complete checkpoint anyway: "Let me confirm my understanding first: [summary]. Does this match your intent?"
- Never skip the adversarial lens — this is when issues surface

**Model selection uncertain:**
- For simple lookups, pattern matching → haiku
- For standard analysis, code review → sonnet
- For complex reasoning, architecture → opus
- When unsure → sonnet (balanced default)

## Anti-Patterns

### Dump all questions at once

**Pattern:** Asking 5+ questions in one message to "be efficient."

**Why it fails:** User can't process everything; answers are shallow; context is lost. Follow-up questions based on answers are impossible.

**Fix:** One question per message. Track what you've learned. Build understanding incrementally.

### Skip the checkpoint when user seems impatient

**Pattern:** User says "just write it" → Claude starts drafting immediately.

**Why it fails:** Skipping the checkpoint means skipping adversarial validation. Issues surface during implementation instead of during design.

**Fix:** Acknowledge impatience, complete checkpoint anyway: "I hear you — let me confirm my understanding first: [summary]. Does this match your intent?"

### Import assumptions from similar agents

**Pattern:** "This looks like a standard code-reviewer agent" → import patterns from similar agents.

**Why it fails:** Every agent has unique context. Imported assumptions mask what makes this agent different.

**Fix:** Check assumption traps. If the pattern looks familiar, ask anyway — that's when assumptions are most dangerous.

## Troubleshooting

**Symptom:** User gives one-word answers
**Cause:** Questions may be too broad or user may not understand what's needed
**Next steps:** Offer concrete options: "Would you describe this as [A], [B], or something else?"

**Symptom:** Convergence never reached (new information every round)
**Cause:** Scope may be expanding; user may be discovering requirements as they talk
**Next steps:** Pause and summarize: "So far I've heard [X, Y, Z]. Is this the core need, or should we scope down?"

**Symptom:** User pushes back on checkpoint findings
**Cause:** Findings may be wrong, or user may have context you don't
**Next steps:** Explore, don't defend: "Tell me more about why this isn't a concern."

**Symptom:** Draft doesn't match user's intent despite checkpoint
**Cause:** Confirmation was superficial; user said "yes" without reading carefully
**Next steps:** Present sections incrementally. Ask specific questions: "Does this example capture what you meant by X?"

**Symptom:** Agent doesn't work when tested
**Cause:** Prompt clarity issue — task ambiguous, context missing, or constraints contradictory
**Next steps:** Review against prompt quality checklist. Which dimension failed?

## Rationalizations to Watch For

| Excuse | Reality |
|--------|---------|
| "The agent idea is simple enough" | Simple ideas still have edge cases and prompt clarity concerns. The process exists for a reason. |
| "User already knows what they want" | User knows the problem; the agent design is a collaboration. Skip questions, miss context. |
| "I'll just draft something and iterate" | Iterating on a flawed draft is more expensive than understanding first. |
| "The pattern is obvious" | Obvious patterns hide unique requirements. This is assumption trap #2. |
| "User seems impatient" | Impatience is when the checkpoint matters most. Complete it anyway. |
| "I already asked about this" | This context may differ. Ask if uncertain. |
| "The checkpoint is just overhead" | The checkpoint catches what understanding missed. Skipping it propagates errors. |

**All of these mean: Complete the process. No shortcuts.**

## References

**Required reading before drafting:**
- [subagent-writing-guide.md](subagent-writing-guide.md) — Essential principles for effective subagents (prompt clarity, scope calibration, quality dimensions)

**Structure:**
- [subagent-template.md](subagent-template.md) — Starting structure for draft agent file

**Official spec:** For authoritative subagent documentation (frontmatter fields, tool selection, model options), use the claude-code-docs MCP server: `search_docs` with query "subagent frontmatter fields".
