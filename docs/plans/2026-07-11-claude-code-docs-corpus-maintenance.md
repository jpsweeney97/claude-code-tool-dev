# claude-code-docs corpus maintenance: category coverage, canary tripwire, live golden queries

**Date:** 2026-07-11
**Package:** `packages/mcp-servers/claude-code-docs/`
**Branch:** `fix/claude-code-docs-corpus-maintenance` (already created from `main`; `main` is edit-protected by a PreToolUse hook)

## Context

The upstream corpus (`https://code.claude.com/docs/llms-full.txt`) grew from 142 pages (May 29, 2026 — the day before this package's last code change) to 165 pages today. The server's content/index refresh works correctly (24h TTL; the live index is current), but three code-level assumptions went stale:

1. **Category mapping:** `deriveCategory` does exact-match segment lookup only, so 40 of 165 pages (199 of 1,340 chunks, ~15%) resolve to `uncategorized` — the second-largest bucket in the index. The nine-page gateway family (`gateways`, `llm-gateway-connect/-protocol/-rollout`, `claude-apps-gateway` + 4 sub-pages) alone is 65 chunks.
2. **Canary blindness:** the fallback-delta canary only fires on *movement* relative to the last accepted baseline. The 40-section fallback count has been absorbed into `policyState.lastHealthyFallbackSectionCount`, so the live index reports `fallbackSectionRatio: 0.242` with zero warnings.
3. **Golden queries are mock-only:** `tests/golden-queries.test.ts` runs against a hard-coded synthetic corpus (fetch is mocked), so it cannot regress when the real corpus changes, and it has zero coverage of the new doc areas.

This plan fixes all three. It is a maintenance pass, not a redesign.

### Amendments from adversarial review (2026-07-11)

A `/review-reviewer` adjudication of the pre-implementation review confirmed four changes, folded into the tasks below:

1. **Production-equivalent live index (R1):** the live golden-query suite must index sections through the same transform production uses — `loadFromOfficial` enriches each section with synthetic `topic`/`id`/`category` frontmatter that feeds searchable metadata tokens and the page-title heading boost (`chunker.ts` `getMetadataTerms`/`headingTokens`; the parser excludes the `# Title` line from section content, so without the frontmatter the boost is lost entirely). Task 4.0 extracts `sectionToMarkdownFile()` from `loader.ts`; Task 4.3 reuses it. Pure refactor — no version bump.
2. **`fallback_ratio_high` serialization round-trip (R3):** Task 3.1 extends `tests/index-cache.test.ts` — a missed or later-regressed `WarningSchema` enum entry compiles clean and surfaces only as the server rejecting its own index cache on every startup.
3. **AGENTS.md resync scope (R2.a):** `AGENTS.md` is a stale, strictly-older copy of this package's `CLAUDE.md` (verified by diff: no unique content). Task 5.3 resyncs it wholesale. The later re-scrutiny below corrects this amendment's original charter classification: adding always-loaded `AGENTS.md` lines is gated even when the source is an existing first-party contract.
4. **Explicit corpus contract for the live suite (R4, narrowed):** the suite honors `CACHE_PATH` like production and fails — rather than passes — when the content cache is older than 7 days. Existence-based skip stays (matches the `corpus-validation.test.ts` convention, which is out of scope here).

### Amendments from re-scrutiny adjudication (2026-07-11)

A second `/review-reviewer` adjudication re-ran the empirical ranking probe through freshly compiled current source and found four deterministic legacy-query failures. The reconciled direction is recorded here before any plan mutation: keep the category expectations and fixed query counts, replace the four ambiguous or stale query phrasings with current-corpus language, keep the suite strictly green, and treat any later live failure as corpus drift or a ranking regression that stops implementation rather than triggering expectation calibration.

1. **Four pre-adjudicated query replacements:** Task 4.1 replaces the quickstart, permissions, slash-command, and plugin-marketplace phrasings. The resulting table is exactly 35 mocked queries + 9 live-only queries = 44 total. A current-source simulation against both the deterministic mock corpus and the real cached corpus produced zero failures (mock strict top-1; live top-3).
2. **Bounded green endgame:** Task 4.4 no longer contains an expectation-calibration loop. The executor may inspect top-5 results after a failure but must not edit expectations, toggle `liveOnly`, add replacement queries, or loosen assertions during implementation. Any failure stops before the Task 4 commit and is reported as a proposed plan amendment.
3. **Complete category-test update:** Task 1.1 now renames the 28-category test, adds `gateways` to its explicit membership list, updates the general-category count, and adds `gateway` to the negative alias invariant.
4. **Gated `AGENTS.md` admission:** Task 5.3 records an **ADMIT** decision under the behavior-contract charter. The decision is already durable in `/Users/jp/.agents` commit `fe03db35`; implementation verifies that precondition before the copy but performs no new cross-repository mutation. Task 5.1 also corrects `CANARY_VERSION`'s documented location (`index-cache.ts`, not `canary.ts`) and removes the `rm -rf dist/` conflict before the text can enter `AGENTS.md`.

### Settled design decisions (do not relitigate)

- New category is named **`gateways`** (plural, matching `providers`/`plugins`/`integrations` convention; the overview page slug is literally `gateways`). Alias `gateway` → `gateways`.
- The resolver gains **longest-prefix matching with a hyphen boundary** (exact match first; then the longest key `K` where the segment starts with `K + '-'`). This auto-absorbs future family sub-pages (`claude-apps-gateway-*` was nine pages in one upstream push).
- The canary check is **warn-only at ratio ≥ 0.10**, official mode only. A static share threshold must never reject (that fragility is why the old taxonomy canary was replaced in PR #130); rejection stays owned by the existing movement gates. The ratio warning must **not** affect policy-state (baseline) advancement.
- The live golden-query suite asserts the expected category **within the top-3 results** (the mocked suite stays strict top-1). The real corpus moves weekly; top-1 against a moving corpus produces churn, not signal.
- Borderline page mappings (accepted as-is): `advisor` → `interactive`, `artifacts` → `interactive`, `champion-kit`/`communications-kit` → `best-practices`.

### Non-goals

- No chunker/tokenizer/BM25 changes. No new MCP tools. No architecture changes.
- The `MAX_CHUNK_LINES` duplication between `chunker.ts` and `corpus-validation.test.ts` is a known nit, out of scope here.

## Working conventions

- **All package commands run from `packages/mcp-servers/claude-code-docs/`** (not the monorepo root). Task 5.3 performs one read-only verification against `/Users/jp/.agents` commit `fe03db35`; the charter-ledger write is already complete and must not be repeated or mixed into package work.
- Test: `npm test` (vitest run). Typecheck: `npx tsc --noEmit`. Focused test file: `npx vitest run tests/<name>.test.ts`.
- The machine this runs on has a populated content cache at `~/Library/Caches/claude-code-docs/llms-full.txt` (165 sections), so `corpus-validation.test.ts` and the new live suite will actually execute, not skip.
- Version-bump policy (from package CLAUDE.md): categories/frontmatter changes → `INGESTION_VERSION`; canary threshold/logic changes → `CANARY_VERSION`. Both bumps are in this plan; without them stale cached indexes would be served.

## File map

| File | Action | Change |
|---|---|---|
| `src/categories.ts` | modify | `gateways` category, 31 mapping-table changes, `resolveSegmentCategory()` prefix resolver, alias |
| `src/frontmatter.ts` | modify | `deriveCategory` + `getUnmappedSegments` delegate to `resolveSegmentCategory` |
| `src/canary.ts` | modify | `FALLBACK_RATIO_WARN_THRESHOLD`, `fallback_ratio_high` warning code + emission |
| `src/index-cache.ts` | modify | `INGESTION_VERSION` 6→7, `CANARY_VERSION` 2→3, `WarningSchema` enum |
| `src/status.ts` | modify | `StatusWarningCodeSchema` enum |
| `src/loader.ts` | modify | extract `sectionToMarkdownFile()` — pure refactor, no behavior change, no version bump |
| `tests/loader.test.ts` | modify | unit test pinning the transform's frontmatter-enriched output |
| `tests/index-cache.test.ts` | modify | `fallback_ratio_high` warning round-trip |
| `tests/categories.test.ts` | modify | 29-count, new mappings, alias, resolver tests |
| `tests/frontmatter.test.ts` | modify | prefix-resolution tests |
| `tests/canary.test.ts` | modify | ratio-tripwire tests |
| `tests/status.test.ts` | modify | `fallback_ratio_high` passthrough test |
| `tests/golden-query-data.ts` | **create** | shared query table (35 mock-covered + 9 live-only; 44 total) |
| `tests/golden-queries.test.ts` | modify | import shared table, filter `liveOnly` |
| `tests/golden-queries.live.test.ts` | **create** | live-corpus suite (production transform, `CACHE_PATH` + 7-day age guard, top-3 assertion + structural checks) |
| `CLAUDE.md` (package) | modify | counts, resolver description, canary description, test table, version-constant path, safe cache-clear wording |
| `README.md` (package) | modify | category list, alias list, warning-code list |
| `AGENTS.md` (package) | modify | charter-admitted full resync — copy of the corrected `CLAUDE.md` (stale strictly-older duplicate; no unique content) |
| `/Users/jp/.agents/docs/agents/contract-decisions.md` | verify only | charter admission already committed as `fe03db35`; must exist before changing package `AGENTS.md` |

Execution order matters: Tasks 1–2 form one commit (categorization change + version bump must land atomically), then 3, 4, 5 are independent commits, 6 is verification.

---

## Task 0: Verify branch and baseline

```bash
cd packages/mcp-servers/claude-code-docs
git branch --show-current   # expect: fix/claude-code-docs-corpus-maintenance
npm test                    # expect: all test files pass (pre-change baseline)
npx tsc --noEmit            # expect: exit 0, no output
```

If the branch is missing: `git checkout -b fix/claude-code-docs-corpus-maintenance main`.

---

## Task 1: `gateways` category and explicit slug mappings

### 1.1 Write failing tests

In `tests/categories.test.ts`:

Rename the canonical-category test, update its general-category count, add `gateways` immediately after `providers` in the explicit membership list, and change the size assertion:

```ts
  it('contains all 29 canonical categories', () => {
    const expected = [
      // Extension categories (10)
      'hooks', 'skills', 'commands', 'agents', 'plugins',
      'plugin-marketplaces', 'mcp', 'channels', 'settings', 'memory',
      // General categories (19)
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'gateways', 'ide', 'ci-cd',
      'automation', 'agent-sdk', 'desktop', 'integrations', 'config',
      'operations', 'troubleshooting', 'changelog', 'uncategorized',
    ];

    expect(KNOWN_CATEGORIES.size).toBe(29);
```

Inside the existing `it('does not contain aliases as canonical categories', ...)` test, add:

```ts
    expect(KNOWN_CATEGORIES.has('gateway')).toBe(false);
```

Add inside the `describe('SECTION_TO_CATEGORY', ...)` block:

```ts
  it('maps the gateway family to gateways', () => {
    expect(SECTION_TO_CATEGORY['gateways']).toBe('gateways');
    expect(SECTION_TO_CATEGORY['claude-apps-gateway']).toBe('gateways');
    expect(SECTION_TO_CATEGORY['llm-gateway']).toBe('gateways');
  });

  it('maps segments added with the 2026-07 corpus growth', () => {
    expect(SECTION_TO_CATEGORY['agents']).toBe('agents');
    expect(SECTION_TO_CATEGORY['agent-view']).toBe('agents');
    expect(SECTION_TO_CATEGORY['admin-setup']).toBe('settings');
    expect(SECTION_TO_CATEGORY['auto-mode-config']).toBe('security');
    expect(SECTION_TO_CATEGORY['sandbox-environments']).toBe('security');
    expect(SECTION_TO_CATEGORY['claude-platform-on-aws']).toBe('providers');
    expect(SECTION_TO_CATEGORY['managed-mcp']).toBe('mcp');
    expect(SECTION_TO_CATEGORY['plugin-dependencies']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['plugin-hints']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['plugin-relevance']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['debug-your-config']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['troubleshoot-install']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['errors']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['ultrareview']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['feature-availability']).toBe('overview');
    expect(SECTION_TO_CATEGORY['glossary']).toBe('overview');
    expect(SECTION_TO_CATEGORY['large-codebases']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['prompt-library']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['champion-kit']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['communications-kit']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['sessions']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['worktrees']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['advisor']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['artifacts']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['deep-links']).toBe('integrations');
    expect(SECTION_TO_CATEGORY['workflows']).toBe('automation');
    expect(SECTION_TO_CATEGORY['goal']).toBe('automation');
    expect(SECTION_TO_CATEGORY['prompt-caching']).toBe('operations');
  });
```

Add inside the `describe('CATEGORY_ALIASES', ...)` block's alias test:

```ts
    expect(CATEGORY_ALIASES['gateway']).toBe('gateways');
```

Run and watch fail:

```bash
npx vitest run tests/categories.test.ts
# expect: FAIL — size 28 !== 29, gateway-family mappings undefined
```

### 1.2 Implement in `src/categories.ts`

Edit the `KNOWN_CATEGORIES` doc comment (line 5): `the 28 categories` → `the 29 categories`.

Edit the general-categories comment (line 19): `// General categories (18)` → `// General categories (19)`.

Add `'gateways',` immediately after the `'providers',` line in `KNOWN_CATEGORIES`.

Change the existing mapping (line 94):

```ts
  'llm-gateway': 'gateways',
```

Add immediately after that line:

```ts
  'gateways': 'gateways',
  'claude-apps-gateway': 'gateways',
```

Append at the end of `SECTION_TO_CATEGORY`, after the `'whats-new': 'changelog',` line and before the closing `};`:

```ts
  // Standalone pages with no family-prefix parent key. Family sub-pages
  // (llm-gateway-*, claude-apps-gateway-*, mcp-*, security-*, desktop-*)
  // resolve via resolveSegmentCategory's longest-prefix rule instead.
  'agents': 'agents',
  'agent-view': 'agents',
  'admin-setup': 'settings',
  'auto-mode-config': 'security',
  'sandbox-environments': 'security',
  'claude-platform-on-aws': 'providers',
  'managed-mcp': 'mcp',
  'plugin-dependencies': 'plugins',
  'plugin-hints': 'plugins',
  'plugin-relevance': 'plugins',
  'debug-your-config': 'troubleshooting',
  'troubleshoot-install': 'troubleshooting',
  'errors': 'troubleshooting',
  'ultrareview': 'ci-cd',
  'feature-availability': 'overview',
  'glossary': 'overview',
  'large-codebases': 'best-practices',
  'prompt-library': 'best-practices',
  'champion-kit': 'best-practices',
  'communications-kit': 'best-practices',
  'sessions': 'interactive',
  'worktrees': 'interactive',
  'advisor': 'interactive',
  'artifacts': 'interactive',
  'deep-links': 'integrations',
  'workflows': 'automation',
  'goal': 'automation',
  'prompt-caching': 'operations',
```

(The comment above references `resolveSegmentCategory`, added in Task 2 — same commit.)

Add to `CATEGORY_ALIASES`:

```ts
  'gateway': 'gateways',
```

### 1.3 Verify

```bash
npx vitest run tests/categories.test.ts
# expect: PASS (including the pre-existing "every mapping value is a known category" invariant test)
```

Do **not** commit yet — Task 2 belongs in the same commit (see version-bump note there).

---

## Task 2: Longest-prefix segment resolution + `INGESTION_VERSION` bump

### 2.1 Write failing tests

Add to `tests/categories.test.ts` — extend the import line to include `resolveSegmentCategory`:

```ts
import { KNOWN_CATEGORIES, SECTION_TO_CATEGORY, CATEGORY_ALIASES, resolveSegmentCategory } from '../src/categories.js';
```

Add a new top-level describe block:

```ts
describe('resolveSegmentCategory', () => {
  it('resolves exact keys', () => {
    expect(resolveSegmentCategory('hooks')).toBe('hooks');
    expect(resolveSegmentCategory('llm-gateway')).toBe('gateways');
  });

  it('resolves family sub-pages by hyphen-bounded prefix', () => {
    expect(resolveSegmentCategory('llm-gateway-rollout')).toBe('gateways');
    expect(resolveSegmentCategory('claude-apps-gateway-on-gcp')).toBe('gateways');
    expect(resolveSegmentCategory('mcp-quickstart')).toBe('mcp');
    expect(resolveSegmentCategory('security-guidance')).toBe('security');
    expect(resolveSegmentCategory('desktop-linux')).toBe('desktop');
  });

  it('prefers the longest matching key', () => {
    // 'desktop-scheduled-tasks' has its own key (automation); the shorter
    // 'desktop' prefix (desktop) must not shadow it — including for deeper
    // hypothetical sub-pages of the more specific family.
    expect(resolveSegmentCategory('desktop-scheduled-tasks')).toBe('automation');
    expect(resolveSegmentCategory('desktop-scheduled-tasks-reference')).toBe('automation');
  });

  it('returns null for unknown segments and bare-prefix lookalikes', () => {
    expect(resolveSegmentCategory('nonexistent-page')).toBe(null);
    expect(resolveSegmentCategory('pluginsomething')).toBe(null);
    expect(resolveSegmentCategory('constructor')).toBe(null);
  });
});
```

Add to `tests/frontmatter.test.ts`, inside the existing `describe('deriveCategory', ...)` block:

```ts
  it('resolves family sub-pages via longest-prefix matching', () => {
    expect(deriveCategory('https://code.claude.com/docs/en/llm-gateway-connect')).toBe('gateways');
    expect(deriveCategory('https://code.claude.com/docs/en/claude-apps-gateway-spend-limits')).toBe('gateways');
    expect(deriveCategory('https://code.claude.com/docs/en/mcp-quickstart')).toBe('mcp');
    expect(deriveCategory('https://code.claude.com/docs/en/security-guidance')).toBe('security');
    expect(deriveCategory('https://code.claude.com/docs/en/desktop-linux')).toBe('desktop');
  });

  it('requires a hyphen boundary for prefix matches', () => {
    expect(deriveCategory('https://code.claude.com/docs/en/pluginsomething')).toBe('uncategorized');
    expect(deriveCategory('https://code.claude.com/docs/en/hookswild')).toBe('uncategorized');
  });
```

And inside the existing `describe('getUnmappedSegments', ...)` block:

```ts
  it('agrees with deriveCategory prefix resolution', () => {
    expect(getUnmappedSegments('https://code.claude.com/docs/en/llm-gateway-connect')).toEqual([]);
    expect(getUnmappedSegments('https://code.claude.com/docs/en/mcp-quickstart')).toEqual([]);
  });
```

Run and watch fail:

```bash
npx vitest run tests/categories.test.ts tests/frontmatter.test.ts
# expect: FAIL — resolveSegmentCategory is not exported; prefix URLs return 'uncategorized'
```

### 2.2 Implement the resolver in `src/categories.ts`

Append after the `SECTION_TO_CATEGORY` declaration (before `CATEGORY_ALIASES`):

```ts
/**
 * Keys of SECTION_TO_CATEGORY sorted longest-first (ties alphabetical) so prefix
 * resolution deterministically prefers the most specific family key
 * (e.g. 'desktop-scheduled-tasks' over 'desktop').
 */
const SECTION_KEYS_LONGEST_FIRST: readonly string[] = Object.keys(SECTION_TO_CATEGORY)
  .sort((a, b) => b.length - a.length || a.localeCompare(b));

/**
 * Resolve one URL path segment to its canonical category.
 *
 * Resolution order:
 * 1. Exact key match in SECTION_TO_CATEGORY.
 * 2. Longest key K such that the segment starts with `K + '-'` — new sub-pages of a
 *    known family (e.g. 'llm-gateway-connect', 'claude-apps-gateway-config',
 *    'mcp-quickstart', 'desktop-linux') resolve without a table edit.
 *
 * The '-' boundary prevents bare-prefix false positives ('pluginsomething' must not
 * match 'plugins'). Returns null when nothing matches.
 */
export function resolveSegmentCategory(segment: string): string | null {
  if (Object.hasOwn(SECTION_TO_CATEGORY, segment)) {
    return SECTION_TO_CATEGORY[segment];
  }
  for (const key of SECTION_KEYS_LONGEST_FIRST) {
    if (segment.startsWith(key + '-')) {
      return SECTION_TO_CATEGORY[key];
    }
  }
  return null;
}
```

### 2.3 Delegate in `src/frontmatter.ts`

Change the import (line 3):

```ts
import { resolveSegmentCategory } from './categories.js';
```

In `deriveCategory`, replace the lookup loop body:

```ts
    for (const seg of segments) {
      const category = resolveSegmentCategory(seg);
      if (category) return category;
    }
```

In `getUnmappedSegments`, replace the `anyMapped` line:

```ts
  const anyMapped = segments.some(seg => resolveSegmentCategory(seg) !== null);
```

Also update `getUnmappedSegments`'s doc comment: replace the sentence `Uses Object.hasOwn to avoid prototype-chain false positives.` with `Shares resolveSegmentCategory with deriveCategory so the loader's fallback diagnostics always agree with actual chunk categorization.`

**Consistency constraint (why both functions must change together):** `loader.ts` computes `fallbackSectionCount` via `deriveCategory` and `unmappedSegments` via `getUnmappedSegments`; the canary consumes both. If only one adopts prefix matching, the diagnostics disagree with the categorization the chunks actually get.

### 2.4 Bump `INGESTION_VERSION`

In `src/index-cache.ts` (line 37):

```ts
export const INGESTION_VERSION = 7;
```

The bump lives in this commit — not Task 1's — because both tasks change category derivation, and an intermediate commit with new mappings but no bump would serve a stale cached index to anyone building at that commit.

### 2.5 Verify and commit

```bash
npx tsc --noEmit                    # expect: exit 0
npm test                            # expect: ALL files pass, incl. loader/chunker/lifecycle
                                    # (they consume deriveCategory; targeted assertions still hold)
git add src/categories.ts src/frontmatter.ts src/index-cache.ts tests/categories.test.ts tests/frontmatter.test.ts
git commit -m "feat(claude-code-docs): close category coverage gap (gateways category, slug mappings, prefix resolver)"
```

Coverage proof for the 40 currently-uncategorized pages: 30 resolve via new/changed explicit keys, 10 via the prefix rule (`claude-apps-gateway-config/-deploy/-on-gcp/-spend-limits`, `llm-gateway-connect/-protocol/-rollout`, `mcp-quickstart`, `security-guidance`, `desktop-linux`). Expected live fallback count after rebuild: **0 of 165**. Task 4's live suite asserts this against the real corpus.

---

## Task 3: Absolute fallback-ratio canary warning

### 3.1 Write failing tests

In `tests/canary.test.ts`, extend the import from `../src/canary.js` to include `FALLBACK_RATIO_WARN_THRESHOLD`, and add to the `'canary threshold constants'` describe:

```ts
  it('has an absolute fallback-ratio warn threshold', () => {
    expect(FALLBACK_RATIO_WARN_THRESHOLD).toBe(0.10);
  });
```

Add a new top-level describe block at the end of the file:

```ts
describe('fallback_ratio_high (absolute ratio tripwire)', () => {
  const baseDiag = {
    sourceAnchoredCount: 165,
    nonEmptySectionCount: 165,
    sectionCount: 165,
    fallbackSegmentCount: 1,
    unmappedSegments: [['some-new-family', 2]] as Array<[string, number]>,
    parseWarningCount: 0,
  };

  it('warns on the 2026-07 real-world shape (40/165 ≈ 24%) even with a stable baseline', () => {
    // This is the exact silent-drift scenario that motivated the check: the delta
    // gates see no movement (baseline == current), yet a quarter of the corpus is
    // uncategorized.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 40 },
      policyState: establishedPolicyState(165, 40),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_segment_drift')).toBe(false);
    const warn = result.warnings.find(w => w.code === 'fallback_ratio_high');
    expect(warn).toBeDefined();
    expect(warn!.severity).toBe('warn');
    expect(warn!.details).toMatchObject({
      fallbackSectionCount: 40,
      sectionCount: 165,
      threshold: FALLBACK_RATIO_WARN_THRESHOLD,
    });
  });

  it('fires at the threshold boundary (>=) and stays silent just below', () => {
    const atThreshold = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, sectionCount: 50, nonEmptySectionCount: 50, sourceAnchoredCount: 50, fallbackSectionCount: 5 },
      policyState: establishedPolicyState(50, 5),
      now: NOW,
    });
    expect(atThreshold.warnings.some(w => w.code === 'fallback_ratio_high')).toBe(true);

    const below = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, sectionCount: 50, nonEmptySectionCount: 50, sourceAnchoredCount: 50, fallbackSectionCount: 4 },
      policyState: establishedPolicyState(50, 4),
      now: NOW,
    });
    expect(below.warnings.some(w => w.code === 'fallback_ratio_high')).toBe(false);
  });

  it('never fires in unsafe mode', () => {
    const result = evaluateCanaries({
      trustMode: 'unsafe',
      diagnostics: { ...baseDiag, fallbackSectionCount: 40 },
      policyState: emptyPolicyState(),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    expect(result.warnings.some(w => w.code === 'fallback_ratio_high')).toBe(false);
  });

  it('does not block fallback-baseline advancement', () => {
    // Ratio warn fires (40/165), but delta is small (+2 < WARN_ABS 5) so there is
    // no drift warn — the baseline must still advance. Freezing on a standing
    // condition would deadlock advancement while the ratio stays high.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 40 },
      policyState: establishedPolicyState(165, 38),
      now: NOW,
    });
    expect(result.warnings.some(w => w.code === 'fallback_ratio_high')).toBe(true);
    expect(result.nextPolicyState.lastHealthyFallbackSectionCount).toBe(40);
    expect(result.nextPolicyState.lastHealthyFallbackObservedAt).toBe(NOW);
  });

  it('coexists with fallback_segment_drift when both conditions hold', () => {
    // baseline 12 → 20 of 165: ratio 0.121 ≥ 0.10; delta +8 ≥ WARN_ABS 5 and
    // mult 1.67 ≥ 1.5 (drift warn) but below FAIL gates → accept with both warnings.
    const result = evaluateCanaries({
      trustMode: 'official',
      diagnostics: { ...baseDiag, fallbackSectionCount: 20 },
      policyState: establishedPolicyState(165, 12),
      now: NOW,
    });
    expect(result.decision).toBe('accept');
    const codes = result.warnings.map(w => w.code);
    expect(codes).toContain('fallback_segment_drift');
    expect(codes).toContain('fallback_ratio_high');
  });
});
```

In `tests/status.test.ts`, add inside `describe('buildRuntimeStatus', ...)`:

```ts
  it('passes fallback_ratio_high through warning_codes', () => {
    const status = buildRuntimeStatus({
      ...BASE_INPUT,
      warningCodes: ['fallback_ratio_high'],
    });
    expect(status.warning_codes).toContain('fallback_ratio_high');
  });
```

In `tests/index-cache.test.ts`, extend the existing `'preserves evaluation warnings through round-trip'` test — append a third warning after the `parse_issues` entry in the `warnings` array:

```ts
          {
            code: 'fallback_ratio_high',
            severity: 'warn',
            details: { fallbackSectionCount: 40, sectionCount: 165, threshold: 0.10 },
          },
```

and update its assertions:

```ts
    expect(parsed!.evaluation.warnings).toHaveLength(3);
    expect(parsed!.evaluation.warnings[0].code).toBe('fallback_segment_drift');
    expect(parsed!.evaluation.warnings[1].code).toBe('parse_issues');
    expect(parsed!.evaluation.warnings[2].code).toBe('fallback_ratio_high');
```

Why this test exists: `WarningCode` (canary.ts), `WarningSchema` (index-cache.ts), and `StatusWarningCodeSchema` (status.ts) have no compile-time link. A missed or later-regressed `WarningSchema` entry compiles clean; at runtime the server writes the warning, then `parseSerializedIndex` rejects its own index cache on the next startup — rebuild on every start. The round-trip pins the serialization surface the way the status passthrough test pins the status surface.

Run and watch fail:

```bash
npx vitest run tests/canary.test.ts tests/status.test.ts tests/index-cache.test.ts
# expect: FAIL — FALLBACK_RATIO_WARN_THRESHOLD not exported; no fallback_ratio_high warnings;
#         round-trip rejects the unknown warning code (parsed is null)
```

### 3.2 Implement in `src/canary.ts`

Add after the `FALLBACK_DELTA_FAIL_REL` constant (line 28):

```ts
// --- Absolute fallback-ratio tripwire (warn-only) ---
// The delta/multiplier gates above only catch movement relative to the last accepted
// baseline. Slow accretion (each load under WARN_ABS/WARN_REL) is absorbed into the
// baseline and becomes permanently invisible — by 2026-07 the real corpus reached
// 40/165 uncategorized sections (24%) with zero warnings. This gate is the standing
// tripwire: it fires on the absolute share regardless of baseline history. Warn-only
// by design — a static share threshold must never reject (that fragility class is why
// the original taxonomy canary was replaced); rejection stays owned by the movement gates.
export const FALLBACK_RATIO_WARN_THRESHOLD = 0.10;
```

Extend the `WarningCode` union (line 55):

```ts
export type WarningCode =
  | 'fallback_segment_drift'
  | 'fallback_ratio_high'
  | 'parse_issues'
  | 'section_count_drift';
```

Add the emission in `evaluateCanaries`, after the first-run fallback drift warning block (the one gated on `baselineFallback === null`) and before the `parseWarningCount` block:

```ts
  // Absolute fallback-ratio tripwire (official mode only): fires on the standing share
  // of uncategorized sections, independent of baseline history. Deliberately excluded
  // from the policy-state advancement below — freezing the baseline on a standing
  // condition would deadlock advancement while the ratio stays high and distort the
  // delta gates' reference point.
  if (
    trustMode === 'official' &&
    fallbackSectionRatio >= FALLBACK_RATIO_WARN_THRESHOLD
  ) {
    warnings.push({
      code: 'fallback_ratio_high',
      severity: 'warn',
      details: {
        fallbackSectionCount,
        sectionCount,
        fallbackSectionRatio,
        threshold: FALLBACK_RATIO_WARN_THRESHOLD,
        sampleSegments: diagnostics.unmappedSegments.slice(0, 10).map(([seg]) => seg),
      },
    });
  }
```

Do **not** touch the advancement logic (`hasFallbackDrift` stays keyed on `'fallback_segment_drift'` only — that exclusion is what the advancement test above proves).

### 3.3 Sync serialization and status schemas

`src/index-cache.ts` — `WarningSchema` (line 209):

```ts
  code: z.enum(['fallback_segment_drift', 'fallback_ratio_high', 'parse_issues', 'section_count_drift']),
```

`src/index-cache.ts` — `CANARY_VERSION` (line 49):

```ts
export const CANARY_VERSION = 3;
```

`src/status.ts` — `StatusWarningCodeSchema` (line 14):

```ts
export const StatusWarningCodeSchema = z.enum([
  'fallback_segment_drift',
  'fallback_ratio_high',
  'parse_issues',
  'section_count_drift',
  'stale_corpus',
]);
```

### 3.4 Verify and commit

```bash
npx tsc --noEmit
npm test
# expect: ALL pass. Existing canary tests use targeted warnings.find/some(code === ...)
# assertions, so the incidentally-added ratio warning in high-ratio fixtures does not
# break them (verified by inspection of tests/canary.test.ts before planning).
git add src/canary.ts src/index-cache.ts src/status.ts tests/canary.test.ts tests/status.test.ts tests/index-cache.test.ts
git commit -m "feat(claude-code-docs): add absolute fallback-ratio canary warning"
```

---

## Task 4: Shared golden-query table + live-corpus suite

### 4.0 Extract the production section→file transform (`src/loader.ts`)

The live suite must build its index from exactly the files production indexes. `loadFromOfficial` enriches each section with synthetic frontmatter (`topic`/`id`/`category`) that feeds searchable metadata tokens and the page-title heading boost; a bare `{ path, content }` mapping would measure rankings the server never produces. Extract the mapping as a pure exported function. Behavior-preserving refactor — **no version bump** (`INGESTION_VERSION` covers ingestion behavior changes; this changes none).

In `src/loader.ts`, add after `deriveIdFromUrl` (above `loadFromOfficial`):

```ts
/**
 * Transform one parsed section into the frontmatter-enriched MarkdownFile the
 * index is built from. Exported so the live golden-query suite indexes the
 * cached corpus through the exact production path (golden-queries.live.test.ts)
 * — keep this the single source of that mapping.
 */
export function sectionToMarkdownFile(s: ParsedSection): MarkdownFile {
  const sourceKey = s.sourceUrl || s.title || '';
  const topic = s.title?.trim() || undefined;
  const id = deriveIdFromUrl(s.sourceUrl);
  const category = deriveCategory(sourceKey);

  // Build synthetic frontmatter to enrich metadata for search
  const frontmatter = buildSyntheticFrontmatter({ topic, id, category });

  return {
    path: s.sourceUrl || s.title || 'unknown',
    content: frontmatter + s.content,
  };
}
```

Replace the entire `files:` mapping at the end of `loadFromOfficial` (the `filtered.map((s) => { ... })` block) with:

```ts
    files: filtered.map(sectionToMarkdownFile),
```

Add to `tests/loader.test.ts` as a new top-level describe (dynamic import matches the file's convention):

```ts
describe('sectionToMarkdownFile', () => {
  it('builds the frontmatter-enriched file the production index consumes', async () => {
    const { sectionToMarkdownFile } = await import('../src/loader.js');
    const file = sectionToMarkdownFile({
      sourceUrl: 'https://code.claude.com/docs/en/hooks-guide',
      title: 'Get started with hooks',
      content: 'Body text.',
    });
    expect(file.path).toBe('https://code.claude.com/docs/en/hooks-guide');
    expect(file.content).toBe(
      '---\n' +
        'topic: "Get started with hooks"\n' +
        'id: "hooks-guide"\n' +
        'category: "hooks"\n' +
        '---\n' +
        'Body text.',
    );
  });
});
```

This is a refactor, not new behavior — the fail-first pattern does not apply; the test passes immediately:

```bash
npx vitest run tests/loader.test.ts   # expect: PASS, incl. the new describe
```

### 4.1 Create `tests/golden-query-data.ts`

Full file content — 31 existing queries are moved verbatim from `tests/golden-queries.test.ts` (lines 552–594), 4 are replaced with the pre-adjudicated current-corpus phrasings below, and the 9 `liveOnly` entries are new. Final invariant: 35 non-`liveOnly` + 9 `liveOnly` = 44 total.

```ts
// tests/golden-query-data.ts
// Shared golden-query table.
// - golden-queries.test.ts runs the non-liveOnly entries against a deterministic
//   mock corpus with strict top-1 assertions.
// - golden-queries.live.test.ts runs ALL entries against the real cached corpus
//   with top-3 assertions.

export interface GoldenQuery {
  query: string;
  expectedTopCategory: string;
  /**
   * True for queries about doc areas that exist only in the real corpus (no mock
   * section in golden-queries.test.ts). Run only by golden-queries.live.test.ts.
   */
  liveOnly?: boolean;
}

export const GOLDEN_QUERIES: GoldenQuery[] = [
  // Extension categories (existing)
  { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
  { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
  { query: 'skill frontmatter', expectedTopCategory: 'skills' },
  { query: 'MCP server registration', expectedTopCategory: 'mcp' },
  { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  { query: 'subagent isolated context delegation', expectedTopCategory: 'agents' },
  // New categories
  // The old generic quickstart/npm query ranked Agent SDK first live. This wording
  // targets the product-installation page and passes mock top-1 + live top-3.
  { query: 'install Claude Code npm package manager', expectedTopCategory: 'getting-started' },
  { query: 'bedrock AWS credentials region', expectedTopCategory: 'providers' },
  { query: 'VS Code keybindings extension', expectedTopCategory: 'ide' },
  { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
  { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
  { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
  { query: 'agent teams leader worker coordination', expectedTopCategory: 'agents' },
  { query: 'authentication login API key', expectedTopCategory: 'security' },
  // Uses the current permissions page's allow/ask/deny vocabulary; the old query
  // ranked Agent SDK permission material above the exact product page.
  { query: 'fine grained permissions allow ask deny rules', expectedTopCategory: 'security' },
  // New priority categories (B12)
  // Custom-command YAML is no longer the product commands page's contract. The
  // current page is the complete built-in/bundled command reference.
  { query: 'built-in commands bundled skills complete reference', expectedTopCategory: 'commands' },
  { query: 'plugin manifest structure install', expectedTopCategory: 'plugins' },
  { query: 'settings hierarchy configuration', expectedTopCategory: 'settings' },
  { query: 'CLAUDE.md memory persistent sessions', expectedTopCategory: 'memory' },
  { query: 'CLI flags model allowedTools', expectedTopCategory: 'cli' },
  { query: 'vim mode interactive editing', expectedTopCategory: 'interactive' },
  { query: 'desktop application native install', expectedTopCategory: 'desktop' },
  { query: 'overview agentic terminal tool', expectedTopCategory: 'overview' },
  // New categories (channels, automation, agent-sdk)
  { query: 'channel push events Telegram Discord', expectedTopCategory: 'channels' },
  { query: 'sender allowlist channel security', expectedTopCategory: 'channels' },
  { query: 'Agent SDK agent loop turns messages', expectedTopCategory: 'agent-sdk' },
  { query: 'scheduled tasks loop recurring prompt', expectedTopCategory: 'automation' },
  // Remaining categories (full coverage)
  // Browse/install is correctly answered by discover-plugins; marketplace authoring
  // is the stable discriminator for the plugin-marketplaces category.
  { query: 'plugin marketplace schema host distribute marketplace', expectedTopCategory: 'plugin-marketplaces' },
  { query: 'effective prompts iterative workflow tips', expectedTopCategory: 'best-practices' },
  { query: 'configuration files model settings override', expectedTopCategory: 'config' },
  { query: 'token usage cost dashboard spending limits', expectedTopCategory: 'operations' },
  { query: 'Slack app mention channel thread integration', expectedTopCategory: 'integrations' },
  { query: 'changelog release version history fixes', expectedTopCategory: 'changelog' },
  // Morphological variant queries (stemming coverage)
  { query: 'configuring MCP servers', expectedTopCategory: 'mcp' },
  { query: 'creating custom skills', expectedTopCategory: 'skills' },
  // Live-only queries — doc areas added upstream 2026-06/07; no mock sections exist.
  { query: 'Claude apps gateway OIDC SSO identity provider', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'connect Claude Code to LLM gateway ANTHROPIC_BASE_URL', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'gateway spend limits cap developer spend', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'advisor consult stronger model before committing', expectedTopCategory: 'interactive', liveOnly: true },
  { query: 'artifacts publish interactive page from session', expectedTopCategory: 'interactive', liveOnly: true },
  { query: 'claude mcp add connect first MCP server', expectedTopCategory: 'mcp', liveOnly: true },
  { query: 'plugin relevance marketplace signals suggestion', expectedTopCategory: 'plugins', liveOnly: true },
  { query: 'feature availability by provider and plan', expectedTopCategory: 'overview', liveOnly: true },
  { query: 'install Claude desktop app Ubuntu Debian apt', expectedTopCategory: 'desktop', liveOnly: true },
];
```

### 4.2 Point the mocked suite at the shared table

In `tests/golden-queries.test.ts`:

Add to the imports:

```ts
import { GOLDEN_QUERIES } from './golden-query-data.js';
```

Delete the entire inline `const goldenQueries = [ ... ];` array (lines 552–594).

Change the loop header from `for (const { query, expectedTopCategory } of goldenQueries) {` to:

```ts
  for (const { query, expectedTopCategory } of GOLDEN_QUERIES.filter((q) => !q.liveOnly)) {
```

Verify the mocked suite still passes unchanged (35 query tests, same assertions):

```bash
npx vitest run tests/golden-queries.test.ts
# expect: PASS, same test count as before the refactor
```

### 4.3 Create `tests/golden-queries.live.test.ts`

Full file content:

```ts
// tests/golden-queries.live.test.ts
// Runs the shared golden-query table against the REAL cached corpus, indexed
// through the SAME transform production uses (sectionToMarkdownFile: synthetic
// topic/id/category frontmatter → metadata tokens + page-title heading boost),
// unlike golden-queries.test.ts which runs against a synthetic mock.
//
// Corpus contract (cached-corpus test, not a network test):
// - Reads the content cache the production server maintains (24h TTL),
//   honoring CACHE_PATH like production.
// - Skips when no cache exists (corpus-validation.test.ts convention).
// - FAILS when the cache is older than MAX_CACHE_AGE_MS — a stale corpus must
//   not silently pass as live-search proof.
//
// Assertions are deliberately looser than the mocked suite (expected category in
// the top-3 results rather than top-1): the live corpus changes upstream weekly,
// and top-1 assertions against a moving corpus produce churn, not signal.
// A failure here means either (a) a ranking regression, or (b) the corpus moved
// materially — investigate before editing any expectation.
import { describe, it, expect, beforeAll } from 'vitest';
import { existsSync } from 'fs';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';
import { parseSections } from '../src/parser.js';
import { readCache, getDefaultCachePath } from '../src/cache.js';
import { sectionToMarkdownFile } from '../src/loader.js';
import { deriveCategory } from '../src/frontmatter.js';
import { GOLDEN_QUERIES } from './golden-query-data.js';

// Mirrors production's CACHE_PATH-first resolution (loader.ts resolveCachePath).
const cachePath = process.env.CACHE_PATH?.trim() || getDefaultCachePath();
const cacheExists = existsSync(cachePath);

// Generous bound: the production server refreshes the cache daily (24h TTL), so
// 7 days means "this machine has not run the server in a week — refresh first".
const MAX_CACHE_AGE_MS = 7 * 24 * 60 * 60 * 1000;

if (!cacheExists) {
  console.warn(
    `SKIPPING live golden queries: content cache not found at ${cachePath}\n` +
      `Run the server once to populate the cache, then re-run tests.`
  );
}

describe.skipIf(!cacheExists)('golden queries (live corpus)', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let sectionUrls: string[] = [];

  beforeAll(async () => {
    const cached = await readCache(cachePath);
    if (!cached) throw new Error(`Cache not readable at ${cachePath}`);
    if (cached.age > MAX_CACHE_AGE_MS) {
      const days = (cached.age / 86400000).toFixed(1);
      throw new Error(
        `Content cache is ${days} days old (max ${MAX_CACHE_AGE_MS / 86400000}). ` +
          `Refresh it (start the server or call reload_docs) before trusting live golden queries.`,
      );
    }
    const sections = parseSections(cached.content).filter(
      (s) => s.content.trim().length > 0,
    );
    sectionUrls = sections.map((s) => s.sourceUrl).filter((u) => u !== '');
    const files = sections.map(sectionToMarkdownFile);
    const chunks = files.flatMap((f) => chunkFile(f).chunks);
    index = buildBM25Index(chunks);
  });

  for (const { query, expectedTopCategory } of GOLDEN_QUERIES) {
    it(`"${query}" surfaces ${expectedTopCategory} in top-3 categories`, () => {
      const results = search(index, query, 3);
      expect(results.length).toBeGreaterThan(0);
      expect(results.map((r) => r.category)).toContain(expectedTopCategory);
    });
  }

  it('live corpus is nearly fully categorized (< 5% uncategorized sections)', () => {
    // Tighter than the runtime canary's 0.10 warn threshold on purpose: tests run
    // at development time where a nag is cheap; the canary guards production loads.
    const uncategorized = sectionUrls.filter((u) => deriveCategory(u) === 'uncategorized');
    const ratio = uncategorized.length / sectionUrls.length;
    expect(ratio, `uncategorized pages: ${uncategorized.join(', ')}`).toBeLessThan(0.05);
  });

  it('gateway family pages are indexed under the gateways category', () => {
    const gatewayChunks = index.chunks.filter((c) => c.category === 'gateways');
    expect(gatewayChunks.length).toBeGreaterThan(0);
  });
});
```

### 4.4 Run the pre-adjudicated live suite

```bash
npx vitest run tests/golden-queries.live.test.ts
```

Expected: all 44 query assertions pass, as do the `< 5% uncategorized` and gateways structural tests. The four prior failures are already adjudicated and replaced in Task 4.1:

| Old query | Finding | Final query | Current proof |
|---|---|---|---|
| `quickstart npm package installation` | Ambiguous with Agent SDK quickstart; keep `getting-started`, target product installation explicitly | `install Claude Code npm package manager` | mock top-1; live top-1 |
| `permission system approval levels` | Exact permissions page existed but ranked below top-5; use its current allow/ask/deny language | `fine grained permissions allow ask deny rules` | mock top-1; live top-1 |
| `slash command definition YAML` | Stale custom-command contract; current product page is a built-in/bundled command reference | `built-in commands bundled skills complete reference` | mock top-1; live top-1 |
| `plugin marketplace browse install community` | Browse/install is correctly answered by `discover-plugins`; target marketplace authoring | `plugin marketplace schema host distribute marketplace` | mock top-1; live top-1 |

The final query-table contract is fixed for this implementation: **35 non-`liveOnly`, 9 `liveOnly`, 44 total**. Do not change an expected category, toggle `liveOnly`, add a replacement query, or loosen top-3 during execution.

Bounded failure protocol:

1. If any query fails, inspect its actual top-5 with a temporary log or one-off script.
2. Record whether the failure is upstream corpus drift, an apparent ranking regression, or an obsolete query contract.
3. Leave the test failing, stop before Task 4.5, and report a proposed plan amendment to the user. Do not calibrate expectations inside implementation.
4. Task 4 may commit only when the mocked suite has all 35 shared queries green at strict top-1, the live suite has all 44 queries green at top-3, and both live structural tests pass. If that gate is red, Tasks 5–6 do not begin.

### 4.5 Verify and commit

```bash
npx tsc --noEmit
npm test    # expect: ALL files pass, including both golden suites and corpus-validation
            # mocked golden contract: 35 queries at top-1
            # live golden contract: 44 queries at top-3 + 2 structural tests
git add src/loader.ts tests/loader.test.ts tests/golden-query-data.ts tests/golden-queries.test.ts tests/golden-queries.live.test.ts
git commit -m "test(claude-code-docs): run golden queries against the live corpus via the production transform"
```

---

## Task 5: Documentation updates

All in `packages/mcp-servers/claude-code-docs/`.

### 5.1 `CLAUDE.md`

1. Search-parameters table, `category` row: replace `One of 28 categories or 5 aliases (see \`categories.ts\`)` with `One of 29 categories or 6 aliases (see \`categories.ts\`)`.
2. Module map, `categories.ts` row: replace the whole description with:
   `29 canonical categories, URL-to-category mapping (exact segment match, then longest hyphen-bounded prefix — see \`resolveSegmentCategory\`), 6 aliases (\`subagents\`→\`agents\`, \`sub-agents\`→\`agents\`, \`slash-commands\`→\`commands\`, \`claude-md\`→\`memory\`, \`configuration\`→\`config\`, \`gateway\`→\`gateways\`)`
3. Testing table, `golden-queries.test.ts` row: replace description with `Mocked-corpus query coverage (35 shared queries, strict top-1) — deterministic search-quality guard`.
4. Testing table: add a new row directly below it:
   `| \`golden-queries.live.test.ts\` | Runs all 44 shared queries (incl. 9 live-only) against the real cached corpus via the production transform, top-3 category assertion (requires content cache ≤ 7 days old; honors \`CACHE_PATH\`) |`
5. Key Design Patterns, trust-modes bullet: replace `enables full canary evaluation (fallback-segment delta + relative-drift checks)` with `enables full canary evaluation (fallback-segment delta + relative-drift checks + absolute fallback-ratio warn)`.
6. Version-bump policy: replace `bump \`CANARY_VERSION\` in \`canary.ts\`` with `bump \`CANARY_VERSION\` in \`index-cache.ts\``. The constant is exported from `src/index-cache.ts`; copying the old sentence into `AGENTS.md` would create an incorrect always-loaded instruction.
7. Auto-Build section: replace `` `rm -rf dist/` also clears the incremental cache `` with `` `trash dist/` also clears the incremental cache `` before the resync. The package `AGENTS.md` inherits the global no-`rm` safety contract and must not admit conflicting command guidance.

### 5.2 `README.md`

1. Canonical categories list (line 77): insert `` `gateways`, `` after `` `providers`, `` (mirrors `KNOWN_CATEGORIES` order).
2. Aliases line (line 80): append ``, `gateway` -> `gateways` ``.
3. Warning-codes row (line 125): replace the code list with `` `fallback_segment_drift`, `fallback_ratio_high`, `parse_issues`, `section_count_drift`, `stale_corpus` ``.

### 5.3 `AGENTS.md` — full resync

`AGENTS.md` is a stale, strictly-older copy of this package's `CLAUDE.md` (verified by diff before planning: every difference is content `CLAUDE.md` gained after 2026-05-30 — trust/canary/status module rows, `DOCS_TRUST_MODE`, the version-bump policy, unsafe-mode and provenance gotchas, Auto-Build; `AGENTS.md` has no unique content). Piecemeal edits would fix this plan's three stale claims but leave that older drift in place, so resync wholesale, AFTER the 5.1 edits:

**Charter admission decision — ADMIT.** This is a gated ambient-contract change, not an exempt factual copy.

- **Owned work:** package-local operating truth for Codex sessions in `packages/mcp-servers/claude-code-docs/` — commands, architecture, cache behavior, test gates, and version-bump obligations. The closest contract is the existing package `AGENTS.md`, which already owns this job; the sync updates that owner rather than creating a second one. Package `CLAUDE.md` serves a different runtime and does not co-load, so there is no same-runtime owner collision.
- **Observed failure prevented:** the current `AGENTS.md` has already drifted behind the code and `CLAUDE.md`, omitting trust/canary/status behavior and detailed version-bump rules. Always-loaded package context is the lightest surface that reliably prevents a Codex executor from serving a stale index or validating the wrong runtime path; a separate reference would be easier to miss and would duplicate the existing package-contract owner.
- **House fit:** first-party, package-scoped, evidence-oriented, and explicit about commands and proof. Task 5.1 corrects the wrong `CANARY_VERSION` path and the global no-`rm` conflict before admission. No new workflow or routing lane is introduced.

The decision is already present in the canonical charter ledger: `/Users/jp/.agents` commit `fe03db35` (`docs(agents): admit claude-code-docs package contract sync`), with amended-plan commit `a6c4d24a` as its durable evidence pointer. Before changing `AGENTS.md`, verify that exact committed entry is available; do not create or edit any `.agents` artifact during package implementation:

```bash
git -C /Users/jp/.agents show --quiet --oneline fe03db35   # expect: the admission commit
git -C /Users/jp/.agents show fe03db35:docs/agents/contract-decisions.md \
  | rg -F 'claude-code-docs` package `AGENTS.md` resync'   # expect: one matching entry
```

If either check fails, stop before changing `AGENTS.md` and report the missing charter evidence. Once both pass, perform the copy:

```bash
cp CLAUDE.md AGENTS.md
cmp -s CLAUDE.md AGENTS.md   # expect: exit 0
```

### 5.4 Commit

```bash
git add CLAUDE.md README.md AGENTS.md
git commit -m "docs(claude-code-docs): document gateways category, prefix resolver, and ratio canary"
```

The `/Users/jp/.agents` ledger commit is intentionally separate and already exists as `fe03db35`; never stage `.agents` content from this repository or fold it into the package documentation commit.

---

## Task 6: Full verification

```bash
npx tsc --noEmit     # expect: exit 0, no output
npm test             # expect: every file passes; golden-queries.live and corpus-validation
                     # actually run (cache exists), not skip
```

Runtime proof that the cache invalidation works end-to-end (the version bumps must force a rebuild that eliminates the uncategorized bucket):

```bash
# BEFORE any server restart — the stale index still shows the old state:
jq '{ingestion: .compatibility.ingestion, fallback: .diagnostics.fallbackSectionCount, warnings: .evaluation.warnings}' \
  ~/Library/Caches/claude-code-docs/llms-full.index.json
# expect: ingestion 6, fallback 40

# Restart the MCP server (new Claude Code session, or call the reload_docs tool from one),
# then re-run the jq:
# expect: ingestion 7, fallback 0, warnings []
```

If `fallback` is not 0 after rebuild, list the survivors: the live suite's `< 5% uncategorized` test prints the exact URLs in its failure message — fix mappings and re-run.

Done means: both commands green; the mocked golden suite proves exactly 35 queries at strict top-1; the live suite proves exactly 44 queries at top-3 plus both structural tests; the jq post-rebuild output matches; charter admission commit `fe03db35` is verifiable in `/Users/jp/.agents`; and all package commits above exist on `fix/claude-code-docs-corpus-maintenance`. Merging either repository's branch is a separate, user-authorized step.

---

## Self-review and outside-view notes

- **Coverage:** item 1 → Tasks 1–2; item 2 → Task 3; item 3 → Task 4; version bumps → 2.4 and 3.3; doc claims → Task 5. All 40 uncategorized pages accounted for (30 explicit keys, 10 prefix-resolved).
- **Review amendments (2026-07-11):** production-transform reuse → 4.0/4.3; `fallback_ratio_high` round-trip → 3.1/3.3; AGENTS.md resync → 5.3; live-suite corpus contract (`CACHE_PATH` + 7-day age guard) → 4.3. Re-scrutiny correction: the AGENTS.md resync is a gated **ADMIT**, with a canonical-ledger precondition and wrong-path/no-`rm` corrections before copying.
- **Query pre-adjudication proof (2026-07-11):** the final 35 mock + 9 live-only table was run through freshly compiled current parser/loader-equivalent/chunker/BM25 code with the plan's mapping applied. Result: zero mock top-1 failures, zero live top-3 failures, zero uncategorized sections; the four replacement queries each ranked their expected category first in both corpora.
- **Collateral audited before planning:** existing `canary.test.ts` assertions are targeted (`warnings.find/some` by code), so the added ratio warning breaks none; `categories.test.ts` pins size 28 (updated in 1.1); no test hardcodes version literals (all import the constants); `schemas.ts`/`server.test.ts`/`dump-index-metadata.ts` derive category lists dynamically from `KNOWN_CATEGORIES`/`CATEGORY_ALIASES`; `error-messages.ts` contains no category text.
- **Outside view:** reference class is "taxonomy/config change with cache-version bump" in this package (prior art: PR #130 canary replacement, the B12 category expansion). That class reliably requires: the version bump itself, Zod schema sync, status-surface sync, doc-claim updates, and a runtime cache-invalidation proof — each is an explicit task above, because earlier changes of this class in this repo needed exactly those and the spec-level ask ("update categories.ts") names none of them. The class also warns that query-expectation calibration against a live corpus balloons; the re-scrutiny therefore moved calibration out of implementation, pre-adjudicated the known failures, fixed the 44-query table, and made any later failure an immediate stop-and-report gate. This is a debias against the class base rate, not a completeness certificate.
