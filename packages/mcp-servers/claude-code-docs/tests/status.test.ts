// tests/status.test.ts
import { describe, it, expect } from 'vitest';
import {
  buildRuntimeStatus,
  projectSearchMeta,
  type RuntimeStatusInput,
  type RuntimeStatus,
} from '../src/status.js';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const BASE_INPUT: RuntimeStatusInput = {
  trustMode: 'official',
  docsUrl: 'https://code.claude.com/docs/llms-full.txt',
  corpus: { sourceKind: 'fetched', obtainedAt: 1700000000000 },
  index: { createdAt: 1700000001000 },
  lastLoadAttemptAt: 1700000001000,
  lastLoadError: null,
  warningCodes: [],
  isLoading: false,
  nowMs: 1700000060000,
};

// ---------------------------------------------------------------------------
// buildRuntimeStatus
// ---------------------------------------------------------------------------

describe('buildRuntimeStatus', () => {
  it('builds complete status from full input', () => {
    const status = buildRuntimeStatus(BASE_INPUT);

    expect(status.trust_mode).toBe('official');
    expect(status.docs_origin).toBe('code.claude.com');
    expect(status.docs_url).toBe('https://code.claude.com/docs/llms-full.txt');
    expect(status.source_kind).toBe('fetched');
    expect(status.index_created_at).toBe(new Date(1700000001000).toISOString());
    expect(status.corpus_age_ms).toBe(1700000060000 - 1700000000000);
    expect(status.corpus_obtained_at).toBe(new Date(1700000000000).toISOString());
    expect(status.last_load_attempt_at).toBe(new Date(1700000001000).toISOString());
    expect(status.last_load_error).toBeNull();
    expect(status.warning_codes).toEqual([]);
    expect(status.is_loading).toBe(false);
  });

  it('derives docs_origin from URL hostname', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      docsUrl: 'https://example.internal/docs/llms-full.txt',
      trustMode: 'unsafe',
    });

    expect(status.docs_origin).toBe('example.internal');
  });

  it('falls back to full URL for malformed docsUrl', () => {
    const badUrl = 'not-a-valid-url';
    const status = buildRuntimeStatus({ ...BASE_INPUT, docsUrl: badUrl });
    expect(status.docs_origin).toBe(badUrl);
  });

  it('appends stale_corpus warning when sourceKind is stale-fallback', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: { sourceKind: 'stale-fallback', obtainedAt: 1700000000000 },
    });

    expect(status.warning_codes).toContain('stale_corpus');
    expect(status.source_kind).toBe('stale-fallback');
  });

  it('preserves other warning_codes when appending stale_corpus', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: { sourceKind: 'stale-fallback', obtainedAt: 1700000000000 },
      warningCodes: ['parse_issues'],
    });

    expect(status.warning_codes).toEqual(['parse_issues', 'stale_corpus']);
  });

  it('does not append stale_corpus when sourceKind is fetched', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: { sourceKind: 'fetched', obtainedAt: 1700000000000 },
    });

    expect(status.warning_codes).not.toContain('stale_corpus');
  });

  it('does not append stale_corpus when sourceKind is cached', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: { sourceKind: 'cached', obtainedAt: 1700000000000 },
    });

    expect(status.warning_codes).not.toContain('stale_corpus');
  });

  it('does not append stale_corpus when sourceKind is bundled-snapshot', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: { sourceKind: 'bundled-snapshot', obtainedAt: 1700000000000 },
    });

    expect(status.warning_codes).not.toContain('stale_corpus');
  });

  it('returns null fields when corpus is null', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      corpus: null,
      index: null,
    });

    expect(status.source_kind).toBeNull();
    expect(status.corpus_age_ms).toBeNull();
    expect(status.corpus_obtained_at).toBeNull();
    expect(status.index_created_at).toBeNull();
  });

  it('returns null for last_load_attempt_at when lastLoadAttemptAt is null', () => {
    const status = buildRuntimeStatus({ ...BASE_INPUT, lastLoadAttemptAt: null });
    expect(status.last_load_attempt_at).toBeNull();
  });

  it('returns null for last_load_attempt_at when lastLoadAttemptAt is 0 (never attempted)', () => {
    const status = buildRuntimeStatus({ ...BASE_INPUT, lastLoadAttemptAt: 0 });
    expect(status.last_load_attempt_at).toBeNull();
  });

  it('surfaces load error', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      lastLoadError: 'Fetch failed: 503',
    });
    expect(status.last_load_error).toBe('Fetch failed: 503');
  });

  it('reflects is_loading=true', () => {
    const status = buildRuntimeStatus({ ...BASE_INPUT, isLoading: true });
    expect(status.is_loading).toBe(true);
  });

  it('uses Date.now() when nowMs is not provided', () => {
    const before = Date.now();
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      nowMs: undefined,
      corpus: { sourceKind: 'fetched', obtainedAt: before - 5000 },
    });
    const after = Date.now();

    // corpus_age_ms should be approximately 5000ms
    expect(status.corpus_age_ms).toBeGreaterThanOrEqual(5000);
    expect(status.corpus_age_ms).toBeLessThan(after - (before - 5000) + 100);
  });
});

// ---------------------------------------------------------------------------
// projectSearchMeta
// ---------------------------------------------------------------------------

describe('projectSearchMeta', () => {
  it('projects exactly four fields from RuntimeStatus', () => {
    const status = buildRuntimeStatus(BASE_INPUT);
    const meta = projectSearchMeta(status);

    const keys = Object.keys(meta).sort();
    expect(keys).toEqual(['corpus_age_ms', 'index_created_at', 'source_kind', 'trust_mode'].sort());
  });

  it('returns only four keys', () => {
    const status = buildRuntimeStatus(BASE_INPUT);
    const meta = projectSearchMeta(status);
    expect(Object.keys(meta)).toHaveLength(4);
  });

  it('copies the correct values', () => {
    const status = buildRuntimeStatus(BASE_INPUT);
    const meta = projectSearchMeta(status);

    expect(meta.trust_mode).toBe(status.trust_mode);
    expect(meta.source_kind).toBe(status.source_kind);
    expect(meta.index_created_at).toBe(status.index_created_at);
    expect(meta.corpus_age_ms).toBe(status.corpus_age_ms);
  });

  it('handles null fields correctly', () => {
    const status = buildRuntimeStatus({ ...BASE_INPUT, corpus: null, index: null });
    const meta = projectSearchMeta(status);

    expect(meta.source_kind).toBeNull();
    expect(meta.index_created_at).toBeNull();
    expect(meta.corpus_age_ms).toBeNull();
  });

  it('does not include warning_codes, docs_url, or other status fields', () => {
    const status = buildRuntimeStatus(BASE_INPUT);
    const meta = projectSearchMeta(status) as Record<string, unknown>;

    expect(meta['warning_codes']).toBeUndefined();
    expect(meta['docs_url']).toBeUndefined();
    expect(meta['docs_origin']).toBeUndefined();
    expect(meta['last_load_error']).toBeUndefined();
    expect(meta['is_loading']).toBeUndefined();
  });
});
