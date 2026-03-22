# CCDI Spec Remediation Plan — Round 5

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-21)
**Scope:** 45 canonical findings + 1 late-filed (1 P0, 24 P1, 21 P2) across 8 normative files
**Spec:** `docs/superpowers/specs/ccdi/` (9 files, 8 normative + 1 non-normative)
**Dominant pattern:** Testing strategy coherence (30% of findings), authority placement gaps, schema prose/definition mismatches

## Strategy

Six tasks in three phases, ordered by dependency and priority:

1. **P0 + test table coherence** — delivery.md test descriptions match normative behavior
2. **Schema ghost fields + prose errors** — remove phantom references, fix mechanism attribution
3. **Design decisions** — resolve 4 contested behavioral specs before structural edits
4. **Authority placement + contract precision** — cross-file structural moves (blocked on 3)
5. **Testing gap specifications** — add missing test specs (blocked on 1, 2, 4)
6. **P2 batch** — remaining 21 lower-priority findings (blocked on 4)

Rationale: Tasks 1–3 are independent and can proceed in parallel. Task 3 gates the critical path because 4 design questions must be answered before 7+ downstream edits (Task 4) can land. Task 5 must wait for normative text to stabilize — writing test specs against text that's about to change is wasted work. Task 6 is lower priority and can be deferred to a separate session if needed.

**Late-filed findings:** CE-12 through CE-15 were filed after synthesis. CE-12 (cooldown exemption authority) is genuinely new (incorporated into Task 4). CE-13 argues SY-27 severity should be P1, not P2. CE-14 and CE-15 reinforce SY-13 and SY-14 with deeper cross-source analysis.

---

## Task 1 — P0: Test Table Coherence

**Finding count:** 1 P0 + 3 P1 = 4 findings
**Files:** delivery.md
**Depends on:** nothing — can start immediately

### P0

#### [SY-2] test_validate_graduation.py test inputs describe a different validator

**Source:** CC-3, VR-1 (independent convergence — strongest corroboration)
**File:** delivery.md lines 107–119

The test table inputs ("shadow registry + active inventory with matching topics," "TTL consistency check") describe a registry-vs-inventory validator. The graduation protocol (step 4) says `validate_graduation.py` checks: `annotations.jsonl` line count, `false_positive_rate` arithmetic, diagnostics file count, metric consistency. An implementer cannot write the test.

Fix: Rewrite test table rows to match the protocol. New inputs: (a) annotations.jsonl with correct/incorrect line count vs. `labeled_topics`, (b) false_positive_rate formula yields different value than stored, (c) diagnostics directory with wrong file count, (d) yield/latency arithmetic inconsistency. If the validator should ALSO cross-check shadow registry vs. active inventory, add that behavior to the protocol step and update both.

### Coupled P1 Findings

#### [SY-16] Layer count mismatch: "Three-Layer" heading vs four-row table

**Source:** CC-1
**File:** delivery.md lines 123–130; decisions.md line 41

Fix: Label all four rows: "Layer 1: Unit tests," "Layer 2a: Replay harness," "Layer 2b: Agent sequence tests," "Layer 3: Shadow mode." Update the heading to "Four-Layer Approach (Layer 2 has two sub-layers)". Update decisions.md locked decision accordingly.

#### [SY-17] multi_pending_facets fixture uses invalid Facet values

**Source:** CC-2
**File:** delivery.md lines 544–547

Fix: Replace `"security"` and `"performance"` with valid Facet enum values (`"schema"` and `"config"` are semantically distinguishable). Update expected output arrays.

#### [SY-18] Chunk-ordering test false attribution

**Source:** CC-4
**File:** delivery.md line 308; packets.md lines 118–127

Fix: Either (a) add the render order ("citations first, then summary, then verbatim snippets") to `packets.md#build-process` as step 7's specification, or (b) remove the ordering claim from the test case if it is implementation-defined. Option (a) preferred — the ordering is a reasonable normative choice.

---

## Task 2 — Schema Ghost Fields + Prose Errors

**Finding count:** 5 P1
**Files:** data-model.md, registry.md
**Depends on:** nothing — can start immediately, parallel to Task 1

All fixes are straightforward prose corrections with no design decisions needed.

#### [SY-3] Ghost `schema_version` in RegistrySeed null-field serialization note

**Source:** SP-5, SP-10, VR-12 (cross-lens confirmation)
**File:** data-model.md line 268

Fix: Remove `schema_version` from the null-field note. The correct non-nullable envelope field is `inventory_snapshot_version`. Rewrite: "Non-nullable fields (`inventory_snapshot_version`) are always present with their concrete values."

#### [SY-4] `confidence` field ghost reference in suppressed→detected re-entry

**Source:** SP-2, VR-11 (cross-lens confirmation)
**File:** registry.md line 109

Fix: Remove `confidence` from the retention list. The sentence should read: "retain prior values for `coverage_target` and `facet`." `consecutive_medium_count` already encodes confidence-relevant scheduling history.

#### [SY-5] registry.md references nonexistent `--prepare` CLI flag

**Source:** CE-2
**File:** registry.md line 245

Fix: Replace "populated by `--prepare`" with "written by `ccdi-gatherer` into the RegistrySeed sentinel block (see data-model.md#registryseed) and consumed by the agent during the initial CCDI commit phase."

#### [SY-11] `absent` state used in state machine but not defined in entry structure

**Source:** SP-1
**File:** registry.md lines 18, 74–79

Fix: Add clarifying note to the `TopicRegistryEntry.state` field: "`absent` is not a persisted field value — it means no entry exists in the `entries[]` array for that `topic_key`. An entry with any persisted state value is by definition not absent."

#### [SY-12] DenyRule build-time vs load-time validation divergence undocumented

**Source:** SP-3
**File:** data-model.md lines 96–104

Fix: Add schema invariant note: "The compiled inventory (`topic_inventory.json`) may contain DenyRules that were valid under a prior schema version but are invalid under the current schema — load-time validation handles this via warn-and-skip per the resilience principle. Build-time enforcement prevents new invalid rules; load-time tolerance preserves backward compatibility."

---

## Task 3 — Design Decisions for Contested Behaviors ✅ RESOLVED

**Finding count:** 4 P1
**Files:** data-model.md, registry.md, integration.md, delivery.md
**Depends on:** nothing
**Status:** All 4 decisions resolved via Codex dialogue (thread `019d138b-0642-79c2-8361-0d76d54fd6c4`, 5 turns, collaborative posture, all converged with high confidence)

#### [SY-13 + CE-14] results_file stripping → **Load-time invariant model**

**Resolution:** `results_file` is stripped from the in-memory registry representation on CLI registry load (unconditionally). Write-back is automatic because all writes serialize the full state. The 4 conflicting sources are reconciled:
- data-model.md "strip before writing back" = observable effect of load-time invariant
- registry.md "strip from in-memory on load" = the mechanism (this was closest)
- integration.md `--mark-injected` stripping = redundant defense-in-depth
- delivery.md "stripped at write time" = test assertion about observable effect

Key insight: The `/dialogue` skill may still read `results_file` from the transport envelope (sentinel seed) before CLI handoff — the transport/live-registry boundary is the distinction.

**Spec edits:** data-model.md:252, registry.md:245, integration.md:43, delivery.md:363

#### [SY-14 + CE-15] docs_epoch comparison → **Pinned inventory snapshot via `--inventory-snapshot`**

**Resolution:** Comparison source is the active dialogue's pinned inventory snapshot `docs_epoch`, passed via `--inventory-snapshot` flag on all full-CCDI CLI commands (`dialogue-turn` and `build-packet`). The registry file's envelope `docs_epoch` becomes pure traceability.

**Emerged:** `dialogue-turn` should scan ALL `suppressed:weak_results` entries each turn for epoch comparison, independent of classifier presence. This creates an intentional asymmetry: `weak_results` gets full-registry scan, `redundant` stays classifier/hint-triggered only. (Suppression staleness and topic relevance are separate concerns.)

**Spec edits:** integration.md:16-18 (add flag), integration.md:54 (widen scan), registry.md:108-109 (split into two clauses), data-model.md:277,280 (docs_epoch → traceability only), delivery.md (new test: epoch-only re-entry without classifier hit)

#### [SY-15] deferred_ttl → **Durable within dialogue (crash recovery scope)**

**Resolution:** The registry file is dialogue-scoped. `deferred_ttl` persists only across reloads of the same registry within an ongoing dialogue, including abnormal process interruption. A new `/dialogue` session starts from a new RegistrySeed and does not inherit deferred entries. The `deferred_ttl:0` load-time handling is crash recovery, not cross-session continuity.

**Spec edits:** data-model.md RegistrySeed section, registry.md TTL Lifecycle section

#### [SY-7] Initial-mode facet consistency → **Documented absence with rationale**

**Resolution:** Neither MUST with cross-check nor SHOULD (wrong RFC 2119 semantics — SHOULD implies "recommended but skippable" when the mechanism is intentionally absent because unnecessary). Add a rationale clause: "Initial mode does not require a runtime facet cross-check because both the prepare-phase ranking facet and the commit-phase facet originate from the same `ClassifierResult.resolved_topics[].facet` via the RegistrySeed."

**Spec edits:** integration.md:37 (add rationale clause)

#### Unresolved (non-blocking)

`last_seen_turn` field semantics on epoch-only re-entry: should it mean "last classifier/hint observation" or "last meaningful state touch"? Decide during T4 implementation.

---

## Task 4 — Authority Placement + Contract Precision

**Finding count:** 6 P1 + T3 decision implementations = 10 edits
**Files:** classifier.md, integration.md, registry.md, decisions.md, data-model.md, delivery.md
**Depends on:** Task 3 (design decisions inform the content of these edits)

### Authority Placement

#### [SY-1] classifier.md type extension outside authority boundary

**Source:** CE-1, AA-7 (cross-lens confirmation)
**File:** classifier.md lines 68–71

Fix: Replace the Note with a forward reference: "The `dialogue-turn` candidates JSON extends this type — see [integration.md#dialogue-turn-candidates-json-schema]."

#### [SY-9] Shadow Mode Gate under delivery authority outside behavior_contract chain

**Source:** AA-1
**Files:** delivery.md → integration.md (content move)

Fix: Move the normative startup gate logic (what file to read, what field values mean, what default applies when absent) from `delivery.md` to `integration.md` under `behavior_contract` authority. `delivery.md` retains the graduation protocol and kill criteria (legitimately `implementation_plan`).

#### [SY-10] decisions.md behavioral invariants as sole enforcement points

**Source:** AA-2
**Files:** decisions.md, integration.md (cross-references)

Fix: Cross-reference each binding invariant into the appropriate component contract. `*ccdi_config*` read prohibition → add explicit statement in `integration.md`. Scout pipeline isolation → add statement in `integration.md` data flow section. decisions.md constraints become backstops, not primary enforcement points.

#### [CE-12] Cooldown exemption in wrong authority file (late-filed)

**Source:** CE-12 (followup from VR-3)
**Files:** registry.md, integration.md

Fix: Move exemption into `registry.md` scheduling step 5: "This limit applies only to `candidate_type: 'new'` candidates. `pending_facet` and `facet_expansion` candidates are exempt." Remove duplicate from integration.md (or retain as non-normative cross-reference).

### Contract Precision

#### [SY-6] Shadow-mode registry invariant contradictory in isolation

**Source:** CE-3
**File:** integration.md lines 353–354

Fix: Rewrite invariant sentence to be complete on first read: "In shadow mode, the only permitted registry mutations are automatic suppressions written by `build-packet` empty output. Agent-driven mutations — `--mark-injected` and `--mark-deferred` — are prohibited."

#### [SY-8] suppressed→detected field update packs two behavioral paths

**Source:** CE-7
**File:** registry.md line 109

Fix: Split into two rows: (a) `suppressed → detected (re-entry, topic in classifier output)` — refresh coverage_target/facet from classifier, and (b) `suppressed → detected (re-entry, docs_epoch-triggered, topic absent from classifier)` — retain prior values.

### T3 Decision Implementations (resolved via Codex dialogue)

#### [SY-13] results_file → load-time invariant

- data-model.md:252 — Rewrite to: "`results_file` is stripped from the in-memory registry representation on CLI registry load. All subsequent writes serialize the stripped state. The `/dialogue` skill reads `results_file` from the transport envelope (sentinel seed) before CLI handoff."
- registry.md:245 — Align failure mode to load-time invariant model
- integration.md:43 — Reframe `--mark-injected` stripping as defense-in-depth, cross-reference data-model.md
- delivery.md:363 — Update test wording: "absence observed on first successful write after load-time sanitization"

#### [SY-14] docs_epoch → pinned inventory snapshot

- integration.md:16-18 — Add `--inventory-snapshot <path>` to `dialogue-turn` and `build-packet` CLI signatures (required on all full-CCDI calls)
- integration.md:54 — Widen suppression re-entry: `dialogue-turn` scans ALL `suppressed:weak_results` entries each turn for epoch comparison, independent of classifier presence. `redundant` stays classifier/hint-triggered only.
- registry.md:108 — Rewrite: "`suppressed_docs_epoch` ← current pinned inventory snapshot's `docs_epoch`"
- registry.md:109 — Split `suppressed→detected` into two clauses: classifier-present vs epoch-only re-entry
- data-model.md:277,280 — Clarify `docs_epoch` is traceability only ("not modified after initial write" preserved)
- delivery.md — Add new test: `weak_results` re-entry on epoch change without classifier hit

#### [SY-15] deferred_ttl → dialogue-scoped (crash recovery)

- data-model.md RegistrySeed section — Add: "The registry file is dialogue-scoped. `deferred_ttl` persists only across reloads of the same registry within an ongoing dialogue, including abnormal process interruption. A new `/dialogue` session starts from a new RegistrySeed and does not inherit deferred entries from prior dialogues."
- registry.md TTL Lifecycle section — Add dialogue-scope clarification

#### [SY-7] facet consistency → documented absence with rationale

- integration.md:37 — Add rationale clause: "Initial mode does not require a runtime facet cross-check because both the prepare-phase ranking facet and the commit-phase facet originate from the same `ClassifierResult.resolved_topics[].facet` via the RegistrySeed. The RegistrySeed entry is the single source of truth for initial-mode commit."

---

## Task 5 — Testing Gap Specifications

**Finding count:** 6 P1
**Files:** delivery.md
**Depends on:** Tasks 1, 2, 4 (normative text must be stable before adding test specs)

All fixes add test specifications to delivery.md for normative behavioral rules that currently have no test coverage.

#### [SY-19] ccdi_trace action values lack individual verification

Fix: Add `trace_assertions` to replay fixtures asserting specific `action` values: `happy_path` → `"inject"`, `scout_defers_ccdi` → `"skip_scout"`, suppression → `"suppress"`.

#### [SY-20] pending_facet/facet_expansion cooldown exemption untested

Fix: Add `pending_facet_exempt_from_cooldown.replay.json`: turn with one `new` topic (consumes cooldown) + one `pending_facet` → assert `pending_facet` processed in same turn.

#### [SY-21] validate_graduation.py failure modes unspecified

Fix: Add failure-mode tests: (a) missing annotations.jsonl → non-zero exit, (b) malformed JSONL → non-zero exit, (c) missing diagnostics/ → non-zero exit, (d) floating-point tolerance for false_positive_rate.

#### [SY-22] Cross-key config validation (min > max) untested

Fix: Add test: `initial_token_budget_min=800, max=600` → both fall back to defaults as a pair, single warning emitted.

#### [SY-23] Shadow mode automatic suppression IS written but untested

Fix: Add Layer 2b test: shadow mode + candidate with weak search results → assert registry file contains `suppressed` state entry. Completes three-part shadow invariant coverage.

#### [SY-24] deferred→deferred TTL-reset with non-default config

Fix: Add CLI integration test: `deferred_ttl_turns=5` config, topic deferred (TTL=5), absent at TTL=0 → TTL resets to 5, state remains `deferred`.

---

## Task 6 — P2 Findings Batch

**Finding count:** 21 P2
**Files:** various (packets.md, data-model.md, registry.md, integration.md, decisions.md, foundations.md, delivery.md)
**Depends on:** Task 4 (some P2s touch same files and sections as T4 edits)

### Authority & Metadata (5)

| ID | Fix |
|----|-----|
| SY-25 | Move packets.md shadow mode behavioral constraint to integration.md + add delivery→packet-contract boundary rule |
| SY-27 | Add `registry-contract` to persistence_schema chain in spec.yaml, OR consolidate RegistrySeed entry fields into data-model.md. **Note:** CE-13 argues this is P1 severity — evaluate during implementation. |
| SY-28 | Move ccdi_trace MUST invariants to integration.md under interface_contract authority |
| SY-29 | Add `supporting` row to README.md authority table to match "9 authorities" claim |
| SY-30 | Add cross-reference in decisions.md shadow-mode constraint linking to integration.md |

### Contract Precision (5)

| ID | Fix |
|----|-----|
| SY-26 | Fix packets.md anchor: `#shadow-mode-kill-criteria` → `#shadow-mode-gate` |
| SY-31 | Clarify scheduling step 2 "materially new" for deferred topics at high confidence |
| SY-32 | Add staleness note to deferred→deferred row for coverage_target/facet |
| SY-33 | Add inline comments explaining scout_priority vs target_mismatch behavioral asymmetry |
| SY-34 | Document topic_key hint constraint as structurally self-enforcing via schema omission |

### Cross-Reference & Coherence (2)

| ID | Fix |
|----|-----|
| SY-35 | Either add turn labels to Review Dialogue table or remove "Review Turn 4" citation |
| SY-36 | Change foundations.md "behavioral definition" to "specification" in link text |

### Testing (3)

| ID | Fix |
|----|-----|
| SY-37 | Remove HTML comment (Known Open Items table is the correct tracking mechanism) |
| SY-38 | Replace trivially-true value assertion with key-presence test |
| SY-39 | Specify subprocess fixture stdin delivery mechanism for PostToolUse hook payload |

### Schema (6)

| ID | Fix |
|----|-----|
| SY-40 | Add schema-level constraint: override_config ↔ rule_id pattern requirement |
| SY-41 | Add note: "No other cross-key constraints defined" to close loophole |
| SY-42 | Add schema-level additive-only invariant for CompiledInventory schema versions |
| SY-43 | Explicitly list all operations subject to alias weight clamping |
| SY-44 | Specify add_deny_rule id uniqueness constraint (recommend: reject on duplicate) |
| SY-45 | Add: "Config key values MUST NOT be null — use built-in default with warning" |

---

## Decision Gates

| After | Condition | Path A | Path B |
|-------|-----------|--------|--------|
| T3 | ✅ All 4 decisions resolved | T4 is unblocked — load-time invariant, pinned snapshot via `--inventory-snapshot`, dialogue-scoped TTL, documented absence with rationale | N/A |
| T4 (SY-27/CE-13) | Upgraded to P1 | spec.yaml modification required before T6 can close authority split | T6 proceeds without spec.yaml changes |

## Critical Path

**Scheduling:** ~~T3 →~~ T4 → T5 (T3 resolved, T4 is now the next critical step)

**Highest-risk task:** T4 (authority placement + contract precision) — likelihood: low; impact: medium; on critical path: yes. 6 P1 fixes + 4 T3 decision implementations across 6 files. The docs_epoch resolution adds an interface change (`--inventory-snapshot` flag) and a new re-entry asymmetry by suppression reason — these are the most complex edits.

**Recommended first move:** Start T1 (clears the P0), T2 (ghost fields), and T4 (authority + T3 implementations) in parallel. T1 and T2 are independent of T4; all three can proceed simultaneously.

## Out of Scope (Parked)

- **spec.yaml authority model changes** — Adding registry-contract to persistence_schema chain affects authority resolution globally. Decide after T4.
- **Anchor resolution exhaustiveness** — Review sampled cross-references; a full audit is separate work.
- **integration-enforcement reviewer** — Not spawned (no enforcement_mechanism claim). Enforcement gaps partially covered.
- **Overlay operational completeness** — Whether all needed overlay operations are defined was out of review scope.
