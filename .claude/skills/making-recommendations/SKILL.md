---
name: making-recommendations
description: Use when asked to make a recommendation, suggest an approach, or choose between options. Use when the user says "what should I use", "which is better", "recommend", or "help me decide". Do not use for simple factual questions or when user has already decided.
---

# Making Recommendations

Make recommendations through rigorous analysis, not pattern matching.

**The problem:** Claude often recommends the first thing that comes to mind — familiar tools, popular options, or whatever fits the pattern. This leads to shallow recommendations that miss alternatives, ignore second-order effects, and don't survive scrutiny.

**This skill ensures:** Every recommendation goes through structured analysis and adversarial challenge before being presented.

## Triggers

- "What should I use for..."
- "Which is better, X or Y?"
- "Recommend a..."
- "Help me decide between..."
- "What's the best way to..."
- "Make a recommendation"
- "What do you recommend?"
- `/recommend`

**Do not use when:**

- User has already decided and wants implementation help
- Question is purely factual ("What is X?")
- User explicitly wants a quick answer without analysis

## Process

### Phase 1: Understand Before Recommending

Before any recommendation, establish:

- **The actual need** — What problem is being solved? (Not what solution is being asked for)
- **Constraints** — Time, budget, team skills, existing systems, preferences
- **Success criteria** — What would make this recommendation "good"?
- **Stakes** — How reversible is this decision? What's the cost of being wrong?

If any of these are unclear, ask. Do not assume.

### Phase 2: Generate Alternatives

List at least 3 viable options:

- The obvious choice (what comes to mind first)
- An unconventional option (what would someone who disagrees suggest?)
- A simpler option (what's the minimum that would work?)

Do not filter yet. Capture all reasonable approaches before evaluating.

### Phase 3: Evaluate Against Criteria

For each option, assess:

| Dimension            | Questions                                                  |
| -------------------- | ---------------------------------------------------------- |
| Fit                  | Does it solve the actual problem? Meet the constraints?    |
| Tradeoffs            | What is gained? What is sacrificed?                        |
| Second-order effects | What downstream impacts? What does this make harder later? |
| Uncertainty          | How confident is Claude? What is unknown?                  |

### Phase 4: Adversarial Challenge

Apply each lens with genuine adversarial intent. Try to break the emerging recommendation.

**Kill the Recommendation**

- What's the strongest argument against this approach?
- If this fails, what will be the cause?
- Would Claude bet on this recommendation?

**Pre-mortem**

- It's 6 months later. This recommendation led to failure.
- What went wrong? What warning signs were ignored?

**Steelman Alternatives**

- Take rejected options seriously: What would make them better than the recommendation?
- Is the rejection justified, or dismissed too quickly?

**Challenge the Framing**

- What if the premise is wrong?
- Is this the right question to be answering?

**Hidden Complexity**

- Where is complexity being underestimated?
- What looks simple but isn't?

**Motivated Reasoning Check**

- Is Claude rationalizing a preferred approach?
- What would the recommendation be if forced to pick something completely different?

### Phase 5: Recommend

State the recommendation with:

- **The choice** — Clear, unambiguous
- **Why this** — Positive case against the criteria
- **Why not others** — What alternatives lacked (having steelmanned them)
- **Tradeoffs accepted** — What is being sacrificed and why it's acceptable
- **Assumptions** — What, if wrong, would change the recommendation
- **Confidence level** — How certain, and why

## Decision Points

**Not enough alternatives:**

- If only 1-2 options come to mind → Stop and actively seek more. "What would someone who disagrees suggest?"
- If all options seem equivalent → Something is missing. Dig deeper on criteria or constraints.

**Uncertainty about the domain:**

- If Claude is not confident in the domain → State so explicitly. "I'm less familiar with X, so this recommendation has higher uncertainty."
- If key facts cannot be verified → State them as assumptions. Do not present guesses as knowledge.

**Adversarial phase finds problems:**

- If pre-mortem reveals serious risks → Either mitigate in the recommendation or reconsider alternatives.
- If steelmanning makes an alternative look better → Follow the evidence. Change the recommendation.

**User wants a quick answer:**

- Give the recommendation BUT still surface the top tradeoff and uncertainty.
- Never skip adversarial thinking; compress the output, not the process.

**High stakes, low confidence:**

- Recommend gathering more information before deciding.
- "I'd recommend [X] with current information, but given the stakes, consider [ways to reduce uncertainty] before committing."

**Conflicting criteria:**

- Make the tradeoff explicit: "Option A wins on X and Y but loses on Z. Given the constraints, X and Y matter more because..."
- Do not hide the conflict in a clean-sounding recommendation.

## Examples

**Scenario:** "I need to add authentication to my app. What should I use?"

### BAD: Pattern-matching without analysis

"I'd recommend using Auth0 or Firebase Auth. They handle the complexity of authentication for you, support multiple providers (Google, GitHub, etc.), and are well-documented. Auth0 is more feature-rich for enterprise needs, while Firebase is simpler and integrates well if you're already using Firebase."

**Why it's bad:**

- No understanding of constraints (team size, budget, existing stack)
- Only considered third-party services — missed self-hosted and library options
- No tradeoffs surfaced
- No adversarial challenge — what if Auth0 pricing explodes at scale?
- Confident tone despite knowing nothing about the context

### GOOD: Structured analysis with adversarial challenge

**Understanding:**

- Need: User authentication for a B2B SaaS app
- Constraints: Small team (2 devs), limited budget, already using PostgreSQL and Node.js
- Success criteria: Secure, maintainable by small team, cost-effective
- Stakes: Medium — can migrate later but painful

**Alternatives:**

1. Auth0/Firebase — Managed auth service
2. Roll your own — bcrypt + sessions/JWT
3. Open source self-hosted — Keycloak, Authentik
4. Lightweight library — Passport.js, Lucia

**Evaluation:**

| Option        | Fit                     | Tradeoffs                         | Second-order                        |
| ------------- | ----------------------- | --------------------------------- | ----------------------------------- |
| Auth0         | Good features           | $$$ at scale, vendor lock-in      | Pricing surprises as you grow       |
| Roll your own | Full control            | Security risk, maintenance burden | Every edge case is your problem     |
| Keycloak      | Feature-rich            | Complex to operate, Java stack    | Operational overhead for small team |
| Lucia         | Lightweight, fits stack | Less batteries-included           | May need to build features later    |

**Adversarial challenge:**

_Kill it:_ Lucia is newer, smaller community. If edge cases are hit, less help available.

_Pre-mortem:_ "Lucia was chosen, then SAML was needed for an enterprise customer. Lucia doesn't support it. A separate solution had to be bolted on, creating two auth systems."

_Steelman Auth0:_ The cost scales with success. If pricing becomes a problem, that's a good problem. Time saved on auth = time spent on product.

**Recommendation:** Lucia

- **Why:** Fits the stack (Node.js), lightweight, gives control without rolling crypto. Budget-friendly.
- **Why not Auth0:** Cost at scale is real concern for bootstrapped B2B; lock-in complicates future options.
- **Why not roll your own:** Security risk too high for 2-person team.
- **Why not Keycloak:** Operational complexity exceeds team capacity.
- **Tradeoff accepted:** Smaller community, may need to build features (SAML) if enterprise customers require them.
- **Assumption:** If enterprise customers needing SAML/OIDC federation appear, revisit Auth0 or add Keycloak alongside.
- **Confidence:** Medium-high. Claude is familiar with these options but hasn't used Lucia in production.

**Why it's good:**

- Established context before recommending
- Generated diverse alternatives (managed, DIY, self-hosted, library)
- Evaluated against criteria with tradeoffs explicit
- Applied adversarial thinking — tried to kill the recommendation, steelmanned alternatives
- Stated assumptions and confidence level

## Anti-Patterns

**Pattern:** Recommending the familiar option
**Why it fails:** "I know React, so use React" isn't analysis. Claude's comfort isn't a criterion for the user's problem.
**Fix:** Generate 3+ alternatives including at least one Claude isn't familiar with.

**Pattern:** Skipping adversarial phase because "it's obviously right"
**Why it fails:** Confidence is when Claude is most likely to miss something. The adversarial phase exists precisely for "obvious" choices.
**Fix:** Pre-mortem and steelman are mandatory, not optional.

**Pattern:** Listing tradeoffs but not weighting them
**Why it fails:** "A has pros X, Y. B has pros Z, W." Unweighted comparison doesn't help decide.
**Fix:** Explicitly state which criteria matter more given the constraints.

**Pattern:** Hiding uncertainty behind confident language
**Why it fails:** "Use X" sounds authoritative but may be a guess. User cannot calibrate trust.
**Fix:** State confidence level and what it's based on. "Medium confidence — I've used X but not at this scale."

**Pattern:** Presenting the recommendation as The Answer
**Why it fails:** Context changes. Assumptions may be wrong. User needs to know when to revisit.
**Fix:** Always state assumptions and conditions that would change the recommendation.

## Troubleshooting

**Symptom:** Claude recommends immediately without analysis
**Cause:** Pattern matching to familiar solutions, not actually analyzing
**Fix:** Return to Phase 1. Explicitly work through each phase before recommending.

**Symptom:** Analysis is thorough but no clear recommendation emerges
**Cause:** Criteria not weighted, or avoiding commitment
**Fix:** Force ranking: "If forced to choose today, which one and why?" Make the tradeoff call.

**Symptom:** User disagrees with recommendation
**Cause:** Different criteria weights or unstated constraints
**Fix:** Do not defend — explore. "What criteria matter most to you? What constraints am I missing?"

**Symptom:** Recommendation seems wrong in hindsight
**Cause:** Missing criteria, wrong assumptions, or overlooked alternatives
**Fix:** Post-mortem: Which criterion was misjudged? What option wasn't considered? Feed back into future recommendations.

**Symptom:** Adversarial phase feels like going through the motions
**Cause:** Not genuinely trying to break the recommendation
**Fix:** The pre-mortem should produce a plausible failure story. If it doesn't feel uncomfortable, dig harder.

## Verification

After completing a recommendation, verify:

- [ ] Context established — constraints, success criteria, and stakes identified before recommending
- [ ] Alternatives explored — at least 3 options considered, including an unconventional one
- [ ] Adversarial applied — recommendation challenged with pre-mortem, steelmanning, and framing checks
- [ ] Tradeoffs explicit — recommendation states what is being sacrificed
- [ ] Assumptions surfaced — assumptions listed with conditions that would change the recommendation
- [ ] Confidence calibrated — uncertainty acknowledged where it exists

**Quick self-test:** If the recommendation were wrong, would the user have enough information to understand why and what to try instead?
