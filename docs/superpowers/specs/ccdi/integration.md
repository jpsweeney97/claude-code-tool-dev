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
| `build-packet [--results-file <path>] [--registry-file <path>] --mode initial\|mid_turn [--topic-key <key>] [--facet <facet>]† [--coverage-target family\|leaf] [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |

†`--facet` is required when `--mark-injected` is passed with `--registry-file`.

All commands accept `--config <path>` to load [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson). If omitted, uses built-in defaults. The live registry file has the structure defined in [data-model.md#live-registry-file-schema](data-model.md#live-registry-file-schema) — `TopicRegistryEntry` durable states plus `RegistrySeed` envelope fields (`docs_epoch`, `inventory_snapshot_version`); `results_file` is stripped at initial commit. See [registry.md](registry.md#durable-vs-attempt-local-states) for the durable vs attempt-local distinction. Attempt-local states (`looked_up`, `built`) exist within a single CLI invocation and are never written to the file.

**`--registry-file` optionality on `build-packet`:** When omitted (CCDI-lite mode), deduplication against prior injections is skipped and `--mark-injected` / `--mark-deferred` are no-ops. CCDI-lite has no registry — each invocation builds a fresh packet without coverage history.

**`--results-file` conditionality:** Required for packet construction (normal build path). Not required when `--skip-build` is passed with `--mark-deferred` — no packet construction occurs in that path.

**`--topic-key <key>` flag:** Required when `--registry-file` is provided. Identifies which topic's registry entry to update for automatic suppression (on empty output), `--mark-injected`, or `--mark-deferred`. Without `--registry-file` (CCDI-lite mode), `--topic-key` is ignored.

**`--facet <facet>` flag:** Serves two purposes depending on mode:

- **During packet construction:** When provided, directs facet-based ranking in [packets.md build process step 3](packets.md#build-process). When absent (initial mode without `--mark-injected`), the CLI derives the ranking facet per-topic from `ClassifierResult.resolved_topics[].facet` (see [packets.md](packets.md#build-process) for fallback rules).
- **At commit time (`--mark-injected`):** Required when `--mark-injected` is passed with `--registry-file`. Specifies which facet to append to `coverage.facets_injected`.

**Facet consistency (mid-turn mode):** In mid-turn mode, the `facet` value at commit time MUST match the facet used during the prepare phase. On mismatch: non-zero exit with descriptive error including both facet values. The prepare-phase facet is authoritative; commit-phase callers MUST provide the matching value. The prepare `build-packet` output includes a `<!-- ccdi-packet ... facet="..." -->` metadata comment containing the facet actually used for the search. The agent passes `candidate.facet` from `dialogue-turn` candidates JSON (the source of truth for both calls) to `--facet` at both prepare and commit time.

**Facet in initial mode:** The ccdi-gatherer's prepare call omits `--facet` because initial packets cover multiple topics, each with its own classifier-resolved facet. The commit call passes `--facet <entry.facet>` per-topic from the seed file, which records the classifier's resolved facet at seed-build time. Consistency is maintained because both the prepare-phase ranking facet (derived per-topic from the classifier result) and the commit-phase `--facet` (from `RegistrySeed.entries[].facet`) originate from the same source: `ClassifierResult.resolved_topics[].facet`. The commit-phase facet is sourced solely from the `RegistrySeed` entry's `facet` field (populated from `ClassifierResult.resolved_topics[].facet` at seed creation). No cross-check mechanism exists in initial mode — the `RegistrySeed` entry is the ground truth for the commit phase.

**`--skip-build` flag:** When passed with `--mark-deferred`, skips packet construction and only writes deferred state to the registry. This avoids redundant rebuilds when the target-match check already determined the packet is not target-relevant. `--skip-build` is only valid with `--mark-deferred`; ignored otherwise. When `--skip-build` is passed with `--mark-deferred`, `--results-file` is not required — no packet construction occurs.

**`--coverage-target family|leaf` flag:** Required when both `--mark-injected` and `--registry-file` are present. When `--registry-file` is absent (CCDI-lite mode), `--coverage-target` is ignored even if passed. Determines whether `coverage.overview_injected` is set (when `family` + facet=overview).

**`--mark-injected` registry side-effects:** When `--mark-injected` is passed with `--registry-file`, the following fields are updated per the [Field Update Rules](registry.md#field-update-rules): `state` → `injected`, `last_injected_turn`, `last_query_fingerprint`, `coverage.injected_chunk_ids` (appended from built packet's chunk IDs), `coverage.facets_injected` (appended), `coverage.pending_facets` (served facet removed if present), `consecutive_medium_count` ← 0. When `--coverage-target family` and `facet=overview`: additionally `coverage.overview_injected` ← true. Additionally, strips `results_file` from the registry file if present (per [data-model.md#registryseed](data-model.md#registryseed) — `results_file` is a transport-only field that MUST NOT persist after initial commit).

### `dialogue-turn` Registry Side-Effects

`dialogue-turn` performs the following registry mutations (per the [Field Update Rules](registry.md#field-update-rules)):

- Writes new `detected` entries for newly resolved topics (`absent → detected`).
- Updates `last_seen_turn` for all re-detected entries; increments `consecutive_medium_count` only for **leaf-kind** entries re-detected at medium confidence — family-kind entries leave `consecutive_medium_count` unchanged (per [registry.md#scheduling-rules](registry.md#scheduling-rules) step 4).
- Resets `consecutive_medium_count` to 0 for entries absent from classifier output.
- Decrements `deferred_ttl` by 1 for all entries in `deferred` state.
- Transitions `deferred → detected` when `deferred_ttl` reaches 0 and topic reappears in classifier output. When `deferred_ttl` reaches 0 and the topic is absent from classifier output: topic remains `deferred` with `deferred_ttl` reset to the configured default (`injection.deferred_ttl_turns`), `deferred_reason` unchanged (see [registry.md#field-update-rules](registry.md#field-update-rules), `deferred → deferred` row).
- For entries in `suppressed` state that appear in classifier output: re-entry condition check is performed first (per [registry.md#suppression-re-entry](registry.md#suppression-re-entry)). If a re-entry condition is met, transitions to `detected` per the field update rules — conditions by reason: (`weak_results`) `docs_epoch` change or any semantic hint resolving to the suppressed topic; (`redundant`) new leaf in same family, or any semantic hint resolving to the suppressed topic. If no re-entry condition is met, NO field update occurs — `last_seen_turn` is NOT updated and `consecutive_medium_count` is NOT modified. Re-entry condition check precedes all field update decisions for suppressed entries.
- Emits `facet_expansion` candidates when `extends_topic` hints resolve to `injected` topics with a facet not yet in `facets_injected` (cascade-resolved facet: hint-resolved → `pending_facets[0]` → `default_facet`; see [registry.md#semantic-hints](registry.md#semantic-hints)). Does NOT mutate `coverage.pending_facets` — emits an immediate `facet_expansion` candidate via [registry.md#scheduling-rules](registry.md#scheduling-rules) step 9. (`pending_facets` is only mutated by `contradicts_prior` hints.)
- Emits `pending_facet` candidates when an `injected` topic has non-empty `pending_facets` (from prior `contradicts_prior` hints) and the first pending facet is not yet in `facets_injected`.

### `build-packet` Automatic Suppression

When `--registry-file` is provided and `build-packet` returns empty output, it automatically writes a suppression state to the registry for the candidate topic. The suppression reason depends on *why* the output is empty:

- `weak_results` — search returned poor results (below quality threshold) or `search_docs` returned empty/error. The search signal is weak.
- `redundant` — search returned useful results but all `chunk_id` values were filtered by deduplication against `injected_chunk_ids`. The topic is already covered.

No flag is needed — empty output triggers suppression unconditionally when a registry is available. See [packets.md#failure-modes](packets.md#failure-modes) for the full decision tree.

**Suppression and deferral precedence:** If `build-packet` returns empty output, automatic suppression (either `weak_results` or `redundant`) writes to the registry. In this case, the target-match check has no packet to evaluate — skip the `--mark-deferred` path entirely. The topic is already handled by suppression. The mid-dialogue flow should check for empty output before proceeding to target-match.

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
| `facet` | `Facet` | Resolved facet for this candidate |
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

Shadow mode active/inactive is controlled by [delivery.md#shadow-mode-gate](delivery.md#shadow-mode-gate) (the gate specification, graduation.json schema, and kill criteria all live under the delivery authority). This data flow section assumes the mode has already been determined at dialogue start.

In **active mode**, packets built by the PREPARE cycle are prepended to follow-up prompts. In **shadow mode**, the PREPARE cycle runs identically but packets are NOT delivered — diagnostics record what CCDI *would have* injected.

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
│  │       If a per-topic build-packet --mark-injected exits non-zero, log the error
│  │       and continue with remaining entries — partial commit is acceptable
│  │       (uncommitted topics remain `detected` and are candidates for re-injection
│  │       in mid-dialogue turns)
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
| `ccdi_policy_snapshot`* | TBD | Phase B | *[Phase B — deferred]* Config snapshot for pinning CCDI tuning params during dialogue. Shape undefined — see [delivery.md#known-open-items](delivery.md#known-open-items). Not operative in Phase A. |

\*Deferred to Phase B. Shape undefined — see [delivery.md#known-open-items](delivery.md#known-open-items). Not operative in Phase A.

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
│   │       ├─ If active mode:
│   │       │   └─ Bash: python3 topic_inventory.py build-packet \
│   │       │            --results-file /tmp/ccdi_results_<id>.json \
│   │       │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │       │            --mode mid_turn \
│   │       │            --mark-deferred <topic_key> --deferred-reason target_mismatch \
│   │       │            --skip-build
│   │       └─ If shadow mode: no registry mutation (diagnostics record the intended deferral)
│   ├─ If candidates AND scout target exists:
│   │   (Scout target detection is agent-side: the codex-dialogue agent determines whether
│   │    execute_scout produced a scout candidate for the current turn from the scope_envelope
│   │    returned by process_turn. No CLI flag is involved — the CLI has no awareness of scout
│   │    state. The agent makes this determination and calls --mark-deferred scout_priority
│   │    when appropriate.)
│   │   ├─ If active mode:
│   │   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │   │            --mode mid_turn \
│   │   │            --mark-deferred <topic_key> --deferred-reason scout_priority \
│   │   │            --skip-build
│   │   └─ If shadow mode: no registry mutation (diagnostics record the intended deferral)
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
│       See [delivery.md#shadow-mode-gate](delivery.md#shadow-mode-gate) for the gate
│       definition, graduation.json schema, and kill criteria.
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

**Shadow-mode registry invariant:** In shadow mode, neither `--mark-injected` (Step 7.5) nor `--mark-deferred` (Step 5.5) mutates the registry. The prepare cycle runs to measure yield and latency for diagnostics, but the registry reflects only classifier-driven state (`detected`, `suppressed` via automatic build-packet suppression). Deferral state is recorded in diagnostics only. This prevents shadow-mode registry pollution from corrupting graduation kill-criteria metrics. See [decisions.md#normative-decision-constraints](decisions.md#normative-decision-constraints).

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
2. The `dump_index_metadata` tool implementation in `claude-code-docs` must document the CCDI consumer dependency (comment in the handler or a `CONSUMERS.md` file).

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `claude-code-docs` not installed | Tool availability check at preflight | Skip CCDI, surface note if topic detected |
| `search_docs` returns empty or errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` in [registry](registry.md) |
| `dialogue-turn` CLI fails mid-dialogue | Non-zero exit | Continue dialogue without mid-turn injection, preserve previous registry |

All failure modes degrade to "proceed without CCDI" per the [resilience principle](foundations.md#resilience-principle).
