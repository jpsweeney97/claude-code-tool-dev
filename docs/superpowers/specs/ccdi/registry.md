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
├── state: "detected" | "injected" | "suppressed" | "deferred"
├── first_seen_turn: number
├── last_seen_turn: number
├── last_injected_turn: number | null
├── last_query_fingerprint: string | null
├── consecutive_medium_count: number   # consecutive turns at medium confidence; reset on injection or confidence change
├── suppression_reason: "weak_results" | "redundant" | null
├── suppressed_docs_epoch: string | null  # docs_epoch at time of suppression; used for re-entry comparison
├── deferred_reason: "cooldown" | "scout_priority" | "target_mismatch" | null
├── deferred_ttl: number | null       # turns remaining before re-evaluation
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
    ├── pending_facets: Facet[]        # facets flagged for re-injection by contradicts_prior hint
    ├── family_context_available: boolean
    └── injected_chunk_ids: string[]
```

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

`injected` commits only after the agent observes successful send (the follow-up prompt containing the packet was delivered to Codex). If send fails, the topic reverts to `detected` — not `injected`.

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
| `absent → detected` | `first_seen_turn` ← current turn, `last_seen_turn` ← current turn, `consecutive_medium_count` ← (1 if medium, else 0) |
| Re-detection at medium confidence | `last_seen_turn` ← current turn, `consecutive_medium_count` ← `consecutive_medium_count` + 1 |
| Re-detection at non-medium confidence (entry exists) | `last_seen_turn` ← current turn, `consecutive_medium_count` ← 0 |
| Topic absent from classifier output (entry exists) | `consecutive_medium_count` ← 0 |
| `contradicts_prior` hint resolves to `injected` topic | `coverage.pending_facets` ← append resolved facet (state stays `injected`) |
| `[built] → injected` (via `--mark-injected`) | `state` ← `injected`, `last_injected_turn` ← current turn, `last_query_fingerprint` ← normalized fingerprint of query used, `coverage.injected_chunk_ids` ← append chunk IDs from built packet, `coverage.facets_injected` ← append facet, `coverage.pending_facets` ← remove served facet (if present), `consecutive_medium_count` ← 0 |
| `[built] → injected` (coverage_target=family, facet=overview) | Additionally: `coverage.overview_injected` ← true |
| `absent → detected` (leaf, parent family has `coverage.overview_injected = true`) | Additionally: `coverage.family_context_available` ← true |
| `absent → detected` (leaf, parent family not injected or not overview-covered) | `coverage.family_context_available` ← false |
| `detected → deferred` (via `--mark-deferred`) | `state` ← `deferred`, `deferred_reason` ← reason, `deferred_ttl` ← `injection.deferred_ttl_turns` from config |
| `[looked_up] → suppressed` | `state` ← `suppressed`, `suppression_reason` ← reason, `suppressed_docs_epoch` ← current inventory's `docs_epoch` |
| `suppressed → detected` (re-entry) | `state` ← `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` ← current turn |
| `deferred → detected` (TTL expiry + reappearance) | `state` ← `detected`, `deferred_reason` ← null, `deferred_ttl` ← null, `last_seen_turn` ← current turn |

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
| `weak_results` | `docs_epoch` differs from `suppressed_docs_epoch` (index updated since suppression — uses null comparison rules below) OR a new query facet is requested for the topic OR an `extends_topic` semantic hint resolves to the suppressed topic (see [Semantic Hints](#semantic-hints)) |
| `redundant` | Coverage state changes — e.g., an injected facet is later identified as insufficient, or a new leaf variant appears under the same family |

**`docs_epoch` comparison semantics:** `null == null` is not a change (no re-entry). `null → non-null` is a change (re-entry fires). `non-null → null` is a change (re-entry fires). Comparison is string equality on non-null values.

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
   - New leaf under an already-covered family
   - Agent provides a `semantic_hint` (see [below](#semantic-hints)) referencing a claim that touches a detected topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Consecutive-turn medium tracking:** For each `detected` topic at medium confidence, increment `consecutive_medium_count`. Reset to 0 if the topic is absent from classifier output or appears at a different confidence level. Injection fires when `consecutive_medium_count` reaches `injection.mid_turn_consecutive_medium_turns` (default: 2). Reset to 0 after injection fires.
4. **Cooldown:** Max one new docs topic injection per turn (configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.cooldown_max_new_topics_per_turn`).
5. **Scout priority:** If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
6. **Target-match check:** After building a packet for a scheduled candidate, verify the packet supports the composed follow-up target. If not target-relevant, defer the topic (→ `deferred` state with `target_mismatch` reason via `--mark-deferred`). The definition of "composed follow-up target" is specified in [integration.md#target-match-predicate](integration.md#target-match-predicate).
7. **Schedule** highest-priority materially new topic for lookup.

## Semantic Hints

The `codex-dialogue` agent provides semantic judgment about Codex's responses; the CLI resolves topic keys and makes scheduling decisions. This separation keeps the CLI deterministic while leveraging the agent's conversational understanding.

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
| `prescriptive` | `detected` | Elevate to "materially new" — schedule for immediate lookup |
| `prescriptive` | `injected` | No effect — topic already covered |
| `contradicts_prior` | `injected` | Flag coverage gap — mark topic for re-injection at a new facet (coverage update, not state revert) |
| `contradicts_prior` | `detected` or `deferred` | Elevate to "materially new" (same as `prescriptive`) |
| `extends_topic` | `suppressed` | Re-enter as `detected` (new signal overrides prior `weak_results` suppression) |
| `extends_topic` | `detected` or `deferred` | Elevate to "materially new" (same as `prescriptive`) |
| `extends_topic` | `injected` | Flag for facet expansion — schedule lookup at a facet not yet in `facets_injected` |
| *(any)* | topic not resolved | Hint ignored — `claim_excerpt` did not match any inventory topic |

**Hint facet resolution:** When a semantic hint elevates a topic, the CLI classifies `claim_excerpt` through the standard two-stage pipeline to resolve both the topic key and the facet hint from matched aliases. The resolved facet from `claim_excerpt` classification is used as the candidate facet, overriding any facet from prior detection.

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
| Staged packet doesn't match composed follow-up target | Target-match check in [Step 5.5 (CCDI PREPARE)](integration.md#target-match-predicate) | Defer CCDI candidate (→ `deferred: target_mismatch`) via `--mark-deferred` |
| Scout takes priority over CCDI candidate | Scout target exists for turn | Defer CCDI candidate (→ `deferred: scout_priority`) |
| Registry file missing or corrupt | CLI error | Reinitialize empty registry, log warning. Coverage history is lost — topics already sent may be re-injected. This is an acceptable degradation: premise enrichment is idempotent from Codex's perspective (duplicate context is low-harm). See [resilience principle](foundations.md#resilience-principle). |
| Semantic hints file malformed | CLI parse warning | Ignore hints, proceed with classifier-only scheduling |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
