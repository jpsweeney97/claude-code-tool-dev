---
module: benchmark-readiness
status: active
normative: true
authority: benchmark-readiness
---

# Benchmark Readiness

Non-decaying blockers, scored-run prerequisite gates, and
benchmark-contract amendment obligations. This is a load-bearing readiness
contract — these are not optional follow-through items.

## <a id="t4-br-01"></a>T4-BR-01: T5 Migration Surfaces

T4's scouting replacements
([boundaries: helper-era migration](boundaries.md)) define how scouting
works in `agent_local` mode. But `agent_local` runs also require T5's
primary migration set to land — without these changes, an `agent_local`
run MUST be rejected as invalid.

**Benchmark-run behavior:** silent downgrade to `server_assisted` is
prohibited during benchmark execution — an `agent_local` benchmark run
that exercises the `server_assisted` evidence path contaminates the
comparison
([benchmark.md:52](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md)).
The run MUST produce an explicit mode-mismatch failure artifact recording
the requested mode, the reason for rejection, and which T5 surface was
missing. This is benchmark-run behavior; non-benchmark contexts may
define their own mode-fallback policy.

| Surface | Location | Required Change | Owner |
|---------|----------|----------------|-------|
| Mode enum definition | [event_schema.py:137](../../../packages/plugins/cross-model/scripts/event_schema.py) | Add `agent_local` to `VALID_MODES` | T5 |
| Conversation summary mode | [dialogue-synthesis-format.md:86](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) | Document `agent_local` in human-readable contract | T5 |
| Pipeline epilogue field | [dialogue-synthesis-format.md:144](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) | Add `agent_local` to JSON epilogue contract | T5 |
| Dialogue skill parser | [SKILL.md:435](../../../packages/plugins/cross-model/skills/dialogue/SKILL.md) | Accept `agent_local` as valid parsed mode | T5 |
| Test enforcement | T5 migration set | Enum assertions, analytics fixtures, propagation tests | T5 |

**Dependency:** T4 defines the scouting contract. T5 defines the mode
contract. Both must land before `agent_local` runs produce valid data.
T4 does NOT claim completeness over T5's migration set — the two are
complementary.

## <a id="t4-br-02"></a>T4-BR-02: Transcript Fidelity Surfaces

These surfaces fulfill the transcript fidelity dependency declared in
[T4-F-13](foundations.md#t4-f-13).

| Surface | Required Change | Owner | Target |
|---------|----------------|-------|--------|
| Benchmark run conditions | Add normative clause: "raw run transcript means untruncated post-containment tool output for every tool call" | T7 | [benchmark.md:95](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |
| Benchmark artifact contract | Specify parseable transcript format sufficient for mechanical diff extraction and per-step metadata recovery (including resolved `scope_root`) | T7 | [benchmark.md:101-112](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |
| Transcript parser | Implement harness-side tool for extracting tool inputs/outputs/evidence blocks and per-step scout metadata (`ScoutStep` fields including `scope_root`) from transcript | T7 | New harness component |
| Mechanical diff engine | Implement harness-side `post_containment_output - citations = uncited` computation | T7 | New harness component |

**Verification:** The spec sub-dependency is satisfied when the benchmark
contract includes the normative clause and a transcript format spec
(including per-step metadata recovery) exists. Parser and diff-engine
implementation are separate T7 deliverables deferred to future
automation-heavy benchmark revisions
([T4-BR-07](#t4-br-07)).

## <a id="t4-br-03"></a>T4-BR-03: Allowed-Scope Safety

**DECLARED SAFETY DEPENDENCY.** Within `allowed_roots`, files may contain
secrets (credentials, tokens, private keys). The helper-era contract had
`redactions_applied` and `risk_signal`
([context-injection-contract.md:671-672](../../../packages/plugins/cross-model/references/context-injection-contract.md)).
T4's direct tools have no equivalent.

| Surface | Required Change | Owner | Target |
|---------|----------------|-------|--------|
| Secret handling policy | Define whether allowed-scope secrets require redaction in benchmark context | T7 | Benchmark contract amendment |
| Redaction/provenance interaction | If redaction required: specify how redacted output interacts with mechanical diff ([T4-PR-11](provenance-and-audit.md#t4-pr-11)) | T7 | Containment amendment or T7 harness spec |

Until resolved, T4 assumes allowed-scope content is safe to capture —
correct for benchmark corpora that are curated, but not for general use.

## <a id="t4-br-04"></a>T4-BR-04: Provenance Index Consumer

These surfaces wire the `claim_provenance_index`
([T4-PR-03](provenance-and-audit.md#t4-pr-03)) into the benchmark
pipeline.

| Surface | Required Change | Owner | Target |
|---------|----------------|-------|--------|
| Pipeline epilogue schema | Add `claim_provenance_index` field to epilogue contract with `claim_id`-keyed schema, two variants (scouted, not_scoutable) | T7 | [dialogue-synthesis-format.md:138-147](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| Epilogue parser | Accept and validate `claim_provenance_index` entries (both variants) | T7 | [emit_analytics.py](../../../packages/plugins/cross-model/scripts/emit_analytics.py) |
| Schema validation | Add `claim_provenance_index` to `event_schema.py` field set | T7 | [event_schema.py](../../../packages/plugins/cross-model/scripts/event_schema.py) |
| Claim ledger `[ref:]` parser | Extract integer `claim_id` annotations from claim ledger entries | T7 | New harness component |

## <a id="t4-br-05"></a>T4-BR-05: Synthesis-Format Contract Updates

These surfaces add T4-required sections and vocabulary to the synthesis
format.

| Surface | Required Change | Owner | Target |
|---------|----------------|-------|--------|
| Claim ledger section | Add `## Claim Ledger` as a new synthesis section with `FACT:` lines, `[ref: N]`, and `[evidence:]` annotations ([T4-PR-05](provenance-and-audit.md#t4-pr-05)) | T7 | [dialogue-synthesis-format.md](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| Claim ledger rules | Document: one line = one atomic factual claim. Separate from checkpoint (outcome-based, unchanged) | T7 | [dialogue-synthesis-format.md](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| `not_scoutable` in claim trajectory | Add `not_scoutable` to the claim trajectory vocabulary (`new → reinforced/revised/conceded/not_scoutable`) | T7 | [dialogue-synthesis-format.md:16](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |
| `not_scoutable` in evidence trajectory | Note which claims were classified as not scoutable (no evidence entry) | T7 | [dialogue-synthesis-format.md:14](../../../packages/plugins/cross-model/references/dialogue-synthesis-format.md) |

### <a id="f6-f7-f11-blockers"></a>F6/F7/F11 Provenance Wire-Format Blockers

`claim_provenance_index` and `ClassificationTrace` have named T7
consumer surfaces in [T4-BR-04](#t4-br-04) and [T4-BR-05](#t4-br-05),
and the rev17 audit findings below were resolved as post-closure
contract amendments. T7 consumer work MAY proceed as exploratory
shakedowns ([T4-BR-08(a)](#t4-br-08)) against the current contract.
Manual benchmark v1 may proceed without these consumers because its
scoring attaches to the final synthesis plus transcript review rather
than these wire formats. Policy-influencing calibration, automation-heavy
scored benchmark revisions, and benchmark-stability claims that consume
these surfaces MUST NOT proceed until all applicable exit conditions in
this table are satisfied.

Resolved-row convention: resolved findings remain in this table. The
`Finding` cell gains `(resolved)`, and the `Exit condition` cell is
replaced by `Resolved in ...` citations to the authoritative clauses
that closed the gap.

| Finding | Blocking surface | Exit condition |
|---------|------------------|----------------|
| F6 (resolved) | Concession lifecycle semantics across three unresolved sub-gaps: retained `ProvenanceEntry` status for conceded claims, dense-array representation of conceded positions, and claim-ledger policy for conceded claims | Resolved in [T4-SM-01](state-model.md#t4-sm-01), [T4-SM-02](state-model.md#t4-sm-02), [T4-SM-06](state-model.md#t4-sm-06), [T4-SM-07](state-model.md#t4-sm-07), [T4-PR-03](provenance-and-audit.md#t4-pr-03), and [T4-PR-06](provenance-and-audit.md#t4-pr-06) |
| F7 (resolved) | Serialization boundary from agent working state into `<!-- pipeline-data -->` during synthesis composition | Resolved in [T4-SM-07](state-model.md#t4-sm-07) and [T4-PR-03](provenance-and-audit.md#t4-pr-03) |
| F11 (resolved) | Versioning policy for external benchmark wire formats with named T7 consumers | Resolved in [T4-PR-03](provenance-and-audit.md#t4-pr-03) and [F11 Consumer Expectations](#f11-consumer-expectations) |

Option B ownership posture now applies to this subsection. F6 and F7
target T4 contract surfaces as post-closure amendments. F11 resolves
through a T4-side normative versioning rule in
[T4-PR-03](provenance-and-audit.md#t4-pr-03) and a T7-side consumer
expectation rule in this subsection, so the split remains recorded in
prose rather than as a new table column.

While any row in this subsection remains unresolved, the next packet
that attempts to freeze either wire format for scored benchmark use MUST
either resolve the applicable row directly or assign a remediation owner
in current gate tables. Canonization MUST NOT be claimed until all
applicable exit conditions in this table are satisfied.

### <a id="f11-consumer-expectations"></a>F11 Consumer Expectations

For future automation-heavy benchmark revisions or policy-influencing
calibration that consumes these surfaces, any T7
component that consumes `claim_provenance_index` or relies on embedded
`ClassificationTrace` semantics MUST declare exact support for specific
`claim_provenance_index_schema_version` values. Unsupported versions
MUST be rejected for those uses: no silent fallback, best-effort
coercion, or partial-compatibility claim is allowed. Support for a new
version requires an explicit consumer update before those benchmark uses
may rely on artifacts carrying that version.

## <a id="t4-br-06"></a>T4-BR-06: Narrative Factual-Claim Inventory

**NOT a G3 concern** ([T4-PR-08](provenance-and-audit.md#t4-pr-08)).
Narrative-only claims are not "accepted scout results." G3 is satisfied
internally by Tier 1 scouted chain. Narrative coverage is a synthesis
quality concern.

| Surface | Required Change | Owner | Target |
|---------|----------------|-------|--------|
| Narrative-claim inventory | Implement harness-side tool that enumerates factual claims from narrative prose and compares to claim ledger entries | T7 | New harness component |
| Ledger completeness checker | Flag narrative factual claims that lack ledger `[ref:]` entries as synthesis completeness failures | T7 | New harness component |
| Ledger coverage metric | `ledger_coverage_rate` (`ledger_factual_claims / total_factual_claims`) — downstream of the inventory. Requires gate-affecting threshold to create contract cost for omission | T7 | [benchmark.md:157](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md) |

The coverage metric cannot be defined independently of the inventory —
computing coverage requires enumerating narrative claims, which IS the
inventory problem.

## <a id="t4-br-07"></a>T4-BR-07: Benchmark-Execution Prerequisites

Any scored benchmark run in v1 MUST declare benchmark-scoped
`allowed_roots` and the per-system `max_evidence` values in
`manifest.json`. If the runtime can carry those values through
`scope_envelope`, it SHOULD do so. If it cannot, v1 permits procedural
enforcement through mirrored run instructions and post-hoc transcript
review. In addition, scored benchmark runs and pass/fail comparisons
MUST NOT proceed until all of the following v1 prerequisites are
operational.

### Four-Item v1 Prerequisite Gate

| # | Category | Prerequisite | What it gates |
|---|----------|-------------|---------------|
| 1 | Comparability | Same commit, working tree state, row prompt, posture, turn budget, model/reasoning settings, dialogue-timeout setting, and row-specific `allowed_roots` recorded for both baseline and candidate runs | Baseline/candidate pair is comparable |
| 2 | Scope and evidence discipline | Per-system `max_evidence` values defined in the benchmark contract, recorded in `manifest.json`, and raw-transcript review confirms scouting stayed within recorded `allowed_roots` | Search space and evidence budget are controlled |
| 3 | Artifact reviewability | `manifest.json`, `runs.json`, `adjudication.json`, `summary.md`, raw transcripts, and final syntheses are stored under a stable repo path with enough metadata to rerun or audit the comparison | Post-hoc review is possible |
| 4 | Manual adjudication | `adjudication.json` records manual claim inventory, per-claim labels, safety findings, and a second-pass completeness review for each run | `supported_claim_rate` and `false_claim_count` are grounded in a reviewed claim set |

### Enforcement

The operator MUST reject scored runs when any of (1)-(4) is unavailable.
Procedural scope enforcement is permitted in v1:
mechanical runtime rejection of out-of-scope scouting is preferred but
not required. A run with missing artifacts, missing completeness review,
or out-of-scope scouting in the raw transcript is invalid and must be
rerun from the same commit.

This v1 gate intentionally defers automation-heavy proof surfaces. The
following do NOT block scored runs under the narrowed benchmark contract:

- narrative-claim inventory tooling and ledger-completeness checker
- validator-grade methodology and invalid-run schemas
- methodology-threshold pass-rule extensions
- transcript parser, mechanical diff engine, and omission-audit proof

For `claim_provenance_index` and `ClassificationTrace`, the
[F6/F7/F11 provenance wire-format blockers](#f6-f7-f11-blockers) remain
relevant to future automation-heavy or policy-shaping benchmark
revisions, but they do not block the manual v1 benchmark defined in the
current benchmark contract.

This prerequisite remains independent of G3 (which governs scouted
provenance retention). Benchmark v1 still requires both: G3 accepted
(scouted provenance chain) and the four prerequisites above operational.

## <a id="t4-br-08"></a>T4-BR-08: Non-Scoring Run Classification

Non-scoring runs are permitted before the v1 prerequisites land, in
two classes:

**(a) Exploratory shakedowns** (schema validation, format testing,
integration checks) — permitted before any prerequisites, results are
non-evidentiary and MUST NOT inform benchmark policy, threshold setting,
or corpus calibration decisions that affect scored comparisons.

**(b) Benchmark rehearsals** (trial transcript capture, dry-run
adjudication, operator playbook rehearsal) — may mirror the scored
benchmark procedure, but remain non-evidentiary unless all four
prerequisites in [T4-BR-07](#t4-br-07) are satisfied and the resulting
artifacts are promoted into the scored comparison record.

Neither class may be used for pass/fail comparisons.

## <a id="t4-br-09"></a>T4-BR-09: Benchmark-Contract Amendment Dependencies

Ten amendment rows defining future automation-focused obligations. They
are retained as design inventory, but they are not prerequisites for the
manual benchmark v1 contract. They become load-bearing again if a future
benchmark revision reintroduces typed methodology thresholds,
schema-validated artifacts, automated omission proof, or validator-only
scope enforcement. T4 defines the future contract floor; T7 owns
schemas, implementations, and artifact naming.

| # | Surface | Required Change | Owner |
|---|---------|----------------|-------|
| 1 | Methodology finding format | Define finding row schema: `(run_id, inventory_claim_id, finding_kind, detection, ledger_claim_id?, detail)`. Five finding kinds: `under_reading` (judgment), `shape_inadequacy` (judgment), `misclassification` (judgment), `decomposition_skipped` (mechanical), `narrative_ledger_violation` (mechanical). Row keyed by `inventory_claim_id`. Optional `ledger_claim_id` cross-reference. `detail` MUST be typed object with per-kind required keys. T7 MUST publish validator-grade JSON Schema for `detail` before benchmark readiness | T7 |
| 2 | Methodology finding consequence | Add `methodology_finding_threshold` to benchmark contract (versioned). Value in `manifest.json`. Per-run methodology-gate check as pass-rule condition 5. Breach alone is not grounds for invalidation or rerun | T7 |
| 3 | Adjudication scope | Expand adjudicator authority to include candidate process artifacts (query traces, `ClassificationTrace`, claim ledger) alongside final synthesis | T7 |
| 4 | Mode-mismatch failure artifact | Define destination for invalid-run mode-mismatch details in `runs.json` as invalid-run entry | T7 |
| 5 | Benchmark-run scope formalization | Define scope configuration for compared runs: `scope_envelope` as run condition, `allowed_roots` equivalence, `source_classes` inclusion, `scope_root` selection rule for all query types. Justification-only policy insufficient: must be validator-enforceable | T7 |
| 6 | Evidence budget parameter | Define `max_evidence` value, bring under change control, record in `manifest.json` | T7 |
| 7 | Benchmark artifact auditability | Extend `manifest.json`/`runs.json` for post-hoc audit: run kind, scope config, benchmark parameters, config version/digest, harness toolchain identity. Per-step `scope_root` recoverable from transcript | T7 |
| 8 | Omission-audit proof surface | Persist derived omission-audit artifact per scored run. Contract floor: (a) run binding (`run_id`, transcript digest, toolchain identity), (b) evidence-record keyed entries, (c) completeness (every synthesis-active evidence record covered, all per-step metadata recovered, no unresolved failures), (d) manifest binding (artifact digest). T7 MUST publish validator-grade schema before benchmark readiness | T7 |
| 9 | Allowed-scope safety | Define secret handling policy for allowed-scope content and redaction/provenance interaction | T7 |
| 10 | Transcript format/parser/diff | Parseable format spec, parser implementation, diff engine implementation | T7 |

### Methodology Finding Detail Types

Required keys by finding kind (T4's contract floor — T7 MAY add
extension keys but MUST NOT remove or redefine required keys):

| Finding Kind | Detection | Required Detail Keys |
|---|---|---|
| `under_reading` | judgment | `read_scope: str`, `required_scope: str`, `contradiction_summary: str` |
| `shape_inadequacy` | judgment | `claim_shape: str`, `query_set_summary: str`, `gap_summary: str` |
| `misclassification` | judgment | `agent_classification: str`, `adjudicator_classification: str`, `rationale: str` |
| `decomposition_skipped` | mechanical | `t4_claim_id: int`, `failed_criterion: 1\|2\|3`, `decomposition_attempted: bool` |
| `narrative_ledger_violation` | mechanical | `violation_type: str`, `narrative_claim_text: str`, `ledger_match_status: str` |

`t4_claim_id` is the integer `claim_id` from T4's
`claim_provenance_index` ([T4-PR-03](provenance-and-audit.md#t4-pr-03));
`failed_criterion` uses the same `1|2|3` values as
`ClassificationTrace.failed_criterion`
([scouting-behavior: claim classification](scouting-behavior.md#t4-sb-05)).
