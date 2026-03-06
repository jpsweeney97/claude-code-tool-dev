# Remove Local Docs Dependency Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all references to local documentation files from the claude-code-docs MCP server, so it relies exclusively on live-fetched/cached content from `code.claude.com`.

**Architecture:** The server already uses `loadFromOfficial` → content cache for production. The local-docs path (`DOCS_PATH`, `loadMarkdownFiles`, `start:dev`, `corpus-validation.test.ts` walking a local directory) is a vestige of an earlier design. We remove the dead code, rewrite corpus-validation to use the content cache, and drop the `glob` dependency that was only needed for local file walking.

**Tech Stack:** TypeScript, vitest, MCP SDK

**Package directory:** `packages/mcp-servers/claude-code-docs/` — all commands run from here.

---

### Task 1: Rewrite corpus-validation to use content cache

The current test walks a local `docs/` directory. Rewrite it to read from the content cache (same `llms-full.txt` that `loadFromOfficial` stores at `~/Library/Caches/claude-code-docs/llms-full.txt` on macOS).

The test should skip if no cache exists (server hasn't been run yet), matching the existing skip-if-unavailable pattern.

**Files:**
- Modify: `tests/corpus-validation.test.ts`

**Step 1: Rewrite the test file**

Replace the entire file. The new version reads the content cache, parses it with `parseSections`, converts to `MarkdownFile[]` (same conversion `loadFromOfficial` does), then runs chunking invariants on each file.

```typescript
// tests/corpus-validation.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import { parseSections } from '../src/parser.js';
import { readCache } from '../src/cache.js';
import { getDefaultCachePath } from '../src/cache.js';
import { existsSync } from 'fs';

const cachePath = getDefaultCachePath();
const cacheExists = existsSync(cachePath);

if (!cacheExists) {
  console.warn(
    `SKIPPING corpus validation: content cache not found at ${cachePath}\n` +
      `Run the server once to populate the cache, then re-run tests.`
  );
}

const MAX_CHUNK_LINES = 150;

async function loadCorpusFiles() {
  const cached = await readCache(cachePath);
  if (!cached) throw new Error(`Cache not readable at ${cachePath}`);

  const sections = parseSections(cached.content);
  return sections
    .filter((s) => s.content.trim().length > 0)
    .map((s) => ({
      path: s.sourceUrl || s.title || 'unknown',
      content: s.content,
    }));
}

describe.skipIf(!cacheExists)('corpus validation', () => {
  it('all chunks within size bounds', async () => {
    const files = await loadCorpusFiles();
    const stats = {
      totalFiles: 0,
      totalChunks: 0,
      maxChunkLines: 0,
      maxChunkChars: 0,
      oversizedChunks: [] as string[],
    };

    for (const file of files) {
      const { chunks } = chunkFile(file);

      stats.totalFiles++;
      stats.totalChunks += chunks.length;

      for (const chunk of chunks) {
        const lines = chunk.content.split('\n').length;
        const chars = chunk.content.length;
        stats.maxChunkLines = Math.max(stats.maxChunkLines, lines);
        stats.maxChunkChars = Math.max(stats.maxChunkChars, chars);

        if (lines > MAX_CHUNK_LINES || chars > MAX_CHUNK_CHARS) {
          stats.oversizedChunks.push(`${chunk.id}: ${lines} lines, ${chars} chars`);
        }
      }
    }

    console.log('Corpus stats:', {
      ...stats,
      oversizedChunks: stats.oversizedChunks.length,
    });

    expect(stats.oversizedChunks).toEqual([]);
    expect(stats.totalFiles).toBeGreaterThan(0);
  });

  it('all chunks have valid IDs', async () => {
    const files = await loadCorpusFiles();
    const ids = new Set<string>();
    const duplicates: string[] = [];

    for (const file of files) {
      const { chunks } = chunkFile(file);

      for (const chunk of chunks) {
        if (ids.has(chunk.id)) {
          duplicates.push(chunk.id);
        }
        ids.add(chunk.id);
      }
    }

    expect(duplicates).toEqual([]);
  });
});
```

Key changes from the original:
- Reads from content cache (`~/Library/Caches/claude-code-docs/llms-full.txt`) instead of a local directory
- Uses `parseSections` to parse the cached `llms-full.txt` into sections (same path as production)
- Removes `DOCS_PATH` env var, `walkMarkdownFiles` helper, and all `fs` directory-walking imports
- Skip condition: cache file doesn't exist (instead of docs directory doesn't exist)

**Step 2: Run tests to verify the rewrite passes**

Run: `npm test -- tests/corpus-validation.test.ts -v`

Expected: 2 tests pass (if server has been run and cache exists), or 2 tests skipped (if no cache). No failures.

**Step 3: Run full test suite**

Run: `npm test`

Expected: All tests pass. Test count may decrease by 2 if cache doesn't exist (tests skip instead of pass).

**Step 4: Commit**

```
git add tests/corpus-validation.test.ts
git commit -m "refactor: rewrite corpus-validation to use content cache instead of local docs"
```

---

### Task 2: Remove `loadMarkdownFiles` and its tests

The deprecated function is no longer needed — corpus-validation was its last indirect consumer (via the local docs pattern). Remove the function from `loader.ts` and its test blocks from `loader.test.ts`.

**Files:**
- Modify: `src/loader.ts` — remove `loadMarkdownFiles` function (lines 54-85) and `glob` import (line 3), and `path` import if unused after removal
- Modify: `tests/loader.test.ts` — remove `loadMarkdownFiles` describe blocks (lines 81-186) and related imports/variables

**Step 1: Remove `loadMarkdownFiles` from `src/loader.ts`**

Remove these sections:
1. Line 3: `import { glob } from 'glob';` — only used by `loadMarkdownFiles`
2. Line 5: `import * as path from 'path';` — check if used elsewhere in the file first. It IS used by `resolveCachePath` and elsewhere, so **keep it**.
3. Lines 54-85: The entire `loadMarkdownFiles` function (including the `@deprecated` JSDoc)

**Step 2: Remove `loadMarkdownFiles` tests from `tests/loader.test.ts`**

Remove these sections:
1. Line 7: `let loadMarkdownFiles: typeof import('../src/loader.js').loadMarkdownFiles;` — remove this variable declaration
2. Lines 81-186: Both `describe('loadMarkdownFiles', ...)` and `describe('loadMarkdownFiles glob failures', ...)` blocks entirely
3. Check if `os` import (line 5) is still used after removal — it's used in the `loadMarkdownFiles` `beforeEach` for `os.tmpdir()`. Grep the remaining test code to confirm. If unused, remove it.

**Step 3: Run type check**

Run: `npx tsc --noEmit`

Expected: No errors. If `glob` import removal causes issues, check for other usages (there are none — confirmed in exploration).

**Step 4: Run tests**

Run: `npm test`

Expected: All remaining tests pass. Test count decreases (the removed `loadMarkdownFiles` tests are gone).

**Step 5: Commit**

```
git add src/loader.ts tests/loader.test.ts
git commit -m "refactor: remove deprecated loadMarkdownFiles and glob dependency"
```

---

### Task 3: Remove `glob` from package.json dependencies

With `loadMarkdownFiles` gone, `glob` is no longer imported anywhere in `src/`.

**Files:**
- Modify: `package.json` — remove `"glob": "^11.0.0"` from `dependencies`

**Step 1: Verify no remaining glob usage**

Run: `grep -r "from 'glob'" src/`

Expected: No matches.

**Step 2: Remove glob from dependencies**

Remove the `"glob": "^11.0.0"` line from the `dependencies` object in `package.json`.

**Step 3: Reinstall dependencies**

Run: `npm install`

Expected: Clean install, no errors.

**Step 4: Run tests**

Run: `npm test`

Expected: All tests pass. The `loader.test.ts` file may still mock `glob` — if so, that was removed in Task 2. Verify no test imports `glob`.

**Step 5: Commit**

```
git add package.json package-lock.json
git commit -m "chore: remove unused glob dependency"
```

---

### Task 4: Remove `start:dev` script

The `start:dev` script sets `DOCS_PATH` which no source code reads. It's a no-op identical to `start`.

**Files:**
- Modify: `package.json` — remove `"start:dev"` script entry

**Step 1: Remove the script**

Remove the line: `"start:dev": "DOCS_PATH=../../../docs/claude-code-documentation node dist/index.js"`

**Step 2: Commit**

```
git add package.json
git commit -m "chore: remove dead start:dev script (DOCS_PATH not read by source)"
```

Note: Tasks 3 and 4 both modify `package.json`. If executing sequentially, they can be combined into a single commit. If executing in parallel, handle the merge conflict.

---

### Task 5: Update CLAUDE.md

Remove all references to local docs, `DOCS_PATH`, `start:dev`, and `loadMarkdownFiles`.

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Apply these changes to CLAUDE.md**

1. **Commands section**: Remove the `npm run start:dev` line and its comment.

2. **Environment Variables table**: Remove the `DOCS_PATH` row entirely. The `INTEGRATION` row added earlier can stay — it gates a live network test, which is a different concern.

3. **Gotchas section**: Remove the `loadMarkdownFiles` gotcha: `- **\`loadMarkdownFiles\` is deprecated**: Only used in tests. Production uses \`loadFromOfficial\`.`

4. **Module Map**: In the `loader.ts` row, the description says "Fetch/cache pipeline — TTL, stale fallback". This is still accurate after removing `loadMarkdownFiles`, so no change needed.

5. **Testing table**: Update `corpus-validation.test.ts` description from `Validates chunking invariants across full corpus (requires \`DOCS_PATH\`)` to `Validates chunking invariants across full corpus (requires content cache)`.

**Step 2: Verify test count**

Run: `npm test`

Update the test count in the Commands section comment (`# vitest run (N tests)`) to match the actual output.

**Step 3: Commit**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md to reflect removal of local docs dependency"
```

---

### Task 6: Delete `docs/claude-code-documentation/`

The local docs copy is no longer referenced by any code.

**Files:**
- Delete: `docs/claude-code-documentation/` (entire directory)

**Step 1: Verify no remaining references**

Run from monorepo root: `grep -r "claude-code-documentation" --include='*.ts' --include='*.json' --include='*.md' .`

Expected: No matches in source/test files (CLAUDE.md references were removed in Task 5). If any remain, fix them first.

Note: the project CLAUDE.md at `.claude/CLAUDE.md` references `docs/claude-code-documentation/` in the directory structure table as `Official Claude Code docs (reference)`. Update that entry to remove the reference.

**Step 2: Delete the directory**

Run: `trash docs/claude-code-documentation/`

(Per project rules: never use `rm`, always use `trash`.)

**Step 3: Update project CLAUDE.md**

In `.claude/CLAUDE.md`, remove or update the `claude-code-documentation` entry in the directory structure table under `docs/`.

**Step 4: Commit**

```
git add -A docs/claude-code-documentation/ .claude/CLAUDE.md
git commit -m "chore: remove stale local docs copy (server fetches live from code.claude.com)"
```

---

## Execution Order

Tasks 1-2 are sequential (Task 2 removes code that Task 1's rewrite replaces).
Tasks 3-4 can run in parallel after Task 2.
Task 5 runs after Tasks 3-4 (needs final test count).
Task 6 runs last (needs Task 5 to update references first).

```
Task 1 → Task 2 → Task 3 ─┐
                  Task 4 ─┤→ Task 5 → Task 6
```

## Verification

After all tasks, run from `packages/mcp-servers/claude-code-docs/`:

```bash
npx tsc --noEmit     # Type check clean
npm test             # All tests pass
grep -r "extension-reference\|loadMarkdownFiles\|start:dev\|DOCS_PATH" src/ tests/ CLAUDE.md package.json
                     # No matches
```
