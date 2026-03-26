import type { TrustMode } from './trust.js';

// --- Threshold constants (code constants, not env vars) ---

export const TAXONOMY_DRIFT_WARN_THRESHOLD = { minSections: 3, minRatio: 0.05 };
export const TAXONOMY_DRIFT_FAIL_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_WARN_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_FAIL_THRESHOLD = 0.50;
export const OFFICIAL_MIN_SECTION_COUNT = 40;
export const UNSAFE_MIN_SECTION_COUNT = 3;

// --- Types ---

export interface LoaderDiagnostics {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  overviewSectionCount: number;
  fallbackOverviewCount: number;
  unmappedSegments: Array<[segment: string, count: number]>;
}

export interface CorpusDiagnostics extends LoaderDiagnostics {
  parseWarningCount: number;
}

export interface PolicyState {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
}

export type WarningCode = 'taxonomy_drift' | 'parse_issues' | 'section_count_drift';

export interface CorpusWarning {
  code: WarningCode;
  severity: 'info' | 'warn' | 'error';
  details: Record<string, unknown>;
}

export type RejectionCode =
  | 'no_source_markers'
  | 'min_section_count'
  | 'section_count_collapse'
  | 'taxonomy_collapse';

export interface CanaryRejection {
  code: RejectionCode;
  reason: string;
  details: Record<string, unknown>;
}

export interface CanaryMetrics {
  overviewRatio: number;
  baselineSectionCount: number | null;
  sectionCountDropRatio: number | null;
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
  const { sourceAnchoredCount, sectionCount, overviewSectionCount, fallbackOverviewCount, parseWarningCount } = diagnostics;

  const minSectionCount = trustMode === 'official' ? OFFICIAL_MIN_SECTION_COUNT : UNSAFE_MIN_SECTION_COUNT;
  const overviewRatio = sectionCount > 0 ? overviewSectionCount / sectionCount : 0;
  const fallbackOverviewRatio = sectionCount > 0 ? fallbackOverviewCount / sectionCount : 0;
  const baselineSectionCount = policyState.lastHealthySectionCount;
  const sectionCountDropRatio =
    baselineSectionCount !== null && baselineSectionCount > 0
      ? (baselineSectionCount - sectionCount) / baselineSectionCount
      : null;

  const metrics: CanaryMetrics = { overviewRatio, baselineSectionCount, sectionCountDropRatio };

  // --- Structural canaries (both modes) ---

  if (sourceAnchoredCount === 0) {
    return reject(
      'no_source_markers',
      'No Source: markers found in corpus',
      { sourceAnchoredCount },
      metrics,
      policyState,
    );
  }

  // --- Section count drift (official mode only, requires baseline) ---
  // Check before min_section_count so collapse takes precedence over absolute floor.

  if (
    trustMode === 'official' &&
    sectionCountDropRatio !== null &&
    sectionCountDropRatio >= SECTION_COUNT_DRIFT_FAIL_THRESHOLD
  ) {
    return reject(
      'section_count_collapse',
      `Section count dropped ${(sectionCountDropRatio * 100).toFixed(0)}% from baseline ${baselineSectionCount}`,
      { sectionCount, baselineSectionCount, dropRatio: sectionCountDropRatio },
      metrics,
      policyState,
    );
  }

  if (sectionCount < minSectionCount) {
    return reject(
      'min_section_count',
      `Section count ${sectionCount} below minimum ${minSectionCount}`,
      { sectionCount, minSectionCount },
      metrics,
      policyState,
    );
  }

  // --- Taxonomy drift (official mode only) ---

  if (trustMode === 'official' && overviewRatio >= TAXONOMY_DRIFT_FAIL_THRESHOLD) {
    return reject(
      'taxonomy_collapse',
      `Overview share ${(overviewRatio * 100).toFixed(0)}% exceeds ${(TAXONOMY_DRIFT_FAIL_THRESHOLD * 100).toFixed(0)}% threshold`,
      { overviewSectionCount, sectionCount, overviewRatio },
      metrics,
      policyState,
    );
  }

  // --- Accepted: collect warnings ---

  const warnings: CorpusWarning[] = [];

  // Section count drift warning (official mode only)
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

  // Taxonomy drift warning (official mode only)
  // Driven by fallbackOverviewCount (sections that defaulted to overview because no
  // mapping exists), not overviewSectionCount (which includes explicitly-mapped overview pages).
  if (trustMode === 'official') {
    const warnMinSections = TAXONOMY_DRIFT_WARN_THRESHOLD.minSections;
    const warnMinRatio = TAXONOMY_DRIFT_WARN_THRESHOLD.minRatio;
    const warnThreshold = Math.max(warnMinSections, Math.ceil(sectionCount * warnMinRatio));

    if (fallbackOverviewCount >= warnThreshold) {
      warnings.push({
        code: 'taxonomy_drift',
        severity: 'warn',
        details: {
          unmapped_section_count: fallbackOverviewCount,
          unmapped_ratio: fallbackOverviewRatio,
          sample_segments: diagnostics.unmappedSegments
            .slice(0, 10)
            .map(([seg]) => seg),
        },
      });
    }
  }

  // Parse issues (both modes)
  if (parseWarningCount > 0) {
    warnings.push({
      code: 'parse_issues',
      severity: 'warn',
      details: { count: parseWarningCount },
    });
  }

  // --- Policy state advancement ---

  const hasSectionCountDrift = warnings.some(w => w.code === 'section_count_drift');
  let nextPolicyState: PolicyState;

  if (trustMode === 'unsafe') {
    nextPolicyState = policyState;
  } else if (hasSectionCountDrift) {
    nextPolicyState = policyState;
  } else {
    nextPolicyState = {
      lastHealthySectionCount: sectionCount,
      lastHealthyObservedAt: now,
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
