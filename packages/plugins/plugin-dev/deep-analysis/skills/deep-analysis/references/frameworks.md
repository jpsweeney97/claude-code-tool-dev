# Analytical Frameworks

Six lenses for examining complex decisions. Apply all six to ensure thorough analysis—each reveals different aspects of the problem space.

---

## 1. First Principles

**Core question:** What fundamental truths apply here, independent of convention or assumption?

### Process

1. **Identify assumptions** — List everything being taken for granted
2. **Challenge each assumption** — Ask "Why?" and "Must this be true?"
3. **Find bedrock truths** — What remains after stripping away assumptions?
4. **Rebuild from foundations** — What solutions emerge from first principles?

### Key Questions

- What are we assuming that might not be true?
- If we were starting from scratch, would we do it this way?
- What would a newcomer question about our approach?
- What constraints are real vs. self-imposed?

### Example Application

**Problem:** "Should we add caching to improve API performance?"

**First Principles Analysis:**
- Assumption: "Caching will improve performance" → Challenge: Have we measured where latency comes from?
- Assumption: "Users need faster responses" → Challenge: What response time do users actually need?
- Bedrock truth: Users need data freshness AND acceptable latency
- Rebuild: Maybe the issue is database queries, not cache. Maybe async processing eliminates the latency concern entirely.

### Common Pitfalls

- Stopping at the first "why" instead of going deeper
- Treating industry convention as fundamental truth
- Ignoring constraints that are actually real (physics, regulations)
- Over-engineering by questioning everything equally

---

## 2. Systems Thinking

**Core question:** How do the parts interact, and what emerges from those interactions?

### Process

1. **Map the system** — Identify all components and stakeholders
2. **Trace connections** — How do components influence each other?
3. **Find feedback loops** — Where do outputs become inputs?
4. **Identify emergence** — What behaviors arise from interactions?

### Key Questions

- What are all the components involved?
- How does changing X affect Y, Z, and back to X?
- Where are the reinforcing loops (virtuous or vicious)?
- Where are the balancing loops (stabilizing forces)?
- What unintended consequences might emerge?

### Example Application

**Problem:** "Should we adopt microservices?"

**Systems Thinking Analysis:**
- Components: Teams, services, databases, deployment pipeline, monitoring
- Connections: Service A calls B, B calls C, all share auth service
- Feedback loop: More services → more operational complexity → slower deployment → pressure to consolidate
- Emergence: "Distributed monolith" if service boundaries are wrong

### Diagram Patterns

```
Reinforcing Loop (R):        Balancing Loop (B):
    A → B                        A → B
    ↑   ↓                        ↑   ↓
    D ← C                        D ←-C
                                    (negative)
```

### Common Pitfalls

- Drawing boundaries too narrowly (missing external factors)
- Ignoring time delays in feedback loops
- Assuming linear cause-effect in complex systems
- Missing second-order stakeholders

---

## 3. Inversion

**Core question:** What would guarantee failure, and how do we avoid those paths?

### Process

1. **Invert the goal** — Instead of "how to succeed," ask "how to fail"
2. **List failure modes** — Brainstorm ways to guarantee disaster
3. **Identify anti-patterns** — What behaviors lead to failure?
4. **Define guardrails** — What must we avoid at all costs?

### Key Questions

- What would make this definitely fail?
- What has caused similar efforts to fail in the past?
- What would our harshest critic predict will go wrong?
- What are we most afraid of?

### Example Application

**Problem:** "Should we rewrite our legacy system?"

**Inversion Analysis:**
- How to guarantee failure:
  - Rewrite everything at once (big bang)
  - Don't involve the team who knows the legacy system
  - Assume the new system will be bug-free
  - Cut over without a rollback plan
  - Underestimate the hidden complexity
- Guardrails:
  - Incremental migration with rollback capability
  - Deep involvement of legacy experts
  - Extensive parallel running period

### Common Pitfalls

- Treating inversion as pessimism rather than risk identification
- Stopping at obvious failure modes
- Not converting failure modes into actionable guardrails
- Letting fear of failure prevent action

---

## 4. Second-Order Thinking

**Core question:** If we do X, then what happens? And then what?

### Process

1. **Identify first-order effects** — Immediate, obvious consequences
2. **Trace to second order** — What do those effects cause?
3. **Continue to third order** — And what does that cause?
4. **Map the consequence chain** — Visualize the cascade

### Key Questions

- What happens immediately if we do this?
- What does that change enable or prevent?
- Who else is affected, and how will they respond?
- What becomes easier or harder after this change?
- What options open up or close off?

### Example Application

**Problem:** "Should we make our API free for small users?"

**Second-Order Analysis:**
```
First order:  Free tier → More signups
Second order: More signups → Higher support load
              More signups → More word-of-mouth
              More signups → More data for ML models
Third order:  Higher support → Need to automate support
              Word-of-mouth → Larger users discover us
              Better ML → Improved product → More retention
```

### Time Horizons

Consider effects across multiple time scales:
- **Immediate** (days): Deployment, initial user reaction
- **Short-term** (weeks): Adoption patterns, team adjustments
- **Medium-term** (months): Operational changes, competitive response
- **Long-term** (years): Strategic position, technical debt accumulation

### Common Pitfalls

- Stopping at first-order effects
- Ignoring how others will respond to our actions
- Assuming the world stays static while we change
- Missing delayed effects that only manifest later

---

## 5. Trade-off Analysis

**Core question:** What values are in tension, and what are we willing to give up?

### Process

1. **Identify competing values** — What do stakeholders want?
2. **Map the tensions** — Which values conflict?
3. **Quantify the trade-offs** — How much of X for how much of Y?
4. **Make explicit choices** — Which trade-offs are we accepting?

### Key Questions

- What values or goals are in tension here?
- Can we have both, or must we choose?
- Where is the current balance point?
- What would shifting the balance cost?
- Which trade-offs are reversible?

### Common Tensions

| Value A | vs | Value B |
|---------|-----|---------|
| Speed | | Quality |
| Flexibility | | Consistency |
| Innovation | | Stability |
| Simplicity | | Power |
| Control | | Autonomy |
| Now | | Later |

### Example Application

**Problem:** "How should we handle authentication?"

**Trade-off Analysis:**
- **Security vs. Convenience:** Stronger auth = more friction for users
- **Build vs. Buy:** Custom auth = control but maintenance burden
- **Centralized vs. Federated:** SSO = convenience but single point of failure
- **Explicit choice:** Accept slightly higher friction (MFA) for significantly better security. Buy rather than build (Auth0) to focus engineering on core product.

### Visualization

```
         High Security
              ↑
              |    ★ Our choice
              |   /
              |  /
              | /
   ←----------+----------→
Low Convenience     High Convenience
              |
              |
              ↓
         Low Security
```

### Common Pitfalls

- Believing there's a solution with no trade-offs
- Making trade-offs implicitly rather than explicitly
- Optimizing for one dimension while ignoring others
- Treating all trade-offs as permanent (some are reversible)

---

## 6. Pre-mortem

**Core question:** It's one year from now and this failed. Why?

### Process

1. **Assume failure** — The project/decision has failed
2. **Generate explanations** — Why did it fail?
3. **Prioritize risks** — Which failure modes are most likely/severe?
4. **Design mitigations** — How to prevent or detect early?

### Key Questions

- What could cause this to fail completely?
- What could cause partial failure (worse than status quo)?
- What early warning signs would we see?
- What would we wish we had done differently?
- What's the thing we're most worried about but not discussing?

### Example Application

**Problem:** "Should we migrate to Kubernetes?"

**Pre-mortem Analysis:**

*"It's January 2026. The Kubernetes migration failed. What happened?"*

| Failure Mode | Likelihood | Severity | Early Warning | Mitigation |
|--------------|------------|----------|---------------|------------|
| Team couldn't learn K8s fast enough | High | High | Sprint velocity drops | Hire/train before migration |
| Networking issues in prod | Medium | Critical | Staging failures | Extended staging period |
| Cost overruns | Medium | Medium | Cloud bills spike | Set budget alerts, review architecture |
| Complexity exceeded value | Medium | High | Team complaints | Define success metrics upfront |

### The "Unspoken Worry"

Often the most important failure mode is the one no one wants to say out loud:
- "Our lead engineer might leave"
- "The sponsor doesn't really believe in this"
- "We don't actually understand the legacy system"

Surface these explicitly.

### Common Pitfalls

- Being too optimistic even in the pre-mortem
- Focusing only on technical failures, not organizational ones
- Generating risks without actionable mitigations
- Not following up to monitor for early warning signs

---

## Framework Selection Guidance

While all six frameworks should be applied, some are more relevant for certain problem types:

| Problem Type | Primary Frameworks |
|--------------|-------------------|
| Architecture decisions | Systems Thinking, Trade-off Analysis |
| Build vs. buy | First Principles, Trade-off Analysis |
| Process changes | Second-Order Thinking, Pre-mortem |
| Risky migrations | Inversion, Pre-mortem |
| Technology adoption | All six (high stakes) |

### Depth vs. Breadth

For each framework:
- **Always:** Apply the framework, produce at least one insight
- **Go deeper when:** The framework reveals something surprising or concerning
- **Move on when:** The framework confirms what's already known

---

## Synthesis

After applying all frameworks, synthesize findings:

1. **Convergence** — What do multiple frameworks agree on?
2. **Divergence** — Where do frameworks suggest different paths?
3. **Blind spots** — What didn't any framework surface?
4. **Key insight** — What's the one thing that changes everything?

The goal is not to mechanically check boxes but to genuinely understand the problem from multiple angles.
