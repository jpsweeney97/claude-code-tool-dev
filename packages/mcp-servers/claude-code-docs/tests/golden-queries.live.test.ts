// tests/golden-queries.live.test.ts
// Runs the shared golden-query table against the REAL cached corpus, indexed
// through the SAME transform production uses (sectionToMarkdownFile: synthetic
// topic/id/category frontmatter → metadata tokens + page-title heading boost),
// unlike golden-queries.test.ts which runs against a synthetic mock.
//
// Corpus contract (cached-corpus test, not a network test):
// - Reads the content cache the production server maintains (24h TTL),
//   honoring CACHE_PATH like production.
// - Skips when no cache exists (corpus-validation.test.ts convention).
// - FAILS when the cache is older than MAX_CACHE_AGE_MS — a stale corpus must
//   not silently pass as live-search proof.
//
// Assertions are deliberately looser than the mocked suite (expected category in
// the top-3 results rather than top-1): the live corpus changes upstream weekly,
// and top-1 assertions against a moving corpus produce churn, not signal.
// A failure here means either (a) a ranking regression, or (b) the corpus moved
// materially — investigate before editing any expectation.
import { describe, it, expect, beforeAll } from 'vitest';
import { existsSync } from 'fs';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';
import { parseSections } from '../src/parser.js';
import { readCache, getDefaultCachePath } from '../src/cache.js';
import { sectionToMarkdownFile } from '../src/loader.js';
import { deriveCategory } from '../src/frontmatter.js';
import { GOLDEN_QUERIES } from './golden-query-data.js';

// Mirrors production's CACHE_PATH-first resolution (loader.ts resolveCachePath).
const cachePath = process.env.CACHE_PATH?.trim() || getDefaultCachePath();
const cacheExists = existsSync(cachePath);

// Generous bound: the production server refreshes the cache daily (24h TTL), so
// 7 days means "this machine has not run the server in a week — refresh first".
const MAX_CACHE_AGE_MS = 7 * 24 * 60 * 60 * 1000;

if (!cacheExists) {
  console.warn(
    `SKIPPING live golden queries: content cache not found at ${cachePath}\n` +
      `Run the server once to populate the cache, then re-run tests.`
  );
}

describe.skipIf(!cacheExists)('golden queries (live corpus)', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let sectionUrls: string[] = [];

  beforeAll(async () => {
    const cached = await readCache(cachePath);
    if (!cached) throw new Error(`Cache not readable at ${cachePath}`);
    if (cached.age > MAX_CACHE_AGE_MS) {
      const days = (cached.age / 86400000).toFixed(1);
      throw new Error(
        `Content cache is ${days} days old (max ${MAX_CACHE_AGE_MS / 86400000}). ` +
          `Refresh it (start the server or call reload_docs) before trusting live golden queries.`,
      );
    }
    const sections = parseSections(cached.content).filter(
      (s) => s.content.trim().length > 0,
    );
    sectionUrls = sections.map((s) => s.sourceUrl).filter((u) => u !== '');
    const files = sections.map(sectionToMarkdownFile);
    const chunks = files.flatMap((f) => chunkFile(f).chunks);
    index = buildBM25Index(chunks);
  });

  for (const { query, expectedTopCategory } of GOLDEN_QUERIES) {
    it(`"${query}" surfaces ${expectedTopCategory} in top-3 categories`, () => {
      const results = search(index, query, 3);
      expect(results.length).toBeGreaterThan(0);
      expect(results.map((r) => r.category)).toContain(expectedTopCategory);
    });
  }

  it('live corpus is nearly fully categorized (< 5% uncategorized sections)', () => {
    // Tighter than the runtime canary's 0.10 warn threshold on purpose: tests run
    // at development time where a nag is cheap; the canary guards production loads.
    const uncategorized = sectionUrls.filter((u) => deriveCategory(u) === 'uncategorized');
    const ratio = uncategorized.length / sectionUrls.length;
    expect(ratio, `uncategorized pages: ${uncategorized.join(', ')}`).toBeLessThan(0.05);
  });

  it('gateway family pages are indexed under the gateways category', () => {
    const gatewayChunks = index.chunks.filter((c) => c.category === 'gateways');
    expect(gatewayChunks.length).toBeGreaterThan(0);
  });
});
