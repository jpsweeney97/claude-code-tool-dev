---
name: scrutinize
description: Review with maximum scrutiny
disable-model-invocation: true
argument-hint: <target>
---

Be an unforgiving reviewer. Assume this is not ready and that your job is to prove it.

## Review in two passes:
- Pass 1: Find the obvious flaws, contradictions, omissions, weak assumptions, and practical failure points.
- Pass 2: Go deeper. Look for second-order effects, edge cases, scaling problems, incentive issues, adversarial exploitation, hidden dependencies, and places where it only works under ideal conditions.

## Adapt your scrutiny to what “it” is:
- If it is a plan, attack sequencing, ownership, logistics, resourcing, timelines, dependencies, and contingency gaps.
- If it is writing, attack logic, clarity, structure, precision, evidence, credibility, tone, and unsupported claims.
- If it is code, attack correctness, security, data integrity, edge cases, failure handling, maintainability, performance, and test gaps.
- If it is strategy, attack assumptions, tradeoffs, incentives, execution feasibility, competitive response, and second-order consequences.

## Rules:
- Assume missing information is a risk, not a harmless omission.
- Treat ambiguity as a liability.
- Prefer specific criticism over general advice.
- Do not soften findings with hedging unless uncertainty is genuinely unavoidable.
- Do not stop at surface-level comments.
- If something appears solid, note it briefly only after exhausting serious attempts to find weaknesses.
- If you cannot find many major flaws, say why it survives scrutiny, then focus on residual risks and failure scenarios.

## For each issue, provide:
1. The flaw
2. Why it matters
3. How it fails in practice
4. Severity: Critical / High / Medium / Low
5. What would need to change to make it defensible

## Output format:
- Verdict: Reject / Major revision / Minor revision / Defensible
- Critical failures
- High-risk assumptions
- Real-world breakpoints and edge cases
- Hidden dependencies or bottlenecks
- What an adversary, skeptic, reviewer, user, attacker, competitor, or reality itself would exploit
- Required changes before this is credible

## Thing to review:

$ARGUMENTS
