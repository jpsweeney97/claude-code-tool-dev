---
module: registry
status: active
normative: true
authority: registry-contract
---

# CCDI Topic Registry

Per-conversation state machine tracking topic lifecycle. Prevents redundant injection and enables "materially new" detection. Used only in Full CCDI mode (not CCDI-lite). Registry state is read and written by the [`dialogue-turn` and `build-packet` CLI commands](integration.md#cli-tool-topic_inventorypy).

## Entry Structure

```
TopicRegistryEntry
├── topic_key: TopicKey
├── family_key: TopicKey
├── state: "detected" | "injected" | "suppressed" | "deferred"  # persisted type; runtime may include "looked_up" | "built" (see Durable vs Attempt-Local States)
├── first_seen_turn: number
├── last_seen_turn: number
├── last_injected_turn: number | null
├── last_query_fingerprint: string | null
├── consecutive_medium_count: number   # consecutive turns at medium confidence; reset on injection or confidence change
├── suppression_reason: "weak_results" | "redundant" | null
├── suppressed_docs_epoch: string | null  # docs_epoch at time of suppression. Written for all suppression reasons. For `weak_results`, used to determine re-entry when `docs_epoch` changes. For `redundant`, set but not consulted for re-entry — `redundant` re-entry is governed by coverage state changes and semantic hints only.
├── deferred_reason: "cooldown" | "scout_priority" | "target_mismatch" | null
├── deferred_ttl: number | null       # turns remaining before re-evaluation
├── coverage_target: "family" | "leaf" # classifier's resolved coverage target; populated at detection time from ClassifierResult
├── facet: Facet                       # classifier's resolved facet; populated at detection time from ClassifierResult.resolved_topics[].facet
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
    ├── pending_facets: Facet[]        # facets flagged for re-injection by contradicts_prior hint
    ├── family_context_available: boolean
    └── injected_chunk_ids: string[]
```

Valid `Facet` values: `overview`, `schema`, `input`, `output`, `control`, `config` (see [data-model.md#queryplan](data-model.md#queryplan)).

**Serialization invariant:** All fields MUST be written to the registry file including null-valued ones — see [data-model.md#registryseed](data-model.md#registryseed) for the normative requirement. An absent field triggers entry reinitialization per the resilience principle. This includes all `coverage.*` sub-fields: `overview_injected`, `facets_injected`, `pending_facets`, `family_context_available`, and `injected_chunk_ids` — all five are durable and MUST be serialized (empty arrays/false values are valid, not omittable).

## Durable vs Attempt-Local States

Only durable states are persisted to the registry file. Attempt-local states exist within a single CLI invocation and are never written to disk.

| State | Durability | Meaning |
|-------|-----------|---------|
| `detected` | Durable | Classifier found this topic; not yet looked up |
| `injected` | Durable | Packet was sent to Codex and send was confirmed |
| `suppressed` | Durable | Lookup returned weak/redundant results; will not re-attempt unless signal strengthens |
| `deferred` | Durable | Valid candidate that yielded to higher priority (scout evidence or cooldown); has TTL for re-evaluation |
| `looked_up` | Attempt-local | Search completed; deciding packet eligibility (not persisted) |
| `built` | Attempt-local | Packet built but not yet sent (not persisted) |

`injected` commits only after the agent observes successful send (the follow-up prompt containing the packet was delivered to Codex). If send fails, the topic remains `detected` (the commit step is skipped; `--mark-injected` is not called; the registry is not modified).

## State Transitions

```
absent ──→ detected ──→ [looked_up] ──→ [built] ──→ injected
                │               │
                │               ├──→ suppressed
                │               └──→ deferred ──→ detected (TTL expiry)
                │
                └──→ deferred (scout priority / cooldown)

suppressed ──→ detected (stronger signal)
```

States in `[brackets]` are attempt-local — they exist only within a single `dialogue-turn` or `build-packet` CLI invocation.

| Transition | Trigger |
|-----------|---------|
| `absent → detected` | Classifier resolves a new topic |
| `detected → [looked_up]` | Scheduler selects topic for docs search (within CLI call) |
| `[looked_up] → [built]` | Search returns enough signal for a non-empty fact packet (within CLI call) |
| `[built] → injected` | Agent confirms packet was included in sent prompt (commit phase) |
| `[looked_up] → suppressed` | Search results weak or redundant |
| `detected → deferred` | Valid candidate but cooldown active, scout evidence takes priority, or packet doesn't match composed target |
| `deferred → detected` | TTL expires AND topic reappears in classifier output (see [TTL lifecycle](#ttl-lifecycle) below) |
| `suppressed → detected` | Re-entry trigger aligned with suppression reason (see [below](#suppression-re-entry)) |

**Forward-only for `injected`:** Once injected, stays injected. If coverage is later insufficient, update `coverage` fields or create a new leaf entry — do not move backwards.

**`deferred` vs `suppressed`:** These are semantically distinct. `suppressed` means "we looked and found nothing useful" — the evidence is weak. `deferred` means "this is a valid candidate that lost to higher priority" — the evidence may be strong but timing was wrong. Deferred reasons: `cooldown` (turn budget exhausted), `scout_priority` (scout evidence took precedence), `target_mismatch` (packet doesn't support the composed follow-up target). Deferred topics get automatic re-evaluation via TTL; suppressed topics require new signal.

### Field Update Rules

Fields updated at each state transition. Fields not listed are unchanged.

| Transition | Fields updated |
|-----------|----------------|
| `absent → detected` | `first_seen_turn` ← current turn, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if medium AND leaf-kind, else 0) (family-kind topics always initialize `consecutive_medium_count` ← 0 regardless of confidence), `coverage_target` ← from `ClassifierResult.resolved_topics[].coverage_target`, `facet` ← from `ClassifierResult.resolved_topics[].facet` |
| Re-detection at medium confidence (entry in `detected` or `deferred` state, leaf-kind only) | `last_seen_turn` ← current turn, `consecutive_medium_count` ← `consecutive_medium_count` + 1. Family-kind topics at medium confidence: `last_seen_turn` updated but `consecutive_medium_count` unchanged. |
| Re-detection at non-medium confidence (entry in `detected` or `deferred` state) | `last_seen_turn` ← current turn, `consecutive_medium_count` ← 0 |
| Re-detection (entry in `injected` state) | `last_seen_turn` ← current turn; all other fields unchanged (state remains `injected`) |
| Re-detection (entry in `suppressed` state) | No field update — re-entry is governed by [Suppression Re-Entry](#suppression-re-entry) conditions, not by re-detection alone |
| Topic absent from classifier output (entry exists, any durable state) | `consecutive_medium_count` ← 0 |
| `contradicts_prior` hint resolves to `injected` topic | `coverage.pending_facets` ← append resolved facet (state stays `injected`) |
| `contradicts_prior`, `prescriptive`, or `extends_topic` hint resolves to `detected` or `deferred` topic | No field update — scheduling effect only (elevated to materially new for immediate lookup) |
| `prescriptive`, `contradicts_prior`, or `extends_topic` hint resolves to `suppressed` topic | Re-enter as `detected` — same field updates as `suppressed → detected` re-entry row below: `state` ← `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` ← current turn. See [Suppression Re-Entry](#suppression-re-entry) and [Semantic Hints](#semantic-hints) scheduling table. |
| `extends_topic` hint resolves to `injected` topic | No field update — `facet_expansion` candidate emitted immediately this turn via [scheduling step 9](#scheduling-rules). `pending_facets` is only mutated by `contradicts_prior` hints (see row above). State stays `injected`. |
| `[built] → injected` (via `--mark-injected`) | `state` ← `injected`, `last_injected_turn` ← current turn, `last_query_fingerprint` ← normalized fingerprint of query used, `coverage.injected_chunk_ids` ← append chunk IDs from built packet, `coverage.facets_injected` ← append facet, `coverage.pending_facets` ← remove served facet (if present), `consecutive_medium_count` ← 0 |
| `[built] → injected` (coverage_target=family, facet=overview) | Additionally: `coverage.overview_injected` ← true |
| `absent → detected` (leaf, parent family has `coverage.overview_injected = true`) | Additionally: `coverage.family_context_available` ← true |
| `absent → detected` (leaf, parent family not injected or not overview-covered) | `coverage.family_context_available` ← false |
| `detected → deferred` (via `--mark-deferred`) | `state` ← `deferred`, `deferred_reason` ← reason, `deferred_ttl` ← `injection.deferred_ttl_turns` from config |
| `[looked_up] → suppressed` | `state` ← `suppressed`, `suppression_reason` ← reason, `suppressed_docs_epoch` ← current inventory's `docs_epoch` |
| `suppressed → detected` (re-entry, any `suppression_reason`) | `state` ← `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if re-entry turn confidence is medium AND leaf-kind, else 0) (consistent with `absent → detected` and `deferred → detected` initialization). **Field sources depend on classifier presence:** If topic is present in current classifier output: `coverage_target` ← from `ClassifierResult.resolved_topics[].coverage_target`, `facet` ← from `ClassifierResult.resolved_topics[].facet` (refreshed from current classifier output, consistent with `deferred → detected`). If topic is absent from classifier output (e.g., `docs_epoch`-triggered re-entry): retain prior values for `coverage_target`, `facet`, and `confidence` — only `state`, `suppression_reason`, `suppressed_docs_epoch`, `last_seen_turn`, and `consecutive_medium_count` are reset. This row applies identically for both `weak_results` and `redundant` suppression reasons — the field resets are the same regardless of reason. |
| `deferred → detected` (TTL expiry + reappearance) | `state` ← `detected`, `deferred_reason` ← null, `deferred_ttl` ← null, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if re-entry turn confidence is medium AND leaf-kind, else 0) (family-kind topics always initialize to 0, consistent with `absent → detected`), `coverage_target` ← from `ClassifierResult.resolved_topics[].coverage_target`, `facet` ← from `ClassifierResult.resolved_topics[].facet` (both updated to current classifier resolution) |
| `deferred → deferred` (TTL=0, topic absent from classifier) | `deferred_ttl` ← `injection.deferred_ttl_turns` from config (reset). `last_seen_turn` is NOT updated — the topic was absent from classifier output this turn. `state`, `deferred_reason` unchanged. `consecutive_medium_count` ← 0 (via the general "topic absent from classifier output" rule in the row above — not a transition-specific action; listed here for completeness). |

**Seed-build initialization:** At seed-build time (in `ccdi-gatherer`, before the first `dialogue-turn` call), durable-state fields are initialized per the `absent → detected` row above. In particular, `consecutive_medium_count` is `1` if the entry's initial detection confidence is `medium`, else `0`. This ensures the mid-dialogue scheduling logic starts with the correct baseline — a topic first detected at medium confidence needs one more medium turn (not two) to reach the injection threshold. See [data-model.md#registryseed](data-model.md#registryseed) for the RegistrySeed schema.

**`consecutive_medium_count` on send failure:** When a packet is staged (prepare phase) but send fails (commit phase skipped), `consecutive_medium_count` is NOT reset — the `[built] → injected` transition never fires, so the counter retains its pre-failure value. On the next turn, if the topic reappears at medium confidence, the counter increments from the retained value. This means injection may fire again on the next medium-confidence turn (acceptable double-attempt; the topic genuinely qualifies). The counter resets to 0 only via: (a) successful `--mark-injected` commit, (b) topic absent from classifier output, or (c) topic appears at a different confidence level.

**`last_query_fingerprint` normalization:** Lowercased query string with whitespace collapsed. Includes `docs_epoch` if available — same key composition as the [session-local cache](#session-local-cache).

### TTL Lifecycle

When a topic transitions to `deferred`, set `deferred_ttl` to the value of [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.deferred_ttl_turns` (default: 3).

**Decrement rule:** Each `dialogue-turn` invocation decrements `deferred_ttl` by 1 for all entries in `deferred` state, regardless of whether the topic appears in the current classifier output.

**Transition rule:** When `deferred_ttl` reaches 0:
- If the topic also appears in the current `dialogue-turn` classifier output → transition to `detected` (re-eligible for scheduling).
- If the topic does NOT appear in the current classifier output → reset `deferred_ttl` to `deferred_ttl_turns` and remain `deferred`. The topic needs both TTL expiry and classifier re-detection to re-enter the pipeline.

### Suppression Re-Entry

Re-entry conditions are aligned with the `suppression_reason`, not with classifier signal strength (suppression is caused by weak search results, not weak alias matching):

| `suppression_reason` | Re-entry trigger |
|---------------------|-----------------|
| `weak_results` | `docs_epoch` differs from `suppressed_docs_epoch` (index updated since suppression — uses null comparison rules below) OR any semantic hint (`extends_topic`, `prescriptive`, or `contradicts_prior`) resolves to the suppressed topic (see [Semantic Hints](#semantic-hints)) |
| `redundant` | Coverage state changes detectable by `dialogue-turn` from classifier output: (a) a new leaf `topic_key` under the same `family_key` as the suppressed topic transitions to `detected` (new leaf variant), or (b) any semantic hint (`extends_topic`, `prescriptive`, or `contradicts_prior`) resolves to the suppressed topic (new signal overrides prior suppression). Path (a) is detected mechanically by `dialogue-turn` when processing classifier output; path (b) requires a semantic hint via `--semantic-hints-file`. The prose example "an injected facet is later identified as insufficient" is only detectable via path (b) — no classifier-only mechanism exists for that case. |

**`docs_epoch` comparison semantics:** `null == null` is not a change (no re-entry). `null → non-null` is a change (re-entry fires). `non-null → null` is a change (re-entry fires). Comparison is string equality on non-null values.

See [integration.md#dialogue-turn-registry-side-effects](integration.md#dialogue-turn-registry-side-effects) for the `dialogue-turn` implementation of these re-entry checks.

## Family vs Leaf Coverage

Family injection does NOT satisfy leaf-specific needs:

| Event | Registry effect |
|-------|----------------|
| Inject `hooks` family overview | `hooks.coverage.overview_injected = true` |
| `hooks.post_tool_use` appears later | New leaf entry in `detected`, with `family_context_available = true` |
| Leaf lookup | `family_context_available` lowers retrieval breadth (skip overview, go to leaf-specific facet) |

## Scheduling Rules

Each turn, after the [classifier](classifier.md) runs on Codex's latest response:

1. **Diff** new resolved topics against registry.
2. **Materially new** = one of:
   - High-confidence topic not yet in `injected` state — includes first appearance (absent from registry) AND re-detection of a `detected` or `deferred` topic at high confidence (per [classifier.md#injection-thresholds](classifier.md#injection-thresholds))
   - New leaf under an already-covered family
   - Agent provides a `semantic_hint` (see [below](#semantic-hints)) referencing a claim that touches a detected topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Facet resolution for lookup:** When scheduling a topic for lookup, use the facet from the classifier's resolved output. If the scheduled facet is not present in the topic's `QueryPlan.facets` (or maps to an empty `QuerySpec[]` array), fall back to `default_facet`. If `default_facet` is also absent (or empty), transition to `suppressed: weak_results` — no valid query is available, which is functionally equivalent to a search returning no results. This prevents an infinite scheduling loop where the topic is re-selected every turn without progressing.
4. **Consecutive-turn medium tracking:** For each `detected` **leaf-kind** topic at medium confidence, increment `consecutive_medium_count`. Family-kind topics at medium confidence are tracked in the registry but do not participate in consecutive-medium injection — only high-confidence detection or a semantic hint can trigger family injection. Reset to 0 if the topic is absent from classifier output or appears at a different confidence level. Injection fires when `consecutive_medium_count` reaches `injection.mid_turn_consecutive_medium_turns` (default: 2). Reset to 0 after injection fires.
5. **Cooldown:** Max one new docs topic injection per turn (configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.cooldown_max_new_topics_per_turn`).
6. **Scout priority:** If context-injection has a scout candidate for the current turn, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
7. **Schedule** highest-priority materially new topic for lookup. **Priority ordering among candidates:** (1) `confidence` descending (`high` before `medium`; `null` for hint-driven candidates sorts after `medium` — see note below), (2) `first_seen_turn` ascending (earlier-detected topics first), (3) `topic_key` lexicographic ascending (deterministic tiebreaker). This ordering ensures identical scheduling decisions for identical inputs regardless of implementation, per the CLI determinism principle in [foundations.md#cliagent-separation](foundations.md#cliagent-separation).
8. **`pending_facet` candidate emission:** For each `injected` topic with non-empty `pending_facets` (populated by prior `contradicts_prior` hints — `extends_topic` does NOT write to `pending_facets`), emit a `pending_facet` candidate at the first pending facet not already in `facets_injected`. The candidate's `coverage_target` is sourced from the persisted `TopicRegistryEntry.coverage_target` (the topic is already `injected`). This check runs on every `dialogue-turn` call, independent of classifier output.
9. **`facet_expansion` candidate emission:** When an `extends_topic` hint resolves to an `injected` topic at a facet not yet in `facets_injected`, emit a `facet_expansion` candidate at the cascade-resolved facet (hint-resolved → `pending_facets[0]` → `default_facet`). The candidate's `coverage_target` is sourced from the persisted `TopicRegistryEntry.coverage_target`. If all candidate facets are already in `facets_injected`, discard the hint silently — no candidate emitted, no state change.

**Steps 1–9 run in the CLI via `dialogue-turn`.** Step 10 runs agent-side after `build-packet` returns.

10. **Target-match check (agent-side):** After building a packet for a scheduled candidate, the agent verifies the packet supports the composed follow-up target. If the check fails, the topic transitions to `deferred` with `target_mismatch` reason. See [integration.md#target-match-predicate](integration.md#target-match-predicate) for the two-condition algorithm (substring check + optional classifier fallback), the definition of "target-relevant," and the CLI interface (`--mark-deferred`, `--skip-build`).

**`confidence: null` sort note:** `confidence` may be `null` for `pending_facet` and `facet_expansion` candidates (see [integration.md#dialogue-turn-registry-side-effects](integration.md#dialogue-turn-registry-side-effects) for the type extension). Null-confidence candidates sort after all non-null candidates.

Each candidate emitted by `dialogue-turn` includes a `candidate_type` discriminator field (`"new"` | `"facet_expansion"` | `"pending_facet"`). See [integration.md#dialogue-turn-candidates-json-schema](integration.md#dialogue-turn-candidates-json-schema) for the full candidates JSON schema.

**`--source codex|user` note:** The `--source` flag on `dialogue-turn` does not affect scheduling rules — both sources use identical scheduling logic. No source-differentiated rules are currently defined. See [delivery.md#known-open-items](delivery.md#known-open-items) for the deferred divergence item.

## Semantic Hints

The `codex-dialogue` agent provides semantic judgment about Codex's responses; the CLI resolves topic keys and makes scheduling decisions. This separation keeps the CLI deterministic while leveraging the agent's conversational understanding (see [foundations.md#cliagent-separation](foundations.md#cliagent-separation) for the architectural principle).

**Agent → CLI interface:** The `dialogue-turn` command accepts an optional `--semantic-hints-file <path>` argument containing a JSON array:

```json
[
  {
    "claim_index": 3,
    "hint_type": "prescriptive",
    "claim_excerpt": "you should use updatedInput to modify..."
  }
]
```

| Field | Type | Purpose |
|-------|------|---------|
| `claim_index` | number | Diagnostic/trace metadata only — position of the claim in Codex's response. The CLI does NOT use this for topic resolution. |
| `hint_type` | `"prescriptive" \| "contradicts_prior" \| "extends_topic"` | What the agent observed |
| `claim_excerpt` | string | **Authoritative locator.** Short excerpt the CLI classifies through its normal alias-matching pipeline (≤ 100 chars). This is how the CLI determines which topic the hint maps to. |

The CLI classifies `claim_excerpt` through its standard two-stage pipeline to resolve the topic key. The agent never emits `topic_key` values — that would couple it to the CCDI taxonomy.

**Scheduling effects by `hint_type`:**

| `hint_type` | Resolved topic state | Scheduling effect |
|------------|---------------------|-------------------|
| `prescriptive` | `detected` or `deferred` | Elevate to "materially new" — schedule for immediate lookup |
| `prescriptive` | `injected` | No effect — topic already covered. **Replay fixture assertion:** `final_registry_file_assertions` MUST verify `pending_facets` array is unchanged from initial state and no injection or deferral mutations occur. |
| `prescriptive` | `suppressed` | Re-enter as `detected` (new agent signal overrides prior suppression — applies to both `weak_results` and `redundant`, same re-entry as `extends_topic`/`suppressed`). Rationale: a prescriptive claim from Codex is strong evidence the topic is relevant, regardless of prior weak search results. |
| `contradicts_prior` | `injected` | Flag coverage gap — append resolved facet to `coverage.pending_facets`. On subsequent scheduling passes, emit a `pending_facet` candidate via `dialogue-turn` candidates JSON ([integration.md#dialogue-turn-candidates-json-schema](integration.md#dialogue-turn-candidates-json-schema)) with the first pending facet not already in `facets_injected`. Coverage update, not state revert. |
| `contradicts_prior` | `detected` or `deferred` | Elevate to "materially new" (same as `prescriptive`) |
| `contradicts_prior` | `suppressed` | Re-enter as `detected` (same re-entry as `prescriptive`/`suppressed` and `extends_topic`/`suppressed`). Rationale: if Codex contradicts prior information about a suppressed topic, the original search results may have been insufficient — re-entry is warranted. |
| `extends_topic` | `suppressed` | Re-enter as `detected` regardless of `suppression_reason` (new signal overrides prior suppression — applies to both `weak_results` and `redundant`; see [Suppression Re-Entry](#suppression-re-entry)) |
| `extends_topic` | `detected` or `deferred` | Elevate to "materially new" (same as `prescriptive`) |
| `extends_topic` | `injected` | Flag for facet expansion via [scheduling step 9](#scheduling-rules). Cascade: (1) facet resolved from `claim_excerpt` classification, (2) `pending_facets[0]` if resolved facet already in `facets_injected`, (3) `default_facet` if all pending facets exhausted. Emit a `facet_expansion` candidate at the first cascade facet not yet in `facets_injected`. If all candidate facets (resolved, pending, default) are already in `facets_injected`: discard hint silently, no state change, no candidate emitted. Does NOT mutate `coverage.pending_facets` — only `contradicts_prior` writes to that field. |
| *(any)* | topic not resolved | Hint ignored — `claim_excerpt` did not match any inventory topic |

**Hint facet resolution:** When a semantic hint triggers any scheduling effect (elevation, facet expansion, or re-entry), the CLI classifies `claim_excerpt` through the standard two-stage pipeline to resolve both the topic key and the facet hint from matched aliases. The resolved facet from `claim_excerpt` classification is used as the `facet` field in the emitted candidates JSON entry for this turn, overriding the stored facet from prior detection for scheduling purposes only. The `TopicRegistryEntry.facet` field in the registry file is NOT modified by hint processing — see field update rules table. This applies to all hint types and all topic states — including `extends_topic` on `injected` topics (where the resolved facet is the primary candidate for expansion).

**`contradicts_prior` on `injected` — operational definition:** When a `contradicts_prior` hint resolves to an `injected` topic, the CLI appends the resolved facet to `coverage.pending_facets` (the field added in the entry structure). The topic's `state` does not change — it remains `injected`. On subsequent scheduling passes, the scheduler checks `pending_facets` and schedules a lookup at the first pending facet not already in `facets_injected`. After successful injection at the pending facet, remove it from `pending_facets`.

## Session-Local Cache

| Cache | Key | Value | Purpose |
|-------|-----|-------|---------|
| Result cache | normalized query fingerprint | search results | Avoid re-searching identical queries |
| Packet cache | `(topic_key, facet)` | built fact packet | Avoid re-building identical packets |
| Negative cache | normalized query fingerprint | `weak` flag | Don't re-search queries that returned noise |

Cache is session-local — dies with the conversation. Include `docs_epoch` in cache keys if available.

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| Packet staged but send fails | Agent observes send failure | No commit (topic stays `detected`, not `injected`) |
| `build-packet` produces empty output at prepare time | Automatic suppression (see [integration.md](integration.md#build-packet-automatic-suppression)) | Topic transitions to `suppressed` at prepare time — this is an intentional exception to the prepare/commit split. Suppression is a deterministic CLI side-effect, not an agent commitment, so it does not require send confirmation. The topic is removed from the candidate pool before the target-match check. |
| Staged packet doesn't match composed follow-up target | Target-match check in [Step 5.5 (CCDI PREPARE)](integration.md#target-match-predicate) | Defer CCDI candidate (→ `deferred: target_mismatch`) via `--mark-deferred` |
| Scout takes priority over CCDI candidate | Scout target exists for turn | Defer CCDI candidate (→ `deferred: scout_priority`) |
| Registry file missing or corrupt | CLI error | Reinitialize empty registry, log warning. See [foundations.md#resilience-principle](foundations.md#resilience-principle) for the registry reinit exception and rationale. |
| Partial commit (in-place mutation interrupted) | CLI error on next load | Each `--mark-injected` or `--mark-deferred` call reads the full file, modifies the target entry in memory, and writes the full file atomically (write to temp, rename). If the write is interrupted, the file may be corrupt — the next CLI load triggers reinitialization per the resilience principle. Partial-commit recovery: uncommitted topics remain in their pre-mutation state and are candidates for re-injection on subsequent turns. |
| Semantic hints file malformed | CLI parse warning | Ignore hints, proceed with classifier-only scheduling |
| Registry file loaded with `deferred_ttl: 0` (abnormal shutdown during TTL processing) | CLI load-time check | Treat as TTL-expired: apply the `deferred → detected` or `deferred → deferred` transition rule on the next `dialogue-turn` call, depending on whether the topic appears in classifier output. A persisted `deferred_ttl: 0` is a valid intermediate state — it means the TTL expired but the transition was not completed before the prior session ended. |
| Registry file loaded with `results_file` field present | CLI load-time check | Strip `results_file` from the in-memory representation and log warning. The `results_file` is a transient field populated by `--prepare` and consumed by the agent within a single turn. Its presence at load time indicates abnormal shutdown. The stripped state is written back on the next normal mutation. |
| `RegistrySeed.inventory_snapshot_version` mismatch at load time | CLI string comparison at seed load | Proceed with best-effort field mapping. Discard entries for `topic_key` values not present in the current inventory and continue. Discarded entries are removed in-memory only — the registry file is NOT rewritten at load time due to version mismatch. Rewriting is deferred to the next normal `--mark-injected` or `--mark-deferred` mutation, at which point the file reflects only the retained entries. |

**Load-time validation:** CLI MUST validate that family-kind entries have `consecutive_medium_count == 0`. A non-zero value on a family-kind entry indicates data corruption — family-kind topics never participate in consecutive-medium tracking (per [scheduling rules](#scheduling-rules) step 4). On violation: reset to 0 and log warning.

All failure modes degrade gracefully — consultations are never blocked per the [resilience principle](foundations.md#resilience-principle). Degradation ranges from session-level CCDI disable to topic-level suppression to state recovery with continued CCDI operation — see individual rows above.
