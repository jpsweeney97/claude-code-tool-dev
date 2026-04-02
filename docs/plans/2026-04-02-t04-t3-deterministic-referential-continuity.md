# T-04 T3 Decision: Deterministic Referential Continuity

**Date:** 2026-04-02
**Context:** T3 from [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Related gate:** G5 in [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
**Related risks:** C in [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md)
**Depends on:** T2 accepted at [2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md](2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md)
**Status:** `Accepted (design)` artifact for T3.

## 1. Decision

Adopt a deterministic hybrid continuity contract:

1. Every extracted, non-synthetic claim gets a derived `claim_key` computed from
   normalized current claim text.
2. Referential claims (`reinforced`, `revised`, `conceded`) gain an explicit
   `referent_text` field that must copy a prior claim's text exactly enough to
   survive the same normalization function.
3. The validator derives `referent_key = normalize(referent_text)` and checks it
   against the prior non-synthetic claim registry.
4. If a referential claim has no valid prior `referent_key`, it is reclassified
   to `new` before counters are computed.
5. Synthetic minimum-fallback claims never enter the referential registry and
   may not be used as referents.

This keeps the continuity mechanism deterministic while avoiding the most
serious weakness of pure exact-current-text matching: `revised` and
`conceded` claims often need to point at an earlier claim even when the current
claim text has changed.

## 2. Why This Direction

The current cross-model reference uses exact text matching on the current claim
text only
([ledger.py](../../packages/plugins/cross-model/context-injection/context_injection/ledger.py)).
That is simple, but it has a structural limitation: it only works cleanly when
the current claim text still matches the prior claim text. That is adequate for
`reinforced` in the easy case, but it is a weak fit for `revised` and
`conceded`, where the current turn often changes the wording.

Pure claim IDs were also considered, but there is no existing claim-ID surface
in the current protocol or state models
([base_types.py](../../packages/plugins/cross-model/context-injection/context_injection/base_types.py),
[types.py](../../packages/plugins/cross-model/context-injection/context_injection/types.py)).
Adding persistent IDs to every claim introduction would widen the protocol and
state surface more than is justified for the benchmark-first slice.

The hybrid keeps the computation deterministic:

- the system never infers continuity from semantic overlap
- the only accepted continuity proof is an exact normalized referent key
- the current claim may change wording, but the referent must still resolve
  mechanically to a prior non-synthetic claim

It also keeps the widening small. The current extraction contract already emits
per-claim `text`, `status`, and `turn`
([codex-dialogue.md](../../packages/plugins/cross-model/agents/codex-dialogue.md)).
Adding optional `referent_text` only for referential claims is narrower than
introducing mandatory stable IDs for every claim introduction and every future
reference.

The `reinforced` case is usually the lightest-weight version of this rule:
in many turns, `referent_text` will equal the current claim text after
normalization. The contract still keeps one explicit referent rule for all
referential statuses so the validation boundary stays uniform.

## 3. State Shape

The benchmark-first candidate's normalized local claim record becomes:

```text
ClaimRecord {
  text: str
  status: "new" | "reinforced" | "revised" | "conceded"
  turn: int
  claim_source: "extracted" | "minimum_fallback"
  referent_text: str | null
  claim_key: str
  referent_key: str | null
}
```

Definitions:

- `claim_key` is always derived as `normalize(text)`.
- `referent_text` is caller-provided only for referential statuses.
- `referent_key` is always derived as `normalize(referent_text)` when
  `referent_text` is present.

Registry rule:

- The continuity registry stores only `claim_key` values for prior claims with
  `claim_source="extracted"`.
- `minimum_fallback` claims are excluded from the registry and cannot satisfy a
  future `referent_key`.
- If multiple prior claims collapse to the same `claim_key`, continuity checks
  still remain deterministic because this slice validates only existence of a
  qualifying prior referent, not identity of a specific prior occurrence.

## 4. Owning Layers

| Layer | Ownership |
|---|---|
| 1 | Extract semantic data and emit claim text, status, and optional `referent_text` |
| 2 | Normalize claims, derive `claim_key` / `referent_key`, validate referential continuity, and reclassify invalid referential claims to `new` |
| 3 | Compute counters, `quality`, and `effective_delta` from the validated claim statuses |

This keeps continuity resolution inside the same local validation boundary as
the other counter-shaping rules.

## 5. Deterministic Algorithm Boundary

### 5.1 Normalization function

The continuity normalizer is:

```text
normalize(text):
    1. Unicode NFKC normalization
    2. trim leading/trailing whitespace
    3. collapse internal whitespace runs to a single space
    4. casefold
    5. strip trailing sentence punctuation: . , ; : ! ?
    6. trim leading/trailing whitespace
```

Nothing else.

The only punctuation widening is terminal sentence punctuation. This is
intentional: trailing punctuation is a common single-character extractor
variance, and stripping only that suffix reduces fragile false mismatches
without introducing semantic matching.

The final trim is intentional. Stripping terminal punctuation can expose a
trailing space that was previously shielded by that punctuation; trimming again
keeps the function idempotent.

In particular, the benchmark-first slice does not strip internal punctuation,
does not drop markdown delimiters, and does not rewrite claim wording.

### 5.2 Registry construction

```text
prior_registry = {
    prior_claim.claim_key
    for prior_claim in prior_normalized_claims
    if prior_claim.claim_source == "extracted"
}
```

`prior_normalized_claims` is the cumulative validated claim history from prior
turns after T2 normalization has added `claim_source` and prior T3 validation
has already derived `claim_key` for those claims.

### 5.3 Validation and reclassification

For each current claim:

```text
claim_key = normalize(claim.text)

if claim.claim_source == "minimum_fallback":
    require claim.status == "new"
    require claim.referent_text is null
    accept claim

elif claim.status == "new":
    require claim.referent_text is null
    accept claim

else:  # reinforced / revised / conceded
    if claim.referent_text is null:
        reclassify claim.status -> "new"
        clear referent_text
        clear referent_key
    else:
        referent_key = normalize(claim.referent_text)
        if referent_key not in prior_registry:
            reclassify claim.status -> "new"
            clear referent_text
            clear referent_key
        else:
            accept referential status
```

`require` violations are pipeline-integrity failures upstream of T3. They must
raise a hard error, not trigger reclassification or silent canonicalization.

The reclassification path is reserved only for the expected extractor-failure
cases in the referential branch above:

- missing `referent_text` for `reinforced` / `revised` / `conceded`
- `referent_text` present but not resolvable in the prior registry

Counter implication:

- Reclassified claims are counted as `new`.
- Valid referential claims preserve `reinforced` / `revised` / `conceded`.
- Synthetic claims never count as prior referents because they never enter the
  registry.

### 5.4 Why T-04 reclassifies instead of warning

Cross-model's current `_referential_warnings()` path is warning-only because a
separate server still owns the authoritative derived state
([ledger.py](../../packages/plugins/cross-model/context-injection/context_injection/ledger.py)).
T-04 does not have that second authority. The same local loop that extracts
claim statuses also consumes them to compute counters and `effective_delta`.

Because of that, warning-only continuity checks are too weak for the
benchmark-first candidate:

- a bad `reinforced` label that remains unreclassified suppresses a real
  `new_claims` increment
- a bad `new` label on what should have been referential inflates
  `effective_delta`
- the misclassification then pollutes the next turn's prior-claim history

Reclassification is therefore part of the deterministic validation boundary,
not an optional reviewer hint.

### 5.5 Why this is better than pure exact-current-text matching

Example:

```text
Turn 1: "JWT is the better fit here."           status=new
Turn 2: "OAuth is preferable after all."        status=revised
          referent_text="JWT is the better fit here."
```

Pure exact-current-text matching would fail because the turn-2 current text
does not match the prior claim text. The hybrid succeeds without semantic
matching because the referent itself is an exact normalized copy of the prior
claim text.

## 6. Documented Non-Goals

The benchmark-first candidate intentionally does not solve:

1. Automatic paraphrase matching without explicit `referent_text`
2. Semantic overlap, synonym, or entailment checks
3. Claim splitting or merging across turns
4. Disambiguation between multiple prior claims that normalize to the same key
5. Recovery when the agent cannot name the prior claim text exactly enough to
   survive normalization

Consequence:

- If the agent cannot provide a valid exact referent, the claim becomes `new`.
- That may over-count advancement in some paraphrase-heavy cases.
- In repeated failure cases, that false advancement can delay plateau detection
  and push a dialogue toward budget exhaustion instead of natural convergence.
- This is accepted as a bounded benchmark-first limitation rather than solved
  with semantic matching.

## 7. Rejected Alternatives

### A. Pure normalized exact match on current claim text

Rejected because it makes `revised` and `conceded` brittle even in ordinary
non-paraphrase cases where the current claim text legitimately changes.

### B. Full claim IDs carried across the whole dialogue

Rejected for the benchmark-first slice because there is no existing ID surface
to inherit, and the added protocol/state churn is larger than this slice needs
before the first dry-run.

### C. Semantic overlap or LLM-judged continuity

Rejected because it violates G5's deterministic computation boundary.

### D. Warning-only referential validation

Rejected because T-04 lacks an external correcting authority. If continuity
validation does not canonicalize statuses before counter computation, the same
misclassification that triggered the warning still distorts `quality`,
`effective_delta`, and the next turn's prior-claim set.

## 8. Option Comparison

| Option | Deterministic | Handles changed wording for `revised` / `conceded` | Protocol/state cost | Benchmark-first verdict |
|---|---|---|---|---|
| Pure current-text exact match | Yes | Poorly | Low | Too brittle |
| Explicit `referent_text` hybrid | Yes | Yes, when extractor can name the prior claim | Medium | Selected |
| Full claim IDs | Yes | Yes | High | Deferred |
| Semantic overlap | No | Yes | Medium-High | Rejected |

## 9. Verification Path

The T3 implementation should be considered correct only if it has tests for:

1. Normalization is idempotent:
   `normalize(normalize(x)) == normalize(x)` for representative inputs.
2. Casefold behavior:
   `normalize("JWT is Better") == normalize("jwt is better")`.
3. Trailing punctuation behavior:
   `normalize("claim text.") == normalize("claim text")`.
4. Whitespace collapse behavior:
   `normalize("claim   text") == normalize("claim text")`.
5. Combined normalization behavior:
   `normalize("  Claim Text!  ") == normalize("claim text")`.
6. `reinforced` with valid `referent_text` to a prior extracted claim preserves
   `reinforced`
7. `revised` with changed current text but valid `referent_text` preserves
   `revised`
8. `conceded` with changed current text but valid `referent_text` preserves
   `conceded`
9. Missing `referent_text` on a referential claim reclassifies it to `new`
10. Unmatched `referent_text` reclassifies it to `new`
11. Synthetic minimum-fallback claims cannot be used as referents
12. A paraphrased claim without valid `referent_text` is treated as `new`
13. The validated status is what feeds counter computation and therefore
   `effective_delta`

## 10. Remaining Question Before G5 Acceptance

This contract is design-ready only if the team accepts one explicit tradeoff:

`referent_text` makes continuity deterministic and auditable, but it still
requires the extracting agent to name the prior claim being reinforced,
revised, or conceded. The computation layer never performs semantic matching on
its behalf.

If that tradeoff is acceptable, G5 can move to `Accepted (design)`. If not, the
alternative is a broader claim-ID design with higher protocol and state cost.
