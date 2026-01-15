import { describe, it, expect } from 'vitest';
import {
  serializeIndex,
  deserializeIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
} from '../src/index-cache.js';
import { buildBM25Index } from '../src/bm25.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';
import type { Chunk } from '../src/types.js';

function makeChunk(id: string, content: string, tokens: string[]): Chunk {
  return {
    id,
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: 'hooks',
    tags: ['test'],
    source_file: 'hooks/test.md',
    heading: 'Test Heading',
    merged_headings: ['Heading 1', 'Heading 2'],
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
});
