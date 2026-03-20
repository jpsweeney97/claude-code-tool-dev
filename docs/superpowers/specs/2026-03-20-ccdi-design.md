# Claude Code Docs Injection (CCDI) — Design Document

**Date:** 2026-03-20
**Status:** Draft
**Author:** JP + Claude + Codex (7-turn collaborative dialogue)
**Location:** `packages/plugins/cross-model/`

---

## 1. Problem and Approach

### Problem

Codex has no training knowledge about Claude Code's extension ecosystem — hooks, skills, plugins, agents, MCP servers, slash commands, frontmatter schemas, event types. When consultations involve reviewing or designing Claude Code extensions, Codex gives generic advice because it doesn't understand the APIs or conventions.

### Approach

Automatically detect when a consultation involves Claude Code extensions and inject relevant documentation from the `claude-code-docs` MCP server into the Codex conversation.

Two injection phases:

- **Initial:** A dedicated subagent runs in parallel with existing `/dialogue` context-gatherers, queries `claude-code-docs`, and produces a compact reference injected into the Codex briefing.
- **Mid-dialogue:** The `codex-dialogue` agent detects new extension topics emerging in Codex's responses and injects targeted fact packets before the next turn.

Two modes:

| Mode | Entry point | Classifier | Registry | Mid-turn injection |
|------|------------|------------|----------|--------------------|
| **CCDI-lite** | `/codex` skill | One-shot | No | No |
| **Full CCDI** | `/dialogue` skill → `codex-dialogue` agent | Per-turn | Yes | Yes |

Detection is automatic (no manual flags). Injection is source-separated from repo evidence (`[ccdocs:...]` citations vs `@ path:line`). CCDI is an optional capability layer — consultations proceed without it if `claude-code-docs` is unavailable.

### Design Principles

| Principle | Meaning |
|-----------|---------|
| Detect aggressively, inject conservatively | High-recall classifier, precision-gated packet builder |
| Search wide, inject narrow | Initial subagent retrieves broadly, delivers 2–3 families |
| Auto-generated scaffold, curated overlay | Topic inventory stays current without full manual maintenance |
| Persist semantics, derive performance | Compiled inventory stores meaning; runtime matcher is separate |

---

## 2. Compiled Topic Inventory

A JSON artifact mapping Claude Code extension concepts to aliases, query plans, and doc references. Shared knowledge base for both the classifier and the query planner.

### Data Model (v1)

```
CompiledInventory
├── schema_version: "1"
├── built_at: ISO timestamp
├── docs_epoch: string | null        # reload/version marker from claude-code-docs
├── topics: Record<TopicKey, TopicRecord>
├── denylist: DenyRule[]
└── overlay_meta: { overlay_version, applied_rules[] }
```

### TopicRecord

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

### Alias

| Field | Type | Purpose |
|-------|------|---------|
| `text` | string | e.g., `"PreToolUse"`, `"updatedInput"` |
| `match_type` | `"exact" \| "phrase" \| "token" \| "regex"` | How to match against input |
| `weight` | 0.0–1.0 | Classification strength |
| `facet_hint` | Facet \| null | Which aspect this alias implies |
| `source` | `"generated" \| "overlay"` | Provenance |

Do NOT collapse Alias to plain strings — alias-level weights and facet hints are where the semantic power lives.

### QueryPlan

```
QueryPlan
├── default_facet: Facet
└── facets: Record<Facet, QuerySpec[]>
    └── QuerySpec: { q: string, category: string | null, priority: number }
```

Facets: `overview`, `schema`, `input`, `output`, `control`, `config`.

### DenyRule

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Rule identifier |
| `pattern` | string | e.g., `"overview"`, `"settings"` |
| `match_type` | `"token" \| "phrase" \| "regex"` | How to match |
| `action` | `"drop" \| "downrank"` | Eliminate or penalize |
| `penalty` | number | Weight reduction for downrank |
| `reason` | string | Why this term is problematic |

### DocRef

| Field | Type | Purpose |
|-------|------|---------|
| `chunk_id` | string | e.g., `"hooks#pretooluse-2"` |
| `category` | string | e.g., `"hooks"` |
| `source_file` | string | URL from docs server |

### Example Entry

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
  {"id": "drop-overview", "pattern": "overview", "match_type": "token", "action": "drop", "penalty": 1.0, "reason": "too generic"},
  {"id": "downrank-schema", "pattern": "schema", "match_type": "token", "action": "downrank", "penalty": 0.35, "reason": "facet word, not topic anchor"}
]
```

### Overlay Merge Semantics

- Scalar fields in `TopicRecord`: replace scaffold values.
- `aliases`, `canonical_refs`, `query_plan.facets[*]`: append + dedupe by normalized value, unless `replace_*` is explicitly set in the overlay rule.
- Overlay can: add topics, remove aliases, add deny rules, override weights.
- Generated scaffold builds the bulk. Overlay only fixes ambiguity and adds missing synonyms.

### Topic Hierarchy (Approximate Scope)

```
hooks                          skills                    plugins
├── hooks.pre_tool_use         ├── skills.skill_md       ├── plugins.manifest
├── hooks.post_tool_use        ├── skills.frontmatter    ├── plugins.structure
├── hooks.stop                 ├── skills.allowed_tools  └── plugins.mcp_integration
├── hooks.subagent_stop        └── skills.context_fork
├── hooks.session_start        agents                    mcp
├── hooks.session_end          ├── agents.subagents      ├── mcp.server_config
├── hooks.permission_request   └── agents.frontmatter    └── mcp.tools
├── hooks.notification         commands                  memory
└── hooks.pre_compact          └── commands.slash        └── memory.claude_md
```

### Lifecycle

- **Generation:** Auto-generated from `claude-code-docs` index metadata via `build_inventory.py` (MCP client calling `dump_index_metadata`).
- **Overlay:** Small curated JSON with denylist rules, alias fixes, weight overrides.
- **Persistence:** Compiled to `data/topic_inventory.json`. Loaded at plugin startup from last-known-good artifact (no live MCP dependency at startup).
- **Refresh:** Tied to `reload_docs` cycle — when docs refresh, inventory refreshes too.

---

## 3. Topic Classifier

Takes input text and resolves it to zero or more Claude Code extension topics with confidence levels and facet hints.

### Two-Stage Pipeline

**Stage 1: Candidate Generation (recall-biased)**

Linear scan over all aliases in the topics map against normalized input text. Produces a broad, intentionally noisy candidate list.

Matching rules by `match_type`:
- `exact` — case-sensitive substring match (e.g., `"PreToolUse"` matches verbatim)
- `phrase` — case-insensitive multi-word match (e.g., `"pre tool use"`)
- `token` — case-insensitive single-word match (e.g., `"hook"`)
- `regex` — compiled regex pattern (sparingly — for patterns like `SKILL\.md`)

Each candidate accumulates a score from matched aliases: sum of `alias.weight` values. Evaluation order: exact before phrase before token. Longer, more specific matches take precedence within the same match type. Repeated mentions of the same alias do NOT inflate the score.

**Stage 2: Ambiguity Resolution (precision-biased)**

Four deterministic rules:

| Rule | Effect | Example |
|------|--------|---------|
| Prefer leaf over family | Leaf with strong match absorbs parent family | `hooks.pre_tool_use` (1.0) absorbs `hooks` (0.4) |
| Generic terms are facet modifiers | Words like `schema`, `config`, `JSON` shift facet, not topic | `"schema"` pushes toward schema facet, doesn't create `plugins.manifest` |
| Collapse nested family matches | Multiple weak leaves in same family → elevate to family | Two weak hook leaves → single `hooks` family at overview facet |
| Suppress orphaned generics | Candidates from only generic/denied tokens with no anchor are dropped | `"settings"` alone → suppressed |

### Confidence Levels

| Level | Criteria |
|-------|----------|
| `high` | At least one exact/phrase match with weight ≥ 0.8 |
| `medium` | Cumulative score ≥ 0.5 from multiple aliases, or one match with weight 0.5–0.79 |
| `low` | Only token matches or generic terms, cumulative score < 0.5 |

### Output Structure

```
ClassifierResult
├── resolved_topics[]
│   ├── topic_key: TopicKey
│   ├── family_key: TopicKey
│   ├── coverage_target: "family" | "leaf"
│   ├── confidence: "high" | "medium" | "low"
│   ├── facet: Facet
│   ├── matched_aliases: { text, span, weight }[]
│   └── reason: string
└── suppressed_candidates[]
    ├── topic_key: TopicKey
    └── reason: string
```

### Injection Thresholds

| Phase | Injection fires when |
|-------|---------------------|
| Initial (pre-dialogue) | 1 high-confidence topic, OR 2+ medium-confidence in same family |
| Mid-dialogue | 1 high-confidence uncovered leaf, OR 1 medium-confidence leaf in 2+ consecutive turns, OR any uncovered topic Codex uses as actionable recommendation |
| `/codex` (CCDI-lite) | Same as initial |

Low-confidence detections are recorded in the topic registry but never trigger injection alone.

### Worked Example

Input: `"I'm building a PreToolUse hook that validates tool inputs against a schema"`

Stage 1 candidates:
```
hooks.pre_tool_use  score=1.6  (PreToolUse:1.0, hook:0.25, tool inputs:0.35)
hooks               score=0.4  (hook:0.4)
skills.frontmatter  score=0.18 (schema:0.18)
plugins.manifest    score=0.15 (schema:0.15)
```

Stage 2 resolution:
```
RESOLVED:  hooks.pre_tool_use  leaf  high  facet=schema
           reason: exact PreToolUse literal plus hook/input context

SUPPRESSED: hooks              → family collapsed under stronger leaf
            skills.frontmatter → generic schema token without family anchor
            plugins.manifest   → generic schema token without family anchor
```

---

## 4. Topic Registry

Per-conversation state machine tracking topic lifecycle. Prevents redundant injection and enables "materially new" detection.

### Entry Structure

```
TopicRegistryEntry
├── topic_key: TopicKey
├── family_key: TopicKey
├── state: "detected" | "looked_up" | "injected" | "suppressed"
├── first_seen_turn: number
├── last_seen_turn: number
├── last_lookup_turn: number | null
├── last_injected_turn: number | null
├── last_query_fingerprint: string | null
├── suppression_reason: "weak_results" | "cooldown" | "redundant" | null
└── coverage
    ├── overview_injected: boolean
    ├── facets_injected: Facet[]
    ├── family_context_available: boolean
    └── injected_chunk_ids: string[]
```

### State Transitions

```
absent ──→ detected ──→ looked_up ──→ injected
                              │
                              └──→ suppressed ──→ detected (re-entry)
```

| Transition | Trigger |
|-----------|---------|
| `absent → detected` | Classifier resolves a new topic |
| `detected → looked_up` | Scheduler selects topic for docs search |
| `looked_up → injected` | Search returns enough signal for a non-empty fact packet |
| `looked_up → suppressed` | Search results weak, redundant, or cooldown active |
| `suppressed → detected` | Stronger alias appears, new facet requested, or cooldown expires and topic reappears |

**Forward-only for `injected`:** Once injected, stays injected. If coverage is later insufficient, update `coverage` fields or create a new leaf entry — do not move backwards.

### Family vs Leaf Coverage

Family injection does NOT satisfy leaf-specific needs:

| Event | Registry Effect |
|-------|----------------|
| Inject `hooks` family overview | `hooks.coverage.overview_injected = true` |
| `hooks.post_tool_use` appears later | New leaf entry in `detected`, with `family_context_available = true` |
| Leaf lookup | `family_context_available` lowers retrieval breadth (skip overview, go to leaf-specific facet) |

### Scheduling Rules

Each turn, after classifier runs on Codex's latest response:

1. **Diff** new resolved topics against registry.
2. **Materially new** = one of:
   - New leaf under an already-covered family
   - Codex makes a prescriptive claim about a family-only topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Cooldown:** Max one new docs topic injection per turn.
4. **Schedule** highest-priority materially new topic for lookup.

### Session-Local Cache

| Cache | Key | Value | Purpose |
|-------|-----|-------|---------|
| Result cache | normalized query fingerprint | search results | Avoid re-searching identical queries |
| Packet cache | `(topic_key, facet)` | built fact packet | Avoid re-building identical packets |
| Negative cache | normalized query fingerprint | `weak` flag | Don't re-search queries that returned noise |

Cache is session-local — dies with the conversation. Include `docs_epoch` in cache keys if available.

---

## 5. Fact Packet Builder

Transforms docs search results into compact, citation-backed content for injection into Codex's context.

### Packet Structure

```
FactPacket
├── packet_kind: "initial" | "mid_turn"
├── topics: TopicKey[]
├── facts: FactItem[]
│   ├── mode: "paraphrase" | "snippet"
│   ├── facet: Facet
│   ├── text: string
│   └── refs: DocRef[]
└── token_estimate: number
```

### Verbatim vs Paraphrase

| Content type | Mode | Rationale |
|-------------|------|-----------|
| Field names, enum values, flags | `snippet` | Easy to misstate; exact syntax matters |
| JSON schema fragments | `snippet` | Structure is the information |
| Conceptual behavior, sequencing | `paraphrase` | Meaning > wording |
| Design implications, constraints | `paraphrase` | Needs contextualization |

Default is paraphrase. At most one snippet per mid-turn packet unless explicitly about schema details.

### Token Budgets

| Phase | Budget | Max topics | Max facts |
|-------|--------|------------|-----------|
| Initial | 600–1000 tokens | 2–3 families | 5–8 facts |
| Mid-turn | 250–450 tokens | 1 topic | 2–3 facts |

**Skip rule:** If top results score below quality threshold or are redundant with already-injected chunks, skip injection entirely. A weak packet is worse than no packet.

### Citation Format

```
[ccdocs:<chunk_id>]
```

Examples: `[ccdocs:hooks#pretooluse]`, `[ccdocs:skills#frontmatter]`. Source-separated from repo evidence (`@ path:line`). `source_file` and `category` stay in the internal packet for traceability but are not rendered inline.

### Rendered Output — Initial Injection

Placed in briefing under `## Material`, source-separated:

```markdown
## Material
### Claude Code Extension Reference
Detected topics: `hooks.pre_tool_use`, `hooks.post_tool_use`

- `PreToolUse` runs before a tool call and can allow, block, or modify it.
  [ccdocs:hooks#pretooluse]
- Output field `hookSpecificOutput.permissionDecision` controls
  allow/block/ask. [ccdocs:hooks#pretooluse]
- `updatedInput` can modify tool input before execution;
  `additionalContext` injects text into the conversation.
  [ccdocs:hooks#pretooluse-2]
- `PostToolUse` runs after successful tool completion; can replace
  output via `updatedMCPToolOutput`. [ccdocs:hooks#posttooluse]

Exact fields:
- `hookSpecificOutput.permissionDecision`
- `hookSpecificOutput.updatedInput`
- `hookSpecificOutput.additionalContext`
```

### Rendered Output — Mid-Dialogue Injection

Lighter format, prepended to follow-up prompt:

```markdown
Claude Code docs context:
- `PostToolUse` runs after a tool completes successfully.
  [ccdocs:hooks#posttooluse]
- For MCP tools, it can replace tool output via
  `updatedMCPToolOutput`. [ccdocs:hooks#posttooluse]
```

### Build Process

1. Receive search results from `claude-code-docs` (chunks with `chunk_id`, `category`, `snippet`, `content`).
2. Dedupe against `injected_chunk_ids` from the topic registry.
3. Rank by relevance to the resolved facet.
4. For each top result: decide paraphrase vs snippet based on content type.
5. Assemble into `FactPacket`, check against token budget.
6. If under quality threshold or budget exceeded with nothing useful: return empty (skip injection).
7. Render to markdown format appropriate to the phase.

---

## 6. Integration Architecture

### CLI Tool: `topic_inventory.py`

All deterministic logic lives in Python, exposed as coarse-grained workflow commands. Agents invoke via Bash with file-oriented I/O.

| Command | Input | Output | Used by |
|---------|-------|--------|---------|
| `classify --text-file <path> [--inventory <path>]` | Text file | `ClassifierResult` JSON (stdout) | Both modes |
| `dialogue-turn --registry-file <path> --text-file <path> --source codex\|user` | Text file + registry | Updated registry file + injection candidates JSON (stdout) | Full CCDI |
| `build-packet --results-file <path> --registry-file <path> --mode initial\|mid_turn [--mark-injected]` | Search results + registry | Rendered markdown (stdout) | Both modes |

Registry is a JSON file. The `codex-dialogue` agent passes it between calls — CLI reads, updates, and writes it back. No in-process state.

### Cross-Plugin Dependency

CCDI depends on `mcp__claude-code-docs__search_docs`. This is an optional dependency.

**Capability detection at preflight:**
1. Check if `search_docs` is available.
2. If available → CCDI enabled.
3. If unavailable + Claude Code topic detected → continue without CCDI, set `ccdi_status: unavailable`, surface note.
4. If unavailable + no Claude Code topic → do nothing.

### New Components

| Component | Type | Location |
|-----------|------|----------|
| `topic_inventory.py` | CLI tool | `scripts/topic_inventory.py` |
| `topic_inventory.json` | Data artifact | `data/topic_inventory.json` |
| `topic_overlay.json` | Data artifact | `data/topic_overlay.json` |
| `build_inventory.py` | Script (MCP client) | `scripts/build_inventory.py` |
| `ccdi-gatherer.md` | Subagent | `agents/ccdi-gatherer.md` |

All paths relative to `packages/plugins/cross-model/`.

### Modified Components

| Component | Change |
|-----------|--------|
| `/codex` skill | Add CCDI-lite: classify → search → build-packet → inject into briefing |
| `/dialogue` skill | Add ccdi-gatherer to parallel dispatch; merge output into `## Material` |
| `codex-dialogue` agent | Add per-turn dialogue-turn + build-packet loop; add `search_docs` to `tools:` |
| `claude-code-docs` MCP server | Add `dump_index_metadata` tool for inventory generation |

### Data Flow: CCDI-lite (`/codex`)

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

### Data Flow: Full CCDI (`/dialogue`)

**Pre-dialogue phase:**

```
User prompt
│
├─ /dialogue skill (Claude)
│  ├─ Bash: python3 topic_inventory.py classify --text-file <prompt>
│  ├─ If topics → dispatch ccdi-gatherer in parallel with context-gatherers
│  └─ Dispatch context-gatherer-code + context-gatherer-falsifier (as before)
│
├─ ccdi-gatherer (subagent, parallel)
│  ├─ tools: mcp__claude-code-docs__search_docs, Read, Bash
│  ├─ Receives: classified topics + query plans
│  ├─ Calls search_docs per topic (broad: families + sibling topics)
│  ├─ Bash: python3 topic_inventory.py build-packet --mode initial --mark-injected
│  └─ Returns: rendered markdown + serialized registry seed (JSON)
│
├─ Briefing assembly
│  ├─ ## Context
│  ├─ ## Material
│  │   ├─ Repo evidence (@ path:line)  ← from context-gatherers
│  │   └─ Claude Code Extension Reference ([ccdocs:...])  ← from ccdi-gatherer
│  └─ ## Question
```

**Mid-dialogue phase (per turn in codex-dialogue):**

```
codex-dialogue agent
│
├─ Send prompt to Codex via codex-reply
├─ Receive Codex response
├─ Write response to /tmp/ccdi_turn_<id>.txt
├─ Bash: python3 topic_inventory.py dialogue-turn \
│        --registry-file /tmp/ccdi_registry_<id>.json \
│        --text-file /tmp/ccdi_turn_<id>.txt --source codex
├─ Read candidates from stdout
├─ If candidates:
│   ├─ search_docs for each candidate's query plan
│   ├─ Write results to /tmp/ccdi_results_<id>.json
│   ├─ Bash: python3 topic_inventory.py build-packet \
│   │        --results-file /tmp/ccdi_results_<id>.json \
│   │        --registry-file /tmp/ccdi_registry_<id>.json \
│   │        --mode mid_turn --mark-injected
│   └─ Prepend rendered packet to next follow-up prompt
├─ Else: no injection this turn
└─ Continue dialogue loop
```

### Inventory Generation

```
dump_index_metadata (new claude-code-docs tool)
│
└─ build_inventory.py (MCP client)
   ├─ Connects to claude-code-docs server
   ├─ Calls dump_index_metadata → categories, headings, chunk IDs, code literals
   ├─ Generates TopicRecord scaffold
   ├─ Reads topic_overlay.json → merges denylist, alias fixes, weight overrides
   └─ Writes topic_inventory.json

Trigger: manual or tied to reload_docs cycle
```

### Untouched Components

- `codex_consult.py` — transport layer
- `codex_shim.py` — MCP interface
- Context-injection pipeline (`process_turn`/`execute_scout`) — repo evidence
- `codex_guard.py` — safety hooks
- `retrieve_learnings.py` — learning injection (separate concern)

---

## 7. Error Handling

### Failure Mode Table

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `claude-code-docs` not installed | Tool availability check | Skip CCDI, surface note if topic detected |
| `topic_inventory.json` missing/corrupt | CLI non-zero exit / parse error | Skip CCDI, log warning |
| `classify` returns no topics | Empty resolved_topics | Proceed without CCDI |
| `search_docs` returns empty/errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` |
| `build-packet` produces empty output | Below quality threshold | Skip injection, mark suppressed |
| `dialogue-turn` CLI fails mid-dialogue | Non-zero exit | Continue dialogue without mid-turn injection, preserve previous registry |
| Registry file missing/corrupt | CLI error | Reinitialize empty registry, lose coverage history |
| Inventory stale | `docs_epoch` mismatch | Use stale with diagnostics warning |

### Design Principle

CCDI failures never block consultations. Every failure path degrades to "consultation proceeds without extension docs" — the current behavior. The system adds value when it works; it's invisible when it doesn't.

### Diagnostics

```json
{
  "ccdi": {
    "status": "active | unavailable | no_topics | error",
    "topics_detected": ["hooks.pre_tool_use"],
    "topics_injected": ["hooks.pre_tool_use"],
    "packets_injected": 2,
    "total_tokens_injected": 680,
    "search_failures": 0,
    "inventory_epoch": "2026-03-20T..."
  }
}
```

---

## 8. Testing Strategy

### Unit Tests: `test_topic_inventory.py`

**Classifier tests:**

| Test | Verifies |
|------|----------|
| Exact alias → high confidence | `"PreToolUse"` → `hooks.pre_tool_use`, high |
| Phrase match with facet hint | `"pre tool use"` → facet=overview |
| Generic token alone suppressed | `"schema"` alone → no resolved topics |
| Generic shifts facet with anchor | `"PreToolUse schema"` → facet=schema |
| Leaf absorbs parent family | `"PreToolUse hook"` → leaf only |
| Weak leaves collapse to family | Two low-weight hook leaves → `hooks` family |
| Denylist drop | `"overview"` → dropped |
| Denylist downrank | `"settings"` → weight reduced |
| No matches → empty | `"fix the database query"` → empty |
| Multiple families detected | `"PreToolUse hook and SKILL.md frontmatter"` → two topics |
| Normalization variants | `PreToolUse`, `pretooluse`, `SKILL.md`, backticked forms |
| Alias collision tiebreak | Same token in two topics → deterministic winner |
| False-positive contexts | `"React hook"`, `"webpack plugin"` → no CCDI topics |
| Missing-facet fallback | Requested facet missing → falls back to `default_facet` |
| Multi-leaf same family | Both `PreToolUse` and `PostToolUse` in one input |
| Repeated mentions don't inflate | `"PreToolUse PreToolUse PreToolUse"` → same score as one mention |

**Registry tests:**

| Test | Verifies |
|------|----------|
| New topic → detected | First appearance starts in detected |
| Happy path: detected → looked_up → injected | Full forward transition |
| Candidate selection after detection | Detected topic in candidates |
| Injected not re-selected | After mark-injected → not in candidates |
| Suppressed: weak results | looked_up → suppressed on empty search |
| Suppressed: redundant | looked_up → suppressed when coverage exists |
| Suppressed re-enters on stronger signal | suppressed → detected |
| Suppressed re-enters on cooldown expiry | suppressed → detected after N turns |
| Cooldown prevents same-turn re-injection | Max one new topic per turn |
| Family injection doesn't cover leaves | Inject hooks → hooks.post_tool_use still detected |
| Leaf inherits family_context_available | Flag set after family injected |
| Leaf then family tracked independently | Both have separate coverage |
| Facet evolution | overview injected, schema still pending → new lookup |
| Idempotent mark-injected | Same packet twice doesn't corrupt |
| Registry corruption recovery | Malformed JSON → reinitialize empty |

**Packet builder tests:**

| Test | Verifies |
|------|----------|
| Initial packet within budget | 600–1000 tokens |
| Mid-turn packet within budget | 250–450 tokens |
| Empty results → no packet | Skip, not empty markdown |
| Duplicate chunk IDs filtered | Already-injected excluded |
| Citation format | `[ccdocs:<chunk_id>]` |
| Snippet mode for field names | Exact identifiers use snippet |
| Paraphrase mode for concepts | Behavioral descriptions use paraphrase |
| Too-large snippet truncated | Graceful handling under budget pressure |

**CLI integration tests:**

| Test | Verifies |
|------|----------|
| `classify` file I/O round-trip | Reads text file, returns valid JSON |
| `dialogue-turn` updates registry file | State persistence across calls |
| `build-packet --mark-injected` updates registry | Side-effect correctness |
| Missing inventory → non-zero exit | Graceful failure |
| Malformed text → non-zero exit | Input validation |
| stdout/stderr separation | JSON on stdout only, errors on stderr |

### Boundary Contract Tests: `test_ccdi_contracts.py`

Tests that verify field names, enum values, and schema shapes agree across component boundaries. Guards against silent downgrade.

| Boundary | Contract verified |
|----------|-------------------|
| Inventory → classifier | `topic_key`, `family_key`, alias normalization, denylist shapes |
| Classifier → registry | `confidence`, `facet`, `coverage_target`, `topic_key` enums |
| Registry → search orchestration | Candidates produce valid query specs and category hints |
| Search results → packet builder | Required fields present (`chunk_id`, `category`, `content`), deduplication, ranking stability |
| Packet builder → prompt assembler | Citation format, valid markdown, token budget enforced |
| CLI → agents | Exit codes, stdout JSON contract, stderr behavior, file-path semantics |

### Integration Tests

| Test | Verifies |
|------|----------|
| ccdi-gatherer produces valid markdown | End-to-end initial injection |
| `/codex` CCDI-lite briefing injection | Briefing contains `### Claude Code Extension Reference` |
| Full dialogue turn with mid-turn injection | Registry persists across turns |
| Graceful degradation without `search_docs` | Consultation proceeds, `ccdi_status: unavailable` |
| Malformed search results handled | Missing `chunk_id`, empty content → skip, not crash |
| Inventory schema version mismatch | Older inventory → warning, not crash |

### Inventory Tests: `test_build_inventory.py`

| Test | Verifies |
|------|----------|
| Scaffold generation from metadata | Topics, aliases, query plans populated |
| Overlay merge: scalar replace | Override canonical_label |
| Overlay merge: array append + dedupe | New alias added, duplicate ignored |
| Overlay references unknown topic | Warning, not crash |
| Denylist applied | Generic terms dropped/downranked |
| Output matches CompiledInventory schema | Schema validation |

---

## 9. Codex Consultation Summary

This design was developed through a 7-turn Codex dialogue (thread: `019d0c24-29c9-7bf1-a2f4-d50f3056553b`).

| Turn | Topic | Key decision |
|------|-------|-------------|
| 1 | Approach selection | Approach 1 (subagent + scout) recommended, but don't put DocSearch in scout pipeline |
| 2 | Component design | Hierarchical topic inventory, topic registry with lifecycle state, compact fact packets |
| 3 | Optimization | Detect aggressively/inject conservatively, search wide/inject narrow, session-local caching |
| 4 | Spec-level detail | Full data models, classifier walkthrough, registry transition rules, packet format |
| 5 | Simplification | Drop inverted indexes, keep alias objects, persist semantics / derive performance |
| 6 | Integration gaps | Coarse-grained CLI commands, optional cross-plugin dependency, MCP client for inventory, CCDI-lite for /codex |
| 7 | Testing review | Boundary contract tests, false-positive contexts, registry partial-coverage, external failure paths |
