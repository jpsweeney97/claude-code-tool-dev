// src/status.ts
import { z } from 'zod';
import type { TrustMode, SourceKind } from './trust.js';
import type { WarningCode } from './canary.js';

// ---------------------------------------------------------------------------
// Zod schemas (declared first — types below are derived from these)
// ---------------------------------------------------------------------------

export const TrustModeSchema = z.enum(['official', 'unsafe']);

export const SourceKindSchema = z.enum(['fetched', 'cached', 'stale-fallback', 'bundled-snapshot']);

export const StatusWarningCodeSchema = z.enum([
  'taxonomy_drift',
  'parse_issues',
  'section_count_drift',
  'stale_corpus',
]);

export const RuntimeStatusSchema = z.object({
  trust_mode: TrustModeSchema,
  docs_origin: z.string(),
  docs_url: z.string(),
  source_kind: SourceKindSchema.nullable(),
  index_created_at: z.string().nullable(),
  corpus_age_ms: z.number().nullable(),
  corpus_obtained_at: z.string().nullable(),
  last_load_attempt_at: z.string().nullable(),
  last_load_error: z.string().nullable(),
  warning_codes: z.array(StatusWarningCodeSchema),
  is_loading: z.boolean(),
});

export const SearchMetaSchema = z.object({
  trust_mode: TrustModeSchema,
  source_kind: SourceKindSchema.nullable(),
  index_created_at: z.string().nullable(),
  corpus_age_ms: z.number().nullable(),
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type StatusWarningCode = WarningCode | 'stale_corpus';

export interface RuntimeStatusInput {
  trustMode: TrustMode;
  docsUrl: string;
  corpus: { sourceKind: SourceKind; obtainedAt: number } | null;
  index: { createdAt: number } | null;
  lastLoadAttemptAt: number | null;
  lastLoadError: string | null;
  warningCodes: WarningCode[];
  isLoading: boolean;
  nowMs?: number;
}

/** Derived from RuntimeStatusSchema — ensures compatibility with MCP structuredContent. */
export type RuntimeStatus = z.infer<typeof RuntimeStatusSchema>;

/** Derived from SearchMetaSchema — four-field inline provenance attached to search responses. */
export type SearchMeta = z.infer<typeof SearchMetaSchema>;

// ---------------------------------------------------------------------------
// Builders
// ---------------------------------------------------------------------------

/**
 * Build a full RuntimeStatus snapshot from ServerState accessors.
 *
 * - docs_origin: hostname of docsUrl
 * - stale_corpus: appended to warning_codes when sourceKind === 'stale-fallback'
 * - corpus_age_ms: computed at response time as (nowMs - corpus.obtainedAt)
 * - lastLoadAttemptAt === 0 is treated as "never attempted" → null
 */
export function buildRuntimeStatus(input: RuntimeStatusInput): RuntimeStatus {
  const {
    trustMode,
    docsUrl,
    corpus,
    index,
    lastLoadAttemptAt,
    lastLoadError,
    warningCodes,
    isLoading,
    nowMs = Date.now(),
  } = input;

  // Derive docs_origin from URL hostname
  let docsOrigin: string;
  try {
    docsOrigin = new URL(docsUrl).hostname;
  } catch {
    docsOrigin = docsUrl;
  }

  // Derive stale_corpus from sourceKind at response time
  const isStale = corpus?.sourceKind === 'stale-fallback';
  const allWarnings: StatusWarningCode[] = isStale
    ? [...warningCodes, 'stale_corpus']
    : [...warningCodes];

  return {
    trust_mode: trustMode,
    docs_origin: docsOrigin,
    docs_url: docsUrl,
    source_kind: corpus?.sourceKind ?? null,
    index_created_at: index !== null ? new Date(index.createdAt).toISOString() : null,
    corpus_age_ms: corpus !== null ? nowMs - corpus.obtainedAt : null,
    corpus_obtained_at: corpus !== null ? new Date(corpus.obtainedAt).toISOString() : null,
    last_load_attempt_at: lastLoadAttemptAt !== null && lastLoadAttemptAt !== 0
      ? new Date(lastLoadAttemptAt).toISOString()
      : null,
    last_load_error: lastLoadError,
    warning_codes: allWarnings,
    is_loading: isLoading,
  };
}

/**
 * Project four-field inline search meta from a RuntimeStatus.
 * These four fields are attached to every search response.
 */
export function projectSearchMeta(status: RuntimeStatus): SearchMeta {
  return {
    trust_mode: status.trust_mode,
    source_kind: status.source_kind,
    index_created_at: status.index_created_at,
    corpus_age_ms: status.corpus_age_ms,
  };
}
