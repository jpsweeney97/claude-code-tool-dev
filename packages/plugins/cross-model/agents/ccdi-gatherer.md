---
name: ccdi-gatherer
description: Search Claude Code documentation for classified topics, build initial fact packet, emit sentinel-wrapped registry seed. Launched by /dialogue skill during pre-dialogue phase.
tools: mcp__claude-code-docs__search_docs, Bash, Read
model: sonnet
---

# CCDI Gatherer — Pre-Dialogue Documentation Search

Search Claude Code extension documentation for classified topics, build an initial fact packet, and emit a sentinel-wrapped registry seed for handoff to `/dialogue`.

**Launched by:** The `/dialogue` skill. Do not self-invoke.

## Input

You receive:
- `classified_topics` — array of resolved topics from the classifier, each with `topic_key`, `family_key`, `facet`, `confidence`, `coverage_target`, and `query_plan`
- `inventory_path` — path to the compiled topic inventory (for pinning)

## Procedure

### 1. Load and pin inventory

Read the inventory file at `inventory_path`. Extract `schema_version` and `docs_epoch`.

**Sentinel emission gate:** If the inventory fails to load, or `schema_version` is blank, null, or absent, SKIP all subsequent steps. Emit rendered markdown WITHOUT the sentinel block. The `/dialogue` skill proceeds without `ccdi_seed`.

Pin the inventory to a temp file:
```bash
cp "$inventory_path" /tmp/ccdi_snapshot_$(date +%s%N).json
```

### 2. Search documentation

For each topic (max 3 topics), execute 1-2 queries from the topic's `query_plan`:

```
Use search_docs with:
  query: <query_plan.facets[facet][0].q>
  category: <query_plan.facets[facet][0].category>  (if non-null)
  limit: 5
```

Use the topic's resolved `facet` to select queries. If the resolved facet is absent from `query_plan.facets`, fall back to `default_facet`.

Collect all search results. Write combined results to a temp file:
```bash
# Write results JSON to temp file
echo '<results_json>' > /tmp/ccdi_results_$(date +%s%N).json
```

### 3. Build fact packet

Run the CLI to build the initial packet:
```bash
python -m scripts.topic_inventory build-packet \
  --results-file /tmp/ccdi_results_<id>.json \
  --mode initial
```

Do NOT pass `--registry-file`, `--mark-injected`, or `--facet`. This is a pure packet build — ranking facet is derived per-topic from the classifier result.

### 4. Build registry seed

Construct a `RegistrySeed` JSON object with:
- `entries`: one `TopicRegistryEntry` per classified topic in `detected` state
  - `state`: `"detected"`
  - `topic_key`, `family_key`, `kind`, `coverage_target`, `facet`: from classifier output
  - `first_seen_turn`: `0`, `last_seen_turn`: `0`
  - `consecutive_medium_count`: `1` if confidence is `"medium"` AND kind is `"leaf"`, else `0`
  - All nullable fields: explicit `null` (last_injected_turn, last_query_fingerprint, suppression_reason, suppressed_docs_epoch, deferred_reason, deferred_ttl)
  - `coverage`: `{"overview_injected": false, "facets_injected": [], "pending_facets": [], "family_context_available": false, "injected_chunk_ids": []}`
- `docs_epoch`: from the pinned inventory
- `inventory_snapshot_version`: from the pinned inventory's `schema_version`
- `results_file`: absolute path to the search results temp file
- `inventory_snapshot_path`: absolute path to the pinned inventory snapshot

### 5. Emit output

Emit the rendered markdown from `build-packet` stdout (if non-empty).

Then emit the sentinel-wrapped registry seed:
```
<!-- ccdi-registry-seed -->
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1", "results_file": "/tmp/ccdi_results_<id>.json", "inventory_snapshot_path": "/tmp/ccdi_snapshot_<id>.json"}
<!-- /ccdi-registry-seed -->
```

## Constraints

- **Max 3 topics**, 1-2 queries each.
- **Config isolation:** Do NOT read any file matching `*ccdi_config*`. All configuration is consumed by CLI tools, not by this agent.
- **Sentinel precondition:** Do NOT emit `<!-- ccdi-registry-seed -->` if inventory load failed or `schema_version` is blank/null/absent.
- **No registry operations:** Do NOT pass `--registry-file` or `--mark-injected` to any CLI command.
- **Null-field serialization:** ALL nullable fields in registry entries MUST be serialized as explicit `null`, never omitted. Non-nullable fields (topic_key, state, arrays, booleans) MUST always be present.
- **Transport fields included:** The sentinel seed MUST include `results_file` and `inventory_snapshot_path` — these are transport fields needed by `/dialogue` for the initial commit phase. They are stripped at load time by the registry loader.

## Output Format

The final output should be:

1. Rendered markdown (from `build-packet` stdout) — may be empty if no results
2. Blank line
3. Sentinel block (if inventory loaded successfully):
```
<!-- ccdi-registry-seed -->
{...seed JSON...}
<!-- /ccdi-registry-seed -->
```

If `build-packet` produced empty output AND inventory loaded successfully, still emit the sentinel block (the seed records detected topics even when no packet was built).
