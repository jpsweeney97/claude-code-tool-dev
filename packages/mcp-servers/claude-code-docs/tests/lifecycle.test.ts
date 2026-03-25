// tests/lifecycle.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ServerState, type ServerStateDeps } from '../src/lifecycle.js';
import type { BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import type { SerializedIndex } from '../src/index-cache.js';
import type { CanaryEvaluation, CorpusDiagnostics, PolicyState } from '../src/canary.js';
import type { CorpusProvenance } from '../src/trust.js';
import {
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  INGESTION_VERSION,
  CANARY_VERSION,
} from '../src/index-cache.js';

function makeMockIndex(chunkCount = 3): BM25Index {
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
  return {
    chunks,
    avgDocLength: 2,
    docFrequency: new Map(),
    invertedIndex: new Map(),
  };
}

const DEFAULT_PROVENANCE: CorpusProvenance = {
  sourceKind: 'fetched',
  obtainedAt: 1000,
};

const DEFAULT_LOADER_DIAGNOSTICS: CorpusDiagnostics = {
  sourceAnchoredCount: 50,
  nonEmptySectionCount: 50,
  sectionCount: 50,
  overviewSectionCount: 0,
  unmappedSegments: [],
  parseWarningCount: 0,
};

function makeAcceptEvaluation(policyState?: PolicyState): CanaryEvaluation {
  return {
    decision: 'accept',
    rejection: null,
    warnings: [],
    metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
    nextPolicyState: policyState ?? { lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 },
  };
}

function makeRejectEvaluation(): CanaryEvaluation {
  return {
    decision: 'reject',
    rejection: { code: 'no_source_markers', reason: 'No Source: markers found', details: {} },
    warnings: [],
    metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
    nextPolicyState: { lastHealthySectionCount: null, lastHealthyObservedAt: null },
  };
}

function makeFullCacheSnapshot(overrides: Partial<SerializedIndex> = {}): SerializedIndex {
  const mockIndex = makeMockIndex();
  return {
    version: INDEX_FORMAT_VERSION,
    corpus: {
      contentHash: 'abc123',
      obtainedAt: 1000,
      sourceKind: 'fetched',
      trustMode: 'official',
      docsUrl: 'https://test.example.com/docs',
    },
    diagnostics: {
      sourceAnchoredCount: 50,
      nonEmptySectionCount: 50,
      sectionCount: 50,
      overviewSectionCount: 0,
      unmappedSegments: [],
      parseWarningCount: 0,
    },
    index: {
      createdAt: 1000,
      avgDocLength: 2,
      chunkCount: 3,
    },
    policyState: {
      lastHealthySectionCount: 50,
      lastHealthyObservedAt: 1000,
    },
    evaluation: {
      canaryVersion: CANARY_VERSION,
      warnings: [],
      metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
    },
    compatibility: {
      tokenizer: TOKENIZER_VERSION,
      chunker: CHUNKER_VERSION,
      ingestion: INGESTION_VERSION,
    },
    avgDocLength: 2,
    docFrequency: [],
    invertedIndex: [],
    chunks: mockIndex.chunks.map((c) => ({
      id: c.id,
      content: c.content,
      tokens: c.tokens,
      termFreqs: Array.from(c.termFreqs.entries()),
      category: c.category,
      tags: c.tags,
      source_file: c.source_file,
      tokenCount: c.tokenCount,
    })),
    ...overrides,
  };
}

function makeDeps(overrides: Partial<ServerStateDeps> = {}): ServerStateDeps {
  const mockIndex = makeMockIndex();
  return {
    loadFn: vi.fn().mockResolvedValue({
      files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
      contentHash: 'abc123',
      provenance: { ...DEFAULT_PROVENANCE },
      diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
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
    serializeIndexFn: vi.fn().mockReturnValue(makeFullCacheSnapshot()),
    deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
    parseSerializedIndexFn: vi.fn().mockReturnValue(null),
    evaluateCanariesFn: vi.fn().mockReturnValue(makeAcceptEvaluation()),
    timerFn: vi.fn().mockReturnValue(1000),
    retryIntervalMs: 60000,
    docsUrl: 'https://test.example.com/docs',
    trustMode: 'official',
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
      let resolveLoad: (v: {
        files: Array<{ path: string; content: string }>;
        contentHash: string;
        provenance: CorpusProvenance;
        diagnostics: CorpusDiagnostics;
      }) => void;
      const loadPromise = new Promise<{
        files: Array<{ path: string; content: string }>;
        contentHash: string;
        provenance: CorpusProvenance;
        diagnostics: CorpusDiagnostics;
      }>((r) => { resolveLoad = r; });

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
        provenance: { ...DEFAULT_PROVENANCE },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
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

  describe('four cache paths', () => {
    describe('Path 1: Full Hit', () => {
      it('uses cached index when all versions, contentHash, canaryVersion match and provenance not better', async () => {
        const mockIndex = makeMockIndex();
        const snapshot = makeFullCacheSnapshot();

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        // Should deserialize cached index, not build fresh
        expect(deps.deserializeIndexFn).toHaveBeenCalledOnce();
        expect(deps.buildIndexFn).not.toHaveBeenCalled();
        expect(deps.writeCacheFn).not.toHaveBeenCalled();
        expect(deps.evaluateCanariesFn).not.toHaveBeenCalled();
        expect(idx).not.toBeNull();
      });

      it('preserves policyState from cache on full hit', async () => {
        const snapshot = makeFullCacheSnapshot({
          policyState: { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        expect(state.getPolicyState()).toEqual({
          lastHealthySectionCount: 42,
          lastHealthyObservedAt: 500,
        });
      });
    });

    describe('Path 2: Canary Replay', () => {
      it('re-evaluates canaries and rewrites cache when canaryVersion mismatches', async () => {
        const mockIndex = makeMockIndex();
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1, // old canary version
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        // Should deserialize (no rebuild), but re-evaluate and write cache
        expect(deps.deserializeIndexFn).toHaveBeenCalledOnce();
        expect(deps.buildIndexFn).not.toHaveBeenCalled();
        expect(deps.evaluateCanariesFn).toHaveBeenCalledOnce();
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('returns index even when cache write fails on canary replay (Path 2)', async () => {
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1, // triggers replay
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(makeMockIndex()),
          writeCacheFn: vi.fn().mockRejectedValue(new Error('disk full')),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).not.toBeNull();
        expect(idx!.chunks).toHaveLength(3);
        // Cache write was attempted and failed
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
      });

      it('carries forward policyState through canary replay', async () => {
        const snapshot = makeFullCacheSnapshot({
          policyState: { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 },
          evaluation: {
            canaryVersion: CANARY_VERSION - 1,
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const evalResult = makeAcceptEvaluation({ lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 });
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          evaluateCanariesFn: vi.fn().mockReturnValue(evalResult),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        // evaluateCanariesFn receives the old policyState from cache
        expect(deps.evaluateCanariesFn).toHaveBeenCalledWith(
          expect.objectContaining({
            policyState: { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 },
          }),
        );

        // ServerState adopts the nextPolicyState from evaluation
        expect(state.getPolicyState()).toEqual({ lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 });
      });
    });

    describe('Path 3: Rebuild', () => {
      it('builds fresh index when compatibility versions mismatch', async () => {
        const snapshot = makeFullCacheSnapshot({
          compatibility: {
            tokenizer: TOKENIZER_VERSION + 1, // mismatch
            chunker: CHUNKER_VERSION,
            ingestion: INGESTION_VERSION,
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(deps.evaluateCanariesFn).toHaveBeenCalledOnce();
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('builds fresh index when contentHash mismatches', async () => {
        const snapshot = makeFullCacheSnapshot({
          corpus: {
            contentHash: 'different-hash',
            obtainedAt: 1000,
            sourceKind: 'fetched',
            trustMode: 'official',
            docsUrl: 'https://test.example.com/docs',
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('builds fresh when no cache exists', async () => {
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(deps.evaluateCanariesFn).toHaveBeenCalledOnce();
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('carries forward policyState from cache on rebuild', async () => {
        const snapshot = makeFullCacheSnapshot({
          policyState: { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 },
          compatibility: {
            tokenizer: TOKENIZER_VERSION + 1, // force rebuild
            chunker: CHUNKER_VERSION,
            ingestion: INGESTION_VERSION,
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        // The evaluateCanariesFn receives the old policyState from cache
        expect(deps.evaluateCanariesFn).toHaveBeenCalledWith(
          expect.objectContaining({
            policyState: { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 },
          }),
        );
      });

      it('merges parseWarningCount from chunking into corpus diagnostics', async () => {
        const mockIndex = makeMockIndex();
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null),
          chunkFn: vi.fn().mockReturnValue({
            chunks: mockIndex.chunks,
            warnings: [{ file: 'a.md', issue: 'bad tag' }, { file: 'b.md', issue: 'bad cat' }],
          }),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        // evaluateCanariesFn should receive diagnostics with parseWarningCount=2
        expect(deps.evaluateCanariesFn).toHaveBeenCalledWith(
          expect.objectContaining({
            diagnostics: expect.objectContaining({
              parseWarningCount: 2,
              sourceAnchoredCount: 50,
            }),
          }),
        );
      });

      it('rebuilds when ingestionVersion mismatches', async () => {
        const snapshot = makeFullCacheSnapshot({
          compatibility: {
            tokenizer: TOKENIZER_VERSION,
            chunker: CHUNKER_VERSION,
            ingestion: INGESTION_VERSION + 1, // mismatch
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(deps.deserializeIndexFn).not.toHaveBeenCalled();
      });

      it('rebuilds when INDEX_FORMAT_VERSION mismatches', async () => {
        const snapshot = makeFullCacheSnapshot({
          version: INDEX_FORMAT_VERSION + 1,
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(deps.deserializeIndexFn).not.toHaveBeenCalled();
      });
    });

    describe('Path 4: Provenance Refresh', () => {
      it('returns index even when cache write fails on provenance refresh (Path 4)', async () => {
        const snapshot = makeFullCacheSnapshot({
          corpus: {
            contentHash: 'abc123',
            obtainedAt: 500, // older
            sourceKind: 'cached',
            trustMode: 'official',
            docsUrl: 'https://test.example.com/docs',
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(makeMockIndex()),
          writeCacheFn: vi.fn().mockRejectedValue(new Error('disk full')),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).not.toBeNull();
        expect(idx!.chunks).toHaveLength(3);
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
      });

      it('rewrites cache when provenance improves, no rebuild', async () => {
        const snapshot = makeFullCacheSnapshot({
          corpus: {
            contentHash: 'abc123',
            obtainedAt: 500, // older than load provenance (1000)
            sourceKind: 'cached',
            trustMode: 'official',
            docsUrl: 'https://test.example.com/docs',
          },
        });

        const mockIndex = makeMockIndex();
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        // Should deserialize (no rebuild), write updated cache
        expect(deps.deserializeIndexFn).toHaveBeenCalledOnce();
        expect(deps.buildIndexFn).not.toHaveBeenCalled();
        expect(deps.evaluateCanariesFn).not.toHaveBeenCalled();
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();

        // Provenance should reflect the new (better) provenance
        expect(state.getCorpusProvenance()).toEqual({
          sourceKind: 'fetched',
          obtainedAt: 1000,
        });
      });
    });

    describe('Path 2+4 Combined', () => {
      it('re-evaluates canaries and updates provenance when both canaryVersion and provenance need updating', async () => {
        const snapshot = makeFullCacheSnapshot({
          corpus: {
            contentHash: 'abc123',
            obtainedAt: 500, // older — provenance better
            sourceKind: 'cached',
            trustMode: 'official',
            docsUrl: 'https://test.example.com/docs',
          },
          evaluation: {
            canaryVersion: CANARY_VERSION - 1, // old canary — needs replay
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const mockIndex = makeMockIndex();
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          deserializeIndexFn: vi.fn().mockReturnValue(mockIndex),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        // Path 2 behavior: canary replay, no rebuild
        expect(deps.deserializeIndexFn).toHaveBeenCalledOnce();
        expect(deps.buildIndexFn).not.toHaveBeenCalled();
        expect(deps.evaluateCanariesFn).toHaveBeenCalledOnce();
        expect(deps.writeCacheFn).toHaveBeenCalledOnce();

        // Path 4 behavior: provenance updated
        expect(state.getCorpusProvenance()).toEqual({
          sourceKind: 'fetched',
          obtainedAt: 1000,
        });

        expect(idx).not.toBeNull();
      });
    });
  });

  describe('canary rejection handling', () => {
    describe('Path 2 (canary replay) rejection', () => {
      it('forces uncached fetch when content was from cache and fetch succeeds with different content', async () => {
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1, // old canary
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        // First eval rejects, second (after forced fetch) accepts
        const evalFn = vi.fn()
          .mockReturnValueOnce(makeRejectEvaluation())
          .mockReturnValueOnce(makeAcceptEvaluation());

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          evaluateCanariesFn: evalFn,
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 }, // not fetched
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test Updated' }],
              contentHash: 'new-hash',
              provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        // Forced fetch should have been called (second loadFn call)
        expect(deps.loadFn).toHaveBeenCalledTimes(2);
        // Should have built fresh index with new content
        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('fails loudly when content was live-fetched', async () => {
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1,
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          evaluateCanariesFn: vi.fn().mockReturnValue(makeRejectEvaluation()),
          // loadFn returns fetched provenance
          loadFn: vi.fn().mockResolvedValue({
            files: [{ path: 'hooks/test.md', content: '# Test' }],
            contentHash: 'abc123',
            provenance: { sourceKind: 'fetched', obtainedAt: 1000 },
            diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
          }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).toBeNull();
        expect(state.getLoadError()).toContain('Canary rejection');
        // Should NOT have tried a second fetch
        expect(deps.loadFn).toHaveBeenCalledOnce();
      });

      it('confirms rejection when forced fetch returns same contentHash', async () => {
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1,
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          evaluateCanariesFn: vi.fn().mockReturnValue(makeRejectEvaluation()),
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockResolvedValueOnce({
              // Forced fetch returns same hash
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).toBeNull();
        expect(state.getLoadError()).toContain('same content');
      });

      it('confirms rejection when forced fetch fails', async () => {
        const snapshot = makeFullCacheSnapshot({
          evaluation: {
            canaryVersion: CANARY_VERSION - 1,
            warnings: [],
            metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
          },
        });

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
          evaluateCanariesFn: vi.fn().mockReturnValue(makeRejectEvaluation()),
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockRejectedValueOnce(new Error('network timeout')),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).toBeNull();
        expect(state.getLoadError()).toContain('forced fetch failed');
      });
    });

    describe('Path 3 (rebuild) rejection', () => {
      it('forces uncached fetch when content was from cache and rebuild rejected', async () => {
        const evalFn = vi.fn()
          .mockReturnValueOnce(makeRejectEvaluation())
          .mockReturnValueOnce(makeAcceptEvaluation());

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null), // no cache
          evaluateCanariesFn: evalFn,
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test Fresh' }],
              contentHash: 'new-hash',
              provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(deps.loadFn).toHaveBeenCalledTimes(2);
        expect(deps.buildIndexFn).toHaveBeenCalledOnce();
        expect(idx).not.toBeNull();
      });

      it('fails loudly on rebuild rejection when content was live-fetched', async () => {
        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null),
          evaluateCanariesFn: vi.fn().mockReturnValue(makeRejectEvaluation()),
          // loadFn returns fetched provenance
          loadFn: vi.fn().mockResolvedValue({
            files: [{ path: 'hooks/test.md', content: '# Test' }],
            contentHash: 'abc123',
            provenance: { sourceKind: 'fetched', obtainedAt: 1000 },
            diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
          }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).toBeNull();
        expect(state.getLoadError()).toContain('Canary rejection');
        expect(deps.loadFn).toHaveBeenCalledOnce();
      });

      it('terminates when forced fetch falls back to stale cache', async () => {
        const evalFn = vi.fn()
          .mockReturnValueOnce(makeRejectEvaluation());

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null), // no index cache → Path 3
          evaluateCanariesFn: evalFn,
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockResolvedValueOnce({
              // Forced fetch returns stale-fallback with DIFFERENT hash
              files: [{ path: 'hooks/test.md', content: '# Test Stale' }],
              contentHash: 'different-hash',
              provenance: { sourceKind: 'stale-fallback', obtainedAt: 500 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            }),
        });
        const state = new ServerState(deps);

        const idx = await state.ensureIndex();

        expect(idx).toBeNull();
        expect(state.getLoadError()).toContain('stale cache');
        // Should NOT have called evaluateCanariesFn a second time (no recursion)
        expect(evalFn).toHaveBeenCalledOnce();
        expect(state.getEvaluation()).not.toBeNull();
        expect(state.getEvaluation()?.decision).toBe('reject');
      });

      it('sets evaluation and policyState when forced fetch returns same content', async () => {
        const rejection = makeRejectEvaluation();

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null),
          evaluateCanariesFn: vi.fn().mockReturnValue(rejection),
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123', // same hash
              provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            }),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        expect(state.getEvaluation()).not.toBeNull();
        expect(state.getEvaluation()?.decision).toBe('reject');
        expect(state.getPolicyState()).toEqual(rejection.nextPolicyState);
      });

      it('sets evaluation and policyState when forced fetch fails', async () => {
        const rejection = makeRejectEvaluation();

        const deps = makeDeps({
          parseSerializedIndexFn: vi.fn().mockReturnValue(null),
          evaluateCanariesFn: vi.fn().mockReturnValue(rejection),
          loadFn: vi.fn()
            .mockResolvedValueOnce({
              files: [{ path: 'hooks/test.md', content: '# Test' }],
              contentHash: 'abc123',
              provenance: { sourceKind: 'cached', obtainedAt: 1000 },
              diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
            })
            .mockRejectedValueOnce(new Error('network timeout')),
        });
        const state = new ServerState(deps);

        await state.ensureIndex();

        expect(state.getEvaluation()).not.toBeNull();
        expect(state.getEvaluation()?.decision).toBe('reject');
        expect(state.getPolicyState()).toEqual(rejection.nextPolicyState);
      });
    });
  });

  describe('RETRY_INTERVAL_MS clamping (B15)', () => {
    it('clamps values below 1000 to default 60000', async () => {
      // Timer calls: ensureIndex(now=0) -> doLoadIndex(lastLoadAttempt=0) -> ensureIndex(now=30000)
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
      // Timer calls: ensureIndex(0) -> doLoadIndex(0) -> ensureIndex(6000) -> doLoadIndex(6000)
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
          provenance: { ...DEFAULT_PROVENANCE },
          diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
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
        loadFn: vi.fn().mockResolvedValue({
          files: [],
          contentHash: 'empty',
          provenance: { ...DEFAULT_PROVENANCE },
          diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
        }),
      });
      const state = new ServerState(deps);

      const idx = await state.ensureIndex();
      expect(idx).toBeNull();
      expect(state.getLoadError()).toContain('No extension documentation found');
    });
  });

  describe('clearAndReload', () => {
    it('does NOT call clearCacheFn — overwrites in place', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);

      // Initial load
      await state.ensureIndex();
      expect(deps.loadFn).toHaveBeenCalledOnce();

      // clearAndReload — should NOT call clearCacheFn
      await state.clearAndReload();
      expect(deps.clearCacheFn).not.toHaveBeenCalled();
      expect(deps.loadFn).toHaveBeenCalledTimes(2);
    });

    it('preserves policyState across reload', async () => {
      const evalResult = makeAcceptEvaluation({
        lastHealthySectionCount: 42,
        lastHealthyObservedAt: 1000,
      });

      const deps = makeDeps({
        evaluateCanariesFn: vi.fn().mockReturnValue(evalResult),
      });
      const state = new ServerState(deps);

      // Initial load sets policyState
      await state.ensureIndex();
      expect(state.getPolicyState()).toEqual({
        lastHealthySectionCount: 42,
        lastHealthyObservedAt: 1000,
      });

      // Reload preserves policyState (no clearCacheFn call, and in-memory state survives)
      await state.clearAndReload();
      expect(state.getPolicyState()).toEqual({
        lastHealthySectionCount: 42,
        lastHealthyObservedAt: 1000,
      });
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
            provenance: { ...DEFAULT_PROVENANCE },
            diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
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
      expect(deps.clearCacheFn).not.toHaveBeenCalled();
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

    it('getPolicyState returns default before load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getPolicyState()).toEqual({
        lastHealthySectionCount: null,
        lastHealthyObservedAt: null,
      });
    });

    it('getCorpusProvenance returns null before load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getCorpusProvenance()).toBeNull();
    });

    it('getDiagnostics returns null before load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getDiagnostics()).toBeNull();
    });

    it('getEvaluation returns null before load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getEvaluation()).toBeNull();
    });

    it('getEvaluation returns a copy, not the internal reference', async () => {
      const deps = makeDeps();
      const state = new ServerState(deps);
      await state.ensureIndex();

      const eval1 = state.getEvaluation();
      const eval2 = state.getEvaluation();
      expect(eval1).not.toBeNull();
      expect(eval1).toEqual(eval2);
      expect(eval1).not.toBe(eval2); // different object references
    });

    it('getTrustMode returns configured trust mode', () => {
      const state = new ServerState(makeDeps({ trustMode: 'unsafe' }));
      expect(state.getTrustMode()).toBe('unsafe');
    });

    it('getTrustMode defaults to official', () => {
      const deps = makeDeps();
      delete (deps as Record<string, unknown>).trustMode;
      const state = new ServerState(deps);
      expect(state.getTrustMode()).toBe('official');
    });

    it('getLastLoadAttempt returns 0 before any load', () => {
      const state = new ServerState(makeDeps());
      expect(state.getLastLoadAttempt()).toBe(0);
    });

    it('isLoading returns false when not loading', () => {
      const state = new ServerState(makeDeps());
      expect(state.isLoading()).toBe(false);
    });

    it('isLoading returns true during load', async () => {
      let resolveLoad: (v: unknown) => void;
      const loadPromise = new Promise((r) => { resolveLoad = r; });

      const deps = makeDeps({
        loadFn: vi.fn().mockReturnValue(loadPromise),
      });
      const state = new ServerState(deps);

      const p = state.ensureIndex();
      expect(state.isLoading()).toBe(true);

      resolveLoad!({
        files: [{ path: 'test.md', content: '# Test' }],
        contentHash: 'hash',
        provenance: { ...DEFAULT_PROVENANCE },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      });
      await p;
      expect(state.isLoading()).toBe(false);
    });
  });
});
