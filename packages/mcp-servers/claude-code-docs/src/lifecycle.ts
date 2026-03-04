// src/lifecycle.ts
import type { BM25Index } from './bm25.js';
import type { MarkdownFile, Chunk } from './types.js';
import type { LoadResult } from './loader.js';
import type { SerializedIndex } from './index-cache.js';
import type { ParseWarning } from './frontmatter.js';
import type { ChunkResult } from './chunker.js';
import { INDEX_FORMAT_VERSION, TOKENIZER_VERSION, CHUNKER_VERSION } from './index-cache.js';

export interface ServerStateDeps {
  loadFn: (url: string, cachePath?: string, forceRefresh?: boolean) => Promise<LoadResult>;
  chunkFn: (file: MarkdownFile) => ChunkResult;
  buildIndexFn: (chunks: Chunk[]) => BM25Index;
  readCacheFn: (cachePath: string) => Promise<unknown>;
  writeCacheFn: (cachePath: string, data: SerializedIndex) => Promise<void>;
  clearCacheFn: () => Promise<void>;
  indexCachePathFn: () => string;
  serializeIndexFn: (index: BM25Index, contentHash: string) => SerializedIndex;
  deserializeIndexFn: (data: SerializedIndex) => BM25Index;
  parseSerializedIndexFn: (data: unknown) => SerializedIndex | null;
  timerFn?: () => number;
  retryIntervalMs?: number;
  docsUrl?: string;
}

export class ServerState {
  private index: BM25Index | null = null;
  private loadError: string | null = null;
  private lastLoadAttempt = 0;
  private loadingPromise: Promise<BM25Index | null> | null = null;
  private warnings: ParseWarning[] = [];
  private readonly effectiveRetryInterval: number;
  private readonly deps: ServerStateDeps;
  private readonly docsUrl: string;
  private readonly timer: () => number;

  constructor(deps: ServerStateDeps) {
    this.deps = deps;
    this.timer = deps.timerFn ?? Date.now;
    this.docsUrl = deps.docsUrl ?? 'https://code.claude.com/docs/llms-full.txt';

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
    await this.deps.clearCacheFn();
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
      const { files, contentHash } = await this.deps.loadFn(this.docsUrl, undefined, forceRefresh);
      if (files.length === 0) {
        this.loadError = 'No extension documentation found after filtering';
        console.error(`ERROR: ${this.loadError}`);
        return null;
      }

      // Try to load cached index
      const indexCachePath = this.deps.indexCachePathFn();
      const cached = this.deps.parseSerializedIndexFn(await this.deps.readCacheFn(indexCachePath));

      if (
        cached &&
        cached.version === INDEX_FORMAT_VERSION &&
        cached.contentHash === contentHash &&
        cached.metadata?.tokenizerVersion === TOKENIZER_VERSION &&
        cached.metadata?.chunkerVersion === CHUNKER_VERSION
      ) {
        this.index = this.deps.deserializeIndexFn(cached);
        console.error(`Loaded cached index (${this.index.chunks.length} chunks)`);
        return this.index;
      }

      // Build fresh index — aggregate chunks and warnings from all files
      const chunkResults = files.map((f) => this.deps.chunkFn(f));
      const chunks = chunkResults.flatMap((r) => r.chunks);
      this.warnings = chunkResults.flatMap((r) => r.warnings);

      if (this.warnings.length > 0) {
        console.error(`\nWARNING: ${this.warnings.length} file(s) with parse issues:`);
        for (const w of this.warnings) {
          console.error(`  - ${w.file}: ${w.issue}`);
        }
        console.error('');
      }

      this.index = this.deps.buildIndexFn(chunks);
      console.error(`Built fresh index (${chunks.length} chunks from ${files.length} sections)`);

      // Persist index
      try {
        const serialized = this.deps.serializeIndexFn(this.index, contentHash);
        await this.deps.writeCacheFn(indexCachePath, serialized);
        console.error('Index cached for future use');
      } catch (err) {
        console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
      }

      return this.index;
    } catch (err) {
      this.loadError = `Failed to load docs: ${err instanceof Error ? err.message : 'unknown'}`;
      console.error(`ERROR: ${this.loadError}`);
      return null;
    }
  }
}
