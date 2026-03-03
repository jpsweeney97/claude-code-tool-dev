# Bridge & Checkpoints Reference

Supporting reference for the [reviewing-designs](../SKILL.md) skill.

## How to Use This File

- **During AHG-5:** Overflow ranking detail is here (core questions and hard-fail rules are in SKILL.md)
- **During checkpoints:** Delta card schema and example are here
- **During loop:** Bridge operations for modifying rows at checkpoints are here
- **Core process lives in SKILL.md** — this file is operational reference only

---

## Bridge Operations

Available at checkpoints to modify bridge rows.

| Operation | Available at | Effect |
|-----------|-------------|--------|
| ADD | Checkpoints 1-2 | New hypothesis from user input or dimensional findings |
| REVISE | Checkpoints 1-2 | Update hypothesis text or retarget dimensions. Audit: record old → new |
| WITHDRAW | Checkpoints 1-3 | Remove hypothesis with rationale (e.g., N/A target, premise invalidated) |
| REOPEN | Checkpoint 3 only | Reopen a tested/disconfirmed row if new evidence contradicts disposition. Triggers another loop pass |

**Checkpoint scoping:**

- Checkpoint 1: full operations (ADD/REVISE/WITHDRAW) — user can correct hypotheses based on context the reviewer missed
- Checkpoint 2: full operations — dimensional findings may invalidate or strengthen hypotheses
- Checkpoint 3: REOPEN only — if adversarial pass contradicts a prior disposition, the row reopens and forces another pass

**REOPEN semantics:**

- A REOPEN triggers exactly one reconciliation loop pass
- During that pass, new D/F entities from dimensional checks on the reopened hypothesis enter Yield% scope normally
- If the reconciliation pass triggers normal REFINE continuation conditions (new dimensions, Yield% above threshold), the loop continues per standard REFINE rules
- If the iteration cap has been reached, REOPEN overrides for exactly one reconciliation pass; after that pass, the cap reasserts
- Reopened rows requiring adversarial re-validation: only relevant lenses re-check the specific reopened rows, not a full 9-lens re-pass

## Alternative Row Schema

| Field | Content |
|-------|---------|
| ID | ALT1-ALT2 |
| Alternative | From early gate Q2 |
| Anchor | Design location |
| Status | open / evaluated / withdrawn |
| Disposition | Dominance check result or withdrawal rationale |

## Alternatives Dominance Check

Runs at checkpoint 2, optional re-check at checkpoint 3.

Decision tree:

- Clearly not dominant → "not dominant — {reason}" → `evaluated`
- Possibly dominant → "unresolved — escalate to /making-recommendations" → `evaluated`
- Clearly dominant → P0 finding: "Alternative ALT-N dominates current design on {criteria}" → `evaluated`

Reviewing-designs identifies the question; making-recommendations answers it.

**ALT → F-code rule:** When an ALT row moves to `evaluated` with "unresolved — escalate," create a corresponding F-code finding (e.g., F-ALT1) in the coverage tracker at P1 priority. This ensures the unresolved decision risk enters Yield% scope and the artifact's Decidable/Undecidable section.

**Integration rules:**

- Dominance check runs only on concrete alternatives; placeholder rows (CONSTRAINED, NONE IDENTIFIED) → `withdrawn` with rationale
- Deferred-ALT promotion must happen by checkpoint 2 via REVISE (not ADD at checkpoint 3)
- A6 (Steelman Alternatives) fallback: constrained case tests constraint validity; unconstrained case treats as framing challenge
- Q2 constrained zero-alt counts as explicit Q2 outcome (not silent skip)

## Anchor Field

Two-level evidence chain:

- **At creation (early gate):** design-level citation (e.g., "Section 3.2, decision rules")
- **At resolution (EXPLORE/VERIFY):** code-level citation added to disposition (e.g., "confirmed — D4 found 3 missing thresholds at lines 301, 505, 309")

AHG-5 hypotheses are framing-level claims — they don't need code citations at creation time.

## N/A Dimension Targeting

If a hypothesis targets a dimension that gets marked N/A:

1. Retarget once to the nearest applicable dimension
2. If no applicable dimension exists, WITHDRAW with rationale citing why the hypothesis premise no longer applies

## Status-Specific Disposition Requirements

Override the generic disposition invariant ("evidence or rationale") with status-specific evidence requirements:

| Status | Required evidence | Minimum quality |
|--------|------------------|----------------|
| `tested` | Finding ID(s) from target dimension checks | At least one finding at E1+ (single source with citation) |
| `disconfirmed` | Counter-evidence from target dimension checks | Specific citation showing hypothesis does not hold |
| `evaluated` (ALT) | Dominance check result | Decision tree outcome with rationale |
| `withdrawn` | Rationale | One-sentence justification citing invalidated premise |

These take precedence over the generic invariant. A formulaic `tested` disposition backed only by an E0 assertion (no citation) does not satisfy this requirement.

**Terminology note:** "Disconfirmation" means different things in the framework and bridge:

- **Framework:** Obligation to attempt disconfirmation of P0 findings (MUST requirement — applied to D-codes and F-codes)
- **Bridge:** Status meaning "hypothesis not supported by evidence" (applied to H-codes)

These are independent obligations. A `disconfirmed` H-row does not satisfy the framework's P0 disconfirmation MUST.

## Overflow Ranking

When more hypotheses emerge than the stakes-level count allows:

- **Rank by:** impact × plausibility × testability
- **Top N:** become bridge H-rows (N = stakes-level count)
- **Remainder:** go in "deferred hypotheses" footnote (not bridge-tracked, preserved for reference)

**Promotion-on-slot-open:** When a bridge slot opens via WITHDRAW, promote the highest-ranked deferred hypothesis into the vacated slot via REVISE at the current checkpoint. This prevents high-signal deferred items from being permanently lost. Promotion must happen by checkpoint 2 — no promotions at checkpoint 3 (only REOPEN is available).

## ALT Overflow

When Q2 surfaces more or fewer than 2 alternatives:

| Case | ALT1 | ALT2 | Action |
|------|------|------|--------|
| 0 alternatives, constrained space | CONSTRAINED:\<source\> | N/A | No framing flag. Gate: external source + single viable now |
| 0 alternatives, unconstrained | NONE IDENTIFIED | N/A | Flag framing risk |
| 1 alternative | \<alternative\> | NONE IDENTIFIED | — |
| 3+ alternatives | Top by impact × plausibility × testability | Second by ranking | Remainder in "deferred ALT" list |

## Delta Card Schema

Shared across all 3 checkpoints:

| Field | Content |
|-------|---------|
| **Checkpoint** | Which checkpoint (1/2/3) + context (e.g., "Dimensional loop converged, 3 passes, Yield% 9%") |
| **What changed** | Summary of work since last card |
| **Bridge updates** | Status changes on H-rows and ALT-rows with dispositions |
| **Net-new findings** | Findings not traceable to bridge hypotheses, with dimension links |
| **Current totals** | Running P0/P1/P2 counts |
| **Reviewer ask** | Specific question or "proceed?" (checkpoint 3: informational, no ask) |

### Example (Checkpoint 2)

```
**Checkpoint 2: Dimensional loop converged** (3 passes, Yield% 9%)

What changed: EXPLORE checked D4-D19 across 3 passes. Yield% dropped from 30% (pass 2) to 9% (pass 3).

Bridge updates:
- H3 (decision-points underspecified) → TESTED: 3 P0 instances (classify threshold, preflight state, create autonomy stage) [D4]
- H5 (session_id load-bearing) → TESTED: P0 — delivery mechanism fragile [D9, Anchor: §4.3 session_id delivery]
- ALT1 (Architecture F) → EVALUATED: not dominant — lacks autonomy enforcement for agent-initiated creates

Net-new findings:
- P0-4: Error codes vs machine states mismatch [D12]
- P0-6: Example ticket missing contract_version [D15]

Current totals: P0: 6 | P1: 10 | P2: 4

Anything to dig deeper on before the adversarial pass?
```

### Artifact Assembly

The artifact (`docs/audits/...`) compiles all 3 delta cards in checkpoint order, followed by the full coverage tracker and iteration log. The delta cards become the Findings section. This is deterministic — no additional synthesis step needed.
