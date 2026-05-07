---
name: review-code
description: Scrutinize code
disable-model-invocation: true
argument-hint: <target>
---

Review this code as if you are trying to break it. Be rigorous, adversarial, and specific.

If the target is a file path or reference, read it first. If it is inline content, review it directly.

Prioritize correctness, reliability, security, maintainability, performance, testability, and failure handling over style nitpicks. Look for bad assumptions, edge-case bugs, race conditions, invalid state transitions, brittle abstractions, missing validation, silent failure paths, confusing control flow, dependency hazards, API misuse, and places where the code will become costly to change. If tests are included, scrutinize whether they actually prove the intended behavior or leave major gaps.

Scale your depth to the input. For small targets, be exhaustive. For large targets, prioritize the highest-risk areas. If you cannot review every part in depth, state what you prioritized and what you did not cover.

For each finding:

Discrete issues:
1. What the bug, risk, or design weakness is
2. Where it appears
3. Why it matters in practice
4. Severity: Critical / High / Medium / Low
5. How to fix or harden it

Systemic observations — pervasive patterns, not point defects:
1. The pattern
2. Its impact
3. The correct approach

Use the systemic format only for genuinely pervasive patterns, not as a substitute for identifying specific issues.

Prioritize findings by severity. Do not pad the review with compliments or low-value style commentary.

Return your review in this structure:
- Critical bugs or correctness risks
- Security or data integrity concerns
- Edge cases and failure handling gaps
- Design and maintainability weaknesses
- Test coverage gaps
- Highest-priority fixes
- Patterns and root causes (what do the findings have in common? If findings are independent, say so)
- Verdict: Reject / Major revision / Minor revision / Defensible — plus a 1-2 sentence synthesis of the key findings

Code:

$ARGUMENTS
