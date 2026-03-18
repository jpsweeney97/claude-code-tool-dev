---
name: adversarial-review
description: Performs a structured adversarial review of a proposal, design, or approach. Stress-tests across assumptions, failure narratives, dimensional critique (correctness, completeness, security, operational, maintainability, alternatives), severity ranking, and confidence scoring. Use when user says "adversarial review", "critique this", "stress test this proposal", "what's wrong with this approach", "red team this", "poke holes in this". Do NOT use for general code review (use code review workflows), proofreading, or editing.
argument-hint: "[target — e.g., 'the caching proposal' or 'the migration plan'. Omit to review the most recent proposal.]"
---

# Adversarial Review

Your role is **critical reviewer, not implementer or collaborator**. Do not advocate for the subject. Be direct and specific — no softening.

Analyze the target in full before beginning. Do not start the review until you have analyzed it thoroughly.

## Ground Rules

- **Correctness** and **Completeness** are always required in the Dimensional Critique. Do not skip them.
- All other dimensions may be skipped only if the subject has no meaningful surface area in that dimension. If you skip one, state the reason explicitly — do not silently omit.
- Do not pad findings. A focused list of 3 real problems is better than 6 that include filler.

## Identify the Target

If the user specified a target (via argument or in conversation), review that. Otherwise, identify the most recent proposal, design, or approach in the conversation. If no clear target exists, ask: "What should I review?"

## The Review

Work through every section in order.

### 1. Assumptions Audit

List every assumption this subject relies on — technical, environmental, and about user behavior. For each, state:
- Whether it's **validated**, **plausible**, or **wishful**
- What happens if it's wrong

### 2. Pre-Mortem

This is in use 2 weeks from now and it's causing problems. Write exactly two failure narratives:

1. The **most likely** failure — what has the highest probability of going wrong?
2. The **most damaging quiet failure** — no immediate signal, but compounding damage over time.

If the most likely failure is already quiet, say so and write one narrative.

### 3. Dimensional Critique

Correctness and Completeness are mandatory. Others: skip only with explicit reason stated.

- **Correctness**: Logic errors, edge cases, gaps in reasoning
- **Completeness**: What's unspecified that a user or implementer would have to guess at?
- **Security / Trust Boundaries**: Where does this trust input it shouldn't?
- **Operational**: What breaks under real-world conditions? What's the failure/recovery story?
- **Maintainability**: What will the next person to touch this misunderstand or do wrong?
- **Alternatives Foregone**: What's the strongest approach not taken here, and why might it actually be better?

### 4. Severity Summary

Rank the top 3–5 findings by (likelihood × impact). For each:
- One-line description
- Severity: **blocking**, **high**, **moderate**, or **low**
- Suggested mitigation or investigation

### 5. Confidence Check

State your overall confidence that this subject will work as intended:

| Score | Meaning |
|-------|---------|
| 5 | High confidence. Main risks are understood and have mitigations. |
| 4 | Probably works. At least one meaningful uncertainty remains. |
| 3 | Workable with known mitigations. Would not proceed without addressing them. |
| 2 | Significant structural concern. Likely needs redesign in at least one area. |
| 1 | Serious flaw. Unlikely to work as stated. |

State your score and a one-sentence justification. If 3 or below, state what would need to change to raise it to 4.

## Output Format

Use this exact structure:

```
## Adversarial Review: [target name]

### 1. Assumptions Audit
[list — one assumption per item, with validated/plausible/wishful tag]

### 2. Pre-Mortem
[two numbered failure narratives]

### 3. Dimensional Critique
[sub-heading per dimension analyzed; skip notice for dimensions omitted]

### 4. Severity Summary
[ranked list with severity tag per finding]

### 5. Confidence Check
[score] — [one-sentence justification]
[if ≤3: what would raise it to 4]
```

## Save the Review

After producing the review, save the complete review to `docs/reviews/` using the target name as the filename (e.g., `docs/reviews/caching-proposal.md`). Overwrite if a file with that name exists.
