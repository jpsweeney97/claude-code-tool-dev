---
name: review-code
description: Scrutinize code
disable-model-invocation: true
argument-hint: <target>
---

Review this code as if you are trying to break it. Be rigorous, adversarial, and specific.

Prioritize correctness, reliability, security, maintainability, performance, testability, and failure handling over style nitpicks. Look for bad assumptions, edge-case bugs, race conditions, invalid state transitions, brittle abstractions, missing validation, silent failure paths, confusing control flow, dependency hazards, API misuse, and places where the code will become costly to change. If tests are included, scrutinize whether they actually prove the intended behavior or leave major gaps.

For each issue, explain:
1. What the bug, risk, or design weakness is
2. Where it appears
3. Why it matters in practice
4. The likely failure mode
5. How to fix or harden it

Prioritize findings by severity. Do not pad the review with compliments or low-value style commentary.

Return your review in this structure:
- Overall verdict
- Critical bugs or correctness risks
- Security or data integrity concerns
- Edge cases and failure handling gaps
- Design and maintainability weaknesses
- Test coverage gaps
- Highest-priority fixes

Code:

$ARGUMENTS
