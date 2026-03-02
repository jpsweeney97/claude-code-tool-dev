# Reviewing-Designs Skill Redesign

**Date:** 2026-03-02
**Status:** Approved (brainstorming complete)
**Scope:** Step 1 of 2-step rollout. Adds early adversarial gate + bridge table + dialogue-first interaction. Does not add Codex integration (Step 2).

## Problem

The reviewing-designs skill is a 470-line compliance checker that verifies designs against source documents using 19 dimensions, Yield% convergence, and evidence levels. It works — D4 produced more P0s than adversarial lenses in both completed reviews, and the brainstorming-skills review found 10 P0s in 4 passes.

But it's incomplete and mis-framed. Four concerns it should address but doesn't:

1. **Intent alignment** — Does the design solve the right problem, not just a problem?
2. **Blind spot surfacing** — An independent perspective that challenges assumptions the designer can't see
3. **Conversational sharpening** — Value is in back-and-forth dialogue, not compliance reports
4. **Optimality** — Is this the best design for its purpose, or did we settle on the first workable approach?

The mechanism (autonomous solo analysis → formal report) doesn't match what's needed (adversarial dialogue → sharper thinking).

## Validation

Three-stage validation before committing to a direction:

### Stage 1: Codex Dialogue (collaborative, 7/14 turns, converged)

**Key finding:** The mechanism is mis-aimed, not broken. The dimensional loop catches implementation-failure issues effectively. The gap is missing intent/optimality objectives, not a broken engine.

**Direction:** C-core + B-experience hybrid — keep structural guarantees, change interaction to dialogue-first. None of the three initial approaches (A: kill framework, B: Codex wrapper, C: reframe labels) alone is sufficient.

**Thread:** `019cb06f-09c4-73a1-84b0-8d20332e6070`

### Stage 2: Historical Comparison

Tested against 4 cases from the audit record (ticket plugin review, context metrics review, hardening plan review, brainstorming-skills review).

| Proposed change | Helped in | Didn't help in |
|----------------|-----------|----------------|
| Early adversarial gate | Cases 1, 2, 4 — catches framing, assumptions, patterns before dimensional pass | Case 3 — false positives need code verification |
| Bridge table | Cases 1, 2 — connects individual findings to common roots | Cases 3, 4 — less relevant when issues are independent |
| Dimensional pass (existing) | All 4 cases — essential for cross-section consistency and enumeration | — |

**Strongest evidence:** P1-13 from the ticket plugin review ("no 'single skill + template' alternative in rejection table") is an intent/optimality failure that survived 5 prior review rounds. The early gate's Q2 would have caught it before any refinement.

### Stage 3: Prototype Test

Ran AHG-5 against the ticket plugin design (717 lines) and compared with the actual Round 6 review (8 P0, 14 P1, 10 P2).

| Metric | Result |
|--------|--------|
| P0s caught by early gate (as hypotheses) | 5 of 8 |
| P0s only catchable by dimensional pass | 3 of 8 (cross-section consistency: D12/D15/D16) |
| Framing issues caught before Round 6 | Both (H1→P1-11, H2→P1-13) |
| Bridge table connections validated | H3 correctly linked to 3 D4 instances via one pattern |

All three stages converge: keep the dimensional engine, add the early gate + bridge, change the interaction.

## Design

### Process Flow

```
Entry Gate (unchanged)
    ↓
AHG-5 Early Gate (NEW)
    ↓
Bridge Table (NEW)
    ↓                    [delta card #1 in chat]
DISCOVER → EXPLORE → VERIFY → REFINE (unchanged)
    ↓                    [delta card #2 in chat]
Adversarial Pass A1-A9 (unchanged)
    ↓                    [delta card #3 in chat]
Exit Gate (unchanged + bridge completion check)
    ↓
Artifact (unchanged format, assembled from delta cards)
```

### 1. Early Adversarial Gate (AHG-5)

Runs after Entry Gate, before DISCOVER. Five concrete questions that surface framing problems, load-bearing assumptions, and systemic patterns.

| # | Question | What it catches |
|---|---------|----------------|
| Q1 | What problem is this solving, and what's the strongest argument it's the wrong problem? | Intent misalignment, over-scoping |
| Q2 | What alternatives were considered, and what would make a rejected alternative better than this? | Anchoring, pre-narrowed framing, motivated reasoning |
| Q3 | What would make this fail in implementation? Name specific mechanisms, not categories. | Systematically underspecified behavior, load-bearing gaps |
| Q4 | Where is complexity underestimated? What looks simple but isn't? | Hidden state spaces, edge case surfaces, interaction effects |
| Q5 | What single assumption, if wrong, would invalidate the whole design? | Load-bearing assumptions, fragile dependencies |

**Output:** 3-5 hypotheses (H1, H2, ...), each a testable claim about a potential design weakness.

**Stakes gating:**

| Stakes | Gate |
|--------|------|
| Adequate | AHG-lite: Q1, Q3, Q5 only. Minimum 2 hypotheses. |
| Rigorous | Full AHG-5: all 5 questions. Minimum 3 hypotheses. |
| Exhaustive | Full AHG-5: all 5 questions. Minimum 4 hypotheses. |

No skip path — a skip recreates the N/A rationalization anti-pattern.

**Hard fail rules:**

- Each question produces a hypothesis OR an explicit "no finding" with one-sentence justification
- Q3 must name specific mechanisms, not categories
- Q5 must identify one assumption and state what breaks if it's wrong
- All 5 questions producing "no finding" → flag: "Early gate produced zero hypotheses. Verify genuine engagement before proceeding."

### 2. Bridge Table

Carries early-gate hypotheses into the dimensional loop. Prevents "generate-then-forget."

**Format:**

| ID | Hypothesis | Target Dimensions | Status | Disposition |
|----|-----------|-------------------|--------|-------------|
| H1-H3 | From early gate | D-codes and/or A-codes | open → tested/disconfirmed | Finding IDs or disconfirmation evidence |

| ID | Alternative | Status | Disposition |
|----|------------|--------|-------------|
| ALT1-ALT2 | From early gate Q2 | open → evaluated | Dominance check result |

**Lifecycle:**

- Rows added after early gate with status `open`
- Status → `tested` when target dimension is checked in EXPLORE or adversarial pass
- Disposition records what was found: confirmed (with finding ID), disconfirmed (with evidence)
- At Exit Gate: no `open` rows allowed

**Size constraint:** Maximum 3 hypothesis rows + 2 alternative rows. Overflow → "deferred hypotheses" footnote (not bridge-tracked).

**Alternatives dominance check:**

- "Does this alternative strictly dominate the design on the user's stated criteria?"
- Clearly not dominant → "not dominant — {reason}" → done
- Possibly dominant → "unresolved — escalate to /making-recommendations" → done

Reviewing-designs identifies the question; making-recommendations answers it.

### 3. Dialogue-First Interaction

Three delta cards in chat at natural breakpoints. The conversation is the primary output; the artifact is a compiled record.

**Checkpoints:**

| # | When | Card contents | User can... |
|---|------|--------------|-------------|
| 1 | After early gate | Hypotheses + alternatives. "Do any surprise you? Anything I'm missing?" | Add context, redirect, confirm |
| 2 | After loop convergence | Bridge dispositions + new findings. Running P0/P1/P2 totals. | Redirect attention, ask to dig deeper |
| 3 | After adversarial pass | Final bridge table + adversarial findings. Overall assessment. | — |

Checkpoints are invitations, not gates. If the user says nothing, the review proceeds.

**Delta card format (example — checkpoint 2):**

```
**Checkpoint 2: Dimensional loop converged** (3 passes, Yield% 9%)

Bridge dispositions:
- H3 (decision-points underspecified) → CONFIRMED: 3 P0 instances (classify threshold, preflight state, create autonomy stage)
- H5 (session_id load-bearing) → CONFIRMED: P0 — delivery mechanism is fragile

New findings beyond hypotheses:
- P0-4: Error codes vs machine states mismatch [D12]
- P0-6: Example ticket missing contract_version [D15]

Running totals: P0: 6 | P1: 10 | P2: 4

Anything you want me to dig deeper on before the adversarial pass?
```

**Output contract change:**

| Before | After |
|--------|-------|
| Full report in artifact only; chat gets brief summary | Delta cards in chat at each checkpoint; artifact compiles all cards + full coverage tracker |

Artifact format unchanged — same sections, same structure. Delivery order changes.

### 4. What Stays the Same

| Component | Status |
|-----------|--------|
| Dimension catalog (D1-D19) | Unchanged |
| Yield% convergence (formula, thresholds, iteration cap) | Unchanged |
| Evidence levels (E0-E3) and confidence-capping rule | Unchanged |
| Cell Schema (Status/Priority/Evidence/Confidence/Artifacts/Notes) | Unchanged |
| Stakes calibration (5-factor table, default Rigorous) | Unchanged |
| Adversarial pass (A1-A9, mandatory after loop) | Unchanged |
| Entry Gate | Unchanged |
| Exit Gate | +1 criterion: bridge table complete |
| Priority downgrade rules | Unchanged |
| Stable entity IDs for Yield% | Unchanged |
| Disconfirmation requirements | Unchanged |
| Dimension applicability rules (D12-D19 mandatory) | Unchanged |
| Artifact location (`docs/audits/...`) | Unchanged |

### 5. What's Deferred (Step 2)

| Item | Why deferred |
|------|-------------|
| Codex dialogue checkpoint | Single cross-model consultation at rigorous+ stakes, between dimensional loop and adversarial pass. Needs: insertion point, integration pattern, stakes gating, fallback. Validate Step 1 first. |
| Yield% supplementary quality gate | Codex dialogue proposed a "disposition quality gate" alongside Yield%. Needs specification. |
| Measurement plan | How to measure whether the early gate improved quality vs. reviewer variance. Needs implementation experience. |
| AHG-5 question refinement | The 5 questions are validated against one design (ticket plugin). May need adjustment after more use. |

## Implementation Notes

**Estimated SKILL.md impact:** +60-80 lines (early gate ~25, bridge table ~20, delta cards ~20, Exit Gate criterion +1). Current: 470 lines. Projected: 530-550 lines (within 500-line soft target with reference overflow).

**Reference file changes:** None expected. The early gate and bridge table are SKILL.md content, not reference material.

**What to change in SKILL.md:**
1. Insert AHG-5 section between Entry Gate and "The Review Loop"
2. Insert Bridge Table section after AHG-5
3. Modify Outputs section: replace artifact-first contract with dialogue-first delta cards
4. Add bridge completion criterion to Exit Gate
5. Add delta card format to Outputs
6. Update Process flow diagram
7. Update Definition of Done checklist

**What NOT to change:** Dimensions, Yield%, evidence levels, Cell Schema, adversarial pass, Entry Gate structure, disconfirmation rules, anti-patterns, troubleshooting, examples reference (though examples.md should be updated to show the new flow after SKILL.md is validated).
