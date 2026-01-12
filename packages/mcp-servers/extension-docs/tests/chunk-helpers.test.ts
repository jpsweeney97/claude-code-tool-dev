import { describe, it, expect } from 'vitest';
import { slugify, generateChunkId, computeTermFreqs } from '../src/chunk-helpers.js';
import type { MarkdownFile } from '../src/types.js';

describe('slugify', () => {
  it('lowercases text', () => {
    expect(slugify('HELLO')).toBe('hello');
  });

  it('replaces non-alphanumeric with hyphens', () => {
    expect(slugify('hello world')).toBe('hello-world');
  });

  it('removes leading/trailing hyphens', () => {
    expect(slugify('--hello--')).toBe('hello');
  });

  it('handles file paths', () => {
    expect(slugify('hooks/input-schema.md')).toBe('hooks-input-schema');
  });

  it('handles markdown headings', () => {
    expect(slugify('## PreToolUse Input')).toBe('pretooluse-input');
  });
});

describe('generateChunkId', () => {
  const file: MarkdownFile = { path: 'hooks/input-schema.md', content: '' };

  it('generates id for whole file chunk', () => {
    expect(generateChunkId(file)).toBe('hooks-input-schema');
  });

  it('generates id with heading fragment', () => {
    expect(generateChunkId(file, '## PreToolUse Input')).toBe('hooks-input-schema#pretooluse-input');
  });
});

describe('generateChunkId with splitIndex', () => {
  it('adds no suffix for splitIndex undefined', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    const id = generateChunkId(file, '## Section');
    expect(id).toBe('hooks-test#section');
  });

  it('adds no suffix for splitIndex 1 (first chunk)', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    const id = generateChunkId(file, '## Section', 1);
    expect(id).toBe('hooks-test#section');
  });

  it('adds suffix for splitIndex 2+', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    expect(generateChunkId(file, '## Section', 2)).toBe('hooks-test#section-2');
    expect(generateChunkId(file, '## Section', 3)).toBe('hooks-test#section-3');
  });

  it('handles file-only id with splitIndex', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    // No heading, but has splitIndex (shouldn't happen in practice, but handle gracefully)
    expect(generateChunkId(file, undefined, 2)).toBe('hooks-test');
  });
});

describe('computeTermFreqs', () => {
  it('returns empty map for empty array', () => {
    expect(computeTermFreqs([])).toEqual(new Map());
  });

  it('counts single term', () => {
    expect(computeTermFreqs(['hello'])).toEqual(new Map([['hello', 1]]));
  });

  it('counts repeated terms', () => {
    expect(computeTermFreqs(['a', 'b', 'a'])).toEqual(
      new Map([
        ['a', 2],
        ['b', 1],
      ]),
    );
  });
});
