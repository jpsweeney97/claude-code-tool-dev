# PR #130 Review Follow-ups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Date:** 2026-05-30

**Goal:** Land the actionable findings from the PR #130 adversarial review. PR #130 replaced the `taxonomy_collapse` / `taxonomy_drift` canary with a "fallback-segment delta" canary, changed `deriveCategory`'s unmapped-URL fallback from `'overview'` to `'uncategorized'`, split `MIN_SECTION_COUNT` (config owns the tunable canary INDEX floor; the loader keeps a FIXED `CACHE_WRITE_MIN_SECTIONS = 40` content-cache write guard), and bumped `INDEX_FORMAT_VERSION 4→5`, `CANARY_VERSION 1→2`, `INGESTION_VERSION 5→6`. **All review findings were code-clean** — the runtime behavior is correct. What remains is documentation/evidence-accuracy drift (the docs never followed the rename and the split), two design-decision items where a human must choose between a code fix and a doc correction, and three test-coverage gaps that pin behavior the current suite leaves unproven.

**Source of truth for the corrected vocabulary:**
- `src/status.ts:14` — `StatusWarningCodeSchema = z.enum(['fallback_segment_drift', 'parse_issues', 'section_count_drift', 'stale_corpus'])`.
- `packages/mcp-servers/claude-code-docs/CLAUDE.md` — already carries the corrected `MIN_SECTION_COUNT` split row and the "fallback-segment delta + relative-drift checks" canary phrasing; AGENTS.md and README must be brought to match.

**Tech Stack:** TypeScript, Node.js (≥18), Vitest, Zod, MCP stdio transport. All commands run from `packages/mcp-servers/claude-code-docs/` unless a path is shown relative to the repo root (the B-prime plan and this plan live at the repo root under `docs/superpowers/plans/`).

**Predecessor plan:** `docs/superpowers/plans/2026-05-28-claude-code-docs-b-prime-recovery.md` (the PR #130 work). Task 3.1 of that plan handled the canonical-count doc sites (`AGENTS.md:11/:47`, `CLAUDE.md:11/:47`, `categories.ts:5`); this plan does NOT re-touch those. Task A7 here revisits one specific freeze decision that plan made (its line ~511 golden-queries "26 categories" freeze).

---

## Findings → Tasks Traceability

| Severity | Finding | Task |
|---|---|---|
| medium | README `get_status` `warning_codes` lists removed `taxonomy_drift` instead of `fallback_segment_drift` | A1 |
| medium | README official trust-mode describes canary as "taxonomy + relative-drift checks" | A2 |
| medium | README `MIN_SECTION_COUNT` env row uses pre-split single-meaning semantics | A3 |
| medium | README canonical-categories list omits `agent-sdk` (pre-existing drift) and `uncategorized` (PR #130) | A4 |
| medium | AGENTS.md `MIN_SECTION_COUNT` env row stale (PR #130 updated CLAUDE.md but not AGENTS.md) | A5 |
| low | `frontmatter.ts` `getUnmappedSegments` docstring still says fallback `'overview'` instead of `'uncategorized'` | A6 |
| nit | Golden-queries doc rows say "26 categories" but distinct `expectedTopCategory` count is 27; B-prime froze 26 on a false rationale | **A7 (DECISION)** |
| medium | PR #130 body: live-boot "warnings []" contradicts first-run warn behavior, and "572 passed" is stale | **A8 (DECISION — external GitHub action)** |
| low | Document the AND-semantics positive-baseline FAIL gate with an H1 escape-hatch pointer | B1 |
| low | Trust-mode flip is not a cache miss with `MIN_SECTION_COUNT` unset — fix predicate vs correct CLAUDE.md gotcha | **B2 (DECISION)** |
| low | `fallbackSectionCount` (pre-filter) and `fallbackSegmentCount`/`unmappedSegments` (post-filter) count over different populations | **B3 (DECISION)** |
| low | Add sequenced freeze-then-accumulate FAIL test to canary `fallback_segment_collapse` suite | C1 |
| low | Make `unmappedSegments` ordering assertion unconditional with a known-category pad base | C2 |
| nit | Add FAIL-boundary multiplier-units test isolating `1 + FAIL_REL = 3.0` | C3 |
| nit | Add e2e category-filter test for literal `'uncategorized'` category | C4 |

---

## Commit Plan

Tasks group into commits by concern, ordered docs → decisions → tests (lowest risk first):

1. **Commit 1 — Docs reconciliation** (A1, A2, A3, A4, A5, A6, A7-docs): README + AGENTS.md + `frontmatter.ts` docstring + golden-queries count. Pure documentation/comment changes; no runtime behavior touched.
2. **Decisions — B2, B3** (and the cross-cutting A7 / A8 decisions): each is a DECISION with a RECOMMENDED option and the alternative. A maintainer chooses before the edit lands. Once chosen, the chosen-option text becomes a commit in its own right.
3. **Commit (tests) — C1, C2, C3, C4**: new/strengthened tests; no source behavior change.

A8 is an **external GitHub PR-body edit**, not branch work — see its task and the Verification Gate note.

---

## Commit 1 — Docs Reconciliation

### Task A1 — README `warning_codes` → match `status.ts` enum

**Severity:** medium

**Files:**
- `packages/mcp-servers/claude-code-docs/README.md` (the `get_status` return-shape table, line ~125)

**Rationale:** README still advertises the pre-PR#130 enum. Source of truth is `status.ts:14` `StatusWarningCodeSchema = z.enum(['fallback_segment_drift', 'parse_issues', 'section_count_drift', 'stale_corpus'])`. PR #130 renamed `taxonomy_drift → fallback_segment_drift`; README never followed. The new code must appear and the removed code must be gone (not merely supplemented). Order already matches the enum once the first entry is swapped.

**Steps:**
- [ ] Replace, in `README.md`:

  OLD:
  ```
  | `warning_codes` | string[] | Active warning codes: `taxonomy_drift`, `parse_issues`, `section_count_drift`, `stale_corpus`. |
  ```
  NEW:
  ```
  | `warning_codes` | string[] | Active warning codes: `fallback_segment_drift`, `parse_issues`, `section_count_drift`, `stale_corpus`. |
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && ! grep -q 'taxonomy_drift' README.md && grep -q 'fallback_segment_drift`, `parse_issues`, `section_count_drift`, `stale_corpus' README.md && echo OK
```

**Commit message:** `docs(claude-code-docs): fix README get_status warning_codes to match status.ts enum (A1)`

---

### Task A2 — README official trust-mode canary name → fallback-segment delta

**Severity:** medium

**Files:**
- `packages/mcp-servers/claude-code-docs/README.md` (the `DOCS_TRUST_MODE` env row, line ~42)

**Rationale:** README names the old "taxonomy" canary. PR #130 replaced the `taxonomy_collapse`/`taxonomy_drift` canary with a fallback-segment delta canary. The package CLAUDE.md Key Design Patterns row already uses the corrected phrasing ("full canary evaluation (fallback-segment delta + relative-drift checks)"). Mirror it. Only the parenthetical changes; the structural-canary half (count + size) is unchanged.

**Steps:**
- [ ] Replace, in `README.md`:

  OLD:
  ```
  | `DOCS_TRUST_MODE` | `official` | Trust mode controlling source validation and canary policy. | `official`: pins source to `code.claude.com`, full canary evaluation (taxonomy + relative-drift checks). `unsafe`: accepts any HTTPS URL, structural canaries only (count + size checks). Use `unsafe` only for local testing or private mirrors. |
  ```
  NEW:
  ```
  | `DOCS_TRUST_MODE` | `official` | Trust mode controlling source validation and canary policy. | `official`: pins source to `code.claude.com`, full canary evaluation (fallback-segment delta + relative-drift checks). `unsafe`: accepts any HTTPS URL, structural canaries only (count + size checks). Use `unsafe` only for local testing or private mirrors. |
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && grep -n 'fallback-segment delta + relative-drift checks' README.md && ! grep -q 'taxonomy + relative-drift' README.md && echo OK
```

**Commit message:** `docs(claude-code-docs): rename README official-mode canary to fallback-segment delta (A2)`

---

### Task A3 — README `MIN_SECTION_COUNT` row → canary-floor/cache-guard split

**Severity:** medium

**Files:**
- `packages/mcp-servers/claude-code-docs/README.md` (the `MIN_SECTION_COUNT` env row, line ~46)

**Rationale:** PR #130 split `MIN_SECTION_COUNT`: config now owns the tunable canary INDEX floor (default unset → official 40 / unsafe 3), while the loader keeps a FIXED `CACHE_WRITE_MIN_SECTIONS = 40` content-cache write guard that env cannot disable. README still documents the old conflated meaning (default 40, "0 disables validation"). Mirror `packages/mcp-servers/claude-code-docs/CLAUDE.md` (the `MIN_SECTION_COUNT` env row), which already carries the corrected split. README's 4-column table format (Variable | Default | Purpose | Constraints/Behavior) is preserved; the default cell becomes "(unset)" and the constraints cell carries the trust-mode defaults plus the fixed-guard caveat.

**Steps:**
- [ ] Replace, in `README.md`:

  OLD:
  ```
  | `MIN_SECTION_COUNT` | `40` | Minimum parsed sections required to accept fetched content. | Integer >=0. `0` disables validation. If below the minimum, fetch is rejected and stale cache may be used. |
  ```
  NEW:
  ```
  | `MIN_SECTION_COUNT` | (unset) | Override for the canary's index floor. | Integer >=0. Unset → canary uses its trust-mode default (official: 40, unsafe: 3). `0` disables the index floor. Does NOT affect the content-cache write guard, which is fixed at 40 (`CACHE_WRITE_MIN_SECTIONS`) and is NOT env-disableable. |
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && grep -n 'canary' README.md | grep -i 'index floor' && grep -n 'CACHE_WRITE_MIN_SECTIONS' README.md && echo OK
```

**Commit message:** `docs(claude-code-docs): rewrite README MIN_SECTION_COUNT row for canary-floor/cache-guard split (A3)`

---

### Task A4 — README canonical-categories list → add `agent-sdk` + `uncategorized`

**Severity:** medium

**Files:**
- `packages/mcp-servers/claude-code-docs/README.md` (the "Canonical categories:" list, line ~77)

**Rationale:** `categories.ts` `KNOWN_CATEGORIES` has 28 entries. The README list has only 26 — missing `agent-sdk` (pre-existing drift; present in source between `automation` and `desktop`) and `uncategorized` (added by PR #130 as the `deriveCategory` fallback, last entry in the Set). The newText inserts `agent-sdk` after `automation` and appends `uncategorized` last, mirroring the source ordering in `categories.ts`, yielding 28 items.

> **Count-reconciliation scope note:** README has NO "N categories" count line (verified: `grep -nE '[0-9]+ categor' README.md` returns no matches and there is no module-map row), so there is nothing in README to renumber — the only README edit is the list itself. The 28-count doc sites live in `AGENTS.md:11/:47` and `CLAUDE.md:11/:47` and were already handled by the B-prime plan Task 3.1; they are out of this packet's README scope.

**Steps:**
- [ ] Replace, in `README.md`:

  OLD:
  ```
  Canonical categories:
  `hooks`, `skills`, `commands`, `agents`, `plugins`, `plugin-marketplaces`, `mcp`, `channels`, `settings`, `memory`, `overview`, `getting-started`, `cli`, `best-practices`, `interactive`, `security`, `providers`, `ide`, `ci-cd`, `automation`, `desktop`, `integrations`, `config`, `operations`, `troubleshooting`, `changelog`
  ```
  NEW:
  ```
  Canonical categories:
  `hooks`, `skills`, `commands`, `agents`, `plugins`, `plugin-marketplaces`, `mcp`, `channels`, `settings`, `memory`, `overview`, `getting-started`, `cli`, `best-practices`, `interactive`, `security`, `providers`, `ide`, `ci-cd`, `automation`, `agent-sdk`, `desktop`, `integrations`, `config`, `operations`, `troubleshooting`, `changelog`, `uncategorized`
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && grep -q '`agent-sdk`' README.md && grep -q '`uncategorized`' README.md && echo OK
```

**Commit message:** `docs(claude-code-docs): add agent-sdk and uncategorized to README canonical-categories list (A4)`

---

### Task A5 — AGENTS.md `MIN_SECTION_COUNT` row → sync with CLAUDE.md split semantics

**Severity:** medium

**Files:**
- `packages/mcp-servers/claude-code-docs/AGENTS.md` (the `MIN_SECTION_COUNT` env row, line ~100)

**Rationale:** AGENTS.md still documents the old conflated `MIN_SECTION_COUNT` meaning (default 40, "Set to 0 to disable"). PR #130 updated the equivalent CLAUDE.md row but not AGENTS.md. Mirror the CLAUDE.md `MIN_SECTION_COUNT` row's combined Purpose-cell text. AGENTS.md's env table is 3-column (Variable | Default | Purpose) vs CLAUDE.md's 4-column, but CLAUDE.md also uses a single combined Purpose cell, so the same cell text transfers directly into AGENTS.md's Purpose column.

**Steps:**
- [ ] Replace, in `AGENTS.md`:

  OLD:
  ```
  | `MIN_SECTION_COUNT` | `40` | Minimum sections in fetched content. Rejects truncated docs. Set to `0` to disable. |
  ```
  NEW:
  ```
  | `MIN_SECTION_COUNT` | (unset) | Override for the canary's index floor. Unset → canary uses its trust-mode default (official: 40, unsafe: 3). Set to `0` to disable the index floor. Does NOT affect the content-cache write guard, which is fixed at 40 (`CACHE_WRITE_MIN_SECTIONS`). |
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && diff <(grep '| `MIN_SECTION_COUNT`' CLAUDE.md) <(grep '| `MIN_SECTION_COUNT`' AGENTS.md) && echo IDENTICAL
```

**Commit message:** `docs(claude-code-docs): sync AGENTS.md MIN_SECTION_COUNT row with CLAUDE.md split semantics (A5)`

---

### Task A6 — `frontmatter.ts` `getUnmappedSegments` docstring → fallback `'uncategorized'`

**Severity:** low

**Files:**
- `packages/mcp-servers/claude-code-docs/src/frontmatter.ts` (the `getUnmappedSegments` docstring, line ~213)

**Rationale:** PR #130 changed `deriveCategory`'s unmapped-URL fallback from `'overview'` to `'uncategorized'` (`frontmatter.ts:196` now returns `'uncategorized'`). The `getUnmappedSegments` docstring still narrates the old fallback target, contradicting the code two functions above it. Only the single word changes; the rest of the docstring is accurate. This is a comment-only change in a `.ts` file (the comment is the load-bearing text, not code).

**Steps:**
- [ ] Replace, in `src/frontmatter.ts`:

  OLD:
  ```
   * Returns non-empty only when NO segment maps, meaning deriveCategory would
   * fall back to 'overview'. Uses Object.hasOwn to avoid prototype-chain
   * false positives. Pure function — no side effects.
  ```
  NEW:
  ```
   * Returns non-empty only when NO segment maps, meaning deriveCategory would
   * fall back to 'uncategorized'. Uses Object.hasOwn to avoid prototype-chain
   * false positives. Pure function — no side effects.
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && sed -n '212,214p' src/frontmatter.ts | grep -q "fall back to 'uncategorized'" && ! grep -n "fall back to 'overview'" src/frontmatter.ts && echo OK
```

**Commit message:** `docs(claude-code-docs): correct getUnmappedSegments docstring fallback to 'uncategorized' (A6)`

---

### Task A7 — Golden-queries coverage count: "26" → "27" (DECISION)

**Severity:** nit

> **DECISION — RESOLVED 2026-05-30 (owner-confirmed).** The override (26 → 27) is confirmed by the repo owner. Verified semantic: `KNOWN_CATEGORIES` = 28; golden queries exercise 27 — all canonical categories except the synthetic `uncategorized` fallback (which correctly has no query). The prior "26 / changelog has none" rationale was empirically false (changelog AND agent-sdk are both exercised). Applied + pushed to PR #130.

**Files:**
- `packages/mcp-servers/claude-code-docs/AGENTS.md` (golden-queries row, line ~86)
- `packages/mcp-servers/claude-code-docs/CLAUDE.md` (golden-queries row, line ~93)
- `docs/superpowers/plans/2026-05-28-claude-code-docs-b-prime-recovery.md` (freeze note, line ~511)

**The disagreement and the evidence (verified at HEAD):**
- `tests/golden-queries.test.ts` has 35 query rows (`grep -c 'expectedTopCategory:'` = 35) covering **27 DISTINCT** `expectedTopCategory` values (`grep -o "expectedTopCategory: '[^']*'" | sort -u | wc -l` = 27): `agent-sdk, agents, automation, best-practices, changelog, channels, ci-cd, cli, commands, config, desktop, getting-started, hooks, ide, integrations, interactive, mcp, memory, operations, overview, plugin-marketplaces, plugins, providers, security, settings, skills, troubleshooting`.
- The B-prime plan (line ~511) deliberately FROZE this at 26 as a "coverage count" with the rationale "golden queries exercise 26 canonical categories; `changelog` has none" — but that rationale is **factually wrong**: `golden-queries.test.ts` contains a row `{ query: 'changelog release version history fixes', expectedTopCategory: 'changelog' }`, so `changelog` IS exercised, and `agent-sdk` is also exercised. The true coverage is 27, not 26.

**RECOMMENDED — set both rows to 27 and fix the plan note.** A frozen-on-false-rationale value is still wrong.

- [ ] In `AGENTS.md` and `CLAUDE.md`, change both rows:

  OLD (identical in both files):
  ```
  | `golden-queries.test.ts` | Multi-category query coverage (35 queries, 26 categories) — validates search quality |
  ```
  NEW (identical in both files):
  ```
  | `golden-queries.test.ts` | Multi-category query coverage (35 queries, 27 categories) — validates search quality |
  ```

- [ ] In `docs/superpowers/plans/2026-05-28-claude-code-docs-b-prime-recovery.md` (line ~511), correct or strike the freeze note so a future maintainer does not re-freeze 26 against the same false "changelog has none" premise. The note currently reads in part: "Leave the golden-queries rows … unchanged — that 26 is a coverage count (golden queries exercise 26 canonical categories; changelog has none)". Replace that justification with a statement that the live distinct-`expectedTopCategory` count is 27 (changelog AND agent-sdk are both exercised), corrected by the 2026-05-30 PR #130 review follow-up (Task A7).

**ALTERNATIVE — leave 26 frozen.** Only valid if a maintainer decides the doc rows should track a definition of "coverage" other than distinct `expectedTopCategory` count. No basis for this was found; the false "changelog has none" premise should be corrected regardless.

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && test "$(grep -o "expectedTopCategory: '[^']*'" tests/golden-queries.test.ts | sort -u | wc -l | tr -d ' ')" = 27 && grep -c '27 categories' AGENTS.md CLAUDE.md
```

**Commit message:** `docs(claude-code-docs): correct golden-queries coverage count to 27 and fix B-prime freeze rationale (A7)`

---

### Task A8 — PR #130 body corrections (DECISION — EXTERNAL GitHub action, NOT branch work)

**Severity:** medium

> **DECISION + EXTERNAL ACTION.** Editing a GitHub PR body is an External/Published action. This plan specifies the corrected wording and the commands that produce the evidence; the edit itself must be performed by a human on GitHub. There is no repo commit for A8.

**Files:**
- PR #130 body on GitHub (external; do not edit from this repo).

**Two factual claims in the PR body that the code at HEAD contradicts:**

1. **"warnings []" (empty) on the isolated live boot.** This is inconsistent with the first-run warn path. `canary.ts:304-320` emits a `fallback_segment_drift` warn when `trustMode === 'official' && baselineFallback === null && fallbackSectionCount >= FALLBACK_DELTA_WARN_ABS`, and `FALLBACK_DELTA_WARN_ABS = 5` (`canary.ts:22`). A genuine first boot against the live ~25-fallback corpus has a null baseline and ≥5 fallback sections, so it MUST emit `fallback_segment_drift` — i.e. warnings cannot be `[]`. (This is the explicit P1 fix landed in `6b1625f6` "warn and establish baseline on first canary run"; a clean cold boot should warn, not stay silent.)
2. **"572 passed" is stale** relative to HEAD (`8dbb0c4`). Do not re-derive the number statically — a grep of `it()`/`test()` literals undercounts because some cases are loop-generated, so it will not match the runtime total.

**Remediation — COMPLETED 2026-05-30 (empirical, GitHub body edited).**

Isolated live boots (fresh `XDG_CACHE_HOME`, 142-section corpus) captured the exact `get_status` output:

| Boot | Path | `source_kind` | `get_status.warning_codes` |
|---|---|---|---|
| A — cold first run (empty cache) | rebuild | `fetched` | `["fallback_segment_drift"]` |
| B — warm reboot, same corpus | provenance-refresh (full-hit class) | `cached` | `["fallback_segment_drift"]` (replayed) |
| C — re-eval vs established baseline (`MIN_SECTION_COUNT=40` → canary replay) | replay | `cached` | `[]` |

Boot A: `decision: accept`, `sectionCount: 142`, `fallbackSectionCount: 25`, baseline established at 25.

**Correction to the original derivation:** the first-run warn is **persisted into the cached evaluation block and replayed on every full-hit / provenance-refresh reboot** (Boot B) — it does NOT clear by simply rebooting on the same corpus. It clears (`[]`) only when the canary **re-evaluates** against the established baseline of 25 (Boot C: delta 0 → no warn), i.e. on a canary replay or a corpus-change rebuild. So `warning_codes: []` is not the first-run state; `["fallback_segment_drift"]` is, by design.

Applied to the PR #130 body (`gh pr edit 130`): the "warnings `[]`" live-boot bullet was replaced with the empirical wording above, and the test count `572 → 581` (the follow-up commits A1–A7/B1–B3/C1–C4 added 5 tests; they were pushed into this PR's branch).

**Commit message:** n/a — the GitHub PR-body edit produces no repo commit; this plan note records that it was done.

---

## Decisions — B2, B3 (and cross-cutting A7/A8 above)

These are DECISIONS: each presents a RECOMMENDED option and the alternative. A maintainer chooses before the edit lands. B1 is included in this section's lead-in for context but is NOT a decision — the B-prime plan already adjudicated it (H1); B1 only adds the documenting comment.

### Task B1 — Document the AND-semantics positive-baseline FAIL gate (not a decision)

**Severity:** low

**Files:**
- `packages/mcp-servers/claude-code-docs/src/canary.ts` (above the positive-baseline FAIL `if`, line ~220)

**Rationale:** The positive-baseline FAIL requires BOTH `fallbackSectionDelta >= FALLBACK_DELTA_FAIL_ABS` (20) AND `fallbackSectionMultiplier >= 1 + FALLBACK_DELTA_FAIL_REL` (3.0). A large-absolute-but-<3x regression (baseline 30→55 = +25, 1.8x) trips the WARN gate (≥5 AND ≥1.5x) but not FAIL, so the degraded index is served. The B-prime plan H1 (the Phase 4 "Design risk (H1 …)" block, line ~657) explicitly resolves this to (a) accept-on-warn-freeze with (b) advance-on-warn as the documented escape hatch, and (c) static-ratio gating REJECTED as the original `taxonomy_collapse` fragility class. A hard-absolute FAIL branch would reintroduce exactly the benign-growth rejection risk H1 was designed to avoid; the inline comment costs nothing and pins future readers to the H1 rationale. `decisionNeeded` is false because the plan already adjudicated this; the spec only adds the documenting comment.

**Steps:**
- [ ] Replace, in `src/canary.ts` (prepend the comment block immediately above the existing positive-baseline FAIL `if`):

  OLD:
  ```
    if (
      trustMode === 'official' &&
      fallbackSectionDelta !== null &&
      fallbackSectionMultiplier !== null &&
      fallbackSectionDelta >= FALLBACK_DELTA_FAIL_ABS &&
      fallbackSectionMultiplier >= 1 + FALLBACK_DELTA_FAIL_REL
    ) {
      return reject('fallback_segment_collapse',
  ```
  NEW:
  ```
    // Positive-baseline FAIL is AND-semantics (delta >= FAIL_ABS AND multiplier >= 1 + FAIL_REL),
    // so a large-absolute-but-sub-3x regression (e.g. baseline 30 -> 55: +25 sections but only 1.8x)
    // only WARNs and serves the degraded index. This is intentional movement-gating, not a static
    // share threshold (the original taxonomy_collapse fragility class). Accepted under the
    // B-prime plan H1 rationale: a hard-absolute FAIL branch would reintroduce benign-growth
    // rejection. If post-WARN growth becomes routine, take H1 escape hatch (b) — flip the
    // advancement ternaries to advance-on-warn and bump CANARY_VERSION. See
    // docs/superpowers/plans/2026-05-28-claude-code-docs-b-prime-recovery.md (H1).
    if (
      trustMode === 'official' &&
      fallbackSectionDelta !== null &&
      fallbackSectionMultiplier !== null &&
      fallbackSectionDelta >= FALLBACK_DELTA_FAIL_ABS &&
      fallbackSectionMultiplier >= 1 + FALLBACK_DELTA_FAIL_REL
    ) {
      return reject('fallback_segment_collapse',
  ```

**Verification:**
```bash
rg -n "H1 rationale" packages/mcp-servers/claude-code-docs/src/canary.ts && cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit && npm test
```

**Commit message:** `docs(claude-code-docs): pin fallback FAIL gate AND-semantics to H1 rationale (B1)`

---

### Task B2 — Trust-mode flip is not a cache miss with `MIN_SECTION_COUNT` unset (DECISION)

**Severity:** low

> **DECISION — RESOLVED 2026-05-30.** Option (i) chosen and implemented (commit `7d5b8f4e`): a `policyMatch` conjunct was added to the cache-hit predicate so a trust-mode/`docsUrl` change forces a rebuild. Field paths verified (`ServerState.trustMode`/`docsUrl`; `corpus.trustMode`/`docsUrl` persisted + schema-validated). TDD: regression tests failed pre-fix, pass post-fix. Pushed to PR #130.

**Files:**
- `packages/mcp-servers/claude-code-docs/src/lifecycle.ts` (the `contentMatch` / `minSectionCountMatch` block, lines ~210-214)
- `packages/mcp-servers/claude-code-docs/CLAUDE.md` (the "Provenance refresh triggers a full rebuild" gotcha)

**Investigation (verified at HEAD):** `lifecycle.ts:213-214` `minSectionCountMatch` compares the RAW env override (`this.minSectionCount`), which is undefined in BOTH official and unsafe when `MIN_SECTION_COUNT` is unset; the trust-mode floor default (OFFICIAL=40 / UNSAFE=3) is resolved INSIDE the canary, never baked into `this.minSectionCount`. The cache stores `evaluation.minSectionCount` as `this.minSectionCount ?? null` = null in both modes. So `minSectionCountMatch` is `null === null` = true, `contentMatch` is true for an identical corpus, `canaryVersion` matches → `canaryMatch` true → Path 1 full hit (`lifecycle.ts:227`), reusing the cached decision WITHOUT re-evaluation. No other part of the load predicate forces a rebuild on trust-mode change: `compatMatch` reads only version constants; `cachedProvenance` extracts only `sourceKind`+`obtainedAt`; `isProvenanceBetter` compares only `sourceKind` rank. `corpus.trustMode` and `corpus.docsUrl` are persisted by `index-cache.ts` but read by NOTHING in the predicate. The CLAUDE.md gotcha "Provenance refresh triggers a full rebuild … when DOCS_TRUST_MODE or DOCS_URL changes" therefore OVERCLAIMS.

#### Option (i) — RECOMMENDED: make the documented behavior real

Add a policy-equality gate so a trust-mode (or `docsUrl`) flip forces re-evaluation. No version-constant bump needed: `corpus.trustMode` and `corpus.docsUrl` are already persisted and schema-validated; a mismatch routes through the existing Path 3 rebuild.

- [ ] Replace, in `src/lifecycle.ts`:

  OLD:
  ```
        const contentMatch = compatMatch && parsed!.corpus?.contentHash === contentHash;
        // A changed effective floor must re-evaluate rather than reuse the cached accept (P2):
        // the canary decision depends on minSectionCount, so it is part of cache compatibility.
        const minSectionCountMatch =
          (parsed?.evaluation?.minSectionCount ?? null) === (this.minSectionCount ?? null);
  ```
  NEW:
  ```
        // A trust-mode or source-URL change alters which canaries run (official runs the
        // fallback-segment + relative-drift checks; unsafe runs none) and which floor default
        // applies, so a cached accept from one policy must not be reused under another even when
        // the corpus bytes match. Treat a policy change as a cache miss (forces rebuild).
        const policyMatch =
          parsed?.corpus?.trustMode === this.trustMode &&
          parsed?.corpus?.docsUrl === this.docsUrl;
        const contentMatch =
          compatMatch && policyMatch && parsed!.corpus?.contentHash === contentHash;
        // A changed effective floor must re-evaluate rather than reuse the cached accept (P2):
        // the canary decision depends on minSectionCount, so it is part of cache compatibility.
        const minSectionCountMatch =
          (parsed?.evaluation?.minSectionCount ?? null) === (this.minSectionCount ?? null);
  ```
- [ ] Add a regression test in `tests/lifecycle.test.ts` asserting a cached official-mode accept is NOT served as a full hit when the `ServerState` trustMode is `'unsafe'` (and vice versa) with identical `contentHash` and `MIN_SECTION_COUNT` unset.

> **Pre-edit check:** confirm `this.trustMode` and `this.docsUrl` exist on `ServerState` (and `parsed.corpus.trustMode` / `parsed.corpus.docsUrl` exist on the parsed schema) at the edit site; if the field names differ, use the real names. The packet asserts these are persisted at `index-cache.ts` corpus block — verify before relying on the exact property path.

#### Option (ii) — ALTERNATIVE: leave code as-is, correct the CLAUDE.md gotcha

- [ ] Replace, in `packages/mcp-servers/claude-code-docs/CLAUDE.md`:

  OLD:
  ```
  - **Provenance refresh triggers a full rebuild**: When `DOCS_TRUST_MODE` or `DOCS_URL` changes between runs, the cached index is invalidated even if all version constants match — the policy change is a cache miss by design.
  ```
  NEW:
  ```
  - **Trust-mode / source-URL change is NOT a cache miss**: The cache compatibility predicate (`lifecycle.ts`) keys only on version constants, `corpus.contentHash`, `CANARY_VERSION`, and the effective `minSectionCount` floor — not on `corpus.trustMode` or `corpus.docsUrl`. With `MIN_SECTION_COUNT` unset, a trust-mode flip (official 40 ↔ unsafe 3) over an identical corpus reuses the prior accept as a full hit, because the trust-mode floor default is applied inside the canary, not baked into the cached `minSectionCount` (which is `null` in both modes). The canary is re-run only when the content hash changes or a version constant / explicit floor differs.
  ```

**Why (i) is recommended:** the gotcha asserts a trust-boundary safety property (policy change = cache miss), and the gap is a real correctness hole — an unsafe-mode accept (which never ran the fallback-segment canary) being served under official trust without re-evaluation. Fixing the code makes the documented safety property true at negligible cost.

**Verification:**
```bash
# Option (i):
rg -n "policyMatch" packages/mcp-servers/claude-code-docs/src/lifecycle.ts && cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit && npm test -- lifecycle
# Option (ii):
rg -n "Trust-mode / source-URL change is NOT a cache miss" packages/mcp-servers/claude-code-docs/CLAUDE.md
```

**Commit message (Option i):** `fix(claude-code-docs): treat trust-mode/docsUrl change as a cache miss (B2)`
**Commit message (Option ii):** `docs(claude-code-docs): correct CLAUDE.md gotcha — trust-mode flip is not a cache miss (B2)`

---

### Task B3 — Pre/post-filter fallback-count population asymmetry (DECISION)

**Severity:** low

> **DECISION — RESOLVED 2026-05-30.** Option (B) chosen and implemented (commit `a22ef08b`): an inline comment documents the intentional pre-filter (gate input) vs post-filter (observability) population asymmetry; no gate-input change, no `INGESTION_VERSION` bump. Pushed to PR #130.

**Files:**
- `packages/mcp-servers/claude-code-docs/src/loader.ts` (the `fallbackSectionCount` computation + its comment, lines ~126-131)

**Investigation (verified at HEAD):** `loader.ts:128-131` computes `fallbackSectionCount` over the PRE-filter `sections` array (same array as `sectionCount = sections.length` at `loader.ts:168`, which the canary thresholds compare against). The unmapped Map that backs `fallbackSegmentCount` (= `sortedUnmapped.length`, `loader.ts:170`) and `unmappedSegments` (`loader.ts:171`) is built by iterating `filtered` (`loader.ts:142`) — the POST-filter non-empty-content set — and additionally skips sections with empty `sourceUrl` (`loader.ts:143`). So the two diagnostics count over different populations. CONFIRMED no gate impact: the canary reads `fallbackSectionCount` only (for the floor and FAIL gates; the WARN at `canary.ts:256-262` keys on `fallbackSectionDelta` derived from `fallbackSectionCount`); `fallbackSegmentCount`/`unmappedSegments` are stored for observability and surfaced in `reject()` details but never gated.

#### Option (B) — RECOMMENDED: document the intentional asymmetry

- [ ] Replace, in `src/loader.ts`:

  OLD:
  ```
    // Count fallback sections (sections where deriveCategory returns 'uncategorized' —
    // i.e. no URL segment was mapped). This is what the fallback-delta canary watches.
    const fallbackSectionCount = sections.filter(s => {
      const sourceKey = s.sourceUrl || s.title || '';
      return deriveCategory(sourceKey) === 'uncategorized';
    }).length;
  ```
  NEW:
  ```
    // Count fallback sections (sections where deriveCategory returns 'uncategorized' —
    // i.e. no URL segment was mapped). This is what the fallback-delta canary watches.
    //
    // NOTE — intentional population asymmetry: fallbackSectionCount is computed over the
    // PRE-filter `sections` array (matching sectionCount = sections.length, the value the
    // canary thresholds compare against), whereas fallbackSegmentCount / unmappedSegments
    // below are derived from the POST-filter `filtered` set (and skip empty-sourceUrl
    // preamble). The two are observability diagnostics over different populations; the
    // canary gates (fallback_segment_collapse FAIL, fallback_segment_drift WARN) read
    // fallbackSectionCount ONLY, so the asymmetry has no gate impact. Keep the gate input
    // on the same pre-filter basis as sectionCount.
    const fallbackSectionCount = sections.filter(s => {
      const sourceKey = s.sourceUrl || s.title || '';
      return deriveCategory(sourceKey) === 'uncategorized';
    }).length;
  ```

#### Option (A) — ALTERNATIVE: unify both over the same `filtered` set

Change `sections.filter(...)` to `filtered.filter(...)`. **REJECTED as default:** it changes the canary GATE input (`fallbackSectionCount` feeds FAIL/WARN) to a different population than the `sectionCount` it is reasoned about alongside, and would alter the persisted diagnostic across the existing cache — a behavior change to a gate for cosmetic symmetry. If chosen, bump `INGESTION_VERSION` (diagnostic computation changed) per the CLAUDE.md version-bump policy.

**Verification:**
```bash
rg -n "intentional population asymmetry" packages/mcp-servers/claude-code-docs/src/loader.ts && cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit && npm test -- loader
```

**Commit message:** `docs(claude-code-docs): document pre/post-filter fallback-count asymmetry (B3)`

---

## Tests — C1, C2, C3, C4

### Task C1 — Sequenced freeze-then-accumulate FAIL test

**Severity:** low

**Files:**
- `packages/mcp-servers/claude-code-docs/tests/canary.test.ts` (append inside the `fallback_segment_collapse` describe, after the "zero baseline, FAIL_ABS reached" test, line ~541)

**Rationale:** The `fallback_segment_collapse` suite proves single-shot reject and single-shot warn but never proves the multi-load freeze-then-accumulate path: that a WARN freezes `lastHealthyFallbackSectionCount` (`canary.ts:351-356`) and that a subsequent load is evaluated against the FROZEN value, allowing gradual drift to eventually cross FAIL. Without this, the freeze logic could regress (e.g. advancing the baseline on a warn) and only this sequenced test would catch it. Numbers verified against canary.ts gates: WARN needs delta≥5 && mult≥1.5; FAIL needs delta≥20 && mult≥3.0. Baseline 6→12 warns+freezes; frozen 6→30 fails (delta 24, mult 5.0). The counter-factual (advanced baseline 12→30 = delta 18 < 20, no fail) makes the freeze load-bearing.

**Steps:**
- [ ] Replace, in `tests/canary.test.ts` (the closing `});` shown is the end of the `fallback_segment_collapse` describe block immediately after the "zero baseline, FAIL_ABS reached" test):

  OLD:
  ```
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
  NEW:
  ```
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
  ```

> **Pre-edit check:** confirm the result object exposes `nextPolicyState` with `lastHealthyFallbackSectionCount` / `lastHealthyFallbackObservedAt` under those exact names. If the freeze field names differ from the packet's assumption, align the assertions to the real field names before committing.

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && npx vitest run tests/canary.test.ts -t 'freeze-then-accumulate'
```

**Commit message:**
```
test(claude-code-docs): cover sequenced freeze-then-accumulate fallback FAIL (C1)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

---

### Task C2 — Make `unmappedSegments` ordering assertion unconditional

**Severity:** low

**Files:**
- `packages/mcp-servers/claude-code-docs/tests/loader.test.ts` (the "returns unmappedSegments sorted by count desc then name asc" test, line ~840)

**Rationale:** The current test pads with the DEFAULT base `https://code.claude.com/docs/en/pad`, whose first segment `pad` is unmapped in `SECTION_TO_CATEGORY`, so the 37 padding sections inject a third unmapped segment (`pad`) with count 37. That defeats the intended assertion: the two target segments are not even at the top of the ordering, and the test had to weaken to a guarded count-desc-only check. Switching the pad base to the known-category `https://code.claude.com/docs/en/hooks/pad` (the same base the adjacent "counts fallback sections correctly" test at `loader.test.ts:827` already uses) keeps padding mapped to `hooks`, leaving exactly the two intended unmapped segments so `segs[0] === ['zzz-unknown', 2]` and `segs[1] === ['aaa-unknown', 1]` hold unconditionally. The signature `buildLargeMockContent(primarySections, padTo = 40, padUrlBase)` (`loader.test.ts:14-18`) supports the third arg.

**Steps:**
- [ ] Replace, in `tests/loader.test.ts`:

  OLD:
  ```
    it('returns unmappedSegments sorted by count desc then name asc', async () => {
      // Build content where multiple sections have unmapped URLs
      // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
      const content = buildLargeMockContent([
        { title: 'A', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'A' },
        { title: 'B', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'B' },
        { title: 'C', url: 'https://code.claude.com/docs/en/aaa-unknown', body: 'C' },
      ]);

      vi.stubGlobal('fetch', mockFetchOk(content));

      const { loadFromOfficial } = await import('../src/loader.js');
      const cachePath = path.join(tempDir, 'cache.txt');
      const result = await loadFromOfficial('https://example.com/docs', cachePath);

      const segs = result.diagnostics.unmappedSegments;
      // zzz-unknown appears 2x, aaa-unknown 1x → zzz first by count
      if (segs.length >= 2) {
        expect(segs[0][1]).toBeGreaterThanOrEqual(segs[1][1]); // count desc
      }
    });
  ```
  NEW:
  ```
    it('returns unmappedSegments sorted by count desc then name asc', async () => {
      // Pad with a KNOWN-category base ('hooks') so the padding sections never land in
      // unmappedSegments — only the two intended unknown segments are unmapped. This lets
      // the ordering assertion be exact and UNCONDITIONAL (no length guard).
      const content = buildLargeMockContent(
        [
          { title: 'A', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'A' },
          { title: 'B', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'B' },
          { title: 'C', url: 'https://code.claude.com/docs/en/aaa-unknown', body: 'C' },
        ],
        40,
        'https://code.claude.com/docs/en/hooks/pad',
      );

      vi.stubGlobal('fetch', mockFetchOk(content));

      const { loadFromOfficial } = await import('../src/loader.js');
      const cachePath = path.join(tempDir, 'cache.txt');
      const result = await loadFromOfficial('https://example.com/docs', cachePath);

      const segs = result.diagnostics.unmappedSegments;
      // zzz-unknown appears 2x, aaa-unknown 1x → zzz first by count, aaa second.
      expect(segs).toHaveLength(2);
      expect(segs[0]).toEqual(['zzz-unknown', 2]); // count desc
      expect(segs[1]).toEqual(['aaa-unknown', 1]); // then name asc
    });
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && npx vitest run tests/loader.test.ts -t 'unmappedSegments sorted'
```

**Commit message:**
```
test(claude-code-docs): make unmappedSegments ordering assertion unconditional (C2)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

---

### Task C3 — FAIL-boundary multiplier-units test isolating `1 + FAIL_REL = 3.0`

**Severity:** nit

**Files:**
- `packages/mcp-servers/claude-code-docs/tests/canary.test.ts` (after the "warns but does not reject when fallback exceeds WARN but not FAIL thresholds" test, line ~439)

**Rationale:** The C1 multiplier-units fix (`canary.ts:16-21` UNITS note) is guarded by tests only for the WARN boundary (1.5) and a 6.0x FAIL. Nothing pins the FAIL relative gate at exactly `1 + FAIL_REL = 3.0`, so a regression that compared `fallbackSectionMultiplier` directly against `FALLBACK_DELTA_FAIL_REL` (2.0) — the exact defect class the UNITS note warns about — would slip through. Verified against `canary.ts:220-238`: FAIL requires delta≥20 AND mult≥3.0. baseline 10/new 30: delta 20, mult 3.0 → reject (at-threshold). baseline 10/new 28: delta 18 (<20) AND mult 2.8 (<3.0) → accept; mult 2.8 ≥ 2.0 so a `FAIL_REL`-direct comparison would mis-reject, making the accept case the discriminating assertion.

**Steps:**
- [ ] Replace, in `tests/canary.test.ts` (append the new `it` immediately after the existing WARN-not-FAIL test):

  OLD:
  ```
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
  ```
  NEW:
  ```
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
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && npx vitest run tests/canary.test.ts -t 'FAIL relative boundary'
```

**Commit message:**
```
test(claude-code-docs): pin FAIL relative gate at 1+FAIL_REL=3.0 boundary (C3)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

---

### Task C4 — e2e category filter for literal `'uncategorized'`

**Severity:** nit

**Files:**
- `packages/mcp-servers/claude-code-docs/tests/bm25.test.ts` (after the "returns empty array when category has no matches" test in the "search with category filtering" block, line ~190)

**Rationale:** PR #130 changed `deriveCategory`'s unmapped-URL fallback from `'overview'` to `'uncategorized'`, and the package CLAUDE.md now documents `'uncategorized'` as a valid search category value. The "search with category filtering" block exercises only mapped categories (`hooks`/`skills`); nothing proves the search path end-to-end with the literal `'uncategorized'` string, so a regression in how the filter handles the fallback category would go undetected. The test reuses the block's existing `makeChunkWithCategory` fixture and matches the established assertion style. Verified `search(index, query, limit?, category?)` signature — both query terms tokenize to `hook`/`content` so both chunks match unfiltered.

**Steps:**
- [ ] Replace, in `tests/bm25.test.ts` (the closing `});` shown is the end of the "search with category filtering" describe block immediately after the "returns empty array when category has no matches" test):

  OLD:
  ```
    it('returns empty array when category has no matches', () => {
      const chunks = [
        makeChunkWithCategory('hooks-1', 'hooks content', ['hook', 'content'], 'hooks'),
      ];
      const index = buildBM25Index(chunks);

      const results = search(index, 'hooks', 5, 'skills');
      expect(results).toHaveLength(0);
    });
  });
  ```
  NEW:
  ```
    it('returns empty array when category has no matches', () => {
      const chunks = [
        makeChunkWithCategory('hooks-1', 'hooks content', ['hook', 'content'], 'hooks'),
      ];
      const index = buildBM25Index(chunks);

      const results = search(index, 'hooks', 5, 'skills');
      expect(results).toHaveLength(0);
    });

    it('filters by the literal \'uncategorized\' fallback category', () => {
      // deriveCategory returns 'uncategorized' for URLs with no segment in SECTION_TO_CATEGORY
      // (categories.ts). A chunk carrying that category must be both searchable unfiltered and
      // selectable via category: 'uncategorized'.
      const chunks = [
        makeChunkWithCategory('uncat-1', 'orphan hooks content', ['orphan', 'hook', 'content'], 'uncategorized'),
        makeChunkWithCategory('hooks-1', 'mapped hooks content', ['mapped', 'hook', 'content'], 'hooks'),
      ];
      const index = buildBM25Index(chunks);

      // Unfiltered: the uncategorized chunk is returned alongside the mapped one.
      const unfiltered = search(index, 'hooks', 5);
      expect(unfiltered.map(r => r.chunk_id).sort()).toEqual(['hooks-1', 'uncat-1']);

      // Filtered by the literal 'uncategorized' category: only the uncategorized chunk.
      const filtered = search(index, 'hooks', 5, 'uncategorized');
      expect(filtered).toHaveLength(1);
      expect(filtered[0].chunk_id).toBe('uncat-1');
      expect(filtered[0].category).toBe('uncategorized');
    });
  });
  ```

**Verification:**
```bash
cd packages/mcp-servers/claude-code-docs && npx vitest run tests/bm25.test.ts -t 'uncategorized'
```

**Commit message:**
```
test(claude-code-docs): e2e category filter for literal 'uncategorized' (C4)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

---

## Verification Gate

After all branch tasks land (A1–A7, B1, the chosen B2/B3 option, and C1–C4), the full suite and type check must stay green:

```bash
cd packages/mcp-servers/claude-code-docs && npx tsc --noEmit && npx vitest run
```

Per-doc grep checks (run from the package directory):

```bash
cd packages/mcp-servers/claude-code-docs
# A1
! grep -q 'taxonomy_drift' README.md && grep -q 'fallback_segment_drift`, `parse_issues`, `section_count_drift`, `stale_corpus' README.md
# A2
grep -q 'fallback-segment delta + relative-drift checks' README.md && ! grep -q 'taxonomy + relative-drift' README.md
# A3
grep -qi 'index floor' README.md && grep -q 'CACHE_WRITE_MIN_SECTIONS' README.md
# A4
grep -q '`agent-sdk`' README.md && grep -q '`uncategorized`' README.md
# A5
diff <(grep '| `MIN_SECTION_COUNT`' CLAUDE.md) <(grep '| `MIN_SECTION_COUNT`' AGENTS.md)
# A6
! grep -q "fall back to 'overview'" src/frontmatter.ts && grep -q "fall back to 'uncategorized'" src/frontmatter.ts
# A7 (if the override is accepted)
grep -q '27 categories' AGENTS.md && grep -q '27 categories' CLAUDE.md
```

**A8 is NOT part of the branch work.** It is an external GitHub PR-body edit to be performed by a human, gated as an External/Published action. Its evidence-capture commands (re-run the live boot and `npx vitest run` at HEAD) inform the corrected PR-body wording but produce no repo commit.

---

## Resolution Log

All decision items are RESOLVED and shipped to PR #130; no open questions remain.

- **A7 (owner-confirmed 2026-05-30):** 26 → 27. Golden queries exercise all 27 canonical categories except the synthetic `uncategorized` fallback (`KNOWN_CATEGORIES` = 28, minus `uncategorized`); the prior "changelog has none" freeze rationale was empirically false (changelog AND agent-sdk are both exercised). Doc rows (AGENTS.md:86 / CLAUDE.md:93) + the B-prime freeze note corrected.
- **B2 (Option i, commit `7d5b8f4e`):** trust-mode/`docsUrl` change is now a cache miss; `ServerState.trustMode`/`docsUrl` and `corpus.trustMode`/`docsUrl` field paths verified; TDD regression tests added (failed pre-fix, pass post-fix).
- **B3 (Option B, commit `a22ef08b`):** pre/post-filter fallback-count population asymmetry documented inline; no gate-input change, no `INGESTION_VERSION` bump.
- **C1 freeze field names:** confirmed — `nextPolicyState.lastHealthyFallbackSectionCount` / `.lastHealthyFallbackObservedAt` exist on the evaluation result and the test passes.
- **No line-number conflicts found:** Where a packet cited a line number, the exact quoted current text was located at HEAD and matched (README ~42/46/77/125; AGENTS.md ~86/100; CLAUDE.md ~93; `frontmatter.ts` ~213; `status.ts:14`; `canary.ts` ~220-262/304-320; `lifecycle.ts` ~210-214; `loader.ts` ~126-171; test anchors at `canary.test.ts:439/541`, `loader.test.ts:14-18/827/840`, `bm25.test.ts:148/190`). The only count discrepancy (26 vs 27 golden-queries categories) is resolved in favor of the verified live count (27) under Task A7.
