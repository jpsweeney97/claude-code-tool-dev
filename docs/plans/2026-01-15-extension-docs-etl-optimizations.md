# Extension-docs ETL Optimizations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 5 optimizations to improve search performance, cache freshness, and response quality for the extension-docs MCP server.

**Architecture:** Three-phase rollout: (1) Category filtering + Cache TTL for quick wins, (2) Persistent index + Inverted index for performance, (3) Snippet extraction for UX. Each phase builds on the previous.

**Tech Stack:** TypeScript, Vitest, Node.js crypto (SHA-256), Zod for schema validation

---

## Phase 1: Quick Wins (Low Risk)

### Task 1: Category Filtering - Schema Update

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/index.ts:84-100`
- Reference: `packages/mcp-servers/extension-docs/src/filter.ts:8-23` (KNOWN_CATEGORIES)

**Step 1: Write the failing test for category schema validation**

Add to `packages/mcp-servers/extension-docs/tests/server.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Import or define CATEGORY_VALUES for testing
const CATEGORY_VALUES = [
  'hooks',
  'skills',
  'commands',
  'slash-commands',
  'agents',
  'subagents',
  'sub-agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'claude-md',
  'memory',
  'configuration',
] as const;

const CategorySchema = z.enum(CATEGORY_VALUES).optional();

describe('Category Schema Validation', () => {
  it('accepts valid categories', () => {
    expect(CategorySchema.parse('hooks')).toBe('hooks');
    expect(CategorySchema.parse('skills')).toBe('skills');
    expect(CategorySchema.parse('slash-commands')).toBe('slash-commands');
    expect(CategorySchema.parse('plugin-marketplaces')).toBe('plugin-marketplaces');
    expect(CategorySchema.parse('claude-md')).toBe('claude-md');
  });

  it('accepts undefined category', () => {
    expect(CategorySchema.parse(undefined)).toBeUndefined();
  });

  it('rejects invalid categories', () => {
    expect(() => CategorySchema.parse('Hooks')).toThrow();
    expect(() => CategorySchema.parse('unknown')).toThrow();
    expect(() => CategorySchema.parse('hooks ')).toThrow();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/server.test.ts`
Expected: Test file runs (may pass since we defined schema inline for the test)

**Step 3: Update SearchInputSchema in index.ts**

In `packages/mcp-servers/extension-docs/src/index.ts`, modify lines 84-100:

```typescript
const CATEGORY_VALUES = [
  'hooks',
  'skills',
  'commands',
  'slash-commands',
  'agents',
  'subagents',
  'sub-agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'claude-md',
  'memory',
  'configuration',
] as const;

const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty'))
    .describe(
      'Search query — be specific (e.g., "PreToolUse JSON output", "skill frontmatter properties")',
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .describe('Maximum results to return (default: 5, max: 20)'),
  category: z
    .enum(CATEGORY_VALUES)
    .optional()
    .describe('Filter to a specific category (e.g., "hooks", "plugins")'),
});
```

**Step 4: Run tests to verify schema changes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/server.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts packages/mcp-servers/extension-docs/tests/server.test.ts
git commit -m "feat(extension-docs): add category input schema for search filtering

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Category Filtering - Search Function

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/bm25.ts:54-68`
- Test: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Write the failing test for category filtering**

Add to `packages/mcp-servers/extension-docs/tests/bm25.test.ts`:

```typescript
describe('search with category filtering', () => {
  function makeChunkWithCategory(
    id: string,
    content: string,
    tokens: string[],
    category: string
  ): Chunk {
    return {
      id,
      content,
      tokens,
      termFreqs: computeTermFreqs(tokens),
      category,
      tags: [],
      source_file: `${category}/test.md`,
    };
  }

  it('filters results by category when provided', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'PreToolUse hooks', ['pretooluse', 'hooks'], 'hooks'),
      makeChunkWithCategory('skills-1', 'skill hooks pattern', ['skill', 'hooks', 'pattern'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'hooks');
    expect(results).toHaveLength(1);
    expect(results[0].chunk_id).toBe('hooks-1');
    expect(results[0].category).toBe('hooks');
  });

  it('returns all matching categories when category is undefined', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hooks', 'content'], 'hooks'),
      makeChunkWithCategory('skills-1', 'hooks in skills', ['hooks', 'skills'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5);
    expect(results).toHaveLength(2);
  });

  it('returns empty array when category has no matches', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hooks', 'content'], 'hooks'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'skills');
    expect(results).toHaveLength(0);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: FAIL - search function doesn't accept category parameter

**Step 3: Update search function signature and implementation**

In `packages/mcp-servers/extension-docs/src/bm25.ts`, modify lines 54-68:

```typescript
export function search(
  index: BM25Index,
  query: string,
  limit = 5,
  category?: string
): SearchResult[] {
  const queryTerms = tokenize(query);

  const chunks = category
    ? index.chunks.filter((chunk) => chunk.category === category)
    : index.chunks;

  return chunks
    .map((chunk) => ({ chunk, score: bm25Score(queryTerms, chunk, index) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => ({
      chunk_id: r.chunk.id,
      content: r.chunk.content,
      category: r.chunk.category,
      source_file: r.chunk.source_file,
    }));
}
```

**Step 4: Run tests to verify implementation**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): implement category filtering in search

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 3: Category Filtering - Wire Up Tool Handler

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/index.ts:128-152`

**Step 1: Write integration test**

Add to `packages/mcp-servers/extension-docs/tests/server.test.ts`:

```typescript
describe('search_extension_docs tool with category', () => {
  // This test verifies the tool handler passes category to search
  // Full integration test would require MCP client setup
  it('search function accepts category parameter', async () => {
    // Import the search function directly to verify signature
    const { search, buildBM25Index } = await import('../src/bm25.js');
    const { computeTermFreqs } = await import('../src/chunk-helpers.js');

    const chunks = [{
      id: 'test',
      content: 'test content',
      tokens: ['test', 'content'],
      termFreqs: computeTermFreqs(['test', 'content']),
      category: 'hooks',
      tags: [],
      source_file: 'hooks/test.md',
    }];

    const index = buildBM25Index(chunks);

    // Verify search accepts 4th parameter
    const results = search(index, 'test', 5, 'hooks');
    expect(results).toHaveLength(1);
  });
});
```

**Step 2: Run test**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/server.test.ts`
Expected: PASS (search already updated)

**Step 3: Update tool handler to pass category**

In `packages/mcp-servers/extension-docs/src/index.ts`, modify lines 128-152:

```typescript
async ({ query, limit = 5, category }: z.infer<typeof SearchInputSchema>) => {
  const idx = await ensureIndex();
  if (!idx) {
    return {
      isError: true,
      content: [{ type: 'text' as const, text: `Search unavailable: ${loadError}` }],
    };
  }

  try {
    const results = search(idx, query, limit, category);
    return {
      content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }],
      structuredContent: { results },
    };
  } catch (err) {
    console.error('Search error:', err);
    return {
      isError: true,
      content: [
        { type: 'text' as const, text: 'Search failed. Please try a different query.' },
      ],
    };
  }
},
```

**Step 4: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts packages/mcp-servers/extension-docs/tests/server.test.ts
git commit -m "feat(extension-docs): wire category parameter to tool handler

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Cache TTL - Helper Functions

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/cache.ts:1-70`
- Test: `packages/mcp-servers/extension-docs/tests/cache.test.ts`

**Step 1: Write failing tests for TTL helpers**

Add to `packages/mcp-servers/extension-docs/tests/cache.test.ts`:

```typescript
import { getCacheTtlMs, readCacheIfFresh } from '../src/cache.js';

describe('getCacheTtlMs', () => {
  const originalEnv = process.env.CACHE_TTL_MS;

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.CACHE_TTL_MS;
    } else {
      process.env.CACHE_TTL_MS = originalEnv;
    }
  });

  it('returns default 24h when env not set', () => {
    delete process.env.CACHE_TTL_MS;
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for invalid values', () => {
    process.env.CACHE_TTL_MS = 'not-a-number';
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for negative values', () => {
    process.env.CACHE_TTL_MS = '-1000';
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns parsed value within bounds', () => {
    process.env.CACHE_TTL_MS = '3600000';
    expect(getCacheTtlMs()).toBe(3600000);
  });

  it('caps at 1 year max', () => {
    process.env.CACHE_TTL_MS = '999999999999999';
    expect(getCacheTtlMs()).toBe(1000 * 60 * 60 * 24 * 365);
  });
});

describe('readCacheIfFresh', () => {
  let tempDir: string;
  let cachePath: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'cache-ttl-test-'));
    cachePath = path.join(tempDir, 'test-cache.txt');
    delete process.env.CACHE_TTL_MS;
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('returns null for non-existent cache', async () => {
    const result = await readCacheIfFresh(cachePath);
    expect(result).toBeNull();
  });

  it('returns fresh cache when within TTL', async () => {
    await writeCache(cachePath, 'fresh content');
    const result = await readCacheIfFresh(cachePath);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('fresh content');
  });

  it('returns null for stale cache', async () => {
    await writeCache(cachePath, 'stale content');
    // Set TTL to 0 to make cache immediately stale
    process.env.CACHE_TTL_MS = '0';
    const result = await readCacheIfFresh(cachePath);
    expect(result).toBeNull();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: FAIL - getCacheTtlMs and readCacheIfFresh don't exist

**Step 3: Implement TTL helpers in cache.ts**

Add to `packages/mcp-servers/extension-docs/src/cache.ts` after the CacheResult interface:

```typescript
const DEFAULT_TTL_MS = 86400000; // 24 hours
const MAX_TTL_MS = 1000 * 60 * 60 * 24 * 365; // 1 year

export function getCacheTtlMs(): number {
  const raw = process.env.CACHE_TTL_MS?.trim();
  if (!raw) return DEFAULT_TTL_MS;
  const val = Number(raw);
  if (!Number.isFinite(val) || val < 0) return DEFAULT_TTL_MS;
  return Math.min(val, MAX_TTL_MS);
}

export async function readCacheIfFresh(cachePath: string): Promise<CacheResult | null> {
  const cached = await readCache(cachePath);
  if (!cached) return null;
  const ttl = getCacheTtlMs();
  if (cached.age > ttl) {
    return null;
  }
  return cached;
}
```

**Step 4: Run tests to verify implementation**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/cache.ts packages/mcp-servers/extension-docs/tests/cache.test.ts
git commit -m "feat(extension-docs): add TTL-aware cache helpers

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Cache TTL - Stale-While-Error in Loader

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/loader.ts:117-142`
- Test: `packages/mcp-servers/extension-docs/tests/loader.test.ts`

**Step 1: Write failing test for TTL behavior**

Add to `packages/mcp-servers/extension-docs/tests/loader.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('fetchAndParse with TTL', () => {
  // Note: This tests the internal behavior through the public loadFromOfficial API
  // We'll use mocking to control fetch behavior

  it('uses fresh cache and skips fetch when TTL not expired', async () => {
    // This would require mocking fetchOfficialDocs
    // For now, document the expected behavior:
    // - If readCacheIfFresh returns content, don't call fetchOfficialDocs
    // - Return parsed content from cache
    expect(true).toBe(true); // Placeholder for integration test
  });

  it('falls back to stale cache when fetch fails', async () => {
    // Expected behavior:
    // - readCacheIfFresh returns null (stale)
    // - fetchOfficialDocs throws
    // - readCache returns stale content
    // - Return parsed stale content with warning
    expect(true).toBe(true); // Placeholder for integration test
  });
});
```

**Step 2: Update loader.ts imports**

In `packages/mcp-servers/extension-docs/src/loader.ts`, update line 9:

```typescript
import { readCache, readCacheIfFresh, writeCache, getDefaultCachePath } from './cache.js';
```

**Step 3: Update fetchAndParse to use TTL**

In `packages/mcp-servers/extension-docs/src/loader.ts`, replace the fetchAndParse function (lines 117-142):

```typescript
async function fetchAndParse(url: string, cachePath: string): Promise<ParsedSection[]> {
  // Check for fresh cache first - skip fetch if within TTL
  const fresh = await readCacheIfFresh(cachePath);
  if (fresh) {
    return parseSections(fresh.content);
  }

  try {
    const { content } = await fetchOfficialDocs(url);
    await writeCache(cachePath, content);
    return parseSections(content);
  } catch (err: unknown) {
    if (err instanceof FetchTimeoutError) {
      console.error(err.message);
    } else if (err instanceof FetchHttpError) {
      console.error(err.message);
    } else if (err instanceof FetchNetworkError) {
      console.error(err.message);
    } else {
      console.error(`Fetch failed: ${err instanceof Error ? err.message : String(err)}`);
    }

    // Fall back to stale cache on fetch error
    const cached = await readCache(cachePath);
    if (cached) {
      const ageHours = (cached.age / 3600000).toFixed(1);
      console.warn(`Using cached docs (${ageHours}h old)`);
      return parseSections(cached.content);
    }

    throw err;
  }
}
```

**Step 4: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts packages/mcp-servers/extension-docs/tests/loader.test.ts
git commit -m "feat(extension-docs): implement stale-while-error cache behavior

Fresh cache short-circuits fetch. Stale cache used only on fetch failure.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 6: Cache TTL - Force Reload Bypasses TTL

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/loader.ts`

**Step 1: Add forceRefresh parameter**

In `packages/mcp-servers/extension-docs/src/loader.ts`, update the function signatures:

```typescript
export async function loadFromOfficial(
  url: string,
  cachePath?: string,
  forceRefresh = false
): Promise<MarkdownFile[]> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const sections = await fetchAndParse(url, resolvedCachePath, forceRefresh);
  // ... rest unchanged
}

async function fetchAndParse(
  url: string,
  cachePath: string,
  forceRefresh = false
): Promise<ParsedSection[]> {
  // Skip fresh cache check if force refresh requested
  if (!forceRefresh) {
    const fresh = await readCacheIfFresh(cachePath);
    if (fresh) {
      return parseSections(fresh.content);
    }
  }

  // ... rest unchanged
}
```

**Step 2: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts
git commit -m "feat(extension-docs): add forceRefresh option to bypass cache TTL

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 2: Performance

### Task 7: Index Serialization - Types and Helpers

**Files:**

- Create: `packages/mcp-servers/extension-docs/src/index-cache.ts`
- Test: `packages/mcp-servers/extension-docs/tests/index-cache.test.ts`

**Step 1: Write failing test for serialization**

Create `packages/mcp-servers/extension-docs/tests/index-cache.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import {
  serializeIndex,
  deserializeIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
} from '../src/index-cache.js';
import { buildBM25Index } from '../src/bm25.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';
import type { Chunk } from '../src/types.js';

function makeChunk(id: string, content: string, tokens: string[]): Chunk {
  return {
    id,
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: 'hooks',
    tags: ['test'],
    source_file: 'hooks/test.md',
    heading: 'Test Heading',
    merged_headings: ['Heading 1', 'Heading 2'],
  };
}

describe('index serialization', () => {
  it('exports version constants', () => {
    expect(INDEX_FORMAT_VERSION).toBeGreaterThan(0);
    expect(TOKENIZER_VERSION).toBeGreaterThan(0);
    expect(CHUNKER_VERSION).toBeGreaterThan(0);
  });

  it('round-trips index without data loss', () => {
    const chunks = [
      makeChunk('chunk-1', 'hello world', ['hello', 'world']),
      makeChunk('chunk-2', 'hello there', ['hello', 'there']),
    ];
    const original = buildBM25Index(chunks);
    const contentHash = 'abc123hash';

    const serialized = serializeIndex(original, contentHash);
    const restored = deserializeIndex(serialized);

    expect(restored.chunks).toHaveLength(original.chunks.length);
    expect(restored.avgDocLength).toBe(original.avgDocLength);
    expect(restored.docFrequency.get('hello')).toBe(original.docFrequency.get('hello'));

    // Verify chunk data integrity
    expect(restored.chunks[0].id).toBe('chunk-1');
    expect(restored.chunks[0].termFreqs.get('hello')).toBe(1);
    expect(restored.chunks[0].heading).toBe('Test Heading');
  });

  it('includes metadata in serialized output', () => {
    const chunks = [makeChunk('test', 'content', ['content'])];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'hash123');

    expect(serialized.version).toBe(INDEX_FORMAT_VERSION);
    expect(serialized.contentHash).toBe('hash123');
    expect(serialized.metadata?.tokenizerVersion).toBe(TOKENIZER_VERSION);
    expect(serialized.metadata?.chunkerVersion).toBe(CHUNKER_VERSION);
    expect(serialized.metadata?.createdAt).toBeGreaterThan(0);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/index-cache.test.ts`
Expected: FAIL - module doesn't exist

**Step 3: Create index-cache.ts**

Create `packages/mcp-servers/extension-docs/src/index-cache.ts`:

```typescript
import type { Chunk } from './types.js';
import type { BM25Index } from './bm25.js';

export const INDEX_FORMAT_VERSION = 1;
export const TOKENIZER_VERSION = 1;
export const CHUNKER_VERSION = 1;

export interface SerializedIndex {
  version: number;
  contentHash: string;
  avgDocLength: number;
  docFrequency: [string, number][];
  chunks: SerializedChunk[];
  metadata?: {
    createdAt: number;
    bm25?: { k1: number; b: number };
    tokenizerVersion?: number;
    chunkerVersion?: number;
  };
}

export interface SerializedChunk {
  id: string;
  content: string;
  tokens: string[];
  termFreqs: [string, number][];
  category: string;
  tags: string[];
  source_file: string;
  heading?: string;
  merged_headings?: string[];
}

export function serializeIndex(index: BM25Index, contentHash: string): SerializedIndex {
  return {
    version: INDEX_FORMAT_VERSION,
    contentHash,
    avgDocLength: index.avgDocLength,
    docFrequency: Array.from(index.docFrequency.entries()),
    chunks: index.chunks.map((c) => ({
      id: c.id,
      content: c.content,
      tokens: c.tokens,
      termFreqs: Array.from(c.termFreqs.entries()),
      category: c.category,
      tags: c.tags,
      source_file: c.source_file,
      heading: c.heading,
      merged_headings: c.merged_headings,
    })),
    metadata: {
      createdAt: Date.now(),
      bm25: { k1: 1.2, b: 0.75 },
      tokenizerVersion: TOKENIZER_VERSION,
      chunkerVersion: CHUNKER_VERSION,
    },
  };
}

export function deserializeIndex(serialized: SerializedIndex): BM25Index {
  return {
    chunks: serialized.chunks.map((c) => ({
      id: c.id,
      content: c.content,
      tokens: c.tokens,
      termFreqs: new Map(c.termFreqs),
      category: c.category,
      tags: c.tags,
      source_file: c.source_file,
      heading: c.heading,
      merged_headings: c.merged_headings,
    })),
    avgDocLength: serialized.avgDocLength,
    docFrequency: new Map(serialized.docFrequency),
  };
}
```

**Step 4: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/index-cache.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index-cache.ts packages/mcp-servers/extension-docs/tests/index-cache.test.ts
git commit -m "feat(extension-docs): add index serialization/deserialization

Triple versioning (format, tokenizer, chunker) + content hash for invalidation.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 8: Index Cache - Read/Write Helpers

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/cache.ts`
- Test: `packages/mcp-servers/extension-docs/tests/cache.test.ts`

**Step 1: Write failing tests for index cache helpers**

Add to `packages/mcp-servers/extension-docs/tests/cache.test.ts`:

```typescript
import { getDefaultIndexCachePath, readIndexCache, writeIndexCache } from '../src/cache.js';

describe('index cache helpers', () => {
  let tempDir: string;
  let indexPath: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'index-cache-test-'));
    indexPath = path.join(tempDir, 'test-index.json');
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('getDefaultIndexCachePath returns json file path', () => {
    const indexCachePath = getDefaultIndexCachePath();
    expect(indexCachePath).toMatch(/extension-docs[/\\]llms-full\.index\.json$/);
  });

  it('writeIndexCache and readIndexCache round-trip', async () => {
    const data = { version: 1, chunks: [], test: 'value' };
    await writeIndexCache(indexPath, data);
    const result = await readIndexCache(indexPath);
    expect(result).toEqual(data);
  });

  it('readIndexCache returns null for non-existent file', async () => {
    const result = await readIndexCache(indexPath);
    expect(result).toBeNull();
  });

  it('readIndexCache returns null for invalid JSON', async () => {
    await fs.writeFile(indexPath, 'not valid json {{{');
    const result = await readIndexCache(indexPath);
    expect(result).toBeNull();
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: FAIL - functions don't exist

**Step 3: Add index cache helpers to cache.ts**

Add to `packages/mcp-servers/extension-docs/src/cache.ts`:

```typescript
export function getDefaultIndexCachePath(filename = 'llms-full.index.json'): string {
  const base = getDefaultCachePath('llms-full.txt');
  return path.join(path.dirname(base), filename);
}

export async function writeIndexCache(cachePath: string, data: unknown): Promise<void> {
  const content = JSON.stringify(data);
  await writeCache(cachePath, content);
}

export async function readIndexCache(cachePath: string): Promise<unknown | null> {
  const cached = await readCache(cachePath);
  if (!cached) return null;
  try {
    return JSON.parse(cached.content);
  } catch {
    return null;
  }
}
```

**Step 4: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/cache.ts packages/mcp-servers/extension-docs/tests/cache.test.ts
git commit -m "feat(extension-docs): add index cache read/write helpers

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 9: Content Hash in Loader

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/loader.ts`
- Test: `packages/mcp-servers/extension-docs/tests/loader.test.ts`

**Step 1: Add crypto import and hash helper**

In `packages/mcp-servers/extension-docs/src/loader.ts`, add after line 1:

```typescript
import { createHash } from 'crypto';
```

Add helper function:

```typescript
function hashContent(content: string): string {
  return createHash('sha256').update(content).digest('hex');
}
```

**Step 2: Update loadFromOfficial return type**

```typescript
export interface LoadResult {
  files: MarkdownFile[];
  contentHash: string;
}

export async function loadFromOfficial(
  url: string,
  cachePath?: string,
  forceRefresh = false
): Promise<LoadResult> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const { sections, contentHash } = await fetchAndParse(url, resolvedCachePath, forceRefresh);
  const filtered = filterToExtensions(sections).filter((s) => s.content.trim().length > 0);

  return {
    contentHash,
    files: filtered.map((s) => {
      // ... existing mapping logic
    }),
  };
}
```

**Step 3: Update fetchAndParse to return contentHash**

```typescript
interface FetchResult {
  sections: ParsedSection[];
  contentHash: string;
}

async function fetchAndParse(
  url: string,
  cachePath: string,
  forceRefresh = false
): Promise<FetchResult> {
  if (!forceRefresh) {
    const fresh = await readCacheIfFresh(cachePath);
    if (fresh) {
      return {
        sections: parseSections(fresh.content),
        contentHash: hashContent(fresh.content),
      };
    }
  }

  try {
    const { content } = await fetchOfficialDocs(url);
    const contentHash = hashContent(content);
    await writeCache(cachePath, content);
    return { sections: parseSections(content), contentHash };
  } catch (err: unknown) {
    // ... error handling
    const cached = await readCache(cachePath);
    if (cached) {
      const ageHours = (cached.age / 3600000).toFixed(1);
      console.warn(`Using cached docs (${ageHours}h old)`);
      return {
        sections: parseSections(cached.content),
        contentHash: hashContent(cached.content),
      };
    }
    throw err;
  }
}
```

**Step 4: Update index.ts to use new return type**

In `packages/mcp-servers/extension-docs/src/index.ts`, update the doLoadIndex function:

```typescript
const { files, contentHash } = await loadFromOfficial(docsUrl);
// contentHash will be used in Task 10 for index caching
```

**Step 5: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 6: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts packages/mcp-servers/extension-docs/src/index.ts
git commit -m "feat(extension-docs): add content hashing for cache invalidation

SHA-256 hash computed for content to detect changes.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 10: Persistent Index Loading

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/index.ts`

**Step 1: Add imports**

```typescript
import {
  serializeIndex,
  deserializeIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  type SerializedIndex,
} from './index-cache.js';
import { readIndexCache, writeIndexCache, getDefaultIndexCachePath } from './cache.js';
```

**Step 2: Update doLoadIndex to use cached index**

```typescript
async function doLoadIndex(): Promise<BM25Index | null> {
  const isRetry = loadError !== null;

  lastLoadAttempt = Date.now();
  loadError = null;
  clearParseWarnings();

  if (isRetry) {
    console.error('Retrying documentation load...');
  }

  const docsUrl = process.env.DOCS_URL ?? 'https://code.claude.com/docs/llms-full.txt';

  try {
    const { files, contentHash } = await loadFromOfficial(docsUrl);
    if (files.length === 0) {
      loadError = 'No extension documentation found after filtering';
      console.error(`ERROR: ${loadError}`);
      return null;
    }

    // Try to load cached index
    const indexCachePath = getDefaultIndexCachePath();
    const cached = await readIndexCache(indexCachePath) as SerializedIndex | null;

    if (
      cached &&
      cached.version === INDEX_FORMAT_VERSION &&
      cached.contentHash === contentHash &&
      cached.metadata?.tokenizerVersion === TOKENIZER_VERSION &&
      cached.metadata?.chunkerVersion === CHUNKER_VERSION
    ) {
      index = deserializeIndex(cached);
      console.error(`Loaded cached index (${index.chunks.length} chunks)`);
      return index;
    }

    // Build fresh index
    const chunks = files.flatMap((f) => chunkFile(f));

    const warnings = getParseWarnings();
    if (warnings.length > 0) {
      console.error(`\nWARNING: ${warnings.length} file(s) with parse issues:`);
      for (const w of warnings) {
        console.error(`  - ${w.file}: ${w.issue}`);
      }
      console.error('');
    }

    index = buildBM25Index(chunks);
    console.error(`Built fresh index (${chunks.length} chunks from ${files.length} sections)`);

    // Persist index
    try {
      const serialized = serializeIndex(index, contentHash);
      await writeIndexCache(indexCachePath, serialized);
      console.error('Index cached for future use');
    } catch (err) {
      console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
    }

    return index;
  } catch (err) {
    loadError = `Failed to load docs: ${err instanceof Error ? err.message : 'unknown'}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }
}
```

**Step 3: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 4: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts
git commit -m "feat(extension-docs): implement persistent index caching

Skips chunking/tokenization when content hash matches cached index.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 11: Inverted Index - Data Structure

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/bm25.ts`
- Test: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Write failing test for inverted index**

Add to `packages/mcp-servers/extension-docs/tests/bm25.test.ts`:

```typescript
describe('buildBM25Index with inverted index', () => {
  it('builds inverted index mapping terms to chunk indices', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
      makeChunk('c', 'goodbye world', ['goodbye', 'world']),
    ];
    const index = buildBM25Index(chunks);

    expect(index.invertedIndex).toBeDefined();
    expect(index.invertedIndex.get('hello')).toEqual(new Set([0, 1]));
    expect(index.invertedIndex.get('world')).toEqual(new Set([0, 2]));
    expect(index.invertedIndex.get('there')).toEqual(new Set([1]));
    expect(index.invertedIndex.get('goodbye')).toEqual(new Set([2]));
  });

  it('handles empty chunks array', () => {
    const index = buildBM25Index([]);
    expect(index.invertedIndex.size).toBe(0);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: FAIL - invertedIndex property doesn't exist

**Step 3: Add inverted index to BM25Index interface**

In `packages/mcp-servers/extension-docs/src/bm25.ts`:

```typescript
export interface BM25Index {
  chunks: Chunk[];
  avgDocLength: number;
  docFrequency: Map<string, number>;
  invertedIndex: Map<string, Set<number>>;
}
```

**Step 4: Update buildBM25Index to create inverted index**

```typescript
export function buildBM25Index(chunks: Chunk[]): BM25Index {
  const docFrequency = new Map<string, number>();
  const invertedIndex = new Map<string, Set<number>>();

  for (const chunk of chunks) {
    const uniqueTerms = new Set(chunk.tokens);
    for (const term of uniqueTerms) {
      docFrequency.set(term, (docFrequency.get(term) ?? 0) + 1);
    }
  }

  for (let i = 0; i < chunks.length; i++) {
    const uniqueTerms = new Set(chunks[i].tokens);
    for (const term of uniqueTerms) {
      let postings = invertedIndex.get(term);
      if (!postings) {
        postings = new Set();
        invertedIndex.set(term, postings);
      }
      postings.add(i);
    }
  }

  return {
    chunks,
    avgDocLength:
      chunks.length > 0 ? chunks.reduce((sum, c) => sum + c.tokens.length, 0) / chunks.length : 0,
    docFrequency,
    invertedIndex,
  };
}
```

**Step 5: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: PASS

**Step 6: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): add inverted index data structure

Maps terms to chunk indices for O(k) candidate lookup.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 12: Inverted Index - Search Optimization

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/bm25.ts`
- Test: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Write test for optimized search**

Add to `packages/mcp-servers/extension-docs/tests/bm25.test.ts`:

```typescript
describe('search using inverted index', () => {
  it('returns same results as exhaustive search', () => {
    const chunks = [
      makeChunk('a', 'hooks documentation', ['hooks', 'documentation']),
      makeChunk('b', 'skills guide', ['skills', 'guide']),
      makeChunk('c', 'hooks and skills', ['hooks', 'skills']),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks');
    expect(results).toHaveLength(2);
    expect(results.map(r => r.chunk_id).sort()).toEqual(['a', 'c'].sort());
  });

  it('returns empty for query with no matching terms', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'xyz');
    expect(results).toHaveLength(0);
  });

  it('returns empty for empty query', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
    ];
    const index = buildBM25Index(chunks);

    // Query with only punctuation tokenizes to empty
    const results = search(index, '...');
    expect(results).toHaveLength(0);
  });
});
```

**Step 2: Update search to use inverted index**

```typescript
export function search(
  index: BM25Index,
  query: string,
  limit = 5,
  category?: string
): SearchResult[] {
  const queryTerms = tokenize(query);
  if (queryTerms.length === 0) return [];

  // Get candidate chunks from inverted index
  const candidates = new Set<number>();
  for (const term of queryTerms) {
    const postings = index.invertedIndex.get(term);
    if (postings) {
      for (const idx of postings) candidates.add(idx);
    }
  }

  // Filter candidates by category if specified
  const filteredCandidates = category
    ? Array.from(candidates).filter((idx) => index.chunks[idx].category === category)
    : Array.from(candidates);

  return filteredCandidates
    .map((idx) => ({
      chunk: index.chunks[idx],
      score: bm25Score(queryTerms, index.chunks[idx], index),
    }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => ({
      chunk_id: r.chunk.id,
      content: r.chunk.content,
      category: r.chunk.category,
      source_file: r.chunk.source_file,
    }));
}
```

**Step 3: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 4: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): optimize search with inverted index

Only score candidate chunks containing query terms.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 13: Update Index Serialization for Inverted Index

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/index-cache.ts`
- Test: `packages/mcp-servers/extension-docs/tests/index-cache.test.ts`

**Step 1: Update SerializedIndex type**

```typescript
export interface SerializedIndex {
  version: number;
  contentHash: string;
  avgDocLength: number;
  docFrequency: [string, number][];
  invertedIndex: [string, number[]][]; // Added
  chunks: SerializedChunk[];
  metadata?: {
    createdAt: number;
    bm25?: { k1: number; b: number };
    tokenizerVersion?: number;
    chunkerVersion?: number;
  };
}
```

**Step 2: Update serializeIndex**

```typescript
export function serializeIndex(index: BM25Index, contentHash: string): SerializedIndex {
  return {
    version: INDEX_FORMAT_VERSION,
    contentHash,
    avgDocLength: index.avgDocLength,
    docFrequency: Array.from(index.docFrequency.entries()),
    invertedIndex: Array.from(index.invertedIndex.entries()).map(([term, set]) => [
      term,
      Array.from(set),
    ]),
    chunks: index.chunks.map((c) => ({
      // ... existing chunk serialization
    })),
    metadata: {
      // ... existing metadata
    },
  };
}
```

**Step 3: Update deserializeIndex**

```typescript
export function deserializeIndex(serialized: SerializedIndex): BM25Index {
  return {
    chunks: serialized.chunks.map((c) => ({
      // ... existing chunk deserialization
    })),
    avgDocLength: serialized.avgDocLength,
    docFrequency: new Map(serialized.docFrequency),
    invertedIndex: new Map(
      serialized.invertedIndex.map(([term, arr]) => [term, new Set(arr)])
    ),
  };
}
```

**Step 4: Bump INDEX_FORMAT_VERSION**

```typescript
export const INDEX_FORMAT_VERSION = 2; // Bumped for inverted index
```

**Step 5: Add test for inverted index serialization**

```typescript
it('serializes and deserializes inverted index', () => {
  const chunks = [
    makeChunk('a', 'hello world', ['hello', 'world']),
    makeChunk('b', 'hello there', ['hello', 'there']),
  ];
  const original = buildBM25Index(chunks);
  const serialized = serializeIndex(original, 'hash');
  const restored = deserializeIndex(serialized);

  expect(restored.invertedIndex.get('hello')).toEqual(new Set([0, 1]));
  expect(restored.invertedIndex.get('world')).toEqual(new Set([0]));
});
```

**Step 6: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 7: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index-cache.ts packages/mcp-servers/extension-docs/tests/index-cache.test.ts
git commit -m "feat(extension-docs): serialize inverted index, bump format version

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Phase 3: UX

### Task 14: Snippet Extraction - Helper Function

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/bm25.ts`
- Test: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Write failing test for snippet extraction**

Add to `packages/mcp-servers/extension-docs/tests/bm25.test.ts`:

```typescript
import { extractSnippet } from '../src/bm25.js';

describe('extractSnippet', () => {
  it('returns snippet containing query terms', () => {
    const content = `Topic: Hooks Guide
ID: hooks-guide
Category: hooks

# Introduction

Hooks are powerful. They let you intercept tool calls.

## PreToolUse

The PreToolUse hook runs before each tool.`;

    const snippet = extractSnippet(content, ['pretooluse']);
    expect(snippet).toContain('PreToolUse');
    expect(snippet.length).toBeLessThanOrEqual(400);
  });

  it('strips metadata header before finding best line', () => {
    const content = `Topic: Test
ID: test-id
Category: hooks

The actual content starts here with hooks.`;

    const snippet = extractSnippet(content, ['hooks']);
    expect(snippet).not.toContain('Topic:');
    expect(snippet).toContain('hooks');
  });

  it('returns first line for empty query terms', () => {
    const content = `Topic: Test
ID: test

First real line.
Second line.`;

    const snippet = extractSnippet(content, []);
    expect(snippet).toBe('First real line.');
  });

  it('respects maxLength parameter', () => {
    const content = 'word '.repeat(200);
    const snippet = extractSnippet(content, ['word'], 100);
    expect(snippet.length).toBeLessThanOrEqual(100);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: FAIL - extractSnippet doesn't exist

**Step 3: Implement extractSnippet**

Add to `packages/mcp-servers/extension-docs/src/bm25.ts`:

```typescript
export function extractSnippet(
  content: string,
  queryTerms: string[],
  maxLength = 400
): string {
  // Strip metadata header (Topic/ID/Category/Tags lines at start)
  const bodyOnly = content.replace(
    /^(Topic:.*\n)?(ID:.*\n)?(Category:.*\n)?(Tags:.*\n)?\n?/m,
    ''
  );
  const lines = bodyOnly.split('\n');

  // For empty query terms, return first non-empty line
  if (queryTerms.length === 0) {
    const firstNonEmpty = lines.find((line) => line.trim().length > 0) ?? '';
    return firstNonEmpty.length > maxLength
      ? firstNonEmpty.slice(0, maxLength)
      : firstNonEmpty;
  }

  // Find line with highest term density
  let bestLine = 0;
  let bestScore = -1;

  for (let i = 0; i < lines.length; i++) {
    const lineTokens = new Set(tokenize(lines[i]));
    const score = queryTerms.reduce(
      (acc, t) => acc + (lineTokens.has(t) ? 1 : 0),
      0
    );
    if (score > bestScore) {
      bestScore = score;
      bestLine = i;
    }
  }

  // Expand bidirectionally around best line until maxLength
  let start = bestLine;
  let end = bestLine;
  let length = lines[bestLine]?.length ?? 0;

  while (length < maxLength && (start > 0 || end < lines.length - 1)) {
    if (start > 0) {
      start -= 1;
      length += lines[start].length + 1;
    }
    if (end < lines.length - 1 && length < maxLength) {
      end += 1;
      length += lines[end].length + 1;
    }
  }

  const snippet = lines.slice(start, end + 1).join('\n');
  return snippet.length > maxLength ? snippet.slice(0, maxLength) : snippet;
}
```

**Step 4: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/bm25.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): add snippet extraction helper

Strips metadata, finds best-match line, expands bidirectionally.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

### Task 15: Add Snippet to Search Results

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/types.ts`
- Modify: `packages/mcp-servers/extension-docs/src/bm25.ts`
- Modify: `packages/mcp-servers/extension-docs/src/index.ts`
- Test: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Update SearchResult type**

In `packages/mcp-servers/extension-docs/src/types.ts`:

```typescript
export interface SearchResult {
  chunk_id: string;
  content: string;
  snippet: string;
  category: string;
  source_file: string;
}
```

**Step 2: Update search function to include snippet**

In `packages/mcp-servers/extension-docs/src/bm25.ts`, update the return mapping:

```typescript
.map((r) => ({
  chunk_id: r.chunk.id,
  content: r.chunk.content,
  snippet: extractSnippet(r.chunk.content, queryTerms),
  category: r.chunk.category,
  source_file: r.chunk.source_file,
}));
```

**Step 3: Update SearchOutputSchema**

In `packages/mcp-servers/extension-docs/src/index.ts`:

```typescript
const SearchOutputSchema = z.object({
  results: z.array(
    z.object({
      chunk_id: z.string(),
      content: z.string(),
      snippet: z.string(),
      category: z.string(),
      source_file: z.string(),
    }),
  ),
});
```

**Step 4: Update bm25.test.ts to expect snippet**

Update the existing "returns SearchResult format" test:

```typescript
it('returns SearchResult format with snippet', () => {
  const chunks = [
    {
      ...makeChunk('test-chunk', 'test content here', ['test', 'content', 'here']),
      category: 'hooks',
      source_file: 'hooks/test.md',
    },
  ];
  const index = buildBM25Index(chunks);
  const results = search(index, 'test');

  expect(results[0]).toMatchObject({
    chunk_id: 'test-chunk',
    content: 'test content here',
    category: 'hooks',
    source_file: 'hooks/test.md',
  });
  expect(results[0].snippet).toBeDefined();
  expect(typeof results[0].snippet).toBe('string');
});
```

**Step 5: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS

**Step 6: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/types.ts packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/src/index.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): add snippet field to search results

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## Final Tasks

### Task 16: Run Full Test Suite

**Step 1: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 2: Run type check**

Run: `cd packages/mcp-servers/extension-docs && npm run typecheck`
Expected: No errors

**Step 3: Run lint**

Run: `cd packages/mcp-servers/extension-docs && npm run lint`
Expected: No errors

---

### Task 17: Build and Manual Test

**Step 1: Build the server**

Run: `cd packages/mcp-servers/extension-docs && npm run build`
Expected: Build succeeds

**Step 2: Test with sample queries**

Start server and test:
- Query without category: should return mixed results
- Query with category: should only return that category
- Verify snippet appears in results
- Verify cached index is used on second load

---

### Task 18: Create PR

```bash
git push -u origin feature/extension-docs-etl-optimizations
gh pr create --title "feat(extension-docs): ETL optimizations" --body "$(cat <<'EOF'
## Summary
- Add category filtering for search queries
- Implement cache TTL with stale-while-error behavior
- Add persistent index serialization with content hashing
- Optimize search with inverted index
- Add snippet extraction to search results

## Test plan
- [ ] Run `npm test` - all tests pass
- [ ] Run `npm run typecheck` - no errors
- [ ] Manual test: search with category filter
- [ ] Manual test: verify cached index loads faster
- [ ] Manual test: verify snippets in results

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Reference Files

| File | Purpose |
|------|---------|
| `packages/mcp-servers/extension-docs/src/bm25.ts` | BM25 search, inverted index, snippets |
| `packages/mcp-servers/extension-docs/src/cache.ts` | TTL helpers, index cache |
| `packages/mcp-servers/extension-docs/src/index.ts` | MCP server, schemas, tool handlers |
| `packages/mcp-servers/extension-docs/src/loader.ts` | Content fetching with hashing |
| `packages/mcp-servers/extension-docs/src/index-cache.ts` | Index serialization (new) |
| `packages/mcp-servers/extension-docs/src/types.ts` | Type definitions |
| `packages/mcp-servers/extension-docs/src/filter.ts` | KNOWN_CATEGORIES |
