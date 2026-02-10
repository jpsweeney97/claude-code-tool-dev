# Codex Delta: Integration Design for `making-recommendations`

**Date:** 2026-02-10
**Method:** `codex-dialogue` subagent (collaborative posture, 4 turns, converged)
**Thread ID present:** yes
**Participants:** Claude Opus 4.6 + OpenAI Codex
**Related:** `docs/audits/2026-02-10-codex-review-making-recommendations.md`, `docs/decisions/2026-02-09-evaluate-making-recommendations-skill.md`

---

## Summary

Design for integrating Codex consultation into the `making-recommendations` decision-making skill. The core concept: **Codex Delta** — a single adversarial injection placed inside the existing pressure-testing phase (I8/I9), triggered when a stable frontrunner first emerges.

## Design

### Placement

Inside the adversarial phase, at the first pass where a stable frontrunner appears. Not after scoring (avoids "math cosplay" debates), not as a final sign-off (too late to change anything).

A frontrunner is "stable enough" when:
- A shortlist of 2-4 options exists
- The frontrunner would survive at least one reasonable criterion reweight
- A cheapest disconfirming test can be named for it

### Mechanism: Two-Phase Reveal

One call to `codex-dialogue`, structured in two phases within a single consultation:

**Phase 1 (no frontrunner revealed):**
- Provide criteria, constraints, and options labeled A/B/C
- Ask Codex to scan for framing flaws (criteria laundering, missing stakeholders, decision/implementation conflation)
- List distinct failure modes per option
- Propose cheapest disconfirming tests

**Phase 2 (reveal frontrunner):**
- Reveal the current frontrunner with minimal rationale
- Switch to adversarial posture
- Ask for kill-it argument, pre-mortem, and "what would change your mind?" tests

This solves the tension between avoiding confirmation bias (Phase 1) and enabling targeted pressure-testing (Phase 2) without requiring two separate consultations.

### Stakes Policy

| Level | Codex Default | Behavior |
|-------|---------------|----------|
| Adequate | Absent | No prompt unless a trigger fires (high irreversibility + high consequence) or user explicitly requests |
| Rigorous | Default-on, skippable | Prompt: "Run Codex Delta check? (recommended) [Y/n]" |
| Exhaustive | Mandatory | Auto-run if available; if unavailable, emit fallback message and run local adversarial lenses |

### Call Budget

- Default: 1 Codex consultation per decision
- Hard cap: 2 (second call allowed only for escalation triggers)
- Escalation triggers: material reframing, option-set change, blocker objection that prevents convergence
- Turn budgets within the consultation: rigorous 3-4 turns, exhaustive 5-8 turns

### Output: "Codex Delta" Block

Same schema at two resolutions (truncation rules, not two formats).

**Inline (Decision Capsule) resolution:**

```
Codex Delta (adversarial, N turns)
- Material challenges: 1-3 bullets (each falsifiable/testable)
- Cheapest disconfirming test: 1 bullet
- Decision updates: 0-2 bullets (what changed in criteria/assumptions/options)
- Disposition: accepted/rejected/deferred + one-line why
```

**File (Decision Record) resolution** adds:
- Session metadata (provider, posture sequence, turns, date)
- Status tags per challenge: resolved / mitigated / accepted risk / invalid / deferred
- Evidence links per challenge
- Transcript: exhaustive-only, otherwise "available on request"

### Skill File Structure

3-5 lines in core SKILL.md (placed immediately after the adversarial phase description):

> If `stakes >= rigorous` and Codex MCP is available, run Codex Delta once at the first pass where a stable frontrunner emerges (single consult, two-phase reveal; posture switches to adversarial after revealing the frontrunner).

> Use the Codex Delta output to add/refresh material objections and required cheapest disconfirming test(s); objections must receive an explicit disposition before convergence can be claimed.

> If Codex MCP is unavailable or skipped, run the local adversarial lenses and continue; do not block completion solely on Codex availability.

> Full invocation spec + output format: see Extension Point "Codex Delta".

Full details (invocation gate, two-phase reveal script, briefing template, output schema, fallback behavior, override knobs, examples, troubleshooting) go in a supporting extension doc.

### Convergence Rule Update

Material objections from Codex Delta must be dispositioned (resolved / mitigated / accepted risk / invalid / deferred) before convergence can be claimed. Consistent with existing convergence indicator "objections resolved" — makes Codex-sourced objections subject to the same rule.

### Fallback Behavior

When Codex is unavailable, local adversarial lenses produce the same Codex Delta block structure. The protocol shape is identical whether Codex is available or not — no forking into "Codex version" and "non-Codex version."

## Novel Ideas (Emerged from Dialogue)

These concepts were not in either side's initial thinking and emerged from the back-and-forth:

1. **Two-phase reveal** — solved the bias vs. targeting tension. Neither fully hiding nor fully showing the frontrunner; do both sequentially within one call.
2. **Fallback produces same schema** — local adversarial lenses output the same block shape, preventing protocol forking.
3. **Objections Ledger as implementation detail** — reuses the existing iteration log pattern rather than introducing new vocabulary. Sharpened adversarial slice with status tags lives in the extension doc, not in the core protocol.

## Open Questions

1. **Rigorous second consult policy:** Should the optional second call be exhaustive-only, or allowed for rigorous with escalation triggers? Stricter = simpler and cheaper; looser = handles edge cases.

2. **Stable-frontrunner gate specifics:** Minimum signals are sketched but not formalized as a checklist. The extension doc needs to make this concrete.

3. **Transcript handling for promoted rigorous decisions:** Currently "no transcript for capsule, exhaustive-only for record." What about rigorous decisions promoted to a file?

4. **Availability detection UX:** What "Codex MCP is available" concretely means, and what message to show when it's not.

5. **Anchoring via option description:** Briefing template should enforce symmetric option descriptions (same fields, same approximate length, neutral labels) to prevent asymmetric framing from biasing Codex.

6. **Disposition evidence bar:** What minimum evidence is required per stakes level before "resolved" is accepted? Without this, disposition theater is likely.

## Next Steps

1. Write the 3-5 core SKILL.md lines (when `making-recommendations` refactor happens)
2. Write the extension doc with full invocation spec, briefing template, and output schema
3. Resolve the open questions above during implementation

## Areas of Agreement (Both Sides)

- One consultation per decision, not per-pass
- Adversarial placement, not final review
- Two-phase reveal solves the bias/targeting tension
- Same schema at two resolutions via truncation
- Extension doc rather than core bloat
- Fallback produces same delta schema
