# Claude Code Docs MCP Server Design

Expand the extension-docs MCP server to include ALL official Claude Code documentation, with appropriate rename.

## Summary

| Aspect | Current | New |
|--------|---------|-----|
| Package name | `@mcp-servers/extension-docs` | `@mcp-servers/claude-code-docs` |
| Server name | `extension-docs` | `claude-code-docs` |
| Tool names | `search_extension_docs`, `reload_extension_docs` | `search_docs`, `reload_docs` |
| Categories | 14 (extension-only) | 24 (all docs) |
| Filter | `filterToExtensions()` discards non-extension docs | No filter (include all) |
| Cache | `~/.cache/extension-docs/` | `~/.cache/claude-code-docs/` |

## Categories

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

### Removed/Merged Categories

| Old | New |
|-----|-----|
| `subagents`, `sub-agents` | `agents` |
| `slash-commands` | `commands` |
| `claude-md` | `memory` |
| `configuration` | `config` |

## Code Changes

### Delete

- `src/filter.ts` — no longer needed
- `tests/filter.test.ts` — tests deleted functionality

### Create

- `src/categories.ts` — exports `KNOWN_CATEGORIES` (24 categories)

### Modify

| File | Changes |
|------|---------|
| `src/frontmatter.ts` | Import from `categories.ts`, update `deriveCategory()` |
| `src/index.ts` | Server name → `claude-code-docs`, tool names → `search_docs`/`reload_docs`, expand `CATEGORY_VALUES` |
| `src/loader.ts` | Remove `filterToExtensions()` import and call |
| `package.json` | Name → `@mcp-servers/claude-code-docs` |

### Tests to Update

- `tests/frontmatter.test.ts` — new category derivation expectations
- `tests/loader.test.ts` — no filtering expected
- `tests/golden-queries.test.ts` — may need new golden queries
- `tests/integration.test.ts` — update expectations

## Migration Script

**Location:** `scripts/migrate-extension-docs.py`

**Usage:**
```bash
uv run scripts/migrate-extension-docs.py          # dry-run (default)
uv run scripts/migrate-extension-docs.py --apply  # execute changes
```

### Scope

| Target | Action |
|--------|--------|
| `packages/mcp-servers/extension-docs/` | Rename to `claude-code-docs/` |
| `package.json` | Update name |
| `src/index.ts` | Update server name, tool names |
| `.claude/agents/extension-docs-researcher.md` | Update references |
| `.claude/settings.local.json` | Update MCP config |
| `~/.claude/settings.json` | Update hook script path |
| `~/.claude/skills/extension-docs/` | Rename to `claude-code-docs/` |
| `~/.claude.json` | Update MCP server config |
| `~/.claude/hooks/extension-docs-reminder.sh` | Rename script |

### Out of Scope

- `docs/plans/*.md` — historical, keep as-is
- `~/.cache/extension-docs/` — orphaned, user deletes manually

## Implementation Order

### Phase 1: Code Changes

1. Create `src/categories.ts` with 24 categories
2. Update `src/frontmatter.ts` to import from `categories.ts`
3. Update `src/index.ts`: server name, tool names, `CATEGORY_VALUES`
4. Update `src/loader.ts`: remove filter
5. Delete `src/filter.ts` and `tests/filter.test.ts`
6. Update remaining tests
7. Rename directory to `claude-code-docs/`
8. Update `package.json`

### Phase 2: Migration Script

1. Create `scripts/migrate-extension-docs.py`
2. Implement dry-run and apply modes
3. Test on repo files

### Phase 3: Production Migration

1. Run `--dry-run` to verify
2. Run `--apply` to execute
3. Rebuild and reinstall MCP server
4. Verify search works

### Phase 4: Cleanup

1. Update skill/agent docs
2. Remove orphaned cache

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Category structure | Flat (24 categories) | Simple, matches current API, manageable count |
| Cross-cutting categories | None (topic-only) | BM25 search handles cross-cutting queries |
| Filter removal | Delete entirely | No use case for extension-only in renamed server |
| Cache handling | Let rebuild | Fast, avoids migration complexity |
| Migration approach | Single script, dry-run default | Safe, simple |
| Tool naming | Short (`search_docs`) | MCP server name provides context |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Search result dilution | Low | Category filter available; BM25 relevance handles |
| Index size increase (~3-4x) | Certain | Still small (~400 chunks); negligible impact |
| Migration script misses a reference | Medium | Dry-run mode; manual verification |
