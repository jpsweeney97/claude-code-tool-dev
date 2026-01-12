import { describe, it, expect } from 'vitest';
import { buildBM25Index, search, type BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';

function makeChunk(id: string, content: string, tokens: string[]): Chunk {
  return {
    id,
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: 'test',
    tags: [],
    source_file: 'test.md',
  };
}

describe('buildBM25Index', () => {
  it('handles empty chunks array', () => {
    const index = buildBM25Index([]);
    expect(index.chunks).toEqual([]);
    expect(index.avgDocLength).toBe(0);
    expect(index.docFrequency.size).toBe(0);
  });

  it('computes average document length', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const index = buildBM25Index(chunks);
    expect(index.avgDocLength).toBe(2); // (2 + 2) / 2
  });

  it('computes document frequency', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const index = buildBM25Index(chunks);
    expect(index.docFrequency.get('hello')).toBe(2);
    expect(index.docFrequency.get('world')).toBe(1);
    expect(index.docFrequency.get('there')).toBe(1);
  });
});

describe('search', () => {
  it('returns empty array for empty index', () => {
    const index = buildBM25Index([]);
    const results = search(index, 'test');
    expect(results).toEqual([]);
  });

  it('returns empty array for no matches', () => {
    const chunks = [makeChunk('a', 'hello world', ['hello', 'world'])];
    const index = buildBM25Index(chunks);
    const results = search(index, 'xyz');
    expect(results).toEqual([]);
  });

  it('returns matching results', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'goodbye world', ['goodbye', 'world']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hello');
    expect(results).toHaveLength(1);
    expect(results[0].chunk_id).toBe('a');
  });

  it('ranks by relevance', () => {
    const chunks = [
      makeChunk('a', 'hooks hooks hooks', ['hooks', 'hooks', 'hooks']),
      makeChunk('b', 'hooks once', ['hooks', 'once']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks');

    // Chunk with more occurrences should rank higher
    expect(results[0].chunk_id).toBe('a');
  });

  it('respects limit parameter', () => {
    const chunks = Array.from({ length: 10 }, (_, i) =>
      makeChunk(`chunk${i}`, `content ${i}`, ['content', `item${i}`]),
    );
    const index = buildBM25Index(chunks);
    const results = search(index, 'content', 3);
    expect(results).toHaveLength(3);
  });

  it('returns SearchResult format', () => {
    const chunks = [
      {
        ...makeChunk('test-chunk', 'test content', ['test', 'content']),
        category: 'hooks',
        source_file: 'hooks/test.md',
      },
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'test');

    expect(results[0]).toEqual({
      chunk_id: 'test-chunk',
      content: 'test content',
      category: 'hooks',
      source_file: 'hooks/test.md',
    });
  });
});
