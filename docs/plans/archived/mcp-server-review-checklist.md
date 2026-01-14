# Extension Docs MCP Server — Implementation Checklist

**Last updated:** 2026-01-11 (after design document revision)

## Algorithm / Design

- [x] Precompute/cached term stats for BM25 — Added `BM25Index` with `docFrequency` map for O(1) df lookup
- [x] Resolve `bm25Score` signature mismatch — Unified on `bm25Score(queryTerms, chunk, index)`
- [x] Confirm line counting matches "≤150 lines" rule — Using `countLines()` helper with `content.split('\n').length`
- [x] Decide fallback for >150-line files with no H2 headings — **NOT NEEDED**: Corpus audit confirmed all 107 files have H2 headings
- [x] Review shared-context regex — Documented: narrow scope intentional, only `hooks-input-schema.md` triggers it
- [x] Ensure `chunk.id` is finalized before any indexing — Added comment + collision warning log

## Edge Cases

- [x] > 150-line file with no H2 headings — Corpus audit: none exist; single-chunk fallback documented
- [x] `##` inside code fences does not split — Fence state tracking in `splitAtH2()`
- [x] Intro content before first H2 included in first chunk — `isFirstH2` logic preserves intro
- [x] Merge small chunks without exceeding 150 lines — Buffer logic in `mergeSmallChunks()`
- [x] Shared context only prepends when first section is truly shared — Regex + documentation added
- [x] Duplicate headings across files get unique IDs via hash suffix — Collision detection + warning log

## Search / Ranking

- [x] Tokenizer splits CamelCase & consecutive caps correctly — Regex chain in `tokenize()`
- [x] Frontmatter header terms affect relevance — Via `formatMetadataHeader()` inclusion in content
- [ ] Queries matching only metadata still return results — Verify during implementation
- [x] Ranking is deterministic across runs — BM25 with precomputed index, no randomness

## Input Validation

- [x] Empty query returns structured error response — `validateSearchInput()` implementation
- [x] Query >500 chars returns structured error response — `validateSearchInput()` implementation
- [x] `limit` clamps to 1–20 — `Math.min(Math.max(...))` in validation

## Runtime / Startup

- [x] `DOCS_PATH` exists or exits with fatal error — `fs.existsSync` check with `process.exit(1)`
- [x] Zero markdown files triggers fatal error — Length check with `process.exit(1)`
- [x] Startup logs only to stderr (no stdout pollution) — All `console.error()`, documented
- [x] Log chunk/file counts on startup — With timing: `"Loaded X chunks from Y files in Zms"`

## Integration

- [x] Tool schema matches implementation (`query` required, `limit` optional) — `searchToolDefinition`
- [x] `SearchResult` includes `chunk_id`, `content`, `category`, `source_file`, `score` — Interface defined
- [ ] Stdio transport initializes cleanly — Verify during implementation

## Documentation / Notes

- [x] Document assumptions (corpus size, fallback chunking rules) — Corpus analysis section added
- [x] Note "metadata boost" = header inclusion, not explicit weighting — Clarified in BM25 section

## Remaining Items (verify during implementation)

- [ ] Queries matching only metadata still return results
- [ ] Stdio transport initializes cleanly
