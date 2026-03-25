// src/lifecycle.ts
import type { BM25Index } from './bm25.js';
import type { MarkdownFile, Chunk } from './types.js';
import type { LoadResult } from './loader.js';
import type { SerializedIndex, SerializeContext } from './index-cache.js';
import type { ParseWarning } from './frontmatter.js';
import type { ChunkResult } from './chunker.js';
import {
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  INGESTION_VERSION,
  CANARY_VERSION,
} from './index-cache.js';
import type { CorpusProvenance, TrustMode } from './trust.js';
import { isProvenanceBetter } from './trust.js';
import type {
  CanaryEvaluation,
  CorpusDiagnostics,
  EvaluateCanariesInput,
  LoaderDiagnostics,
  PolicyState,
} from './canary.js';

export interface ServerStateDeps {
  loadFn: (url: string, cachePath?: string, forceRefresh?: boolean) => Promise<LoadResult>;
  chunkFn: (file: MarkdownFile) => ChunkResult;
  buildIndexFn: (chunks: Chunk[]) => BM25Index;
  readCacheFn: (cachePath: string) => Promise<unknown>;
  writeCacheFn: (cachePath: string, data: SerializedIndex) => Promise<void>;
  clearCacheFn: () => Promise<void>;  // kept for emergency reset, NOT called in reload
  indexCachePathFn: () => string;
  serializeIndexFn: (index: BM25Index, contentHash: string, context: SerializeContext) => SerializedIndex;
  deserializeIndexFn: (data: SerializedIndex) => BM25Index;
  parseSerializedIndexFn: (data: unknown) => SerializedIndex | null;
  evaluateCanariesFn: (input: EvaluateCanariesInput) => CanaryEvaluation;
  timerFn?: () => number;
  retryIntervalMs?: number;
  docsUrl?: string;
  trustMode?: TrustMode;
}

const DEFAULT_POLICY_STATE: PolicyState = {
  lastHealthySectionCount: null,
  lastHealthyObservedAt: null,
};

export class ServerState {
  private index: BM25Index | null = null;
  private contentHash: string | null = null;
  private loadError: string | null = null;
  private lastLoadAttempt = 0;
  private indexCreatedAt: number | null = null;
  private loadingPromise: Promise<BM25Index | null> | null = null;
  private warnings: ParseWarning[] = [];
  private policyState: PolicyState = { ...DEFAULT_POLICY_STATE };
  private corpusProvenance: CorpusProvenance | null = null;
  private diagnostics: CorpusDiagnostics | null = null;
  private evaluation: CanaryEvaluation | null = null;
  private readonly trustMode: TrustMode;
  private readonly effectiveRetryInterval: number;
  private readonly deps: ServerStateDeps;
  private readonly docsUrl: string;
  private readonly timer: () => number;

  constructor(deps: ServerStateDeps) {
    this.deps = deps;
    this.timer = deps.timerFn ?? Date.now;
    this.docsUrl = deps.docsUrl ?? 'https://code.claude.com/docs/llms-full.txt';
    this.trustMode = deps.trustMode ?? 'official';

    const retryMs = deps.retryIntervalMs ?? 60000;
    this.effectiveRetryInterval =
      retryMs >= 1000 && retryMs <= 600000 ? retryMs : 60000;
  }

  async ensureIndex(forceRefresh = false): Promise<BM25Index | null> {
    if (this.index && !forceRefresh) return this.index;

    if (this.loadingPromise) return this.loadingPromise;

    const now = this.timer();
    if (this.loadError && now - this.lastLoadAttempt < this.effectiveRetryInterval && !forceRefresh) {
      return null;
    }

    this.loadingPromise = this.doLoadIndex(forceRefresh);

    try {
      return await this.loadingPromise;
    } finally {
      this.loadingPromise = null;
    }
  }

  getIndex(): BM25Index | null {
    return this.index;
  }

  getLoadError(): string | null {
    return this.loadError;
  }

  getLoadingPromise(): Promise<BM25Index | null> | null {
    return this.loadingPromise;
  }

  getWarnings(): ParseWarning[] {
    return [...this.warnings];
  }

  getContentHash(): string | null {
    return this.contentHash;
  }

  getIndexCreatedAt(): number | null {
    return this.indexCreatedAt;
  }

  getPolicyState(): PolicyState {
    return { ...this.policyState };
  }

  getCorpusProvenance(): CorpusProvenance | null {
    return this.corpusProvenance ? { ...this.corpusProvenance } : null;
  }

  getDiagnostics(): CorpusDiagnostics | null {
    return this.diagnostics ? { ...this.diagnostics } : null;
  }

  getEvaluation(): CanaryEvaluation | null {
    return this.evaluation;
  }

  getTrustMode(): TrustMode {
    return this.trustMode;
  }

  getDocsUrl(): string {
    return this.docsUrl;
  }

  getLastLoadAttempt(): number {
    return this.lastLoadAttempt;
  }

  isLoading(): boolean {
    return this.loadingPromise !== null;
  }

  async clearAndReload(): Promise<BM25Index | null> {
    const inProgress = this.loadingPromise;
    if (inProgress) {
      console.error('Waiting for in-progress load to complete before reload...');
      try {
        await inProgress;
      } catch {
        // In-progress load failed — proceeding with forced reload
      }
    }

    console.error('Forcing documentation reload...');
    // Do NOT call clearCacheFn — reload overwrites in place, preserving policyState
    return this.ensureIndex(true);
  }

  private async doLoadIndex(forceRefresh = false): Promise<BM25Index | null> {
    const isRetry = this.loadError !== null;

    this.lastLoadAttempt = this.timer();
    this.loadError = null;
    this.warnings = [];

    if (isRetry) {
      console.error('Retrying documentation load...');
    }

    try {
      const loadResult = await this.deps.loadFn(this.docsUrl, undefined, forceRefresh);
      const { files, contentHash, provenance, diagnostics: loaderDiagnostics } = loadResult;

      if (files.length === 0) {
        this.loadError = 'No extension documentation found after filtering';
        console.error(`ERROR: ${this.loadError}`);
        return null;
      }

      // Read existing index cache
      const indexCachePath = this.deps.indexCachePathFn();
      const parsed = this.deps.parseSerializedIndexFn(await this.deps.readCacheFn(indexCachePath));

      // Extract policyState from cache (or use current in-memory state)
      const oldPolicyState: PolicyState = parsed?.policyState
        ? { ...parsed.policyState }
        : { ...this.policyState };

      // Check compatibility versions
      const compatMatch = parsed !== null &&
        parsed.version === INDEX_FORMAT_VERSION &&
        parsed.compatibility?.tokenizer === TOKENIZER_VERSION &&
        parsed.compatibility?.chunker === CHUNKER_VERSION &&
        parsed.compatibility?.ingestion === INGESTION_VERSION;

      const contentMatch = compatMatch && parsed!.corpus?.contentHash === contentHash;
      const canaryMatch = contentMatch && parsed!.evaluation?.canaryVersion === CANARY_VERSION;

      // Determine provenance comparison
      const cachedProvenance: CorpusProvenance | null = parsed?.corpus
        ? { sourceKind: parsed.corpus.sourceKind, obtainedAt: parsed.corpus.obtainedAt }
        : null;
      const provenanceBetter = cachedProvenance !== null && isProvenanceBetter(provenance, cachedProvenance);

      // --- Path 1: Full Hit ---
      if (canaryMatch && !provenanceBetter) {
        this.index = this.deps.deserializeIndexFn(parsed!);
        this.contentHash = contentHash;
        this.indexCreatedAt = parsed!.index.createdAt;
        this.corpusProvenance = cachedProvenance;
        this.policyState = oldPolicyState;
        this.evaluation = {
          decision: 'accept',
          rejection: null,
          warnings: parsed!.evaluation.warnings,
          metrics: parsed!.evaluation.metrics,
          nextPolicyState: oldPolicyState,
        };
        // Reconstruct diagnostics from cache
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          overviewSectionCount: parsed!.diagnostics.overviewSectionCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;
        console.error(`Loaded cached index (${this.index.chunks.length} chunks)`);
        return this.index;
      }

      // --- Path 2: Canary Replay ---
      if (contentMatch && !canaryMatch) {
        // Re-evaluate canaries with persisted diagnostics
        const cachedDiagnostics: CorpusDiagnostics = parsed!.diagnostics;
        const evalResult = this.deps.evaluateCanariesFn({
          trustMode: this.trustMode,
          diagnostics: cachedDiagnostics,
          policyState: oldPolicyState,
          now: this.timer(),
        });

        if (evalResult.decision === 'reject') {
          // Canary replay rejected — try forced uncached fetch if content was cached
          if (provenance.sourceKind !== 'fetched') {
            return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath);
          }
          // Content was live-fetched — fail loudly
          console.error(`ERROR: Canary replay rejected live-fetched content: ${evalResult.rejection?.reason}`);
          this.loadError = `Canary rejection: ${evalResult.rejection?.reason}`;
          this.evaluation = evalResult;
          this.policyState = evalResult.nextPolicyState;
          return null;
        }

        // Canary replay accepted — update evaluation in cache, no rebuild needed
        this.index = this.deps.deserializeIndexFn(parsed!);
        this.contentHash = contentHash;
        this.indexCreatedAt = parsed!.index.createdAt;
        this.policyState = evalResult.nextPolicyState;
        this.evaluation = evalResult;
        this.diagnostics = cachedDiagnostics;

        // Check if provenance also improved (Path 2+4 combined)
        const effectiveProvenance = provenanceBetter ? provenance : cachedProvenance!;
        this.corpusProvenance = effectiveProvenance;

        // Write updated cache with new evaluation (and possibly new provenance)
        try {
          const serialized = this.deps.serializeIndexFn(this.index, contentHash, {
            obtainedAt: effectiveProvenance.obtainedAt,
            sourceKind: effectiveProvenance.sourceKind,
            trustMode: this.trustMode,
            docsUrl: this.docsUrl,
            diagnostics: cachedDiagnostics,
            policyState: evalResult.nextPolicyState,
            evaluation: {
              canaryVersion: CANARY_VERSION,
              warnings: evalResult.warnings,
              metrics: evalResult.metrics,
            },
          });
          await this.deps.writeCacheFn(indexCachePath, serialized);
          console.error('Cache updated (canary replay)');
        } catch (err) {
          console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
        }

        console.error(`Loaded cached index (${this.index.chunks.length} chunks)`);
        return this.index;
      }

      // --- Path 4: Provenance Refresh ---
      if (canaryMatch && provenanceBetter) {
        this.index = this.deps.deserializeIndexFn(parsed!);
        this.contentHash = contentHash;
        this.indexCreatedAt = parsed!.index.createdAt;
        this.corpusProvenance = provenance;
        this.policyState = oldPolicyState;
        this.evaluation = {
          decision: 'accept',
          rejection: null,
          warnings: parsed!.evaluation.warnings,
          metrics: parsed!.evaluation.metrics,
          nextPolicyState: oldPolicyState,
        };
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          overviewSectionCount: parsed!.diagnostics.overviewSectionCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;

        // Write updated cache with new provenance
        try {
          const serialized = this.deps.serializeIndexFn(this.index, contentHash, {
            obtainedAt: provenance.obtainedAt,
            sourceKind: provenance.sourceKind,
            trustMode: this.trustMode,
            docsUrl: this.docsUrl,
            diagnostics: parsed!.diagnostics,
            policyState: oldPolicyState,
            evaluation: {
              canaryVersion: CANARY_VERSION,
              warnings: parsed!.evaluation.warnings,
              metrics: parsed!.evaluation.metrics,
            },
          });
          await this.deps.writeCacheFn(indexCachePath, serialized);
          console.error('Cache updated (provenance refresh)');
        } catch (err) {
          console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
        }

        console.error(`Loaded cached index (${this.index.chunks.length} chunks)`);
        return this.index;
      }

      // --- Path 3: Rebuild ---
      return this.buildFreshIndex(files, contentHash, provenance, loaderDiagnostics, oldPolicyState, indexCachePath);
    } catch (err) {
      this.loadError = `Failed to load docs: ${err instanceof Error ? err.message : 'unknown'}`;
      console.error(`ERROR: ${this.loadError}`);
      return null;
    }
  }

  /**
   * Build a fresh index from files: chunk, evaluate canaries, build BM25 index, write cache.
   * On canary rejection with non-fetched content, forces an uncached fetch and retries once.
   */
  private async buildFreshIndex(
    files: MarkdownFile[],
    contentHash: string,
    provenance: CorpusProvenance,
    loaderDiagnostics: LoaderDiagnostics,
    oldPolicyState: PolicyState,
    indexCachePath: string,
  ): Promise<BM25Index | null> {
    const chunkResults = files.map((f) => this.deps.chunkFn(f));
    const chunks = chunkResults.flatMap((r) => r.chunks);
    this.warnings = chunkResults.flatMap((r) => r.warnings);
    const parseWarningCount = this.warnings.length;

    if (this.warnings.length > 0) {
      console.error(`\nWARNING: ${this.warnings.length} file(s) with parse issues:`);
      for (const w of this.warnings) {
        console.error(`  - ${w.file}: ${w.issue}`);
      }
      console.error('');
    }

    // Merge loader diagnostics + parseWarningCount → CorpusDiagnostics
    const corpusDiagnostics: CorpusDiagnostics = {
      ...loaderDiagnostics,
      parseWarningCount,
    };

    // Evaluate canaries
    const evalResult = this.deps.evaluateCanariesFn({
      trustMode: this.trustMode,
      diagnostics: corpusDiagnostics,
      policyState: oldPolicyState,
      now: this.timer(),
    });

    if (evalResult.decision === 'reject') {
      // If content was NOT fetched, force one uncached fetch and retry
      if (provenance.sourceKind !== 'fetched') {
        return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath);
      }
      // Content was live-fetched — fail loudly
      console.error(`ERROR: Canary rejection on fresh build: ${evalResult.rejection?.reason}`);
      this.loadError = `Canary rejection: ${evalResult.rejection?.reason}`;
      this.evaluation = evalResult;
      this.policyState = evalResult.nextPolicyState;
      return null;
    }

    // Canaries accepted — build index
    this.index = this.deps.buildIndexFn(chunks);
    this.contentHash = contentHash;
    this.indexCreatedAt = this.timer();
    this.corpusProvenance = provenance;
    this.policyState = evalResult.nextPolicyState;
    this.evaluation = evalResult;
    this.diagnostics = corpusDiagnostics;
    console.error(`Built fresh index (${chunks.length} chunks from ${files.length} sections)`);

    // Persist index
    try {
      const serialized = this.deps.serializeIndexFn(this.index, contentHash, {
        obtainedAt: provenance.obtainedAt,
        sourceKind: provenance.sourceKind,
        trustMode: this.trustMode,
        docsUrl: this.docsUrl,
        diagnostics: corpusDiagnostics,
        policyState: evalResult.nextPolicyState,
        evaluation: {
          canaryVersion: CANARY_VERSION,
          warnings: evalResult.warnings,
          metrics: evalResult.metrics,
        },
      });
      await this.deps.writeCacheFn(indexCachePath, serialized);
      console.error('Index cached for future use');
    } catch (err) {
      console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
    }

    return this.index;
  }

  /**
   * Force an uncached fetch and do a full rebuild.
   * If the forced fetch returns different content (different contentHash), full rebuild.
   * If same contentHash or fetch fails, confirm rejection (return null).
   */
  private async forceFetchAndRebuild(
    originalContentHash: string,
    oldPolicyState: PolicyState,
    indexCachePath: string,
  ): Promise<BM25Index | null> {
    console.error('Canary rejection — forcing uncached fetch...');
    try {
      const freshResult = await this.deps.loadFn(this.docsUrl, undefined, true);
      if (freshResult.contentHash === originalContentHash) {
        // Same content — confirmed rejection
        console.error('ERROR: Forced fetch returned same content — canary rejection confirmed');
        this.loadError = 'Canary rejection confirmed after forced fetch (same content)';
        return null;
      }
      // Different content — full rebuild with new content
      return this.buildFreshIndex(
        freshResult.files,
        freshResult.contentHash,
        freshResult.provenance,
        freshResult.diagnostics,
        oldPolicyState,
        indexCachePath,
      );
    } catch (err) {
      console.error(`ERROR: Forced fetch failed: ${err instanceof Error ? err.message : 'unknown'}`);
      this.loadError = `Canary rejection confirmed (forced fetch failed: ${err instanceof Error ? err.message : 'unknown'})`;
      return null;
    }
  }
}
