---
module: integration
status: active
normative: true
authority: integration
---

# CCDI Integration Architecture

## CLI Tool: `topic_inventory.py`

All deterministic logic lives in Python, exposed as coarse-grained workflow commands. Agents invoke via Bash with file-oriented I/O.

| Command | Input | Output | Used by |
|---------|-------|--------|---------|
| `classify --text-file <path> [--inventory <path>] [--config <path>]` | Text file | `ClassifierResult` JSON (stdout) | Both modes |
| `dialogue-turn --registry-file <path> --text-file <path> --source codex\|user --inventory-snapshot <path>‡ [--semantic-hints-file <path>] [--config <path>] [--shadow-mode]` | Text file + registry + inventory snapshot + optional hints (hints file schema: see [registry.md#semantic-hints](registry.md#semantic-hints)) | Updated registry file + injection candidates JSON (stdout) | Full CCDI |
| `build-packet [--results-file <path>] [--registry-file <path>] --mode initial\|mid_turn [--topic-key <key>] [--facet <facet>]† [--coverage-target family\|leaf] [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--inventory-snapshot <path>] [--config <path>]` | Search results + optional registry + optional inventory snapshot | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |

†`--facet` is required when `--mark-injected` is passed with `--registry-file`.

‡`--inventory-snapshot` is required when `--registry-file` is present (full-CCDI mode). When absent on a full-CCDI call: non-zero exit with descriptive error. Not required in CCDI-lite mode. Note: `classify` uses `--inventory` (same purpose — path to inventory file) while `dialogue-turn` and `build-packet` use `--inventory-snapshot`. The naming difference is intentional: `--inventory-snapshot` signals the pinned copy; `--inventory` on `classify` is a general override. `--inventory-snapshot` is required on `dialogue-turn` when `--registry-file` is present. On `build-packet`, `--inventory-snapshot` is required when `--registry-file` is present (symmetric with `dialogue-turn` requirement). When `--registry-file` is absent (CCDI-lite), `--inventory-snapshot` is optional.

**`--shadow-mode` flag:** Suppresses cooldown deferral writes. When set, `candidate_type: 'new'` entries excluded by the per-turn cooldown limit remain in `detected` state (no `deferred: cooldown` write). Passed by `codex-dialogue` when `graduation.json` `status` is not `'approved'`. The flag name `--shadow-mode` MUST match the flag name accepted by the CLI tool — see the [`topic_inventory.py` CLI table](#cli-tool-topic_inventorypy) above. Implementations MUST NOT use `--shadow_mode` (underscore) or any other variant.

**`--shadow-mode` flag scope:** `--shadow-mode` on `build-packet` affects ONLY registry write operations (`--mark-deferred` becomes a no-op). Packet construction is unaffected by `--shadow-mode` alone — use `--skip-build` to skip construction. The two flags are orthogonal: `--shadow-mode` guards registry writes; `--skip-build` guards packet construction.

All commands accept `--config <path>` to load [`ccdi_config.json`](data-model.md#configuration-ccdiconfigjson). If omitted, uses built-in defaults. The live registry file has the structure defined in [data-model.md#live-registry-file-schema](data-model.md#live-registry-file-schema) — `TopicRegistryEntry` durable states plus `RegistrySeed` envelope fields (`docs_epoch`, `inventory_snapshot_version`); `results_file` is stripped at initial commit. See [registry.md](registry.md#durable-vs-attempt-local-states) for the durable vs attempt-local distinction. Attempt-local states (`looked_up`, `built`) exist within a single CLI invocation and are never written to the file.

**`--registry-file` optionality on `build-packet`:** When omitted (CCDI-lite mode), deduplication against prior injections is skipped and `--mark-injected` / `--mark-deferred` are no-ops. CCDI-lite has no registry — each invocation builds a fresh packet without coverage history.

**`--results-file` conditionality:** Required unless `--skip-build` is passed. Required for packet construction (normal build path). Not required when `--skip-build` is passed with `--mark-deferred` — no packet construction occurs in that path.

**`--topic-key <key>` flag:** Required when `--registry-file` is provided. Identifies which topic's registry entry to update for automatic suppression (on empty output), `--mark-injected`, or `--mark-deferred`. Without `--registry-file` (CCDI-lite mode), `--topic-key` is ignored.

**`--facet <facet>` flag:** Serves two purposes depending on mode:

- **During packet construction:** When provided, directs facet-based ranking in [packets.md build process step 3](packets.md#build-process). When absent (initial mode without `--mark-injected`), the CLI derives the ranking facet per-topic from `ClassifierResult.resolved_topics[].facet` (see [packets.md](packets.md#build-process) for fallback rules).
- **At commit time (`--mark-injected`):** Required when `--mark-injected` is passed with `--registry-file`. Specifies which facet to append to `coverage.facets_injected`.

**Facet consistency (mid-turn mode):** In mid-turn mode, the `facet` value at commit time MUST match the facet used during the prepare phase. On mismatch: non-zero exit with descriptive error including both facet values. The prepare-phase facet is authoritative; commit-phase callers MUST provide the matching value. The prepare `build-packet` output includes a `<!-- ccdi-packet ... facet="..." -->` metadata comment containing the facet actually used for the search. The agent passes `candidate.facet` from `dialogue-turn` candidates JSON (the source of truth for both calls) to `--facet` at both prepare and commit time.

**Facet in initial mode:** The ccdi-gatherer's prepare call omits `--facet` because initial packets cover multiple topics, each with its own classifier-resolved facet. The commit call passes `--facet <entry.facet>` per-topic from the seed file, which records the classifier's resolved facet at seed-build time. Consistency is maintained because both the prepare-phase ranking facet (derived per-topic from the classifier result) and the commit-phase `--facet` (from `RegistrySeed.entries[].facet`) originate from the same source: `ClassifierResult.resolved_topics[].facet`. The commit-phase facet is sourced solely from the `RegistrySeed` entry's `facet` field (populated from `ClassifierResult.resolved_topics[].facet` at seed creation). No cross-check mechanism exists in initial mode — the `RegistrySeed` entry is the ground truth for the commit phase. Initial mode does not require a runtime facet cross-check because both the prepare-phase ranking facet (derived per-topic from the classifier result) and the commit-phase `--facet` (from `RegistrySeed.entries[].facet`) originate from the same source: `ClassifierResult.resolved_topics[].facet`. The RegistrySeed entry is the single source of truth for initial-mode commit. If `entry.facet` is absent from the topic's `QueryPlan.facets` at commit time, `build-packet` falls back to `default_facet` per [packets.md](packets.md#build-process). `entry.facet` is still written to `coverage.facets_injected` for traceability.

**Flag validation order for `build-packet`:** Required-flag presence checks fire first: if `--registry-file` is present but `--inventory-snapshot` is absent, exit non-zero before any other validation. Facet consistency checks (mid-turn mode `--facet` mismatch) fire second. This ordering ensures deterministic error messages and stable test assertions regardless of how many validation failures are present simultaneously.

**`--inventory-snapshot <path>` flag:** Required on all full-CCDI CLI calls (`dialogue-turn` and `build-packet` with `--registry-file`). Points to the pinned `CompiledInventory` snapshot loaded at dialogue start. The CLI reads `CompiledInventory.docs_epoch` from this file as the "current `docs_epoch`" for suppression re-entry comparisons (see [registry.md#suppression-re-entry](registry.md#suppression-re-entry)). Since the inventory is pinned at dialogue start, this value is stable within a dialogue but changes across dialogues when a new inventory is loaded. Not required in CCDI-lite mode (no `--registry-file`).

**`--skip-build` flag:** When passed with `--mark-deferred`, skips packet construction and only writes deferred state to the registry. This avoids redundant rebuilds when the target-match check already determined the packet is not target-relevant. `--skip-build` is only valid with `--mark-deferred`; ignored otherwise. When `--skip-build` is passed with `--mark-deferred`, `--results-file` is not required — no packet construction occurs.

**`--coverage-target family|leaf` flag:** Required when both `--mark-injected` and `--registry-file` are present. When `--registry-file` is absent (CCDI-lite mode), `--coverage-target` is ignored even if passed. Determines whether `coverage.overview_injected` is set (when `family` + facet=overview).

**`--mark-injected` registry side-effects:** When `--mark-injected` is passed with `--registry-file`, the following fields are updated per the [Field Update Rules](registry.md#field-update-rules): `state` → `injected`, `last_injected_turn`, `last_query_fingerprint`, `coverage.injected_chunk_ids` (appended from built packet's chunk IDs), `coverage.facets_injected` (appended), `coverage.pending_facets` (served facet removed if present), `consecutive_medium_count` ← 0. When `--coverage-target family` and `facet=overview`: additionally `coverage.overview_injected` ← true. Additionally, the `results_file` field is absent from the in-memory registry at this point — it was stripped on load (per [data-model.md#registryseed](data-model.md#registryseed)). This write therefore persists the stripped state to disk, which is the observable effect of the load-time invariant.

### `dialogue-turn` Registry Side-Effects

`dialogue-turn` performs the following registry mutations (per the [Field Update Rules](registry.md#field-update-rules)):

- Writes new `detected` entries for newly resolved topics (`absent → detected`).
- Updates `last_seen_turn` for all re-detected entries; increments `consecutive_medium_count` only for **leaf-kind** entries re-detected at medium confidence — family-kind entries leave `consecutive_medium_count` unchanged (per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 4).
- Resets `consecutive_medium_count` to 0 for **non-suppressed** entries absent from classifier output.
- Decrements `deferred_ttl` by 1 for all entries in `deferred` state.
- Transitions `deferred → detected` immediately (bypassing TTL) when a topic in `deferred` state is re-detected at high confidence — clears `deferred_reason` and `deferred_ttl`, makes topic eligible for scheduling in the same call (see [registry.md#scheduling-rules](registry.md#scheduling-rules) step 2).
- Transitions `deferred → detected` when a semantic hint (`prescriptive`, `contradicts_prior`, or `extends_topic`) resolves to a `deferred` topic — clears `deferred_reason` and `deferred_ttl`, applies `deferred → detected` field update rules from [registry.md#field-update-rules](registry.md#field-update-rules), then enters the lookup path from `detected`. This is distinct from the high-confidence bypass above: hint-driven transitions fire regardless of classifier confidence.
- Transitions `deferred → detected` when `deferred_ttl` reaches 0 and topic reappears in classifier output. When `deferred_ttl` reaches 0 and the topic is absent from classifier output: topic remains `deferred` with `deferred_ttl` reset to the configured default (`injection.deferred_ttl_turns`), `deferred_reason` unchanged (see [registry.md#field-update-rules](registry.md#field-update-rules), `deferred → deferred` row).
- For entries in `suppressed` state: re-entry condition check is scoped by `suppression_reason` (per [registry.md#suppression-re-entry](registry.md#suppression-re-entry)). **`weak_results` entries:** `dialogue-turn` scans ALL `suppressed:weak_results` entries each turn for `docs_epoch` change (comparing `suppressed_docs_epoch` against the pinned inventory snapshot's `docs_epoch` from `--inventory-snapshot`), independent of classifier presence. Semantic hint re-entry also applies. **`redundant` entries:** re-entry requires classifier presence (new leaf in same family) or a semantic hint — no full-registry scan. **Semantic hint re-entry (all suppression reasons):** When a semantic hint (`prescriptive`, `contradicts_prior`, or `extends_topic` via `--semantic-hints-file`) resolves to a `suppressed` topic (regardless of `suppression_reason`), transition to `detected` per the `suppressed → detected` re-entry field update rules in [registry.md#field-update-rules](registry.md#field-update-rules): `state` ← `detected`, `suppression_reason` ← null, `suppressed_docs_epoch` ← null, `last_seen_turn` ← current turn, `consecutive_medium_count` ← 0 (topic absent from classifier — no confidence to evaluate). This applies to both `weak_results` and `redundant` reasons. If a re-entry condition is met, transitions to `detected` per the field update rules. If no re-entry condition is met, NO field update occurs — `last_seen_turn` is NOT updated and `consecutive_medium_count` is NOT modified. Re-entry condition check precedes all field update decisions for suppressed entries.
- Emits `facet_expansion` candidates when `extends_topic` hints resolve to `injected` topics with a facet not yet in `facets_injected` (cascade-resolved facet: hint-resolved → `pending_facets[0]` → `default_facet`; see [registry.md#semantic-hints](registry.md#semantic-hints)). Does NOT mutate `coverage.pending_facets` — emits an immediate `facet_expansion` candidate via [registry.md#scheduling-rules](registry.md#scheduling-rules) step 9. (`pending_facets` is only mutated by `contradicts_prior` hints.)
- Emits `pending_facet` candidates when an `injected` topic has non-empty `pending_facets` (from prior `contradicts_prior` hints) and the first pending facet is not yet in `facets_injected`.
- For `candidate_type: 'new'` entries excluded by the per-turn cooldown limit ([registry.md#scheduling-rules](registry.md#scheduling-rules) step 5), writes `deferred: cooldown` state to the registry (same field updates as `detected → deferred` per the [Field Update Rules](registry.md#field-update-rules)). These entries do NOT appear in the candidates JSON output — the cooldown deferral is an internal CLI side-effect.
**Shadow-mode exception:** When `--shadow-mode` is passed, the cooldown deferral write is suppressed — `candidate_type: 'new'` entries excluded by the per-turn cooldown limit remain in `detected` state. A `shadow_defer_intent` trace entry with `reason: "cooldown"` is emitted instead (see [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization)).

**Intra-turn hint ordering:** Hint processing is sequential in array order. `contradicts_prior` mutations to `coverage.pending_facets` are immediately visible to subsequent `extends_topic` cascade resolution within the same `--semantic-hints-file` invocation. Implementations MUST process hints sequentially, not in parallel. *(See registry.md#semantic-hints for the authoritative intra-turn ordering specification.)*

### `build-packet` Automatic Suppression

When `--registry-file` is provided and `build-packet` returns empty output, it automatically writes a suppression state to the registry for the candidate topic. The suppression reason depends on *why* the output is empty:

- `weak_results` — search returned poor results (below quality threshold) or `search_docs` returned empty/error. The search signal is weak.
- `redundant` — search returned useful results but all `chunk_id` values were filtered by deduplication against `injected_chunk_ids`. The topic is already covered.

No flag is needed — empty output triggers suppression unconditionally when a registry is available. See [packets.md#failure-modes](packets.md#failure-modes) for the full decision tree.

**Suppression and deferral precedence:** If `build-packet` returns empty output, automatic suppression (either `weak_results` or `redundant`) writes to the registry. In this case, the target-match check has no packet to evaluate — skip the `--mark-deferred` path entirely. The topic is already handled by suppression. The mid-dialogue flow should check for empty output before proceeding to target-match.

**CCDI-lite empty output:** When `--registry-file` is absent and `build-packet` produces empty output, the command MUST exit 0 with empty stdout and no stderr output. The CCDI-lite path has no suppression side-effect — empty output simply means no packet was built.

#### `dialogue-turn` Candidates JSON Schema

The `dialogue-turn` command writes injection candidates to stdout as a JSON array:

```json
[
  {
    "topic_key": "hooks.pre_tool_use",
    "family_key": "hooks",
    "facet": "schema",
    "confidence": "high",
    "coverage_target": "leaf",
    "candidate_type": "new",
    "query_plan": {"default_facet": "overview", "facets": {"schema": [...]}}
  }
]
```

**Candidate fields:**

| Field | Type | Description |
|-------|------|-------------|
| `topic_key` | `string` | Hierarchical topic key |
| `family_key` | `string` | Parent family key |
| `facet` | `Facet` | Resolved facet for this candidate (see [data-model.md#queryplan](data-model.md#queryplan) for valid values) |
| `confidence` | `"high" \| "medium" \| null` | `null` for `facet_expansion` and `pending_facet` candidates which bypass confidence thresholds. Low-confidence topics are tracked in the registry but excluded from injection candidates (see [classifier.md#injection-thresholds](classifier.md#injection-thresholds)). |
| `coverage_target` | `"family" \| "leaf"` | For `candidate_type: "new"`: sourced from `ClassifierResult.resolved_topics[].coverage_target`. For `facet_expansion` and `pending_facet`: sourced from persisted `TopicRegistryEntry.coverage_target`. |
| `candidate_type` | `"new" \| "facet_expansion" \| "pending_facet"` | How the candidate was scheduled (see table below) |
| `query_plan` | `QueryPlan` | The topic's [QueryPlan](data-model.md#queryplan) from the inventory, for the agent to execute search |

An empty array means no injection candidates this turn.

**`candidate_type` field:** Discriminates how the candidate was scheduled. The agent uses this to distinguish standard injection candidates from hint-driven facet operations on already-injected topics.

| `candidate_type` | Meaning | When emitted |
|------------------|---------|-------------|
| `"new"` | Standard injection candidate (topic not yet `injected`) | Classifier-driven detection or re-detection |
| `"facet_expansion"` | Facet expansion on an `injected` topic | `extends_topic` hint resolved to an injected topic with a facet not yet in `facets_injected` |
| `"pending_facet"` | Pending facet re-injection on an `injected` topic | `contradicts_prior` hint previously appended to `pending_facets`; scheduler selected the first pending facet |

For `facet_expansion` and `pending_facet` candidates, the `facet` field contains the cascade-resolved facet computed by `dialogue-turn` (the facet the agent should pass to `--facet` at both prepare and commit time). The `confidence` field is `null` for these candidate types (confidence is a classifier concept; hint-driven candidates bypass confidence thresholds). The topic's state remains `injected` — these candidates do not change the topic's durable state until `--mark-injected` commits the facet coverage update.

**`--source codex|user` on `dialogue-turn`:** `codex` = classifier runs on Codex's response text; `user` = classifier runs on the user's turn text. Both sources use the same two-stage pipeline and identical scheduling behavior — no source-differentiated rules are currently defined. See [delivery.md#known-open-items](delivery.md#known-open-items) for the deferred divergence item.

### Pipeline Isolation Invariants (subset)

The following invariants are a subset cross-referenced from [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints) and elevated here under `behavior_contract` authority (which outranks `decision_record` for behavioral claims per `spec.yaml` claim_precedence). For the full set of normative decision constraints with behavior implications, see [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints):

- **Scout pipeline isolation:** `execute_scout` and `process_turn` MUST NOT invoke any `topic_inventory.py` command or `search_docs` for CCDI purposes. CCDI search and context-injection search are separate pipelines.
- **Config file isolation:** The agent MUST NOT Read files matching `*ccdi_config*`. All configuration is consumed exclusively by CLI tools via `--config` flag.
- **Sentinel structure invariant:** Registry seed MUST be transmitted as JSON within `<!-- ccdi-registry-seed -->` sentinel tags in `ccdi-gatherer` output, not inline in the delegation envelope. See [§Registry Seed Handoff](#registry-seed-handoff).
- **Shadow-mode commitment prohibition:** See [§Shadow-mode registry invariant](#shadow-mode-registry-invariant) below.
- **Scout-beats-CCDI targeting invariant:** When context-injection has a scout candidate for the current turn, CCDI topic injection MUST defer — scout targets take priority per [foundations.md#design-principles](foundations.md#design-principles). *(Authority layering: the architectural principle (cross-cutting scope) is under `architecture_rule` authority in foundations.md#design-principles. This entry captures the behavioral enforcement contract under `behavior_contract` authority.)*
- **Agent pre-dispatch threshold invariant:** The agent-side pre-dispatch gate (in `/codex` and `/dialogue` flows) uses a fixed heuristic with hardcoded defaults matching the built-in `ccdi_config.json` values. When CLI config keys (`classifier.confidence_high_min_weight`, `injection.cooldown_max_new_topics_per_turn`) are overridden via `ccdi_config.json` or overlay `config_overrides`, agent-side gate outcomes and CLI scheduling outcomes MAY diverge — this divergence is intentional. The agent gate is a coarse pre-filter; the CLI scheduling is authoritative.

## Cross-Plugin Dependency

CCDI depends on `mcp__claude-code-docs__search_docs`. This is an optional dependency.

**Capability detection at preflight:**

1. Check if `search_docs` is available.
2. If available → CCDI enabled.
3. If unavailable + Claude Code topic detected → continue without CCDI, set `ccdi_status: unavailable`, surface note.
4. If unavailable + no Claude Code topic → do nothing.

## New Components

All paths relative to `packages/plugins/cross-model/`.

| Component | Type | Location |
|-----------|------|----------|
| `topic_inventory.py` | CLI tool | `scripts/topic_inventory.py` |
| `topic_inventory.json` | Data artifact | `data/topic_inventory.json` |
| `topic_overlay.json` | Data artifact | `data/topic_overlay.json` |
| `ccdi_config.json` | Config artifact | `data/ccdi_config.json` |
| `build_inventory.py` | Script (MCP client) | `scripts/build_inventory.py` |
| `ccdi-gatherer.md` | Subagent | `agents/ccdi-gatherer.md` |

## Modified Components

| Component | Change |
|-----------|--------|
| `/codex` skill | Add CCDI-lite: classify → search → build-packet → inject into briefing |
| `/dialogue` skill | Add ccdi-gatherer to parallel dispatch; merge output into `## Material` |
| `codex-dialogue` agent | Add per-turn dialogue-turn + build-packet loop; add `search_docs` to `tools:` |
| `claude-code-docs` MCP server | Add `dump_index_metadata` tool for inventory generation |

## Data Flow: CCDI-lite (`/codex`)

```
User prompt
│
├─ /codex skill (Claude)
│  ├─ Write prompt to /tmp/ccdi_text_<id>.txt
│  ├─ Bash: python3 topic_inventory.py classify --text-file /tmp/ccdi_text_<id>.txt
│  ├─ If no topics → proceed without CCDI
│  ├─ Check injection threshold (agent-side fixed heuristic — not affected by `ccdi_config.json` overrides):
│  │   1 high-confidence topic, OR 2+ medium-confidence in same family
│  ├─ If threshold not met → proceed without CCDI (discard low/insufficient topics)
│  ├─ If threshold met:
│  │   ├─ search_docs per topic's query plan (1–2 queries)
│  │   ├─ Write results to /tmp/ccdi_results_<id>.json
│  │   ├─ Bash: python3 topic_inventory.py build-packet \
│  │   │        --results-file /tmp/ccdi_results_<id>.json --mode initial
│  │   └─ Inject rendered markdown into ## Material > ### Claude Code Extension Reference
│  └─ Continue normal /codex briefing assembly
```

## Data Flow: Full CCDI (`/dialogue`)

The shadow mode gate (evaluated at dialogue start) determines whether packets are delivered — see [Shadow Mode Gate](#shadow-mode-gate) below. In **active mode**, packets built by the PREPARE cycle are prepended to follow-up prompts. In **shadow mode**, the PREPARE cycle runs identically but packets are NOT delivered — diagnostics record what CCDI *would have* injected. The graduation protocol, `graduation.json` schema, and kill criteria live under delivery authority (see [delivery.md#graduation-protocol](delivery.md#graduation-protocol)).

### Pre-Dialogue Phase

```
User prompt
│
├─ /dialogue skill (Claude)
│  ├─ Bash: python3 topic_inventory.py classify --text-file <prompt>
│  ├─ If injection threshold met → dispatch ccdi-gatherer in parallel
│  │   (agent-side fixed heuristic: 1 high-confidence OR 2+ medium-confidence
│  │    same family — not affected by `ccdi_config.json` overrides; see
│  │    classifier.md#injection-thresholds for definitions)
│  ├─ If topics below threshold → proceed without CCDI
│  └─ Dispatch context-gatherer-code + context-gatherer-falsifier (as before)
│
├─ ccdi-gatherer (subagent, parallel)
│  ├─ tools: mcp__claude-code-docs__search_docs, Read, Bash
│  ├─ Receives: classified topics + query plans
│  ├─ Calls search_docs per topic (broad: families + sibling topics)
│  ├─ Writes search results to /tmp/ccdi_results_<id>.json
│  ├─ Bash: python3 topic_inventory.py build-packet \
│  │        --results-file /tmp/ccdi_results_<id>.json --mode initial
│  │        (NO --registry-file, NO --mark-injected, NO --facet — pure packet build;
│  │         ranking facet derived per-topic from ClassifierResult.resolved_topics[].facet)
│  └─ Returns: rendered markdown block + sentinel-wrapped registry seed
│             + results file path in sentinel block for commit-phase use
│
├─ Briefing assembly
│  ├─ ## Context
│  ├─ ## Material
│  │   ├─ Repo evidence (@ path:line)  ← from context-gatherers
│  │   └─ Claude Code Extension Reference ([ccdocs:...])  ← from ccdi-gatherer
│  └─ ## Question
│
├─ Send briefing to Codex (via codex tool)
│
├─ Registry seed handoff
│  ├─ /dialogue skill extracts JSON from ccdi-gatherer's sentinel block
│  ├─ Writes registry seed to /tmp/ccdi_registry_<id>.json
│  │   (seed entries contain `coverage_target` and `facet` per entry from classifier)
│  └─ Seed file is now the live registry file for the rest of the dialogue
│
├─ Initial CCDI COMMIT (after briefing send confirmed)
│  ├─ If briefing was sent successfully:
│  │   └─ For each seed entry, read `coverage_target` and `facet` from the seed file:
│  │       Bash: python3 topic_inventory.py build-packet \
│  │              --results-file /tmp/ccdi_results_<id>.json \
│  │              --registry-file /tmp/ccdi_registry_<id>.json \
│  │              --mode initial --topic-key <entry.topic_key> \
│  │              --facet <entry.facet> \
│  │              --coverage-target <entry.coverage_target> \
│  │              --inventory-snapshot <ccdi_inventory_snapshot_path> --mark-injected
│  │       (commit mutates the seed file in-place — entries transition to `injected`)
│  │       Per-topic postconditions (three outcomes):
│  │       1. Exit non-zero: log error, continue with remaining entries — topic
│  │          remains uncommitted (`detected`) and is a candidate for mid-dialogue
│  │          re-injection.
│  │       2. Exit 0 with empty stdout: automatic suppression fired — topic is
│  │          now `suppressed`. Do not log error; this is expected when results
│  │          fall below quality threshold. Continue with remaining entries.
│  │       3. Exit 0 with non-empty stdout: commit succeeded — topic is now
│  │          `injected`.
│  │
│  │       NOTE (CE-8 / D1): This initial commit is NOT subject to the shadow-mode
│  │       gate. Phase A (initial injection) is always active regardless of
│  │       `graduation.json` status. The shadow-mode gate governs only Phase B
│  │       mid-dialogue mutations in `codex-dialogue`. See delivery.md Phase A/B
│  │       risk boundary.
│  └─ If briefing send failed: no commit (seed entries remain `detected`)
│
├─ Pass ccdi_seed envelope field to codex-dialogue delegation
```

### Registry Seed Handoff

The `ccdi-gatherer` subagent emits its [registry seed](data-model.md#registryseed) as a sentinel-wrapped JSON block at the end of its output:

```
<!-- ccdi-registry-seed -->
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1", "results_file": "/tmp/ccdi_results_<id>.json", "inventory_snapshot_path": "/tmp/ccdi_snapshot_<id>.json"}
<!-- /ccdi-registry-seed -->
```

**Sentinel emission precondition:** `ccdi-gatherer` MUST NOT emit the `<!-- ccdi-registry-seed -->` sentinel block if the inventory failed to load at seed-build time. The sentinel MUST be emitted only when a valid `CompiledInventory` was loaded and `inventory_snapshot_version` can be sourced from a non-blank, non-null `schema_version` value. When the inventory fails to load or when `schema_version` is blank, null, or absent in the loaded inventory, the gatherer suppresses sentinel emission entirely — the `/dialogue` skill proceeds without `ccdi_seed` in the delegation envelope (Phase A initial injection is disabled for this session).

The `/dialogue` skill:

1. Extracts JSON between the sentinels from the ccdi-gatherer's output.
2. Reads `results_file` from the extracted JSON (the search results path needed for the initial commit).
2b. Reads `inventory_snapshot_path` from the extracted JSON (the pinned inventory snapshot path needed for `--inventory-snapshot` on initial commit `build-packet` calls and for the `ccdi_inventory_snapshot` delegation envelope field).
3. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`).
4. Passes the file path as `ccdi_seed: <path>` and the inventory snapshot path as `ccdi_inventory_snapshot: <inventory_snapshot_path>` in the delegation envelope to `codex-dialogue`. These two fields are an atomic pair — both MUST be present or both absent.

The `codex-dialogue` agent detects the `ccdi_seed` field and uses the file as its initial `--registry-file` for the mid-dialogue CCDI loop. If the field is absent, CCDI mid-dialogue is disabled for the session.

### Delegation Envelope Fields

The `/dialogue` skill passes these optional fields to `codex-dialogue`:

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `ccdi_seed` | file path (string) | ccdi-gatherer output | Initial registry file for mid-dialogue CCDI loop. Absent → mid-dialogue CCDI disabled. |
| `ccdi_inventory_snapshot` | file path (string) | `inventory_snapshot_path` field in ccdi-gatherer sentinel block | Pinned inventory snapshot for `--inventory-snapshot` on all `build-packet` CLI calls. Required when `ccdi_seed` is present. |
| `scope_envelope` | object | context-gatherers | Existing field — repo evidence scope. |
| `ccdi_debug` | boolean \| absent | `/dialogue` skill | When `true`, `codex-dialogue` emits `ccdi_trace` in its output. Absent or `false` → no trace. Testing-only; see [below](#ccditrace-output-contract) for the output contract and [delivery.md#debug-gated-ccditrace](delivery.md#debug-gated-ccditrace) for the trace schema and replay harness. |
| `ccdi_policy_snapshot`* | TBD | Phase B | *[Phase B — deferred]* Config snapshot for pinning CCDI tuning params during dialogue. Shape undefined — see [delivery.md#known-open-items](delivery.md#known-open-items). Not operative in Phase A. |

\*Deferred to Phase B. Shape undefined — see [delivery.md#known-open-items](delivery.md#known-open-items). Not operative in Phase A.

### `ccdi_trace` Output Contract

When `ccdi_debug: true` is set in the delegation envelope, `codex-dialogue` MUST emit a `ccdi_trace` key in its output containing an array of per-turn trace entries. Each trace entry MUST include all of the following keys regardless of value: `turn`, `classifier_result`, `semantic_hints`, `candidates`, `action`, `packet_staged`, `scout_conflict`, `commit`, `shadow_suppressed`. `semantic_hints` MUST be `null` when no hints exist (not absent from the entry).
**`shadow_suppressed` field:** Each per-turn trace entry includes a `shadow_suppressed: boolean` field (9th required key). Value is `true` when the trace entry describes an action whose registry mutation was suppressed by shadow mode — currently `skip_cooldown` (CLI-enforced via `--shadow-mode` flag) and `skip_scout` (agent-enforced abstention from `--mark-deferred scout_priority`); `false` otherwise. This field disambiguates whether the registry mutation described by the `action` value actually occurred.
**Exception for diagnostic entries:** `shadow_defer_intent` trace entries are counterfactual observations, not turn-loop observations. They are exempt from the 9-key requirement and use a reduced schema: `turn`, `action`, `topic_key`, `reason`, `classify_result_hash`. See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for the entry schema and semantics.
**Type discrimination:** The `ccdi_trace` array contains two structurally different entry types: per-turn entries (9 keys) and `shadow_defer_intent` entries (5 keys). Trace consumers MUST filter entries by `action` value before applying key-presence requirements. The 9-key invariant applies only to entries where `action != "shadow_defer_intent"`. Code iterating the trace array MUST NOT assume all entries have the same structure.

**`action` normative values:**

| Value | Meaning | Registry mutation |
|-------|---------|-------------------|
| `none` | No CCDI action this turn (no candidates or all filtered) | None |
| `classify` | Classifier pipeline executed | None |
| `schedule` | Topic scheduled for lookup | None |
| `search` | Search query executed | None |
| `build_packet` | Packet construction attempted | None |
| `prepare` | Packet staged for injection (prepare phase) | None |
| `inject` | Topic injected (`--mark-injected` committed) | Yes — active mode only; prohibited in shadow mode |
| `defer` | Topic deferred (`--mark-deferred` committed). Corresponds to `deferred_reason: "target_mismatch"` — see [registry.md#entry-structure](registry.md#entry-structure). | Yes — active mode only; prohibited in shadow mode |
| `suppress` | Topic suppressed (build-packet returned empty) | Yes — automatic suppression, both active and shadow modes |
| `skip_cooldown` | Topic deferred due to per-turn cooldown. In active mode: `deferred: cooldown` state written by `dialogue-turn`, `shadow_suppressed: false`. In shadow mode: registry write suppressed by `--shadow-mode` flag, `shadow_suppressed: true`, and a separate `shadow_defer_intent` entry with `reason: "cooldown"` is emitted per [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). Consumers MUST check `shadow_suppressed` to determine whether the registry mutation actually occurred. | Yes (active) / No (shadow — `shadow_suppressed: true`) |
| `skip_scout` | Topic deferred due to scout priority (deferred_reason: `"scout_priority"` — see [registry.md#entry-structure](registry.md#entry-structure)). In active mode, `skip_scout` is emitted (not `defer`) even though `--mark-deferred` is committed — the scout reason takes priority over the generic defer action. In shadow mode, `skip_scout` has `shadow_suppressed: true` — the `--mark-deferred scout_priority` call IS made with `--shadow-mode` appended; the CLI backstop makes `--mark-deferred` a no-op and the registry write is suppressed. | Yes via `--mark-deferred` (active) / No (shadow — `shadow_suppressed: true`) |
| `shadow_defer_intent` | Shadow mode counterfactual deferral: agent would have called `--mark-deferred` in active mode but is prohibited in shadow mode. Emitted as a diagnostic-only trace entry — see [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization). | N/A — diagnostic entry, no registry operation |

**`shadow_defer_intent` entry schema:** Unlike per-turn trace entries (which use the 9-key structure above), `shadow_defer_intent` entries use a diagnostic-only schema:

```json
{"turn": 3, "action": "shadow_defer_intent", "topic_key": "hooks.pre_tool_use", "reason": "target_mismatch", "classify_result_hash": "a7f3..."}
```

Fields: `turn` (integer — the turn number), `action` (always `"shadow_defer_intent"`), `topic_key` (string — the topic that would have been deferred), `reason` (`"target_mismatch"` or `"cooldown"` — the deferral reason that would have been written), `classify_result_hash` (string — hash of the classify result payload for evidence-freshness tracking). See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for repeat-detection semantics and intent resolution.
**`classify_result_hash` computation:** Hash of the classifier result for topic T. The hash MUST include `confidence`, `facet`, and `matched_aliases` (not just `topic_key`) — same `topic_key` with different `matched_aliases` MUST produce different hashes. Same classify payload MUST produce the same hash (stability invariant). See [delivery.md#shadow-mode-denominator-normalization](delivery.md#shadow-mode-denominator-normalization) for collision requirements and repeat-detection semantics.

**Scope note:** `shadow_defer_intent` is scoped to deferrals that participate in shadow yield normalization (`cooldown`, `target_mismatch`). Scout-priority is represented by `skip_scout` with `shadow_suppressed: true` and by `packets_deferred_scout` in diagnostics; it does not emit `shadow_defer_intent` under the current normalization model because scout-priority defers before search/build and does not inflate `packets_prepared`.

This follows the existing delegation envelope pattern (parallel to `scope_envelope`). The registry seed is NOT embedded in the briefing text — it is a separate envelope field. The consultation contract §6 does not need modification: `ccdi_seed` is an optional additive field, not a change to the existing envelope schema.

**Seed file identity invariant:** The registry seed file written by `/dialogue` at `/tmp/ccdi_registry_<id>.json` is the same file path passed to the commit-phase `build-packet --mark-injected` call. The commit mutates the seed file in-place. By the time `codex-dialogue` receives `ccdi_seed` and begins its mid-dialogue loop, the registry file reflects post-commit state (`injected` entries). The seed is not a separate read-only artifact — it is the live registry file from dialogue start.

### Shadow Mode Gate

At dialogue start, `codex-dialogue` determines whether CCDI runs in active or shadow mode:

1. Read `data/ccdi_shadow/graduation.json`. If the file is absent, default to shadow mode.
2. If `graduation.json` contains `"status": "approved"`, run in **active mode** (packets are injected into follow-up prompts).
3. If `status` is any other value (including `"rejected"`), run in **shadow mode**: the full CCDI PREPARE cycle runs and diagnostics accumulate, but packets are NOT prepended to follow-up prompts. `packets_injected` stays 0.

This gate determines only whether packets are delivered to Codex. In both modes, the prepare cycle runs identically — shadow mode observes what CCDI *would have* injected for kill-criteria evaluation (see [delivery.md#shadow-mode-kill-criteria](delivery.md#shadow-mode-kill-criteria)). The `status` enum values are defined in [delivery.md#graduation-protocol](delivery.md#graduation-protocol). The gate evaluates `status == "approved"` and treats all other values as shadow mode — this semantics is intentionally permissive of enum expansion.

**Phase A carve-out:** This gate governs Phase B mid-dialogue mutations in `codex-dialogue` only. Phase A initial injection (pre-delegation, in `/dialogue`) is unconditional and not subject to this gate — initial CCDI commits fire regardless of `graduation.json` status. See the `NOTE (CE-8 / D1)` in the [data flow](#data-flow-full-ccdi-dialogue) for the inline confirmation.

### Mid-Dialogue Phase (Per Turn in `codex-dialogue`)

CCDI integrates into the existing turn loop as a **prepare/commit** protocol — not a single monolithic step. This prevents registering injection for packets that were built but never sent.

```
codex-dialogue agent — existing turn loop with CCDI prepare/commit
│
├─ [Steps 1-4: existing turn logic — extract, process_turn, scout, compose]
│
├─ Step 5.5: CCDI PREPARE (after composition, before send)
│   ├─ Write Codex's latest response to /tmp/ccdi_turn_<id>.txt
│   ├─ Optionally write semantic hints to /tmp/ccdi_hints_<id>.json
│   ├─ If active mode:
│   │   └─ Bash: python3 topic_inventory.py dialogue-turn \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --inventory-snapshot <ccdi_snapshot_path> \
│   │            --text-file /tmp/ccdi_turn_<id>.txt --source codex \
│   │            [--semantic-hints-file /tmp/ccdi_hints_<id>.json]
│   ├─ If shadow mode:
│   │   └─ Bash: python3 topic_inventory.py dialogue-turn \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --inventory-snapshot <ccdi_snapshot_path> \
│   │            --text-file /tmp/ccdi_turn_<id>.txt --source codex \
│   │            --shadow-mode \
│   │            [--semantic-hints-file /tmp/ccdi_hints_<id>.json]
│   ├─ Read candidates from stdout
│   ├─ If candidates AND no scout target for this turn:
│   │   ├─ search_docs for the scheduled candidate's query plan
│   │   ├─ Write results to /tmp/ccdi_results_<id>.json
│   │   ├─ Bash: python3 topic_inventory.py build-packet \
│   │   │        --results-file /tmp/ccdi_results_<id>.json \
│   │   │        --registry-file /tmp/ccdi_registry_<id>.json \
│   │   │        --mode mid_turn --topic-key <candidate.topic_key> \
│   │   │        --facet <candidate.facet> \
│   │   │        --coverage-target <candidate.coverage_target> \
│   │   │        --inventory-snapshot <ccdi_snapshot_path>   (NO --mark-injected yet; --facet provided for ranking consistency; --inventory-snapshot required when --registry-file is present — ensures suppressed_docs_epoch is recorded with the current docs_epoch rather than null, preventing spurious re-entry on subsequent dialogue-turn calls)
│   │   ├─ If build-packet returned empty: no packet to stage (automatic suppression already fired); skip target-match
│   │   ├─ Target-match check: verify staged packet supports the composed follow-up target
│   │   ├─ If target-relevant: stage for prepending
│   │   └─ If not target-relevant:
│   │       ├─ If active mode:
│   │       │   └─ Bash: python3 topic_inventory.py build-packet \
│   │       │            --results-file /tmp/ccdi_results_<id>.json \
│   │       │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │       │            --inventory-snapshot <ccdi_snapshot_path> \
│   │       │            --mode mid_turn \
│   │       │            --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │       │            --skip-build
│   │       └─ If shadow mode: Bash: python3 topic_inventory.py build-packet \
│   │                    --registry-file /tmp/ccdi_registry_<id>.json \
│   │                    --inventory-snapshot <ccdi_snapshot_path> \
│   │                    --mode mid_turn \
│   │                    --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │                    --shadow-mode --skip-build
│   │            (--shadow-mode makes --mark-deferred a no-op; diagnostics record the intent)
│   ├─ If candidates AND scout target exists:
│   │   (Scout target detection is agent-side: the codex-dialogue agent determines whether
│   │    execute_scout produced a scout candidate for the current turn from the scope_envelope
│   │    returned by process_turn. No CLI flag is involved — the CLI has no awareness of scout
│   │    state. The agent makes this determination and calls --mark-deferred scout_priority
│   │    when appropriate.)
│   │   ├─ If active mode:
│   │   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │   │            --inventory-snapshot <ccdi_snapshot_path> \
│   │   │            --mode mid_turn \
│   │   │            --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │   │            --skip-build
│   │   └─ If shadow mode: Bash: python3 topic_inventory.py build-packet \
│   │                --registry-file /tmp/ccdi_registry_<id>.json \
│   │                --inventory-snapshot <ccdi_snapshot_path> \
│   │                --mode mid_turn \
│   │                --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │                --shadow-mode --skip-build
│   │        (--shadow-mode makes --mark-deferred a no-op; diagnostics record the intent)
│   └─ If no candidates: no CCDI this turn
│
│   **Multi-candidate turns:** When `dialogue-turn` emits multiple candidates:
│   - Process candidates in scheduling priority order (highest priority first).
│   - The per-turn cooldown (registry.md scheduling step 5) applies only to
│     `candidate_type: "new"` entries. `pending_facet` and `facet_expansion`
│     candidates are exempt from the cooldown and may be processed in the same
│     turn as a `new` candidate.
│   - If multiple candidates remain after cooldown filtering, process all in
│     sequence within the same turn. Each candidate gets its own search →
│     build-packet → target-match cycle.
│
├─ [Step 6: send follow-up to Codex]
│   ├─ If active mode AND packet staged: prepend packet to follow-up before sending
│   └─ If shadow mode: send follow-up without packet (diagnostics record the staged packet)
│       See [delivery.md#graduation-protocol-and-kill-criteria](delivery.md#graduation-protocol-and-kill-criteria) for the gate
│       definition, graduation.json schema, and kill criteria.
│
├─ Step 7.5: CCDI COMMIT (after send confirmed)
│   ├─ If active mode AND packet was sent:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --results-file /tmp/ccdi_results_<id>.json \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --inventory-snapshot <ccdi_snapshot_path> \
│   │            --mode mid_turn --topic-key <candidate.topic_key> \
│   │            --facet <candidate.facet> \
│   │            --coverage-target <candidate.coverage_target> --mark-injected
│   ├─ If shadow mode: no commit (packet staged but not delivered)
│   └─ If send failed or packet was not staged: no commit
│
└─ Continue dialogue loop
```

#### Shadow-mode Registry Invariant

In shadow mode, the only permitted registry mutations are automatic suppressions written by `build-packet` empty output (`suppressed: weak_results` or `suppressed: redundant`). All other mutation types are prohibited, enforced at two distinct layers:

**CLI-enforced (via `--shadow-mode` flag):** `dialogue-turn` cooldown deferral writes (Step 5.5, the cooldown deferral bullet in `dialogue-turn` registry side-effects) are suppressed when the `--shadow-mode` flag is passed. The CLI itself prevents the `deferred: cooldown` state write — no agent logic is involved. `candidate_type: 'new'` entries excluded by the cooldown limit remain in `detected` state.

**Agent-enforced (split model):** The agent MUST NOT call `--mark-injected` (Step 7.5) in shadow mode — this is true abstention (no CLI backstop exists for injection commits). For `--mark-deferred` (Step 5.5), the agent MUST pass `--shadow-mode` to every `build-packet --mark-deferred` call — the CLI backstop makes `--mark-deferred` a no-op when `--shadow-mode` is set (see below). The agent calls `--mark-deferred` in both active and shadow modes; the behavioral difference is enforced by the CLI flag, not by agent abstention.

**CLI backstop for `build-packet`:** `build-packet` accepts `--shadow-mode`. When passed, `--mark-deferred` is a no-op: the command logs the intended deferral reason and topic key to stderr but does NOT write to the registry file. Exit code is 0 (success). This converts the agent-abstention requirement for scout-priority and target-mismatch deferrals into a CLI-level guard, preventing shadow-mode registry corruption from agent implementation bugs. The `codex-dialogue` agent MUST pass `--shadow-mode` to `build-packet` whenever `graduation.json` status is not `"approved"`. **Layer 2b test:** Verify that `build-packet --shadow-mode --mark-deferred scout_priority` produces exit 0 with zero registry mutations and a stderr log entry.

**Suppression failure in shadow mode:** When `build-packet` empty output occurs in shadow mode and the automatic suppression registry write fails (e.g., due to disk I/O error), the topic remains in `detected` state and will be re-evaluated on the next turn. This is acceptable degradation per the [resilience principle](foundations.md#resilience-principle) — shadow mode is diagnostic, and a missed suppression does not affect graduation metrics (suppression counts are not part of the kill criteria).

The prepare cycle runs to measure yield and latency for diagnostics, but the registry reflects only classifier-driven state. Deferral state is recorded in diagnostics only. This prevents shadow-mode registry pollution from corrupting graduation kill-criteria metrics. See [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints).

**Key invariant:** `--mark-injected` is called only after the packet-containing prompt has been confirmed sent to Codex. This applies to both paths: the initial injection commit (after briefing send in `/dialogue`) and the mid-dialogue commit (Step 7.5 after follow-up send in `codex-dialogue`). This prevents the registry from recording injection for packets that were staged but never delivered (e.g., if the briefing or follow-up prompt failed).

**Idempotency invariant:** `build-packet` called at commit time with the same `--results-file` and `--facet` as the prepare phase MUST produce identical chunk IDs. The packet builder MUST be deterministic given identical inputs — no randomization, stable sort for ranking. This ensures `coverage.injected_chunk_ids` accurately reflects the content sent to Codex, preserving deduplication correctness in subsequent turns.

### Target-Match Predicate

The **composed follow-up target** is the follow-up question text that `codex-dialogue` has composed for the current turn (the text that will be sent to Codex via `codex-reply`). This text exists after Step 4 (composition) and before Step 5.5 (CCDI PREPARE).

The target-match check determines whether a CCDI packet is relevant to the composed question. A packet is **target-relevant** when at least one of:

- **(a)** Any of the packet's `topics` (from the `<!-- ccdi-packet -->` metadata comment) appears as a substring (case-insensitive) in the composed follow-up text.
- **(b)** Running `classify` on the composed follow-up text produces a topic that overlaps with the packet's `topics`.

The agent performs this check. When condition (a) fails, the agent MUST invoke `classify --text-file <follow-up>` and evaluate condition (b) before deciding to defer. The agent makes the final pass/fail decision and invokes `build-packet --mark-deferred <topic_key> --deferred-reason target_mismatch --skip-build` if the check fails.

**CLI interface:** The target-match check is performed by the agent, not the CLI. The CLI provides two supporting operations:
1. `classify --text-file <follow-up>` — used by the agent for condition (b) when condition (a) fails.
2. `build-packet --mark-deferred <topic_key> --deferred-reason target_mismatch --skip-build` — invoked by the agent when neither condition passes.

**Inventory snapshot for condition (b):** The `classify` invocation for condition (b) MUST use the pinned inventory snapshot (`--inventory <ccdi_snapshot_path>`) to ensure topic resolution is consistent with the `dialogue-turn` classification within the same dialogue.

**Flag name enforcement:** `classify` accepts `--inventory` (not `--inventory-snapshot`). Passing `--inventory-snapshot` to `classify` is not a valid flag — implementations MUST reject it with a non-zero exit or ignore it with a warning. See the CLI integration tests in [delivery.md](delivery.md#cli-integration-tests) for the negative test.

**Replay fixture assertion:** The `target_mismatch_deferred.replay.json` fixture provides a `composed_target` field in each trace entry. The harness feeds this to the target-match check logic. The assertion verifies the registry transitions to `deferred: target_mismatch` when the packet topics do not appear in the composed target.

## Inventory Generation

```
dump_index_metadata (new claude-code-docs tool)
│
└─ build_inventory.py (MCP client)
   ├─ Connects to claude-code-docs server
   ├─ Calls dump_index_metadata → categories, headings, chunk IDs, code literals
   ├─ Generates TopicRecord scaffold
   ├─ Reads topic_overlay.json → merges denylist, alias fixes, weight overrides
   └─ Writes topic_inventory.json

Trigger: automatic post-reload hook (when docs_epoch changes) or manual (--force)
```

## `dump_index_metadata` Response Schema

New tool added to the `claude-code-docs` MCP server. Returns structured metadata about the indexed documentation corpus — categories, headings, chunk IDs, and distinctive terms — without returning full document content.

**Parameters:** None (dumps the full index metadata).

**Response:**

```json
{
  "index_version": "string",
  "built_at": "ISO timestamp",
  "docs_epoch": "string | null",
  "categories": [
    {
      "name": "hooks",
      "aliases": ["hook"],
      "chunk_count": 12,
      "chunks": [
        {
          "chunk_id": "hooks#pretooluse",
          "source_file": "https://code.claude.com/docs/en/hooks",
          "headings": ["Hooks", "Hook Events", "PreToolUse"],
          "code_literals": ["PreToolUse", "permissionDecision", "updatedInput", "additionalContext"],
          "config_keys": ["hookSpecificOutput"],
          "distinctive_terms": ["PreToolUse", "tool_input", "permissionDecision"]
        }
      ]
    }
  ]
}
```

**Field types:**

| Field | Type | Description |
|-------|------|-------------|
| `index_version` | `string` | Version tag for the search index schema. |
| `built_at` | `string` (ISO 8601 timestamp) | When the index was last built. |
| `docs_epoch` | `string \| null` | Hash of the indexed document set; `null` when index is empty. |
| `categories` | `array` of category objects | One per indexed documentation category. |

`docs_epoch` is the index epoch — a version marker that changes on each `reload_docs` call. `build_inventory.py` records this value as `CompiledInventory.docs_epoch` and propagates it to `RegistrySeed.docs_epoch`. The suppression re-entry logic in [registry.md#suppression-re-entry](registry.md#suppression-re-entry) compares `suppressed_docs_epoch` against the current `docs_epoch` to determine whether `weak_results`-suppressed topics should re-enter. If `docs_epoch` is null (e.g., index has never been reloaded), it is stored as-is.

`build_inventory.py` consumes this to generate topic scaffolds: category names → family topics, headings → leaf topics, code literals → exact aliases, distinctive terms → phrase/token aliases, config_keys → exact aliases with `facet_hint: "config"`.

**Cross-package contract:** This response schema is a dependency of the `cross-model` plugin, but `dump_index_metadata` is implemented in `packages/mcp-servers/claude-code-docs/` (a separate TypeScript package). To prevent silent breakage:

1. A boundary contract test in `test_ccdi_contracts.py` validates the response shape against expected fields.
2. The `dump_index_metadata` tool implementation in `claude-code-docs` must document the CCDI consumer dependency (comment in the handler).

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `claude-code-docs` not installed | Tool availability check at preflight | Skip CCDI, surface note if topic detected |
| `search_docs` returns empty or errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` in [registry](registry.md) |
| `dialogue-turn` CLI fails mid-dialogue | Non-zero exit | Continue dialogue without mid-turn injection, preserve previous registry |
| `--inventory-snapshot` absent on full-CCDI call | Missing required flag when `--registry-file` present | Non-zero exit with descriptive error identifying the missing flag |
| `--inventory-snapshot` absent on `build-packet` with `--registry-file` present | Missing required flag when `--registry-file` present | Non-zero exit with descriptive error identifying the missing flag (symmetric with `dialogue-turn` behavior per footnote ‡) |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
