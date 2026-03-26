# claude-code-docs MCP Server

BM25-based search server for Claude Code documentation. Fetches docs from `https://code.claude.com/docs/llms-full.txt`, chunks into semantic sections, builds an in-memory BM25 index, and exposes four tools (`search_docs`, `reload_docs`, `dump_index_metadata`, `get_status`) via MCP stdio transport.

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
| `index.ts` | Entry point — MCP server setup, tool registration (`search_docs`, `reload_docs`, `dump_index_metadata`, `get_status`) |
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
| `trust.ts` | Trust modes (`official`/`unsafe`), source kinds, provenance comparison |
| `canary.ts` | Canary evaluation pure function, threshold constants, policy types |
| `status.ts` | Runtime status snapshot, search meta projection, `get_status` Zod schema |

### Key Design Patterns

- **Constructor injection** in `ServerState` — all I/O functions injected, enabling test isolation without mocks
- **Five version constants** gate cache validity: `INDEX_FORMAT_VERSION`, `TOKENIZER_VERSION`, `CHUNKER_VERSION`, `INGESTION_VERSION`, `CANARY_VERSION`. Bump the relevant constant when changing a subsystem.
- **Two-cache architecture**: content cache (TTL-based, raw HTTP response) and index cache (version-based, serialized BM25 index) invalidate independently
- **Chunking hierarchy**: H2 → H3 → paragraph → hard split with overlap. Each level cascades when chunks exceed size limits.
- **Five-block serialized index structure**: `corpus` (content hash + provenance), `diagnostics` (canary evaluation inputs), `index` (build timestamp + counts), `policyState` (baseline tracking), `evaluation` (canary pass/fail + CANARY_VERSION) + top-level `compatibility` block (all version constants). BM25 data (chunks, docFrequency, invertedIndex) lives at the top level outside the named blocks.
- **Four cache load paths**: (1) full hit — all versions match and canary passes; (2) canary replay — versions match but canary re-evaluated (threshold changed); (3) rebuild — version mismatch, fetch fresh; (4) provenance refresh — provenance improved (better source kind or newer), re-persist corpus block
- **Trust modes**: `official` pins the source URL to `code.claude.com` and enables full canary evaluation (taxonomy + relative-drift checks); `unsafe` accepts any HTTPS URL and runs structural canaries only (count + size checks)
- **`CANARY_VERSION`** in the evaluation block — bump when changing canary thresholds or adding/removing canary checks. Changing only the diagnostic computation (not thresholds) bumps `INGESTION_VERSION` instead.

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
| `DOCS_TRUST_MODE` | `official` | Trust mode: `official` (pins to code.claude.com) or `unsafe` (any HTTPS URL) |
| `RETRY_INTERVAL_MS` | `60000` | Retry interval after fetch failure |
| `CACHE_TTL_MS` | `86400000` (24h) | Content cache TTL |
| `DOCS_CACHE_MAX_STALE_MS` | `0` (disabled) | Hard limit on stale content cache age. Set to enable (e.g. `604800000` for 7d). |
| `MIN_SECTION_COUNT` | `40` | Minimum sections in fetched content. Rejects truncated docs. Set to `0` to disable. |
| `MAX_INDEX_CACHE_BYTES` | `52428800` (50 MB) | Hard limit on serialized index size before write |
| `INTEGRATION` | (unset) | Set to `1` to run `integration.test.ts` against live `code.claude.com` |

## Gotchas

- **Working directory**: All commands must run from this package directory, not the monorepo root.
- **Version bump policy**:
  - Changing canary thresholds or adding/removing canary checks → bump `CANARY_VERSION` in `canary.ts`
  - Changing diagnostic computation (not thresholds) → bump `INGESTION_VERSION` in `index-cache.ts`
  - Adding a required diagnostic field → bump `INGESTION_VERSION` (not the Zod schema alone)
  - Adding an optional diagnostic field → update the Zod schema only, no version bump needed
  - Changing chunker, tokenizer, or parser → bump `CHUNKER_VERSION` or `TOKENIZER_VERSION` in `index-cache.ts`
  - Without the correct bump, stale cached indexes will be served.
- **BM25 params are query-time only**: `k1`, `b`, `headingBoost`, `headingMinCoverage`, `snippetMaxLength` in `BM25_CONFIG` do not affect the stored index. No cache invalidation needed when changing them.
- **Zod strips unknown keys by default**: When adding fields to serialized structures, update both the TypeScript interface and the Zod schema in `index-cache.ts`.
- **Unsafe mode is an escape hatch, not multi-corpus support**: In `unsafe` mode, taxonomy and relative-drift canary checks are disabled. The server accepts any HTTPS source URL but cannot verify corpus authenticity against expected Claude Code doc structure. Use only for local testing or private mirrors.
- **Provenance refresh triggers a full rebuild**: When `DOCS_TRUST_MODE` or `DOCS_URL` changes between runs, the cached index is invalidated even if all version constants match — the policy change is a cache miss by design.

## Auto-Build

The MCP server is registered to start via `scripts/run-mcp.sh`, a wrapper that runs `tsc` before `exec node dist/index.js`. This ensures `dist/` always reflects the TypeScript source on every session restart.

**How it works:**
- Wrapper redirects tsc output to stderr (stdout is reserved for MCP JSON-RPC)
- `exec` replaces bash with node so signals reach the server process directly
- Incremental compilation (`incremental: true` in tsconfig) makes no-op builds fast
- `.tsbuildinfo` lives in `dist/` — `rm -rf dist/` also clears the incremental cache

**If tsc fails:** The server does not start. This is intentional — running stale compiled code is worse than no server. Fix the TypeScript error and restart the session.

**Registration:** `claude mcp get claude-code-docs` shows the current config. To re-register after moving the repo:
```bash
claude mcp remove claude-code-docs -s user
claude mcp add-json --scope user claude-code-docs '{"type":"stdio","command":"<repo>/packages/mcp-servers/claude-code-docs/scripts/run-mcp.sh","env":{"DOCS_PATH":"<repo>/docs/extension-reference"}}'
```
