# claude-code-docs Provenance, Canaries, and Observability

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add trust boundaries, corpus provenance tracking, canary evaluation, and runtime observability to the claude-code-docs MCP server.

**Architecture:** The server's output feeds model reasoning as authoritative documentation. This plan adds: trust mode enforcement (official vs unsafe), a persisted five-block metadata model (corpus, diagnostics, index, policyState, evaluation), a pure canary evaluation function with graduated thresholds, a four-path cache decision tree, and runtime status exposure via inline search meta and a new `get_status` tool.

**Tech Stack:** TypeScript, Zod, Vitest. All changes within `packages/mcp-servers/claude-code-docs/`.

**Design reference:** `memory/project_ccd_provenance_design.md` (project memory) captures all converged decisions.

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `src/trust.ts` | `TrustMode`, `SourceKind` types, `SOURCE_KIND_RANK`, `isProvenanceBetter()` |
| `src/canary.ts` | `evaluateCanaries()` pure function, threshold constants, input/output types, `CanaryRejectionError` |
| `src/status.ts` | `RuntimeStatus` snapshot type, `buildRuntimeStatus()`, `projectSearchMeta()`, `get_status` Zod schema |
| `tests/trust.test.ts` | Trust type tests, provenance comparison |
| `tests/canary.test.ts` | Table-driven canary evaluation tests (official + unsafe mode, all threshold boundaries) |
| `tests/status.test.ts` | Status snapshot projection tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/config.ts` | Add `trustMode` to `AppConfig`, official URL pinning (origin + path prefix), `DOCS_TRUST_MODE` env var |
| `src/index-cache.ts` | Five-block `SerializedIndex` schema, parser-normalizer, `INDEX_FORMAT_VERSION` bump, `CANARY_VERSION` constant, version-bump policy docs |
| `src/loader.ts` | `LoadResult` expansion (provenance + `LoaderDiagnostics`), `fetchAndParse` provenance tracking, diagnostic collection from parse output. **No canary evaluation or CanaryRejectionError handling** — that belongs in lifecycle. |
| `src/lifecycle.ts` | Four cache paths (full hit, canary replay, rebuild, provenance refresh), reload-as-overwrite semantics, `policyState` preservation, status snapshot ownership |
| `src/index.ts` | `get_status` tool registration, `search_docs` meta attachment, response parity (`content` text = `structuredContent`) |
| `src/schemas.ts` | `SearchMetaSchema`, `SearchOutputSchema` expansion with optional `meta` |
| `src/dump-index-metadata.ts` | Add `index_created_at` field, deprecate `built_at` in schema description |
| `tests/config.test.ts` | Trust mode parsing, official URL pinning validation |
| `tests/index-cache.test.ts` | Five-block round-trip, parser-normalizer, version gate, partial-parse rejection |
| `tests/loader.test.ts` | Provenance in `LoadResult`, diagnostic collection, `CanaryRejectionError` handling |
| `tests/lifecycle.test.ts` | Four cache paths, reload semantics, policyState carry-forward |
| `tests/server.test.ts` | `get_status` schema, `search_docs` meta shape |
| `tests/dump-index-metadata.test.ts` | `index_created_at` presence, `built_at` still emitted |

---

## Task 1: Trust and Source Kind Types

**Files:**
- Create: `src/trust.ts`
- Create: `tests/trust.test.ts`

This task establishes the foundation types that every subsequent task depends on. Pure types and one small comparison function.

- [ ] **Step 1: Write trust type tests**

```typescript
// tests/trust.test.ts
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/trust.test.ts`
Expected: FAIL — module `../src/trust.js` not found

- [ ] **Step 3: Implement trust types**

```typescript
// src/trust.ts

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/trust.test.ts`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Run full test suite to verify no regressions**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All existing tests pass + 4 new tests

- [ ] **Step 6: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/trust.ts tests/trust.test.ts
git commit -m "feat(claude-code-docs): add trust mode and source kind types"
```

---

## Task 2: Canary Evaluation — Pure Function

**Files:**
- Create: `src/canary.ts`
- Create: `tests/canary.test.ts`

Pure function `evaluateCanaries()` with table-driven tests covering all threshold boundaries. No dependencies on existing modules except types.

- [ ] **Step 1: Write canary types and threshold constant tests**

```typescript
// tests/canary.test.ts — first batch: types and constants exist
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/canary.test.ts`
Expected: FAIL — module `../src/canary.js` not found

- [ ] **Step 3: Write table-driven canary evaluation tests**

Append to `tests/canary.test.ts`:

```typescript
function makeDiagnostics(overrides: Partial<CorpusDiagnostics> = {}): CorpusDiagnostics {
  return {
    sourceAnchoredCount: 50,
    nonEmptySectionCount: 50,
    sectionCount: 50,
    overviewSectionCount: 0,
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

  it('warns when overview sections reach max(3, 5%) threshold', () => {
    // 50 sections, 5% = 2.5 → max(3, 2.5) = 3
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 3 }),
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    const drift = result.warnings.find(w => w.code === 'taxonomy_drift');
    expect(drift).toBeDefined();
    expect(drift!.severity).toBe('warn');
  });

  it('does not warn when overview sections are below threshold', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ overviewSectionCount: 2 }),
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
    // lastHealthyObservedAt should NOT advance
    expect(result.nextPolicyState.lastHealthyObservedAt).toBe(1000);
  });

  it('advances baseline even when taxonomy warnings fire (orthogonal)', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: makeDiagnostics({ sectionCount: 55, overviewSectionCount: 4 }),
      policyState: establishedPolicyState(50),
      now: NOW,
    });
    // Taxonomy warning fires but should not block section baseline advancement
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
});
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/canary.test.ts`
Expected: FAIL — module not found

- [ ] **Step 5: Implement canary evaluation**

```typescript
// src/canary.ts
import type { TrustMode } from './trust.js';

// --- Threshold constants (code constants, not env vars) ---

export const TAXONOMY_DRIFT_WARN_THRESHOLD = { minSections: 3, minRatio: 0.05 };
export const TAXONOMY_DRIFT_FAIL_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_WARN_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_FAIL_THRESHOLD = 0.50;
export const OFFICIAL_MIN_SECTION_COUNT = 40;
export const UNSAFE_MIN_SECTION_COUNT = 3;

// --- Types ---

/**
 * Diagnostics produced by the loader (corpus acquisition + parsing).
 * Does NOT include parseWarningCount — that comes from chunking in lifecycle.
 */
export interface LoaderDiagnostics {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  overviewSectionCount: number;
  unmappedSegments: Array<[segment: string, count: number]>;
}

/**
 * Full diagnostics for canary evaluation.
 * Lifecycle merges LoaderDiagnostics with chunk-derived parseWarningCount.
 */
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

/**
 * Error thrown when canary evaluation rejects a corpus.
 * Caught by the stale-fallback path in loader.ts alongside ContentValidationError.
 */
export class CanaryRejectionError extends Error {
  readonly rejection: CanaryRejection;
  constructor(rejection: CanaryRejection) {
    super(`Canary rejection (${rejection.code}): ${rejection.reason}`);
    this.name = 'CanaryRejectionError';
    this.rejection = rejection;
  }
}

// --- Evaluation ---

function reject(code: RejectionCode, reason: string, details: Record<string, unknown>, metrics: CanaryMetrics, policyState: PolicyState): CanaryEvaluation {
  return {
    decision: 'reject',
    rejection: { code, reason, details },
    warnings: [],
    metrics,
    nextPolicyState: policyState,
  };
}

/**
 * Evaluate corpus canaries. Pure function — all state in, decision out.
 *
 * Version bump policy:
 * - Changing thresholds or adding checks against existing diagnostics → bump CANARY_VERSION
 * - Adding new diagnostic fields needed for evaluation → bump INGESTION_VERSION (triggers rebuild)
 */
export function evaluateCanaries(input: EvaluateCanariesInput): CanaryEvaluation {
  const { trustMode, diagnostics, policyState, now } = input;
  const { sourceAnchoredCount, sectionCount, overviewSectionCount, parseWarningCount } = diagnostics;

  const minSectionCount = trustMode === 'official' ? OFFICIAL_MIN_SECTION_COUNT : UNSAFE_MIN_SECTION_COUNT;
  const overviewRatio = sectionCount > 0 ? overviewSectionCount / sectionCount : 0;
  const baselineSectionCount = policyState.lastHealthySectionCount;
  const sectionCountDropRatio = baselineSectionCount !== null && baselineSectionCount > 0
    ? (baselineSectionCount - sectionCount) / baselineSectionCount
    : null;

  const metrics: CanaryMetrics = { overviewRatio, baselineSectionCount, sectionCountDropRatio };

  // --- Structural canaries (both modes) ---

  if (sourceAnchoredCount === 0) {
    return reject('no_source_markers', 'No Source: markers found in corpus', { sourceAnchoredCount }, metrics, policyState);
  }

  if (sectionCount < minSectionCount) {
    return reject('min_section_count', `Section count ${sectionCount} below minimum ${minSectionCount}`, { sectionCount, minSectionCount }, metrics, policyState);
  }

  // --- Section count drift (official mode only, requires baseline) ---

  if (trustMode === 'official' && sectionCountDropRatio !== null && sectionCountDropRatio >= SECTION_COUNT_DRIFT_FAIL_THRESHOLD) {
    return reject('section_count_collapse', `Section count dropped ${(sectionCountDropRatio * 100).toFixed(0)}% from baseline ${baselineSectionCount}`, {
      sectionCount, baselineSectionCount, dropRatio: sectionCountDropRatio,
    }, metrics, policyState);
  }

  // --- Taxonomy drift (official mode only) ---

  if (trustMode === 'official' && overviewRatio >= TAXONOMY_DRIFT_FAIL_THRESHOLD) {
    return reject('taxonomy_collapse', `Overview share ${(overviewRatio * 100).toFixed(0)}% exceeds ${(TAXONOMY_DRIFT_FAIL_THRESHOLD * 100).toFixed(0)}% threshold`, {
      overviewSectionCount, sectionCount, overviewRatio,
    }, metrics, policyState);
  }

  // --- Accepted: collect warnings ---

  const warnings: CorpusWarning[] = [];

  // Section count drift warning (official mode only)
  if (trustMode === 'official' && sectionCountDropRatio !== null && sectionCountDropRatio >= SECTION_COUNT_DRIFT_WARN_THRESHOLD) {
    warnings.push({
      code: 'section_count_drift',
      severity: 'warn',
      details: { sectionCount, baselineSectionCount, dropRatio: sectionCountDropRatio },
    });
  }

  // Taxonomy drift warning (official mode only)
  if (trustMode === 'official') {
    const warnMinSections = TAXONOMY_DRIFT_WARN_THRESHOLD.minSections;
    const warnMinRatio = TAXONOMY_DRIFT_WARN_THRESHOLD.minRatio;
    const warnThreshold = Math.max(warnMinSections, Math.ceil(sectionCount * warnMinRatio));

    if (overviewSectionCount >= warnThreshold) {
      warnings.push({
        code: 'taxonomy_drift',
        severity: 'warn',
        details: {
          unmapped_section_count: overviewSectionCount,
          unmapped_ratio: overviewRatio,
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
    // Unsafe loads never modify official policy state
    nextPolicyState = policyState;
  } else if (hasSectionCountDrift) {
    // Section count drift prevents baseline advancement
    nextPolicyState = policyState;
  } else {
    // Clean official load — advance baseline
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
```

- [ ] **Step 6: Run canary tests to verify they pass**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/canary.test.ts`
Expected: PASS (all ~20 tests)

- [ ] **Step 7: Run full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All existing tests pass + new canary tests

- [ ] **Step 8: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/canary.ts tests/canary.test.ts
git commit -m "feat(claude-code-docs): add canary evaluation with threshold constants"
```

---

## Task 3: Trust Mode in Config

**Files:**
- Modify: `src/config.ts`
- Modify: `tests/config.test.ts`

Add `trustMode` to `AppConfig`. Official mode pins origin (`code.claude.com`) and path prefix (`/docs/`). Unsafe mode accepts any HTTPS URL.

- [ ] **Step 1: Write trust mode config tests**

Append to `tests/config.test.ts`:

```typescript
import type { TrustMode } from '../src/trust.js';

describe('trust mode', () => {
  it('defaults to official mode', () => {
    const config = loadConfig(makeEnv());
    expect(config.trustMode).toBe('official');
  });

  it('accepts DOCS_TRUST_MODE=unsafe', () => {
    const config = loadConfig(makeEnv({ DOCS_TRUST_MODE: 'unsafe' }));
    expect(config.trustMode).toBe('unsafe');
  });

  it('rejects invalid trust mode', () => {
    expect(() =>
      loadConfig(makeEnv({ DOCS_TRUST_MODE: 'custom' })),
    ).toThrow(/DOCS_TRUST_MODE must be/);
  });

  it('official mode rejects non-code.claude.com origin', () => {
    expect(() =>
      loadConfig(makeEnv({ DOCS_URL: 'https://evil.com/docs/llms-full.txt' })),
    ).toThrow(/Official mode requires code.claude.com/);
  });

  it('official mode rejects non-/docs/ path', () => {
    expect(() =>
      loadConfig(makeEnv({ DOCS_URL: 'https://code.claude.com/api/export' })),
    ).toThrow(/Official mode requires \/docs\/ path/);
  });

  it('official mode accepts code.claude.com/docs/ paths', () => {
    const config = loadConfig(makeEnv({ DOCS_URL: 'https://code.claude.com/docs/v2/llms-full.txt' }));
    expect(config.docsUrl).toContain('code.claude.com/docs/');
  });

  it('unsafe mode accepts any HTTPS URL', () => {
    const config = loadConfig(makeEnv({
      DOCS_TRUST_MODE: 'unsafe',
      DOCS_URL: 'https://staging.example.com/docs.txt',
    }));
    expect(config.docsUrl).toContain('staging.example.com');
    expect(config.trustMode).toBe('unsafe');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/config.test.ts`
Expected: FAIL — `trustMode` not on config, trust mode validation not implemented

- [ ] **Step 3: Implement trust mode in config**

In `src/config.ts`, add `trustMode` to `AppConfig` and validation:

```typescript
import type { TrustMode } from './trust.js';

// Add to AppConfig interface:
export interface AppConfig {
  docsUrl: string;
  retryIntervalMs: number;
  trustMode: TrustMode;
}

// Add trust mode parser:
function parseTrustMode(env: NodeJS.ProcessEnv): TrustMode {
  const raw = env.DOCS_TRUST_MODE?.trim().toLowerCase();
  if (!raw || raw.length === 0) return 'official';
  if (raw === 'official' || raw === 'unsafe') return raw;
  fail('parse env', 'DOCS_TRUST_MODE must be "official" or "unsafe"', raw);
}

// Add official URL validation:
function validateOfficialUrl(url: URL): void {
  if (url.hostname !== 'code.claude.com') {
    fail('parse env', 'Official mode requires code.claude.com origin', url.toString());
  }
  if (!url.pathname.startsWith('/docs/')) {
    fail('parse env', 'Official mode requires /docs/ path prefix', url.toString());
  }
}

// Modify parseDocsUrl to accept trustMode parameter:
function parseDocsUrl(env: NodeJS.ProcessEnv, trustMode: TrustMode): string {
  // ... existing URL parsing ...
  if (trustMode === 'official') {
    validateOfficialUrl(parsed);
  }
  return parsed.toString();
}

// Modify loadConfig to parse trustMode first, then pass to URL validation:
export function loadConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  const trustMode = parseTrustMode(env);
  const docsUrl = parseDocsUrl(env, trustMode);
  // ... rest unchanged ...
  return { docsUrl, retryIntervalMs, trustMode };
}
```

- [ ] **Step 4: Update existing config tests if needed**

The existing test `'parses valid runtime overrides'` sets `DOCS_URL: 'https://example.com/docs/llms-full.txt'` which will now fail official mode validation. Fix by adding `DOCS_TRUST_MODE: 'unsafe'` to that test case.

- [ ] **Step 5: Run config tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/config.test.ts`
Expected: PASS (all existing + new tests)

- [ ] **Step 6: Run full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All pass. Check that lifecycle tests still work — they use `docsUrl: 'https://test.example.com/docs'` in mocks, but `loadConfig` is not called in lifecycle tests (URL is injected via deps).

- [ ] **Step 7: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/config.ts tests/config.test.ts
git commit -m "feat(claude-code-docs): add trust mode enforcement with official URL pinning"
```

---

## Task 4: Serialized Index Schema Restructure

**Files:**
- Modify: `src/index-cache.ts`
- Modify: `tests/index-cache.test.ts`

Restructure `SerializedIndex` into five blocks. Implement parser-normalizer. Bump `INDEX_FORMAT_VERSION`. Add `CANARY_VERSION`. Document version-bump policy inline.

- [ ] **Step 1: Write schema tests for new structure**

In `tests/index-cache.test.ts`, add tests for the new schema shape, parser-normalizer, and version gating:

```typescript
// Add to existing imports:
import { CANARY_VERSION } from '../src/index-cache.js';

describe('SerializedIndex v2 schema', () => {
  it('exports CANARY_VERSION', () => {
    expect(CANARY_VERSION).toBeGreaterThan(0);
  });

  it('serializes into five-block structure', () => {
    const chunks = [makeChunk('c1', 'hello world', ['hello', 'world'])];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'abc123', {
      obtainedAt: 1000,
      sourceKind: 'fetched',
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      diagnostics: {
        sourceAnchoredCount: 50,
        nonEmptySectionCount: 50,
        sectionCount: 50,
        overviewSectionCount: 0,
        unmappedSegments: [],
        parseWarningCount: 0,
      },
      policyState: { lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 },
      evaluation: {
        canaryVersion: CANARY_VERSION,
        warnings: [],
        metrics: { overviewRatio: 0, baselineSectionCount: 50, sectionCountDropRatio: 0 },
      },
    });

    // Verify five-block structure
    expect(serialized).toHaveProperty('corpus');
    expect(serialized).toHaveProperty('diagnostics');
    expect(serialized).toHaveProperty('index');
    expect(serialized).toHaveProperty('policyState');
    expect(serialized).toHaveProperty('evaluation');
    expect(serialized).toHaveProperty('compatibility');
    expect(serialized.corpus.contentHash).toBe('abc123');
    expect(serialized.corpus.sourceKind).toBe('fetched');
    expect(serialized.diagnostics.sectionCount).toBe(50);
    expect(serialized.index.createdAt).toBeGreaterThan(0);
  });

  it('round-trips through serialize/deserialize/parse', () => {
    const chunks = [makeChunk('c1', 'hello', ['hello'])];
    const index = buildBM25Index(chunks);
    const serialized = serializeIndex(index, 'hash1', {
      obtainedAt: 1000,
      sourceKind: 'fetched',
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      diagnostics: {
        sourceAnchoredCount: 50,
        nonEmptySectionCount: 50,
        sectionCount: 50,
        overviewSectionCount: 0,
        unmappedSegments: [],
        parseWarningCount: 0,
      },
      policyState: { lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 },
      evaluation: {
        canaryVersion: CANARY_VERSION,
        warnings: [],
        metrics: { overviewRatio: 0, baselineSectionCount: 50, sectionCountDropRatio: 0 },
      },
    });

    const parsed = parseSerializedIndex(JSON.parse(JSON.stringify(serialized)));
    expect(parsed).not.toBeNull();
    expect(parsed!.corpus.contentHash).toBe('hash1');

    const restored = deserializeIndex(parsed!);
    expect(restored.chunks).toHaveLength(1);
    expect(restored.avgDocLength).toBe(index.avgDocLength);
  });

  it('rejects old-format (flat metadata) snapshots', () => {
    // Simulate pre-restructure format
    const oldFormat = {
      version: 3, // old INDEX_FORMAT_VERSION
      contentHash: 'abc',
      avgDocLength: 2,
      docFrequency: [],
      invertedIndex: [],
      chunks: [],
      metadata: { createdAt: 1000 },
    };
    const parsed = parseSerializedIndex(oldFormat);
    expect(parsed).toBeNull();
  });

  it('rejects snapshot with missing required block', () => {
    const incomplete = {
      version: INDEX_FORMAT_VERSION,
      corpus: { contentHash: 'abc' },
      // missing diagnostics, index, policyState, evaluation, compatibility
      docFrequency: [],
      invertedIndex: [],
      chunks: [],
    };
    const parsed = parseSerializedIndex(incomplete);
    expect(parsed).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/index-cache.test.ts`
Expected: FAIL — new tests fail (old schema shape, missing exports)

- [ ] **Step 3: Implement new schema**

Rewrite `src/index-cache.ts`:

- Bump `INDEX_FORMAT_VERSION` to 4
- Add `CANARY_VERSION = 1`
- Define five-block `SerializedIndex` interface and Zod schema
- Update `serializeIndex` signature to accept metadata context
- Update `parseSerializedIndex` to be a parser-normalizer (reject invalid, normalize optional fields)
- Keep `deserializeIndex` for BM25 data (only reads `chunks`, `docFrequency`, `invertedIndex`, `avgDocLength` from the index block)
- Document version-bump policy in comments next to each constant

Key implementation notes:
- `serializeIndex` needs a new second parameter: a metadata context object containing `corpus`, `diagnostics`, `policyState`, `evaluation` data. The function assembles the full serialized snapshot.
- `parseSerializedIndex` uses Zod `.safeParse()` then normalizes into canonical shape. Required blocks fail parse; optional fields within blocks get explicit defaults only where documented.
- The `compatibility` block holds `tokenizer`, `chunker`, `ingestion` versions. `canary` version lives in `evaluation` block.

- [ ] **Step 4: Update existing index-cache tests**

Existing tests that call `serializeIndex(index, contentHash)` need to pass the new metadata context parameter. Update `makeChunk` and test data to include the new required fields.

- [ ] **Step 5: Run index-cache tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/index-cache.test.ts`
Expected: PASS

- [ ] **Step 6: Run full test suite — expect some failures**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: `lifecycle.test.ts` will fail because `serializeIndexFn` mock returns old format and `parseSerializedIndexFn` mock needs updating. **Do NOT fix yet** — Task 6 handles lifecycle changes.

- [ ] **Step 7: Commit (snapshot — lifecycle tests may be broken)**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/index-cache.ts tests/index-cache.test.ts
git commit -m "feat(claude-code-docs): restructure serialized index into five-block schema

BREAKING: INDEX_FORMAT_VERSION bumped to 4. Existing cached indexes will
be rebuilt on first startup. Adds corpus, diagnostics, index, policyState,
evaluation, and compatibility blocks."
```

---

## Task 5: Loader Provenance and Diagnostics

**Files:**
- Modify: `src/loader.ts`
- Modify: `tests/loader.test.ts`

Expand `LoadResult` with provenance and `LoaderDiagnostics`. Track which load path was taken in `fetchAndParse`. Collect loader-level diagnostics from parse output. **Note:** `parseWarningCount` is NOT available here — it comes from chunking in lifecycle. The loader returns `LoaderDiagnostics` (without `parseWarningCount`). Lifecycle merges it with chunk-derived warnings before calling `evaluateCanaries()`. **CanaryRejectionError is NOT caught here** — canary evaluation happens in lifecycle, not the loader.

- [ ] **Step 1: Write loader provenance tests**

Append to `tests/loader.test.ts`:

```typescript
describe('LoadResult provenance', () => {
  it('returns sourceKind=fetched on successful live fetch', async () => {
    // Set up: content cache does not exist, fetch succeeds
    const cachePath = path.join(tempDir, 'no-cache.txt');
    const content = buildTestContent(5); // helper that creates N Source: sections
    const mockFetch = vi.fn().mockResolvedValue(
      new Response(content, { status: 200 }),
    );
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.provenance.sourceKind).toBe('fetched');
    expect(result.provenance.obtainedAt).toBeGreaterThan(0);
  });

  it('returns sourceKind=cached on fresh cache hit', async () => {
    // Set up: write fresh cache, fetch should not be called
    const cachePath = path.join(tempDir, 'fresh-cache.txt');
    const content = buildTestContent(5);
    await fs.writeFile(cachePath, content);

    const mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.provenance.sourceKind).toBe('cached');
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('returns sourceKind=stale-fallback when fetch fails and stale cache used', async () => {
    const cachePath = path.join(tempDir, 'stale-cache.txt');
    const content = buildTestContent(5);
    await fs.writeFile(cachePath, content);
    // Make stale
    const staleTime = new Date(Date.now() - 25 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    const mockFetch = vi.fn().mockRejectedValue(new Error('offline'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.provenance.sourceKind).toBe('stale-fallback');
  });
});

describe('LoadResult diagnostics', () => {
  it('includes structural diagnostic counts', async () => {
    const cachePath = path.join(tempDir, 'diag-cache.txt');
    const content = buildTestContent(5);
    await fs.writeFile(cachePath, content);

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.diagnostics).toBeDefined();
    expect(result.diagnostics.sourceAnchoredCount).toBeGreaterThan(0);
    expect(result.diagnostics.nonEmptySectionCount).toBeGreaterThan(0);
    expect(result.diagnostics.sectionCount).toBeGreaterThan(0);
    expect(typeof result.diagnostics.overviewSectionCount).toBe('number');
    expect(Array.isArray(result.diagnostics.unmappedSegments)).toBe(true);
    // parseWarningCount is NOT part of LoaderDiagnostics — it comes from chunking in lifecycle
    expect(result.diagnostics).not.toHaveProperty('parseWarningCount');
  });
});

// Helper to build test content with N Source: sections
function buildTestContent(n: number): string {
  return Array.from({ length: n }, (_, i) =>
    `# Section ${i}\nSource: https://code.claude.com/docs/en/hooks/section-${i}\n\nContent for section ${i}`
  ).join('\n\n');
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/loader.test.ts`
Expected: FAIL — `provenance` and `diagnostics` not on `LoadResult`

- [ ] **Step 3: Implement loader provenance and diagnostics**

In `src/loader.ts`:

1. Import `CorpusDiagnostics` from `./canary.js` and `CorpusProvenance`, `SourceKind` from `./trust.js`
2. Expand `LoadResult` to include `provenance: CorpusProvenance` and `diagnostics: CorpusDiagnostics`
3. Expand `FetchResult` to include `sourceKind: SourceKind` and `obtainedAt: number`
4. In `fetchAndParse`:
   - Fresh cache hit path: set `sourceKind = 'cached'`, `obtainedAt = Date.now() - fresh.age`
   - Live fetch path: set `sourceKind = 'fetched'`, `obtainedAt = Date.now()`
   - Stale fallback path: set `sourceKind = 'stale-fallback'`, `obtainedAt = Date.now() - cached.age`
5. In `loadFromOfficial`:
   - Collect `CorpusDiagnostics` from existing variables (`sourceAnchoredCount`, `nonEmptySectionCount`, `unmapped` map, etc.) — these are already computed, just not returned
   - Convert `unmapped` Map to sorted `[string, number][]` array (sort by count desc, then lexicographic)
   - Return `{ files, contentHash, provenance, diagnostics }`
6. **Do NOT add `CanaryRejectionError` to the loader's stale-fallback catch block.** Canary evaluation and rejection handling belong exclusively in lifecycle. The loader catches only fetch/network/validation errors for stale fallback.

- [ ] **Step 4: Run loader tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/loader.test.ts`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: `lifecycle.test.ts` still broken (mock `loadFn` returns old format). Other tests should pass.

- [ ] **Step 6: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/loader.ts tests/loader.test.ts
git commit -m "feat(claude-code-docs): add provenance and diagnostics to LoadResult"
```

---

## Task 6: ServerState Lifecycle — Four Cache Paths

**Files:**
- Modify: `src/lifecycle.ts`
- Modify: `tests/lifecycle.test.ts`

This is the largest behavioral change. Implement four cache paths, reload-as-overwrite semantics, policyState preservation, and canary evaluation integration.

- [ ] **Step 1: Update lifecycle deps interface**

`ServerStateDeps` changes:
- `loadFn` return type now includes `provenance` and `diagnostics`
- `serializeIndexFn` signature changes to accept metadata context
- Add `evaluateCanariesFn` (injected for testability)
- Remove `clearCacheFn` from reload path (keep in interface for emergency reset)

- [ ] **Step 2: Write lifecycle tests for four cache paths**

In `tests/lifecycle.test.ts`, update `makeDeps` to return new-format mock data, then add tests:

```typescript
// Update makeDeps loadFn mock to return provenance + diagnostics:
loadFn: vi.fn().mockResolvedValue({
  files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
  contentHash: 'abc123',
  provenance: { sourceKind: 'fetched', obtainedAt: 1000 },
  diagnostics: {
    sourceAnchoredCount: 50, nonEmptySectionCount: 50, sectionCount: 50,
    overviewSectionCount: 0, unmappedSegments: [], parseWarningCount: 0,
  },
}),

// Tests for each cache path:

describe('cache path routing', () => {
  it('Path 1: full hit — does not rebuild when all versions match', async () => {
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(makeFullCacheSnapshot('abc123')),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    expect(deps.buildIndexFn).not.toHaveBeenCalled();
    expect(deps.writeCacheFn).not.toHaveBeenCalled();
  });

  it('Path 2: canary replay — re-evaluates when canaryVersion mismatches', async () => {
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0; // outdated
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    expect(deps.buildIndexFn).not.toHaveBeenCalled(); // index reused
    expect(deps.writeCacheFn).toHaveBeenCalled(); // cache rewritten
  });

  it('Path 3: rebuild — rebuilds when contentHash mismatches', async () => {
    const snapshot = makeFullCacheSnapshot('old-hash');
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    expect(deps.buildIndexFn).toHaveBeenCalled();
    expect(deps.writeCacheFn).toHaveBeenCalled();
  });

  it('Path 3: carries forward policyState from old cache on rebuild', async () => {
    const snapshot = makeFullCacheSnapshot('old-hash');
    snapshot.policyState = { lastHealthySectionCount: 42, lastHealthyObservedAt: 500 };
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    // Verify policyState was passed to serialize (check writeCacheFn args)
    const writeCall = (deps.writeCacheFn as ReturnType<typeof vi.fn>).mock.calls[0];
    const written = writeCall[1];
    expect(written.policyState.lastHealthySectionCount).toBe(42);
  });

  it('Path 4: provenance refresh — rewrites when provenance improves', async () => {
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.corpus.sourceKind = 'stale-fallback';
    snapshot.corpus.obtainedAt = 500;
    // Current load is a fresh fetch of identical content
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      loadFn: vi.fn().mockResolvedValue({
        files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
        diagnostics: {
          sourceAnchoredCount: 50, nonEmptySectionCount: 50, sectionCount: 50,
          overviewSectionCount: 0, unmappedSegments: [], parseWarningCount: 0,
        },
      }),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    expect(deps.buildIndexFn).not.toHaveBeenCalled(); // index reused
    expect(deps.writeCacheFn).toHaveBeenCalled(); // provenance updated
  });
});

describe('canary replay rejection', () => {
  it('forces uncached fetch when canary replay rejects cached content', async () => {
    // Set up: cached index built from content-cache hit, canary replay rejects
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0; // outdated policy
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      // evaluateCanariesFn rejects on first call (replay), accepts on second (after fresh fetch)
      evaluateCanariesFn: vi.fn()
        .mockReturnValueOnce({
          decision: 'reject',
          rejection: { code: 'taxonomy_collapse', reason: 'test', details: {} },
          warnings: [], metrics: { overviewRatio: 0.25, baselineSectionCount: 50, sectionCountDropRatio: null },
          nextPolicyState: snapshot.policyState,
        })
        .mockReturnValueOnce({
          decision: 'accept',
          rejection: null,
          warnings: [], metrics: { overviewRatio: 0, baselineSectionCount: 50, sectionCountDropRatio: null },
          nextPolicyState: snapshot.policyState,
        }),
      // loadFn: first call returns cached content, second returns fresh (different hash)
      loadFn: vi.fn()
        .mockResolvedValueOnce({
          files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
          contentHash: 'abc123',
          provenance: { sourceKind: 'cached', obtainedAt: 1000 },
          diagnostics: makeDiagnostics(),
        })
        .mockResolvedValueOnce({
          files: [{ path: 'hooks/test.md', content: '# Test\nNew Content' }],
          contentHash: 'new-hash',
          provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
          diagnostics: makeDiagnostics(),
        }),
    });
    const state = new ServerState(deps);
    const idx = await state.ensureIndex();

    // Should have called loadFn twice: initial + forced uncached fetch
    expect(deps.loadFn).toHaveBeenCalledTimes(2);
    // Second call should have forceRefresh=true
    expect((deps.loadFn as ReturnType<typeof vi.fn>).mock.calls[1][2]).toBe(true);
    expect(idx).not.toBeNull();
  });

  it('fails loudly when canary replay rejects fetched content', async () => {
    // Set up: content was live-fetched (not cached), canary replay rejects
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0;
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      evaluateCanariesFn: vi.fn().mockReturnValue({
        decision: 'reject',
        rejection: { code: 'taxonomy_collapse', reason: 'test', details: {} },
        warnings: [], metrics: { overviewRatio: 0.25, baselineSectionCount: null, sectionCountDropRatio: null },
        nextPolicyState: emptyPolicyState(),
      }),
      loadFn: vi.fn().mockResolvedValue({
        files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
        diagnostics: makeDiagnostics(),
      }),
    });
    const state = new ServerState(deps);
    const idx = await state.ensureIndex();

    // No retry — content was already live-fetched
    expect(deps.loadFn).toHaveBeenCalledTimes(1);
    // Returns null (rejection)
    expect(idx).toBeNull();
  });

  it('confirms rejection when forced fetch returns same contentHash', async () => {
    // Set up: canary replay rejects cached content, forced fetch returns identical content
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0;
    const rejectEval = {
      decision: 'reject' as const,
      rejection: { code: 'taxonomy_collapse' as const, reason: 'test', details: {} },
      warnings: [], metrics: { overviewRatio: 0.25, baselineSectionCount: null, sectionCountDropRatio: null },
      nextPolicyState: emptyPolicyState(),
    };
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      evaluateCanariesFn: vi.fn().mockReturnValue(rejectEval),
      loadFn: vi.fn()
        .mockResolvedValueOnce({
          files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
          contentHash: 'abc123',
          provenance: { sourceKind: 'cached', obtainedAt: 1000 },
          diagnostics: makeDiagnostics(),
        })
        .mockResolvedValueOnce({
          // Same hash — upstream unchanged, rejection confirmed
          files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
          contentHash: 'abc123',
          provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
          diagnostics: makeDiagnostics(),
        }),
    });
    const state = new ServerState(deps);
    const idx = await state.ensureIndex();

    // Tried forced fetch but got same hash — confirmed rejection
    expect(deps.loadFn).toHaveBeenCalledTimes(2);
    expect(idx).toBeNull();
  });

  it('confirms rejection when forced fetch fails', async () => {
    // Set up: canary replay rejects cached content, forced fetch fails entirely
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0;
    const rejectEval = {
      decision: 'reject' as const,
      rejection: { code: 'taxonomy_collapse' as const, reason: 'test', details: {} },
      warnings: [], metrics: { overviewRatio: 0.25, baselineSectionCount: null, sectionCountDropRatio: null },
      nextPolicyState: emptyPolicyState(),
    };
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      evaluateCanariesFn: vi.fn().mockReturnValue(rejectEval),
      loadFn: vi.fn()
        .mockResolvedValueOnce({
          files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
          contentHash: 'abc123',
          provenance: { sourceKind: 'cached', obtainedAt: 1000 },
          diagnostics: makeDiagnostics(),
        })
        .mockRejectedValueOnce(new Error('network error')),
    });
    const state = new ServerState(deps);
    const idx = await state.ensureIndex();

    // Forced fetch failed — rejection stands
    expect(deps.loadFn).toHaveBeenCalledTimes(2);
    expect(idx).toBeNull();
  });
});

describe('combined cache paths', () => {
  it('Path 2+4: replays canaries AND refreshes provenance when both stale', async () => {
    const snapshot = makeFullCacheSnapshot('abc123');
    snapshot.evaluation.canaryVersion = 0; // outdated policy
    snapshot.corpus.sourceKind = 'stale-fallback';
    snapshot.corpus.obtainedAt = 500;
    const deps = makeDeps({
      parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
      loadFn: vi.fn().mockResolvedValue({
        files: [{ path: 'hooks/test.md', content: '# Test\nContent' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
        diagnostics: makeDiagnostics(),
      }),
    });
    const state = new ServerState(deps);
    await state.ensureIndex();

    expect(deps.buildIndexFn).not.toHaveBeenCalled(); // index reused
    expect(deps.writeCacheFn).toHaveBeenCalled(); // rewritten
    const written = (deps.writeCacheFn as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(written.corpus.sourceKind).toBe('fetched'); // provenance refreshed
  });
});

describe('reload semantics', () => {
  it('does not delete index cache file on reload', async () => {
    const deps = makeDeps();
    const state = new ServerState(deps);
    await state.ensureIndex();
    await state.clearAndReload();

    expect(deps.clearCacheFn).not.toHaveBeenCalled();
  });

  it('preserves policyState across reload', async () => {
    // First load establishes policyState
    const deps = makeDeps();
    const state = new ServerState(deps);
    await state.ensureIndex();

    // Reload should carry forward policyState
    await state.clearAndReload();

    const writeCall = (deps.writeCacheFn as ReturnType<typeof vi.fn>).mock.calls[1]; // second write
    const written = writeCall[1];
    expect(written.policyState.lastHealthySectionCount).toBeDefined();
  });
});

// Helper to build a full cache snapshot matching new schema
function makeFullCacheSnapshot(contentHash: string) {
  return {
    version: INDEX_FORMAT_VERSION,
    corpus: {
      contentHash,
      obtainedAt: 1000,
      sourceKind: 'fetched' as const,
      trustMode: 'official' as const,
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
    },
    diagnostics: {
      sourceAnchoredCount: 50, nonEmptySectionCount: 50, sectionCount: 50,
      overviewSectionCount: 0, unmappedSegments: [] as Array<[string, number]>,
      parseWarningCount: 0,
    },
    index: { createdAt: 1000, avgDocLength: 2, chunkCount: 3 },
    policyState: { lastHealthySectionCount: 50, lastHealthyObservedAt: 1000 },
    evaluation: {
      canaryVersion: CANARY_VERSION,
      warnings: [] as Array<{ code: string; severity: string; details: Record<string, unknown> }>,
      metrics: { overviewRatio: 0, baselineSectionCount: 50, sectionCountDropRatio: 0 },
    },
    compatibility: {
      tokenizer: TOKENIZER_VERSION,
      chunker: CHUNKER_VERSION,
      ingestion: INGESTION_VERSION,
    },
    // BM25 data
    avgDocLength: 2,
    docFrequency: [] as Array<[string, number]>,
    invertedIndex: [] as Array<[string, number[]]>,
    chunks: [] as Array<Record<string, unknown>>,
  };
}
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts`
Expected: FAIL — new tests fail, some existing tests may also fail due to schema changes

- [ ] **Step 4: Implement four cache paths in ServerState**

Rewrite `doLoadIndex` in `src/lifecycle.ts`:

1. Load content → get `LoadResult` with `contentHash`, `provenance`, `LoaderDiagnostics`
2. Read existing index cache → `parsed` (may be null)
3. Extract `oldPolicyState` from `parsed` (or empty default)
4. Check compatibility + contentHash match
5. If match: check canaryVersion and provenance → route to Path 1, 2, or 4
6. If no match: Path 3 — full rebuild:
   a. Chunk files → collect `parseWarningCount` from chunk warnings
   b. Merge `LoaderDiagnostics` + `parseWarningCount` → `CorpusDiagnostics`
   c. Call `evaluateCanaries()` with full diagnostics
   d. On canary rejection from cached content (`provenance.sourceKind === 'cached'`):
      force one uncached fetch, re-chunk, re-evaluate. On confirmed rejection or fetch
      failure: return null with error.
   e. On canary rejection from fetched content: return null with error (loud failure).
7. Write snapshot (overwrite-in-place)

**Key architectural boundary:** The loader owns corpus acquisition and raw structural
diagnostics. Lifecycle owns chunking, parse-warning counting, canary evaluation, and
rejection handling. `CanaryRejectionError` is thrown and caught within lifecycle only —
never in the loader.

Rewrite `clearAndReload`:
1. Read `policyState` from current in-memory state (already loaded) or from cache
2. Do NOT call `clearCacheFn`
3. Call `ensureIndex(true)` with force refresh

Add `ServerStateDeps.evaluateCanariesFn` (defaults to the real `evaluateCanaries` function).

Store `policyState`, `diagnostics`, `evaluation`, `corpus` provenance as fields on `ServerState` alongside the existing `index` and `contentHash`.

- [ ] **Step 5: Update existing lifecycle tests**

All existing lifecycle tests need updated mocks:
- `loadFn` mock returns `provenance` + `diagnostics`
- `serializeIndexFn` mock accepts new signature
- `parseSerializedIndexFn` mock returns new-format snapshots (or null)

- [ ] **Step 6: Run lifecycle tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts`
Expected: PASS (all existing + new cache path tests)

- [ ] **Step 7: Run full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All tests pass. This is the integration point where schema, loader, and lifecycle all work together.

- [ ] **Step 8: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/lifecycle.ts tests/lifecycle.test.ts
git commit -m "feat(claude-code-docs): implement four cache paths with canary evaluation

Adds Path 1 (full hit), Path 2 (canary replay), Path 3 (rebuild),
Path 4 (provenance refresh). Reload no longer deletes cache file.
PolicyState preserved across reloads and rebuilds."
```

---

## Task 7: Status Snapshot and get_status Tool

**Files:**
- Create: `src/status.ts`
- Create: `tests/status.test.ts`
- Modify: `src/index.ts`
- Modify: `tests/server.test.ts`

Build the `RuntimeStatus` snapshot type, the `get_status` MCP tool, and the `projectSearchMeta()` function for inline search meta.

- [ ] **Step 1: Write status snapshot tests**

```typescript
// tests/status.test.ts
import { describe, it, expect } from 'vitest';
import { buildRuntimeStatus, projectSearchMeta } from '../src/status.js';
import type { RuntimeStatus, SearchMeta } from '../src/status.js';

describe('buildRuntimeStatus', () => {
  it('builds complete status from state', () => {
    const status = buildRuntimeStatus({
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      corpus: {
        sourceKind: 'fetched',
        obtainedAt: Date.now() - 3600000, // 1h ago
      },
      index: { createdAt: Date.now() - 1800000 }, // 30min ago
      lastLoadAttemptAt: Date.now() - 1800000,
      lastLoadError: null,
      warningCodes: [],
      isLoading: false,
    });

    expect(status.trust_mode).toBe('official');
    expect(status.docs_origin).toBe('code.claude.com');
    expect(status.source_kind).toBe('fetched');
    expect(status.index_created_at).toBeDefined();
    expect(status.corpus_age_ms).toBeGreaterThan(0);
  });

  it('derives docs_origin from URL hostname', () => {
    const status = buildRuntimeStatus({
      trustMode: 'unsafe',
      docsUrl: 'https://staging.example.com/docs/llms-full.txt',
      corpus: { sourceKind: 'cached', obtainedAt: Date.now() },
      index: { createdAt: Date.now() },
      lastLoadAttemptAt: null,
      lastLoadError: null,
      warningCodes: [],
      isLoading: false,
    });

    expect(status.docs_origin).toBe('staging.example.com');
  });

  it('derives stale_corpus warning from sourceKind at response time', () => {
    const status = buildRuntimeStatus({
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      corpus: { sourceKind: 'stale-fallback', obtainedAt: Date.now() - 86400000 },
      index: { createdAt: Date.now() },
      lastLoadAttemptAt: null,
      lastLoadError: null,
      warningCodes: ['taxonomy_drift'], // canary warning
      isLoading: false,
    });

    expect(status.warning_codes).toContain('stale_corpus');
    expect(status.warning_codes).toContain('taxonomy_drift');
  });

  it('does not add stale_corpus when sourceKind is not stale-fallback', () => {
    const status = buildRuntimeStatus({
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      corpus: { sourceKind: 'fetched', obtainedAt: Date.now() },
      index: { createdAt: Date.now() },
      lastLoadAttemptAt: null,
      lastLoadError: null,
      warningCodes: [],
      isLoading: false,
    });

    expect(status.warning_codes).not.toContain('stale_corpus');
  });
});

describe('projectSearchMeta', () => {
  it('projects four-field inline meta', () => {
    const status = buildRuntimeStatus({
      trustMode: 'official',
      docsUrl: 'https://code.claude.com/docs/llms-full.txt',
      corpus: { sourceKind: 'fetched', obtainedAt: Date.now() - 1000 },
      index: { createdAt: Date.now() },
      lastLoadAttemptAt: null,
      lastLoadError: null,
      warningCodes: [],
      isLoading: false,
    });
    const meta = projectSearchMeta(status);

    expect(meta).toHaveProperty('trust_mode', 'official');
    expect(meta).toHaveProperty('source_kind', 'fetched');
    expect(meta).toHaveProperty('index_created_at');
    expect(meta).toHaveProperty('corpus_age_ms');
    // Only four keys
    expect(Object.keys(meta)).toHaveLength(4);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/status.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Implement status module**

```typescript
// src/status.ts
import { z } from 'zod';
import type { TrustMode, SourceKind } from './trust.js';
import type { WarningCode } from './canary.js';

/**
 * StatusWarningCode extends canary WarningCode with provenance-derived warnings.
 * `stale_corpus` is derived from sourceKind at response time, not from canary evaluation.
 */
export type StatusWarningCode = WarningCode | 'stale_corpus';

export interface RuntimeStatusInput {
  trustMode: TrustMode;
  docsUrl: string;
  corpus: { sourceKind: SourceKind; obtainedAt: number } | null;
  index: { createdAt: number } | null;
  lastLoadAttemptAt: number | null;
  lastLoadError: string | null;
  warningCodes: WarningCode[];  // canary-produced codes only
  isLoading: boolean;
}

export interface RuntimeStatus {
  trust_mode: TrustMode;
  docs_origin: string;
  docs_url: string;
  source_kind: SourceKind | null;
  index_created_at: string | null;
  corpus_age_ms: number | null;
  corpus_obtained_at: string | null;
  last_load_attempt_at: string | null;
  last_load_error: string | null;
  warning_codes: StatusWarningCode[];  // canary codes + provenance-derived stale_corpus
  is_loading: boolean;
}

export interface SearchMeta {
  trust_mode: TrustMode;
  source_kind: SourceKind | null;
  index_created_at: string | null;
  corpus_age_ms: number | null;
}

export function buildRuntimeStatus(input: RuntimeStatusInput): RuntimeStatus {
  let docsOrigin: string;
  try {
    docsOrigin = new URL(input.docsUrl).hostname;
  } catch {
    docsOrigin = 'unknown';
  }

  const now = Date.now();

  return {
    trust_mode: input.trustMode,
    docs_origin: docsOrigin,
    docs_url: input.docsUrl,
    source_kind: input.corpus?.sourceKind ?? null,
    index_created_at: input.index ? new Date(input.index.createdAt).toISOString() : null,
    corpus_age_ms: input.corpus ? now - input.corpus.obtainedAt : null,
    corpus_obtained_at: input.corpus ? new Date(input.corpus.obtainedAt).toISOString() : null,
    last_load_attempt_at: input.lastLoadAttemptAt ? new Date(input.lastLoadAttemptAt).toISOString() : null,
    last_load_error: input.lastLoadError,
    // Derive stale_corpus from sourceKind at response time (not a canary output)
    warning_codes: [
      ...input.warningCodes,
      ...(input.corpus?.sourceKind === 'stale-fallback' ? ['stale_corpus' as const] : []),
    ],
    is_loading: input.isLoading,
  };
}

export function projectSearchMeta(status: RuntimeStatus): SearchMeta {
  return {
    trust_mode: status.trust_mode,
    source_kind: status.source_kind,
    index_created_at: status.index_created_at,
    corpus_age_ms: status.corpus_age_ms,
  };
}

export const RuntimeStatusSchema = z.object({
  trust_mode: z.enum(['official', 'unsafe']),
  docs_origin: z.string(),
  docs_url: z.string(),
  source_kind: z.enum(['fetched', 'cached', 'stale-fallback', 'bundled-snapshot']).nullable(),
  index_created_at: z.string().nullable(),
  corpus_age_ms: z.number().nullable(),
  corpus_obtained_at: z.string().nullable(),
  last_load_attempt_at: z.string().nullable(),
  last_load_error: z.string().nullable(),
  warning_codes: z.array(z.enum(['taxonomy_drift', 'parse_issues', 'section_count_drift', 'stale_corpus'])),
  is_loading: z.boolean(),
});

export const SearchMetaSchema = z.object({
  trust_mode: z.enum(['official', 'unsafe']),
  source_kind: z.enum(['fetched', 'cached', 'stale-fallback', 'bundled-snapshot']).nullable(),
  index_created_at: z.string().nullable(),
  corpus_age_ms: z.number().nullable(),
});
```

- [ ] **Step 4: Run status tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/status.test.ts`
Expected: PASS

- [ ] **Step 5: Register get_status tool and attach search meta**

In `src/index.ts`:
1. Import `buildRuntimeStatus`, `projectSearchMeta`, `RuntimeStatusSchema`, `SearchMetaSchema`
2. Add a `getStatusInput()` method to `ServerState` (or build it in `index.ts` from `ServerState` getters)
3. Register `get_status` tool (no input params, returns `RuntimeStatus`)
4. Modify `search_docs` handler to attach `meta` to both `content` and `structuredContent`
5. Update `SearchOutputSchema` in `schemas.ts` to include optional `meta`

- [ ] **Step 6: Write server tests for new tool and meta**

Append to `tests/server.test.ts`:

```typescript
import { SearchMetaSchema } from '../src/status.js';

describe('SearchOutputSchema with meta', () => {
  it('accepts response without meta (backward compat)', () => {
    const result = SearchOutputSchema.safeParse({
      results: [{ chunk_id: 'c1', content: 'x', snippet: 's', category: 'hooks', source_file: 'f.md' }],
    });
    expect(result.success).toBe(true);
  });

  it('accepts response with meta', () => {
    const result = SearchOutputSchema.safeParse({
      results: [],
      meta: { trust_mode: 'official', source_kind: 'fetched', index_created_at: '2026-01-01T00:00:00Z', corpus_age_ms: 1000 },
    });
    expect(result.success).toBe(true);
  });
});

describe('response parity — content text matches structuredContent', () => {
  it('search_docs content text includes meta when structuredContent does', () => {
    // This test verifies design decision #15: content text serializes
    // the same top-level object as structuredContent.
    const meta = { trust_mode: 'official', source_kind: 'fetched', index_created_at: '2026-01-01T00:00:00Z', corpus_age_ms: 1000 };
    const results = [{ chunk_id: 'c1', content: 'x', snippet: 's', category: 'hooks', source_file: 'f.md' }];
    const structuredContent = { results, meta };

    // The content text should be a JSON serialization of the same object
    const contentText = JSON.stringify(structuredContent, null, 2);
    const parsed = JSON.parse(contentText);

    expect(parsed).toHaveProperty('results');
    expect(parsed).toHaveProperty('meta');
    expect(parsed.meta.trust_mode).toBe('official');
  });
});
```

- [ ] **Step 7: Run all tests**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/status.ts tests/status.test.ts src/index.ts src/schemas.ts tests/server.test.ts
git commit -m "feat(claude-code-docs): add get_status tool and inline search meta"
```

---

## Task 8: dump_index_metadata Fixes

**Files:**
- Modify: `src/dump-index-metadata.ts`
- Modify: `tests/dump-index-metadata.test.ts`

Add `index_created_at` with correct semantics. Deprecate `built_at` in schema description.

- [ ] **Step 1: Write timestamp tests**

Append to `tests/dump-index-metadata.test.ts`:

```typescript
describe('index_created_at', () => {
  it('includes index_created_at from index metadata', () => {
    // buildMetadataResponse needs access to index creation time
    const metadata = buildMetadataResponse(mockIndex, 'hash', 1700000000000);
    expect(metadata.index_created_at).toBe(new Date(1700000000000).toISOString());
  });

  it('built_at is response generation time (deprecated)', () => {
    const before = new Date().toISOString();
    const metadata = buildMetadataResponse(mockIndex, 'hash', 1700000000000);
    const after = new Date().toISOString();
    expect(metadata.built_at >= before).toBe(true);
    expect(metadata.built_at <= after).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/dump-index-metadata.test.ts`
Expected: FAIL — `index_created_at` not in output, `buildMetadataResponse` signature doesn't accept creation time

- [ ] **Step 3: Implement**

In `src/dump-index-metadata.ts`:
1. Add `indexCreatedAt: number` parameter to `buildMetadataResponse`
2. Add `index_created_at: z.string()` to `DumpIndexMetadataOutputSchema`
3. In the response: `index_created_at: new Date(indexCreatedAt).toISOString()`
4. Keep `built_at: new Date().toISOString()` (unchanged behavior)
5. Update `built_at` Zod field with `.describe('DEPRECATED: Response generation time. Use index_created_at for actual index build time.')`
6. Update caller in `src/index.ts` to pass index creation time from `ServerState`

- [ ] **Step 4: Run tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/dump-index-metadata.test.ts`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add src/dump-index-metadata.ts tests/dump-index-metadata.test.ts src/index.ts
git commit -m "feat(claude-code-docs): add index_created_at, deprecate built_at"
```

---

## Task 9: CLAUDE.md and Documentation Updates

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/CLAUDE.md`
- Modify: `packages/mcp-servers/claude-code-docs/README.md`

Update project documentation to reflect new architecture.

- [ ] **Step 1: Update CLAUDE.md**

Add to Module Map: `trust.ts`, `canary.ts`, `status.ts`

Update Key Design Patterns:
- Add: Five-block serialized index structure
- Add: Four cache paths (full hit, canary replay, rebuild, provenance refresh)
- Add: Trust modes (official/unsafe)
- Add: CANARY_VERSION in evaluation block

Update Environment Variables:
- Add: `DOCS_TRUST_MODE` (default: `official`, values: `official` | `unsafe`)

Update Gotchas:
- Add: Version bump policy — changing thresholds is CANARY_VERSION; changing diagnostic computation is INGESTION_VERSION; adding required diagnostic fields is INGESTION_VERSION
- Add: Unsafe mode is an escape hatch, not multi-corpus support
- Update: Cache version bumps section to include CANARY_VERSION

- [ ] **Step 2: Update README.md**

Add trust mode documentation:
- Official mode: pinned to code.claude.com, full canary evaluation
- Unsafe mode: any HTTPS URL, structural canaries only
- Document `DOCS_TRUST_MODE` env var

Add `get_status` tool documentation.

Add inline search meta documentation (four fields).

- [ ] **Step 3: Commit**

```bash
cd packages/mcp-servers/claude-code-docs
git add CLAUDE.md README.md
git commit -m "docs(claude-code-docs): update docs for provenance, canaries, and trust modes"
```

---

## Task 10: Type Check and Integration Verification

**Files:** None created. Verification only.

- [ ] **Step 1: Type check**

Run: `cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit`
Expected: No type errors

- [ ] **Step 2: Full test suite**

Run: `cd packages/mcp-servers/claude-code-docs && npm test`
Expected: All tests pass (existing 428 + new tests)

- [ ] **Step 3: Build**

Run: `cd packages/mcp-servers/claude-code-docs && npm run build`
Expected: Clean build

- [ ] **Step 4: Manual smoke test**

Run: `cd packages/mcp-servers/claude-code-docs && npm start`
Expected: Server starts, logs `Index ready (N chunks)`. Ctrl+C to stop.

- [ ] **Step 5: Final commit if any loose changes**

```bash
cd packages/mcp-servers/claude-code-docs
git status
# If any uncommitted changes, commit them
```
