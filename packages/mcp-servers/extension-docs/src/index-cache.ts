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
  const chunks = serialized.chunks.map((c) => ({
    id: c.id,
    content: c.content,
    tokens: c.tokens,
    termFreqs: new Map(c.termFreqs),
    category: c.category,
    tags: c.tags,
    source_file: c.source_file,
    heading: c.heading,
    merged_headings: c.merged_headings,
  }));

  // Rebuild inverted index from chunks
  // TODO(complete): Task 13 will add serialization for invertedIndex to avoid this rebuild
  const invertedIndex = new Map<string, Set<number>>();
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
    avgDocLength: serialized.avgDocLength,
    docFrequency: new Map(serialized.docFrequency),
    invertedIndex,
  };
}
