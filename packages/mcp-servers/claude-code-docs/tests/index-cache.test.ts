import { describe, it, expect } from 'vitest';
import {
  serializeIndex,
  deserializeIndex,
  parseSerializedIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  CANARY_VERSION,
  INGESTION_VERSION,
  type SerializeContext,
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

function makeSerializeContext(overrides?: Partial<SerializeContext>): SerializeContext {
  return {
    obtainedAt: Date.now(),
    sourceKind: 'fetched',
    trustMode: 'official',
    docsUrl: 'https://code.claude.com/docs/llms-full.txt',
    diagnostics: {
      sourceAnchoredCount: 10,
      nonEmptySectionCount: 50,
      sectionCount: 55,
      overviewSectionCount: 2,
      fallbackOverviewCount: 0,
      unmappedSegments: [],
      parseWarningCount: 0,
    },
    policyState: {
      lastHealthySectionCount: 55,
      lastHealthyObservedAt: Date.now() - 86400000,
    },
    evaluation: {
      canaryVersion: CANARY_VERSION,
      warnings: [],
      metrics: {
        overviewRatio: 0.036,
        baselineSectionCount: 55,
        sectionCountDropRatio: 0,
      },
    },
    ...overrides,
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

    const serialized = serializeIndex(original, contentHash, makeSerializeContext());
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
    const serialized = serializeIndex(index, 'hash123', makeSerializeContext());

    expect(serialized.version).toBe(INDEX_FORMAT_VERSION);
    expect(serialized.corpus.contentHash).toBe('hash123');
    expect(serialized.compatibility.tokenizer).toBe(TOKENIZER_VERSION);
    expect(serialized.compatibility.chunker).toBe(CHUNKER_VERSION);
    expect(serialized.index.createdAt).toBeGreaterThan(0);
  });

  it('serializes and deserializes inverted index', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const original = buildBM25Index(chunks);
    const serialized = serializeIndex(original, 'hash', makeSerializeContext());
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
    const serialized = serializeIndex(original, 'hash', makeSerializeContext());
    const parsed = parseSerializedIndex(serialized);

    expect(parsed).not.toBeNull();
    expect(parsed?.version).toBe(INDEX_FORMAT_VERSION);
    expect(parsed?.corpus.contentHash).toBe('hash');
  });

  it('round-trips headingTokens and tokenCount through serialization', () => {
    const chunks = [
      makeChunk('test', 'hooks guide', ['hook', 'guid'], '## Hooks Guide'),
    ];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'hash123', makeSerializeContext());
    const parsed = parseSerializedIndex(serialized);
    expect(parsed).not.toBeNull();
    const restored = deserializeIndex(parsed!);

    expect(restored.chunks[0].tokenCount).toBe(2);
    expect(restored.chunks[0].headingTokens).toBeInstanceOf(Set);
    expect(restored.chunks[0].headingTokens!.has('hook')).toBe(true);
    expect(restored.chunks[0].headingTokens!.has('guid')).toBe(true);
  });
});

describe('SerializedIndex v4 schema', () => {
  it('exports CANARY_VERSION', () => {
    expect(CANARY_VERSION).toBeGreaterThan(0);
  });

  it('serializes into five-block structure', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const index = buildBM25Index(chunks);
    const ctx = makeSerializeContext({
      sourceKind: 'cached',
      trustMode: 'unsafe',
      docsUrl: 'https://example.com/docs.txt',
    });
    const serialized = serializeIndex(index, 'hash-five', ctx);

    // corpus block
    expect(serialized.corpus.contentHash).toBe('hash-five');
    expect(serialized.corpus.obtainedAt).toBe(ctx.obtainedAt);
    expect(serialized.corpus.sourceKind).toBe('cached');
    expect(serialized.corpus.trustMode).toBe('unsafe');
    expect(serialized.corpus.docsUrl).toBe('https://example.com/docs.txt');

    // diagnostics block
    expect(serialized.diagnostics.sourceAnchoredCount).toBe(10);
    expect(serialized.diagnostics.sectionCount).toBe(55);
    expect(serialized.diagnostics.parseWarningCount).toBe(0);

    // index block
    expect(serialized.index.createdAt).toBeGreaterThan(0);
    expect(serialized.index.avgDocLength).toBe(index.avgDocLength);
    expect(serialized.index.chunkCount).toBe(2);

    // policyState block
    expect(serialized.policyState.lastHealthySectionCount).toBe(55);
    expect(serialized.policyState.lastHealthyObservedAt).toBeGreaterThan(0);

    // evaluation block
    expect(serialized.evaluation.canaryVersion).toBe(CANARY_VERSION);
    expect(serialized.evaluation.warnings).toEqual([]);
    expect(serialized.evaluation.metrics.overviewRatio).toBeCloseTo(0.036);

    // compatibility block
    expect(serialized.compatibility.tokenizer).toBe(TOKENIZER_VERSION);
    expect(serialized.compatibility.chunker).toBe(CHUNKER_VERSION);
    expect(serialized.compatibility.ingestion).toBe(INGESTION_VERSION);
  });

  it('uses provided indexCreatedAt instead of Date.now()', () => {
    const chunks = [makeChunk('ts-1', 'timestamp test', ['timestamp', 'test'])];
    const index = buildBM25Index(chunks);
    const preserved = 1700000000000;
    const ctx = makeSerializeContext({ indexCreatedAt: preserved });
    const serialized = serializeIndex(index, 'ts-hash', ctx);
    expect(serialized.index.createdAt).toBe(preserved);
  });

  it('defaults to recent timestamp when indexCreatedAt omitted', () => {
    const chunks = [makeChunk('ts-2', 'default test', ['default', 'test'])];
    const index = buildBM25Index(chunks);
    const before = Date.now();
    const ctx = makeSerializeContext();
    const serialized = serializeIndex(index, 'ts-hash', ctx);
    expect(serialized.index.createdAt).toBeGreaterThanOrEqual(before);
  });

  it('round-trips through serialize/deserialize/parse', () => {
    const chunks = [
      makeChunk('rt-1', 'round trip test', ['round', 'trip', 'test']),
    ];
    const index = buildBM25Index(chunks);
    const ctx = makeSerializeContext();
    const serialized = serializeIndex(index, 'rt-hash', ctx);

    const parsed = parseSerializedIndex(serialized);
    expect(parsed).not.toBeNull();

    const restored = deserializeIndex(parsed!);
    expect(restored.chunks).toHaveLength(1);
    expect(restored.chunks[0].id).toBe('rt-1');
    expect(restored.avgDocLength).toBe(index.avgDocLength);
    expect(restored.docFrequency.get('round')).toBe(1);

    // Verify blocks survive parse round-trip
    expect(parsed!.corpus.contentHash).toBe('rt-hash');
    expect(parsed!.diagnostics.sectionCount).toBe(55);
    expect(parsed!.evaluation.canaryVersion).toBe(CANARY_VERSION);
    expect(parsed!.compatibility.tokenizer).toBe(TOKENIZER_VERSION);
  });

  it('rejects old-format (flat metadata) snapshots', () => {
    const oldFormat = {
      version: 3,
      contentHash: 'abc',
      avgDocLength: 2,
      docFrequency: [],
      invertedIndex: [],
      chunks: [],
      metadata: { createdAt: 1000 },
    };
    expect(parseSerializedIndex(oldFormat)).toBeNull();
  });

  it('rejects snapshot with missing required block', () => {
    const chunks = [makeChunk('a', 'hello', ['hello'])];
    const index = buildBM25Index(chunks);
    const ctx = makeSerializeContext();
    const serialized = serializeIndex(index, 'hash', ctx);

    // Remove a required block
    const incomplete = { ...serialized } as Record<string, unknown>;
    delete incomplete.evaluation;
    expect(parseSerializedIndex(incomplete)).toBeNull();
  });

  it('rejects non-object input', () => {
    expect(parseSerializedIndex(null)).toBeNull();
    expect(parseSerializedIndex(undefined)).toBeNull();
    expect(parseSerializedIndex('string')).toBeNull();
    expect(parseSerializedIndex(42)).toBeNull();
  });

  it('preserves null policyState fields', () => {
    const chunks = [makeChunk('a', 'hello', ['hello'])];
    const index = buildBM25Index(chunks);
    const ctx = makeSerializeContext({
      policyState: {
        lastHealthySectionCount: null,
        lastHealthyObservedAt: null,
      },
    });
    const serialized = serializeIndex(index, 'hash', ctx);
    const parsed = parseSerializedIndex(serialized);

    expect(parsed).not.toBeNull();
    expect(parsed!.policyState.lastHealthySectionCount).toBeNull();
    expect(parsed!.policyState.lastHealthyObservedAt).toBeNull();
  });

  it('preserves evaluation warnings through round-trip', () => {
    const chunks = [makeChunk('a', 'hello', ['hello'])];
    const index = buildBM25Index(chunks);
    const ctx = makeSerializeContext({
      evaluation: {
        canaryVersion: CANARY_VERSION,
        warnings: [
          {
            code: 'taxonomy_drift',
            severity: 'warn',
            details: { unmapped_section_count: 5 },
          },
          {
            code: 'parse_issues',
            severity: 'warn',
            details: { count: 3 },
          },
        ],
        metrics: {
          overviewRatio: 0.1,
          baselineSectionCount: 50,
          sectionCountDropRatio: 0.05,
        },
      },
    });
    const serialized = serializeIndex(index, 'hash', ctx);
    const parsed = parseSerializedIndex(serialized);

    expect(parsed).not.toBeNull();
    expect(parsed!.evaluation.warnings).toHaveLength(2);
    expect(parsed!.evaluation.warnings[0].code).toBe('taxonomy_drift');
    expect(parsed!.evaluation.warnings[1].code).toBe('parse_issues');
    expect(parsed!.evaluation.metrics.sectionCountDropRatio).toBeCloseTo(0.05);
  });
});
