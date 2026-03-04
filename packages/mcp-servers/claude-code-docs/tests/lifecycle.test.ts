// tests/lifecycle.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ServerState, type ServerStateDeps } from '../src/lifecycle.js';
import type { BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { INDEX_FORMAT_VERSION, TOKENIZER_VERSION, CHUNKER_VERSION } from '../src/index-cache.js';

function makeMockIndex(chunkCount = 3): BM25Index {
  const chunks: Chunk[] = Array.from({ length: chunkCount }, (_, i) => ({
    id: `chunk-${i}`,
    content: `content ${i}`,
    tokens: ['content', `${i}`],
    termFreqs: new Map([['content', 1], [`${i}`, 1]]),
    category: 'hooks',
    tags: [],
    source_file: `hooks/test-${i}.md`,
  }));
  return {
    chunks,
    avgDocLength: 2,
    docFrequency: new Map(),
    invertedIndex: new Map(),
  };
}

function makeDeps(overrides: Partial<ServerStateDeps> = {}): ServerStateDeps {
  const mockIndex = makeMockIndex();
  return {
    loadFn: vi.fn().mockResolvedValue({
      files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
      contentHash: 'abc123',
    }),
    chunkFn: vi.fn().mockReturnValue({
      chunks: mockIndex.chunks,
      warnings: [],
    }),
    buildIndexFn: vi.fn().mockReturnValue(mockIndex),
    readCacheFn: vi.fn().mockResolvedValue(null),
    writeCacheFn: vi.fn().mockResolvedValue(undefined),
    clearCacheFn: vi.fn().mockResolvedValue(undefined),
    indexCachePathFn: vi.fn().mockReturnValue('/tmp/test-cache.json'),
    serializeIndexFn: vi.fn().mockReturnValue({ version: INDEX_FORMAT_VERSION }),
    deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
    parseSerializedIndexFn: vi.fn().mockReturnValue(null),
    timerFn: vi.fn().mockReturnValue(1000),
    retryIntervalMs: 60000,
    docsUrl: 'https://test.example.com/docs',
    ...overrides,
  };
}

describe('ServerState', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('ensureIndex', () => {
    it('loads and returns index on first call', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      const idx = await state.ensureIndex();

      expect(idx).not.toBeNull();
      expect(idx!.chunks).toHaveLength(3);
      expect(deps.loadFn).toHaveBeenCalledOnce();
    });

    it('returns cached index on subsequent calls', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      await state.ensureIndex();
      const idx = await state.ensureIndex();

      expect(idx).not.toBeNull();
      expect(deps.loadFn).toHaveBeenCalledOnce();
    });

    it('shares loadingPromise for concurrent calls (A1 concurrency guard)', async () => {
      let resolveLoad: (v: { files: Array<{ path: string; content: string }>; contentHash: string }) => void;
      const loadPromise = new Promise<{ files: Array<{ path: string; content: string }>; contentHash: string }>(r => { resolveLoad = r; });

      const deps = makeDeps({
        loadFn: vi.fn().mockReturnValue(loadPromise),
      });
      const state = new ServerState(deps);

      // Start two concurrent calls
      const p1 = state.ensureIndex();
      const p2 = state.ensureIndex();

      // Both should be waiting on the same promise
      resolveLoad!({
        files: [{ path: 'test.md', content: '# Test' }],
        contentHash: 'hash',
      });

      const [r1, r2] = await Promise.all([p1, p2]);
      expect(r1).toBe(r2);
      expect(deps.loadFn).toHaveBeenCalledOnce();
    });

    it('shares loadingPromise for concurrent calls when load fails', async () => {
      let rejectLoad: (err: Error) => void;
      const loadPromise = new Promise<never>((_, r) => { rejectLoad = r; });

      const deps = makeDeps({
        loadFn: vi.fn().mockReturnValue(loadPromise),
      });
      const state = new ServerState(deps);

      // Start two concurrent calls
      const p1 = state.ensureIndex();
      const p2 = state.ensureIndex();

      // Reject the shared promise
      rejectLoad!(new Error('network down'));

      const [r1, r2] = await Promise.all([p1, p2]);

      // Both receive null (failure)
      expect(r1).toBeNull();
      expect(r2).toBeNull();
      expect(deps.loadFn).toHaveBeenCalledOnce();
      expect(state.getLoadError()).toContain('network down');

      // loadingPromise is cleared — subsequent call after retry interval can proceed
      expect(state.getLoadingPromise()).toBeNull();
    });

    it('respects retry interval after failure (A1 retry)', async () => {
      let time = 1000;
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('network down')),
        timerFn: () => time,
        retryIntervalMs: 60000,
      });
      const state = new ServerState(deps);

      // First call fails
      await state.ensureIndex();
      expect(state.getLoadError()).toContain('network down');

      // Second call within retry interval — returns null without calling loadFn
      time = 30000;
      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(deps.loadFn).toHaveBeenCalledOnce();

      // Third call after retry interval — retries
      time = 70000;
      await state.ensureIndex();
      expect(deps.loadFn).toHaveBeenCalledTimes(2);
    });

    it('forceRefresh bypasses retry interval (B11)', async () => {
      let time = 1000;
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('network down')),
        timerFn: () => time,
        retryIntervalMs: 60000,
      });
      const state = new ServerState(deps);

      // First call fails
      await state.ensureIndex();

      // forceRefresh ignores retry interval
      time = 2000;
      await state.ensureIndex(true);
      expect(deps.loadFn).toHaveBeenCalledTimes(2);
    });

    it('forceRefresh reloads even when index exists (B11)', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      await state.ensureIndex();
      expect(deps.loadFn).toHaveBeenCalledOnce();

      await state.ensureIndex(true);
      expect(deps.loadFn).toHaveBeenCalledTimes(2);
    });
  });

  describe('cache version checks (A1)', () => {
    it('uses cached index when all versions match', async () => {
      const mockIndex = makeMockIndex();
      const serializedIndex = {
        version: INDEX_FORMAT_VERSION,
        contentHash: 'abc123',
        metadata: {
          tokenizerVersion: TOKENIZER_VERSION,
          chunkerVersion: CHUNKER_VERSION,
        },
        chunks: [],
        docFreqs: [],
        avgDocLength: 2,
      };

      const deps = makeDeps({
        parseSerializedIndexFn: vi.fn().mockReturnValue(serializedIndex),
        readCacheFn: vi.fn().mockResolvedValue(serializedIndex),
        deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();

      // Should deserialize cached index, not build fresh
      expect(deps.deserializeIndexFn).toHaveBeenCalledOnce();
      expect(deps.buildIndexFn).not.toHaveBeenCalled();
    });

    it('rebuilds when INDEX_FORMAT_VERSION mismatches', async () => {
      const serializedIndex = {
        version: INDEX_FORMAT_VERSION + 1,
        contentHash: 'abc123',
        metadata: {
          tokenizerVersion: TOKENIZER_VERSION,
          chunkerVersion: CHUNKER_VERSION,
        },
      };

      const deps = makeDeps({
        parseSerializedIndexFn: vi.fn().mockReturnValue(serializedIndex),
        readCacheFn: vi.fn().mockResolvedValue(serializedIndex),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();

      // Should build fresh index, not deserialize
      expect(deps.buildIndexFn).toHaveBeenCalledOnce();
      expect(deps.deserializeIndexFn).not.toHaveBeenCalled();
    });

    it('rebuilds when contentHash mismatches', async () => {
      const serializedIndex = {
        version: INDEX_FORMAT_VERSION,
        contentHash: 'different-hash',
        metadata: {
          tokenizerVersion: TOKENIZER_VERSION,
          chunkerVersion: CHUNKER_VERSION,
        },
      };

      const deps = makeDeps({
        parseSerializedIndexFn: vi.fn().mockReturnValue(serializedIndex),
        readCacheFn: vi.fn().mockResolvedValue(serializedIndex),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();

      expect(deps.buildIndexFn).toHaveBeenCalledOnce();
    });
  });

  describe('RETRY_INTERVAL_MS clamping (B15)', () => {
    it('clamps values below 1000 to default 60000', async () => {
      // Timer calls: ensureIndex(now=0) → doLoadIndex(lastLoadAttempt=0) → ensureIndex(now=30000)
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('fail')),
        retryIntervalMs: 500,
        timerFn: vi.fn()
          .mockReturnValueOnce(0)      // ensureIndex check (loadError null, unused)
          .mockReturnValueOnce(0)      // doLoadIndex sets lastLoadAttempt
          .mockReturnValueOnce(30000), // ensureIndex retry check: 30000 - 0 = 30000 < 60000
      });
      const state = new ServerState(deps);

      await state.ensureIndex();
      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(deps.loadFn).toHaveBeenCalledOnce(); // clamped to 60s, so 30s is within interval
    });

    it('clamps values above 600000 to default 60000', async () => {
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('fail')),
        retryIntervalMs: 1000000,
        timerFn: vi.fn()
          .mockReturnValueOnce(0)
          .mockReturnValueOnce(0)
          .mockReturnValueOnce(30000),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();
      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(deps.loadFn).toHaveBeenCalledOnce(); // clamped to 60s
    });

    it('accepts valid retry interval values', async () => {
      // Timer calls: ensureIndex(0) → doLoadIndex(0) → ensureIndex(6000) → doLoadIndex(6000)
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('fail')),
        retryIntervalMs: 5000,
        timerFn: vi.fn()
          .mockReturnValueOnce(0)
          .mockReturnValueOnce(0)
          .mockReturnValueOnce(6000)
          .mockReturnValueOnce(6000),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();
      await state.ensureIndex();
      expect(deps.loadFn).toHaveBeenCalledTimes(2); // retried because 6s > 5s interval
    });
  });

  describe('warning aggregation', () => {
    it('collects warnings from multiple files', async () => {
      const deps = makeDeps({
        loadFn: vi.fn().mockResolvedValue({
          files: [
            { path: 'a.md', content: 'a' },
            { path: 'b.md', content: 'b' },
          ],
          contentHash: 'hash',
        }),
        chunkFn: vi.fn()
          .mockReturnValueOnce({
            chunks: [makeMockIndex(1).chunks[0]],
            warnings: [{ file: 'a.md', issue: 'bad tag' }],
          })
          .mockReturnValueOnce({
            chunks: [makeMockIndex(1).chunks[0]],
            warnings: [{ file: 'b.md', issue: 'bad category' }],
          }),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();

      const warnings = state.getWarnings();
      expect(warnings).toHaveLength(2);
      expect(warnings[0]).toEqual({ file: 'a.md', issue: 'bad tag' });
      expect(warnings[1]).toEqual({ file: 'b.md', issue: 'bad category' });
    });

    it('clears warnings on each load', async () => {
      const deps = makeDeps({
        chunkFn: vi.fn().mockReturnValue({
          chunks: makeMockIndex(1).chunks,
          warnings: [{ file: 'test.md', issue: 'warning' }],
        }),
      });
      const state = new ServerState(deps);

      await state.ensureIndex();
      expect(state.getWarnings()).toHaveLength(1);

      // Force reload — warnings should reset
      await state.ensureIndex(true);
      expect(state.getWarnings()).toHaveLength(1); // new warnings from new load, not accumulated
    });
  });

  describe('load failure behavior', () => {
    it('sets loadError on failure', async () => {
      const deps = makeDeps({
        loadFn: vi.fn().mockRejectedValue(new Error('connection refused')),
      });
      const state = new ServerState(deps);

      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(state.getLoadError()).toContain('connection refused');
    });

    it('preserves existing index on reload failure', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      // First load succeeds
      const idx1 = await state.ensureIndex();
      expect(idx1).not.toBeNull();

      // Reload fails
      vi.mocked(deps.loadFn).mockRejectedValueOnce(new Error('network down'));
      await state.ensureIndex(true);

      // Old index preserved
      expect(state.getIndex()).not.toBeNull();
      expect(state.getIndex()).toBe(idx1);
      expect(state.getLoadError()).toContain('network down');
    });

    it('sets loadError when no files returned', async () => {
      const deps = makeDeps({
        loadFn: vi.fn().mockResolvedValue({ files: [], contentHash: 'empty' }),
      });
      const state = new ServerState(deps);

      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(state.getLoadError()).toContain('No extension documentation found');
    });
  });

  describe('clearAndReload', () => {
    it('clears cache and force-refreshes index', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      // Initial load
      await state.ensureIndex();
      expect(deps.loadFn).toHaveBeenCalledOnce();

      // clearAndReload clears cache then reloads
      await state.clearAndReload();
      expect(deps.clearCacheFn).toHaveBeenCalledOnce();
      expect(deps.loadFn).toHaveBeenCalledTimes(2);
    });

    it('handles in-progress load failure gracefully before reload', async () => {
      let rejectLoad: (err: Error) => void;
      const loadPromise = new Promise<never>((_, r) => { rejectLoad = r; });

      const deps = makeDeps({
        loadFn: vi.fn()
          .mockReturnValueOnce(loadPromise)
          .mockResolvedValue({
            files: [{ path: 'test.md', content: '# Test' }],
            contentHash: 'hash2',
          }),
      });
      const state = new ServerState(deps);

      // Start a load that will fail
      const initialLoad = state.ensureIndex();

      // Start clearAndReload — it should wait for in-progress load
      const reloadPromise = state.clearAndReload();

      // Reject the initial load
      rejectLoad!(new Error('timeout'));
      await initialLoad;

      // clearAndReload should succeed with the second loadFn call
      const idx = await reloadPromise;
      expect(idx).not.toBeNull();
      expect(deps.clearCacheFn).toHaveBeenCalledOnce();
    });
  });

  describe('getters', () => {
    it('getIndex returns null before load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getIndex()).toBeNull();
    });

    it('getLoadError returns null before any failure', () => {
      const state = new ServerState(makeDeps());
      expect(state.getLoadError()).toBeNull();
    });

    it('getLoadingPromise returns null when not loading', () => {
      const state = new ServerState(makeDeps());
      expect(state.getLoadingPromise()).toBeNull();
    });
  });
});
