# Claude Code Docs MCP Server Design

Expand the extension-docs MCP server (located at `packages/mcp-servers/extension-docs/`) to include ALL official Claude Code documentation, with appropriate rename.

**Context:** The extension-docs server provides search over Claude Code extension documentation via MCP. This design expands it to cover all Claude Code docs, not just extensions.

## Summary

| Aspect | Current | New |
|--------|---------|-----|
| Package name | `@claude-tools/extension-docs` | `@claude-tools/claude-code-docs` |
| Server name | `extension-docs` | `claude-code-docs` |
| Tool names | `search_extension_docs`, `reload_extension_docs` | `search_docs`, `reload_docs` |
| Categories | 9 (extension-only) | 24 (all docs) |
| Filter | `filterToExtensions()` discards non-extension docs | No filter (include all) |
| Cache | `~/.cache/extension-docs/` | `~/.cache/claude-code-docs/` |

## Categories

Section names (e.g., "hooks-guide", "plugins-reference") correspond to URL paths on docs.anthropic.com (e.g., `/en/docs/claude-code/hooks-guide`).

### Extension Categories (9)

| Category | Sections Covered |
|----------|------------------|
| `hooks` | hooks, hooks-guide |
| `skills` | skills |
| `commands` | commands, slash-commands |
| `agents` | sub-agents |
| `plugins` | plugins, plugins-reference, discover-plugins |
| `plugin-marketplaces` | plugin-marketplaces |
| `mcp` | mcp |
| `settings` | settings |
| `memory` | memory, claude-md |

### New Categories (15)

| Category | Sections Covered |
|----------|------------------|
| `overview` | overview, features-overview, how-claude-code-works |
| `getting-started` | quickstart, setup |
| `cli` | cli-reference |
| `best-practices` | best-practices, common-workflows |
| `interactive` | interactive-mode, checkpointing |
| `security` | security, data-usage, sandboxing, iam, legal-and-compliance |
| `providers` | amazon-bedrock, google-vertex-ai, microsoft-foundry, llm-gateway |
| `ide` | vs-code, jetbrains, devcontainer |
| `ci-cd` | github-actions, gitlab-ci-cd, headless |
| `desktop` | desktop, chrome, claude-code-on-the-web |
| `integrations` | slack, third-party-integrations |
| `config` | configuration, model-config, network-config, terminal-config, output-styles, statusline |
| `operations` | analytics, costs, monitoring-usage |
| `troubleshooting` | troubleshooting |
| `changelog` | changelog |

**Note:** BM25 (Best Matching 25) is a term-frequency ranking algorithm used for relevance-based search. The current server uses BM25 to rank search results.

### Category Aliases (Accepted but Normalized)

These alternate names are accepted by the search tool's category filter but normalized to the canonical category:

| Input Alias | Normalized To |
|-------------|---------------|
| `subagents`, `sub-agents` | `agents` |
| `slash-commands` | `commands` |
| `claude-md` | `memory` |
| `configuration` | `config` |

## Code Changes

### Delete

- `src/filter.ts` — no longer needed (note: `KNOWN_CATEGORIES` export moves to new `categories.ts`)
- `tests/filter.test.ts` — tests deleted functionality

### Create

- `src/categories.ts` — exports `KNOWN_CATEGORIES: Set<string>` with all 24 canonical category names (moved from `filter.ts`):

```typescript
export const KNOWN_CATEGORIES = new Set([
  // Extension categories (9)
  'hooks', 'skills', 'commands', 'agents', 'plugins',
  'plugin-marketplaces', 'mcp', 'settings', 'memory',
  // General categories (15)
  'overview', 'getting-started', 'cli', 'best-practices',
  'interactive', 'security', 'providers', 'ide', 'ci-cd',
  'desktop', 'integrations', 'config', 'operations',
  'troubleshooting', 'changelog',
]);
```

### Modify

| File | Changes |
|------|---------|
| `src/frontmatter.ts` | Change import from `filter.ts` to `categories.ts`, update `deriveCategory()` to map new sections (see example below) |
| `src/index.ts` | Server name → `claude-code-docs`, tool names → `search_docs`/`reload_docs`, expand `CATEGORY_VALUES` to include 24 canonical categories, add `CATEGORY_ALIASES` and `.transform()` to normalize aliases (see below) |
| `src/loader.ts` | Remove `filterToExtensions()` import and call |
| `src/cache.ts` | Update `getDefaultCachePath()` directory from `'extension-docs'` to `'claude-code-docs'` (line 31) |
| `package.json` | Name → `@claude-tools/claude-code-docs` |

**Example `deriveCategory()` change:**
```typescript
// Before (current): returns first segment or 'general' for URLs
export function deriveCategory(path: string): string {
  if (isHttpUrl(path)) {
    const segments = extractContentPath(path);
    for (const seg of segments) {
      if (KNOWN_CATEGORIES.has(seg)) {
        return seg;
      }
    }
    return segments[0] ?? 'general';
  }
  // ... file path logic
}

// After: explicit section → category mapping, default 'overview'
const SECTION_TO_CATEGORY: Record<string, string> = {
  // Extension categories (see Categories table above for complete list)
  'hooks': 'hooks',
  'hooks-guide': 'hooks',
  'skills': 'skills',
  'commands': 'commands',
  'slash-commands': 'commands',
  'sub-agents': 'agents',
  'plugins': 'plugins',
  'plugins-reference': 'plugins',
  'discover-plugins': 'plugins',
  'plugin-marketplaces': 'plugin-marketplaces',
  'mcp': 'mcp',
  'settings': 'settings',
  'memory': 'memory',
  'claude-md': 'memory',
  // New categories (see Categories table above for complete list)
  'overview': 'overview',
  'features-overview': 'overview',
  'how-claude-code-works': 'overview',
  'quickstart': 'getting-started',
  'setup': 'getting-started',
  'cli-reference': 'cli',
  'best-practices': 'best-practices',
  'common-workflows': 'best-practices',
  'interactive-mode': 'interactive',
  'checkpointing': 'interactive',
  'security': 'security',
  'data-usage': 'security',
  'sandboxing': 'security',
  'iam': 'security',
  'legal-and-compliance': 'security',
  'amazon-bedrock': 'providers',
  'google-vertex-ai': 'providers',
  'microsoft-foundry': 'providers',
  'llm-gateway': 'providers',
  'vs-code': 'ide',
  'jetbrains': 'ide',
  'devcontainer': 'ide',
  'github-actions': 'ci-cd',
  'gitlab-ci-cd': 'ci-cd',
  'headless': 'ci-cd',
  'desktop': 'desktop',
  'chrome': 'desktop',
  'claude-code-on-the-web': 'desktop',
  'slack': 'integrations',
  'third-party-integrations': 'integrations',
  'configuration': 'config',
  'model-config': 'config',
  'network-config': 'config',
  'terminal-config': 'config',
  'output-styles': 'config',
  'statusline': 'config',
  'analytics': 'operations',
  'costs': 'operations',
  'monitoring-usage': 'operations',
  'troubleshooting': 'troubleshooting',
  'changelog': 'changelog',
};

export function deriveCategory(path: string): string {
  if (isHttpUrl(path)) {
    const segments = extractContentPath(path);
    for (const seg of segments) {
      const category = SECTION_TO_CATEGORY[seg];
      if (category) return category;
    }
    // Default unmapped sections to 'overview' — ensures searchability
    // Consider logging unmapped sections for maintenance visibility
    return 'overview';
  }
  // ... file path logic unchanged
}
```

**Example alias normalization in `src/index.ts`:**
```typescript
const CATEGORY_ALIASES: Record<string, string> = {
  'subagents': 'agents',
  'sub-agents': 'agents',
  'slash-commands': 'commands',
  'claude-md': 'memory',
  'configuration': 'config',
};

// In SearchInputSchema:
category: z
  .enum([...CATEGORY_VALUES, ...Object.keys(CATEGORY_ALIASES)])
  .transform((val) => CATEGORY_ALIASES[val] ?? val)
  .optional()
```

### Tests to Update

| Test File | Changes Required |
|-----------|------------------|
| `tests/frontmatter.test.ts` | New category derivation expectations; default 'overview' instead of 'general' |
| `tests/loader.test.ts` | Remove filtering expectations; all sections pass through |
| `tests/golden-queries.test.ts` | Add golden queries for new categories (at least one per new category) |
| `tests/integration.test.ts` | Update chunk counts, category expectations |
| `tests/filter.test.ts` | **Delete** (functionality removed) |
| `tests/server.test.ts` | Update tool names (`search_docs`, `reload_docs`), server name |
| `tests/corpus-validation.test.ts` | No category changes needed (tests chunk size bounds, not categories) |

Tests unchanged: `bm25.test.ts`, `cache.mock.test.ts`, `chunk-helpers.test.ts`, `chunker.test.ts`, `error-messages.test.ts`, `fence-tracker.test.ts`, `fetcher.test.ts`, `index-cache.test.ts`, `parser.test.ts`, `tokenizer.test.ts`, `url-helpers.test.ts`

**Note:** `cache.test.ts` requires updates — tests at lines 33-35 and 229-231 explicitly assert `extension-docs` in the cache path regex.

## Migration Script

**Location:** `scripts/migrate-extension-docs.py`

**Usage:**
```bash
uv run scripts/migrate-extension-docs.py          # dry-run (default)
uv run scripts/migrate-extension-docs.py --apply  # execute changes
```

**Dry-run output format:**
```
[DRY-RUN] Would rename: packages/mcp-servers/extension-docs/ → claude-code-docs/
[DRY-RUN] Would update: packages/mcp-servers/claude-code-docs/package.json
  - name: "@claude-tools/extension-docs" → "@claude-tools/claude-code-docs"
[DRY-RUN] Would update: ~/.claude.json
  - mcpServers.extension-docs → mcpServers.claude-code-docs
...
Summary: N files would be modified, N directories would be renamed
```

**On failure:** Script preserves original files (no partial writes). If interrupted, re-run `--dry-run` to see remaining changes. No automatic rollback needed — each file is written atomically.

### Scope

| Target | Action |
|--------|--------|
| `packages/mcp-servers/extension-docs/` | Rename to `claude-code-docs/` |
| `package.json` | Update name |
| `src/index.ts` | Update server name, tool names |
| `src/cache.ts` | Update default cache directory |
| `.claude/agents/extension-docs-researcher.md` | Rename to `claude-code-docs-researcher.md`, update tool references (`mcp__extension-docs__*` → `mcp__claude-code-docs__*`), update prose references ("extension-docs MCP server" → "claude-code-docs MCP server") |
| `.claude/skills/extension-docs/` | Rename to `claude-code-docs/`, update name, tool references (`mcp__extension-docs__*` → `mcp__claude-code-docs__*`), description, and prose references to "extension-docs MCP server" in troubleshooting section |
| `.claude/settings.local.json` | Update tool permission (`mcp__extension-docs__search_extension_docs` → `mcp__claude-code-docs__search_docs`). Note: `reload_extension_docs` not in permissions — only `search_extension_docs` requires update |
| `~/.claude/settings.json` | Update hook references (if any) |
| `~/.claude/skills/extension-docs/` | Rename to `claude-code-docs/`, update contents (if exists) |
| `~/.claude.json` | Update MCP server config (`mcpServers.extension-docs` → `mcpServers.claude-code-docs`) |
| `~/.claude/hooks/extension-docs-reminder.sh` | Rename to `claude-code-docs-reminder.sh`, update tool names in content (`search_extension_docs` → `search_docs`, `reload_extension_docs` → `reload_docs`, "extension-docs MCP" → "claude-code-docs MCP") (if exists) |

### Out of Scope

- `docs/plans/*.md` — historical references, no migration (these are snapshots of past state)
- `docs/decisions/*.md` — active references are acceptable; document decisions reference tooling at time of writing
- `.claude/skills/testing-skills/references/*.md` — contains contextual reference ("use extension-docs MCP") that will naturally update to "claude-code-docs MCP" in prose; not critical path
- `~/.cache/extension-docs/` — orphaned cache directory (see Phase 4 for cleanup instructions)

## Implementation Order

### Phase 1: Code Changes (in `packages/mcp-servers/extension-docs/`)

1. Create `src/categories.ts` with 24 categories
2. Update `src/frontmatter.ts` to import from `categories.ts`
3. Update `src/index.ts`: server name, tool names, `CATEGORY_VALUES`
4. Update `src/loader.ts`: remove filter
5. Delete `src/filter.ts` and `tests/filter.test.ts`
6. Update affected tests (see Tests to Update table)
7. Update `package.json` name field

**Exit criterion:** `npm test` passes with all tests green.

**Note:** Directory rename happens in Phase 2 via migration script, not manually here.

### Phase 2: Migration Script

1. Create `scripts/migrate-extension-docs.py`
2. Implement dry-run and apply modes
3. Test on repo files

**Exit criterion:** `--dry-run` completes without error and shows expected file list matching Scope table.

### Phase 3: Production Migration

1. Run `--dry-run` to verify
2. Run `--apply` to execute
3. Rebuild and reinstall MCP server
4. Verify search works:
   - `search_docs("hooks PreToolUse")` returns hooks docs
   - `search_docs("quickstart")` returns getting-started docs (new category)
   - `search_docs("bedrock")` returns providers docs (new category)
   - Category filter works: `search_docs("permissions", category="security")` returns only security docs

### Phase 4: Cleanup

1. Delete orphaned cache: `rm -rf ~/.cache/extension-docs/`
   - Migration script prints this command in its completion message
   - Not automated because cache deletion is low-risk and user may want to verify migration first
2. Verify negative test: old tool names (`search_extension_docs`) should error

**Note:** Agent and skill updates are handled by migration script in Phase 3, not manually here.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Category structure | Flat (24 categories) | Simple, matches current API, manageable count |
| Cross-cutting categories | None (topic-only) | BM25 handles cross-cutting queries via relevance ranking; no need for explicit cross-category tagging |
| Filter removal | Delete entirely | No use case for extension-only in renamed server |
| Cache handling | Allow automatic rebuild | Index rebuilds in <5s; avoids cache migration complexity and potential corruption |
| Migration approach | Single script, dry-run default | Dry-run shows all changes before execution; single script ensures atomic rename across all references |
| Tool naming | Short (`search_docs`) | MCP server name (`claude-code-docs`) provides namespace context |
| Default unmapped category | `'overview'` instead of `'general'` | `'general'` too vague; `'overview'` is the actual catch-all category for docs homepage content |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Search result dilution | Low | Category filter available; BM25 relevance ranking prioritizes matches. Extension queries typically use specific terms (e.g., "PreToolUse") that won't match non-extension docs. General queries (e.g., "how to configure") may return broader results, but category filter addresses this when precision needed. |
| Index size increase (~3-4x) | Certain | Current index: ~100 chunks. New index: ~400 chunks. Memory impact negligible (<10MB). |
| Migration script misses a reference | Medium | Dry-run mode shows all changes; grep for "extension-docs" after migration to catch stragglers |
| Partial migration state | Low | Script writes atomically; if interrupted, re-run `--dry-run` to see remaining changes; no rollback needed |
| Config file doesn't exist or has unexpected structure | Low | Script should check for file existence before modification; skip with warning if missing |
