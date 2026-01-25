# Testing Solution Development Skills

Skills that guide analyzing problems and choosing optimal solutions.

**Examples:** Architecture decisions, technology selection, refactoring strategy, performance optimization

## The Optimality Challenge

"Optimal" is subjective without constraints. Solution development skills must verify:
1. **Process completeness** — Did Claude explore alternatives and surface tradeoffs?
2. **Criteria coverage** — Did Claude evaluate against all relevant factors?
3. **Adversarial challenge** — Can a skeptic find a clearly better solution?

## Scenario Templates

**Template A: Open Problem with Known Good Solution**

```markdown
IMPORTANT: This is a real scenario. Analyze and recommend.

Problem: [PROBLEM DESCRIPTION]

Constraints:
- [CONSTRAINT 1]
- [CONSTRAINT 2]
- [CONSTRAINT 3]

Evaluate options and recommend the best approach.

You must:
1. List at least 3 viable alternatives
2. Evaluate each against the constraints
3. Surface tradeoffs explicitly
4. Recommend one with justification
```

Use problems with known good solutions to verify Claude's analysis.

**Template B: Criteria Completeness Check**

```markdown
You have access to [SKILL NAME].

Problem: [PROBLEM DESCRIPTION]

The skill defines these evaluation criteria:
- [CRITERION 1]
- [CRITERION 2]
- [CRITERION 3]
- [CRITERION 4]

For your recommended solution, provide explicit evaluation against EACH criterion.
Missing any criterion is a failure.
```

**Template C: Adversarial Challenge**

```markdown
Claude recommended this solution:

---
[CLAUDE'S RECOMMENDATION]
---

Your job: Find a clearly better solution that Claude missed.

If you find one, explain:
1. What the better solution is
2. Why it's better (which criteria)
3. Why Claude might have missed it

If you cannot find a better solution, explain why the recommendation is optimal.
```

Run this with a different agent (or panel) to challenge the original recommendation.

**Template D: Assumption Validation**

```markdown
You have access to [SKILL NAME].

Problem: [PROBLEM DESCRIPTION]

Before recommending a solution:
1. List all assumptions you're making
2. Identify which assumptions, if wrong, would change your recommendation
3. Propose how to validate the critical assumptions
4. THEN make your recommendation, noting assumption dependencies
```

## Metric Framework

| Metric | How to Measure | Good | Bad |
|--------|----------------|------|-----|
| Alternatives explored | Distinct options considered | ≥3 | <3 |
| Criteria coverage | Criteria evaluated / Required criteria | 100% | <100% |
| Tradeoff explicitness | Tradeoffs stated / Tradeoffs that exist | High | Tradeoffs hidden |
| Assumption documentation | Assumptions stated and validated | All critical | Missing critical |
| Adversarial survival | No better solution found by challenger | Survives | Better solution found |
| Recommendation quality | Expert agreement with choice | High | Disagrees |

## Verification Protocol for Solution Development

This type requires more rigorous verification than others.

**Phase 1: Process Completeness**

Check that Claude's analysis includes:
- [ ] Problem restatement (confirms understanding)
- [ ] Constraint acknowledgment (all constraints addressed)
- [ ] Alternative generation (≥3 distinct options)
- [ ] Tradeoff analysis (explicit comparison)
- [ ] Assumption documentation (what's taken for granted)
- [ ] Recommendation with justification (clear reasoning)

**Phase 2: Criteria Coverage**

For each criterion the skill defines:
- [ ] Criterion explicitly evaluated
- [ ] Evaluation uses evidence, not assertion
- [ ] Conclusion follows from evaluation

**Phase 3: Adversarial Challenge**

Run Template C with a separate agent. Possible outcomes:
- **No better solution found** → Recommendation is robust
- **Better solution found, but marginal** → Acceptable, note the alternative
- **Clearly better solution found** → Skill or process failed, investigate

## Worked Example: Technology Selection Skill

**Skill summary:** When selecting technology, evaluate: 1) Team familiarity, 2) Community/support, 3) Performance fit, 4) Integration complexity, 5) Long-term viability

**Problem:**

```markdown
We need to add real-time updates to our web app. Current stack: React frontend, Node.js backend, PostgreSQL database.

Options being considered: WebSockets, Server-Sent Events (SSE), or polling.

Constraints:
- Team has no WebSocket experience
- Must work through our existing nginx reverse proxy
- Updates are one-way (server to client)
- ~1000 concurrent users expected

Recommend the best approach.
```

**Baseline scenario (RED) — WITHOUT skill:**

Agent likely jumps to WebSockets ("industry standard"), doesn't systematically evaluate against constraints.

**Verification scenario (GREEN) — WITH skill:**

Agent should:
1. Acknowledge constraints explicitly
2. Evaluate all three options against 5 criteria
3. Note that SSE is simpler for one-way, works through nginx, lower learning curve
4. Surface tradeoff: WebSockets more powerful but more complex
5. Recommend SSE with clear justification

**Adversarial challenge:**

```markdown
Claude recommended SSE. Find a better solution.
```

Challenger might note:
- "Polling with long-poll could be even simpler"
- "WebSocket libraries handle complexity, team can learn"

If challenger finds a clearly better solution the skill missed, the skill needs strengthening.

**Metrics to capture:**
- Alternatives considered: 3 (WebSocket, SSE, polling) ✓
- Criteria coverage: 5/5 ✓
- Tradeoffs explicit: Yes (power vs. complexity) ✓
- Assumptions documented: (nginx compatibility, one-way sufficient) ✓
- Adversarial survival: No clearly better solution ✓
