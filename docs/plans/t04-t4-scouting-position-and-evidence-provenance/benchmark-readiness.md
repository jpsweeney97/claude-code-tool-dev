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
implementation are separate T7 deliverables gated by prerequisite item 8
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

Any benchmark run (scored comparison, calibration dry run, or schema
shakedown) MUST have `scope_envelope` with non-empty `allowed_roots`
present in the consultation configuration
([containment](containment.md) — containment is inoperative
without it). In addition, **scored benchmark runs and pass/fail
comparisons** MUST NOT proceed until ALL of the following T7 dependencies
are operational:

### Eight-Item Prerequisite Gate

| # | Category | Prerequisite | What it gates |
|---|----------|-------------|---------------|
| 1 | Artifact completeness | Narrative-claim inventory and ledger completeness checker | `supported_claim_rate` computed against complete population |
| 2 | Artifact completeness | Methodology-finding format defined in `adjudication.json` schema (five finding kinds, `detection` field, `inventory_claim_id` key, typed `detail` object per finding kind) | `adjudication.json` structural completeness |
| 3 | Artifact completeness | Mode-mismatch invalid-run schema defined in `runs.json` schema | `runs.json` structural completeness |
| 4 | Artifact completeness | `methodology_finding_threshold` defined in benchmark contract and recorded in `manifest.json` | Pass-rule condition 5 evaluable |
| 5 | Comparability and auditability | Benchmark-relevant scope configuration formalized: `scope_envelope` with non-empty `allowed_roots` as run condition, `allowed_roots` equivalence rule for compared runs, `source_classes` inclusion or explicit irrelevance, and `scope_root` selection rule for all query types including conceptual queries | Compared runs operate on equivalent search space |
| 6 | Comparability and auditability | `max_evidence` defined in benchmark contract, recorded in `manifest.json`, and under benchmark change control | Evidence budget is a controlled parameter |
| 7 | Comparability and auditability | Benchmark artifact contract extended for post-hoc compliance audit (run kind, resolved scope config, benchmark parameters, benchmark config version or digest, harness toolchain identity in `manifest.json`/`runs.json`; per-step `scope_root` recoverable from run transcript) | Run-condition compliance verifiable after the fact |
| 8 | Operational readiness and proof | Transcript parser and mechanical diff engine produce the derived omission-audit proof surface for the scored transcript. Acceptance test: proof surface present, run-bound, evidence-record complete, extraction-failure-free. Absence or incompleteness invalidates scored run | T4's omission surface ([T4-PR-11](provenance-and-audit.md#t4-pr-11)) is both computable and provably computed |

### Enforcement

The benchmark runner or manifest validator MUST reject scored runs when
any of (1)-(8) is unavailable. Items (1)-(7) are verifiable from
artifact metadata. Item 8 is verifiable from the derived omission-audit
proof surface: the runner produces it, the manifest records its digest,
and a post-hoc validator confirms run binding, evidence-record
completeness, and absence of extraction failures.

Without (1), `supported_claim_rate`
([benchmark.md:160](../../superpowers/specs/codex-collaboration/dialogue-supersession-benchmark.md))
is computed against an incomplete claim population — the comparison is
contaminated, not merely degraded. Without (2)-(4), benchmark artifacts
are incomplete: `adjudication.json` and `runs.json` lack structures T4
requires, and the pass rule cannot evaluate condition 5.

Items 1-4 gate **artifact completeness**: without them, `adjudication.json`,
`runs.json`, and the pass rule lack structures T4 requires. Items 5-7
gate **comparability and auditability**: without formalized scope, a
defined evidence budget, and auditable artifact metadata, runs are not
comparable and compliance is not verifiable even if artifacts are
structurally complete. Item 8 gates **operational readiness and
run-level proof**: without parser and diff engine producing the derived
omission-audit artifact, T4's authoritative omission surface is specified
but neither computable nor provably computed for a given run.

This prerequisite is independent of G3 (which governs scouted provenance
retention). Benchmark-readiness requires BOTH: G3 accepted (scouted
provenance chain) AND all eight T7 dependencies above operational.

## <a id="t4-br-08"></a>T4-BR-08: Non-Scoring Run Classification

Non-scoring runs are permitted before the eight prerequisites land, in
two classes:

**(a) Exploratory shakedowns** (schema validation, format testing,
integration checks) — permitted before any prerequisites, results are
non-evidentiary and MUST NOT inform benchmark policy, threshold setting,
or corpus calibration decisions that affect scored comparisons.

**(b) Policy-influencing calibration** (corpus calibration per
[scouting-behavior: claim classification](scouting-behavior.md#t4-sb-05),
classification criteria tuning, threshold setting) — require all eight
prerequisites because their conclusions shape the benchmark's rules.

**Exception:** the initial `methodology_finding_threshold` value is a
benchmark contract decision (T7-owned), not a calibration output;
calibration validates it empirically and may propose adjustment under
benchmark change control.

Neither class may be used for pass/fail comparisons.

## <a id="t4-br-09"></a>T4-BR-09: Benchmark-Contract Amendment Dependencies

Ten amendment rows defining T7 obligations. T4 defines the contract
floor; T7 owns schemas, implementations, and artifact naming.

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
