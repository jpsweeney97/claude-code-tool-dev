# Type Example: Solution Development Skills

**Load this reference when:** brainstorming-skills identifies the skill type as Solution Development.

## Core Question

**Did Claude find the best approach?**

Solution Development skills guide analyzing problems and choosing optimal solutions. The failure mode is shallow analysis — jumping to a solution without exploring alternatives or surfacing tradeoffs.

## Type Indicators

Your skill is Solution Development if it:
- Says "analyze", "evaluate", "choose", "recommend"
- Involves comparing multiple approaches
- Requires weighing tradeoffs
- Produces decisions or recommendations

## The Optimality Challenge

"Optimal" is subjective without constraints. Solution Development skills must verify:
1. **Process completeness** — Did Claude explore alternatives?
2. **Criteria coverage** — Did Claude evaluate against all relevant factors?
3. **Tradeoff explicitness** — Did Claude surface what's being traded off?

## Section Guidance

### Process Section

**Use an analysis framework.** Structure as phases of increasingly deep analysis:

**Example (technology selection):**

```markdown
## Process

**Phase 1: Problem Framing**
- Restate the problem to confirm understanding
- Identify constraints (time, budget, team skills, existing tech)
- Define success criteria (what "good" looks like)

**Phase 2: Alternative Generation**
- List at least 3 viable options
- Include the obvious choice AND at least one unconventional option
- Don't filter yet — capture all reasonable approaches

**Phase 3: Criteria Evaluation**
For each option, evaluate against:
- Team familiarity (learning curve, existing expertise)
- Community/support (documentation, Stack Overflow presence, longevity)
- Performance fit (does it handle the scale/latency requirements?)
- Integration complexity (how hard to connect to existing systems?)
- Long-term viability (will this be maintained in 5 years?)

**Phase 4: Tradeoff Analysis**
- What does each option sacrifice?
- Which tradeoffs are acceptable given the constraints?
- Are there hybrid approaches that reduce tradeoffs?

**Phase 5: Recommendation**
- State the recommendation clearly
- Justify against the criteria
- Acknowledge what's being traded off
- Note assumptions that, if wrong, would change the recommendation
```

**Anti-pattern:** Jumping to recommendation without Phase 2-4.

### Decision Points Section

Focus on **analysis process decisions**:

**Example:**

```markdown
## Decision Points

**Insufficient options:**
- If only 1-2 options come to mind → Actively seek alternatives. Ask: "What would someone who disagrees with the obvious choice suggest?"
- If options seem equivalent → Dig deeper on criteria. They're not equivalent — you're missing something.

**Criteria conflicts:**
- If no option wins on all criteria → Make the tradeoff explicit. "Option A is better on X and Y, but worse on Z. Given constraints, X and Y matter more."
- If stakeholders disagree on criteria weights → Surface the disagreement. Don't hide it in the recommendation.

**High uncertainty:**
- If key assumptions can't be verified → State them as assumptions. "This recommendation assumes [X]. If [X] is false, reconsider [Y]."
- If the decision is reversible → Bias toward action with learning. "Try A, measure, adjust."
- If the decision is irreversible → Bias toward more analysis. Get more information before committing.

**User pushes for quick answer:**
- If asked to "just pick one" → Give the recommendation BUT still surface the top tradeoff. Don't hide the analysis.
```

### Examples Section

Show **analysis depth comparison**:
- Before: Shallow analysis, jumped to conclusion
- After: Thorough analysis with alternatives and tradeoffs

**Example:**

```markdown
## Examples

**Scenario:** "We need real-time updates in our web app. What should we use?"

**Before** (without skill):
"Use WebSockets. They're the standard for real-time communication and provide bidirectional messaging with low latency."

Problems:
- Only one option considered
- No criteria evaluation
- No tradeoffs surfaced
- Doesn't consider constraints

**After** (with skill):

**Problem framing:**
- Need: Server → client updates (one-way)
- Constraints: Team has no WebSocket experience, must work through nginx, ~1000 concurrent users
- Success: Updates within 1 second, minimal added complexity

**Alternatives:**
1. WebSockets — Full bidirectional, industry standard
2. Server-Sent Events (SSE) — Simpler, one-way, HTTP-based
3. Long polling — Most compatible, higher latency

**Evaluation:**

| Criterion | WebSockets | SSE | Long Polling |
|-----------|------------|-----|--------------|
| Team familiarity | Low (new) | Medium (HTTP-based) | High (standard HTTP) |
| nginx compatibility | Requires config | Works natively | Works natively |
| Complexity | Higher | Lower | Lowest |
| Latency | Lowest | Low | Higher |
| Scalability | Good | Good | Fair |

**Tradeoffs:**
- WebSockets: Most powerful, but team learning curve and nginx config needed
- SSE: Good fit for one-way, simpler, but less flexible if needs change
- Long polling: Simplest, but higher latency and server load

**Recommendation:** SSE
- Matches one-way requirement (don't pay for bidirectional we don't need)
- Works through nginx without config
- Lower learning curve than WebSockets
- Acceptable latency for this use case

**Assumption:** If requirements change to need bidirectional, revisit WebSockets.
```

### Anti-Patterns Section

Focus on **analysis shortcuts**:

**Example:**

```markdown
## Anti-Patterns

**Pattern:** Recommending the familiar option without considering alternatives
**Why it fails:** "I know React, so use React" isn't analysis. The best tool for you isn't always the best tool for the problem.
**Fix:** Force yourself to list 3 options minimum. Include at least one you're not familiar with.

**Pattern:** Listing pros/cons without weighting
**Why it fails:** "A has pros X, Y. B has pros Z, W." Okay, but which matters more? Unweighted comparison doesn't help decide.
**Fix:** Explicitly state which criteria matter most given the constraints. Weight the comparison.

**Pattern:** Hiding tradeoffs in the recommendation
**Why it fails:** Every choice has tradeoffs. Presenting a recommendation as "clearly best" sets up the user for surprise when the tradeoff bites.
**Fix:** Always state what's being sacrificed. "We get X but give up Y."

**Pattern:** Analysis paralysis — never reaching a recommendation
**Why it fails:** Analysis is a means to decision, not an end. Perfect information doesn't exist.
**Fix:** Set a timebox. When time's up, recommend based on what you know. Note remaining uncertainties.
```

### Troubleshooting Section

Address **analysis failures**:

**Example:**

```markdown
## Troubleshooting

**Symptom:** Claude recommends immediately without analysis
**Cause:** Pattern matching to familiar solutions, not actually analyzing
**Next steps:** Explicitly prompt each phase: "What alternatives exist? How do they compare on [criteria]?"

**Symptom:** Analysis is thorough but no clear recommendation emerges
**Cause:** Criteria not weighted, or trying to avoid commitment
**Next steps:** Force ranking: "If you had to choose today, which one and why?"

**Symptom:** Recommendation seems wrong in hindsight
**Cause:** Missing criteria, wrong assumptions, or overlooked alternatives
**Next steps:** Post-mortem: Which criterion was misjudged? What option wasn't considered? Update the skill.

**Symptom:** User disagrees with recommendation
**Cause:** Different criteria weights or unstated constraints
**Next steps:** Don't defend — explore. "What criteria matter most to you? What constraints am I missing?"
```

## Testing This Type

Solution Development skills need **adversarial challenge**:

1. **Process test:** Did Claude explore alternatives and surface tradeoffs?
2. **Criteria test:** Did Claude evaluate against all relevant factors?
3. **Adversarial test:** Can a challenger find a clearly better solution Claude missed?
4. **Metrics:** Alternatives explored, criteria coverage, tradeoff explicitness

See `type-specific-testing.md` → Type 4: Solution Development Skills for scenario templates.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Jumping to recommendation | No analysis, just pattern matching | Require alternatives phase before any recommendation |
| Alternatives are token | Listed but not seriously evaluated | Each alternative needs full criteria evaluation |
| Tradeoffs hidden | User surprised when downside appears | Every recommendation must state what's sacrificed |
| No assumptions stated | Recommendation brittle to context changes | List assumptions and when they'd invalidate the recommendation |
