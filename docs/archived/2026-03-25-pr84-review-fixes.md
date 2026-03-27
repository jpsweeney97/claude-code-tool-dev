# PR #84 Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 6 findings from the PR #84 review — 2 critical doc accuracy issues, 2 important pre-existing doc gaps, and 2 test coverage suggestions.

**Architecture:** All fixes are independent — no task depends on another. Doc fixes are string replacements. Test additions follow existing patterns in `categories.test.ts` and `golden-queries.test.ts`.

**Tech Stack:** TypeScript (Vitest), Markdown

---

### Task 1: Fix golden-query stats in CLAUDE.md and AGENTS.md

**Finding:** #1 (Critical) — Both files say "26 queries, 16 categories" but actual is 35 queries, 26 categories.

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/CLAUDE.md:93`
- Modify: `packages/mcp-servers/claude-code-docs/AGENTS.md:86`

- [ ] **Step 1: Fix CLAUDE.md**

Replace line 93:
```
| `golden-queries.test.ts` | Multi-category query coverage (26 queries, 16 categories) — validates search quality |
```
With:
```
| `golden-queries.test.ts` | Multi-category query coverage (35 queries, 26 categories) — validates search quality |
```

- [ ] **Step 2: Fix AGENTS.md**

Replace line 86:
```
| `golden-queries.test.ts` | Multi-category query coverage (26 queries, 16 categories) — validates search quality |
```
With:
```
| `golden-queries.test.ts` | Multi-category query coverage (35 queries, 26 categories) — validates search quality |
```

- [ ] **Step 3: Fix TESTING.md off-by-one**

Replace line 55 in `.planning/codebase/TESTING.md`:
```
- `golden-queries.test.ts` — search quality validation (34 queries, 26 categories) using inline mock corpus
```
With:
```
- `golden-queries.test.ts` — search quality validation (35 queries, 26 categories) using inline mock corpus
```

- [ ] **Step 4: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/CLAUDE.md packages/mcp-servers/claude-code-docs/AGENTS.md .planning/codebase/TESTING.md
git commit -m "docs(claude-code-docs): fix golden-query stats in CLAUDE.md, AGENTS.md, TESTING.md

All three files had stale counts. Actual: 35 queries covering 26 categories."
```

---

### Task 2: Fix AGENTS.md tool count and module map

**Finding:** #3, #4 (Important) — AGENTS.md says "three tools" and module map omits `get_status`.

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/AGENTS.md:3`
- Modify: `packages/mcp-servers/claude-code-docs/AGENTS.md:40`

- [ ] **Step 1: Fix opening description**

Replace line 3:
```
BM25-based search server for Claude Code documentation. Fetches docs from `https://code.claude.com/docs/llms-full.txt`, chunks into semantic sections, builds an in-memory BM25 index, and exposes three tools (`search_docs`, `reload_docs`, `dump_index_metadata`) via MCP stdio transport.
```
With:
```
BM25-based search server for Claude Code documentation. Fetches docs from `https://code.claude.com/docs/llms-full.txt`, chunks into semantic sections, builds an in-memory BM25 index, and exposes four tools (`search_docs`, `reload_docs`, `dump_index_metadata`, `get_status`) via MCP stdio transport.
```

- [ ] **Step 2: Fix module map entry**

Replace line 40:
```
| `index.ts` | Entry point — MCP server setup, tool registration (`search_docs`, `reload_docs`, `dump_index_metadata`) |
```
With:
```
| `index.ts` | Entry point — MCP server setup, tool registration (`search_docs`, `reload_docs`, `dump_index_metadata`, `get_status`) |
```

- [ ] **Step 3: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/AGENTS.md
git commit -m "docs(claude-code-docs): fix AGENTS.md tool count and module map

AGENTS.md said 'three tools' but get_status was added previously. Now lists
all four tools in both the description and module map."
```

---

### Task 3: Add referential integrity test for SECTION_TO_CATEGORY

**Finding:** #5 (Suggestion) — No test asserts all `SECTION_TO_CATEGORY` values are members of `KNOWN_CATEGORIES`. A typo in a future mapping would silently create unreachable chunks.

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/tests/categories.test.ts`

- [ ] **Step 1: Write the failing test (verify it would catch a bug)**

Add to the `SECTION_TO_CATEGORY` describe block (after line 84, before the closing `});` of the describe block):

```typescript
  it('all values target a known category', () => {
    for (const [segment, category] of Object.entries(SECTION_TO_CATEGORY)) {
      expect(
        KNOWN_CATEGORIES.has(category),
        `segment '${segment}' maps to unknown category '${category}'`,
      ).toBe(true);
    }
  });
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/categories.test.ts`

Expected: All tests PASS (this test validates existing correctness — it's a regression guard).

- [ ] **Step 3: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/tests/categories.test.ts
git commit -m "test(claude-code-docs): add referential integrity test for SECTION_TO_CATEGORY

Asserts every value in SECTION_TO_CATEGORY is a member of KNOWN_CATEGORIES.
Catches typos in future mappings that would silently create unreachable chunks."
```

---

### Task 4: Add `web-scheduled-tasks` mock section to golden queries

**Finding:** #6 (Suggestion) — Only `headless` and `scheduled-tasks` exercise the `automation` category through the full pipeline. `web-scheduled-tasks` has a unit test in `categories.test.ts:74` but no end-to-end coverage.

**Files:**
- Modify: `packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts`

- [ ] **Step 1: Add mock content section**

Add after the `scheduled-tasks` section (after line 346, before the `---` that starts the `Overview` section at line 348):

```
---
# Cloud-hosted scheduled tasks
Source: https://code.claude.com/docs/en/web-scheduled-tasks

Create durable scheduled tasks that run on Anthropic cloud infrastructure. Unlike session-scoped /loop tasks, web scheduled tasks survive restarts and run independently of any local CLI session.

## Creating web scheduled tasks

Use the web dashboard or API to create scheduled tasks with cron expressions. Each task runs a prompt against a specified repository on Anthropic-hosted runners.

## Managing web scheduled tasks

View, pause, and delete web scheduled tasks from the dashboard. Each run produces a log with the full conversation transcript.
```

- [ ] **Step 2: Add `web-scheduled-tasks` to the chunk category verification**

In the `cases` array at line 672, add after the `scheduled-tasks` entry (line 675):

```typescript
      { urlFragment: 'web-scheduled-tasks', expectedCategory: 'automation' },
```

- [ ] **Step 3: Run tests**

Run: `cd packages/mcp-servers/claude-code-docs && npx vitest run tests/golden-queries.test.ts`

Expected: All tests PASS. The new mock section should parse, chunk, and categorize as `automation`.

- [ ] **Step 4: Update doc stats (query count unchanged, but section count increased)**

The `MOCK_LLMS_CONTENT` now has 31 sections (was 30). No query count changes — `web-scheduled-tasks` is covered by existing golden queries for `automation`.

No doc files need updating — the "35 queries, 26 categories" stats remain accurate. The section count is not referenced in any doc file.

- [ ] **Step 5: Commit**

```bash
git add packages/mcp-servers/claude-code-docs/tests/golden-queries.test.ts
git commit -m "test(claude-code-docs): add web-scheduled-tasks mock for full automation pipeline coverage

All three automation segments (headless, scheduled-tasks, web-scheduled-tasks)
now exercise the full ingestion → chunk → categorize pipeline in golden queries."
```

---

## Verification

After all tasks:

- [ ] Run full test suite: `cd packages/mcp-servers/claude-code-docs && npm test`
- [ ] Expected: 562+ tests passing (559 + referential integrity test + web-scheduled-tasks chunk assertions)
- [ ] Type check: `npx tsc --noEmit`
- [ ] Verify no other stale references: `grep -rn "26 queries\|16 categories\|three tools" packages/mcp-servers/claude-code-docs/`
