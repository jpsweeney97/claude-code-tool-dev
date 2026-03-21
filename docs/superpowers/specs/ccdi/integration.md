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
| `dialogue-turn --registry-file <path> --text-file <path> --source codex\|user [--semantic-hints-file <path>] [--config <path>]` | Text file + registry + optional hints | Updated registry file + injection candidates JSON (stdout) | Full CCDI |
| `build-packet --results-file <path> [--registry-file <path>] --mode initial\|mid_turn [--coverage-target family\|leaf] [--mark-injected] [--mark-deferred <topic_key> --deferred-reason <reason>] [--skip-build] [--config <path>]` | Search results + optional registry | Rendered markdown (stdout); registry updated in-place if `--mark-injected` or `--mark-deferred` | Both modes |

All commands accept `--config <path>` to load [`ccdi_config.json`](data-model.md#configuration-ccdi_configjson). If omitted, uses built-in defaults. Registry is a JSON file containing only durable states (see [registry.md](registry.md#durable-vs-attempt-local-states)). Attempt-local states (`looked_up`, `built`) exist within a single CLI invocation and are never written to the file.

**`--registry-file` optionality on `build-packet`:** When omitted (CCDI-lite mode), deduplication against prior injections is skipped and `--mark-injected` / `--mark-deferred` are no-ops. CCDI-lite has no registry — each invocation builds a fresh packet without coverage history.

**`--skip-build` flag:** When passed with `--mark-deferred`, skips packet construction and only writes deferred state to the registry. This avoids redundant rebuilds when the target-match check already determined the packet is not target-relevant. `--skip-build` is only valid with `--mark-deferred`; ignored otherwise. When `--skip-build` is passed with `--mark-deferred`, `--results-file` is not required — no packet construction occurs.

**`--coverage-target family|leaf` flag:** Required when `--mark-injected` is passed with `--registry-file`. Determines whether `coverage.overview_injected` is set (when `family` + facet=overview). Omitted in CCDI-lite mode (no registry).

**`--mark-injected` registry side-effects:** When `--mark-injected` is passed with `--registry-file`, the following fields are updated per the [Field Update Rules](registry.md#field-update-rules): `state` → `injected`, `last_injected_turn`, `last_query_fingerprint`, `coverage.injected_chunk_ids` (appended from built packet's chunk IDs), `coverage.facets_injected` (appended), `coverage.pending_facets` (served facet removed if present), `consecutive_medium_count` ← 0. When `--coverage-target family` and `facet=overview`: additionally `coverage.overview_injected` ← true.

**`build-packet` automatic suppression:** When `--registry-file` is provided and `build-packet` returns empty output (below quality threshold), it automatically writes `suppressed: weak_results` to the registry for the candidate topic. This prevents repeated failed lookups with no backoff. No flag is needed — empty output triggers suppression unconditionally when a registry is available.

**Suppression and deferral precedence:** If `build-packet` returns empty output (below quality threshold), automatic suppression writes `suppressed: weak_results` to the registry. In this case, the target-match check has no packet to evaluate — skip the `--mark-deferred` path entirely. The topic is already handled by suppression. The mid-dialogue flow should check for empty output before proceeding to target-match.

**`dialogue-turn` candidates JSON schema:** The `dialogue-turn` command writes injection candidates to stdout as a JSON array:

```json
[
  {
    "topic_key": "hooks.pre_tool_use",
    "family_key": "hooks",
    "facet": "schema",
    "confidence": "high",
    "coverage_target": "leaf",
    "query_plan": {"default_facet": "overview", "facets": {"schema": [...]}}
  }
]
```

Each element contains: `topic_key` (string), `family_key` (string), `facet` (Facet — the resolved facet for this candidate), `confidence` (`"high" | "medium"` — low-confidence topics are tracked in the registry but excluded from injection candidates; see [classifier.md#injection-thresholds](classifier.md#injection-thresholds)), `coverage_target` (`"family" | "leaf"` — the classifier's resolved coverage target for this candidate), and `query_plan` (the topic's QueryPlan from the inventory, for the agent to execute search). An empty array means no injection candidates this turn.

**`--source codex|user` on `dialogue-turn`:** `codex` = classifier runs on Codex's response text; `user` = classifier runs on the user's turn text. Both sources use the same two-stage pipeline. Scheduling behavior by source is defined in [registry.md#scheduling-rules](registry.md#scheduling-rules); see [delivery.md#known-open-items](delivery.md#known-open-items) for deferred divergence.

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
│  ├─ If topics:
│  │   ├─ search_docs per topic's query plan (1–2 queries)
│  │   ├─ Write results to /tmp/ccdi_results_<id>.json
│  │   ├─ Bash: python3 topic_inventory.py build-packet \
│  │   │        --results-file /tmp/ccdi_results_<id>.json --mode initial
│  │   └─ Inject rendered markdown into ## Material > ### Claude Code Extension Reference
│  └─ Continue normal /codex briefing assembly
```

## Data Flow: Full CCDI (`/dialogue`)

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
│  ├─ Bash: python3 topic_inventory.py build-packet --mode initial
│  │        (NO --mark-injected — seed entries stay in `detected` state)
│  └─ Returns: rendered markdown block + sentinel-wrapped registry seed
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
├─ Initial CCDI COMMIT (after briefing send confirmed)
│  ├─ If briefing was sent successfully:
│  │   └─ Bash: python3 topic_inventory.py build-packet \
│  │            --results-file /tmp/ccdi_results_<id>.json \
│  │            --registry-file /tmp/ccdi_registry_<id>.json \
│  │            --mode initial --coverage-target <target> --mark-injected
│  └─ If briefing send failed: no commit (seed entries remain `detected`)
│
├─ Registry seed handoff
│  ├─ /dialogue skill extracts JSON from ccdi-gatherer's sentinel block
│  ├─ Writes registry seed to /tmp/ccdi_registry_<id>.json
│  └─ Passes ccdi_seed envelope field to codex-dialogue delegation
```

### Registry Seed Handoff

The `ccdi-gatherer` subagent emits its [registry seed](data-model.md#registryseed) as a sentinel-wrapped JSON block at the end of its output:

```
<!-- ccdi-registry-seed -->
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1"}
<!-- /ccdi-registry-seed -->
```

The `/dialogue` skill:

1. Extracts JSON between the sentinels from the ccdi-gatherer's output.
2. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`).
3. Passes the file path as `ccdi_seed: <path>` in the delegation envelope to `codex-dialogue`.

The `codex-dialogue` agent detects the `ccdi_seed` field and uses the file as its initial `--registry-file` for the mid-dialogue CCDI loop. If the field is absent, CCDI mid-dialogue is disabled for the session.

### Delegation Envelope Fields

The `/dialogue` skill passes these optional fields to `codex-dialogue`:

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `ccdi_seed` | file path (string) | ccdi-gatherer output | Initial registry file for mid-dialogue CCDI loop. Absent → mid-dialogue CCDI disabled. |
| `scope_envelope` | object | context-gatherers | Existing field — repo evidence scope. |
| `ccdi_debug` | boolean \| absent | `/dialogue` skill | When `true`, `codex-dialogue` emits `ccdi_trace` in its output. Absent or `false` → no trace. Testing-only; see [delivery.md#debug-gated-ccdi_trace](delivery.md#debug-gated-ccdi_trace) for trace schema. |

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
│   │   │        --mode mid_turn --coverage-target <target>   (NO --mark-injected yet)
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
├─ [Step 6: send follow-up to Codex with staged CCDI packet prepended]
│
├─ Step 7.5: CCDI COMMIT (after send confirmed)
│   ├─ If packet was sent:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --results-file /tmp/ccdi_results_<id>.json \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --mode mid_turn --coverage-target <target> --mark-injected
│   └─ If send failed or packet was not staged: no commit
│
└─ Continue dialogue loop
```

**Key invariant:** `--mark-injected` is called only after the packet-containing prompt has been confirmed sent to Codex. This applies to both paths: the initial injection commit (after briefing send in `/dialogue`) and the mid-dialogue commit (Step 7.5 after follow-up send in `codex-dialogue`). This prevents the registry from recording injection for packets that were staged but never delivered (e.g., if the briefing or follow-up prompt failed).

### Target-Match Predicate

The **composed follow-up target** is the follow-up question text that `codex-dialogue` has composed for the current turn (the text that will be sent to Codex via `codex-reply`). This text exists after Step 4 (composition) and before Step 5.5 (CCDI PREPARE).

The target-match check determines whether a CCDI packet is relevant to the composed question. A packet is **target-relevant** when at least one of the packet's `topics` appears as a substring (case-insensitive) in the composed follow-up text, OR the packet's primary `facet` matches a concept referenced in the follow-up text (determined by running the classifier on the follow-up text and checking for topic overlap).

**CLI interface:** The target-match check is performed by the agent, not the CLI. The agent:
1. Reads the `build-packet` stdout (rendered markdown).
2. Compares the packet's topic coverage against the composed follow-up text.
3. If not target-relevant: invokes `build-packet --mark-deferred --deferred-reason target_mismatch --skip-build`.

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
