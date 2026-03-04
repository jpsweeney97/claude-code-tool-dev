import { z } from 'zod';
import type { Chunk } from './types.js';
import { BM25_CONFIG, type BM25Index } from './bm25.js';

export const INDEX_FORMAT_VERSION = 3; // Bumped for headingTokens + tokenCount
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
 * NOT included (separately versioned):
 * - tokenizer.ts → TOKENIZER_VERSION
 * - chunker.ts → CHUNKER_VERSION
 */
export const INGESTION_VERSION = 1;

export interface SerializedIndex {
  version: number;
  contentHash: string;
  avgDocLength: number;
  docFrequency: [string, number][];
  invertedIndex: [string, number[]][];
  chunks: SerializedChunk[];
  metadata?: {
    createdAt: number;
    bm25?: {
      k1: number;
      b: number;
      headingBoost: number;
      headingMinCoverage: number;
      snippetMaxLength: number;
    };
    tokenizerVersion?: number;
    chunkerVersion?: number;
    ingestionVersion?: number;
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
  headingTokens?: string[];
  tokenCount: number;
}

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

const SerializedIndexSchema = z.object({
  version: z.number(),
  contentHash: z.string(),
  avgDocLength: z.number(),
  docFrequency: z.array(z.tuple([z.string(), z.number()])),
  invertedIndex: z.array(z.tuple([z.string(), z.array(z.number())])),
  chunks: z.array(SerializedChunkSchema),
  metadata: z
    .object({
      createdAt: z.number(),
      bm25: z
        .object({
          k1: z.number(),
          b: z.number(),
          headingBoost: z.number(),
          headingMinCoverage: z.number(),
          snippetMaxLength: z.number(),
        })
        .optional(),
      tokenizerVersion: z.number().optional(),
      chunkerVersion: z.number().optional(),
      ingestionVersion: z.number().optional(),
    })
    .optional(),
});

export function parseSerializedIndex(data: unknown): SerializedIndex | null {
  const result = SerializedIndexSchema.safeParse(data);
  return result.success ? (result.data as SerializedIndex) : null;
}

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
    metadata: {
      createdAt: Date.now(),
      bm25: BM25_CONFIG,
      tokenizerVersion: TOKENIZER_VERSION,
      chunkerVersion: CHUNKER_VERSION,
      ingestionVersion: INGESTION_VERSION,
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
