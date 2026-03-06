---
name: openai-docs
description: "Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations (for example: Codex, Responses API, Chat Completions, Apps SDK, Agents SDK, Realtime, model capabilities or limits); prioritize OpenAI docs MCP tools and restrict any fallback browsing to official OpenAI domains."
allowed-tools:
  - mcp__openaiDeveloperDocs__search_openai_docs
  - mcp__openaiDeveloperDocs__fetch_openai_doc
  - mcp__openaiDeveloperDocs__list_openai_docs
---

# OpenAI Docs

Provide authoritative, current guidance from OpenAI developer docs using the developers.openai.com MCP server.

## When to Use

- User asks how to build with OpenAI APIs (Codex, Responses, Chat Completions, Realtime, Agents SDK, Apps SDK)
- User needs current model capabilities, limits, or pricing
- Verifying technical claims about OpenAI products against official docs
- User asks about OpenAI SDK usage (Python or Node)

## When NOT to Use

- General programming questions unrelated to OpenAI APIs
- Questions about Claude, Anthropic, or non-OpenAI AI services
- Questions about OpenAI company news, policies, or non-developer topics
- Debugging user code that doesn't involve OpenAI API surface

## Product Snapshots

Use these to scope search queries to the right product area:

| Product | What it is | Key search terms |
|---------|-----------|-----------------|
| Codex | Coding agent (CLI, cloud, GitHub Action) | `codex exec`, `codex cloud`, sandbox, AGENTS.md |
| Responses API | Unified endpoint for agentic workflows | `responses`, tools, streaming, built-in tools |
| Chat Completions | Message-based generation | `chat/completions`, messages, functions |
| Apps SDK | ChatGPT app builder (web UI + MCP server) | `apps-sdk`, components, MCP |
| Agents SDK | Multi-agent orchestration toolkit | `agents-sdk`, handoffs, traces, guardrails |
| Realtime API | Speech-to-speech, low-latency | `realtime`, WebSocket, audio |
| gpt-oss | Open-weight reasoning models | `gpt-oss-120b`, `gpt-oss-20b`, Apache 2.0 |

## Constraints

- Requires `openaiDeveloperDocs` MCP server
- Treat OpenAI docs as source of truth — do not speculate beyond what docs state
- Never guess doc URLs — only use URLs returned by `search_openai_docs` or `list_openai_docs`

## Search Discipline

These rules prevent the most common failure modes: oversized results, noisy cross-product matches, and wasted fetches on non-existent URLs.

### Rule 1: Always set `limit`

Every `search_openai_docs` call must include `limit`. Use `limit: 3` for focused queries, `limit: 5` for broader ones. The default result set is too large and can overflow output.

### Rule 2: One scope per search

Search one product or topic at a time. Multi-scope queries return noisy cross-product results.

**Bad:** `"Codex delegation Agents SDK handoff tools sandbox"`
**Good:** `"Codex exec sandbox modes"`, then separately `"Agents SDK handoffs"`

### Rule 3: Never guess URLs

Only pass URLs returned by `search_openai_docs` or `list_openai_docs` to `fetch_openai_doc`. The URL structure is not predictable — guessing produces "No documentation entry found" errors.

### Rule 4: Fetch before searching again

When search returns a relevant hit:

1. Fetch the returned URL (use `anchor` if the search result includes one)
2. Read the fetched content
3. Only search again if the fetched page does not answer the question

Do not run parallel broad searches. Follow: search -> fetch -> evaluate -> search again if needed.

### Rule 5: Large results mean broad query

If a search result overflows or returns many irrelevant hits, the query was too broad. Narrow the query — do not treat this as an MCP server failure.

## Procedure

1. **Scope** — Identify which product the question targets (use Product Snapshots table)
2. **Search** — `search_openai_docs` with a narrow query using official terms, `limit: 5`
3. **Fetch** — `fetch_openai_doc` on the best hit. Use `anchor` when the search result includes one
4. **Answer** — Synthesize from fetched content. Cite the doc URL
5. **Expand** — If the fetched page doesn't fully answer, search again with a refined query on the missing aspect only

## Decision Points

**Search returns 0 results:**
1. Rephrase using official terms from the Product Snapshots table
2. Try `list_openai_docs` with `limit: 10` to browse available pages
3. After 2 failed attempts, fall back to web search (see Fallback section)

**Search returns results but none are relevant:**
1. Check if you're searching the wrong product scope
2. Rephrase with more specific terms (e.g., `"codex exec --json JSONL events"` not `"codex output format"`)
3. After 2 irrelevant attempts, state uncertainty and offer web search fallback

**Multiple pages cover the same topic:**
- Fetch both. If they differ, cite both and note the difference
- Prefer the more specific page (e.g., `/codex/noninteractive/` over `/codex/cli/`)

**Fetched page shows raw JS/JSX instead of rendered content:**
- Some reference pages use `<ConfigTable>` React components
- Read the JS export objects directly — they contain the actual flag/option definitions as structured data (key, type, description, defaultValue fields)

## Verification

Before considering a response complete:

- [ ] At least one `fetch_openai_doc` was called (search alone is insufficient)
- [ ] All technical claims cite a specific doc URL
- [ ] No URLs were guessed — every URL came from a search or list result
- [ ] Quotes are short; prefer paraphrase with citation

## Fallback: Web Search

Use only after the MCP server returns no meaningful results on 2+ attempts.

- Restrict to official domains: `developers.openai.com`, `platform.openai.com`
- Cite the source URL
- Note that the information came from web search, not the docs MCP

## If MCP Server Missing

If MCP tools are unavailable:

1. Run: `claude mcp add --transport http openaiDeveloperDocs https://developers.openai.com/mcp`
2. If that fails, ask the user to run the command and restart Claude Code
3. Re-run after restart

## Troubleshooting

**Symptom:** Search returns oversized or overflowing results
**Cause:** Query too broad or `limit` not set
**Fix:** Add `limit: 3`, narrow query to one product/topic

**Symptom:** `fetch_openai_doc` returns "No documentation entry found"
**Cause:** URL was guessed or is outdated
**Fix:** Search first, then fetch the URL from results. Never construct URLs manually

**Symptom:** Fetched page shows raw JS/JSX instead of rendered content
**Cause:** Page uses React components (`<ConfigTable>`) for interactive tables
**Fix:** Read the JS export objects — they contain flag/option definitions as structured data

**Symptom:** Search returns results from the wrong product
**Cause:** Query terms overlap across products (e.g., "sandbox" appears in Codex, Agents SDK, and Apps SDK)
**Fix:** Include the product name in the query (e.g., `"Codex sandbox modes"` not `"sandbox modes"`)
