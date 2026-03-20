# Reviewing-Designs Skill Redesign

**Date:** 2026-03-02
**Status:** Approved (brainstorming complete)
**Scope:** Step 1 of 2-step rollout. Adds early adversarial gate + bridge table + dialogue-first interaction. Does not add Codex integration (Step 2).

## Problem

The reviewing-designs skill is a 470-line compliance checker that verifies designs against source documents using 19 dimensions, Yield% convergence, and evidence levels. It works — D4 produced more P0s by count than the adversarial lenses in both completed reviews (ticket plugin: 3 D4 P0s vs. 2 adversarial-escalated P0s; context metrics: 1 D4 P0), and the brainstorming-skills review found 10 P0s in 4 passes.

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

**Output:** Hypotheses (H1, H2, ...), each a testable claim about a potential design weakness. Count is deterministic per stakes level.

**Stakes gating:**

| Stakes | Questions | Hypothesis count | Bridge H-rows |
|--------|-----------|-----------------|---------------|
| Adequate | AHG-lite: Q1, Q3, Q5 only | Exactly 2 | H1-H2 + ALT1-ALT2 = 4 rows |
| Rigorous | Full AHG-5: all 5 questions | Exactly 3 | H1-H3 + ALT1-ALT2 = 5 rows |
| Exhaustive | Full AHG-5: all 5 questions | Exactly 4 | H1-H4 + ALT1-ALT2 = 6 rows |

No skip path — a skip recreates the N/A rationalization anti-pattern.

**Hard fail rules** (scoped to each *run* question, not all 5):

- Each run question produces a hypothesis OR an explicit "no finding" with one-sentence justification
- Q3 must name specific mechanisms, not categories
- Q5 must identify one assumption and state what breaks if it's wrong
- All run questions producing "no finding" → flag: "Early gate produced zero hypotheses. Verify genuine engagement before proceeding."

**Overflow:** If more hypotheses emerge than the stakes-level count, rank by impact × plausibility × testability. Top N become bridge rows; remainder go in a "deferred hypotheses" footnote (not bridge-tracked, but preserved for reference).

### 2. Bridge Table

Carries early-gate hypotheses into the dimensional loop. Prevents "generate-then-forget."

**Hypothesis row schema:**

| ID | Hypothesis | Target Dimensions | Anchor | Status | Disposition |
|----|-----------|-------------------|--------|--------|-------------|
| H1-H*N* | From early gate (*N* = stakes-level count: 2/3/4) | D-codes and/or A-codes | Design location (section, line range, or structural element) | open/tested/disconfirmed/withdrawn | Finding IDs, disconfirmation evidence, or withdrawal rationale |

**Alternative row schema:**

| ID | Alternative | Anchor | Status | Disposition |
|----|------------|--------|--------|-------------|
| ALT1-ALT2 | From early gate Q2 | Design location | open/evaluated/withdrawn | Dominance check result or withdrawal rationale |

**Anchor field:** Two-level evidence chain. At creation (early gate): design-level citation (e.g., "Section 3.2, decision rules"). At resolution (EXPLORE/VERIFY): code-level citation added to disposition (e.g., "confirmed — D4 found 3 missing thresholds at lines 301, 505, 309"). AHG-5 hypotheses are framing-level claims — they don't need code citations at creation time.

**Status values:**

| Status | Meaning | Required disposition |
|--------|---------|---------------------|
| `open` | Not yet checked | — |
| `tested` | Target dimension checked, hypothesis confirmed | Finding ID + evidence |
| `disconfirmed` | Target dimension checked, hypothesis not supported | Counter-evidence + rationale |
| `evaluated` | ALT row: dominance check completed | Check result + rationale |
| `withdrawn` | Hypothesis no longer applicable | Rationale citing why premise no longer applies |

**Disposition invariant:** Every non-`open` row must include: (1) disposition text, (2) evidence or rationale, (3) audit entry (when/checkpoint + why + prior status). Rows without evidence-backed dispositions create false convergence — the invariant makes this structurally impossible.

**Lifecycle:**

- Rows added after early gate with status `open`
- Status transitions via bridge operations (see below)
- At Exit Gate: no `open` rows allowed

**Bridge operations** (available at checkpoints):

| Operation | When | Effect |
|-----------|------|--------|
| ADD | Checkpoints 1-2 | New hypothesis from user input or dimensional findings |
| REVISE | Checkpoints 1-2 | Update hypothesis text or retarget dimensions (audit: record old → new) |
| WITHDRAW | Checkpoints 1-3 | Remove hypothesis with rationale (e.g., N/A target, premise invalidated) |
| REOPEN | Checkpoint 3 only | Reopen a tested/disconfirmed row if new evidence contradicts disposition. Triggers another loop pass. |

Checkpoint 1: full operations (ADD/REVISE/WITHDRAW) — user can correct hypotheses based on context the reviewer missed.
Checkpoint 2: full operations — dimensional findings may invalidate or strengthen hypotheses.
Checkpoint 3: REOPEN only — if adversarial pass contradicts a prior disposition, the row reopens and forces another pass.

**N/A dimension targeting:** If a hypothesis targets a dimension that gets marked N/A, retarget once to the nearest applicable dimension. If no applicable dimension exists, WITHDRAW with rationale citing why the hypothesis premise no longer applies.

**Size constraint:** Determined by stakes level (see AHG-5 stakes gating table). Overflow hypotheses ranked by impact × plausibility × testability → deferred hypotheses footnote (not bridge-tracked).

**Alternatives dominance check** (at checkpoint 2, optional re-check at checkpoint 3):

- "Does this alternative strictly dominate the design on the user's stated criteria?"
- Clearly not dominant → "not dominant — {reason}" → `evaluated`
- Possibly dominant → "unresolved — escalate to /making-recommendations" → `evaluated`
- Clearly dominant → P0 finding: "Alternative ALT-N dominates current design on {criteria}" → `evaluated`

Reviewing-designs identifies the question; making-recommendations answers it.

### 3. Dialogue-First Interaction

Three delta cards in chat at natural breakpoints. The conversation is the primary output; the artifact is a compiled record.

**Checkpoints:**

| # | When | Card contents | User can... |
|---|------|--------------|-------------|
| 1 | After early gate | Hypotheses + alternatives + bridge table. | Add context, ADD/REVISE/WITHDRAW bridge rows, confirm |
| 2 | After loop convergence | Bridge dispositions + new findings beyond hypotheses. Running P0/P1/P2 totals. ALT dominance check results. | Redirect attention, ADD/REVISE/WITHDRAW bridge rows, ask to dig deeper |
| 3 | After adversarial pass | Final bridge table + adversarial findings (bridge-mapped and NET-NEW). Overall assessment. | Informational closeout. REOPEN only if adversarial findings contradict a disposition. |

Checkpoints are invitations, not gates. If the user says nothing, the review proceeds.

**Adversarial pass / AHG-5 overlap:** Adversarial lenses A1 (Assumption Hunting), A6 (Steelman Alternatives), A7 (Challenge the Framing), and A8 (Hidden Complexity) overlap with AHG-5 questions. To prevent duplicate findings without restricting adversarial discovery:
- Adversarial pass evaluates mapped bridge rows first (e.g., A1 checks H5 before generating new assumption findings)
- Findings that extend or confirm bridge hypotheses link to the existing H-code
- Genuinely new findings (not traceable to any bridge row) are marked **NET-NEW** with a one-sentence justification of why the early gate didn't catch them

**Delta card schema** (shared across all 3 checkpoints):

| Field | Content |
|-------|---------|
| **Checkpoint** | Which checkpoint (1/2/3) + context (e.g., "Dimensional loop converged, 3 passes, Yield% 9%") |
| **What changed** | Summary of work since last card |
| **Bridge updates** | Status changes on H-rows and ALT-rows with dispositions |
| **Net-new findings** | Findings not traceable to bridge hypotheses, with dimension links |
| **Current totals** | Running P0/P1/P2 counts |
| **Reviewer ask** | Specific question or "proceed?" (checkpoint 3: informational, no ask) |

**Example (checkpoint 2):**

```
**Checkpoint 2: Dimensional loop converged** (3 passes, Yield% 9%)

What changed: EXPLORE checked D4-D19 across 3 passes. Yield% dropped from 30% (pass 2) to 9% (pass 3).

Bridge updates:
- H3 (decision-points underspecified) → TESTED/CONFIRMED: 3 P0 instances (classify threshold, preflight state, create autonomy stage) [D4]
- H5 (session_id load-bearing) → TESTED/CONFIRMED: P0 — delivery mechanism fragile [D9, Anchor: §4.3 session_id delivery]
- ALT1 (Architecture F) → EVALUATED: not dominant — lacks autonomy enforcement for agent-initiated creates

Net-new findings:
- P0-4: Error codes vs machine states mismatch [D12]
- P0-6: Example ticket missing contract_version [D15]

Current totals: P0: 6 | P1: 10 | P2: 4

Anything to dig deeper on before the adversarial pass?
```

**Artifact assembly:** The artifact (`docs/audits/...`) compiles all 3 delta cards in checkpoint order, followed by the full coverage tracker and iteration log. The delta cards become the Findings section of the artifact. This is deterministic — no additional synthesis step needed.

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
| Exit Gate | +1 criterion: bridge table complete (no `open` rows; all non-open rows satisfy disposition invariant) |
| Priority downgrade rules | Unchanged |
| Stable entity IDs for Yield% | Unchanged. H-codes are scaffolding — not Yield-tracked entities. Only D-codes and F-codes enter E_prev/E_cur. Bridge completion is an independent exit criterion. |
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

**Estimated SKILL.md impact:** +95-130 lines (early gate ~25, bridge table ~45 (schema + lifecycle + operations + invariant), delta cards ~25 (schema + assembly), adversarial overlap ~10, Exit Gate ~5). Current: 470 lines. Projected: 565-600 lines. Option: move bridge operations and delta card schema to a reference doc to hold SKILL.md near 530-550 lines.

**Reference file changes:** Likely needed — bridge operations detail and delta card schema may overflow SKILL.md's soft line target. Candidate: `references/bridge-and-checkpoints.md`.

**What to change in SKILL.md:**
1. Insert AHG-5 section between Entry Gate and "The Review Loop"
2. Insert Bridge Table section after AHG-5
3. Modify Outputs section: replace artifact-first contract with dialogue-first delta cards
4. Add bridge completion criterion to Exit Gate
5. Add delta card format to Outputs
6. Update Process flow diagram
7. Update Definition of Done checklist

**What NOT to change:** Dimensions, Yield%, evidence levels, Cell Schema, adversarial pass, Entry Gate structure, disconfirmation rules, anti-patterns, troubleshooting, examples reference (though examples.md should be updated to show the new flow after SKILL.md is validated).
