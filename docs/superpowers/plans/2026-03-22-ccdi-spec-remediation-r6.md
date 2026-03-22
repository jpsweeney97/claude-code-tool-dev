# CCDI Spec Review Round 6 — Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 35 findings (5 P0, 19 P1, 11 P2) from CCDI spec review round 6.

**Architecture:** All changes are to spec files in `docs/superpowers/specs/ccdi/`. No code changes. Three commits ordered by priority and dependency: P0 + tightly-coupled P1 → remaining P1 → P2. Two pattern clusters drive sequencing: Cluster A (`shadow_defer_intent` — 6 findings across 4 reviewers) and Cluster B (high-confidence TTL bypass — 2 findings across 2 reviewers).

**Tech Stack:** Markdown spec files

**Review workspace:** `.review-workspace/synthesis/report.md` (35 canonical findings), `.review-workspace/findings/` (5 reviewer files)

---

## File Map

| File | Changes | Findings Addressed |
|------|---------|-------------------|
| `integration.md` | Add `shadow_defer_intent` to action enum + key-presence exception; fix shadow-mode cooldown contradiction; move schema authority from delivery.md; add `skip_cooldown` shadow-mode behavior; clarify `--inventory-snapshot` footnote; add target-match snapshot note | SY-1, SY-2, SY-3, SY-6, SY-9, SY-27, SY-28 |
| `delivery.md` | Add `### Graduation Protocol` heading; add Layer 2b mechanism test + freshness guardrail test; update `shadow_defer_intent` section to reference integration.md; add 10 replay fixtures/tests; revise harness execution model; specify `avg_latency_ms` aggregation | SY-4, SY-5, SY-6, SY-14, SY-15–SY-24, SY-31–SY-35 |
| `registry.md` | Add high-confidence bypass Field Update Rules row; fix seed-build leaf-kind qualifier; change counter fields to `integer` | SY-7, SY-8, SY-30 |
| `data-model.md` | Fix seed-build leaf-kind qualifier; add `replace_aliases` non-empty enforcement; make `results_file` optional; fix `docs_epoch` contradiction; replace inline field enumeration with forward-reference | SY-8, SY-10, SY-11, SY-12, SY-13 |
| `packets.md` | Align `token_estimate` schema diagram to `integer` | SY-29 |
| `README.md` | Add "Normative" column to authority table | SY-25 |
| `decisions.md` | Fix misleading link text | SY-26 |

---

## Dependency Graph

```
SY-1 ──┐
SY-2 ──┼── Cluster A root (commit 1) ──► SY-18, SY-21 (commit 2)
SY-6 ──┘
SY-3 ── independent P0 (commit 1) ──► SY-9 (commit 1)
SY-7 ── Cluster B root (commit 1) ──► SY-15 (commit 2)
SY-4, SY-5, SY-8, SY-14 ── independent (commit 1)
All other P1 ── no upstream deps (commit 2)
All P2 ── no upstream deps (commit 3)
```

---

### Task 1: Remediate 5 P0 + 5 P1 findings [Cluster A root + shadow-mode + verification foundations]

Fixes the root causes that downstream P1 findings depend on. All "implementer builds wrong system" defects.

**Files:**
- Modify: `docs/superpowers/specs/ccdi/integration.md:62,278,280-294,293,393`
- Modify: `docs/superpowers/specs/ccdi/delivery.md:85-100,116,647-669`
- Modify: `docs/superpowers/specs/ccdi/registry.md:89-114,116`
- Modify: `docs/superpowers/specs/ccdi/data-model.md:266`

#### SY-1 (P0): Add `shadow_defer_intent` to integration.md action enum

- [ ] **Step 1: Add action value to normative table**

In `integration.md`, add a new row to the `action` normative values table (after the `skip_scout` row at line 294):

```markdown
| `shadow_defer_intent` | Shadow mode counterfactual deferral: agent would have called `--mark-deferred` in active mode but is prohibited in shadow mode. Emitted as a diagnostic-only trace entry — see [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). |
```

#### SY-2 (P0): Carve key-presence exception for `shadow_defer_intent` entries

- [ ] **Step 2: Add exception to key-presence invariant**

In `integration.md` line 278, after the sentence ending with `...`semantic_hints` MUST be `null` when no hints exist (not absent from the entry).`, add:

```markdown
**Exception for diagnostic entries:** `shadow_defer_intent` trace entries are counterfactual observations, not turn-loop observations. They are exempt from the 8-key requirement and use a reduced schema: `turn`, `action`, `topic_key`, `reason`, `classify_result_hash`. See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for the entry schema and semantics.
```

#### SY-3 (P0): Fix shadow-mode cooldown deferral three-way contradiction

- [ ] **Step 3: Add shadow-mode exception to `dialogue-turn` cooldown writes**

In `integration.md` line 62, after "These entries do NOT appear in the candidates JSON output — the cooldown deferral is an internal CLI side-effect.", add:

```markdown
**Shadow-mode exception:** In shadow mode, the cooldown deferral write is suppressed — `candidate_type:'new'` entries excluded by the per-turn cooldown limit remain in `detected` state. A `shadow_defer_intent` trace entry with `reason: "cooldown"` is emitted instead (see [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization)).
```

- [ ] **Step 4: Update shadow-mode registry invariant**

In `integration.md` line 393, replace the shadow-mode registry invariant paragraph (starts with "**Shadow-mode registry invariant:** In shadow mode, the only permitted registry mutations are automatic suppressions", ends with "See [decisions.md#normative-decision-constraints]...") with:

```markdown
**Shadow-mode registry invariant:** In shadow mode, the only permitted registry mutations are automatic suppressions written by `build-packet` empty output (`suppressed: weak_results` or `suppressed: redundant`). All three other mutation types are prohibited: (1) agent-driven `--mark-injected` (Step 7.5), (2) agent-driven `--mark-deferred` (Step 5.5), and (3) `dialogue-turn` cooldown deferral writes (Step 5.5, line 62). The prepare cycle runs to measure yield and latency for diagnostics, but the registry reflects only classifier-driven state. Deferral state is recorded in diagnostics only. This prevents shadow-mode registry pollution from corrupting graduation kill-criteria metrics. See [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints).
```

#### SY-4 (P0): Add Layer 2b mechanism feasibility test

- [ ] **Step 5: Add named CI test as Phase A prerequisite**

In `delivery.md`, in the "Phase A feasibility gate" paragraph (line 669), replace:

```
**Done when:** One mechanism is implemented and the 3 behavioral agent sequence tests (classify ordering, skip-when-no-candidates, --mark-injected-after-codex-reply) pass.
```

with:

```
**Done when:** One mechanism is implemented, `test_layer2b_mechanism_selection` passes (asserts the chosen mechanism is one of {primary, fallback} via a fixture constant, and verifies the shim identity test passes — argv[0] ≠ python3), and the 3 behavioral agent sequence tests (classify ordering, skip-when-no-candidates, --mark-injected-after-codex-reply) pass.
```

#### SY-5 (P0): Add freshness guardrail test

- [ ] **Step 6: Add guardrail test specification**

In `delivery.md`, after the freshness guardrail paragraph (line 98), add:

```markdown
**Freshness guardrail test:** A Layer 2b test MUST verify the guardrail fires correctly. Configure a fixture where `classify_result_hash` produces identical hashes for different input texts across two turns (simulating a non-freshness-sensitive hash function). Assert that `validate_graduation.py` reports `shadow_adjusted_yield` as non-authoritative and uses only raw `effective_prepare_yield` for kill-criteria evaluation. Alternatively, a unit test against the `shadow_defer_intent` resolution logic covering the case where `classify_result_hash` is identical across turns despite input change — the intent MUST NOT resolve via condition (a).
```

#### SY-6 (P1): Move `shadow_defer_intent` schema authority to integration.md

- [ ] **Step 7: Add entry schema to integration.md**

In `integration.md`, after the new `shadow_defer_intent` row added in Step 1, add:

```markdown
**`shadow_defer_intent` entry schema:** Unlike per-turn trace entries (which use the 8-key structure above), `shadow_defer_intent` entries use a diagnostic-only schema:

```json
{"turn": 3, "action": "shadow_defer_intent", "topic_key": "hooks.pre_tool_use", "reason": "target_mismatch", "classify_result_hash": "a7f3..."}
```

Fields: `turn` (integer — the turn number), `action` (always `"shadow_defer_intent"`), `topic_key` (string — the topic that would have been deferred), `reason` (`"target_mismatch"` or `"cooldown"` — the deferral reason that would have been written), `classify_result_hash` (string — hash of the classify result payload for evidence-freshness tracking). See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for repeat-detection semantics and intent resolution.
```

- [ ] **Step 8: Update delivery.md to reference integration.md**

In `delivery.md` lines 85–100, replace the inline schema definition and the sentence "the `shadow_defer_intent` trace entries stay within `delivery.md` diagnostics authority" (line 100) with a reference. Replace:

```
**`shadow_defer_intent` trace entry:** Emitted when the agent would have called `--mark-deferred` in active mode but is prohibited in shadow mode:

```json
{"turn": 3, "action": "shadow_defer_intent", "topic_key": "hooks.pre_tool_use", "reason": "target_mismatch", "classify_result_hash": "a7f3..."}
```

- `reason`: `"target_mismatch"` or `"cooldown"` — the deferral reason that would have been written
- `classify_result_hash`: hash of the classify result payload for this topic on this turn, used as an evidence-freshness marker
```

with:

```
**`shadow_defer_intent` trace entry:** Emitted when the agent would have called `--mark-deferred` in active mode but is prohibited in shadow mode. Entry schema defined in [integration.md#ccdi_trace-output-contract](integration.md#ccdi_trace-output-contract) under the `shadow_defer_intent` action value. Key fields: `reason` (`"target_mismatch"` or `"cooldown"`), `classify_result_hash` (evidence-freshness marker).
```

And remove the sentence "the `shadow_defer_intent` trace entries stay within `delivery.md` diagnostics authority — they are counterfactual observations, not committed registry mutations." from line 100 (the authority claim is now correctly in integration.md).

#### SY-7 (P1): Add high-confidence TTL bypass row to Field Update Rules

- [ ] **Step 9: Add row to Field Update Rules table**

In `registry.md`, after the `deferred → detected (TTL expiry + reappearance)` row (line 113), add a new row:

```markdown
| `deferred → detected` (high-confidence bypass, via [scheduling step 2](#scheduling-rules)) | `state` ← `detected`, `deferred_reason` ← null, `deferred_ttl` ← null, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if re-entry turn confidence is medium AND leaf-kind, else 0) (note: this row fires only on high-confidence re-detection, so `consecutive_medium_count` is always 0 here — listed for completeness and consistency with `deferred → detected (TTL expiry)` row), `coverage_target` ← from `ClassifierResult.resolved_topics[].coverage_target`, `facet` ← from `ClassifierResult.resolved_topics[].facet` (both updated to current classifier resolution, identical to TTL-expiry row) |
```

#### SY-8 (P1): Add leaf-kind qualifier to seed-build initialization notes

- [ ] **Step 10: Fix registry.md seed-build note**

In `registry.md` line 116, replace:

```
In particular, `consecutive_medium_count` is `1` if the entry's initial detection confidence is `medium`, else `0`.
```

with:

```
In particular, `consecutive_medium_count` is `1` if the entry's initial detection confidence is `medium` AND the entry is a leaf-kind topic, else `0`. Family-kind topics always initialize `consecutive_medium_count` to `0` regardless of confidence.
```

- [ ] **Step 11: Fix data-model.md seed-build note**

In `data-model.md` line 266, the "Seed-build initialization" paragraph references registry.md. Verify it does not restate the rule incorrectly. If it restates "consecutive_medium_count is 1 if medium" without the leaf-kind qualifier, add "AND leaf-kind" to match the registry.md fix.

#### SY-9 (P1): Add `skip_cooldown` shadow-mode behavior

- [ ] **Step 12: Add shadow-mode clarification to `skip_cooldown` action**

In `integration.md` line 293, replace the `skip_cooldown` row:

```
| `skip_cooldown` | Topic deferred due to per-turn cooldown (`deferred: cooldown` state written by `dialogue-turn`) |
```

with:

```
| `skip_cooldown` | Topic deferred due to per-turn cooldown (`deferred: cooldown` state written by `dialogue-turn` in active mode). In shadow mode, `skip_cooldown` is emitted even though the `deferred: cooldown` registry write is suppressed (per the shadow-mode exception on line 62). The `skip_cooldown` trace entry records the active-mode action; a separate `shadow_defer_intent` entry with `reason: "cooldown"` is emitted to the counterfactual log per [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). |
```

#### SY-14 (P1): Add `### Graduation Protocol` heading

- [ ] **Step 13: Add heading in delivery.md**

In `delivery.md`, immediately before line 116 (`**Graduation protocol:** Shadow-to-active graduation...`), add:

```markdown
### Graduation Protocol
```

And change line 116 from:

```
**Graduation protocol:** Shadow-to-active graduation is a manual gate with a concrete approval artifact:
```

to:

```
Shadow-to-active graduation is a manual gate with a concrete approval artifact:
```

(The bold inline text becomes the section heading instead.)

- [ ] **Step 14: Verify integration.md cross-references**

Confirm that `integration.md` lines 182 and 308 reference `delivery.md#graduation-protocol` — this anchor now exists. No change needed if the links already use this anchor.

- [ ] **Step 15: Commit**

```bash
git add docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/delivery.md docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/data-model.md
git commit -m "fix(spec): remediate 5 P0 + 5 P1 findings from CCDI spec review round 6

P0: SY-1 (shadow_defer_intent enum), SY-2 (key-presence exception),
SY-3 (shadow-mode cooldown contradiction), SY-4 (Layer 2b mechanism test),
SY-5 (freshness guardrail test)

P1: SY-6 (authority placement), SY-7 (high-confidence bypass row),
SY-8 (leaf-kind qualifier), SY-9 (skip_cooldown shadow-mode),
SY-14 (orphaned anchor)"
```

---

### Task 2: Remediate 14 P1 findings [remaining spec defects + verification gaps]

**Files:**
- Modify: `docs/superpowers/specs/ccdi/data-model.md:239,255,260,285`
- Modify: `docs/superpowers/specs/ccdi/delivery.md:141-153,355-356,387-388,541-558,562-568,638-639,645-675`

#### SY-10 (P1): Add non-empty enforcement for `replace_aliases`

- [ ] **Step 1: Add enforcement to overlay rule**

In `data-model.md` line 239, replace the `replace_aliases` row:

```
| `replace_aliases` | `rule_id`, `operation`, `topic_key`, `aliases` (Alias[]) | — |
```

with:

```
| `replace_aliases` | `rule_id`, `operation`, `topic_key`, `aliases` (Alias[] — MUST include at least one element. On violation (empty `aliases` array): reject the overlay rule with descriptive error.) | — |
```

#### SY-11 (P1): Make `results_file` optional in schema diagram

- [ ] **Step 2: Add optionality marker**

In `data-model.md` line 255, replace:

```
└── results_file: string            # path to search results file for initial commit phase
```

with:

```
└── results_file?: string           # path to search results file for initial commit phase; absent when no pre-dialogue search was performed
```

#### SY-12 (P1): Fix `docs_epoch` self-contradiction

- [ ] **Step 3: Remove incorrect initialization sentence**

In `data-model.md` line 285, replace the `docs_epoch` row description:

```
| `docs_epoch` | `string \| null` | Hash of the indexed document set at seed creation time; retained for traceability only. The `docs_epoch` used for suppression re-entry comparisons is sourced from the pinned inventory snapshot (via `--inventory-snapshot`), not from this field. This field's value initializes `TopicRegistryEntry.suppressed_docs_epoch` at suppression time (see [registry.md#field-update-rules](registry.md#field-update-rules)). |
```

with:

```
| `docs_epoch` | `string \| null` | Hash of the indexed document set at seed creation time; retained for traceability only. This field is NOT read by the CLI at suppression time — `suppressed_docs_epoch` is sourced from the pinned inventory snapshot (via `--inventory-snapshot`), not from this envelope field. See [registry.md#field-update-rules](registry.md#field-update-rules). |
```

#### SY-13 (P1): Replace inline field enumeration with forward-reference

- [ ] **Step 4: Replace inline coverage enumeration**

In `data-model.md` line 260, in the `entries` field paragraph, replace:

```
This includes the `coverage` sub-object and all five of its sub-fields: `overview_injected` (boolean), `facets_injected` (Facet[]), `pending_facets` (Facet[]), `family_context_available` (boolean), `injected_chunk_ids` (string[]) — all durable, all serialized.
```

with:

```
This includes all durable-state fields from `TopicRegistryEntry` as defined in [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states), including the `coverage` sub-object with all of its sub-fields — all durable, all serialized.
```

#### SY-15 (P1): Add TTL=1 edge case test

- [ ] **Step 5: Add TTL=1 bypass fixture**

In `delivery.md`, after the `high_confidence_bypasses_deferred_ttl.replay.json` fixture (line 639), add:

```markdown
| `high_confidence_bypasses_deferred_ttl_ttl1.replay.json` | Configure `deferred_ttl_turns=2`. Turn 1 → topic D deferred:target_mismatch (TTL=2). Turn 2 → TTL decrements to 1; same topic D re-detected at high confidence in the same `dialogue-turn` call → assert topic D transitions to `detected` with `deferred_reason: null`, `deferred_ttl: null` (bypass fires, NOT the `deferred → deferred` TTL-reset path at TTL=0). This exercises the TTL=1 edge case where decrement and bypass interact in the same turn. |
```

#### SY-16 (P1): Add fresh initialization fixture

- [ ] **Step 6: Add seed initialization fixture**

In `delivery.md`, after the `seed_medium_baseline.replay.json` fixture (line 568), add:

```markdown
#### `seed_medium_fresh_init.replay.json`

Exercises the seed-build initialization rule for `consecutive_medium_count` from a brand-new topic (no prior registry state).

- **Initial state:** Registry file with NO entry for the test topic (topic absent from registry).
- **Classifier output:** Topic detected at medium confidence, leaf-kind.
- **Expected:** `consecutive_medium_count` = 1 after first `dialogue-turn` (seed-build initialization rule applied: medium AND leaf-kind → 1).

This directly tests the `absent → detected` initialization path. The existing `seed_medium_baseline.replay.json` tests counter persistence (pre-existing count=2 → 3), not first-time initialization. Retitle `seed_medium_baseline` description to "Exercises counter persistence across serialization boundary" (not "seed-build initialization").
```

#### SY-17 (P1): Revise `results_file` strip test description

- [ ] **Step 7: Make two-step nature explicit**

In `delivery.md` lines 387–388, replace the test description:

```
Run `build-packet --mark-injected` with an invalid `--topic-key` (not in seed) → non-zero exit. Assert `results_file` is still stripped from the file on the next successful mutation (the field is stripped at write time, not as a commit side-effect).
```

with:

```
Two-step test: (1) Run `build-packet --mark-injected` with an invalid `--topic-key` (not in seed) → non-zero exit, file unchanged. (2) Run a successful mutation (e.g., `dialogue-turn` that writes a state update) → assert `results_file` absent from on-disk JSON after the successful write. This verifies write-time stripping semantics: the field is stripped from the in-memory representation at load time, and this stripped state is persisted on the next successful mutation — not as a side-effect of the failed commit.
```

#### SY-18 (P1): Add `shadow_defer_intent` resolution condition (b) and (c) tests

- [ ] **Step 8: Add resolution tests**

In `delivery.md`, in the Layer 2b agent sequence tests section (after the shadow-mode tests around line 675), add two test rows:

```markdown
| Shadow mode: `shadow_defer_intent` resolves on topic disappearance | Fixture: Turn 2 emits `shadow_defer_intent` for topic T. Turn 3 → T absent from classifier output → assert intent is resolved, `repeat_detections_from_missing_deferral` does NOT increment on turn 3 even if T reappears on a later turn with a new `classify_result_hash`. Verifies resolution condition (b). |
| Shadow mode: `shadow_defer_intent` resolves on committed state transition | Fixture: Turn 2 emits `shadow_defer_intent` for topic T. Turn 3 → T reaches `suppressed` state (via `build-packet` empty output / automatic suppression). Turn 4 → T reappears in classifier output → assert intent is resolved (suppression would have prevented re-evaluation in active mode), `repeat_detections_from_missing_deferral` does NOT increment. Verifies resolution condition (c). |
```

#### SY-19 (P1): Add `consecutive_medium_count` reset assertion to deferred fixture

- [ ] **Step 9: Add assertion to existing fixture**

In `delivery.md` line 638, in the `deferred_ttl_countdown_resets.replay.json` fixture description, after "Turn 5 → topic B reappears → verify transition to `detected`.", add:

```markdown
`final_registry_file_assertions` MUST include: `{"path": "<topic>.consecutive_medium_count", "equals": 0}` at a turn where topic B is in `deferred` state and absent from classifier output (verifying the general "topic absent from classifier output → `consecutive_medium_count` ← 0" rule applies during `deferred → deferred` transitions).
```

#### SY-20 (P1): Extend replay harness for multi-candidate turns

- [ ] **Step 10: Extend harness execution model**

In `delivery.md`, in the replay harness execution model (line 547, step 5), replace:

```
5. If candidates are non-empty AND `search_results` are provided for the candidate topic:
```

with:

```
5. For each candidate in the candidates array (in scheduling priority order): if `search_results` are provided for the candidate's topic:
```

And after step 7 (line 557), add:

```markdown
   Repeat steps 5–7 for each remaining candidate in the array.
```

Also, in the `pending_facet_exempt_from_cooldown.replay.json` fixture (line 643), add:

```markdown
`assertions.cli_pipeline_sequence` MUST verify two `build-packet` invocations occurred in the same turn (one per candidate).
```

#### SY-21 (P1): Add `shadow_defer_intent` trace entry production test

- [ ] **Step 11: Add Layer 2b test**

In `delivery.md`, in the Layer 2b agent sequence tests section, add:

```markdown
| Shadow mode: `shadow_defer_intent` trace entries emitted | Delegation envelope with `ccdi_seed`, no `graduation.json`, fixture has a candidate that would be deferred for `target_mismatch` or `cooldown` → after dialogue, read `ccdi_trace` from diagnostics and assert at least one entry with `action: "shadow_defer_intent"` is present, with correct `topic_key`, `reason`, and `classify_result_hash` fields. Verifies the diagnostic entry is produced in shadow mode per [integration.md#ccdi_trace-output-contract](integration.md#ccdi_trace-output-contract). |
```

#### SY-22 (P1): Add complementary config threshold divergence test

- [ ] **Step 12: Add permissive-config test**

In `delivery.md`, after the "Agent gate unchanged when `initial_threshold_*` overridden" test (line 355–356), add:

```markdown
| Agent gate unchanged when config is more permissive than hardcoded threshold | `ccdi_config.json` with `injection.initial_threshold_high_count: 0` (permissive — any detection would meet CLI threshold). Input has 0 high-confidence topics and 1 medium-confidence topic (not meeting the agent's hardcoded 2+ same-family medium threshold). Assert the agent-side gate does NOT dispatch, confirming the agent uses its hardcoded threshold (1 high-confidence OR 2+ medium same-family) and DOES NOT read `ccdi_config.json`. Complements the existing test which covers the converse direction (agent dispatches when CLI would not). |
```

#### SY-23 (P1): Add minimum sample size enforcement test

- [ ] **Step 13: Add test to `test_validate_graduation.py` table**

In `delivery.md`, in the `test_validate_graduation.py` test table (lines 141–153), add a new row:

```markdown
| Labeled topics below minimum sample size | `graduation.json` with `labeled_topics: 50`, `status: "approved"`, `false_positive_rate: 0.04` | Exit 1, error reports "labeled_topics: 50 is below minimum 100 required for false_positive_rate evaluation" |
```

#### SY-24 (P1): Add `weak_results` full-scan no-op test

- [ ] **Step 14: Add replay fixture**

In `delivery.md`, after the `weak_results_reentry_on_epoch_change.replay.json` fixture (line 645), add:

```markdown
| `weak_results_scan_noop_absent.replay.json` | Registry with topic suppressed:weak_results at `docs_epoch="A"`. Inventory snapshot `docs_epoch="A"` (unchanged). Topic absent from classifier output. After `dialogue-turn`: assert registry file is byte-identical (no field updates from the full-scan evaluation — `docs_epoch` unchanged, topic absent, no re-entry condition met). Verifies the `weak_results` full-scan no-op path: scan fires (per spec, every turn for all `suppressed:weak_results` entries) but produces no mutations when epoch is unchanged and topic is absent. |
```

- [ ] **Step 15: Commit**

```bash
git add docs/superpowers/specs/ccdi/data-model.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 14 P1 findings from CCDI spec review round 6

Spec defects: SY-10 (replace_aliases enforcement), SY-11 (results_file optional),
SY-12 (docs_epoch contradiction), SY-13 (forward-reference)

Verification gaps: SY-15 (TTL=1 edge case), SY-16 (seed fresh init),
SY-17 (results_file test revision), SY-18 (shadow_defer_intent resolution),
SY-19 (consecutive_medium_count reset), SY-20 (multi-candidate harness),
SY-21 (shadow_defer_intent test), SY-22 (config divergence complement),
SY-23 (minimum sample size), SY-24 (weak_results scan no-op)"
```

---

### Task 3: Remediate 11 P2 findings [naming, types, minor test gaps]

**Files:**
- Modify: `docs/superpowers/specs/ccdi/README.md:18-28`
- Modify: `docs/superpowers/specs/ccdi/decisions.md:61`
- Modify: `docs/superpowers/specs/ccdi/integration.md:22,399-412`
- Modify: `docs/superpowers/specs/ccdi/packets.md:24`
- Modify: `docs/superpowers/specs/ccdi/registry.md:19-27`
- Modify: `docs/superpowers/specs/ccdi/delivery.md:528-537,629,452`

#### SY-25 (P2): Add normative column to README authority table

- [ ] **Step 1: Update authority table**

In `README.md` lines 18–28, add a "Normative" column to the authority table:

```markdown
| Authority | Claims | Scope | Normative |
|-----------|--------|-------|-----------|
| `foundation` | architecture_rule | Cross-cutting architecture, design principles, resilience principle, scope boundary | Yes |
| `data-model` | persistence_schema, architecture_rule | Topic inventory schema, version axes, overlay merge semantics, config schema, lifecycle | Yes |
| `classifier-contract` | behavior_contract, interface_contract | Two-stage pipeline, confidence levels, injection thresholds | Yes |
| `registry-contract` | behavior_contract, interface_contract | State machine, transitions, scheduling, semantic hints | Yes |
| `packet-contract` | behavior_contract, interface_contract | Fact packets, token budgets, citation format, rendering | Yes |
| `integration` | behavior_contract, interface_contract | CLI interface, data flows, prepare/commit, delegation | Yes |
| `delivery` | implementation_plan, verification_strategy | Rollout, testing, diagnostics | Yes |
| `decisions` | decision_record | Locked design decisions from Codex dialogues | Yes |
| `supporting` | *(none)* | README and reference material | No |
```

#### SY-26 (P2): Fix misleading link text in decisions.md

- [ ] **Step 2: Fix link text**

In `decisions.md` line 61, replace:

```
[integration.md#shadow-mode-registry-invariant](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue)
```

with:

```
[integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue)
```

#### SY-27 (P2): Clarify `--inventory-snapshot` footnote scope

- [ ] **Step 3: Clarify footnote**

In `integration.md` line 22, at the end of the ‡ footnote, add:

```
`--inventory-snapshot` is required on `dialogue-turn` when `--registry-file` is present. On `build-packet`, `--inventory-snapshot` is optional; when absent, `suppressed_docs_epoch` is recorded as null if the topic is auto-suppressed.
```

#### SY-28 (P2): Add target-match inventory snapshot note

- [ ] **Step 4: Add snapshot note**

In `integration.md`, in the Target-Match Predicate section (after line 408), add:

```markdown
**Inventory snapshot for condition (b):** The `classify` invocation for condition (b) SHOULD use the pinned inventory snapshot (`--inventory <ccdi_snapshot_path>`) to ensure topic resolution is consistent with the `dialogue-turn` classification within the same dialogue. Using the default on-disk inventory for target-match is acceptable if mid-dialogue inventory refresh is guaranteed not to alter topic taxonomy.
```

#### SY-29 (P2): Align `token_estimate` type in packets.md

- [ ] **Step 5: Fix schema diagram type**

In `packets.md` line 24, replace:

```
└── token_estimate: number
```

with:

```
└── token_estimate: integer   # >= 0
```

#### SY-30 (P2): Change counter fields to `integer` in registry.md

- [ ] **Step 6: Update TopicRegistryEntry schema**

In `registry.md` lines 19–27, replace:

```
├── first_seen_turn: number
├── last_seen_turn: number
├── last_injected_turn: number | null
```

with:

```
├── first_seen_turn: integer
├── last_seen_turn: integer
├── last_injected_turn: integer | null
```

And replace:

```
├── consecutive_medium_count: number   # consecutive turns at medium confidence; reset on injection or confidence change
```

with:

```
├── consecutive_medium_count: integer  # consecutive turns at medium confidence; reset on injection or confidence change
```

And replace:

```
├── deferred_ttl: number | null       # turns remaining before re-evaluation
```

with:

```
├── deferred_ttl: integer | null      # turns remaining before re-evaluation
```

#### SY-31 (P2): Add `replace_refs`/`replace_queries` unknown-topic tests

- [ ] **Step 7: Add validation tests**

In `delivery.md`, in the inventory test suite, add:

```markdown
| `replace_refs` on unknown topic → warning, rule skipped, inventory unchanged | Overlay with `replace_refs` targeting `nonexistent.topic` → non-zero exit not required; warning emitted, rule skipped, compiled inventory unchanged. Mirrors the `remove_alias` on unknown topic test. |
| `replace_queries` on unknown topic → warning, rule skipped, inventory unchanged | Overlay with `replace_queries` targeting `nonexistent.topic` → same skip-on-unknown behavior as `replace_refs`. |
```

#### SY-32 (P2): Extend `ccdi_trace` key-presence checks

- [ ] **Step 8: Add comprehensive key assertions to happy_path fixture**

In `delivery.md`, in the `happy_path.replay.json` fixture description (line 610), add:

```markdown
`trace_assertions` MUST also include `assert_key_present` checks for ALL 8 required keys (`turn`, `classifier_result`, `semantic_hints`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`) on at least one turn entry. This exercises the key-presence invariant at the replay harness level.
```

#### SY-33 (P2): Add ordering assertion to `target_match_classifier_branch`

- [ ] **Step 9: Add condition (a) evaluation assertion**

In `delivery.md` line 629, in the `target_match_classifier_branch.replay.json` fixture, append:

```markdown
Required assertions MUST also include: CLI call log shows `classify --text-file <composed_target_tempfile>` was invoked (confirming condition (b) was reached, which implies condition (a) was evaluated first and failed). Symmetric with `target_match_both_fail.replay.json` assertion pattern.
```

#### SY-34 (P2): Add duplicate `rule_id` test

- [ ] **Step 10: Add overlay-level uniqueness test**

In `delivery.md`, in the inventory tests, add:

```markdown
| Duplicate `rule_id` across non-`add_deny_rule` operations → non-zero exit | Overlay with two `override_weight` rules sharing the same `rule_id` value → non-zero exit, error identifies the duplicate `rule_id`. Tests the overlay-level `rule_id` uniqueness constraint (distinct from the `add_deny_rule`-specific `deny_rule.id` uniqueness test). |
```

#### SY-35 (P2): Specify `avg_latency_ms` aggregation method

- [ ] **Step 11: Add aggregation specification**

In `delivery.md`, in the `validate_graduation.py` section (after line 126, within the validator checks), add:

```markdown
**Aggregation method:** `avg_latency_ms` is the unweighted mean of ALL `per_turn_latency_ms` entries across ALL diagnostics files (mean-of-all-turns, not mean-of-dialogue-means). For heterogeneous dialogues where per-dialogue mean latencies differ, these formulas produce different values. The validator MUST use mean-of-all-turns.
```

And in the `test_validate_graduation.py` table (line 149), update the "Yield/latency metrics arithmetically inconsistent" test to specify:

```markdown
| Yield/latency metrics arithmetically inconsistent (heterogeneous dialogues) | Per-dialogue diagnostics files with heterogeneous per-turn latency distributions — mean-of-all-turns differs from mean-of-dialogue-means. `graduation.json` declares the mean-of-dialogue-means value. | Exit 1, error identifies `avg_latency_ms` inconsistency with computed mean-of-all-turns vs declared mean-of-means |
```

- [ ] **Step 12: Commit**

```bash
git add docs/superpowers/specs/ccdi/README.md docs/superpowers/specs/ccdi/decisions.md docs/superpowers/specs/ccdi/integration.md docs/superpowers/specs/ccdi/packets.md docs/superpowers/specs/ccdi/registry.md docs/superpowers/specs/ccdi/delivery.md
git commit -m "fix(spec): remediate 11 P2 findings from CCDI spec review round 6

SY-25 (README normative column), SY-26 (decisions.md link text),
SY-27 (inventory-snapshot footnote), SY-28 (target-match snapshot),
SY-29 (token_estimate type), SY-30 (counter integer types),
SY-31 (replace_refs/queries tests), SY-32 (key-presence checks),
SY-33 (target_match ordering), SY-34 (duplicate rule_id test),
SY-35 (avg_latency_ms aggregation)"
```
