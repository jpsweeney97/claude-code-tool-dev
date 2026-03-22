---
module: data-model
status: active
normative: true
authority: data-model
---

# CCDI Data Model

## CompiledInventory

A JSON artifact mapping Claude Code extension concepts to aliases, query plans, and doc references. Shared knowledge base for both the [classifier](classifier.md) and the [packet builder](packets.md).

```
CompiledInventory
├── schema_version: string             # current: "1"
├── built_at: ISO timestamp
├── docs_epoch: string | null          # reload/version marker from claude-code-docs. All nullable fields (`docs_epoch`) MUST be serialized with explicit null when null — never omitted.
├── topics: Record<TopicKey, TopicRecord>
├── denylist: DenyRule[]
├── overlay_meta?: { overlay_version: string, overlay_schema_version: string, applied_rules: AppliedRule[] }  # optional — absent in inventories built without an overlay (see Failure Modes)
└── merge_semantics_version: string    # current: "1"; version of the overlay merge algorithm
```

### OverlayMeta

| Field | Type | Purpose |
|-------|------|---------|
| `overlay_version` | string | Instance version of the curated overlay file (monotonically incremented by curator) |
| `overlay_schema_version` | string | Format version of the overlay file (validated at merge time) |
| `applied_rules` | `AppliedRule[]` | Records of overlay operations applied during inventory build |

## Version Axes

Four version axes prevent coupled evolution (three compatibility axes + one instance version):

| Axis | Field | What changes | Who changes it |
|------|-------|-------------|---------------|
| Inventory schema | `schema_version` | TopicRecord fields, Alias structure, DenyRule shape | Code change (Python) |
| Overlay schema | `overlay_meta.overlay_schema_version` | Overlay file format, supported operations | Code change (Python) |
| Merge semantics | `merge_semantics_version` | How overlay operations apply to inventory | Code change (Python) |
| Overlay instance | `overlay_meta.overlay_version` | Which version of the curated overlay file was applied | Manual edit (human) |

**Version string format:** All version fields (`schema_version`, `overlay_schema_version`, `merge_semantics_version`, `overlay_version`, `config_version`, `inventory_snapshot_version`) are opaque strings. The current convention uses integer strings (`"1"`, `"2"`, ...) for simplicity. Comparison is string equality — no semver parsing, no numeric ordering. A version mismatch means "not equal," not "older than."

`overlay_version` is an **instance version** (which edit of the overlay file), not a **compatibility axis** (whether the overlay format is readable). It is monotonically incremented by the overlay curator on each manual edit. `build_inventory.py` records it in `overlay_meta` for traceability but does not validate compatibility — that is the job of `overlay_schema_version`.

`build_inventory.py` validates compatibility between all three axes at merge time. On mismatch: fail loudly with specific version pair and required action. Do NOT silently fall back — overlays are curated artifacts, and silent incompatibility corrupts human-maintained data.

**Validation when `overlay_meta` absent:** When `overlay_meta` is absent, no overlay was applied; version-axis validation for `overlay_schema_version` and `overlay_version` is vacuously satisfied (there is nothing to validate). `merge_semantics_version` is always present at the top level of `CompiledInventory` and is validated against the CLI's supported version at load time regardless of whether an overlay was applied.

### Schema Evolution Constraint

`CompiledInventory` schema evolution is additive-only: new fields with defaults, never removed or renamed fields. This invariant makes best-effort field mapping safe at load time (see [Failure Modes](#failure-modes)) — consumers can read inventories built under a prior schema version because unknown fields are ignored and missing fields fall back to defaults. All files that consume `CompiledInventory` (classifier.md, registry.md, packets.md) depend on this constraint.

**Registry Entry Schema Field Defaults:** These defaults are used when loading a registry file serialized under an older schema version. Fields absent in the loaded `TopicRegistryEntry` are initialized to these values. Although placed here under the Schema Evolution Constraint (which governs both inventory and registry schemas), these defaults apply specifically to `TopicRegistryEntry` fields within the live registry file — not to `CompiledInventory` fields. See [registry.md#entry-structure](registry.md#entry-structure) for the authoritative field definitions.

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
| `first_seen_turn` | `0` |
| `family_key` | derived from `topic_key` (family prefix) |
| `kind` | `"leaf"` |
| `coverage_target` | `"leaf"` |
| `facet` | `"overview"` |
| `coverage.overview_injected` | `false` |
| `coverage.family_context_available` | `false` |

**Defaults vs initialization:** The defaults above are load-time schema-evolution fallbacks only — they apply when a field is absent from a serialized registry entry loaded under an older schema version. For new entry initialization at runtime (`absent → detected`), see [registry.md#field-update-rules](registry.md#field-update-rules). In particular, `consecutive_medium_count` initializes to `1` (not `0`) for medium-confidence leaf-kind entries at detection time. The schema default `0` is a safe fallback for old entries missing the field; it does not govern runtime initialization.

These defaults ensure safe load-time migration for entries serialized before these fields were added. `family_key` default is derived by extracting the family prefix from `topic_key` (e.g., `hooks` from `hooks.pre_tool_use`).

## TopicRecord

| Field | Type | Purpose |
|-------|------|---------|
| `topic_key` | string | Hierarchical key, e.g., `hooks.pre_tool_use` |
| `family_key` | string | Parent family, e.g., `hooks` |
| `kind` | `"family" \| "leaf"` | Family = category, leaf = specific concept |
| `canonical_label` | string | Display name, e.g., `"PreToolUse"` |
| `category_hint` | string | Maps to `claude-code-docs` category filter |
| `parent_topic` | TopicKey \| null | null for families |
| `aliases` | Alias[] (minimum 1) | All terms that refer to this topic. Every topic must have at least one searchable alias — a topic with zero aliases is not classifiable. |
| `query_plan` | QueryPlan | Pre-computed search queries per facet |
| `canonical_refs` | DocRef[] | Known chunk IDs for diagnostics/packet building. MAY be empty (scaffold-generated topics with no known chunks); empty array is valid and does not prevent classification or scheduling — only packet building uses this field. |

## Alias

| Field | Type | Purpose |
|-------|------|---------|
| `text` | string | e.g., `"PreToolUse"`, `"updatedInput"` |
| `match_type` | `"exact" \| "phrase" \| "token" \| "regex"` | How to match against input |
| `weight` | 0.0–1.0 | Classification strength |
| `facet_hint` | Facet \| null | Which aspect this alias implies |
| `source` | `"generated" \| "overlay"` | Provenance |

Do NOT collapse Alias to plain strings — alias-level weights and facet hints are where the semantic power lives.

**Weight range enforcement:** `weight` MUST be in `[0.0, 1.0]`. `build_inventory.py` clamps out-of-range alias weights to this range with a warning. Clamping applies to all alias-producing operations: scaffold generation, `add_topic` (each alias in `topic_record.aliases`), `override_weight`, and `replace_aliases` (each alias in the replacement array). All four operations use identical clamping behavior: values above 1.0 are clamped to 1.0; values below 0.0 are clamped to 0.0.

## QueryPlan

```
QueryPlan
├── default_facet: Facet
└── facets: Record<Facet, QuerySpec[]>
    └── QuerySpec: { q: string, category: string | null, priority: number }
```

Facets: `overview`, `schema`, `input`, `output`, `control`, `config`.

## DenyRule

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Rule identifier |
| `pattern` | string | e.g., `"overview"`, `"settings"` |
| `match_type` | `"token" \| "phrase" \| "regex"` | How to match. `"exact"` is intentionally excluded — deny rules operate on alias text during compilation, where `"token"` covers whole-word denial, `"phrase"` covers multi-word, and `"regex"` covers precise patterns. Use `"token"` for whole-word denial of identifiers. |
| `action` | `"drop" \| "downrank"` | Eliminate or penalize |
| `penalty` | number \| null | Discriminated by `action`: when `action: "drop"`, `penalty` MUST be `null`. When `action: "downrank"`, `penalty` MUST be a non-null number in the range (0.0, 1.0] — i.e., strictly greater than zero and at most 1.0. `penalty: 0` violates this constraint and is a build-time error (not merely a warning) because a zero-penalty downrank rule silently has no effect on alias weights, defeating the purpose of the curated deny rule. Violations of the discriminated union (drop + non-null, downrank + null, downrank + zero) are build-time errors — `build_inventory.py` rejects the overlay with non-zero exit. |
| `reason` | string | Why this term is problematic |

**Build-time penalty validation:** During overlay build (`build_inventory.py`): all penalty validation rules are defined in the `DenyRule` discriminated union constraint above — violations (including `penalty: 0`, out-of-range values, and union mismatches) are build-time errors.

**Load-time validation:** When loading a compiled inventory, each DenyRule MUST satisfy its `action`/`penalty` discriminated union: `action: "drop"` requires `penalty: null`; `action: "downrank"` requires non-null `penalty` in (0.0, 1.0]. Out-of-range `penalty` values (`penalty ≤ 0.0` or `penalty > 1.0`) for `downrank` rules are treated identically to discriminated-union violations: skip the offending rule with a warning log entry. Do not fail the entire inventory load. This aligns with the [resilience principle](foundations.md#resilience-principle).

**Schema invariant — build-time vs load-time asymmetry:** The compiled inventory (`topic_inventory.json`) may contain DenyRules that were valid under a prior schema version but are invalid under the current schema — load-time validation handles this via warn-and-skip per the resilience principle. Build-time enforcement prevents new invalid rules; load-time tolerance preserves backward compatibility.

**Penalty application:** `downrank` reduces the individual alias weight before summing into the topic score. If alias `A` has weight 0.6 and matches denylist rule with penalty 0.35, the effective weight is `0.6 - 0.35 = 0.25`. Negative effective weights are clamped to 0.

## DocRef

| Field | Type | Purpose |
|-------|------|---------|
| `chunk_id` | string | e.g., `"hooks#pretooluse-2"` |
| `category` | string | e.g., `"hooks"` |
| `source_file` | string | URL from docs server |

## Examples

### TopicRecord Example

```json
{
  "topic_key": "hooks.pre_tool_use",
  "family_key": "hooks",
  "kind": "leaf",
  "canonical_label": "PreToolUse",
  "category_hint": "hooks",
  "parent_topic": "hooks",
  "aliases": [
    {"text": "PreToolUse", "match_type": "exact", "weight": 1.0, "facet_hint": "overview", "source": "generated"},
    {"text": "pre tool use", "match_type": "phrase", "weight": 0.95, "facet_hint": "overview", "source": "generated"},
    {"text": "permissionDecision", "match_type": "exact", "weight": 0.9, "facet_hint": "schema", "source": "generated"},
    {"text": "updatedInput", "match_type": "exact", "weight": 0.7, "facet_hint": "schema", "source": "generated"},
    {"text": "tool inputs", "match_type": "phrase", "weight": 0.35, "facet_hint": "input", "source": "overlay"}
  ],
  "query_plan": {
    "default_facet": "overview",
    "facets": {
      "overview": [{"q": "PreToolUse hook", "category": "hooks", "priority": 1}],
      "schema": [
        {"q": "PreToolUse JSON output", "category": "hooks", "priority": 1},
        {"q": "PreToolUse decision control", "category": "hooks", "priority": 2}
      ],
      "input": [{"q": "PreToolUse input tool_input", "category": "hooks", "priority": 1}]
    }
  },
  "canonical_refs": [
    {"chunk_id": "hooks#pretooluse", "category": "hooks", "source_file": "https://code.claude.com/docs/en/hooks"},
    {"chunk_id": "hooks#pretooluse-2", "category": "hooks", "source_file": "https://code.claude.com/docs/en/hooks"}
  ]
}
```

### Denylist Example

```json
[
  {"id": "drop-overview", "pattern": "overview", "match_type": "token", "action": "drop", "penalty": null, "reason": "too generic"},
  {"id": "downrank-schema", "pattern": "schema", "match_type": "token", "action": "downrank", "penalty": 0.35, "reason": "facet word, not topic anchor"}
]
```

## AppliedRule

Records which overlay operations were applied during inventory build. Stored in `overlay_meta.applied_rules[]`.

**Dual-source note:** Most `applied_rules[]` entries correspond to items in the overlay's `rules[]` array. The exception is `operation: "override_config"` — these entries originate from the `config_overrides` root key, not from `rules[]`. Code reading `applied_rules[]` must handle this: there is no corresponding `OverlayRule` in `rules[]` for config override entries. **Schema discriminator:** `operation: "override_config"` entries MUST use the `config-override:` prefix in `rule_id` (e.g., `config-override:classifier.confidence_high_min_weight`). Consumers can distinguish config-override entries from rule-sourced entries by checking `rule_id.startswith("config-override:")` OR `operation == "override_config"` — both are reliable discriminators.

| Field | Type | Purpose |
|-------|------|---------|
| `rule_id` | string | Overlay rule identifier (for `override_config`: a synthetic ID formatted as `config-override:<dot.path>`, e.g., `config-override:classifier.confidence_high_min_weight`). **Uniqueness constraint:** Each `rule_id` MUST be unique across all rules in the overlay's `rules[]` array. On duplicate `rule_id`: reject the overlay with non-zero exit and descriptive error identifying the duplicates. |
| `operation` | `"add_topic" \| "remove_alias" \| "add_deny_rule" \| "override_weight" \| "replace_aliases" \| "replace_refs" \| "replace_queries" \| "override_config"` | What the rule did |
| `target` | string | Semantics depend on operation: for topic-scoped operations (`add_topic`, `remove_alias`, `override_weight`, `replace_aliases`, `replace_refs`, `replace_queries`), this is a TopicKey (e.g., `"hooks.pre_tool_use"`); for `add_deny_rule`, this is the `deny_rule.id` value of the embedded DenyRule; for `override_config`, this is a dot-delimited config key path (e.g., `"classifier.confidence_high_min_weight"`). For `operation: override_config` entries, `target` is a dot-delimited config key path matching a leaf scalar in `ccdi_config.json` (e.g., `classifier.confidence_high_min_weight`). |

## Overlay Merge Semantics

- Scalar fields in `TopicRecord`: replace scaffold values.
- `aliases`, `canonical_refs`, `query_plan.facets[*]`: append + dedupe by normalized value, unless `replace_*` is explicitly set in the overlay rule.
- Overlay can: add topics, remove aliases, add deny rules, override weights, replace aliases, replace refs, replace queries.
- `remove_alias` on a known topic with unknown `alias_text`: warning, rule skipped (no-op). Stale remove rules are expected as the scaffold evolves.
- `replace_aliases(topic_key, aliases[])`: Atomically replaces the entire `aliases` array on the target topic. If `topic_key` does not exist in the inventory: warning logged, rule skipped.
- `replace_refs(topic_key, canonical_refs[])`: Atomically replaces the entire `canonical_refs` array. Same unknown-topic behavior.
- `replace_queries(topic_key, query_plan)`: Atomically replaces the entire `query_plan` object. Same unknown-topic behavior.
- Generated scaffold builds the bulk. Overlay only fixes ambiguity and adds missing synonyms.

**Post-merge alias validation:** After applying all overlay operations, `build_inventory.py` MUST validate that every TopicRecord has at least one alias. On violation: reject the overlay build with non-zero exit and identify the zero-alias topic(s).

### Overlay File Format

The overlay file (`topic_overlay.json`) is a JSON object with these root keys:

```json
{
  "overlay_version": "1",
  "overlay_schema_version": "1",
  "rules": [
    {
      "rule_id": "add-tool-inputs-alias",
      "operation": "remove_alias",
      "topic_key": "hooks.pre_tool_use",
      "alias_text": "tool inputs"
    },
    {
      "rule_id": "boost-pretooluse",
      "operation": "override_weight",
      "topic_key": "hooks.pre_tool_use",
      "alias_text": "tool inputs",
      "weight": 0.5
    },
    {
      "rule_id": "add-custom-topic",
      "operation": "add_topic",
      "topic_key": "hooks.user_prompt_submit",
      "topic_record": { "...": "full TopicRecord" }
    }
  ],
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9
  }
}
```

| Root key | Type | Required | Purpose |
|----------|------|----------|---------|
| `overlay_version` | string | Yes | Instance version — monotonically incremented by curator on each edit |
| `overlay_schema_version` | string | Yes | Format version — validated against `build_inventory.py`'s supported range |
| `rules` | `OverlayRule[]` | Yes | Ordered list of overlay operations |
| `config_overrides` | `Record<string, scalar>` | No | See [Config Overrides in Overlay](#config-overrides-in-overlay) |

**OverlayRule fields by operation:**

| Operation | Required fields | Optional fields |
|-----------|----------------|-----------------|
| `add_topic` | `rule_id`, `operation`, `topic_key`, `topic_record` (MUST include all TopicRecord fields: `topic_key`, `family_key`, `kind`, `canonical_label`, `category_hint`, `parent_topic`, `aliases` (non-empty), `query_plan` (MUST include `default_facet` — a QueryPlan without `default_facet` makes the topic unsearchable), `canonical_refs`). On violation (empty `aliases` array): reject the overlay rule with descriptive error. On violation (`query_plan` missing `default_facet`): reject the overlay rule with descriptive error. | — |
| `remove_alias` | `rule_id`, `operation`, `topic_key`, `alias_text` | — |
| `add_deny_rule` | `rule_id`, `operation`, `deny_rule` (DenyRule object — the embedded `deny_rule.id` is the DenyRule's identity in the compiled denylist; `rule_id` is the overlay rule's identity in `applied_rules[]`. These are independent identifiers — `rule_id` tracks provenance, `deny_rule.id` is the operational identifier used by the classifier. **Uniqueness constraint:** `deny_rule.id` MUST be unique across all `add_deny_rule` operations in the overlay. On duplicate `deny_rule.id`: reject the overlay with non-zero exit and descriptive error identifying both rules.) | — |
| `override_weight` | `rule_id`, `operation`, `topic_key`, `alias_text`, `weight` (0.0–1.0; out-of-bounds values are clamped with warning) | — |
| `replace_aliases` | `rule_id`, `operation`, `topic_key`, `aliases` (Alias[] — MUST include at least one element. On violation (empty `aliases` array): reject the overlay rule with descriptive error.) | — |
| `replace_refs` | `rule_id`, `operation`, `topic_key`, `canonical_refs` (DocRef[]) | — |
| `replace_queries` | `rule_id`, `operation`, `topic_key`, `query_plan` (QueryPlan — MUST include `default_facet`; a QueryPlan without `default_facet` makes the topic unsearchable. On violation: reject the overlay rule with descriptive error.) | — |
| `override_config` | Expressed via `config_overrides` root key, not as a rule entry | — |

`override_config` is not expressed as an `OverlayRule`. It uses the separate `config_overrides` root key. `build_inventory.py` records each applied config override as an `AppliedRule` with `operation: "override_config"` — see [Config Overrides in Overlay](#config-overrides-in-overlay).

## RegistrySeed

Schema for the registry seed emitted by `ccdi-gatherer` and consumed by `codex-dialogue` via the [registry seed handoff](integration.md#registry-seed-handoff).

```
RegistrySeed
├── entries: TopicRegistryEntry[]   # durable-state fields only
├── docs_epoch: string | null       # docs_epoch from the inventory at build time
├── inventory_snapshot_version: string  # schema_version from the active inventory. If the inventory fails to load at seed-build time, `ccdi-gatherer` MUST NOT emit a `<!-- ccdi-registry-seed -->` sentinel block. The sentinel block MUST only be emitted when a valid CompiledInventory was loaded and `inventory_snapshot_version` can be sourced from a real `schema_version` value.
└── results_file?: string | null     # transport-only; never persisted in live file; stripped on load. Path to search results file for initial commit phase; absent when no pre-dialogue search was performed
```

**`results_file` field:** `results_file` is required in the sentinel RegistrySeed when a pre-dialogue search was performed. If absent (no results generated), the initial CCDI commit phase is skipped — no results to commit. When present, the value is an absolute path to the search results JSON file written by `ccdi-gatherer` during the pre-dialogue phase (e.g., `/tmp/ccdi_results_<id>.json`). The `/dialogue` skill reads this path from the sentinel block and passes it to the initial CCDI commit's `build-packet --results-file` call. This is a transport field for the handoff — it is not written to the live registry file and is not used after the initial commit completes. **Load-time invariant:** Implementations MUST strip `results_file` from the in-memory registry representation at load time (no load-time write-back). The stripped state is persisted to disk on the next normal mutation, ensuring the field never appears in the live registry file after a successful write. **Definition:** A "normal mutation" is any CLI operation that successfully writes the registry file to disk: `dialogue-turn` state updates, `--mark-injected` commits, `--mark-deferred` writes, or automatic suppression writes from `build-packet` empty output. Read-only operations (e.g., `classify`) are not mutations. See [registry.md#failure-modes](registry.md#failure-modes) for load-time handling. The `/dialogue` skill reads the field from the transport envelope (sentinel seed) before CLI handoff — the boundary between transport and live registry is the key distinction. Stale paths to deleted temp files would cause failures on subsequent loads if the field were not stripped.

**`entries` field:** Each element contains all durable-state fields from `TopicRegistryEntry` — see [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states) for the authoritative field list (all fields except attempt-local states `looked_up` and `built`). This includes all durable-state fields from `TopicRegistryEntry` as defined in [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states), including the `coverage` sub-object with all of its sub-fields — all durable, all serialized. **Authority split:** data-model.md (persistence_schema authority) owns the RegistrySeed envelope schema (`entries`, `docs_epoch`, `inventory_snapshot_version`, `results_file`). registry.md (registry-contract authority) owns the `TopicRegistryEntry` field set and durable/attempt-local classification within `entries[]`. When the entry field set changes in registry.md, the RegistrySeed envelope schema here does not need updating — only the entry-level fields change. **Conflict resolution:** For `behavior_contract` and `interface_contract` claims about entry-level field semantics (which fields are durable vs attempt-local, what values mean), registry.md is authoritative. For `persistence_schema` claims about serialization format and envelope structure, data-model.md is authoritative per `spec.yaml` → `claim_precedence` → `persistence_schema`. For a complete enumeration of durable fields serialized within `entries[]`, implementers MUST read [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states). `data-model.md` owns the envelope fields only.

`coverage_target` and `facet` are standard durable fields in `TopicRegistryEntry`, populated at `absent → detected` from `ClassifierResult.resolved_topics[]` (see [registry.md#field-update-rules](registry.md#field-update-rules)). They are required at commit time by `build-packet --mark-injected --coverage-target` and `--facet` respectively.

Topics in attempt-local states (`looked_up`, `built`) are not persisted to the seed — these states exist only within a single CLI invocation.

**Seed-build initialization:** At seed-build time, durable-state fields are initialized per the `absent → detected` field update rule in [registry.md#field-update-rules](registry.md#field-update-rules). See the seed-build initialization note in that section for the specific `consecutive_medium_count` baseline rule (which requires both medium confidence AND leaf-kind for initialization to 1).

**State at seed time:** After the [initial CCDI commit](integration.md#data-flow-full-ccdi-dialogue), entries transition to `injected` if the briefing was sent successfully. Before the commit, entries are in `detected` state.

**Initial-mode immutability:** The RegistrySeed is the single source of truth for initial-mode `--facet` values and MUST NOT be mutated between prepare and commit.

**In-place mutation:** The `/dialogue` skill writes the seed to a temp file, which is then updated in-place by the commit-phase `build-packet --mark-injected` call at the same path. After commit, entries at that path reflect `injected` state. See [integration.md#registry-seed-handoff](integration.md#registry-seed-handoff) for the full lifecycle.

**Dialogue scope:** The registry file is dialogue-scoped — a new `/dialogue` session starts from a new RegistrySeed and does not inherit entries from prior dialogues. Durable fields (including `deferred_ttl`) persist only across reloads of the same registry within an ongoing dialogue, including abnormal process interruption. See [registry.md#ttl-lifecycle](registry.md#ttl-lifecycle) for the TTL dialogue-scope clarification.

**Null-field serialization:** All **nullable** durable-state fields are always serialized in JSON including when null (e.g., `last_injected_turn: null`, `last_query_fingerprint: null`, `suppression_reason: null`, `suppressed_docs_epoch: null`, `deferred_reason: null`, `deferred_ttl: null`) — never omitted. Non-nullable fields (`inventory_snapshot_version`) are always present with their concrete values. An absent field is treated as missing on load and triggers entry reinitialization per the [resilience principle](foundations.md#resilience-principle). Implementations MUST NOT omit null-valued fields during serialization. This invariant applies to both entry-level fields within `entries[]` and envelope-level nullable fields (`docs_epoch`) — `docs_epoch: null` MUST be serialized as an explicit null, not omitted.

**Non-nullable always-present fields:** In addition to the nullable fields above, all non-nullable fields in `TopicRegistryEntry` MUST always be present in serialized JSON — absent keys are not valid. This includes `consecutive_medium_count` (integer, always serialized including when `0` — family-kind entries MUST have value `0`), and all `coverage.*` sub-fields: `overview_injected` (boolean), `facets_injected` (array), `pending_facets` (array), `family_context_available` (boolean), `injected_chunk_ids` (array). Empty arrays and `false` values are valid and MUST NOT be omitted. See [registry.md#entry-structure](registry.md#entry-structure) for the authoritative field list.

**Array ordering constraint:** `coverage.pending_facets` MUST be serialized in insertion order (FIFO). JSON serializers MUST NOT sort or reorder this array. The ordering semantics are defined in [registry.md#entry-structure](registry.md#entry-structure); this constraint surfaces the behavioral invariant at the persistence layer.

### Live Registry File Schema

The post-commit live registry file is the RegistrySeed with `results_file` stripped at initial commit. Structure:

| Field | Type | Description |
|-------|------|-------------|
| `entries` | `TopicRegistryEntry[]` | Array of topic entries in durable states (see [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states)) |
| `docs_epoch` | `string \| null` | Hash of the indexed document set at seed creation time; retained for traceability only. This field is NOT read by the CLI at suppression time — `suppressed_docs_epoch` is sourced from the pinned inventory snapshot (via `--inventory-snapshot`), not from this envelope field. See [registry.md#field-update-rules](registry.md#field-update-rules). |
| `inventory_snapshot_version` | `string` | `CompiledInventory.schema_version` captured at seed creation; used for version-mismatch gating at seed load |

`results_file` is stripped on load (load-time invariant) and MUST NOT appear in the live file. `docs_epoch` and `inventory_snapshot_version` are retained as traceability fields and are not modified after initial write. The `docs_epoch` used for suppression re-entry comparisons is sourced from the pinned inventory snapshot (via `--inventory-snapshot`), not from the registry file's envelope field.

**`inventory_snapshot_version` write-time contract:** At seed-build time, `inventory_snapshot_version` MUST equal the `CompiledInventory.schema_version` value from the inventory that was successfully loaded. A sentinel block with a blank, null, or absent `inventory_snapshot_version` indicates a build defect. At seed load, if `inventory_snapshot_version` is empty, null, or absent, treat as a version mismatch (log warning, apply best-effort field mapping per [Failure Modes](#failure-modes)).

**Entry-level null-field serialization:** All nullable durable-state fields within each `entries[]` element MUST be serialized as explicit `null` when null — see [Null-field serialization](#registryseed) above. This invariant applies to both entry-level fields (e.g., `last_query_fingerprint: null`, `deferred_reason: null`) and the envelope-level nullable field (`docs_epoch`).

## Inventory Lifecycle

| Phase | Mechanism | Trigger |
|-------|-----------|---------|
| Generation | Auto-generated from `claude-code-docs` index metadata via `build_inventory.py` (MCP client calling `dump_index_metadata`) | Post-reload hook (when `docs_epoch` changes) or manual (`--force`) |
| Overlay | Small curated JSON with denylist rules, alias fixes, weight overrides | Manual edit |
| Persistence | Compiled to `data/topic_inventory.json` | Build completion |
| Startup load | Loaded from last-known-good artifact (no live MCP dependency at startup) | Plugin init |
| Dialogue pinning | Running dialogue uses inventory snapshot loaded at dialogue start | Dialogue start |

Inventory refreshes mid-dialogue do NOT affect active conversations — the [classifier](classifier.md) operates on a pinned copy for the dialogue lifetime.

## Configuration: `ccdi_config.json`

Tuning parameters live in a separate config file consumed only by the CLI tool. The agent never parses this file — it sees only the CLI's behavioral output.

```json
{
  "config_version": "1",
  "classifier": {
    "confidence_high_min_weight": 0.8,
    "confidence_medium_min_score": 0.5,
    "confidence_medium_min_single_weight": 0.5
  },
  "injection": {
    "initial_threshold_high_count": 1,
    "initial_threshold_medium_same_family_count": 2,
    "mid_turn_consecutive_medium_turns": 2,
    "cooldown_max_new_topics_per_turn": 1,
    "deferred_ttl_turns": 3
  },
  "packets": {
    "initial_token_budget_min": 600,
    "initial_token_budget_max": 1000,
    "initial_max_topics": 3,
    "initial_max_facts": 8,
    "mid_turn_token_budget_min": 250,
    "mid_turn_token_budget_max": 450,
    "mid_turn_max_topics": 1,
    "mid_turn_max_facts": 3,
    "quality_min_result_score": 0.3,
    "quality_min_useful_facts": 1
  }
}
```

`config_version` current supported value: `"1"`. The CLI treats files with an unrecognized `config_version` as unreadable — falls back to built-in defaults and logs a warning (see [Failure Modes](#failure-modes)). The CLI accepts only the single value `'1'` for `config_version`. Any other value is treated as unrecognized.

All keys are optional. If `ccdi_config.json` is absent or a key is missing, the built-in defaults shown above apply. Type for each key is inferred from its default value (numeric keys are `number`; `string` keys are `string`). Config key values MUST NOT be `null` — a key present with a `null` value is treated as invalid (same as out-of-range): use the built-in default for that key and emit a warning.

**Semantic range constraints:** Weight/score thresholds (`confidence_high_min_weight`, `confidence_medium_min_score`, `confidence_medium_min_single_weight`, `quality_min_result_score`) MUST be in `[0.0, 1.0]`. Count/turn thresholds (`initial_threshold_high_count`, `initial_threshold_medium_same_family_count`, `mid_turn_consecutive_medium_turns`, `cooldown_max_new_topics_per_turn`, `deferred_ttl_turns`, `initial_max_topics`, `initial_max_facts`, `mid_turn_max_topics`, `mid_turn_max_facts`, `quality_min_useful_facts`) MUST be positive integers. Token budgets (`*_token_budget_min`, `*_token_budget_max`) MUST be positive integers with `min ≤ max`. Out-of-range values are treated as invalid: the CLI uses the built-in default for that key and emits a warning.

**Config consumer scope:** `initial_threshold_high_count` and `initial_threshold_medium_same_family_count` configure threshold evaluation in the CLI `classify` command only. The agent-side pre-dispatch gate (in `/codex` and `/dialogue` flows) uses a fixed heuristic with hardcoded defaults matching the built-in values shown above. When these keys are overridden via `ccdi_config.json` or overlay `config_overrides`, agent-side gate and CLI threshold outcomes MAY diverge — this divergence is intentional (see [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints)).

**Cross-key validation:** After per-key validation, if `token_budget_min > token_budget_max` for either the initial or mid-turn pair, fall back to defaults for **both** keys in the pair as a unit and log a warning. Do not fall back for each key independently — independent fallback can itself produce `min > max` when only one key was invalid (e.g., valid custom `min` paired with default `max` that is lower). No other cross-key constraints are defined — keys outside the token-budget pairs are validated independently per the semantic range constraints above.

### Config Overrides in Overlay

The overlay file may include an optional `config_overrides` object that overrides default values in `ccdi_config.json`. Merge semantics: **scalar replace only** — `scalar` means `string | number | boolean` (no arrays, objects, or null). The scalar-only constraint for config override values applies to `overlay_schema_version: '1'`. Future versions that permit null MUST introduce a new `overlay_schema_version` and specify null semantics explicitly. Config override values must match the type of the target key in `ccdi_config.json`. Type mismatches (e.g., string where number expected) are treated as unknown keys: warned and skipped. Unknown keys are warned and skipped.

```json
{
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9,
    "packets.initial_max_topics": 2
  }
}
```

Keys use dot-separated paths matching the config schema above (e.g., `classifier.confidence_high_min_weight`). A key is "defined in the schema" when the full dot-path resolves to a leaf scalar in the `ccdi_config.json` structure — exact-match only, no prefix matching. Valid namespace but unknown leaf (e.g., `classifier.nonexistent_key`) is treated as unknown: warned and skipped.

`build_inventory.py` records each applied config override in `overlay_meta.applied_rules[]` with `operation: "override_config"` and `target` set to the config key path. `build_inventory.py` MUST process `config_overrides` using strict JSON parsing that rejects duplicate keys, or detect duplicates after parsing and reject with non-zero exit.

**Processing order:** `rules[]` operations are applied first, then `config_overrides`. These keys modify independent build artifacts (`rules[]` modifies the compiled inventory topics/denylist, `config_overrides` modifies the config output written alongside the inventory) and do not interact within a single build run.

**Config consumers:** Parameters are referenced by:
- CLI config loader — `config_version` (version mismatch gating; see [Failure Modes](#failure-modes))
- [classifier.md](classifier.md#confidence-levels) — `classifier.*` keys (confidence thresholds)
- [classifier.md](classifier.md#injection-thresholds) — `injection.initial_threshold_*` keys (initial injection thresholds)
- [registry.md](registry.md#scheduling-rules) — `injection.cooldown_max_new_topics_per_turn`, `injection.deferred_ttl_turns`, and `injection.mid_turn_consecutive_medium_turns`
- [packets.md](packets.md#token-budgets) — `packets.*` keys (token budgets, quality thresholds)

Changes to config keys require checking all consumer files.

**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. For behavioral meaning of each parameter, see the consumer file listed in the config consumers table above. See `spec.yaml` → `claim_precedence` for resolution order when consumer files conflict.

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `topic_inventory.json` missing or corrupt | CLI non-zero exit / parse error | Skip CCDI, log warning |
| `ccdi_config.json` missing | CLI fallback | Use built-in defaults, log info |
| `ccdi_config.json` corrupt or invalid | CLI parse error | Use built-in defaults, log warning |
| `ccdi_config.json` version mismatch (`config_version` differs from CLI's supported version) | CLI version check | Use built-in defaults, log warning (same behavior as corrupt/invalid — version-mismatched config is treated as unreadable) |
| `CompiledInventory.schema_version` does not match CLI's expected version | CLI string comparison at startup | Log warning and proceed with best-effort field mapping. Fields absent in the loaded version use schema defaults. Fields present but unrecognized are preserved on write-back. Fail-open: stale inventory is better than no inventory. **Rationale for asymmetry with build-time fail-loud:** Build-time validation (overlay merge) rejects version mismatches because the curator can fix them before publishing. Load-time validation accepts mismatches because the compiled inventory is a pre-built artifact the CLI cannot fix at runtime — and `CompiledInventory` schema evolution is additive-only (new fields with defaults, never removed or renamed fields). This additive-only invariant is what makes best-effort field mapping safe. |
| Inventory stale (`docs_epoch` mismatch) | Diagnostic check | Use stale inventory with diagnostics warning |
| Version axis mismatch at build time | `build_inventory.py` validation | Fail loudly with version pair and required action |
| `RegistrySeed.inventory_snapshot_version` differs from current inventory `schema_version` | CLI string comparison at seed load | Version mismatch is a valid load-time state. Log warning and continue — `topic_key` values are stable across patch versions. Field is used for traceability and forward-compatibility gating. See [registry.md#failure-modes](registry.md#failure-modes) for entry-level handling and rewrite-deferral behavior. |
| `merge_semantics_version` absent in loaded inventory | CLI field validation | Log warning, assume version `"1"` (initial version), proceed with best-effort merge. Consistent with `schema_version` mismatch treatment. |
| `merge_semantics_version` mismatch at load time | CLI string comparison at startup | Log warning, proceed with best-effort field mapping. Distinct from build-time mismatch (which fails loudly per version-axis validation). |
| `topic_inventory.json` valid JSON but missing `overlay_meta` field | CLI field validation | Treat as partial inventory: log warning, use empty `applied_rules[]` and omit config overrides, continue CCDI. This is not "corrupt" — the inventory is usable without overlay metadata. |
| Registry file loaded with `deferred_ttl: 0` (abnormal shutdown during TTL processing) | CLI load-time check | A value of 0 is a valid persisted state indicating TTL expired before transition was written. See [registry.md#failure-modes](registry.md#failure-modes) for recovery behavior (state transition on next `dialogue-turn` call). |
| Registry file loaded with `results_file` field present | CLI load-time check | `results_file` is a transient field not intended for long-term persistence; its presence at load time indicates an incomplete initial commit. See [registry.md#failure-modes](registry.md#failure-modes) for load-time handling (strip and write-back behavior). |

All failure modes degrade gracefully — consultations are never blocked per the [resilience principle](foundations.md#resilience-principle). Degradation ranges from session-level CCDI disable (inventory missing) to continued operation with built-in defaults or stale data — see individual rows above.
