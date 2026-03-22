# CCDI Spec Remediation Plan — Round 6

**Source:** `.review-workspace/synthesis/report.md` (5-reviewer team, 2026-03-22)
**Scope:** 37 canonical findings (1 P0, 23 P1, 13 P2) across 8 normative files + spec.yaml
**Spec:** `docs/superpowers/specs/ccdi/` (10 files, 8 normative + 1 non-normative + spec.yaml)
**Dominant patterns:** integration.md underspecification (9 findings touch this file), test gap density in delivery.md (18 findings), shadow mode behavioral tensions

## Strategy

Six tasks in three phases, ordered by dependency and priority:

1. **P0 + TTL-bypass cluster** — fix the sole P0 (untested scheduling rule) and its coupled spec gap
2. **integration.md spec gaps** — clear fixes that unblock downstream test work (duplicate headings, cooldown deferral, --inventory-snapshot contradiction)
3. **Schema + metadata fixes** — data-model.md, delivery.md, spec.yaml corrections (add_topic rejection, config_version, layer count, boundary rule, trace schema dedup)
4. **Design decisions** — resolve 2 contested behavioral specs (agent threshold observability, shadow mode metric inflation)
5. **P1 test gap specifications** — 12 test specs in delivery.md (blocked on T1–T4)
6. **P2 batch** — 13 lower-priority fixes (blocked on T2–T3)

**Rationale:** T1–T3 are independent and can proceed in parallel (different file sections). T4 is also independent but requires design input — run concurrently with implementation of T1–T3 so decisions are ready when T5 begins. T5 must wait for normative text to stabilize. T6 is lowest priority and can be deferred.

**Dependency chains:**
1. SY-9 (T3) → SY-18 `add_topic` half (T5): Fix `add_topic` rejection behavior before writing the `default_facet` test
2. SY-7 (T2) → SY-19 (T5): Fix `--inventory-snapshot` spec contradiction before writing the missing-flag CLI test
3. SY-24 (T1) + SY-1 (T1): Fix integration.md side-effects gap, then add replay fixture — same task, sequential within it

---

## Task 1 — P0: TTL-Bypass Spec Gap + Replay Fixture

**Finding count:** 1 P0 + 1 P1 = 2 findings
**Files:** integration.md, delivery.md
**Depends on:** nothing — start immediately

The P0 and its coupled spec gap are two sides of the same defect: a normative scheduling rule (high-confidence re-detection bypasses TTL on deferred topics) that is both missing from the integration.md side-effects section AND has no replay fixture exercising it.

#### [SY-24] High-confidence TTL-bypass missing from integration.md side-effects

**Source:** CE-7
**File:** integration.md lines 47–58 (dialogue-turn Registry Side-Effects)

`registry.md` scheduling step 2 specifies that high-confidence re-detection of a `deferred` topic triggers immediate `deferred → detected` transition bypassing TTL. `integration.md`'s side-effects section omits this mutation entirely.

**Fix:** Add to `integration.md#dialogue-turn-registry-side-effects`: "Transitions `deferred → detected` immediately (bypassing TTL) when a topic in `deferred` state is re-detected at high confidence — clears `deferred_reason` and `deferred_ttl`, makes topic eligible for scheduling in the same call. See registry.md#scheduling-rules step 2."

#### [SY-1] No replay fixture for deferred→detected high-confidence TTL-bypass

**Source:** VR-2
**File:** delivery.md, Replay Harness fixtures list (lines 558–595)

**Fix:** Add `high_confidence_bypasses_deferred_ttl.replay.json` fixture spec: Topic deferred (TTL=3), turn 2 same topic at high confidence → assert topic transitions to `detected` with `deferred_reason: null`, `deferred_ttl: null`, ready for scheduling in the same turn. `final_registry_file_assertions` MUST verify TTL fields cleared. `trace_assertions` MUST include `{"turn": 2, "action": "inject"}` (or appropriate action for the re-detected topic).

---

## Task 2 — integration.md Spec Gaps (Clear Fixes)

**Finding count:** 3 P1
**Files:** integration.md (primary), delivery.md, packets.md (cross-ref updates)
**Depends on:** nothing — start immediately, parallel to T1 and T3
**Unblocks:** SY-19 in T5 (via SY-7 fix)

#### [SY-2] Cooldown deferral enforcement mechanism unspecified + `skip_cooldown` action label semantics

**Source:** CE-1 + CE-6
**File:** integration.md lines 47–58 (dialogue-turn Registry Side-Effects), line 292 (`skip_cooldown` action)

The `deferred: cooldown` state transition is referenced across registry.md but `integration.md` never specifies how `dialogue-turn` writes this state. The `skip_cooldown` trace action label says "skipped" but the behavior is a durable state write — contradictory semantics.

**Fix (2 edits):**
1. Add to `integration.md#dialogue-turn-registry-side-effects`: "For `candidate_type: 'new'` entries excluded by the per-turn cooldown limit, `dialogue-turn` writes `deferred: cooldown` state to the registry (same field updates as `detected → deferred`). These entries do NOT appear in the candidates JSON output."
2. Change `skip_cooldown` action description in the normative values table from "Topic skipped due to per-turn cooldown" to "Topic deferred due to per-turn cooldown (`deferred: cooldown` state written by `dialogue-turn`)."

#### [SY-3] Shadow Mode Gate duplicate headings

**Source:** AA-1 + CC-2 (cross-lens confirmation)
**File:** integration.md lines 178 and 299; inbound links from delivery.md, packets.md

Two `### Shadow Mode Gate` headings. All inbound cross-file links resolve to line 178 (a redirect paragraph), not line 299 (the actual gate algorithm).

**Fix:** Merge into a single `### Shadow Mode Gate` heading at the algorithm location (line 299). Incorporate any useful context from line 178's redirect paragraph into the merged section body. Add cross-reference: "graduation.json schema and graduation protocol are defined in delivery.md#graduation-protocol." Update inbound references from delivery.md and packets.md to confirm they resolve correctly (removing the first heading eliminates the ambiguity).

#### [SY-7] `--inventory-snapshot` required prose vs optional syntax

**Source:** CE-9
**File:** integration.md line 17 (command table), line 39 (flag description)

Prose says "Required on all full-CCDI CLI calls" but command table shows `[--inventory-snapshot <path>]` in optional brackets. No behavior specified for the absent case.

**Fix (3 edits):**
1. Remove optional brackets from command table when `--registry-file` present (or add footnote: "Required when `--registry-file` is present").
2. Add to flag description: "When absent on a full-CCDI call (`--registry-file` present): non-zero exit with descriptive error. Not required in CCDI-lite mode."
3. Add failure mode row: "`--inventory-snapshot` absent on full-CCDI call → non-zero exit with descriptive error."

---

## Task 3 — Schema + Metadata Fixes

**Finding count:** 5 P1
**Files:** data-model.md, delivery.md, spec.yaml
**Depends on:** nothing — start immediately, parallel to T1 and T2
**Unblocks:** SY-18 `add_topic` half in T5 (via SY-9 fix)

All fixes are mechanical with no design decisions needed.

#### [SY-6] graduation.json cross-authority dependency unprotected

**Source:** AA-3 + CE-8 (cross-lens confirmation)
**File:** spec.yaml boundary_rules

`integration.md`'s gate evaluates `graduation.json` status values defined in `delivery.md`. No boundary rule protects `delivery → integration` changes.

**Fix:** Add boundary rule to `spec.yaml`:
```yaml
- on_change_to: [delivery]
  review_authorities: [integration]
  reason: graduation.json status enum changes affect the shadow mode gate algorithm in integration.md.
```
Additionally, add a normative comment to integration.md Shadow Mode Gate (after SY-3 merge): "The `status` enum values are defined in delivery.md#graduation-protocol. The gate evaluates `status == 'approved'` and treats all other values as shadow mode."

#### [SY-8] ccdi_trace schema duplicated across authority tiers

**Source:** AA-2
**File:** delivery.md lines 128–159 (Debug-Gated ccdi_trace section)

delivery.md contains a full `action` value table and trace entry JSON example that duplicates integration.md's normative content — and delivery.md is not in the interface_contract precedence chain.

**Fix:** In delivery.md, replace the `action` value table and trace-entry JSON example with a normative reference: "See [integration.md#ccdi_trace-output-contract](integration.md#ccdi_trace-output-contract) for the complete trace entry schema, required keys, and `action` normative values." Keep only the replay-harness-specific testing context (how the harness uses the trace, not what the trace contains).

#### [SY-9] `add_topic` missing rejection behavior

**Source:** SP-1
**File:** data-model.md lines 231 (OverlayRule table)

`add_topic` with empty `aliases` or missing `default_facet` has no rejection behavior, unlike peer operations which have explicit "On violation: reject" language.

**Fix:** Add to the `add_topic` row in the OverlayRule table:
- "On violation (empty `aliases` array): reject the overlay rule with descriptive error."
- "On violation (`query_plan` missing `default_facet`): reject the overlay rule with descriptive error."

Consistent with the `replace_queries` and `add_deny_rule` patterns.

#### [SY-10] `config_version` behavioral contradiction

**Source:** SP-2
**File:** data-model.md line 332 vs line 375

Line 332 says CLI "rejects" files with unrecognized `config_version`; Failure Modes table (line 375) says "use built-in defaults, log warning."

**Fix:** Change line 332 to: "`config_version` current supported value: `'1'`. The CLI treats files with an unrecognized `config_version` as unreadable — falls back to built-in defaults and logs a warning (see [Failure Modes](#failure-modes))."

#### [SY-11] "three-layer" vs "four-layer" count mismatch

**Source:** CC-1
**File:** spec.yaml line 30 (delivery authority description)

spec.yaml says "three-layer approach" but delivery.md and decisions.md both define a four-layer approach (Layers 1, 2a, 2b, 3).

**Fix:** Update spec.yaml delivery description from "three-layer approach" to "four-layer approach."

---

## Task 4 — Design Decisions ✅ RESOLVED

**Finding count:** 2 P1
**Files:** integration.md, data-model.md, decisions.md, delivery.md
**Depends on:** nothing
**Status:** Both decisions resolved via Codex dialogue (thread `019d13e4-5207-74d2-861b-01abed080d39`, 5 turns, collaborative posture, converged with high confidence)

#### [SY-4] Agent-side threshold check → **Fixed agent heuristic with intentional divergence**

**Resolution:** Option B confirmed. The agent pre-dispatch gate uses hardcoded thresholds (1 high-confidence topic OR 2+ medium-confidence same-family). The `initial_threshold_high_count` and `initial_threshold_medium_same_family_count` config keys configure threshold evaluation in the CLI `classify` command only. When these keys are overridden, agent gate and CLI threshold outcomes MAY diverge — that divergence is intentional.

**Spec edits:**
1. **integration.md** — Add normative note in both CCDI-lite (line 164) and full CCDI (line 191) flows: "The agent gate is a fixed heuristic using built-in defaults. It is not affected by `ccdi_config.json` overrides."
2. **data-model.md** — Annotate both `initial_threshold_*` config keys (lines 310-312) with "CLI `classify` scope" — these keys do not affect the agent pre-dispatch gate.
3. **decisions.md** — Add one-line invariant to normative constraints table: "Agent pre-dispatch threshold is a fixed heuristic; divergence from `initial_threshold_*` config overrides is intentional." This prevents accidental "consistency" cleanup that would break pipeline isolation.
4. **delivery.md** — Add test: "Agent gate unchanged when config overrides exist — override `initial_threshold_high_count: 2` in config, classify produces 1 high-confidence topic → agent still dispatches (gate uses hardcoded default 1, not configured 2)."

**Naming risk (deferred):** `initial_threshold_*` key names suggest they govern the initial gate, but they only affect CLI classify evaluation. A doc note suffices for this remediation cycle; renaming is out of scope.

#### [SY-5] Shadow mode metric inflation → **Non-mutating shadow mode with denominator normalization**

**Resolution:** Option B+ (emerged from dialogue — a third option superior to both originals). Shadow mode remains fully non-mutating. The existing "zero `--mark-deferred` invocations in shadow mode" test (delivery.md:554) stays unchanged. Instead of adding a second uncalibrated threshold, the yield denominator is **normalized** to remove inflation from repeated re-scheduling.

**Mechanism:**
- New `shadow_defer_intent` trace entry records counterfactual deferral decisions: `{action: "shadow_defer_intent", topic_key, reason: "target_mismatch" | "cooldown", classify_result_hash}`
- `shadow_adjusted_yield = packets_surviving_precedence / (packets_prepared - repeat_detections_from_missing_deferral)` — uses same 40% threshold as active mode
- Repeat detection: same `topic_key` + unresolved `shadow_defer_intent` + same `classify_result_hash` → all repeated prepares count
- Intent resolution: `shadow_defer_intent` becomes resolved when `classify_result_hash` changes, `topic_key` disappears from classify output, or committed state transition would have prevented re-evaluation
- **Freshness guardrail:** If `classify_result_hash` cannot be freshness-sensitive (payload does not change with new evidence), `shadow_adjusted_yield` must not gate graduation
- Authority: `shadow_defer_intent` stays within `delivery.md` diagnostics authority (counterfactual observation, not committed mutation)

**Spec edits:**
1. **integration.md** — Shadow mode invariant unchanged (no `--mark-deferred` permitted)
2. **delivery.md** — Add `shadow_defer_intent` trace entry to diagnostics schema. Add `shadow_adjusted_yield` formula and freshness guardrail. Require diagnostics to report both raw `effective_prepare_yield` and `shadow_adjusted_yield`. Kill-criteria evaluation uses `shadow_adjusted_yield` in shadow mode.

#### Unresolved (non-blocking, deferred)

- `classify_result_hash` freshness sensitivity — implementation must validate that classify payload changes with new evidence (raised T3-T4, resolved in principle)
- `initial_threshold_*` key naming — misleading names, doc note suffices for now (raised T3, deferred)

---

## Task 5 — P1 Test Gap Specifications

**Finding count:** 12 P1
**Files:** delivery.md
**Depends on:** T1 (replay fixtures stable), T2 (SY-7 → SY-19), T3 (SY-9 → SY-18), T4 (design decisions resolved)

All fixes add test specifications to delivery.md for normative behavioral rules that currently have no test coverage. The normative text must be stable before writing these.

#### [SY-12] Alias cross-type suppression (phrase beats token) untested

**Source:** VR-1
**File:** delivery.md, Classifier Tests

**Fix:** Add test row: "Phrase suppresses token on same topic — input matches both a phrase alias (weight 0.6) and a token alias (weight 0.4) for the same topic → final score is 0.6 only (token contribution excluded)."

#### [SY-13] `suppressed:redundant` re-entry via new leaf — no replay fixture

**Source:** VR-3
**File:** delivery.md, Replay Harness fixtures

**Fix:** Add `redundant_reentry_via_new_leaf.replay.json`: Turn 1 → family topic A suppressed:redundant. Turn 2 → new leaf topic under same family detected → assert topic A transitions to `detected`. `final_registry_file_assertions` MUST verify `state: "detected"`, `suppression_reason: null`.

#### [SY-14] `weak_results` full-registry scan — missing REQUIRED assertions

**Source:** VR-4
**File:** delivery.md, `weak_results_reentry_on_epoch_change.replay.json` fixture spec

**Fix:** Amend fixture spec to include REQUIRED `final_registry_file_assertions`: `{"path": "<topic>.last_seen_turn", "equals": 2}` and `{"path": "<topic>.consecutive_medium_count", "equals": 0}`. Mark as MUST.

#### [SY-15] Paraphrase extractive selection determinism untested

**Source:** VR-5
**File:** delivery.md, Packet Builder Tests

**Fix:** Add test: "Paraphrase selection deterministic — same content field with 3 sentences, facet='schema', run twice → assert identical sentence(s) selected in both runs; tied-score sentences broken by position (first wins)."

#### [SY-16] `add_topic`/`replace_aliases` weight clamping untested

**Source:** VR-7
**File:** delivery.md, Inventory Tests

**Fix:** Add two test rows:
1. "`add_topic` alias weight out-of-bounds → clamped: overlay with `add_topic`, `aliases[0].weight = 1.5` → build succeeds, compiled alias weight = 1.0, warning emitted."
2. "`replace_aliases` alias weight out-of-bounds → clamped: overlay with `replace_aliases`, alias weight = -0.1 → clamped to 0.0, warning emitted."

#### [SY-17] `deny_rule.id` uniqueness constraint untested

**Source:** VR-8
**File:** delivery.md, Inventory Tests

**Fix:** Add test: "Duplicate `deny_rule.id` across `add_deny_rule` operations → non-zero exit: overlay with two `add_deny_rule` operations sharing `deny_rule.id: 'dup-rule'` → non-zero exit, error message identifies both rule positions."

#### [SY-18] `replace_queries`/`add_topic` `default_facet` validation untested

**Source:** VR-9
**File:** delivery.md, Inventory Tests
**Dependency:** `add_topic` half blocked on SY-9 (T3)

**Fix:** Add two test rows:
1. "`replace_queries` missing `default_facet` → error: overlay `replace_queries` where `query_plan` has no `default_facet` key → non-zero exit, descriptive error."
2. "`add_topic` `query_plan` missing `default_facet` → error: overlay `add_topic` with `query_plan` without `default_facet` → non-zero exit, descriptive error." (Requires SY-9 spec fix first.)

#### [SY-19] `--inventory-snapshot` missing-flag behavior untested

**Source:** VR-10
**File:** delivery.md, CLI Integration Tests
**Dependency:** Blocked on SY-7 (T2)

**Fix:** Add test: "Missing `--inventory-snapshot` on full-CCDI `dialogue-turn` → non-zero exit: `dialogue-turn --registry-file <reg> --text-file <text> --source codex` (without `--inventory-snapshot`) → non-zero exit with descriptive error."

#### [SY-20] Layer 2b interception completeness unverifiable

**Source:** VR-11
**File:** delivery.md, Layer 2b tests

**Fix:** Add prerequisite test: "Interception completeness: Run a known fixture with exactly N expected `topic_inventory.py` invocations. Assert captured invocation count equals N." Guards against silent miss-counting in whichever interception mechanism is chosen.

#### [SY-21] `validate_graduation.py` CLI interface unspecified

**Source:** VR-12
**File:** delivery.md, Graduation Protocol

**Fix:** Add CLI interface specification for `validate_graduation.py`: arguments (flags for paths to annotations, diagnostics dir, graduation file — or auto-discovery convention), exit codes (0 = pass, 1 = fail), stdout/stderr format. Update test table inputs to reference the specified flags.

#### [SY-22] `ccdi_cli_recorder` shim naming constraint unenforced

**Source:** VR-13
**File:** delivery.md, Layer 2b tests

**Fix:** Add setup test: "Shim identity: assert `argv[0]` is NOT `python3` and is NOT on PATH as `python3`. Assert that `python3 <non-ccdi-script>` does not produce a CCDI log entry." Can be a pytest fixture-level assertion.

#### [SY-23] Shadow-mode `dialogue-turn` deferral isolation untested at CLI level

**Source:** VR-15
**File:** delivery.md, Layer 2b tests or Replay Harness fixtures

**Fix:** Add replay harness test: "Shadow mode: `dialogue-turn` with scout conflict does NOT write deferred state — run `dialogue-turn` with scout target active in fixture → assert candidates include scout-priority deferral candidate AND registry file does NOT contain any `deferred` state entry after `dialogue-turn` completes."

---

## Task 6 — P2 Batch

**Finding count:** 13 P2
**Files:** integration.md, data-model.md, delivery.md, registry.md, packets.md
**Depends on:** T2, T3 (some P2s touch same file sections as P1 fixes)

### Cross-Reference & Coherence (4)

| SY | Fix |
|----|-----|
| SY-25 | Change integration.md "Pipeline Isolation Invariants" header to "Pipeline Isolation Invariants (subset)" + add: "For the full set, see decisions.md#normative-decision-constraints." |
| SY-29 | Fix broken anchor in delivery.md: `packets.md#verbatim-vs-paraphrase` → correct GFM anchor, OR simplify packets.md heading to `## Verbatim vs Paraphrase` |
| SY-30 | Update delivery.md line 267 citation from `data-model.md#registryseed` to `registry.md#failure-modes` (the normative source) |
| SY-31 | Add note to integration.md CLI table: "`classify` uses `--inventory` (same purpose as `--inventory-snapshot` on other commands)" and show `--inventory <path>` in pre-dialogue/target-match flow examples |

### Contract Precision (3)

| SY | Fix |
|----|-----|
| SY-27 | Add to integration.md action normative values table: "In active mode, scout-priority deferral emits `skip_scout` (not `defer`) even though `--mark-deferred` is committed. In shadow mode, `skip_scout` indicates intended deferral not committed." |
| SY-28 | Harmonize data-model.md `results_file` phrasing to: "Strip from in-memory representation on load; stripped state is written to disk on the next normal mutation, not as a load-time side effect." |
| SY-33 | Add uniqueness constraint to data-model.md: "`rule_id` MUST be unique across all rules in the overlay's `rules[]` array. On duplicate: reject with non-zero exit." |

### Schema (3)

| SY | Fix |
|----|-----|
| SY-26 | Promote additive-only schema evolution invariant from data-model.md Failure Modes rationale to `## Version Axes` section as `### Schema Evolution Constraint`. Cross-reference from Failure Modes row. |
| SY-32 | Mark `overlay_meta` as optional in CompiledInventory schema tree: `overlay_meta?: { ... }` + add note: "May be absent in inventories built without an overlay — see Failure Modes." |
| SY-34 | Add note to Live Registry File Schema: "Entry-level null-field serialization: all nullable durable-state fields within each `entries[]` element MUST be serialized as explicit null — see Null-field serialization above." |

### Testing (3)

| SY | Fix |
|----|-----|
| SY-35 | Add TODO boundary test row to `test_ccdi_contracts.py` table: "`ccdi_policy_snapshot` field: present in delegation envelope → agent reads at dialogue start (Phase B only — mark XFAIL until shape defined)." |
| SY-36 | Add pytest mark pattern: behavioral equivalence test uses `@pytest.mark.source_equivalence_baseline`; meta-test asserts zero tests with this mark when source-differentiated entries exist. |
| SY-37 | Soften Layer 1 coverage claim from "full coverage" to "coverage of core data shapes and state transitions" + add note listing known gaps (multi-alias score accumulation, `overview_injected` → `family_context_available` propagation). |

---

## Decision Gates

| After | Condition | Path A | Path B |
|-------|-----------|--------|--------|
| T4 | ✅ Both decisions resolved | T5 is fully unblocked once T1–T3 land | N/A |
| T3 (SY-9) | `add_topic` rejection language landed | SY-18 `add_topic` half in T5 proceeds | SY-18 `add_topic` half deferred; `replace_queries` half proceeds independently |
| T2 (SY-7) | `--inventory-snapshot` contradiction resolved | SY-19 in T5 proceeds | SY-19 deferred until spec contradiction resolved |

## Critical Path

**Scheduling:** ~~T4 → T5~~ (T4 resolved). T1, T2, T3 execute in parallel. T4 edits interleave with T1–T3 (different file sections — T4 touches integration.md flow descriptions and data-model.md config keys, while T1–T3 touch side-effects, headings, CLI table, overlay table, spec.yaml). When T1–T4 complete, T5 starts. T6 can interleave with T5.

**Highest-risk task:** T2 (SY-3 — Shadow Mode Gate heading merge). The duplicate heading has 3 inbound cross-file references and the merge must preserve link resolution. Verify all anchors after the edit. Second: T4's SY-5 resolution adds substantial new spec content (`shadow_defer_intent` trace entry, `shadow_adjusted_yield` formula, freshness guardrail) — review for internal consistency after landing.

**Recommended first move:** Start T1 (clears the P0), T2, T3, and T4 in parallel — all four are now unblocked and touch different file sections.

## Out of Scope (Parked)

- **Cross-spec consistency** — no comparison with engram spec, consultation contract, or context-injection spec was in review scope
- **README accuracy** — README.md is non-normative and was checked only for authority misplacement
- **Design quality** — findings address internal consistency, not whether the design is optimal
- **`last_seen_turn` semantics on epoch-only re-entry** — deferred from round 5 T3; decide during implementation
