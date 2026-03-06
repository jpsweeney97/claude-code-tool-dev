# claude-code-docs MCP Server

**Version:** 1.0.0  
**Runtime:** Node.js >=18 (TypeScript, ESM)  
**Key dependencies:** `@modelcontextprotocol/sdk`, `zod`, `yaml`, `stemmer`  
**License:** Not specified in this package

## Problem Statement
Claude Code's documentation is large and frequently updated, but most MCP clients need fast, local search results rather than full-document scans. This server fetches the official docs, chunks them into semantic sections, builds an in-memory BM25 index, and exposes MCP tools that return ranked snippets.

The result is a small, focused MCP server that provides deterministic, query-focused results with minimal client integration surface: a stdio transport, two tools, and a cache-backed indexing pipeline.

## Quick Start
1. From this directory, install dependencies:
   `npm install`
2. Build the server:
   `npm run build`
3. Start the MCP server (stdio transport):
   `npm start`

To use the server from an MCP client, see Client Configuration below.

## How It Works
Pipeline overview:
1. Fetch official docs from the configured URL and parse `Source:` markers into sections.
2. Synthesize frontmatter (topic/id/category) and chunk each section at semantic boundaries.
3. Tokenize and build a BM25 index (with heading-based score boosting).
4. Serve MCP tool calls against the in-memory index.

Design properties:
- Two-cache model: a raw content cache (TTL-based) and a serialized index cache (version-gated).
- Fail-open on expected fetch/validation errors by falling back to stale cache when allowed.
- Fail-closed on programmer errors to avoid masking regressions.
- Concurrency-safe index loading with a shared in-flight promise and retry backoff.

## Configuration
Environment variables:

| Variable | Default | Purpose | Constraints / Behavior |
| --- | --- | --- | --- |
| `DOCS_URL` | `https://code.claude.com/docs/llms-full.txt` | Source documentation URL. | Used verbatim; should be https and return text content. |
| `RETRY_INTERVAL_MS` | `60000` | Retry backoff for failed index loads. | If <1000, >600000, or non-numeric, it is clamped to `60000`. |
| `CACHE_TTL_MS` | `86400000` | Content cache freshness window in milliseconds. | Integer >=0. `0` means the cache is never considered fresh (fetch each load); values > 1 year are capped. |
| `DOCS_CACHE_MAX_STALE_MS` | `0` | Maximum allowed age for stale cache fallback. | Integer >=0. `0` disables the limit; invalid values are treated as `0`. |
| `MIN_SECTION_COUNT` | `40` | Minimum parsed sections required to accept fetched content. | Integer >=0. `0` disables validation. If below the minimum, fetch is rejected and stale cache may be used. |
| `MAX_INDEX_CACHE_BYTES` | `52428800` | Max serialized index size in bytes before writing cache. | Integer >0. If exceeded, index cache write is skipped (server keeps in-memory index). |
| `MAX_RESPONSE_BYTES` | `10485760` | Max HTTP response size in bytes. | Integer >0. If declared or streamed size exceeds, fetch fails and may fall back to cache. |
| `FETCH_TIMEOUT_MS` | `30000` | HTTP fetch timeout in milliseconds. | Integer >=0. `0` results in immediate timeout. |
| `CACHE_PATH` | unset | Override the content cache file path. | Must include a filename (not just a directory). Does not move the index cache. |
| `XDG_CACHE_HOME` | unset | Base cache directory for defaults. | When set, affects default content and index cache paths. |

Default cache locations:
- macOS content cache: `~/Library/Caches/claude-code-docs/llms-full.txt`
- macOS index cache: `~/Library/Caches/claude-code-docs/llms-full.index.json`
- Linux content cache: `$XDG_CACHE_HOME/claude-code-docs/llms-full.txt` (or `~/.cache/claude-code-docs/llms-full.txt`)
- Linux index cache: same directory, `llms-full.index.json`

Notes:
- `CACHE_PATH` overrides only the content cache file path. The index cache always uses the default cache directory derived from `XDG_CACHE_HOME` or OS defaults.
- Content cache writes use a lock file (`.lock`) to coordinate concurrent writers.

## Tools

### `search_docs`
Searches the indexed Claude Code docs.

Parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `query` | string | yes | - | Max 500 chars, trimmed, must be non-empty. |
| `limit` | integer | no | `5` | 1-20. |
| `category` | string | no | - | Canonical categories or aliases (see below). |

Canonical categories:
`hooks`, `skills`, `commands`, `agents`, `plugins`, `plugin-marketplaces`, `mcp`, `settings`, `memory`, `overview`, `getting-started`, `cli`, `best-practices`, `interactive`, `security`, `providers`, `ide`, `ci-cd`, `desktop`, `integrations`, `config`, `operations`, `troubleshooting`, `changelog`

Aliases:
`subagents` -> `agents`, `sub-agents` -> `agents`, `slash-commands` -> `commands`, `claude-md` -> `memory`, `configuration` -> `config`

Return shape:

| Field | Type | Description |
| --- | --- | --- |
| `results[]` | object | Array of matches. |
| `results[].chunk_id` | string | Chunk identifier. |
| `results[].content` | string | Full chunk content. |
| `results[].snippet` | string | Snippet best matching the query. |
| `results[].category` | string | Derived category. |
| `results[].source_file` | string | Source URL/path. |
| `error` | string | Present only on failure. |

### `reload_docs`
Forces a refresh of the docs and rebuilds the index.

Parameters: none.

Return:
- Text message indicating success, chunk count, and any parse warnings.

## Resources
None.

## Transport
The server uses stdio transport via the MCP SDK.

## Client Configuration
Example `.mcp.json` entry:

```json
{
  "mcpServers": {
    "claude-code-docs": {
      "command": "node",
      "args": ["/absolute/path/to/claude-code-docs/dist/index.js"]
    }
  }
}
```

## Tests
Run:
`npm test`

Latest run:
- Total: 396 passed, 1 skipped (integration)

Per-file breakdown:

| Test file | Tests | Notes |
| --- | --- | --- |
| `tests/parser.test.ts` | 21 | |
| `tests/bm25.test.ts` | 40 | |
| `tests/lifecycle.test.ts` | 24 | |
| `tests/frontmatter.test.ts` | 39 | |
| `tests/chunker.test.ts` | 39 | |
| `tests/golden-queries.test.ts` | 29 | |
| `tests/jsx-block-tracker.test.ts` | 14 | |
| `tests/fence-tracker.test.ts` | 13 | |
| `tests/server.test.ts` | 23 | |
| `tests/fetcher.test.ts` | 8 | |
| `tests/index-cache.test.ts` | 7 | |
| `tests/loader.test.ts` | 20 | |
| `tests/url-helpers.test.ts` | 20 | |
| `tests/chunk-helpers.test.ts` | 20 | |
| `tests/tokenizer.test.ts` | 22 | |
| `tests/categories.test.ts` | 6 | |
| `tests/config.test.ts` | 10 | |
| `tests/protected-block-tracker.test.ts` | 6 | |
| `tests/integration.test.ts` | 1 | Skipped unless `INTEGRATION=1` |
| `tests/error-messages.test.ts` | 8 | |
| `tests/cache.mock.test.ts` | 1 | |
| `tests/corpus-validation.test.ts` | 2 | |
| `tests/cache.test.ts` | 24 | |

## Known Limitations
- Stdio transport only; no HTTP/SSE transport.
- No background refresh loop; use `reload_docs` for refreshes.
- Category filtering is limited to the predefined list above.
