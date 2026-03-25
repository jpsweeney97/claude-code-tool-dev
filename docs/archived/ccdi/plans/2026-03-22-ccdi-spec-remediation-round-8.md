# CCDI Spec Remediation Plan — Round 8

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 62 findings (1 P0, 34 P1, 27 P2) from the CCDI spec review round 8.

**Architecture:** Spec text edits organized by file-section locality to enable parallel execution within phases. Verification test specifications (delivery.md) are sequenced after normative text changes to ensure test specs reference stable prose.

**Tech Stack:** Markdown spec files in `docs/superpowers/specs/ccdi/`

---

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 62 canonical findings (1 P0, 34 P1, 27 P2) across 8 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/ccdi/` (9 normative files + 1 supporting + spec.yaml)

## Strategy

Seven tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Five tasks, all parallel (touch non-overlapping sections of shared files):
   - **T1:** P0 + shadow-mode P1s (4) — integration.md §shadow-mode-registry-invariant, §ccdi_trace
   - **T2:** Schema defaults + serialization invariants (7 P1) — data-model.md §schema-evolution, §RegistrySeed
   - **T3:** Authority + cross-reference corrections (6 P1) — delivery.md §shadow-mode-gate + §diagnostics + §ccdi_trace, decisions.md §normative-constraints, registry.md §entry-structure
   - **T4:** Contract enforcement gaps (7 P1) — integration.md §CLI-tool + §failure-modes + §pipeline-isolation, registry.md §field-update-rules + §suppression-re-entry, data-model.md §config-overrides
   - **T5:** Version axes + chunk determinism (4 P1) — data-model.md §version-axes + §failure-modes, packets.md §build-process

2. **Phase 2** — After Phase 1 (normative text must be stable):
   - **T6:** Verification gap specifications (8 P1) — delivery.md test tables + fixture specs

3. **Phase 3** — After Phase 1:
   - **T7:** P2 batch (27 P2) — all files

**Rationale:** T1–T5 touch non-overlapping sections of shared files — safe to parallelize. T6 adds test specifications in delivery.md that reference normative text established by T1–T5 (VR-2 depends on CE-1's shadow-mode split from T1, VR-5 depends on CC-2's hash rule from T1, VR-7 references the action enum from T1). T7 is lowest priority.

**Dependency chains:**
1. CE-1/CE-4 (T1) → VR-2 (T6): shadow-mode enforcement model must be stable before writing test specs
2. CC-2 (T1) → VR-5 (T6): `classify_result_hash` computation rule must be in integration.md
3. CE-6 (T4) → delivery.md test (T6): `--inventory-snapshot` failure mode row must exist
4. SY-1 (T2) → future tests: "normal mutation" definition must exist before referencing
5. SP-6 (T2) → VR-3 (T7, P2): FIFO invariant must be in data-model.md before raw JSON test

**Commit strategy:**
1. `fix(spec): remediate 1 P0 + 3 P1 shadow-mode and trace findings from ccdi spec review round 8` (T1)
2. `fix(spec): remediate 7 P1 schema + 6 P1 authority findings from ccdi spec review round 8` (T2+T3)
3. `fix(spec): remediate 7 P1 contract + 4 P1 version axis findings from ccdi spec review round 8` (T4+T5)
4. `fix(spec): remediate 8 P1 verification gap findings from ccdi spec review round 8` (T6)
5. `fix(spec): remediate 27 P2 findings from ccdi spec review round 8` (T7)

**Design decisions (inline):**
- CE-4: Add `shadow_suppressed: boolean` field to trace entries (less disruptive than new action values)
- CE-10: Add explicit type discrimination statement (less disruptive than new `entry_type` field)
- AA-6: Update authority note to acknowledge test-consumer contract (less disruptive than changing spec.yaml claims)
- CC-4: Add `"unavailable"` as third valid `status` value in diagnostics schema
- SP-1: Retitle table in data-model.md rather than relocating across files
- CC-9 (P2): Remove `CONSUMERS.md` option, keep "comment in handler" only

---

## Task 1 — P0 + Shadow-Mode Enforcement (4 findings)

**Finding count:** 1 P0 + 3 P1
**Files:** integration.md
**Depends on:** nothing — start immediately
**Design decisions:** 1 inline choice (CE-4 disambiguation approach)

### [CE-1] Shadow-mode invariant conflates CLI-flag-enforced and agent-enforced prohibitions

**Sources:** CE-1 (P0)
**File:** integration.md line 410 (shadow-mode registry invariant)

- [ ] **Step 1: Replace the shadow-mode registry invariant paragraph**

Replace the single paragraph at line 410:

Old:
```
**Shadow-mode registry invariant:** In shadow mode, the only permitted registry mutations are automatic suppressions written by `build-packet` empty output (`suppressed: weak_results` or `suppressed: redundant`). All three other mutation types are prohibited: (1) agent-driven `--mark-injected` (Step 7.5), (2) agent-driven `--mark-deferred` (Step 5.5), and (3) `dialogue-turn` cooldown deferral writes (Step 5.5, line 62). The prepare cycle runs to measure yield and latency for diagnostics, but the registry reflects only classifier-driven state. Deferral state is recorded in diagnostics only. This prevents shadow-mode registry pollution from corrupting graduation kill-criteria metrics. See [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints).
```

New:
```
**Shadow-mode registry invariant:** In shadow mode, the only permitted registry mutations are automatic suppressions written by `build-packet` empty output (`suppressed: weak_results` or `suppressed: redundant`). All other mutation types are prohibited, enforced at two distinct layers:

**CLI-enforced (via `--shadow-mode` flag):** `dialogue-turn` cooldown deferral writes (Step 5.5, line 62) are suppressed when the `--shadow-mode` flag is passed. The CLI itself prevents the `deferred: cooldown` state write — no agent logic is involved. `candidate_type: 'new'` entries excluded by the cooldown limit remain in `detected` state.

**Agent-enforced (via agent abstention):** The agent MUST NOT call `--mark-injected` (Step 7.5) or `--mark-deferred` (Step 5.5) in shadow mode. These are agent-initiated CLI calls, not CLI-internal behavior — the prohibition requires the agent to not invoke these commands.

The prepare cycle runs to measure yield and latency for diagnostics, but the registry reflects only classifier-driven state. Deferral state is recorded in diagnostics only. This prevents shadow-mode registry pollution from corrupting graduation kill-criteria metrics. See [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints).
```

- [ ] **Step 2: Verify cross-references**

Confirm that delivery.md Layer 2b tests referencing `shadow-mode-registry-invariant` still resolve (the anchor name is unchanged).

---

### [CE-4] `skip_cooldown` trace action has dual semantics across modes

**Sources:** CE-4 (P1)
**File:** integration.md lines 299–300 (action normative values table)
**Design decision:** Add `shadow_suppressed: boolean` field to per-turn trace entries (option a). Less disruptive than introducing new action values which would require updating all trace consumers and delivery.md test fixtures.

- [ ] **Step 3: Update `skip_cooldown` action description**

In the action normative values table, replace the `skip_cooldown` row:

Old:
```
| `skip_cooldown` | Topic deferred due to per-turn cooldown (`deferred: cooldown` state written by `dialogue-turn` in active mode). In shadow mode, `skip_cooldown` is emitted even though the `deferred: cooldown` registry write is suppressed (per the shadow-mode exception on line 62). The `skip_cooldown` trace entry records the active-mode action; a separate `shadow_defer_intent` entry with `reason: "cooldown"` is emitted to the counterfactual log per [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). |
```

New:
```
| `skip_cooldown` | Topic deferred due to per-turn cooldown. In active mode: `deferred: cooldown` state written by `dialogue-turn`, `shadow_suppressed: false`. In shadow mode: registry write suppressed by `--shadow-mode` flag, `shadow_suppressed: true`, and a separate `shadow_defer_intent` entry with `reason: "cooldown"` is emitted per [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). Consumers MUST check `shadow_suppressed` to determine whether the registry mutation actually occurred. |
```

- [ ] **Step 4: Add `shadow_suppressed` field to trace entry schema**

After the 8-key requirement paragraph (line 284), add:

```
**`shadow_suppressed` field:** Each per-turn trace entry includes a `shadow_suppressed: boolean` field (9th field, not counted in the 8-key invariant for backward compatibility). Value is `true` when the trace entry describes an action whose registry mutation was suppressed by `--shadow-mode` (currently only `skip_cooldown`); `false` otherwise. This field disambiguates whether the registry mutation described by the `action` value actually occurred.
```

---

### [CE-10] `shadow_defer_intent` entries lack type discriminator in trace array

**Sources:** CE-10 (P1)
**File:** integration.md lines 283–286 (ccdi_trace output contract)

- [ ] **Step 5: Add type discrimination guidance**

After the `shadow_defer_intent` exception paragraph (line 285), add:

```
**Type discrimination:** The `ccdi_trace` array contains two structurally different entry types: per-turn entries (8+ keys) and `shadow_defer_intent` entries (5 keys). Trace consumers MUST filter entries by `action` value before applying key-presence requirements. The 8-key invariant applies only to entries where `action != "shadow_defer_intent"`. Code iterating the trace array MUST NOT assume all entries have the same structure.
```

---

### [CC-2] `classify_result_hash` computation rule defined only in delivery.md

**Sources:** CC-2 (P1)
**File:** integration.md lines 304–310 (shadow_defer_intent entry schema)

- [ ] **Step 6: Add computation rule to integration.md**

After the `classify_result_hash` field description in the `shadow_defer_intent` schema paragraph (line 310), add:

```
**`classify_result_hash` computation:** Hash of the classifier result for topic T. The hash MUST include `confidence`, `facet`, and `matched_aliases` (not just `topic_key`) — same `topic_key` with different `matched_aliases` MUST produce different hashes. Same classify payload MUST produce the same hash (stability invariant). See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for collision requirements and repeat-detection semantics.
```

- [ ] **Step 7: Commit T1**

```bash
git add docs/superpowers/specs/ccdi/integration.md
git commit -m "fix(spec): remediate 1 P0 + 3 P1 shadow-mode and trace findings from ccdi spec review round 8

Findings addressed:
- CE-1 (P0): Split shadow-mode invariant into CLI-enforced (--shadow-mode flag)
  and agent-enforced (abstention from --mark-injected/--mark-deferred) layers
- CE-4 (P1): Add shadow_suppressed boolean field to disambiguate skip_cooldown
  across active/shadow modes
- CE-10 (P1): Add type discrimination guidance for shadow_defer_intent entries
- CC-2 (P1): Add classify_result_hash computation rule to integration.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2 — Schema Defaults + Serialization Invariants (7 findings)

**Finding count:** 7 P1
**Files:** data-model.md
**Depends on:** nothing — start immediately (parallel with T1, T3, T4, T5)

### [SP-1] Schema Field Defaults table misplaced under CompiledInventory

**File:** data-model.md line 54 (Schema Field Defaults heading)

- [ ] **Step 1: Retitle the Schema Field Defaults subsection**

Old:
```
**Schema Field Defaults:** These defaults are used when loading a registry file serialized under an older schema version. Fields absent in the loaded version are initialized to these values.
```

New:
```
**Registry Entry Schema Field Defaults:** These defaults are used when loading a registry file serialized under an older schema version. Fields absent in the loaded `TopicRegistryEntry` are initialized to these values. Although placed here under the Schema Evolution Constraint (which governs both inventory and registry schemas), these defaults apply specifically to `TopicRegistryEntry` fields within the live registry file — not to `CompiledInventory` fields. See [registry.md#entry-structure](registry.md#entry-structure) for the authoritative field definitions.
```

---

### [CC-1] `consecutive_medium_count` default `0` confused with initialization rule

**File:** data-model.md line 62 (consecutive_medium_count row in defaults table)

- [ ] **Step 2: Add disambiguation note after the defaults table**

After the table (after line 68), add:

```
**Defaults vs initialization:** The defaults above are load-time schema-evolution fallbacks only — they apply when a field is absent from a serialized registry entry loaded under an older schema version. For new entry initialization at runtime (`absent → detected`), see [registry.md#field-update-rules](registry.md#field-update-rules). In particular, `consecutive_medium_count` initializes to `1` (not `0`) for medium-confidence leaf-kind entries at detection time. The schema default `0` is a safe fallback for old entries missing the field; it does not govern runtime initialization.
```

---

### [SP-3] `coverage` sub-fields not in null-field serialization invariant

**File:** data-model.md line 296 (null-field serialization paragraph)

- [ ] **Step 3: Expand null-field serialization to cover non-nullable always-present fields**

After the existing null-field paragraph (line 296), add a new paragraph:

```
**Non-nullable always-present fields:** In addition to the nullable fields above, all non-nullable fields in `TopicRegistryEntry` MUST always be present in serialized JSON — absent keys are not valid. This includes `consecutive_medium_count` (integer, always serialized including when `0` — family-kind entries MUST have value `0`), and all `coverage.*` sub-fields: `overview_injected` (boolean), `facets_injected` (array), `pending_facets` (array), `family_context_available` (boolean), `injected_chunk_ids` (array). Empty arrays and `false` values are valid and MUST NOT be omitted. See [registry.md#entry-structure](registry.md#entry-structure) for the authoritative field list.
```

---

### [SP-4] `suppression_reason` missing from null-field serialization examples

**File:** data-model.md line 296 (null-field serialization paragraph)

- [ ] **Step 4: Expand the nullable field example list**

In the null-field serialization paragraph, replace the example list:

Old:
```
(e.g., `last_query_fingerprint: null`, `deferred_reason: null`, `suppressed_docs_epoch: null`)
```

New:
```
(e.g., `last_injected_turn: null`, `last_query_fingerprint: null`, `suppression_reason: null`, `suppressed_docs_epoch: null`, `deferred_reason: null`, `deferred_ttl: null`)
```

---

### [SP-6] `pending_facets` FIFO ordering not in persistence schema

**File:** data-model.md §RegistrySeed (after the non-nullable always-present paragraph added in step 3)

- [ ] **Step 5: Add ordering constraint to serialization invariants**

After the non-nullable always-present paragraph (added in step 3), add:

```
**Array ordering constraint:** `coverage.pending_facets` MUST be serialized in insertion order (FIFO). JSON serializers MUST NOT sort or reorder this array. The ordering semantics are defined in [registry.md#entry-structure](registry.md#entry-structure); this constraint surfaces the behavioral invariant at the persistence layer.
```

---

### [SY-1] "Normal mutation" undefined for `results_file` write-back timing

**Sources:** CE-8 + SP-13 (merged)
**File:** data-model.md line 276 (`results_file` field paragraph)

- [ ] **Step 6: Define "normal mutation" inline**

In the `results_file` paragraph, replace:

Old:
```
The stripped state is persisted to disk on the next normal mutation (per [registry.md#failure-modes](registry.md#failure-modes)), ensuring the field never appears in the live registry file after a successful write.
```

New:
```
The stripped state is persisted to disk on the next normal mutation, ensuring the field never appears in the live registry file after a successful write. **Definition:** A "normal mutation" is any CLI operation that successfully writes the registry file to disk: `dialogue-turn` state updates, `--mark-injected` commits, `--mark-deferred` writes, or automatic suppression writes from `build-packet` empty output. Read-only operations (e.g., `classify`) are not mutations. See [registry.md#failure-modes](registry.md#failure-modes) for load-time handling.
```

---

### [SP-14] Schema defaults table missing fields for schema evolution coverage

**Sources:** SP-14 (P1, Cluster B)
**File:** data-model.md lines 54–68 (Registry Entry Schema Field Defaults table)

- [ ] **Step 7: Expand schema defaults table with missing fields**

Add the following rows to the Registry Entry Schema Field Defaults table:

```
| `first_seen_turn` | `0` |
| `family_key` | derived from `topic_key` (family prefix) |
| `kind` | `"leaf"` |
| `coverage_target` | `"leaf"` |
| `facet` | `"overview"` |
| `coverage.overview_injected` | `false` |
| `coverage.family_context_available` | `false` |
```

Add a note after the table: "These defaults ensure safe load-time migration for entries serialized before these fields were added. `family_key` default is derived by extracting the family prefix from `topic_key` (e.g., `hooks` from `hooks.pre_tool_use`)."

---

- [ ] **Step 8: Verify T2 edits don't overlap with T5 sections**

Confirm T2 edits (lines 54–68, 276, 294–296) do not overlap with T5 target sections (lines 14–48, 396–412). These are in separate sections of data-model.md.

---

## Task 3 — Authority + Cross-Reference Corrections (6 findings)

**Finding count:** 6 P1
**Files:** delivery.md, decisions.md, registry.md
**Depends on:** nothing — start immediately (parallel with T1, T2, T4, T5)

### [AA-1] Shadow Mode Gate section title falsely implies delivery authority

**File:** delivery.md line 21 (section heading)

- [ ] **Step 1: Rename the section**

Old:
```
### Shadow Mode Gate
```

New:
```
### Graduation Protocol and Kill Criteria
```

Also update the normative note on line 23 — remove the redundant gate reference since the section no longer claims the gate:

Old:
```
> **Normative source:** Gate algorithm is defined in [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) under `behavior_contract` authority. This section covers only graduation protocol and kill criteria.
```

New:
```
> **Normative source:** The shadow-mode gate algorithm (what file to read, what field values mean, what default applies) is defined in [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) under `behavior_contract` authority.
```

---

### [AA-6] Diagnostics schema authority annotation contradicts test assertions

**File:** delivery.md line 41 (diagnostics authority note)

- [ ] **Step 2: Update the authority annotation**

Old:
```
(**Authority note:** The diagnostics schema is defined here under the `verification_strategy` claim for testing purposes. It is not an `interface_contract` — no external consumer depends on this schema.)
```

New:
```
(**Authority note:** The diagnostics schema is defined here under the `verification_strategy` claim. It is not an `interface_contract` for production consumers, but field presence is contractual for test fixtures — Layer 2b tests assert on the presence and absence of shadow-mode-specific fields (`packets_target_relevant`, `packets_surviving_precedence`, `false_positive_topic_detections`). Changes to this schema's field set require updating the corresponding test assertions.)
```

---

### [AA-7] decisions.md self-delegates scout-beats-CCDI authority inverting precedence

**File:** decisions.md line 60 ("Scout target always beats CCDI targeting" row)

- [ ] **Step 3: Restructure the scout-beats-CCDI row**

Old:
```
| Scout target always beats CCDI targeting (Review Turn 4) | Scout-sourced repo evidence takes precedence when both produce content for the same turn — see [foundations.md#design-principles](foundations.md#design-principles) for the authoritative design principle. | [foundations.md](foundations.md#design-principles): premise enrichment, not retargeting |
```

New:
```
| Scout target always beats CCDI targeting (Review Turn 4) | Scout-sourced repo evidence takes precedence when both produce content for the same turn — see [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants) for the authoritative behavioral constraint (under `behavior_contract` authority). Design principle: [foundations.md#design-principles](foundations.md#design-principles). | delivery.md [Layer 2b: Agent Sequence Tests](delivery.md#layer-2b-agent-sequence-tests) |
```

---

### [AA-9] `ccdi_trace` schema defined in two places — normative note buried after example

**File:** delivery.md lines 197–228 (Debug-Gated ccdi_trace section)

- [ ] **Step 4: Move normative note before the JSON example**

Move lines 226–228 (the normative output contract note) to immediately after the section heading (after line 199), before the JSON example:

Old order:
```
### Debug-Gated `ccdi_trace`
[prose about gating]
[26-line JSON example]
Full candidate object schema: see ...
**Normative output contract:** The complete trace entry schema...
```

New order:
```
### Debug-Gated `ccdi_trace`
[prose about gating]

**Normative output contract:** The complete trace entry schema, required keys, `action` normative values, and key-presence invariant are defined in [integration.md#ccditrace-output-contract](integration.md#ccditrace-output-contract) under `interface_contract` authority. The JSON example below is illustrative — integration.md is authoritative for the trace schema. The key-presence invariant is validated by `trace_assertions` with `assert_key_present` checks (see replay harness below).

[26-line JSON example]
Full candidate object schema: see ...
```

---

### [CC-3] `deferred_reason` enum vs `ccdi_trace` action naming asymmetry uncross-referenced

**File:** registry.md line 26 (`deferred_reason` field in entry structure)

- [ ] **Step 5: Add cross-reference for naming asymmetry**

After the `deferred_reason` field line in the entry structure, add a note:

```
**Trace action mapping:** The corresponding `ccdi_trace` `action` values use different names: `"skip_scout"` for `"scout_priority"`, `"skip_cooldown"` for `"cooldown"`, `"defer"` for `"target_mismatch"`. See [integration.md#ccditrace-output-contract](integration.md#ccditrace-output-contract).
```

---

### [CC-5] `seed_medium_baseline` fixture contains un-executed retitling instruction

**File:** delivery.md lines 602–608 (`seed_medium_baseline.replay.json` fixture)

- [ ] **Step 6: Execute the retitling**

Old:
```
#### `seed_medium_baseline.replay.json`

Exercises seed-build initialization of `consecutive_medium_count` across the JSON → RegistrySeed → first `dialogue-turn` boundary.

- **Initial state:** Registry file with one leaf topic in `detected` state, `consecutive_medium_count: 2` (pre-existing from prior session).
- **Classifier output:** Same topic at medium confidence.
- **Expected:** `consecutive_medium_count` increments to 3 (seed correctly preserves the counter across serialization boundary). Retitle `seed_medium_baseline` description to "Exercises counter persistence across serialization boundary" (not "seed-build initialization").
```

New:
```
#### `seed_medium_baseline.replay.json`

Exercises counter persistence across the JSON → RegistrySeed → `dialogue-turn` serialization boundary.

- **Initial state:** Registry file with one leaf topic in `detected` state, `consecutive_medium_count: 2` (pre-existing counter from prior turns).
- **Classifier output:** Same topic at medium confidence.
- **Expected:** `consecutive_medium_count` increments to 3 (seed correctly preserves the counter across serialization boundary).
```

- [ ] **Step 7: Commit T2+T3**

```bash
git add docs/superpowers/specs/ccdi/data-model.md docs/superpowers/specs/ccdi/delivery.md docs/superpowers/specs/ccdi/decisions.md docs/superpowers/specs/ccdi/registry.md
git commit -m "fix(spec): remediate 7 P1 schema + 6 P1 authority findings from ccdi spec review round 8

Schema + serialization findings (T2):
- SP-1: Retitle Schema Field Defaults table to clarify registry scope
- CC-1: Add disambiguation note for consecutive_medium_count default vs init
- SP-3: Add non-nullable always-present fields to serialization invariants
- SP-4: Expand nullable field examples to include suppression_reason, deferred_ttl
- SP-6: Add pending_facets FIFO ordering to persistence constraints
- SY-1: Define 'normal mutation' for results_file write-back timing
- SP-14: Expand schema defaults table with missing fields (first_seen_turn, etc.)

Authority + cross-reference findings (T3):
- AA-1: Rename delivery.md section to 'Graduation Protocol and Kill Criteria'
- AA-6: Update diagnostics authority note re test-consumer contract
- AA-7: Fix scout-beats-CCDI authority delegation in decisions.md
- AA-9: Move ccdi_trace normative note before JSON example in delivery.md
- CC-3: Add deferred_reason → trace action cross-reference in registry.md
- CC-5: Execute seed_medium_baseline retitling

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4 — Contract Enforcement Gaps (7 findings)

**Finding count:** 7 P1
**Files:** integration.md, registry.md, data-model.md
**Depends on:** nothing — start immediately (parallel with T1, T2, T3, T5)

### [CE-2] `build-packet` CCDI-lite empty-output behavior unspecified

**File:** integration.md §build-packet-automatic-suppression (after line 76)

- [ ] **Step 1: Add CCDI-lite empty-output specification**

After the "Suppression and deferral precedence" paragraph (line 76), add:

```
**CCDI-lite empty output:** When `--registry-file` is absent and `build-packet` produces empty output, the command MUST exit 0 with empty stdout and no stderr output. The CCDI-lite path has no suppression side-effect — empty output simply means no packet was built.
```

---

### [CE-5] `consecutive_medium_count` reset for deferred entries at TTL > 0 undocumented

**File:** registry.md line 104 (general rule for topic absent from classifier output)

- [ ] **Step 2: Add explicit note for deferred entries mid-TTL**

After the general rule row (line 104), add a note:

```
**Applicability to `deferred` entries:** The general `consecutive_medium_count ← 0` rule applies to `deferred` entries at any TTL value when the topic is absent from classifier output, not only at TTL=0. A `deferred` entry absent from classifier output at TTL > 0 has its `consecutive_medium_count` reset to 0 by this general rule before any transition-specific rules fire.
```

---

### [CE-6] `--inventory-snapshot` failure mode missing for `build-packet`

**File:** integration.md lines 501–510 (failure modes table)

- [ ] **Step 3: Add failure mode row for build-packet**

After the existing `--inventory-snapshot` row (line 508), add:

```
| `--inventory-snapshot` absent on `build-packet` with `--registry-file` present | Missing required flag when `--registry-file` present | Non-zero exit with descriptive error identifying the missing flag (symmetric with `dialogue-turn` behavior per footnote ‡) |
```

---

### [CE-7] `suppressed:redundant` re-entry guard not a named invariant

**File:** registry.md §suppression-re-entry (after line 148)

- [ ] **Step 4: Add named re-entry guard invariant**

After the `docs_epoch` comparison semantics paragraph (line 148), add:

```
**Re-entry guard invariant:** The `docs_epoch` re-entry scan MUST be gated on `suppression_reason == "weak_results"`. A `redundant`-suppressed entry MUST NOT re-enter due to `docs_epoch` change regardless of whether `suppressed_docs_epoch` differs from the current epoch. Implementations iterating suppressed entries for `docs_epoch` re-entry MUST filter by `suppression_reason` before comparing epoch values.
```

---

### [CE-9] `classify --inventory-snapshot` negative test missing

**File:** integration.md §target-match-predicate (after line 431)

- [ ] **Step 5: Add negative test note for classify flag name**

After the inventory snapshot paragraph (line 431), add:

```
**Flag name enforcement:** `classify` accepts `--inventory` (not `--inventory-snapshot`). Passing `--inventory-snapshot` to `classify` is not a valid flag — implementations MUST reject it with a non-zero exit or ignore it with a warning. See the CLI integration tests in [delivery.md](delivery.md#cli-integration-tests) for the negative test.
```

---

### [CC-4] `ccdi_status: unavailable` not in diagnostics schema

**File:** delivery.md §diagnostics (after line 101) and integration.md line 140

- [ ] **Step 6: Add `unavailable` status to diagnostics schema**

In delivery.md, after the `per_turn_latency_ms` field definition (line 101), add:

```
**`status: "unavailable"`:** When `claude-code-docs` is not installed or the inventory cannot be loaded, the diagnostics record uses `status: "unavailable"`. In this case, only `status` and `phase` fields are populated — all count/array fields are absent. See [integration.md#failure-modes](integration.md#failure-modes) for the capability detection flow.
```

---

### [CC-7] `config_overrides` vs `rules[]` processing order unspecified

**File:** data-model.md §config-overrides-in-overlay (after line 383)

- [ ] **Step 7: Specify processing order**

After the `build_inventory.py` records paragraph (line 383), add:

```
**Processing order:** `rules[]` operations are applied first, then `config_overrides`. These keys modify independent build artifacts (`rules[]` modifies the compiled inventory topics/denylist, `config_overrides` modifies the config output written alongside the inventory) and do not interact within a single build run.
```

- [ ] **Step 8: Verify T4 edits don't overlap with T1 sections in integration.md**

T1 touches: lines 284–285 (ccdi_trace), 299–300 (action table), 410 (shadow-mode invariant).
T4 touches: lines 76 (build-packet), 431 (target-match), 501–510 (failure modes).
No overlap — safe to parallelize.

---

## Task 5 — Version Axes + Chunk Determinism (4 findings)

**Finding count:** 4 P1
**Files:** data-model.md, packets.md
**Depends on:** nothing — start immediately (parallel with T1, T2, T3, T4)

### [SP-7] `inventory_snapshot_version` has no write-time constraint

**File:** data-model.md line 306 (Live Registry File Schema table, `inventory_snapshot_version` row)

- [ ] **Step 1: Add write-time validation rule**

After the Live Registry File Schema table description (line 308), add:

```
**`inventory_snapshot_version` write-time contract:** At seed-build time, `inventory_snapshot_version` MUST equal the `CompiledInventory.schema_version` value from the inventory that was successfully loaded. A sentinel block with a blank, null, or absent `inventory_snapshot_version` indicates a build defect. At seed load, if `inventory_snapshot_version` is empty, null, or absent, treat as a version mismatch (log warning, apply best-effort field mapping per [Failure Modes](#failure-modes)).
```

---

### [SP-9] `overlay_meta` optional vs version axis validation gap

**File:** data-model.md §version-axes (after line 48)

- [ ] **Step 2: Clarify vacuous validation when overlay_meta absent**

After the build-time validation paragraph (line 48), add:

```
**Validation when `overlay_meta` absent:** When `overlay_meta` is absent, no overlay was applied; version-axis validation for `overlay_schema_version` and `overlay_version` is vacuously satisfied (there is nothing to validate). `merge_semantics_version` is always present at the top level of `CompiledInventory` and is validated against the CLI's supported version at load time regardless of whether an overlay was applied.
```

---

### [SP-10] `merge_semantics_version` missing from failure modes

**File:** data-model.md §failure-modes table (after line 407)

- [ ] **Step 3: Add failure mode rows for merge_semantics_version**

After the `RegistrySeed.inventory_snapshot_version` row (line 407), add:

```
| `merge_semantics_version` absent in loaded inventory | CLI field validation | Log warning, assume version `"1"` (initial version), proceed with best-effort merge. Consistent with `schema_version` mismatch treatment. |
| `merge_semantics_version` mismatch at load time | CLI string comparison at startup | Log warning, proceed with best-effort field mapping. Distinct from build-time mismatch (which fails loudly per version-axis validation). |
```

---

### [CE-3] Chunk-ordering tiebreaker missing from packets.md

**File:** packets.md §build-process (chunk ranking step)

- [ ] **Step 4: Read packets.md build process to find exact insertion point**

Read the build process section of packets.md to locate the ranking step.

- [ ] **Step 5: Add tiebreaker rule**

In the build process step that ranks chunks by relevance, add:

```
**Chunk-ordering tiebreaker:** When two chunks have equal relevance scores after facet-based ranking, break ties by `chunk_id` ascending (lexicographic). This ensures deterministic ordering given identical inputs, preserving the [idempotency invariant](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue).
```

- [ ] **Step 6: Commit T4+T5**

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/data-model.md docs/superpowers/specs/ccdi/delivery.md docs/superpowers/specs/ccdi/packets.md
git commit -m "fix(spec): remediate 7 P1 contract + 4 P1 version axis findings from ccdi spec review round 8

Contract enforcement findings (T4):
- CE-2: Specify build-packet CCDI-lite empty-output behavior (exit 0, empty stdout)
- CE-5: Document consecutive_medium_count reset for deferred at TTL > 0
- CE-6: Add --inventory-snapshot failure mode row for build-packet
- CE-7: Add suppressed:redundant re-entry guard as named invariant
- CE-9: Add negative test note for classify --inventory-snapshot flag
- CC-4: Add ccdi_status: unavailable to diagnostics schema
- CC-7: Specify config_overrides vs rules[] processing order

Version axis + determinism findings (T5):
- SP-7: Add inventory_snapshot_version write-time validation contract
- SP-9: Clarify overlay_meta absent → vacuous version-axis validation
- SP-10: Add merge_semantics_version to failure modes table
- CE-3: Add chunk-ordering tiebreaker rule (chunk_id ascending) to packets.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6 — Verification Test Specifications (8 findings)

**Finding count:** 8 P1
**Files:** delivery.md
**Depends on:** T1 (CE-1/CE-4 → VR-2), T4 (CE-6 → delivery.md test)

### [VR-1] Freshness guardrail lacks positive-path test

**File:** delivery.md §Layer 2b (after existing shadow-mode tests)

- [ ] **Step 1: Add positive-path freshness test**

Add a Layer 2b test row:

```
| Shadow mode: freshness guardrail positive path | Fixture: classify produces different `classify_result_hash` values across turns for a topic with `shadow_defer_intent`. Assert `shadow_adjusted_yield` IS used as the graduation gate (validator does NOT emit the guardrail warning). Complements the negative-path `shadow_freshness_guardrail_non_authoritative.replay.json`. |
```

---

### [VR-2] No Layer 2a test for `--shadow-mode` flag on `dialogue-turn`

**File:** delivery.md §replay-harness (required fixtures)

- [ ] **Step 2: Add shadow-mode cooldown suppressed replay fixture**

Add a required fixture:

```
| `shadow_mode_cooldown_suppressed.replay.json` | `dialogue-turn` called with `--shadow-mode` flag and two high-confidence candidates (forcing cooldown for the second). Assertions: (a) registry does NOT contain any `deferred: cooldown` entry after `dialogue-turn` completes, (b) `ccdi_trace` contains a `shadow_defer_intent` entry with `reason: "cooldown"`, (c) second candidate remains in `detected` state (not deferred). Tests the CLI-level `--shadow-mode` flag behavior per [integration.md#shadow-mode-registry-invariant](integration.md#shadow-mode-registry-invariant). |
```

---

### [VR-5] `classify_result_hash` stability untested at E2E trace level

**File:** delivery.md §Layer 2b tests

- [ ] **Step 3: Add hash stability trace assertion**

Add to the "Shadow mode: `shadow_defer_intent` trace entries emitted" test description:

```
Additionally: for any topic T that produces `shadow_defer_intent` entries on two consecutive turns with identical classifier input, assert the `classify_result_hash` values are identical across those turns. This exercises hash stability at the E2E trace level (complements the unit-level stability test in Registry Tests).
```

---

### [VR-7] No regression test for `ccdi_trace` action enum constraint

**File:** delivery.md §integration-tests (ccdi_debug gating test, line 439)

- [ ] **Step 4: Add action enum assertion**

Append to the `ccdi_debug` gating test description:

```
Additionally: for every trace entry where `action != "shadow_defer_intent"`, assert `entry["action"]` is in the normative action set: `{none, classify, schedule, search, build_packet, prepare, inject, defer, suppress, skip_cooldown, skip_scout, shadow_defer_intent}`. This guards against undocumented action value expansion.
```

---

### [VR-8] `empty_build_skips_target_match` missing negative assertion on `--mark-deferred`

**File:** delivery.md §replay-harness (empty_build fixture, approximately line 670+)

- [ ] **Step 5: Add negative CLI pipeline assertion to empty_build fixture**

Locate the `empty_build_skips_target_match.replay.json` fixture description and add:

```
**Required `assertions.cli_pipeline_sequence` entry:** The fixture MUST include a negative assertion: `"build-packet --mark-deferred" not in cli_call_log`. This formally enforces that the target-match/defer path is skipped when build-packet returns empty (automatic suppression handles the topic). The assertion guards against implementations that suppress AND defer, writing inconsistent state.
```

---

### [VR-9] PostToolUse hook test has no field-name sensitivity guard

**File:** delivery.md §test_ccdi_hooks (after line 504)

- [ ] **Step 6: Add field-name sensitivity test row**

Add a test row to the `test_ccdi_hooks.py` table:

```
| Hook ignores `tool_result` field | Mock PostToolUse event with `docs_epoch` field change nested under `tool_result` (wrong key) instead of `tool_response` | `build_inventory.py` NOT invoked (hook correctly ignores wrong field name) |
```

---

### [VR-13] Replay harness "semantically identical" comparison undefined for null-field handling

**File:** delivery.md §replay-harness (`weak_results_scan_noop_absent.replay.json` fixture)

- [ ] **Step 7: Define deep-equality comparison**

Add to the fixture description (or to the replay harness general section):

```
**Deep-equality comparison (`assert_registry_unchanged`):** The "semantically identical" comparison MUST: (1) parse both files with `json.loads` (not the registry loader), (2) assert deep equality including presence of null-valued keys — a file with `"deferred_reason": null` is NOT equivalent to a file with `deferred_reason` absent. This enforces the null-field serialization invariant during comparison. Name this comparison mode `assert_registry_unchanged` in the harness.
```

---

### [VR-14] Phase A feasibility gate has no CI enforcement for Phase B test ordering

**File:** delivery.md §Layer 2b (Phase A feasibility gate paragraph)

- [ ] **Step 8: Add prerequisite specification**

Add to the Phase A feasibility gate section:

```
**Phase B prerequisite enforcement:** The three graduation gate tests (`Graduation gate: file absent`, `status rejected`, `status approved`) MUST carry `@pytest.mark.skipif(not phase_a_resolved(), reason="Phase B only — requires Phase A feasibility gate")` where `phase_a_resolved()` checks whether `test_layer2b_mechanism_selection` passed in the current test session. This prevents misleading failures when Phase A is still in progress.
```

- [ ] **Step 9: Commit T6**

```bash
git add docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 8 P1 verification gap findings from ccdi spec review round 8

Findings addressed:
- VR-1: Add shadow freshness guardrail positive-path test
- VR-2: Add shadow_mode_cooldown_suppressed.replay.json fixture spec
- VR-5: Add classify_result_hash E2E stability assertion to trace tests
- VR-7: Add ccdi_trace action enum regression guard to integration tests
- VR-8: Add negative --mark-deferred assertion to empty_build fixture
- VR-9: Add PostToolUse field-name sensitivity test (tool_result vs tool_response)
- VR-13: Define assert_registry_unchanged deep-equality comparison for replay harness
- VR-14: Add Phase A prerequisite enforcement for Phase B graduation tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 7 — P2 Batch (27 findings)

**Finding count:** 27 P2
**Files:** All normative files + spec.yaml
**Depends on:** T1–T5 (normative text must be stable)

Organized by file for edit locality. Each finding is a single edit.

### data-model.md (6 findings)

- [ ] **Step 1: SP-2 — Move consecutive_medium_count always-serialize note**

Co-locate the `consecutive_medium_count` always-serialize statement (line 294) with the non-nullable always-present paragraph added in T2/SP-3. The existing line 294 text becomes redundant with T2's addition — remove the standalone note and verify it's covered by the unified paragraph.

- [ ] **Step 2: SP-5 — deferred_ttl now covered by expanded null-field examples**

Verify that T2/SP-4's expanded example list already includes `deferred_ttl: null`. If so, no additional edit needed (SP-5 is resolved by T2/SP-4).

- [ ] **Step 3: SP-8 — Retitle penalty enforcement paragraph for scope clarity**

Replace "**Penalty range enforcement:**" with "**Build-time penalty validation:**" and prepend "During overlay build (`build_inventory.py`):" to the first sentence.

- [ ] **Step 4: SP-11 — Define config_version compatibility model**

After the `config_version` paragraph (line 358), add: "The CLI accepts only the single value `'1'` for `config_version`. Any other value is treated as unrecognized."

- [ ] **Step 5: SP-12 — Add formal RegistrySeed completeness acknowledgment**

In the `entries` field paragraph (line 278), add: "For a complete enumeration of durable fields serialized within `entries[]`, implementers MUST read [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states). `data-model.md` owns the envelope fields only."

- [ ] **Step 6: SP-15 — Add AppliedRule.target format note**

In the AppliedRule section, after `target: string`, add: "For `operation: override_config` entries, `target` is a dot-delimited config key path matching a leaf scalar in `ccdi_config.json` (e.g., `classifier.confidence_high_min_weight`)."

### integration.md (3 findings)

- [ ] **Step 7: CE-11 — Add initial-mode facet stale-inventory note**

After the facet in initial mode paragraph (line 41), add: "If `entry.facet` is absent from the topic's `QueryPlan.facets` at commit time, `build-packet` falls back to `default_facet` per [packets.md](packets.md#build-process). `entry.facet` is still written to `coverage.facets_injected` for traceability."

- [ ] **Step 8: CE-13 — Track config file isolation as known open item**

In the config file isolation Layer 2b test note (delivery.md line 651), replace the passive tracking note with: "**Known open item:** Config file isolation runtime enforcement is currently test-verified-only. Add a PreToolUse hook blocking Read on `*ccdi_config*` patterns when Phase B is active AND shadow evaluation confirms the invariant is load-bearing."

- [ ] **Step 9: CE-14 — Clarify boundary rule 3 scope**

In spec.yaml boundary rule 3, update the reason text to clarify that `RegistrySeed.entries` durable-field changes in registry.md do NOT require data-model.md review (only envelope schema changes do).

### delivery.md (7 findings)

- [ ] **Step 10: VR-3 — Add raw JSON parse step to pending_facets boundary test**

Amend the boundary contract test row for `pending_facets serialization preserves insertion order`: add "Raw JSON parse step: after serialization, read the file with `json.loads()` (not the registry loader) and assert array order before reloading via the registry loader."

- [ ] **Step 11: VR-4 — Add cross-type rule_id collision test**

Add inventory test row: "Duplicate `rule_id` across mixed operation types | Overlay with one `add_deny_rule` and one `override_weight` sharing same `rule_id` → non-zero exit, error identifies the duplicate."

- [ ] **Step 12: VR-6 — Add rejected graduation notes test**

Add `test_validate_graduation.py` row: "Rejected status with absent or empty `notes` field | `graduation.json` with `status: 'rejected'`, `notes: ''` | Exit 1, error reports 'notes field required and must be non-empty when status is rejected'."

- [ ] **Step 13: VR-10 — Separate xfail placeholder from behavioral claim**

In the `ccdi_policy_snapshot` boundary contract test row, replace "Field present in delegation envelope → `codex-dialogue` agent reads it at dialogue start" with: "Behavioral assertion deferred to Phase B — the xfail test is a placeholder only, not a behavioral verification."

- [ ] **Step 14: VR-11 — Add attempt-local state load test**

Add boundary contract test row: "Registry file with attempt-local state | Load registry with `state: 'looked_up'` → entry reinitialized per resilience principle, warning logged."

- [ ] **Step 15: VR-12 — Add meta-test self-verification**

Add to the `ast.parse` meta-test description: "Self-verification: include two synthetic module tests — (1) module with `if args.source == 'codex'` branch → detection returns True; (2) module without source branch → detection returns False."

- [ ] **Step 16: VR-15 — Add --inventory-snapshot CCDI-lite test**

Add CLI integration test row: "`--inventory-snapshot` passed without `--registry-file` | `build-packet --mode initial --results-file <path> --inventory-snapshot <path>` (no `--registry-file`) → exit 0, normal packet output, flag silently ignored."

### decisions.md (1 finding)

- [ ] **Step 17: AA-3 — Update foundations.md reference**

In the "Scout target always beats CCDI targeting" row (already modified in T3/AA-7), verify that the cross-reference now points to integration.md as authoritative. If AA-3's specific concern (Test Reference column) is not yet addressed, update the Test Reference to point to delivery.md Layer 2b (already done in T3/AA-7 — verify).

### registry.md (0 additional findings)

CC-8 and AA-2 are in registry.md but handled below.

### spec.yaml (2 findings)

- [ ] **Step 18: AA-4 — Add section-level claim elevation note**

In spec.yaml precedence section, add comment: "A normative file may explicitly claim authority for a specific section under a claim family outside its default_claims (section-level claim elevation). See integration.md §pipeline-isolation-invariants for an example."

- [ ] **Step 19: AA-10 — Clarify fallback_authority_order scope**

Add comment after `fallback_authority_order`: "Applies only when a claim is not covered by any defined claim_precedence chain. For defined claim families, always use the specific chain — this is not a tiebreaker within defined chains."

### classifier.md + registry.md (1 finding)

- [ ] **Step 20: CC-8 — Remove inline facet enum re-statement**

In classifier.md line 52 and registry.md line 38, replace the inline enumeration of facet values with: "Valid `Facet` values: see [data-model.md#queryplan](data-model.md#queryplan) for the authoritative enum."

### foundations.md (1 finding)

- [ ] **Step 21: AA-5 — Add authority boundary to schema evolution reference**

Update foundations.md line 43: change "see [data-model.md#schema-evolution-constraint](data-model.md#schema-evolution-constraint) for the authoritative elaboration" to "see [data-model.md#schema-evolution-constraint](data-model.md#schema-evolution-constraint) for the authoritative elaboration under `persistence_schema` authority."

### Remaining cluster findings (3 findings)

- [ ] **Step 22: AA-2 — Fix RegistrySeed authority split note**

In data-model.md line 278, replace: "For persistence_schema conflicts involving entry-level fields serialized within `entries[]`, registry.md (registry-contract) is authoritative for field semantics and durable/attempt-local classification; data-model.md is authoritative for serialization format and envelope structure." with: "For `behavior_contract` and `interface_contract` claims about entry-level field semantics (which fields are durable vs attempt-local, what values mean), registry.md is authoritative. For `persistence_schema` claims about serialization format and envelope structure, data-model.md is authoritative per `spec.yaml` → `claim_precedence` → `persistence_schema`."

- [ ] **Step 23: AA-8 — Acknowledge circular boundary dependency**

In spec.yaml boundary rule 3 (or as a comment), add: "Note: boundary rules 3 and 8 create a bidirectional dependency between data-model and registry-contract for `RegistrySeed.entries` — changes to either file require reviewing the other. This is an accepted architectural trade-off of the authority split."

- [ ] **Step 24: CC-6 — Clarify --results-file conditionality**

In integration.md line 30, update the `--results-file` conditionality paragraph: prepend "Required unless `--skip-build` is passed" to the first sentence.

- [ ] **Step 25: CC-9 — Remove CONSUMERS.md option**

In integration.md line 499, replace "(comment in the handler or a `CONSUMERS.md` file)" with "(comment in the handler)."

- [ ] **Step 26: CE-12 — Add DenyRule load-time warn-and-skip test**

Add delivery.md boundary contract test row: "DenyRule load-time warn-and-skip | Load `topic_inventory.json` with DenyRule `action: 'downrank'`, `penalty: -0.5` → warning logged, rule skipped, remaining classification proceeds normally. No non-zero exit."

- [ ] **Step 27: Commit T7**

```bash
git add docs/superpowers/specs/ccdi/
git commit -m "fix(spec): remediate 27 P2 findings from ccdi spec review round 8

Authority/placement: AA-2, AA-3, AA-4, AA-5, AA-8, AA-10
Enforcement gaps: CE-11, CE-12, CE-13, CE-14
Terminology/coherence: CC-6, CC-8, CC-9
Schema/persistence: SP-2, SP-5, SP-8, SP-11, SP-12, SP-15
Verification: VR-3, VR-4, VR-6, VR-10, VR-11, VR-12, VR-15

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```
