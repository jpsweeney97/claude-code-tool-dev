---
module: foundations
status: active
normative: true
authority: foundation
---

# Foundations

Core design decisions, rationale, and cross-cutting architectural constraints
for the T4 scouting and evidence provenance contract.

## Monolith Revision History

The following table summarizes the evolution of the monolithic design document
through 21 revisions and 6 hostile review rounds. Full revision entries are
preserved in the
[archived monolith](../archive/2026-04-02-t04-t4-scouting-position-and-evidence-provenance.md).
Future changes are tracked at the file level via git history.

| Rev | Key Theme |
|-----|-----------|
| 1 | Initial draft |
| 2 | Loop order, discovery/citation separation, ClaimRef, verification model |
| 3 | T4-owned occurrence registry, unified semantics, run artifacts |
| 4 | Occurrence index, record-level conflicted, match_digest, canonical sort |
| 5 | Revised claims as occurrences, citation cap, evidence export, disposition rubric |
| 6 | Evidence removed from synthesis, same-text merger, transcript fidelity spec |
| 7 | Unresolved-item scouting removed, per-claim attempt limit, query coverage, pending rounds |
| 8 | Forced-new reclassification, omission as mechanical diff, mandatory query types, migration enumeration |
| 9 | Dead-referent reclassification extended, containment contract, claim-class scope, budget accounting |
| 10 | not_scoutable as terminal status, scope_envelope grounding, transcript fidelity owner assigned |
| 11 | Checkpoint completeness, not_scoutable propagation, budget accounting fix |
| 12 | claim_id as join key, two-tier provenance, atomic line rule, read-scope rule, audit fields |
| 13 | G3 gate condition, checkpoint grammar, wire format canonical, full-file read scope |
| 14 | Claim ledger separated from checkpoint, G3 decoupled from narrative coverage |
| 15 | Narrative-to-ledger relationship, decomposition obligation, corpus calibration, claim-shape adequacy |
| 16 | Decomposition converted to audit-side, methodology findings, mode-mismatch artifact |
| 17 | Methodology finding threshold gate (pass-rule condition 5), adjudication scope amendment |
| 18 | Methodology authority unified, safety-leak taxonomy, ClassificationTrace invariants |
| 19 | Scope_envelope authority downgrade, scope_root derivation, max_evidence parameter, 7-item prerequisites |
| 20 | Cross-surface integration, scope_root_rationale removed, justification prohibition |
| 21 | Parser/diff prerequisite (item 8), derived proof surface, graduated readiness, non-scoring classification, runner enforcement unified |

## Design Decisions

Thirteen locked design decisions. Each carries a stable requirement ID.

### <a id="t4-f-01"></a>T4-F-01: Control Before Scouting

Control decision before scouting. Scouting only on live turns.

### <a id="t4-f-02"></a>T4-F-02: Evidence Records With Source Linkage

Evidence records separate discovery steps from citation spans with
`source_step_index` linkage. Steps carry `match_digest` as
compressed-block guide.

### <a id="t4-f-03"></a>T4-F-03: T4-Owned Occurrence Registry

T4-owned occurrence registry tracks claim introductions for `new` and
`revised` claims. Both subject to same-text merger against live
occurrences. Dead-referent claims reclassified to `new` for ALL consumers
(both `reinforced` and `revised`). No claims discarded — all survive to
T2/T3 counters.

### <a id="t4-f-04"></a>T4-F-04: Disposition From Full Output

Disposition assessed from full tool output. Citations illustrate,
polarity-preserving. Per-round total citation cap of 5; Glob=0 is the
only per-tool hard constraint.

### <a id="t4-f-05"></a>T4-F-05: Record-Level Conflicted Disposition

Record-level `conflicted` disposition for mixed-polarity rounds.

### <a id="t4-f-06"></a>T4-F-06: One Verification Rule

One verification/synthesis rule. `conflicted` expands to both `supports`
and `contradicts` in all contexts.

### <a id="t4-f-07"></a>T4-F-07: Compression-Resistant Evidence Block

Compression-resistant evidence block within 2500ch budget. Tiered
compression drops snippets at tier 3 — no recovery reads. Single capture
point is absolute.

### <a id="t4-f-08"></a>T4-F-08: Evidence In Transcript

Evidence persists via run transcript, not synthesis artifact. Audit chain
is transcript-complete. Omission surface is the mechanical diff of raw
tool output minus citations — authoritative given transcript fidelity
([T4-F-13](#t4-f-13)). Harness computes this diff by default.

### <a id="t4-f-09"></a>T4-F-09: Claim-Only Scouting With Graduated Limits

Scouting targets claims only. Per-claim attempt limit: 1 for `not_found`,
2 for `conflicted`/`ambiguous`. Abandoned rounds consume both claim-local
and conversation-wide budget (`scout_budget_spent`).

### <a id="t4-f-10"></a>T4-F-10: Two Mandatory Query Types

Two mandatory scout query types: entity-definition AND falsification.
Second attempts MUST use different queries (objective criteria). Round
budget: 2-5 tool calls.

### <a id="t4-f-11"></a>T4-F-11: Direct-Tool Containment Contract

Direct-tool containment contract
([containment](containment.md)): pre-execution confinement,
post-containment capture in transcript. "Raw" means unprocessed by the
agent, not unfiltered by the harness.

### <a id="t4-f-12"></a>T4-F-12: Synthesis-Record Join Via Provenance Index

Synthesis→record join via `claim_provenance_index` in
`<!-- pipeline-data -->` keyed by `claim_id`
([T4-PR-02](provenance-and-audit.md#t4-pr-02)). Two provenance tiers:
scouted (`record_indices`, full mechanical chain) and not_scoutable
(`ClassificationTrace`, classification provenance only). Separate claim
ledger section (`## Claim Ledger`) carries `FACT:` lines with `[ref: N]`
annotations ([T4-PR-05](provenance-and-audit.md#t4-pr-05)). Checkpoint
stays outcome-based (unchanged). Atomic ledger lines (one fact per line).
Claim-class scope defined
([scouting-behavior: claim classification](scouting-behavior.md#t4-sb-05)):
scoutable, relational-scoutable, and `not_scoutable` as terminal
verification status with objective classification criteria, structured
`ClassificationTrace`, and adjudicator audit.

## Rationale

Design justification for the locked decisions above. Each heading
corresponds to one or more decisions.

### Control Before Scouting

Dead turns must not scout
([codex-dialogue.md:346](../../../packages/plugins/cross-model/agents/codex-dialogue.md)).

### T3 Does Not Preserve Occurrence Identity

T4 builds a parallel registry without reopening T3
([T3:144-148](../2026-04-02-t04-t3-deterministic-referential-continuity.md)).

### Revised Claims Need New Occurrences

Revised claims get new `ClaimRef`s
([state-model: verification state](state-model.md#t4-sm-06)).
If they are not registered, later referential claims cannot resolve to them.

### Same-Text Merger Applies to Both New and Revised Claims

The assumption that revised claims always have different text ("different
text by definition") is wrong. Extractor errors can emit duplicate revised
claims in one turn, and separate revisions across turns can converge to
the same normalized text. Without merger, these create multiple live
occurrences with identical text under the same key — exactly the
collision class the design eliminated for `new` claims. Extending merger
to `revised` claims closes this gap. A `revised` claim that produces the
same normalized text as a live occurrence is not actually a new truth
condition — it is convergent re-expression. Merger is the correct response.

### Concession Exception

Conceded occurrences remain in the registry for evidence history but are
excluded from both merger candidacy and referent resolution.
Reintroduction after concession always creates a fresh identity.

### Forced-New Resurrection

When a referential claim's referent is dead (all occurrences conceded),
T4 cannot bind it. The claim is reclassified to `status = "new"` and
`claim_source = "extracted"` before T2/T3 processing. This applies to
BOTH `reinforced` AND `revised` claims with dead referents. A `revised`
claim whose referent no longer exists is not revising anything — it is
functionally a fresh assertion. Without reclassification, the claim would
be "new" for identity but "revised" for T2 counters and the synthesis
`validated_entry` trajectory — the same dual semantic state that rev 8
fixed for `reinforced`. T2/T3 and the claim-history surface all see a
`new` claim. This IS a T2/T3 input change (declared in
[boundaries](boundaries.md)).

### Two-Phase Layer-2 Processing

Within a single turn, a claim can be conceded AND a new claim with the
same key introduced. Phase 1 (status changes) runs before Phase 2
(registrations with merger checks). This makes identity deterministic
regardless of claim ordering in the extractor output.

### Per-Round Citation Cap

A `Read` step can expose both supporting and contradicting passages.
Per-tool caps conflict with the polarity-preserving rule. A per-round
total of 5 with Glob=0 resolves this.

### Disposition From Full Output

Capped citation selection creates a cherry-pick path if disposition is
derived only from the selected subset.

### No Snippet Recovery Reads

Tier 3 preserves `path:line_range`. A second evidence-gathering phase
during synthesis violates G3's single fixed capture point.

### Evidence Not In Synthesis

The benchmark scores the final synthesis. Embedded evidence data
contaminates scoring and creates safety risk. Evidence persists through
the transcript.

### Omission Surface Is Mechanical

`match_digest` is a compressed-block guide (capped at 20 lines). The
authority for cherry-pick detection is the mechanical diff:
post-containment tool output (all match lines, in transcript) minus
citations (agent-selected, in evidence record)
([T4-PR-11](provenance-and-audit.md#t4-pr-11)). This diff is computable
by the harness without relying on agent self-reporting. On large outputs
where `match_digest` is truncated, the mechanical diff catches everything.
The harness MUST compute this diff by default for every evidence record —
match_digest is a human convenience overlay, never a gate for escalation.
The authority claim is contingent on transcript fidelity
([T4-F-13](#t4-f-13)): if the benchmark contract does not normatively
require untruncated tool output, the diff degrades to "verifiable up to
the evidence block."

### Graduated Attempt Limit

`not_found` claims get one attempt — there is nothing to find and
retrying wastes budget. `conflicted` and `ambiguous` claims get two
attempts — the evidence was real but inconclusive. A second scout with a
different query approach may clarify. After the limit, claims are
deprioritized.

### Two Mandatory Query Types

Entity-definition (what it IS) plus falsification (what would contradict
the claim). Together these ensure the scout output covers both actual
entity behavior and the specific negation of the claim's assertion. This
is stronger than a single definition-query rule and auditable via `query`
fields. Not foolproof (an agent can craft weak queries), but raises the
bar for systematic bias.

### Claim-Only Scouting

Rev 6 attempted unresolved-item scouting. Review showed 4 critical
incompatibilities
([rejected-alternatives: 7.27](rejected-alternatives.md#727-unresolved-item-scouting-as-secondary-target-type)).
One-turn delay accepted with structural justification.

### Audit Chain Is Transcript-Complete

The authority chain requires only the synthesis and transcript — both
already required by the benchmark spec
([benchmark.md:95-96](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md),
[benchmark.md:107-108](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
Authority contingent on transcript fidelity ([T4-F-13](#t4-f-13)).

### Helper-Era Scouting Surfaces Enumerated

`agent_local` mode (T5) severs helper-era surfaces.
[Boundaries: helper-era migration](boundaries.md) enumerates every
T4-replaced scouting surface. T5's primary migration set is declared as
an external blocker
([T4-BR-01](benchmark-readiness.md#t4-br-01)).

### Transcript Fidelity Is a Prerequisite

T4 interprets "raw run transcript" as untruncated tool output per call.
If this interpretation is wrong, the audit chain degrades from "fully
verifiable" to "verifiable up to the evidence block." This is declared as
a prerequisite, not a follow-up clarification.

## <a id="t4-f-13"></a>T4-F-13: Transcript Fidelity Specification

**BLOCKING EXTERNAL DEPENDENCY.** The benchmark contract MUST normatively
specify untruncated tool output when it requires "raw run transcript"
([benchmark.md:95-96](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
T4's evidence provenance — specifically the mechanical omission diff
([T4-PR-11](provenance-and-audit.md#t4-pr-11)), query coverage audit
([scouting-behavior: query coverage](scouting-behavior.md#t4-sb-04)),
and containment verification
([containment](containment.md)) — depends on this
interpretation. This dependency resolves in two layers:

**(a) v1 scored-benchmark layer** — normative clause plus transcript
retention sufficient for human recovery of tool inputs, outputs, and
scope choices. This is the transcript floor required by the narrowed
v1 benchmark gate in
([T4-BR-07](benchmark-readiness.md#t4-br-07)).

**(b) Future automation layer** — parseable transcript format with a
functional parser and mechanical diff engine. This remains deferred
future benchmark automation work.

Exploratory non-scoring runs are permitted before (a). The v1 scored
benchmark requires (a). Future automation-heavy benchmark revisions and
omission-proof claims require both layers.

### What T4 Requires From the Transcript

| Item | Required for |
|------|-------------|
| Complete post-containment Glob/Grep/Read outputs per call | Mechanical omission diff ([T4-PR-11](provenance-and-audit.md#t4-pr-11)) |
| Agent evidence block re-emission each round | Structured record extraction |
| Tool call inputs (queries, paths, scope roots) | Query coverage audit ([scouting-behavior: query coverage](scouting-behavior.md#t4-sb-04)) |
| Deterministic transcript parsing | Harness diff engine, evidence extraction |

### Degradation Path

If this dependency is NOT resolved — if "raw transcript" permits
truncation or lossy capture — the audit chain degrades from "fully
verifiable via mechanical diff" to "verifiable up to match_digest in the
evidence block." T4 declares this degradation path explicitly rather than
hiding the dependency.

### Required Benchmark-Contract Text

The benchmark contract should state: *"Raw run transcript means
untruncated tool output for every tool call in every turn."* T4 declares
this as a prerequisite for its provenance story, not a follow-up
clarification.
