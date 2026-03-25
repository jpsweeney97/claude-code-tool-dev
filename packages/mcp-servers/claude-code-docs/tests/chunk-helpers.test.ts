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
    expect(generateChunkId(file, undefined, 1)).toBe('hooks-test');
    expect(generateChunkId(file, undefined, 2)).toBe('hooks-test-2');
    expect(generateChunkId(file, undefined, 3)).toBe('hooks-test-3');
  });
});

describe('generateChunkId with URLs', () => {
  it('simplifies URL to content path', () => {
    const file: MarkdownFile = {
      path: 'https://code.claude.com/docs/en/hooks',
      content: '',
    };
    expect(generateChunkId(file)).toBe('hooks');
  });

  it('handles nested URL paths', () => {
    const file: MarkdownFile = {
      path: 'https://code.claude.com/docs/en/hooks/input-schema',
      content: '',
    };
    expect(generateChunkId(file)).toBe('hooks-input-schema');
  });

  it('handles URL with heading', () => {
    const file: MarkdownFile = {
      path: 'https://code.claude.com/docs/en/hooks/input-schema',
      content: '',
    };
    expect(generateChunkId(file, 'PreToolUse Input')).toBe('hooks-input-schema#pretooluse-input');
  });

  it('handles URL with heading and splitIndex', () => {
    const file: MarkdownFile = {
      path: 'https://code.claude.com/docs/en/hooks',
      content: '',
    };
    expect(generateChunkId(file, 'What are hooks', 1)).toBe('hooks#what-are-hooks');
    expect(generateChunkId(file, 'What are hooks', 2)).toBe('hooks#what-are-hooks-2');
    expect(generateChunkId(file, 'What are hooks', 3)).toBe('hooks#what-are-hooks-3');
  });

  it('handles URL without /docs/ prefix', () => {
    const file: MarkdownFile = {
      path: 'https://example.com/hooks/overview',
      content: '',
    };
    expect(generateChunkId(file)).toBe('hooks-overview');
  });

  it('returns unknown for URL with no content path', () => {
    const file: MarkdownFile = {
      path: 'https://example.com/',
      content: '',
    };
    expect(generateChunkId(file)).toBe('unknown');
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
