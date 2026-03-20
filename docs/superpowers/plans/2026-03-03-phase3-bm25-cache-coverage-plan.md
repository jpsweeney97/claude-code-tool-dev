# Phase 3: BM25 Optimization, Cache Hardening, Test Coverage

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Phase 3 of the claude-code-docs MCP server remediation (PR5 → PR6 → PR7) with sequential execution.

**Architecture:** Three PRs executed sequentially. PR5 changes `Chunk` type and serialization (INDEX_FORMAT_VERSION bump). PR6 adds cache validation checks on the post-PR5 schema. PR7 adds test coverage for the final codebase state.

**Tech Stack:** TypeScript, Vitest, Zod, ESM modules

**Baseline:** 368 tests passing, branch `main` at `691f547`

**Working directory:** `packages/mcp-servers/claude-code-docs/`

**B10 disposition:** Accepted as-is. CamelCase splitting in `tokenize()` prevents cheap approximation. ~150ms worst-case cost is acceptable. Document as known limitation in commit message.

**C14 disposition:** `tokenCount` is added as an enabler for a future step that removes the `tokens` array from runtime objects. Standalone performance benefit is negligible (~0.12 ns/op). The `tokens` array is retained because `buildBM25Index` still iterates it (`new Set(chunks[i].tokens)`). Document as future enabler, not standalone optimization.

### Codex Adversarial Review Amendments (2026-03-03)

Review converged in 5 turns (adversarial posture, xhigh reasoning effort). 11 RESOLVED, 3 EMERGED. Key amendments:

| # | Finding | Severity | Amendment |
|---|---------|----------|-----------|
| R1 | B8 k1/b cache checks are wrong fix — all BM25 params are query-time only | High | Drop B8 from PR6 entirely. Structural-only cache policy. |
| R2 | PARSER_VERSION scope too narrow — 5 subsystems shape chunks | High | Rename to `INGESTION_VERSION` with documented bump triggers. |
| R3 | `createWholeFileChunk` never sets headingTokens — size-dependent ranking | High | PR5 amendment: derive headingTokens via `fm.topic ?? regex` fallback chain (D3). |
| R4 | Merge test is vacuous — conditional guard skips all assertions | High | Rewrite with deterministic content forcing split-then-merge. |
| R5 | 48h stale warning detached from `CACHE_TTL_MS` | High | Remove 48h tier. Keep `DOCS_CACHE_MAX_STALE_MS` rejection only. |
| R6 | Task 1 test uses `await` in non-async callback | Medium | Fix callback to be async. |
| R7 | PR7 mock-only tests can't detect doc structure drift | Medium | Add URL segment validation against `SECTION_TO_CATEGORY`. |
| R8 | BM25 metadata Zod schema silently strips headingBoost/headingMinCoverage | Medium | No code change needed (B8 dropped), but document for awareness. |

### Codex Deep Review Amendments (2026-03-03)

Review converged in 5 turns (evaluative posture, xhigh reasoning effort). 9 RESOLVED, 3 EMERGED. Focused on implementation correctness after adversarial review addressed design-level concerns.

| # | Finding | Severity | Amendment |
|---|---------|----------|-----------|
| D1 | Merge test (R4) still vacuous — fixture below whole-file thresholds | Blocking | Increase filler to 50 lines/section to exceed `MAX_CHUNK_LINES=150` total. |
| D2 | headingTokens-from-heading test routes through whole-file chunking | Blocking | Increase section content to 80 lines each to force H2 splitting. |
| D3 | R3 incomplete — regex-only misses official docs where parser consumes `# Title` | Blocking | Use `fm.topic ?? regex` fallback chain in `createWholeFileChunk`. |
| D4 | Task 8 stale cache tests under-specified — hidden CACHE_TTL_MS fresh-path routing | Blocking | Full test implementations with `forceRefresh`/low TTL, add 5th boundary test. |
| D5 | `url-helpers.ts` missing from INGESTION_VERSION bump-trigger list | Advisory | Add as 6th subsystem in bump-trigger comment. |
| D6 | Fence-safe heading regex is a known limitation | Advisory | Document deferral — `fm.topic` covers primary case. |
| D7 | `integration.test.ts` has latent API-shape bug (`loadFromOfficial` return type) | Informational | Document in Task 11 assessment scope. |

---

## PR5: `perf/b9-c2-c14-bm25-tokens`

**Branch:** `perf/b9-c2-c14-bm25-tokens` from `main`

**Findings:** B9 (heading re-tokenization), C2 (magic number 400), C14 (tokens array retained)

**Files:**
- Modify: `src/types.ts` — add `headingTokens`, `tokenCount` to `Chunk`
- Modify: `src/chunker.ts` — compute new fields during chunk creation
- Modify: `src/bm25.ts` — use precomputed fields, add `snippetMaxLength` to config
- Modify: `src/index-cache.ts` — serialize/deserialize new fields, bump version
- Modify: `src/lifecycle.ts` — no changes needed (cache validation uses existing version check)
- Modify: `tests/bm25.test.ts` — update `makeChunk`, update `headingBoostMultiplier` calls
- Modify: `tests/lifecycle.test.ts` — add `tokenCount` to `makeMockIndex`
- Modify: `tests/server.test.ts` — add `tokenCount` to test chunk
- Modify: `tests/chunker.test.ts` — update assertions for new fields

### Task 1: C2 — Move magic number to BM25_CONFIG

**Files:**
- Modify: `src/bm25.ts`
- Test: `tests/bm25.test.ts`

**Step 1: Write failing test for snippetMaxLength config**

In `tests/bm25.test.ts`, add to the `extractSnippet` describe block:

```typescript
it('uses BM25_CONFIG.snippetMaxLength as default', async () => {
  const { BM25_CONFIG } = await import('../src/bm25.js');
  expect(BM25_CONFIG.snippetMaxLength).toBe(400);
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --reporter verbose 2>&1 | grep -A2 'snippetMaxLength'`
Expected: FAIL — `snippetMaxLength` doesn't exist on `BM25_CONFIG`

**Step 3: Add snippetMaxLength to BM25_CONFIG and use it**

In `src/bm25.ts`:

1. Add `snippetMaxLength: 400` to `BM25_CONFIG` object (after `headingMinCoverage`)
2. Change `extractSnippet` signature from `maxLength = 400` to `maxLength = BM25_CONFIG.snippetMaxLength`

**Step 4: Run tests to verify all pass**

Run: `npm test`
Expected: All 368 tests pass

**Step 5: Commit**

```
git add src/bm25.ts tests/bm25.test.ts
git commit -m "refactor(bm25): move snippet maxLength to BM25_CONFIG (C2)"
```

### Task 2: Add headingTokens and tokenCount to Chunk type

**Files:**
- Modify: `src/types.ts`

**Step 1: Add new fields to Chunk interface**

In `src/types.ts`, add to the `Chunk` interface:

```typescript
headingTokens?: Set<string>;  // Precomputed union of tokenize(heading) + tokenize(merged_headings)
tokenCount: number;            // tokens.length — avoids depending on array post-build
```

**Step 2: Run tests — expect compilation failures**

Run: `npm test`
Expected: FAIL — `tokenCount` is required but missing from all chunk construction sites.

This is expected and will be fixed in subsequent tasks. Note: TypeScript compilation errors will cascade. Proceed to Task 3.

### Task 3: Update chunker to compute new Chunk fields

**Files:**
- Modify: `src/chunker.ts`
- Test: `tests/chunker.test.ts`

**Step 1: Write failing tests for headingTokens and tokenCount**

In `tests/chunker.test.ts`, add a new describe block:

```typescript
describe('chunk metadata fields', () => {
  it('sets tokenCount equal to tokens.length', () => {
    const file = { path: 'test.md', content: '# Title\n\nSome content here' };
    const { chunks } = chunkFile(file);
    expect(chunks.length).toBeGreaterThan(0);
    for (const chunk of chunks) {
      expect(chunk.tokenCount).toBe(chunk.tokens.length);
    }
  });

  it('computes headingTokens from heading when present', () => {
    // (D2) Content must exceed whole-file thresholds (MAX_CHUNK_LINES=150 or
    // MAX_CHUNK_CHARS=8000) to force H2 splitting. 80 lines/section × 2 sections
    // + headings = ~165 lines total, safely above 150.
    const sections = Array.from({ length: 80 }, (_, i) =>
      `Line ${i} of content for this section to ensure splitting occurs`
    ).join('\n');
    const file = {
      path: 'test.md',
      content: `# Title\n\n## Hooks Guide\n\n${sections}\n\n## Skills Overview\n\n${sections}`,
    };
    const { chunks } = chunkFile(file);
    // Precondition: verify H2 splitting actually occurred (non-vacuous)
    expect(chunks.length).toBeGreaterThan(1);
    const headingChunk = chunks.find(c => c.heading?.includes('Hooks'));
    expect(headingChunk).toBeDefined();
    expect(headingChunk!.headingTokens).toBeDefined();
    expect(headingChunk!.headingTokens).toBeInstanceOf(Set);
    // "## Hooks Guide" tokenizes to ["hook", "guid"]
    expect(headingChunk!.headingTokens!.has('hook')).toBe(true);
    expect(headingChunk!.headingTokens!.has('guid')).toBe(true);
  });

  it('derives headingTokens from first # heading for whole-file chunks', () => {
    const file = { path: 'test.md', content: '# Hooks Guide\n\nShort content about hooks.' };
    const { chunks } = chunkFile(file);
    expect(chunks).toHaveLength(1);
    expect(chunks[0].headingTokens).toBeDefined();
    expect(chunks[0].headingTokens).toBeInstanceOf(Set);
    expect(chunks[0].headingTokens!.has('hook')).toBe(true);
    expect(chunks[0].headingTokens!.has('guid')).toBe(true);
  });

  it('derives headingTokens from fm.topic for whole-file chunks (D3)', () => {
    // Official docs: parser consumes # Title, body has no H1, but fm.topic is set
    const file = {
      path: 'test.md',
      content: 'Body content with no heading at all.',
      frontmatter: { topic: 'Hooks Guide' },
    };
    const { chunks } = chunkFile(file);
    expect(chunks).toHaveLength(1);
    expect(chunks[0].headingTokens).toBeDefined();
    expect(chunks[0].headingTokens!.has('hook')).toBe(true);
    expect(chunks[0].headingTokens!.has('guid')).toBe(true);
  });

  it('headingTokens is undefined for whole-file chunks with no heading or topic', () => {
    const file = { path: 'test.md', content: 'Short content with no heading at all' };
    const { chunks } = chunkFile(file);
    expect(chunks).toHaveLength(1);
    expect(chunks[0].headingTokens).toBeUndefined();
  });

  it('merges headingTokens from all chunks when combining', () => {
    // (D1) Content must exceed whole-file thresholds to force H2 splitting,
    // but each section must be small enough to trigger mergeSmallChunks.
    // Strategy: 3+ H2 sections with ~50 lines each. Total ~155 lines exceeds
    // MAX_CHUNK_LINES=150, forcing splitAtH2. Individual sections (~50 lines)
    // are below merge thresholds, so adjacent small sections get merged.
    const filler = (tag: string) => Array.from({ length: 50 }, (_, i) =>
      `${tag} content line ${i} with enough words to count as real content`
    ).join('\n');
    const file = {
      path: 'test.md',
      content: [
        '# Title',
        '',
        '## Alpha Section',
        '',
        filler('alpha'),
        '',
        '## Beta Section',
        '',
        filler('beta'),
        '',
        '## Gamma Section',
        '',
        filler('gamma'),
      ].join('\n'),
    };
    const { chunks } = chunkFile(file);
    // Precondition: verify merge actually happened (non-vacuous)
    const mergedChunk = chunks.find(c => c.merged_headings && c.merged_headings.length > 0);
    expect(mergedChunk).toBeDefined();
    // headingTokens should contain tokens from both headings
    expect(mergedChunk!.headingTokens).toBeDefined();
    expect(mergedChunk!.headingTokens).toBeInstanceOf(Set);
    // Check for tokens from at least two sections in the merged chunk
    const headingTokens = mergedChunk!.headingTokens!;
    const matchedSections = ['alpha', 'beta', 'gamma'].filter(t => headingTokens.has(t));
    expect(matchedSections.length).toBeGreaterThanOrEqual(2);
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -- --reporter verbose 2>&1 | grep -E '(FAIL|chunk metadata)'`
Expected: FAIL — `tokenCount` missing from Chunk construction, `headingTokens` not computed

**Step 3: Update chunk creation functions**

In `src/chunker.ts`:

1. Add import: `import { tokenize } from './tokenizer.js';` — already imported, verify at top.

2. In `createWholeFileChunk` (line ~74-87):
   - Derive headingTokens using `fm.topic` first, regex second (D3: `loadFromOfficial`
     always sets `fm.topic` from the section title, and the parser consumes the `# Title`
     line before the section body, so official doc bodies rarely contain H1. Regex is the
     correct fallback for local files without frontmatter):
     ```typescript
     // Derive headingTokens: fm.topic (official docs) → first # heading (local files)
     // (R3 + D3: avoid size-dependent ranking; D6: regex has no fence protection — known limitation)
     const headingSource = file.frontmatter?.topic
       ?? content.match(/^#\s+(.+)$/m)?.[1];
     const headingTokens = headingSource
       ? new Set(tokenize(headingSource))
       : undefined;
     ```
   - The `file` parameter in `createWholeFileChunk` already has access to frontmatter
     from the `MarkdownFile` type. Verify `MarkdownFile.frontmatter?.topic` is typed.
   - Add `tokenCount: tokens.length` and `headingTokens` to the return object.

3. In `createSplitChunk` (line ~124-148):
   - Before the return, compute heading tokens:
     ```typescript
     const headingTokens = heading ? new Set(tokenize(heading)) : undefined;
     ```
   - Add `tokenCount: tokens.length` and `headingTokens` to the return object.

4. In `combineChunks` (line ~184-206):
   - Before the return, merge heading tokens from all chunks:
     ```typescript
     const mergedHeadingTokens = new Set<string>();
     for (const c of chunks) {
       if (c.headingTokens) {
         for (const t of c.headingTokens) mergedHeadingTokens.add(t);
       }
     }
     ```
   - Add `tokenCount: tokens.length` and `headingTokens: mergedHeadingTokens.size > 0 ? mergedHeadingTokens : undefined` to the return object.

**Step 4: Fix existing chunker test assertions**

Many existing tests in `chunker.test.ts` construct Chunk objects or check chunk properties. The `tokenCount` field is now required. Scan for any test that constructs a Chunk literal and add `tokenCount`. Most tests use `chunkFile()` which now returns chunks with `tokenCount` — those tests should pass without changes.

**Step 5: Run tests**

Run: `npm test`
Expected: Still FAIL — other test files (`bm25.test.ts`, `lifecycle.test.ts`, `server.test.ts`) construct Chunk objects without `tokenCount`. Fix in subsequent tasks.

**Step 6: Commit chunker changes**

```
git add src/types.ts src/chunker.ts tests/chunker.test.ts
git commit -m "feat(chunk): add headingTokens and tokenCount to Chunk type (B9, C14)

Precompute headingTokens (Set<string>) during chunking from heading,
merged_headings, and fm.topic/first # heading (for whole-file chunks).
tokenCount is an enabler for future removal of tokens array from runtime
objects — standalone perf benefit is negligible (~0.12 ns/op).

B10 (extractSnippet re-tokenization) accepted as-is: CamelCase splitting
in tokenize() prevents cheap approximation for line-level scoring."
```

### Task 4: Update BM25 to use precomputed fields (B9, C14)

**Files:**
- Modify: `src/bm25.ts`
- Test: `tests/bm25.test.ts`

**Step 1: Write failing tests for new headingBoostMultiplier signature**

In `tests/bm25.test.ts`, add a new test in the `heading boost` describe block:

```typescript
it('accepts precomputed headingTokens Set', () => {
  const headingTokens = new Set(['hook', 'guid']);
  // 2/2 coverage → boost applied
  expect(headingBoostMultiplier(['hook', 'guid'], headingTokens)).toBeGreaterThan(1.0);
  // 0/2 coverage → no boost
  expect(headingBoostMultiplier(['skill', 'overview'], headingTokens)).toBe(1.0);
  // undefined → no boost
  expect(headingBoostMultiplier(['hook'], undefined)).toBe(1.0);
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -- --reporter verbose 2>&1 | grep 'precomputed'`
Expected: FAIL — wrong number of arguments

**Step 3: Change headingBoostMultiplier signature**

In `src/bm25.ts`, replace the `headingBoostMultiplier` function:

```typescript
/**
 * Post-score multiplier for heading relevance.
 * Returns 1.0 (no boost) when headingTokens is empty/undefined or coverage is below threshold.
 * Coverage formula: |unique(queryTerms) ∩ headingTokens| / |unique(queryTerms)|
 */
export function headingBoostMultiplier(
  queryTerms: string[],
  headingTokens: Set<string> | undefined,
): number {
  if (!headingTokens || headingTokens.size === 0) return 1.0;
  const { headingBoost, headingMinCoverage } = BM25_CONFIG;

  const uniqueQueryTerms = new Set(queryTerms);
  if (uniqueQueryTerms.size === 0) return 1.0;

  let matches = 0;
  for (const term of uniqueQueryTerms) {
    if (headingTokens.has(term)) matches++;
  }

  const coverage = matches / uniqueQueryTerms.size;
  return coverage >= headingMinCoverage ? 1.0 + headingBoost : 1.0;
}
```

**Step 4: Update search() to pass headingTokens**

In `src/bm25.ts`, in the `search` function, change:

```typescript
// Before:
headingBoostMultiplier(queryTerms, index.chunks[idx].heading, index.chunks[idx].merged_headings),

// After:
headingBoostMultiplier(queryTerms, index.chunks[idx].headingTokens),
```

**Step 5: Use tokenCount in bm25Score and buildBM25Index**

In `src/bm25.ts`:

1. In `bm25Score`: change `const dl = chunk.tokens.length;` to `const dl = chunk.tokenCount;`

2. In `buildBM25Index`: change the avgDocLength computation:
   ```typescript
   // Before:
   avgDocLength: chunks.length > 0 ? chunks.reduce((sum, c) => sum + c.tokens.length, 0) / chunks.length : 0,

   // After:
   avgDocLength: chunks.length > 0 ? chunks.reduce((sum, c) => sum + c.tokenCount, 0) / chunks.length : 0,
   ```

**Step 6: Update makeChunk helper in bm25.test.ts**

In `tests/bm25.test.ts`, update the `makeChunk` function:

```typescript
function makeChunk(id: string, content: string, tokens: string[], heading?: string, merged_headings?: string[]): Chunk {
  // Compute headingTokens from heading and merged_headings
  const headingTokens = new Set<string>();
  if (heading) for (const t of tokenize(heading)) headingTokens.add(t);
  if (merged_headings) for (const h of merged_headings) for (const t of tokenize(h)) headingTokens.add(t);

  return {
    id,
    content,
    tokens,
    tokenCount: tokens.length,
    termFreqs: computeTermFreqs(tokens),
    category: 'test',
    tags: [],
    source_file: 'test.md',
    heading,
    merged_headings,
    headingTokens: headingTokens.size > 0 ? headingTokens : undefined,
  };
}
```

Add `tokenize` to the imports:
```typescript
import { tokenize } from '../src/tokenizer.js';
```

**Step 7: Update all direct headingBoostMultiplier test calls**

Find all direct calls to `headingBoostMultiplier` in `bm25.test.ts` and update to the new signature. Pattern:

```typescript
// Before:
headingBoostMultiplier(['hook', 'document', 'guid'], '## Hooks', undefined)

// After:
headingBoostMultiplier(['hook', 'document', 'guid'], new Set(tokenize('## Hooks')))
```

All occurrences:
- `heading boost` describe: "does not boost when heading coverage is below threshold" — 1 call
- `heading boost` describe: "does not boost merged_headings below coverage threshold" — 1 call
- Search integration tests with `makeChunkWithCategory` — update to include `tokenCount` and `headingTokens`

**Step 8: Update makeChunkWithCategory in search category tests**

In `tests/bm25.test.ts`, the `makeChunkWithCategory` helper also needs `tokenCount`:

```typescript
function makeChunkWithCategory(id: string, content: string, tokens: string[], category: string): Chunk {
  return {
    id,
    content,
    tokens,
    tokenCount: tokens.length,
    termFreqs: computeTermFreqs(tokens),
    category,
    tags: [],
    source_file: `${category}/test.md`,
  };
}
```

**Step 9: Update lifecycle.test.ts makeMockIndex**

In `tests/lifecycle.test.ts`, add `tokenCount: 2` to the chunk creation in `makeMockIndex`:

```typescript
const chunks: Chunk[] = Array.from({ length: chunkCount }, (_, i) => ({
  id: `chunk-${i}`,
  content: `content ${i}`,
  tokens: ['content', `${i}`],
  tokenCount: 2,
  termFreqs: new Map([['content', 1], [`${i}`, 1]]),
  category: 'hooks',
  tags: [],
  source_file: `hooks/test-${i}.md`,
}));
```

**Step 10: Update server.test.ts test chunk**

In `tests/server.test.ts`, add `tokenCount: 2` to the chunk in the `search_docs tool with category` test:

```typescript
const chunks = [{
  id: 'test',
  content: 'test content',
  tokens: ['test', 'content'],
  tokenCount: 2,
  termFreqs: computeTermFreqs(['test', 'content']),
  category: 'hooks',
  tags: [],
  source_file: 'hooks/test.md',
}];
```

**Step 11: Run all tests**

Run: `npm test`
Expected: All tests pass (368 + new tests from Task 3 Step 1)

**Step 12: Commit**

```
git add src/bm25.ts tests/bm25.test.ts tests/lifecycle.test.ts tests/server.test.ts
git commit -m "perf(bm25): use precomputed headingTokens and tokenCount (B9, C14)

headingBoostMultiplier now takes Set<string> instead of re-tokenizing
heading strings on every search call. bm25Score uses chunk.tokenCount
instead of chunk.tokens.length."
```

### Task 5: Update index-cache serialization

**Files:**
- Modify: `src/index-cache.ts`
- Test: (existing tests cover serialization round-trip)

**Step 1: Write failing test for new serialized fields**

In a new test or existing test, verify round-trip:

```typescript
// In tests/bm25.test.ts or a new serialization test section
it('round-trips headingTokens and tokenCount through serialization', async () => {
  const { serializeIndex, deserializeIndex, parseSerializedIndex } = await import('../src/index-cache.js');
  const chunks = [
    makeChunk('test', 'hooks guide', ['hook', 'guid'], '## Hooks Guide'),
  ];
  const index = buildBM25Index(chunks);
  const serialized = serializeIndex(index, 'hash123');
  const parsed = parseSerializedIndex(serialized);
  expect(parsed).not.toBeNull();
  const restored = deserializeIndex(parsed!);

  expect(restored.chunks[0].tokenCount).toBe(2);
  expect(restored.chunks[0].headingTokens).toBeInstanceOf(Set);
  expect(restored.chunks[0].headingTokens!.has('hook')).toBe(true);
  expect(restored.chunks[0].headingTokens!.has('guid')).toBe(true);
});
```

**Step 2: Run test to verify it fails**

Expected: FAIL — `headingTokens` and `tokenCount` not in serialized schema

**Step 3: Update SerializedChunk and schema**

In `src/index-cache.ts`:

1. Add to `SerializedChunk` interface:
   ```typescript
   headingTokens?: string[];
   tokenCount: number;
   ```

2. Update `SerializedChunkSchema`:
   ```typescript
   headingTokens: z.array(z.string()).optional(),
   tokenCount: z.number(),
   ```

3. Bump `INDEX_FORMAT_VERSION` from `2` to `3`:
   ```typescript
   export const INDEX_FORMAT_VERSION = 3; // Bumped for headingTokens + tokenCount
   ```

4. Update `serializeIndex` chunk mapping:
   ```typescript
   chunks: index.chunks.map((c) => ({
     // ... existing fields ...
     headingTokens: c.headingTokens ? Array.from(c.headingTokens) : undefined,
     tokenCount: c.tokenCount,
   })),
   ```

5. Update `deserializeIndex` chunk mapping:
   ```typescript
   chunks: serialized.chunks.map((c) => ({
     // ... existing fields ...
     headingTokens: c.headingTokens ? new Set(c.headingTokens) : undefined,
     tokenCount: c.tokenCount,
   })),
   ```

**Step 4: Run all tests**

Run: `npm test`
Expected: All tests pass. The VERSION bump will cause lifecycle tests that use the mock cache with `version: INDEX_FORMAT_VERSION` to still work because they import the constant.

**Step 5: Commit**

```
git add src/index-cache.ts tests/bm25.test.ts
git commit -m "feat(cache): serialize headingTokens and tokenCount, bump INDEX_FORMAT_VERSION to 3

New fields on Chunk (headingTokens: Set<string>, tokenCount: number) are
now persisted in the index cache. Existing caches will be rebuilt on
next load due to version bump."
```

### Task 6: PR5 final verification and PR creation

**Step 1: Run full test suite**

Run: `npm test`
Expected: All tests pass (368 baseline + ~5 new = ~373)

**Step 2: Type check**

Run: `npx tsc --noEmit`
Expected: Clean

**Step 3: Verify no regressions with golden queries**

Run: `npm test -- tests/golden-queries.test.ts --reporter verbose`
Expected: All golden query tests pass — search quality unchanged

**Step 4: Create PR**

```
git push -u origin perf/b9-c2-c14-bm25-tokens
gh pr create --base main --title "perf: precompute heading tokens and token count (B9, C2, C14)" --body "..."
```

**Step 5: Merge PR**

After CI passes: `gh pr merge --squash`
Pull to main: `git checkout main && git pull`

---

## PR6: `fix/b4-b7-cache-hardening`

**Branch:** `fix/b4-b7-cache-hardening` from `main` (after PR5 merged)

**Findings:** B4 (no ingestion version in cache), B7 (unbounded stale cache)

**B8 disposition (Codex R1):** Dropped. All four BM25 params (k1, b, headingBoost, headingMinCoverage) are query-time only — they don't affect the serialized index structure (docFrequency, invertedIndex, avgDocLength). Cache invalidation should track what affects stored data, not what affects how you use the data. Additionally, the Zod schema silently strips headingBoost/headingMinCoverage (R8), making partial checking internally inconsistent.

**Files:**
- Modify: `src/index-cache.ts` — add `INGESTION_VERSION`, update metadata schema
- Modify: `src/lifecycle.ts` — add B4 cache validation check
- Modify: `src/loader.ts` — add B7 stale cache `DOCS_CACHE_MAX_STALE_MS` limit
- Modify: `tests/lifecycle.test.ts` — add B4 cache validation tests
- Modify: `tests/loader.test.ts` — add B7 stale cache tests

### Task 7: B4 — Add INGESTION_VERSION to cache validation

**Files:**
- Modify: `src/index-cache.ts`
- Modify: `src/lifecycle.ts`
- Test: `tests/lifecycle.test.ts`

**Codex review note (R1):** B8 (BM25 param checks) dropped entirely. All BM25 params are query-time only and don't affect the serialized index. Checking k1/b but not headingBoost/headingMinCoverage was internally inconsistent. Cache policy is structural-only: invalidate when the stored data would differ, not when scoring parameters change.

**Codex review note (R2):** `PARSER_VERSION` renamed to `INGESTION_VERSION` because five subsystems shape the chunk corpus without changing the content hash: `parser.ts`, `frontmatter.ts`, `categories.ts`, `chunk-helpers.ts`, `loader.ts`. A parser-only constant gives false coverage.

**Step 1: Write failing test for INGESTION_VERSION cache check (B4)**

In `tests/lifecycle.test.ts`, add to the `cache version checks` describe block:

```typescript
it('rebuilds when ingestionVersion mismatches (B4)', async () => {
  const serializedIndex = {
    version: INDEX_FORMAT_VERSION,
    contentHash: 'abc123',
    metadata: {
      tokenizerVersion: TOKENIZER_VERSION,
      chunkerVersion: CHUNKER_VERSION,
      ingestionVersion: 999, // Wrong version
    },
  };

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(serializedIndex),
    readCacheFn: vi.fn().mockResolvedValue(serializedIndex),
  });
  const state = new ServerState(deps);

  await state.ensureIndex();

  expect(deps.buildIndexFn).toHaveBeenCalledOnce();
  expect(deps.deserializeIndexFn).not.toHaveBeenCalled();
});
```

**Step 2: Update the existing "uses cached index when all versions match" test**

The existing test needs `ingestionVersion` added to the serialized index mock to continue matching:

```typescript
it('uses cached index when all versions match', async () => {
  const mockIndex = makeMockIndex();
  const serializedIndex = {
    version: INDEX_FORMAT_VERSION,
    contentHash: 'abc123',
    metadata: {
      tokenizerVersion: TOKENIZER_VERSION,
      chunkerVersion: CHUNKER_VERSION,
      ingestionVersion: INGESTION_VERSION,  // NEW (B4)
    },
    chunks: [],
    docFreqs: [],
    avgDocLength: 2,
  };
  // ... rest unchanged
});
```

**Step 3: Run tests to verify they fail**

Run: `npm test -- tests/lifecycle.test.ts --reporter verbose`
Expected: FAIL — `INGESTION_VERSION` not exported, cache validation doesn't check it

**Step 4: Add INGESTION_VERSION to index-cache.ts**

In `src/index-cache.ts`:

1. Add constant with documented bump triggers:
   ```typescript
   /**
    * Bump when any corpus-shaping subsystem changes:
    * - parser.ts (section/heading extraction)
    * - frontmatter.ts (metadata extraction)
    * - categories.ts (URL-to-category mapping)
    * - chunk-helpers.ts (term freq computation, chunk ID generation)
    * - loader.ts (content fetching/parsing pipeline)
    * - url-helpers.ts (URL normalization — affects category derivation and chunk IDs) (D5)
    *
    * NOT included (separately versioned):
    * - tokenizer.ts → TOKENIZER_VERSION
    * - chunker.ts → CHUNKER_VERSION
    */
   export const INGESTION_VERSION = 1;
   ```

2. Add `ingestionVersion` to metadata in `SerializedIndex` interface:
   ```typescript
   metadata?: {
     createdAt: number;
     bm25?: { k1: number; b: number };
     tokenizerVersion?: number;
     chunkerVersion?: number;
     ingestionVersion?: number;  // NEW (B4)
   };
   ```

3. Add to `SerializedIndexSchema` metadata:
   ```typescript
   ingestionVersion: z.number().optional(),
   ```

4. Include in `serializeIndex` metadata:
   ```typescript
   metadata: {
     createdAt: Date.now(),
     bm25: BM25_CONFIG,
     tokenizerVersion: TOKENIZER_VERSION,
     chunkerVersion: CHUNKER_VERSION,
     ingestionVersion: INGESTION_VERSION,
   },
   ```

**Step 5: Add cache validation check to lifecycle.ts**

In `src/lifecycle.ts`:

1. Update imports:
   ```typescript
   import { INDEX_FORMAT_VERSION, TOKENIZER_VERSION, CHUNKER_VERSION, INGESTION_VERSION } from './index-cache.js';
   ```
   (No `BM25_CONFIG` import needed — B8 dropped)

2. Update the cache validation block in `doLoadIndex` (~line 121-127):
   ```typescript
   if (
     cached &&
     cached.version === INDEX_FORMAT_VERSION &&
     cached.contentHash === contentHash &&
     cached.metadata?.tokenizerVersion === TOKENIZER_VERSION &&
     cached.metadata?.chunkerVersion === CHUNKER_VERSION &&
     cached.metadata?.ingestionVersion === INGESTION_VERSION   // B4 NEW
   ) {
   ```

**Step 6: Update lifecycle.test.ts imports**

Add `INGESTION_VERSION` to the import:
```typescript
import { INDEX_FORMAT_VERSION, TOKENIZER_VERSION, CHUNKER_VERSION, INGESTION_VERSION } from '../src/index-cache.js';
```

**Step 7: Run tests**

Run: `npm test`
Expected: All tests pass

**Step 8: Commit**

```
git add src/index-cache.ts src/lifecycle.ts tests/lifecycle.test.ts
git commit -m "fix(cache): add INGESTION_VERSION to cache validation (B4)

Cache now invalidates when any corpus-shaping subsystem changes.
INGESTION_VERSION covers parser, frontmatter, categories, chunk-helpers,
loader, and url-helpers (D5) — broader than a parser-only constant. BM25 params (k1, b,
headingBoost, headingMinCoverage) are NOT checked because they are
query-time only and don't affect the serialized index structure."
```

### Task 8: B7 — Stale cache max stale limit

**Files:**
- Modify: `src/loader.ts`
- Test: `tests/loader.test.ts`

**Codex review note (R5):** The 48h "very stale" warning tier has been removed. The hardcoded threshold was detached from `CACHE_TTL_MS` (configurable, default 24h) — an operator setting `CACHE_TTL_MS` to 1h would get silent stale-cache serving for 47h. Instead, keep only: (1) the existing `console.warn("Using cached docs (Xh old)")` message for all stale fallbacks, and (2) the new `DOCS_CACHE_MAX_STALE_MS` env var for hard rejection.

**Step 1: Write failing tests for stale cache handling**

In `tests/loader.test.ts`, add a new describe block (or add to an existing stale-cache section):

**Codex deep review note (D4):** Tests must force the stale fallback path. A 12h-old cache with
default 24h `CACHE_TTL_MS` is treated as *fresh* by `readCacheIfFresh`, so the stale fallback is
never reached. Two approaches: (a) set `CACHE_TTL_MS` to a low value (e.g., `'1'` = 1ms) so the
cache is always stale, or (b) use ages well beyond 24h. Approach (b) is clearer for readers.
Also: `cached.age > maxStaleMs` uses strict `>`, so the boundary test must verify `age === max`
is accepted. Added as 5th test.

```typescript
describe('stale cache handling (B7)', () => {
  let tmpDir: string;

  beforeEach(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-stale-'));
    process.env.MIN_SECTION_COUNT = '0';
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('network down'));
  });

  afterEach(async () => {
    delete process.env.DOCS_CACHE_MAX_STALE_MS;
    delete process.env.CACHE_TTL_MS;
    delete process.env.MIN_SECTION_COUNT;
    vi.restoreAllMocks();
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  // Helper: write a cache file and backdate it
  async function writeStaleCacheFile(ageMs: number): Promise<string> {
    const cachePath = path.join(tmpDir, 'llms-full.txt');
    const content = '# Test\n\nMinimal valid content for testing.';
    await fs.writeFile(cachePath, content);
    const pastTime = new Date(Date.now() - ageMs);
    await fs.utimes(cachePath, pastTime, pastTime);
    return cachePath;
  }

  it('rejects cache exceeding DOCS_CACHE_MAX_STALE_MS', async () => {
    const ageMs = 72 * 3600_000; // 72h
    await writeStaleCacheFile(ageMs);
    process.env.DOCS_CACHE_MAX_STALE_MS = String(24 * 3600_000); // 24h limit
    process.env.CACHE_TTL_MS = '1'; // force stale path

    const warnSpy = vi.spyOn(console, 'error');
    await expect(fetchAndParse(tmpDir)).rejects.toThrow();
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('exceeds max stale limit')
    );
  });

  it('accepts cache within DOCS_CACHE_MAX_STALE_MS', async () => {
    const ageMs = 12 * 3600_000; // 12h
    await writeStaleCacheFile(ageMs);
    process.env.DOCS_CACHE_MAX_STALE_MS = String(24 * 3600_000); // 24h limit
    process.env.CACHE_TTL_MS = '1'; // force stale path

    const warnSpy = vi.spyOn(console, 'warn');
    const result = await fetchAndParse(tmpDir);
    expect(result).toBeDefined();
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Using cached docs')
    );
  });

  it('accepts any age when DOCS_CACHE_MAX_STALE_MS is unset', async () => {
    const ageMs = 168 * 3600_000; // 7 days
    await writeStaleCacheFile(ageMs);
    delete process.env.DOCS_CACHE_MAX_STALE_MS; // no limit
    process.env.CACHE_TTL_MS = '1'; // force stale path

    const warnSpy = vi.spyOn(console, 'warn');
    const result = await fetchAndParse(tmpDir);
    expect(result).toBeDefined();
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Using cached docs')
    );
  });

  it('ignores invalid DOCS_CACHE_MAX_STALE_MS values', async () => {
    const ageMs = 72 * 3600_000; // 72h
    await writeStaleCacheFile(ageMs);
    process.env.DOCS_CACHE_MAX_STALE_MS = 'banana'; // invalid
    process.env.CACHE_TTL_MS = '1'; // force stale path

    // "banana" → NaN → treated as 0 (no limit) → serves stale cache
    const result = await fetchAndParse(tmpDir);
    expect(result).toBeDefined();
  });

  it('accepts cache at exactly DOCS_CACHE_MAX_STALE_MS boundary (D4)', async () => {
    // strict > comparison: age === max should be accepted
    const maxMs = 24 * 3600_000;
    await writeStaleCacheFile(maxMs); // exactly at limit
    process.env.DOCS_CACHE_MAX_STALE_MS = String(maxMs);
    process.env.CACHE_TTL_MS = '1'; // force stale path

    const result = await fetchAndParse(tmpDir);
    expect(result).toBeDefined();
  });
});
```

Each test:
- Creates a temp directory for cache isolation
- Sets `CACHE_TTL_MS = '1'` to force the stale fallback path (D4 fix)
- Uses `fs.utimes` to set deterministic cache file age
- Cleans up both `DOCS_CACHE_MAX_STALE_MS` and `CACHE_TTL_MS` env vars in afterEach

**Step 2: Run tests to verify they fail**

Run: `npm test -- tests/loader.test.ts --reporter verbose 2>&1 | grep -A2 'stale cache'`
Expected: FAIL — no stale-specific rejection logic exists

**Step 3: Add getMaxStaleCacheMs helper to loader.ts**

In `src/loader.ts`, add near the other env-var helpers:

```typescript
/**
 * Maximum age (ms) for stale cache to be accepted on fetch failure.
 * 0 = no limit (accept any stale cache). Default: 0.
 */
function getMaxStaleCacheMs(): number {
  const raw = process.env.DOCS_CACHE_MAX_STALE_MS?.trim();
  if (!raw) return 0;
  const val = Number(raw);
  if (!Number.isFinite(val) || val < 0) return 0;
  return val;
}
```

**Step 4: Add stale cache rejection logic**

In `src/loader.ts`, in the `fetchAndParse` catch block, update the stale cache fallback (currently around lines 239-257):

```typescript
const cached = await readCache(cachePath);
if (cached) {
  const ageHours = (cached.age / 3600000).toFixed(1);

  // Check optional max stale limit (B7)
  const maxStaleMs = getMaxStaleCacheMs();
  if (maxStaleMs > 0 && cached.age > maxStaleMs) {
    const maxHours = (maxStaleMs / 3600000).toFixed(1);
    console.error(
      `Stale cache rejected: ${ageHours}h old exceeds max stale limit of ${maxHours}h`
    );
    throw err;
  }

  console.warn(`Using cached docs (${ageHours}h old)`);

  return {
    sections: parseSections(cached.content),
    contentHash: hashContent(cached.content),
  };
}
```

**Step 5: Run tests**

Run: `npm test`
Expected: All tests pass

**Step 6: Commit**

```
git add src/loader.ts tests/loader.test.ts
git commit -m "fix(loader): add DOCS_CACHE_MAX_STALE_MS hard limit for stale cache (B7)

New optional DOCS_CACHE_MAX_STALE_MS env var sets a hard limit on stale
cache age. Cache older than the limit is rejected on fetch failure
instead of silently served. Default: no limit (existing behavior).
The existing 'Using cached docs (Xh old)' warning covers all stale
fallbacks — no separate warning tier needed."
```

### Task 9: PR6 final verification and PR creation

**Step 1: Run full test suite**

Run: `npm test`
Expected: All tests pass

**Step 2: Type check**

Run: `npx tsc --noEmit`
Expected: Clean

**Step 3: Create and merge PR**

```
git push -u origin fix/b4-b7-cache-hardening
gh pr create --base main --title "fix: add ingestion version cache check, stale cache limit (B4, B7)" --body "..."
gh pr merge --squash
git checkout main && git pull
```

---

## PR7: `test/b12-b13-coverage`

**Branch:** `test/b12-b13-coverage` from `main` (after PR6 merged)

**Findings:** B12 (14/24 categories without golden queries), B13 (integration test skipped)

**Files:**
- Modify: `tests/golden-queries.test.ts` — add 8 mock sections + 8 golden queries
- Read: `tests/integration.test.ts` — assess feasibility
- Test-only PR: no source changes

### Task 10: B12 — Add 8 priority golden query categories

**Files:**
- Modify: `tests/golden-queries.test.ts`

The 8 missing priority categories: `commands`, `plugins`, `settings`, `memory`, `cli`, `interactive`, `desktop`, `overview`

**Step 1: Add mock sections to MOCK_LLMS_CONTENT**

Add 8 new sections to `MOCK_LLMS_CONTENT` in `tests/golden-queries.test.ts`. Each section needs:
- A `# Title` + `Source: https://code.claude.com/docs/en/<url-segment>` header
- Content with category-specific keywords
- At least one H2 subsection

New sections to add (after the existing Permissions section):

```
---
# Slash Commands
Source: https://code.claude.com/docs/en/slash-commands

Create and use custom slash commands in Claude Code for task automation.

## Defining custom commands

Create command files in .claude/commands/ with YAML frontmatter specifying name and description. Commands can accept arguments and execute shell scripts.

## Built-in commands

Claude Code includes built-in slash commands like /help, /clear, /compact, and /init for common operations.
---
# Plugins
Source: https://code.claude.com/docs/en/plugins

Extend Claude Code functionality with plugins. Plugins bundle commands, skills, hooks, agents, and MCP servers.

## Plugin structure

A plugin requires a plugin.json manifest file defining its components. Plugins are distributed via marketplaces.

## Installing plugins

Install plugins from marketplaces using claude plugin install or by specifying a local path.
---
# Settings
Source: https://code.claude.com/docs/en/settings

Configure Claude Code behavior through settings.json and environment variables.

## Settings hierarchy

Settings follow a hierarchy: global (~/.claude/settings.json), project (.claude/settings.json), and environment variables. More specific settings override general ones.

## Common settings

Configure model preferences, permission modes, and tool restrictions through the settings system.
---
# Memory and CLAUDE.md
Source: https://code.claude.com/docs/en/memory

Claude Code uses CLAUDE.md files as persistent memory across sessions. Project instructions are stored in CLAUDE.md.

## CLAUDE.md locations

CLAUDE.md files can exist at global (~/.claude/CLAUDE.md), project root, and subdirectory levels. Each level adds context for that scope.

## Auto-memory

Claude Code can automatically save insights to memory files for future reference across sessions.
---
# CLI Reference
Source: https://code.claude.com/docs/en/cli-reference

Command-line interface reference for Claude Code. Run claude with various flags and options.

## CLI flags

Common CLI flags include --model for model selection, --allowedTools for tool restrictions, and --print for non-interactive output mode.

## Environment variables

Configure Claude Code behavior through environment variables like ANTHROPIC_API_KEY and CLAUDE_DEBUG.
---
# Interactive Features
Source: https://code.claude.com/docs/en/interactive-mode

Interactive features in Claude Code including vim mode, multi-line editing, and fast mode.

## Vim mode

Enable vim keybindings for efficient text editing in the Claude Code terminal interface.

## Fast mode

Toggle fast mode for faster responses. Fast mode uses the same model with optimized output speed.
---
# Desktop Application
Source: https://code.claude.com/docs/en/desktop

Claude Code desktop application for macOS and Windows. Native app with terminal integration.

## Desktop installation

Download and install the Claude Code desktop app from the official website. The desktop app bundles the CLI.

## Desktop features

The desktop app provides a native window, system tray integration, and automatic updates.
---
# Overview
Source: https://code.claude.com/docs/en/overview

Claude Code is an agentic coding tool that lives in your terminal. It understands your codebase and helps with software engineering tasks.

## What Claude Code can do

Claude Code can edit files, run commands, search code, manage git, create pull requests, and more — all from your terminal.

## How Claude Code works

Claude Code operates as an interactive agent with access to tools for file editing, code search, and command execution.
```

**Step 1b: Verify URL segments resolve in SECTION_TO_CATEGORY (R7)**

Before adding golden queries, verify that all 8 new URL segments have corresponding entries in `src/categories.ts` `SECTION_TO_CATEGORY`. Read `categories.ts` and confirm each segment maps to the expected category:

| URL segment | Expected category |
|-------------|------------------|
| `slash-commands` | `commands` |
| `plugins` | `plugins` |
| `settings` | `settings` |
| `memory` | `memory` |
| `cli-reference` | `cli` |
| `interactive-mode` | `interactive` |
| `desktop` | `desktop` |
| `overview` | `overview` |

If any segment is missing from `SECTION_TO_CATEGORY`, the golden query test will fail with a wrong category. Add missing mappings to `categories.ts` if needed (this would be a source change, making PR7 no longer test-only — update the PR description accordingly).

**Step 2: Add golden queries for new categories**

Add to the `goldenQueries` array:

```typescript
// New priority categories (B12)
{ query: 'slash command definition YAML', expectedTopCategory: 'commands' },
{ query: 'plugin manifest structure install', expectedTopCategory: 'plugins' },
{ query: 'settings hierarchy configuration', expectedTopCategory: 'settings' },
{ query: 'CLAUDE.md memory persistent sessions', expectedTopCategory: 'memory' },
{ query: 'CLI flags model allowedTools', expectedTopCategory: 'cli' },
{ query: 'vim mode interactive editing', expectedTopCategory: 'interactive' },
{ query: 'desktop application native install', expectedTopCategory: 'desktop' },
{ query: 'overview agentic terminal tool', expectedTopCategory: 'overview' },
```

**Step 3: Add category existence assertions**

Add to the `new category chunks exist` test:

```typescript
const commandsChunks = index.chunks.filter(c => c.source_file.includes('slash-commands'));
const pluginsChunks = index.chunks.filter(c => c.source_file.includes('plugins'));
const settingsChunks = index.chunks.filter(c => c.source_file.includes('settings'));
const memoryChunks = index.chunks.filter(c => c.source_file.includes('memory'));
const cliChunks = index.chunks.filter(c => c.source_file.includes('cli-reference'));
const interactiveChunks = index.chunks.filter(c => c.source_file.includes('interactive'));
const desktopChunks = index.chunks.filter(c => c.source_file.includes('desktop'));
const overviewChunks = index.chunks.filter(c => c.source_file.includes('overview'));

expect(commandsChunks.length).toBeGreaterThan(0);
expect(pluginsChunks.length).toBeGreaterThan(0);
// ... etc for all 8

for (const chunk of commandsChunks) expect(chunk.category).toBe('commands');
for (const chunk of pluginsChunks) expect(chunk.category).toBe('plugins');
for (const chunk of settingsChunks) expect(chunk.category).toBe('settings');
for (const chunk of memoryChunks) expect(chunk.category).toBe('memory');
for (const chunk of cliChunks) expect(chunk.category).toBe('cli');
for (const chunk of interactiveChunks) expect(chunk.category).toBe('interactive');
for (const chunk of desktopChunks) expect(chunk.category).toBe('desktop');
for (const chunk of overviewChunks) expect(chunk.category).toBe('overview');
```

**Step 4: Run tests**

Run: `npm test -- tests/golden-queries.test.ts --reporter verbose`
Expected: All golden query tests pass (existing + 8 new)

**Step 5: Commit**

```
git add tests/golden-queries.test.ts
git commit -m "test: add golden queries for 8 priority categories (B12)

Cover commands, plugins, settings, memory, cli, interactive, desktop,
and overview. 18/24 categories now have golden query coverage (up from
10/24)."
```

### Task 11: B13 — Integration test assessment

**Files:**
- Read: `tests/integration.test.ts`

**Step 1: Read integration test**

Read `tests/integration.test.ts` to understand what's skipped and why.

**Step 2: Assess feasibility**

Evaluate:
- What does the test attempt to do?
- Why is it skipped?
- What would be needed to unskip it?
- Is a mock server approach viable?
- Cost vs. benefit assessment
- **(D7)** Check for latent API-shape bug: `loadFromOfficial` returns `{ files, contentHash }` but
  the skipped test may treat it as array-like. If confirmed, document the fix needed alongside
  the feasibility assessment.

**Step 3: Document assessment in commit**

Write assessment as a code comment in the integration test file (replacing the `it.skip` or adding context above it). If the test can be unskipped with reasonable effort, do so. If not, document why.

**Step 4: Commit**

```
git add tests/integration.test.ts
git commit -m "docs: assess integration test feasibility (B13)

[Assessment details in commit body]"
```

### Task 12: PR7 final verification and PR creation

**Step 1: Run full test suite**

Run: `npm test`
Expected: All tests pass

**Step 2: Create and merge PR**

```
git push -u origin test/b12-b13-coverage
gh pr create --base main --title "test: golden query coverage for 8 categories + integration test assessment (B12, B13)" --body "..."
gh pr merge --squash
git checkout main && git pull
```

---

## Verification

After all 3 PRs merged:

1. **Test count:** Should be ~385+ (368 baseline + ~17 new across PR5-PR7)
2. **Type check:** `npx tsc --noEmit` from `packages/mcp-servers/claude-code-docs/` — clean
3. **Golden queries:** All 25+ golden queries pass across 18+ categories
4. **Cache invalidation:** Delete `~/Library/Caches/claude-code-docs/llms-full.index.json`, run server, verify fresh index build with `INDEX_FORMAT_VERSION=3`
5. **Search quality:** Manual `search_docs` queries via MCP should return same-quality results
6. **Whole-file heading boost:** Verify a small doc with `# Title` gets heading boost (R3 fix)
7. **Structural cache policy:** Verify changing `BM25_CONFIG.k1` does NOT trigger cache rebuild (B8 dropped)
8. **fm.topic heading derivation:** Verify an official doc section (with `fm.topic` set, no H1 in body) gets heading boost (D3 fix)
9. **Merge test non-vacuity:** Verify the merge test precondition `expect(mergedChunk).toBeDefined()` actually passes (D1 fix)
10. **Stale cache boundary:** Verify cache at exactly `DOCS_CACHE_MAX_STALE_MS` is accepted (D4 boundary test)
11. **Remediation plan status:** Phase 3 complete (PR5-PR7 merged). Only PR8 (cleanup) remains.

## Key References

| Resource | Path |
|----------|------|
| Remediation plan | `docs/plans/2026-03-03-claude-code-docs-remediation-plan.md` |
| Full audit | `docs/audits/2026-03-03-claude-code-docs-full-audit.md` |
| Source directory | `packages/mcp-servers/claude-code-docs/src/` |
| Test directory | `packages/mcp-servers/claude-code-docs/tests/` |
| BM25 engine | `src/bm25.ts` — search, headingBoostMultiplier, extractSnippet |
| Chunk type | `src/types.ts` — Chunk interface |
| Chunker | `src/chunker.ts` — chunkFile, createSplitChunk, combineChunks |
| Index cache | `src/index-cache.ts` — serialization, version constants |
| Lifecycle | `src/lifecycle.ts` — ServerState, cache validation |
| Loader | `src/loader.ts` — fetchAndParse, stale cache fallback |
| Tokenizer | `src/tokenizer.ts` — tokenize (Porter stemmer + CamelCase) |
| Chunk helpers | `src/chunk-helpers.ts` — computeTermFreqs, generateChunkId |
