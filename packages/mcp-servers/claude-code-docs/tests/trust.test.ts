import { describe, it, expect } from 'vitest';
import { isProvenanceBetter, SOURCE_KIND_RANK } from '../src/trust.js';
import type { TrustMode, SourceKind, CorpusProvenance } from '../src/trust.js';

describe('SOURCE_KIND_RANK', () => {
  it('ranks fetched highest', () => {
    expect(SOURCE_KIND_RANK['fetched']).toBeGreaterThan(SOURCE_KIND_RANK['cached']);
    expect(SOURCE_KIND_RANK['cached']).toBeGreaterThan(SOURCE_KIND_RANK['stale-fallback']);
    expect(SOURCE_KIND_RANK['stale-fallback']).toBeGreaterThan(SOURCE_KIND_RANK['bundled-snapshot']);
  });
});

describe('isProvenanceBetter', () => {
  it('prefers more recent obtainedAt regardless of source kind', () => {
    const current: CorpusProvenance = { sourceKind: 'cached', obtainedAt: 2000 };
    const cached: CorpusProvenance = { sourceKind: 'fetched', obtainedAt: 1000 };
    expect(isProvenanceBetter(current, cached)).toBe(true);
  });

  it('uses source kind rank as tiebreaker at same timestamp', () => {
    const current: CorpusProvenance = { sourceKind: 'fetched', obtainedAt: 1000 };
    const cached: CorpusProvenance = { sourceKind: 'stale-fallback', obtainedAt: 1000 };
    expect(isProvenanceBetter(current, cached)).toBe(true);
  });

  it('returns false when cached is more recent', () => {
    const current: CorpusProvenance = { sourceKind: 'fetched', obtainedAt: 1000 };
    const cached: CorpusProvenance = { sourceKind: 'cached', obtainedAt: 2000 };
    expect(isProvenanceBetter(current, cached)).toBe(false);
  });

  it('returns false when same timestamp and same rank', () => {
    const current: CorpusProvenance = { sourceKind: 'cached', obtainedAt: 1000 };
    const cached: CorpusProvenance = { sourceKind: 'cached', obtainedAt: 1000 };
    expect(isProvenanceBetter(current, cached)).toBe(false);
  });
});
