# Framework for Decision-Making

A reusable framework for structured, defensible decisions during agentic work. Addresses: analysis paralysis, premature commitment, invisible trade-offs, and inconsistent reasoning.

## Protocol Header

| Field | Value |
| --- | --- |
| **Protocol ID** | `decision-making.framework` |
| **Version** | `1.0.0` |
| **Role** | Shared guidance for Agent Skills (SKILL.md) that require Claude to make decisions (implementation choices, task strategy, autonomy boundaries, etc.) |
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
- **Complete all outer loop activities** before entering the inner loop.
- **Complete all inner loop activities** before claiming a decision is ready.
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

## Entry Gate

Before starting, establish:

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

### Convergence by Level

| Level | Frontrunner Stability | Additional Requirements |
|-------|----------------------|------------------------|
| Adequate | 1 pass | Trade-offs stated |
| Rigorous | 2 passes | Objections resolved, perspectives checked |
| Exhaustive | 2+ passes | Disconfirmation empty, sensitivity robust |

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
