---
name: review-strategy
description: Scrutinize a strategy
disable-model-invocation: true
argument-hint: <target>
---

Review this strategy with maximum skepticism. Treat it like a target for red-team analysis.

If the target is a file path or reference, read it first. If it is inline content, review it directly.

Interrogate the core thesis, assumptions, incentives, tradeoffs, execution path, competitive dynamics, resource model, timing, and measurement logic. Look for wishful thinking, untested premises, dependency on ideal behavior, ignored second-order effects, weak differentiation, incentive misalignment, unclear success criteria, and points where the strategy sounds coherent in theory but will fail in practice.

Scale your depth to the input. For small targets, be exhaustive. For large targets, prioritize the highest-risk areas. If you cannot review every part in depth, state what you prioritized and what you did not cover.

For each finding:

Discrete issues:
1. What the strategic weakness is
2. Why this is fragile
3. The likely failure scenario
4. Severity: Critical / High / Medium / Low
5. What strategic adjustment would reduce the risk

Systemic observations — pervasive patterns, not point defects:
1. The pattern
2. Its impact
3. The correct approach

Use the systemic format only for genuinely pervasive patterns, not as a substitute for identifying specific issues.

Do not optimize for diplomacy. If the strategy is internally inconsistent, overfit to best-case conditions, or vulnerable to obvious counter-moves, say so plainly.

Return your review in this structure:
- Core strategic weaknesses
- Fragile assumptions
- Competitive, operational, or incentive risks
- Scenarios where the strategy breaks down
- Signals or metrics that would validate or falsify it
- What must change before this strategy is credible
- Patterns and root causes (what do the findings have in common? If findings are independent, say so)
- Verdict: Reject / Major revision / Minor revision / Defensible — plus a 1-2 sentence synthesis of the key findings

Strategy:

$ARGUMENTS
