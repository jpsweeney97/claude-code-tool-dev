import { describe, it, expect } from 'vitest';
import {
  evaluateCanaries,
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
    fallbackSectionCount: 0,
    fallbackSegmentCount: 0,
    unmappedSegments: [],
    parseWarningCount: 0,
    ...overrides,
  };
}

function emptyPolicyState(): PolicyState {
  return {
    lastHealthySectionCount: null,
    lastHealthyObservedAt: null,
    lastHealthyFallbackSectionCount: null,
    lastHealthyFallbackObservedAt: null,
  };
}

function establishedPolicyState(count: number, fallbackCount: number | null = null): PolicyState {
  return {
    lastHealthySectionCount: count,
    lastHealthyObservedAt: 1000,
    lastHealthyFallbackSectionCount: fallbackCount,
    lastHealthyFallbackObservedAt: fallbackCount !== null ? 1000 : null,
  };
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
        fallbackSectionCount: 0,
      }),
      policyState: emptyPolicyState(),
      now: 1000,
    });

    expect(result.decision).toBe('reject');
    expect(result.rejection?.code).toBe('min_section_count');
    expect(result.metrics.fallbackSectionRatio).toBe(0);
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
      diagnostics: makeDiagnostics({ fallbackSectionCount: 5, sectionCount: 50 }),
      policyState: establishedPolicyState(60),
      now: NOW,
    });
    expect(result.metrics.fallbackSectionRatio).toBeCloseTo(0.1);
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

describe('evaluateCanaries — minSectionCount override', () => {
  it('respects minSectionCount override from input', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: {
        sourceAnchoredCount: 10,
        nonEmptySectionCount: 10,
        sectionCount: 10,
        fallbackSectionCount: 0,
        fallbackSegmentCount: 0,
        unmappedSegments: [],
        parseWarningCount: 0,
      },
      policyState: {
        lastHealthySectionCount: null,
        lastHealthyObservedAt: null,
        lastHealthyFallbackSectionCount: null,
        lastHealthyFallbackObservedAt: null,
      },
      now: 1,
      minSectionCount: 5,
    });
    expect(result.decision).toBe('accept'); // 10 >= 5 (override) even though default would be 40
  });

  it('respects minSectionCount = 0 (floor disabled)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: {
        sourceAnchoredCount: 1,
        nonEmptySectionCount: 1,
        sectionCount: 1,
        fallbackSectionCount: 0,
        fallbackSegmentCount: 0,
        unmappedSegments: [],
        parseWarningCount: 0,
      },
      policyState: {
        lastHealthySectionCount: null,
        lastHealthyObservedAt: null,
        lastHealthyFallbackSectionCount: null,
        lastHealthyFallbackObservedAt: null,
      },
      now: 1,
      minSectionCount: 0,
    });
    expect(result.decision).toBe('accept');
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

  it('ignores fallback segment drift in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: makeDiagnostics({ fallbackSectionCount: 40, sectionCount: 50 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.find(w => w.code === 'fallback_segment_drift')).toBeUndefined();
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

describe('fallback_segment_collapse (delta canary)', () => {
  const baseDiag = {
    sourceAnchoredCount: 140,
    nonEmptySectionCount: 140,
    sectionCount: 140,
    fallbackSegmentCount: 0,
    unmappedSegments: [] as Array<[string, number]>,
    parseWarningCount: 0,
  };

  it('does not reject when baseline is null (first run)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 50 },
      policyState: {
        lastHealthySectionCount: null, lastHealthyObservedAt: null,
        lastHealthyFallbackSectionCount: null, lastHealthyFallbackObservedAt: null,
      },
      now: 1,
    });
    expect(result.decision).toBe('accept');
  });

  it('rejects when fallback jumps absolutely AND relatively past thresholds', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 60 }, // +50 abs, 6x rel from baseline=10
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection?.code).toBe('fallback_segment_collapse');
  });

  it('warns but does not reject when fallback exceeds WARN but not FAIL thresholds', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 16 }, // +6 abs (>= WARN_ABS 5, < FAIL_ABS 20), 1.6x mult (>= 1+WARN_REL = 1.5, < 1+FAIL_REL = 3.0) -> warn, no reject
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(true);
  });

  it('does not warn when fallback shrinks or stays same', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 8 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(false);
  });

  it('advances baseline only when fallback_segment_drift did not warn', () => {
    const accepted = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 8 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 42,
    });
    expect(accepted.nextPolicyState.lastHealthyFallbackSectionCount).toBe(8);
    expect(accepted.nextPolicyState.lastHealthyFallbackObservedAt).toBe(42);
  });

  it('today\'s real-world data (141 sections, 24 fallback) passes when baseline allows growth', () => {
    // Simulates the live scenario that caused the original failure.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: {
        sourceAnchoredCount: 141,
        nonEmptySectionCount: 141,
        sectionCount: 141,
        fallbackSectionCount: 24,
        fallbackSegmentCount: 24,
        unmappedSegments: [],
        parseWarningCount: 0,
      },
      policyState: {
        lastHealthySectionCount: 100, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 18, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    // 24 vs 18 baseline = +6 abs (warn threshold), 1.33x rel (below warn threshold of 1.5)
    // → no warn, accept
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(false);
  });

  // --- Zero-baseline branch (Blocker 1): the multiplier is null at baseline 0, so the
  //     relative gates can't fire; the absolute-only branch must catch a 0→many wipe. ---

  it('zero baseline, small growth: accepts quietly and advances the baseline (0→3)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 3 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 0, lastHealthyFallbackObservedAt: 0,
      },
      now: 7,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(false);
    // Below WARN_ABS, no drift → baseline advances to the new (still-healthy) count.
    expect(result.nextPolicyState.lastHealthyFallbackSectionCount).toBe(3);
  });

  it('zero baseline, WARN_ABS reached: warns and freezes the baseline at 0 (0→5)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 5 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 0, lastHealthyFallbackObservedAt: 0,
      },
      now: 7,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(true);
    // Drift warned → baseline must NOT advance to the suspect count.
    expect(result.nextPolicyState.lastHealthyFallbackSectionCount).toBe(0);
  });

  it('zero baseline, FAIL_ABS reached: rejects a 0→many wipe (0→20)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 20 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 0, lastHealthyFallbackObservedAt: 0,
      },
      now: 7,
    });
    expect(result.decision).toBe('reject');
    expect(result.rejection?.code).toBe('fallback_segment_collapse');
  });
});
