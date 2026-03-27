# Provenance PR Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all Critical and Important findings from the PR #83 review, then realign documentation and backfill regression tests.

**Architecture:** All lifecycle control-flow and state-ownership fixes land in `lifecycle.ts`. Documentation regenerated from runtime schemas in `status.ts`. Test backfill uses existing `makeDeps`/`makeFullCacheSnapshot` helpers in `lifecycle.test.ts`.

**Tech Stack:** TypeScript, Vitest, Zod

**Schedule:** `T1 -> T2 -> (T3 || T4) -> T5`

---

### Task 1: Fix lifecycle control flow (C1, I5, I4)

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/src/lifecycle.ts:452-480`
- Test: `packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts`

**Context:** `forceFetchAndRebuild` has three issues: (1) no guard against recursion when forced fetch returns stale-fallback content, (2) termination paths ("same content", "fetch failed") don't set `this.evaluation` or `this.policyState`, and (3) cache-write failure logs understate the consequence (policyState loss on cold restart). All three share the `forceFetchAndRebuild` contract.

**Change summary:**
- Add `triggeringEvaluation: CanaryEvaluation` parameter to `forceFetchAndRebuild`
- Add `sourceKind !== 'fetched'` guard before the `buildFreshIndex` call
- Set `this.evaluation` and `this.policyState` from `triggeringEvaluation` on all three termination paths
- Update both call sites (Path 2 rejection at line 255, Path 3 rejection at line 403)
- Improve cache-write failure messages on Paths 2 and 4 to note policyState loss risk

- [ ] **Step 1: Write failing test — stale-fallback guard**

Add to the `Path 3 (rebuild) rejection` describe block in `lifecycle.test.ts`:

```typescript
it('terminates when forced fetch falls back to stale cache', async () => {
  const evalFn = vi.fn()
    .mockReturnValueOnce(makeRejectEvaluation());

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(null), // no index cache → Path 3
    evaluateCanariesFn: evalFn,
    loadFn: vi.fn()
      .mockResolvedValueOnce({
        files: [{ path: 'hooks/test.md', content: '# Test' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'cached', obtainedAt: 1000 },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      })
      .mockResolvedValueOnce({
        // Forced fetch returns stale-fallback with DIFFERENT hash
        files: [{ path: 'hooks/test.md', content: '# Test Stale' }],
        contentHash: 'different-hash',
        provenance: { sourceKind: 'stale-fallback', obtainedAt: 500 },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      }),
  });
  const state = new ServerState(deps);

  const idx = await state.ensureIndex();

  expect(idx).toBeNull();
  expect(state.getLoadError()).toContain('stale cache');
  // Should NOT have called evaluateCanariesFn a second time (no recursion)
  expect(evalFn).toHaveBeenCalledOnce();
});
```

- [ ] **Step 2: Write failing test — same-content path sets evaluation state**

Add to the `Path 3 (rebuild) rejection` describe block:

```typescript
it('sets evaluation and policyState when forced fetch returns same content', async () => {
  const rejection = makeRejectEvaluation();

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(null),
    evaluateCanariesFn: vi.fn().mockReturnValue(rejection),
    loadFn: vi.fn()
      .mockResolvedValueOnce({
        files: [{ path: 'hooks/test.md', content: '# Test' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'cached', obtainedAt: 1000 },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      })
      .mockResolvedValueOnce({
        files: [{ path: 'hooks/test.md', content: '# Test' }],
        contentHash: 'abc123', // same hash
        provenance: { sourceKind: 'fetched', obtainedAt: 2000 },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      }),
  });
  const state = new ServerState(deps);

  await state.ensureIndex();

  expect(state.getEvaluation()).not.toBeNull();
  expect(state.getEvaluation()?.decision).toBe('reject');
  expect(state.getPolicyState()).toEqual(rejection.nextPolicyState);
});
```

- [ ] **Step 3: Write failing test — fetch-failed path sets evaluation state**

Add to the `Path 3 (rebuild) rejection` describe block:

```typescript
it('sets evaluation and policyState when forced fetch fails', async () => {
  const rejection = makeRejectEvaluation();

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(null),
    evaluateCanariesFn: vi.fn().mockReturnValue(rejection),
    loadFn: vi.fn()
      .mockResolvedValueOnce({
        files: [{ path: 'hooks/test.md', content: '# Test' }],
        contentHash: 'abc123',
        provenance: { sourceKind: 'cached', obtainedAt: 1000 },
        diagnostics: { ...DEFAULT_LOADER_DIAGNOSTICS },
      })
      .mockRejectedValueOnce(new Error('network timeout')),
  });
  const state = new ServerState(deps);

  await state.ensureIndex();

  expect(state.getEvaluation()).not.toBeNull();
  expect(state.getEvaluation()?.decision).toBe('reject');
  expect(state.getPolicyState()).toEqual(rejection.nextPolicyState);
});
```

- [ ] **Step 4: Run tests to verify all three fail**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts 2>&1 | tail -30`

Expected: 3 failures (stale cache guard, same-content state, fetch-failed state).

- [ ] **Step 5: Implement the fix**

Replace `forceFetchAndRebuild` in `lifecycle.ts` (lines 452-480) with:

```typescript
  /**
   * Force an uncached fetch and do a full rebuild.
   * - If forced fetch returns non-fetched content (stale fallback): confirm rejection, terminate.
   * - If forced fetch returns same contentHash: confirm rejection, terminate.
   * - If forced fetch returns different content with sourceKind 'fetched': rebuild.
   * - If forced fetch throws: confirm rejection, terminate.
   *
   * All termination paths set this.evaluation and this.policyState from triggeringEvaluation.
   */
  private async forceFetchAndRebuild(
    originalContentHash: string,
    oldPolicyState: PolicyState,
    indexCachePath: string,
    triggeringEvaluation: CanaryEvaluation,
  ): Promise<BM25Index | null> {
    console.error('Canary rejection — forcing uncached fetch...');
    try {
      const freshResult = await this.deps.loadFn(this.docsUrl, undefined, true);

      // Guard: forced fetch fell back to stale cache — don't recurse into buildFreshIndex
      if (freshResult.provenance.sourceKind !== 'fetched') {
        console.error('ERROR: Forced fetch fell back to stale cache — canary rejection confirmed');
        this.loadError = 'Canary rejection confirmed (forced fetch fell back to stale cache)';
        this.evaluation = triggeringEvaluation;
        this.policyState = triggeringEvaluation.nextPolicyState;
        return null;
      }

      if (freshResult.contentHash === originalContentHash) {
        // Same content — confirmed rejection
        console.error('ERROR: Forced fetch returned same content — canary rejection confirmed');
        this.loadError = 'Canary rejection confirmed after forced fetch (same content)';
        this.evaluation = triggeringEvaluation;
        this.policyState = triggeringEvaluation.nextPolicyState;
        return null;
      }
      // Different content — full rebuild with new content
      return this.buildFreshIndex(
        freshResult.files,
        freshResult.contentHash,
        freshResult.provenance,
        freshResult.diagnostics,
        oldPolicyState,
        indexCachePath,
      );
    } catch (err) {
      console.error(`ERROR: Forced fetch failed: ${err instanceof Error ? err.message : 'unknown'}`);
      this.loadError = `Canary rejection confirmed (forced fetch failed: ${err instanceof Error ? err.message : 'unknown'})`;
      this.evaluation = triggeringEvaluation;
      this.policyState = triggeringEvaluation.nextPolicyState;
      return null;
    }
  }
```

Update the two call sites:

**Path 2 rejection** (line ~255 in `doLoadIndex`): Change:
```typescript
return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath);
```
to:
```typescript
return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath, evalResult);
```

**Path 3 rejection** (line ~403 in `buildFreshIndex`): Change:
```typescript
return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath);
```
to:
```typescript
return this.forceFetchAndRebuild(contentHash, oldPolicyState, indexCachePath, evalResult);
```

- [ ] **Step 6: Improve cache-write failure messages**

In the Path 2 cache-write catch block (~line 296), change:
```typescript
console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
```
to:
```typescript
console.error(`ERROR: Failed to write index cache (policyState advancement will be lost on restart): ${err instanceof Error ? err.message : 'unknown'}`);
```

Same change for the Path 4 cache-write catch block (~line 345).

Path 3 (`buildFreshIndex`) cache-write failure has different semantics — the baseline isn't being advanced from a previous value, it's being established. Keep the existing WARN level.

- [ ] **Step 7: Run tests to verify all pass**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts 2>&1 | tail -30`

Expected: All tests pass (49 existing + 3 new = 52).

- [ ] **Step 8: Type check**

Run: `cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit 2>&1`

Expected: Clean (no output).

- [ ] **Step 9: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/src/lifecycle.ts packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts
git commit -m "fix(claude-code-docs): harden forceFetchAndRebuild termination and state management

Add sourceKind guard to prevent recursion when forced fetch returns stale-
fallback content. Set evaluation and policyState on all termination paths
(same content, fetch failed, stale fallback). Promote cache-write failure
logs on Paths 2 and 4 to note policyState loss risk.

Addresses: C1 (latent recursion), I5 (stale evaluation state), I4 (log
severity for policyState loss)."
```

---

### Task 2: Fix getEvaluation getter (I3)

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/src/lifecycle.ts:132-134`
- Test: `packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts`

**Context:** `getEvaluation()` returns the raw internal reference. Other getters (`getPolicyState`, `getCorpusProvenance`, `getDiagnostics`) all return shallow copies. This one should match the pattern.

- [ ] **Step 1: Write failing test**

Add to the `getters` describe block in `lifecycle.test.ts`:

```typescript
it('getEvaluation returns a copy, not the internal reference', async () => {
  const deps = makeDeps();
  const state = new ServerState(deps);
  await state.ensureIndex();

  const eval1 = state.getEvaluation();
  const eval2 = state.getEvaluation();
  expect(eval1).not.toBeNull();
  expect(eval1).toEqual(eval2);
  expect(eval1).not.toBe(eval2); // different object references
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts -t "getEvaluation returns a copy" 2>&1 | tail -15`

Expected: FAIL — `toBe` check succeeds when it should fail (same reference).

- [ ] **Step 3: Implement the fix**

In `lifecycle.ts`, replace:
```typescript
  getEvaluation(): CanaryEvaluation | null {
    return this.evaluation;
  }
```
with:
```typescript
  getEvaluation(): CanaryEvaluation | null {
    return this.evaluation ? { ...this.evaluation } : null;
  }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/lifecycle.test.ts 2>&1 | tail -15`

Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/src/lifecycle.ts packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts
git commit -m "fix(claude-code-docs): return shallow copy from getEvaluation

Match the defensive-copy pattern used by getPolicyState, getCorpusProvenance,
and getDiagnostics. Prevents callers from mutating internal state."
```

---

### Task 3: Schema-driven documentation repair (C2, I1, I2)

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/README.md:92-125`
- Modify: `packages/mcp-servers/claude-code-docs/CLAUDE.md:71`
- Reference (read-only): `packages/mcp-servers/claude-code-docs/src/status.ts` (RuntimeStatusSchema, SearchMetaSchema)

**Context:** README documents wrong `get_status` fields (6/9 incorrect), wrong `meta.source_kind` enum values, and wrong `meta.corpus_age_ms` description. CLAUDE.md has wrong five-block descriptions. All corrections must be derived from the actual schemas and types, not from memory.

- [ ] **Step 1: Fix search_docs meta table in README.md**

Replace the `meta` rows in the `search_docs` return shape table (README.md ~lines 92-96) with values from `SearchMetaSchema` in `status.ts`:

```markdown
| `meta` | object | Index provenance attached to each search response. |
| `meta.trust_mode` | string | Active trust mode: `official` or `unsafe`. |
| `meta.source_kind` | string or null | How content was obtained: `fetched`, `cached`, `stale-fallback`, or `bundled-snapshot`. Null if no corpus loaded. |
| `meta.index_created_at` | string or null | ISO timestamp when the BM25 index was built. Null if not yet loaded. |
| `meta.corpus_age_ms` | integer or null | Milliseconds since the corpus content was obtained (`Date.now() - corpus.obtainedAt`). Null if no corpus loaded. |
```

- [ ] **Step 2: Fix get_status return shape table in README.md**

Replace the `get_status` return shape table (README.md ~lines 114-125) with values from `RuntimeStatusSchema` in `status.ts`:

```markdown
| Field | Type | Description |
| --- | --- | --- |
| `trust_mode` | string | Active trust mode: `official` or `unsafe`. |
| `docs_origin` | string | Hostname of the documentation source URL. |
| `docs_url` | string | Full documentation source URL. |
| `source_kind` | string or null | How content was obtained: `fetched`, `cached`, `stale-fallback`, or `bundled-snapshot`. Null if no corpus loaded. |
| `index_created_at` | string or null | ISO timestamp when the BM25 index was built. Null if not yet loaded. |
| `corpus_age_ms` | number or null | Milliseconds since corpus content was obtained. Null if no corpus loaded. |
| `corpus_obtained_at` | string or null | ISO timestamp when corpus content was obtained. Null if no corpus loaded. |
| `last_load_attempt_at` | string or null | ISO timestamp of the most recent load attempt. Null if never attempted. |
| `last_load_error` | string or null | Error message from the most recent failed load. Null if last load succeeded. |
| `warning_codes` | string[] | Active warning codes: `taxonomy_drift`, `parse_issues`, `section_count_drift`, `stale_corpus`. |
| `is_loading` | boolean | Whether a load/reload is currently in progress. |
```

- [ ] **Step 3: Fix five-block description in CLAUDE.md**

In CLAUDE.md line 71, replace:
```
`corpus` (chunks + term frequencies), `diagnostics` (canary evaluation inputs), `index` (inverted index + IDF weights), `policyState` (trust mode + source URL at build time), `evaluation` (canary pass/fail + CANARY_VERSION) + top-level `compatibility` block (all version constants)
```
with:
```
`corpus` (content hash + provenance), `diagnostics` (canary evaluation inputs), `index` (build timestamp + counts), `policyState` (baseline tracking), `evaluation` (canary pass/fail + CANARY_VERSION) + top-level `compatibility` block (all version constants). BM25 data (chunks, docFrequency, invertedIndex) lives at the top level outside the named blocks.
```

Also fix the `policyState` description in the four cache load paths line (~72):
```
(4) provenance refresh — provenance improved (better source kind or newer), re-persist corpus block
```

- [ ] **Step 4: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/README.md packages/mcp-servers/claude-code-docs/CLAUDE.md
git commit -m "docs(claude-code-docs): fix get_status, search meta, and five-block descriptions

Regenerate get_status return shape from RuntimeStatusSchema (6/9 fields
were wrong). Fix search meta source_kind enum and corpus_age_ms description.
Fix five-block descriptions in CLAUDE.md to match actual block contents."
```

---

### Task 4: Backfill regression tests (S1-S4)

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts`
- Modify: `packages/mcp-servers/claude-code-docs/tests/canary.test.ts`

**Context:** Review found test gaps in canary edge cases and lifecycle cache-write failure paths. These are not blocking but lock in correct behavior.

- [ ] **Step 1: Add cache-write failure test for Path 2 (canary replay)**

Add to the `cache paths` describe block in `lifecycle.test.ts`:

```typescript
it('returns index even when cache write fails on canary replay (Path 2)', async () => {
  const snapshot = makeFullCacheSnapshot({
    evaluation: {
      canaryVersion: CANARY_VERSION - 1, // triggers replay
      warnings: [],
      metrics: { overviewRatio: 0, baselineSectionCount: null, sectionCountDropRatio: null },
    },
  });

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
    deserializeIndexFn: vi.fn().mockReturnValue(makeMockIndex()),
    writeCacheFn: vi.fn().mockRejectedValue(new Error('disk full')),
  });
  const state = new ServerState(deps);

  const idx = await state.ensureIndex();

  expect(idx).not.toBeNull();
  expect(idx!.chunks).toHaveLength(3);
  // Cache write was attempted and failed
  expect(deps.writeCacheFn).toHaveBeenCalledOnce();
});
```

- [ ] **Step 2: Add cache-write failure test for Path 4 (provenance refresh)**

```typescript
it('returns index even when cache write fails on provenance refresh (Path 4)', async () => {
  const snapshot = makeFullCacheSnapshot({
    corpus: {
      contentHash: 'abc123',
      obtainedAt: 500, // older
      sourceKind: 'cached',
      trustMode: 'official',
      docsUrl: 'https://test.example.com/docs',
    },
  });

  const deps = makeDeps({
    parseSerializedIndexFn: vi.fn().mockReturnValue(snapshot),
    deserializeIndexFn: vi.fn().mockReturnValue(makeMockIndex()),
    writeCacheFn: vi.fn().mockRejectedValue(new Error('disk full')),
  });
  const state = new ServerState(deps);

  const idx = await state.ensureIndex();

  expect(idx).not.toBeNull();
  expect(idx!.chunks).toHaveLength(3);
  expect(deps.writeCacheFn).toHaveBeenCalledOnce();
});
```

- [ ] **Step 3: Add canary sectionCount=0 edge case test**

Add to the `evaluateCanaries` describe block in `canary.test.ts`:

```typescript
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
```

- [ ] **Step 4: Add canary unsafe-mode section drift passthrough test**

Add to the `unsafe mode` describe block in `canary.test.ts`:

```typescript
it('does not reject on large section count drop from baseline in unsafe mode', () => {
  const result = evaluateCanaries({
    trustMode: 'unsafe',
    diagnostics: makeDiagnostics({ sectionCount: 20 }), // 60% drop from baseline of 50
    policyState: establishedPolicyState(),
    now: 1000,
  });

  expect(result.decision).toBe('accept');
  // No section_count_drift or section_count_collapse warnings
  const codes = result.warnings.map(w => w.code);
  expect(codes).not.toContain('section_count_drift');
});
```

- [ ] **Step 5: Run all tests**

Run: `cd packages/mcp-servers/claude-code-docs && npm test 2>&1 | tail -15`

Expected: All pass (537 existing + 3 from Codex fixes + 3 from T1 + 1 from T2 + 4 from T4 = 548).

- [ ] **Step 6: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts packages/mcp-servers/claude-code-docs/tests/canary.test.ts
git commit -m "test(claude-code-docs): backfill regression tests for cache-write failure and canary edge cases

Add cache-write failure tests for Paths 2 and 4, sectionCount=0 edge case,
and unsafe-mode section drift passthrough."
```

---

### Task 5: Parked hygiene (deferred)

These items are out of scope for this PR unless touched naturally by earlier tasks:

| Item | Description | Defer reason |
|------|-------------|--------------|
| S5 | Make `CanaryEvaluation` a discriminated union | Type-only change, no runtime impact |
| S6 | Typed `CorpusWarning.details` per warning code | Breaking change to existing shape |
| S7 | Sync `StatusWarningCode` Zod enum with TS union | Low risk, no current divergence |
| S8 | Log Zod failure in `parseSerializedIndex` | Minor observability, no behavior change |
| S9 | Remove bare catch in `status.ts` URL parsing | Unreachable in production |
| S10 | Add JSDoc to `evaluateCanaries` / `doLoadIndex` | Documentation only |
| S11 | Remove hardcoded counts from CLAUDE.md comments | Stale risk, not current inaccuracy |

---

## Final Verification

After all tasks complete:

```bash
cd packages/mcp-servers/claude-code-docs
npx tsc --noEmit        # type check
npm test                 # all tests
npm run build            # build check
```

Expected: Clean on all three. Push branch and update PR #83.
