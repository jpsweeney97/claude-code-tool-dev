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
├── schema_version: "1"
├── built_at: ISO timestamp
├── docs_epoch: string | null        # reload/version marker from claude-code-docs
├── topics: Record<TopicKey, TopicRecord>
├── denylist: DenyRule[]
├── overlay_meta: { overlay_version, overlay_schema_version, applied_rules: AppliedRule[] }
└── merge_semantics_version: "1"     # version of the overlay merge algorithm
```

## Version Axes

Four version axes prevent coupled evolution (three compatibility axes + one instance version):

| Axis | Field | What changes | Who changes it |
|------|-------|-------------|---------------|
| Inventory schema | `schema_version` | TopicRecord fields, Alias structure, DenyRule shape | Code change (Python) |
| Overlay schema | `overlay_meta.overlay_schema_version` | Overlay file format, supported operations | Code change (Python) |
| Merge semantics | `merge_semantics_version` | How overlay operations apply to inventory | Code change (Python) |
| Overlay instance | `overlay_meta.overlay_version` | Which version of the curated overlay file was applied | Manual edit (human) |

`overlay_version` is an **instance version** (which edit of the overlay file), not a **compatibility axis** (whether the overlay format is readable). It is monotonically incremented by the overlay curator on each manual edit. `build_inventory.py` records it in `overlay_meta` for traceability but does not validate compatibility — that is the job of `overlay_schema_version`.

`build_inventory.py` validates compatibility between all three axes at merge time. On mismatch: fail loudly with specific version pair and required action. Do NOT silently fall back — overlays are curated artifacts, and silent incompatibility corrupts human-maintained data.

## TopicRecord

| Field | Type | Purpose |
|-------|------|---------|
| `topic_key` | string | Hierarchical key, e.g., `hooks.pre_tool_use` |
| `family_key` | string | Parent family, e.g., `hooks` |
| `kind` | `"family" \| "leaf"` | Family = category, leaf = specific concept |
| `canonical_label` | string | Display name, e.g., `"PreToolUse"` |
| `category_hint` | string | Maps to `claude-code-docs` category filter |
| `parent_topic` | TopicKey \| null | null for families |
| `aliases` | Alias[] | All terms that refer to this topic |
| `query_plan` | QueryPlan | Pre-computed search queries per facet |
| `canonical_refs` | DocRef[] | Known chunk IDs for diagnostics/packet building |

## Alias

| Field | Type | Purpose |
|-------|------|---------|
| `text` | string | e.g., `"PreToolUse"`, `"updatedInput"` |
| `match_type` | `"exact" \| "phrase" \| "token" \| "regex"` | How to match against input |
| `weight` | 0.0–1.0 | Classification strength |
| `facet_hint` | Facet \| null | Which aspect this alias implies |
| `source` | `"generated" \| "overlay"` | Provenance |

Do NOT collapse Alias to plain strings — alias-level weights and facet hints are where the semantic power lives.

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

**Penalty range enforcement:** Out-of-bounds `penalty` values (<= 0.0 or > 1.0) in `add_deny_rule` overlay operations are build-time errors — `build_inventory.py` fails loudly with the penalty value and valid range. This includes `penalty: 0`, which is a build-time error (not a warning) because a zero-penalty downrank is a no-op that almost certainly indicates a curator mistake. Do NOT clamp silently (unlike `override_weight` which clamps with a warning), because deny rules are curated artifacts where silent modification is misleading.

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

**Dual-source note:** Most `applied_rules[]` entries correspond to items in the overlay's `rules[]` array. The exception is `operation: "override_config"` — these entries originate from the `config_overrides` root key, not from `rules[]`. Code reading `applied_rules[]` must handle this: there is no corresponding `OverlayRule` in `rules[]` for config override entries.

| Field | Type | Purpose |
|-------|------|---------|
| `rule_id` | string | Overlay rule identifier (for `override_config`: a synthetic ID based on the config key) |
| `operation` | `"add_topic" \| "remove_alias" \| "add_deny_rule" \| "override_weight" \| "replace_aliases" \| "replace_refs" \| "replace_queries" \| "override_config"` | What the rule did |
| `target` | string | TopicKey or alias text affected; for `override_config`, the dot-separated config key path (e.g., `classifier.confidence_high_min_weight`) |

## Overlay Merge Semantics

- Scalar fields in `TopicRecord`: replace scaffold values.
- `aliases`, `canonical_refs`, `query_plan.facets[*]`: append + dedupe by normalized value, unless `replace_*` is explicitly set in the overlay rule.
- Overlay can: add topics, remove aliases, add deny rules, override weights.
- `remove_alias` on a known topic with unknown `alias_text`: warning, rule skipped (no-op). Stale remove rules are expected as the scaffold evolves.
- Generated scaffold builds the bulk. Overlay only fixes ambiguity and adds missing synonyms.

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
| `add_topic` | `rule_id`, `operation`, `topic_key`, `topic_record` | — |
| `remove_alias` | `rule_id`, `operation`, `topic_key`, `alias_text` | — |
| `add_deny_rule` | `rule_id`, `operation`, `deny_rule` (DenyRule object) | — |
| `override_weight` | `rule_id`, `operation`, `topic_key`, `alias_text`, `weight` (0.0–1.0; out-of-bounds values are clamped with warning) | — |
| `replace_aliases` | `rule_id`, `operation`, `topic_key`, `aliases` (Alias[]) | — |
| `replace_refs` | `rule_id`, `operation`, `topic_key`, `canonical_refs` (DocRef[]) | — |
| `replace_queries` | `rule_id`, `operation`, `topic_key`, `query_plan` (QueryPlan) | — |
| `override_config` | Expressed via `config_overrides` root key, not as a rule entry | — |

`override_config` is not expressed as an `OverlayRule`. It uses the separate `config_overrides` root key. `build_inventory.py` records each applied config override as an `AppliedRule` with `operation: "override_config"` — see [Config Overrides in Overlay](#config-overrides-in-overlay).

## RegistrySeed

Schema for the registry seed emitted by `ccdi-gatherer` and consumed by `codex-dialogue` via the [registry seed handoff](integration.md#registry-seed-handoff).

```
RegistrySeed
├── entries: TopicRegistryEntry[]   # durable-state fields only
├── docs_epoch: string | null       # docs_epoch from the inventory at build time
├── inventory_snapshot_version: string  # schema_version from the active inventory
└── results_file: string            # path to search results file for initial commit phase
```

**`results_file` field:** Absolute path to the search results JSON file written by `ccdi-gatherer` during the pre-dialogue phase (e.g., `/tmp/ccdi_results_<id>.json`). The `/dialogue` skill reads this path from the sentinel block and passes it to the initial CCDI commit's `build-packet --results-file` call. This is a transport field for the handoff — it is not written to the live registry file and is not used after the initial commit completes. Implementations MUST strip `results_file` from the JSON before writing the file back during in-place mutation (e.g., `--mark-injected`). The field is read once at initial commit time and MUST NOT appear in the persisted registry file after the first write — stale paths to deleted temp files would cause failures on subsequent loads.

**`entries` field:** Each element contains all durable-state fields from `TopicRegistryEntry` — see [registry.md#durable-vs-attempt-local-states](registry.md#durable-vs-attempt-local-states) for the authoritative field list (all fields except attempt-local states `looked_up` and `built`). registry.md is the single source of truth for which fields are durable; this section covers the RegistrySeed envelope schema (`entries`, `docs_epoch`, `inventory_snapshot_version`, `results_file`), not the entry field set.

`coverage_target` and `facet` are standard durable fields in `TopicRegistryEntry`, populated at `absent → detected` from `ClassifierResult.resolved_topics[]` (see [registry.md#field-update-rules](registry.md#field-update-rules)). They are required at commit time by `build-packet --mark-injected --coverage-target` and `--facet` respectively.

Topics in attempt-local states (`looked_up`, `built`) are not persisted to the seed — these states exist only within a single CLI invocation.

**Seed-build initialization:** At seed-build time, durable-state fields are initialized per the `absent → detected` field update rule in [registry.md#field-update-rules](registry.md#field-update-rules). See the seed-build initialization note in that section for the specific `consecutive_medium_count` baseline rule.

**State at seed time:** After the [initial CCDI commit](integration.md#data-flow-full-ccdi-dialogue), entries transition to `injected` if the briefing was sent successfully. Before the commit, entries are in `detected` state.

**In-place mutation:** The `/dialogue` skill writes the seed to a temp file, which is then updated in-place by the commit-phase `build-packet --mark-injected` call at the same path. After commit, entries at that path reflect `injected` state. See [integration.md#registry-seed-handoff](integration.md#registry-seed-handoff) for the full lifecycle.

**Null-field serialization:** All durable-state fields are always serialized in JSON, including those with null values (e.g., `last_query_fingerprint: null`, `deferred_reason: null`). An absent field is treated as missing on load and triggers entry reinitialization per the [resilience principle](foundations.md#resilience-principle). Implementations MUST NOT omit null-valued fields during serialization.

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

### Config Overrides in Overlay

The overlay file may include an optional `config_overrides` object that overrides default values in `ccdi_config.json`. Merge semantics: **scalar replace only** — `scalar` means `string | number | boolean` (no arrays, objects, or null). Config override values must match the type of the target key in `ccdi_config.json`. Type mismatches (e.g., string where number expected) are treated as unknown keys: warned and skipped. Unknown keys are warned and skipped.

```json
{
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9,
    "packets.initial_max_topics": 2
  }
}
```

Keys use dot-separated paths matching the config schema above (e.g., `classifier.confidence_high_min_weight`). A key is "defined in the schema" when the full dot-path resolves to a leaf scalar in the `ccdi_config.json` structure — exact-match only, no prefix matching. Valid namespace but unknown leaf (e.g., `classifier.nonexistent_key`) is treated as unknown: warned and skipped.

`build_inventory.py` records each applied config override in `overlay_meta.applied_rules[]` with `operation: "override_config"` and `target` set to the config key path.

**Config consumers:** Parameters are referenced by:
- CLI config loader — `config_version` (version mismatch gating; see [Failure Modes](#failure-modes))
- [classifier.md](classifier.md#confidence-levels) — `classifier.*` keys (confidence thresholds)
- [classifier.md](classifier.md#injection-thresholds) — `injection.initial_threshold_*` and `injection.initial_threshold_medium_same_family_count` keys (initial injection thresholds)
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
| Inventory stale (`docs_epoch` mismatch) | Diagnostic check | Use stale inventory with diagnostics warning |
| Version axis mismatch at build time | `build_inventory.py` validation | Fail loudly with version pair and required action |
| `RegistrySeed.inventory_snapshot_version` differs from current inventory `schema_version` | CLI string comparison at seed load | Log warning. Continue with seed — `topic_key` values are stable across patch versions. Discard entries for `topic_key` values not present in the current inventory and continue. Discarded entries are removed in-memory only — the registry file is NOT rewritten at load time due to version mismatch. Rewriting is deferred to the next normal `--mark-injected` or `--mark-deferred` mutation, at which point the file reflects only the retained entries. Field is used for traceability and forward-compatibility gating, not behavioral decisions. |
| `topic_inventory.json` valid JSON but missing `overlay_meta` field | CLI field validation | Treat as partial inventory: log warning, use empty `applied_rules[]` and omit config overrides, continue CCDI. This is not "corrupt" — the inventory is usable without overlay metadata. |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
