export type TrustMode = 'official' | 'unsafe';
export type SourceKind = 'fetched' | 'cached' | 'stale-fallback' | 'bundled-snapshot';

export interface CorpusProvenance {
  sourceKind: SourceKind;
  obtainedAt: number;
}

export const SOURCE_KIND_RANK: Record<SourceKind, number> = {
  'fetched': 3,
  'cached': 2,
  'stale-fallback': 1,
  'bundled-snapshot': 0,
};

/**
 * Compare two provenance records to determine if `current` is better than `cached`.
 * Recency is the primary signal; source kind rank is the tiebreaker.
 */
export function isProvenanceBetter(
  current: CorpusProvenance,
  cached: CorpusProvenance,
): boolean {
  if (current.obtainedAt > cached.obtainedAt) return true;
  if (current.obtainedAt === cached.obtainedAt) {
    return SOURCE_KIND_RANK[current.sourceKind] > SOURCE_KIND_RANK[cached.sourceKind];
  }
  return false;
}
