# Full Audit: claude-code-docs MCP Server

**Date:** 2026-03-03
**Scope:** All 18 source files (~3,400 lines) + 22 test files (~3,600 lines)
**Baseline:** 328 tests passing, 3 skipped, 2 todo
**Method:** 4 parallel audit agents (architecture, error handling, test coverage, security/performance) + cross-agent deduplication and severity calibration

## Executive Summary

41 unique findings across 4 dimensions. No exploitable security vulnerabilities on the query path. The server has correct inverted-index search, safe cache construction, and minimal dependency surface. The primary risks are: untested critical paths (especially `index.ts` orchestration), race conditions during reload, and absence of resource limits on the fetch pipeline.

| Severity | Count | Description |
|----------|-------|-------------|
| A (Critical) | 5 | Bugs, untested critical paths, resource exhaustion |
| B (Important) | 16 | Design issues, coverage gaps, reliability concerns |
| C (Minor) | 20 | Cleanup, optimization, test quality |

## Severity A — Critical

### A1. `ensureIndex` / `doLoadIndex` entirely untested
**File:** `src/index.ts:34-120`
**Agents:** Test Coverage

The core server orchestration — concurrent load deduplication (`loadingPromise` guard), retry interval enforcement, cache hit/miss branching, index version/hash/tokenizer/chunker comparison — has zero direct tests. `server.test.ts` only tests Zod schemas. The `ensureIndex` concurrency guard (the `loadingPromise` singleton) is completely untested. This is the most-executed code path in the server.

### A2. `reload_docs` race condition — stale `index` during reload window
**File:** `src/index.ts:218-228`
**Agents:** Architecture, Error Handling

`reload_docs` sets `index = null` then calls `ensureIndex(true)`. Between these two operations, a concurrent `search_docs` call sees `index = null` and `loadingPromise = null`, returning "Index not available" — a misleading error instead of a transient wait. The window is narrow but the effect is user-visible.

### A3. Unbounded memory on large fetched documents
**File:** `src/fetcher.ts:71`, `src/index-cache.ts:24-33`
**Agents:** Error Handling, Security

`response.text()` buffers the entire HTTP response with no size limit. No `Content-Length` check, no streaming, no abort at a byte threshold. Downstream, `parseSections` materializes all regex matches, `chunkFile` produces token arrays, and `serializeIndex` JSON-stringifies the entire index. A multi-gigabyte response would cascade through the pipeline. The default URL is hardcoded to `code.claude.com` (trusted), so exploitation requires env var misconfiguration or MITM.

### A4. TTL cache-hit path has `it.todo` — most common production path untested
**File:** `src/loader.ts:205-212`, `tests/loader.test.ts:13-15`
**Agents:** Test Coverage

The `fetchAndParse` TTL cache branch (fresh cache skips fetch) is the most common production code path. It has explicit `it.todo` markers in tests. The stale-cache fallback on fetch failure is also untested.

### A5. `hardSplitWithOverlap` produces oversized chunks for single long lines
**File:** `src/chunker.ts:426-428`
**Agents:** Error Handling

When a single line exceeds `MAX_CHUNK_CHARS` (8000), the guard forces `end = start + 1` to prevent infinite loops. The resulting chunk exceeds both char and line limits with no truncation. Searches over it work, but returned content is oversized.

## Severity B — Important

### B1. Deprecated global `parseWarnings` kept alive alongside clean return path
**File:** `src/frontmatter.ts:29-40, 157, 177`
**Agents:** Architecture

`parseFrontmatter` returns warnings in `ParseResult` (clean API) AND pushes to module-level `parseWarnings` (deprecated). The only callers (`chunker.ts`) discard the returned warnings and rely on the global. The "deprecated" path is the only working path — the returned `warnings` go unused.

### B2. `splitBounded` `introContent` parameter always called with `[]`
**File:** `src/chunker.ts:87, 590-593`
**Agents:** Architecture

`splitBounded` accepts `introContent: string[]` with logic to prepend to the first H2 section, but the only call site passes `[]`. Dead parameter implying a non-existent extension point.

### B3. `loadMarkdownFiles` exported but never called in production pipeline
**File:** `src/loader.ts:46`
**Agents:** Architecture

Filesystem loader is exported but has no production callers. Creates false impression that local file loading is supported in production.

### B4. Content cache has no format version — parser changes don't invalidate
**File:** `src/cache.ts` vs `src/index-cache.ts:5-7`
**Agents:** Architecture

Raw content cache (`llms-full.txt`) has no version. If parser behavior changes, stale cache is served and re-parsed without invalidation. Content hash only detects upstream doc changes, not local parser changes.

### B5. Lock file leak on process kill during cache write
**File:** `src/cache.ts:102-115`
**Agents:** Error Handling, Security

If the process is killed mid-write (SIGKILL, OOM), `${cachePath}.lock` is left on disk. Next startup spins for 2 seconds then throws. No stale-lock detection (e.g., check if PID in lock is alive).

### B6. `FenceTracker` — unclosed fence suppresses all subsequent heading splits
**File:** `src/fence-tracker.ts:27-32`
**Agents:** Architecture, Error Handling

A malformed fence (opened but never properly closed) leaves `inFence = true` for the rest of the document. All heading-based chunk splits are suppressed — the remainder of the document becomes one giant chunk.

### B7. Stale cache accepted without TTL bound on fetch failure
**File:** `src/loader.ts:250-257`
**Agents:** Error Handling

When network fails, any cache — regardless of age — is accepted. A 1-year-old cache produces incorrect results with only a log line warning. No upper bound on staleness.

### B8. BM25 config (`k1`, `b`) not checked on cache load — changes don't invalidate
**File:** `src/bm25.ts:11-16`, `src/index.ts:78-88`
**Agents:** Architecture

`serializeIndex` persists `k1` and `b` but the cache validation only checks `version`, `contentHash`, `tokenizerVersion`, `chunkerVersion`. Changing BM25 parameters doesn't invalidate the cache. Heading boost values are not persisted at all.

### B9. `headingBoostMultiplier` re-tokenizes headings on every search call
**File:** `src/bm25.ts:84-90`
**Agents:** Architecture

`tokenize(heading)` is called per candidate chunk per query. Heading tokens are stable post-index-build and could be precomputed on the `Chunk` struct (matching the existing pattern of `tokens` and `termFreqs`).

### B10. `extractSnippet` re-tokenizes every line instead of using cached tokens
**File:** `src/bm25.ts:125-135`
**Agents:** Security/Performance

Called once per result (max 20), each call re-tokenizes every line in the chunk (up to 150 lines) through the Porter stemmer. ~3000 tokenization+stemming passes per search at maximum results. Could use pre-computed data.

### B11. `reload_docs` tool handler untested
**File:** `src/index.ts:205-247`
**Agents:** Test Coverage

The `reload_docs` handler has distinct logic (waiting on in-progress loads, clearing index cache, forcing refresh, returning parse warnings) with no tests.

### B12. 14 of 24 categories have no golden query
**File:** `tests/golden-queries.test.ts`
**Agents:** Test Coverage

Golden queries cover 10 categories. Missing: `commands`, `plugins`, `plugin-marketplaces`, `settings`, `memory`, `overview`, `cli`, `best-practices`, `interactive`, `desktop`, `integrations`, `config`, `operations`, `changelog`.

### B13. Integration test entirely skipped
**File:** `tests/integration.test.ts`
**Agents:** Test Coverage

Single test marked `it.skip`. No automated end-to-end test of the full pipeline.

### B14. `server.test.ts` re-declares `SearchInputSchema` instead of importing
**File:** `tests/server.test.ts:14-25`
**Agents:** Test Coverage

Schema copy will silently diverge if the real schema changes. Tests would pass while testing a schema that no longer reflects production.

### B15. `RETRY_INTERVAL_MS` env-var clamping logic untested
**File:** `src/index.ts:31-32`
**Agents:** Architecture, Test Coverage

Values outside `[1000, 600000]` silently fall back to 60,000ms with no log, no error. Also untested.

### B16. Network redirect following with no domain restriction
**File:** `src/fetcher.ts:57-59`
**Agents:** Security

`redirect: 'follow'` follows cross-domain redirects without restriction. Relevant only if `DOCS_URL` is misconfigured or the trusted domain is compromised.

## Severity C — Minor

### C1. `error-messages.ts` is 4 lines — no justification for separate file
**File:** `src/error-messages.ts`

### C2. Magic number `400` for snippet `maxLength` not in `BM25_CONFIG`
**File:** `src/bm25.ts:107`

### C3. `NO_STEM` set has only 2 entries with no discoverability or export
**File:** `src/tokenizer.ts:7`

### C4. `CATEGORY_ALIASES` partially duplicates `SECTION_TO_CATEGORY` — implicit distinction
**File:** `src/categories.ts:113-119`

### C5. `splitBounded` `intro` return value always discarded
**File:** `src/chunker.ts:590, 87`

### C6. `JsxBlockTracker` depth-cap reset is silent — no signal to caller
**File:** `src/jsx-block-tracker.ts:69-73`

### C7. `formatSearchError` drops error class name
**File:** `src/error-messages.ts:1-4`

### C8. `extractSnippet` can overshoot `maxLength` by two lines before truncation
**File:** `src/bm25.ts:142-154`

### C9. `tokenize` does not guard against `stemmer` throwing
**File:** `src/tokenizer.ts:31-33`

### C10. `deriveCategory` silently defaults unmapped URLs to `'overview'`
**File:** `src/frontmatter.ts:211`

### C11. Empty-string `content` produces indexable chunk with zero discriminatory value
**File:** `src/chunker.ts:22-24`

### C12. `writeIndexCache` has no size guard on `JSON.stringify`
**File:** `src/cache.ts:124`

### C13. Zod validates entire cache on every load — no version fast-path
**File:** `src/index-cache.ts:65-68`

### C14. `tokens` array retained post-index-build when only `.length` is needed
**File:** `src/bm25.ts`, `src/types.ts`

### C15. Snippet existence asserted without content check in tests
**File:** `tests/bm25.test.ts:113`

### C16. Oversized char-limit test uses +1000 slop (12.5%)
**File:** `tests/chunker.test.ts:379`

### C17. Cache-fallback test only checks file count, not content
**File:** `tests/loader.test.ts:551`

### C18. `cache.mock.test.ts` tests mock infrastructure, not application code
**File:** `tests/cache.mock.test.ts`

### C19. `FETCH_TIMEOUT_MS` env-var fallback path untested
**File:** `tests/fetcher.test.ts`

### C20. `frontmatter.test.ts` global `parseWarnings` state leak between describe blocks
**File:** `tests/frontmatter.test.ts`

## Coupling Map

| Module | Direct Dependencies |
|--------|-------------------|
| `index.ts` | loader, chunker, bm25, frontmatter, categories, index-cache, cache, error-messages (8) |
| `loader.ts` | fetcher, parser, cache, url-helpers, frontmatter (5) |
| `chunker.ts` | tokenizer, frontmatter, chunk-helpers, protected-block-tracker, types (5) |
| `frontmatter.ts` | url-helpers, categories (2) |
| `bm25.ts` | tokenizer, types (2) |
| `index-cache.ts` | bm25 (BM25_CONFIG), types (2) |
| `protected-block-tracker.ts` | fence-tracker, jsx-block-tracker (2) |

No circular dependencies. `index.ts` is the most coupled (8 deps) — appropriate for orchestration.

## Recommended Fix Priority

### Immediate (correctness / reliability)
1. **A2** — Fix reload race: hold old index until new one is ready
2. **A5** — Truncate or split oversized single-line chunks
3. **B5** — Add stale-lock detection (check PID liveness)
4. **B6** — Add fence recovery (force-close at section boundaries)

### Short-term (test coverage / observability)
5. **A1** — Write tests for `ensureIndex` / `doLoadIndex` orchestration
6. **A4** — Implement the `it.todo` tests for TTL cache path
7. **B11** — Test `reload_docs` handler
8. **B14** — Import real schema in `server.test.ts` instead of copying
9. **B12** — Add golden queries for uncovered categories (prioritize `commands`, `plugins`, `settings`)
10. **B15** — Test and add logging for `RETRY_INTERVAL_MS` clamping

### Medium-term (design / performance)
11. **B1** — Remove deprecated global `parseWarnings`; have callers use returned warnings
12. **B9/B10** — Precompute heading tokens; cache line-level token data for snippets
13. **A3** — Add `Content-Length` check or streaming with byte limit to fetcher
14. **B4** — Add parser version to content cache validation
15. **B8** — Include BM25 config params in cache validation

### Low priority (cleanup)
16. **B2/C5** — Remove dead `introContent` parameter and unused `intro` return
17. **B3** — Remove or document `loadMarkdownFiles` export
18. C-level items as convenient
