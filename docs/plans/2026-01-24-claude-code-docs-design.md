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

- `src/filter.ts` — no longer needed
- `tests/filter.test.ts` — tests deleted functionality

### Create

- `src/categories.ts` — exports `KNOWN_CATEGORIES: Set<string>` with all 24 category names:

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
| `src/frontmatter.ts` | Import from `categories.ts`, update `deriveCategory()` to map new sections (see example below) |
| `src/index.ts` | Server name → `claude-code-docs`, tool names → `search_docs`/`reload_docs`, expand `CATEGORY_VALUES` enum, add `.transform()` to normalize category aliases (see below) |
| `src/loader.ts` | Remove `filterToExtensions()` import and call |
| `package.json` | Name → `@claude-tools/claude-code-docs` |

**Example `deriveCategory()` change:**
```typescript
// Before: only extension sections
function deriveCategory(section: string): string | null {
  const map: Record<string, string> = {
    'hooks': 'hooks',
    'hooks-guide': 'hooks',
    'skills': 'skills',
    // ... 9 extension categories
  };
  return map[section] ?? null; // null = filtered out
}

// After: all sections mapped, KNOWN_CATEGORIES used for validation elsewhere
function deriveCategory(section: string): string {
  const map: Record<string, string> = {
    'hooks': 'hooks',
    'quickstart': 'getting-started',
    'amazon-bedrock': 'providers',
    // ... all section → category mappings
  };
  // Default to 'overview' for unmapped sections (e.g., new docs added upstream).
  // This ensures new content is searchable immediately, even if miscategorized.
  // The KNOWN_CATEGORIES set is used elsewhere to validate user-provided filters.
  return map[section] ?? 'overview';
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
| `tests/corpus-validation.test.ts` | Update expected category list |

Tests unchanged: `bm25.test.ts`, `cache*.test.ts`, `chunk*.test.ts`, `chunker.test.ts`, `error-messages.test.ts`, `fence-tracker.test.ts`, `fetcher.test.ts`, `index-cache.test.ts`, `parser.test.ts`, `tokenizer.test.ts`, `url-helpers.test.ts`

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
  - name: "@mcp-servers/extension-docs" → "@mcp-servers/claude-code-docs"
[DRY-RUN] Would update: ~/.claude.json
  - mcpServers.extension-docs → mcpServers.claude-code-docs
...
Summary: 8 files would be modified, 2 directories would be renamed
```

**On failure:** Script preserves original files (no partial writes). If interrupted, re-run `--dry-run` to see remaining changes. No automatic rollback needed — each file is written atomically.

### Scope

| Target | Action |
|--------|--------|
| `packages/mcp-servers/extension-docs/` | Rename to `claude-code-docs/` |
| `package.json` | Update name |
| `src/index.ts` | Update server name, tool names |
| `.claude/agents/extension-docs-researcher.md` | Update references |
| `.claude/settings.local.json` | Update MCP config |
| `~/.claude/settings.json` | Update hook references (global Claude Code settings) |
| `~/.claude/skills/extension-docs/` | Rename to `claude-code-docs/` |
| `~/.claude.json` | Update MCP server config (MCP server definitions) |
| `~/.claude/hooks/extension-docs-reminder.sh` | Rename script |

### Out of Scope

- `docs/plans/*.md` — historical references, no migration (these are snapshots of past state)
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

1. Update extension-docs-researcher agent to reference new tool names
2. Delete orphaned cache: `rm -rf ~/.cache/extension-docs/`
   - Migration script prints this command in its completion message
   - Not automated because cache deletion is low-risk and user may want to verify migration first

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Category structure | Flat (24 categories) | Simple, matches current API, manageable count |
| Cross-cutting categories | None (topic-only) | BM25 (a term-frequency ranking algorithm) handles cross-cutting queries via relevance ranking; no need for explicit cross-category tagging |
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
