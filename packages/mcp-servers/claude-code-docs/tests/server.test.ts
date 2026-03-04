// tests/server.test.ts
import { describe, it, expect } from 'vitest';

import { z } from 'zod';
import { KNOWN_CATEGORIES } from '../src/categories.js';
import { SearchInputSchema } from '../src/schemas.js';

// Test the state management and schema validation logic
// Full MCP integration tests require spawning the server process

const CATEGORY_VALUES = [...KNOWN_CATEGORIES] as const;

describe('SearchInputSchema validation', () => {
  it('rejects empty query', () => {
    const result = SearchInputSchema.safeParse({ query: '' });
    expect(result.success).toBe(false);
  });

  it('rejects whitespace-only query', () => {
    const result = SearchInputSchema.safeParse({ query: '   ' });
    expect(result.success).toBe(false);
  });

  it('rejects query over 500 characters', () => {
    const result = SearchInputSchema.safeParse({ query: 'a'.repeat(501) });
    expect(result.success).toBe(false);
  });

  it('accepts valid query', () => {
    const result = SearchInputSchema.safeParse({ query: 'hooks' });
    expect(result.success).toBe(true);
  });

  it('trims whitespace from query', () => {
    const result = SearchInputSchema.safeParse({ query: '  hooks  ' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.query).toBe('hooks');
    }
  });

  it('rejects non-integer limit', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 5.5 });
    expect(result.success).toBe(false);
  });

  it('rejects limit below 1', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 0 });
    expect(result.success).toBe(false);
  });

  it('rejects limit above 20', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 21 });
    expect(result.success).toBe(false);
  });

  it('uses undefined limit when not provided', () => {
    const result = SearchInputSchema.safeParse({ query: 'test' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.limit).toBeUndefined();
    }
  });
});

describe('Category Schema Validation', () => {
  const CategorySchema = z.enum(CATEGORY_VALUES as [string, ...string[]]).optional();

  it('accepts valid categories', () => {
    expect(CategorySchema.parse('hooks')).toBe('hooks');
    expect(CategorySchema.parse('skills')).toBe('skills');
    expect(CategorySchema.parse('plugin-marketplaces')).toBe('plugin-marketplaces');
    expect(CategorySchema.parse('memory')).toBe('memory');
    expect(CategorySchema.parse('security')).toBe('security');
  });

  it('accepts undefined category', () => {
    expect(CategorySchema.parse(undefined)).toBeUndefined();
  });

  it('rejects invalid categories', () => {
    expect(() => CategorySchema.parse('Hooks')).toThrow();
    expect(() => CategorySchema.parse('unknown')).toThrow();
    expect(() => CategorySchema.parse('hooks ')).toThrow();
  });

  it('accepts category in SearchInputSchema', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'hooks' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('hooks');
    }
  });

  it('accepts undefined category in SearchInputSchema', () => {
    const result = SearchInputSchema.safeParse({ query: 'test' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBeUndefined();
    }
  });

  it('rejects invalid category in SearchInputSchema', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'invalid' });
    expect(result.success).toBe(false);
  });
});

describe('Category alias normalization', () => {
  it('normalizes subagents to agents', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'subagents' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('agents');
    }
  });

  it('normalizes sub-agents to agents', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'sub-agents' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('agents');
    }
  });

  it('normalizes claude-md to memory', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'claude-md' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('memory');
    }
  });

  it('normalizes configuration to config', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'configuration' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('config');
    }
  });

  it('normalizes slash-commands to commands', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'slash-commands' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('commands');
    }
  });

  it('passes through canonical categories unchanged', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'hooks' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('hooks');
    }
  });
});

describe('New category validation', () => {
  it('accepts new general categories', () => {
    const newCategories = [
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'ide', 'ci-cd',
      'desktop', 'integrations', 'config', 'operations',
      'troubleshooting', 'changelog',
    ];

    for (const cat of newCategories) {
      const result = SearchInputSchema.safeParse({ query: 'test', category: cat });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.category).toBe(cat);
      }
    }
  });
});

describe('search_docs tool with category', () => {
  // This test verifies the tool handler passes category to search
  // Full integration test would require MCP client setup
  it('search function accepts category parameter', async () => {
    // Import the search function directly to verify signature
    const { search, buildBM25Index } = await import('../src/bm25.js');
    const { computeTermFreqs } = await import('../src/chunk-helpers.js');

    const chunks = [{
      id: 'test',
      content: 'test content',
      tokens: ['test', 'content'],
      tokenCount: 2,
      termFreqs: computeTermFreqs(['test', 'content']),
      category: 'hooks',
      tags: [],
      source_file: 'hooks/test.md',
    }];

    const index = buildBM25Index(chunks);

    // Verify search accepts 4th parameter
    const results = search(index, 'test', 5, 'hooks');
    expect(results).toHaveLength(1);
  });
});
