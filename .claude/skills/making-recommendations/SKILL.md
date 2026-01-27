---
name: making-recommendations
description: Use when asked to recommend, suggest an approach, or choose between options. Use when user says "what should I use", "which is better", "recommend", or "help me decide". Use when user says "make a recommendation" during an ongoing conversation. Do not use for trivial decisions where both scope and reversibility are negligible.
---

# Making Recommendations

Make recommendations through structured analysis, not pattern matching.

**Protocol:** [decision-making.framework@1.0.0](../../../docs/frameworks/framework-for-decision-making_v1.0.0.md)

**The problem:** Claude often recommends the first thing that comes to mind — familiar tools, popular options, or whatever fits the pattern. This leads to:
- Premature commitment without iteration
- No signal for when a recommendation is "ready" vs just "made"
- Same shallow process for trivial and high-stakes decisions
- Missing activities: null option, information gaps, sensitivity analysis

**YOU MUST:**
- Follow the decision-making framework for every recommendation
- Calibrate depth to stakes (adequate/rigorous/exhaustive)
- Achieve explicit convergence before claiming "ready"
- Create a persistent Decision Record with traceable reasoning

**Outputs:**
- Decision Record file at `docs/decisions/YYYY-MM-DD-<decision-slug>.md`
- Inline summary: recommendation + key reasoning in chat

**Definition of Done:**
- Decision Record file created and complete for stakes level
- Convergence indicators satisfied
- Recommendation + summary presented in chat

## Triggers

**Direct request:**
- "What should I use for..."
- "Which is better, X or Y?"
- "Recommend a..."
- "Help me decide between..."
- "What's the best way to..."
- "What do you recommend?"

**Mid-conversation pivot:**
- "Just make a recommendation"
- "What would you recommend?" (after discussion)
- "Stop asking and decide"

**Do not use when:**
- User has already decided and wants implementation help
- Question is purely factual ("What is X?")
- Open-ended ideation where option space is unknown — use thoroughness exploration first, then return here when 2+ options identified
- Decision is trivial (both scope AND reversibility are negligible)
  - Scope: affects only a single line/variable/name
  - Reversibility: < 5 minutes to undo
  - **Both must be true to skip** — if either has substance, use the skill

## Process

### Entry Gate

Before any analysis, establish and record:

**1. Entry context check:**
- **Direct request:** Proceed to full Entry Gate
- **Mid-conversation pivot:** First summarize what you understood from prior conversation, confirm with user, then proceed to full Entry Gate

**2. Thoroughness gate:**
- Can you name 2+ plausible options (including "defer/do nothing")?
- Is the remaining uncertainty about preferences/trade-offs (not basic facts)?

If NO to either: **Stop.** Recommend running thoroughness exploration first. Do not proceed until option space is known or user explicitly overrides (see Decision Points: Thoroughness gate blocks).

**3. Stakes calibration:**

| Factor | Adequate | Rigorous | Exhaustive |
|--------|----------|----------|------------|
| Reversibility | Easy to undo | Some undo cost | Hard/irreversible |
| Blast radius | Localized | Moderate | Wide/systemic |
| Cost of error | Low | Medium | High |
| Uncertainty | Low | Moderate | High |
| Time pressure | High (need action) | Moderate | Low / no constraint |

**Rule:** If any two factors land in a higher column, choose that level. To choose a lower level despite this, document why those factors don't apply (e.g., "Blast radius appears wide but is limited to test environment").

**4. Record Entry Gate outputs:**

| Field | Record |
|-------|--------|
| Stakes level | adequate / rigorous / exhaustive |
| Rationale | Why this level matches the situation |
| Time budget | Deadline or "no constraint" |
| Iteration cap | adequate: 2, rigorous: 3, exhaustive: 5 |
| Minimum passes | adequate: 1, rigorous: 2, exhaustive: 3 |
| Evidence bar | What must be true before EXIT is allowed |
| Allowed skips | Which optional activities will be skipped and why |
| Overrides | Any non-default parameters: `[param]: [old]→[new] because [reason]` |
| Escalation trigger | What will cause escalation to user |

### Recalibration

If during execution you discover the decision is more complex than initially assessed (e.g., hidden dependencies surface, stakeholder conflict emerges, option space expands significantly):

1. **Pause** at the current pass boundary
2. **Re-evaluate** using the Stakes Calibration table
3. **If stakes level changes:** Document in iteration log: `Recalibrated from [old level] to [new level] because [trigger]`. Adjust iteration cap and activity depth accordingly.
4. **Continue** from current pass (don't restart)

### Adequate Fast Path (Optional)

For low-stakes decisions where you want a defensible record without a large artifact, use this streamlined approach:

1. **Entry Gate (brief):** Stakes level = adequate, time budget, iteration cap (default 2), allowed skips, escalation trigger
2. **Frame:** Decision statement, 2-5 constraints, 3-6 criteria (weights optional), key stakeholders (if any)
3. **Options:** 3+ options including **Null (do nothing/defer)**
4. **Trade-offs:** 1-2 sentences per option (explicit gains and sacrifices)
5. **Evaluation:** Lightweight scoring or ranking against criteria; call out unknowns
6. **Pressure test:** 2-3 strongest objections to frontrunner and responses (or accepted risks)
7. **Decision:** Choice, trade-offs accepted, confidence, and what would change the decision

**Exit condition:** One pass is OK if frontrunner is stable and trade-offs are explicit; otherwise do a second pass or escalate.

**When to use:** Time pressure is high, reversibility is easy, and blast radius is localized. Skip this path if any of those conditions aren't met.

### Outer Loop: Frame the Decision

Complete before entering the inner loop. Each guards against a specific failure mode.

| Activity | Question | Failure if Skipped |
|----------|----------|-------------------|
| **Identify the choice** | What exactly are we deciding? State as a clear question. | Wrong problem |
| **Surface constraints** | What limits our options? (Technical, budget, time, policy) | Infeasible options |
| **Define criteria** | What does "good" look like? Assign weights (1-5). | Arbitrary selection |
| **Identify stakeholders** | Who's affected? What do they value? | Key perspectives missed |
| **Surface assumptions** | What are we taking for granted? | Hidden assumptions |
| **Check scope** | Is this one decision or several? Split or combine? | Scope confusion |
| **Assess reversibility** | How hard to undo each potential path? | Miscalibrated rigor |
| **Identify dependencies** | Does this block or depend on other decisions? | Blocked cascade |
| **Downstream impact** | What will this decision affect later? | Unintended consequences |

**Depth by level:**
- **Adequate:** O1-O4 required; O5-O9 noted briefly
- **Rigorous:** All required
- **Exhaustive:** All required at deep analysis

**Output:** Frame document in Decision Record with: decision statement, constraints, weighted criteria, stakeholders, assumptions, scope, reversibility, dependencies, downstream impacts.

**Frame converges when:** Frame hasn't changed across an inner loop pass.

### Inner Loop: Evaluate Options

With a stable frame, evaluate alternatives. Each activity guards against a specific failure mode.

**Generate alternatives (I1-I3):**
- List at least 3 viable options (4+ for rigorous, exhaust space for exhaustive)
- **Always include null option:** What if we do nothing or defer?
- Check for hidden options: Hybrids? Orthogonal approaches?

**Assess trade-offs (I4-I5):**
- For each option: What is gained? What is sacrificed?
- Score against weighted criteria (0-5 scale)
- Mark speculative scores with `?` and list in Information Gaps

**Scoring rubric:**
| Score | Meaning |
|-------|---------|
| 0 | Fails criterion |
| 3 | Acceptable |
| 5 | Excellent |

**Weighted total:** `sum(score × weight)`. If option violates a hard constraint, mark **disqualified**.

**Identify gaps (I6):**
- What don't we know that would change the ranking?
- What evidence would we need to increase confidence?

**Check for bias (I7):**

| Bias | Check Question | If Yes |
|------|----------------|--------|
| **Anchoring** | Was the first option I considered still my frontrunner? | Re-score options in random order |
| **Familiarity** | Is the frontrunner something I/we have used before? | Explicitly score unfamiliar option's learning curve vs long-term benefit |
| **Sunk cost** | Have we already invested in one option (time, money, reputation)? | Score as if starting fresh; past investment is not a criterion |
| **Confirmation** | Did I seek evidence FOR my frontrunner more than AGAINST it? | Run I9 (disconfirmation) more aggressively |
| **Availability** | Am I weighting recent experiences or vivid examples too heavily? | Check base rates; ask "how often does this actually happen?" |

**Pressure-test frontrunner (I8-I9) — Adversarial Challenge:**

Apply these lenses with genuine adversarial intent. Objections must cause discomfort if true — softball objections don't count.

| Lens | Question |
|------|----------|
| **Kill it** | What's the strongest argument against this? If it fails, what's the cause? |
| **Pre-mortem** | It's 6 months later, this failed. What went wrong? What warning signs were ignored? |
| **Steelman alternatives** | What would make rejected options better than the frontrunner? |
| **Challenge framing** | What if the premise is wrong? Is this the right question? |
| **Hidden complexity** | Where is complexity being underestimated? |
| **Motivated reasoning** | Am I rationalizing a preferred approach? |

**Check perspectives (I10):**
- How does this look from each stakeholder's view?
- Would any stakeholder strongly object?

**Identify risks (I11-I12):**
- What could go wrong with each option?
- What does this choice enable or preclude next? (Second-order effects)

**Sensitivity analysis (I13):**
- Required for exhaustive; recommended for rigorous; skip allowed for adequate
- Weight swap: If most important criterion's weight changed ±1, does ranking change?
- Assumption flip: Score frontrunner in best/worst plausible case

**Output:** Evaluation record with options, trade-offs, scores, risks, and pressure-tested frontrunner.

### Transition Trees

**After inner loop pass, evaluate:**

```
Is there a clear frontrunner?
├─ NO → Are more options discoverable?
│        ├─ YES → ITERATE inner (focus on I1-I3)
│        └─ NO → BREAK to outer (frame may be wrong)
│
└─ YES → Has it survived pressure-testing?
         ├─ NO → ITERATE inner (focus on I8-I9)
         └─ YES → Are stakeholder perspectives aligned?
                  ├─ NO → ITERATE inner (focus on I10)
                  └─ YES → Convergence criteria met?
                           ├─ NO → ITERATE inner
                           └─ YES → EXIT (decide)

ESCAPE: Stuck after iteration cap with no progress? → ESCALATE to user
```

**After outer loop (inner exits or breaks):**

```
Did inner loop EXIT with a decision?
├─ YES → Did frame remain stable throughout?
│        ├─ YES → EXIT (produce Decision Record)
│        └─ NO → ITERATE outer (frame changed, re-validate)
│
└─ NO (inner BROKE) → Is a better frame apparent?
                      ├─ YES → ITERATE outer (reframe)
                      └─ NO → ESCALATE to user
```

### Convergence Indicators

| Level | Requirements |
|-------|--------------|
| **Adequate** | Frontrunner stable 1 pass, trade-offs stated, criteria defined |
| **Rigorous** | Frontrunner stable 2 passes, objections resolved, all perspectives checked |
| **Exhaustive** | Frontrunner stable 2+ passes, disconfirmation yielded nothing new, sensitivity shows robustness |

### Iteration Log

**YOU MUST** maintain an iteration log showing what changed between passes:

| Pass | Frame Changes | Frontrunner | Key Findings |
|------|---------------|-------------|--------------|
| 1 | (initial) | Option A | ... |
| 2 | None | Option A | Pressure-test survived |

**Convergence justification:** If claiming convergence, explain why — not just "stable" but what evidence supports stability. If nothing changed, state what was tested that could have changed it.

### Exit Gate

Cannot claim "done" until all criteria pass for the chosen level:

| Criterion | Check |
|-----------|-------|
| **Minimum passes met** | adequate: 1, rigorous: 2, exhaustive: 3 |
| **Frame complete** | All required outer loop activities documented |
| **Evaluation complete** | All required inner loop activities documented |
| **Convergence met** | Indicators satisfied for chosen level |
| **Trade-offs explicit** | Decision record includes "Trade-offs Accepted" |
| **Iteration log complete** | Pass-by-pass changes documented with justification |
| **Transition tree passed** | Exited via proper tree path, not bypassed |

### Produce Output

**1. Create Decision Record file:**

Location: `docs/decisions/YYYY-MM-DD-<decision-slug>.md`

Use the Decision Record Template from [decision-making.framework@1.0.0](../../../docs/frameworks/framework-for-decision-making_v1.0.0.md). Include all sections appropriate to stakes level.

**2. Present in chat:**

After creating the file, present inline:

```
**Recommendation:** [Selected option]

**Why:** [2-3 sentence summary of positive case]

**Trade-offs accepted:** [What's being sacrificed]

**Confidence:** High / Medium / Low

**Caveats:** [What would change this]

**Full analysis:** [link to Decision Record file]
```

This summary lets the user see the answer without opening the file, while the file preserves full reasoning.

## Decision Points

**Thoroughness gate blocks:**
- If option space unknown or evidence weak → Recommend thoroughness exploration first
- If user overrides → Document override in Entry Gate, proceed with explicit uncertainty

**Stakes unclear:**
- If factors split across columns → Choose the higher level
- If user disagrees with stakes assessment → User's assessment wins; document rationale

**Mid-conversation pivot:**
- Summarize prior understanding → Confirm with user → Run full Entry Gate
- Prior conversation informs the gate but doesn't skip steps

**All options fail criteria:**
- BREAK to outer loop → Ask: "Can constraints change?"
- If no → ESCALATE: "Given current constraints, no option meets criteria. What should we prioritize?"

**Near-tie (top options within ~10%):**
- Treat as tie → Choose based on declared priority (e.g., safety > speed)
- Or run a small spike targeting the one unknown most likely to break the tie
- Or defer: pick safest reversible step now, decide when evidence arrives

**Pressure to skip ("just decide"):**
- Acknowledge the pressure
- Complete at least minimum passes for stakes level
- Compress output, not process: "Here's the recommendation. Full analysis in the Decision Record."

**Iteration cap reached without convergence:**
- ESCALATE: Present current state to user
- "After [N] passes, [frontrunner] leads but [uncertainty remains]. Do you want to decide now or [gather more information]?"

**Adversarial phase feels perfunctory:**
- If objections don't cause discomfort → They're too weak
- Red flag: "I can't think of strong objections" → Try harder. Steelman the alternatives. What would a critic say?

**Hard deadline forces early termination:**
- Document current state (frontrunner, confidence, open questions) in Decision Record
- Mark confidence as "Low — analysis truncated by deadline"
- Present best available recommendation with caveat: "Given time constraint, recommend [X] but [Y uncertainty remains]"
- Note in Decision Record what would need verification post-decision

## Examples

**Scenario:** "I need to add authentication to my app. What should I use?"

### BAD: Pattern-matching without analysis

"I'd recommend using Auth0 or Firebase Auth. They handle the complexity of authentication for you, support multiple providers (Google, GitHub, etc.), and are well-documented. Auth0 is more feature-rich for enterprise needs, while Firebase is simpler."

**Why it's bad:**
- No Entry Gate — stakes not assessed, no iteration cap set
- No constraints gathered — team size, budget, existing stack unknown
- Only considered third-party services — missed self-hosted and library options
- No null option — didn't consider "defer" or "roll minimal"
- No trade-offs surfaced — vendor lock-in, pricing at scale not mentioned
- No adversarial challenge — what if Auth0 pricing explodes?
- No Decision Record — reasoning not preserved, not reproducible
- Confident tone despite knowing nothing about context

### GOOD: Framework-driven analysis with Decision Record

**Entry Gate:**
- Stakes: Rigorous (moderate blast radius, some undo cost, medium uncertainty)
- Rationale: Auth affects all users (moderate blast radius) and is costly to change later (some undo cost)
- Time budget: This sprint
- Iteration cap: 3
- Minimum passes: 2
- Evidence bar: Confirm approach handles common auth patterns; verify migration path exists
- Allowed skips: Deep sensitivity analysis (will do lightweight version)
- Overrides: None
- Escalation trigger: Team disagrees on security vs simplicity trade-off

**Frame:**
- Decision: "What authentication approach for a B2B SaaS app?"
- Constraints: Small team (2 devs), limited budget, PostgreSQL + Node.js stack
- Criteria: Security (5), Maintainability (4), Cost (4), Time-to-implement (3)
- Stakeholders: Dev team, end users, future maintainers

**Options (including null):**
1. Auth0/Firebase — Managed service
2. Lucia — Lightweight library
3. Keycloak — Self-hosted
4. Roll own — bcrypt + sessions
5. Null: Defer auth, use basic API keys for now

**Evaluation (Pass 1):**
| Option | Security | Maint. | Cost | Time | Total |
|--------|----------|--------|------|------|-------|
| Auth0 | 5 | 4 | 2 | 5 | 58 |
| Lucia | 4 | 4 | 5 | 3 | 56 |
| Keycloak | 5 | 2 | 4 | 2 | 46 |
| Roll own | 2 | 3 | 5 | 1 | 36 |
| Defer | 1 | 5 | 5 | 5 | 48 |

Frontrunner: Auth0

**Adversarial (Pass 1):**
- Kill it: Auth0 pricing scales with MAU — could become painful at 10k+ users
- Pre-mortem: "We hit enterprise customer needing on-prem, Auth0 can't do it"
- Steelman Lucia: Cheaper long-term, fits stack, avoids lock-in

**Evaluation (Pass 2):**
Revised Cost score for Auth0 to 2 (from 3) after pricing analysis. Lucia now leads.

**Adversarial (Pass 2):**
- Kill Lucia: Smaller community, less battle-tested
- Response: Acceptable risk for B2B SaaS; can migrate if needed

**Convergence:** Frontrunner (Lucia) stable across 2 passes. Objections addressed.

**Inline output:**

> **Recommendation:** Lucia
>
> **Why:** Fits Node.js stack, lightweight, gives control without rolling crypto. Budget-friendly for small team.
>
> **Trade-offs accepted:** Smaller community, may need to build SAML if enterprise customers require it.
>
> **Confidence:** Medium-high
>
> **Caveats:** If enterprise customers needing SAML appear early, revisit Auth0.
>
> **Full analysis:** docs/decisions/2024-01-15-auth-approach.md

**Why it's good:**
- Entry Gate calibrated stakes before starting
- Gathered constraints before evaluating
- Generated 5 options including null
- Weighted scoring with explicit criteria
- Two passes with genuine adversarial challenge
- Trade-offs explicit in recommendation
- Decision Record preserves full reasoning

## Anti-Patterns

**Pattern:** Recommending the familiar option
**Why it fails:** "I know React, so use React" isn't analysis. Claude's comfort isn't a criterion for the user's problem.
**Fix:** Generate 3+ alternatives including at least one Claude isn't familiar with.

**Pattern:** Skipping adversarial phase because "it's obviously right"
**Why it fails:** Confidence is when Claude is most likely to miss something. The adversarial phase exists precisely for "obvious" choices.
**Fix:** Pre-mortem and steelman are mandatory, not optional. If objections don't cause discomfort, they're too weak.

**Pattern:** Listing trade-offs but not weighting them
**Why it fails:** "A has pros X, Y. B has pros Z, W." Unweighted comparison doesn't help decide.
**Fix:** Explicitly state which criteria matter more given the constraints. Use weighted scoring.

**Pattern:** Hiding uncertainty behind confident language
**Why it fails:** "Use X" sounds authoritative but may be a guess. User cannot calibrate trust.
**Fix:** State confidence level and what it's based on. "Medium confidence — I've used X but not at this scale."

**Pattern:** Presenting the recommendation as The Answer
**Why it fails:** Context changes. Assumptions may be wrong. User needs to know when to revisit.
**Fix:** Always state assumptions and conditions that would change the recommendation.

**Pattern:** Claiming convergence after one pass
**Why it fails:** One pass means the frontrunner was never challenged. "Stable" requires testing stability.
**Fix:** Minimum passes: adequate 1, rigorous 2, exhaustive 3. Iteration log must show what was tested.

**Pattern:** Softball objections in adversarial phase
**Why it fails:** "A minor concern is..." isn't pressure-testing. The phase becomes theater.
**Fix:** Objections must cause discomfort if true. Steelman alternatives seriously. Ask: "What would make me change my mind?"

**Pattern:** Skipping null option
**Why it fails:** "Do nothing" or "defer" is often valid. Omitting it biases toward action.
**Fix:** Always include null option. Score it against criteria like any other option.

**Pattern:** Treating user pressure as permission to skip steps
**Why it fails:** "Just decide" doesn't change what good analysis requires. Fast wrong recommendations are slower than methodical right ones.
**Fix:** Acknowledge pressure, complete minimum passes, compress output not process.

**Pattern:** Empty iteration log
**Why it fails:** "Pass 1... Pass 2..." without content is checkbox compliance, not iteration.
**Fix:** Each pass must show: what changed, what was tested, why convergence is (or isn't) reached.

## Troubleshooting

**Symptom:** Claude recommends immediately without Entry Gate
**Cause:** Pattern matching to familiar solutions, not following the process
**Next steps:** Return to Entry Gate. Explicitly work through stakes calibration before any analysis.

**Symptom:** Analysis is thorough but no clear recommendation emerges
**Cause:** Criteria not weighted, or avoiding commitment
**Next steps:** Force ranking: "If forced to choose today, which one and why?" Make the trade-off call. If genuinely tied, use near-tie protocol.

**Symptom:** User disagrees with recommendation
**Cause:** Different criteria weights or unstated constraints
**Next steps:** Do not defend — explore. "What criteria matter most to you? What constraints am I missing?" Update frame and re-evaluate.

**Symptom:** Frontrunner keeps changing across passes
**Cause:** Criteria unclear, options too close, or frame unstable
**Next steps:** Check: Are criteria well-defined? Are weights appropriate? If options are genuinely close, treat as near-tie.

**Symptom:** Adversarial phase feels like going through the motions
**Cause:** Not genuinely trying to break the recommendation
**Next steps:** The pre-mortem should produce a plausible failure story. If it doesn't feel uncomfortable, dig harder. Try: "What would a critic of this approach say?"

**Symptom:** Claude skipped steps 2-4 and went straight to recommending
**Cause:** High confidence in the diagnosis ("I know what this is")
**Next steps:** Confidence isn't proof. The process exists because confident guesses are often wrong. Return to Entry Gate.

**Symptom:** Iteration cap reached without convergence
**Cause:** Genuinely difficult decision, or frame is wrong
**Next steps:** ESCALATE. Present current state to user: frontrunner, uncertainty, what would resolve it. Let user decide or provide more information.

**Symptom:** Decision Record file not created
**Cause:** Process completed in chat only
**Next steps:** The file is mandatory. Create Decision Record at `docs/decisions/YYYY-MM-DD-<slug>.md` before claiming done.

**Symptom:** User interrupted demanding immediate action
**Cause:** External pressure (deadline, frustration, authority)
**Next steps:** Acknowledge the pressure. Complete minimum passes for stakes level. Compress output: "Here's the recommendation — full analysis in the Decision Record."

## Verification

After completing a recommendation, verify:

**Entry Gate:**
- [ ] Stakes level assessed and recorded with rationale
- [ ] Time budget established
- [ ] Thoroughness gate passed (or override documented)
- [ ] Iteration cap and minimum passes set
- [ ] Evidence bar defined
- [ ] Allowed skips documented (if any)
- [ ] Escalation trigger identified

**Frame:**
- [ ] Decision statement is a clear question
- [ ] Constraints identified
- [ ] Criteria defined with weights
- [ ] Stakeholders identified

**Evaluation:**
- [ ] 3+ options generated (including null option)
- [ ] Trade-offs explicit for each option
- [ ] Scoring against weighted criteria
- [ ] Information gaps identified

**Adversarial:**
- [ ] Frontrunner pressure-tested with genuine objections
- [ ] Objections would cause discomfort if true
- [ ] Alternatives steelmanned

**Convergence:**
- [ ] Minimum passes completed for stakes level
- [ ] Iteration log shows what changed each pass
- [ ] Convergence justification explains why stable (not just claims it)

**Output:**
- [ ] Decision Record file created at `docs/decisions/YYYY-MM-DD-<slug>.md`
- [ ] Inline summary presented in chat with recommendation, trade-offs, confidence, caveats

**Quick self-test:** If the recommendation were wrong, would the user have enough information to understand why and what to try instead?

## Extension Points

**Framework handoffs:**
- If option space unknown → Hand off to [thoroughness.framework](../../../docs/frameworks/framework-for-thoroughness_v1.0.0.md) first
- Return condition: When thoroughness identifies 2+ viable options with evidence, resume this skill at Entry Gate
- Outputs from thoroughness (dimensions, findings, gaps) feed directly into this skill's Entry Gate

**Domain-specific criteria:**
- Skills can extend the criteria table with domain-specific dimensions
- Example: Security skill might add "Attack surface", "Compliance requirements"

**Custom Decision Record locations:**
- Default: `docs/decisions/YYYY-MM-DD-<slug>.md`
- Projects can override via CLAUDE.md if a different convention exists
