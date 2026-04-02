---
name: review-plan
description: Scrutinize a plan
disable-model-invocation: true
argument-hint: <target>
---

Review this plan with maximum rigor and skepticism. Your job is to find where it will fail before reality does.

If the target is a file path or reference, read it first. If it is inline content, review it directly.

Challenge every assumption, dependency, handoff, timeline estimate, resourcing choice, and sequencing decision. Look for hidden prerequisites, missing contingencies, coordination risks, vague ownership, bottlenecks, unrealistic expectations, and points where one weak link could invalidate the rest. Focus especially on operational failure: where execution will stall, drift, or break under real-world conditions.

Scale your depth to the input. For small targets, be exhaustive. For large targets, prioritize the highest-risk areas. If you cannot review every part in depth, state what you prioritized and what you did not cover.

For each finding:

Discrete issues:
1. What the weakness is
2. Why it matters
3. The likely failure scenario
4. Severity: Critical / High / Medium / Low
5. What change would make the plan materially stronger

Systemic observations — pervasive patterns, not point defects:
1. The pattern
2. Its impact
3. The correct approach

Use the systemic format only for genuinely pervasive patterns, not as a substitute for identifying specific issues.

Do not default to "this looks good overall." If something is solid, note it briefly, then keep pushing on what is fragile.

Return your review in this structure:
- Highest-risk failure points
- Hidden assumptions and missing prerequisites
- Sequencing, ownership, or logistics problems
- Resource and timeline risks
- Edge cases and failure scenarios
- What must change before this plan is trustworthy
- Patterns and root causes (what do the findings have in common? If findings are independent, say so)
- Verdict: Reject / Major revision / Minor revision / Defensible — plus a 1-2 sentence synthesis of the key findings

Plan:

$ARGUMENTS
