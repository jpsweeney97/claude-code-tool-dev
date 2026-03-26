import { describe, it, expect } from 'vitest';
import {
  evaluateCanaries,
  TAXONOMY_DRIFT_WARN_THRESHOLD,
  TAXONOMY_DRIFT_FAIL_THRESHOLD,
  SECTION_COUNT_DRIFT_WARN_THRESHOLD,
  SECTION_COUNT_DRIFT_FAIL_THRESHOLD,
  OFFICIAL_MIN_SECTION_COUNT,
  UNSAFE_MIN_SECTION_COUNT,
} from '../src/canary.js';
import type {
  CorpusDiagnostics,
  PolicyState,
  CanaryEvaluation,
  CorpusWarning,
} from '../src/canary.js';

describe('canary threshold constants', () => {
  it('has graduated taxonomy thresholds', () => {
    expect(TAXONOMY_DRIFT_WARN_THRESHOLD).toEqual({ minSections: 3, minRatio: 0.05 });
    expect(TAXONOMY_DRIFT_FAIL_THRESHOLD).toBe(0.20);
  });

  it('has section count drift thresholds', () => {
    expect(SECTION_COUNT_DRIFT_WARN_THRESHOLD).toBe(0.20);
    expect(SECTION_COUNT_DRIFT_FAIL_THRESHOLD).toBe(0.50);
  });

  it('has per-mode minimum section counts', () => {
    expect(OFFICIAL_MIN_SECTION_COUNT).toBe(40);
    expect(UNSAFE_MIN_SECTION_COUNT).toBe(3);
  });
});

function makeDiagnostics(overrides: Partial<CorpusDiagnostics> = {}): CorpusDiagnostics {
  return {
    sourceAnchoredCount: 50,
    nonEmptySectionCount: 50,
    sectionCount: 50,
    overviewSectionCount: 0,
    fallbackOverviewCount: 0,
    unmappedSegments: [],
    parseWarningCount: 0,
    ...overrides,
  };
}

function emptyPolicyState(): PolicyState {
  return { lastHealthySectionCount: null, lastHealthyObservedAt: null };
}

function establishedPolicyState(count: number): PolicyState {
  return { lastHealthySectionCount: count, lastHealthyObservedAt: 1000 };
}

const NOW = 5000;

describe('evaluateCanaries — official mode', () => {
  // --- Structural hard-fail canaries ---

  it('rejects when sourceAnchoredCount is 0', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sourceAnchoredCount: 0 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('no_source_markers');
  });

  it('rejects when sectionCount below official minimum', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 10, nonEmptySectionCount: 10 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('min_section_count');
  });

  it('handles sectionCount=0 without division by zero', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({
        sourceAnchoredCount: 1,
        sectionCount: 0,
        nonEmptySectionCount: 0,
        overviewSectionCount: 0,
      }),
      policyState: emptyPolicyState(),
      now: 1000,
    });

    expect(result.decision).toBe('reject');
    expect(result.rejection?.code).toBe('min_section_count');
    expect(result.metrics.overviewRatio).toBe(0);
  });

  // --- Section count drift ---

  it('accepts first load without baseline — no drift possible', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 45 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'section_count_drift')).toBeUndefined();
  });

  it('warns when section count drops >= 20% below baseline', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 40 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    const drift = result.warnings.find(w => w.code === 'section_count_drift');
    expect(drift).toBeDefined();
    expect(drift!.severity).toBe('warn');
  });

  it('does not warn when section count drop is just under 20%', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 41 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'section_count_drift')).toBeUndefined();
  });

  it('rejects when section count drops >= 50% below baseline', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 25 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('section_count_collapse');
  });

  // --- Taxonomy drift ---

  it('warns when fallback overview count reaches max(3, 5%) threshold', () => {
    // 50 sections, 5% = 2.5 → max(3, 2.5) = 3
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ fallbackOverviewCount: 3, overviewSectionCount: 3 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    const drift = result.warnings.find(w => w.code === 'taxonomy_drift');
    expect(drift).toBeDefined();
    expect(drift!.severity).toBe('warn');
  });

  it('does not warn when fallback overview count is below threshold', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ fallbackOverviewCount: 2, overviewSectionCount: 2 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'taxonomy_drift')).toBeUndefined();
  });

  it('does not warn when overviewSectionCount is high but fallbackOverviewCount is zero', () => {
    // Explicitly-mapped overview sections should not trigger taxonomy_drift.
    // This is the bypass-path test: 10 overview sections, all explicitly mapped, 0 fallback.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 10, fallbackOverviewCount: 0, sectionCount: 70 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'taxonomy_drift')).toBeUndefined();
  });

  it('rejects when overview share reaches 20%', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 10, sectionCount: 50 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('taxonomy_collapse');
  });

  it('does not reject at 19% overview share', () => {
    // 50 sections, 19% = 9.5, so 9 sections should be just under
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 9, sectionCount: 50 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
  });

  // --- Parse issues ---

  it('emits parse_issues warning when parseWarningCount > 0', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ parseWarningCount: 3 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    const parse = result.warnings.find(w => w.code === 'parse_issues');
    expect(parse).toBeDefined();
    expect(parse!.details).toHaveProperty('count', 3);
  });

  // --- Policy state advancement ---

  it('advances baseline on clean official load', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 55 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.nextPolicyState.lastHealthySectionCount).toBe(55);
    expect(result.nextPolicyState.lastHealthyObservedAt).toBe(NOW);
  });

  it('does not advance baseline when section_count_drift warning fires', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 40 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.nextPolicyState.lastHealthySectionCount).toBe(50);
    expect(result.nextPolicyState.lastHealthyObservedAt).toBe(1000);
  });

  it('advances baseline even when taxonomy warnings fire (orthogonal)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 55, overviewSectionCount: 4, fallbackOverviewCount: 4 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    expect(result.warnings.find(w => w.code === 'taxonomy_drift')).toBeDefined();
    expect(result.nextPolicyState.lastHealthySectionCount).toBe(55);
  });

  it('establishes baseline on first clean official load', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 50 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.nextPolicyState.lastHealthySectionCount).toBe(50);
    expect(result.nextPolicyState.lastHealthyObservedAt).toBe(NOW);
  });

  // --- Metrics ---

  it('includes computed metrics in result', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 5, sectionCount: 50 }),
      policyState: establishedPolicyState(60),
      now: NOW,
    });
    expect(result.metrics.overviewRatio).toBeCloseTo(0.1);
    expect(result.metrics.baselineSectionCount).toBe(60);
    expect(result.metrics.sectionCountDropRatio).toBeCloseTo((60 - 50) / 60);
  });

  // --- Property: nextPolicyState.lastHealthySectionCount invariant ---

  it('nextPolicyState.lastHealthySectionCount is always null, previous value, or current sectionCount', () => {
    const inputs = [
      { diagnostics: makeDiagnostics({ sectionCount: 50 }), policyState: emptyPolicyState() },
      { diagnostics: makeDiagnostics({ sectionCount: 40 }), policyState: establishedPolicyState(50) },
      { diagnostics: makeDiagnostics({ sectionCount: 55 }), policyState: establishedPolicyState(50) },
    ];
    for (const { diagnostics, policyState } of inputs) {
      const result = evaluateCanaries({ trustMode: 'official', diagnostics, policyState, now: NOW });
      const next = result.nextPolicyState.lastHealthySectionCount;
      const valid = next === null || next === policyState.lastHealthySectionCount || next === diagnostics.sectionCount;
      expect(valid).toBe(true);
    }
  });
});

describe('evaluateCanaries — unsafe mode', () => {
  it('rejects when sourceAnchoredCount is 0', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ sourceAnchoredCount: 0 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('no_source_markers');
  });

  it('rejects when sectionCount below unsafe minimum (3)', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ sectionCount: 2, nonEmptySectionCount: 2 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection!.code).toBe('min_section_count');
  });

  it('accepts 3 sections in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ sectionCount: 3, nonEmptySectionCount: 3 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
  });

  it('ignores taxonomy drift in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ overviewSectionCount: 40, sectionCount: 50 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'taxonomy_drift')).toBeUndefined();
  });

  it('does not advance policyState in unsafe mode', () => {
    const prevState = establishedPolicyState(50);
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ sectionCount: 55 }),
      policyState: prevState,
      now: NOW,
    });
    expect(result.nextPolicyState).toEqual(prevState);
  });

  it('preserves parse_issues in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ parseWarningCount: 2 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    const parse = result.warnings.find(w => w.code === 'parse_issues');
    expect(parse).toBeDefined();
  });

  it('does not reject on large section count drop from baseline in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ sectionCount: 20 }), // 60% drop from baseline of 50
      policyState: establishedPolicyState(50),
      now: 1000,
    });

    expect(result.decision).toBe('accept');
    // No section_count_drift or section_count_collapse warnings
    const codes = result.warnings.map(w => w.code);
    expect(codes).not.toContain('section_count_drift');
  });
});
