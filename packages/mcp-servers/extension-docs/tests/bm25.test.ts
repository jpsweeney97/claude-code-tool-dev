import { describe, it, expect } from 'vitest';
import { buildBM25Index, search, extractSnippet, type BM25Index } from '../src/bm25.js';
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

describe('buildBM25Index with inverted index', () => {
  it('builds inverted index mapping terms to chunk indices', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
      makeChunk('c', 'goodbye world', ['goodbye', 'world']),
    ];
    const index = buildBM25Index(chunks);

    expect(index.invertedIndex).toBeDefined();
    expect(index.invertedIndex.get('hello')).toEqual(new Set([0, 1]));
    expect(index.invertedIndex.get('world')).toEqual(new Set([0, 2]));
    expect(index.invertedIndex.get('there')).toEqual(new Set([1]));
    expect(index.invertedIndex.get('goodbye')).toEqual(new Set([2]));
  });

  it('handles empty chunks array', () => {
    const index = buildBM25Index([]);
    expect(index.invertedIndex.size).toBe(0);
  });
});

describe('search with category filtering', () => {
  function makeChunkWithCategory(
    id: string,
    content: string,
    tokens: string[],
    category: string
  ): Chunk {
    return {
      id,
      content,
      tokens,
      termFreqs: computeTermFreqs(tokens),
      category,
      tags: [],
      source_file: `${category}/test.md`,
    };
  }

  it('filters results by category when provided', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'PreToolUse hooks', ['pretooluse', 'hooks'], 'hooks'),
      makeChunkWithCategory('skills-1', 'skill hooks pattern', ['skill', 'hooks', 'pattern'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'hooks');
    expect(results).toHaveLength(1);
    expect(results[0].chunk_id).toBe('hooks-1');
    expect(results[0].category).toBe('hooks');
  });

  it('returns all matching categories when category is undefined', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hooks', 'content'], 'hooks'),
      makeChunkWithCategory('skills-1', 'hooks in skills', ['hooks', 'skills'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5);
    expect(results).toHaveLength(2);
  });

  it('returns empty array when category has no matches', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hooks', 'content'], 'hooks'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'skills');
    expect(results).toHaveLength(0);
  });
});

describe('search using inverted index', () => {
  it('returns same results as exhaustive search', () => {
    const chunks = [
      makeChunk('a', 'hooks documentation', ['hooks', 'documentation']),
      makeChunk('b', 'skills guide', ['skills', 'guide']),
      makeChunk('c', 'hooks and skills', ['hooks', 'skills']),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks');
    expect(results).toHaveLength(2);
    expect(results.map(r => r.chunk_id).sort()).toEqual(['a', 'c'].sort());
  });

  it('returns empty for query with no matching terms', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'xyz');
    expect(results).toHaveLength(0);
  });

  it('returns empty for empty query', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
    ];
    const index = buildBM25Index(chunks);

    // Query with only punctuation tokenizes to empty
    const results = search(index, '...');
    expect(results).toHaveLength(0);
  });
});

describe('extractSnippet', () => {
  it('returns snippet containing query terms', () => {
    const content = `Topic: Hooks Guide
ID: hooks-guide
Category: hooks

# Introduction

Hooks are powerful. They let you intercept tool calls.

## PreToolUse

The PreToolUse hook runs before each tool.`;

    const snippet = extractSnippet(content, ['pretooluse']);
    expect(snippet).toContain('PreToolUse');
    expect(snippet.length).toBeLessThanOrEqual(400);
  });

  it('strips metadata header before finding best line', () => {
    const content = `Topic: Test
ID: test-id
Category: hooks

The actual content starts here with hooks.`;

    const snippet = extractSnippet(content, ['hooks']);
    expect(snippet).not.toContain('Topic:');
    expect(snippet).toContain('hooks');
  });

  it('returns first line for empty query terms', () => {
    const content = `Topic: Test
ID: test

First real line.
Second line.`;

    const snippet = extractSnippet(content, []);
    expect(snippet).toBe('First real line.');
  });

  it('respects maxLength parameter', () => {
    const content = 'word '.repeat(200);
    const snippet = extractSnippet(content, ['word'], 100);
    expect(snippet.length).toBeLessThanOrEqual(100);
  });
});
