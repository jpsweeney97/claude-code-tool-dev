import type { TrustMode } from './trust.js';

// --- Threshold constants (code constants, not env vars) ---

// --- Section count drift (unchanged from prior canary) ---
export const SECTION_COUNT_DRIFT_WARN_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_FAIL_THRESHOLD = 0.50;
export const OFFICIAL_MIN_SECTION_COUNT = 40;
export const UNSAFE_MIN_SECTION_COUNT = 3;

// --- Fallback-segment delta canary (replaces taxonomy_collapse / taxonomy_drift) ---
// Catches loader/normalization regressions where a full-shape corpus is loaded but
// suddenly many more sections fall to 'uncategorized'. Requires absolute AND relative
// increase from the last healthy baseline. Missing baseline = warn-only, never reject.
//
// UNITS: the *_REL constants are relative-INCREASE fractions, not multipliers.
// The gate compares the new/old multiplier against (1 + REL):
//   WARN_REL 0.50 → multiplier ≥ 1.5 → "+50% over baseline"
//   FAIL_REL 2.0  → multiplier ≥ 3.0 → "+200% over baseline (3x)"
// Do NOT compare the multiplier directly against REL (that was the C1 defect:
// `multiplier >= 0.50` is true for almost every load, making the gate inert).
export const FALLBACK_DELTA_WARN_ABS = 5;        // at least 5 more uncategorized sections than baseline
export const FALLBACK_DELTA_WARN_REL = 0.50;     // at least +50% over baseline (multiplier ≥ 1.5)
export const FALLBACK_DELTA_FAIL_ABS = 20;       // at least 20 more uncategorized sections than baseline
export const FALLBACK_DELTA_FAIL_REL = 2.0;      // at least 3x baseline / +200% (multiplier ≥ 3.0)

// --- Types ---

export interface LoaderDiagnostics {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  /** Count of sections whose URL has NO segment mapped in SECTION_TO_CATEGORY (i.e. deriveCategory returned 'uncategorized'). Section-level count, not segment-distinct count. */
  fallbackSectionCount: number;
  /** Count of DISTINCT unmapped URL segments encountered in this load. Used as a secondary signal — segment churn vs section churn. */
  fallbackSegmentCount: number;
  unmappedSegments: Array<[segment: string, count: number]>;
}

export interface CorpusDiagnostics extends LoaderDiagnostics {
  parseWarningCount: number;
}

export interface PolicyState {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
  /** Baseline for fallback delta canary. Section count that produced 'uncategorized' on the last accepted load. */
  lastHealthyFallbackSectionCount: number | null;
  lastHealthyFallbackObservedAt: number | null;
}

export type WarningCode = 'fallback_segment_drift' | 'parse_issues' | 'section_count_drift';

export interface CorpusWarning {
  code: WarningCode;
  severity: 'info' | 'warn' | 'error';
  details: Record<string, unknown>;
}

export type RejectionCode =
  | 'no_source_markers'
  | 'min_section_count'
  | 'section_count_collapse'
  | 'fallback_segment_collapse';

export interface CanaryRejection {
  code: RejectionCode;
  reason: string;
  details: Record<string, unknown>;
}

export interface CanaryMetrics {
  /** Sections classified as 'uncategorized' as a fraction of total. Replaces the broken overviewRatio. */
  fallbackSectionRatio: number;
  baselineSectionCount: number | null;
  sectionCountDropRatio: number | null;
  /** Absolute change in fallback section count from last healthy baseline. */
  fallbackSectionDelta: number | null;
  /** Multiplicative change in fallback section count from last healthy baseline. */
  fallbackSectionMultiplier: number | null;
}

export interface CanaryEvaluation {
  decision: 'accept' | 'reject';
  rejection: CanaryRejection | null;
  warnings: CorpusWarning[];
  metrics: CanaryMetrics;
  nextPolicyState: PolicyState;
}

export interface EvaluateCanariesInput {
  trustMode: TrustMode;
  diagnostics: CorpusDiagnostics;
  policyState: PolicyState;
  now: number;
  /** Override floor. Undefined → use OFFICIAL_MIN_SECTION_COUNT / UNSAFE_MIN_SECTION_COUNT per trust mode. 0 → no floor. */
  minSectionCount?: number;
}

export class CanaryRejectionError extends Error {
  readonly rejection: CanaryRejection;
  constructor(rejection: CanaryRejection) {
    super(`Canary rejection (${rejection.code}): ${rejection.reason}`);
    this.name = 'CanaryRejectionError';
    this.rejection = rejection;
  }
}

// --- Evaluation ---

function reject(
  code: RejectionCode,
  reason: string,
  details: Record<string, unknown>,
  metrics: CanaryMetrics,
  policyState: PolicyState,
): CanaryEvaluation {
  return {
    decision: 'reject',
    rejection: { code, reason, details },
    warnings: [],
    metrics,
    nextPolicyState: policyState,
  };
}

export function evaluateCanaries(input: EvaluateCanariesInput): CanaryEvaluation {
  const { trustMode, diagnostics, policyState, now } = input;
  const {
    sourceAnchoredCount,
    sectionCount,
    fallbackSectionCount,
    fallbackSegmentCount,
    parseWarningCount,
  } = diagnostics;

  const minSectionCount =
    input.minSectionCount !== undefined
      ? input.minSectionCount
      : trustMode === 'official' ? OFFICIAL_MIN_SECTION_COUNT : UNSAFE_MIN_SECTION_COUNT;

  const baselineSectionCount = policyState.lastHealthySectionCount;
  const sectionCountDropRatio =
    baselineSectionCount !== null && baselineSectionCount > 0
      ? (baselineSectionCount - sectionCount) / baselineSectionCount
      : null;

  const fallbackSectionRatio = sectionCount > 0 ? fallbackSectionCount / sectionCount : 0;

  const baselineFallback = policyState.lastHealthyFallbackSectionCount;
  const fallbackSectionDelta = baselineFallback !== null ? fallbackSectionCount - baselineFallback : null;
  // Multiplier is new/old (e.g. 1.5 means fallback is 1.5x baseline == +50%). The
  // relative gates below compare against (1 + REL) so REL reads as a relative-increase
  // fraction. See the UNITS note on the FALLBACK_DELTA_* constants.
  const fallbackSectionMultiplier =
    baselineFallback !== null && baselineFallback > 0
      ? fallbackSectionCount / baselineFallback
      : null;

  const metrics: CanaryMetrics = {
    fallbackSectionRatio,
    baselineSectionCount,
    sectionCountDropRatio,
    fallbackSectionDelta,
    fallbackSectionMultiplier,
  };

  // --- Structural canaries (both modes) ---

  if (sourceAnchoredCount === 0) {
    return reject('no_source_markers', 'No Source: markers found in corpus',
      { sourceAnchoredCount }, metrics, policyState);
  }

  // --- Section count collapse (official mode, requires baseline) ---
  // Check before min_section_count so collapse takes precedence over absolute floor.
  if (
    trustMode === 'official' &&
    sectionCountDropRatio !== null &&
    sectionCountDropRatio >= SECTION_COUNT_DRIFT_FAIL_THRESHOLD
  ) {
    return reject('section_count_collapse',
      `Section count dropped ${(sectionCountDropRatio * 100).toFixed(0)}% from baseline ${baselineSectionCount}`,
      { sectionCount, baselineSectionCount, dropRatio: sectionCountDropRatio },
      metrics, policyState);
  }

  if (sectionCount < minSectionCount) {
    return reject('min_section_count',
      `Section count ${sectionCount} below minimum ${minSectionCount}`,
      { sectionCount, minSectionCount }, metrics, policyState);
  }

  // --- Fallback-segment delta canary (official mode only) ---
  // Positive baseline: both absolute AND relative criteria must be met.
  // Zero baseline: the multiplier is null (no divide-by-zero), so the relative gate is
  //   inapplicable — gate on the absolute count alone (Blocker 1). Without this branch a
  //   0→many jump (e.g. a SECTION_TO_CATEGORY wipe landing a full-shape corpus as
  //   all-uncategorized) slips BOTH the FAIL and WARN gates below and then advances the
  //   baseline to the bad count, laundering the regression into trusted state.
  // Null baseline (first run): never reject — distinct from 0, do not conflate.
  if (
    trustMode === 'official' &&
    baselineFallback === 0 &&
    fallbackSectionCount >= FALLBACK_DELTA_FAIL_ABS
  ) {
    return reject('fallback_segment_collapse',
      `Fallback section count jumped from 0 to ${fallbackSectionCount} ` +
      `(prior healthy load had no uncategorized sections) — possible loader regression`,
      {
        fallbackSectionCount,
        baselineFallback,
        fallbackSectionDelta,
        fallbackSectionMultiplier,
        fallbackSegmentCount,
      },
      metrics, policyState);
  }

  if (
    trustMode === 'official' &&
    fallbackSectionDelta !== null &&
    fallbackSectionMultiplier !== null &&
    fallbackSectionDelta >= FALLBACK_DELTA_FAIL_ABS &&
    fallbackSectionMultiplier >= 1 + FALLBACK_DELTA_FAIL_REL
  ) {
    return reject('fallback_segment_collapse',
      `Fallback section count jumped from ${baselineFallback} to ${fallbackSectionCount} ` +
      `(+${fallbackSectionDelta}, ${fallbackSectionMultiplier.toFixed(1)}x) — possible loader regression`,
      {
        fallbackSectionCount,
        baselineFallback,
        fallbackSectionDelta,
        fallbackSectionMultiplier,
        fallbackSegmentCount,
      },
      metrics, policyState);
  }

  // --- Accepted: collect warnings ---
  const warnings: CorpusWarning[] = [];

  if (
    trustMode === 'official' &&
    sectionCountDropRatio !== null &&
    sectionCountDropRatio >= SECTION_COUNT_DRIFT_WARN_THRESHOLD
  ) {
    warnings.push({
      code: 'section_count_drift',
      severity: 'warn',
      details: { sectionCount, baselineSectionCount, dropRatio: sectionCountDropRatio },
    });
  }

  // Fallback-segment drift warning (official mode only)
  if (
    trustMode === 'official' &&
    fallbackSectionDelta !== null &&
    fallbackSectionMultiplier !== null &&
    fallbackSectionDelta >= FALLBACK_DELTA_WARN_ABS &&
    fallbackSectionMultiplier >= 1 + FALLBACK_DELTA_WARN_REL
  ) {
    warnings.push({
      code: 'fallback_segment_drift',
      severity: 'warn',
      details: {
        fallbackSectionCount,
        baselineFallback,
        fallbackSectionDelta,
        fallbackSectionMultiplier,
        sampleSegments: diagnostics.unmappedSegments.slice(0, 10).map(([seg]) => seg),
      },
    });
  }

  // Zero-baseline fallback drift warning (official mode): the relative WARN gate above
  // can't fire when baselineFallback === 0 (multiplier is null), so gate on absolute alone.
  // The zero-baseline FAIL gate already returned early, so reaching here means
  // fallbackSectionCount < FALLBACK_DELTA_FAIL_ABS.
  if (
    trustMode === 'official' &&
    baselineFallback === 0 &&
    fallbackSectionCount >= FALLBACK_DELTA_WARN_ABS
  ) {
    warnings.push({
      code: 'fallback_segment_drift',
      severity: 'warn',
      details: {
        fallbackSectionCount,
        baselineFallback,
        fallbackSectionDelta,
        fallbackSectionMultiplier,
        sampleSegments: diagnostics.unmappedSegments.slice(0, 10).map(([seg]) => seg),
      },
    });
  }

  // First-run fallback drift warning (official mode): on a null baseline there is no prior
  // healthy load to compare against, so we never reject — but the count is about to become
  // the trusted baseline below, so it must not be blessed SILENTLY. Surface a warn once the
  // count crosses the absolute WARN threshold, making a first-load classification regression
  // visible instead of laundered into trusted state. Absolute-count gate only (no ratio —
  // ratio gating on a fixed threshold was the original canary's fragility class).
  if (
    trustMode === 'official' &&
    baselineFallback === null &&
    fallbackSectionCount >= FALLBACK_DELTA_WARN_ABS
  ) {
    warnings.push({
      code: 'fallback_segment_drift',
      severity: 'warn',
      details: {
        fallbackSectionCount,
        baselineFallback,
        fallbackSectionDelta,
        fallbackSectionMultiplier,
        sampleSegments: diagnostics.unmappedSegments.slice(0, 10).map(([seg]) => seg),
      },
    });
  }

  if (parseWarningCount > 0) {
    warnings.push({
      code: 'parse_issues',
      severity: 'warn',
      details: { count: parseWarningCount },
    });
  }

  // --- Policy state advancement ---
  // Advance section-count baseline only when section_count_drift did not warn.
  // Advance fallback baseline only when fallback_segment_drift did not warn.
  const hasSectionCountDrift = warnings.some(w => w.code === 'section_count_drift');
  const hasFallbackDrift = warnings.some(w => w.code === 'fallback_segment_drift');

  let nextPolicyState: PolicyState;
  if (trustMode === 'unsafe') {
    nextPolicyState = policyState;
  } else {
    nextPolicyState = {
      lastHealthySectionCount: hasSectionCountDrift
        ? policyState.lastHealthySectionCount
        : sectionCount,
      lastHealthyObservedAt: hasSectionCountDrift
        ? policyState.lastHealthyObservedAt
        : now,
      // Freeze the fallback baseline on a drift warn ONLY when an established (non-null)
      // baseline exists. A null baseline (first run) must still establish even though the
      // first-run warn fired above — otherwise it would freeze at null forever and the
      // delta canary would never activate.
      lastHealthyFallbackSectionCount: (baselineFallback !== null && hasFallbackDrift)
        ? policyState.lastHealthyFallbackSectionCount
        : fallbackSectionCount,
      lastHealthyFallbackObservedAt: (baselineFallback !== null && hasFallbackDrift)
        ? policyState.lastHealthyFallbackObservedAt
        : now,
    };
  }

  return {
    decision: 'accept',
    rejection: null,
    warnings,
    metrics,
    nextPolicyState,
  };
}
