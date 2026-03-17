---
name: adversarial-review
description: Performs a structured adversarial review of a proposal, design, or approach. Systematically stress-tests across seven orthogonal dimensions (steel-man, assumptions, failure modes, underspecification, opportunity cost, second-order effects, severity ranking). Use when user says "adversarial review", "critique this", "stress test this proposal", "what's wrong with this approach", "red team this", "poke holes in this". Do NOT use for general code review (use code review workflows), proofreading, or editing. Pairs with review-validator skill for review quality assurance.
argument-hint: "[target — e.g., 'the caching proposal' or 'the migration plan'. Omit to review the most recent proposal.]"
---

# Adversarial Review

Perform a rigorous, structured critique of a proposal. The goal is to surface real risks and blind spots — not to appear thorough.

## Before You Begin

### Identify the Target

If the user specified a target, review that. Otherwise, identify the most recent proposal, design, or approach in the conversation. If no clear proposal exists, ask: "What should I review?"

### Calibrate Depth

Assess the proposal's stakes and set depth accordingly. This controls how much evidence each section requires — not whether sections can be skipped. **Every section is mandatory regardless of depth.**

- **High stakes** (architecture decisions, data migrations, security boundaries, public APIs, irreversible changes): each section requires 3+ concrete, specific points with trigger conditions and consequences.
- **Standard** (feature designs, implementation approaches, workflow changes): each section requires 2+ concrete points.
- **Low stakes** (utility refactors, internal tooling, configuration changes): each section requires 1+ concrete point, but points must still be specific and falsifiable.

State the calibration level and why at the top of the review.

## The Seven Lenses

Work through every section in order. Do not skip sections. Do not reorder sections. Do not merge sections. Each lens attacks from a different angle — collapsing them defeats the purpose.

### 1. Steel-Man

State the single strongest argument for why this approach is **correct** — not merely adequate, not "it addresses the problem," but why a reasonable engineer would actively choose this over alternatives.

The steel-man must:
- Identify a specific *advantage* of this approach (not a restatement of the goal it serves)
- Be strong enough that reading it makes you think "okay, this really does have merit"
- Not contain hedging language ("somewhat," "partially," "to an extent," "arguably")

**Why this section exists:** Without a genuine steel-man, the review degenerates into a teardown. Anchoring on the proposal's real strength prevents dismissing it prematurely and forces subsequent critiques to overcome the steel-man's argument, not just ignore it.

**Self-check:** If your steel-man would apply equally to *any* solution to this problem, it's a tautology. Rewrite it.

### 2. Assumptions Audit

List every assumption baked into the proposal — technical, environmental, organizational, temporal.

For each assumption, state:
- **The assumption** — what is being taken as given
- **What breaks** — the specific consequence if this assumption is wrong
- **Early detection** — how you would discover the assumption is false *before* it causes the consequence

Do not list assumptions that are explicitly stated and justified in the proposal. The goal is to surface *unstated* assumptions — things the proposal takes for granted without acknowledgment.

**Self-check:** If you listed fewer than 3 assumptions for a non-trivial proposal, you're not looking hard enough. Every proposal assumes things about its environment, its users, its dependencies, and its future.

### 3. Failure Modes

Identify:
- The **top 3 most likely** failure modes (things that will probably go wrong)
- The **single highest-severity** failure mode (even if unlikely)

For each failure mode:
- **Trigger condition** — the specific circumstances that cause this failure
- **Blast radius** — what is affected and what is not
- **Loud or silent** — does this failure produce an obvious error, or does it silently corrupt state / produce wrong results / degrade over time?

**Silent failures are the priority.** A loud failure gets caught and fixed. A silent failure compounds. If you identified zero silent failure modes, go back and look again.

**Self-check:** If every failure mode you listed is "the system crashes" or "an error is thrown," you only found loud failures. Where does this proposal fail *without anyone noticing*?

### 4. What's Underspecified

Identify anything that:
- Requires a decision that hasn't been made
- Defers a detail that will constrain future choices
- Has multiple valid interpretations that would lead to different implementations

For each item, classify it:
- **Accidentally omitted** — this was likely not considered
- **Intentionally deferred** — this was probably scoped out deliberately, but the deferral has consequences worth noting

Do not classify everything as intentionally deferred. That is the comfortable default. If the proposal doesn't explicitly acknowledge deferring something, assume it was accidental unless you have strong evidence otherwise.

**Self-check:** Read the proposal as if you are the person who has to implement it tomorrow with no access to the author. What questions would you have?

### 5. Opportunity Cost

Answer two questions:
- **What are we implicitly ruling out** by committing to this approach? Name specific alternatives that become harder or impossible after this decision.
- **What alternative did we dismiss too quickly?** Identify at least one alternative approach and state its strongest advantage over the current proposal (the "anti-steel-man" — the best case for a different path).

This section is explicitly adversarial. The goal is not to re-litigate the decision but to make the cost of the current choice visible.

### 6. Second-Order Effects

Identify downstream consequences that aren't obvious from the proposal:
- **Dependencies created** — what now depends on this, and what does this depend on?
- **Maintenance burden** — what ongoing cost does this introduce?
- **Behavioral effects** — how does this change what's easy/hard for the team going forward? Does it create incentives to do things a particular way?

Focus on effects the proposal's author probably didn't intend. First-order effects are features; second-order effects are surprises.

### 7. Severity Ranking

Rank **every issue** surfaced in sections 2–6 using these tags:

- `[fatal]` — this approach cannot work as described. Must redesign.
- `[serious]` — this must be resolved before proceeding. Blocks implementation or causes significant rework if deferred.
- `[moderate]` — real risk that should be mitigated. Can proceed with an explicit accept-and-mitigate plan.
- `[minor]` — worth noting for future reference. Does not affect the current decision.

**Rules:**
- If a non-trivial proposal has zero `[serious]` or `[fatal]` issues, state this explicitly and justify why — don't just silently omit higher severities.
- If you assigned `[fatal]`, the review must explain why the approach is unrecoverable, not merely flawed.
- The severity ranking must cover *every* issue from sections 2–6. Do not introduce new issues here. Do not drop issues that appeared earlier.

## Output Format

Use this exact structure. The response-validator skill depends on these headings.

```
## Adversarial Review: [target name]

**Depth calibration:** [High/Standard/Low] — [one-line justification]

### 1. Steel-Man
[content]

### 2. Assumptions Audit
[content — use a list, one assumption per item]

### 3. Failure Modes
[content — use sub-headings or bold labels per failure mode]

### 4. Underspecification
[content — classify each item as Accidental or Intentional Deferral]

### 5. Opportunity Cost
[content]

### 6. Second-Order Effects
[content]

### 7. Severity Ranking
[content — table or list with [severity] tag per issue]
```

### Save the Review

After producing the review, write the complete review to `/Users/jp/Projects/active/claude-code-tool-dev/docs/reviews/`. This file is the data bridge to the `review-validator` skill, which runs as an isolated subagent and cannot see conversation history.

- **Always overwrite** the file — "latest" means latest.
- **Write the complete review** — do not summarize or truncate.
- **Do not skip this step.** The review-validator cannot function without it.

## Rationalization Table

| Excuse | Reality |
| --- | --- |
| "This proposal is straightforward — it doesn't need a full review" | Depth calibration handles this. Set Low stakes if appropriate, but complete all sections. Simple proposals still have assumptions and failure modes. |
| "I already considered these issues when making the proposal" | You are now the reviewer, not the proposer. Prior consideration doesn't exempt an issue from being documented. If you considered it and accepted the risk, say so in the review with justification. |
| "There aren't enough issues to fill every section" | Every non-trivial proposal has at least one assumption, one failure mode, and one underspecified element. If you can't find them, you aren't looking from the right angle. |
| "The issues I found are more important than the ones I didn't" | You don't know which issues you didn't find. Coverage completeness matters precisely because you can't judge the importance of unknown unknowns. |
| "Listing minor issues dilutes the important ones" | That's what the severity ranking is for. List everything, rank it, and the reader can filter. Omitting minor issues to "focus" is editorial — and it hides information. |

## Red Flags — STOP and Rewrite

If you notice yourself doing any of the following, the review is going off track:

- **Writing a section in under 30 seconds** — you're pattern-matching, not analyzing
- **Every issue is [moderate]** — you're avoiding commitment. Some things are serious; some are minor. Force a spread.
- **Using the phrase "this is fine because..."** — you've switched from reviewer to defender. Step back.
- **Steel-man uses words like "somewhat" or "to a degree"** — it's not a steel-man, it's a concession. Strengthen it or admit the proposal's foundation is weak.
- **All failure modes are loud** — you haven't looked for the silent ones. Go back to Section 3.
- **Assumptions list has fewer than 3 items** — you're only seeing the obvious ones. Consider: deployment environment, user behavior, data volume, dependency stability, team knowledge, timeline.
- **Section 5 says "no better alternatives"** — there is always an opportunity cost. At minimum, "do nothing" or "defer this decision" is an alternative with its own advantages.
