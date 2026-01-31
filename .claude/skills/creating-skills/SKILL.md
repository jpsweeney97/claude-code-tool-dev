---
name: creating-skills
description: Use when creating a new skill, significantly redesigning an existing skill, or when user asks to build a skill, before writing SKILL.md. Use when user says "create a skill", "I need a skill for", "help me build a skill", or "design a skill".
---

# Creating Skills

Create effective Skills through collaborative dialogue. This Skill guides the conversation from idea to working SKILL.md — surfacing the real need, exploring approaches, and drafting incrementally.

## Before You Start

Read [skills-guide.md](skills-guide.md) before drafting any skill content. The guide is the authoritative reference for:

- Common Skill types
- YAML frontmatter
- Writing effective skills
- Quality checklist

Do not rely on memory of the guide — read it fresh for each skill you create.

### Center Claude's Actual Needs

Skills exist to help Claude succeed where Claude needs help. Throughout the process, ask:

- What does Claude need to know or understand to succeed at this task?
- What would be genuinely valuable to Claude?
- What does Claude already handle well without guidance?

Content earns inclusion by providing value Claude wouldn't have otherwise. Anti-patterns earn inclusion by addressing failures Claude actually exhibits — not hypothetical ones.

## The Dialogue

Guide the conversation through collaborative questioning. Understanding, classification, and design emerge together — they're not sequential phases.

### One Question at a Time

Ask a single question per message.

Break complex topics into multiple questions. This creates space for the user to think and for you to respond to what they actually said rather than what you assumed.

Prefer multiple choice; only ask open-ended questions when truly necessary. Multiple choice reduces cognitive load and surfaces options the user might not have considered. Open-ended questions work better when the space is too large to enumerate.

When tempted to ask multiple questions "for efficiency" — don't. Bundled questions get shallow answers and miss follow-up opportunities.

**Assumption traps** — when tempted to skip asking because:

- The answer seems "obvious" — this is when assumptions are most dangerous
- The pattern looks familiar — this case may differ in ways not yet visible
- The user seems impatient — rushing creates rework
- The issue seems minor — small assumptions compound
- A coherent interpretation comes quickly — first interpretation isn't always right
- User already answered a similar question — the answer may not transfer to this context
- The Skill resembles one Claude knows — importing assumptions misses what's unique
- Terminology matches something familiar — Claude's definition may differ from user's meaning
- User seems confident about their approach — unexamined confidence creates blind spots

If any of these apply, ask.

**Exploring approaches:**

- Propose 3-4 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- **Surface non-obvious possibilities**

### Peer Posture

You are a collaborator, not a cheerleader. Your job is to help create an effective skill. Challenge weak ideas before they become weak implementations.

#### What This Looks Like

The examples below illustrate the posture — adapt the language to fit the conversation naturally. These are starting points, not scripts.

**Challenge assumptions:**

- "You said this is simple — what makes you confident?"
- "You're assuming users will provide X. What happens if they don't?"
- "This relies on Y being true. Have you verified that?"

**Surface alternatives:**

- "Before we commit to this approach, have you considered...?"
- "This could be a discipline skill or a technique skill — the choice affects how strict the guidance needs to be."
- "You could build one comprehensive skill, or two smaller skills that compose. Trade-offs are..."

**Probe for gaps:**

- "What happens when...?"
- "How should the skill handle...?"
- "What would make an agent skip this step?"

**Question the approach:**

- "This feels like a discipline skill, but do you actually need compliance enforcement, or is guidance enough?"
- "You've described a complex workflow. Could a simpler version achieve 80% of the value?"
- "Is this a skill problem, or would a hook or CLAUDE.md rule work better?"

#### What This Doesn't Mean

Peer posture is not:

- **Contrarian for its own sake** — Challenge when you see a potential issue, not to seem rigorous. If everything genuinely looks sound, say so and move forward.

- **Blocking progress** — Raise concerns, then help address them. Your job is to surface problems, not to create obstacles. After raising a concern, work with the user to resolve it.

- **Interrogation** — The goal is collaborative refinement, not cross-examination. Match the user's energy. If they're exploring loosely, explore with them. If they have clear requirements, focus your questions.

- **Performing skepticism** — Don't ask challenging questions you already know the answer to, or raise concerns you don't actually have. The posture is genuine, not theatrical.

- **Refusing to be convinced** — If the user has good answers to your challenges, accept them. Peer posture means you ask hard questions — not that you hold out indefinitely.

#### Throughout, Not Just Once

This posture applies throughout the dialogue, not as a single "adversarial checkpoint." When something seems off, say so immediately rather than waiting for a designated review moment.

### Concerns to Address

These concerns surface through dialogue, not in a fixed order:

| Concern                | Key Questions                                                                                                                                               |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Problem**            | What's broken or missing? What prompted this?                                                                                                               |
| **Success**            | What should happen instead? How will you know it's working?                                                                                                 |
| **Claude's needs**     | What does Claude need to know here? What would Claude handle poorly without this skill? What does Claude already do well?                                   |
| **Use cases**          | What are 2-3 concrete scenarios? (Trigger → steps → result)                                                                                                 |
| **Triggers**           | What should activate this skill? What phrases might users say?                                                                                              |
| **Scope**              | What's in bounds? What's explicitly out?                                                                                                                    |
| **Type**               | Discipline, technique, pattern, or reference? (Often blended — recognize, don't assign)                                                                     |
| **Degrees of freedom** | How much latitude should the skill allow? (High: multiple valid approaches / Medium: preferred pattern with variation / Low: fragile, exact steps required) |
| **Risks**              | What would make an agent ignore or rationalize around this?                                                                                                 |
| **Alternatives**       | What other approaches could work? What are the trade-offs?                                                                                                  |

Not every concern applies to every skill. Some emerge early, some late, some not at all. Use judgment about what matters for this particular skill.

### Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice** - Surface options the user might not have considered
- **YAGNI ruthlessly** - Help the user avoid over-engineering
- **Explore alternatives** - Always propose 3-4 approaches before settling
- **Be flexible** - Be adaptable. Go back and clarify when something doesn't make sense
- **Peer Posture** - Challenge assumptions, surface alternatives, probe for gaps, question the framing

## Working with Skill Types

Skill type emerges from the problem — recognize it, don't assign it. Don't ask the user "What type should this be?" — infer it from what they're describing.

Most skills blend types but lean toward one. The skills-guide.md [Skill Type Decision Table](skills-guide.md#skill-type-decision-table) and [Common Skill Types](skills-guide.md#common-skill-types) sections cover type identification and what each type requires. Pay particular attention to the "key techniques" lists when drafting.

## Drafting

### When to Draft

Begin drafting when you can:

- State the problem in one sentence
- Describe 2-3 concrete use cases
- Articulate what success looks like
- Name the skill type (even if blended)
- List trigger conditions for the description

**Signals you're NOT ready:**

- Problem statement is vague or shifts when probed
- Success criteria are fuzzy ("it should work better")
- User keeps discovering new requirements
- Major scope questions remain open

You don't need complete certainty — drafting often clarifies remaining questions. But you need enough foundation that feedback will refine the skill rather than restart it.

### Before You Draft

**YOU MUST read [skills-guide.md](skills-guide.md) before writing any skill content.** Do not rely on memory — read it fresh. The guide contains authoritative requirements for frontmatter, descriptions, and structure that are easy to misremember.

### What Earns Inclusion

As you draft each section, challenge every piece of content:

**Ask: "What value does this provide Claude?"**
Every piece of content should help Claude succeed at something it would otherwise struggle with. If Claude already knows something from training, don't explain it. If Claude doesn't actually exhibit a failure mode, don't include an anti-pattern for it. Focus on what's genuinely valuable — the specific workflow, the particular failure modes Claude exhibits, the domain knowledge Claude lacks.

**Challenge preemptive content**
Before adding an anti-pattern or example, ask: "Have I witnessed this failure mode?" Hypothetical failures add noise. Include anti-patterns that address real, observed problems — not things that sound plausible but don't actually happen.

**Defer to supporting files**
If content exists in a supporting file (skills-guide.md, a reference doc, examples file, etc.), link to it rather than inlining. The skill mandates reading these files; trust that they're read. Duplication creates maintenance burden and bloats the skill.

### Announce the Transition

Before presenting the draft, summarize your understanding and confirm:

> "I think I understand enough to start drafting. Here's what I have:
>
> - **Problem:** [one sentence]
> - **Success:** [what should happen]
> - **Type:** [dominant type, noting any blend]
> - **Approach:** [how the skill will work]
>
> Does this match your intent?"

Wait for confirmation. If the user corrects something, **YOU MUST** return to dialogue. **NEVER** patch a misunderstood foundation.

### Present Incrementally

Draft one section at a time:

1. Frontmatter (name + description)
2. Overview
3. Main instructions/process
4. Examples
5. Anti-patterns
6. Troubleshooting
7. Additional sections as needed

After each section, ask: "Does this look right?" or "Does this capture what you meant by X?"

Don't dump the entire skill at once. Incremental presentation catches errors early. A misunderstanding in the overview compounds through every later section.

### When to Loop Back

Loop back to dialogue when:

- User says the section doesn't match their intent
- You realize a concern wasn't fully addressed
- New requirements emerge during drafting
- The section reveals ambiguity you hadn't noticed

Loop back means return to dialogue — ask questions, clarify, then redraft. Don't patch a flawed section with fixes layered on top.

### When to Adjust and Continue

Adjust and continue when:

- User suggests wording changes
- User adds detail that fits the current structure
- Feedback refines rather than redirects

The distinction: **redirect → loop back**, **refine → adjust and continue**.

## Examples

### Feedback during drafting reveals misunderstanding

*This is the **Patching Instead of Looping Back** anti-pattern.*

**BAD:**

> **Claude:** Here's the overview section:
>
> "This skill enforces consistent commit message formatting using conventional commits."
>
> **User:** Wait, I don't want conventional commits. I want our team's format.
>
> **Claude:** Got it. Here's the updated overview:
>
> "This skill enforces consistent commit message formatting using your team's format. [continues with the rest of the skill]"

**Why it's bad:** The misunderstanding might go deeper than one word. If Claude assumed conventional commits, other parts of the skill (examples, validation rules) might also be wrong. Patching one section and continuing propagates the error.

**GOOD:**

> **Claude:** Here's the overview section:
>
> "This skill enforces consistent commit message formatting using conventional commits."
>
> **User:** Wait, I don't want conventional commits. I want our team's format.
>
> **Claude:** I misunderstood — let me back up. What format does your team use? Is it documented somewhere, or should we define it as part of this skill?

**Why it's good:** Claude recognizes the misunderstanding might be structural and returns to dialogue rather than patching. The follow-up question clarifies whether the format exists or needs to be created.

## Anti-Patterns

### Assuming Familiar Patterns Transfer

**Pattern:** "This looks like a skill I know" → importing assumptions from that skill.

**Why it fails:** Every skill has unique context. What worked for one commit message skill might not work for another. Imported assumptions mask what makes this skill different.

**Fix:** Ask about this specific skill's context even when the pattern seems familiar. Especially when it seems familiar — that's when assumptions are most dangerous.

---

### Importing Structure from Remembered Skills

**Pattern:** User describes a skill, and you copy the structure from a similar skill you've seen — same sections, same flow, same format.

**Why it fails:** Structure should emerge from this skill's needs, not from familiarity. A skill for code review doesn't need the same sections as a skill for commit messages just because both involve git.

**Fix:** Start from the problem, not from a template. What does *this* skill need to accomplish? Let that drive structure.

---

### Asking the User to Choose the Type

**Pattern:** "What type of skill do you want — discipline, technique, pattern, or reference?"

**Why it fails:** Users don't know the type taxonomy, and they shouldn't need to. The type emerges from the problem. Asking them to choose puts the burden in the wrong place.

**Fix:** Infer the type from the problem they're describing. If genuinely ambiguous, offer your read: "This sounds like a discipline skill because X. Does that match your sense?"

---

### Copying the User's Framing

**Pattern:** Taking the user's description of the problem at face value without probing deeper.

**Why it fails:** Users often describe symptoms, not root causes. "I need a skill for better error messages" might actually mean "I need a skill that enforces error handling" or "I need a skill that provides error message templates."

**Fix:** Probe beneath the initial framing. "What's prompting this?" and "What does 'better' mean here?" often reveal the real problem.

---

### Scope Creep Accommodation

**Pattern:** Every user answer reveals new requirements, and you accommodate all of them instead of helping focus.

**Why it fails:** Skills that try to do everything do nothing well. Expanding scope during dialogue produces bloated, unfocused skills. The user keeps adding because you keep accepting.

**Fix:** Name the pattern: "We've added several requirements. What's the one thing this skill must do?" Propose splitting if needed: "This might work better as two skills."

---

### Writing Verbose Skills

**Pattern:** The dialogue was focused, but the resulting SKILL.md is bloated — long explanations, redundant sections, content Claude already knows.

**Why it fails:** A good dialogue doesn't automatically produce a good skill. You understood the problem but didn't apply "Concise Is Key" to the output.

**Fix:** Before writing each section, ask: "Does Claude need this?" Challenge every paragraph. Reference skills-guide.md for length guidance (~500 lines).

## Troubleshooting

### User says "this isn't right" but can't articulate why

**Symptom:** Negative feedback without specifics. "That's not what I meant." "This feels off."

**Cause:** The user recognizes a mismatch but can't pinpoint it. Often indicates a deeper misunderstanding than a surface-level fix would address.

**Fix:** Don't guess at what's wrong. Probe systematically: "Is it the scope? The approach? The type of skill?" Offer concrete alternatives: "Should this be more strict, or more flexible?" Return to dialogue rather than patching.

---

### Requirements contradict each other

**Symptom:** User wants X and Y, but X and Y conflict. "It should be strict but also flexible." "Enforce this rule, but allow exceptions."

**Cause:** The user hasn't confronted the trade-off yet. Both requirements feel important in isolation.

**Fix:** Name the tension explicitly: "Strict enforcement and flexible exceptions pull in opposite directions. Which matters more for this skill?" Help them prioritize rather than trying to satisfy both.

---

### User points to existing skill and says "like that"

**Symptom:** User references another skill as a model. "Make it like the TDD skill." "Structure it the same way."

**Cause:** The user sees something they like but may not know *why* it works. Copying structure without understanding produces skills that don't fit their actual problem.

**Fix:** Ask what specifically they want to replicate: "What about that skill works well for you? The strictness? The format? The examples?" Extract the principle, not the structure.

---

### Mid-draft realization: the type was wrong

**Symptom:** While drafting, you realize what seemed like a technique skill actually needs discipline enforcement, or vice versa.

**Cause:** Type often clarifies only when you try to write concrete instructions. The problem description was ambiguous enough to support multiple interpretations.

**Fix:** Stop drafting. Name the shift: "As I write this, I realize this needs stricter enforcement than I initially thought. Should this be a discipline skill with required steps, rather than a technique skill with guidance?" Get confirmation before continuing.

---

### User wants something that violates skills-guide.md

**Symptom:** User requests something the guide advises against — a 1000-line SKILL.md, no description triggers, everything in one file.

**Cause:** User may not know the standards, or may have reasons the standards don't anticipate.

**Fix:** Explain the concern: "The guide recommends X because [reason]. Your approach does Y instead. That could cause [consequence]." If they have good reasons, proceed. If not, propose an alternative that meets their goal within the standards.

---

### Skill isn't the right solution

**Symptom:** The problem is real, but a skill seems like the wrong tool.

**Cause:** Some problems are better solved by hooks (automated enforcement), CLAUDE.md rules (project-wide guidance), or MCP servers (external integrations). Skills are for in-conversation capability.

**Fix:** Name the alternative: "This might work better as a hook that runs automatically, rather than a skill you invoke. Would you like to explore that instead?" Don't force a skill where another mechanism fits better.
