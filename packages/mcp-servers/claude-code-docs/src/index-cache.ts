import { z } from 'zod';
import type { BM25Index } from './bm25.js';
import type { SourceKind, TrustMode } from './trust.js';
import type {
  CorpusDiagnostics,
  CorpusWarning,
  CanaryMetrics,
  PolicyState,
} from './canary.js';

/**
 * Bump when the serialized index structure changes (block layout, field
 * additions/removals/renames, Zod schema changes). Existing cached indexes
 * are rebuilt on first startup after a bump.
 */
export const INDEX_FORMAT_VERSION = 4;

export const TOKENIZER_VERSION = 2; // Bumped: added Porter stemming with CamelCase protection
export const CHUNKER_VERSION = 1;

/**
 * Bump when any corpus-shaping subsystem changes:
 * - parser.ts (section/heading extraction)
 * - frontmatter.ts (metadata extraction)
 * - categories.ts (URL-to-category mapping)
 * - chunk-helpers.ts (term freq computation, chunk ID generation)
 * - loader.ts (content fetching/parsing pipeline)
 * - url-helpers.ts (URL normalization — affects category derivation and chunk IDs) (D5)
 *
 * Also bump when diagnostic computation changes (new counters, changed
 * semantics of existing counters) since diagnostics feed canary evaluation.
 *
 * NOT included (separately versioned):
 * - tokenizer.ts → TOKENIZER_VERSION
 * - chunker.ts → CHUNKER_VERSION
 */
export const INGESTION_VERSION = 2;

/**
 * Bump when canary policy interpretation or threshold constants change:
 * - canary.ts threshold constants (drift warn/fail, min section counts)
 * - canary.ts evaluateCanaries logic (acceptance/rejection criteria)
 * - Metric computation changes (overviewRatio, sectionCountDropRatio)
 *
 * NOT included (separately versioned):
 * - Diagnostic field additions → INGESTION_VERSION
 * - Serialized layout changes → INDEX_FORMAT_VERSION
 */
export const CANARY_VERSION = 1;

// ---- Five-block types ----

export interface CorpusBlock {
  contentHash: string;
  obtainedAt: number;
  sourceKind: SourceKind;
  trustMode: TrustMode;
  docsUrl: string;
}

export interface DiagnosticsBlock {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  overviewSectionCount: number;
  unmappedSegments: Array<[string, number]>;
  parseWarningCount: number;
}

export interface IndexBlock {
  createdAt: number;
  avgDocLength: number;
  chunkCount: number;
}

export interface PolicyStateBlock {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
}

export interface EvaluationBlock {
  canaryVersion: number;
  warnings: CorpusWarning[];
  metrics: CanaryMetrics;
}

export interface CompatibilityBlock {
  tokenizer: number;
  chunker: number;
  ingestion: number;
}

// ---- Serialized chunk (unchanged) ----

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
  headingTokens?: string[];
  tokenCount: number;
}

// ---- Serialized index (five-block layout) ----

export interface SerializedIndex {
  version: number;

  // Five lifecycle/provenance blocks
  corpus: CorpusBlock;
  diagnostics: DiagnosticsBlock;
  index: IndexBlock;
  policyState: PolicyStateBlock;
  evaluation: EvaluationBlock;

  // Compatibility versions (gate cache reuse)
  compatibility: CompatibilityBlock;

  // BM25 data (consumed by deserializeIndex — authoritative source; index.avgDocLength is observability only)
  avgDocLength: number;
  docFrequency: [string, number][];
  invertedIndex: [string, number[]][];
  chunks: SerializedChunk[];
}

// ---- Serialize context ----

export interface SerializeContext {
  obtainedAt: number;
  sourceKind: SourceKind;
  trustMode: TrustMode;
  docsUrl: string;
  diagnostics: CorpusDiagnostics;
  policyState: PolicyState;
  evaluation: {
    canaryVersion: number;
    warnings: CorpusWarning[];
    metrics: CanaryMetrics;
  };
}

// ---- Zod schemas ----

const SerializedChunkSchema = z.object({
  id: z.string(),
  content: z.string(),
  tokens: z.array(z.string()),
  termFreqs: z.array(z.tuple([z.string(), z.number()])),
  category: z.string(),
  tags: z.array(z.string()),
  source_file: z.string(),
  heading: z.string().optional(),
  merged_headings: z.array(z.string()).optional(),
  headingTokens: z.array(z.string()).optional(),
  tokenCount: z.number(),
});

const CorpusBlockSchema = z.object({
  contentHash: z.string(),
  obtainedAt: z.number(),
  sourceKind: z.enum(['fetched', 'cached', 'stale-fallback', 'bundled-snapshot']),
  trustMode: z.enum(['official', 'unsafe']),
  docsUrl: z.string(),
});

const DiagnosticsBlockSchema = z.object({
  sourceAnchoredCount: z.number(),
  nonEmptySectionCount: z.number(),
  sectionCount: z.number(),
  overviewSectionCount: z.number(),
  unmappedSegments: z.array(z.tuple([z.string(), z.number()])),
  parseWarningCount: z.number(),
});

const IndexBlockSchema = z.object({
  createdAt: z.number(),
  avgDocLength: z.number(),
  chunkCount: z.number(),
});

const PolicyStateBlockSchema = z.object({
  lastHealthySectionCount: z.number().nullable(),
  lastHealthyObservedAt: z.number().nullable(),
});

const WarningSchema = z.object({
  code: z.enum(['taxonomy_drift', 'parse_issues', 'section_count_drift']),
  severity: z.enum(['info', 'warn', 'error']),
  details: z.record(z.unknown()),
});

const CanaryMetricsSchema = z.object({
  overviewRatio: z.number(),
  baselineSectionCount: z.number().nullable(),
  sectionCountDropRatio: z.number().nullable(),
});

const EvaluationBlockSchema = z.object({
  canaryVersion: z.number(),
  warnings: z.array(WarningSchema),
  metrics: CanaryMetricsSchema,
});

const CompatibilityBlockSchema = z.object({
  tokenizer: z.number(),
  chunker: z.number(),
  ingestion: z.number(),
});

const SerializedIndexSchema = z.object({
  version: z.number(),
  corpus: CorpusBlockSchema,
  diagnostics: DiagnosticsBlockSchema,
  index: IndexBlockSchema,
  policyState: PolicyStateBlockSchema,
  evaluation: EvaluationBlockSchema,
  compatibility: CompatibilityBlockSchema,
  avgDocLength: z.number(),
  docFrequency: z.array(z.tuple([z.string(), z.number()])),
  invertedIndex: z.array(z.tuple([z.string(), z.array(z.number())])),
  chunks: z.array(SerializedChunkSchema),
});

// ---- Parser-normalizer ----

/**
 * Parse and validate serialized index data. Rejects:
 * - Old-format snapshots (identified by flat `metadata` or `contentHash` at top level)
 * - Any payload that fails Zod validation (missing required blocks, wrong types)
 */
export function parseSerializedIndex(data: unknown): SerializedIndex | null {
  if (typeof data !== 'object' || data === null) return null;

  // Reject old-format snapshots: presence of flat `metadata` or `contentHash`
  // at top level indicates pre-v4 format.
  const record = data as Record<string, unknown>;
  if ('metadata' in record || 'contentHash' in record) return null;

  const result = SerializedIndexSchema.safeParse(data);
  return result.success ? (result.data as SerializedIndex) : null;
}

// ---- Serialize ----

export function serializeIndex(
  index: BM25Index,
  contentHash: string,
  context: SerializeContext,
): SerializedIndex {
  return {
    version: INDEX_FORMAT_VERSION,

    corpus: {
      contentHash,
      obtainedAt: context.obtainedAt,
      sourceKind: context.sourceKind,
      trustMode: context.trustMode,
      docsUrl: context.docsUrl,
    },

    diagnostics: {
      sourceAnchoredCount: context.diagnostics.sourceAnchoredCount,
      nonEmptySectionCount: context.diagnostics.nonEmptySectionCount,
      sectionCount: context.diagnostics.sectionCount,
      overviewSectionCount: context.diagnostics.overviewSectionCount,
      unmappedSegments: context.diagnostics.unmappedSegments,
      parseWarningCount: context.diagnostics.parseWarningCount,
    },

    index: {
      createdAt: Date.now(),
      avgDocLength: index.avgDocLength,
      chunkCount: index.chunks.length,
    },

    policyState: {
      lastHealthySectionCount: context.policyState.lastHealthySectionCount,
      lastHealthyObservedAt: context.policyState.lastHealthyObservedAt,
    },

    evaluation: {
      canaryVersion: context.evaluation.canaryVersion,
      warnings: context.evaluation.warnings,
      metrics: context.evaluation.metrics,
    },

    compatibility: {
      tokenizer: TOKENIZER_VERSION,
      chunker: CHUNKER_VERSION,
      ingestion: INGESTION_VERSION,
    },

    avgDocLength: index.avgDocLength,
    docFrequency: Array.from(index.docFrequency.entries()),
    invertedIndex: Array.from(index.invertedIndex.entries()).map(([term, set]) => [
      term,
      Array.from(set),
    ]),
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
      headingTokens: c.headingTokens ? Array.from(c.headingTokens) : undefined,
      tokenCount: c.tokenCount,
    })),
  };
}

// ---- Deserialize (reads BM25 data only) ----

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
      headingTokens: c.headingTokens ? new Set(c.headingTokens) : undefined,
      tokenCount: c.tokenCount,
    })),
    avgDocLength: serialized.avgDocLength,
    docFrequency: new Map(serialized.docFrequency),
    invertedIndex: new Map(
      serialized.invertedIndex.map(([term, arr]) => [term, new Set(arr)])
    ),
  };
}
