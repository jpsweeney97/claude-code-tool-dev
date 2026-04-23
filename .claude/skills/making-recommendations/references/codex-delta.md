# Codex Delta: Adversarial Check via codex-collaboration

Extension point for the `making-recommendations` skill. Single adversarial consultation using `codex.consult`, placed inside the I8-I9 pressure-testing phase.

**Design origin:** `docs/audits/2026-02-10-codex-delta-integration-design.md`

## Invocation Gate

Run Codex Delta when ALL conditions are met:

1. **Stakes >= rigorous** (adequate decisions skip unless an override trigger fires)
2. **Codex MCP is available** (see [Availability Detection](#availability-detection))
3. **Stable frontrunner exists** (see [Stable-Frontrunner Gate](#stable-frontrunner-gate))
4. **First pass where frontrunner emerges** (do not re-run on subsequent passes)

### Override Triggers (Adequate Stakes)

At adequate stakes, Codex Delta is absent by default. Run it if BOTH:
- Decision has high irreversibility (hard to undo)
- Decision has high consequence (wide blast radius or significant cost of error)

### Stakes Policy

| Level | Default | Behavior |
|-------|---------|----------|
| Adequate | Absent | No prompt unless override trigger fires or user explicitly requests |
| Rigorous | Default-on, skippable | Prompt: "Run Codex Delta check? (recommended) [Y/n]" |
| Exhaustive | Mandatory | Auto-run; if unavailable, emit fallback message and run local adversarial lenses |

## Stable-Frontrunner Gate

A frontrunner is "stable enough" for Codex Delta when all three conditions hold:

- [ ] **Shortlist exists:** 2-4 options scored against weighted criteria
- [ ] **Survives reweight:** Frontrunner still leads if highest-weight criterion changes by ±1
- [ ] **Cheapest disconfirming test named:** At least one concrete, actionable test that could disprove the frontrunner's advantage

If any condition fails, continue local adversarial lenses. Return to this gate on the next pass if conditions change.

## Structured Adversarial Prompt

One call to `codex.consult` with `profile="adversarial-challenge"`. The prompt merges analysis and adversarial questions in a single structured message. Bias mitigation is preserved by placing neutral option descriptions and analysis questions before the frontrunner reveal.

### Prompt Template

```
## Context
Decision: [decision statement from frame]
Stakes: [level]
Constraints: [numbered list]

## Criteria
[Table: criterion, weight, definition]

## Options (neutral labels — analyze before reading the frontrunner reveal below)
Option A: [name]
- Description: [1-2 sentences]
- Key trade-off: [gains X, sacrifices Y]
- Score: [total against weighted criteria]

Option B: [name]
- Description: [1-2 sentences]
- Key trade-off: [gains X, sacrifices Y]
- Score: [total against weighted criteria]

[repeat for each option]

## Analysis Questions
1. Scan for framing flaws: criteria laundering, missing stakeholders, decision/implementation conflation.
2. List distinct failure modes per option (not shared failure modes — those indicate a framing problem).
3. Propose the cheapest disconfirming test for each option.

## Frontrunner Reveal
Current frontrunner: Option [X] ([name])
Rationale (brief): [2-3 sentences — why it leads]

## Adversarial Questions
Argue against the frontrunner:
1. What is the strongest kill-it argument?
2. Pre-mortem: it's 6 months later, this failed. What went wrong?
3. What specific, testable conditions would change your mind about this choice?
```

### Invocation

Call `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult` with:

| Parameter | Value |
|-----------|-------|
| `repo_root` | Output of `git rev-parse --show-toplevel` |
| `objective` | The structured prompt above |
| `profile` | `adversarial-challenge` |

## Output: Codex Delta Block

Produce one block at two resolutions (truncation rules, not two formats).

### Inline Resolution (Decision Capsule)

Include in the chat summary and Decision Record inline:

```
**Codex Delta** (adversarial, 1 turn)
- Material challenges: [1-3 bullets, each falsifiable/testable]
- Cheapest disconfirming test: [1 bullet]
- Decision updates: [0-2 bullets — what changed in criteria/assumptions/options]
- Disposition: [accepted/rejected/deferred] — [one-line why]
```

### File Resolution (Decision Record)

Add to the Decision Record file (after the Pressure Test section):

```
### Codex Delta

**Session:** codex.consult | adversarial-challenge | 1 turn | YYYY-MM-DD

**Material Challenges:**

| # | Challenge | Status | Evidence |
|---|-----------|--------|----------|
| 1 | [challenge text] | resolved / mitigated / accepted risk / invalid / deferred | [link or description] |
| 2 | ... | ... | ... |

**Cheapest Disconfirming Test:** [description]

**Decision Updates:** [what changed in criteria, assumptions, or options as a result]
```

### Status Tags

Each material challenge receives one status:

| Status | Meaning | Required Evidence |
|--------|---------|-------------------|
| resolved | Challenge addressed, no longer applies | Rigorous: specific evidence cited. Exhaustive: evidence + disconfirmation attempted |
| mitigated | Risk reduced to acceptable level | Mitigation described with residual risk stated |
| accepted risk | Risk acknowledged, proceeding anyway | What would change the calculus |
| invalid | Challenge based on incorrect premise | Premise identified and refuted |
| deferred | Cannot resolve now, tracked for later | Trigger condition for revisiting |

## Call Budget

- **Default:** 1 `codex.consult` call per decision
- **Hard cap:** 2 (second call exhaustive-only)
- **Second call triggers:** Material reframing (criteria or constraints changed), option-set change (new option added or option disqualified), blocker objection preventing convergence
- At rigorous stakes, escalation triggers upgrade to a second local adversarial pass, not a second Codex consultation

## Convergence Rule

Material objections from Codex Delta must be dispositioned before convergence can be claimed. This applies the existing "objections resolved" convergence indicator to Codex-sourced objections — no special rule, same standard.

An objection is dispositioned when it has a status tag (see Status Tags above) with required evidence for the stakes level. "Resolved" without evidence is not dispositioned — it is assertion.

## Fallback Behavior

When Codex MCP is unavailable:

1. Emit: "Codex MCP unavailable — continuing with local adversarial lenses."
2. Run local adversarial lenses (I8-I9 from SKILL.md)
3. Produce the same Codex Delta block structure with `**Session:** local adversarial lenses` instead of codex.consult metadata
4. Status tags and disposition rules still apply

The protocol shape is identical whether Codex is available or not. No forking into "Codex version" and "non-Codex version."

## Availability Detection

"Codex MCP is available" means:
- MCP tool `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult` is listed as available

Check at the start of the adversarial phase. If unavailable, fall back immediately — do not retry or wait.

## Anti-Patterns

| Pattern | Why It Fails | Fix |
|---------|--------------|-----|
| Running Codex Delta after scoring is final | Too late to change anything — becomes rubber-stamp | Run at first stable frontrunner, before convergence |
| Asymmetric option descriptions | Longer/richer description for frontrunner biases Codex | Same fields, approximate length, neutral labels |
| Dispositioned as "resolved" without evidence | Theater — objection dismissed without work | Evidence bar by stakes level (see Status Tags) |
| Running two Codex consultations at rigorous | Expensive and rarely needed | Second call exhaustive-only; rigorous gets a second local pass |
| Blocking decision on Codex unavailability | Codex is a supplement, not a gate | Fall back to local lenses; same output structure |

## Troubleshooting

### Codex MCP tools not found

**Cause:** Codex MCP server not running or not configured.
**Fix:** Check `mcp__plugin_codex-collaboration_codex-collaboration__codex.consult` availability. If not present, fall back to local adversarial lenses.

### Codex returns shallow or generic response

**Cause:** Briefing too vague, or option descriptions too short for meaningful analysis.
**Fix:** Ensure briefing includes: concrete criteria with weights, specific constraints, and option descriptions with trade-offs. Vague in = vague out.

### All objections dispositioned as "invalid"

**Cause:** Likely disposition theater — dismissing without engaging.
**Fix:** At least one material challenge should survive as "mitigated" or "accepted risk." If all are genuinely invalid, document why the adversarial check found no real issues (this is rare and worth noting).
