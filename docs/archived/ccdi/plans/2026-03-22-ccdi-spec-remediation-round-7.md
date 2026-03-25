# CCDI Spec Remediation Plan — Round 7

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 57 canonical findings (5 P0, 33 P1, 19 P2) across 9 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/ccdi/` (10 files, 9 normative + 1 supporting + spec.yaml)
**Dominant patterns:** CLI/agent boundary violations (P0×2 + P1×6), infinite suppress-detect loop (P0×1), broken cross-file anchors (5 patterns, 26 links), schema invariants implied but unstated (7 P1), verification density in delivery.md (9 P1)

## Strategy

Seven tasks in three phases, ordered by dependency and edit-locality:

1. **Phase 1** — Five tasks, all parallel (touch different sections of shared files):
   - **T1:** P0 fixes (5) — registry.md scheduling rules, integration.md CLI table + mid-turn flow, delivery.md test strategy
   - **T2:** Broken cross-file anchors (5 P1) — all files, mechanical search-and-replace
   - **T3:** Schema invariants + documentation (7 P1) — data-model.md schema tables + failure modes, registry.md entry structure + field definitions
   - **T4:** CLI/agent contract drift (9 P1) — classifier.md pipeline, registry.md semantic hints + field update rules, integration.md pipeline isolation, data-model.md results_file + defaults, decisions.md constraints
   - **T5:** Authority placement (3 P1) — decisions.md normative table, integration.md invariants section, delivery.md gate heading

2. **Phase 2** — After Phase 1 (normative text must be stable):
   - **T6:** Verification gap specifications (9 P1) — delivery.md test tables + fixture specs

3. **Phase 3** — After Phase 1:
   - **T7:** P2 batch (19 P2) — all files

**Rationale:** T1–T5 touch non-overlapping sections of shared files — safe to parallelize. T6 adds test specifications in delivery.md that reference normative text established by T1–T5 (VR-8 depends on SP-6's FIFO invariant from T3, VR-15/VR-16 depend on SP-6/SP-7 from T3, VR-7 references SY-4's `--inventory-snapshot` fix from T1). T7 is lowest priority.

**Dependency chains:**
1. SP-6 (T3) → VR-8, VR-15 (T6): FIFO ordering invariant must be in schema before writing test specs for it
2. SP-7 (T3) → VR-16 (T6): Dedup constraint must exist before requiring uniqueness assertions in tests
3. SY-4 (T1) → VR-7 (T6): `classify_result_hash` definition depends on `--inventory-snapshot` being required
4. CE-8 (T7, P2) → VR-3 (T6): Target-match SHOULD→MUST upgrade (P2) enriches VR-3's harness fix but is not blocking — VR-3 can add `--inventory` to harness regardless

**Commit strategy:**
1. `fix(spec): remediate 5 P0 findings from ccdi spec review round 7` (T1)
2. `fix(spec): remediate 5 P1 anchor + 7 P1 schema findings from ccdi spec review round 7` (T2+T3)
3. `fix(spec): remediate 9 P1 contract drift + 3 P1 authority findings from ccdi spec review round 7` (T4+T5)
4. `fix(spec): remediate 9 P1 verification gap findings from ccdi spec review round 7` (T6)
5. `fix(spec): remediate 19 P2 findings from ccdi spec review round 7` (T7)

---

## Task 1 — P0 Fixes (5 findings)

**Finding count:** 5 P0
**Files:** registry.md, integration.md, delivery.md
**Depends on:** nothing — start immediately
**Design decisions:** 3 inline choices (SY-2 flag approach, VR-1 test path, VR-2 aggregation method)

### [SY-1] Scout-priority step misattributed to CLI — contradictory blueprints

**Sources:** CE-1, AA-7 (cross-lens confirmation)
**File:** registry.md §Scheduling Rules step 6 + attribution line

registry.md attributes steps 1–9 to `dialogue-turn` CLI. Step 6 (scout priority) requires knowing whether `execute_scout` produced a candidate — information available only agent-side via `scope_envelope`. integration.md explicitly states: "No CLI flag is involved — the CLI has no awareness of scout state."

**Fix (1 edit):**
In registry.md, change the attribution line after step 9 from:
> "Steps 1–9 run in the CLI via `dialogue-turn`. Step 10 runs agent-side after `build-packet` returns."

To:
> "Steps 1–5 and 7–9 run in the CLI via `dialogue-turn`. Step 6 (scout priority) and Step 10 (target-match) run agent-side — the CLI has no scout awareness and no target-match input. See [integration.md#mid-dialogue-phase](integration.md#mid-dialogue-phase) for the agent-side flow."

---

### [SY-2] Shadow-mode cooldown deferral suppression unimplementable by CLI

**Sources:** CE-7, AA-8 (cross-lens confirmation)
**File:** integration.md §dialogue-turn Registry Side-Effects (shadow-mode exception); CLI tool table

integration.md specifies that `dialogue-turn` suppresses cooldown deferral writes in shadow mode. But `dialogue-turn` has no `--shadow-mode` flag and no mechanism to determine graduation status.

**Design decision: Add `[--shadow-mode]` flag to `dialogue-turn`** (option A from both reviewers). This keeps cooldown deferral suppression as a single atomic operation inside `dialogue-turn` and is consistent with the CLI/agent separation principle: the agent provides semantic judgment (reads `graduation.json`, determines mode) and the CLI acts on explicit input. Option B (re-specify as agent-side) would fragment the cooldown logic across two components.

**Fix (3 edits):**
1. **CLI tool table:** Add `[--shadow-mode]` to the `dialogue-turn` flag list: `dialogue-turn --registry-file <path> --text-file <path> --source codex|user --inventory-snapshot <path>‡ [--semantic-hints-file <path>] [--config <path>] [--shadow-mode]`
2. **Flag description:** Add row: "`--shadow-mode` — Suppresses cooldown deferral writes. When set, `candidate_type: 'new'` entries excluded by the per-turn cooldown limit remain in `detected` state (no `deferred: cooldown` write). Passed by `codex-dialogue` when `graduation.json` `status` is not `'approved'`."
3. **Shadow-mode exception line:** Change "In shadow mode, the cooldown deferral write is suppressed" to "When `--shadow-mode` is passed, the cooldown deferral write is suppressed — `candidate_type: 'new'` entries excluded by the per-turn cooldown limit remain in `detected` state."

---

### [SY-4] Missing `--inventory-snapshot` on mid-turn `build-packet` causes infinite suppress-detect loop

**Sources:** CE-2, SP-17 (cross-lens confirmation, escalated from P1 to P0)
**File:** integration.md §Mid-Dialogue Phase step 5.5; registry.md §Suppression Re-Entry null comparison rules

Mid-turn `build-packet` does not pass `--inventory-snapshot`. When search returns weak results, auto-suppression records `suppressed_docs_epoch: null`. On the next `dialogue-turn` (which always carries a non-null `docs_epoch`), the `null → non-null` comparison forces re-entry. The cycle repeats every turn — infinite loop.

**Fix (2 edits):**
1. **integration.md step 5.5 `build-packet` call:** Add `--inventory-snapshot <ccdi_snapshot_path>` to the mid-turn `build-packet` invocation. Add note: "Required when `--registry-file` is present — ensures `suppressed_docs_epoch` is recorded with the current `docs_epoch` rather than null, preventing spurious re-entry on subsequent `dialogue-turn` calls."
2. **integration.md CLI tool table footnote:** Change "On `build-packet`, `--inventory-snapshot` is optional" to "On `build-packet`, `--inventory-snapshot` is required when `--registry-file` is present (symmetric with `dialogue-turn` requirement). When `--registry-file` is absent (CCDI-lite), `--inventory-snapshot` is optional."

---

### [VR-1] Freshness guardrail test has ambiguous OR — neither path definitively required

**File:** delivery.md §Shadow Mode Denominator Normalization

"A Layer 2b test MUST verify the guardrail fires correctly... Alternatively, a unit test" — the OR makes neither path unconditionally required.

**Design decision: Layer 2b is the required path.** The freshness guardrail involves the full `shadow_defer_intent` → intent resolution → `shadow_adjusted_yield` pipeline, which only Layer 2b can exercise end-to-end.

**Fix (1 edit):**
Replace the ambiguous OR clause with a single normative path:
> "A Layer 2b test MUST verify the guardrail fires correctly. Named fixture: `shadow_freshness_guardrail_non_authoritative.replay.json` — configure classify to produce identical `classify_result_hash` values across turns for a topic with `shadow_defer_intent`. Assert `shadow_adjusted_yield` is not used as a graduation gate (validator emits a warning that freshness guardrail is not satisfied for this topic)."

Remove the "Alternatively, a unit test" clause.

---

### [VR-2] `validate_graduation.py` yield aggregation semantics untested for heterogeneous dialogues

**File:** delivery.md §test_validate_graduation.py

Test matrix covers heterogeneous latency but not yield computation across dialogues with different `packets_prepared` counts. `effective_prepare_yield` aggregation method is undefined.

**Design decision: Global ratio** — `sum(packets_surviving_precedence) / sum(packets_prepared)` across all dialogues. Per-dialogue mean overweights small dialogues (a dialogue with 2 packets prepared and 2 surviving would contribute yield=1.0 equally with a dialogue that prepared 100 packets). Global ratio is the standard statistical approach and matches the latency specification's mean-of-all-turns method.

**Fix (2 edits):**
1. **Aggregation definition:** Add to the graduation protocol section: "`effective_prepare_yield` is computed as a global ratio: `sum(packets_surviving_precedence across all dialogues) / sum(packets_prepared across all dialogues)`. This is not a per-dialogue mean."
2. **Test fixture:** Add row to test matrix: "Yield arithmetic inconsistent — heterogeneous packets_prepared: dialogue A has `packets_prepared=10, packets_surviving_precedence=8`, dialogue B has `packets_prepared=2, packets_surviving_precedence=2`. `graduation.json` declares `effective_prepare_yield: 0.9` (per-dialogue mean, not global ratio `10/12 = 0.833`). → Exit 1 with yield discrepancy."

---

## Task 2 — Broken Cross-File Anchors (5 P1)

**Finding count:** 5 P1 (CC-1, CC-2, CC-3, CC-4, CC-5)
**Files:** classifier.md, registry.md, packets.md, integration.md, delivery.md, decisions.md (6 files affected)
**Depends on:** nothing — start immediately
**Total broken links:** 26

**Root cause:** Markdown headings with backtick-enclosed identifiers strip underscores when generating GFM anchors. All cross-references preserve underscores. Systematic mismatch.

| ID | Broken Anchor | Correct Anchor | Files | Instances |
|----|--------------|----------------|-------|-----------|
| CC-1 | `#configuration-ccdi_configjson` | `#configuration-ccdiconfigjson` | classifier.md (2), registry.md (2), packets.md (1), integration.md (1), delivery.md (2), decisions.md (1) | 9 |
| CC-2 | `#cli-tool-topic_inventorypy` | `#cli-tool-topicinventorypy` | classifier.md (1), registry.md (3) | 4 |
| CC-3 | `#ccdi_trace-output-contract` | `#ccditrace-output-contract` | integration.md (1 self-ref), delivery.md (8) | 9 |
| CC-4 | `#debug-gated-ccdi_trace` | `#debug-gated-ccditrace` | integration.md (2) | 2 |
| CC-5 | `#boundary-contract-tests-test_ccdi_contractspy` / `#replay-harness-teststest_ccdi_replaypy` | `#boundary-contract-tests-testccdicontractspy` / `#replay-harness-teststestccdireplaypy` | decisions.md (2) | 2 |

**Fix:** For each row, search-and-replace the broken anchor with the correct one across all affected files. The pattern is consistent: remove underscores from anchor references where the target heading contains backtick-enclosed identifiers.

---

## Task 3 — Schema Invariants + Documentation (7 P1)

**Finding count:** 7 P1 (SP-2, SP-3, SP-4, SP-6, SP-7, SP-10, SP-12)
**Files:** data-model.md, registry.md
**Depends on:** nothing — start immediately
**Unblocks:** VR-8, VR-15, VR-16 in T6 (via SP-6 and SP-7)

### [SP-2] `AppliedRule.target` semantics for `add_deny_rule` unspecified

**File:** data-model.md §AppliedRule (target field definition, lines 176–177)

The `target` field semantics enumerate topic-scoped operations and `override_config` but omit `add_deny_rule`, despite it being in the `operation` enum.

**Fix:** Add to the AppliedRule `target` field semantics: "for `add_deny_rule`, this is the `deny_rule.id` value of the embedded DenyRule."

### [SP-3] `consecutive_medium_count` re-entry initialization asymmetry undocumented

**File:** registry.md §TopicRegistryEntry schema (consecutive_medium_count field definition, ~line 20)

Three initialization rules exist for `consecutive_medium_count` on re-entry (`suppressed→detected` with classifier present, without classifier, and `deferred→detected`). The field definition says "reset on injection or confidence change" but doesn't document the re-entry initialization semantics.

**Fix:** Add note to the `consecutive_medium_count` field definition: "Initialization on re-entry to detected state: 1 when re-entering from classifier output at medium confidence AND leaf-kind; 0 otherwise (including family-kind, absent-from-classifier, and non-medium confidence cases). See field update rules for `suppressed → detected` and `deferred → detected` rows."

### [SP-4] `DenyRule` load-time out-of-range penalty behavior unspecified

**File:** data-model.md §DenyRule load-time validation (lines 106–108)

Load-time validation covers discriminated union violations but not out-of-range `penalty` values (e.g., `penalty: 2.5` for `downrank`).

**Fix:** Clarify in the load-time validation section: "Out-of-range `penalty` values (`penalty ≤ 0.0` or `penalty > 1.0`) for `downrank` rules are treated identically to discriminated-union violations: skip the offending rule with a warning log entry."

### [SP-6] `pending_facets` FIFO ordering not in schema

**File:** registry.md §Entry Structure (coverage sub-object, lines 30–35)

`pending_facets` is a durable array with no serialization ordering invariant, but scheduling step 8 consumes from index 0 and `multi_pending_facets.replay.json` explicitly tests FIFO ordering.

**Fix:** Add to `coverage.pending_facets` in the entry structure: "`pending_facets` is an ordered FIFO queue: facets are appended on `contradicts_prior` hint and consumed from index 0 by scheduling step 8. Implementations MUST serialize `pending_facets` in insertion order and MUST NOT sort or reorder this field."

### [SP-7] `facets_injected`/`injected_chunk_ids` no deduplication invariant

**File:** registry.md §Field Update Rules (`[built] → injected` row, line 105)

Append-only semantics can produce duplicates on retry paths. No dedup constraint exists despite the idempotency invariant.

**Fix (2 edits):**
1. Add deduplication invariant to the `[built] → injected` field update row: "When appending to `coverage.facets_injected`, skip if the facet is already present. When appending to `coverage.injected_chunk_ids`, skip if the chunk ID is already present. These arrays are sets; implementations MUST enforce uniqueness on append."
2. Update the delivery.md "Idempotent mark-injected" test description to include: "Assert no duplicate entries in `facets_injected` or `injected_chunk_ids` after double-commit."

### [SP-10] `remove_alias` can deplete aliases below minimum-1

**File:** data-model.md §Overlay Merge (remove_alias behavior, lines 183–184)

Sequential `remove_alias` operations can leave a topic with zero aliases, violating the TopicRecord invariant "minimum 1 alias."

**Fix:** Add a post-merge validation step to the overlay merge section: "After applying all overlay operations, `build_inventory.py` MUST validate that every TopicRecord has at least one alias. On violation: reject the overlay build with non-zero exit and identify the zero-alias topic(s)."

### [SP-12] `inventory_snapshot_version` fallback undefined when inventory absent

**File:** data-model.md §RegistrySeed (inventory_snapshot_version field, lines 253–254)

No fallback is specified for the edge case where inventory fails to load at seed-build time.

**Fix:** Add: "If the inventory fails to load at seed-build time, `ccdi-gatherer` MUST NOT emit a `<!-- ccdi-registry-seed -->` sentinel block. The sentinel block MUST only be emitted when a valid CompiledInventory was loaded and `inventory_snapshot_version` can be sourced from a real `schema_version` value."

---

## Task 4 — CLI/Agent Contract Drift (9 P1)

**Finding count:** 9 P1 (CE-4, CE-5, CE-10, CE-11, CE-12, SP-16, SY-3, SY-5, SY-6)
**Files:** classifier.md, registry.md, integration.md, data-model.md, decisions.md
**Depends on:** nothing — start immediately (different sections from T1)

### [CE-4] `exact` match = case-sensitive substring with no word-boundary constraint

**File:** classifier.md §Two-Stage Pipeline Stage 1 matching rules table

An `exact` alias like `"use"` can match inside `"PreToolUse"` with no word-boundary requirement. Stage 2 only suppresses orphaned generics, not substring-contaminated exact matches.

**Fix:** Amend Stage 1 `exact` match definition to: "Case-sensitive substring match **at word boundaries** (the matched text must not be preceded or followed by a word character `[a-zA-Z0-9_]`). The word-boundary constraint prevents short aliases from spuriously matching inside longer identifiers."

### [CE-5] Hint elevates `deferred` topic to lookup without state transition path

**File:** registry.md §Semantic Hints scheduling table + §State Transitions

`contradicts_prior` on `deferred` elevates to "materially new (same as prescriptive)" but no state transition path exists from `deferred` to `[looked_up]` in the state machine diagram.

**Fix (2 edits):**
1. Add clarification to the semantic hints scheduling table `contradicts_prior`/`detected or deferred` row: "When elevating a `deferred` topic: the topic transitions to `detected` first (applying `deferred → detected` field update rules — clears `deferred_reason`, `deferred_ttl`), then enters the lookup path from `detected`."
2. Add note to the state transitions section: "Semantic hints that elevate a `deferred` topic to 'materially new' trigger an implicit `deferred → detected` transition before the lookup path."

### [CE-10] Agent config isolation has no runtime enforcement

**File:** decisions.md §Normative Decision Constraints; integration.md §Pipeline Isolation Invariants; delivery.md Layer 2b tests

The invariant that the agent MUST NOT read `ccdi_config.json` is enforced only by test — no runtime guard exists.

**Fix:** Add a note to delivery.md's Layer 2b test for agent config isolation: "This invariant degrades to test-verified-only in production — no PreToolUse hook blocks agent reads of config files at runtime. The spec acknowledges this gap. If a runtime guard is later added (e.g., a PreToolUse hook matching `*ccdi_config*`), update this note." This documents the known limitation explicitly rather than leaving it implicit.

### [CE-11] Hint-driven injection from `deferred` leaves `deferred_reason`/`deferred_ttl` non-null

**File:** registry.md §Field Update Rules

When a hint elevates `deferred` to lookup and the topic is subsequently injected, the `[built] → injected` row does not include clearing `deferred_reason` and `deferred_ttl` — they would persist as stale values.

**Fix:** Add to the `[built] → injected` field update row: "`deferred_reason` ← null, `deferred_ttl` ← null (clear any stale deferral context from prior state)." This ensures clean state after injection regardless of the path that led to lookup.

### [CE-12] Shadow-mode commitment prohibition not elevated to Pipeline Isolation Invariants

**File:** integration.md §Pipeline Isolation Invariants (lines 120–126)

The shadow-mode commitment prohibition is specified at line 404 but not gathered in the Pipeline Isolation Invariants section.

**Fix:** Add to integration.md Pipeline Isolation Invariants section: "**Shadow-mode commitment prohibition:** In shadow mode, `dialogue-turn` MUST be called with `--shadow-mode` (suppresses cooldown deferral writes) and `build-packet --mark-deferred` / `--mark-injected` MUST NOT be called (no committed mutations). See [§Shadow-mode registry invariant](#shadow-mode-registry-invariant)."

### [SP-16] "any durable state" absent-from-classifier rule contradicts suppressed entry no-update rule

**File:** registry.md §Field Update Rules (line 100); integration.md (line 55, 59)

The "absent from classifier output" rule says it applies to "any durable state" but integration.md explicitly says suppressed entries get NO field updates unless re-entry fires.

**Fix (2 edits):**
1. **registry.md line 100:** Change "Topic absent from classifier output (entry exists, any durable state)" to "Topic absent from classifier output (entry exists, any durable state **except `suppressed`**)." Add parenthetical: "(Suppressed entries are governed exclusively by their re-entry conditions — see Suppression Re-Entry. When no re-entry condition is met, no field update occurs for suppressed entries regardless of classifier presence or absence.)"
2. **integration.md line 55:** Change "Resets `consecutive_medium_count` to 0 for entries absent from classifier output" to "Resets `consecutive_medium_count` to 0 for **non-suppressed** entries absent from classifier output."

### [SY-3] No schema defaults table for best-effort field mapping

**Sources:** SP-15, VR-17 (cross-lens confirmation)
**File:** data-model.md §Failure Modes or registry.md §TopicRegistryEntry

Schema evolution is additive-only but no per-field defaults table exists for the case where a seed from schema version N is loaded under version N+1.

**Fix:** Add a "Schema Field Defaults" table to data-model.md after the additive-only evolution statement:

| Field | Default when absent |
|-------|-------------------|
| `state` | `"detected"` |
| `last_seen_turn` | `null` |
| `last_injected_turn` | `null` |
| `last_query_fingerprint` | `null` |
| `consecutive_medium_count` | `0` |
| `deferred_reason` | `null` |
| `deferred_ttl` | `null` |
| `suppressed_docs_epoch` | `null` |
| `coverage.facets_injected` | `[]` |
| `coverage.injected_chunk_ids` | `[]` |
| `coverage.pending_facets` | `[]` |

Add note: "These defaults are used when loading a registry file serialized under an older schema version. Fields absent in the loaded version are initialized to these values."

### [SY-5] `results_file` strip-to-disk timing contradicts across files

**Sources:** SP-1, CE-13 (cross-lens confirmation)
**File:** data-model.md §RegistrySeed (lines 258)

data-model.md says "Implementations MUST strip `results_file` from the in-memory registry representation immediately on CLI registry load. All subsequent writes serialize the stripped state" — the word "immediately" can be read as requiring a load-time write-back, contradicting registry.md's "not as a load-time side effect."

**Fix:** In data-model.md, replace the strip description with: "Implementations MUST strip `results_file` from the in-memory registry representation at load time (no load-time write-back). The stripped state is persisted to disk on the next normal mutation (per [registry.md#failure-modes](registry.md#failure-modes)), ensuring the field never appears in the live registry file after a successful write."

### [SY-6] `last_query_fingerprint` "if available" ambiguity

**Sources:** SP-13, CE-14 (cross-lens confirmation)
**File:** registry.md §Field Update Rules (last_query_fingerprint normalization, line 121)

"Includes `docs_epoch` if available" — but null `docs_epoch` and absent `--inventory-snapshot` are different conditions with different fingerprint outputs.

**Fix:** Replace "Includes `docs_epoch` if available" with: "Always includes `docs_epoch` as a component, even when null. Fingerprint format: `normalize(query) + '|' + str(docs_epoch)` where null becomes the literal string `'null'`. When `--inventory-snapshot` is absent on a CLI call, `docs_epoch` is treated as null for fingerprint composition." Update the session-local cache rule (line 237) with the same clarification.

---

## Task 5 — Authority Placement (3 P1)

**Finding count:** 3 P1 (AA-1, AA-3, AA-6)
**Files:** decisions.md, integration.md, delivery.md
**Depends on:** nothing — start immediately (different sections from T1 and T4)

### [AA-1] decisions.md uses MUST language for behavioral constraints owned by component contracts

**File:** decisions.md §Normative Decision Constraints table (lines 51–62)

**Fix:** Convert MUST language in each row to cross-reference language. Examples:
- "MUST NOT commit injections" → "Does not commit injections — see [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) for the authoritative behavioral constraint."
- "MUST NOT invoke any topic_inventory.py command" → "Must not invoke per [integration.md#pipeline-isolation-invariants](integration.md#pipeline-isolation-invariants)."

This preserves the cross-reference utility while making clear that decisions.md is not the normative source for behavioral constraints.

### [AA-3] integration.md partial elevation — 3 of 5 behavioral invariants remain unmatched

**File:** integration.md §Pipeline Isolation Invariants (lines 120–126)

The Pipeline Isolation Invariants section elevates two invariants but three others in decisions.md have no behavior_contract-authority counterpart.

**Fix:** Expand integration.md Pipeline Isolation Invariants section (or add companion invariant block) to include:
1. **Sentinel structure invariant:** "Registry seed MUST be transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags, not inline in the delegation envelope."
2. **Shadow-mode commitment prohibition:** Add cross-reference: "See [§Shadow-mode registry invariant](#shadow-mode-registry-invariant) below." (The invariant already exists at line 404; this section needs only a pointer.)
3. **Scout-beats-CCDI targeting invariant:** "When context-injection has a scout candidate for the current turn, CCDI topic injection MUST defer — scout targets take priority per [foundations.md#design-principles](foundations.md#design-principles)."

### [AA-6] delivery.md Shadow Mode Gate heading creates authority ambiguity

**File:** delivery.md §Shadow Mode Gate (lines 21–23)

The heading implies delivery.md owns the gate definition, though the explicit forward-reference to integration.md exists.

**Fix:** Add blockquote callout immediately after the heading:
> `> **Normative source:** Gate algorithm is defined in [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) under behavior_contract authority. This section covers only graduation protocol and kill criteria.`

---

## Task 6 — Verification Gap Specifications (9 P1)

**Finding count:** 9 P1 (VR-3, VR-4, VR-5, VR-6, VR-7, VR-8, VR-9, VR-15, VR-16)
**Files:** delivery.md
**Depends on:** T1 (SY-4 → VR-7), T3 (SP-6 → VR-8/VR-15, SP-7 → VR-16)

All fixes add test specifications to delivery.md. Listed in table format since all follow the same pattern: "Add test row/fixture spec to delivery.md."

| ID | Title | Test Section | Fix |
|----|-------|-------------|-----|
| VR-3 | Target-match condition (b) inventory pinning | Replay Harness (harness execution model step 5b) | Update step 5b: `classify --text-file <composed_target_tempfile> --inventory <pinned_snapshot_path>`. Add assertion to `target_match_classifier_branch.replay.json`: assert `classify` invocation includes `--inventory <snapshot>`. |
| VR-4 | `ccdi_debug: false` case untested | CLI Integration Tests | Add test row: "ccdi_debug: false → no ccdi_trace key" (distinct from the "absent" case). |
| VR-5 | Layer 2b interception completeness — no fixture or N | Layer 2b Agent-Sequence Tests | Specify named fixture: `interception_completeness_3_invocations.json` — dialogue produces exactly 3 `topic_inventory.py` invocations (classify + dialogue-turn + build-packet). Assert captured count = 3. |
| VR-6 | `--force` trigger of `build_inventory.py` untested | Hook Tests (`test_ccdi_hooks.py`) | Add test row: "Manual `--force` flag bypasses epoch check — invoke `build_inventory.py --force` with unchanged `docs_epoch` → assert build executes and regenerates `topic_inventory.json`." |
| VR-7 | `classify_result_hash` computation undefined and untested | Unit Tests / Shadow Mode Tests | Add two tests: (1) "classify_result_hash input coverage — same `topic_key` with different `matched_aliases` → different hashes." (2) "Same classify payload → same hash (stability)." Define hash inputs: hash MUST include `confidence`, `facet`, and `matched_aliases` (not just `topic_key`). |
| VR-8 | `multi_pending_facets` Turn-2 assertion not required | Replay Harness (`multi_pending_facets.replay.json`) | Add REQUIRED `final_registry_file_assertions` entry: `{"path": "<topic>.coverage.pending_facets", "equals": []}` (after Turn 2). |
| VR-9 | Shim identity test not specified as autouse fixture | Layer 2b Setup | Change "can be a pytest fixture-level assertion" to "MUST be implemented as a pytest `autouse` fixture in `conftest.py` for `tests/test_ccdi_agent_sequence.py`." Name the fixture: `ccdi_shim_identity_check`. |
| VR-15 | No boundary contract test for `pending_facets` ordering | Boundary Contract Tests (`test_ccdi_contracts.py`) | Add test: "pending_facets serialization preserves insertion order — append two facets, serialize registry, reload → assert array order matches insertion order (FIFO)." |
| VR-16 | Idempotent `--mark-injected` test doesn't assert uniqueness | CLI Integration Tests / Replay Harness | Update the "Idempotent mark-injected" test: "Assert `facets_injected` and `injected_chunk_ids` arrays contain no duplicate entries after double-commit." |

---

## Task 7 — P2 Batch (19 P2)

**Finding count:** 19 P2
**Files:** All spec files
**Depends on:** T2–T5 (some P2 fixes touch sections modified by P1 tasks)

### Cross-Reference & Coherence (2)

| ID | Fix |
|----|-----|
| CC-6 | Split delivery.md diagnostics JSON example into two labeled blocks: one for active mode (without shadow-only fields) and one for shadow mode (with `packets_target_relevant`, `packets_surviving_precedence`, `false_positive_topic_detections`). |
| CE-9 | In packets.md step 7, replace undefined terms: "Within each topic chunk: (1) paraphrase-mode facts first (each with inline `[ccdocs:...]` citation), (2) snippet-mode facts last (exact field names/values). Citations are inline per fact, not a leading block." Remove undefined term "summary." |

### Authority & Architecture (2)

| ID | Fix |
|----|-----|
| AA-2 | Update README.md authority table foundation row to include "topic hierarchy, component inventory" to match spec.yaml. |
| AA-4 | Add brief cross-reference in foundations.md: "Schema evolution constraint (additive-only): see [data-model.md#schema-evolution-constraint](data-model.md#schema-evolution-constraint) for the authoritative elaboration." |

### Contract Precision (4)

| ID | Fix |
|----|-----|
| CE-3 | Add immutability constraint to initial-mode description: "The RegistrySeed is the single source of truth for initial-mode `--facet` values and MUST NOT be mutated between prepare and commit." |
| CE-6 | Add ordering note to field update rules: "General state-independent rules (e.g., 'topic absent from classifier output') are evaluated first each turn, then transition-specific rules apply. When a transition row references a general rule, the general rule has already fired — the transition row listing is informational only." |
| CE-8 | In integration.md target-match predicate, strengthen SHOULD to MUST for condition (b) `classify` invocation in full-CCDI mode: "The `classify` invocation for condition (b) MUST use the pinned inventory snapshot (`--inventory <ccdi_snapshot_path>`)." Remove the "acceptable if" escape clause. |
| CC-5 | Fix 2 broken anchors in decisions.md: `#boundary-contract-tests-test_ccdi_contractspy` → `#boundary-contract-tests-testccdicontractspy`, `#replay-harness-teststest_ccdi_replaypy` → `#replay-harness-teststestccdireplaypy`. |

### Schema (5)

| ID | Fix |
|----|-----|
| SP-5 | Annotate `results_file` in RegistrySeed schema: `results_file: string \| null  # transport-only; never persisted in live file; stripped on load`. |
| SP-8 | Add serialization note to CompiledInventory schema: "All nullable fields (`docs_epoch`) MUST be serialized with explicit null when null — never omitted." |
| SP-9 | Add `suppressed_docs_epoch` to data-model.md null-field serialization examples: "...e.g., `last_query_fingerprint: null`, `deferred_reason: null`, `suppressed_docs_epoch: null`..." |
| SP-11 | Add: "The scalar-only constraint for config override values applies to `overlay_schema_version: '1'`. Future versions that permit null MUST introduce a new `overlay_schema_version` and specify null semantics explicitly." |
| SP-14 | Add: "`build_inventory.py` MUST process `config_overrides` using strict JSON parsing that rejects duplicate keys, or detect duplicates after parsing and reject with non-zero exit." |

### Testing (6)

| ID | Fix |
|----|-----|
| VR-10 | Add resolution trigger to known Layer 1 test gaps: "Must be closed before Phase B graduation." |
| VR-11 | Define meta-test detection mechanism: "The meta-test uses `ast.parse` to scan `topic_inventory.py` for any conditional branch on `args.source`. If found, assert zero `source_equivalence_baseline`-marked tests." |
| VR-12 | Add note to 100-topic sample size: "This is an operational minimum for feasibility. The statistical confidence of a 10% threshold at N=100 depends on the true false-positive rate — see the graduation protocol for details on when larger samples are recommended." |
| VR-13 | Add explicit XFAIL test skeleton requirement: "A test named `test_ccdi_policy_snapshot_boundary` MUST exist with `@pytest.mark.xfail(reason='Policy snapshot shape not yet defined')` marker. Presence is required; pass is not." |
| VR-14 | Soften byte-identity assertion for `weak_results_scan_noop_absent.replay.json`: "Assert registry file is **semantically identical** (JSON-parse both, deep-compare) rather than byte-identical. Byte identity may break if the JSON serializer reorders keys even with no value change." |
| CC-5 | (Covered above under Contract Precision — already listed.) |

**Note:** CC-5 appears under both Contract Precision and Testing above because the finding involves test section anchors. The fix is a single anchor replacement — listed once under Contract Precision.

---

## Decision Gates

| After | Condition | Path A | Path B |
|-------|-----------|--------|--------|
| T1 (SY-2) | `--shadow-mode` flag landed | CE-12 (T4) references the new flag | CE-12 must describe the mechanism differently |
| T3 (SP-6) | FIFO invariant in schema | VR-8, VR-15 (T6) reference the invariant | VR-8/VR-15 must define the invariant inline in the test spec |
| T3 (SP-7) | Dedup constraint in schema | VR-16 (T6) references the constraint | VR-16 must define dedup expectation inline |
| T7 (CE-8) | SHOULD→MUST for condition (b) | VR-3 (T6) harness change is consistent | VR-3 harness change is still valid but CE-8 upgrade strengthens the contract |

All gates have a clear fallback path — T6 can proceed even if T3 is delayed by inlining the expected behavior in the test spec.

## Critical Path

**Phase 1 tasks (T1–T5) are all independent.** The critical path runs through whichever task takes longest to complete, followed by T6.

**Highest-risk task:** T1 (SY-2 — adding `--shadow-mode` flag). This is a CLI interface addition that must be consistent with:
- The shadow-mode registry invariant (integration.md line 404)
- The CE-12 Pipeline Isolation elevation (T4)
- The shadow-mode commitment prohibition tests (delivery.md)

All three are in different tasks but reference the same concept. After T1 and T4 complete, verify the three descriptions are mutually consistent.

**Second-highest risk:** T4 (SY-3 — schema defaults table). This is new normative content. The defaults must match the initialization rules scattered across registry.md's field update rules table. Verify each default against the applicable transition row.

**Recommended first move:** Start all Phase 1 tasks. If executing sequentially: T2 (mechanical anchors, 15 minutes) → T1 (P0, highest priority) → T3 (schema, unblocks T6) → T5 (authority, small) → T4 (CLI/agent, most edits).

## Out of Scope (Parked)

- **Cross-spec consistency** — no comparison with engram, consultation contract, or context-injection specs
- **Round 6 plan overlap** — round 6 was already applied (`1e23c97`); round 7 findings are all new
- **`initial_threshold_*` key naming** — deferred from round 6 T4; doc note suffices for now
- **Runtime enforcement for agent config isolation** (CE-10) — documented as known limitation; hook addition is out of scope for this remediation
- **README accuracy beyond AA-2** — README is non-normative; checked only for authority misplacement
