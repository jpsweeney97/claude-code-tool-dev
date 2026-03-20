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
├── suppression_reason: "weak_results" | "redundant" | null
├── deferred_reason: "cooldown" | "scout_priority" | "target_mismatch" | null
├── deferred_ttl: number | null       # turns remaining before re-evaluation
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
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
| `weak_results` | `docs_epoch` changes (index updated) OR a new query facet is requested for the topic |
| `redundant` | Coverage state changes — e.g., an injected facet is later identified as insufficient, or a new leaf variant appears under the same family |

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
3. **Cooldown:** Max one new docs topic injection per turn (configurable via [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson) → `injection.cooldown_max_new_topics_per_turn`).
4. **Scout priority:** If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
5. **Schedule** highest-priority materially new topic for lookup.

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
| Staged packet doesn't match composed follow-up target | Target-match check in [Step 5.5](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) | Defer CCDI candidate (→ `deferred: target_mismatch`) via `--mark-deferred` |
| Scout takes priority over CCDI candidate | Scout target exists for turn | Defer CCDI candidate (→ `deferred: scout_priority`) |
| Registry file missing or corrupt | CLI error | Reinitialize empty registry, lose coverage history |
| Semantic hints file malformed | CLI parse warning | Ignore hints, proceed with classifier-only scheduling |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
