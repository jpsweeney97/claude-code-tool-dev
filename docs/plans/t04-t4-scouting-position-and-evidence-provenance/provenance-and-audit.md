---
module: provenance-and-audit
status: active
normative: true
authority: provenance
---

# Provenance and Audit

Synthesis citation surface, provenance index, claim ledger, audit chain,
and mechanical omission surface. These surfaces connect scouted evidence
to scored synthesis claims and provide post-hoc auditability.

## <a id="t4-pr-01"></a>T4-PR-01: Evidence Trajectory

Derived from `evidence_log`
([dialogue-synthesis-format.md:15](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)):

| Field | Derivation |
|-------|-----------|
| Record index | `record.index` (deterministic join key) |
| Entity | `record.entity` |
| Found | Citation snippet if available; `(path:line_range)` at tier 3 |
| Disposition | `record.disposition` |
| Impact | `supports` → "claim supported", `contradicts` → "premise falsified", `conflicted` → "evidence contradictory", `ambiguous` → "inconclusive", `not_found` → "no evidence" |

Only `EvidenceRecord` entries appear in the trajectory. No uncited or
un-dispositioned content enters the scored synthesis. Each trajectory
entry MUST include the record index to enable deterministic join from
synthesis claims to specific evidence records
([T4-PR-02](#t4-pr-02)). Deterministic here means the T4-SM-05
invariant holds: for `evidence_log[i]`, `record.index == i`.

### Projection to Per-Turn Scout Outcomes

```text
scout_outcomes[turn_N] = [
    evidence_log[i]
    for i in range(len(evidence_log))
    if evidence_log[i].turn == turn_N
]
```

Populated in step 5d
([scouting-behavior: per-turn loop](scouting-behavior.md#t4-sb-01)).
The synthesis assembler reads `scout_outcomes` from `turn_history` as
before — entries are now `EvidenceRecord`s with full schema rather than
`evidence_wrapper` strings.

## <a id="t4-pr-02"></a>T4-PR-02: Synthesis-Record Join

**Deterministic via `claim_id`.** Inline citations use
`(path:line_range)` in the scored narrative. The same `(path:line_range)`
can appear in multiple evidence records across turns. The deterministic
join from a synthesis claim to its specific evidence record requires two
structured surfaces:

**Surface 1: `claim_provenance_index` in `<!-- pipeline-data -->`** —
maps each `claim_id` to its provenance entry. See
[T4-PR-03](#t4-pr-03) for wire format.

**Surface 2: Claim ledger** — a synthesis section separate from the
checkpoint. See [T4-PR-05](#t4-pr-05).

## <a id="t4-pr-03"></a>T4-PR-03: Claim Provenance Index

Two provenance variants:

```text
claim_provenance_index: [
  { claim_id: 0, claim_ref: [3, "compute_action behavior", 0],
    type: "scouted", record_indices: [2, 5] },
  { claim_id: 1, claim_ref: [4, "validate_input return type", 0],
    type: "scouted", record_indices: [3] },
  { claim_id: 2, claim_ref: [5, "module uses dependency injection", 0],
    type: "not_scoutable", classification_trace: {
      claim_id: 2, candidate_entity: "module", failed_criterion: 3,
      decomposition_attempted: true, subclaims_considered: [],
      residual_reason: "module is an architectural label, not a code
        entity with inspectable state" } }
]
```

### Canonical Wire Format

Dense JSON array. Invariant: `claim_provenance_index[i].claim_id == i`
for all entries. Array length equals `next_claim_id`. All allocated
`claim_id`s persist in the index, including claims later conceded
(concession removes from `verification_state` but the provenance entry
is historical). No sparse IDs, no gaps, no reordering.

### Embedded claim_id Equality Invariant

When `classification_trace` is embedded in a provenance entry,
`classification_trace.claim_id` MUST equal the containing entry's
`claim_id`. This is redundant by construction (the trace is created
during the same registration that allocates the `claim_id`), but the
invariant is stated explicitly because `ClassificationTrace` is also
referenced standalone in adjudicator audit
([scouting-behavior: claim classification](scouting-behavior.md#t4-sb-05)).
Validators MUST reject entries where the two values diverge.

Each entry retains the full `ClaimRef` for human readability. The `type`
field distinguishes scouted (has `record_indices`) from not_scoutable
(has `classification_trace`). This is provenance metadata — appropriate
for pipeline-data.

## <a id="t4-pr-04"></a>T4-PR-04: Two Provenance Tiers

| Tier | Type | Join Chain | Guarantee |
|------|------|-----------|-----------|
| 1 | `scouted` | `claim_id` → `record_indices` → evidence blocks in transcript → tool output | Full mechanical chain. Deterministic given transcript fidelity ([T4-F-13](foundations.md#t4-f-13)) |
| 2 | `not_scoutable` | `claim_id` → `classification_trace` → adjudicator audit | Classification provenance only. No evidence chain (no scouting occurred). Adjudicator independently evaluates claim truth |

The deterministic-audit guarantee applies to **Tier 1 (scouted claims)
only**. Tier 2 claims have auditable classification (the trace records
what was attempted and which criterion failed) but no evidence
provenance — there is nothing to audit beyond whether the classification
was correct.

## <a id="t4-pr-05"></a>T4-PR-05: Claim Ledger

The claim ledger is a flat inventory of atomic factual claims with
`[ref:]` annotations. This is the provenance surface. It is a new
synthesis section, separate from the checkpoint.

```text
## Claim Ledger
FACT: compute_action returns ActionResult [ref: 0]
FACT: validate_input rejects None [ref: 1]
FACT: module uses dependency injection [evidence: not_scoutable] [ref: 2]
FACT: module dependency ordering unclear [ref: 3]
```

### Separation of Concerns

The checkpoint and claim ledger serve different purposes and MUST NOT be
conflated:

| Surface | Purpose | Grammar | Content |
|---------|---------|---------|---------|
| **Checkpoint** | Dialogue outcome summary | `RESOLVED`, `UNRESOLVED`, `EMERGED` (outcome-based, per [dialogue-synthesis-format.md:55-65](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md)) | What happened during the dialogue. Unchanged from synthesis-format contract |
| **Claim ledger** | Provenance inventory | `FACT` (fact-based) | Every atomic factual claim about the repo, with `[ref:]` for provenance join |

The checkpoint is NOT the provenance surface. Many repo facts in a
synthesis are supporting observations, not dialogue outcomes — they
don't fit `RESOLVED`/`UNRESOLVED`/`EMERGED`. Forcing them into the
checkpoint grammar would require agents to either jam facts into outcome
tags or leave them in narrative prose with no provenance.

### Claim Ledger Rules

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

## <a id="t4-pr-06"></a>T4-PR-06: Narrative-to-Ledger Relationship

**Normative.** The claim ledger is the canonical factual-claim inventory.
Every factual claim about repository state, implementation behavior,
contract or spec requirements, or current code relationships
([benchmark.md:123-128](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
in the synthesis MUST have a corresponding claim ledger entry with
`[ref:]`. This mirrors the benchmark's claim inventory categories exactly.
Narrative prose may elaborate on, contextualize, or provide reasoning
about ledger facts, but MUST NOT introduce independent factual claims in
any benchmark-scored category that lack a ledger entry.

### Scoring Interaction

The benchmark still scores the full synthesis
([benchmark.md:118-123](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)):
the adjudicator enumerates every distinct factual claim from the complete
synthesis. A narrative-only factual claim (present in prose but absent
from the ledger) is scored normally by the adjudicator AND recorded as a
methodology finding (`finding_kind: narrative_ledger_violation`,
`detection: mechanical`). The claim is not exempt from scoring; the
missing ledger entry is an additional methodology finding that counts
toward the per-run `methodology_finding_threshold`
([T4-BR-07](benchmark-readiness.md#t4-br-07) pass-rule condition 5). The
finding row is keyed by `inventory_claim_id` (from T7 adjudicator claim
inventory), not ledger `claim_id` — by definition, narrative-only claims
have no ledger ID.

### Dedup Rule

When the same fact appears in both narrative prose and the claim ledger,
the harness and ledger checker treat the ledger entry as canonical for the
provenance join. The adjudicator scores distinct factual claims per the
benchmark
([benchmark.md:123](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md));
the dedup rule prevents double-counting in the harness join path, not in
adjudication.

### Mechanical Enforcement

Ledger completeness is not mechanically enforceable without a narrative
factual-claim inventory (requires semantic extraction). Benchmark runs
MUST NOT proceed until T7 delivers the inventory and ledger completeness
checker ([T4-BR-07](benchmark-readiness.md#t4-br-07)). After T7, the
ledger checker mechanically flags narrative facts without ledger entries.
The narrative-to-ledger MUST is a synthesis contract obligation that
agents must comply with regardless of enforcement availability.

## <a id="t4-pr-07"></a>T4-PR-07: Provenance Coverage of Scored Claims

- **Ledger claims with `[ref:]`** → Tier 1 or Tier 2 provenance
  (deterministic or classification). Full chain.
- **Narrative-only claims (no ledger entry)** → synthesis-contract
  violation. Scored normally by adjudicator. No mechanical provenance
  audit possible. Missing ledger entry is a `narrative_ledger_violation`
  methodology finding (mechanical, keyed by `inventory_claim_id`).

### Narrative Coverage Gap

With the narrative-to-ledger relationship
([T4-PR-06](#t4-pr-06)), narrative-only factual claims are
synthesis-contract violations — there IS a defined contract cost.
Mechanical enforcement requires T7 to deliver the narrative factual-claim
inventory and ledger completeness checker
([T4-BR-06](benchmark-readiness.md#t4-br-06)). Benchmark runs are blocked
until T7 enforcement is operational
([T4-BR-07](benchmark-readiness.md#t4-br-07)). The
`ledger_coverage_rate` metric is downstream of the inventory — it cannot
be defined independently (computing coverage requires enumerating
narrative claims, which IS the inventory).

## <a id="t4-pr-08"></a>T4-PR-08: G3 Scope

G3's invariant
([risk-register:35](../../reviews/2026-04-01-t04-convergence-loop-risk-register.md))
is: "Every accepted scout result MUST be retained as structured
provenance, not just counted." T4 satisfies this via Tier 1 scouted
provenance: `EvidenceRecord`
([state-model: evidence record](state-model.md#t4-sm-05)) →
`claim_provenance_index` ([T4-PR-03](#t4-pr-03)) → `[ref:]` in claim
ledger ([T4-PR-05](#t4-pr-05)) → full records in transcript. The G3
invariant concerns **scouted claims** — it does not require provenance
for unscouted narrative claims (there are no scout results to retain).

**NOT a G3 concern.** Narrative-only claims are not "accepted scout
results." G3 is satisfied by T4's Tier 1 scouted chain. Narrative
coverage is a separate synthesis quality concern for T7.

## <a id="t4-pr-09"></a>T4-PR-09: Aggregation Rule

A claim is `supported` in the benchmark sense when the verification
status derivation in
[state-model: verification state](state-model.md#t4-sm-06)
produces `status == "supported"`.

## <a id="t4-pr-10"></a>T4-PR-10: Authority Chain

**Two tiers, contingent on [T4-F-13](foundations.md#t4-f-13).**

**Tier 1 (scouted claims):** synthesis claim → claim ledger `[ref: N]` →
`claim_provenance_index[N]` → `record_indices` → evidence blocks in
transcript (claim_ref, disposition, citations) → post-containment tool
output in transcript. This chain is authoritative given transcript
fidelity ([T4-F-13](foundations.md#t4-f-13)). Without the blocking
external dependency resolved, the chain degrades to "verifiable up to the
evidence block."

**Tier 2 (not_scoutable claims):** synthesis claim → claim ledger
`[ref: N]` → `claim_provenance_index[N]` → `classification_trace`
(candidate_entity, failed_criterion). Chain terminates at classification.
The adjudicator independently evaluates the claim's truth value and the
classification's correctness. No mechanical audit beyond the
classification decision.

**Narrative-only claims (no ledger entry):** No provenance chain.
Synthesis-contract violation ([T4-PR-06](#t4-pr-06)). Benchmark runs
blocked until T7 delivers mechanical enforcement
([T4-BR-07](benchmark-readiness.md#t4-br-07)). This gap is separate from
G3 — it concerns synthesis quality, not scouted provenance.

## <a id="t4-pr-11"></a>T4-PR-11: Mechanical Omission Diff

For any evidence record, the full set of uncited matches is:

```text
uncited = {
    (path, line) for (path, line) in post_containment_tool_output
    if (path, line) not in record.citations
}
```

The harness MUST compute this diff **by default** for every evidence
record used in the synthesis. This is computable from two sources already
in the transcript: (1) post-containment tool output (all match lines
returned by Grep/Read, after containment
([containment](containment.md))), (2) `CitationSpan`
entries in the evidence block (which lines the agent cited). No agent
self-reporting is needed.

### Per-Tool Omission Relevance

The omission surface is shape-sensitive — a broad read inflates uncited
lines, a narrow read minimizes them. To prevent the agent from gaming
diff cleanliness via read strategy, tool outputs are classified by
omission relevance:

| Tool | Omission-relevant output | Rationale |
|------|-------------------------|-----------|
| **Grep** | All match lines | Agent chose the query. Every match is a candidate the agent saw |
| **Read (line_range)** | All lines in requested range | Agent chose the scope. The range bounds the evidence surface |
| **Read (full file)** | **All lines in the file** | Agent chose to read the full file. Every line is omission-relevant |
| **Glob** | None (path list only) | No content to omit |

**Omission boundary is determined at read time, not citation time.** The
agent's read scope determines the omission surface. There is no
post-citation boundary shrinking — the agent cannot do a broad read, cite
a narrow favorable function, and have the omission surface retroactively
narrowed to the enclosing scope of cited lines. This closes the
shape-gaming exploit: a full-file read means the harness diffs every line
in the file against citations.

### match_digest Is a Convenience

`match_digest` is a guide in the compressed evidence block, capped at 20
lines. On large outputs (80+ matches), it truncates. The harness does NOT
wait for match_digest to signal uncited matches before computing the
diff — it computes the diff unconditionally. match_digest helps human
reviewers do quick triage but is never load-bearing for the audit.

### Why Mechanical Diff Is Stronger

An agent cannot suppress contradictory evidence from the diff — the tool
returned it, it is in the transcript, the harness sees it. The diff
operates on the full post-containment output regardless of agent-authored
summaries.

## <a id="t4-pr-12"></a>T4-PR-12: Read-Scope Rule

**Normative.** Scout reads MUST be anchored to one of:

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
`read_anchor` field
([scouting-behavior: query coverage](scouting-behavior.md#t4-sb-04))
are a contract violation. The `read_anchor` field records which class the
agent claims. The adjudicator verifies: a 2000-line module read with
`read_anchor: "whole_file"` is auditable misuse. The contract consequence
is the omission surface: full-file reads produce full-file diffs, creating
strong incentive for targeted reads.

## <a id="t4-pr-13"></a>T4-PR-13: Methodology Findings for Omission and Coverage

### Under-Reading Finding

The adjudicator flags under-reading when:
- The claim shape required broader context than the agent's read scope
- Contradictory evidence existed in the un-read portion of a file the
  agent chose to read narrowly

An under-reading finding is a **methodology finding**
(`finding_kind: under_reading`, `detection: judgment`) — it does not
change claim labels (`supported`/`unsupported`/`false` per
[benchmark.md:135](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
but appears in `adjudication.json` as a finding row keyed by
`inventory_claim_id`. This is an adjudicator judgment, not a mechanical
harness check — the harness can only diff what was actually read, not
what the agent failed to inspect.

Methodology findings are recorded for benchmark consumption. T4 specifies
the required pass-rule effect: a per-run `methodology_finding_threshold`
gate as condition 5 (threshold breach = valid scored run that fails
condition 5, not an invalid run). T7 owns adding this condition to the
benchmark contract
([T4-BR-07](benchmark-readiness.md#t4-br-07)). Until the amendment
lands, findings exist as structured audit data without mechanical
pass/fail consequences.

## <a id="t4-pr-14"></a>T4-PR-14: Reviewer Workflow

1. Claim in synthesis → `claim_provenance_index`
   ([T4-PR-03](#t4-pr-03)) → record indices → evidence block
2. Harness-computed mechanical diff ([T4-PR-11](#t4-pr-11)) (not gated
   by agent choices; derived omission-audit proof surface per
   [T4-F-13](foundations.md#t4-f-13) and
   [T4-BR-07](benchmark-readiness.md#t4-br-07))
3. Compare uncited match content against disposition (using per-tool
   relevance classification)
4. match_digest for quick human triage (convenience overlay)
5. Query coverage
   ([scouting-behavior: query coverage](scouting-behavior.md#t4-sb-04)):
   were both mandatory types included?
6. Containment verification
   ([containment](containment.md)): all tool calls within
   allowed_roots?

**Optional enrichment:** T7 MAY construct `evidence.json` from the
transcript. This is a convenience, not provenance authority.
