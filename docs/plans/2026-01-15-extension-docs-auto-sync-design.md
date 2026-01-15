# Extension-Docs Auto-Sync Design

## Problem

The `extension-docs` MCP server indexes local copies of official Anthropic documentation. These copies drift from the source when Anthropic updates their docs, causing stale or incorrect search results.

## Solution

Fetch fresh documentation from the official source on every server startup. Fall back to a cached copy if the fetch fails.

## Official Source

- **URL:** `https://code.claude.com/docs/llms-full.txt`
- **Format:** Single markdown file (~200k words) with all documentation concatenated
- **Section delimiter:** `Source: <url>` lines separate each doc page

## Architecture

### Current Flow

```
Startup → Load markdown files from DOCS_PATH → Chunk → Build BM25 index → Serve
```

### New Flow

```
Startup → Fetch llms-full.txt → Parse sections → Filter to extensions → Chunk → Build index → Serve
                ↓ (on failure)
         Load cached copy from disk
                ↓ (on success)
         Save to cache for future fallback
```

## New Components

### fetcher.ts

HTTPS fetch with typed errors and timeout.

```typescript
interface FetchResult {
  content: string;
  status: number;
}

class FetchTimeoutError extends Error { ... }
class FetchHttpError extends Error { status: number; ... }
class FetchNetworkError extends Error { ... }

async function fetchOfficialDocs(url: string, timeoutMs?: number): Promise<FetchResult>
```

- Uses Node's built-in `fetch` with `AbortController` for timeout
- Timeout cascades: explicit param → `FETCH_TIMEOUT_MS` env var → 30s default
- Throws typed errors for different failure modes

### parser.ts

Splits the monolithic `llms-full.txt` into sections.

```typescript
interface ParsedSection {
  sourceUrl: string;
  title: string;
  content: string;
}

function parseSections(raw: string): ParsedSection[]
```

- Splits on `^Source:\s+(\S+)\s*$` (multiline regex)
- Extracts title from nearest preceding `#{1,6}` heading
- Handles preamble content before first `Source:` line
- Preserves empty titles for malformed sections (no content loss)

### filter.ts

Keeps only extension-related sections.

```typescript
function isExtensionSection(section: ParsedSection): boolean
function filterToExtensions(sections: ParsedSection[]): ParsedSection[]
```

**URL patterns matched:**
- `/hooks`, `/skills`, `/commands`, `/slash-commands`
- `/agents`, `/subagents`, `/sub-agents`
- `/plugins`, `/plugin-marketplaces`, `/mcp`
- `/settings`, `/claude-md`, `/memory`, `/configuration`

**Title patterns matched:**
- Word-boundary matches for: hooks, skills, commands, agents, subagents, plugins, mcp, settings, memory, configuration, extensions

### cache.ts

Atomic read/write with file locking for crash safety.

```typescript
interface CacheResult {
  content: string;
  age: number;  // milliseconds since last write
}

function getDefaultCachePath(filename?: string): string
async function readCache(cachePath: string): Promise<CacheResult | null>
async function writeCache(cachePath: string, content: string): Promise<void>
```

**Cache location (platform-aware):**
- `XDG_CACHE_HOME` if set
- macOS: `~/Library/Caches/extension-docs/`
- Linux: `~/.cache/extension-docs/`

**Write safety:**
- File-based lock with exclusive create (`wx` flag)
- Atomic write via temp file + rename
- Lock timeout: 2s with 50ms polling

## Modified Components

### loader.ts

Replace filesystem loading with fetch pipeline.

```typescript
function resolveCachePath(): string  // CACHE_PATH env var || getDefaultCachePath()

async function loadFromOfficial(url: string): Promise<MarkdownFile[]>
async function fetchAndParse(url: string): Promise<ParsedSection[]>
```

**Pipeline:**
1. Fetch from URL
2. Write to cache (for fallback)
3. Parse into sections
4. Filter to extensions
5. Remove empty content
6. Convert to `MarkdownFile[]` for existing chunker

**Fallback logic:**
- On fetch failure, log error (using typed error classes)
- Attempt cache read
- If cache exists, log warning with age, use cached content
- If no cache, propagate error (search unavailable)

### index.ts

Replace `DOCS_PATH` configuration with `DOCS_URL`.

```typescript
const docsUrl = process.env.DOCS_URL ?? "https://code.claude.com/docs/llms-full.txt";
const files = await loadFromOfficial(docsUrl);
```

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DOCS_URL` | `https://code.claude.com/docs/llms-full.txt` | Official documentation source |
| `FETCH_TIMEOUT_MS` | `30000` | HTTP fetch timeout in milliseconds |
| `CACHE_PATH` | Platform-specific | Override default cache location |

**Removed:** `DOCS_PATH` (no longer needed)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Fetch timeout | Log message (no stack), fall back to cache |
| HTTP error (4xx/5xx) | Log status, fall back to cache |
| Network error | Log message, fall back to cache |
| Cache hit after failure | Log warning with cache age, continue |
| No cache after failure | Search tool returns "unavailable" error |

## Testing Strategy

1. **Unit tests for parser:** Various `Source:` patterns, edge cases (preamble, missing titles)
2. **Unit tests for filter:** URL and title pattern matching
3. **Unit tests for cache:** Read/write, lock contention, atomic writes
4. **Integration test:** Mock fetch, verify full pipeline
5. **Golden query tests:** Ensure key extension queries still return relevant results

## Migration

1. Remove `DOCS_PATH` from documentation and example configs
2. Update any existing `settings.json` entries that reference `DOCS_PATH`
3. First startup after upgrade will fetch fresh docs and populate cache
