# T-04 T2 Decision: Synthetic Claim Provenance And Unresolved Closure Accounting

**Date:** 2026-04-02
**Context:** T2 from [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Related gate:** G2 in [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
**Related risks:** A, K in [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md)
**Status:** `Accepted (design)` artifact for T2.

## 1. Decision

Adopt claim-level provenance plus exact-text unresolved diffing for the
benchmark-first candidate loop.

1. The normalized local claim shape gains `claim_source` with two values:
   `extracted` and `minimum_fallback`.
2. If turn extraction yields zero distinct claims, the normalizer creates
   exactly one fallback claim from the turn `position` with:
   `status="new"` and `claim_source="minimum_fallback"`.
3. Counter computation treats only `claim_source="extracted"` claims as
   countable for `new_claims`, `revised`, and `conceded`.
4. `unresolved_closed` is derived before counter computation by exact-text
   set diff between the prior turn's unresolved list and the current turn's
   unresolved list.
5. T2 does not solve referential continuity. T3 will define how
   `minimum_fallback` claims are excluded from continuity matching and how
   paraphrase limits are handled for real claims.

This keeps the non-empty-claims invariant while preventing minimum-claim
fallbacks from inflating `effective_delta` or `compute_quality`.

## 2. Why This Direction

Two source constraints force this design.

First, fallback claims cannot be corrected after the fact by quality logic.
`compute_quality()` is counter-derived and marks any `new_claims > 0` turn as
substantive, while `compute_effective_delta()` marks any `new_claims > 0` turn
as advancing
([ledger.py](../../packages/plugins/cross-model/context-injection/context_injection/ledger.py)).
If a minimum-claim fallback stays indistinguishable from a real `new` claim,
the candidate loop mechanically overstates progress.

Second, `unresolved_closed` is already an explicit caller-owned input in the
reference pipeline rather than a field inferred inside `compute_counters()`
([ledger.py](../../packages/plugins/cross-model/context-injection/context_injection/ledger.py),
[pipeline.py](../../packages/plugins/cross-model/context-injection/context_injection/pipeline.py)).
The current pipeline computes it by exact-text diff against only the prior
turn's unresolved list, not against cumulative history. T2 should preserve that
deterministic boundary instead of inventing a looser closure heuristic.

## 3. State Shape

The benchmark-first candidate's normalized local claim record is:

```text
ClaimRecord {
  text: str
  status: "new" | "reinforced" | "revised" | "conceded"
  turn: int
  claim_source: "extracted" | "minimum_fallback"
}
```

Notes:

- `status` remains the semantic relationship to prior dialogue state.
  `claim_source` is orthogonal provenance.
- A fallback claim remains `status="new"` because it is a structural claim
  placeholder, not a new semantic status class.
- Normalized local state must materialize `claim_source` explicitly before any
  counter or continuity logic runs. Do not hide fallback provenance in
  turn-level tags or prose-only notes.

The per-turn derived value is:

```text
unresolved_closed: int
```

computed from the previous turn's unresolved list versus the current turn's
unresolved list.

## 4. Owning Layers

| Layer | Ownership |
|---|---|
| 1 | Extract semantic data and emit raw claims/unresolved items from the Codex turn |
| 1-2 | If no raw claims exist, create the single `minimum_fallback` claim from `position` |
| 2 | Normalize every claim to an explicit `claim_source` and derive `unresolved_closed` from prior state |
| 3 | Compute counters, `quality`, and `effective_delta` from normalized claims plus `unresolved_closed` |

This split keeps the design inside the existing "compute, don't assess"
boundary. Extraction identifies what happened. Normalization makes provenance
and closure state explicit. Counter logic stays mechanical.

## 5. Deterministic Algorithm Boundary

### 5.1 Claim provenance normalization

```text
raw_claims = extracted claims from the current turn

if raw_claims is empty:
    normalized_claims = [
        {
            text: position,
            status: "new",
            turn: current_turn,
            claim_source: "minimum_fallback",
        }
    ]
else:
    normalized_claims = [
        {claim..., claim_source: "extracted"} for claim in raw_claims
    ]
```

Expected invariant:

- Valid turns should not intentionally mix `extracted` and `minimum_fallback`
  claims. The fallback exists only to satisfy the minimum-one-claim invariant
  when zero real claims were extracted.

Defensive rule:

- If malformed mixed input still appears, counter computation must ignore
  `minimum_fallback` claims rather than letting them inflate the derived state.
  Validation behavior can hard-reject or soft-fail later, but computation must
  not count them as real movement.

### 5.2 `unresolved_closed` derivation

```text
if prior turn exists:
    prior_unresolved = set(previous_turn.unresolved.text)
    current_unresolved = set(current_turn.unresolved.text)
    unresolved_closed = len(prior_unresolved - current_unresolved)
else:
    unresolved_closed = 0
```

Important boundaries:

- Compare only to the immediately prior turn.
- Use exact-text set semantics, matching the current pipeline contract.
- A wording change in an unresolved item is not treated as semantic continuity
  work in T2. If the text changes, the deterministic result is "old one
  closed, new one opened."

### 5.3 Counter computation

```text
countable_claims = [
    claim for claim in normalized_claims
    if claim.claim_source == "extracted"
]

new_claims = count(status == "new" for claim in countable_claims)
revised = count(status == "revised" for claim in countable_claims)
conceded = count(status == "conceded" for claim in countable_claims)
```

Then reuse the existing mechanical rules:

- `quality` is substantive iff any of `new_claims`, `revised`, `conceded`, or
  `unresolved_closed` is non-zero.
- `effective_delta` is advancing iff `new_claims > 0`, shifting iff
  `revised > 0 or conceded > 0`, else static.

This means:

- an all-fallback turn becomes `SHALLOW` + `STATIC`
- a closure-only turn becomes `SUBSTANTIVE` + `STATIC`
- a real-new-claim turn remains `SUBSTANTIVE` + `ADVANCING`

## 6. Rejected Alternatives

### A. Overload `status` instead of adding provenance

Rejected because `status` describes semantic relationship across turns, while
fallback provenance describes why the claim exists at all. A synthetic-minimum
claim is not a fifth semantic relationship.

### B. Track fallback only at the turn level

Rejected because T3 needs claim-level exclusion for continuity matching, and
turn-level flags are too coarse if malformed mixed input ever appears.

### C. Correct inflated state after counters are computed

Rejected because post-hoc quality or delta downgrades would duplicate the
counter logic and break the "compute, don't assess" rule. The exclusion must
happen at the counting boundary, not in a later interpretive patch.

### D. Leave `unresolved_closed` at zero unless later evidence proves closure

Rejected because the reference pipeline already treats closure as a deterministic
previous-vs-current unresolved diff. Leaving it at zero permanently would make
closure-only turns invisible and degrade ledger trustworthiness for no gain.

## 7. Verification Path

The T2 implementation should be considered correct only if it has tests for:

1. All-fallback turn: one `minimum_fallback` claim produces
   `new_claims=0`, `quality=SHALLOW`, `effective_delta=STATIC`.
2. Real-new-claim turn: one `extracted` `new` claim produces
   `new_claims=1`, `quality=SUBSTANTIVE`, `effective_delta=ADVANCING`.
3. Closure-only turn: no countable claims plus `unresolved_closed > 0`
   produces `quality=SUBSTANTIVE` and `effective_delta=STATIC`.
4. First-turn closure behavior: `unresolved_closed=0`.
5. Exact-text closure diff: dropped unresolved items increment
   `unresolved_closed`; unchanged unresolved items do not.
6. Malformed mixed input: any `minimum_fallback` claim is excluded from
   counters even if a bad caller also included real extracted claims.

## 8. What T2 Intentionally Leaves To T3

T2 resolves provenance and closure accounting only. It does not decide:

- how real claims maintain deterministic continuity across paraphrase pressure
- whether the continuity mechanism is exact-text, IDs, or a deterministic hybrid
- whether unresolved items need any normalization beyond exact text

T3 should treat `claim_source` as a settled input and specify only how
continuity excludes `minimum_fallback` claims and handles real claims.
