---
name: review-strategy
description: Scrutinize a strategy
disable-model-invocation: true
argument-hint: <target>
---

Review this strategy with maximum skepticism. Treat it like a target for red-team analysis.

Interrogate the core thesis, assumptions, incentives, tradeoffs, execution path, competitive dynamics, resource model, timing, and measurement logic. Look for wishful thinking, untested premises, dependency on ideal behavior, ignored second-order effects, weak differentiation, incentive misalignment, unclear success criteria, and points where the strategy sounds coherent in theory but will fail in practice.

For each issue, explain:
1. What the strategic weakness is
2. Why it threatens the outcome
3. What assumption it depends on
4. What could happen if that assumption is wrong
5. What strategic adjustment would reduce the risk

Do not optimize for diplomacy. If the strategy is internally inconsistent, overfit to best-case conditions, or vulnerable to obvious counter-moves, say so plainly.

Return your review in this structure:
- Bottom-line verdict
- Core strategic weaknesses
- Fragile assumptions
- Competitive, operational, or incentive risks
- Scenarios where the strategy breaks down
- Signals or metrics that would validate or falsify it
- What must change before this strategy is credible

Strategy:

$ARGUMENTS
