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
| `dialogue-turn --registry-file <path> --text-file <path> --source codex\|user [--semantic-hints-file <path>] [--config <path>]` | Text file + registry + optional hints (hints file schema: see [registry.md#semantic-hints](registry.md#semantic-hints)) | Updated registry file + injection candidates JSON (stdout) | Full CCDI |
| `build-packet [--results-file <path>] [--registry-file <path>] --mode initial\|mid_turn [--topic-key <key>] [--facet <facet>] [--coverage-target family\|leaf] [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |

All commands accept `--config <path>` to load [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson). If omitted, uses built-in defaults. Registry is a JSON file containing only durable states (see [registry.md](registry.md#durable-vs-attempt-local-states)). Attempt-local states (`looked_up`, `built`) exist within a single CLI invocation and are never written to the file.

**`--registry-file` optionality on `build-packet`:** When omitted (CCDI-lite mode), deduplication against prior injections is skipped and `--mark-injected` / `--mark-deferred` are no-ops. CCDI-lite has no registry — each invocation builds a fresh packet without coverage history.

**`--results-file` conditionality:** Required for packet construction (normal build path). Not required when `--skip-build` is passed with `--mark-deferred` — no packet construction occurs in that path.

**`--topic-key <key>` flag:** Required when `--registry-file` is provided. Identifies which topic's registry entry to update for automatic suppression (on empty output), `--mark-injected`, or `--mark-deferred`. Without `--registry-file` (CCDI-lite mode), `--topic-key` is ignored.

**`--facet <facet>` flag:** Serves two purposes depending on mode:

- **During packet construction:** When provided, directs facet-based ranking in [packets.md build process step 3](packets.md#build-process). When absent (initial mode without `--mark-injected`), the CLI derives the ranking facet per-topic from `ClassifierResult.resolved_topics[].facet` (see [packets.md](packets.md#build-process) for fallback rules).
- **At commit time (`--mark-injected`):** Required when `--mark-injected` is passed with `--registry-file`. Specifies which facet to append to `coverage.facets_injected`.

**Facet consistency (mid-turn mode):** In mid-turn mode, the `facet` value at commit time MUST match the facet used during the prepare phase. The prepare `build-packet` output includes a `<!-- ccdi-packet ... facet="..." -->` metadata comment containing the facet actually used for the search. The agent passes `candidate.facet` from `dialogue-turn` candidates JSON (the source of truth for both calls) to `--facet` at both prepare and commit time.

**Facet in initial mode:** The ccdi-gatherer's prepare call omits `--facet` because initial packets cover multiple topics, each with its own classifier-resolved facet. The commit call passes `--facet <entry.facet>` per-topic from the seed file, which records the classifier's resolved facet at seed-build time. Consistency is maintained because both the prepare-phase ranking facet (derived per-topic from the classifier result) and the commit-phase `--facet` (from `RegistrySeed.entries[].facet`) originate from the same source: `ClassifierResult.resolved_topics[].facet`.

**`--skip-build` flag:** When passed with `--mark-deferred`, skips packet construction and only writes deferred state to the registry. This avoids redundant rebuilds when the target-match check already determined the packet is not target-relevant. `--skip-build` is only valid with `--mark-deferred`; ignored otherwise. When `--skip-build` is passed with `--mark-deferred`, `--results-file` is not required — no packet construction occurs.

**`--coverage-target family|leaf` flag:** Required when both `--mark-injected` and `--registry-file` are present. When `--registry-file` is absent (CCDI-lite mode), `--coverage-target` is ignored even if passed. Determines whether `coverage.overview_injected` is set (when `family` + facet=overview).

**`--mark-injected` registry side-effects:** When `--mark-injected` is passed with `--registry-file`, the following fields are updated per the [Field Update Rules](registry.md#field-update-rules): `state` → `injected`, `last_injected_turn`, `last_query_fingerprint`, `coverage.injected_chunk_ids` (appended from built packet's chunk IDs), `coverage.facets_injected` (appended), `coverage.pending_facets` (served facet removed if present), `consecutive_medium_count` ← 0. When `--coverage-target family` and `facet=overview`: additionally `coverage.overview_injected` ← true.

**`dialogue-turn` registry side-effects:** `dialogue-turn` performs the following registry mutations (per the [Field Update Rules](registry.md#field-update-rules)):

- Writes new `detected` entries for newly resolved topics (`absent → detected`).
- Updates `last_seen_turn` and `consecutive_medium_count` for existing entries on re-detection.
- Resets `consecutive_medium_count` to 0 for entries absent from classifier output.
- Decrements `deferred_ttl` by 1 for all entries in `deferred` state.
- Transitions `deferred → detected` when `deferred_ttl` reaches 0 and topic reappears in classifier output; resets `deferred_ttl` to config value when topic is absent at TTL=0.
- Re-enters `suppressed → detected` when re-entry conditions are met: `docs_epoch` change for `weak_results`, coverage state change for `redundant`.
- Re-enters `suppressed → detected` when `--semantic-hints-file` contains an `extends_topic` hint that resolves to a suppressed topic (applying the field updates from the `suppressed → detected` re-entry row).
- Emits `facet_expansion` candidates when `extends_topic` hints resolve to `injected` topics with a facet not yet in `facets_injected` (cascade-resolved facet: hint-resolved → `pending_facets[0]` → `default_facet`; see [registry.md#semantic-hints](registry.md#semantic-hints)). Updates `coverage.pending_facets` per the field update rules.
- Emits `pending_facet` candidates when an `injected` topic has non-empty `pending_facets` (from prior `contradicts_prior` hints) and the first pending facet is not yet in `facets_injected`.

**`build-packet` automatic suppression:** When `--registry-file` is provided and `build-packet` returns empty output, it automatically writes a suppression state to the registry for the candidate topic. The suppression reason depends on *why* the output is empty:

- `weak_results` — search returned poor results (below quality threshold) or `search_docs` returned empty/error. The search signal is weak.
- `redundant` — search returned useful results but all `chunk_id` values were filtered by deduplication against `injected_chunk_ids`. The topic is already covered.

No flag is needed — empty output triggers suppression unconditionally when a registry is available. See [packets.md#failure-modes](packets.md#failure-modes) for the full decision tree.

**Suppression and deferral precedence:** If `build-packet` returns empty output, automatic suppression (either `weak_results` or `redundant`) writes to the registry. In this case, the target-match check has no packet to evaluate — skip the `--mark-deferred` path entirely. The topic is already handled by suppression. The mid-dialogue flow should check for empty output before proceeding to target-match.

**`dialogue-turn` candidates JSON schema:** The `dialogue-turn` command writes injection candidates to stdout as a JSON array:

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

Each element contains: `topic_key` (string), `family_key` (string), `facet` (Facet — the resolved facet for this candidate), `confidence` (`"high" | "medium" | null` — `null` for `facet_expansion` and `pending_facet` candidates which bypass confidence thresholds; low-confidence topics are tracked in the registry but excluded from injection candidates; see [classifier.md#injection-thresholds](classifier.md#injection-thresholds)), `coverage_target` (`"family" | "leaf"` — the classifier's resolved coverage target for this candidate), `candidate_type` (see below), and `query_plan` (the topic's QueryPlan from the inventory, for the agent to execute search). An empty array means no injection candidates this turn.

**`candidate_type` field:** Discriminates how the candidate was scheduled. The agent uses this to distinguish standard injection candidates from hint-driven facet operations on already-injected topics.

| `candidate_type` | Meaning | When emitted |
|------------------|---------|-------------|
| `"new"` | Standard injection candidate (topic not yet `injected`) | Classifier-driven detection or re-detection |
| `"facet_expansion"` | Facet expansion on an `injected` topic | `extends_topic` hint resolved to an injected topic with a facet not yet in `facets_injected` |
| `"pending_facet"` | Pending facet re-injection on an `injected` topic | `contradicts_prior` hint previously appended to `pending_facets`; scheduler selected the first pending facet |

For `facet_expansion` and `pending_facet` candidates, the `facet` field contains the cascade-resolved facet computed by `dialogue-turn` (the facet the agent should pass to `--facet` at both prepare and commit time). The `confidence` field is `null` for these candidate types (confidence is a classifier concept; hint-driven candidates bypass confidence thresholds). The topic's state remains `injected` — these candidates do not change the topic's durable state until `--mark-injected` commits the facet coverage update.

**`--source codex|user` on `dialogue-turn`:** `codex` = classifier runs on Codex's response text; `user` = classifier runs on the user's turn text. Both sources use the same two-stage pipeline and identical scheduling behavior — no source-differentiated rules are currently defined. See [delivery.md#known-open-items](delivery.md#known-open-items) for the deferred divergence item.

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
│  ├─ Check injection threshold (same as initial — per classifier.md#injection-thresholds):
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

### Shadow Mode Gate

At dialogue start, `codex-dialogue` determines whether CCDI runs in active or shadow mode:

1. Read `data/ccdi_shadow/graduation.json`. If the file is absent, default to shadow mode.
2. If `graduation.json` contains `"status": "approved"`, run in **active mode** (packets are injected into follow-up prompts).
3. If `status` is any other value (including `"rejected"`), run in **shadow mode**: the full CCDI PREPARE cycle runs and diagnostics accumulate, but packets are NOT prepended to follow-up prompts. `packets_injected` stays 0.

This gate determines only whether packets are delivered to Codex. In both modes, the prepare cycle runs identically — shadow mode observes what CCDI *would have* injected for kill-criteria evaluation (see [delivery.md#shadow-mode-kill-criteria](delivery.md#shadow-mode-kill-criteria)).

### Pre-Dialogue Phase

```
User prompt
│
├─ /dialogue skill (Claude)
│  ├─ Bash: python3 topic_inventory.py classify --text-file <prompt>
│  ├─ If injection threshold met → dispatch ccdi-gatherer in parallel
│  │   (threshold: 1 high-confidence OR 2+ medium-confidence same family;
│  │    per classifier.md#injection-thresholds)
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
│  │              --coverage-target <entry.coverage_target> --mark-injected
│  │       (commit mutates the seed file in-place — entries transition to `injected`)
│  └─ If briefing send failed: no commit (seed entries remain `detected`)
│
├─ Pass ccdi_seed envelope field to codex-dialogue delegation
```

### Registry Seed Handoff

The `ccdi-gatherer` subagent emits its [registry seed](data-model.md#registryseed) as a sentinel-wrapped JSON block at the end of its output:

```
<!-- ccdi-registry-seed -->
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1", "results_file": "/tmp/ccdi_results_<id>.json"}
<!-- /ccdi-registry-seed -->
```

The `/dialogue` skill:

1. Extracts JSON between the sentinels from the ccdi-gatherer's output.
2. Reads `results_file` from the extracted JSON (the search results path needed for the initial commit).
3. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`).
4. Passes the file path as `ccdi_seed: <path>` in the delegation envelope to `codex-dialogue`.

The `codex-dialogue` agent detects the `ccdi_seed` field and uses the file as its initial `--registry-file` for the mid-dialogue CCDI loop. If the field is absent, CCDI mid-dialogue is disabled for the session.

### Delegation Envelope Fields

The `/dialogue` skill passes these optional fields to `codex-dialogue`:

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `ccdi_seed` | file path (string) | ccdi-gatherer output | Initial registry file for mid-dialogue CCDI loop. Absent → mid-dialogue CCDI disabled. |
| `scope_envelope` | object | context-gatherers | Existing field — repo evidence scope. |
| `ccdi_debug` | boolean \| absent | `/dialogue` skill | When `true`, `codex-dialogue` emits `ccdi_trace` in its output. Absent or `false` → no trace. Testing-only; see [delivery.md#debug-gated-ccdi_trace](delivery.md#debug-gated-ccdi_trace) for trace schema. |
| `ccdi_policy_snapshot` | TBD | Phase B | Config snapshot for pinning CCDI tuning params during dialogue. Shape undefined — see [delivery.md#known-open-items](delivery.md#known-open-items). |

This follows the existing delegation envelope pattern (parallel to `scope_envelope`). The registry seed is NOT embedded in the briefing text — it is a separate envelope field. The consultation contract §6 does not need modification: `ccdi_seed` is an optional additive field, not a change to the existing envelope schema.

**Seed file identity invariant:** The registry seed file written by `/dialogue` at `/tmp/ccdi_registry_<id>.json` is the same file path passed to the commit-phase `build-packet --mark-injected` call. The commit mutates the seed file in-place. By the time `codex-dialogue` receives `ccdi_seed` and begins its mid-dialogue loop, the registry file reflects post-commit state (`injected` entries). The seed is not a separate read-only artifact — it is the live registry file from dialogue start.

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
│   ├─ Bash: python3 topic_inventory.py dialogue-turn \
│   │        --registry-file /tmp/ccdi_registry_<id>.json \
│   │        --text-file /tmp/ccdi_turn_<id>.txt --source codex \
│   │        [--semantic-hints-file /tmp/ccdi_hints_<id>.json]
│   ├─ Read candidates from stdout
│   ├─ If candidates AND no scout target for this turn:
│   │   ├─ search_docs for the scheduled candidate's query plan
│   │   ├─ Write results to /tmp/ccdi_results_<id>.json
│   │   ├─ Bash: python3 topic_inventory.py build-packet \
│   │   │        --results-file /tmp/ccdi_results_<id>.json \
│   │   │        --registry-file /tmp/ccdi_registry_<id>.json \
│   │   │        --mode mid_turn --topic-key <candidate.topic_key> \
│   │   │        --facet <candidate.facet> \
│   │   │        --coverage-target <candidate.coverage_target>   (NO --mark-injected yet; --facet provided for ranking consistency)
│   │   ├─ If build-packet returned empty: no packet to stage (automatic suppression already fired); skip target-match
│   │   ├─ Target-match check: verify staged packet supports the composed follow-up target
│   │   ├─ If target-relevant: stage for prepending
│   │   └─ If not target-relevant:
│   │       └─ Bash: python3 topic_inventory.py build-packet \
│   │                --results-file /tmp/ccdi_results_<id>.json \
│   │                --registry-file /tmp/ccdi_registry_<id>.json \
│   │                --mode mid_turn \
│   │                --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │                --skip-build
│   ├─ If candidates AND scout target exists:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --mode mid_turn \
│   │            --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │            --skip-build
│   └─ If no candidates: no CCDI this turn
│
├─ [Step 6: send follow-up to Codex]
│   ├─ If active mode AND packet staged: prepend packet to follow-up before sending
│   └─ If shadow mode: send follow-up without packet (diagnostics record the staged packet)
│
├─ Step 7.5: CCDI COMMIT (after send confirmed)
│   ├─ If active mode AND packet was sent:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --results-file /tmp/ccdi_results_<id>.json \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --mode mid_turn --topic-key <candidate.topic_key> \
│   │            --facet <candidate.facet> \
│   │            --coverage-target <candidate.coverage_target> --mark-injected
│   ├─ If shadow mode: no commit (packet staged but not delivered)
│   └─ If send failed or packet was not staged: no commit
│
└─ Continue dialogue loop
```

**Key invariant:** `--mark-injected` is called only after the packet-containing prompt has been confirmed sent to Codex. This applies to both paths: the initial injection commit (after briefing send in `/dialogue`) and the mid-dialogue commit (Step 7.5 after follow-up send in `codex-dialogue`). This prevents the registry from recording injection for packets that were staged but never delivered (e.g., if the briefing or follow-up prompt failed).

### Target-Match Predicate

The **composed follow-up target** is the follow-up question text that `codex-dialogue` has composed for the current turn (the text that will be sent to Codex via `codex-reply`). This text exists after Step 4 (composition) and before Step 5.5 (CCDI PREPARE).

The target-match check determines whether a CCDI packet is relevant to the composed question. A packet is **target-relevant** when at least one of the packet's `topics` appears as a substring (case-insensitive) in the composed follow-up text, OR running the classifier on the follow-up text produces a topic that overlaps with the packet's `topics`.

**CLI interface:** The target-match check is performed by the agent, not the CLI. The agent:
1. Reads the `build-packet` stdout (rendered markdown).
2. Checks condition (a): any of the packet's `topics` appears as a case-insensitive substring in the composed follow-up text.
3. If condition (a) fails, checks condition (b): runs `classify --text-file <follow-up>` on the composed follow-up text and checks whether any classifier output topic matches a packet topic.
4. If neither condition passes (not target-relevant): invokes `build-packet --mark-deferred --deferred-reason target_mismatch --skip-build`.

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

`docs_epoch` is the index epoch — a version marker that changes on each `reload_docs` call. `build_inventory.py` records this value as `CompiledInventory.docs_epoch` and propagates it to `RegistrySeed.docs_epoch`. The suppression re-entry logic in [registry.md#suppression-re-entry](registry.md#suppression-re-entry) compares `suppressed_docs_epoch` against the current `docs_epoch` to determine whether `weak_results`-suppressed topics should re-enter. If `docs_epoch` is null (e.g., index has never been reloaded), it is stored as-is.

`build_inventory.py` consumes this to generate topic scaffolds: category names → family topics, headings → leaf topics, code literals → exact aliases, distinctive terms → phrase/token aliases, config_keys → exact aliases with `facet_hint: "config"`.

**Cross-package contract:** This response schema is a dependency of the `cross-model` plugin, but `dump_index_metadata` is implemented in `packages/mcp-servers/claude-code-docs/` (a separate TypeScript package). To prevent silent breakage:

1. A boundary contract test in `test_ccdi_contracts.py` validates the response shape against expected fields.
2. The `dump_index_metadata` tool implementation in `claude-code-docs` must document the CCDI consumer dependency (comment in the handler or a `CONSUMERS.md` file).

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `claude-code-docs` not installed | Tool availability check at preflight | Skip CCDI, surface note if topic detected |
| `search_docs` returns empty or errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` in [registry](registry.md) |
| `dialogue-turn` CLI fails mid-dialogue | Non-zero exit | Continue dialogue without mid-turn injection, preserve previous registry |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
