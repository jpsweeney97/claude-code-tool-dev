import { describe, it, expect } from 'vitest';
import { buildBM25Index, search, extractSnippet, headingBoostMultiplier, type BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';

function makeChunk(id: string, content: string, tokens: string[], heading?: string, merged_headings?: string[]): Chunk {
  return {
    id,
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: 'test',
    tags: [],
    source_file: 'test.md',
    heading,
    merged_headings,
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

  it('returns SearchResult format with snippet', () => {
    const chunks = [
      {
        ...makeChunk('test-chunk', 'test content here', ['test', 'content', 'here']),
        category: 'hooks',
        source_file: 'hooks/test.md',
      },
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'test');

    expect(results[0]).toMatchObject({
      chunk_id: 'test-chunk',
      content: 'test content here',
      category: 'hooks',
      source_file: 'hooks/test.md',
    });
    expect(results[0].snippet).toBeDefined();
    expect(typeof results[0].snippet).toBe('string');
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

  it('returns empty string when content is empty', () => {
    const snippet = extractSnippet('', ['hooks']);
    expect(snippet).toBe('');
  });

  it('returns empty string when content is whitespace and query is empty', () => {
    const snippet = extractSnippet('   \n\n', []);
    expect(snippet).toBe('');
  });
});

describe('heading boost', () => {
  it('boosts chunks whose heading matches query terms', () => {
    const chunks = [
      // Body-only match: "hooks" appears in body, heading is unrelated
      makeChunk('body-match', 'hooks documentation guide', ['hooks', 'documentation', 'guide'], '## Getting Started'),
      // Heading match: "hooks" appears in heading AND body
      makeChunk('heading-match', 'hooks documentation guide', ['hooks', 'documentation', 'guide'], '## Hooks'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks');

    // Both match, but heading-match should rank first due to boost
    expect(results).toHaveLength(2);
    expect(results[0].chunk_id).toBe('heading-match');
  });

  it('does not boost when heading coverage is below threshold', () => {
    const chunks = [
      // Heading has "hooks" but query is "hooks documentation guide" — only 1/3 coverage
      makeChunk('low-coverage', 'hooks documentation guide', ['hooks', 'documentation', 'guide'], '## Hooks'),
      makeChunk('no-heading', 'hooks documentation guide', ['hooks', 'documentation', 'guide']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks documentation guide');

    // "Hooks" heading covers only 1/3 of query terms (< 0.5 threshold)
    // Both chunks should have the same score (no boost applied)
    expect(results).toHaveLength(2);
    // Verify directly that the multiplier returns 1.0 for below-threshold coverage
    // "Hooks" covers 1/3 of query terms — below 0.5 threshold
    expect(headingBoostMultiplier(['hooks', 'documentation', 'guide'], '## Hooks', undefined)).toBe(1.0);
  });

  it('does not boost chunks without headings', () => {
    const chunks = [
      makeChunk('with-heading', 'hooks guide here', ['hooks', 'guide', 'here'], '## Hooks Guide'),
      makeChunk('no-heading', 'hooks guide here', ['hooks', 'guide', 'here']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks guide');

    // with-heading should rank first (2/2 = 100% coverage, above threshold)
    expect(results[0].chunk_id).toBe('with-heading');
  });

  it('handles single-term query with heading match', () => {
    const chunks = [
      makeChunk('heading-yes', 'security overview', ['security', 'overview'], '## Security'),
      makeChunk('heading-no', 'security overview', ['security', 'overview'], '## Overview'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'security');

    // Single term, 1/1 = 100% coverage on heading-yes
    expect(results[0].chunk_id).toBe('heading-yes');
  });

  it('boosts via merged_headings when primary heading does not match', () => {
    const chunks = [
      // Primary heading is unrelated, but merged_headings contains "Hooks"
      makeChunk('merged-match', 'hooks documentation guide', ['hooks', 'documentation', 'guide'],
        '## Getting Started', ['## Hooks', '## Hook Events']),
      // No headings at all
      makeChunk('no-heading', 'hooks documentation guide', ['hooks', 'documentation', 'guide']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks');

    // merged-match should rank first — "hooks" appears in merged_headings
    expect(results[0].chunk_id).toBe('merged-match');
  });

  it('unions primary heading and merged_headings for coverage calculation', () => {
    const chunks = [
      // Primary heading covers "hooks", merged_headings covers "guide" — union covers 2/2
      makeChunk('union-match', 'hooks guide content', ['hooks', 'guide', 'content'],
        '## Hooks', ['## Configuration Guide']),
      // Only primary heading, covers 1/2 — below 0.5 threshold
      makeChunk('partial-match', 'hooks guide content', ['hooks', 'guide', 'content'],
        '## Hooks'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks guide');

    // union-match has 2/2 coverage (boosted), partial-match has 1/2 (not boosted)
    expect(results[0].chunk_id).toBe('union-match');
  });

  it('does not boost merged_headings below coverage threshold', () => {
    const chunks = [
      // merged_headings match 1 of 3 query terms — below 0.5 threshold
      makeChunk('low-coverage', 'hooks guide content', ['hooks', 'guide', 'content'],
        '## Overview', ['## Hooks']),
      makeChunk('no-heading', 'hooks guide content', ['hooks', 'guide', 'content']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks guide content');

    // Both should have same score — merged_headings covers only 1/3 (below threshold)
    expect(results).toHaveLength(2);
    // Verify multiplier is 1.0 when merged_headings cover only 1/3 of query terms
    expect(headingBoostMultiplier(['hooks', 'guide', 'content'], '## Overview', ['## Hooks'])).toBe(1.0);
  });
});
