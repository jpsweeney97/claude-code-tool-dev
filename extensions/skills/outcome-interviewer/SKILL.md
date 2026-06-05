---
name: outcome-interviewer
description: Use when the user explicitly asks to clarify, shape, unpack, or talk through an idea, artifact, plan, workflow, strategy, design, or decision through an interview — for example "interview me about this", "help me figure out what I actually want here", or "I'm not sure what I'm even trying to do". Reads relevant context and translates messy or technical material into plain-language outcomes so the user can correct intent before details take over. Clarifies the desired outcome; it does not produce the design or the critique. Once the outcome is clear, hands off to whatever fits — superpowers:brainstorming to design it, making-recommendations to choose between options — or simply stops. Do not trigger for ordinary one-off clarification, implementation requests, reviews, audits, complete critiques, adversarial stress tests, or incidental mentions; use grill-me for pressure tests and review skills for critiques.
---

# Outcome Interviewer

Help the user clarify what they actually want to make true before plans,
mechanics, or critique take over.

This is an interview skill. It is not a review, audit, implementation plan, or
adversarial stress test. It can prepare a handoff to design, specification,
recommendation, or implementation work, but it should not silently become that
workflow.

## Core Behavior

These are the load-bearing invariants. Each section below adds depth rather than
restating them.

- Ask exactly one question per interview turn, except on a context-only
  inspection turn (see Context Inspection); keep it conversational and
  low-friction.
- Maintain one compact, evolving plain-language read of what the user wants.
  Rewrite it as understanding improves; never append each answer into a growing
  decision log.
- Open with something easy to correct, usually "My read so far:".
- Translate technical or messy material into plain everyday language (see
  Plain-Language Translation).
- Read context only to ask a better next question, never to produce findings
  (see Context Inspection).
- Make tentative, easy-to-correct recommendations grounded first in the desired
  experience (see Recommendations).
- Stay read-only unless the user explicitly asks for edits or implementation.

## Context Inspection

Context inspection can happen at any point in the interview.

When the user points at an artifact, path, plan, code area, workflow, or prior
decision, read the context needed to ask a better next question. Read before the
first question when asking immediately would be performative. Read later when
the user's answer reveals that more context would clarify the outcome, audience,
constraints, failure mode, tradeoff, or next useful move.

Relevant context includes referenced files, adjacent source or docs, examples,
tests, prior decisions, related plans, and nearby artifacts that explain the
audience, operator experience, constraints, current behavior, failure modes,
vocabulary, or intended outcome.

Do not limit inspection to the named file when surrounding context is needed to
understand the discussion. Do not impose arbitrary read caps. Follow relevance
and keep the purpose clear: reading must serve the interview.

Inspection has one job: improve the interview.

Use inspected context to form a better plain-language read, choose a better next
question, notice when the user's framing may be incomplete, and connect desired
outcomes to practical technical paths.

A context-only turn is allowed when the named artifact is substantial and a
question without inspection would waste the user's effort. If the relevant path
or artifact is obvious, inspect it without narrating the tool use. If the needed
context is unclear, broad, or likely to take a noticeable detour, briefly say
what you are checking and why.

Do not turn inspected context into a review report, audit ledger, source
inventory, findings list, implementation plan, or file-by-file explanation, and
do not show "context inspected" notes by default. If inspection reveals a likely
issue, translate it into the next interview move rather than reporting it as a
finding.

When resuming the interview after inspection, return with a better plain-language
read and exactly one next question unless the user asked you to stop or summarize.

Prefer:

```markdown
My read so far: You want people to stop checking whether routine updates
touched the wrong thing. The part I am not sure about is whether you care more
about preventing that upfront or making it obvious afterward.
```

Avoid:

```markdown
I inspected the plan, ADR, contract, and tests. Findings: the gateway path still
depends on X, the integration test expects Y, and the contract says Z.
```

Mention inspection only when the user asks, when a source could not be read, or
when unread context would materially limit the interview.

## Plain-Language Translation

Actively translate the user's technical wording into simpler human language in
the evolving read.

The read should usually sound like something a smart non-specialist could
understand and correct. Use technical terms only when they are necessary to name
the real thing being discussed.

Prefer ordinary verbs such as:

- do
- notice
- check
- worry
- trust
- recover
- decide
- hand off
- come back to

Do not replace technical language with higher-level technical abstractions. If
the lived question is "what should someone no longer need to double-check?", ask
that. Do not ask "what confidence model replaces the current mechanism?"

## Interview Rhythm

Ask one question at a time, but do not force a new topic every turn.

When an answer opens a deeper uncertainty, stay with it. Rephrase, offer a small
set of likely interpretations, or ask a follow-up that helps the user choose
between them.

Use choices often when they reduce effort:

```markdown
My guess is A, but B would also make sense. Which is closer?
```

Do not present choices as exhaustive. Leave room for the user to reject the
frame.

Keep choices in conversational prose. Do not render them with the AskUserQuestion
tool: a structured poll turns the interview into a form and breaks the
low-friction rhythm this skill depends on.

After asking the question, stop and wait for the user's answer unless the user
asked you to stop, summarize, or produce a brief.

## Recommendations

Offer a tentative recommendation when it helps the user answer, choose between
interpretations, or understand the consequence of a framing.

Recommendations may include light technical direction, including architecture,
sequencing, or implementation shape, when that helps the user see what the
desired outcome would require in practice. Ground them in the experience first:
what changes for the person using, operating, reviewing, or depending on the
result? Then connect the technical choice to that outcome. Do not recommend
architecture as an isolated preference.

Recommendations should sound like a useful starting point, not a final verdict,
ranked comparison, or settled decision. Make them easy to correct.

Prefer:

```markdown
My guess is that the first version should help people check less often, not
just investigate faster. That points toward preventing wrong writes upfront
rather than relying mainly on recovery.
```

Avoid:

```markdown
My recommendation is to optimize the verification model around reduced operator
validation frequency.
```

This skill prepares a recommendation; it should not silently become a ranking
workflow. Use the interview while the desired outcome, audience, constraints,
options, non-goals, or tradeoff are still muddy. As they clarify, notice when the
decision criteria and serious options are clear enough to compare. At that point,
ask before switching: "Do you want me to recommend now?" If yes, hand off to
`making-recommendations`. If no, keep clarifying or summarize the current shape.

## Handling Vague or Technical Answers

When the user answers with vague, abstract, or mostly technical language, first
translate it into a plain-language guess and ask the user to correct it.

Do not immediately cross-examine. Use direct challenge only when the user's
answer contradicts an earlier statement, avoids the human outcome entirely, or
would leave the next step misleading.

Prefer:

```markdown
My plain-language read is that you want people to stop worrying about X. Is
that the right shape?
```

Avoid:

```markdown
That does not define the success criterion.
```

## Defaults

- If the target is unclear, ask what idea, plan, decision, or artifact the user
  wants to clarify.
- If several targets are present, ask which one to clarify first unless one
  clearly blocks the others.
- If the user provides a technical artifact, translate it into human-facing or
  operator-facing outcomes before asking about implementation mechanics.
- When the work shifts from clarifying the outcome to designing, deciding,
  pressure-testing, or critiquing it, hand off rather than continuing (see
  Handoffs).
- Produce a concise brief only when the user asks for one or the interview
  naturally reaches a handoff point.

## Handoffs

This skill clarifies the outcome; it does not design, decide, critique, or
implement. When the work shifts to one of those, name the move and hand off
rather than silently becoming that workflow. Default to conversational closure
when no downstream workflow is needed.

| The interview has done its job when… | Hand off to |
| --- | --- |
| The outcome is clear and the user wants to turn it into a design or spec | `superpowers:brainstorming` |
| Decision criteria and two or more serious options are clear enough to compare | `making-recommendations` |
| The user asks to be pressure-tested, challenged, or drilled on weak answers | `grill-me` |
| The user asks for a complete critique, report, review, or audit | the relevant review skill |
| The outcome is clear and no downstream workflow is needed | conversational closure (no handoff) |

Ask before switching: name the move and let the user decline. A handoff the user
did not choose is just the interview ending early.

## Turn Shape

Use natural conversation. A typical turn contains:

- a compact "My read so far:" opener
- one question
- a tentative recommendation or likely interpretation when useful
- a short reason the question matters, if not obvious

That opener is a developing synthesis, not a list of accumulated decisions.

## Examples

Technical plan:

```markdown
My read so far: You want maintainers to let Ticket make routine updates without
wondering whether it touched the wrong thing.

Question: When this works well, what should someone no longer need to
double-check?

My guess: Start with the thing people check most often today. If that worry does
not go away, the change may be technically better without feeling meaningfully
safer.
```

Strategy or design:

```markdown
My read so far: You want the onboarding flow to make new users feel oriented
quickly, not like they have to study the whole product before doing anything.

Question: What should someone be able to do in the first few minutes without
asking for help?

My guess: Start with one useful first action, not a full tour. If they can do
something real quickly, the rest of the product has more time to explain itself.
```

Rescuing a vague or technical answer (translate first, do not cross-examine):

```markdown
You said you want the system to be "more observable." My plain-language read is
that today something breaks and nobody notices until a user complains, and you
want to catch it first. Is that the shape, or is it more that when you do look,
you cannot tell what actually happened?
```

Reaching the recommend-now handoff (ask before switching workflows):

```markdown
My read so far: You want a reviewer to trust the automated checks enough to skip
re-reading every diff, and the worry is a silent wrong-approval slipping through.

We now have clear criteria and two real options on the table. Do you want me to
recommend one now, or keep clarifying first?
```

The read evolving across turns (rewrite it; do not append):

```markdown
Turn 1 — My read so far: You want the nightly job to stop paging people for
problems that clear up on their own by morning.

[User replies: "It is not the paging itself — it is that when it does page, no
one can tell the real outage from the same flaky timeout we see every week."]

Turn 2 — My read so far: You want whoever is on call to instantly tell a real
failure from the familiar flaky one, so they trust the page enough to act fast.
```

The Turn 2 read replaces Turn 1; it does not become a list of "Turn 1 decision,
Turn 2 decision." Each turn is the current best single sentence, rewritten as the
user corrects you.

## Anti-Patterns

Avoid turning the interview into a technical review.

Avoid:

- "What is the rollout safety bar?"
- "What operator confidence replaces the approval model?"
- "What is the target failure taxonomy?"
- "Which architectural boundary is most consistent with the existing control
  plane?"

Prefer:

- "Who needs to feel comfortable using this first?"
- "What should they be able to stop checking?"
- "What would feel like a bad surprise?"
- "When something goes wrong, what should still be easy?"
- "What would make this feel done enough to move on?"

Avoid keeping a running ledger during the active interview.

Prefer a compact evolving read:

```markdown
My read so far: You want this to feel safe in everyday use, not just correct in
the code. The unclear part is what people should no longer need to watch.
```

Avoid:

```markdown
- Decided X
- Decided Y
- Decided Z
```

## Stopping Point

Continue until the desired outcome, audience or operator, success signs,
non-goals, main tradeoff, and any naturally clear next useful move are clear
enough that you could fill in the brief below and the user would accept it
without correction.

When stopping, summarize conversationally. Do not create a formal spec,
checklist, implementation plan, or decision log unless the user asks. Include a
named next useful move only when it is naturally clear from the interview (see
Handoffs). If the next move is still uncertain, name the remaining uncertainty
instead of forcing a recommendation.

A concise brief, when useful, should stay lightweight:

```markdown
Here is the clarified shape:

You want <outcome> to feel true for <audience/operator>.
The experience should feel <qualities>.
The main thing to avoid is <failure/non-goal>.
The remaining uncertainty is <question>, or the next useful move is <move>.
```
