import type { Chunk, SearchResult } from './types.js';
import { tokenize } from './tokenizer.js';

export interface BM25Index {
  chunks: Chunk[];
  avgDocLength: number;
  docFrequency: Map<string, number>;
  invertedIndex: Map<string, Set<number>>;
}

export const BM25_CONFIG = {
  k1: 1.2,
  b: 0.75,
  headingBoost: 0.2,
  headingMinCoverage: 0.5,
  snippetMaxLength: 400,
};

const METADATA_HEADER_RE = /^(Topic:.*\n)?(ID:.*\n)?(Category:.*\n)?(Tags:.*\n)?\n?/m;

export function buildBM25Index(chunks: Chunk[]): BM25Index {
  const docFrequency = new Map<string, number>();
  const invertedIndex = new Map<string, Set<number>>();

  for (let i = 0; i < chunks.length; i++) {
    const uniqueTerms = new Set(chunks[i].tokens);
    for (const term of uniqueTerms) {
      docFrequency.set(term, (docFrequency.get(term) ?? 0) + 1);
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
      chunks.length > 0 ? chunks.reduce((sum, c) => sum + c.tokenCount, 0) / chunks.length : 0,
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
  const dl = chunk.tokenCount;

  if (N === 0 || avgdl === 0) return 0;

  return queryTerms.reduce((score, term) => {
    const df = index.docFrequency.get(term) ?? 0;
    const tf = chunk.termFreqs.get(term) ?? 0;
    const idfScore = idf(N, df);
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + (b * dl) / avgdl));
    return score + idfScore * tfNorm;
  }, 0);
}

/**
 * Post-score multiplier for heading relevance.
 * Returns 1.0 (no boost) when headingTokens is empty/undefined or coverage is below threshold.
 * Coverage formula: |unique(queryTerms) ∩ headingTokens| / |unique(queryTerms)|
 */
export function headingBoostMultiplier(
  queryTerms: string[],
  headingTokens: Set<string> | undefined,
): number {
  if (!headingTokens || headingTokens.size === 0) return 1.0;
  const { headingBoost, headingMinCoverage } = BM25_CONFIG;

  const uniqueQueryTerms = new Set(queryTerms);
  if (uniqueQueryTerms.size === 0) return 1.0;

  let matches = 0;
  for (const term of uniqueQueryTerms) {
    if (headingTokens.has(term)) matches++;
  }

  const coverage = matches / uniqueQueryTerms.size;
  return coverage >= headingMinCoverage ? 1.0 + headingBoost : 1.0;
}

export function extractSnippet(
  content: string,
  queryTerms: string[],
  maxLength = BM25_CONFIG.snippetMaxLength
): string {
  // Strip metadata header (Topic/ID/Category/Tags lines at start)
  const bodyOnly = content.replace(METADATA_HEADER_RE, '');
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
      score: bm25Score(queryTerms, index.chunks[idx], index) *
             headingBoostMultiplier(queryTerms, index.chunks[idx].headingTokens),
    }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => ({
      chunk_id: r.chunk.id,
      content: r.chunk.content,
      snippet: extractSnippet(r.chunk.content, queryTerms),
      category: r.chunk.category,
      source_file: r.chunk.source_file,
    }));
}
