import type { Chunk, SearchResult } from './types.js';
import { tokenize } from './tokenizer.js';

export interface BM25Index {
  chunks: Chunk[];
  avgDocLength: number;
  docFrequency: Map<string, number>;
  invertedIndex: Map<string, Set<number>>;
}

const BM25_CONFIG = {
  k1: 1.2,
  b: 0.75,
};

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

function idf(N: number, df: number): number {
  return Math.log((N - df + 0.5) / (df + 0.5) + 1);
}

function bm25Score(queryTerms: string[], chunk: Chunk, index: BM25Index): number {
  const { k1, b } = BM25_CONFIG;
  const N = index.chunks.length;
  const avgdl = index.avgDocLength;
  const dl = chunk.tokens.length;

  if (N === 0 || avgdl === 0) return 0;

  return queryTerms.reduce((score, term) => {
    const df = index.docFrequency.get(term) ?? 0;
    const tf = chunk.termFreqs.get(term) ?? 0;
    const idfScore = idf(N, df);
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + (b * dl) / avgdl));
    return score + idfScore * tfNorm;
  }, 0);
}

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
