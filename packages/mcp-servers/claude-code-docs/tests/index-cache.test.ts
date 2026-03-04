import { describe, it, expect } from 'vitest';
import {
  serializeIndex,
  deserializeIndex,
  parseSerializedIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
} from '../src/index-cache.js';
import { buildBM25Index } from '../src/bm25.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';
import { tokenize } from '../src/tokenizer.js';
import type { Chunk } from '../src/types.js';

function makeChunk(
  id: string,
  content: string,
  tokens: string[],
  heading?: string,
  merged_headings?: string[],
): Chunk {
  const headingTokens = new Set<string>();
  if (heading) for (const t of tokenize(heading)) headingTokens.add(t);
  if (merged_headings) for (const h of merged_headings) for (const t of tokenize(h)) headingTokens.add(t);

  return {
    id,
    content,
    tokens,
    tokenCount: tokens.length,
    termFreqs: computeTermFreqs(tokens),
    category: 'hooks',
    tags: ['test'],
    source_file: 'hooks/test.md',
    heading: heading ?? 'Test Heading',
    merged_headings: merged_headings ?? ['Heading 1', 'Heading 2'],
    headingTokens: headingTokens.size > 0 ? headingTokens : undefined,
  };
}

describe('index serialization', () => {
  it('exports version constants', () => {
    expect(INDEX_FORMAT_VERSION).toBeGreaterThan(0);
    expect(TOKENIZER_VERSION).toBeGreaterThan(0);
    expect(CHUNKER_VERSION).toBeGreaterThan(0);
  });

  it('round-trips index without data loss', () => {
    const chunks = [
      makeChunk('chunk-1', 'hello world', ['hello', 'world']),
      makeChunk('chunk-2', 'hello there', ['hello', 'there']),
    ];
    const original = buildBM25Index(chunks);
    const contentHash = 'abc123hash';

    const serialized = serializeIndex(original, contentHash);
    const restored = deserializeIndex(serialized);

    expect(restored.chunks).toHaveLength(original.chunks.length);
    expect(restored.avgDocLength).toBe(original.avgDocLength);
    expect(restored.docFrequency.get('hello')).toBe(original.docFrequency.get('hello'));

    // Verify chunk data integrity
    expect(restored.chunks[0].id).toBe('chunk-1');
    expect(restored.chunks[0].termFreqs.get('hello')).toBe(1);
    expect(restored.chunks[0].heading).toBe('Test Heading');
  });

  it('includes metadata in serialized output', () => {
    const chunks = [makeChunk('test', 'content', ['content'])];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'hash123');

    expect(serialized.version).toBe(INDEX_FORMAT_VERSION);
    expect(serialized.contentHash).toBe('hash123');
    expect(serialized.metadata?.tokenizerVersion).toBe(TOKENIZER_VERSION);
    expect(serialized.metadata?.chunkerVersion).toBe(CHUNKER_VERSION);
    expect(serialized.metadata?.createdAt).toBeGreaterThan(0);
  });

  it('serializes and deserializes inverted index', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const original = buildBM25Index(chunks);
    const serialized = serializeIndex(original, 'hash');
    const restored = deserializeIndex(serialized);

    expect(restored.invertedIndex.get('hello')).toEqual(new Set([0, 1]));
    expect(restored.invertedIndex.get('world')).toEqual(new Set([0]));
    expect(restored.invertedIndex.get('there')).toEqual(new Set([1]));
  });

  it('parseSerializedIndex returns null for invalid data', () => {
    const invalid = { version: INDEX_FORMAT_VERSION, contentHash: 'x' };
    expect(parseSerializedIndex(invalid)).toBeNull();
  });

  it('parseSerializedIndex accepts serialized output', () => {
    const chunks = [makeChunk('a', 'hello world', ['hello', 'world'])];
    const original = buildBM25Index(chunks);
    const serialized = serializeIndex(original, 'hash');
    const parsed = parseSerializedIndex(serialized);

    expect(parsed).not.toBeNull();
    expect(parsed?.version).toBe(INDEX_FORMAT_VERSION);
    expect(parsed?.contentHash).toBe('hash');
  });

  it('round-trips headingTokens and tokenCount through serialization', () => {
    const chunks = [
      makeChunk('test', 'hooks guide', ['hook', 'guid'], '## Hooks Guide'),
    ];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'hash123');
    const parsed = parseSerializedIndex(serialized);
    expect(parsed).not.toBeNull();
    const restored = deserializeIndex(parsed!);

    expect(restored.chunks[0].tokenCount).toBe(2);
    expect(restored.chunks[0].headingTokens).toBeInstanceOf(Set);
    expect(restored.chunks[0].headingTokens!.has('hook')).toBe(true);
    expect(restored.chunks[0].headingTokens!.has('guid')).toBe(true);
  });
});
