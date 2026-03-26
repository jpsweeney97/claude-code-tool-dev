# claude-code-docs MCP Server

BM25-based search server for Claude Code documentation. Fetches docs from `https://code.claude.com/docs/llms-full.txt`, chunks into semantic sections, builds an in-memory BM25 index, and exposes three tools (`search_docs`, `reload_docs`, `dump_index_metadata`) via MCP stdio transport.

### Search Tool Parameters

| Parameter | Type | Required | Default | Constraints |
|-----------|------|----------|---------|-------------|
| `query` | string | yes | — | Max 500 chars, trimmed |
| `limit` | integer | no | `5` | 1–20 |
| `category` | string | no | — | One of 26 categories or 5 aliases (see `categories.ts`) |

## Commands

```bash
npm test              # vitest run
npx tsc --noEmit      # type check
npm run build         # tsc → dist/
npm start             # run server (fetches from code.claude.com)
```

All commands must run from this directory (`packages/mcp-servers/claude-code-docs/`).

## Architecture

### Pipeline

```
loadFromOfficial (fetch + parse docs)
  → parseSections (split by Source: markers into sections)
    → chunkFile (split sections into semantic chunks)
      → buildBM25Index (term frequencies, inverted index)
        → search (BM25 scoring + heading boost + category filter)
```

### Module Map

| Module | Role |
|--------|------|
| `index.ts` | Entry point — MCP server setup, tool registration (`search_docs`, `reload_docs`, `dump_index_metadata`) |
| `lifecycle.ts` | `ServerState` class — index loading, caching, retry, concurrency control |
| `loader.ts` | Fetch/cache pipeline — TTL, stale fallback |
| `chunker.ts` | Document splitting — H2/H3/paragraph/hard split hierarchy |
| `bm25.ts` | BM25 scoring, heading boost, snippet extraction |
| `index-cache.ts` | Serialization, version constants, Zod schemas |
| `tokenizer.ts` | Porter stemmer + CamelCase splitting |
| `categories.ts` | 26 canonical categories, URL-to-category mapping, 5 aliases (`subagents`→`agents`, `sub-agents`→`agents`, `slash-commands`→`commands`, `claude-md`→`memory`, `configuration`→`config`) |
| `types.ts` | `Chunk`, `SearchResult`, `MarkdownFile`, `ParsedSection` interfaces |
| `cache.ts` | Filesystem cache read/write for index persistence |
| `parser.ts` | Parses `llms-full.txt` into `ParsedSection[]` via Source-line splitting |
| `fetcher.ts` | HTTP fetch with redirect handling |
| `schemas.ts` | Zod schemas for search tool input/output |
| `dump-index-metadata.ts` | Metadata/introspection builder for `dump_index_metadata` |
| `error-messages.ts` | User-facing error formatting |
| `chunk-helpers.ts` | `computeTermFreqs`, `generateChunkId` |
| `frontmatter.ts` | YAML frontmatter parsing |
| `url-helpers.ts` | URL normalization and matching |
| `fence-tracker.ts` | Tracks code fence boundaries during splitting |
| `protected-block-tracker.ts` | Tracks code blocks and JSX during splitting |
| `jsx-block-tracker.ts` | Tracks JSX component boundaries |

### Key Design Patterns

- **Constructor injection** in `ServerState` — all I/O functions injected, enabling test isolation without mocks
- **Four version constants** gate cache validity: `INDEX_FORMAT_VERSION`, `TOKENIZER_VERSION`, `CHUNKER_VERSION`, `INGESTION_VERSION`. Bump the relevant constant when changing a subsystem.
- **Two-cache architecture**: content cache (TTL-based, raw HTTP response) and index cache (version-based, serialized BM25 index) invalidate independently
- **Chunking hierarchy**: H2 → H3 → paragraph → hard split with overlap. Each level cascades when chunks exceed size limits.

### Cache Paths

Both caches resolve via `getDefaultCachePath()` / `getDefaultIndexCachePath()` in `cache.ts`. Override with `CACHE_PATH` env var.

| Platform | Content cache | Index cache |
|----------|--------------|-------------|
| macOS | `~/Library/Caches/claude-code-docs/llms-full.txt` | `~/Library/Caches/claude-code-docs/llms-full.index.json` |
| Linux | `$XDG_CACHE_HOME/claude-code-docs/` (or `~/.cache/claude-code-docs/`) | Same directory |

Writes use a PID-based lock file (`llms-full.txt.lock`) with stale-lock detection.

## Testing

Tests mirror source 1:1 (`src/foo.ts` → `tests/foo.test.ts`). Additional test files:

| Test | Purpose |
|------|---------|
| `golden-queries.test.ts` | Multi-category query coverage (35 queries, 26 categories) — validates search quality |
| `integration.test.ts` | End-to-end pipeline assessment (skipped by default — run with `INTEGRATION=1`) |
| `corpus-validation.test.ts` | Validates chunking invariants across full corpus (requires content cache) |
| `cache.mock.test.ts` | Cache behavior with mocked filesystem |
| `server.test.ts` | MCP server integration — tool registration, error handling |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DOCS_URL` | `https://code.claude.com/docs/llms-full.txt` | Documentation source URL |
| `RETRY_INTERVAL_MS` | `60000` | Retry interval after fetch failure |
| `CACHE_TTL_MS` | `86400000` (24h) | Content cache TTL |
| `DOCS_CACHE_MAX_STALE_MS` | `0` (disabled) | Hard limit on stale content cache age. Set to enable (e.g. `604800000` for 7d). |
| `MIN_SECTION_COUNT` | `40` | Minimum sections in fetched content. Rejects truncated docs. Set to `0` to disable. |
| `MAX_INDEX_CACHE_BYTES` | `52428800` (50 MB) | Hard limit on serialized index size before write |
| `INTEGRATION` | (unset) | Set to `1` to run `integration.test.ts` against live `code.claude.com` |

## Gotchas

- **Working directory**: All commands must run from this package directory, not the monorepo root.
- **Version bumps required**: Changing chunker, tokenizer, parser, or related subsystems requires bumping the corresponding version constant in `index-cache.ts`. Without the bump, stale cached indexes will be served.
- **BM25 params are query-time only**: `k1`, `b`, `headingBoost`, `headingMinCoverage`, `snippetMaxLength` in `BM25_CONFIG` do not affect the stored index. No cache invalidation needed when changing them.
- **Zod strips unknown keys by default**: When adding fields to serialized structures, update both the TypeScript interface and the Zod schema in `index-cache.ts`.
