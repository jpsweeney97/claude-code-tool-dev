# Codex Review: `making-recommendations` Skill

**Date:** 2026-02-10
**Reviewer:** OpenAI Codex (via `/codex` skill)
**Primary agent:** Claude Opus 4.6
**Thread ID:** `019c4668-954d-72a2-bbb9-8507aeedad64`
**File reviewed:** `.claude/skills/making-recommendations/SKILL.md` (581 lines)
**Related:** `docs/decisions/2026-02-09-evaluate-making-recommendations-skill.md`

---

## Round 1: Initial Review

### Structural Quality

**Strengths:**
- Clear intent ("structured analysis, not pattern matching") and crisp invocation/exclusion criteria
- Outer loop vs inner loop separation is a good mental model
- Transition trees, convergence indicators, and iteration cap + escalation trigger are "unusually good guardrails"

**Issues:**
- Too much "primary law" in one file — normative protocol, operational checklist, examples, troubleshooting, verification, and extension points all mixed together
- Redundancy (null option and convergence repeated across sections) increases chance of partial compliance
- Decision Points section referenced more than operationalized

**Suggestion:** Shrink to 150–250 line "Quickstart + Executable Protocol" core. Move examples/anti-patterns/troubleshooting into linked docs. Add inline copy-pastable Decision Record template.

### Process Design

**Sound elements:**
- Entry Gate + stakes calibration with explicit rule ("if any two factors land higher…")
- Outer-loop requirements directly address most common recommendation failures
- Mandatory adversarial pressure-testing

**Unaddressed failure modes:**
- **False precision from scoring** — LLMs turn weighted scoring into "math cosplay" and feel locked-in by totals. Mitigation: "scores are relative shape, narrative wins if they disagree."
- **Criteria laundering** — criteria can be defined to pre-ordain the preferred option
- **Option padding** — "at least 3 options" can produce filler. Require each option to be "meaningfully different along at least one top-2 criterion."
- **Mis-framing not strongly testable** — no requirement for alternate framing statement

**LLM reliability:** Number of required micro-steps is high. Under time pressure, model will either comply cosmetically or skip to recommendation and backfill. Strongest boost: hard formatting constraints (fixed headings, required table columns).

### Practical Concerns

- 581 lines too long for *consistent execution* (fidelity, not context)
- **Mandatory persistent Decision Record for every recommendation is the adoption killer**
- Adequate fast path still feels ceremonial
- Suggested: make adequate = inline only (no file), persistent DR for rigorous/exhaustive

### Missing Anti-Patterns

1. Decision/implementation conflation (no "next step to validate cheaply")
2. No revisit trigger / review date
3. Proxy-metric trap (criteria easy to score but not what user values)
4. Iteration log theater (multiple passes that don't actually change anything)
5. Non-viable null option (listed but not described)
6. Local optimum lock-in (ignoring hybrid/sequencing options)
7. Stakeholder tokenism (listed but don't affect ranking)

### Overall Assessment

**Verdict: Keep, but refactor.** Four paths offered:

1. **Split + tighten (recommended)** — executable core + appendices, relax DR for adequate
2. Keep as-is — max rigor, low adoption
3. Replace with simpler "Rec Card" — max adoption, lower auditability
4. Two-stage workflow — fast inline answer, promote to record on demand

---

## Claude's Assessment of Round 1

**Agreed:**
- Length problem is about fidelity, not context — compliance theater irony
- Persistent DR for adequate is the adoption killer
- False precision from scoring is most actionable new failure mode

**Pushed back:**
- Alternate framing statement: more ceremony, transition tree BREAK path already handles this
- "One criterion frontrunner isn't best at": gameable (trivial criterion to lose), bias check I7 already covers
- Rec Card replacement (path 3): loses distinctive value — adversarial phase and convergence indicators are the point

**Proposed direction: hybrid of paths 1 + 4:**
1. Adequate = inline only (no file, chat summary format)
2. Rigorous/Exhaustive = persistent Decision Record
3. "Promote" mechanism — escalate adequate to file with one additional pass
4. Split the file — core protocol (~200 lines) in SKILL.md, rest in supporting files

---

## Round 2: Reaction to Proposed Direction

Codex endorsed the direction: "fixes the two biggest practical blockers (fidelity + adoption) without throwing away the distinctive bits (adversarial + convergence)."

### New Failure Modes from Two-Stage Approach

| Risk | Description |
|------|-------------|
| **Promotion debt** | Important decisions never get promoted because the moment passes |
| **Retrospective rationalization** | Promotion after implementation becomes justification, not evaluation |
| **Context loss** | Inline summary omits constraints/assumptions, making later promotion archaeology |
| **Under-calibration** | Users stick with "adequate inline" even when stakes cross into rigorous |
| **Traceability gaps** | Some decisions in `docs/decisions/`, others only in chat, no index |

### Proposed Mitigations

- **Automatic promotion triggers** — if any two stakes factors are rigorous+, promotion is required (not optional)
- **Decision Capsule** — make adequate output promotion-ready by design: decision statement, constraints, top criteria, chosen option, biggest risk, revisit trigger. Promotion becomes copy/paste + one pass, not archaeology.
- **Revisit trigger even for adequate** — date or event that forces re-examination

### What Stays in Core (~200 lines)

**Keep in core** (behavior-forcing at decision time):
- When to invoke / don't invoke + trivial decision rule
- Entry Gate (stakes calibration, iteration cap, escalation trigger)
- Adequate inline protocol: 3+ meaningfully different options incl null, lightweight criteria + trade-offs, adversarial mini-pass (2-3 objections), scores optional ("relative shape, narrative wins"), revisit trigger required
- Rigorous/Exhaustive protocol: outer/inner loop checklist (compressed), adversarial lenses, convergence indicators, iteration log, sensitivity as brief MUST for exhaustive
- Promote mechanism: when/how, what extra work happens

**Move out** (supporting files in skill directory):
- Long-form examples, anti-pattern catalog, troubleshooting, extended verification checklists, framework theory, scoring rubric expansions, deep bias tables, sensitivity walkthroughs

### Pushback Responses

Codex accepted all three pushbacks with refinements:

- **Framing:** Instead of alternate framing requirement, add "Decision statement still correct? Y/N" once per pass — lighter, still catches misframing
- **Criteria laundering:** Swap to "criteria must be outcome-based and not mention any option/tool by name; if they do, rewrite" — harder to game than "one criterion frontrunner loses"
- **Rec Card:** Accepted rejection but wants to steal one ingredient: a required **"cheapest validation step"** (spike/pilot/measurement) to prevent decision/implementation conflation

### Open Question

Should promotion be user-driven only (A) or auto-promote on triggers (B)?

---

## Claude's Assessment of Round 2

**Key insight:** The Decision Capsule concept is the most valuable new idea. It makes inline adequate output promotion-ready by design — the two-stage approach becomes "one process at two resolutions" instead of two separate processes.

**Agreed:**
- Decision Capsule solves context loss, promotion debt, and traceability in one move
- "Criteria must not mention options by name" is better than "one criterion the frontrunner loses"
- "Cheapest validation step" worth adding — fights decision/implementation conflation
- Revisit trigger even for adequate — low cost, high value

**On the open question:** Lean **B with user confirmation** — auto-detect when triggers trip, flag it ("Stakes have risen — this should be promoted to a Decision Record"), user confirms or overrides. Preserves adoption while catching under-calibration. Matches project autonomy model (ask first for scope-expanding actions).

---

## Agreed Next Steps

Refactor the skill based on this direction:
1. Core SKILL.md (~200 lines): executable protocol with Decision Capsule as adequate output format
2. Supporting files: examples, anti-patterns, troubleshooting, verification checklists
3. Two-tier artifact policy: inline for adequate, persistent file for rigorous/exhaustive
4. Promote mechanism with auto-detection + user confirmation
5. New guardrails: "scores are relative shape," outcome-based criteria rule, cheapest validation step, revisit trigger
