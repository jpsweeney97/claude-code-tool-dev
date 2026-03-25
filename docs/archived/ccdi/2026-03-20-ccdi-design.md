# Claude Code Docs Injection (CCDI) — Design Document

**Date:** 2026-03-20
**Status:** Draft (reviewed)
**Author:** JP + Claude + Codex (7-turn design dialogue + 6-turn review dialogue)
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
| CCDI is premise enrichment, not retargeting | CCDI adds context to the follow-up prompt; it never changes what the agent asks Codex about |
| Scout evidence beats CCDI evidence | When context-injection has a scout candidate at the same boundary, CCDI yields |

### Rollout Strategy

Ship in two phases to isolate risk:

| Phase | Scope | Risk profile |
|-------|-------|-------------|
| **Phase A** | Initial CCDI only (ccdi-gatherer subagent + CCDI-lite) | Low — clean additive feature, no interaction with existing turn loop |
| **Phase B** | Mid-dialogue CCDI (per-turn prepare/commit in codex-dialogue) | Higher — control-plane duplication risk, source hierarchy inversion potential |

Phase B enters **shadow mode** first: the prepare/commit cycle runs and emits diagnostics but does NOT inject packets into the follow-up prompt. Shadow mode has kill criteria:

- Abort if `effective_prepare_yield` < 40% — where yield = (prepared AND target-relevant AND surviving precedence) / total prepared. Low yield means CCDI is doing work that doesn't reach Codex.
- Abort if average per-turn CCDI latency (prepare + commit) exceeds 500ms
- Abort if false-positive injection rate (CCDI fires on non-Claude-Code topics) exceeds 10%

Secondary diagnostic (not a hard kill): `relevant_but_scout_deferred_rate` — high values indicate healthy scout precedence, not CCDI failure.

Graduate from shadow to active when kill criteria are clear across 10+ shadow dialogues.

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
├── overlay_meta: { overlay_version, overlay_schema_version, applied_rules[] }
└── merge_semantics_version: "1"     # version of the overlay merge algorithm
```

### Version Axes

Three independent version axes prevent coupled evolution:

| Axis | Field | What changes | Who changes it |
|------|-------|-------------|---------------|
| Inventory schema | `schema_version` | TopicRecord fields, Alias structure, DenyRule shape | Code change (Python) |
| Overlay schema | `overlay_meta.overlay_schema_version` | Overlay file format, supported operations | Code change (Python) |
| Merge semantics | `merge_semantics_version` | How overlay operations apply to inventory | Code change (Python) |

`build_inventory.py` validates compatibility between all three axes at merge time. On mismatch: fail loudly with specific version pair and required action. Do NOT silently fall back — overlays are curated artifacts, and silent incompatibility corrupts human-maintained data.

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

**Penalty application:** `downrank` reduces the individual alias weight before summing into the topic score. If alias `A` has weight 0.6 and matches denylist rule with penalty 0.35, the effective weight is `0.6 - 0.35 = 0.25`. Negative effective weights are clamped to 0.

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
- **Overlay:** Small curated JSON with denylist rules, alias fixes, weight overrides. Has its own `overlay_schema_version` validated at merge time.
- **Persistence:** Compiled to `data/topic_inventory.json`. Loaded at plugin startup from last-known-good artifact (no live MCP dependency at startup).
- **Refresh trigger:** `build_inventory.py` runs automatically as a post-reload hook when `reload_docs` is called and `docs_epoch` has changed since the last build. Also runnable manually: `python3 scripts/build_inventory.py [--force]`. The `--force` flag rebuilds even if `docs_epoch` matches.
- **Dialogue pinning:** A running dialogue uses the inventory snapshot loaded at dialogue start. Inventory refreshes mid-dialogue do NOT affect active conversations — the classifier operates on a pinned copy for the dialogue lifetime.

### Configuration: `ccdi_config.json`

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

The overlay can override config values via an optional `config_overrides` section — same merge semantics as topic overrides. This keeps all tuning in data files, not Python code.

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

Thresholds are configurable via `ccdi_config.json` → `classifier`. Defaults shown:

| Level | Criteria | Config key |
|-------|----------|-----------|
| `high` | At least one exact/phrase match with weight ≥ 0.8 | `confidence_high_min_weight` |
| `medium` | Cumulative score ≥ 0.5 from multiple aliases, or one match with weight 0.5–0.79 | `confidence_medium_min_score`, `confidence_medium_min_single_weight` |
| `low` | Only token matches or generic terms, cumulative score < 0.5 | (below medium thresholds) |

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

Thresholds are configurable via `ccdi_config.json` → `injection`. Defaults shown:

| Phase | Injection fires when | Config keys |
|-------|---------------------|------------|
| Initial (pre-dialogue) | 1 high-confidence topic, OR 2+ medium-confidence in same family | `initial_threshold_high_count`, `initial_threshold_medium_same_family_count` |
| Mid-dialogue | 1 high-confidence uncovered leaf, OR 1 medium-confidence leaf in 2+ consecutive turns, OR agent provides semantic hint (see §4) | `mid_turn_consecutive_medium_turns` |
| `/codex` (CCDI-lite) | Same as initial | (same keys) |

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

### Durable vs Attempt-Local States

Only **durable states** are persisted to the registry file. Attempt-local states exist within a single CLI invocation and are never written to disk.

| State | Durability | Meaning |
|-------|-----------|---------|
| `detected` | Durable | Classifier found this topic; not yet looked up |
| `injected` | Durable | Packet was sent to Codex and send was confirmed |
| `suppressed` | Durable | Lookup returned weak/redundant results; will not re-attempt unless signal strengthens |
| `deferred` | Durable | Valid candidate that yielded to higher priority (scout evidence or cooldown); has TTL for re-evaluation |
| `looked_up` | Attempt-local | Search completed; deciding packet eligibility (not persisted) |
| `built` | Attempt-local | Packet built but not yet sent (not persisted) |

`injected` commits only after the agent observes successful send (the follow-up prompt containing the packet was delivered to Codex). If send fails, the topic reverts to `detected` — not `injected`.

### State Transitions

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
| `deferred → detected` | TTL expires (configurable, default 3 turns) and topic reappears in classifier output |
| `suppressed → detected` | Stronger alias appears or new facet requested |

**Forward-only for `injected`:** Once injected, stays injected. If coverage is later insufficient, update `coverage` fields or create a new leaf entry — do not move backwards.

**`deferred` vs `suppressed`:** These are semantically distinct. `suppressed` means "we looked and found nothing useful" — the evidence is weak. `deferred` means "this is a valid candidate that lost to higher priority" — the evidence may be strong but timing was wrong. Deferred reasons: `cooldown` (turn budget exhausted), `scout_priority` (scout evidence took precedence), `target_mismatch` (packet doesn't support the composed follow-up target). Deferred topics get automatic re-evaluation via TTL; suppressed topics require new signal.

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
   - Agent provides a `semantic_hint` (see below) referencing a claim that touches a detected topic
   - Codex contradicts or extends an injected topic (coverage gap)
3. **Cooldown:** Max one new docs topic injection per turn (configurable via `ccdi_config.json` → `injection.cooldown_max_new_topics_per_turn`).
4. **Scout priority:** If context-injection has a scout candidate targeting the same code boundary, defer the CCDI candidate (→ `deferred` state with `scout_priority` reason).
5. **Schedule** highest-priority materially new topic for lookup.

### Semantic Hints

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

The CLI uses hints as scheduling signals — a `prescriptive` hint on a detected-but-not-yet-injected topic elevates it to "materially new." The CLI classifies `claim_excerpt` through its standard two-stage pipeline to resolve the topic key. The agent never emits `topic_key` values — that would couple it to the CCDI taxonomy.

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

**Clarification:** Both modes are deterministic operations in the CLI — no LLM involvement.
- `snippet`: extract verbatim text from the search result's `content` or `snippet` field, trim to budget.
- `paraphrase`: select the most relevant sentence(s) from the search result's `content` field based on facet keyword overlap, trim to budget. This is extractive selection, not generative rewriting. The CLI picks passages; it does not rephrase them.

### Token Budgets

All budget values are configurable via `ccdi_config.json` → `packets`. Defaults shown:

| Phase | Budget | Max topics | Max facts | Config keys |
|-------|--------|------------|-----------|------------|
| Initial | 600–1000 tokens | 2–3 families | 5–8 facts | `initial_token_budget_*`, `initial_max_*` |
| Mid-turn | 250–450 tokens | 1 topic | 2–3 facts | `mid_turn_token_budget_*`, `mid_turn_max_*` |

**Quality threshold:** Skip injection when the best search result's relevance score is below `quality_min_result_score` (default: 0.3) OR when fewer than `quality_min_useful_facts` (default: 1) facts survive deduplication and budget constraints. A weak packet is worse than no packet.

**Source hierarchy:** CCDI packets are premise enrichment — they provide background knowledge, not primary evidence. When both CCDI docs content and repo evidence (`@ path:line`) address the same concept, repo evidence takes precedence. The packet builder must not produce rhetorically dominant content that could override Codex's assessment of repo-specific code.

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
| `classify --text-file <path> [--inventory <path>] [--config <path>]` | Text file | `ClassifierResult` JSON (stdout) | Both modes |
| `dialogue-turn --registry-file <path> --text-file <path> --source codex\|user [--semantic-hints-file <path>] [--config <path>]` | Text file + registry + optional hints | Updated registry file + injection candidates JSON (stdout) | Full CCDI |
| `build-packet --results-file <path> --registry-file <path> --mode initial\|mid_turn [--mark-injected] [--config <path>]` | Search results + registry | Rendered markdown (stdout) | Both modes |

All commands accept `--config <path>` to load `ccdi_config.json`. If omitted, uses built-in defaults. Registry is a JSON file containing only durable states (§4). Attempt-local states (`looked_up`, `built`) exist within a single CLI invocation and are never written to the file.

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
| `ccdi_config.json` | Config artifact | `data/ccdi_config.json` |
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
│  └─ Returns: rendered markdown block + sentinel-wrapped registry seed
│
├─ Briefing assembly
│  ├─ ## Context
│  ├─ ## Material
│  │   ├─ Repo evidence (@ path:line)  ← from context-gatherers
│  │   └─ Claude Code Extension Reference ([ccdocs:...])  ← from ccdi-gatherer
│  └─ ## Question
│
├─ Registry seed handoff
│  ├─ /dialogue skill extracts JSON from ccdi-gatherer's sentinel block
│  ├─ Writes registry seed to /tmp/ccdi_registry_<id>.json
│  └─ Passes ccdi_seed envelope field to codex-dialogue delegation
```

### Registry Seed Handoff

The `ccdi-gatherer` subagent emits its registry seed as a sentinel-wrapped JSON block at the end of its output:

```
<!-- ccdi-registry-seed -->
{"entries": [...], "docs_epoch": "...", "inventory_snapshot_version": "1"}
<!-- /ccdi-registry-seed -->
```

The `/dialogue` skill:
1. Extracts JSON between the sentinels from the ccdi-gatherer's output
2. Writes the seed to a temp file (`/tmp/ccdi_registry_<id>.json`)
3. Passes the file path as `ccdi_seed: <path>` in the delegation envelope to `codex-dialogue`

The `codex-dialogue` agent detects the `ccdi_seed` field and uses the file as its initial `--registry-file` for the mid-dialogue CCDI loop. If the field is absent, CCDI mid-dialogue is disabled for the session.

This follows the existing delegation envelope pattern (parallel to `scope_envelope`). The registry seed is NOT embedded in the briefing text — it is a separate envelope field. The consultation contract §6 does not need modification: `ccdi_seed` is an optional additive field, not a change to the existing envelope schema.

**Mid-dialogue phase (per turn in codex-dialogue):**

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
│   │   │        --mode mid_turn   (NO --mark-injected yet)
│   │   ├─ Target-match check: verify staged packet supports the composed follow-up target
│   │   └─ If target-relevant: stage for prepending. If not: defer (target_mismatch)
│   ├─ If candidates AND scout target exists: defer CCDI (scout wins)
│   └─ If no candidates: no CCDI this turn
│
├─ [Step 6: send follow-up to Codex with staged CCDI packet prepended]
│
├─ Step 7.5: CCDI COMMIT (after send confirmed)
│   ├─ If packet was sent:
│   │   └─ Bash: python3 topic_inventory.py build-packet \
│   │            --results-file /tmp/ccdi_results_<id>.json \
│   │            --registry-file /tmp/ccdi_registry_<id>.json \
│   │            --mode mid_turn --mark-injected
│   └─ If send failed or packet was not staged: no commit
│
└─ Continue dialogue loop
```

**Key invariant:** `--mark-injected` is called only in the commit phase (Step 7.5), after the packet has been confirmed sent. This prevents the registry from recording injection for packets that were staged but never delivered (e.g., if the follow-up prompt was superseded by scout evidence or the Codex call failed).

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

Trigger: automatic post-reload hook (when docs_epoch changes) or manual (--force)
```

### `dump_index_metadata` Response Schema

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

`build_inventory.py` consumes this to generate topic scaffolds: category names → family topics, headings → leaf topics, code literals → exact aliases, distinctive terms → phrase/token aliases.

**Cross-package contract:** This response schema is a dependency of the `cross-model` plugin, but `dump_index_metadata` is implemented in `packages/mcp-servers/claude-code-docs/` (a separate TypeScript package). To prevent silent breakage:
1. A boundary contract test in `test_ccdi_contracts.py` validates the response shape against expected fields.
2. The `dump_index_metadata` tool implementation in `claude-code-docs` must document the CCDI consumer dependency (comment in the handler or a `CONSUMERS.md` file).

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
| `ccdi_config.json` missing | CLI fallback | Use built-in defaults, log info |
| `ccdi_config.json` corrupt/invalid | CLI parse error | Use built-in defaults, log warning |
| `classify` returns no topics | Empty resolved_topics | Proceed without CCDI |
| `search_docs` returns empty/errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` |
| `build-packet` produces empty output | Below quality threshold | Skip injection, mark suppressed |
| Packet staged but send fails | Agent observes send failure | No commit (topic stays `detected`, not `injected`) |
| Scout takes priority over CCDI candidate | Scout target exists for turn | Defer CCDI candidate (→ `deferred: scout_priority`) |
| `dialogue-turn` CLI fails mid-dialogue | Non-zero exit | Continue dialogue without mid-turn injection, preserve previous registry |
| Registry file missing/corrupt | CLI error | Reinitialize empty registry, lose coverage history |
| Inventory stale | `docs_epoch` mismatch | Use stale with diagnostics warning |
| Semantic hints file malformed | CLI parse warning | Ignore hints, proceed with classifier-only scheduling |
| Version axis mismatch at build time | `build_inventory.py` validation | Fail loudly with version pair and required action |

### Design Principle

CCDI failures never block consultations. Every failure path degrades to "consultation proceeds without extension docs" — the current behavior. The system adds value when it works; it's invisible when it doesn't.

### Diagnostics

Per-dialogue summary, accumulated across turns and emitted once at dialogue end via the analytics emitter:

```json
{
  "ccdi": {
    "status": "active | shadow | unavailable | no_topics | error",
    "phase": "initial_only | full",
    "topics_detected": ["hooks.pre_tool_use"],
    "topics_injected": ["hooks.pre_tool_use"],
    "topics_deferred": ["skills.frontmatter"],
    "topics_suppressed": [],
    "packets_prepared": 3,
    "packets_injected": 2,
    "packets_deferred_scout": 1,
    "total_tokens_injected": 680,
    "semantic_hints_received": 1,
    "search_failures": 0,
    "inventory_epoch": "2026-03-20T...",
    "config_source": "data/ccdi_config.json | defaults"
  }
}
```

In shadow mode (Phase B rollout), `packets_prepared` accumulates but `packets_injected` stays 0. The shadow diagnostics reveal what CCDI *would have* injected for kill-criteria evaluation.

---

## 8. Testing Strategy

### Three-Layer Approach

| Layer | What it tests | How |
|-------|--------------|-----|
| **Unit tests** | CLI deterministic logic (classifier, registry, packet builder) | Standard pytest, full coverage of data shapes and state transitions |
| **Replay harness** | Agent integration (prepare/commit loop, semantic hints, tool-call sequence) | Structured `ccdi_trace` + assertion on tool-call sequence and outcomes, not prose |
| **Shadow mode** | End-to-end quality (false positives, source hierarchy, latency) | Phase B rollout with kill criteria (see §1 Rollout Strategy) |

### Debug-Gated `ccdi_trace`

The `codex-dialogue` agent emits a structured trace when CCDI is active, gated by a `ccdi_debug` flag in the delegation envelope:

```json
{
  "turn": 3,
  "classifier_result": {"resolved_topics": [...], "suppressed": [...]},
  "semantic_hints": [{"claim_index": 3, "hint_type": "prescriptive"}],
  "candidates": ["hooks.post_tool_use"],
  "action": "prepare",
  "packet_staged": true,
  "scout_conflict": false,
  "commit": true
}
```

The replay harness collects these traces and asserts on:
- Tool-call sequence: classify → dialogue-turn → search_docs → build-packet (prepare) → codex-reply → build-packet --mark-injected (commit)
- State transitions: topic moved from `detected` → `[looked_up]` → `[built]` → `injected`
- Deferred handling: scout conflict → `deferred` state, not `injected`
- Semantic hint propagation: hint received → candidate elevated → packet built

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
| Happy path: detected → [looked_up] → [built] → injected | Full forward transition with commit |
| Attempt states not persisted | looked_up and built absent from written registry file |
| Candidate selection after detection | Detected topic in candidates |
| Injected not re-selected | After mark-injected → not in candidates |
| Suppressed: weak results | [looked_up] → suppressed on empty search |
| Suppressed: redundant | [looked_up] → suppressed when coverage exists |
| Suppressed re-enters on stronger signal | suppressed → detected |
| Deferred: cooldown | Candidate deferred when cooldown active |
| Deferred: scout priority | Candidate deferred when scout target exists |
| Deferred TTL expiry | deferred → detected after configured turns |
| Deferred TTL not expired | deferred stays deferred before TTL |
| Deferred vs suppressed distinction | Different reasons, different re-entry paths |
| Cooldown configurable | Reads from ccdi_config.json |
| Family injection doesn't cover leaves | Inject hooks → hooks.post_tool_use still detected |
| Leaf inherits family_context_available | Flag set after family injected |
| Leaf then family tracked independently | Both have separate coverage |
| Facet evolution | overview injected, schema still pending → new lookup |
| Idempotent mark-injected | Same packet twice doesn't corrupt |
| No commit without send | build-packet without --mark-injected leaves topic in detected |
| Registry corruption recovery | Malformed JSON → reinitialize empty |
| Semantic hint elevates candidate | Prescriptive hint on detected topic → materially new |
| Semantic hint with unknown topic | Hint doesn't match any topic → ignored |
| Malformed hints file | Invalid JSON → ignored with warning |

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
| Semantic hints → CLI | `claim_index`, `hint_type` enum values, `claim_excerpt` length cap, classifier resolution of excerpt |
| `dump_index_metadata` → `build_inventory.py` | Response shape matches expected fields (`index_version`, `categories[].chunks[].chunk_id`, etc.) — cross-package contract |
| Config → CLI | `ccdi_config.json` schema validated at load; unknown keys warned, missing keys use defaults |
| Registry seed → delegation envelope | `ccdi_seed` file path valid, seed JSON parses to expected schema |
| Version axes → overlay merge | `schema_version`, `overlay_schema_version`, `merge_semantics_version` compatibility validated at build time |

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

### Design Dialogue (7 turns)

Thread: `019d0c24-29c9-7bf1-a2f4-d50f3056553b`

| Turn | Topic | Key decision |
|------|-------|-------------|
| 1 | Approach selection | Approach 1 (subagent + scout) recommended, but don't put DocSearch in scout pipeline |
| 2 | Component design | Hierarchical topic inventory, topic registry with lifecycle state, compact fact packets |
| 3 | Optimization | Detect aggressively/inject conservatively, search wide/inject narrow, session-local caching |
| 4 | Spec-level detail | Full data models, classifier walkthrough, registry transition rules, packet format |
| 5 | Simplification | Drop inverted indexes, keep alias objects, persist semantics / derive performance |
| 6 | Integration gaps | Coarse-grained CLI commands, optional cross-plugin dependency, MCP client for inventory, CCDI-lite for /codex |
| 7 | Testing review | Boundary contract tests, false-positive contexts, registry partial-coverage, external failure paths |

### Review Dialogue (6 turns)

Thread: `019d0c5d-59d7-7ec2-9a90-c0e6b44bdcd0`

System design review surfaced 7 findings and 2 tensions; 6-turn exploratory dialogue resolved all major items:

| Resolution | Source | Confidence |
|-----------|--------|-----------|
| Semantic hints with claim-index refs (not topic_ids) for prescriptive-claim detection | Convergence | High |
| Briefing-carried ccdi_seed + opaque checkpoint for registry handoff | Convergence | High |
| Prepare/commit split (Step 5.5 / Step 7.5) for turn-loop integration | Convergence | High |
| Durable vs attempt-local registry states | Convergence | High |
| CLI-only typed config file for tuning parameters | Convergence | High |
| Scout target always beats CCDI targeting | Convergence | High |
| Three version axes for schema evolution | Concession | Medium |
| Three-layer test strategy with ccdi_trace replay harness | Concession | Medium |
| Staged rollout: initial CCDI first, mid-dialogue in shadow mode | Concession | Medium |

Unresolved (detail-level, for implementation): `ccdi_policy_snapshot` shape, version compatibility matrix format, `--source codex|user` differentiation semantics.
