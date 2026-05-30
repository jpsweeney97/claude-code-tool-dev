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

  it('first run with notable fallback warns for visibility and still establishes the baseline', () => {
    // P1: a null baseline must not SILENTLY bless a first-load fallback count. We can't
    // reject (no prior healthy load to compare against, and the real corpus legitimately
    // carries ~25 uncategorized sections), but the first run must surface a
    // fallback_segment_drift warn AND establish the baseline so the canary becomes active.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 50 },
      policyState: {
        lastHealthySectionCount: null, lastHealthyObservedAt: null,
        lastHealthyFallbackSectionCount: null, lastHealthyFallbackObservedAt: null,
      },
      now: 99,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(true);
    // Establishment must survive the first-run warn (no freeze deadlock).
    expect(result.nextPolicyState.lastHealthyFallbackSectionCount).toBe(50);
    expect(result.nextPolicyState.lastHealthyFallbackObservedAt).toBe(99);
  });

  it('first run with no notable fallback stays quiet (no warn noise) and establishes baseline', () => {
    // The first-run visibility warn is gated on the absolute WARN threshold, so a clean
    // first load with few/no uncategorized sections does not emit spurious warnings.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 2 },
      policyState: {
        lastHealthySectionCount: null, lastHealthyObservedAt: null,
        lastHealthyFallbackSectionCount: null, lastHealthyFallbackObservedAt: null,
      },
      now: 99,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(false);
    expect(result.nextPolicyState.lastHealthyFallbackSectionCount).toBe(2);
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

  it('FAIL relative boundary: multiplier compared against 1+FAIL_REL=3.0, not FAIL_REL=2.0', () => {
    // Both inputs hold the absolute delta at/above FAIL_ABS (20) so the relative gate is the
    // sole discriminator — isolating the multiplier-units guard at the FAIL boundary the same
    // way the WARN cases isolate it at 1.5. If the gate ever regressed to comparing the
    // multiplier directly against FAIL_REL (2.0), the 2.8x 'accept' case would wrongly reject.
    //
    // At-threshold: baseline 10, new 30 → delta +20 (== FAIL_ABS), mult 3.0 (== 1+FAIL_REL) → reject.
    const atThreshold = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 30 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    expect(atThreshold.decision).toBe('reject');
    expect(atThreshold.rejection?.code).toBe('fallback_segment_collapse');

    // Just-below: baseline 10, new 28 → delta +18 (< FAIL_ABS 20) AND mult 2.8 (< 3.0) → accept.
    // mult 2.8 is >= FAIL_REL 2.0, so a direct multiplier>=FAIL_REL comparison would mis-reject here.
    const justBelow = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 28 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 10, lastHealthyFallbackObservedAt: 0,
      },
      now: 1,
    });
    expect(justBelow.decision).toBe('accept');
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

  it('freeze-then-accumulate: a WARN freezes the baseline, then a later load crosses FAIL relative to the FROZEN value', () => {
    // Sequenced regime the existing single-shot tests never exercise: drift is gradual.
    // Load 1 warns (freezes the fallback baseline at 6); load 2 — fed the frozen state —
    // crosses FAIL against the FROZEN 6, not against load 1's suspect count.
    //
    // Load 1: baseline 6, new 12 → delta +6 (≥ WARN_ABS 5, < FAIL_ABS 20),
    //         mult 2.0 (≥ 1+WARN_REL 1.5, < 1+FAIL_REL 3.0) → warn, accept, FREEZE at 6.
    const warned = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 12 },
      policyState: {
        lastHealthySectionCount: 140, lastHealthyObservedAt: 0,
        lastHealthyFallbackSectionCount: 6, lastHealthyFallbackObservedAt: 0,
      },
      now: 100,
    });
    expect(warned.decision).toBe('accept');
    expect(warned.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(true);
    // The drift warn must have FROZEN the baseline at 6 (not advanced it to the suspect 12).
    expect(warned.nextPolicyState.lastHealthyFallbackSectionCount).toBe(6);
    expect(warned.nextPolicyState.lastHealthyFallbackObservedAt).toBe(0);

    // Load 2: feed the frozen state back, now with 30 uncategorized sections.
    //   delta vs FROZEN 6 = +24 (≥ FAIL_ABS 20), mult 30/6 = 5.0 (≥ 1+FAIL_REL 3.0) → reject.
    // The freeze is load-bearing: had the baseline advanced to 12 on load 1,
    //   delta would be 30−12 = 18 (< FAIL_ABS 20) and load 2 would NOT reject.
    const rejected = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 30 },
      policyState: warned.nextPolicyState,
      now: 200,
    });
    expect(rejected.decision).toBe('reject');
    expect(rejected.rejection?.code).toBe('fallback_segment_collapse');
  });
});
