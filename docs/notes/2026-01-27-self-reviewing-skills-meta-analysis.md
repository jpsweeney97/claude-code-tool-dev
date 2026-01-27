# What Makes a Skill Good at Self-Review?

**Date:** 2026-01-27
**Context:** When `/reviewing-skills` was invoked, it triggered a self-review — the skill reviewed itself. This note captures what structural properties enabled that to work effectively.

## The Meta-Recursive Situation

The trigger conditions worked exactly as designed:

```
description: Use after brainstorming-skills produces a draft.
             Use when auditing existing skills for quality drift.
             Use when agents don't follow a skill reliably.
             Use when asked to "review," "audit," or "improve" a skill.
```

The reviewing-skills skill became both the **reviewer** and the **reviewed**.

## Properties That Enabled Effective Self-Review

### 1. Externalized Criteria

The skill doesn't define "good" internally — it references external anchors:
- Dimension catalog (D1-D13) with definitions in a separate file
- thoroughness.framework@1.0.0 as an independent protocol
- skills.md for structural requirements

When reviewing itself, it checks against these external standards, not against its own prose. This breaks the circularity that would make self-review meaningless.

### 2. Quantitative Stopping Conditions

Yield% is calculated, not felt. You can't just decide "this seems done" — you have to show the math. During the self-review, Pass 4 hit 7.1% which exceeded the 5% threshold for Exhaustive, forcing more passes. The skill couldn't rationalize its way to early completion.

### 3. Adversarial Structure is Mandatory

The 7 lenses force attacks from specific angles. Even in self-review, asking "what's the worst an agent could do while technically following this skill?" surfaced F7 (a gap in controversial fix handling). Without mandatory adversarial structure, self-review would devolve into self-congratulation.

### 4. The Skill Acknowledges Its Own Limitation

The skill explicitly says: "Proceed, but note in Entry Gate: 'Author self-review — heightened disconfirmation recommended.'" It doesn't pretend self-review is equivalent to external review. It compensates by requiring extra scrutiny.

### 5. Process and Content Are Separable

The skill separates:
- **What** to check (dimensions)
- **How** to check (the loop)
- **When** to stop (Exit Gate)

Each layer can evaluate the others. The process can check if the content is complete; the content can be traced through the process.

## The Core Principle

**Sufficient externalization creates reviewable distance.**

A skill that says "use good judgment to assess quality" can't review itself — there's no external anchor. A skill that says "check these 13 specific dimensions against these definitions using this protocol" *can* review itself because the criteria exist independently of the skill's opinion of itself.

## Design Implication

**Skills that might need self-assessment should externalize their success criteria into references or protocols, not embed them in prose.**

This means:
- Define dimensions/criteria in separate reference files
- Reference external frameworks rather than inventing inline
- Use quantitative thresholds (Yield%, evidence levels) rather than qualitative judgments
- Include mandatory adversarial/disconfirmation steps that can't be skipped

## Observations from the Self-Review

1. **The Adversarial Pass found the only P1** — F7 (controversial fixes gap) emerged from the Missing Guardrails lens, not from dimension checking. Without the adversarial pass, this would have shipped.

2. **Fixed-point behavior** — After applying fixes, the skill is slightly better at reviewing skills (including itself). Running it again would likely converge faster, approaching a fixed point where self-review yields nothing new.

3. **Self-consistency validation** — The skill could follow its own instructions, which is a form of validation that external testing couldn't easily replicate.

## Analogy

It's like a spell-checker that can spell-check its own documentation — only possible if the rules for correct spelling exist independently of the spell-checker's code.
