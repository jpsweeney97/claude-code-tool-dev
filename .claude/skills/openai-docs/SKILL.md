---
name: openai-docs
description: Use this skill when working with the OpenAI API, OpenAI SDKs (Python or TypeScript), ChatGPT Codex, Realtime API, Assistants API, or any OpenAI product with a developer API. Invoke it to look up exact API parameters, request/response schemas, code examples, SDK usage patterns, or to verify current behavior. Always use this skill when code imports `openai` or `@openai`, when discussing OpenAI models (GPT-5, o4-mini, gpt-image), or when working with OpenAI API features (Responses API, function calling, structured outputs, web search, file search, embeddings, fine-tuning, batch API, vector stores, images, audio, video, moderation). Never answer OpenAI API questions from training memory alone — OpenAI's APIs evolve rapidly and documentation is authoritative. Not for Claude/Anthropic API usage, Claude Code extensions, or general AI/ML concepts.
allowed-tools:
  - mcp__openaiDeveloperDocs__search_openai_docs
  - mcp__openaiDeveloperDocs__list_openai_docs
  - mcp__openaiDeveloperDocs__fetch_openai_doc
  - mcp__openaiDeveloperDocs__list_api_endpoints
  - mcp__openaiDeveloperDocs__get_openapi_spec
---

# OpenAI Docs

The openaiDeveloperDocs MCP server provides search and retrieval over official OpenAI documentation from developers.openai.com and platform.openai.com. It also exposes the full OpenAPI specification for every API endpoint. This skill teaches you how to use it effectively.

## Search Discipline

**Documentation is authoritative over training knowledge.** OpenAI's API surface changes frequently — new models ship, parameters get added or deprecated, SDK methods change signatures. Your training data captures a snapshot; the docs capture the current state.

**When to search:**

- API parameters, request/response schemas, or SDK method signatures
- "How do I..." with any OpenAI API feature
- Verifying model capabilities, rate limits, or pricing
- Writing or reviewing code that calls the OpenAI API
- Anything where being wrong about the details causes broken API calls

**When training knowledge is sufficient:**

- General programming concepts unrelated to OpenAI APIs
- High-level "what is function calling" explanations (though search to confirm details)
- Questions about Claude, Anthropic SDKs, or Claude Code (different documentation entirely)

**When in doubt, search.** A redundant search costs seconds. A wrong answer from stale training data costs the user's time debugging a 400 error from a deprecated parameter.

## The Two-Step Workflow

Unlike search engines that return content directly, this MCP server separates discovery from retrieval. Understanding this is essential.

**Step 1 — Discover:** Use `search_openai_docs` to find relevant pages. Results return URLs and page hierarchy (title, section headings), but usually not the actual content.

**Step 2 — Retrieve:** Use `fetch_openai_doc` with the URL to get the full markdown. Use the `anchor` parameter (e.g., `#streaming`, `#function-tool-example`) to fetch just one section — this is critical for keeping context small.

Always complete both steps. Search results alone rarely contain enough detail to answer a question accurately.

## Five Tools, Three Workflows

### Guide and concept lookup

For understanding features, reading guides, or finding examples:

```
search_openai_docs("Responses API function calling")
  → finds URL: developers.openai.com/api/docs/guides/function-calling/
fetch_openai_doc(url, anchor="#function-tool-example")
  → returns the actual code examples and explanation
```

This is your primary workflow. Use it for guides, tutorials, cookbooks, and conceptual documentation.

### API reference lookup

For exact schemas, parameters, and request/response formats:

```
list_api_endpoints()
  → browse 161 endpoints to find the right path (e.g., /responses)
get_openapi_spec(url="https://api.openai.com/v1/responses", languages=["python"])
  → returns full schema + Python code examples
```

Use this when you need the precise parameter types, required fields, or want to see request/response pairs for a specific endpoint. The `languages` filter (`python`, `javascript`, `curl`) keeps output focused. Set `codeExamplesOnly: true` when you only need the code.

### Browsing

When you don't know what to search for:

```
list_openai_docs(limit=20)
  → browse available pages by title
fetch_openai_doc(url)
  → read the interesting one
```

Use pagination (`cursor`) to page through results. This is rarely needed — search is almost always better — but useful for discovering what documentation exists.

## Crafting Effective Queries

The search engine is Algolia-based (not BM25). It matches against page titles, section headings, and content. A few things to know:

### Use feature names, not questions

Algolia matches tokens in headings and content. Feature names outperform natural language questions.

| Instead of | Use |
|------------|-----|
| "how do I make the model call functions" | "function calling" |
| "how to get structured JSON back" | "structured outputs" |
| "sending images to the API" | "image input" or "vision" |
| "making the model search the internet" | "web search tool" |

### Combine topic + specificity

When you need something specific within a broad topic, combine terms:

- "Responses API streaming" (not just "streaming")
- "function calling strict mode" (not just "function calling")
- "embeddings dimensions parameter" (not just "embeddings")
- "batch API file format" (not just "batch")

### Use the anchor parameter aggressively

Search results often include anchored URLs (e.g., `#enable-streaming`, `#function-tool-example`). Pass these anchors to `fetch_openai_doc` to get just that section instead of the entire page. This saves significant context.

If a search result URL contains an anchor, always use it when fetching.

### Know the documentation domains

Results come from two domains with different content:

| Domain | Content |
|--------|---------|
| `developers.openai.com` | API guides, cookbooks, API reference, tutorials |
| `platform.openai.com` | Dashboard settings, billing, usage, API keys |

Platform.openai.com results (settings, billing) are rarely useful for API questions. If your search returns mostly platform.openai.com hits, refine your query with more specific API terms.

## Multi-Search Strategies

### When results are sparse or irrelevant

1. **Try the canonical feature name:** "Responses API" not "response endpoint", "Chat Completions" not "chat API"
2. **Try adjacent terms:** "tool use" / "function calling", "JSON mode" / "structured outputs"
3. **Broaden:** If "batch API error handling" returns nothing, try just "batch API" and then fetch the page to find the error section
4. **Switch to the API reference:** If guides don't cover it, `get_openapi_spec` for the endpoint often has the detail you need

### When results are too broad

1. **Add specificity:** "Responses API streaming events" not just "streaming"
2. **Lower the limit:** `limit: 3` forces top matches only
3. **Use anchors after fetching:** If the page is long, re-search for the specific section heading and fetch with that anchor

### When building a complete answer

Some questions span multiple documentation pages. Search iteratively:

1. Search for the core concept
2. Fetch the most relevant page
3. If it references other features, search for those too
4. For exact parameter details, follow up with `get_openapi_spec`

**Example:** "How do I use structured outputs with function calling?"
1. Search: "structured outputs function calling" — find the guide
2. Fetch the guide page with relevant anchor
3. Search: "strict mode JSON schema" — for the constraint details
4. `get_openapi_spec` for `/responses` — for the exact parameter schema

## Context Efficiency

Documentation lookups are expensive — each `fetch_openai_doc` call can return thousands of tokens, and `get_openapi_spec` returns full schemas with multiple code examples. Undisciplined fetching bloats context and slows responses. The goal is to answer the question with the minimum number of fetches at the minimum granularity.

### Pick the right tool for the detail level needed

| What you need | Best tool | Why |
|--------------|-----------|-----|
| Exact parameter types and required fields | `get_openapi_spec` with `languages` filter | Structured, focused, no prose |
| Just code examples | `get_openapi_spec` with `codeExamplesOnly: true` | Eliminates schema prose entirely |
| Conceptual explanation or guide | `fetch_openai_doc` with anchor | Prose context around the concept |
| Quick "does this feature exist" check | `search_openai_docs` alone | Hierarchy in results often answers the question without fetching |

Start with the most constrained tool. If `get_openapi_spec` answers the question, don't also fetch the guide page. If a search result's hierarchy (`lvl1`/`lvl2` headings) answers a yes/no question, don't fetch at all.

### Always use anchors when available

A full page fetch can return 3,000-10,000 tokens. An anchored fetch returns 200-1,000 tokens for the relevant section. That's a 5-10x difference.

**Before fetching**, read the search result URLs. If a result URL contains an anchor (e.g., `#enable-streaming`, `#function-tool-example`), pass that anchor to `fetch_openai_doc`. If the URL has no anchor but the `hierarchy.lvl2` field names the section you want, use that as the anchor (lowercase, hyphens for spaces).

### Cap your fetches

For a typical question, aim for this budget:

- **Simple questions** (one concept): 1 search + 1 anchored fetch. Sometimes just 1 search if the hierarchy answers it.
- **Moderate questions** (concept + parameters): 1 search + 1 anchored fetch + 1 `get_openapi_spec` call.
- **Complex questions** (multiple features): 2 searches + 2-3 anchored fetches. Rarely more.

If you've done 4+ fetches and still don't have the answer, stop and synthesize what you have. Note the gaps rather than continuing to fetch.

### Read the search hierarchy before fetching

Search results include a `hierarchy` object with `lvl0` through `lvl6`. This tells you the page structure before you fetch anything:

```
hierarchy: { lvl1: "Function calling", lvl2: "Strict mode" }
```

This means the page "Function calling" has a section "Strict mode". Fetch with anchor `#strict-mode` instead of fetching the entire function calling guide.

## Using Results

### Cite the source URL

Include the documentation URL so the user can verify and read further. Use the anchored URL when you fetched a specific section.

### Prefer docs over training knowledge

When search results contradict your training knowledge, go with the documentation. OpenAI ships changes frequently — a parameter that existed last month may be deprecated today. State the finding clearly.

### Handle gaps explicitly

If the documentation doesn't cover something:
- Say so directly: "The OpenAI documentation doesn't cover [X]"
- Share any related information from search results
- Do not fill gaps with speculation about undocumented behavior

### Distinguish Responses API from Chat Completions

OpenAI has two generation APIs. Code and documentation for one does not apply to the other:

- **Responses API** (`/v1/responses`): Newer, supports built-in tools (web search, file search, computer use), multi-turn via `previous_response_id`
- **Chat Completions** (`/v1/chat/completions`): Established, message-based, function calling via `tools` parameter

When the user's code uses `client.responses.create()`, search for Responses API docs. When it uses `client.chat.completions.create()`, search for Chat Completions docs. Do not mix them.

## Troubleshooting

**Search returns "MCP server not available":**
The openaiDeveloperDocs MCP server isn't running. Check `/mcp` to verify server status.

**Search returns few/no results for a known feature:**
The query terms don't match the documentation vocabulary. Try the canonical feature name (e.g., "Responses API" not "response endpoint"), try with and without specificity qualifiers, or broaden to just the product name. If search consistently fails, use `list_api_endpoints` to confirm the endpoint exists, then `get_openapi_spec` to get details directly.

**`fetch_openai_doc` returns empty or minimal content:**
The URL may be stale, or the page may have been reorganized. Re-search to find the current URL. Some pages (especially `platform.openai.com` settings pages) have minimal indexable content — these are dashboard links, not documentation. Filter them out and focus on `developers.openai.com` results.

**`get_openapi_spec` returns no code samples:**
Not all endpoints have code samples in the OpenAPI spec. Fall back to searching for guide pages that cover the endpoint, or check the cookbooks at `developers.openai.com/cookbook/` for worked examples.

**Results seem outdated or contradicted by the user's experience:**
OpenAI ships changes frequently. If the user reports behavior that contradicts the docs, note the discrepancy and suggest the user check the changelog or status page. Do not assume the docs are wrong — but do not assume the user is wrong either. State what the documentation says and flag the conflict.
