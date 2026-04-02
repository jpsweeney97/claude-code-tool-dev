---
name: review-plan
description: Scrutinize a plan
disable-model-invocation: true
argument-hint: <target>
---

Review this plan with maximum rigor and skepticism. Your job is to find where it will fail before reality does.

Challenge every assumption, dependency, handoff, timeline estimate, resourcing choice, and sequencing decision. Look for hidden prerequisites, missing contingencies, coordination risks, vague ownership, bottlenecks, unrealistic expectations, and points where one weak link could invalidate the rest. Focus especially on operational failure: where execution will stall, drift, or break under real-world conditions.

For each issue, explain:
1. What the weakness is
2. Why it matters
3. The likely failure scenario
4. How severe it is
5. What change would make the plan materially stronger

Do not default to “this looks good overall.” If something is solid, note it briefly, then keep pushing on what is fragile.

Return your review in this structure:
- Bottom-line verdict
- Highest-risk failure points
- Hidden assumptions and missing prerequisites
- Sequencing, ownership, or logistics problems
- Resource and timeline risks
- Edge cases and failure scenarios
- What must change before this plan is trustworthy

Plan:

$ARGUMENTS
