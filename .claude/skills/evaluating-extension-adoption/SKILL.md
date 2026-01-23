---
name: evaluating-extension-adoption
description: Use when deciding whether to adopt Claude Code extensions, patterns, methodologies, or approaches discovered during exploration. Use when asked to "evaluate [finding] for adoption", "should I adopt this approach", "compare these methodologies", or "evaluate all P0 findings". Consumes findings from exploring-claude-repos.
---

# Evaluating Extension Adoption

Structured evaluation of Claude Code extensions, patterns, and methodologies using the Framework for Decision-Making.

## Overview

This skill applies `decision-making.framework@1.0.0` to adoption decisions for findings from `exploring-claude-repos`, producing:

- Defensible adoption decisions with explicit trade-offs
- Stakeholder-aligned recommendations
- Pressure-tested conclusions that survive scrutiny

**The loop:** FRAME (what are we deciding?) → EVALUATE (assess options) → converge or iterate

**Default stakes:** Adequate (most adoption decisions are reversible)

**Protocol:** [references/framework-for-decision-making.md](references/framework-for-decision-making.md)

**Companion skill:** Use `exploring-claude-repos` first to discover findings with signals.

**Adoption outcomes:**
- **Adopt as-is** — Import directly into your setup
- **Adapt** — Import with specified modifications
- **Inspire** — Learn from the pattern, implement differently
- **Skip** — Not worth adopting (with rationale)
- **Defer** — Interesting but not now (with revisit trigger)

## Triggers

**Single finding evaluation:**
- "Evaluate F3 for adoption"
- "Should I adopt this skill/hook/pattern?"
- "Is this approach worth using?"

**Comparative evaluation:**
- "Should I use repo A's approach or repo B's?"
- "Compare these two methodologies"
- "Which pattern is better for my setup?"

**Batch triage:**
- "Evaluate all P0 findings"
- "Which of these findings should I prioritize?"
- "Triage these extensions for adoption"

**Slash command:** `/evaluate-extension`

**Pre-requisite:** Findings should come from `exploring-claude-repos` or be explicitly described. If no exploration has been done, recommend running exploration first.

## When to Use

**Use when:**
- You have findings from `exploring-claude-repos` and want to decide on adoption
- You found a specific extension/pattern and want structured adoption evaluation (no prior exploration required)
- Comparing approaches/patterns and need structured trade-off analysis
- Batch triaging multiple findings to prioritize what to adopt first
- Making adoption decisions that affect your workflow or setup

**Don't use when:**
- Decision is trivial (single line change, obvious yes/no) → just do it
- You've already decided and need implementation help → implement directly
- Pure information gathering (what exists?) → that's exploration, not evaluation

**Input modes:**
- **From exploration:** Findings come with signals (novelty, quality, conflict, complexity) pre-assessed
- **Ad-hoc:** Extension/pattern provided directly; skill gathers minimal context and assesses signals as part of framing

## Outputs

**Artifact:** Decision record at `docs/decisions/YYYY-MM-DD-<extension-or-pattern>-adoption.md`

**Decision record includes:**
- Context (protocol, stakes level, what triggered the decision)
- Frame (decision statement, constraints, criteria, stakeholders)
- Options evaluated (including null/defer)
- Trade-offs for each option
- Evaluation scoring
- Pressure-testing results
- Decision with explicit trade-offs accepted
- Iteration log (for rigorous/exhaustive)

**Inline summary (presented in chat):**

```
**Decision:** [Adopt / Adapt / Inspire / Skip / Defer]

**Why:** [2-3 sentence positive case]

**Trade-offs accepted:** [What's being sacrificed]

**Confidence:** High / Medium / Low

**Caveats:** [What would change this decision]

**Full analysis:** [link to decision record]
```

**Batch mode output:**
- Prioritized list of findings with decision for each
- Summary table: Finding ID | Decision | Confidence | Key reason
- Individual decision records for complex items (P0 findings)
- Consolidated record acceptable for straightforward items (P1/P2)

**Definition of Done:**
- Entry Gate completed (stakes calibrated)
- Frame stable (criteria defined, stakeholders identified)
- Convergence indicators satisfied for stakes level
- Trade-offs explicitly documented
- Decision record written
- Inline summary presented

## Process

This skill follows `decision-making.framework@1.0.0`. This section summarizes; see [references/framework-for-decision-making.md](references/framework-for-decision-making.md) for full protocol.

### Entry Gate

Before evaluation, establish:

| Field | Record |
|-------|--------|
| Stakes level | adequate / rigorous / exhaustive |
| Rationale | Why this level (reversibility, blast radius, cost of error) |
| Iteration cap | adequate: 2, rigorous: 3, exhaustive: 5 |
| Evidence bar | What's needed before deciding |
| Escalation trigger | What causes escalation to user |

**Stakes calibration:**

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |

**Default:** Adequate (most extension adoptions are reversible)

**Gate check:** Cannot proceed until stakes level chosen and evidence bar set.

### Consuming Exploration Findings

When findings come from `exploring-claude-repos`, signals map to the decision frame:

| Signal | How it informs evaluation |
|--------|---------------------------|
| **Novelty** | Frames the decision: `new` → full evaluation; `similar-to` → compare to existing; `extends` → incremental decision |
| **Quality** | Becomes a criterion weight: `polished` reduces implementation risk; `rough` increases it |
| **Conflict** | Becomes a hard constraint: `conflicts-with` may disqualify or require resolution |
| **Complexity** | Informs effort/risk criteria: `drop-in` vs `significant-integration` |

**Ad-hoc input (no prior exploration):**
1. Read the extension/pattern source
2. Assess the four signals against user's setup
3. Proceed to framing with signals as input

### Outer Loop: Frame the Decision

| Activity | Question | Failure if Skipped |
|----------|----------|-------------------|
| **Identify the choice** | Adopt this extension/pattern? Compare approaches? | Wrong problem |
| **Surface constraints** | Technical compatibility, dependencies, philosophy fit | Infeasible adoption |
| **Define criteria** | What does "good adoption" look like? Weights 1-5. | Arbitrary decision |
| **Identify stakeholders** | Who's affected? (You, team, future maintainers) | Missing perspectives |
| **Surface assumptions** | What about your setup are you taking for granted? | Hidden blockers |
| **Assess reversibility** | How hard to undo this adoption? | Miscalibrated rigor |

**Default criteria for extension adoption:**

| Criterion | Weight | Definition |
|-----------|--------|------------|
| Value | 5 | Does this improve my workflow meaningfully? |
| Fit | 4 | Compatible with my setup, philosophy, patterns? |
| Effort | 3 | Implementation and maintenance burden? |
| Risk | 3 | What could go wrong? Conflict, breakage? |

Adjust weights based on context. Add domain-specific criteria as needed.

**Frame converges when:** Criteria and constraints stable across an evaluation pass.

### Inner Loop: Evaluate Options

**Generate options (always include null):**

| Option | Description |
|--------|-------------|
| **Adopt as-is** | Import directly, minimal changes |
| **Adapt** | Import with modifications (specify what) |
| **Inspire** | Learn pattern, implement differently |
| **Skip** | Don't adopt (with rationale) |
| **Defer** | Not now, revisit when [trigger] |

**Score against criteria:**

| Score | Meaning |
|-------|---------|
| 0 | Fails criterion |
| 3 | Acceptable |
| 5 | Excellent |

**Weighted total:** `sum(score × weight)`

**Pressure-test the frontrunner:**

| Lens | Question |
|------|----------|
| **Kill it** | What's the strongest argument against adopting? |
| **Pre-mortem** | 3 months later, this adoption failed. What happened? |
| **Steelman alternatives** | What would make Skip/Defer better than adopting? |
| **Conflict check** | Does this clash with anything in my current setup? |

**Check perspectives:**
- How does this affect daily workflow?
- What about edge cases or advanced usage?
- Will future-me thank or curse this decision?

### Transition Trees

**After inner loop pass:**

```
Clear frontrunner?
├─ NO → More options possible?
│        ├─ YES → ITERATE (generate more options)
│        └─ NO → BREAK to outer (reframe)
│
└─ YES → Survived pressure-testing?
         ├─ NO → Can objections be addressed?
         │        ├─ YES → ITERATE (revise option or find new frontrunner)
         │        └─ NO → Consider Skip/Defer as frontrunner
         └─ YES → Convergence met?
                  ├─ NO → ITERATE
                  └─ YES → EXIT (decide)

ESCAPE: Stuck after cap? → ESCALATE to user
```

### Convergence Indicators

| Level | Requirements |
|-------|--------------|
| **Adequate** | Frontrunner stable 1 pass, trade-offs stated |
| **Rigorous** | Frontrunner stable 2 passes, objections resolved |
| **Exhaustive** | Frontrunner stable 2+ passes, disconfirmation yielded nothing |

### Exit Gate

Cannot claim "done" until:
- [ ] Frame complete (criteria defined, constraints surfaced)
- [ ] All options evaluated (including Skip/Defer)
- [ ] Frontrunner pressure-tested
- [ ] Trade-offs explicitly documented
- [ ] Convergence indicators satisfied for stakes level
- [ ] Decision record written
- [ ] Inline summary presented

## Decision Points

**Choosing stakes level:**
- Single extension, easily removed → Adequate
- Pattern that affects multiple workflows → Rigorous
- Philosophical shift or foundational change → Exhaustive

**When signals conflict:**
- High quality but high conflict → Conflict is a hard constraint; evaluate if resolution is worth the effort
- High novelty but high complexity → Value vs effort trade-off; score against criteria
- Low quality but high value → Adapt option may address quality; assess effort to improve

**When comparison targets differ philosophically:**
- Document the philosophical difference explicitly
- "Better" may be context-dependent, not absolute
- Consider: which philosophy fits YOUR setup and preferences?

**Single vs batch evaluation:**
- Single finding → Full decision record
- Batch (3-5 findings) → Summary table + individual records for P0 items
- Large batch (>5) → Triage first (quick pass to identify P0s), then evaluate P0s fully

**When the answer is obviously Skip:**
- Still document why (2-3 sentences minimum)
- "Obviously skip" without rationale is assertion, not evaluation
- Future you may not remember why it was obvious

**When the answer is Defer:**
- Specify the revisit trigger: "Revisit when X happens"
- Without a trigger, Defer becomes Skip in practice

**Ad-hoc input (no exploration):**
- Spend time understanding the extension/pattern before framing
- Assess the four signals (novelty, quality, conflict, complexity) explicitly
- Treat this as mini-exploration focused on one item

**Pressure to skip process ("just tell me yes or no"):**
- Acknowledge the request
- Complete at least Entry Gate + one evaluation pass
- Compress output: "Yes, adopt it. Trade-off: X. Full analysis in decision record."

## Examples

**Scenario:** User asks "Evaluate F1 (tdd-workflow skill) for adoption" after exploring a community repo.

### BAD: Gut-feel recommendation

Claude glances at the skill and says:

> "Yes, you should adopt the TDD workflow skill. It looks well-structured and TDD is a good practice. Just copy it to your skills folder."

**Why it's bad:**
- No Entry Gate — stakes not assessed
- No criteria defined — "well-structured" isn't a criterion
- No alternatives considered — what about Adapt, Inspire, or Defer?
- No trade-offs stated — what does adoption cost?
- No pressure-testing — what could go wrong?
- No decision record — reasoning not preserved

### GOOD: Framework-driven evaluation

**Entry Gate:**
- Stakes: Adequate (skill can be removed if it doesn't work)
- Evidence bar: Understand skill behavior, check for conflicts

**Consuming signals from exploration:**
- Novelty: `new` (user has no TDD skill)
- Quality: `polished` (well-documented, clear structure)
- Conflict: `none`
- Complexity: `needs-adaptation` (references testing framework user doesn't use)

**Frame:**
- Decision: Should I adopt this TDD workflow skill?
- Constraints: Must work with my test runner (pytest, not jest)
- Criteria: Value (5), Fit (4), Effort (3), Risk (3)

**Options:**

| Option | Value | Fit | Effort | Risk | Total |
|--------|-------|-----|--------|------|-------|
| Adopt as-is | 5 | 2 | 5 | 2 | 54 |
| Adapt (change test runner refs) | 5 | 5 | 3 | 4 | 66 |
| Inspire (write my own TDD skill) | 5 | 5 | 1 | 5 | 59 |
| Skip | 0 | 5 | 5 | 5 | 45 |
| Defer | 2 | 5 | 5 | 5 | 51 |

**Pressure-test (Adapt):**
- Kill it: "Adapting means ongoing maintenance if upstream changes"
- Response: Acceptable — skill is self-contained, upstream changes unlikely to affect core workflow
- Pre-mortem: "Adaptation missed a jest reference, skill broke on first use"
- Response: Do thorough search-replace, test before committing

**Inline output:**

> **Decision:** Adapt
>
> **Why:** TDD workflow adds significant value. Adaptation is straightforward (test runner references). Quality is high, reducing implementation risk.
>
> **Trade-offs accepted:** One-time adaptation effort; won't receive upstream updates automatically.
>
> **Confidence:** High
>
> **Caveats:** If adaptation proves more complex than expected, consider Inspire instead.
>
> **Full analysis:** docs/decisions/2024-01-15-tdd-workflow-adoption.md

**Why it's good:**
- Stakes calibrated before analysis
- Signals from exploration informed the frame
- All five options considered with scoring
- Trade-offs explicit
- Frontrunner pressure-tested
- Decision record preserves reasoning

## Anti-Patterns

**Pattern:** Skipping the null option (Skip/Defer)
**Why it fails:** "Should I adopt X?" assumes adoption is the right answer. Skip and Defer are valid outcomes that must be evaluated.
**Fix:** Always include Skip and Defer as options. Score them against criteria like any other option.

**Pattern:** "Obviously should adopt" without adversarial challenge
**Why it fails:** Confidence is when you're most likely to miss something. The adversarial phase exists precisely for "obvious" choices.
**Fix:** Pre-mortem and pressure-test are mandatory. If objections don't cause discomfort, they're too weak.

**Pattern:** Treating signals as decisions
**Why it fails:** `quality: polished` doesn't mean "adopt." Signals inform the frame; criteria determine the decision.
**Fix:** Signals → frame inputs. Criteria → evaluation. Decision → weighted scoring + pressure-testing.

**Pattern:** Skipping conflict resolution
**Why it fails:** `conflicts-with: X` noted but not addressed means adopting a known problem.
**Fix:** Conflict is a hard constraint. Either resolve it (adaptation plan) or it disqualifies the option.

**Pattern:** Defer without trigger
**Why it fails:** "Maybe later" without specifying when becomes "never." Defer decays into Skip.
**Fix:** Every Defer needs a revisit trigger: "Revisit when X happens" or "Revisit in Y context."

**Pattern:** Batch triage without prioritization
**Why it fails:** "Evaluate these 10 findings" with equal depth for all wastes effort on low-value items.
**Fix:** Quick pass to categorize by priority. Full evaluation for P0s; summary decisions for P1/P2.

**Pattern:** Hiding uncertainty behind confident language
**Why it fails:** "Adopt this" sounds authoritative but may be a guess. User can't calibrate trust.
**Fix:** State confidence level. "High confidence — well-understood extension, clear fit" vs "Medium — untested in similar setups."

**Pattern:** No decision record for "simple" decisions
**Why it fails:** Simple decisions still have reasoning. Without a record, you can't revisit or learn from outcomes.
**Fix:** Every evaluation produces at least an inline summary. Adequate stakes can use shorter records, but not zero.

## Troubleshooting

**Symptom:** All options score similarly (near-tie)
**Cause:** Criteria not weighted appropriately, or options are genuinely close
**Next steps:**
- Revisit criteria weights — does one criterion matter more than reflected?
- If genuinely close, pick based on declared priority (e.g., lower risk > higher value)
- Or: run a small experiment to break the tie

**Symptom:** Frontrunner keeps changing across passes
**Cause:** Frame unstable, or new information keeps emerging
**Next steps:**
- Check if criteria are well-defined and stable
- Check if you're discovering new constraints mid-evaluation
- If frame keeps changing, BREAK to outer loop and stabilize

**Symptom:** Pressure-test feels perfunctory
**Cause:** Not genuinely trying to break the recommendation
**Next steps:**
- Pre-mortem should produce a plausible failure story
- If objections don't cause discomfort, dig harder
- Try: "What would someone who chose Skip say about this?"

**Symptom:** Can't assess signals (no exploration, unfamiliar extension)
**Cause:** Ad-hoc input without enough context
**Next steps:**
- Spend more time reading the extension/pattern source
- Compare against your setup explicitly to assess novelty/conflict
- If still unclear, run lightweight exploration first

**Symptom:** User disagrees with decision
**Cause:** Different criteria weights, unstated constraints, or different risk tolerance
**Next steps:**
- Don't defend — explore: "What matters most to you here?"
- Update frame with user's actual priorities
- Re-evaluate with corrected weights

**Symptom:** Decision was Adopt, but adoption failed
**Cause:** Pressure-testing missed something, or circumstances changed
**Next steps:**
- Not a skill failure — the process worked if reasoning was sound at the time
- Document what was missed for future evaluations
- Consider: was this predictable? Should stakes have been higher?

**Symptom:** Too many findings to evaluate individually
**Cause:** Batch too large for thorough evaluation
**Next steps:**
- Triage first: quick pass to categorize by priority
- Full evaluation for P0 items only
- Summary decisions for P1/P2 (one-liner rationale acceptable)

## Verification

**Quick check:** Decision record written with trade-offs explicit and convergence met for stakes level.

**Deeper validation:**

Entry Gate:
- [ ] Stakes level assessed with rationale
- [ ] Evidence bar set
- [ ] Iteration cap appropriate for stakes

Frame:
- [ ] Decision statement is clear question
- [ ] Criteria defined with weights
- [ ] Constraints surfaced (including from conflict signals)
- [ ] Signals from exploration consumed (if applicable)

Evaluation:
- [ ] All five options considered (Adopt, Adapt, Inspire, Skip, Defer)
- [ ] Scoring against weighted criteria
- [ ] Defer has revisit trigger (if selected)

Adversarial:
- [ ] Frontrunner pressure-tested with genuine objections
- [ ] Pre-mortem produced plausible failure scenario
- [ ] Objections addressed or accepted as trade-offs

Convergence:
- [ ] Frontrunner stable for required passes
- [ ] Trade-offs explicitly documented
- [ ] Iteration log shows what changed (for rigorous/exhaustive)

Output:
- [ ] Decision record written at `docs/decisions/YYYY-MM-DD-<name>-adoption.md`
- [ ] Inline summary presented with decision, trade-offs, confidence, caveats

**Self-test:** If this decision turns out wrong, would the record help you understand why and what to try instead?

## References

**Required protocol:**
- [references/framework-for-decision-making.md](references/framework-for-decision-making.md) — Full framework specification (Entry/Exit Gates, nested loops, transition trees, convergence indicators, decision record template)

**Companion skill:**
- `exploring-claude-repos` — Use first to discover extensions/patterns with signals

**The framework reference contains:**
- Normative requirements (MUST/SHOULD/MAY)
- Outer loop activities (Frame the Decision)
- Inner loop activities (Evaluate Options)
- Transition trees for loop navigation
- Convergence indicators by stakes level
- Decision Record Template
- Worked examples (Adequate, Rigorous, Exhaustive)
