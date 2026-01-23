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

**Protocol:** [references/framework-for-decision-making_v1.0.0.md](references/framework-for-decision-making_v1.0.0.md) — **YOU MUST read this file for normative requirements (MUST/SHOULD/MAY), activity depth by level, transition trees, and Decision Record Template.**

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

**IMPORTANT:** The full evaluation report goes in the artifact ONLY. Chat receives a brief summary. Do NOT reproduce the full analysis, scoring tables, or pressure-testing details in chat.

**Artifact (full report):** Decision record at `docs/decisions/YYYY-MM-DD-<extension-or-pattern>-adoption.md`

**Decision record structure:** Use the **Decision Record Template** from the framework (see [references/framework-for-decision-making_v1.0.0.md](references/framework-for-decision-making_v1.0.0.md)). Required sections:
- Context (protocol version, stakes level, decision trigger, time pressure)
- Entry Gate (all fields: stakes, rationale, time budget, iteration cap, evidence bar, allowed skips, overrides, escalation trigger)
- Frame (decision statement as clear question, constraints, criteria with weights, stakeholders with values and priorities, assumptions with status, scope, reversibility, dependencies, downstream impact)
- Options Considered (each with description and trade-offs including null/defer)
- Evaluation (criteria scores table, risks per option, information gaps, bias check)
- Perspectives (stakeholder views table)
- Pressure Test (arguments against frontrunner with responses, disconfirmation attempts)
- Decision (choice, trade-offs accepted, confidence, caveats)
- Downstream Impact (enables, precludes, next decisions triggered)
- Iteration Log (pass-by-pass: frame changes, frontrunner, key findings)
- Exit Gate (all criteria with explicit status)

**Chat summary (brief — not the full report):**

```
**Decision:** [Adopt / Adapt / Inspire / Skip / Defer] — [Finding ID if applicable]

**Why:** [1-2 sentences — the key reason]

**Trade-offs:** [What's being sacrificed, briefly]

**Confidence:** High / Medium / Low

**Full analysis:** `docs/decisions/YYYY-MM-DD-<name>-adoption.md`
```

Do NOT include in chat: scoring tables, detailed options analysis, pressure-testing questions/answers, iteration logs, or full constraint lists. These belong in the artifact only.

**Batch mode output:**
- Prioritized list of findings with decision for each
- Summary table: Finding ID | Decision | Confidence | Key reason
- Individual decision records for complex items (P0 findings)
- Consolidated record acceptable for straightforward items (P1/P2)

**Definition of Done:**
- Entry Gate completed (stakes calibrated)
- Frame stable (criteria defined, stakeholders identified)
- Signals consumed explicitly (if from exploration)
- Convergence indicators satisfied for stakes level
- Trade-offs explicitly documented
- Decision record written to artifact
- Brief summary presented in chat (NOT full report)

## Process

This skill follows `decision-making.framework@1.0.0`. This section summarizes; see [references/framework-for-decision-making_v1.0.0.md](references/framework-for-decision-making_v1.0.0.md) for full protocol.

### Entry Gate

Before evaluation, establish:

| Field | Record |
|-------|--------|
| Decision trigger | What prompted this decision? |
| Stakes level | adequate / rigorous / exhaustive |
| Rationale | Why this level (use Stakes Calibration Rubric) |
| Time budget | Is there urgency? Deadline or "no constraint" |
| Iteration cap | adequate: 2, rigorous: 3, exhaustive: 5 |
| Evidence bar | What must be true before EXIT is allowed? |
| Allowed skips | Which optional activities will be skipped and why? |
| Overrides | Any non-default parameters? Format: `[param]: [old]→[new] because [reason]` |
| Escalation trigger | What causes escalation to user? |
| Initial frame | What do we think we're deciding? (Draft decision statement) |
| Known constraints | What limits are already apparent? |
| Known stakeholders | Who's obviously affected? |

**Stakes calibration:**

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High (need action) | Moderate | Low / no constraint |

**Rule of thumb:** If any two factors land in a higher column, choose that higher stakes level. To choose a lower level despite this, document in Entry Gate: (1) which factors triggered the higher level, and (2) why those factors don't apply here.

**Default:** Adequate (most extension adoptions are reversible)

**Recalibration:** If during evaluation you discover the decision is more complex than initially assessed (hidden dependencies, stakeholder conflict, option space expands):
1. **Pause** at the current pass boundary
2. **Re-evaluate** using the Stakes Calibration Rubric
3. **If stakes level changes:** Document in iteration log: `Recalibrated from [old level] to [new level] because [trigger]`
4. **Adjust** iteration cap and activity depth accordingly
5. **Continue** from current pass (don't restart)

**Gate check:** Cannot proceed until stakes level chosen, initial frame drafted, and evidence bar set.

### Consuming Exploration Findings

When findings come from `exploring-claude-repos`, signals MUST be explicitly consumed in the decision frame.

**Reference the finding ID:** When evaluating a finding (e.g., F3), include its ID in the Entry Gate and Frame sections.

**Mandatory signal mapping:**

| Signal | How it informs evaluation | Frame location |
|--------|---------------------------|----------------|
| **Novelty** | Frames the decision: `new` → full evaluation; `similar-to` → compare to existing; `extends` → incremental decision | Include in "Identify the choice" |
| **Quality** | Becomes a criterion weight: `polished` reduces implementation risk; `rough` increases it | Adjust Risk/Effort criterion weights |
| **Conflict** | Becomes a hard constraint: `conflicts-with` may disqualify or require resolution | Add to "Surface constraints" |
| **Complexity** | Informs effort/risk criteria: `drop-in` vs `significant-integration` | Add to "Surface constraints" |

**When framing, explicitly state:**
```
**Finding:** F3 — tdd-workflow skill
**Signals consumed:**
- Novelty: new → requires full evaluation
- Quality: polished → lower Risk weight (2 instead of 3)
- Conflict: none → no hard constraints from signals
- Complexity: needs-adaptation → adds effort constraint
```

**Ad-hoc input (no prior exploration):**
1. Read the extension/pattern source
2. Assess the four signals against user's setup
3. Document signal assessment before proceeding to framing

### Outer Loop: Frame the Decision

| Activity | Question | Failure if Skipped |
|----------|----------|-------------------|
| **Identify the choice** | Adopt this extension/pattern? Compare approaches? | Wrong problem |
| **Surface constraints** | Technical compatibility, dependencies, philosophy fit | Infeasible adoption |
| **Define criteria** | What does "good adoption" look like? Weights 1-5. | Arbitrary decision |
| **Identify stakeholders** | Who's affected? (You, team, future maintainers) | Missing perspectives |
| **Surface assumptions** | What about your setup are you taking for granted? | Hidden blockers |
| **Check scope** | Is this one decision or several? Should we split/combine? | Scope confusion |
| **Assess reversibility** | How hard to undo this adoption? | Miscalibrated rigor |
| **Identify dependencies** | Does this block or depend on other decisions? | Blocked cascade |
| **Identify downstream impact** | What will this decision affect later? | Unintended consequences |

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
| 0 | Completely fails to meet |
| 1-2 | Below acceptable |
| 3 | Meets expectations |
| 4 | Exceeds expectations |
| 5 | Excellent |

**Weights:** 1-5 per criterion (1 = minor consideration, 3 = important, 5 = critical/blocking)

**Weighted total:** `sum(score × weight)` — include totals and brief narrative for non-obvious scores

**Unknowns:** If a score is speculative, mark it with `?` (e.g., `3?`) and list the uncertainty in Information Gaps

**Hard constraints:** If an option violates a hard constraint (from O2), mark as **DISQUALIFIED** — do not score it. Disqualified options cannot be chosen.

**Check for bias (before pressure-testing):**

| Bias | Check Question | If Yes |
|------|----------------|--------|
| **Anchoring** | Was my first option still the frontrunner? | Re-score in random order |
| **Familiarity** | Is frontrunner something I've used before? | Score unfamiliar option's learning curve vs long-term benefit |
| **Sunk cost** | Have I already invested in one option? | Score as if starting fresh |
| **Confirmation** | Did I seek evidence FOR my frontrunner more than AGAINST? | Run pressure-test more aggressively |

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

**Second-order effects:**
- What does this choice enable next? (new capabilities, patterns, integrations)
- What does it preclude? (conflicting patterns, alternative approaches)

**Sensitivity analysis (rigorous/exhaustive):**
- **Weight swap:** Increase the most important criterion's weight by +1 (or decrease by -1) and recalculate totals. If the leader changes, flag as near-tie.
- **Assumption flip:** For one key assumption, score the frontrunner under "best plausible" and "worst plausible" interpretations. If ranking changes, the decision is fragile on that assumption.
- **Threshold check:** If any hard constraint is near-violated (within 10% of limit), treat as disqualified until verified.

### Activity Depth by Level

| Activity | Adequate | Rigorous | Exhaustive |
|----------|----------|----------|------------|
| **I1-I3** (Options) | 3+ options | 4+ options | 5+ options; document search |
| **I4-I5** (Trade-offs, Scoring) | Required | Required | Required |
| **I6** (Information gaps) | Identify | Address critical | Address all |
| **I7** (Bias check) | Quick check | Full check | Multiple checks |
| **I8-I9** (Pressure-test, Disconfirm) | Basic | Active | Aggressive |
| **I10** (Perspectives) | Key stakeholders | All stakeholders | Deep per stakeholder |
| **I11-I12** (Risks, Second-order) | Identify | Analyze | Mitigate |
| **I13** (Sensitivity) | Skip allowed | Recommended | Required |

**What "Aggressive" disconfirmation looks like (exhaustive):**
1. **Falsification question:** "What evidence would prove the frontrunner is wrong?"
2. **Seek that evidence:** Actively look for it (don't just imagine objections)
3. **Document the search:** What you looked for, where, and what you found (or didn't)
4. **Red team assumptions:** For each assumption, ask "What if this is false?" and trace the impact

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
| **Adequate** | Frontrunner stable 1 pass, trade-offs stated, criteria defined |
| **Rigorous** | Frontrunner stable 2 consecutive passes, objections resolved, all perspectives checked, bias check completed |
| **Exhaustive** | Frontrunner stable 2+ consecutive passes, disconfirmation yielded nothing new, sensitivity analysis shows robustness, all activities at full depth |

### Escalation Paths

When the framework cannot resolve, escalate to the user:

| Situation | Escalation Action |
|-----------|-------------------|
| **Frame won't stabilize** | Ask user to clarify the actual decision |
| **All options fail criteria** | Ask user if constraints can change |
| **Stuck after iteration cap** | Present current state, ask user to decide |
| **Stakeholders conflict irreconcilably** | Surface conflict, ask user for priority |
| **Critical information gap is unfillable** | Document uncertainty, ask user for risk tolerance |

**What to provide when escalating:**
1. Current state: What was evaluated, what the frontrunner is (if any), what remains uncertain
2. Blocking issue: Why the framework cannot proceed
3. Options considered: What was tried, why it didn't resolve
4. Decision needed: Specific question the user must answer

### Near-Ties

When top options are close, avoid false precision. Treat as near-tie if:
- Top two options within 10% of each other on weighted score, OR
- Ranking flips when any single weight changes by ±1, OR
- Difference depends on an unresolved information gap

**Near-tie actions (pick one and document):**
- **Treat as tie:** Choose based on declared priority (e.g., lower risk > higher value)
- **Run experiment:** Small spike targeting the unknown most likely to change ranking
- **Defer/phase:** Pick safest reversible step now; schedule decision when evidence arrives
- **Escalate:** When trade-offs are value-laden or stakeholders disagree

### Exit Gate

Cannot claim "done" until ALL criteria pass:

| Criterion | Check |
|-----------|-------|
| **Frame complete** | All O1-O9 activities documented at required depth for level |
| **Signals consumed** | If from exploration: finding ID and signal → frame mapping explicit |
| **Evaluation complete** | All I1-I13 activities documented at required depth for level |
| **Bias check** | Completed at Entry Gate start, after pressure-testing, and before final exit |
| **All options evaluated** | Including Skip/Defer; each scored against criteria |
| **Frontrunner pressure-tested** | With genuine objections (not softball) |
| **Second-order effects** | Documented: what this enables, what it precludes |
| **Sensitivity analysis** | Completed at required depth (skip allowed at adequate; required at exhaustive) |
| **Trade-offs explicit** | "Trade-offs Accepted" section complete — no decision without stating sacrifices |
| **Convergence met** | Frontrunner stable for required passes (1 adequate, 2 rigorous, 2+ exhaustive) |
| **Transition tree passed** | Exited via proper tree path (not bypassed); documented which path |
| **Defensible** | Could explain reasoning to skeptical stakeholder |
| **Decision record written** | At `docs/decisions/YYYY-MM-DD-<name>-adoption.md` |
| **Summary presented** | Brief summary in chat (NOT full report) |

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

**Signals consumed (explicit — required):**
```
**Finding:** F1 — tdd-workflow skill
**Signals consumed:**
- Novelty: new → requires full evaluation (user has no TDD skill)
- Quality: polished → lower Risk weight (2 instead of 3)
- Conflict: none → no hard constraints from signals
- Complexity: needs-adaptation → adds constraint (references jest, user has pytest)
```

**Frame:**
- Decision: Should I adopt this TDD workflow skill?
- Constraints: Must work with my test runner (pytest, not jest) [from complexity signal]
- Criteria: Value (5), Fit (4), Effort (3), Risk (2) [reduced from 3 due to quality signal]

**Options, scoring, and pressure-testing:** *(documented in decision record, not shown in chat)*

**Chat output (brief summary only):**

> **Decision:** Adapt — F1
>
> **Why:** TDD workflow adds significant value; adaptation is straightforward (test runner refs).
>
> **Trade-offs:** One-time adaptation effort; no automatic upstream updates.
>
> **Confidence:** High
>
> **Full analysis:** `docs/decisions/2024-01-15-tdd-workflow-adoption.md`

**Why it's good:**
- Stakes calibrated before analysis
- Signals explicitly consumed and documented
- Signals inform criteria weights and constraints
- Full analysis (scoring, pressure-testing) in artifact only
- Chat gets brief summary, not full report
- Decision record preserves complete reasoning

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

**Quick check:** Decision record written with trade-offs explicit; brief summary in chat (not full report).

**Deeper validation:**

Entry Gate:
- [ ] All 12 Entry Gate fields recorded
- [ ] Stakes level assessed with rationale (all 5 factors considered)
- [ ] Initial frame drafted
- [ ] Evidence bar set
- [ ] Iteration cap appropriate for stakes

Frame (Outer Loop):
- [ ] O1: Decision statement is clear question
- [ ] O2: Constraints surfaced (including from conflict signals)
- [ ] O3: Criteria defined with weights (1-5)
- [ ] O4: Stakeholders identified with what they value
- [ ] O5: Assumptions surfaced with status
- [ ] O6: Scope checked (one decision or several?)
- [ ] O7: Reversibility assessed
- [ ] O8: Dependencies identified (blocks/blocked-by)
- [ ] O9: Downstream impact identified (enables/precludes)
- [ ] Signals from exploration consumed explicitly (finding ID, signal → frame mapping)

Evaluation (Inner Loop):
- [ ] I1-I3: All five options considered (Adopt, Adapt, Inspire, Skip, Defer)
- [ ] I4-I5: Scoring against weighted criteria with trade-offs
- [ ] I6: Information gaps identified (and addressed at rigorous+)
- [ ] I7: Bias check completed (at required depth for level)
- [ ] I8-I9: Frontrunner pressure-tested with genuine objections
- [ ] I10: Perspectives checked (at required depth for level)
- [ ] I11-I12: Risks and second-order effects documented
- [ ] I13: Sensitivity analysis completed (at required depth for level)
- [ ] Defer has revisit trigger (if selected)

Convergence:
- [ ] Frontrunner stable for required passes (1/2/2+ by level)
- [ ] Near-tie handled if applicable (action documented)
- [ ] Trade-offs explicitly documented ("Trade-offs Accepted" section)
- [ ] Iteration log shows what changed (for rigorous/exhaustive)
- [ ] Transition tree exited via proper path (documented which path)

Output:
- [ ] Decision record written at `docs/decisions/YYYY-MM-DD-<name>-adoption.md`
- [ ] Full analysis (scoring, pressure-testing, options) in artifact ONLY
- [ ] Chat contains brief summary: decision, why (1-2 sentences), trade-offs, confidence, link
- [ ] Chat does NOT contain: scoring tables, detailed options, pressure-test Q&A, iteration logs

**Self-test:** If this decision turns out wrong, would the record help you understand why and what to try instead?

## References

**Required protocol — YOU MUST read before executing:**
- [references/framework-for-decision-making_v1.0.0.md](references/framework-for-decision-making_v1.0.0.md) — Full framework specification

**The framework reference contains (authoritative):**
- Normative requirements (MUST/SHOULD/MAY) — this skill inherits them
- Key Terms definitions (pass, iteration, frontrunner, convergence, escalation)
- Stakes Calibration Rubric — for choosing stakes level
- Recalibration procedure — for mid-execution adjustments
- Outer loop activities (O1-O9) — Frame the Decision
- Inner loop activities (I1-I13) — Evaluate Options with depth by level
- Bias Check Questions — the 5 biases to check
- Transition trees — for loop navigation (inner and outer)
- Near-Ties handling — 4 specific actions
- Fast Sensitivity Analysis method — weight swap, assumption flip, threshold check
- Convergence indicators by stakes level
- Failure modes and countermeasures (frame failures, evaluation failures, process failures)
- Decision Record Template — required output structure
- Worked examples (Adequate, Rigorous) with full detail

**Companion skill:**
- `exploring-claude-repos` — Use first to discover extensions/patterns with signals
