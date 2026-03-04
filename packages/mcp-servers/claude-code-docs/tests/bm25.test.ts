import { describe, it, expect } from 'vitest';
import { buildBM25Index, search, extractSnippet, headingBoostMultiplier, type BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';
import { tokenize } from '../src/tokenizer.js';

function makeChunk(id: string, content: string, tokens: string[], heading?: string, merged_headings?: string[]): Chunk {
  // Compute headingTokens from heading and merged_headings
  const headingTokens = new Set<string>();
  if (heading) for (const t of tokenize(heading)) headingTokens.add(t);
  if (merged_headings) for (const h of merged_headings) for (const t of tokenize(h)) headingTokens.add(t);

  return {
    id,
    content,
    tokens,
    tokenCount: tokens.length,
    termFreqs: computeTermFreqs(tokens),
    category: 'test',
    tags: [],
    source_file: 'test.md',
    heading,
    merged_headings,
    headingTokens: headingTokens.size > 0 ? headingTokens : undefined,
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
      makeChunk('a', 'hooks hooks hooks', ['hook', 'hook', 'hook']),
      makeChunk('b', 'hooks once', ['hook', 'onc']),
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
      tokenCount: tokens.length,
      termFreqs: computeTermFreqs(tokens),
      category,
      tags: [],
      source_file: `${category}/test.md`,
    };
  }

  it('filters results by category when provided', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'PreToolUse hooks', ['pre', 'tool', 'use', 'hook'], 'hooks'),
      makeChunkWithCategory('skills-1', 'skill hooks pattern', ['skill', 'hook', 'pattern'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'hooks');
    expect(results).toHaveLength(1);
    expect(results[0].chunk_id).toBe('hooks-1');
    expect(results[0].category).toBe('hooks');
  });

  it('returns all matching categories when category is undefined', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hook', 'content'], 'hooks'),
      makeChunkWithCategory('skills-1', 'hooks in skills', ['hook', 'skill'], 'skills'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5);
    expect(results).toHaveLength(2);
  });

  it('returns empty array when category has no matches', () => {
    const chunks = [
      makeChunkWithCategory('hooks-1', 'hooks content', ['hook', 'content'], 'hooks'),
    ];
    const index = buildBM25Index(chunks);

    const results = search(index, 'hooks', 5, 'skills');
    expect(results).toHaveLength(0);
  });
});

describe('search using inverted index', () => {
  it('returns same results as exhaustive search', () => {
    const chunks = [
      makeChunk('a', 'hooks documentation', ['hook', 'document']),
      makeChunk('b', 'skills guide', ['skill', 'guid']),
      makeChunk('c', 'hooks and skills', ['hook', 'skill']),
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
  it('uses BM25_CONFIG.snippetMaxLength as default', async () => {
    const { BM25_CONFIG } = await import('../src/bm25.js');
    expect(BM25_CONFIG.snippetMaxLength).toBe(400);
  });

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

describe('extractSnippet post-stemming', () => {
  it('selects line with stemmed match over line without', () => {
    const content = 'This is the overview section.\nConfiguration of MCP servers is done here.\nSee the FAQ for details.';
    const snippet = extractSnippet(content, ['configur'], 200);
    expect(snippet).toContain('Configuration');
  });

  it('selects highest-coverage line when multiple lines have stemmed matches', () => {
    const content = 'Hooks are event-driven.\nHook configuration and customization guide.\nUnrelated content here.';
    const snippet = extractSnippet(content, ['hook', 'configur'], 200);
    expect(snippet).toContain('Hook configuration');
  });

  it('handles threshold-adjacent morphology correctly', () => {
    const content = 'The runner finished first.\nRunning the test suite is simple.\nNo matches here.';
    const snippet = extractSnippet(content, ['run'], 200);
    expect(snippet).toMatch(/runner|Running/i);
  });

  it('does not select metadata lines over content lines after stemming', () => {
    const content = 'Source: https://example.com/hooks\nHooks let you intercept tool calls.\nMore details below.';
    const snippet = extractSnippet(content, ['hook'], 200);
    expect(snippet).toContain('Hooks let you');
  });

  it('respects maxLength when stemmed matches span long lines', () => {
    const longLine = 'Configuration '.repeat(50) + 'of servers.';
    const content = `Short line.\n${longLine}\nAnother short line.`;
    const snippet = extractSnippet(content, ['configur'], 200);
    expect(snippet.length).toBeLessThanOrEqual(250);
  });
});

describe('heading boost', () => {
  it('boosts chunks whose heading matches query terms', () => {
    const chunks = [
      // Body-only match: "hooks" appears in body, heading is unrelated
      makeChunk('body-match', 'hooks documentation guide', ['hook', 'document', 'guid'], '## Getting Started'),
      // Heading match: "hooks" appears in heading AND body
      makeChunk('heading-match', 'hooks documentation guide', ['hook', 'document', 'guid'], '## Hooks'),
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
      makeChunk('low-coverage', 'hooks documentation guide', ['hook', 'document', 'guid'], '## Hooks'),
      makeChunk('no-heading', 'hooks documentation guide', ['hook', 'document', 'guid']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks documentation guide');

    // "Hooks" heading covers only 1/3 of query terms (< 0.5 threshold)
    // Both chunks should have the same score (no boost applied)
    expect(results).toHaveLength(2);
    // Verify directly that the multiplier returns 1.0 for below-threshold coverage
    // "Hooks" covers 1/3 of stemmed query terms — below 0.5 threshold
    expect(headingBoostMultiplier(['hook', 'document', 'guid'], new Set(tokenize('## Hooks')))).toBe(1.0);
  });

  it('does not boost chunks without headings', () => {
    const chunks = [
      makeChunk('with-heading', 'hooks guide here', ['hook', 'guid', 'here'], '## Hooks Guide'),
      makeChunk('no-heading', 'hooks guide here', ['hook', 'guid', 'here']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks guide');

    // with-heading should rank first (2/2 = 100% coverage, above threshold)
    expect(results[0].chunk_id).toBe('with-heading');
  });

  it('handles single-term query with heading match', () => {
    const chunks = [
      makeChunk('heading-yes', 'security overview', ['secur', 'overview'], '## Security'),
      makeChunk('heading-no', 'security overview', ['secur', 'overview'], '## Overview'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'security');

    // Single term, 1/1 = 100% coverage on heading-yes
    expect(results[0].chunk_id).toBe('heading-yes');
  });

  it('boosts via merged_headings when primary heading does not match', () => {
    const chunks = [
      // Primary heading is unrelated, but merged_headings contains "Hooks"
      makeChunk('merged-match', 'hooks documentation guide', ['hook', 'document', 'guid'],
        '## Getting Started', ['## Hooks', '## Hook Events']),
      // No headings at all
      makeChunk('no-heading', 'hooks documentation guide', ['hook', 'document', 'guid']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks');

    // merged-match should rank first — "hooks" appears in merged_headings
    expect(results[0].chunk_id).toBe('merged-match');
  });

  it('unions primary heading and merged_headings for coverage calculation', () => {
    const chunks = [
      // Primary heading covers "hooks", merged_headings covers "guide" — union covers 2/2
      makeChunk('union-match', 'hooks guide content', ['hook', 'guid', 'content'],
        '## Hooks', ['## Configuration Guide']),
      // Only primary heading, covers 1/2 — below 0.5 threshold
      makeChunk('partial-match', 'hooks guide content', ['hook', 'guid', 'content'],
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
      makeChunk('low-coverage', 'hooks guide content', ['hook', 'guid', 'content'],
        '## Overview', ['## Hooks']),
      makeChunk('no-heading', 'hooks guide content', ['hook', 'guid', 'content']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks guide content');

    // Both should have same score — merged_headings covers only 1/3 (below threshold)
    expect(results).toHaveLength(2);
    // Verify multiplier is 1.0 when merged_headings cover only 1/3 of query terms
    const headingTokens = new Set([...tokenize('## Overview'), ...tokenize('## Hooks')]);
    expect(headingBoostMultiplier(['hook', 'guid', 'content'], headingTokens)).toBe(1.0);
  });

  it('accepts precomputed headingTokens Set', () => {
    const headingTokens = new Set(['hook', 'guid']);
    // 2/2 coverage → boost applied
    expect(headingBoostMultiplier(['hook', 'guid'], headingTokens)).toBeGreaterThan(1.0);
    // 0/2 coverage → no boost
    expect(headingBoostMultiplier(['skill', 'overview'], headingTokens)).toBe(1.0);
    // undefined → no boost
    expect(headingBoostMultiplier(['hook'], undefined)).toBe(1.0);
  });
});

describe('pairwise ranking (recalibration gate)', () => {
  // These tests verify that stemming + heading boost produce correct
  // relative rankings. They are NEVER updated during recalibration —
  // they are the external quality signal.

  it('stemmed query ranks heading-match above body-only-match', () => {
    const chunks = [
      makeChunk('heading-match', 'permission system overview', ['permiss', 'system', 'overview'], '## Permission System'),
      makeChunk('body-only', 'permission system overview', ['permiss', 'system', 'overview'], '## Getting Started'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'permissions');
    expect(results[0].chunk_id).toBe('heading-match');
  });

  it('plural query finds singular heading via stemming', () => {
    const chunks = [
      makeChunk('control-heading', 'boundary control docs', ['boundari', 'control', 'doc'], '## Boundary Control'),
      makeChunk('no-heading', 'boundary control docs', ['boundari', 'control', 'doc']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'boundary controls');
    expect(results[0].chunk_id).toBe('control-heading');
  });

  it('multi-term stemmed query with merged_headings coverage', () => {
    const chunks = [
      makeChunk('merged-coverage', 'hook config docs', ['hook', 'configur', 'doc'],
        '## Hooks', ['## Configuration Guide']),
      makeChunk('partial-coverage', 'hook config docs', ['hook', 'configur', 'doc'],
        '## Hooks'),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'configuring hooks');
    expect(results[0].chunk_id).toBe('merged-coverage');
  });
});
