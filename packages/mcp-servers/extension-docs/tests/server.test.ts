// tests/server.test.ts
import { describe, it, expect } from 'vitest';

import { z } from 'zod';

// Test the state management and schema validation logic
// Full MCP integration tests require spawning the server process

// Import the schemas we'll define
const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty')),
  limit: z.number().int().min(1).max(20).optional(),
});

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
