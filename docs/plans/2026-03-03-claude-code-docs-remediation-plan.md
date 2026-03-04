# Remediation Plan: claude-code-docs MCP Server

**Date:** 2026-03-03
**Source:** Full audit (`docs/audits/2026-03-03-claude-code-docs-full-audit.md`) + 6-turn collaborative Codex dialogue
**Scope:** 41 findings (5A, 16B, 20C) across 18 source files

## PR Sequence

### PR1: `fix/a2-atomic-reload` (Immediate)
**Findings:** A2
**Risk:** Eliminates race condition where `search_docs` sees null index during `reload_docs`
**Files:** `src/index.ts`
**Change:** Hold old index reference alive during reload. Replace `index = null; ... ensureIndex(true)` with atomic swap: load new index into temp variable, then assign to module-level `index` only on success. On failure, keep the old index.
**Tests:** Verify concurrent search during reload returns results (not "Index not available")
**Depends on:** Nothing

### PR2: `fix/a5-b5-b6-c7-leaf-correctness` (Immediate, parallel with PR1)
**Findings:** A5, B5, B6, C7
**Risk:** Four independent leaf-node correctness fixes
**Files:** `src/chunker.ts`, `src/cache.ts`, `src/fence-tracker.ts`, `src/error-messages.ts`

| Finding | Fix |
|---------|-----|
| A5: Oversized single-line chunk | Truncate line to `MAX_CHUNK_CHARS` in `hardSplitWithOverlap` when `end = start + 1` |
| B5: Lock file leak on SIGKILL | Add PID-liveness check in `acquireLock` — read `.lock` file, check if PID is alive, steal if dead |
| B6: Unclosed fence suppresses splits | Force-close fence at section boundaries (when a new `Source:` line is encountered) |
| C7: `formatSearchError` drops error class | Include `err.constructor.name` in format |

**Tests:** One test per fix
**Depends on:** Nothing

### PR3: `fix/a3-fetch-limits` (Short-term, parallel with PR1/PR2)
**Findings:** A3, C12
**Risk:** Defense-in-depth against oversized responses
**Files:** `src/fetcher.ts`, `src/cache.ts`

| Finding | Fix |
|---------|-----|
| A3: Unbounded fetch memory | Content-Length precheck (reject > 10MB) + streaming byte cap with early abort |
| C12: Unbounded index write | Size guard on `JSON.stringify` output before write (reject > 50MB) |

**Tests:** Mock large response, verify abort. Mock large index, verify rejection.
**Depends on:** Nothing

### PR4: `refactor/lifecycle-extraction` (After PR1)
**Findings:** A1, A4, B1, B11, B14, B15
**Risk:** Makes orchestration testable; migrates deprecated warning state
**Files:** `src/index.ts` (major refactor), `src/lifecycle.ts` (new), `src/schemas.ts` (new), `src/frontmatter.ts`, `src/chunker.ts`, tests

**3 commits:**
1. **Mechanical extraction:** Extract `ensureIndex`/`doLoadIndex` into `lifecycle.ts` as a C-lite `ServerState` class with constructor injection. Extract `SearchInputSchema` to `schemas.ts`. No behavior changes.
2. **Warning migration:** Have `chunker.ts` callers use returned `ParseResult.warnings` instead of global `parseWarnings`. Remove deprecated global from `frontmatter.ts`.
3. **Tests:** Write tests for `ServerState` (A1: concurrency guard, retry interval, cache version checks), TTL cache path (A4: `it.todo` items), `reload_docs` handler (B11), `RETRY_INTERVAL_MS` clamping (B15). Import `SearchInputSchema` from `schemas.ts` in `server.test.ts` (B14).

**Depends on:** PR1 (tests should validate race-safe behavior)

### PR5: `perf/b9-b10-c2-c14-bm25-tokens` (Independent)
**Findings:** B9, B10, C2, C14
**Risk:** Performance improvement — eliminate redundant tokenization at query time
**Files:** `src/types.ts`, `src/bm25.ts`, `src/chunker.ts`, `src/index-cache.ts`

| Finding | Fix |
|---------|-----|
| B9: headingBoostMultiplier re-tokenizes | Precompute `headingTokens: Set<string>` on Chunk during chunking |
| B10: extractSnippet re-tokenizes lines | Cache line-level token data on Chunk or use pre-computed term coverage |
| C2: Magic number 400 for maxLength | Move to `BM25_CONFIG.snippetMaxLength` |
| C14: Full tokens array retained | Replace with `tokenCount: number` after index build (tokens only needed during build) |

**Requires:** `INDEX_FORMAT_VERSION` bump (new serialized fields on Chunk)
**Tests:** Verify heading tokens precomputed. Verify snippet quality unchanged. Benchmark optional.
**Depends on:** Nothing (but should merge after PR4 to avoid conflicts in `index-cache.ts`)

### PR6: `fix/b4-b8-b7-c12-cache-hardening` (After PR4)
**Findings:** B4, B7, B8
**Risk:** Cache integrity and observability improvements
**Files:** `src/cache.ts`, `src/index-cache.ts`, `src/index.ts`, `src/loader.ts`

| Finding | Fix |
|---------|-----|
| B4: Content cache no parser version | Add `PARSER_VERSION` constant, include in cache metadata |
| B8: BM25 params not in cache check | Add `k1`/`b` comparison in cache validation |
| B7: Unbounded stale cache | Log warning at 48h staleness, add optional `DOCS_CACHE_MAX_STALE_MS` env var |

**Depends on:** PR4 (index.ts changes), coordinate `INDEX_FORMAT_VERSION` bump with PR5

### PR7: `test/b11-b12-b15-coverage` (After PR4)
**Findings:** B12, B13
**Risk:** Coverage gaps in golden queries and integration
**Files:** test files only

| Finding | Fix |
|---------|-----|
| B12: 14/24 categories without golden queries | Add golden queries for `commands`, `plugins`, `settings`, `memory`, `cli`, `interactive`, `desktop`, `overview` (prioritized 8 of 14) |
| B13: Integration test skipped | Evaluate feasibility of unskipping with mock server or keep as manual step |

**Depends on:** PR4 (B11 tests already in PR4)

### PR8: `chore/cleanup-accepted` (Anytime)
**Findings:** B2, B3, C5
**Risk:** Dead code removal, documentation
**Files:** `src/chunker.ts`, `src/loader.ts`, docs

| Finding | Fix |
|---------|-----|
| B2+C5: Dead `introContent`/`intro` | Remove parameter and return value from `splitBounded` |
| B3: `loadMarkdownFiles` dead export | Add `@deprecated` annotation with rationale |

**Depends on:** Nothing

## Accepted as Known Limitations

C1, C3, C4, C8-C11, C13, C15-C20 — documented in audit, no action planned.

B16 (redirect following) — accepted with risk-register conditions: local-only server, trusted admin, no multi-tenant. Reassess if deployment model changes.

## Dependency Graph

```
PR1 ──→ PR4 ──→ PR6
                  PR7
PR2 (parallel with PR1)
PR3 (parallel with PR1)
PR5 (independent, merge after PR4 preferred)
PR8 (anytime)
```

## Execution Strategy

Phase 1: PR1 + PR2 + PR3 in parallel (immediate correctness + defense-in-depth)
Phase 2: PR4 (lifecycle extraction — the structural backbone)
Phase 3: PR5 + PR6 + PR7 in parallel (performance + cache hardening + coverage)
Phase 4: PR8 (cleanup)
