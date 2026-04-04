---
module: state-model
status: active
normative: true
authority: state-model
---

# State Model

Data structures, schemas, wire formats, processing rules, and state
machines for claims, evidence, verification, and budgets.

## <a id="t4-sm-01"></a>T4-SM-01: Claim Occurrence Registry

T4-owned, built during layer 2 after T3 validation:

```text
occurrence_registry: dict[str, list[ClaimOccurrence]]
```

```text
ClaimOccurrence {
  introduction_turn: int
  claim_text: str
  claim_key: str
  occurrence_index: int
}
```

### Construction Rules

| Claim type | Registered? | Details |
|-----------|-------------|---------|
| `new` extracted | With merger check | If `claim_key` matches a **live** occurrence AND normalized `claim_text` matches → merge. Conceded excluded. If no live match → new occurrence |
| `revised` extracted | With merger check | Same merger rule as `new`. If `claim_key` matches a **live** occurrence AND normalized `claim_text` matches → merge (convergent re-expression). If no live match → new occurrence with new identity |
| `reinforced` | No | Shares referent's live occurrence via resolution ([T4-SM-03](#t4-sm-03)) |
| `conceded` | No | Referent's occurrence remains in registry for evidence history |
| `minimum_fallback` | No | Never enters evidence model (T2) |

`occurrence_index` is 0-based count of same-key entries already
registered for this turn. (Usually 0.)

### Same-Text Same-Key Merger Rule

When a `new` or `revised` claim has the same `claim_key` AND the same
normalized `claim_text` (NFKC, trim, collapse whitespace, casefold, strip
trailing punctuation — same normalization as T3) as an existing **live**
`ClaimOccurrence`, the registry does NOT create a new occurrence. The
claim shares the existing occurrence's `ClaimRef`. Evidence binding stays
unified. T2/T3 still count the claim with its original status (`new` or
`revised`). The merger is invisible to T2/T3.

### Concession Exception

An occurrence is **live** if its `ClaimRef` has an active entry in
`verification_state`. Conceded claims are removed from
`verification_state` ([T4-SM-06](#t4-sm-06) lifecycle). Their occurrences
remain in the registry for evidence history but are excluded from merger
candidacy. Reintroduction after concession always creates a new
occurrence.

**No claims discarded.** All validated claims proceed to T2 counter
computation with their original extraction status.

## <a id="t4-sm-02"></a>T4-SM-02: Within-Turn Processing Order

Layer 2 processes the current turn's claims in two deterministic phases.

### Canonical Intra-Phase Ordering

Before processing, each phase sorts its claims by
`(claim_key, status, claim_text)` ascending (lexicographic on all three
fields). The tertiary `claim_text` key breaks ties when two claims share
the same `claim_key` and `status` within a single turn. This makes
`claim_id` allocation ([T4-SM-06](#t4-sm-06)) deterministic from claim
text content, not from extractor output order. T2 preserves raw extractor
order for counter computation but T4's processing order is independent —
the sort happens at T4's layer 2 entry, after T2/T3 have already
processed the claims.

### Phase 1 — Status Changes

Process all `conceded` and `reinforced` claims (sorted ascending):
- `conceded`: remove entry from `verification_state`. Occurrence stays
  in registry (evidence history) but is now dead.
- `reinforced`: resolve referent ([T4-SM-03](#t4-sm-03)), share
  `ClaimRef`. No state change.

### Phase 1.5 — Forced-New Reclassification

After Phase 1, before Phase 2, check all referential claims
(`reinforced`, `revised`) whose referent has no live occurrences. Both
types are reclassified:
- `reinforced` with dead referent → reclassified to `status = "new"`,
  `claim_source = "extracted"`. Enters Phase 2 as a `new` claim.
- `revised` with dead referent → reclassified to `status = "new"`,
  `claim_source = "extracted"`. Enters Phase 2 as a `new` claim.

Both cases represent the same semantic situation: a claim that references
something that no longer exists is functionally a fresh assertion. The
`revised` case is not "revising" anything — without reclassification, it
would be "new" for identity (new occurrence, new ClaimRef) but "revised"
for T2 counters and the synthesis `validated_entry` trajectory. This is
the same dual semantic state that reclassification eliminates for
`reinforced`.

This reclassification IS a T2/T3 input change: T2's counter computation
sees a `new` claim instead of `reinforced` or `revised`. The synthesis
claim-history surface (`validated_entry` trajectory in
[dialogue-synthesis-format.md:7](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md))
also sees the reclassified status.

### Phase 2 — New Registrations

Process all `new` and `revised` claims (sorted ascending):
- `new`: merger check against **live** occurrences (per
  [T4-SM-01](#t4-sm-01)). Phase 1 already processed concessions, so
  `verification_state` reflects the current turn's concessions.
- `revised`: same merger check. A revised claim whose normalized text
  matches a live occurrence merges (convergent re-expression).

For claims that produce a new occurrence (not merged), scoutable
classification ([T4-SB-05](scouting-behavior.md#t4-sb-05)) determines
the initial verification status: `unverified` if scoutable,
`not_scoutable` if not. Classification happens at registration time
before entry creation in `verification_state`
([T4-SM-06](#t4-sm-06) lifecycle).

### T2/T3/Synthesis Interaction

Both phases produce claims that feed into T2 counter computation (step 3)
and the synthesis `validated_entry` trajectory. The reclassification in
Phase 1.5 changes claim status before ANY consumer sees it — T2 counters,
T3 registry, and synthesis trajectory all see the reclassified status.

## <a id="t4-sm-03"></a>T4-SM-03: Referent Resolution

When a referential claim passes T3 validation with `referent_key`:

```text
candidates = [
    c for c in occurrence_registry.get(referent_key, [])
    if ClaimRef_from(c) in verification_state
]
# Filter to live occurrences only.
# T3 guarantees referent_key exists in prior registry,
# but all matching occurrences may be conceded.

if not candidates:
    # All occurrences for this key are conceded.
    # This claim will be reclassified in Phase 1.5 (T4-SM-02).
    # Both `reinforced` and `revised`: reclassified to `new`.
    return NO_LIVE_REFERENT

# Exact text match first among live candidates
exact = [c for c in candidates if c.claim_text == claim.referent_text]
target = exact[-1] if exact else candidates[-1]
```

**Dead-occurrence exclusion:** Referent resolution filters to live
occurrences only. If no live candidates exist, the claim is routed to
forced-new reclassification ([T4-SM-02](#t4-sm-02) Phase 1.5).

Exact text match resolves ambiguity among live candidates. Recency is the
tie-breaker only for distinct-text collisions. Same-text collisions among
live occurrences cannot arise — the merger rule prevents them.

## <a id="t4-sm-04"></a>T4-SM-04: Claim Reference

```text
ClaimRef {
  introduction_turn: int
  claim_key: str
  occurrence_index: int
}
```

Unique by construction. Derived from `ClaimOccurrence`.

**Wire format:** When serialized in `claim_provenance_index`
([T4-PR-03](provenance-and-audit.md#t4-pr-03)), `ClaimRef` is a dense
array: `[introduction_turn, claim_key, occurrence_index]`.

## <a id="t4-sm-05"></a>T4-SM-05: Evidence Record

```text
EvidenceRecord {
  index: int
  turn: int
  claim_ref: ClaimRef
  claim_text: str
  entity: str
  steps: list[ScoutStep]
  citations: list[CitationSpan]
  disposition: "supports" | "contradicts" | "conflicted"
              | "ambiguous" | "not_found"
}
```

```text
ScoutStep {
  step_index: int
  tool: "Glob" | "Grep" | "Read"
  query: str
  query_type: "definition" | "falsification" | "supplementary"
  expected_contradiction_target: str | null
  read_anchor: "query_result" | "entity_span" | "whole_file" | null
  scope_root: str
  match_count: int
  match_digest: str | null
}
```

```text
CitationSpan {
  source_step_index: int
  path: str
  line_range: str | null
  snippet: str | null
}
```

### Key Fields

- `index`: dense append-time identifier for the record. Assigned as
  `len(evidence_log)` immediately before append, so
  `evidence_log[i].index == i` is an invariant for the run.
  `record_indices` and synthesis trajectory joins use this key.
- `claim_text`: unnormalized snapshot. Self-contained record.
- `entity`: grammar `<path_or_symbol>`, `<path_or_symbol> <qualifier>`,
  or `<entity> × <entity>` for relational claims
  ([T4-SB-05](scouting-behavior.md#t4-sb-05)). The primary entity
  (left of `×`) determines scouting focus. Only identifiers from claim
  text or tool output.
- `query_type`: classifies each scout query. `"definition"` targets what
  the entity IS. `"falsification"` targets what would contradict the
  claim. `"supplementary"` is any additional query.
- `match_digest`: compressed-block guide. Format:
  `"5 in control.py: cited L42,L58; uncited L103,L187,L201"`. Capped at
  20 lines. **This is a navigation aid, not the authoritative omission
  surface.** The authority is the mechanical diff
  ([T4-PR-11](provenance-and-audit.md#t4-pr-11)).
- `snippet`: present at tiers 1-2. `null` at tier 3.
- `source_step_index`: links citation to producing step.

### Disposition Assessment

Disposition is assessed from **full tool output**, not from selected
citations:

1. Agent executes 2-5 tool calls
   ([T4-SB-04](scouting-behavior.md#t4-sb-04) query types).
2. Agent reads ALL output.
3. Agent assesses disposition:

| Disposition | Meaning |
|-------------|---------|
| `supports` | Full output directly confirms target claim. No contradicting evidence found |
| `contradicts` | Full output directly refutes target claim. No supporting evidence found |
| `conflicted` | Full output contains both confirming and refuting evidence |
| `ambiguous` | Output relevant but neither confirms nor refutes |
| `not_found` | No relevant evidence in output |

**Disposition rubric:**
- "Directly confirms" = the passage's meaning is unambiguous with respect
  to the claim's assertion.
- "Directly refutes" = the passage unambiguously contradicts the claim.
- Borderline cases → `ambiguous`.
- Remaining interpretation variance is the same class the adjudicator
  faces. If benchmark results show disposition variance degrading metrics,
  the rubric should be tightened as a benchmark-contract amendment.

4. Agent selects citations that ILLUSTRATE the disposition.

### Citation Rules

| Rule | Constraint |
|------|-----------|
| Total per round | Max 5 |
| Glob steps | 0 citations (hard — discovery, not evidence) |
| Polarity preservation | If `conflicted`: at least one confirming AND one refuting citation. If `contradicts`: at least one refuting. If `supports`: at least one confirming |
| Ordering | Candidates sorted by `(path, line_number)` before selection |

**Assessment boundary:** Reading code and determining what it means is
agent judgment. The polarity-preserving rule prevents selective omission.
The mechanical diff ([T4-PR-11](provenance-and-audit.md#t4-pr-11))
provides the audit surface — no agent self-reporting is load-bearing.

### Audit Fields Are Non-Authoritative

`expected_contradiction_target` and `read_anchor` are structured agent
explanations, not proof. They reduce audit burden (reviewer can check
coherence without re-deriving intent from the raw query) but are not
evidence. The authoritative surfaces remain: the actual queries in
`query`, the tool outputs in the transcript, and the mechanical diff
([T4-PR-11](provenance-and-audit.md#t4-pr-11)).

Non-authoritative does not mean unauditable. `read_anchor` is a declared
justification class that the adjudicator reviews against the actual read
scope and tool output ([T4-PR-12](provenance-and-audit.md#t4-pr-12)).
The field records the agent's stated reason for the read scope; the
adjudicator independently verifies whether that claim holds. These roles
are compatible: `read_anchor` is not evidence of read-scope
justification, but it IS the surface against which the adjudicator
checks justification.

## <a id="t4-sm-06"></a>T4-SM-06: Verification State Model

```text
VerificationEntry {
  claim_id: int
  claim_ref: ClaimRef
  status: "unverified" | "supported" | "contradicted"
        | "conflicted" | "ambiguous" | "not_scoutable"
  evidence_indices: list[int]
  scout_attempts: int
}
```

### claim_id Allocation Rule

`claim_id` is a run-scoped auto-increment integer assigned at the moment
a new `VerificationEntry` is created. Allocation happens AFTER Phase 1.5
reclassification AND Phase 2 merger resolution
([T4-SM-02](#t4-sm-02)) — a merged claim reuses the existing entry's
`claim_id`, and a reclassified claim allocates a new `claim_id` as a
`new` claim. Reintroductions after concession allocate a new `claim_id`.
The allocation sequence is deterministic: given the same dialogue
transcript and the same processing order, the same `claim_id`s are
produced.

**`claim_id` is the canonical join key** for provenance
([T4-PR-03](provenance-and-audit.md#t4-pr-03)) and claim ledger
annotations ([T4-PR-05](provenance-and-audit.md#t4-pr-05) `[ref:]`).
`ClaimRef` ([T4-SM-04](#t4-sm-04)) remains the structural identity for
registry lookups and lifecycle tracking. `claim_id` is the
serialization-safe integer that appears in external surfaces.

### Status Derivation (One Rule, Used Everywhere)

```text
effective = set()
for i in evidence_indices:
    d = evidence_log[i].disposition
    if d == "conflicted":
        effective.add("supports")
        effective.add("contradicts")
    elif d in ("supports", "contradicts", "ambiguous"):
        effective.add(d)

if "contradicts" in effective and "supports" in effective:
    status = "conflicted"
elif "contradicts" in effective:
    status = "contradicted"
elif "supports" in effective:
    status = "supported"
elif "ambiguous" in effective:
    status = "ambiguous"
else:
    status = "unverified"
```

**This same rule governs:**
- Verification state updates (this section)
- Scout target selection
  ([T4-SB-03](scouting-behavior.md#t4-sb-03))
- Synthesis supported-claim aggregation
  ([T4-PR-09](provenance-and-audit.md#t4-pr-09))

A claim is `supported` in the benchmark sense when
`status == "supported"` — meaning at least one `supports` disposition
exists in the evidence set and no `contradicts` disposition exists.

### Lifecycle

| Event | Transition |
|-------|-----------|
| New extracted claim (scoutable) | Allocate `claim_id`. Add: `unverified`, `evidence_indices=[]`, `scout_attempts=0` |
| New extracted claim (not scoutable) | Allocate `claim_id`. Add: `not_scoutable`, `evidence_indices=[]`, `scout_attempts=0`. Terminal — never selected for scouting |
| Revised claim (new occurrence, scoutable) | Allocate `claim_id`. New `ClaimRef`, new entry at `unverified`, `scout_attempts=0` |
| Revised claim (new occurrence, not scoutable) | Allocate `claim_id`. New `ClaimRef`, new entry at `not_scoutable`, `scout_attempts=0`. Terminal |
| Revised claim (merged) | Reuse existing `claim_id`. Shares existing `ClaimRef`. No new entry. T2/T3 still count as `revised` |
| Evidence stored | Append record with `index = len(evidence_log)` (pre-append), recompute from full set, `scout_attempts += 1` |
| `not_found` stored | Append record with `index = len(evidence_log)` (pre-append; no effect on effective set), `scout_attempts += 1` |
| `minimum_fallback` | Never enters model |
| `reinforced` | Shares referent's `ClaimRef`. No new entry |
| Forced-new (dead referent, scoutable) | Allocate `claim_id`. Reclassified to `new` ([T4-SM-02](#t4-sm-02) Phase 1.5). New occurrence, new `ClaimRef`, new entry at `unverified` |
| Forced-new (dead referent, not scoutable) | Allocate `claim_id`. Reclassified to `new` ([T4-SM-02](#t4-sm-02) Phase 1.5). New occurrence, new `ClaimRef`, new entry at `not_scoutable`. Terminal |
| `conceded` | Remove entry from `verification_state`. Occurrence stays in registry, excluded from merger and resolution |
| Reintroduction after concession (scoutable) | Allocate `claim_id`. New occurrence (concession exception), new `ClaimRef`, new `unverified` entry |
| Reintroduction after concession (not scoutable) | Allocate `claim_id`. New occurrence (concession exception), new `ClaimRef`, new `not_scoutable` entry. Terminal |
| Pending round (abandoned) | `scout_attempts += 1`. No evidence index appended, no status recompute |

`scout_budget_spent` is NOT incremented in lifecycle events. It
increments exactly once per round at step 5b
([T4-SB-01](scouting-behavior.md#t4-sb-01)), covering both completed and
abandoned rounds. The lifecycle table tracks claim-local state only. See
[T4-SM-07](#t4-sm-07) for the conversation-wide budget model.

## <a id="t4-sm-07"></a>T4-SM-07: Agent Working State

| Field | Type | Initial |
|-------|------|---------|
| `occurrence_registry` | `dict[str, list[ClaimOccurrence]]` | `{}` |
| `evidence_log` | `list[EvidenceRecord]` | `[]` |
| `verification_state` | `dict[ClaimRef, VerificationEntry]` | `{}` |
| `next_claim_id` | `int` | `0` |
| `claim_provenance_index` | `dict[int, ProvenanceEntry]` | `{}` |
| `scout_budget_spent` | `int` | `0` |

`evidence_count = len(evidence_log)`.

### Claim Provenance Index

Keyed by `claim_id`. Two variants:

```text
ProvenanceEntry (scouted) {
  claim_id: int
  claim_ref: ClaimRef
  type: "scouted"
  record_indices: list[int]
}

ProvenanceEntry (not_scoutable) {
  claim_id: int
  claim_ref: ClaimRef
  type: "not_scoutable"
  classification_trace: ClassificationTrace
}
```

Scouted claims accumulate `record_indices` as evidence records are
created (step 5d). `not_scoutable` claims get their
`ClassificationTrace` at Phase 2 registration.

**Serialization boundary:** The `dict[int, ProvenanceEntry]` above is
the agent's internal working state. When serialized to
`<!-- pipeline-data -->`, it becomes the dense JSON array defined in
[T4-PR-03](provenance-and-audit.md#t4-pr-03): entries ordered by
`claim_id`, array index == `claim_id`, length == `next_claim_id`. The
transformation is mechanical — no information is added or removed.

### Two Budget Surfaces

| Surface | Counter | Gate | What it controls |
|---------|---------|------|-----------------|
| Evidence budget | `evidence_count` (`len(evidence_log)`) | `evidence_count >= max_evidence` | Completed evidence records (scoring quality) |
| Effort budget | `scout_budget_spent` | `scout_budget_spent >= max_scout_rounds` | Total rounds started, completed or abandoned (prevents unbounded search) |

**Increment rule for `scout_budget_spent`:** Increments exactly once per
round, at step 5b (first tool call executed in
[T4-SB-01](scouting-behavior.md#t4-sb-01)). NOT incremented in lifecycle
events ([T4-SM-06](#t4-sm-06) lifecycle tracks claim-local state only).
Both completed and abandoned ([T4-SM-09](#t4-sm-09)) rounds count — a
round that starts with a tool call and then aborts still consumed the
increment at 5b. `max_scout_rounds = max_evidence + 2` — allows up to 2
abandoned rounds per run before the effort budget is exhausted.

`max_evidence` is a benchmark-contract parameter, not a T4 constant. Its
value MUST be governed by benchmark change control
([benchmark.md:200-207](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
and recorded in `manifest.json`. T4 consumes `max_evidence` but does not
define its value
([T4-BR-07](benchmark-readiness.md#t4-br-07) prerequisite item 6).

### Pipeline-Data Mapping

`<!-- pipeline-data -->` field `scout_count` maps to `evidence_count`
(= `len(evidence_log)`), preserving the existing contract
([dialogue-synthesis-format.md:150](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md),
[codex-dialogue.md:134](../../../packages/plugins/cross-model/agents/codex-dialogue.md)).

| Concept | Counter | Drives | Pipeline-data |
|---------|---------|--------|---------------|
| Evidence completed | `evidence_count` | Evidence budget gate, synthesis trajectory, analytics, `scout_count` | Yes (`scout_count`) |
| Effort spent | `scout_budget_spent` | Effort budget gate only | No (internal state) |

`scout_count` in pipeline-data intentionally reflects only completed
evidence records, not abandoned rounds. The effort budget is a T4-local
guardrail; downstream consumers see only the evidence budget.

## <a id="t4-sm-08"></a>T4-SM-08: Compression-Resistant Evidence Block

Re-emitted after each completed scouting round (part of layer-4
completion, before follow-up composition). Tiered compression within
2500-character budget.

### Worst-Case Accounting

| Scenario | Records | Tier 1 (~120ch/cite) | Tier 2 (~90ch/cite) | Tier 3 (~60ch/cite) |
|----------|---------|---------------------|--------------------|--------------------|
| B1-B7 (6t, 3 cites avg) | 6 | ~2880 ch | ~2160 ch | ~1440 ch |
| B8 (8t, 3 cites avg) | 8 | ~3840 ch | ~2880 ch | ~1920 ch |

### Format (Tier 1)

```text
## Evidence Block
E0: T1 | ref=(1,key,0) | supports
  entity: control.py:compute_action
  digest: 5 in control.py: cited L42,L58; uncited L103,L187,L201
  [0] → control.py:58-60 "def compute_action(…) -> ControlDecision:"
```

**Tier 2:** Snippets truncated to ~30 characters.

**Tier 3:** Snippets dropped. Citations become `path:line_range` only.

**Atomic round commit:** Evidence block re-emitted immediately after
evidence record creation (step 5e), before follow-up composition.

**Single capture point:** Evidence is gathered during layer-4 scouting
and ONLY during layer-4 scouting. No second evidence-access phase.

## <a id="t4-sm-09"></a>T4-SM-09: Pending-Round Emission

If a scouting round is interrupted before evidence record creation, the
agent emits a pending-round marker before T1 termination:

```text
## Pending Round (abandoned)
target_claim_id: 7
steps_executed: 2 of 3
last_tool: Grep "compute_action" → 5 matches
reason: scope_breach | error
```

Records target, steps completed, and abandonment reason. Does NOT record
disposition or citations. Raw tool output is in the transcript.

### Attempt Accounting

Any round that executes at least one tool call increments
`scout_attempts` for the target claim ([T4-SM-06](#t4-sm-06) lifecycle),
regardless of whether the round completes. `scout_budget_spent` was
already incremented at step 5b (round start, [T4-SM-07](#t4-sm-07)).
Without this rule, repeated mid-round aborts (e.g., systematic scope
breaches on the same claim) could let one claim consume unlimited
attempts without ever hitting the per-claim attempt limit. The
conversation-wide effort cap
(`scout_budget_spent >= max_scout_rounds`) independently prevents
unbounded search — each round start consumed one increment at 5b.

## <a id="t4-sm-10"></a>T4-SM-10: Evidence Persistence

Evidence persists through the **run transcript**, NOT through the
synthesis artifact.

**Per-round capture:** Evidence block re-emitted after each completed
round ([T4-SM-08](#t4-sm-08)). Post-containment tool output captured per
call ([T4-CT-03](containment.md#t4-ct-03)).

**Audit chain is transcript-complete (given
[T4-F-13](foundations.md#t4-f-13)).** The authority chain requires only
the synthesis and transcript — both already required by the benchmark
spec
([benchmark.md:95-96](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md),
[benchmark.md:107-108](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).

**Synthesis artifact contains NO evidence data.** Only: narrative text,
inline `(path:line_range)` citations, synthesis checkpoint, claim ledger
([T4-PR-05](provenance-and-audit.md#t4-pr-05)), and
`<!-- pipeline-data -->`.

### Terminal Paths

| Exit | Evidence state |
|------|---------------|
| Normal completion | Last evidence block in transcript (all rounds committed) |
| Scope breach mid-round | Pending-round marker + prior committed rounds |
| Error termination (T1 `error`) | Last committed block + any pending-round marker. No synthesis dependency |
| Crash/abort | Transcript has whatever was captured. Run invalid. Rerun |
