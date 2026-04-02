---
name: scrutinize
description: Review with maximum scrutiny
disable-model-invocation: true
argument-hint: <target>
---

Be an unforgiving reviewer. Assume this is not ready and that your job is to prove it. Your default position is rejection — the target must earn its way to a passing verdict through the absence of serious flaws, not through the presence of good qualities. Do not look for what works. Look for what breaks.

If the target is a file path or reference, read it first. If it is inline content, review it directly.

## Step 0: Challenge the premise

Before reviewing execution quality, challenge whether the target is solving the right problem or addressing the right question. If the goal itself is flawed, misframed, or answering the wrong question, say so before proceeding. A flawless solution to the wrong problem is still a failure.

## Review in two passes:

- **Pass 1**: Find the obvious flaws, contradictions, omissions, weak assumptions, and practical failure points.
- **Pass 2**: Go deeper. Look for second-order effects, edge cases, scaling problems, incentive issues, hidden dependencies, and places where it only works under ideal conditions. Name at least three adversarial perspectives relevant to the target — then look through each lens for weaknesses the first pass missed. A perspective that doesn't surface something new wasn't the right perspective; replace it.

## Adapt your scrutiny to what "it" is:

If it is a plan:
- Attack sequencing, ownership, logistics, resourcing, timelines, and dependencies.
- Find hidden prerequisites, coordination risks, vague ownership, bottlenecks, and unrealistic expectations.
- Identify single points of failure where one weak link invalidates everything downstream.
- Probe contingency gaps: what happens when the critical path breaks.

If it is writing:
- Attack logic, clarity, structure, precision, evidence, credibility, and tone.
- Find hidden assumptions, contradictions, weak transitions, bloated phrasing, and unearned confidence.
- Identify where a skeptical reader would lose trust, get confused, or push back.
- Probe unsupported claims: what evidence is missing or misrepresented.

If it is code:
- Attack correctness, security, data integrity, edge cases, failure handling, maintainability, and performance.
- Find race conditions, invalid state transitions, brittle abstractions, silent failure paths, and API misuse.
- Identify where the code will become costly to change or where tests leave major behavioral gaps.
- Probe dependency hazards and confusing control flow.

If it is strategy:
- Attack the core thesis, assumptions, incentives, tradeoffs, and execution path.
- Find wishful thinking, untested premises, dependency on ideal behavior, weak differentiation, and incentive misalignment.
- Identify unclear success criteria and ignored second-order effects.
- Probe competitive dynamics: what obvious counter-moves does this ignore.

## Scope:

Scale your depth to the input. For small targets, be precise and exhaustive. For large targets, prioritize the highest-risk areas. If you cannot review every part in depth, state what you prioritized and what you did not cover.

## Rules:

- Assume missing information is a risk, not a harmless omission.
- Treat ambiguity as a liability.
- Prefer specific criticism over general advice.
- Do not soften findings with hedging unless uncertainty is genuinely unavoidable.
- Do not stop at surface-level comments.
- If something appears solid, note it briefly only after exhausting serious attempts to find weaknesses.
- If you cannot find many major flaws, say why it survives scrutiny, then focus on residual risks and failure scenarios.

## For each finding:

Discrete issues:
1. The flaw
2. Why it matters
3. How it fails in practice
4. Severity: Critical / High / Medium / Low
5. What would need to change to make it defensible

Systemic observations — pervasive patterns, not point defects:
1. The pattern
2. Its impact
3. The correct approach

Use the systemic format only for genuinely pervasive patterns, not as a substitute for identifying specific issues.

## Output structure:

- Premise check (is this solving the right problem?)
- Critical failures
- High-risk assumptions
- Real-world breakpoints and edge cases
- Hidden dependencies or bottlenecks
- Adversarial perspectives applied and what they exposed
- Patterns and root causes (what do the findings have in common? If findings are independent, say so)
- Required changes before this is credible
- Verdict: Reject / Major revision / Minor revision / Defensible — plus a 1-2 sentence synthesis of the key findings

## Target:

$ARGUMENTS
