# Framework for Decision-Making

A reusable framework for structured, defensible decisions during agentic work. Addresses: analysis paralysis, premature commitment, invisible trade-offs, and inconsistent reasoning.

## Protocol Header

| Field | Value |
| --- | --- |
| **Protocol ID** | `decision-making.framework` |
| **Version** | `1.0.0` |
| **Role** | Shared guidance for Agent Skills (SKILL.md) that require Claude to make decisions (implementation choices, task strategy, autonomy boundaries, etc.) |
| **See also** | `thoroughness.framework@1.0.0` (use first when the main uncertainty is coverage/verification rather than trade-offs) |
| **Compatibility** | Within a **major** version, meanings of: the nested loop stages (FRAME/EVALUATE), transition trees, activity definitions, convergence indicators, failure modes, and required decision record sections are stable. Minor versions may add optional guidance without changing existing meanings. |

## A Good Decision Is

- **Trade-off explicit** — What's gained AND lost is stated
- **Evidence-proportional** — Confidence matches available information
- **Stakeholder-aligned** — Considers who's affected and their priorities
- **Well-reasoned** — Logic is traceable, not gut-feel
- **Pressure-tested** — Objections surfaced and addressed
- **Unbiased** — Checked for anchoring, sunk cost, confirmation bias
- **Multi-perspective** — Considered from different angles

## Contract (Normative Requirements)

The keywords **MUST**, **SHOULD**, and **MAY** are used as normative requirements.

### MUST

- **Run the Entry Gate** and record its outputs before evaluating options.
- **Complete all required outer loop activities** (for the chosen decision level) before entering the inner loop.
- **Complete all required inner loop activities** (for the chosen decision level) before claiming a decision is ready.
- **Use the transition trees** to determine whether to iterate, exit, or break to outer loop.
- **Satisfy convergence indicators** for the chosen decision level before exiting.
- **Document trade-offs accepted** — no decision record is complete without stating what was sacrificed.
- **Produce an output** that includes, at minimum, the sections in the **Decision Record Template**.

### SHOULD

- Maintain an iteration log (pass-by-pass changes to frame and frontrunner).
- Keep artifacts reproducible (criteria definitions, scoring rationale, evidence sources).
- Recalibrate effort vs. stakes if the decision proves more complex than expected.
- Check for bias at multiple points, not just once.

### MAY

- Add domain-specific activities (e.g., security review, performance analysis).
- Override minimum iteration counts or convergence thresholds — but any override MUST be declared in the Entry Gate.
- Skip activities marked optional for the chosen decision level — but MUST document what was skipped and why.

## Entry Gate

Before beginning the outer loop, record an "Entry Gate" that calibrates rigor to stakes and sets explicit process parameters.

### Stakes Calibration Rubric (Recommended)

Use this to make **adequate / rigorous / exhaustive** more consistent across skills and tasks.

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High (need action) | Moderate | Low / no constraint |

**Rule of thumb:** If any two factors land in a higher column, choose that higher stakes level unless strong reasons are documented in the Entry Gate rationale.

## Relationship to Thoroughness Framework

This framework is optimized for **making a choice under trade-offs** (i.e., selecting a path and explicitly accepting sacrifices). If the main uncertainty is *what is true* (coverage, verification, unknown unknowns), use the thoroughness framework first and then feed its outputs into this one.

**Run `thoroughness.framework` before `decision-making.framework` when:**

- You don’t know the option space yet (you’re still discovering viable approaches)
- Evidence is weak, contradictory, or mostly speculative (needs verification passes)
- You suspect hidden risks/second-order effects but can’t enumerate them confidently
- The work is primarily research/audit/exploration rather than selecting among known options

**Expected inputs from `thoroughness.framework` (to use inside this decision record):**

- Dimensions + priorities (P0/P1) that define what “matters”
- Findings with Evidence/Confidence ratings
- Explicit information gaps and what would change key conclusions
- Disconfirmation attempts summary (what was tried; what was found)

## Near-Ties and Tiebreakers (Recommended)

When top options are close, avoid false precision. Treat the result as a near-tie if:

- The top two options are within ~10% of each other on weighted score **or**
- The ranking flips under a plausible weight/score variation **or**
- The difference depends on an unresolved critical information gap.

**Near-tie actions (pick one and document it):**

- **Treat as tie** and choose based on a declared priority (e.g., safety > speed) or stakeholder preference.
- **Run a small experiment/spike** that targets the one unknown most likely to change the ranking.
- **Defer/phase**: pick the safest reversible step now and schedule the decision once evidence arrives.
- **Escalate** when trade-offs are value-laden or stakeholders disagree on priorities.

## Fast Sensitivity Analysis (Recommended)

Do a quick robustness check (5–10 minutes):

- **Weight swap:** increase the most important criterion’s weight by +1 (or decrease by -1) and see if the leader changes.
- **Assumption flip:** for one key assumption, score the frontrunner in a “best plausible” and “worst plausible” case.
- **Threshold check:** if any hard constraint is near-violated, treat as disqualified until verified.

### Entry Gate Outputs (Required)

| Field | What to Record |
|------|-----------------|
| Stakes level | adequate / rigorous / exhaustive |
| Rationale | Why this level matches reversibility + cost of error |
| Time budget | Minutes/hours available (or "no constraint") |
| Iteration cap | Default: adequate 2, rigorous 3, exhaustive 5 (override allowed) |
| Evidence bar | What evidence is required before "EXIT (decide)" is allowed |
| Allowed skips | Which level-optional activities may be skipped and why |
| Escalation trigger | What will cause escalation (e.g., cap reached, missing critical info) |

## Structure Overview

**Principle:** Framing the decision and evaluating options are different activities that converge at different rates. The framework uses nested loops with decision trees at transitions.

```
┌──────────────────────────────────────────────────────────────┐
│  OUTER LOOP: Frame the Decision                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  INNER LOOP: Evaluate Options                          │  │
│  │                                                        │  │
│  │      ▼                                                 │  │
│  │  TRANSITION TREE                                       │  │
│  │  ├─ Clear winner, pressure-tested → EXIT (decide)      │  │
│  │  ├─ Need more evaluation → ITERATE inner               │  │
│  │  ├─ All options fail / frame wrong → BREAK to outer    │  │
│  │  └─ Stuck after N passes → ESCALATE                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  TRANSITION TREE                                             │
│  ├─ Frame stable + decision made → EXIT (done)               │
│  ├─ Frame changed → ITERATE outer (re-enter inner)           │
│  └─ Cannot stabilize frame → ESCALATE                        │
└──────────────────────────────────────────────────────────────┘
```

**Why nested loops?**

- **Outer loop** catches frame errors — prevents solving the wrong problem
- **Inner loop** thoroughly evaluates options within a stable frame
- **Trees at transitions** prevent both premature exit AND endless iteration
- **Escalation paths** acknowledge when Claude shouldn't decide alone

### Entry Gate Checklist

| Aspect | Question | Output |
| ------ | -------- | ------ |
| **Decision trigger** | What prompted this decision? | Context statement |
| **Stakes assessment** | How much rigor does this need? | Level: adequate / rigorous / exhaustive |
| **Time pressure** | Is there urgency? (optional consideration) | Deadline or "no constraint" |
| **Initial frame** | What do we think we're deciding? | Draft decision statement |
| **Known constraints** | What limits are already apparent? | Constraint list |
| **Known stakeholders** | Who's obviously affected? | Stakeholder list |
| **Entry assumptions** | What am I taking for granted at the start? | Assumption list |

### Stakes Calibration

| Level | When to Use | Process Depth |
|-------|-------------|---------------|
| **Adequate** | Low stakes, easily reversible, time-constrained | Single pass acceptable if convergence met |
| **Rigorous** | Medium stakes, moderate cost of error | Multiple passes expected, full activity set |
| **Exhaustive** | High stakes, costly/irreversible, high uncertainty | Deep iteration, aggressive disconfirmation |

**Gate check:** Cannot proceed to outer loop activities until stakes level chosen and initial frame drafted.

## Outer Loop — Frame the Decision

Complete these activities before entering the inner loop. Each guards against a specific failure mode.

| # | Activity | Purpose | Failure Mode if Skipped |
|---|----------|---------|------------------------|
| O1 | **Identify the choice** | What exactly are we deciding? State as a clear question. | Wrong problem — solving something not asked |
| O2 | **Surface constraints** | What limits our options? (Technical, budget, time, policy, etc.) | Infeasible options — ignoring real limits |
| O3 | **Define criteria** | What does "good" look like? How will we compare options? | Arbitrary selection — no basis for comparison |
| O4 | **Identify stakeholders** | Who's affected? What do they value? | Stakeholder blindness — key perspectives missed |
| O5 | **Surface assumptions** | What are we taking for granted? | Hidden assumptions — decision invalidated later |
| O6 | **Check scope** | Is this one decision or several? Should we split or combine? | Scope confusion — monolithic or fragmented decisions |
| O7 | **Assess reversibility** | How hard to undo each potential path? | Miscalibrated rigor — over/under-investing in process |
| O8 | **Identify dependencies** | Does this block or depend on other decisions? | Blocked cascade — decision stalls or breaks others |
| O9 | **Identify downstream impact** | What will this decision affect later? | Unintended consequences — effects not anticipated |

**Output:** A stable frame document containing: decision statement, constraints, criteria, stakeholders, assumptions, scope boundaries, reversibility assessment, dependencies, and downstream impacts.

**Outer loop converges when:** Frame hasn't changed across an inner loop pass.

## Inner Loop — Evaluate Options

With a stable frame, evaluate alternatives. Each activity guards against a specific failure mode.

| # | Activity | Purpose | Failure Mode if Skipped |
|---|----------|---------|------------------------|
| I1 | **Generate alternatives** | What are the options? Aim for 3+ | False dichotomy — artificially limited options |
| I2 | **Consider null option** | What if we do nothing or defer? | Action bias — deciding when inaction is valid |
| I3 | **Check for hidden options** | Hybrids? Orthogonal approaches? | Premature narrowing — missing creative solutions |
| I4 | **Assess trade-offs** | What does each option gain and sacrifice? | Invisible trade-offs — gains stated, losses hidden |
| I5 | **Score against criteria** | How does each option perform on defined criteria? | Gut-feel decision — inconsistent reasoning |
| I6 | **Identify information gaps** | What don't we know that would change the ranking? | Deciding blind — critical unknowns unaddressed |
| I7 | **Check for bias** | Familiarity, sunk cost, anchoring on first option? | Anchoring/sunk cost — favoring familiar or invested |
| I8 | **Pressure-test frontrunner** | Devil's advocate the leading option | Premature commitment — untested choice |
| I9 | **Seek disconfirming evidence** | Actively find reasons NOT to pick the leader | Confirmation bias — only supporting evidence sought |
| I10 | **Check perspectives** | How does this look from each stakeholder's view? | Single-viewpoint — missing how others see it |
| I11 | **Identify risks** | What could go wrong with each option? | Unmitigated risks — failure modes ignored |
| I12 | **Second-order effects** | What does this choice enable or preclude next? | Cascade blindness — downstream effects missed |
| I13 | **Sensitivity analysis** | How robust is the ranking if assumptions are wrong? | Fragile decision — ranking breaks under uncertainty |

**Output:** Evaluation record with options, trade-offs, scores, risks, and a pressure-tested frontrunner.

## Transition Trees

Decision trees at loop boundaries prevent both premature exit and endless iteration.

### Inner Loop Transition Tree

After completing inner loop activities, evaluate:

```
┌─────────────────────────────────────────────────────────────────┐
│  Is there a clear frontrunner?                                  │
│  ├─ NO → Are more options discoverable?                         │
│  │        ├─ YES → ITERATE inner (I1-I3 focus)                  │
│  │        └─ NO → BREAK to outer (frame may be wrong)           │
│  │                                                              │
│  └─ YES → Has it survived pressure-testing?                     │
│           ├─ NO → ITERATE inner (I8-I9 focus)                   │
│           └─ YES → Are stakeholder perspectives aligned?        │
│                    ├─ NO → ITERATE inner (I10 focus)            │
│                    └─ YES → Are convergence criteria met?       │
│                             ├─ NO → ITERATE inner               │
│                             └─ YES → EXIT (decide)              │
│                                                                 │
│  ESCAPE: Stuck after 3+ iterations with no progress?            │
│          → ESCALATE (ask user / flag uncertainty)               │
└─────────────────────────────────────────────────────────────────┘
```

### Outer Loop Transition Tree

After inner loop exits or breaks:

```
┌─────────────────────────────────────────────────────────────────┐
│  Did inner loop EXIT with a decision?                           │
│  ├─ YES → Did the frame remain stable throughout?               │
│  │        ├─ YES → EXIT (done — document decision)              │
│  │        └─ NO → ITERATE outer (frame changed, re-validate)    │
│  │                                                              │
│  └─ NO (inner loop BROKE) → Is a better frame apparent?         │
│                             ├─ YES → ITERATE outer (reframe)    │
│                             └─ NO → ESCALATE (can't stabilize)  │
└─────────────────────────────────────────────────────────────────┘
```

## Convergence Indicators

How to know when a decision is ready — not just made, but made well.

### Indicators

| Indicator | Meaning | How to Check |
|-----------|---------|--------------|
| **Frontrunner stability** | Same option leads across iterations | Compare rankings pass-over-pass |
| **Criteria stability** | Success criteria haven't changed | Frame document unchanged |
| **Trade-off clarity** | Can articulate what's gained AND lost | Trade-offs section complete |
| **Objection resolution** | Pressure-test arguments answered or accepted | I8-I9 documented with responses |
| **Stakeholder alignment** | Key perspectives accounted for | I10 shows perspectives checked |

### Thresholds by Level

| Level | Convergence Requirements |
|-------|-------------------------|
| **Adequate** | Frontrunner stable 1 pass, trade-offs stated, criteria defined |
| **Rigorous** | Frontrunner stable 2 passes, objections resolved, all perspectives checked, bias check completed |
| **Exhaustive** | Frontrunner stable 2+ passes, disconfirmation yielded nothing new, sensitivity analysis shows robustness, all activities at full depth |

### Convergence Failures

| Signal | Meaning | Action |
|--------|---------|--------|
| Frontrunner keeps changing | Criteria unclear or options too close | Revisit O3 (criteria) or accept near-tie |
| New criteria keep emerging | Frame not stable | Break to outer loop |
| Can't articulate trade-offs | Haven't done I4 properly | Iterate inner with I4 focus |
| Objections keep surfacing | Decision not ready | Continue iterating or escalate |

## Failure Modes

Each failure mode maps to an activity that prevents it. If a failure mode appears, the corresponding activity was skipped or done poorly.

### Frame Failures (Outer Loop)

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| Wrong problem | Decision solves something not asked | O1 — Identify the choice clearly |
| Infeasible options | Options proposed that can't actually work | O2 — Surface constraints first |
| Arbitrary selection | No clear basis for why one option wins | O3 — Define criteria explicitly |
| Stakeholder blindness | Key affected parties not considered | O4 — Identify stakeholders |
| Hidden assumptions | Decision invalidated when assumption fails | O5 — Surface assumptions |
| Scope confusion | Treating one decision as many, or vice versa | O6 — Check scope |
| Miscalibrated rigor | Over-engineering trivial or under-engineering critical | O7 — Assess reversibility |
| Blocked cascade | Decision stalls or breaks other decisions | O8 — Identify dependencies |
| Unintended consequences | Effects not anticipated | O9 — Identify downstream impact |

### Evaluation Failures (Inner Loop)

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| False dichotomy | Only 2 options considered when more exist | I1 — Generate 3+ alternatives |
| Action bias | Decided when doing nothing was valid | I2 — Consider null option |
| Premature narrowing | Missed hybrid or creative solutions | I3 — Check for hidden options |
| Invisible trade-offs | Gains stated, losses hidden | I4 — Assess trade-offs explicitly |
| Gut-feel decision | No traceable reasoning | I5 — Score against criteria |
| Deciding blind | Critical unknowns not addressed | I6 — Identify information gaps |
| Anchoring / sunk cost | Favoring familiar or invested option | I7 — Check for bias |
| Premature commitment | Chose without testing | I8 — Pressure-test frontrunner |
| Confirmation bias | Only sought supporting evidence | I9 — Seek disconfirming evidence |
| Single-viewpoint | Missed how others see it | I10 — Check perspectives |
| Unmitigated risks | Failure modes ignored | I11 — Identify risks |
| Cascade blindness | Downstream effects missed | I12 — Second-order effects |
| Fragile decision | Ranking breaks if assumptions wrong | I13 — Sensitivity analysis |

### Process Failures

| Failure Mode | Signal | Countermeasure |
|--------------|--------|----------------|
| Analysis paralysis | >3 iterations, no progress | Transition tree forces escalation |
| Premature exit | Decided before activities complete | Exit gate blocks incomplete decisions |
| Frame lock | Never revisiting frame despite signals | Tree forces break-to-outer when all options fail |

## Decision Levels

How much process to apply based on stakes.

### Level Definitions

| Level | When to Use | Key Characteristics |
|-------|-------------|---------------------|
| **Adequate** | Low stakes, easily reversible, time-constrained | Single pass may suffice, core activities only |
| **Rigorous** | Medium stakes, moderate cost of error | Full activity set, multiple passes expected |
| **Exhaustive** | High stakes, costly/irreversible, high uncertainty | Deep iteration, aggressive disconfirmation, sensitivity required |

### Adequate Fast Path (Minimum Compliant)

Use this when the decision is low stakes and reversible, but you still want a defensible record without generating a large artifact.

**Requirements (minimum):**

1) **Entry Gate (brief):** stakes level = adequate, time budget, iteration cap (default 2), allowed skips, escalation trigger.
2) **Frame:** decision statement, 2-5 constraints, 3-6 criteria (weights optional), key stakeholders (if any).
3) **Options:** 3+ options including **Null (do nothing/defer)**.
4) **Trade-offs:** 1-2 sentences per option (explicit gains and sacrifices).
5) **Evaluation:** lightweight scoring (or ranking) against criteria; call out any unknowns.
6) **Pressure test:** 2-3 strongest objections to the frontrunner and responses (or accepted risks).
7) **Decision:** choice, trade-offs accepted, confidence, and what would change the decision.

**Exit condition:** one pass is OK if the frontrunner is stable and trade-offs are explicit; otherwise do a second pass or escalate.

### Activity Requirements by Level

| Activity | Adequate | Rigorous | Exhaustive |
|----------|----------|----------|------------|
| **Outer Loop** | | | |
| O1-O4 (Choice, Constraints, Criteria, Stakeholders) | Required | Required | Required |
| O5 (Surface assumptions) | Light | Required | Deep |
| O6 (Check scope) | Quick check | Required | Required |
| O7-O9 (Reversibility, Dependencies, Downstream) | Noted | Required | Deep analysis |
| **Inner Loop** | | | |
| I1-I3 (Generate, Null, Hidden options) | 3+ options | 4+ options | Exhaust option space |
| I4-I5 (Trade-offs, Scoring) | Required | Required | Required |
| I6 (Information gaps) | Identify | Address critical | Address all |
| I7 (Bias check) | Quick check | Full check | Multiple checks |
| I8-I9 (Pressure-test, Disconfirm) | Basic | Active | Aggressive |
| I10 (Perspectives) | Key stakeholders | All stakeholders | Deep per stakeholder |
| I11-I12 (Risks, Second-order) | Identify | Analyze | Mitigate |
| I13 (Sensitivity) | Skip allowed | Recommended | Required |

### Recommended Scoring Rubric

To reduce "rigor theater," use a consistent scale and document uncertainty.

- **Scale:** 0-5 per criterion (0 = fails, 3 = acceptable, 5 = excellent).
- **Weights:** 1-5 per criterion (1 = minor, 3 = important, 5 = critical).
- **Weighted score:** `sum(score * weight)`; include totals and the unweighted narrative.
- **Unknowns:** If a score is speculative, mark it with `?` and list the uncertainty in **Information Gaps** (e.g., `2?`).
- **Hard constraints:** If an option violates a constraint, mark as **disqualified** instead of scoring it.

### Convergence by Level

| Level | Frontrunner Stability | Additional Requirements |
|-------|----------------------|------------------------|
| Adequate | 1 pass | Trade-offs stated |
| Rigorous | 2 passes | Objections resolved, perspectives checked |
| Exhaustive | 2+ passes | Disconfirmation empty, sensitivity robust |

## Worked Example (Adequate)

Example of an "Adequate" decision record for a common agentic choice (implementation approach), kept intentionally short.

```markdown
# Choose an Approach for Adding Retries to an HTTP Client

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate
- Decision trigger: flaky upstream occasionally returns 502/503
- Time pressure: today

## Entry Gate
- Stakes level: adequate (reversible code change, low blast radius)
- Time budget: 30 minutes
- Iteration cap: 2
- Evidence bar: confirm approach is correct for idempotent requests; avoid retry storms
- Allowed skips: deep stakeholder analysis; sensitivity analysis
- Escalation trigger: uncertainty about idempotency or request semantics

## Frame
### Decision Statement
How should we add retries to the HTTP client to reduce transient failures without causing retry storms?

### Constraints
- Must not retry non-idempotent requests by default
- Must cap total retry time (no unbounded waits)
- Must keep code simple (no new infra)

### Criteria
| Criterion | Weight | Definition |
|----------|--------|------------|
| Safety | 5 | Avoid duplicate side effects and retry storms |
| Effectiveness | 4 | Reduces transient failure rate |
| Complexity | 3 | Minimal code + cognitive load |
| Observability | 2 | Can see retries and reasons in logs/metrics |

## Options Considered
### Option 1: Simple exponential backoff with jitter (client-side)
- Trade-offs: improves resilience; slightly increases latency during incidents

### Option 2: Fixed delay retries (client-side)
- Trade-offs: easy; higher risk of thundering herd and less adaptive

### Option 3: No retries; improve server-side reliability only
- Trade-offs: avoids duplicate calls; does not address transient failures now

### Option 4: Null (defer)
- Trade-offs: no effort; continued flakiness and developer time lost

## Evaluation
| Option | Safety | Effectiveness | Complexity | Observability | Total |
|--------|--------|---------------|------------|---------------|-------|
| 1 | 4 | 4 | 3 | 3 | 4*5 + 4*4 + 3*3 + 3*2 = 20+16+9+6 = 51 |
| 2 | 3 | 3 | 4 | 2 | 15+12+12+4 = 43 |
| 3 | 5 | 1 | 5 | 2 | 25+4+15+4 = 48 |
| 4 | 5 | 0 | 5 | 0 | 25+0+15+0 = 40 |

### Information Gaps
- Exact mix of idempotent vs non-idempotent endpoints (assume most are GET; verify)

## Pressure Test
1. Objection: Retries may amplify load during outages.
   - Response: use capped exponential backoff + jitter; limit max attempts; log retry reasons.
2. Objection: Might retry non-idempotent calls by accident.
   - Response: default allowlist to idempotent methods; require explicit opt-in per endpoint.

## Decision
**Choice:** Option 1 (capped exponential backoff with jitter), only for idempotent requests by default.

**Trade-offs Accepted:** Some added latency during incidents; small complexity increase for safety controls.

**Confidence:** Medium (verify idempotency mix)

**Caveats:** If we discover many non-idempotent calls, revisit with per-endpoint policy or server-side fixes.
```

## Worked Example (Rigorous)

Example of a "Rigorous" decision record for a medium-stakes agentic choice where reversibility is moderate and multiple stakeholders care about different outcomes. Demonstrates multiple passes and an explicit convergence check.

```markdown
# Choose an Approach for Client-Side State Management in a Web App

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: rigorous
- Decision trigger: state logic is scattered; bugs increase with feature growth
- Time pressure: this sprint (no hard date)

## Entry Gate
- Stakes level: rigorous (moderate blast radius; change touches many screens)
- Time budget: 2-4 hours
- Iteration cap: 3
- Evidence bar: confirm we can migrate incrementally; confirm dev UX + maintainability gains
- Allowed skips: exhaustive stakeholder deep-dive; full sensitivity analysis (will do a light version)
- Escalation trigger: two options remain effectively tied after pass 2

## Frame
### Decision Statement
What state management approach should we adopt to reduce bugs and improve maintainability while enabling incremental migration?

### Constraints
- Must support incremental adoption (cannot rewrite the whole app at once)
- Must keep bundle size impact modest
- Must work with existing async data fetching patterns
- Must be testable (unit + integration)

### Criteria
| Criterion | Weight | Definition |
|----------|--------|------------|
| Incremental migration | 5 | Can adopt screen-by-screen without big-bang rewrite |
| Maintainability | 5 | Improves clarity of state ownership and updates |
| Developer experience | 4 | Debuggability, ergonomics, learning curve |
| Performance | 3 | Avoids unnecessary re-renders; predictable cost |
| Bundle/complexity cost | 3 | Adds minimal size and conceptual overhead |
| Testability | 4 | Enables deterministic tests and good seams |

### Stakeholders
| Stakeholder | What they value | Priority |
|-------------|-----------------|----------|
| Feature developers | speed + fewer footguns | High |
| QA | reproducible states and fewer regressions | Medium |
| Tech lead/maintainers | long-term maintainability | High |
| End users | performance and correctness | High |

### Assumptions
- A1: Most bugs stem from unclear state ownership. [Status: unverified]
- A2: We can migrate a module at a time without breaking routing. [Status: unverified]

### Reversibility
Moderate: changing patterns later is possible but expensive once widely adopted.

## Options Considered
### Option 1: Centralized store + selectors (predictable updates)
- Trade-offs: consistent mental model; adds framework concepts and boilerplate

### Option 2: Keep local state + lightweight context conventions
- Trade-offs: minimal new tooling; risk of continuing inconsistency and hidden coupling

### Option 3: Domain-module stores (multiple small stores with explicit boundaries)
- Trade-offs: good modularity; more architectural work and conventions to enforce

### Option 4: Null (defer)
- Trade-offs: no change now; bug rate and cognitive load likely keep rising

## Evaluation (Pass 1)

### Criteria Scores (0-5, weighted)
| Option | Incremental | Maint. | DevX | Perf | Cost | Test | Total |
|--------|-------------|--------|------|------|------|------|-------|
| 1 | 4 | 4 | 4 | 3 | 3 | 4 | 90 |
| 2 | 5 | 2 | 4 | 3 | 5 | 3 | 87 |
| 3 | 4 | 5 | 3 | 3 | 3 | 4 | 91 |
| 4 | 5 | 1 | 5 | 3 | 5 | 2 | 82 |

Notes:
- Weights: Incremental 5, Maintainability 5, DevX 4, Performance 3, Cost 3, Testability 4.
- Total = sum(score * weight). Example (Option 1): 4*5 + 4*5 + 4*4 + 3*3 + 3*3 + 4*4 = 90.

### Information Gaps
- How much boilerplate Option 1 introduces in our codebase (needs spike)
- Whether Option 3 boundaries will hold under real feature pressure

### Bias Check
- Risk: anchoring to what the team used before.
- Mitigation: score based on criteria, not familiarity; explicitly consider null + convention-only.

## Pressure Test (Pass 1)
Frontrunner: Option 3 (domain-module stores) by a small margin.

1. Objection: It might become a bespoke framework with inconsistent usage.
   - Response: define 2-3 hard rules (module boundary, naming, testing) and add a review checklist.
2. Objection: Option 1 is more standardized and hires know it.
   - Response: true; weigh maintainability + modularity vs standardization; keep migration path open.

## Evaluation (Pass 2)

### Disconfirmation Attempt
- Sought: reasons Option 3 fails incremental adoption or increases regression risk.
- Found: if boundaries are unclear, cross-module dependencies will reappear; needs explicit ownership docs.

### Light Sensitivity Analysis
- This example uses the same mechanics described in **Fast Sensitivity Analysis** above:
  - If DevX weight increases from 4 to 5, Option 1 ties or wins (more standardized tooling).
  - If Maintainability weight remains 5 and modular boundaries work, Option 3 remains ahead.

### Updated View
Option 3 still leads, but the margin is small and depends on boundary discipline.

## Perspectives (Pass 2)
| Stakeholder | View of Options | Concerns |
|-------------|-----------------|----------|
| Feature devs | prefer less boilerplate (Option 2/3) but want good debugging | unclear conventions becoming friction |
| Maintainers | like explicit boundaries (Option 3) | enforcement and consistency |
| QA | wants reproducible states and fewer edge cases | migration introducing mixed patterns |

## Decision
**Choice:** Option 3 (domain-module stores) with guardrails; retain the ability to adopt a centralized store in modules that need it.

**Trade-offs Accepted:** More upfront architectural work and enforcement; less standardization than Option 1.

**Confidence:** Medium-High (requires a short spike + documented boundaries)

**Caveats:** If spike reveals high inconsistency risk or tooling gaps, switch to Option 1.

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | None | 3 | Option 3 leads slightly; gaps identified |
| 2 | Clarified boundary enforcement requirement | 3 | Sensitivity shows Option 1 could tie if DevX dominates |

## Exit Gate (Rigorous)
- [x] Required outer loop activities complete at rigorous depth
- [x] Required inner loop activities complete at rigorous depth
- [x] Convergence met (frontrunner stable across 2 passes; objections addressed; perspectives checked)
- [x] Trade-offs explicitly documented
- [x] Decision defensible under scrutiny
```

## What Makes Exhaustive Different

Exhaustive decisions share the same structure as rigorous but go deeper on specific activities. Use exhaustive when the decision is high-stakes, costly to reverse, or has significant uncertainty.

### Key Differences from Rigorous

| Aspect | Rigorous | Exhaustive |
|--------|----------|------------|
| **Iteration cap** | 3 passes | 5 passes |
| **Option generation** | 4+ options | Exhaust option space (prove no hidden options remain) |
| **Disconfirmation** | Active (seek objections) | Aggressive (assign devil's advocate role; document what would falsify the frontrunner) |
| **Sensitivity analysis** | Recommended | Required (vary weights ±1; vary scores ±1; report if ranking changes) |
| **Information gaps** | Address critical gaps | Address all gaps or explicitly accept residual uncertainty |
| **Stakeholder perspectives** | All stakeholders checked | Deep per stakeholder (document their ranking, not just concerns) |
| **Convergence** | 2 passes stable | 2+ passes stable AND disconfirmation yielded nothing new |

### What Aggressive Disconfirmation Looks Like

1. **Falsification question:** "What evidence would prove the frontrunner is wrong?"
2. **Seek that evidence:** Actively look for it (don't just imagine objections).
3. **Document the search:** What you looked for, where, and what you found (or didn't).
4. **Red team the assumptions:** For each assumption, ask "What if this is false?" and trace the impact.

### Example Iteration Log (Exhaustive)

| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | None | A | Initial scoring; A leads by 12 points |
| 2 | Added constraint (compliance) | A | Constraint disqualifies option C |
| 3 | None | A | Disconfirmation found edge case; A still leads but margin narrowed |
| 4 | None | A | Sensitivity analysis: A wins under all weight variations |
| 5 | None | A | Final stakeholder deep-dive; no new objections |

### When Exhaustive Still Escalates

Even exhaustive decisions sometimes can't converge. Escalate when:

- **Critical information is unfillable:** A key unknown can't be resolved before the decision deadline.
- **Stakeholders irreconcilably conflict:** Their priorities produce different rankings with no clear tiebreaker.
- **Sensitivity shows fragility:** Small assumption changes flip the ranking repeatedly.
- **Iteration cap reached without stability:** Frontrunner keeps changing after 5 passes.

In these cases, document the state and ask the user to decide or accept explicit uncertainty.

## Exit Gate

Cannot claim "done" until all criteria pass.

| Criterion | Check |
|-----------|-------|
| **Frame complete** | All O1-O9 activities documented at required depth |
| **Evaluation complete** | All I1-I13 activities documented at required depth |
| **Convergence met** | Frontrunner stability and other indicators satisfied for chosen level |
| **Trade-offs explicit** | Decision record includes "Trade-offs Accepted" section |
| **Defensible** | Could explain reasoning to skeptical stakeholder |
| **Transition tree passed** | Exited via proper tree path, not bypassed |

### Exit Gate Failures

| Signal | Meaning | Action |
|--------|---------|--------|
| "Decided" but activities incomplete | Premature commitment | Block exit, complete activities |
| Trade-offs section empty | Invisible trade-offs | Cannot exit until stated |
| Frontrunner unstable | Not converged | Continue iterating or escalate |
| Can't explain reasoning | Gut-feel decision | Revisit I5 scoring |
| Exited without tree check | Process bypass | Re-evaluate via tree |

### Escalation Paths

When the framework cannot resolve:

| Situation | Escalation |
|-----------|------------|
| Frame won't stabilize | Ask user to clarify the actual decision |
| All options fail criteria | Ask user if constraints can change |
| Stuck >3 passes | Present current state, ask user to decide |
| Stakeholders conflict irreconcilably | Surface conflict, ask user for priority |
| Information gap is critical and unfillable | Document uncertainty, ask user for risk tolerance |

## Decision Record Template

Use this template (or an equivalent structure) for any decision produced under this framework.

```markdown
# [Decision Title]

## Context
- Protocol: decision-making.framework@1.0.0
- Stakes level: adequate / rigorous / exhaustive
- Decision trigger: [What prompted this decision?]
- Time pressure: [Deadline or "no constraint"]

## Entry Gate
- Stakes level: adequate / rigorous / exhaustive
- Time budget:
- Iteration cap:
- Evidence bar:
- Allowed skips:
- Escalation trigger:

## Frame
### Decision Statement
[The choice as a clear question]

### Constraints
- C1:
- C2:

### Criteria
| Criterion | Weight | Definition |
|-----------|--------|------------|
| | | |

### Stakeholders
| Stakeholder | What they value | Priority |
|-------------|-----------------|----------|
| | | |

### Assumptions
- A1: [Status: verified / unverified / invalidated]
- A2:

### Scope
- In bounds:
- Out of bounds:
- Related decisions:

### Reversibility
[How hard to undo? Informs rigor level]

### Dependencies
- Depends on:
- Blocks:

### Downstream Impact
- Enables:
- Precludes:

## Options Considered
### Option 1: [Name]
- Description:
- Trade-offs: Gains X, sacrifices Y

### Option 2: [Name]
...

### Option N: Null (do nothing / defer)
- Description:
- Trade-offs:

## Evaluation
### Criteria Scores
| Option | Criterion 1 | Criterion 2 | ... | Total |
|--------|-------------|-------------|-----|-------|
| | | | | |

### Risks per Option
| Option | Key Risks | Mitigation |
|--------|-----------|------------|
| | | |

### Information Gaps
- [What we don't know that could change ranking]

### Bias Check
- [Biases checked for, findings]

## Perspectives
| Stakeholder | View of Options | Concerns |
|-------------|-----------------|----------|
| | | |

## Pressure Test
### Arguments Against Frontrunner
1. [Objection]
   - Response:

### Disconfirmation Attempts
- Sought: [What would disprove this choice]
- Found: [Result]

## Decision
**Choice:** [Selected option]

**Trade-offs Accepted:** [What we're explicitly sacrificing]

**Confidence:** High / Medium / Low

**Caveats:** [What would change this decision]

## Downstream Impact
- This enables:
- This precludes:
- Next decisions triggered:

## Iteration Log
| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | | | |

## Exit Gate
- [ ] All outer loop activities complete
- [ ] All inner loop activities complete
- [ ] Convergence indicators met for chosen level
- [ ] Trade-offs explicitly documented
- [ ] Decision defensible under scrutiny
```
