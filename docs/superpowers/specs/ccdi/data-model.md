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
| `match_type` | `"token" \| "phrase" \| "regex"` | How to match |
| `action` | `"drop" \| "downrank"` | Eliminate or penalize |
| `penalty` | number \| null | Weight reduction for `downrank`; null or omit for `drop` (penalty is not applied when action is `drop`) |
| `reason` | string | Why this term is problematic |

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

| Field | Type | Purpose |
|-------|------|---------|
| `rule_id` | string | Overlay rule identifier |
| `operation` | `"add_topic" \| "remove_alias" \| "add_deny_rule" \| "override_weight" \| "replace_aliases" \| "replace_refs" \| "replace_queries"` | What the rule did |
| `target` | string | TopicKey or alias text affected |

## Overlay Merge Semantics

- Scalar fields in `TopicRecord`: replace scaffold values.
- `aliases`, `canonical_refs`, `query_plan.facets[*]`: append + dedupe by normalized value, unless `replace_*` is explicitly set in the overlay rule.
- Overlay can: add topics, remove aliases, add deny rules, override weights.
- Generated scaffold builds the bulk. Overlay only fixes ambiguity and adds missing synonyms.

## RegistrySeed

Schema for the registry seed emitted by `ccdi-gatherer` and consumed by `codex-dialogue` via the [registry seed handoff](integration.md#registry-seed-handoff).

```
RegistrySeed
├── entries: TopicRegistryEntry[]   # durable-state fields only
├── docs_epoch: string | null       # docs_epoch from the inventory at build time
└── inventory_snapshot_version: string  # schema_version from the active inventory
```

**`entries` field:** Each element is a `TopicRegistryEntry` (see [registry.md#entry-structure](registry.md#entry-structure)) containing only durable-state fields (`topic_key`, `family_key`, `state`, `first_seen_turn`, `last_seen_turn`, `last_injected_turn`, `last_query_fingerprint`, `consecutive_medium_count`, `suppression_reason`, `deferred_reason`, `deferred_ttl`, `coverage`). Attempt-local fields (`looked_up`, `built`) are never included.

**State at seed time:** After the [initial CCDI commit](integration.md#data-flow-full-ccdi-dialogue), entries transition to `injected` if the briefing was sent successfully. Before the commit, entries are in `detected` state.

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

The overlay file may include an optional `config_overrides` object that overrides default values in `ccdi_config.json`. Merge semantics: **scalar replace only** (config values are flat scalars, not arrays or nested objects). Unknown keys are warned and skipped.

```json
{
  "config_overrides": {
    "classifier.confidence_high_min_weight": 0.9,
    "packets.initial_max_topics": 2
  }
}
```

Keys use dot-separated paths matching the config schema above (e.g., `classifier.confidence_high_min_weight`). Only keys defined in the `ccdi_config.json` schema are valid override targets.

`build_inventory.py` records each applied config override in `overlay_meta.applied_rules[]` with `operation: "override_config"` and `target` set to the config key path.

**Config consumers:** Parameters are referenced by:
- [classifier.md](classifier.md#confidence-levels) — `classifier.*` keys (confidence thresholds) and `injection.*` keys (injection thresholds)
- [registry.md](registry.md#scheduling-rules) — `injection.cooldown_max_new_topics_per_turn`, `injection.deferred_ttl_turns`, and `injection.mid_turn_consecutive_medium_turns`
- [packets.md](packets.md#token-budgets) — `packets.*` keys (token budgets, quality thresholds)

Changes to config keys require checking all consumer files.

**Authority scope:** This section is normative for the config file's **schema** (field names, types, default values) under the `persistence_schema` claim. The **behavioral meaning** of each parameter is authoritative in its consumer file (classifier-contract, registry-contract, or packet-contract). For precedence between config schema and behavioral contracts, see `spec.yaml` → `claim_precedence`.

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `topic_inventory.json` missing or corrupt | CLI non-zero exit / parse error | Skip CCDI, log warning |
| `ccdi_config.json` missing | CLI fallback | Use built-in defaults, log info |
| `ccdi_config.json` corrupt or invalid | CLI parse error | Use built-in defaults, log warning |
| Inventory stale (`docs_epoch` mismatch) | Diagnostic check | Use stale inventory with diagnostics warning |
| Version axis mismatch at build time | `build_inventory.py` validation | Fail loudly with version pair and required action |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
