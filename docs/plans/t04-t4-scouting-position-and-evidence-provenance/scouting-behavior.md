---
module: scouting-behavior
status: active
normative: true
authority: scouting-behavior
---

# Scouting Behavior

Behavioral rules for the scouting loop — per-turn mechanics, target
selection, query coverage, claim classification, and methodology findings.

## <a id="t4-sb-01"></a>T4-SB-01: Per-Turn Loop

```text
1. Extract semantic data (layer 1)
2. Validate, normalize, register occurrences (layer 2):
   2a. Phase 1: process concessions, reinforcements (T4-SM-02)
   2b. Phase 1.5: reclassify dead-referent claims to `new` (T4-SM-02)
   2c. Phase 2: register new/revised claims with merger checks (T4-SM-01)
3. Compute counters, quality, effective_delta (layer 3)
4. Control decision (T1 ControlDecision)
5. Scout (layer 4):
   5a. Select target (T4-SB-03)
   5b. Execute tool calls (T4-SB-04 query coverage) [scout_budget_spent += 1 here]
   5c. Assess disposition, select citations
   5d. Create evidence record, update verification state
   5e. Re-emit evidence block (atomic commit)
   — SKIP 5a-5e if conclude, budget, or no targets
6. Compose follow-up (layer 5) — SKIP if conclude
7. Send follow-up — SKIP if conclude
```

## <a id="t4-sb-02"></a>T4-SB-02: Scout Skip Conditions

| Condition | Source |
|----------|--------|
| `action == "conclude"` | Control decision |
| `evidence_count >= max_evidence` | Evidence budget exhausted |
| `scout_budget_spent >= max_scout_rounds` | Effort budget exhausted ([T4-SM-07](state-model.md#t4-sm-07)) |
| No scoutable targets ([T4-SB-03](#t4-sb-03)) | Nothing to scout |

## <a id="t4-sb-03"></a>T4-SB-03: Scout Target Selection

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

### Graduated Attempt Limit

| After first scout returns... | Max attempts | Rationale |
|-----------------------------|-------------|-----------|
| `not_found` | 1 | Nothing to find. Retrying wastes budget |
| `ambiguous` | 2 | Evidence was real but inconclusive. Different query may clarify |
| `conflicted` | 2 | Evidence was real but mixed. Second query may resolve |
| `supports` | 1 | Terminal — claim verified |
| `contradicts` | 1 | Terminal — claim refuted |

A `not_found` result leaves status at `unverified` with
`scout_attempts = 1` → priority 4. An `ambiguous` or `conflicted` result
allows a second attempt with a different query approach.

### One-Turn Delay

Unresolved questions become scoutable claims one turn after Codex
responds. At most one lost scout per question cycle. Rev 6 analysis in
[rejected-alternatives: 7.27](rejected-alternatives.md#727-unresolved-item-scouting-as-secondary-target-type).

## <a id="t4-sb-04"></a>T4-SB-04: Scout Query Coverage

Each scouting round executes 2-5 tool calls. Two query types are
mandatory. Minimum 2 calls (one per mandatory type). Target 3. Hard cap 5
(prevents budget monopolization by a single claim):

| Type | What it targets | Example | Required |
|------|----------------|---------|----------|
| `definition` | What the entity IS or DOES | `Grep "def compute_action"`, `Read control.py:55-65` | Yes (1+) |
| `falsification` | What would CONTRADICT the claim | `Grep "compute_action.*None"`, search for alternative return types | Yes (1+) |
| `supplementary` | Additional context | Usage sites, test coverage, callers | Optional |

### Two Mandatory Types

A single definition query covers entity behavior but not claim negation.
A single falsification query checks the claim but may miss entity
context. Together they ensure the scout output covers both what the entity
does AND what would disprove the claim.

### Falsification Query Design

The agent MUST construct a query that targets a **specific
expected-contradicting condition**. The `expected_contradiction_target`
field in `ScoutStep` ([T4-SM-05](state-model.md#t4-sm-05)) records what
the query was designed to find. Examples:
- Claim "function X returns type Y" →
  `expected_contradiction_target`: "X returns non-Y type" →
  query: `Grep "def X.*->.*(?!Y)"`
- Claim "module X contains Y" →
  `expected_contradiction_target`: "Y defined outside X" →
  query: `Grep "class Y" --glob "!module_x/"`

A falsification query that searches for the same entity as the definition
query (with no contradicting condition) fails the diversity check. The
`expected_contradiction_target` must name a condition distinct from the
definition query's target.

### Claim-Shape Adequacy

**Normative.** The adequacy of query coverage is claim-shape-dependent.
For relational or multi-file claims, satisfying the mandatory query-type
quota (one definition, one falsification) is necessary but not
sufficient — the query set must address the claim's actual structure. A
relational claim "X calls Y" is not considered adequately covered by a
definition query for X and a falsification query for X alone; the query
set must also address Y. The adjudicator audits whether the query set
matches the claim shape, not just whether the mandatory query types were
present. A shape-inadequacy finding is a **methodology finding**
(`finding_kind: shape_inadequacy`, `detection: judgment`) that appears in
`adjudication.json`. It does not change claim labels.

Methodology findings are recorded in `adjudication.json` for benchmark
consumption ([T4-BR-09](benchmark-readiness.md#t4-br-09)). T4 specifies
the required semantics: a per-run `methodology_finding_threshold` gate as
pass-rule condition 5 (threshold breach = valid scored run that fails
condition 5, not an invalid run). T7 owns adding this condition to the
benchmark contract — the live benchmark currently has four conditions.
Until the amendment lands, findings exist as structured audit data without
mechanical pass/fail consequences.

### read_anchor Field

For Read tool calls, records the justification for the read scope
([T4-PR-12](provenance-and-audit.md#t4-pr-12) read-scope rule). `null`
for Grep/Glob calls.

### Audit

`query_type` field in each `ScoutStep` classifies the query. A reviewer
verifies at least one `definition` and one `falsification` per round,
checks `expected_contradiction_target` for coherence, and confirms the
falsification query targets a different condition than the definition
query. Post-hoc auditing cannot fix a bad benchmark run, but it detects
systematic bias across the benchmark corpus.

### Second-Attempt Queries

When a claim gets a second scout attempt ([T4-SB-03](#t4-sb-03)), the
agent MUST use different queries than the first attempt. At least one
mandatory-type query (definition or falsification) in the second round
MUST have query text that does not appear in any first-round query of the
same type (not just type reclassification — the actual search string must
change). Supplementary queries do not count toward this diversity
requirement. The `query` fields from the first round's `ScoutStep`s are
in the evidence block — the agent has them in context.

**Objective difference criterion:** there exists
`t ∈ {definition, falsification}` and a round-2 query `q2` of type `t`
such that `q2.query` is unequal to the `query` field of every round-1
`ScoutStep` of type `t`.

This text-level rule is the minimum mechanical check. Substantive
diversity — whether the second attempt explores a materially different
investigative direction — is adjudicated using the existing claim-shape
and `expected_contradiction_target` audit surfaces. The adjudicator may
treat semantically recycled retries as inadequate query coverage using
existing methodology-finding surfaces, without requiring a specific
finding kind.

## <a id="t4-sb-05"></a>T4-SB-05: Claim-Class Scope

Not all benchmark claims are scoutable. T4 defines three claim classes:

| Class | Entity grammar | Scouting behavior |
|-------|---------------|-------------------|
| **Scoutable** | `<path_or_symbol>` or `<path_or_symbol> <qualifier>` | Standard scouting: definition + falsification queries |
| **Relational-scoutable** | `<entity> × <entity>` | Primary entity (left of `×`) determines scouting focus. Queries target the relationship |
| **Not scoutable** | N/A | No scouting. Terminal verification status: `not_scoutable` ([T4-SM-06](state-model.md#t4-sm-06)) |

### Scoutable Claims

Claims whose truth condition is verifiable by examining entities
locatable in the repo — file paths, symbols, code patterns, configuration
values. Most benchmark claims about repository state and implementation
behavior fall here.

### Relational-Scoutable Claims

Claims about relationships between two entities. "Function X calls
function Y" → entity `X × Y`, scout focus on X, definition query for X's
implementation, falsification query for whether X calls something other
than Y. The evidence record's `entity` field uses the `×` grammar;
queries encode the relationship.

### Not-Scoutable Claims

Abstract interpretations, meta-properties, cross-system claims, or
spec-interpretation claims where the truth condition cannot be reduced to
repo-searchable entities. These claims enter the verification model at
terminal status `not_scoutable`
([T4-SM-06](state-model.md#t4-sm-06) lifecycle). No `EvidenceRecord` is
created — no scouting occurred. They are excluded from target selection
([T4-SB-03](#t4-sb-03), priority 4 skip). They appear in the benchmark
claim inventory and the synthesis.

### Classification Criteria (Objective)

A claim is scoutable if and only if the agent can identify:
1. At least one entity fitting the `<path_or_symbol>` grammar (possibly
   with `<qualifier>` or `×` relational form)
2. A definition query that could be executed via Grep/Read
3. A falsification query that would surface contradicting evidence if it
   existed

If ANY of these three cannot be identified, the claim is `not_scoutable`.
The classification decision is made during Phase 2 registration
([T4-SM-02](state-model.md#t4-sm-02)) and is recorded as the terminal
verification status.

### Decomposition Analysis (Audit-Side, MUST)

Before classifying a claim as `not_scoutable`, the agent MUST perform a
decomposition check: whether the claim can be decomposed into subclaims
that individually satisfy all three scoutable criteria. The agent records
this analysis in the `ClassificationTrace` (below) for adjudicator
review. However, the agent MUST NOT register decomposed subclaims as new
pipeline entries — T2/T3 define two claim sources (`extracted`,
`minimum_fallback`) and decomposed subclaims have no defined
`claim_source`, counter semantics, or continuity behavior.

The decomposition check may conclude quickly — if no plausible
entity-bearing subclaim candidates are identifiable, the agent records
`decomposition_attempted: true`, `subclaims_considered: []`, and
`residual_reason` explaining why no subclaims were found. This is a valid
outcome, not a finding. `decomposition_attempted: false` is always a
methodology finding (`finding_kind: decomposition_skipped`,
`detection: mechanical`) regardless of which criterion failed for the
whole claim.

The adjudicator evaluates decomposition adequacy: whether scoutable
subclaims exist that the agent failed to identify, and whether the
`not_scoutable` classification was justified. A finding occurs when the
adjudicator independently identifies scoutable subclaims the agent's
trace failed to consider.

### ClassificationTrace

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

`candidate_entity` is the closest entity the agent considered (null if no
entity fitting the grammar could be identified — criterion 1 failure).
`failed_criterion` is which of the three objective criteria failed first.

### State-Machine Invariants

| `decomposition_attempted` | `subclaims_considered` | `residual_reason` | Structurally valid? |
|---------------------------|----------------------|-------------------|---------------------|
| `false` | MUST be `null` | MUST be `null` | Yes — decomposition not performed |
| `true` | `[]` (empty) | MUST be non-null `str` | Yes — attempted, none found, reason required |
| `true` | non-empty `list[str]` | MUST be non-null `str` | Yes — subclaims found but not individually scoutable, reason required |
| `true` | `null` | any | **No** — decomposition attempted implies subclaims were evaluated |
| `true` | non-empty `list[str]` | `null` | **No** — non-empty subclaims require explanation |
| `false` | non-null | any | **No** — no decomposition means no subclaim data |

"Structurally valid" means the trace passes schema and invariant checks.
A structurally valid trace can still constitute a methodology finding:
`decomposition_attempted: false` is always a `decomposition_skipped`
finding regardless of structural validity. Validators MUST reject
structurally invalid traces; the adjudicator evaluates methodology
consequences for structurally valid ones.

All fields are **explicitly non-authoritative** — they are the agent's
explanation of its classification, not proof.

### Adjudicator Audit

The adjudicator independently reviews all `not_scoutable` classifications
using the `ClassificationTrace` as a starting point. The adjudicator
evaluates:
1. Whether the classification was correct (agent could have identified
   all three criteria for the original claim)
2. Whether decomposition analysis was adequate (whether scoutable
   subclaims exist that the agent failed to identify)

A misclassification is recorded as a methodology finding
(`finding_kind: misclassification`, `detection: judgment`). Inadequate
decomposition where the adjudicator identifies missed scoutable subclaims
is also a methodology finding. Both appear in `adjudication.json`
([T4-BR-09](benchmark-readiness.md#t4-br-09)). The adjudicator still
independently evaluates the claim's truth value — `not_scoutable` affects
scouting, not scoring.

### Synthesis Policy

`not_scoutable` claims MUST appear in the scored synthesis if they are
factual claims about the repo. The agent cannot suppress claims by
classifying them as `not_scoutable`. The adjudicator scores them
independently ([T4-PR-09](provenance-and-audit.md#t4-pr-09) aggregation
does not count them as `supported` — they have no evidence).

### Why This Scope Matters

Without explicit claim-class scope, agents either shoehorn multi-entity
claims into fake single-entity evidence (producing formally compliant but
substantively useless queries) or produce falsification queries that
cannot meaningfully test the claim. Explicit scope gives the agent a
legitimate path for claims that do not fit the evidence model. Terminal
status prevents retry loops.

### Corpus Calibration Requirement

After implementation, the `not_scoutable` classification rate MUST be
validated against the benchmark corpus via dry run. The dry run MUST
produce a report of `not_scoutable` rate broken down by task ID. Corpus
tasks dominated by cross-system and spec-interpretation claims (B1, B4,
B5, B7, B8) are most susceptible to over-classification. If the rate
renders a material fraction of scored synthesis claims unprovenanced for
these tasks, the classification criteria or decomposition rules must be
tightened before benchmark execution. The dry-run report is a required
artifact, not a deferred aspiration.
