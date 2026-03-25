# claude-code-docs MCP Server

**Version:** 1.0.0  
**Runtime:** Node.js >=18 (TypeScript, ESM)  
**Key dependencies:** `@modelcontextprotocol/sdk`, `zod`, `yaml`, `stemmer`  
**License:** Not specified in this package

## Problem Statement
Claude Code's documentation is large and frequently updated, but most MCP clients need fast, local search results rather than full-document scans. This server fetches the official docs, chunks them into semantic sections, builds an in-memory BM25 index, and exposes MCP tools that return ranked snippets.

The result is a small, focused MCP server that provides deterministic, query-focused results with minimal client integration surface: a stdio transport, four tools, and a cache-backed indexing pipeline.

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
| `DOCS_URL` | `https://code.claude.com/docs/llms-full.txt` | Source documentation URL. | Validated on startup; must be a valid `https` URL. |
| `DOCS_TRUST_MODE` | `official` | Trust mode controlling source validation and canary policy. | `official`: pins source to `code.claude.com`, full canary evaluation (taxonomy + relative-drift checks). `unsafe`: accepts any HTTPS URL, structural canaries only (count + size checks). Use `unsafe` only for local testing or private mirrors. |
| `RETRY_INTERVAL_MS` | `60000` | Retry backoff for failed index loads. | Validated on startup; must be an integer between `1000` and `600000`. |
| `CACHE_TTL_MS` | `86400000` | Content cache freshness window in milliseconds. | Integer >=0. `0` means the cache is never considered fresh (fetch each load); values > 1 year are capped. |
| `DOCS_CACHE_MAX_STALE_MS` | `0` | Maximum allowed age for stale cache fallback. | Validated on startup; must be an integer >=0. `0` disables the limit. |
| `MIN_SECTION_COUNT` | `40` | Minimum parsed sections required to accept fetched content. | Integer >=0. `0` disables validation. If below the minimum, fetch is rejected and stale cache may be used. |
| `MAX_INDEX_CACHE_BYTES` | `52428800` | Max serialized index size in bytes before writing cache. | Validated on startup; must be an integer >0. If exceeded, index cache write is skipped (server keeps in-memory index). |
| `MAX_RESPONSE_BYTES` | `10485760` | Max HTTP response size in bytes. | Integer >0. If declared or streamed size exceeds, fetch fails and falls back to stale cache when available. |
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
| `meta` | object | Index provenance attached to each search response. |
| `meta.trust_mode` | string | Active trust mode: `official` or `unsafe`. |
| `meta.source_kind` | string or null | How content was obtained: `fetched`, `cached`, `stale-fallback`, or `bundled-snapshot`. Null if no corpus loaded. |
| `meta.index_created_at` | string or null | ISO timestamp when the BM25 index was built. Null if not yet loaded. |
| `meta.corpus_age_ms` | integer or null | Milliseconds since the corpus content was obtained (`Date.now() - corpus.obtainedAt`). Null if no corpus loaded. |
| `error` | string | Present only on failure. |

### `reload_docs`
Forces a refresh of the docs and rebuilds the index.

Parameters: none.

Return:
- Text message indicating success, chunk count, and any parse warnings.

### `get_status`
Returns a lightweight runtime status snapshot. Use this to check index health, trust configuration, and canary evaluation results without triggering a reload or dumping the full metadata.

Parameters: none.

Return shape:

| Field | Type | Description |
| --- | --- | --- |
| `trust_mode` | string | Active trust mode: `official` or `unsafe`. |
| `docs_origin` | string | Hostname of the documentation source URL. |
| `docs_url` | string | Full documentation source URL. |
| `source_kind` | string or null | How content was obtained: `fetched`, `cached`, `stale-fallback`, or `bundled-snapshot`. Null if no corpus loaded. |
| `index_created_at` | string or null | ISO timestamp when the BM25 index was built. Null if not yet loaded. |
| `corpus_age_ms` | number or null | Milliseconds since corpus content was obtained. Null if no corpus loaded. |
| `corpus_obtained_at` | string or null | ISO timestamp when corpus content was obtained. Null if no corpus loaded. |
| `last_load_attempt_at` | string or null | ISO timestamp of the most recent load attempt. Null if never attempted. |
| `last_load_error` | string or null | Error message from the most recent failed load. Null if last load succeeded. |
| `warning_codes` | string[] | Active warning codes: `taxonomy_drift`, `parse_issues`, `section_count_drift`, `stale_corpus`. |
| `is_loading` | boolean | Whether a load/reload is currently in progress. |

### `dump_index_metadata`
Returns structured index metadata useful for debugging ingestion, category mapping, and chunk coverage without dumping the full corpus.

Parameters: none.

Return shape:

| Field | Type | Description |
| --- | --- | --- |
| `index_version` | string | Serialized index format version. |
| `built_at` | string | ISO timestamp for the response build time. |
| `docs_epoch` | string or null | Content hash for the currently loaded docs. |
| `categories[]` | object | Per-category chunk metadata. |
| `categories[].name` | string | Canonical category name. |
| `categories[].aliases` | string[] | Accepted aliases for the category. |
| `categories[].chunk_count` | integer | Number of chunks in the category. |
| `categories[].chunks[]` | object | Chunk-level metadata for debugging and inventory building. |

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

The suite covers parser, chunker, loader, lifecycle, fetcher, metadata, and cache behavior. Special cases:

- `tests/integration.test.ts` is skipped unless `INTEGRATION=1`.
- `tests/corpus-validation.test.ts` depends on a populated content cache.

## Known Limitations
- Stdio transport only; no HTTP/SSE transport.
- No background refresh loop; use `reload_docs` for refreshes.
- Category filtering is limited to the predefined list above.
