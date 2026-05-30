# claude-code-docs B-prime Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore claude-code-docs MCP server to working state by replacing the brittle `taxonomy_collapse` / `taxonomy_drift` canaries with a loader-regression delta canary, renaming the dishonest `fallbackOverviewCount` metric, changing the unmapped-URL fallback from `'overview'` to `'uncategorized'`, deduping the duplicated `MIN_SECTION_COUNT` env parse into a single config-owned source (the loader keeps a fixed cache-write guard; the canary owns the tunable index floor — B1), and fixing the `AGENTS.md` version-constant doc drift.

**Architecture:** Reframe the canary's job from "is our static category ontology still complete?" (S1, ontology coverage — what the broken `taxonomy_collapse` measured) to "did this load suddenly classify much more content as fallback than the last healthy load?" (S2, loader-regression smoke). Keep `category` as a soft enrichment field on chunks; defer full removal as a v2 cleanup pending an external-consumer audit.

**Tech Stack:** TypeScript, Node.js (≥20), Vitest, Zod, MCP stdio transport. All commands run from `packages/mcp-servers/claude-code-docs/`.

**Source of design decisions:** Codex dialogue at `/dialogue` turn 4 (2026-05-28). Convergence code: `convergence`, score: B-prime 8/7/6/8 vs C-deferred 8/8/8/8.

---

## File Structure

| File | Role in this PR |
|---|---|
| `AGENTS.md` | Fix doc drift: "Four version constants" → "Five" |
| `src/config.ts` | Add `minSectionCount?: number` to `AppConfig`; centralize env parse |
| `src/loader.ts` | Remove `getMinSectionCount()` and `ContentValidationError` section-count gate; compute `fallbackSegmentCount` instead of `fallbackOverviewCount` + `overviewSectionCount` |
| `src/canary.ts` | Drop `taxonomy_collapse` rejection + `taxonomy_drift` warning; add `fallback_segment_drift` warning + `fallback_segment_collapse` rejection; replace metric set; consume `minSectionCount` from input; thread new `PolicyState` fields |
| `src/frontmatter.ts` | Change `deriveCategory` fallback from `'overview'` to `'uncategorized'` |
| `src/categories.ts` | Add `'uncategorized'` to `KNOWN_CATEGORIES` |
| `src/index-cache.ts` | `INDEX_FORMAT_VERSION 4→5`, `CANARY_VERSION 1→2`, `INGESTION_VERSION 5→6`; `DiagnosticsBlock` loses `overviewSectionCount` + `fallbackOverviewCount`, gains `fallbackSegmentCount`; `PolicyStateBlock` gains `lastHealthyFallbackSectionCount` + `lastHealthyFallbackObservedAt`; `WarningSchema` enum + `CanaryMetricsSchema` updated |
| `src/lifecycle.ts` | Update `DiagnosticsBlock` field set in the two reconstruction sites (Path 1 hit, **Path 4 provenance refresh**); Path 2 replay passes the object through unchanged; thread new `PolicyState` fields |
| `src/status.ts` | `StatusWarningCodeSchema`: drop `'taxonomy_drift'`, add `'fallback_segment_drift'` |
| `tests/canary.test.ts` | Delete tests for `taxonomy_collapse`/`taxonomy_drift`; add tests for delta canary |
| `tests/loader.test.ts` | Rewrite the truncation test to the fixed `CACHE_WRITE_MIN_SECTIONS` floor (B1 keeps the guard); update diagnostic field assertions |
| `tests/frontmatter.test.ts` | Update fallback assertion `'overview'` → `'uncategorized'` |
| `tests/categories.test.ts` | Verify `'uncategorized'` in `KNOWN_CATEGORIES` |
| `tests/index-cache.test.ts` | Update serialization round-trip for new schema |
| `tests/lifecycle.test.ts` | Update for new `PolicyStateBlock` and `DiagnosticsBlock` shapes |
| `tests/status.test.ts` | Update for warning code change |
| `tests/config.test.ts` | Add test for `minSectionCount` returned from `loadConfig` |

**Commit cadence:** 5 commits total, one per phase. Each phase ends in a buildable state with tests green.

---

## Phase 0: Worktree Setup

### Task 0.1: Create isolated worktree

**Files:** none (workspace setup)

- [ ] **Step 1: Invoke worktree skill**

Use `superpowers:using-git-worktrees` to create a worktree for branch `feature/claude-code-docs-b-prime-recovery` based on `main`. Skill handles all the safety/sync logic. After it returns, `cd` into the worktree.

Expected state after this task: `git branch --show-current` returns `feature/claude-code-docs-b-prime-recovery`; `git status` clean; the worktree is rooted at a path like `/Users/jp/Projects/active/claude-code-tool-dev/.worktrees/feature/claude-code-docs-b-prime-recovery/` (or wherever the skill placed it).

All subsequent paths in this plan are relative to the worktree root, with `<pkg>` shorthand for `packages/mcp-servers/claude-code-docs`.

---

## Phase 1: AGENTS.md Doc Drift Fix (warmup commit)

### Task 1.1: Fix version-constant count

**Files:**
- Modify: `<pkg>/AGENTS.md:65`

- [ ] **Step 1: Read the current line**

Run: `grep -n "version constants" <pkg>/AGENTS.md`

Expected: line 65 is a bullet with markdown bold and backtick-wrapped constants (the edit must preserve both):

```markdown
- **Four version constants** gate cache validity: `INDEX_FORMAT_VERSION`, `TOKENIZER_VERSION`, `CHUNKER_VERSION`, `INGESTION_VERSION`. Bump the relevant constant when changing a subsystem.
```

- [ ] **Step 2: Update the count and add CANARY_VERSION**

Edit `<pkg>/AGENTS.md` line 65. Match VERBATIM — including the leading `- `, the `**bold**`, the backticks around each constant, and the trailing "Bump the relevant constant…" sentence. A de-formatted match string will not match the file; a de-formatted replacement would strip the bold/backticks and drop the trailing sentence (B2).

Old (verbatim):
```markdown
- **Four version constants** gate cache validity: `INDEX_FORMAT_VERSION`, `TOKENIZER_VERSION`, `CHUNKER_VERSION`, `INGESTION_VERSION`. Bump the relevant constant when changing a subsystem.
```

New:
```markdown
- **Five version constants** gate cache validity: `INDEX_FORMAT_VERSION`, `TOKENIZER_VERSION`, `CHUNKER_VERSION`, `INGESTION_VERSION`, `CANARY_VERSION`. Bump the relevant constant when changing a subsystem.
```

(The package `CLAUDE.md` already says "Five version constants" — only `AGENTS.md` is stale, so this commit brings the two docs into agreement.)

- [ ] **Step 3: Verify**

Run: `grep -n "Five version constants" <pkg>/AGENTS.md`

Expected: exactly one match on line 65, with the backtick formatting and the trailing "Bump the relevant constant…" sentence preserved.

- [ ] **Step 4: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/AGENTS.md
git commit -m "docs(claude-code-docs): fix version constant count in AGENTS.md (Four → Five)"
```

---

## Phase 2: MIN_SECTION_COUNT Centralization

The current system has three independent code paths handling the same env var:

1. `<pkg>/src/canary.ts:9-10` — hardcoded `OFFICIAL_MIN_SECTION_COUNT = 40` and `UNSAFE_MIN_SECTION_COUNT = 3` consumed inside `evaluateCanaries`.
2. `<pkg>/src/loader.ts:25-36` — `DEFAULT_MIN_SECTION_COUNT = 40` with own `process.env.MIN_SECTION_COUNT` parse, used as a pre-canary gate that throws `ContentValidationError`.
3. `<pkg>/src/config.ts:117` — `parseOptionalInt(env, 'MIN_SECTION_COUNT', { min: 0 })` for validation only (return value discarded).

After this phase: one parse in `config.ts`, threaded to the canary as input; loader's pre-canary section gate removed.

### Task 2.1: Add minSectionCount to AppConfig

**Files:**
- Modify: `<pkg>/src/config.ts:9-13` (AppConfig interface), `:105-128` (loadConfig)
- Modify: `<pkg>/tests/config.test.ts` (add test)

- [ ] **Step 1: Write failing test**

Add to `<pkg>/tests/config.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { loadConfig } from '../src/config.js';

describe('loadConfig: MIN_SECTION_COUNT', () => {
  it('returns minSectionCount when env is set', () => {
    const config = loadConfig({ MIN_SECTION_COUNT: '25' } as NodeJS.ProcessEnv);
    expect(config.minSectionCount).toBe(25);
  });

  it('returns undefined when env is unset', () => {
    const config = loadConfig({} as NodeJS.ProcessEnv);
    expect(config.minSectionCount).toBeUndefined();
  });

  it('accepts 0 (disable floor)', () => {
    const config = loadConfig({ MIN_SECTION_COUNT: '0' } as NodeJS.ProcessEnv);
    expect(config.minSectionCount).toBe(0);
  });

  it('rejects negative values', () => {
    expect(() => loadConfig({ MIN_SECTION_COUNT: '-1' } as NodeJS.ProcessEnv)).toThrow();
  });
});
```

- [ ] **Step 2: Run, verify FAIL**

Run: `cd <pkg> && npx vitest run tests/config.test.ts -t "MIN_SECTION_COUNT"`

Expected: 4 failing tests — `minSectionCount` is not a property on `AppConfig`.

- [ ] **Step 3: Update AppConfig and loadConfig**

In `<pkg>/src/config.ts`, change the `AppConfig` interface and `loadConfig` body.

Old (lines 9-13):
```typescript
export interface AppConfig {
  docsUrl: string;
  retryIntervalMs: number;
  trustMode: TrustMode;
}
```

New:
```typescript
export interface AppConfig {
  docsUrl: string;
  retryIntervalMs: number;
  trustMode: TrustMode;
  /** Override for the canary's minimum-section-count floor. Undefined → canary uses its default per trust mode. 0 → floor disabled. */
  minSectionCount?: number;
}
```

In `loadConfig` (around line 117), change the `MIN_SECTION_COUNT` parse from validation-only to value-capture, and return it. Also allow zero.

Replace `parseOptionalInt(env, 'MIN_SECTION_COUNT', { min: 0 });` with:

```typescript
  const minSectionCount = parseOptionalInt(env, 'MIN_SECTION_COUNT', { min: 0, allowZero: true });
```

Update the return:

```typescript
  return {
    docsUrl,
    retryIntervalMs,
    trustMode,
    minSectionCount,
  };
```

- [ ] **Step 4: Run, verify PASS**

Run: `cd <pkg> && npx vitest run tests/config.test.ts -t "MIN_SECTION_COUNT"`

Expected: 4 passing tests.

### Task 2.2: Thread minSectionCount into canary

**Files:**
- Modify: `<pkg>/src/canary.ts:66-72` (EvaluateCanariesInput), `:100-104` (evaluateCanaries)
- Modify: `<pkg>/tests/canary.test.ts` (add test for override)

- [ ] **Step 1: Write failing test**

Add to `<pkg>/tests/canary.test.ts` (after the existing official-mode tests):

```typescript
import { evaluateCanaries } from '../src/canary.js';

it('respects minSectionCount override from input', () => {
  const result = evaluateCanaries({
    trustMode: 'official',
    diagnostics: {
      sourceAnchoredCount: 10,
      nonEmptySectionCount: 10,
      sectionCount: 10,
      overviewSectionCount: 0,
      fallbackOverviewCount: 0,
      unmappedSegments: [],
      parseWarningCount: 0,
    },
    policyState: { lastHealthySectionCount: null, lastHealthyObservedAt: null },
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
      overviewSectionCount: 0,
      fallbackOverviewCount: 0,
      unmappedSegments: [],
      parseWarningCount: 0,
    },
    policyState: { lastHealthySectionCount: null, lastHealthyObservedAt: null },
    now: 1,
    minSectionCount: 0,
  });
  expect(result.decision).toBe('accept');
});
```

- [ ] **Step 2: Run, verify FAIL**

Run: `cd <pkg> && npx vitest run tests/canary.test.ts -t "minSectionCount"`

Expected: 2 failing tests — `minSectionCount` is not on `EvaluateCanariesInput`.

- [ ] **Step 3: Add optional override to EvaluateCanariesInput**

In `<pkg>/src/canary.ts`, modify the `EvaluateCanariesInput` interface (around line 66):

```typescript
export interface EvaluateCanariesInput {
  trustMode: TrustMode;
  diagnostics: CorpusDiagnostics;
  policyState: PolicyState;
  now: number;
  /** Override floor. Undefined → use OFFICIAL_MIN_SECTION_COUNT / UNSAFE_MIN_SECTION_COUNT per trust mode. 0 → no floor. */
  minSectionCount?: number;
}
```

In `evaluateCanaries`, change line 104 from:

```typescript
const minSectionCount = trustMode === 'official' ? OFFICIAL_MIN_SECTION_COUNT : UNSAFE_MIN_SECTION_COUNT;
```

To:

```typescript
const minSectionCount =
  input.minSectionCount !== undefined
    ? input.minSectionCount
    : trustMode === 'official' ? OFFICIAL_MIN_SECTION_COUNT : UNSAFE_MIN_SECTION_COUNT;
```

- [ ] **Step 4: Run, verify PASS**

Run: `cd <pkg> && npx vitest run tests/canary.test.ts -t "minSectionCount"`

Expected: 2 passing tests; no regressions in the other canary tests.

### Task 2.3: Replace loader's env-driven section gate with a fixed cache-write guard (B1)

**Files:**
- Modify: `<pkg>/src/loader.ts:19-46` (delete `DEFAULT_MIN_SECTION_COUNT` + `getMinSectionCount`; **keep** the `ContentValidationError` class; add a fixed `CACHE_WRITE_MIN_SECTIONS` const)
- Modify: `<pkg>/src/loader.ts:225-232` (re-gate the truncation throw on the fixed const instead of `getMinSectionCount()`)
- Modify: `<pkg>/src/loader.ts:240-249` (**no change** — `ContentValidationError` stays in the expected-error union; see Step 4)
- Modify: `<pkg>/src/lifecycle.ts` (remove any `getMinSectionCount` import; **keep** any `ContentValidationError` import — the class stays)
- Modify: `<pkg>/tests/loader.test.ts` (rewrite the truncation test to drive the fixed floor instead of an env value)

> **Resolved (B1) — keep the guard (Option G).** The original Task 2.3 removed the throw entirely
> ("the canary is the sole authority on minimum section count"). Reading `loader.ts` shows that conflates
> two protections: the throw fires *before* `writeCache` (loader.ts:226-232 → :235), so it guards the
> *content cache* (`llms-full.txt`) from being overwritten by truncated content; the canary guards only
> the *served index*. Remove the throw and a single truncated fetch poisons the content cache — on the next
> load the server rebuilds from the truncated copy, the canary rejects the index, and the server is stuck
> with no valid index until a good fetch eventually succeeds. That is the exact "stuck on bad cached
> content" failure this recovery PR exists to undo. So: delete the duplicated *env parse* (dedup goal met
> — one parse, in `config.ts`), but keep a fixed-floor cache-write guard.
>
> **Shape: fixed const, not threaded.** `loadFn` is constructor-injected (lifecycle.ts:180, 466); threading
> `minSectionCount` into it would change the injected signature and risk rippling to every test that fakes
> or asserts `loadFn`. The fixed const keeps the change inside `loader.ts`. One behavior delta to accept:
> the cache-write floor is no longer env-tunable (fixed at 40); `MIN_SECTION_COUNT` now tunes only the
> canary/index floor (Task 2.4). Edge case: an `unsafe`-mode private mirror with <40 sections can no longer
> lower this guard — acceptable for a recovery PR (note it in the PR body). If full env-tunability is
> needed later, thread `config.minSectionCount` through `loadFromOfficial` / `fetchAndParse` and pass
> `this.minSectionCount` at the two `loadFn` call sites, defaulting to 40 when undefined.

- [ ] **Step 1: Locate callers of the symbols being removed**

Run:
```bash
cd <pkg> && grep -rn "getMinSectionCount\|DEFAULT_MIN_SECTION_COUNT" src/ tests/
```

Record every match — each must be deleted or rewritten below. `ContentValidationError` is deliberately **not** in this grep: the class, its throw, and its place in the expected-error union all stay — that is the B1 guard.

- [ ] **Step 2: Delete the env parsing; add the fixed floor; keep the error class**

In `<pkg>/src/loader.ts`, delete the `DEFAULT_MIN_SECTION_COUNT` const and the `getMinSectionCount` function (the env machinery). **Keep** the `ContentValidationError` class. Add a fixed floor constant near the top of the file:

```typescript
/** Absolute floor below which fetched content is treated as truncated and must NOT overwrite the
 *  content cache (B1). Fixed, not env-tunable: MIN_SECTION_COUNT tunes only the canary/index floor
 *  (Task 2.4). The official corpus is ~141 sections, so 40 is a wide truncation margin. */
const CACHE_WRITE_MIN_SECTIONS = 40;
```

- [ ] **Step 3: Re-gate the throw in fetchAndParse**

In `<pkg>/src/loader.ts`, find this block (around line 225-232):

```typescript
    const { content } = await fetchOfficialDocs(url);
    const sections = parseSections(content);

    // Validate section count to detect truncated content
    const minSections = getMinSectionCount();
    if (minSections > 0 && sections.length < minSections) {
      throw new ContentValidationError(
        `Fetched content has only ${sections.length} sections (minimum: ${minSections}). ` +
          'Content may be truncated or incomplete.',
      );
    }
```

Replace with (keep the throw; swap the env lookup for the fixed const):

```typescript
    const { content } = await fetchOfficialDocs(url);
    const sections = parseSections(content);

    // Refuse to overwrite the content cache with truncated content (B1). Fixed floor; the canary
    // owns the tunable index floor (Task 2.4). The throw fires BEFORE writeCache, so the good cache survives.
    if (sections.length < CACHE_WRITE_MIN_SECTIONS) {
      throw new ContentValidationError(
        `Fetched content has only ${sections.length} sections (minimum: ${CACHE_WRITE_MIN_SECTIONS}). ` +
          'Content may be truncated or incomplete.',
      );
    }
```

`ContentValidationError` is still an expected error (Step 4), so a truncated fetch is caught and the load falls back to the last-good cache (loader.ts:257-277) — today's self-healing behavior, preserved.

- [ ] **Step 4: Confirm `ContentValidationError` stays in the expected-error union**

In `<pkg>/src/loader.ts`, the `catch` block (around line 241-246) lists `ContentValidationError` as an expected error, and a branch a few lines below logs it. **Leave both unchanged** — they are what routes the truncation throw to the stale-cache fallback instead of crashing the load. (The original Task 2.3 removed this; Option G keeps it.)

```typescript
    const isExpected =
      err instanceof FetchHttpError ||
      err instanceof FetchNetworkError ||
      err instanceof FetchResponseTooLargeError ||
      err instanceof FetchTimeoutError ||
      err instanceof ContentValidationError;
```

- [ ] **Step 5: Update tests/loader.test.ts**

Rewrite (don't delete) the truncation test: it previously set `MIN_SECTION_COUNT` via env and asserted the throw. The floor is now the fixed `CACHE_WRITE_MIN_SECTIONS` (40), so drive it with a fetched corpus of <40 sections and assert (a) `ContentValidationError` is thrown before any cache write, and (b) the load falls back to a prior good cache when one exists. Delete only assertions tied to the removed `getMinSectionCount` / env-tunability. The canary-level index floor is tested separately at Task 2.2 and end-to-end in Phase 5.

- [ ] **Step 6: Run type check**

Run: `cd <pkg> && npx tsc --noEmit`

Expected: 0 errors. If you missed a caller in Step 1, this surfaces it.

- [ ] **Step 7: Run loader tests**

Run: `cd <pkg> && npx vitest run tests/loader.test.ts`

Expected: all tests pass.

### Task 2.4: Wire config.minSectionCount to canary calls

**Files:**
- Modify: `<pkg>/src/lifecycle.ts` (callers of `evaluateCanariesFn` — find via grep)
- Modify: `<pkg>/src/index.ts` (where ServerState is constructed) — pass `config.minSectionCount` into deps

- [ ] **Step 1: Find evaluateCanaries call sites**

Run: `cd <pkg> && grep -n "evaluateCanariesFn\|evaluateCanaries(" src/`

Expected: matches in `lifecycle.ts` (Path 2 canary replay around line 246, plus the rebuild path).

- [ ] **Step 2: Thread minSectionCount through ServerState via its deps object**

`ServerState`'s only constructor is `constructor(deps: ServerStateDeps)` (lifecycle.ts:66) — it takes a single deps object, and `index.ts` already constructs it that way (`docsUrl`, `trustMode`, `retryIntervalMs` all arrive via deps). Use the **deps route**; do NOT add a positional constructor argument — that changes the constructor arity and ripples to every `new ServerState({...})` test (DR-3, the original "new parameter or via deps" wording left this to chance; pinned in the readiness review).

1. Add the field to the `ServerStateDeps` interface (lifecycle.ts:25-41), alongside the existing optional `docsUrl?` / `trustMode?`:

```typescript
  minSectionCount?: number;
```

2. Add a private readonly field to the class body (near lifecycle.ts:60-64, beside the other `private readonly` fields):

```typescript
  private readonly minSectionCount?: number;
```

3. Assign it in the constructor body (near lifecycle.ts:67-70, beside `this.docsUrl = deps.docsUrl ?? …`):

```typescript
    this.minSectionCount = deps.minSectionCount;
```

- [ ] **Step 3: Pass minSectionCount into every evaluateCanaries call inside lifecycle.ts**

At each `this.deps.evaluateCanariesFn({...})` call site, add `minSectionCount: this.minSectionCount` to the input object.

- [ ] **Step 4: Wire from loadConfig at server boot**

In `<pkg>/src/index.ts`, locate where `loadConfig()` is called and the `ServerState` is constructed. Pass `config.minSectionCount` into the constructor.

- [ ] **Step 5: Run type check + full test suite**

Run: `cd <pkg> && npx tsc --noEmit && npx vitest run`

Expected: type check passes; all tests pass.

- [ ] **Step 6: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/src/config.ts \
        packages/mcp-servers/claude-code-docs/src/canary.ts \
        packages/mcp-servers/claude-code-docs/src/loader.ts \
        packages/mcp-servers/claude-code-docs/src/lifecycle.ts \
        packages/mcp-servers/claude-code-docs/src/index.ts \
        packages/mcp-servers/claude-code-docs/tests/config.test.ts \
        packages/mcp-servers/claude-code-docs/tests/canary.test.ts \
        packages/mcp-servers/claude-code-docs/tests/loader.test.ts
git commit -m "refactor(claude-code-docs): centralize MIN_SECTION_COUNT env parse in config; canary owns index floor, loader keeps fixed cache-write guard"
```

---

## Phase 3: Fallback Rename + INGESTION_VERSION Bump

Change `deriveCategory`'s fallback from `'overview'` (which conflates with the legitimate explicit overview category) to `'uncategorized'`. This propagates to every chunk's persisted `category` field via `chunker.ts:75`, so it requires `INGESTION_VERSION` bump.

### Task 3.1: Add 'uncategorized' to KNOWN_CATEGORIES

**Files:**
- Modify: `<pkg>/src/categories.ts:7-37` (KNOWN_CATEGORIES Set)
- Modify: `<pkg>/tests/categories.test.ts` (add test)

- [ ] **Step 1: Write failing test**

Add to `<pkg>/tests/categories.test.ts`:

```typescript
import { KNOWN_CATEGORIES } from '../src/categories.js';

describe('KNOWN_CATEGORIES: uncategorized fallback', () => {
  it("includes 'uncategorized' for fallback classification", () => {
    expect(KNOWN_CATEGORIES.has('uncategorized')).toBe(true);
  });
});
```

Also update the EXISTING assertions in the same file so they survive Step 3 (they pass now but break the moment `'uncategorized'` is added — this is the C2/D3 gap that made Phase 3 commit a red suite):

- `tests/categories.test.ts`: bump `expect(KNOWN_CATEGORIES.size).toBe(27)` → `toBe(28)`, add `'uncategorized'` to the `expected` array, and retitle `it('contains all 27 canonical categories', …)` → 28.
- Count-reference drift (fix in this commit for one source of truth). Five lines move `26`/`27` → `28`:
  - `src/categories.ts:5` comment ("27 categories" → 28)
  - `AGENTS.md:11` Search-Tool-Parameters row ("One of 26 categories" → 28 + note `'uncategorized'`)
  - `AGENTS.md:47` `categories.ts` module-map row ("26 canonical categories" → "28 canonical categories")
  - `CLAUDE.md:11` `category` param ("One of 26 categories or 5 aliases" → 28)
  - `CLAUDE.md:47` `categories.ts` module-map row ("26 canonical categories" → "28 canonical categories")

  The golden-queries rows (`AGENTS.md:86`, `CLAUDE.md:93`) report a *coverage* count — the number of distinct `expectedTopCategory` values the queries exercise — not the canonical-category count, so it does not move with the 26→28 canonical change. **Corrected by the 2026-05-30 PR #130 review follow-up (Task A7): the live distinct-`expectedTopCategory` count is 27, not 26.** The original "26 / `changelog` has none" rationale was factually wrong — `golden-queries.test.ts` exercises both `changelog` and `agent-sdk` — so both rows now read "35 queries, 27 categories". (SF-1: the first correction pass fixed `AGENTS.md:11` but omitted `AGENTS.md:47` — both `CLAUDE.md` rows were fixed, only one of AGENTS.md's two.)

- [ ] **Step 2: Run, verify FAIL**

Run: `cd <pkg> && npx vitest run tests/categories.test.ts -t "uncategorized"`

Expected: the new `has('uncategorized')` test fails. (The existing `.size` test still passes here — it breaks only after Step 3, which is why Step 1 pre-updates it.)

- [ ] **Step 3: Add to KNOWN_CATEGORIES**

In `<pkg>/src/categories.ts`, add `'uncategorized'` to the `KNOWN_CATEGORIES` Set. Add to the "General categories" group at the end of the existing list:

```typescript
  'troubleshooting',
  'changelog',
  'uncategorized',  // fallback for URLs with no segment in SECTION_TO_CATEGORY
]);
```

- [ ] **Step 4: Run, verify PASS**

Run: `cd <pkg> && npx vitest run tests/categories.test.ts`

Expected: all tests pass — including (a) the referential-integrity test (line 100) that asserts every `SECTION_TO_CATEGORY` value is in `KNOWN_CATEGORIES` (additive, unaffected), and (b) the size/`expected`-array assertions updated in Step 1 (now 28).

Then run the doc-count completeness check:

```bash
cd <pkg> && grep -rn "26 canonical\|One of 26" AGENTS.md CLAUDE.md
```

Expected: **zero** matches. Both patterns target only the canonical-count lines (`AGENTS.md:11/:47`, `CLAUDE.md:11/:47`); the golden-queries "26 categories" coverage lines match neither pattern, so they're correctly excluded. A nonzero result means a count-reference site was missed — this is the check that would have caught SF-1.

### Task 3.2: Change deriveCategory fallback

**Files:**
- Modify: `<pkg>/src/frontmatter.ts:180-201` (deriveCategory function — note the docstring at line 181 also names the fallback)
- Modify: `<pkg>/tests/frontmatter.test.ts` (update fallback assertions AND the test titles/comments that hardcode 'overview')

- [ ] **Step 1: Update existing test expectations**

Run: `cd <pkg> && grep -n "'overview'" tests/frontmatter.test.ts`

For every test that asserts `deriveCategory` returns `'overview'` as a fallback (NOT for a URL where `overview` is the actual mapped segment), update the expected value to `'uncategorized'`.

All five matches are fallback assertions (none is a URL where `overview` is a mapped segment), so flip every `.toBe('overview')` → `.toBe('uncategorized')` at lines 144, 145, 150, 164, 165.

Then update the test TITLES and inline comments that hardcode "overview" — otherwise each test asserts `'uncategorized'` while its title still claims "returns overview", a lie the suite would carry forward (DR-1, caught in the readiness review):

- line 143: `it('returns overview for URL with no content path', …)` → `…returns uncategorized for URL with no content path…`
- line 148: `it('returns overview for unknown URL sections', …)` → `…returns uncategorized for unknown URL sections…`
- line 149: comment `// Unknown sections default to overview, not the first segment` → `…default to uncategorized…`
- line 162: `it('returns overview for unmapped URL sections', …)` → `…returns uncategorized for unmapped URL sections…`
- line 163: comment `// Unknown sections default to 'overview' not 'general'` → `…default to 'uncategorized' not 'general'`

- [ ] **Step 2: Run, verify FAIL**

Run: `cd <pkg> && npx vitest run tests/frontmatter.test.ts`

Expected: tests fail because `deriveCategory` still returns `'overview'`.

- [ ] **Step 3: Change deriveCategory**

In `<pkg>/src/frontmatter.ts`, find line 194-195:

```typescript
    // Default unmapped sections to 'overview' — ensures searchability
    return 'overview';
```

Replace with:

```typescript
    // Default unmapped URLs to 'uncategorized' — keeps the explicit 'overview' category
    // semantically distinct from "we don't recognize this slug yet"
    return 'uncategorized';
```

- [ ] **Step 3b: Update the deriveCategory docstring (it also names the fallback)**

The function docstring at `<pkg>/src/frontmatter.ts:181` still describes the old fallback, so it goes stale the moment Step 3 lands (DR-2, caught in the readiness review). Update it so the docstring and the code agree.

Old (line 181):
```typescript
 * - Falls back to 'overview' for unmapped sections
```

New:
```typescript
 * - Falls back to 'uncategorized' for unmapped sections
```

(Line 185's ` * - Falls back to 'general'` belongs to the file-path branch — leave it unchanged; that branch still returns `'general'` at line 200.)

- [ ] **Step 4: Run, verify PASS**

Run: `cd <pkg> && npx vitest run tests/frontmatter.test.ts`

Expected: all tests pass.

### Task 3.3: Bump INGESTION_VERSION

**Files:**
- Modify: `<pkg>/src/index-cache.ts:37`

- [ ] **Step 1: Bump the constant**

In `<pkg>/src/index-cache.ts`, change line 37:

```typescript
export const INGESTION_VERSION = 5;
```

To:

```typescript
export const INGESTION_VERSION = 6;
```

- [ ] **Step 2: Run full test suite**

Run: `cd <pkg> && npx vitest run`

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/src/categories.ts \
        packages/mcp-servers/claude-code-docs/src/frontmatter.ts \
        packages/mcp-servers/claude-code-docs/src/index-cache.ts \
        packages/mcp-servers/claude-code-docs/tests/categories.test.ts \
        packages/mcp-servers/claude-code-docs/tests/frontmatter.test.ts
git commit -m "feat(claude-code-docs): deriveCategory fallback 'overview' → 'uncategorized'; bump INGESTION_VERSION 5→6

Stops conflating the explicit 'overview' category with sections whose slug isn't
in SECTION_TO_CATEGORY. Every persisted chunk.category may change, so
INGESTION_VERSION bumps to force rebuild on first startup."
```

---

## Phase 4: Canary Redesign (big commit — coupled changes)

This phase is one cohesive commit because the type changes cascade across `canary.ts`, `index-cache.ts`, `loader.ts`, `lifecycle.ts`, and `status.ts` together. Breaking it apart leaves the code in a non-buildable state between commits.

> **Design risk (H1 — resolved (a), with (b) as a documented escape hatch).** The fallback
> baseline advances to the current `fallbackSectionCount` on every accepted load *until*
> `fallback_segment_drift` warns; once a WARN fires the baseline freezes at the last healthy
> value (the `lastHealthyFallbackSectionCount` ternary in Task 4.3's policy-state advancement
> block freezes only when `hasFallbackDrift` is true). So there are two regimes, not one:
>
> - **Below-WARN growth (normal operation):** every load advances the baseline, so slow drift
>   is *tracked, never accumulated* — the canary stays silent.
> - **After a WARN (frozen baseline):** subsequent growth is measured against the frozen value,
>   so deltas accumulate across loads. A `fallback_segment_collapse` FAIL is therefore reachable
>   two ways — a single load that jumps ≥20 sections **and** ≥3.0× over baseline, *or* sustained
>   post-WARN growth that accumulates to those thresholds. (FAIL is **not** limited to a single
>   large burst. An earlier draft mislabeled the *WARN* thresholds (≥5 ∧ ≥1.5×) as the FAIL
>   condition; the actual FAIL gate is ≥20 ∧ ≥3.0×.) This is the same "benign growth → rejection"
>   class as the original `taxonomy_collapse`, but moved from a static ratio to a movement-gated
>   accumulating delta that only bites *after* the canary has already warned.
>
> **Why (a) is acceptable:** in normal operation a WARN rarely fires, so the freeze-then-accumulate
> regime is rarely entered. The motivating growth is ~24 unmapped slugs over ~9 weeks (≈2–3/week)
> against a 24h content TTL. **Caveat (directional, not re-measured):** that cadence is a slug/segment
> rate, but `WARN_ABS = 5` gates on `fallbackSectionCount` (sections, not slugs) and one new slug can
> attach to several sections — so a single batchy slug *could* contribute ≥5 sections in one fetch and
> trip WARN even when the slug rate looks low. The residual risk is therefore a batch upstream release,
> which is exactly what (b) covers.
>
> **(b) is the escape hatch:** if `fallback_segment_drift` warns fire more than rarely in production — e.g.
> upstream ships docs in big batches (a relaunch dumping 30 slugs / many sections in one fetch) — flip the
> two advancement ternaries in Task 4.3's `nextPolicyState` block to advance-on-warn and bump
> `CANARY_VERSION`. A *persistent* `fallback_segment_drift` warn (warns on consecutive loads without
> resolving) is the explicit trigger to (i) investigate whether `SECTION_TO_CATEGORY` needs updating, and
> (ii) if drift keeps recurring, take v2 Option C (remove the fallback canary entirely).
>
> **(c) is rejected:** gating on a static `fallbackSectionRatio` threshold reintroduces the same
> static-ratio fragility class as the original `taxonomy_collapse` bug this PR exists to remove. The
> delta-with-baseline design is strictly better *because* it gates on movement, not absolute share.
> (`fallbackSectionRatio` is still computed and stored in `metrics` for observability — it is simply
> not gated on.)

### Task 4.1: Update canary types — drop taxonomy_*, add fallback_segment_*

**Files:**
- Modify: `<pkg>/src/canary.ts:32-44` (WarningCode + RejectionCode unions)
- Modify: `<pkg>/src/canary.ts:52-56` (CanaryMetrics)
- Modify: `<pkg>/src/canary.ts:14-30` (LoaderDiagnostics, CorpusDiagnostics)
- Modify: `<pkg>/src/canary.ts:27-30` (PolicyState)

- [ ] **Step 1: Update LoaderDiagnostics — drop overviewSectionCount + fallbackOverviewCount, add fallbackSegmentCount**

In `<pkg>/src/canary.ts`, change the `LoaderDiagnostics` interface (around line 14-21):

Old:
```typescript
export interface LoaderDiagnostics {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  overviewSectionCount: number;
  fallbackOverviewCount: number;
  unmappedSegments: Array<[segment: string, count: number]>;
}
```

New:
```typescript
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
```

`CorpusDiagnostics` extends `LoaderDiagnostics` and stays unchanged.

- [ ] **Step 2: Update PolicyState — add baseline fields**

Change the `PolicyState` interface (around line 27-30):

Old:
```typescript
export interface PolicyState {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
}
```

New:
```typescript
export interface PolicyState {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
  /** Baseline for fallback delta canary. Section count that produced 'uncategorized' on the last accepted load. */
  lastHealthyFallbackSectionCount: number | null;
  lastHealthyFallbackObservedAt: number | null;
}
```

- [ ] **Step 3: Update WarningCode and RejectionCode unions**

Change (around line 32):

```typescript
export type WarningCode = 'taxonomy_drift' | 'parse_issues' | 'section_count_drift';
```

To:

```typescript
export type WarningCode = 'fallback_segment_drift' | 'parse_issues' | 'section_count_drift';
```

Change (around line 40-44):

```typescript
export type RejectionCode =
  | 'no_source_markers'
  | 'min_section_count'
  | 'section_count_collapse'
  | 'taxonomy_collapse';
```

To:

```typescript
export type RejectionCode =
  | 'no_source_markers'
  | 'min_section_count'
  | 'section_count_collapse'
  | 'fallback_segment_collapse';
```

- [ ] **Step 4: Update CanaryMetrics**

Change (around line 52-56):

```typescript
export interface CanaryMetrics {
  overviewRatio: number;
  baselineSectionCount: number | null;
  sectionCountDropRatio: number | null;
}
```

To:

```typescript
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
```

### Task 4.2: Update threshold constants in canary.ts

**Files:**
- Modify: `<pkg>/src/canary.ts:5-10`

- [ ] **Step 1: Replace threshold constants**

Change (around line 5-10):

```typescript
export const TAXONOMY_DRIFT_WARN_THRESHOLD = { minSections: 3, minRatio: 0.05 };
export const TAXONOMY_DRIFT_FAIL_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_WARN_THRESHOLD = 0.20;
export const SECTION_COUNT_DRIFT_FAIL_THRESHOLD = 0.50;
export const OFFICIAL_MIN_SECTION_COUNT = 40;
export const UNSAFE_MIN_SECTION_COUNT = 3;
```

To:

```typescript
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
```

### Task 4.3: Rewrite evaluateCanaries

**Files:**
- Modify: `<pkg>/src/canary.ts:100-238` (evaluateCanaries function body)

- [ ] **Step 1: Replace the function**

Replace the entire body of `evaluateCanaries` (from `export function evaluateCanaries(input: EvaluateCanariesInput): CanaryEvaluation {` to its closing brace) with:

```typescript
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
      lastHealthyFallbackSectionCount: hasFallbackDrift
        ? policyState.lastHealthyFallbackSectionCount
        : fallbackSectionCount,
      lastHealthyFallbackObservedAt: hasFallbackDrift
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
```

- [ ] **Step 2: Type check**

Run: `cd <pkg> && npx tsc --noEmit`

Expected: errors in `index-cache.ts`, `loader.ts`, `lifecycle.ts`, `status.ts`, and tests. These will be resolved in the next tasks. Note them.

### Task 4.4: Update Zod schemas + version bumps in index-cache.ts

**Files:**
- Modify: `<pkg>/src/index-cache.ts:16` (INDEX_FORMAT_VERSION), `:49` (CANARY_VERSION)
- Modify: `<pkg>/src/index-cache.ts:61-69` (DiagnosticsBlock interface)
- Modify: `<pkg>/src/index-cache.ts:77-80` (PolicyStateBlock interface)
- Modify: `<pkg>/src/index-cache.ts:174-182` (DiagnosticsBlockSchema)
- Modify: `<pkg>/src/index-cache.ts:190-193` (PolicyStateBlockSchema)
- Modify: `<pkg>/src/index-cache.ts:195-199` (WarningSchema)
- Modify: `<pkg>/src/index-cache.ts:201-205` (CanaryMetricsSchema)
- Modify: `<pkg>/src/index-cache.ts:270-289` (serializeIndex body)

- [ ] **Step 1: Bump versions**

Change line 16: `export const INDEX_FORMAT_VERSION = 4;` → `export const INDEX_FORMAT_VERSION = 5;`
Change line 49: `export const CANARY_VERSION = 1;` → `export const CANARY_VERSION = 2;`

(INGESTION_VERSION was already bumped to 6 in Phase 3.)

- [ ] **Step 2: Update DiagnosticsBlock interface and schema**

Change `DiagnosticsBlock` interface (lines 61-69):

Old:
```typescript
export interface DiagnosticsBlock {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  overviewSectionCount: number;
  fallbackOverviewCount: number;
  unmappedSegments: Array<[string, number]>;
  parseWarningCount: number;
}
```

New:
```typescript
export interface DiagnosticsBlock {
  sourceAnchoredCount: number;
  nonEmptySectionCount: number;
  sectionCount: number;
  fallbackSectionCount: number;
  fallbackSegmentCount: number;
  unmappedSegments: Array<[string, number]>;
  parseWarningCount: number;
}
```

Change `DiagnosticsBlockSchema` (lines 174-182):

Old:
```typescript
const DiagnosticsBlockSchema = z.object({
  sourceAnchoredCount: z.number(),
  nonEmptySectionCount: z.number(),
  sectionCount: z.number(),
  overviewSectionCount: z.number(),
  fallbackOverviewCount: z.number(),
  unmappedSegments: z.array(z.tuple([z.string(), z.number()])),
  parseWarningCount: z.number(),
});
```

New:
```typescript
const DiagnosticsBlockSchema = z.object({
  sourceAnchoredCount: z.number(),
  nonEmptySectionCount: z.number(),
  sectionCount: z.number(),
  fallbackSectionCount: z.number(),
  fallbackSegmentCount: z.number(),
  unmappedSegments: z.array(z.tuple([z.string(), z.number()])),
  parseWarningCount: z.number(),
});
```

- [ ] **Step 3: Update PolicyStateBlock interface and schema**

Change `PolicyStateBlock` interface (lines 77-80):

Old:
```typescript
export interface PolicyStateBlock {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
}
```

New:
```typescript
export interface PolicyStateBlock {
  lastHealthySectionCount: number | null;
  lastHealthyObservedAt: number | null;
  lastHealthyFallbackSectionCount: number | null;
  lastHealthyFallbackObservedAt: number | null;
}
```

Change `PolicyStateBlockSchema` (lines 190-193):

Old:
```typescript
const PolicyStateBlockSchema = z.object({
  lastHealthySectionCount: z.number().nullable(),
  lastHealthyObservedAt: z.number().nullable(),
});
```

New:
```typescript
const PolicyStateBlockSchema = z.object({
  lastHealthySectionCount: z.number().nullable(),
  lastHealthyObservedAt: z.number().nullable(),
  lastHealthyFallbackSectionCount: z.number().nullable(),
  lastHealthyFallbackObservedAt: z.number().nullable(),
});
```

- [ ] **Step 4: Update WarningSchema enum**

Change (lines 195-199):

Old:
```typescript
const WarningSchema = z.object({
  code: z.enum(['taxonomy_drift', 'parse_issues', 'section_count_drift']),
  severity: z.enum(['info', 'warn', 'error']),
  details: z.record(z.unknown()),
});
```

New:
```typescript
const WarningSchema = z.object({
  code: z.enum(['fallback_segment_drift', 'parse_issues', 'section_count_drift']),
  severity: z.enum(['info', 'warn', 'error']),
  details: z.record(z.unknown()),
});
```

- [ ] **Step 5: Update CanaryMetricsSchema**

Change (lines 201-205):

Old:
```typescript
const CanaryMetricsSchema = z.object({
  overviewRatio: z.number(),
  baselineSectionCount: z.number().nullable(),
  sectionCountDropRatio: z.number().nullable(),
});
```

New:
```typescript
const CanaryMetricsSchema = z.object({
  fallbackSectionRatio: z.number(),
  baselineSectionCount: z.number().nullable(),
  sectionCountDropRatio: z.number().nullable(),
  fallbackSectionDelta: z.number().nullable(),
  fallbackSectionMultiplier: z.number().nullable(),
});
```

- [ ] **Step 6: Update serializeIndex diagnostics and policyState blocks**

In `serializeIndex` (around lines 270-289), update the `diagnostics` block:

Old:
```typescript
    diagnostics: {
      sourceAnchoredCount: context.diagnostics.sourceAnchoredCount,
      nonEmptySectionCount: context.diagnostics.nonEmptySectionCount,
      sectionCount: context.diagnostics.sectionCount,
      overviewSectionCount: context.diagnostics.overviewSectionCount,
      fallbackOverviewCount: context.diagnostics.fallbackOverviewCount,
      unmappedSegments: context.diagnostics.unmappedSegments,
      parseWarningCount: context.diagnostics.parseWarningCount,
    },
```

New:
```typescript
    diagnostics: {
      sourceAnchoredCount: context.diagnostics.sourceAnchoredCount,
      nonEmptySectionCount: context.diagnostics.nonEmptySectionCount,
      sectionCount: context.diagnostics.sectionCount,
      fallbackSectionCount: context.diagnostics.fallbackSectionCount,
      fallbackSegmentCount: context.diagnostics.fallbackSegmentCount,
      unmappedSegments: context.diagnostics.unmappedSegments,
      parseWarningCount: context.diagnostics.parseWarningCount,
    },
```

Update the `policyState` block:

Old:
```typescript
    policyState: {
      lastHealthySectionCount: context.policyState.lastHealthySectionCount,
      lastHealthyObservedAt: context.policyState.lastHealthyObservedAt,
    },
```

New:
```typescript
    policyState: {
      lastHealthySectionCount: context.policyState.lastHealthySectionCount,
      lastHealthyObservedAt: context.policyState.lastHealthyObservedAt,
      lastHealthyFallbackSectionCount: context.policyState.lastHealthyFallbackSectionCount,
      lastHealthyFallbackObservedAt: context.policyState.lastHealthyFallbackObservedAt,
    },
```

### Task 4.5: Update loader.ts to compute new diagnostics

**Files:**
- Modify: `<pkg>/src/loader.ts:138-185` (diagnostics computation block in `loadFromOfficial`)

- [ ] **Step 1: Compute fallbackSectionCount and fallbackSegmentCount**

Find the diagnostics computation block in `loadFromOfficial` (around lines 138-185). Locate:

```typescript
  // Count overview sections (sections where deriveCategory returns 'overview')
  const overviewSectionCount = sections.filter(s => {
    const sourceKey = s.sourceUrl || s.title || '';
    return deriveCategory(sourceKey) === 'overview';
  }).length;
```

Replace with:

```typescript
  // Count fallback sections (sections where deriveCategory returns 'uncategorized' —
  // i.e. no URL segment was mapped). This is what the fallback-delta canary watches.
  const fallbackSectionCount = sections.filter(s => {
    const sourceKey = s.sourceUrl || s.title || '';
    return deriveCategory(sourceKey) === 'uncategorized';
  }).length;
```

Then find the return diagnostics block (around lines 178-185):

Old:
```typescript
    diagnostics: {
      sourceAnchoredCount,
      nonEmptySectionCount: filtered.length,
      sectionCount: sections.length,
      overviewSectionCount,
      fallbackOverviewCount: sortedUnmapped.length,
      unmappedSegments: sortedUnmapped,
    },
```

New:
```typescript
    diagnostics: {
      sourceAnchoredCount,
      nonEmptySectionCount: filtered.length,
      sectionCount: sections.length,
      fallbackSectionCount,
      fallbackSegmentCount: sortedUnmapped.length,
      unmappedSegments: sortedUnmapped,
    },
```

### Task 4.6: Update lifecycle.ts paths 1 + 2 + rebuild

**Files:**
- Modify: `<pkg>/src/lifecycle.ts` (multiple locations)

- [ ] **Step 1: Grep for old field names**

Run:
```bash
cd <pkg> && grep -n "overviewSectionCount\|fallbackOverviewCount" src/lifecycle.ts
```

Expected: **two** matches — Path 1 / Full Hit (≈ lines 233-234) and **Path 4 / Provenance Refresh (≈ lines 322-323)**. Path 2 / Canary Replay (≈ line 245) is `const cachedDiagnostics: CorpusDiagnostics = parsed!.diagnostics;` — a whole-object passthrough that names no individual field, so it does **not** appear in this grep; it is handled separately in Step 3. So three load paths need attention but only two contain the old identifiers. The `tsc` gate in Step 5 catches any miss. Path 4 is the site the original plan and self-review omitted (D1). (SF-2: the first correction pass said this grep matches "THREE places" — it matches two.)

- [ ] **Step 2: Update Path 1 diagnostics reconstruction**

Find (around lines 229-237):

```typescript
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          overviewSectionCount: parsed!.diagnostics.overviewSectionCount,
          fallbackOverviewCount: parsed!.diagnostics.fallbackOverviewCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;
```

Replace with:

```typescript
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          fallbackSectionCount: parsed!.diagnostics.fallbackSectionCount,
          fallbackSegmentCount: parsed!.diagnostics.fallbackSegmentCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;
```

- [ ] **Step 3: Update Path 2 diagnostics passing (explicit mapping required)**

In Path 2 (around line 245):

```typescript
        const cachedDiagnostics: CorpusDiagnostics = parsed!.diagnostics;
```

**Replace this whole-object passthrough with the explicit field mapping below — do NOT leave the passthrough in place "if `tsc` is happy."** Runtime *safety* does not depend on this edit: the version gate runs before any load path (`compatMatch` requires `parsed.version === INDEX_FORMAT_VERSION`, lifecycle.ts ≈199–206), so after the `INDEX_FORMAT_VERSION 4→5` bump (Task 4.4) a pre-v5 cache carrying the old field names can never reach Path 2, and the updated Zod `DiagnosticsBlockSchema` is a second guard at the parse step. The mapping is mandatory for *readability and coupling*: an explicit field list documents the post-rename shape at the call site so a future reader does not re-open the "does this passthrough still typecheck?" question, and anyone who later hand-edits the schema sees the dependency at the use site. Replace with:

```typescript
        const cachedDiagnostics: CorpusDiagnostics = {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          fallbackSectionCount: parsed!.diagnostics.fallbackSectionCount,
          fallbackSegmentCount: parsed!.diagnostics.fallbackSegmentCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        };
```

- [ ] **Step 3b: Update Path 4 (Provenance Refresh) diagnostics reconstruction**

This block (around lines 318-326) is identical in shape to Path 1 and needs the same field swap. It was missing from the original plan (D1).

Old:
```typescript
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          overviewSectionCount: parsed!.diagnostics.overviewSectionCount,
          fallbackOverviewCount: parsed!.diagnostics.fallbackOverviewCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;
```

New:
```typescript
        this.diagnostics = parsed!.diagnostics ? {
          sourceAnchoredCount: parsed!.diagnostics.sourceAnchoredCount,
          nonEmptySectionCount: parsed!.diagnostics.nonEmptySectionCount,
          sectionCount: parsed!.diagnostics.sectionCount,
          fallbackSectionCount: parsed!.diagnostics.fallbackSectionCount,
          fallbackSegmentCount: parsed!.diagnostics.fallbackSegmentCount,
          unmappedSegments: parsed!.diagnostics.unmappedSegments,
          parseWarningCount: parsed!.diagnostics.parseWarningCount,
        } : null;
```

(Path 4 also passes `parsed!.diagnostics` and `parsed!.evaluation.metrics` into `serializeIndexFn` — those are passthroughs of the now-reconstructed shapes and need no change, since the `INDEX_FORMAT_VERSION` bump prevents any pre-v5 cache from reaching this path.)

- [ ] **Step 4: Find ServerState's default policyState initializer**

Run: `cd <pkg> && grep -n "lastHealthySectionCount" src/lifecycle.ts`

For every `PolicyState` literal that has only the two old fields, extend it with the two new ones (default both to `null`). The grep surfaces `DEFAULT_POLICY_STATE` (≈ lines 43-46) — that is the one to extend.

- [ ] **Step 5: Run type check**

Run: `cd <pkg> && npx tsc --noEmit`

Expected: 0 errors.

### Task 4.7: Update status.ts

**Files:**
- Modify: `<pkg>/src/status.ts:14` (StatusWarningCodeSchema)

- [ ] **Step 1: Read current schema**

Run: `cd <pkg> && grep -n "taxonomy_drift" src/status.ts`

Expected: one match in `StatusWarningCodeSchema`.

- [ ] **Step 2: Update the enum**

Find the `StatusWarningCodeSchema` definition:

Old:
```typescript
export const StatusWarningCodeSchema = z.enum([
  'taxonomy_drift',
  'parse_issues',
  'section_count_drift',
  'stale_corpus',
]);
```

New:
```typescript
export const StatusWarningCodeSchema = z.enum([
  'fallback_segment_drift',
  'parse_issues',
  'section_count_drift',
  'stale_corpus',
]);
```

### Task 4.8: Update canary tests

**Files:**
- Modify: `<pkg>/tests/canary.test.ts` (rewrite shared helpers + imports, delete taxonomy tests, add fallback-delta tests)

> **Phase-4 break note (D2):** the shared helpers and import block in `canary.test.ts`
> reference fields/constants removed in Phase 4. They MUST be rewritten or the file will
> not compile, independent of which individual tests are kept. Do Step 1 before Steps 2-4.

- [ ] **Step 1: Rewrite shared helpers, imports, and metric assertions**

Used by ~25 existing tests; all break under the Phase 4 type changes:

- **`makeDiagnostics` helper** (currently sets `overviewSectionCount: 0` / `fallbackOverviewCount: 0`): replace with `fallbackSectionCount: 0` and `fallbackSegmentCount: 0` (the new `CorpusDiagnostics` fields).
- **`emptyPolicyState` / `establishedPolicyState` helpers**: add `lastHealthyFallbackSectionCount` + `lastHealthyFallbackObservedAt` (default both `null`; give `establishedPolicyState` a second optional arg for a fallback baseline so the delta tests can set it).
- **Import block**: drop `TAXONOMY_DRIFT_WARN_THRESHOLD` and `TAXONOMY_DRIFT_FAIL_THRESHOLD` (deleted in Phase 4).
- **`'canary threshold constants'` describe block**: delete `it('has graduated taxonomy thresholds', …)` (references the deleted constants); keep the section-count and min-section assertions.
- **`result.metrics.overviewRatio` assertions** (≈2 sites): the metric is gone. Replace with `result.metrics.fallbackSectionRatio` where exercised, or delete.
- **Carry forward the Task 2.2 `minSectionCount` override tests**: they use the old inline diagnostic shape — rename `overviewSectionCount`/`fallbackOverviewCount` to `fallbackSectionCount`/`fallbackSegmentCount` so they compile under the new `CorpusDiagnostics`.

- [ ] **Step 2: Delete taxonomy_collapse and taxonomy_drift tests**

Search for tests referencing `taxonomy_collapse` or `taxonomy_drift` and delete them entirely (they assert dropped behavior).

Run: `cd <pkg> && grep -n "taxonomy_collapse\|taxonomy_drift" tests/canary.test.ts`

For every match, delete the enclosing `it(...)` block.

- [ ] **Step 3: Add tests for fallback_segment_collapse rejection**

These assert outcomes under the CORRECTED gates. For a **positive** baseline: WARN =
`delta ≥ 5 ∧ multiplier ≥ 1.5`; FAIL = `delta ≥ 20 ∧ multiplier ≥ 3.0` (multiplier = new/old).
For a **zero** baseline the multiplier is null, so the absolute-only branch applies (Blocker 1):
WARN = `count ≥ 5`, FAIL = `count ≥ 20`. For a **null** baseline (first run): never reject.
Reconciled truth table — the first six rows pass against the `>= 1 + REL` comparison from Task 4.3
(the C1 fix, no assertion changes); the last three exercise the zero-baseline branch added for Blocker 1:

| Test | baseline | new | delta | mult | WARN? | FAIL? | decision | drift warn |
|---|---|---|---|---|---|---|---|---|
| baseline null (first run) | null | 50 | — | — | — | — | accept | no |
| rejects (abs ∧ rel) | 10 | 60 | 50 | 6.0 | — | yes | reject | — |
| WARN met, FAIL not | 10 | 16 | 6 | 1.6 | yes | no | accept | yes |
| shrinks / same | 10 | 8 | −2 | 0.8 | no | no | accept | no |
| advances baseline (no warn) | 10 | 8 | −2 | 0.8 | no | no | accept (base→8) | no |
| today's real data | 18 | 24 | 6 | 1.33 | no (1.33 < 1.5) | no | accept | no |
| zero-baseline quiet (Blocker 1) | 0 | 3 | 3 | — (null) | no | no | accept (base→3) | no |
| zero-baseline WARN (Blocker 1) | 0 | 5 | 5 | — (null) | yes | no | accept (base frozen 0) | yes |
| zero-baseline FAIL (Blocker 1) | 0 | 20 | 20 | — (null) | — | yes | reject | — |

The "today" row is the C1 regression guard: under the old `>= REL` comparison the
multiplier gate was `1.33 ≥ 0.50` (true) → it warned → the test's `toBe(false)` failed.
Under `>= 1 + REL` the gate is `1.33 ≥ 1.5` (false) → no warn → the test passes.

Add to `<pkg>/tests/canary.test.ts`:

```typescript
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

  it('warns but does not reject when only relative threshold exceeded', () => {
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 16 }, // +6 abs (passes WARN_ABS=5), 1.6x rel (passes WARN_REL=0.5)
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
```

- [ ] **Step 4: Run canary tests**

Run: `cd <pkg> && npx vitest run tests/canary.test.ts`

Expected: all tests pass (including the "today's real data" regression guard — see table above).

### Task 4.9: Update remaining tests

**Files:**
- Modify: `<pkg>/tests/index-cache.test.ts`
- Modify: `<pkg>/tests/lifecycle.test.ts`
- Modify: `<pkg>/tests/status.test.ts`

- [ ] **Step 1: index-cache.test.ts**

Run: `cd <pkg> && grep -n "overviewSectionCount\|fallbackOverviewCount\|taxonomy_drift\|overviewRatio" tests/index-cache.test.ts`

Replace each:
- `overviewSectionCount: <N>` → `fallbackSectionCount: <N>`
- `fallbackOverviewCount: <N>` → `fallbackSegmentCount: <N>`
- `'taxonomy_drift'` (in warning codes) → `'fallback_segment_drift'`
- `overviewRatio: <N>` → `fallbackSectionRatio: <N>`

Add the two new policy-state fields to any `PolicyStateBlock` literal: `lastHealthyFallbackSectionCount: null, lastHealthyFallbackObservedAt: null` (or non-null values where the test exercises them).

Add the two new metric fields to any `CanaryMetricsSchema` test object: `fallbackSectionDelta: null, fallbackSectionMultiplier: null`.

- [ ] **Step 2: lifecycle.test.ts**

Same systematic find-and-replace. Run: `cd <pkg> && grep -n "overviewSectionCount\|fallbackOverviewCount\|taxonomy" tests/lifecycle.test.ts` and update each occurrence.

- [ ] **Step 3: status.test.ts**

Run: `cd <pkg> && grep -n "taxonomy_drift" tests/status.test.ts`

Replace `'taxonomy_drift'` → `'fallback_segment_drift'`.

- [ ] **Step 4: Run full test suite**

Run: `cd <pkg> && npx vitest run`

Expected: all tests pass. If any fail, fix the references they expose.

### Task 4.10: Commit

- [ ] **Step 1: Stage everything in this phase**

```bash
git add packages/mcp-servers/claude-code-docs/src/canary.ts \
        packages/mcp-servers/claude-code-docs/src/index-cache.ts \
        packages/mcp-servers/claude-code-docs/src/loader.ts \
        packages/mcp-servers/claude-code-docs/src/lifecycle.ts \
        packages/mcp-servers/claude-code-docs/src/status.ts \
        packages/mcp-servers/claude-code-docs/tests/canary.test.ts \
        packages/mcp-servers/claude-code-docs/tests/index-cache.test.ts \
        packages/mcp-servers/claude-code-docs/tests/lifecycle.test.ts \
        packages/mcp-servers/claude-code-docs/tests/status.test.ts
```

- [ ] **Step 2: Verify type check is clean**

Run: `cd <pkg> && npx tsc --noEmit`

Expected: 0 errors.

- [ ] **Step 3: Verify full test suite green**

Run: `cd <pkg> && npx vitest run`

Expected: 0 failures.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(claude-code-docs): replace taxonomy canaries with fallback-segment delta canary

Drops taxonomy_collapse rejection and taxonomy_drift warning (both keyed on
SECTION_TO_CATEGORY ontology coverage — fires on benign upstream growth).
Adds fallback_segment_collapse rejection and fallback_segment_drift warning,
both gated on absolute AND relative increase from a baseline persisted in
PolicyStateBlock. Missing baseline = warn-only, never reject.

Renames fallbackOverviewCount → fallbackSegmentCount (it counts distinct
unmapped segments, not sections). Adds fallbackSectionCount (the section-
level metric the new delta canary actually watches).

Schema changes:
- DiagnosticsBlock loses overviewSectionCount + fallbackOverviewCount,
  gains fallbackSectionCount + fallbackSegmentCount
- PolicyStateBlock gains lastHealthyFallbackSectionCount +
  lastHealthyFallbackObservedAt
- CanaryMetrics loses overviewRatio, gains fallbackSectionRatio +
  fallbackSectionDelta + fallbackSectionMultiplier
- WarningCode union: taxonomy_drift → fallback_segment_drift
- RejectionCode union: taxonomy_collapse → fallback_segment_collapse
- StatusWarningCodeSchema mirrors WarningCode

Version bumps:
- INDEX_FORMAT_VERSION 4 → 5 (persisted-shape change)
- CANARY_VERSION 1 → 2 (acceptance criteria change)

(INGESTION_VERSION bumped 5 → 6 in prior commit when fallback was renamed
'overview' → 'uncategorized'.)"
```

---

## Phase 5: End-to-End Verification

This phase has no commits unless issues are found. Its purpose is to confirm the live server now accepts the current upstream corpus.

### Task 5.1: Build and start server in isolation

**Files:** none (verification only)

- [ ] **Step 1: Clean dist and rebuild**

Run: `cd <pkg> && trash dist && npx tsc`

(Use `trash`, not `rm -rf` — repo hard rule. This still gives a clean rebuild: `.tsbuildinfo` lives in `dist/`, so trashing the dir clears the incremental cache too.)

Expected: 0 errors.

- [ ] **Step 2: Snapshot current cache state (for rollback if needed)**

Run:
```bash
ls -la ~/Library/Caches/claude-code-docs/ > /tmp/ccd-cache-before.txt
cat ~/Library/Caches/claude-code-docs/llms-full.txt | head -3
```

- [ ] **Step 3: Delete index cache to force rebuild**

Run: `trash ~/Library/Caches/claude-code-docs/llms-full.index.json`

(The content cache `llms-full.txt` stays — it's the latest upstream fetch.)

- [ ] **Step 4: Run server in standalone mode against cached content**

Run:
```bash
cd <pkg> && node dist/index.js < /dev/null > /tmp/ccd-server.log 2>&1 &
SERVER_PID=$!
sleep 5
ls -la ~/Library/Caches/claude-code-docs/llms-full.index.json
cat /tmp/ccd-server.log | grep -E "Loaded|Cache|index|canary|Error" | head -30
kill $SERVER_PID
```

Expected:
- `llms-full.index.json` exists (was just written)
- Log shows a successful load message — something like `Loaded cached index (NNN chunks)` or `Cache updated (rebuild)` — NOT `Canary rejection`

If the server reports `Canary rejection`, capture the full log and stop. Diagnose before proceeding (likely a residual reference to the old canary or a test that was missed).

### Task 5.2: MCP-level verification via fresh Claude Code session

**Files:** none (verification only)

- [ ] **Step 1: Restart the Claude Code MCP wrapper**

In a fresh Claude Code session (or after explicitly killing the current MCP child), call the live MCP tool:

```
mcp__claude-code-docs__get_status
```

Expected JSON: `source_kind` is `"cached"` or `"fetched"` (NOT `null`), `index_created_at` is a recent timestamp, `last_load_error` is `null`, `warning_codes` is `[]` (or contains only `fallback_segment_drift` if today's corpus is the first run and the prior baseline was zero — that's acceptable on first run).

- [ ] **Step 2: Issue a search**

Call:

```
mcp__claude-code-docs__search_docs { "query": "hooks SessionStart", "limit": 3 }
```

Expected: 3 results, all referencing hooks documentation. Inspect `meta` fields: `trust_mode: "official"`, `source_kind: "cached"` or `"fetched"`, `corpus_age_ms` is reasonable.

- [ ] **Step 3: Verify a new-slug query works**

Call:

```
mcp__claude-code-docs__search_docs { "query": "managed mcp servers admin", "limit": 3 }
```

Expected: results from the `managed-mcp` and/or `admin-setup` pages. These slugs were previously unmapped (causing the canary failure); they're now indexed under `category: 'uncategorized'` and BM25 still finds them.

If results are empty or wrong, the canary may have rejected the rebuild after all. Capture the full log and diagnose.

---

## Phase 6: Create PR

### Task 6.1: Push branch and open PR

**Files:** none (process)

- [ ] **Step 1: Push the branch**

```bash
git push -u origin feature/claude-code-docs-b-prime-recovery
```

- [ ] **Step 2: Open PR using gh**

```bash
gh pr create --title "fix(claude-code-docs): replace brittle taxonomy canary with fallback-segment delta canary" --body "$(cat <<'EOF'
## Summary

- Drops `taxonomy_collapse` rejection + `taxonomy_drift` warning (the canary that was rejecting today's upstream because `overviewSectionCount/sectionCount = 29/141 = 20.6%` just over the 20% threshold)
- Adds `fallback_segment_collapse` rejection + `fallback_segment_drift` warning, both gated on absolute AND relative increase from a baseline persisted in `PolicyStateBlock`
- Changes `deriveCategory` fallback from `'overview'` to `'uncategorized'` so unmapped slugs don't dilute a legitimate explicit category
- Centralizes the duplicate `MIN_SECTION_COUNT` env parse in `config.ts`; the canary owns the tunable **index** floor, while the loader keeps a fixed `CACHE_WRITE_MIN_SECTIONS` guard over the **content cache** (B1)
- Keeps `ContentValidationError` and the loader's throw-before-`writeCache` — it guards the content cache against truncated fetches and routes to stale-cache fallback, a protection distinct from the canary (which only guards the served index)
- Fixes `AGENTS.md` doc drift ("Four version constants" → "Five")
- Version bumps: `INDEX_FORMAT_VERSION 4→5`, `CANARY_VERSION 1→2`, `INGESTION_VERSION 5→6`. All three invalidate cached indexes on first startup — full rebuild is the correct behavior for a corpus-shape change.

## Why this shape

The Codex dialogue at `/dialogue` (2026-05-28) converged on this exact shape after weighing it against three alternatives (patch the map, drop categorization entirely, derive categories from upstream). Decision recorded in the linked plan.

The redesigned canary reframes its job from "is our static category ontology still complete?" (which was failing on benign upstream growth) to "did this load suddenly classify much more content as fallback than the last healthy load?" (which catches loader/normalization regressions — the original S2 signal taxonomy_collapse was actually serving).

## Out of scope

- Full removal of `SECTION_TO_CATEGORY` + `category` filter (Option C in the dialogue) — deferred to a follow-up PR pending audit of `dump-index-metadata.ts` and external consumers
- Redesign of the 5 version constants / 4 cache load paths / 5-block schema — captured as separate design ticket
- Updating `SECTION_TO_CATEGORY` with the 24 new slugs from upstream — this PR makes those slugs work as `'uncategorized'` so they're searchable; if more precise filtering is wanted, that's a separate ergonomics PR

## Test plan

- [x] `npx vitest run` — full suite green
- [x] `npx tsc --noEmit` — type check clean
- [x] Server boot smoke: deleted `~/Library/Caches/claude-code-docs/llms-full.index.json`, restarted server, confirmed rebuild succeeded
- [x] `mcp__claude-code-docs__get_status` returns non-null `source_kind` + `index_created_at`
- [x] `mcp__claude-code-docs__search_docs` returns sensible results for both old slugs (`hooks`) and new slugs (`managed-mcp`, `admin-setup`)
- [x] Specific canary regression test (`canary.test.ts`) covering today's real corpus shape (141 sections, 24 fallback) passes

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Return PR URL to operator for review and merge**

The PR is now open. Operator reviews and merges via standard process.

---

## Phase 7: Worktree Cleanup (after PR merge)

### Task 7.1: Clean up worktree

**Files:** none (workspace teardown)

- [ ] **Step 1: After PR is merged, invoke the exit skill**

Use `superpowers:finishing-a-development-branch` or `exiting-worktrees` to clean up the worktree per the repo conventions. The skill verifies the merge landed on `main`, syncs local `main`, confirms with the operator, and calls `ExitWorktree`.

---

# V2 Plan: Option C — Full Category Removal (Deferred)

This section describes the follow-up PR that would take the dialogue's deferred Option C. **It is not part of the recovery PR above.** Run only after the recovery PR is merged AND the audit gates below pass.

## When to take this PR

Only when ALL of these conditions hold:

1. The B-prime PR has been merged and running in production for at least 7 days with no `fallback_segment_*` warnings or rejections.
2. The audit below confirms zero external consumers of the `category` field outside the package's own tests.
3. Operator explicitly approves the schema reduction (it's another `INDEX_FORMAT_VERSION` bump + full rebuild).

## V2-Phase A: External-Consumer Audit

This phase is read-only — no code changes. It produces a go/no-go decision.

### Task V2-A.1: Audit MCP-tool surface

**Files:** none (read-only audit)

- [ ] **Step 1: Grep dump-index-metadata.ts for category references**

Run: `cd <pkg> && grep -n "category" src/dump-index-metadata.ts`

Document every emission. If `category` is exposed in the tool's response payload, downstream MCP clients (Claude Code itself, possibly third-party tools) may parse it. Note severity.

- [ ] **Step 2: Inspect search_docs response shape**

Run: `cd <pkg> && grep -n "category" src/bm25.ts src/schemas.ts src/index.ts`

Document whether `category` appears in `SearchResult` and whether the `search_docs` MCP tool surfaces it. If yes, that's a public API.

- [ ] **Step 3: Audit get_status payload**

Run: `cd <pkg> && grep -n "category" src/status.ts`

Document whether `category` info appears in the status payload.

- [ ] **Step 4: Search Claude Code session transcripts for category usage**

Search recent operator sessions (if logs are available) for queries like `search_docs.*category` to see whether the filter is actually used in practice.

### Task V2-A.2: Decide go/no-go

**Files:** none (decision)

- [ ] **Step 1: Categorize findings**

For each finding from Task V2-A.1, classify as:
- **Contained:** Internal to the package; can be removed cleanly.
- **Visible internal:** Exposed in MCP responses but no known external dependency; would need a deprecation notice.
- **External dependency:** Known downstream consumer; removal would break a contract.

- [ ] **Step 2: Decision criteria**

Proceed with C if:
- All findings are **Contained** or **Visible internal**.
- The `category` filter parameter on `search_docs` is reachable but has no production callers (verified above).

Defer if:
- Any **External dependency** exists.

If deferring, the right next step is not "redo audit later" but "design a backward-compatible deprecation path" — a separate planning round.

## V2-Phase B: Implementation (only if go decision)

The following is the rough shape, not a full task breakdown. The user requested high-level details for V2; expand into bite-sized tasks at the time of implementation.

### V2-B.1: Remove category from the public surface

- Delete `category` param from the `search_docs` MCP tool input schema (`src/schemas.ts`)
- Remove `category` field from `SearchResult` (`src/types.ts`, `src/bm25.ts:164-166`)
- Remove `category` field from `dump_index_metadata` output (`src/dump-index-metadata.ts`)

### V2-B.2: Remove category from internal pipeline

- Delete `SECTION_TO_CATEGORY`, `KNOWN_CATEGORIES`, `CATEGORY_ALIASES` from `src/categories.ts` (delete the file if it has no other exports)
- Delete `deriveCategory` and `getUnmappedSegments` from `src/frontmatter.ts`
- Remove the synthetic-frontmatter `category` field from `src/loader.ts:103-116` (the `buildSyntheticFrontmatter` helper)
- Remove `category` field from `Chunk` type (`src/types.ts`)
- Remove `category` field from `SerializedChunk` and its Zod schema (`src/index-cache.ts:101-108, 152-164`)
- Remove `fallbackSectionCount`, `fallbackSegmentCount`, `unmappedSegments` from `DiagnosticsBlock` (no consumer remains)
- Remove `lastHealthyFallbackSectionCount`, `lastHealthyFallbackObservedAt` from `PolicyStateBlock`
- Remove `fallback_segment_drift` from `WarningCode` and `fallback_segment_collapse` from `RejectionCode` — the delta canary itself goes away
- The remaining canaries become purely structural: `no_source_markers`, `min_section_count`, `section_count_collapse`, plus `section_count_drift` warn and `parse_issues` warn

### V2-B.3: Compensating signal (decide before removal)

After C, the only remaining health signals are corpus structure (Source: markers exist, section count is sane). The S2 signal — "did the loader suddenly start mis-classifying?" — disappears with the category field.

Decide before merging:
- **Option C-bare:** Accept the loss of S2. Argument: BM25 still ranks correctly even on misclassified content; loader regressions surface through search quality, not through canary rejection.
- **Option C+golden:** Replace S2 with a periodic golden-query smoke test that asserts known queries return known results. Catches loader regressions via behavior change rather than structural drift. Runs as scheduled CI job.

Make this decision explicitly. Do not silently accept C-bare without surfacing the trade-off.

### V2-B.4: Versioning

- `INDEX_FORMAT_VERSION 5 → 6` (chunk schema change, DiagnosticsBlock + PolicyStateBlock changes)
- `INGESTION_VERSION 6 → 7` (every chunk's persisted shape changes)
- `CANARY_VERSION 2 → 3` (canary set shrinks)

### V2-B.5: Documentation update

- Update `CLAUDE.md` and `AGENTS.md` to reflect the removed surface
- Note in the release commit message that the `category` filter is no longer supported and any client passing one will receive an `invalid input` error

---

# Self-Review

This section is my (the plan author's) own check against the spec. It is not part of the executor's work.

**1. Spec coverage check.** Every item from the Codex dialogue's recommendation has a task:

| Dialogue item | Plan location |
|---|---|
| Drop `taxonomy_collapse` rejection | Task 4.1 (RejectionCode union) + Task 4.3 (evaluateCanaries body) |
| Drop `taxonomy_drift` warning | Task 4.1 (WarningCode union) + Task 4.3 (evaluateCanaries body) + Task 4.7 (StatusWarningCodeSchema) |
| Add loader-regression delta canary in PolicyStateBlock | Task 4.1 (PolicyState fields) + Task 4.4 (PolicyStateBlock schema) + Task 4.3 (delta logic) |
| Rename `fallbackOverviewCount` → `fallbackSegmentCount` (honest naming) | Task 4.1 (LoaderDiagnostics) + Task 4.4 (DiagnosticsBlock schema) + Task 4.5 (loader.ts emission) |
| Add `fallbackSectionCount` (the section-level metric the delta watches) | Task 4.1 + Task 4.4 + Task 4.5 |
| Change `deriveCategory` fallback `'overview'` → `'uncategorized'` | Task 3.1 + Task 3.2 |
| Update `RejectionCode`, `WarningCode`, `WarningSchema`, `StatusWarningCodeSchema` | Task 4.1 + Task 4.4 + Task 4.7 |
| Bump `INDEX_FORMAT_VERSION`, `CANARY_VERSION`, `INGESTION_VERSION` | Task 3.3 (INGESTION) + Task 4.4 (INDEX_FORMAT + CANARY) |
| Centralize `MIN_SECTION_COUNT` env parse; loader keeps a fixed cache-write guard (B1) | Phase 2 (entire phase) |
| Fix `AGENTS.md` "Four" → "Five" doc drift | Task 1.1 |
| Defer Option C with audit gates | V2 plan section |

**2. Placeholder scan.** No TBDs, no "implement later", no "similar to Task N" without inline content. Every code-change step has the actual code block.

**3. Type consistency.** Names used in later tasks match earlier definitions:

- `fallbackSectionCount` (PolicyState field uses `lastHealthyFallbackSectionCount` — consistent)
- `fallbackSegmentCount` (count of distinct segments — used in `DiagnosticsBlock`, `LoaderDiagnostics`, loader emission — consistent)
- `fallback_segment_drift` / `fallback_segment_collapse` (WarningCode / RejectionCode strings — consistent across schema, canary, status, tests)
- `minSectionCount` (config field, input to canary — consistent through threading)

One thing to watch: in Task 4.3 the canary code computes `fallbackSectionRatio` but I don't use this for any threshold — it's just observability. If you later want to gate on it, document the threshold here. (Left as observability-only by design; the delta canary is the gating logic.)

**4. Verification gap.** Phase 5 confirms the server accepts today's corpus. It does NOT include a regression-style test that the delta canary REJECTS a synthetic loader-regression. The test at Task 4.8 Step 3 ("rejects when fallback jumps absolutely AND relatively") covers this in unit form. Acceptable.

**5. Post-scrutiny corrections (2026-05-28).** A `$scrutinize` pass found defects now fixed in-place above:

- **C1 (Critical):** the relative gate compared the new/old multiplier directly against the relative-increase fraction (`>= REL`), making the gate inert and failing the "today's real data" test. Fixed to `>= 1 + REL` in Task 4.3; constants documented as relative-increase fractions in Task 4.2; reconciled truth table added to Task 4.8 Step 3. No test assertion changed — only the code.
- **C2/D3:** Task 3.1 now updates the existing `KNOWN_CATEGORIES.size` (27 → 28), the `expected` array, the test title, and the 26-vs-27 count drift across `categories.ts` / `AGENTS.md` / `CLAUDE.md`. Phase 3 now ends green.
- **D1:** Task 4.6 adds Step 3b for the Path 4 / Provenance Refresh reconstruction (lines 318-326). Three load paths touch diagnostics (Path 1 + Path 4 reconstruct field-by-field; Path 2 passes the object through), but only Path 1 and Path 4 name the old fields — the original plan and self-review omitted Path 4.
- **D2:** Task 4.8 Step 1 now rewrites the `canary.test.ts` shared helpers, import block, threshold-constant test, and `overviewRatio` assertions, and carries the Task 2.2 override tests forward — none of which compiled under the Phase 4 type changes.
- **B1 (resolved):** Task 2.3 now *keeps* a fixed-floor cache-write guard (Option G) rather than removing the gate — reading `loader.ts:226-232 → :235` confirmed the throw fires before `writeCache`, so removal would poison the content cache. Only the duplicated env parse is deleted; `ContentValidationError` and the throw stay (re-gated on a fixed `CACHE_WRITE_MIN_SECTIONS = 40`). The cache-write floor is no longer env-tunable — a documented, accepted delta.
- **B2:** Task 1.1 now quotes `AGENTS.md:65` verbatim (bold + backticks + trailing sentence).
- **H1 (resolved — (a)):** the Phase 4 intro resolves to (a) accept freeze-on-warn (cadence math: ~0–1 new unmapped slugs per 24h fetch vs `WARN_ABS = 5`), with (b) advance-on-warn as the documented escape hatch and a persistent warn as the v2 Option C trigger; (c) static-ratio gating is rejected as the original bug's fragility class.

**6. Post-review-of-corrections (2026-05-28).** An implementation review of the correction commit (`9396e2d7`) found two residual gaps in the correction pass itself — both verified against source and fixed in-place:

- **SF-1:** the D3 count-reference fix listed `AGENTS.md:11` but omitted `AGENTS.md:47` (the `categories.ts` module-map row, also "26 canonical categories"). Task 3.1 now enumerates all five `26`/`27 → 28` sites and adds a closing `grep -rn "26 canonical\|One of 26"` completeness check (expects zero; the golden-queries "26 categories" coverage lines correctly don't match).
- **SF-2:** Task 4.6 Step 1 claimed the field-name grep matches "THREE places" incl. Path 2 (line 245); it matches two (Path 1, Path 4) — Path 2 is a whole-object passthrough that names no field. Reworded to "two matches; three sites need attention; Path 2 handled in Step 3."
- **N-1 (noted, not changed):** `allowZero: true` at Task 2.1 is redundant with `{ min: 0 }` *today* (config.ts:40-44 — `0 < 0` is false, so 0 passes anyway), but it robustly encodes "0 = disable" against a future `min` increase, so it stays (Future-Proof over Minimal).
- **One finding beyond the review:** the File-Structure table (line 25) named the PolicyState field `lastHealthyFallbackSegmentCount`, while the code and all 18 other plan sites use `lastHealthyFallbackSectionCount`. Corrected to `Section`.

**7. Post-adversarial-Codex-dialogue (2026-05-28).** An adversarial `/dialogue` review (posture `adversarial`, 6 turns, Codex-ratified, zero residual uncertainties) found two execution blockers and three non-blocking corrections that the prior self-review and implementation review both missed. All five verified against source and fixed in-place:

- **Blocker — zero-baseline canary bypass:** when `lastHealthyFallbackSectionCount === 0`, `fallbackSectionMultiplier` is null (its guard requires baseline `> 0`), so BOTH the FAIL and WARN gates — each carrying a `fallbackSectionMultiplier !== null` conjunct — skipped, and policy advancement then wrote the bad count as the new healthy baseline. A `SECTION_TO_CATEGORY` wipe (0→many uncategorized) would be silently laundered into trusted state, untested. Task 4.3 now has a strict `baselineFallback === 0` absolute-only branch (FAIL at `count ≥ FAIL_ABS`, WARN at `count ≥ WARN_ABS`) placed before the positive-baseline gates, preserving `=== null` first-run acceptance (not a falsy check — `0` and `null` must stay distinct). Task 4.8 adds 0→3 / 0→5 / 0→20 tests and three truth-table rows. (The Infinity-multiplier shortcut was explicitly rejected: `fallbackSectionMultiplier` is `z.number().nullable()`, so a persisted `Infinity` round-trips to `null` and re-creates the bypass on cache reload.)
- **Blocker — Phase 5 `rm -rf dist`:** violated the repo's hard `rm`/`rm -rf` prohibition (and clears `.tsbuildinfo`, so not a no-op). Task 5.1 Step 1 now uses `trash dist`.
- **H1 prose:** the freeze-on-warn paragraph contradicted itself ("never advances" vs "advances on nearly every load"), claimed FAIL needs a "single-cycle burst" despite admitting accumulation-to-FAIL, and mislabeled the WARN thresholds (≥5 ∧ ≥1.5×) as the FAIL condition (actual FAIL is ≥20 ∧ ≥3.0×). Rewritten to two explicit regimes, threshold labels corrected, stale line refs replaced with symbolic anchors, the slug-vs-section cadence caveat stated, and persistent drift made an investigation trigger.
- **PR body:** still said "canary is now the sole authority" and "Removes … the now-orphan `ContentValidationError` class" — contradicting the B1 resolution (Task 2.3 keeps both). Rewritten to match.
- **Path 2 (non-blocking, clarity):** Task 4.6 Step 3 made the explicit field mapping mandatory rather than "if `tsc` complains." Runtime safety is already guaranteed by the version gate preceding all load paths (a v4 cache can't reach Path 2 after the 4→5 bump); the mapping is required for readability.

**8. Post-readiness-review (2026-05-29).** A readiness review verified every quoted "Old" block against live source (all matched verbatim; the feared `parseOptionalInt` `allowZero` excess-property blocker does not exist — the options type already declares `allowZero?: boolean`). It surfaced three non-blocking scope gaps, all patched in-place above:

- **DR-1:** Task 3.2 Step 1 said "update fallback assertions only," leaving three `frontmatter.test.ts` test titles (lines 143, 148, 162) and two comments (149, 163) asserting `'uncategorized'` under an "returns overview" title. Step 1 now enumerates the five `.toBe` flips AND the title/comment fixes.
- **DR-2:** Task 3.2 changed the inline comment + `return` at frontmatter.ts:194-195 but not the function docstring at line 181 (`Falls back to 'overview' for unmapped sections`), which would go stale. Added Step 3b with the verbatim docstring swap. (Line 185's `'general'` fallback is the file-path branch — correctly left unchanged.)
- **DR-3:** Task 2.4 Step 2 offered "a new parameter or via deps," but `ServerState`'s sole constructor is `constructor(deps: ServerStateDeps)` — a positional arg would change arity and break every `new ServerState({...})` call site. Rewritten to pin the deps-field route with the three concrete edits (interface field, private readonly field, constructor assignment).

A separate logistics item (not a plan-content defect): the corrected plan lived only on `docs/b-prime-plan-corrections`, never on `main`, so Phase 0's "worktree off `main`" would have started from a baseline lacking this plan. Resolved by merging the docs branch to `main` before execution.

---

# Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-28-claude-code-docs-b-prime-recovery.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
