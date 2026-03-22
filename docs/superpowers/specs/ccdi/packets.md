---
module: packets
status: active
normative: true
authority: packet-contract
---

# CCDI Fact Packet Builder

Transforms docs search results into compact, citation-backed content for injection into Codex's context. Operates on results from `claude-code-docs` search and [registry](registry.md) coverage state.

## Packet Structure

```
FactPacket
├── packet_kind: "initial" | "mid_turn"
├── topics: TopicKey[]           # MUST NOT be empty; max length: initial_max_topics (initial) or mid_turn_max_topics (mid_turn) from config
├── facet: Facet                 # primary facet used for the search — the resolved facet from scheduling
├── facts: FactItem[]
│   ├── mode: "paraphrase" | "snippet"
│   ├── facet: Facet
│   ├── text: string
│   └── refs: [DocRef](data-model.md#docref)[]
└── token_estimate: integer   # >= 0
```

**FactPacket field types:**

| Field | Type | Description |
|-------|------|-------------|
| `packet_kind` | `"initial" \| "mid_turn"` | Injection phase that produced this packet |
| `topics` | `TopicKey[]` | Topic keys included in this packet; bounded by config (`initial_max_topics` or `mid_turn_max_topics`). MUST NOT be empty. |
| `facet` | `Facet` | Primary facet used for the search (see [data-model.md#queryplan](data-model.md#queryplan)) |
| `facts` | `FactItem[]` | Ordered list of fact items |
| `token_estimate` | `integer` (>= 0) | Estimated token count for the rendered packet |

The top-level `facet` is the primary facet used when building the packet (from `--facet` flag or the scheduled candidate's resolved facet). Individual `FactItem.facet` may differ when facts span multiple facets within a topic. The top-level `facet` is emitted in the `<!-- ccdi-packet -->` metadata comment in mid-turn rendered output, enabling the agent to evaluate target-match without parsing fact-level details.

## Verbatim vs Paraphrase

| Content type | Mode | Rationale |
|-------------|------|-----------|
| Field names, enum values, flags | `snippet` | Easy to misstate; exact syntax matters |
| JSON schema fragments | `snippet` | Structure is the information |
| Conceptual behavior, sequencing | `paraphrase` | Meaning > wording |
| Design implications, constraints | `paraphrase` | Needs contextualization |

Default is paraphrase. At most one snippet per mid-turn packet unless explicitly about schema details.

Both modes are deterministic operations in the CLI — no LLM involvement (see [foundations.md#cliagent-separation](foundations.md#cliagent-separation)):

- **`snippet`**: Extract verbatim text from the search result's `content` or `snippet` field, trim to budget.
- **`paraphrase`**: Select the most relevant sentence(s) from the search result's `content` field based on facet keyword overlap, trim to budget. This is extractive selection, not generative rewriting. The CLI picks passages; it does not rephrase them.

## Token Budgets

All budget values are configurable via [`ccdi_config.json`](data-model.md#configuration-ccdiconfigjson) → `packets`. Defaults shown:

| Phase | Budget | Max topics | Max facts | Config keys |
|-------|--------|------------|-----------|------------|
| Initial | 600–1000 tokens | ≤ 3 topics | ≤ 8 facts | `initial_token_budget_*`, `initial_max_*` |
| Mid-turn | 250–450 tokens | 1 topic | ≤ 3 facts | `mid_turn_token_budget_*`, `mid_turn_max_*` |

**Quality threshold:** Skip injection when the best search result's relevance score is below `quality_min_result_score` (default: 0.3) OR when fewer than `quality_min_useful_facts` (default: 1) facts survive deduplication and budget constraints. A weak packet is worse than no packet.

**Source hierarchy:** CCDI packets are premise enrichment — they provide background knowledge, not primary evidence. When both CCDI docs content and repo evidence (`@ path:line`) address the same concept, repo evidence takes precedence. CCDI content is placed under `## Material` source-separated from repo evidence (`[ccdocs:...]` citations vs `@ path:line` citations). See [foundations.md#design-principles](foundations.md#design-principles) for the "premise enrichment, not retargeting" architectural constraint.

## Citation Format

```
[ccdocs:<chunk_id>]
```

Examples: `[ccdocs:hooks#pretooluse]`, `[ccdocs:skills#frontmatter]`. Source-separated from repo evidence (`@ path:line`). `source_file` and `category` stay in the internal packet for traceability but are not rendered inline.

## Rendered Output

### Initial Injection

Placed in briefing under `## Material`, source-separated from repo evidence:

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

### Mid-Dialogue Injection

Lighter format, prepended to follow-up prompt:

```markdown
<!-- ccdi-packet topics="hooks.post_tool_use" facet="schema" -->
Claude Code docs context:
- `PostToolUse` runs after a tool completes successfully.
  [ccdocs:hooks#posttooluse]
- For MCP tools, it can replace tool output via
  `updatedMCPToolOutput`. [ccdocs:hooks#posttooluse]
```

The `<!-- ccdi-packet ... -->` comment is a structured metadata line emitted by `build-packet` in mid-turn mode. It carries `topics` (comma-separated topic keys) and `facet` (the resolved facet used for the search). The agent reads this comment to evaluate target-match condition (a) — checking whether any listed topic key appears as a substring in the composed follow-up text. The comment is invisible to Codex (HTML comments are not rendered). In initial mode, topic metadata is already present as the human-readable "Detected topics:" line.

## Build Process

1. Receive search results from `claude-code-docs` (chunks with `chunk_id`, `category`, `source_file`, `snippet`, `content`).
2. Dedupe against `injected_chunk_ids` from the [topic registry](registry.md). When no `--registry-file` is provided (CCDI-lite mode or the initial ccdi-gatherer call in Full CCDI where no prior state exists), skip deduplication.
3. Rank by relevance to the resolved facet. **Facet source:** When `--facet` is provided, use it. When `--facet` is absent (initial mode without `--mark-injected`), use each topic's classifier-resolved facet from the query plan (i.e., the facet in the `ClassifierResult.resolved_topics[].facet` that drove query selection). If the resolved facet is absent from the topic's `QueryPlan.facets`, fall back to `default_facet`.
4. For each top result: decide paraphrase vs snippet based on content type.
5. Assemble into `FactPacket`, check against token budget.
6. If under quality threshold or budget exceeded with nothing useful: return empty (skip injection). Suppression reason depends on *why* the output is empty — see [Failure Modes](#failure-modes).
7. Render to markdown format appropriate to the phase. Within each topic chunk: (1) paraphrase-mode facts first (each with inline `[ccdocs:...]` citation), (2) snippet-mode facts last (exact field names/values). Citations are inline per fact, not a leading block.

**Shadow mode:** In shadow mode, the build process runs identically but rendered output is staged for diagnostics only — not delivered to Codex. See [integration.md#shadow-mode-gate](integration.md#shadow-mode-gate) for the gate condition and [integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue](integration.md#mid-dialogue-phase-per-turn-in-codex-dialogue) for the behavioral contract governing shadow-mode delivery suppression.

## Failure Modes

| Failure | Detection | Behavior |
|---------|-----------|----------|
| `build-packet` produces empty output — weak search results | Best result score below `quality_min_result_score` OR fewer than `quality_min_useful_facts` survive | Skip injection, mark topic `suppressed: weak_results` in [registry](registry.md) |
| `build-packet` produces empty output — all results already injected | All results filtered by deduplication (step 2) — search returned useful results but every `chunk_id` is already in `injected_chunk_ids` | Skip injection, mark topic `suppressed: redundant` in [registry](registry.md) |
| `search_docs` returns empty or errors | Empty results / MCP error | Skip injection for topic, mark `suppressed: weak_results` |

**Suppression and the prepare/commit split:** Automatic suppression (`weak_results` or `redundant`) writes to the registry at prepare time when `--registry-file` is provided. This is an intentional exception to the prepare/commit separation — suppression is a deterministic CLI side-effect, not an agent commitment, so it does not require send confirmation. See [registry.md#failure-modes](registry.md#failure-modes) for the rationale.

Per the [resilience principle](foundations.md#resilience-principle), packet builder failure never blocks consultations.
