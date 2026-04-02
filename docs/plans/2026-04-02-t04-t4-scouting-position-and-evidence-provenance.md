# T-04 T4 Decision: Scouting Position And Evidence Provenance

**Date:** 2026-04-02
**Context:** T4 from [2026-04-01-t04-benchmark-first-design-plan.md](2026-04-01-t04-benchmark-first-design-plan.md)
**Related gate:** G3 in [2026-04-01-t04-convergence-loop-risk-register.md](../reviews/2026-04-01-t04-convergence-loop-risk-register.md)
**Related risks:** J, D, F, E in [2026-04-01-t04-convergence-loop-risk-analysis.md](../reviews/2026-04-01-t04-convergence-loop-risk-analysis.md)
**Depends on:** T2 accepted at [2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md](2026-04-02-t04-t2-synthetic-claim-and-closure-contract.md)
**Status:** Draft for review (revision 17).

## Revision History

| Rev | Key changes |
|-----|-------------|
| 1 | Initial draft. |
| 2 | Loop order, discovery/citation, ClaimRef, verification model, evidence block. |
| 3 | T4-owned occurrence registry, unified semantics, citation-step linkage, self-contained records, claim-only scouting justification, run artifacts. |
| 4 | Occurrence index (no dedup), record-level `conflicted`, disposition from full output, polarity-preserving citations, match_digest, exact-text referent resolution, canonical result sort, harness-owned persistence, honest compression accounting. |
| 5 | Revised claims as occurrences. Per-round citation cap. Snippet recovery reads. Evidence export via synthesis epilogue. Richer match_digest. Disposition rubric. Synthesis aggregation with conflicted expansion. Crash=invalid. Transcript fidelity dependency. |
| 6 | Evidence removed from synthesis artifact. No snippet recovery reads. Same-text same-key merger. Unresolved-item scouting. `candidate_matches`. Transcript fidelity as specification. |
| 7 | Unresolved-item scouting removed (broke 4 contracts). `candidate_matches` dropped (agent self-report). Dead-occurrence exclusion in referent resolution. Per-claim attempt limit. Scout query coverage rule. Pending-round emission. Atomic round commit. `evidence.json` optional. Within-turn two-phase processing. `scout_outcomes` projection declared. |
| 8 | (1) Forced-new resurrection reclassifies claim to `new` across all consumers — eliminates dual semantic state. (2) Merger extended to `revised` claims — eliminates same-text live collisions from convergent revisions. (3) Authoritative omission surface is mechanical diff (raw output minus citations), not agent-reported match_digest. (4) Attempt limit graduated: 1 for `not_found`, 2 for `conflicted`/`ambiguous`. (5) Two mandatory query types: entity-definition AND falsification. (6) Full helper-era migration enumeration. (7) Transcript fidelity as benchmark-contract prerequisite. |
| 9 | (1) Forced-new reclassification extended to `revised` with dead referent — eliminates last dual semantic state. (2) Authoritative language conditional on transcript fidelity; transcript fidelity elevated to blocking external dependency. (3) Direct-tool containment contract: pre-execution confinement, post-containment capture, "raw" = unprocessed-by-agent. (4) Synthesis→record join via `evidence_map` in pipeline-data. (5) Claim-class scope: scoutable, relational-scoutable, not-scoutable with `ambiguous`/`not_scoutable` path. (6) Harness computes mechanical diff by default — match_digest no longer gates escalation. (7) Abandoned rounds consume attempt budget. (8) Second-attempt query diversity: SHOULD→MUST with objective criteria. (9) Round budget relaxed to 2-5 calls. (10) Helper-era migration completeness claim replaced with T4-replaces + T5-external-blockers split. (11) Claim-history surface (`validated_entry` trajectory) added to declared changes. |
| 10 | (1) `not_scoutable` wired as terminal verification status — enters model without scout round, excluded from target selection, objective classification criteria, adjudicator audit. (2) `evidence_map` join changed from `claim_key` to `ClaimRef`; synthesis checkpoint carries `[ref:]` annotations for deterministic harness join. (3) `scout_budget_spent` counter: abandoned rounds consume conversation-wide budget, not just claim-local attempts. (4) §4.6 containment re-grounded in `scope_envelope` from consultation contract; safety dependency owned, blame-shifting language removed. (5) Transcript-fidelity blocker assigned owner (T7) and target patch set. `evidence_map` consumer named. (6) §3.3 round budget normalized to 2-5 everywhere. |
| 11 | (1) Checkpoint completeness rule: every factual claim in the narrative MUST have a corresponding checkpoint entry with `[ref:]` — checkpoint is the completeness surface, not a summary. Approximate content matching eliminated. (2) `not_scoutable` propagated to ALL claim registration paths: revised claims and forced-new claims get scoutable/not-scoutable split. Synthesis-format contract update declared as external blocker. (3) Budget accounting fixed: `scout_budget_spent` increments exactly once per round at step 5b (round start), NOT in lifecycle entries. Stale "one concept" sentence removed. `scout_count` (pipeline-data) maps to evidence budget only; effort budget is internal. |
| 12 | (1) `claim_id: int` added to `VerificationEntry` as parse-safe join key — deterministic allocation after Phase 1.5/Phase 2 resolution. `[ref:]` annotations use integer `claim_id`, not text-embedded `ClaimRef` tuple. (2) Two-tier provenance: `evidence_map` replaced by `claim_provenance_index` with separate `scouted` (record_indices) and `not_scoutable` (ClassificationTrace) variants. Deterministic audit guarantee narrowed to scouted claims. (3) Checkpoint completeness rule relaxed from MUST to SHOULD — enforcement requires narrative factual-claim inventory, declared as T7 blocker. Benchmark scoring kept on full synthesis. (4) Atomic checkpoint line rule: one line = one claim. No claim compression into multi-ref lines. (5) Per-tool omission relevance boundaries and normative read-scope rule: reads anchored to query result, entity span, or justified whole-file class. (6) Structured non-authoritative audit fields: `expected_contradiction_target` in ScoutStep, `read_anchor` for read justification, `ClassificationTrace` for not_scoutable. All explicitly non-authoritative. |
| 13 | (1) G3 gate condition: narrative provenance gap is a hard blocker — T4/G3 cannot close until benchmark defines `checkpoint_coverage_rate` metric OR T7 delivers narrative-claim inventory. Current benchmark metrics don't penalize missing coverage. (2) Checkpoint grammar kept outcome-based: `NOT_SCOUTABLE` tag removed, replaced with `[evidence: not_scoutable]` annotation. Outcome axis (RESOLVED/UNRESOLVED/EMERGED) and evidence axis are orthogonal. (3) `claim_provenance_index` canonical wire format: dense JSON array, invariant `claim_id == index`, all allocated IDs persist. (4) Full-file reads: omission surface = full file. No post-citation boundary shrinking (closes shape-gaming exploit). Enclosing-scope heuristic removed. (5) Canonical intra-phase ordering: `(claim_key, status)` ascending sort before Phase 1 and Phase 2, making `claim_id` deterministic from text content. |
| 14 | (1) Claim ledger separated from checkpoint. New `## Claim Ledger` section: flat `FACT:` lines with `[ref: N]` and `[evidence:]` annotations. Checkpoint stays outcome-based (RESOLVED/UNRESOLVED/EMERGED, unchanged from synthesis-format contract). (2) G3 decoupled from narrative coverage. G3 invariant is "accepted scout results retained as structured provenance" — satisfied by Tier 1 scouted chain. Narrative coverage is a separate synthesis quality concern for T7. (3) `checkpoint_coverage_rate` removed as independent option — metric depends on narrative-claim inventory (computing coverage IS the inventory problem). Single mechanism: T7 inventory. Coverage metric is downstream output, not alternative. (4) Stale "bounded by incentives" language removed from §5.3 — no defined cost until T7 mechanism lands. (5) Checkpoint no longer dual-purpose: outcome summary (checkpoint) and fact inventory (claim ledger) are separate surfaces with different grammars. |
| 15 | (1) Canonical provenance surface cleanup: all stale checkpoint-based `[ref:]` references updated to claim ledger throughout §5.3 audit chain, verification checklist, and rejected-alternatives "Changed to" sentences. (2) Narrative-to-ledger relationship: claim ledger is canonical factual-claim inventory. Every synthesis factual claim MUST have a ledger entry. Narrative-only factual claims are synthesis-contract violations. Dedup rule for harness/checker join path. (3) Silent mode downgrade → hard invalid-run: benchmark `agent_local` runs MUST hard-fail on mode mismatch with failure artifact. Scoped to benchmark behavior. (4) Benchmark-execution prerequisite: runner/manifest validator MUST reject runs when T7 narrative-claim inventory/checker unavailable. Independent of G3. (5) Decomposition obligation before `not_scoutable` classification: agent MUST attempt decomposition into scoutable subclaims when truth condition preserved. `ClassificationTrace` extended with `decomposition_attempted`, `subclaims_considered`, `residual_reason`. (6) Corpus calibration requirement: `not_scoutable` rate validated via dry run, report by task ID. Required artifact. (7) Read-scope eligibility expanded: whole-file justified by file-level truth conditions (presence/absence, pattern/convention claims), not path mention. Under-reading finding added (adjudicator, non-mechanical, same weight as omission). (8) Claim-shape adequacy: query-type quota is necessary but not sufficient for relational/multi-file claims. Adjudicator audits query-set-to-claim-shape match. |
| 16 | (1) Decomposition converted from mandatory runtime to audit-side analysis. Agent MUST NOT register decomposed subclaims — T2/T3 pipeline boundary (`claim_source`, counter semantics, registry construction undefined for decomposed claims). Agent SHOULD consider decomposition; records analysis in ClassificationTrace. Adjudicator audits adequacy as methodology finding. (2) Narrative-to-ledger category list aligned with benchmark exactly: added "current code relationships" to mirror [benchmark.md:123-128]. (3) Pre-T7 enforcement story made single-valued: benchmark runs are blocked until T7 (§6.2 prerequisite). All "adjudicator catches violations pre-T7" language removed from benchmark-oriented sections. Contract obligation exists regardless; enforcement is T7-only. (4) Under-reading, claim-shape inadequacy, and misclassification defined as **methodology findings** in `adjudication.json` — do not change claim labels, are recorded for system comparison. Finding format is T7 adjudication-format dependency. (5) Mode-mismatch failure artifact destination defined: invalid-run entry in `runs.json`. Schema is T7 benchmark-contract dependency. (6) Hygiene: header updated to rev 16, verification checklist renumbered (55-70), stale SHOULD→MUST in checklist item 45, duplicate item numbers resolved. |
| 17 | (1) Methodology findings given concrete benchmark consequence: candidate-only per-run threshold gate (pass-rule condition 5). `methodology_finding_threshold` pinned in versioned benchmark contract, recorded in `manifest.json`. Threshold breach is a valid scored run that fails condition 5 — not an invalid run, not grounds alone for rerun. Five finding kinds defined: `under_reading`, `shape_inadequacy`, `misclassification`, `decomposition_skipped`, `narrative_ledger_violation`. Finding row schema: `(run_id, inventory_claim_id, finding_kind, detection, ledger_claim_id?, detail)`. Row keyed by T7 adjudicator `inventory_claim_id`, not ledger `claim_id` (narrative-ledger violations have no ledger ID). Detection field distinguishes `judgment` from `mechanical`. All stale "creates pressure" / "for system comparison" language replaced with explicit T7 dependency. (2) Benchmark-execution prerequisite extended to all T7 schema dependencies: narrative inventory/checker AND methodology-finding format AND mode-mismatch schema AND `methodology_finding_threshold`. Scoped to scored runs — calibration dry runs permitted but MUST NOT be used for pass/fail comparisons. (3) Decomposition analysis SHOULD→MUST. No criterion-based exceptions. `decomposition_attempted: false` is always a `decomposition_skipped` methodology finding. Valid "nothing to decompose" path: `decomposition_attempted: true, subclaims_considered: [], residual_reason` populated. (4) Adjudication scope amendment: benchmark must expand adjudicator authority to include candidate process artifacts (query traces, ClassificationTrace, claim ledger) alongside final synthesis. (5) Narrative-ledger violations typed as `narrative_ledger_violation` methodology finding for benchmark accounting. |

## 1. Decision

1. Control decision before scouting. Scouting only on live turns.
2. Evidence records separate discovery steps from citation spans with
   `source_step_index` linkage. Steps carry `match_digest` as
   compressed-block guide.
3. T4-owned occurrence registry tracks claim introductions for `new`
   and `revised` claims. Both subject to same-text merger against live
   occurrences. Dead-referent claims reclassified to `new` for ALL
   consumers (both `reinforced` and `revised`). No claims discarded —
   all survive to T2/T3 counters.
4. Disposition assessed from full tool output. Citations illustrate,
   polarity-preserving. Per-round total citation cap of 5; Glob=0 is the
   only per-tool hard constraint.
5. Record-level `conflicted` disposition for mixed-polarity rounds.
6. One verification/synthesis rule. `conflicted` expands to both
   `supports` and `contradicts` in all contexts.
7. Compression-resistant evidence block within 2500ch budget. Tiered
   compression drops snippets at tier 3 — no recovery reads. Single
   capture point is absolute.
8. Evidence persists via run transcript, not synthesis artifact. Audit
   chain is transcript-complete. Omission surface is the mechanical
   diff of raw tool output minus citations — authoritative given
   transcript fidelity (§3.9). Harness computes this diff by default.
9. Scouting targets claims only. Per-claim attempt limit: 1 for
   `not_found`, 2 for `conflicted`/`ambiguous`. Abandoned rounds
   consume both claim-local and conversation-wide budget
   (`scout_budget_spent`).
10. Two mandatory scout query types: entity-definition AND falsification.
    Second attempts MUST use different queries (objective criteria).
    Round budget: 2-5 tool calls.
11. Direct-tool containment contract (§4.6): pre-execution confinement,
    post-containment capture in transcript. "Raw" means unprocessed by
    the agent, not unfiltered by the harness.
12. Synthesis→record join via `claim_provenance_index` in
    `<!-- pipeline-data -->` keyed by `claim_id` (§5.2). Two provenance
    tiers: scouted (record_indices, full mechanical chain) and
    not_scoutable (ClassificationTrace, classification provenance only).
    Separate claim ledger section (`## Claim Ledger`) carries `FACT:`
    lines with `[ref: N]` annotations. Checkpoint stays outcome-based
    (unchanged). Atomic ledger lines (one fact per line).
    Claim-class scope defined (§4.7): scoutable, relational-scoutable,
    and `not_scoutable` as terminal verification status with objective
    classification criteria, structured ClassificationTrace, and
    adjudicator audit.

## 2. Why This Direction

**Control before scouting.** Dead turns must not scout
([codex-dialogue.md:346](../../packages/plugins/cross-model/agents/codex-dialogue.md)).

**T3 does not preserve occurrence identity.** T4 builds a parallel
registry without reopening T3
([T3:144-148](2026-04-02-t04-t3-deterministic-referential-continuity.md)).

**Revised claims need new occurrences.** §3.4 gives revised claims new
`ClaimRef`s. If they are not registered, later referential claims cannot
resolve to them.

**Same-text merger applies to BOTH `new` and `revised` claims.** The
assumption that revised claims always have different text ("different
text by definition") is wrong. Extractor errors can emit duplicate
revised claims in one turn, and separate revisions across turns can
converge to the same normalized text. Without merger, these create
multiple live occurrences with identical text under the same key —
exactly the collision class the design eliminated for `new` claims.
Extending merger to `revised` claims closes this gap. A `revised` claim
that produces the same normalized text as a live occurrence is not
actually a new truth condition — it is convergent re-expression. Merger
is the correct response.

**Concession exception excludes dead occurrences from merger AND
resolution.** Conceded occurrences remain in the registry for evidence
history but are excluded from both merger candidacy and referent
resolution. Reintroduction after concession always creates a fresh
identity.

**Forced-new resurrection reclassifies to `new` — ALL referential
types.** When a referential claim's referent is dead (all occurrences
for the key are conceded), T4 cannot bind it. The claim is reclassified
to `status = "new"` and `claim_source = "extracted"` before T2/T3
processing. This applies to BOTH `reinforced` AND `revised` claims with
dead referents. A `revised` claim whose referent no longer exists is not
revising anything — it is functionally a fresh assertion. Without
reclassification, the claim would be "new" for identity (new occurrence,
new ClaimRef) but "revised" for T2 counters and the synthesis
`validated_entry` trajectory — the same dual semantic state that rev 8
fixed for `reinforced`. T2/T3 and the claim-history surface all see a
`new` claim. This IS a T2/T3 input change (declared).

**Two-phase layer-2 processing.** Within a single turn, a claim can be
conceded AND a new claim with the same key introduced. Phase 1 (status
changes) runs before Phase 2 (registrations with merger checks). This
makes identity deterministic regardless of claim ordering in the
extractor output.

**Per-round citation cap, not per-tool.** A `Read` step can expose both
supporting and contradicting passages. Per-tool caps conflict with the
polarity-preserving rule. A per-round total of 5 with Glob=0 resolves
this.

**Disposition from full output.** Capped citation selection creates a
cherry-pick path if disposition is derived only from the selected subset.

**No snippet recovery reads.** Tier 3 preserves `path:line_range`. A
second evidence-gathering phase during synthesis violates G3's single
fixed capture point.

**Evidence NOT in the synthesis artifact.** The benchmark scores the
final synthesis. Embedded evidence data contaminates scoring and creates
safety risk. Evidence persists through the transcript.

**Omission surface is mechanical, not agent-reported — authoritative
given transcript fidelity (§3.9).** `match_digest` is a compressed-block
guide (capped at 20 lines). The authority for cherry-pick detection is
the mechanical diff: post-containment tool output (all match lines, in
transcript) minus citations (agent-selected, in evidence record). This
diff is computable by the harness without relying on agent
self-reporting. On large outputs where `match_digest` is truncated, the
mechanical diff catches everything. The harness MUST compute this diff
by default for every evidence record — match_digest is a human
convenience overlay, never a gate for escalation. The authority claim is
contingent on transcript fidelity (§3.9): if the benchmark contract does
not normatively require untruncated tool output, the diff degrades to
"verifiable up to the evidence block."

**Graduated attempt limit.** `not_found` claims get one attempt — there
is nothing to find and retrying wastes budget. `conflicted` and
`ambiguous` claims get two attempts — the evidence was real but
inconclusive. A second scout with a different query approach may
clarify. After the limit, claims are deprioritized.

**Two mandatory query types.** Entity-definition (what it IS) plus
falsification (what would contradict the claim). Together these ensure
the scout output covers both actual entity behavior and the specific
negation of the claim's assertion. This is stronger than a single
definition-query rule and auditable via `query` fields. Not foolproof
(an agent can craft weak queries), but raises the bar for systematic
bias.

**Claim-only scouting (structural justification).** Rev 6 attempted
unresolved-item scouting. Review showed 4 critical incompatibilities
(§7.27). One-turn delay accepted with structural justification.

**Audit chain is transcript-complete (given §3.9).** The authority chain
requires only the synthesis and transcript — both already required by
the benchmark spec. No dependency on `evidence.json` or any additional
artifact. Authority contingent on transcript fidelity (§3.9).

**Helper-era scouting surfaces enumerated; external blockers declared.**
`agent_local` mode (T5) severs helper-era surfaces. §6.1 enumerates
every T4-replaced scouting surface. T5's primary migration set (enum
schema, synthesis format, dialogue skill, tests) are declared as
external blockers (§6.2) — they must land before `agent_local` runs
produce valid data.

**Transcript fidelity is a benchmark-contract prerequisite.** T4
interprets "raw run transcript" as untruncated tool output per call. If
this interpretation is wrong, the audit chain degrades from "fully
verifiable" to "verifiable up to the evidence block." This is declared
as a prerequisite, not a follow-up clarification.

## 3. State Shape

### 3.1 Claim occurrence registry

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

**Construction rules:**

| Claim type | Registered? | Details |
|-----------|-------------|---------|
| `new` extracted | With merger check | If `claim_key` matches a **live** occurrence AND normalized `claim_text` matches → merge. Conceded excluded. If no live match → new occurrence |
| `revised` extracted | With merger check | Same merger rule as `new`. If `claim_key` matches a **live** occurrence AND normalized `claim_text` matches → merge (convergent re-expression). If no live match → new occurrence with new identity |
| `reinforced` | No | Shares referent's live occurrence via resolution (§3.1.1) |
| `conceded` | No | Referent's occurrence remains in registry for evidence history |
| `minimum_fallback` | No | Never enters evidence model (T2) |

`occurrence_index` is 0-based count of same-key entries already
registered for this turn. (Usually 0.)

**Same-text same-key merger rule:** When a `new` or `revised` claim has
the same `claim_key` AND the same normalized `claim_text` (NFKC, trim,
collapse whitespace, casefold, strip trailing punctuation — same
normalization as T3) as an existing **live** `ClaimOccurrence`, the
registry does NOT create a new occurrence. The claim shares the existing
occurrence's `ClaimRef`. Evidence binding stays unified. T2/T3 still
count the claim with its original status (`new` or `revised`). The
merger is invisible to T2/T3.

**Concession exception:** An occurrence is **live** if its `ClaimRef`
has an active entry in `verification_state`. Conceded claims are removed
from `verification_state` (§3.4 lifecycle). Their occurrences remain in
the registry for evidence history but are excluded from merger
candidacy. Reintroduction after concession always creates a new
occurrence.

**No claims discarded.** All validated claims proceed to T2 counter
computation with their original extraction status.

#### 3.1.2 Within-turn processing order

Layer 2 processes the current turn's claims in two deterministic phases.

**Canonical intra-phase ordering:** Before processing, each phase sorts
its claims by `(claim_key, status)` ascending (lexicographic on both
fields). This makes `claim_id` allocation (§3.4) deterministic from
claim text content, not from extractor output order. T2 preserves raw
extractor order for counter computation but T4's processing order is
independent — the sort happens at T4's layer 2 entry, after T2/T3 have
already processed the claims.

**Phase 1 — Status changes:** Process all `conceded` and `reinforced`
claims (sorted by `(claim_key, status)` ascending):
- `conceded`: remove entry from `verification_state`. Occurrence stays
  in registry (evidence history) but is now dead.
- `reinforced`: resolve referent (§3.1.1), share `ClaimRef`. No state
  change.

**Phase 2 — New registrations:** Process all `new` and `revised` claims
(sorted by `(claim_key, status)` ascending):
- `new`: merger check against **live** occurrences (per §3.1). Phase 1
  already processed concessions, so `verification_state` reflects the
  current turn's concessions.
- `revised`: same merger check. A revised claim whose normalized text
  matches a live occurrence merges (convergent re-expression).

**Forced-new reclassification (Phase 1.5):** After Phase 1, before
Phase 2, check all referential claims (`reinforced`, `revised`) whose
referent has no live occurrences. Both types are reclassified:
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
[dialogue-synthesis-format.md:7](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md))
also sees the reclassified status.

**T2/T3/synthesis interaction:** Both phases produce claims that feed
into T2 counter computation (step 3) and the synthesis `validated_entry`
trajectory. The reclassification in Phase 1.5 changes claim status
before ANY consumer sees it — T2 counters, T3 registry, and synthesis
trajectory all see the reclassified status.

#### 3.1.1 Referent resolution

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
    # This claim will be reclassified in Phase 1.5 (§3.1.2).
    # Both `reinforced` and `revised`: reclassified to `new`.
    return NO_LIVE_REFERENT

# Exact text match first among live candidates
exact = [c for c in candidates if c.claim_text == claim.referent_text]
target = exact[-1] if exact else candidates[-1]
```

**Dead-occurrence exclusion:** Referent resolution filters to live
occurrences only. If no live candidates exist, the claim is routed
to forced-new reclassification (§3.1.2 Phase 1.5).

Exact text match resolves ambiguity among live candidates. Recency is
the tie-breaker only for distinct-text collisions. Same-text collisions
among live occurrences cannot arise — the merger rule prevents them.

### 3.2 Claim reference

```text
ClaimRef {
  introduction_turn: int
  claim_key: str
  occurrence_index: int
}
```

Unique by construction. Derived from `ClaimOccurrence`.

### 3.3 Evidence record

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

**Key fields:**

- `claim_text`: unnormalized snapshot. Self-contained record.
- `entity`: grammar `<path_or_symbol>`, `<path_or_symbol> <qualifier>`,
  or `<entity> × <entity>` for relational claims (§4.7). The primary
  entity (left of `×`) determines scouting focus. Only identifiers from
  claim text or tool output.
- `query_type`: classifies each scout query. `"definition"` targets what
  the entity IS. `"falsification"` targets what would contradict the
  claim. `"supplementary"` is any additional query. Auditable: a reviewer
  verifies at least one of each mandatory type per round.
- `match_digest`: compressed-block guide. Format:
  `"5 in control.py: cited L42,L58; uncited L103,L187,L201"`.
  Capped at 20 lines. For large outputs:
  `"80 in module.py: cited L42,L58; 78 uncited (first 20: L12,L15,...)"`.
  **This is a navigation aid, not the authoritative omission surface.**
  The authority is the mechanical diff (§5.3).
- `snippet`: present at tiers 1-2. `null` at tier 3.
- `source_step_index`: links citation to producing step.

**Disposition assessment:**

Disposition is assessed from **full tool output**, not from selected
citations:

1. Agent executes 2-5 tool calls (§4.4 query types).
2. Agent reads ALL output.
3. Agent assesses disposition:

| Disposition | Meaning |
|-------------|---------|
| `supports` | Full output directly confirms target claim. No contradicting evidence found in output |
| `contradicts` | Full output directly refutes target claim. No supporting evidence found in output |
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

**Citation rules:**

| Rule | Constraint |
|------|-----------|
| Total per round | Max 5 |
| Glob steps | 0 citations (hard — discovery, not evidence) |
| Polarity preservation | If `conflicted`: at least one confirming AND one refuting citation. If `contradicts`: at least one refuting. If `supports`: at least one confirming |
| Ordering | Candidates sorted by `(path, line_number)` before selection |

**Assessment boundary:** Reading code and determining what it means is
agent judgment. The polarity-preserving rule prevents selective omission.
The mechanical diff (§5.3) provides the audit surface — no agent
self-reporting is load-bearing.

### 3.4 Verification state model

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

**`claim_id` allocation rule:** `claim_id` is a run-scoped auto-increment
integer assigned at the moment a new `VerificationEntry` is created.
Allocation happens AFTER Phase 1.5 reclassification AND Phase 2 merger
resolution — a merged claim reuses the existing entry's `claim_id`, and
a reclassified claim allocates a new `claim_id` as a `new` claim.
Reintroductions after concession allocate a new `claim_id`. The
allocation sequence is deterministic: given the same dialogue transcript
and the same processing order (§3.1.2), the same `claim_id`s are
produced.

**`claim_id` is the canonical join key** for provenance (§5.2) and
claim ledger annotations (§5.2 `[ref:]`). `ClaimRef` (§3.2) remains the
structural identity for registry lookups and lifecycle tracking.
`claim_id` is the serialization-safe integer that appears in external
surfaces.

**Status derivation (one rule, used everywhere):**

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
- Verification state updates (§3.4)
- Scout target selection skip conditions (§4.2)
- Synthesis supported-claim aggregation (§5.2)

A claim is `supported` in the benchmark sense when `status == "supported"`
— meaning at least one `supports` disposition exists in the evidence set
and no `contradicts` disposition exists.

**Lifecycle:**

| Event | Transition |
|-------|-----------|
| New extracted claim (scoutable, §4.7) | Allocate `claim_id`. Add: `unverified`, `evidence_indices=[]`, `scout_attempts=0` |
| New extracted claim (not scoutable, §4.7) | Allocate `claim_id`. Add: `not_scoutable`, `evidence_indices=[]`, `scout_attempts=0`. Terminal — never selected for scouting |
| Revised claim (new occurrence, scoutable) | Allocate `claim_id`. New `ClaimRef`, new entry at `unverified`, `scout_attempts=0` |
| Revised claim (new occurrence, not scoutable) | Allocate `claim_id`. New `ClaimRef`, new entry at `not_scoutable`, `scout_attempts=0`. Terminal |
| Revised claim (merged) | Reuse existing `claim_id`. Shares existing `ClaimRef`. No new entry. T2/T3 still count as `revised` |
| Evidence stored | Append index, recompute from full set, `scout_attempts += 1` |
| `not_found` stored | Append index (no effect on effective set), `scout_attempts += 1` |
| `minimum_fallback` | Never enters model |
| `reinforced` | Shares referent's `ClaimRef`. No new entry |
| Forced-new (dead referent, scoutable) | Allocate `claim_id`. Reclassified to `new` (§3.1.2 Phase 1.5). New occurrence, new `ClaimRef`, new entry at `unverified` |
| Forced-new (dead referent, not scoutable) | Allocate `claim_id`. Reclassified to `new` (§3.1.2 Phase 1.5). New occurrence, new `ClaimRef`, new entry at `not_scoutable`. Terminal |
| `conceded` | Remove entry from `verification_state`. Occurrence stays in registry, excluded from merger and resolution |
| Reintroduction after concession (scoutable) | Allocate `claim_id`. New occurrence (concession exception), new `ClaimRef`, new `unverified` entry |
| Reintroduction after concession (not scoutable) | Allocate `claim_id`. New occurrence (concession exception), new `ClaimRef`, new `not_scoutable` entry. Terminal |
| Pending round (abandoned, §3.7) | `scout_attempts += 1`. No evidence index appended, no status recompute |

`scout_budget_spent` is NOT incremented in lifecycle events. It
increments exactly once per round at step 5b (§4.1), covering both
completed and abandoned rounds. The lifecycle table tracks claim-local
state only. See §3.5 for the conversation-wide budget model.

### 3.5 Agent working state

| Field | Type | Initial |
|-------|------|---------|
| `occurrence_registry` | `dict[str, list[ClaimOccurrence]]` | `{}` |
| `evidence_log` | `list[EvidenceRecord]` | `[]` |
| `verification_state` | `dict[ClaimRef, VerificationEntry]` | `{}` |
| `next_claim_id` | `int` | `0` |
| `claim_provenance_index` | `dict[int, ProvenanceEntry]` | `{}` |
| `scout_budget_spent` | `int` | `0` |

`evidence_count = len(evidence_log)`.

**Claim provenance index:** Keyed by `claim_id`. Two variants:

```text
ProvenanceEntry (scouted) {
  claim_id: int
  claim_ref: ClaimRef
  record_indices: list[int]
}

ProvenanceEntry (not_scoutable) {
  claim_id: int
  claim_ref: ClaimRef
  classification_trace: ClassificationTrace
}
```

Scouted claims accumulate `record_indices` as evidence records are
created (step 5d). `not_scoutable` claims get their
`ClassificationTrace` at Phase 2 registration. The index is the
provenance authority for §5.2.

**Two budget surfaces:**

| Surface | Counter | Gate | What it controls |
|---------|---------|------|-----------------|
| Evidence budget | `evidence_count` (`len(evidence_log)`) | `evidence_count >= max_evidence` | Completed evidence records (scoring quality) |
| Effort budget | `scout_budget_spent` | `scout_budget_spent >= max_scout_rounds` | Total rounds started, completed or abandoned (prevents unbounded search) |

**Increment rule for `scout_budget_spent`:** Increments exactly once per
round, at step 5b (first tool call executed in §4.1). NOT incremented
in lifecycle events (§3.4 lifecycle tracks claim-local state only).
Both completed and abandoned (§3.7) rounds count — a round that starts
with a tool call and then aborts still consumed the increment at 5b.
`max_scout_rounds = max_evidence + 2` — allows up to 2 abandoned rounds
per run before the effort budget is exhausted.

**Pipeline-data mapping:** `<!-- pipeline-data -->` field `scout_count`
maps to `evidence_count` (= `len(evidence_log)`), preserving the
existing contract
([dialogue-synthesis-format.md:150](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md),
[codex-dialogue.md:134](../../packages/plugins/cross-model/agents/codex-dialogue.md)).

**Two concepts, two consumers:**

| Concept | Counter | Drives | Pipeline-data |
|---------|---------|--------|---------------|
| Evidence completed | `evidence_count` | Evidence budget gate, synthesis trajectory, analytics, `scout_count` in pipeline-data | Yes (`scout_count`) |
| Effort spent | `scout_budget_spent` | Effort budget gate only | No (internal state) |

`scout_count` in pipeline-data intentionally reflects only completed
evidence records, not abandoned rounds. The effort budget is a T4-local
guardrail; downstream consumers see only the evidence budget.

### 3.6 Compression-resistant evidence block

Re-emitted after each completed scouting round (part of layer-4
completion, before follow-up composition). Tiered compression within
2500-character budget.

**Worst-case accounting** (1 scout/turn, round-max 5 citations):

| Scenario | Records | Tier 1 (~120ch/cite) | Tier 2 (~90ch/cite) | Tier 3 (~60ch/cite) |
|----------|---------|---------------------|--------------------|--------------------|
| B1-B7 (6t, 3 cites avg) | 6 | ~2880 ch | ~2160 ch | ~1440 ch |
| B8 (8t, 3 cites avg) | 8 | ~3840 ch | ~2880 ch | ~1920 ch |

**Format (tier 1):**

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

### 3.7 Pending-round emission

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

**Attempt accounting:** Any round that executes at least one tool call
increments `scout_attempts` for the target claim (§3.4 lifecycle),
regardless of whether the round completes. `scout_budget_spent` was
already incremented at step 5b (round start, §3.5). Without this rule,
repeated mid-round aborts (e.g., systematic scope breaches on the same
claim) could let one claim consume unlimited attempts without ever
hitting the per-claim attempt limit. The conversation-wide effort cap
(`scout_budget_spent >= max_scout_rounds`) independently prevents
unbounded search — each round start consumed one increment at 5b.

### 3.8 Evidence persistence

Evidence persists through the **run transcript**, NOT through the
synthesis artifact.

**Per-round capture:** Evidence block re-emitted after each completed
round (§3.6). Post-containment tool output captured per call (§4.6).

**Audit chain is transcript-complete (given §3.9).** The authority chain
requires only the synthesis and transcript — both already required by
the benchmark spec
([benchmark.md:95-96](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md),
[benchmark.md:107-108](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
Authority contingent on transcript fidelity (§3.9).

**Synthesis artifact contains NO evidence data.** Only: narrative text,
inline `(path:line_range)` citations, synthesis checkpoint,
claim ledger (`## Claim Ledger`), and `<!-- pipeline-data -->`.

**Terminal paths:**

| Exit | Evidence state |
|------|---------------|
| Normal completion | Last evidence block in transcript (all rounds committed) |
| Scope breach mid-round | Pending-round marker + prior committed rounds |
| Error termination (T1 `error`) | Last committed block + any pending-round marker. No synthesis dependency |
| Crash/abort | Transcript has whatever was captured. Run invalid. Rerun |

### 3.9 Transcript fidelity specification

**BLOCKING EXTERNAL DEPENDENCY.** The benchmark contract MUST
normatively specify untruncated tool output when it requires "raw run
transcript"
([benchmark.md:95-96](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
T4's evidence provenance — specifically the mechanical omission diff
(§5.3), query coverage audit (§4.4), and containment verification
(§4.6) — depends on this interpretation. **T4 implementation MUST NOT
proceed until this dependency is resolved.** The benchmark contract must
also specify a parseable transcript format sufficient for the harness to
extract tool call inputs, outputs, and evidence blocks mechanically.

**What T4 requires from the transcript:**

| Item | Required for |
|------|-------------|
| Complete post-containment Glob/Grep/Read outputs per call | Mechanical omission diff (§5.3) |
| Agent evidence block re-emission each round | Structured record extraction |
| Tool call inputs (queries, paths, scope roots) | Query coverage audit (§4.4) |
| Deterministic transcript parsing | Harness diff engine, evidence extraction |

**If this dependency is NOT resolved** — if "raw transcript" permits
truncation or lossy capture — the audit chain degrades from "fully
verifiable via mechanical diff" to "verifiable up to match_digest in
the evidence block." T4 declares this degradation path explicitly rather
than hiding the dependency.

**Benchmark-contract text:** The benchmark contract should state:
*"Raw run transcript means untruncated tool output for every tool call
in every turn."* T4 declares this as a prerequisite for its provenance
story, not a follow-up clarification.

## 4. Scouting Position In The Loop

### 4.1 Per-turn loop

```text
1. Extract semantic data (layer 1)
2. Validate, normalize, register occurrences (layer 2):
   2a. Phase 1: process concessions, reinforcements (§3.1.2)
   2b. Phase 1.5: reclassify dead-referent claims to `new` (§3.1.2)
   2c. Phase 2: register new/revised claims with merger checks (§3.1)
3. Compute counters, quality, effective_delta (layer 3)
4. Control decision (T1 ControlDecision)
5. Scout (layer 4):
   5a. Select target (§4.3)
   5b. Execute tool calls (§4.4 query coverage) [scout_budget_spent += 1 here]
   5c. Assess disposition, select citations
   5d. Create evidence record, update verification state
   5e. Re-emit evidence block (atomic commit)
   — SKIP 5a-5e if conclude, budget, or no targets
6. Compose follow-up (layer 5) — SKIP if conclude
7. Send follow-up — SKIP if conclude
```

### 4.2 Scout skip conditions

| Condition | Source |
|----------|--------|
| `action == "conclude"` | Control decision |
| `evidence_count >= max_evidence` | Evidence budget exhausted |
| `scout_budget_spent >= max_scout_rounds` | Effort budget exhausted (§3.5) |
| No scoutable targets (§4.3) | Nothing to scout |

### 4.3 Scout target selection

| Priority | Status | Condition |
|----------|--------|-----------|
| 1 | `unverified` | `scout_attempts == 0` |
| 2 | `conflicted` | `scout_attempts < 2` |
| 3 | `ambiguous` | `scout_attempts < 2` |
| 4 (skip) | `supported`, `contradicted`, `not_scoutable` | Terminal |
| 4 (skip) | `unverified` | `scout_attempts >= 1` (first scout was `not_found`) |
| 4 (skip) | `conflicted`, `ambiguous` | `scout_attempts >= 2` |

Secondary sort: `introduction_turn` ascending. Tertiary: `claim_key`
lexicographic. Quaternary: `occurrence_index` ascending.

**Graduated attempt limit:**

| After first scout returns... | Max attempts | Rationale |
|-----------------------------|-------------|-----------|
| `not_found` | 1 | Nothing to find. Retrying wastes budget |
| `ambiguous` | 2 | Evidence was real but inconclusive. Different query may clarify |
| `conflicted` | 2 | Evidence was real but mixed. Second query may resolve |
| `supports` | 1 | Terminal — claim verified |
| `contradicts` | 1 | Terminal — claim refuted |

A `not_found` result leaves status at `unverified` with
`scout_attempts = 1` → priority 4. An `ambiguous` or `conflicted`
result allows a second attempt with a different query approach.

**One-turn delay (claim-only scouting):** Unresolved questions become
scoutable claims one turn after Codex responds. At most one lost scout
per question cycle. Rev 6 analysis in §7.27.

### 4.4 Scout query coverage

Each scouting round executes 2-5 tool calls. Two query types are
mandatory. Minimum 2 calls (one per mandatory type). Target 3.
Hard cap 5 (prevents budget monopolization by a single claim):

| Type | What it targets | Example | Required |
|------|----------------|---------|----------|
| `definition` | What the entity IS or DOES | `Grep "def compute_action"`, `Read control.py:55-65` | Yes (1+) |
| `falsification` | What would CONTRADICT the claim | `Grep "compute_action.*None"`, search for alternative return types | Yes (1+) |
| `supplementary` | Additional context | Usage sites, test coverage, callers | Optional |

**Why two types:** A single definition query covers entity behavior but
not claim negation. A single falsification query checks the claim but
may miss entity context. Together they ensure the scout output covers
both what the entity does AND what would disprove the claim.

**Falsification query design:** The agent MUST construct a query that
targets a **specific expected-contradicting condition**. The
`expected_contradiction_target` field in `ScoutStep` records what the
query was designed to find. Examples:
- Claim "function X returns type Y" → `expected_contradiction_target`:
  "X returns non-Y type" → query: `Grep "def X.*->.*(?!Y)"`
- Claim "module X contains Y" → `expected_contradiction_target`:
  "Y defined outside X" → query: `Grep "class Y" --glob "!module_x/"`

A falsification query that searches for the same entity as the
definition query (with no contradicting condition) fails the diversity
check. The `expected_contradiction_target` must name a condition
distinct from the definition query's target.

**Claim-shape adequacy (normative):** The adequacy of query coverage is
claim-shape-dependent. For relational or multi-file claims, satisfying
the mandatory query-type quota (one definition, one falsification) is
necessary but not sufficient — the query set must address the claim's
actual structure. A relational claim "X calls Y" is not considered
adequately covered by a definition query for X and a falsification
query for X alone; the query set must also address Y. The adjudicator
audits whether the query set matches the claim shape, not just whether
the mandatory query types were present. A shape-inadequacy finding is a
**methodology finding** (`finding_kind: shape_inadequacy`,
`detection: judgment`) that appears in `adjudication.json`. It does not
change claim labels. Methodology findings are recorded in
`adjudication.json` for benchmark consumption (§6.2). Their effect on
the pass rule (per-run `methodology_finding_threshold` gate, condition
5) requires a T7 benchmark-contract amendment. Before that amendment,
findings exist as structured audit data without mechanical pass/fail
consequences. The methodology finding format is a T7 adjudication-format
dependency (§6.2).

**`read_anchor` field:** For Read tool calls, records the justification
for the read scope (§5.3 read-scope rule). `null` for Grep/Glob calls.

**Audit fields are non-authoritative.** `expected_contradiction_target`
and `read_anchor` are structured agent explanations, not proof. They
reduce audit burden (reviewer can check coherence without re-deriving
intent from the raw query) but are not evidence. The authoritative
surfaces remain: the actual queries in `query`, the tool outputs in the
transcript, and the mechanical diff (§5.3).

**Audit:** `query_type` field in each `ScoutStep` classifies the query.
A reviewer verifies at least one `definition` and one `falsification`
per round, checks `expected_contradiction_target` for coherence, and
confirms the falsification query targets a different condition than the
definition query. Post-hoc auditing cannot fix a bad benchmark run, but
it detects systematic bias across the benchmark corpus.

**Second-attempt queries:** When a claim gets a second scout attempt
(§4.3), the agent MUST use different queries than the first attempt. At
least one query in the second round MUST differ in query text from ALL
queries in the first round (not just type reclassification — the actual
search string must change). The `query` fields from the first round's
`ScoutStep`s are in the evidence block — the agent has them in context.
Objective difference criterion: `query_text_2 != query_text_1` for at
least one step pair.

### 4.5 Scope breach handling

**Canonical paths:** All paths resolved via realpath. Symlinks resolved.

**Per-call counting:** N out-of-scope results from one call = 1 breach.

**Root-constrained invocation:** `Glob`/`Grep` receive `path` within
`allowed_roots`. Post-execution filter on canonical paths.

**Pre-execution:** `Read` target checked before execution.

**Partial-round:** `scope_breach_count >= 3` mid-round → pending-round
marker (§3.7) → T1 termination.

### 4.6 Direct-tool containment contract

T4 replaces helper-era `execute_scout` (which had truncation, redaction,
and risk_signal at
[context-injection-contract.md:665](../../packages/plugins/cross-model/references/context-injection-contract.md))
with direct Glob/Grep/Read. The helper-era safety surfaces are replaced
by this containment contract:

**Pre-execution confinement:**

| Tool | Confinement |
|------|------------|
| `Read` | Target path checked against `allowed_roots` BEFORE execution. Out-of-scope → rejected, no output |
| `Grep` | `path` parameter set to `scope_root` within `allowed_roots`. Only results under scope root |
| `Glob` | `path` parameter set to `scope_root` within `allowed_roots`. Only results under scope root |

**Post-containment capture:** The transcript records **post-containment**
output. "Raw" in T4's provenance story means "unprocessed by the agent"
— not "unfiltered by the harness." Containment is a harness function
applied before the agent sees the output:

1. Pre-execution: tool invocation confined to `allowed_roots`
2. Post-execution: any residual out-of-scope results filtered on
   canonical paths (§4.5)
3. Post-containment output enters the transcript
4. Agent assesses disposition from post-containment output
5. Evidence record and citations reference post-containment output

**Why containment does not break provenance authority:** Containment is
deterministic and declared — scope roots are immutable, set at
delegation time via `scope_envelope`
([consultation-contract.md:127-131](../../packages/plugins/cross-model/references/consultation-contract.md)).
The benchmark restricts tool classes to Glob/Grep/Read
([benchmark.md:93-94](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
but does not itself define scope roots. The `scope_envelope` from the
consultation contract provides the immutable `allowed_roots` and source
classes. The agent cannot influence what containment filters. The
mechanical diff (§5.3) operates on post-containment output and remains
authoritative because both sides of the diff (tool output, citations)
are post-containment.

**Safety interaction:** The benchmark treats forbidden-path leakage as a
safety failure
([benchmark.md:145](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
Containment is T4's mechanism for preventing this, but a containment
failure is still a safety violation on the run — regardless of whether
the root cause is in the harness, the scope_envelope configuration, or
the tool invocation. T4 owns the pre-execution and post-execution
containment checks (§4.5). If a leak occurs despite correct checks, the
run is invalid per the benchmark safety rule.

**DECLARED SAFETY DEPENDENCY: Allowed-scope secret handling.** Within
`allowed_roots`, files may contain secrets (credentials, tokens, private
keys). The helper-era contract had `redactions_applied` and `risk_signal`
([context-injection-contract.md:671-672](../../packages/plugins/cross-model/references/context-injection-contract.md)).
T4's direct tools have no equivalent. This is an **explicit external
blocker** owned by T7: the benchmark harness must define whether
allowed-scope secrets require redaction, and if so, how redacted output
interacts with the post-containment provenance model. Until resolved,
T4 assumes allowed-scope content is safe to capture — correct for
benchmark corpora that are curated, but not for general use.

### 4.7 Claim-class scope

Not all benchmark claims are scoutable. T4 defines three claim classes:

| Class | Entity grammar | Scouting behavior |
|-------|---------------|-------------------|
| **Scoutable** | `<path_or_symbol>` or `<path_or_symbol> <qualifier>` | Standard scouting: definition + falsification queries |
| **Relational-scoutable** | `<entity> × <entity>` | Primary entity (left of `×`) determines scouting focus. Queries target the relationship between entities |
| **Not scoutable** | N/A | No scouting. Terminal verification status: `not_scoutable` (§3.4) |

**Scoutable claims:** Claims whose truth condition is verifiable by
examining entities locatable in the repo — file paths, symbols, code
patterns, configuration values. Most benchmark claims about repository
state and implementation behavior fall here.

**Relational-scoutable claims:** Claims about relationships between two
entities. "Function X calls function Y" → entity `X × Y`, scout focus
on X, definition query for X's implementation, falsification query for
whether X calls something other than Y. The evidence record's `entity`
field uses the `×` grammar; queries encode the relationship.

**Not-scoutable claims:** Abstract interpretations, meta-properties,
cross-system claims, or spec-interpretation claims where the truth
condition cannot be reduced to repo-searchable entities. These claims
enter the verification model at terminal status `not_scoutable` (§3.4
lifecycle). No `EvidenceRecord` is created — no scouting occurred. They
are excluded from target selection (§4.3, priority 4 skip). They appear
in the benchmark claim inventory and the synthesis.

**Classification criteria (objective):** A claim is scoutable if and
only if the agent can identify:
1. At least one entity fitting the `<path_or_symbol>` grammar (possibly
   with `<qualifier>` or `×` relational form)
2. A definition query that could be executed via Grep/Read
3. A falsification query that would surface contradicting evidence if it
   existed

If ANY of these three cannot be identified, the claim is `not_scoutable`.
The classification decision is made during Phase 2 registration (§3.1.2)
and is recorded as the terminal verification status.

**Decomposition analysis (audit-side, MUST):** Before classifying a
claim as `not_scoutable`, the agent MUST perform a decomposition check:
whether the claim can be decomposed into subclaims that individually
satisfy all three scoutable criteria. The agent records this analysis in
the `ClassificationTrace` (below) for adjudicator review. However, the
agent MUST NOT register decomposed subclaims as new pipeline entries —
T2/T3 define two claim sources (`extracted`, `minimum_fallback`) and
decomposed subclaims have no defined `claim_source`, counter semantics,
or continuity behavior. Subclaim registration, if desired at runtime,
requires T2/T3 pipeline integration (out of T4 scope).

The decomposition check may conclude quickly — if no plausible entity-
bearing subclaim candidates are identifiable, the agent records
`decomposition_attempted: true`, `subclaims_considered: []`, and
`residual_reason` explaining why no subclaims were found. This is a
valid outcome, not a finding. `decomposition_attempted: false` is always
a methodology finding (`finding_kind: decomposition_skipped`,
`detection: mechanical`) regardless of which criterion failed for the
whole claim. The decomposition check is the step that determines whether
subclaims exist — skipping it presupposes the answer.

The adjudicator evaluates decomposition adequacy: whether scoutable
subclaims exist that the agent failed to identify, and whether the
`not_scoutable` classification of the whole claim was justified given
the available decomposition. A finding occurs when the adjudicator
independently identifies scoutable subclaims that the agent's trace
failed to consider. This creates audit-side pressure against over-
classification without introducing pipeline-boundary violations.

**Classification trace (structured, non-authoritative):** When a claim
is classified `not_scoutable`, the agent records a `ClassificationTrace`:

```text
ClassificationTrace {
  claim_id: int
  candidate_entity: str | null
  failed_criterion: 1 | 2 | 3
  decomposition_attempted: bool
  subclaims_considered: list[str] | null
  residual_reason: str | null
}
```

`candidate_entity` is the closest entity the agent considered (null if
no entity fitting the grammar could be identified — criterion 1 failure).
`failed_criterion` is which of the three objective criteria failed first.
`decomposition_attempted` records whether the agent performed the
mandatory decomposition check before classification.
`decomposition_attempted: false` is always a `decomposition_skipped`
methodology finding — no exceptions. `subclaims_considered` lists any
subclaims the agent identified during decomposition (empty list `[]` if
decomposition was attempted but no subclaim candidates were found — a
valid outcome when `residual_reason` is populated).
`residual_reason` explains why no subclaims were found or why
identified subclaims were not individually scoutable (null only when
`subclaims_considered` is non-empty and explains itself).
All fields are **explicitly
non-authoritative** — they are the agent's explanation of its
classification, not proof. The adjudicator uses them as a starting
point for audit, not as evidence.

**Adjudicator audit:** The adjudicator independently reviews all
`not_scoutable` classifications using the `ClassificationTrace` as a
starting point. The adjudicator evaluates:
1. Whether the classification was correct (agent could have identified
   all three criteria for the original claim)
2. Whether decomposition analysis was adequate (whether scoutable
   subclaims exist that the agent failed to identify in the trace)
A misclassification is recorded as a methodology finding
(`finding_kind: misclassification`, `detection: judgment`). Inadequate
decomposition where the adjudicator identifies scoutable subclaims the
agent missed is also a methodology finding (`finding_kind:
misclassification`, `detection: judgment`). Both appear in
`adjudication.json` (§6.2 T7 adjudication-format dependency).
Methodology findings are recorded for benchmark consumption; their
effect on the pass rule requires a T7 amendment (§6.2). The adjudicator
still independently evaluates the claim's truth value — `not_scoutable`
affects scouting, not scoring.

**Synthesis policy:** `not_scoutable` claims MUST appear in the scored
synthesis if they are factual claims about the repo. The agent cannot
suppress claims by classifying them as not-scoutable. The adjudicator
scores them independently (§5.2 aggregation does not count them as
`supported` — they have no evidence).

**Why this scope matters:** Without explicit claim-class scope, agents
either shoehorn multi-entity claims into fake single-entity evidence
(producing formally compliant but substantively useless queries) or
produce falsification queries that cannot meaningfully test the claim.
Explicit scope gives the agent a legitimate path for claims that do not
fit the evidence model. Terminal status prevents retry loops.

**Corpus calibration requirement:** After implementation, the
`not_scoutable` classification rate MUST be validated against the
benchmark corpus via dry run. The dry run MUST produce a report of
`not_scoutable` rate broken down by task ID. Corpus tasks dominated by
cross-system and spec-interpretation claims (B1, B4, B5, B7, B8) are
most susceptible to over-classification. If the rate renders a material
fraction of scored synthesis claims unprovenanced for these tasks, the
classification criteria or decomposition rules must be tightened before
benchmark execution. The dry-run report is a required artifact, not a
deferred aspiration.

## 5. Synthesis Citation Surface

### 5.1 Evidence trajectory

Derived from `evidence_log`
([dialogue-synthesis-format.md:15](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)):

| Field | Derivation |
|-------|-----------|
| Record index | `record.index` (deterministic join key) |
| Entity | `record.entity` |
| Found | Citation snippet if available; `(path:line_range)` at tier 3 |
| Disposition | `record.disposition` |
| Impact | `supports` → "claim supported", `contradicts` → "premise falsified", `conflicted` → "evidence contradictory", `ambiguous` → "inconclusive", `not_found` → "no evidence" |

Only `EvidenceRecord` entries appear in the trajectory. No uncited
or un-dispositioned content enters the scored synthesis. Each trajectory
entry MUST include the record index to enable deterministic join from
synthesis claims to specific evidence records (§5.2).

**Projection to per-turn `scout_outcomes`:**

```text
scout_outcomes[turn_N] = [
    evidence_log[i]
    for i in range(len(evidence_log))
    if evidence_log[i].turn == turn_N
]
```

Populated in step 5d. The synthesis assembler reads `scout_outcomes`
from `turn_history` as before — entries are now `EvidenceRecord`s with
full schema rather than `evidence_wrapper` strings.

### 5.2 Inline citations and aggregation

Format: `(path:line_range)`. Only `CitationSpan` entries.

**Synthesis→record join (deterministic via `claim_id`):** Inline
citations use `(path:line_range)` in the scored narrative. The same
`(path:line_range)` can appear in multiple evidence records across turns.
The deterministic join from a synthesis claim to its specific evidence
record requires two structured surfaces:

**Surface 1: `claim_provenance_index` in `<!-- pipeline-data -->`** —
maps each `claim_id` to its provenance entry. Two variants:

```text
claim_provenance_index: [
  { claim_id: 0, claim_ref: [3, "compute_action behavior", 0], type: "scouted", record_indices: [2, 5] },
  { claim_id: 1, claim_ref: [4, "validate_input return type", 0], type: "scouted", record_indices: [3] },
  { claim_id: 2, claim_ref: [5, "module uses dependency injection", 0], type: "not_scoutable", classification_trace: { candidate_entity: "module", failed_criterion: 3 } }
]
```

**Canonical wire format:** Dense JSON array. Invariant:
`claim_provenance_index[i].claim_id == i` for all entries. Array length
equals `next_claim_id`. All allocated `claim_id`s persist in the index,
including claims later conceded (concession removes from
`verification_state` but the provenance entry is historical). No sparse
IDs, no gaps, no reordering.

Each entry retains the full `ClaimRef` for human readability. The `type`
field distinguishes scouted (has `record_indices`) from not_scoutable
(has `classification_trace`). This is provenance metadata — appropriate
for pipeline-data.

**Two provenance tiers:**

| Tier | Type | Join chain | Guarantee |
|------|------|-----------|-----------|
| 1 | `scouted` | `claim_id` → `record_indices` → evidence blocks in transcript → tool output | Full mechanical chain. Deterministic given transcript fidelity (§3.9) |
| 2 | `not_scoutable` | `claim_id` → `classification_trace` → adjudicator audit | Classification provenance only. No evidence chain (no scouting occurred). Adjudicator independently evaluates claim truth |

The deterministic-audit guarantee applies to **Tier 1 (scouted claims)
only**. Tier 2 claims have auditable classification (the trace records
what was attempted and which criterion failed) but no evidence
provenance — there is nothing to audit beyond whether the classification
was correct.

**Surface 2: Claim ledger** — a new synthesis section, separate from
the checkpoint. The claim ledger is a flat inventory of atomic factual
claims with `[ref:]` annotations. This is the provenance surface.

```text
## Claim Ledger
FACT: compute_action returns ActionResult [ref: 0]
FACT: validate_input rejects None [ref: 1]
FACT: module uses dependency injection [evidence: not_scoutable] [ref: 2]
FACT: module dependency ordering unclear [ref: 3]
```

**Separation of concerns:** The checkpoint and claim ledger serve
different purposes and MUST NOT be conflated:

| Surface | Purpose | Grammar | Content |
|---------|---------|---------|---------|
| **Checkpoint** | Dialogue outcome summary | `RESOLVED`, `UNRESOLVED`, `EMERGED` (outcome-based, per [dialogue-synthesis-format.md:55-65](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)) | What happened during the dialogue. Unchanged from synthesis-format contract |
| **Claim ledger** | Provenance inventory | `FACT` (fact-based) | Every atomic factual claim about the repo, with `[ref:]` for provenance join |

The checkpoint is NOT the provenance surface. Many repo facts in a
synthesis are supporting observations, not dialogue outcomes — they
don't fit `RESOLVED`/`UNRESOLVED`/`EMERGED`. Forcing them into the
checkpoint grammar would require agents to either jam facts into
outcome tags or leave them in narrative prose with no provenance.

**Claim ledger rules:**
- Each line is one atomic factual claim. One `FACT:`, one `[ref:]`.
- `[evidence: not_scoutable]` annotation for Tier 2 claims.
- No outcome tags. Facts are facts, not dialogue events.
- The `[ref:]` annotation is the harness join point. The `claim_id`
  integer is parse-safe. The harness reads: `[ref: N]` →
  `claim_provenance_index[N]` → record indices (Tier 1) or
  classification trace (Tier 2).
- When one claim has multiple evidence records, the provenance entry's
  `record_indices` list has multiple elements — but the ledger line
  still has one `[ref:]` pointing to one `claim_id`.

**Narrative-to-ledger relationship (normative):** The claim ledger is
the canonical factual-claim inventory. Every factual claim about
repository state, implementation behavior, contract or spec
requirements, or current code relationships
([benchmark.md:123-128](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
in the synthesis MUST have a corresponding claim ledger entry with
`[ref:]`. This mirrors the benchmark's claim inventory categories
exactly. Narrative prose may elaborate on, contextualize, or provide
reasoning about ledger facts, but MUST NOT introduce independent
factual claims in any benchmark-scored category that lack a ledger
entry.

**Scoring interaction:** The benchmark still scores the full synthesis
([benchmark.md:118-123](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)):
the adjudicator enumerates every distinct factual claim from the
complete synthesis. A narrative-only factual claim (present in prose but
absent from the ledger) is scored normally by the adjudicator AND
recorded as a methodology finding (`finding_kind:
narrative_ledger_violation`, `detection: mechanical`). The claim is not
exempt from scoring; the missing ledger entry is an additional
methodology finding that counts toward the per-run
`methodology_finding_threshold` (§6.2 pass-rule condition 5). The
finding row is keyed by `inventory_claim_id` (from T7 adjudicator claim
inventory), not ledger `claim_id` — by definition, narrative-only claims
have no ledger ID.

**Dedup rule (for harness and ledger checker):** When the same fact
appears in both narrative prose and the claim ledger, the harness and
ledger checker treat the ledger entry as canonical for the provenance
join. The adjudicator scores distinct factual claims per the benchmark
([benchmark.md:123](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md));
the dedup rule prevents double-counting in the harness join path, not
in adjudication.

**Mechanical enforcement:** Ledger completeness is not mechanically
enforceable without a narrative factual-claim inventory (requires
semantic extraction). Benchmark runs MUST NOT proceed until T7 delivers
the inventory and ledger completeness checker (§6.2 benchmark-execution
prerequisite). After T7, the ledger checker mechanically flags narrative
facts without ledger entries. The narrative-to-ledger MUST is a
synthesis contract obligation that agents must comply with regardless of
enforcement availability.

**Provenance coverage of scored claims:**
- Ledger claims with `[ref:]` → Tier 1 or Tier 2 provenance
  (deterministic or classification). Full chain.
- Narrative-only claims (no ledger entry) → synthesis-contract
  violation. Scored normally by adjudicator. No mechanical provenance
  audit possible. Missing ledger entry is a `narrative_ledger_violation`
  methodology finding (mechanical, keyed by `inventory_claim_id`).

**G3 scope (evidence provenance retention):** G3's invariant
([risk-register:35](../reviews/2026-04-01-t04-convergence-loop-risk-register.md))
is: "Every accepted scout result MUST be retained as structured
provenance, not just counted." T4 satisfies this via Tier 1 scouted
provenance: `EvidenceRecord` (§3.3) → `claim_provenance_index` →
`[ref:]` in claim ledger → full records in transcript. The G3
invariant concerns **scouted claims** — it does not require provenance
for unscouted narrative claims (there are no scout results to retain).

**Narrative coverage gap (separate from G3):** With the narrative-to-
ledger relationship (above), narrative-only factual claims are
synthesis-contract violations — there IS a defined contract cost.
Mechanical enforcement requires T7 to deliver the narrative factual-
claim inventory and ledger completeness checker (§6.2). Benchmark runs
are blocked until T7 enforcement is operational (§6.2 benchmark-
execution prerequisite). The `ledger_coverage_rate` metric is
downstream of the inventory — it cannot be defined independently
(computing coverage requires enumerating narrative claims, which IS the
inventory).

**Aggregation rule (same as §3.4 verification derivation):**

A claim is `supported` in the benchmark sense when the verification
status derivation in §3.4 produces `status == "supported"`.

### 5.3 Audit chain

**Authority chain (two tiers, contingent on §3.9):**

**Tier 1 (scouted claims):** synthesis claim → claim ledger `[ref: N]` →
`claim_provenance_index[N]` → `record_indices` → evidence blocks in
transcript (claim_ref, disposition, citations) → post-containment tool
output in transcript. This chain is authoritative given transcript
fidelity (§3.9). Without the blocking external dependency resolved, the
chain degrades to "verifiable up to the evidence block."

**Tier 2 (not_scoutable claims):** synthesis claim → claim ledger
`[ref: N]` → `claim_provenance_index[N]` → `classification_trace`
(candidate_entity, failed_criterion). Chain terminates at classification.
The adjudicator independently evaluates the claim's truth value and the
classification's correctness. No mechanical audit beyond the
classification decision.

**Narrative-only claims (no ledger entry):** No provenance chain.
Synthesis-contract violation (§5.2 narrative-to-ledger relationship).
Benchmark runs blocked until T7 delivers mechanical enforcement (§6.2
benchmark-execution prerequisite). This gap is separate from G3 — it
concerns synthesis quality, not scouted provenance.

**Omission surface (mechanical diff, contingent on §3.9):**

For any evidence record, the full set of uncited matches is:

```text
uncited = {
    (path, line) for (path, line) in post_containment_tool_output
    if (path, line) not in record.citations
}
```

The harness MUST compute this diff **by default** for every evidence
record used in the synthesis. This is computable from two sources
already in the transcript: (1) post-containment tool output (all match
lines returned by Grep/Read, after §4.6 containment), (2) `CitationSpan`
entries in the evidence block (which lines the agent cited). No agent
self-reporting is needed.

**Per-tool omission relevance:** The omission surface is
shape-sensitive — a broad read inflates uncited lines, a narrow read
minimizes them. To prevent the agent from gaming diff cleanliness via
read strategy, tool outputs are classified by omission relevance:

| Tool | Omission-relevant output | Rationale |
|------|-------------------------|-----------|
| **Grep** | All match lines | Agent chose the query. Every match is a candidate the agent saw |
| **Read (line_range)** | All lines in requested range | Agent chose the scope. The range bounds the evidence surface |
| **Read (full file)** | **All lines in the file** | Agent chose to read the full file. Every line is omission-relevant |
| **Glob** | None (path list only) | No content to omit |

**Omission boundary is determined at read time, not citation time.**
The agent's read scope determines the omission surface. There is no
post-citation boundary shrinking — the agent cannot do a broad read,
cite a narrow favorable function, and have the omission surface
retroactively narrowed to the enclosing scope of cited lines. This
closes the shape-gaming exploit: a full-file read means the harness
diffs every line in the file against citations.

**Read-scope rule (normative):** Scout reads MUST be anchored to one of:
1. A prior query result (e.g., Read the function that Grep matched)
2. An entity span (e.g., Read lines 55-80 where the function is defined)
3. A justified whole-file inspection class:
   - Config files or short modules under 50 lines where entity scope ≈
     file scope
   - Presence/absence claims (e.g., "module X uses dependency
     injection") where the truth condition is file-level — the entire
     file is the evidence unit
   - Pattern or convention claims (e.g., "all handlers follow X
     pattern") where sampling a narrow range would be confirmation bias

Whole-file eligibility depends on file-level truth conditions, not on
whether the file path appears in the claim text. A path mention alone
does not justify a whole-file read — the claim's truth condition must
require file-level context.

Full-file reads without justification class `"whole_file"` in the
`read_anchor` field are a contract violation. The `read_anchor` field
(§4.4) records which class the agent claims. The adjudicator verifies:
a 2000-line module read with `read_anchor: "whole_file"` is auditable
misuse. The contract consequence is the omission surface: full-file
reads produce full-file diffs, creating strong incentive for targeted
reads.

**Under-reading finding (adjudicator, non-mechanical):** The
adjudicator flags under-reading when:
- The claim shape required broader context than the agent's read scope
- Contradictory evidence existed in the un-read portion of a file the
  agent chose to read narrowly

An under-reading finding is a **methodology finding**
(`finding_kind: under_reading`, `detection: judgment`) — it does not
change claim labels (`supported`/`unsupported`/`false` per
[benchmark.md:135](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
but appears in `adjudication.json` as a finding row keyed by
`inventory_claim_id`. This is an adjudicator judgment, not a mechanical
harness check — the harness can only diff what was actually read, not
what the agent failed to inspect. Methodology findings are recorded for
benchmark consumption; their effect on the pass rule (per-run
`methodology_finding_threshold` gate, condition 5) requires a T7
benchmark-contract amendment (§6.2). Before that amendment, findings
exist as structured audit data without mechanical pass/fail consequences.

**match_digest is a human convenience, not a gate.** `match_digest` is
a guide in the compressed evidence block, capped at 20 lines. On large
outputs (80+ matches), it truncates. The harness does NOT wait for
match_digest to signal uncited matches before computing the diff — it
computes the diff unconditionally. match_digest helps human reviewers
do quick triage but is never load-bearing for the audit.

**Why mechanical diff is stronger:** An agent cannot suppress
contradictory evidence from the diff — the tool returned it, it is in
the transcript, the harness sees it. The diff operates on the full
post-containment output regardless of agent-authored summaries.

**Reviewer workflow:**
1. Claim in synthesis → `claim_provenance_index` → record indices →
   evidence block
2. Harness-computed mechanical diff (always available, not gated)
3. Compare uncited match content against disposition (using per-tool
   relevance classification)
4. match_digest for quick human triage (convenience overlay)
5. Query coverage (§4.4): were both mandatory types included?
6. Containment verification (§4.6): all tool calls within allowed_roots?

**Optional enrichment:** T7 MAY construct `evidence.json` from the
transcript. This is a convenience, not provenance authority.

## 6. Explicit Non-Changes

| Surface | Why |
|---------|-----|
| Pipeline `<!-- pipeline-data -->` | `scout_count` = `len(evidence_log)`. **New field:** `claim_provenance_index` (§5.2) for claim→record join (replaces `evidence_map` from rev 10-11) |
| Synthesis artifact content | Narrative, inline citations, checkpoint (outcome-based, unchanged), claim ledger (`FACT:` lines with `[ref:]`), `<!-- pipeline-data -->` |
| T3 continuity registry | `set[claim_key]`. T4 builds parallel occurrence registry |
| T1 termination | Scope breach uses T1. T4 owns partial-round and pending marker |
| T5 mode | Direct tools. `agent_local` preserved |
| `ConsultEvidence` | Out of scope |
| Benchmark artifact set | No new required artifacts |
| Synthesis assembler `scout_outcomes` key | **Changed:** entries become `EvidenceRecord`s (§5.1). Declared migration |

**T2/T3/synthesis input changes (declared):**

| Change | Surface | Effect |
|--------|---------|--------|
| Forced-new reclassification (`reinforced`) | T2 counter computation, synthesis `validated_entry` trajectory | `reinforced` with dead referent → counted as `new` everywhere |
| Forced-new reclassification (`revised`) | T2 counter computation, synthesis `validated_entry` trajectory | `revised` with dead referent → counted as `new` everywhere |
| Merger for `new`/`revised` claims | None | Merger is invisible to T2/T3 — claim keeps original status |
| Claim-history surface | Synthesis `validated_entry` trajectory ([dialogue-synthesis-format.md:7](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)) | Reclassified claims appear as `new` in per-turn records and claim trajectory |
| `not_scoutable` verification status | Synthesis claim trajectory, evidence trajectory, claim ledger grammar | New terminal state not in current synthesis-format vocabulary. Requires format update (§6.2) |
| Claim ledger section | New `## Claim Ledger` in synthesis | Flat factual claim inventory with `FACT:` lines and `[ref: N]`. Separate from checkpoint (which stays outcome-based, unchanged) |
| Ledger completeness (MUST, enforcement deferred to T7) | Claim ledger | Factual narrative claims MUST have ledger entries with `[ref:]` (§5.2 narrative-to-ledger relationship). Synthesis-contract violation if missing. Not a G3 concern. Mechanical enforcement requires T7 inventory |
| `claim_provenance_index` | Pipeline `<!-- pipeline-data -->` | Replaces `evidence_map` (rev 10-11). Two variants: scouted (record_indices) and not_scoutable (ClassificationTrace) |

### 6.1 Helper-era migration

`agent_local` mode (T5) uses direct Glob/Grep/Read instead of
`execute_scout` / `process_turn`. The following helper-era surfaces are
severed and replaced by T4-local equivalents:

| Helper-era surface | Source | T4 replacement | Notes |
|-------------------|--------|---------------|-------|
| `evidence_wrapper` in follow-up | [codex-dialogue.md:368](../../packages/plugins/cross-model/agents/codex-dialogue.md), [codex-dialogue.md:414](../../packages/plugins/cross-model/agents/codex-dialogue.md) | Evidence block entry (entity, disposition, citations) | Follow-up references evidence record |
| `evidence_wrapper` in `scout_outcomes` | [codex-dialogue.md:144](../../packages/plugins/cross-model/agents/codex-dialogue.md) | `EvidenceRecord` (§5.1 projection) | Declared above |
| `read_result` / `grep_result` storage | [codex-dialogue.md:369](../../packages/plugins/cross-model/agents/codex-dialogue.md) | Raw tool output in transcript | Direct tools, no helper mediation |
| `execute_scout` call | [codex-dialogue.md:354](../../packages/plugins/cross-model/agents/codex-dialogue.md) | Direct Glob/Grep/Read (§4.4) | Per T5 `agent_local` mode |
| `scout_token` / `scout_option` | [context-injection-contract.md:673](../../packages/plugins/cross-model/references/context-injection-contract.md) | T4 target selection (§4.3) | Local priority ranking |
| `budget.scout_available` | [codex-dialogue.md:352](../../packages/plugins/cross-model/agents/codex-dialogue.md) | `evidence_count >= max_evidence` | Local budget check |
| `template_candidates` from `process_turn` | [codex-dialogue.md:348](../../packages/plugins/cross-model/agents/codex-dialogue.md) | T4 verification state (§4.3) | Local priority ranking |

This is the set of **scouting-related** surfaces that T4 replaces.
Non-scouting surfaces (e.g., `process_turn` for claim extraction,
`state_checkpoint` for ledger) are addressed by T5/T6, not T4.

### 6.2 External blockers for `agent_local` mode

T4's replacements (§6.1) define how scouting works in `agent_local`
mode. But `agent_local` runs also require T5's primary migration set to
land — without these changes, an `agent_local` run MUST be rejected as
invalid. **Benchmark-run behavior:** silent downgrade to
`server_assisted` is prohibited during benchmark execution — an
`agent_local` benchmark run that exercises the `server_assisted`
evidence path contaminates the comparison
([benchmark.md:52](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
The run MUST produce an explicit mode-mismatch failure artifact
recording the requested mode, the reason for rejection, and which T5
surface was missing. This is benchmark-run behavior; non-benchmark
contexts may define their own mode-fallback policy:

| Surface | Location | Required change | Owner |
|---------|----------|----------------|-------|
| Mode enum definition | [event_schema.py:137](../../packages/plugins/cross-model/scripts/event_schema.py) | Add `agent_local` to `VALID_MODES` | T5 |
| Conversation summary mode | [dialogue-synthesis-format.md:86](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) | Document `agent_local` in human-readable contract | T5 |
| Pipeline epilogue field | [dialogue-synthesis-format.md:144](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) | Add `agent_local` to JSON epilogue contract | T5 |
| Dialogue skill parser | [SKILL.md:435](../../packages/plugins/cross-model/skills/dialogue/SKILL.md) | Accept `agent_local` as valid parsed mode | T5 |
| Test enforcement | T5 migration set | Enum assertions, analytics fixtures, propagation tests | T5 |

**Dependency:** T4 defines the scouting contract. T5 defines the mode
contract. Both must land before `agent_local` runs produce valid data.
T4 does NOT claim completeness over T5's migration set — the two are
complementary.

**Transcript fidelity and transcript parser (§3.9):**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Benchmark run conditions | Add normative clause: "raw run transcript means untruncated post-containment tool output for every tool call" | T7 | [benchmark.md:95](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |
| Benchmark artifact contract | Specify parseable transcript format sufficient for mechanical diff extraction | T7 | [benchmark.md:101-112](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |
| Transcript parser | Implement harness-side tool for extracting tool inputs/outputs/evidence blocks from transcript | T7 | New harness component |
| Mechanical diff engine | Implement harness-side `post_containment_output - citations = uncited` computation | T7 | New harness component |

**Verification:** T4 implementation unblocked when the benchmark contract
text includes the normative clause AND a transcript format spec exists.

**Allowed-scope safety (§4.6):**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Secret handling policy | Define whether allowed-scope secrets require redaction in benchmark context | T7 | Benchmark contract amendment |
| Redaction/provenance interaction | If redaction required: specify how redacted output interacts with mechanical diff | T7 | §4.6 amendment or T7 harness spec |

**`claim_provenance_index` consumer (§5.2):**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Pipeline epilogue schema | Add `claim_provenance_index` field to epilogue contract with `claim_id`-keyed schema, two variants (scouted, not_scoutable) | T7 | [dialogue-synthesis-format.md:138-147](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| Epilogue parser | Accept and validate `claim_provenance_index` entries (both variants) | T7 | [emit_analytics.py](../../packages/plugins/cross-model/scripts/emit_analytics.py) |
| Schema validation | Add `claim_provenance_index` to `event_schema.py` field set | T7 | [event_schema.py](../../packages/plugins/cross-model/scripts/event_schema.py) |
| Claim ledger `[ref:]` parser | Extract integer `claim_id` annotations from claim ledger entries | T7 | New harness component |

**Synthesis-format contract updates (§5.2, §4.7):**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Claim ledger section | Add `## Claim Ledger` as a new synthesis section with `FACT:` lines, `[ref: N]`, and `[evidence:]` annotations | T7 | [dialogue-synthesis-format.md](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| Claim ledger rules | Document: one line = one atomic factual claim. Separate from checkpoint (outcome-based, unchanged) | T7 | [dialogue-synthesis-format.md](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| `not_scoutable` in claim trajectory | Add `not_scoutable` to the claim trajectory vocabulary (`new → reinforced/revised/conceded/not_scoutable`) | T7 | [dialogue-synthesis-format.md:16](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| `not_scoutable` in evidence trajectory | Note which claims were classified as not scoutable (no evidence entry) | T7 | [dialogue-synthesis-format.md:14](../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |

**Narrative factual-claim inventory (§5.2 ledger completeness — NOT a
G3 concern):**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Narrative-claim inventory | Implement harness-side tool that enumerates factual claims from narrative prose and compares to claim ledger entries | T7 | New harness component |
| Ledger completeness checker | Flag narrative factual claims that lack ledger `[ref:]` entries as synthesis completeness failures | T7 | New harness component |
| Ledger coverage metric | `ledger_coverage_rate` (`ledger_factual_claims / total_factual_claims`) — downstream of the inventory. Requires gate-affecting threshold to create contract cost for omission | T7 | [benchmark.md:157](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |

**NOT a G3 gate dependency.** Narrative-only claims are not "accepted
scout results" — G3 concerns scouted provenance, which T4 satisfies
internally (Tier 1 chain). Narrative-only factual claims are
synthesis-contract violations (§5.2 narrative-to-ledger relationship),
but the mechanical enforcement requires T7. The coverage metric cannot
be defined independently of the inventory — computing coverage requires
enumerating narrative claims, which IS the inventory problem.

**Benchmark-execution prerequisite (comprehensive):** Scored benchmark
runs and pass/fail comparisons MUST NOT proceed until ALL of the
following T7 dependencies are operational:

1. Narrative-claim inventory and ledger completeness checker
2. Methodology-finding format defined in `adjudication.json` schema
   (five finding kinds, detection-method field, `inventory_claim_id`
   key)
3. Mode-mismatch invalid-run schema defined in `runs.json` schema
4. `methodology_finding_threshold` defined in benchmark contract and
   recorded in `manifest.json`

The benchmark runner or manifest validator MUST reject scored runs when
any of (1)-(4) is unavailable. Without (1), `supported_claim_rate`
([benchmark.md:160](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
is computed against an incomplete claim population — the comparison is
contaminated, not merely degraded. Without (2)-(4), benchmark artifacts
are incomplete: `adjudication.json` and `runs.json` lack structures T4
requires, and the pass rule cannot evaluate condition 5.

Non-scoring runs (corpus calibration dry runs per §4.7, schema
shakedown) are permitted before these dependencies land — their results
MUST NOT be used for pass/fail comparisons.

This prerequisite is independent of G3 (which governs scouted provenance
retention). Benchmark-readiness requires BOTH: G3 accepted (scouted
provenance chain) AND all four T7 dependencies above operational.

**Benchmark-contract amendment dependencies:**

| Surface | Required change | Owner | Target |
|---------|----------------|-------|--------|
| Methodology finding format | Define finding row schema: `(run_id, inventory_claim_id, finding_kind, detection, ledger_claim_id?, detail)`. Five finding kinds: `under_reading` (judgment), `shape_inadequacy` (judgment), `misclassification` (judgment), `decomposition_skipped` (mechanical), `narrative_ledger_violation` (mechanical). Row keyed by `inventory_claim_id` from T7 adjudicator claim inventory. Optional `ledger_claim_id` cross-reference for finding kinds that have one. Findings do not change claim labels | T7 | [benchmark.md](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) / `adjudication.json` schema |
| Methodology finding consequence | Add `methodology_finding_threshold` to benchmark contract (versioned per [benchmark.md:202](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)). Value recorded in `manifest.json`. Add per-run methodology-gate check as pass-rule condition 5. A methodology-gate breach alone is not grounds for invalidation or rerun — the run is valid and scored, the breach fails condition 5. T7 defines initial threshold value | T7 | [benchmark.md](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) pass rule, config, `manifest.json` |
| Adjudication scope | Expand adjudicator authority to include candidate process artifacts (query traces, `ClassificationTrace`, claim ledger) alongside final synthesis. Methodology findings derive from these artifacts, not only from synthesis content | T7 | [benchmark.md](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) adjudication rules |
| Mode-mismatch failure artifact | Define destination for invalid-run mode-mismatch details (requested mode, missing T5 surface, rejection reason). Belongs in `runs.json` as invalid-run entry per [benchmark.md:98-99](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) | T7 | [benchmark.md](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) / `runs.json` schema |

## 7. Rejected Alternatives

### Revisions 1-3

Flat evidence (7.1), per-tool-call disposition (7.2), cross-model
scout_outcomes (7.3), full tool output (7.4), evidence in pipeline
epilogue (7.5), claim_key-only join (7.6), boolean backlog (7.7),
single-path ToolCallResult (7.8), lossy summary row (7.9), scout before
control (7.10), "later wins" (7.11), inferred T3 occurrence (7.12),
internal-only records (7.13), same-turn dedup (7.14), disposition from
citation subset (7.15), recency-only binding (7.16), tool result order
(7.17), agent-written evidence (7.18), unresolved-item scouting as
primary mechanism (7.19).

### 7.20 Per-tool citation caps (rev 4)

Rejected: Read=1 conflicts with polarity-preserving rule.

### 7.21 Only register `new` claims (rev 4)

Rejected: revised claims need registration for referential resolution.

### 7.22 Derive disposition from citations (rev 3-4)

Rejected: polarity-preserving rule and mechanical diff audit prevent
cherry-picking.

### 7.23 Snippet recovery reads during synthesis (rev 5)

Rejected: violates G3 single capture point.

### 7.24 Evidence export via synthesis epilogue (rev 5)

Rejected: contaminates scored synthesis.

### 7.25 Recency fallback for same-text collisions (rev 5)

Rejected: same-text same-key merger prevents orphaning.

### 7.26 Agent-authored `candidate_matches` as provenance (rev 6)

Rejected: agent self-report is not provenance. Mechanical diff (raw
output minus citations) provides the authoritative omission surface.

### 7.27 Unresolved-item scouting as secondary target type (rev 6)

Rejected: 4 critical incompatibilities (follow-up contract, synthesis
scoring, pipeline-data accounting, evidence trajectory).

### 7.28 Flat `max_attempts_per_claim = 1` (rev 7)

Rejected: too rigid. `conflicted` and `ambiguous` claims need a second
attempt — the evidence was real but inconclusive. `not_found` correctly
gets only one attempt. Graduated limit (§4.3) balances coverage with
resolution.

### 7.29 `revised` claims exempt from merger (rev 1-7)

Rejected: the "different text by definition" assumption is wrong.
Extractor errors produce duplicate revised claims; convergent revisions
across turns produce same-text revised claims. Without merger, these
create identical-text live collisions — the same class of problem
merger was designed to prevent. Extending merger to `revised` claims
closes the gap.

### 7.30 Single definition-query coverage rule (rev 7)

Rejected: too weak. An agent can satisfy it with one token-compliant
but low-value query and bias the rest of the round. Two mandatory types
(entity-definition AND falsification) cover both actual behavior and
claim negation. Not foolproof, but a higher bar for systematic bias.

### 7.31 `revised` claims exempt from forced-new reclassification (rev 8)

Rejected: creates the same dual semantic state that reclassification
fixes for `reinforced`. A `revised` claim with a dead referent gets a
new occurrence and new ClaimRef (identity = new) but stays `revised` for
T2 counters and synthesis `validated_entry` trajectory (semantics =
revised). One claim, two incompatible states. Extending reclassification
to `revised` eliminates the last dual-state case.

### 7.32 match_digest as escalation gate for mechanical diff (rev 8)

Rejected: reviewer workflow in rev 8 only computed the mechanical diff
when match_digest signaled uncited matches. This reintroduces trust in
the non-authoritative summary surface. A truncated or biased
match_digest suppresses escalation, and auditors skip the only real
omission test. The harness MUST compute the diff by default.

### 7.33 2-3 call round budget (rev 1-8)

Rejected: too tight for claims requiring grep-plus-read for each query
type. Forces shallow evidence — agents do one thin grep, one perfunctory
falsification query, then lock in premature dispositions. 2-5 call
budget (target 3, cap 5) gives room for meaningful evidence gathering
while preventing monopolization.

### 7.34 SHOULD for second-attempt query diversity (rev 8)

Rejected: `SHOULD` in §4.4 contradicted verification item 18 (which
treated difference as required). Reviewers cannot tell whether same-query
retries are invalid or merely discouraged. MUST with objective criteria
(at least one query text must differ) resolves the contradiction.

### 7.35 "Full helper-era migration enumeration" claim (rev 8)

Rejected: overstated readiness. T4 enumerates scouting-surface
replacements; T5's primary migration set (enum schema, synthesis format,
dialogue skill, tests) is a separate complementary set that must also
land. Claiming "full enumeration" when live surfaces still only accept
`server_assisted`/`manual_legacy` is misleading.

### 7.36 `not_scoutable` as prose-only `ambiguous` with reason field (rev 9)

Rejected: `VerificationEntry` had no `reason` field, target selection
still retried ordinary `ambiguous` claims, and no `EvidenceRecord` could
encode the classification. The "not_scoutable path" existed only in §4.7
prose. Wired as terminal verification status in rev 10: enters model
without scout round, excluded from target selection, objective
classification criteria, adjudicator audit.

### 7.37 `evidence_map` keyed by `claim_key` (rev 9)

Rejected: `claim_key` is not a unique synthesis-claim identifier.
Repeated, merged, or paraphrased claims share a key. One narrative
sentence can compress multiple keys. The harness cannot deterministically
recover which record supports which scored claim. Changed to `ClaimRef`-
keyed map (unique by construction) with claim ledger `[ref:]`
annotations providing the harness join point.

### 7.38 Abandoned rounds consume only claim-local budget (rev 9)

Rejected: `scout_attempts += 1` constrains per-claim retries but does
not affect `evidence_count` (the conversation-wide budget gate). Repeated
failed rounds could burn tool effort indefinitely. Added
`scout_budget_spent` counter with `max_scout_rounds` gate (§3.5).

### 7.39 Containment cited to benchmark tool-class restriction (rev 9)

Rejected: benchmark lines 93-94 only restrict tool classes (Glob/Grep/
Read), not scope roots. The actual immutable-scope contract is
`scope_envelope` in the consultation contract. "Harness bug" framing
dismissed containment failures when the benchmark still counts them as
safety violations. Reground in consultation contract; safety dependency
owned explicitly.

### 7.40 Blocker without ownership (rev 9 transcript fidelity)

Rejected: a blocker that names no owner, target document, or concrete
normative edits is an indefinite pause point. T5 blockers had owners and
file paths; transcript/parser blocker was only a sentence. Assigned to
T7 with specific target files and verification criteria.

### 7.41 Approximate content matching for free-text narrative claims (rev 10)

Rejected: the `[ref:]` join was deterministic for checkpoint claims but
free-text narrative claims fell back to approximate content matching.
The benchmark scores every factual claim in the final synthesis, not
just checkpoint lines. Replaced with claim ledger completeness rule
(§5.2): every factual narrative claim MUST have a claim ledger entry
with `[ref:]`. No approximate matching path exists. Enforcement gap
acknowledged; T7 blocker declared.

### 7.42 `not_scoutable` only for new extracted claims (rev 10)

Rejected: lifecycle only had a dedicated `not_scoutable` path for new
extracted claims. Revised claims, forced-new claims, and reintroductions
all entered at `unverified` regardless of scoutable classification.
Extended to ALL claim registration paths: revised (new occurrence),
forced-new, and reintroduction after concession.

### 7.43 `scout_budget_spent` incremented in lifecycle entries (rev 10)

Rejected: `scout_budget_spent` was incremented on "Evidence stored,"
"`not_found` stored," and "Pending round (abandoned)" AND described as
incrementing on round start. Double-counting: a completed round would
increment at 5b (start) and again in the lifecycle (completion).
Fixed: single increment point at step 5b. Lifecycle tracks claim-local
state only.

### 7.44 Checkpoint as sole scored factual surface (rev 12)

Rejected: moving benchmark scoring from the full synthesis to checkpoint
entries only would buy determinism by no longer scoring what the reader
sees. False repo-state assertions in narrative prose would become
effectively unscored. This creates an escape hatch — agents can slip
unsupported facts into narrative while maintaining a clean checkpoint.
The benchmark at
[benchmark.md:118-123](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)
explicitly scores the full synthesis. To make checkpoint-only scoring
defensible, narrative would need to be prohibited from introducing
independent factual claims — a larger design change than the provenance
gap warrants. Instead: keep full-synthesis scoring and declare T7
blocker for narrative factual-claim inventory.

**Rev 14-15 resolution:** The claim ledger (§5.2) provides the
dedicated inventory surface that makes the narrative prohibition
feasible without restricting the scored surface. Full-synthesis scoring
is preserved — the adjudicator still enumerates claims from the
complete synthesis. But the claim ledger is the canonical inventory:
narrative MUST NOT introduce independent factual claims without ledger
entries (§5.2 narrative-to-ledger relationship). This resolves the
original concern without the checkpoint-only scoring escape hatch.

### 7.45 Multi-ref checkpoint lines for claim compression (rev 12)

Rejected: allowing one checkpoint line with `[ref: 42,43,44]` to
compress multiple distinct claims collapses the claim inventory problem
into the checkpoint. One line with three refs is ambiguous: one atomic
claim with three supporting records, or three distinct claims bundled?
The benchmark scores distinct factual claims
([benchmark.md:123](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)),
not bundles. Fixed: one claim ledger line = one atomic claim. One claim
with multiple evidence records has one `claim_id` whose
`record_indices` list has multiple elements.

### 7.46 Overloading `evidence_map` with classification traces (rev 12)

Rejected: putting `record_indices: []` plus a `ClassificationTrace`
into `evidence_map` mixes evidence provenance with classification audit
in one structure. The entry type (`scouted` vs `not_scoutable`) would
have to be inferred from whether `record_indices` is empty — fragile
and semantically muddy. Fixed: `claim_provenance_index` with explicit
`type` field and two variants, each with their own fields.

### 7.47 Text-embedded `ClaimRef` as `[ref:]` join key (rev 10-11)

Rejected: `[ref: (3,compute_action behavior,0)]` embeds a normalized
`claim_key` in tuple-like text. T3 normalization (NFKC + casefold +
strip punctuation) does not guarantee absence of commas, brackets,
quotes, or parentheses in claim keys. Parsing requires ad hoc escaping
rules the note never defined. Claim keys containing structural
characters break the join or force collision handling. Fixed: `claim_id:
int` as opaque, parse-safe join key. `[ref: 42]` — integer parsing is
unambiguous. `ClaimRef` retained in provenance entries for human
readability.

### 7.48 Checkpoint completeness as MUST rule (rev 11)

Rejected: "every factual narrative claim MUST have a corresponding
checkpoint entry" is unenforceable without a narrative factual-claim
inventory — which requires semantic extraction, the same approximate
matching the rule claimed to eliminate. The rule relocates the problem
from "synthesis→record join" to "narrative→checkpoint completeness
check" without resolving it. Fixed: claim ledger completeness is MUST (§5.2), with mechanical
enforcement deferred to T7. T7 blocker declared for narrative
factual-claim inventory and completeness checker.

### 7.49 `NOT_SCOUTABLE` as checkpoint tag (rev 12)

Rejected: adding `NOT_SCOUTABLE` as a checkpoint tag alongside
`RESOLVED`, `UNRESOLVED`, `EMERGED` mixes two different axes. The
existing tags are outcome-based (what happened during the dialogue).
`not_scoutable` is evidence-state-based (whether scouting was possible).
A claim can be unresolved and not_scoutable simultaneously, making one-
tag-per-line semantics incoherent. Downstream cross-reference rules
(every RESOLVED must appear in Areas of Agreement, etc.) break when the
tag is an evidence state, not an outcome. Fixed: checkpoint tags remain
outcome-based. Evidence state encoded as `[evidence: not_scoutable]`
annotation — same structural pattern as `[basis:]` and `[confidence:]`.

### 7.50 Enclosing-scope heuristic for full-file read omission (rev 12)

Rejected: using "enclosing scope of cited lines" as the omission
boundary for full-file reads allows a shape-gaming exploit. An agent
does a broad read, cites a narrow favorable function, and the post-hoc
enclosing-scope boundary erases contradictory lines elsewhere in the
file from the omission surface. The boundary is determined after
citation selection — the agent controls it. Fixed: full-file reads
get full-file omission surface. Boundary is determined at read time
(the scope the agent requested), not at citation time.

### 7.51 Narrative provenance gap as "bounded" without benchmark penalty (rev 12)

Rejected: the rev 12 narrative-claim gap story claimed the gap was
"bounded by checkpoint completeness incentives" and that "missing
checkpoint entries are visible to the adjudicator." But the benchmark
defines `supported_claim_rate`, `false_claim_count`, citations, and
safety — no checkpoint-completeness metric. A gap that is visible but
not penalized is not bounded. Rev 13 made it a hard G3 gate; rev 14
separated it from G3 entirely (see 7.53).

### 7.52 Checkpoint as dual-purpose outcome summary and provenance ledger (rev 12-13)

Rejected: the checkpoint was asked to serve two incompatible roles —
dialogue outcome summary (RESOLVED/UNRESOLVED/EMERGED) and atomic
factual claim inventory (one line per repo fact with `[ref:]`). Many
repo facts in a synthesis are supporting observations, not dialogue
outcomes — they don't fit outcome tags. Agents either jam facts into
`RESOLVED` inappropriately or leave them in narrative prose with no
provenance. Fixed: separate claim ledger (`## Claim Ledger`) with
`FACT:` lines. Checkpoint stays outcome-based, unchanged from the
synthesis-format contract.

### 7.53 Narrative coverage gap as G3 blocker (rev 13)

Rejected: rev 13 made the narrative provenance gap a hard G3 blocker.
But G3's invariant
([risk-register:35](../reviews/2026-04-01-t04-convergence-loop-risk-register.md))
is "accepted scout results retained as structured provenance." Narrative-
only claims are not accepted scout results — there are no scout results
to retain. Stretching G3 to cover unscouted claims is gate-definition
drift. Fixed: G3 satisfied by T4's Tier 1 scouted chain. Narrative
coverage is a separate synthesis quality concern for T7, not a gate.

### 7.54 `checkpoint_coverage_rate` as independent G3 option (rev 13)

Rejected: rev 13 offered `checkpoint_coverage_rate` as an alternative to
the T7 narrative-claim inventory. But the metric computes
`checkpoint_factual_claims / total_factual_claims`, which requires
enumerating `total_factual_claims` — which IS the inventory problem.
The metric depends on the same machinery as the checker. It is a
downstream output, not an independent mechanism. Fixed: single
mechanism (T7 inventory). Coverage metric is downstream. Not a gate.

### 7.55 Mandatory runtime decomposition of `not_scoutable` claims (rev 15)

Rejected: rev 15 required agents to decompose `not_scoutable` claims
into scoutable subclaims and register them as separate pipeline
entries. But T2/T3 define two claim sources (`extracted`,
`minimum_fallback`) — decomposed subclaims have no defined
`claim_source`, no counter semantics (T2 §5.3 filters on
`claim_source == "extracted"`), and no continuity behavior (T3 §5.2
registry filters on `claim_source == "extracted"`). The system being
scored would no longer be the system T2/T3 describe. Fixed:
decomposition is an audit-side analysis. Agent records decomposition
considerations in `ClassificationTrace`. Adjudicator evaluates
adequacy as methodology finding. No new pipeline entries created.

### 7.56 Non-binding methodology findings (rev 16)

Rejected: rev 16 defined methodology findings in `adjudication.json`
but explicitly excluded them from claim labels and pass/fail conditions.
The benchmark pass rule consumed only claim labels, convergence, and
safety. A candidate could accumulate many methodology findings and still
pass, making the audit surface non-load-bearing. Fixed: per-run
`methodology_finding_threshold` gate added as pass-rule condition 5.
Finding artifact defined as one row per `(run_id, inventory_claim_id,
finding_kind)` with detection-method field.

### 7.57 SHOULD decomposition with implicit MUST semantics (rev 16)

Rejected: rev 16 said the agent SHOULD consider decomposition, but the
trace definition treated `decomposition_attempted: false` as a finding
for audit. No clear cases where skipping was acceptable — the practical
rule behaved like MUST while the formal keyword said SHOULD. Reviewers
could not tell whether skipped decomposition was acceptable discretion
or a defect. Fixed: decomposition analysis is MUST, no exceptions.
`decomposition_attempted: false` is always a `decomposition_skipped`
methodology finding. The valid "nothing to decompose" path is
`decomposition_attempted: true, subclaims_considered: [],
residual_reason` populated — the agent must perform the check, not skip
it.

### 7.58 Comparative methodology-finding metric (rev 17 proposal)

Rejected: initial rev 17 proposal used `candidate ≤ baseline`
comparison for `methodology_finding_count`. But none of the five
finding kinds are symmetric — the baseline system produces no scouting
traces, `ClassificationTrace`, or claim ledger. The baseline count
would be zero or undefined for all finding kinds, making the comparison
structurally unsound. Fixed: candidate-only per-run threshold gate. The
threshold is a benchmark configuration parameter pinned in the versioned
contract, not a comparative metric.

### 7.59 Ledger `claim_id` as methodology finding row key (rev 17 proposal)

Rejected: `narrative_ledger_violation` findings identify claims present
in synthesis but absent from ledger — by definition, these claims have
no ledger `claim_id`. Fixed: finding rows keyed by `inventory_claim_id`
from T7 adjudicator claim inventory. Optional `ledger_claim_id`
cross-reference for finding kinds that have one.

### 7.60 Methodology-gate breach as invalid run (rev 17 clarification)

Rejected: treating methodology-gate failures as invalid runs would
allow rerunning until findings fall below threshold, defeating the gate.
Invalid runs are reserved for run-condition violations
([benchmark.md:98](../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
Fixed: methodology-gate breach alone is not grounds for invalidation or
rerun. The run is valid and scored; the breach fails pass-rule
condition 5.

### 7.61 Criterion-1 exception for decomposition (rev 17 proposal)

Rejected: initial rev 17 proposal exempted decomposition when
`failed_criterion == 1` (no entity fitting the grammar). But
criterion-1 failure for the whole claim does not imply no entity-bearing
subclaims exist — decomposition is precisely the step that asks whether
subclaims could have identifiable entities. Exempting criterion-1
failures gives the most abstract claims the least decomposition
pressure, which is backward. Fixed: decomposition check is always MUST.
The trace-based outcome `decomposition_attempted: true,
subclaims_considered: []` is the legitimate "nothing to decompose" path,
not a criterion-based exemption.

## 8. Verification Items

1. **Loop order:** No record for turns where `action == "conclude"`.

2. **Scout skip:** Conclude, evidence budget exhausted, effort budget
   exhausted, or all claims at skip priority.

3. **Occurrence registry — merger for `new` AND `revised`:** Both types
   checked against live occurrences. Same key + same normalized text +
   live → merge. Conceded occurrences excluded.

4. **Concession exception:** Conceded occurrences excluded from merger
   AND resolution. Reintroduction → new occurrence.

5. **No counter impact from merger:** Merged claims keep original status
   for T2/T3 (`new` stays `new`, `revised` stays `revised`).

6. **Forced-new reclassification:** Both `reinforced` AND `revised`
   with dead referent → reclassified to `new` before ANY consumer.
   T2 counters, T3 registry, and synthesis `validated_entry` trajectory
   all see `new`.

7. **Two-phase processing:** Phase 1 (concessions) → Phase 1.5
   (reclassification) → Phase 2 (registrations). Same-turn concession
   + reintroduction → deterministic fresh identity.

8. **ClaimRef uniqueness:** `(turn, key, occurrence_index)` unique.

9. **Referent resolution — dead exclusion:** Filters to live candidates.
   No live → routed to Phase 1.5 reclassification.

10. **Evidence record structure:** `claim_text` non-empty. `entity`
    follows grammar (§3.3, including `×` for relational claims per §4.7).
    Steps 2-5. Each citation has valid `source_step_index`. Total
    citations ≤ 5, Glob = 0. `match_digest` capped at 20 lines.

11. **Query coverage:** At least one `definition` and one `falsification`
    query per round. `query_type` field classifies each step.

12. **Disposition from full output:** Mixed evidence → `conflicted`.

13. **Polarity preservation:** `conflicted` cites both polarities.

14. **Mechanical omission diff:** Post-containment output minus
    citations = uncited lines. Harness computes by default for every
    evidence record. match_digest is convenience, not gate.

15. **Verification derivation:** Same rule everywhere.

16. **Synthesis aggregation:** `supported` = `status == "supported"`.

17. **Graduated attempt limit:** `not_found` → skip after 1.
    `ambiguous`/`conflicted` → skip after 2. Terminal states → skip.

18. **Second-attempt queries:** MUST differ from first attempt. At least
    one query text must be different (objective criterion).

19. **Compression accounting:** 6-turn tier 2, 8-turn tier 3.

20. **No snippet recovery:** Tier 3 uses `path:line_range`. No reads
    during synthesis.

21. **Evidence NOT in synthesis:** No machine blocks.

22. **Evidence in transcript:** Atomic round commit (step 5e).

23. **Pending round on interruption:** Target, steps, reason. No
    fabricated disposition.

24. **Error path independence:** No synthesis dependency.

25. **Crash = invalid run.** Rerun.

26. **Audit chain transcript-complete (given §3.9).** No artifact
    beyond synthesis + transcript needed. Authority conditional on
    transcript fidelity.

27. **Scope breach:** Per-call counting, pending marker.

28. **Pipeline-data.** `scout_count` unchanged. New field:
    `claim_provenance_index` for claim→record join (§5.2).

29. **Claim-only scouting.** One-turn delay accepted (§7.27).

30. **Helper-era migration.** Scouting surfaces enumerated in §6.1.
    External blockers (T5 migration set) declared in §6.2.

31. **T2/T3/synthesis input changes declared.** Forced-new
    reclassification for both `reinforced` and `revised`. Claim-history
    surface (`validated_entry` trajectory) included.

32. **Transcript fidelity — blocking external dependency.** Benchmark
    contract must normatively specify untruncated output and parseable
    format. T4 implementation blocked until resolved. Degradation path
    declared.

33. **Revised-claim merger.** Convergent revisions merge. No
    identical-text live collisions.

34. **`scout_outcomes` projection.** `evidence_log[i].turn == N`.
    `EvidenceRecord` replaces `evidence_wrapper`.

35. **Direct-tool containment (§4.6).** Pre-execution confinement
    grounded in `scope_envelope` from consultation contract. Transcript
    captures post-containment output. Containment failure = safety
    violation on the run. Allowed-scope safety declared as external
    blocker owned by T7.

36. **Claim-class scope (§4.7).** Scoutable, relational-scoutable,
    `not_scoutable`. `not_scoutable` is terminal verification status
    (§3.4). Applies to ALL claim registration paths: new, revised,
    forced-new, reintroduction. Enters model without scout round,
    excluded from target selection. Objective classification criteria
    (3 conditions). Adjudicator audits all classifications.

37. **Synthesis→record join.** `claim_provenance_index` in pipeline-data
    keyed by `claim_id` (integer). Two variants: scouted
    (record_indices) and not_scoutable (ClassificationTrace). Claim
    ledger carries `[ref: N]` annotations with integer `claim_id`.
    Harness join: claim ledger → claim_id → provenance entry → record
    indices (Tier 1) or classification trace (Tier 2).

38. **Abandoned-round accounting.** Any round executing at least one
    tool call increments `scout_attempts` (claim-local). 
    `scout_budget_spent` was already incremented at step 5b.

39. **Round budget.** 2-5 tool calls per round. Minimum 2 (mandatory
    types). Hard cap 5.

40. **External blockers declared (§6.2).** T5 migration set named
    with owners. Transcript fidelity named with owner (T7), target
    files, and verification criteria. `claim_provenance_index` consumer
    named. Allowed-scope safety named. Narrative factual-claim inventory
    and completeness checker named as T7 blocker.

41. **Authority claims conditional.** "Authoritative" language
    throughout is contingent on transcript fidelity (§3.9). Without
    it, audit degrades to evidence-block level.

42. **Two budget surfaces (§3.5).** Evidence budget:
    `evidence_count >= max_evidence`. Effort budget:
    `scout_budget_spent >= max_scout_rounds`. Both gate scouting.
    `scout_budget_spent` increments exactly once per round at step 5b
    (not in lifecycle entries). `scout_count` in pipeline-data maps to
    evidence budget only; effort budget is internal.

43. **`not_scoutable` synthesis policy.** `not_scoutable` factual
    claims MUST appear in scored synthesis. Agent cannot suppress
    claims via classification. Adjudicator scores independently.

44. **Containment source.** `scope_envelope` from consultation
    contract (immutable, set at delegation time). NOT benchmark
    tool-class restriction.

45. **Ledger completeness (§5.2).** MUST — synthesis-contract violation
    if missing. Mechanical enforcement deferred to T7 narrative-claim
    inventory. Benchmark runs blocked until T7 enforcement operational
    (§6.2). NOT a G3 concern (G3 is about scouted provenance).

46. **`not_scoutable` across all registration paths.** New, revised,
    forced-new, and reintroduction all have scoutable/not-scoutable
    split in lifecycle. No generic `unverified` entry for claims that
    satisfy not-scoutable criteria.

47. **Single increment point for `scout_budget_spent`.** Step 5b only.
    NOT in lifecycle entries. Lifecycle tracks claim-local state only.

48. **Synthesis-format contract updates declared (§6.2).** Claim ledger
    grammar (`[ref: N]`, `[evidence:]`), atomic line rule,
    `not_scoutable` in claim trajectory and evidence trajectory — all
    named as external blockers with owner and target.

49. **`claim_id` allocation deterministic (§3.4).** Allocated after
    Phase 1.5 reclassification and Phase 2 merger resolution. Merged
    claims reuse existing `claim_id`. Reintroductions allocate new.
    Same dialogue transcript + same processing order → same `claim_id`s.

50. **Two provenance tiers (§5.2).** Scouted: `claim_id` →
    `record_indices` → transcript. Not_scoutable: `claim_id` →
    `ClassificationTrace`. Deterministic-audit guarantee scoped to
    Tier 1 only.

51. **`claim_provenance_index` replaces `evidence_map`.** Keyed by
    `claim_id` (integer). Dense JSON array, `claim_id == index`
    invariant. Two explicit variants. No overloading of evidence
    structure with classification data. All allocated IDs persist.

52. **Atomic claim ledger lines.** One `FACT:` line = one atomic
    factual claim. One `[ref: N]` per line. No claim compression.

53. **Parse-safe `[ref:]` annotation.** `[ref: N]` where N is integer
    `claim_id`. No embedded claim text. No escaping rules needed.

54. **Per-tool omission relevance (§5.3).** Grep: all match lines.
    Read (line_range): all requested lines. Read (full file): **all
    lines in the file** (no post-citation shrinking). Glob: none.

55. **Read-scope rule (§5.3, normative).** Scout reads anchored to
    query result, entity span, or justified whole-file class
    (file-level truth conditions, not path mention). Under-reading
    finding: methodology finding when claim shape required broader
    context (adjudicator, non-mechanical).
    `read_anchor` field in ScoutStep records justification.

56. **Claim-shape adequacy (§4.4, normative).** Query-type quota
    (1 definition + 1 falsification) is necessary but not sufficient.
    Relational/multi-file claims require query set matching actual claim
    structure. Shape-inadequacy finding is a methodology finding.

57. **Structured non-authoritative audit fields.** ScoutStep:
    `expected_contradiction_target`, `read_anchor`. ClassificationTrace:
    `candidate_entity`, `failed_criterion`, `decomposition_attempted`,
    `subclaims_considered`, `residual_reason`. All explicitly
    non-authoritative — agent explanation, not proof.

58. **Decomposition analysis (§4.7, MUST).** Agent MUST perform
    decomposition check before `not_scoutable` classification — no
    exceptions. Records analysis in ClassificationTrace.
    `decomposition_attempted: false` is always a `decomposition_skipped`
    methodology finding. `decomposition_attempted: true` with empty
    `subclaims_considered` is valid if `residual_reason` is populated.
    Agent MUST NOT register decomposed subclaims (T2/T3 pipeline
    boundary — no defined `claim_source` or counter semantics).
    Adjudicator audits decomposition adequacy as methodology finding.

59. **Corpus calibration (§4.7).** `not_scoutable` rate validated
    against benchmark corpus via dry run. Report by task ID. Tighten
    criteria if material fraction unprovenanced.

60. **Narrative-claim enforcement (§5.2, §6.2).** Every benchmark-
    scored factual claim MUST have a ledger entry. Narrative-only
    factual claims are synthesis-contract violations. Benchmark runs
    blocked until T7 enforcement operational. NOT a G3 gate.

61. **Checkpoint taxonomy outcome-based (§5.2).** Tags: RESOLVED,
    UNRESOLVED, EMERGED. Evidence state (`not_scoutable`) is
    `[evidence:]` annotation, not a tag. Axes are orthogonal.

62. **`claim_provenance_index` wire format canonical (§5.2).** Dense
    JSON array. `claim_id == index` invariant. Length == `next_claim_id`.
    No sparse IDs. Conceded claims persist.

63. **Full-file read omission = full file (§5.3).** No post-citation
    enclosing-scope shrinking. Boundary determined at read time.
    Closes shape-gaming exploit.

64. **Canonical intra-phase ordering (§3.1.2).** `(claim_key, status)`
    ascending sort before Phase 1 and Phase 2. Makes `claim_id`
    sequence deterministic from text content.

65. **G3 satisfied by Tier 1 scouted provenance.** G3 invariant:
    "accepted scout results retained as structured provenance." T4's
    EvidenceRecord → claim_provenance_index → [ref:] → transcript
    satisfies this. Narrative coverage is NOT G3.

66. **Claim ledger separate from checkpoint.** Checkpoint: outcome
    summary (RESOLVED/UNRESOLVED/EMERGED, unchanged). Claim ledger:
    atomic fact inventory (FACT: lines with [ref:]). Different
    surfaces, different grammars, different purposes.

67. **Coverage metric downstream of inventory.** `ledger_coverage_rate`
    cannot be defined independently — computing coverage requires
    enumerating narrative claims, which IS the inventory problem.
    Single mechanism: T7 delivers inventory; metric is output.

68. **Methodology findings (§4.4, §4.7, §5.2, §5.3).** Five finding
    kinds: `under_reading` (judgment), `shape_inadequacy` (judgment),
    `misclassification` (judgment), `decomposition_skipped` (mechanical),
    `narrative_ledger_violation` (mechanical). Finding rows in
    `adjudication.json` keyed by `inventory_claim_id` (T7 adjudicator
    inventory, not ledger `claim_id`). Do not change claim labels.
    Per-run `methodology_finding_threshold` gate is pass-rule condition
    5. Threshold pinned in versioned benchmark contract, recorded in
    `manifest.json`. Threshold breach is a valid scored run that fails
    condition 5 — not an invalid run, not grounds alone for rerun.
    Format and threshold are T7 benchmark-contract dependencies (§6.2).

69. **Mode-mismatch failure artifact (§6.2).** `agent_local` benchmark
    run with missing T5 surfaces produces invalid-run entry in
    `runs.json`. Scoped to benchmark behavior. Artifact schema is T7
    benchmark-contract dependency (§6.2).

70. **Benchmark-execution prerequisite (§6.2).** Scored runs blocked
    until T7 delivers ALL: narrative-claim inventory, ledger
    completeness checker, methodology-finding schema in
    `adjudication.json`, mode-mismatch schema in `runs.json`, and
    `methodology_finding_threshold` in benchmark contract.
    Runner/manifest validator enforces. Calibration dry runs permitted
    but MUST NOT be used for pass/fail comparisons. Independent of G3.
