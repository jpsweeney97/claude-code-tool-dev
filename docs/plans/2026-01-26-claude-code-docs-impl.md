# Claude Code Docs MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the extension-docs MCP server to include all Claude Code documentation, rename it to claude-code-docs, and update all references.

**Architecture:** Three-phase approach: (1) Code changes in existing directory with TDD, (2) Migration script for renames, (3) Production migration and cleanup. The filter module is deleted entirely; categories expand from 9 to 24; tool names become generic (`search_docs`, `reload_docs`).

**Tech Stack:** TypeScript, Vitest, Zod, Python (migration script)

**Phase Dependencies:** Phase 1 must be fully committed before running Phase 2 migration script. Phase 3 requires Claude Code restart to pick up new MCP server config.

**Error Handling:** If a test fails unexpectedly (not the expected "FAIL before implementation"), investigate the cause before proceeding. Common causes: existing code differs from plan assumptions, imports missing, or test assertions incorrect. Fix the issue or update the plan before continuing.

---

## Phase 1: Code Changes

All changes happen in `packages/mcp-servers/extension-docs/` until Phase 2 renames it.

### Task 1: Create Categories Module

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/categories.ts`
- Test: `packages/mcp-servers/extension-docs/tests/categories.test.ts`

**Step 1: Write the failing test**

```typescript
// tests/categories.test.ts
import { describe, it, expect } from 'vitest';
import { KNOWN_CATEGORIES, SECTION_TO_CATEGORY, CATEGORY_ALIASES } from '../src/categories.js';

describe('KNOWN_CATEGORIES', () => {
  it('contains all 24 canonical categories', () => {
    const expected = [
      // Extension categories (9)
      'hooks', 'skills', 'commands', 'agents', 'plugins',
      'plugin-marketplaces', 'mcp', 'settings', 'memory',
      // General categories (15)
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'ide', 'ci-cd',
      'desktop', 'integrations', 'config', 'operations',
      'troubleshooting', 'changelog',
    ];

    expect(KNOWN_CATEGORIES.size).toBe(24);
    for (const cat of expected) {
      expect(KNOWN_CATEGORIES.has(cat)).toBe(true);
    }
  });

  it('does not contain aliases as canonical categories', () => {
    expect(KNOWN_CATEGORIES.has('subagents')).toBe(false);
    expect(KNOWN_CATEGORIES.has('sub-agents')).toBe(false);
    expect(KNOWN_CATEGORIES.has('slash-commands')).toBe(false);
    expect(KNOWN_CATEGORIES.has('claude-md')).toBe(false);
    expect(KNOWN_CATEGORIES.has('configuration')).toBe(false);
  });
});

describe('SECTION_TO_CATEGORY', () => {
  it('maps extension sections to categories', () => {
    expect(SECTION_TO_CATEGORY['hooks']).toBe('hooks');
    expect(SECTION_TO_CATEGORY['hooks-guide']).toBe('hooks');
    expect(SECTION_TO_CATEGORY['slash-commands']).toBe('commands');
    expect(SECTION_TO_CATEGORY['sub-agents']).toBe('agents');
    expect(SECTION_TO_CATEGORY['plugins-reference']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['discover-plugins']).toBe('plugins');
  });

  it('maps new sections to categories', () => {
    expect(SECTION_TO_CATEGORY['quickstart']).toBe('getting-started');
    expect(SECTION_TO_CATEGORY['setup']).toBe('getting-started');
    expect(SECTION_TO_CATEGORY['amazon-bedrock']).toBe('providers');
    expect(SECTION_TO_CATEGORY['google-vertex-ai']).toBe('providers');
    expect(SECTION_TO_CATEGORY['vs-code']).toBe('ide');
    expect(SECTION_TO_CATEGORY['github-actions']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['sandboxing']).toBe('security');
    expect(SECTION_TO_CATEGORY['model-config']).toBe('config');
  });
});

describe('CATEGORY_ALIASES', () => {
  it('maps aliases to canonical categories', () => {
    expect(CATEGORY_ALIASES['subagents']).toBe('agents');
    expect(CATEGORY_ALIASES['sub-agents']).toBe('agents');
    expect(CATEGORY_ALIASES['slash-commands']).toBe('commands');
    expect(CATEGORY_ALIASES['claude-md']).toBe('memory');
    expect(CATEGORY_ALIASES['configuration']).toBe('config');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/categories.test.ts`
Expected: FAIL with "Cannot find module '../src/categories.js'"

**Step 3: Write minimal implementation**

```typescript
// src/categories.ts

/**
 * Canonical list of all documentation categories.
 * These are the 24 categories used for categorizing all Claude Code docs.
 */
export const KNOWN_CATEGORIES = new Set([
  // Extension categories (9)
  'hooks',
  'skills',
  'commands',
  'agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'memory',
  // General categories (15)
  'overview',
  'getting-started',
  'cli',
  'best-practices',
  'interactive',
  'security',
  'providers',
  'ide',
  'ci-cd',
  'desktop',
  'integrations',
  'config',
  'operations',
  'troubleshooting',
  'changelog',
]);

/**
 * Maps URL section segments to their canonical category.
 * Section names correspond to URL paths on docs.anthropic.com.
 */
export const SECTION_TO_CATEGORY: Record<string, string> = {
  // Extension categories
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
  // New categories
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

/**
 * Maps category aliases to their canonical category.
 * These are accepted as input but normalized before use.
 */
export const CATEGORY_ALIASES: Record<string, string> = {
  'subagents': 'agents',
  'sub-agents': 'agents',
  'slash-commands': 'commands',
  'claude-md': 'memory',
  'configuration': 'config',
};
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/categories.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/categories.ts packages/mcp-servers/extension-docs/tests/categories.test.ts
git commit -m "$(cat <<'EOF'
feat(extension-docs): add categories module with 24 categories

Adds KNOWN_CATEGORIES (24 canonical categories), SECTION_TO_CATEGORY
(URL segment mappings), and CATEGORY_ALIASES (input normalization).
Prepares for expanding beyond extension-only documentation.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Update Frontmatter to Use New Categories

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/frontmatter.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/frontmatter.test.ts`

**Step 1: Add new tests and modify existing tests**

In `tests/frontmatter.test.ts`, add these NEW tests to the existing `describe('deriveCategory')` block:

```typescript
// ADD these new tests:

it('uses SECTION_TO_CATEGORY mapping for URLs', () => {
  // Known sections map to their category
  expect(deriveCategory('https://code.claude.com/docs/en/quickstart')).toBe('getting-started');
  expect(deriveCategory('https://code.claude.com/docs/en/amazon-bedrock')).toBe('providers');
  expect(deriveCategory('https://code.claude.com/docs/en/vs-code')).toBe('ide');
  expect(deriveCategory('https://code.claude.com/docs/en/github-actions')).toBe('ci-cd');
});

it('returns overview for unmapped URL sections', () => {
  // Unknown sections default to 'overview' not 'general'
  expect(deriveCategory('https://code.claude.com/docs/en/unknown-page')).toBe('overview');
  expect(deriveCategory('https://code.claude.com/docs/en/some-new-page')).toBe('overview');
});
```

Then MODIFY these existing tests (search for them by their `it()` description):

```typescript
// FIND AND REPLACE: "returns general for URL with no content path"
// Change 'general' to 'overview':
it('returns overview for URL with no content path', () => {
  expect(deriveCategory('https://code.claude.com/')).toBe('overview');
  expect(deriveCategory('https://code.claude.com/docs/en/')).toBe('overview');
});

// FIND AND REPLACE: "falls back to first segment for unknown category"
// Change to return 'overview' instead of the first segment:
it('returns overview for unknown URL sections', () => {
  // Unknown sections default to overview, not the first segment
  expect(deriveCategory('https://example.com/custom/page')).toBe('overview');
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/frontmatter.test.ts`
Expected: FAIL — 'quickstart' returns 'quickstart' or 'general' instead of 'getting-started'

**Step 3: Update the import and deriveCategory function**

In `src/frontmatter.ts`, change:

```typescript
// Before (line 3):
import { KNOWN_CATEGORIES } from './filter.js';

// After:
import { SECTION_TO_CATEGORY } from './categories.js';
```

Then update `deriveCategory`:

```typescript
// Replace the existing deriveCategory function (around line 204-220):
export function deriveCategory(path: string): string {
  if (isHttpUrl(path)) {
    const segments = extractContentPath(path);
    for (const seg of segments) {
      const category = SECTION_TO_CATEGORY[seg];
      if (category) return category;
    }
    // Default unmapped sections to 'overview' — ensures searchability
    return 'overview';
  }

  // Original logic for file paths
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/frontmatter.test.ts`
Expected: PASS

**Step 5: Run all tests to verify**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/frontmatter.test.ts`
Expected: PASS

**Step 6: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/frontmatter.ts packages/mcp-servers/extension-docs/tests/frontmatter.test.ts
git commit -m "$(cat <<'EOF'
feat(extension-docs): update deriveCategory to use SECTION_TO_CATEGORY

- Import from categories.ts instead of filter.ts
- Use explicit section→category mapping for URLs
- Default unmapped sections to 'overview' instead of first segment
- Update tests for new 'overview' default

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Remove Filter from Loader

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/loader.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/loader.test.ts`

**Step 1: Write the failing test**

Update `tests/loader.test.ts` to expect non-extension sections to pass through:

```typescript
// Replace the existing test "fetches, parses, and filters to extension sections":
it('fetches, parses, and returns all sections (no filtering)', async () => {
  const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here

# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Getting started content`;

  const mockFetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'text/plain' }),
    text: () => Promise.resolve(mockContent),
  });
  vi.stubGlobal('fetch', mockFetch);

  const { loadFromOfficial } = await import('../src/loader.js');

  const cachePath = path.join(tempDir, 'cache.txt');
  const { files, contentHash } = await loadFromOfficial('https://example.com/docs', cachePath);

  // Now expects 2 files (both hooks AND quickstart), not 1
  expect(files).toHaveLength(2);
  expect(files.some(f => f.path.includes('hooks'))).toBe(true);
  expect(files.some(f => f.path.includes('quickstart'))).toBe(true);
  expect(contentHash).toMatch(/^[a-f0-9]{64}$/);
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/loader.test.ts`
Expected: FAIL — expected 2 files but got 1 (quickstart was filtered)

**Step 3: Remove filter import and call**

In `src/loader.ts`:

```typescript
// Remove this import (line 9):
import { filterToExtensions } from './filter.js';

// Change line 121 from:
const filtered = filterToExtensions(sections).filter((s) => s.content.trim().length > 0);

// To:
const filtered = sections.filter((s) => s.content.trim().length > 0);
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/loader.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts packages/mcp-servers/extension-docs/tests/loader.test.ts
git commit -m "$(cat <<'EOF'
feat(extension-docs): remove extension filtering from loader

All sections now pass through; no longer filters to extension-only.
This allows the server to index all Claude Code documentation.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Delete Filter Module

**Files:**
- Delete: `packages/mcp-servers/extension-docs/src/filter.ts`
- Delete: `packages/mcp-servers/extension-docs/tests/filter.test.ts`

**Step 1: Verify no other files import filter.ts**

Run: `grep -r "from.*filter" packages/mcp-servers/extension-docs/src/`
Expected: No output (frontmatter.ts was already updated)

**Step 2: Delete the files**

```bash
rm packages/mcp-servers/extension-docs/src/filter.ts
rm packages/mcp-servers/extension-docs/tests/filter.test.ts
```

**Step 3: Run all tests to verify nothing breaks**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: PASS (all tests)

**Step 4: Commit**

```bash
git add -u packages/mcp-servers/extension-docs/
git commit -m "$(cat <<'EOF'
refactor(extension-docs): delete filter module

filterToExtensions() is no longer needed — all docs are now indexed.
KNOWN_CATEGORIES moved to categories.ts in previous commit.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Update Index with New Categories and Tool Names

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/index.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/server.test.ts`

**Step 1: Write the failing test**

Update `tests/server.test.ts`:

```typescript
// Replace CATEGORY_VALUES (lines 10-25) with:
const CATEGORY_VALUES = [
  // Extension categories (9)
  'hooks', 'skills', 'commands', 'agents', 'plugins',
  'plugin-marketplaces', 'mcp', 'settings', 'memory',
  // General categories (15)
  'overview', 'getting-started', 'cli', 'best-practices',
  'interactive', 'security', 'providers', 'ide', 'ci-cd',
  'desktop', 'integrations', 'config', 'operations',
  'troubleshooting', 'changelog',
] as const;

// Add alias handling to schema (after existing CATEGORY_VALUES):
const CATEGORY_ALIASES: Record<string, string> = {
  'subagents': 'agents',
  'sub-agents': 'agents',
  'slash-commands': 'commands',
  'claude-md': 'memory',
  'configuration': 'config',
};

const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty')),
  limit: z.number().int().min(1).max(20).optional(),
  category: z
    .enum([...CATEGORY_VALUES, ...Object.keys(CATEGORY_ALIASES)] as [string, ...string[]])
    .transform((val) => CATEGORY_ALIASES[val] ?? val)
    .optional(),
});

// Add new tests for alias normalization:
describe('Category alias normalization', () => {
  it('normalizes subagents to agents', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'subagents' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('agents');
    }
  });

  it('normalizes sub-agents to agents', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'sub-agents' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('agents');
    }
  });

  it('normalizes claude-md to memory', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'claude-md' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('memory');
    }
  });

  it('normalizes configuration to config', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'configuration' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('config');
    }
  });

  it('passes through canonical categories unchanged', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', category: 'hooks' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category).toBe('hooks');
    }
  });
});

// Add tests for new categories:
describe('New category validation', () => {
  it('accepts new general categories', () => {
    const newCategories = [
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'ide', 'ci-cd',
      'desktop', 'integrations', 'config', 'operations',
      'troubleshooting', 'changelog',
    ];

    for (const cat of newCategories) {
      const result = SearchInputSchema.safeParse({ query: 'test', category: cat });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.category).toBe(cat);
      }
    }
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/server.test.ts`
Expected: FAIL — new categories not in enum

**Step 3: Update src/index.ts**

Make these changes in order:

**3a. Add import** — near the top of the file, after the existing imports (around line 10):
```typescript
import { KNOWN_CATEGORIES, CATEGORY_ALIASES } from './categories.js';
```

**3b. Replace CATEGORY_VALUES** (search for `const CATEGORY_VALUES = [`):
```typescript
const CATEGORY_VALUES = [...KNOWN_CATEGORIES] as const;

// **3c. Update SearchInputSchema** — search for `const SearchInputSchema = z.object({`:
const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty'))
    .describe(
      'Search query — be specific (e.g., "PreToolUse JSON output", "skill frontmatter properties")',
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .describe('Maximum results to return (default: 5, max: 20)'),
  category: z
    .enum([...CATEGORY_VALUES, ...Object.keys(CATEGORY_ALIASES)] as [string, ...string[]])
    .transform((val) => CATEGORY_ALIASES[val] ?? val)
    .optional()
    .describe('Filter to a specific category (e.g., "hooks", "plugins", "security")'),
});

// **3d. Update server name** — search for `name: 'extension-docs'`:
const server = new McpServer({
  name: 'claude-code-docs',
  version: '1.0.0',
});

// **3e. Update search tool** — search for `'search_extension_docs'`:
server.registerTool(
  'search_docs',
  {
    title: 'Search Claude Code Docs',
    description:
      'Search Claude Code documentation (extensions, setup, security, providers, IDE integration, CI/CD, and more). Use specific queries.',
    // ... rest unchanged
  },

// **3f. Update reload tool** — search for `'reload_extension_docs'`:
server.registerTool(
  'reload_docs',
  {
    title: 'Reload Claude Code Docs',
    description:
      'Force reload of Claude Code documentation. Use after editing docs to refresh search index.',
    inputSchema: z.object({}),  // unchanged
  },
  // handler function unchanged
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/server.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts packages/mcp-servers/extension-docs/tests/server.test.ts
git commit -m "$(cat <<'EOF'
feat(extension-docs): expand categories and rename tools

- Import categories from categories.ts
- Expand CATEGORY_VALUES to all 24 categories
- Add CATEGORY_ALIASES with .transform() normalization
- Rename server to 'claude-code-docs'
- Rename tools to 'search_docs' and 'reload_docs'

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Update Cache Path

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/cache.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/cache.test.ts`

**Step 1: Write the failing test**

Update `tests/cache.test.ts`:

```typescript
// Change lines 33-35:
describe('getDefaultCachePath', () => {
  it('returns path ending with claude-code-docs/llms-full.txt', () => {
    const cachePath = cache.getDefaultCachePath();
    expect(cachePath).toMatch(/claude-code-docs[/\\]llms-full\.txt$/);
  });

  it('accepts custom filename', () => {
    const cachePath = cache.getDefaultCachePath('custom.txt');
    expect(cachePath).toMatch(/claude-code-docs[/\\]custom\.txt$/);
  });
});

// Change line 231:
it('getDefaultIndexCachePath returns json file path', () => {
  const indexCachePath = cache.getDefaultIndexCachePath();
  expect(indexCachePath).toMatch(/claude-code-docs[/\\]llms-full\.index\.json$/);
});
```

**Step 2: Run test to verify it fails**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: FAIL — path contains 'extension-docs' not 'claude-code-docs'

**Step 3: Update cache.ts**

```typescript
// Change line 31 from:
return path.join(baseDir, 'extension-docs', filename);

// To:
return path.join(baseDir, 'claude-code-docs', filename);
```

**Step 4: Run test to verify it passes**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/cache.ts packages/mcp-servers/extension-docs/tests/cache.test.ts
git commit -m "$(cat <<'EOF'
feat(extension-docs): update cache directory to claude-code-docs

Cache files now stored in ~/.cache/claude-code-docs/ instead of
~/.cache/extension-docs/. Old cache will be orphaned (cleanup in Phase 4).

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Add Golden Queries for New Categories

**Files:**
- Modify: `packages/mcp-servers/extension-docs/tests/golden-queries.test.ts`

**Step 1: Update mock content and add new queries**

```typescript
// Expand MOCK_LLMS_CONTENT to include new category samples:
const MOCK_LLMS_CONTENT = `# Hooks
Source: https://code.claude.com/docs/en/hooks

Learn how to automate actions in Claude Code using hooks—shell commands that run automatically before or after specific events.

## What are hooks

Hooks are shell commands that Claude Code executes automatically at specific points during its operation. They allow you to customize behavior, enforce policies, and integrate with external tools.

## Exit codes and blocking

Exit codes control hook behavior:
- Exit code 0: Success, Claude Code continues
- Exit code 2: Block the operation (for PreToolUse hooks)
- Other non-zero: Warning logged, operation continues

## PreToolUse JSON output

When using JSON output mode, PreToolUse hooks receive tool input as structured JSON on stdin. The output format includes tool name, parameters, and context.

## Common fields in hook input

All hooks receive common fields including session_id, timestamp, tool_name (for tool hooks), and user context.

# Skills
Source: https://code.claude.com/docs/en/skills

Learn how to extend Claude Code with custom skills—reusable instruction sets that guide Claude's behavior for specific tasks.

## Skill frontmatter

Skills use YAML frontmatter to define metadata:
- name: Skill identifier
- description: What the skill does
- model_invocable: Whether Claude can invoke directly

## Creating skills

Create a SKILL.md file in your .claude/skills directory with the appropriate frontmatter and instructions.

# MCP Servers
Source: https://code.claude.com/docs/en/mcp

Model Context Protocol (MCP) enables Claude to communicate with external tools and data sources.

## MCP server registration

Register MCP servers in your settings.json under the "mcpServers" key. Each server needs a command to launch and optional arguments.

## Building MCP servers

MCP servers expose tools that Claude can invoke. Use the @modelcontextprotocol/sdk to build servers with tool definitions.

# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Get started with Claude Code in minutes. This guide walks you through installation and your first interaction.

## Installation

Install Claude Code using npm: npm install -g @anthropic-ai/claude-code

## First run

Run claude in your terminal to start an interactive session.

# Amazon Bedrock
Source: https://code.claude.com/docs/en/amazon-bedrock

Configure Claude Code to use Amazon Bedrock as the model provider.

## Setting up Bedrock

Configure your AWS credentials and set the provider in your claude settings.

# VS Code Integration
Source: https://code.claude.com/docs/en/vs-code

Integrate Claude Code with Visual Studio Code for inline assistance.

## Installing the extension

Install the Claude Code extension from the VS Code marketplace.

# GitHub Actions
Source: https://code.claude.com/docs/en/github-actions

Run Claude Code in CI/CD pipelines with GitHub Actions.

## Workflow setup

Add Claude Code to your GitHub Actions workflow for automated code review.

# Security
Source: https://code.claude.com/docs/en/security

Understand Claude Code's security model and best practices.

## Sandboxing

Claude Code uses sandboxing to limit file system access and command execution.

# Troubleshooting
Source: https://code.claude.com/docs/en/troubleshooting

Common issues and solutions when using Claude Code.

## Connection errors

If you see connection errors, check your network settings and API key.
`;

// Add new golden queries for expanded categories:
const goldenQueries = [
  // Extension categories (existing)
  { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
  { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
  { query: 'skill frontmatter', expectedTopCategory: 'skills' },
  { query: 'MCP server registration', expectedTopCategory: 'mcp' },
  { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  // New categories
  { query: 'installation npm', expectedTopCategory: 'getting-started' },
  { query: 'bedrock AWS credentials', expectedTopCategory: 'providers' },
  { query: 'VS Code extension marketplace', expectedTopCategory: 'ide' },
  { query: 'GitHub Actions workflow', expectedTopCategory: 'ci-cd' },
  { query: 'sandboxing file system access', expectedTopCategory: 'security' },
  { query: 'connection errors network', expectedTopCategory: 'troubleshooting' },
];
```

**Step 2: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/golden-queries.test.ts`
Expected: PASS

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/golden-queries.test.ts
git commit -m "$(cat <<'EOF'
test(extension-docs): add golden queries for new categories

Adds test coverage for getting-started, providers, ide, ci-cd,
security, and troubleshooting categories with mock content.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Update Package Name

**Files:**
- Modify: `packages/mcp-servers/extension-docs/package.json`

**Step 1: Update package.json**

```json
{
  "name": "@claude-tools/claude-code-docs",
  "version": "1.0.0",
  ...
}
```

**Step 2: Run tests to verify build**

Run: `cd packages/mcp-servers/extension-docs && npm run build && npm test`
Expected: PASS

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/package.json
git commit -m "$(cat <<'EOF'
chore(extension-docs): rename package to @claude-tools/claude-code-docs

Package name updated in preparation for directory rename.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 2: Migration Script

### Task 9: Create Migration Script

**Files:**
- Create: `scripts/migrate-extension-docs.py`

**Step 1: Write the migration script**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Migration script for renaming extension-docs to claude-code-docs.

Usage:
    uv run scripts/migrate-extension-docs.py          # dry-run (default)
    uv run scripts/migrate-extension-docs.py --apply  # execute changes
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path


def log(msg: str, prefix: str = "") -> None:
    """Print a log message with optional prefix."""
    print(f"{prefix}{msg}")


def dry_log(msg: str) -> None:
    """Print a dry-run log message."""
    log(msg, "[DRY-RUN] ")


def apply_log(msg: str) -> None:
    """Print an apply log message."""
    log(msg, "[APPLY] ")


def read_file(path: Path) -> str | None:
    """Read a file, returning None if it doesn't exist."""
    try:
        return path.read_text()
    except FileNotFoundError:
        return None


def write_file(path: Path, content: str) -> None:
    """Write content to a file atomically."""
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(content)
    temp_path.rename(path)


def update_json_file(
    path: Path,
    updates: dict,
    dry_run: bool,
) -> bool:
    """Update specific keys in a JSON file."""
    content = read_file(path)
    if content is None:
        log(f"Skipping (not found): {path}")
        return False

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        log(f"Skipping (invalid JSON): {path} - {e}")
        return False

    changed = False
    for key_path, transform in updates.items():
        keys = key_path.split(".")
        obj = data
        for key in keys[:-1]:
            if key not in obj:
                break
            obj = obj[key]
        else:
            final_key = keys[-1]
            if final_key in obj:
                old_val = obj[final_key]
                new_val = transform(old_val) if callable(transform) else transform
                if old_val != new_val:
                    if dry_run:
                        dry_log(f"Would update {path}")
                        dry_log(f"  - {key_path}: {old_val!r} → {new_val!r}")
                    else:
                        obj[final_key] = new_val
                    changed = True

    if changed and not dry_run:
        write_file(path, json.dumps(data, indent=2) + "\n")
        apply_log(f"Updated: {path}")

    return changed


def update_text_file(
    path: Path,
    replacements: list[tuple[str, str]],
    dry_run: bool,
) -> bool:
    """Apply text replacements to a file."""
    content = read_file(path)
    if content is None:
        log(f"Skipping (not found): {path}")
        return False

    new_content = content
    changes = []
    for old, new in replacements:
        if old in new_content:
            changes.append((old, new))
            new_content = new_content.replace(old, new)

    if not changes:
        return False

    if dry_run:
        dry_log(f"Would update: {path}")
        for old, new in changes:
            dry_log(f"  - {old!r} → {new!r}")
    else:
        write_file(path, new_content)
        apply_log(f"Updated: {path}")

    return True


def rename_path(old_path: Path, new_path: Path, dry_run: bool) -> bool:
    """Rename a file or directory."""
    if not old_path.exists():
        log(f"Skipping (not found): {old_path}")
        return False

    if new_path.exists():
        log(f"Skipping (target exists): {new_path}")
        return False

    if dry_run:
        dry_log(f"Would rename: {old_path} → {new_path}")
    else:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))
        apply_log(f"Renamed: {old_path} → {new_path}")

    return True


def migrate(dry_run: bool) -> int:
    """Run the migration."""
    repo_root = Path(__file__).parent.parent
    home = Path.home()

    changes = 0

    # 1. Rename MCP server directory
    old_server = repo_root / "packages/mcp-servers/extension-docs"
    new_server = repo_root / "packages/mcp-servers/claude-code-docs"
    if rename_path(old_server, new_server, dry_run):
        changes += 1

    # 2. Rename agent file
    old_agent = repo_root / ".claude/agents/extension-docs-researcher.md"
    new_agent = repo_root / ".claude/agents/claude-code-docs-researcher.md"
    if rename_path(old_agent, new_agent, dry_run):
        changes += 1

    # Update agent content
    agent_path = new_agent if new_agent.exists() else old_agent
    if update_text_file(
        agent_path,
        [
            ("extension-docs-researcher", "claude-code-docs-researcher"),
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
            ("mcp__extension-docs__reload_extension_docs", "mcp__claude-code-docs__reload_docs"),
            ("extension-docs MCP server", "claude-code-docs MCP server"),
        ],
        dry_run,
    ):
        changes += 1

    # 3. Rename skill directory
    old_skill = repo_root / ".claude/skills/extension-docs"
    new_skill = repo_root / ".claude/skills/claude-code-docs"
    if rename_path(old_skill, new_skill, dry_run):
        changes += 1

    # Update skill content
    skill_path = (new_skill if new_skill.exists() else old_skill) / "SKILL.md"
    if update_text_file(
        skill_path,
        [
            ("name: extension-docs", "name: claude-code-docs"),
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
            ("mcp__extension-docs__reload_extension_docs", "mcp__claude-code-docs__reload_docs"),
            ("extension-docs MCP server", "claude-code-docs MCP server"),
            ("search_extension_docs", "search_docs"),
            ("reload_extension_docs", "reload_docs"),
        ],
        dry_run,
    ):
        changes += 1

    # 4. Update .claude/settings.local.json
    if update_text_file(
        repo_root / ".claude/settings.local.json",
        [
            ("mcp__extension-docs__search_extension_docs", "mcp__claude-code-docs__search_docs"),
        ],
        dry_run,
    ):
        changes += 1

    # 5. Update ~/.claude.json (MCP server config)
    claude_json = home / ".claude.json"
    content = read_file(claude_json)
    if content:
        try:
            data = json.loads(content)
            # Idempotency: skip if already migrated
            if "mcpServers" in data and "claude-code-docs" in data["mcpServers"]:
                log(f"Skipping (already migrated): {claude_json}")
            elif "mcpServers" in data and "extension-docs" in data["mcpServers"]:
                if dry_run:
                    dry_log(f"Would update: {claude_json}")
                    dry_log("  - mcpServers.extension-docs → mcpServers.claude-code-docs")
                else:
                    # Backup before modifying
                    backup_path = claude_json.with_suffix(".json.bak")
                    backup_path.write_text(content)
                    apply_log(f"Backed up: {claude_json} → {backup_path}")
                    data["mcpServers"]["claude-code-docs"] = data["mcpServers"].pop("extension-docs")
                    write_file(claude_json, json.dumps(data, indent=2) + "\n")
                    apply_log(f"Updated: {claude_json}")
                changes += 1
        except json.JSONDecodeError:
            log(f"Skipping (invalid JSON): {claude_json}")

    # 6. Update ~/.claude/skills/extension-docs if it exists
    home_old_skill = home / ".claude/skills/extension-docs"
    home_new_skill = home / ".claude/skills/claude-code-docs"
    if home_old_skill.exists():
        if rename_path(home_old_skill, home_new_skill, dry_run):
            changes += 1
        skill_md = (home_new_skill if home_new_skill.exists() else home_old_skill) / "SKILL.md"
        if skill_md.exists():
            if update_text_file(
                skill_md,
                [
                    ("name: extension-docs", "name: claude-code-docs"),
                    ("mcp__extension-docs__", "mcp__claude-code-docs__"),
                    ("search_extension_docs", "search_docs"),
                    ("reload_extension_docs", "reload_docs"),
                ],
                dry_run,
            ):
                changes += 1

    # 7. Update ~/.claude/hooks/extension-docs-reminder.sh if it exists
    old_hook = home / ".claude/hooks/extension-docs-reminder.sh"
    new_hook = home / ".claude/hooks/claude-code-docs-reminder.sh"
    if old_hook.exists():
        if rename_path(old_hook, new_hook, dry_run):
            changes += 1
        hook_path = new_hook if new_hook.exists() else old_hook
        if update_text_file(
            hook_path,
            [
                ("search_extension_docs", "search_docs"),
                ("reload_extension_docs", "reload_docs"),
                ("extension-docs MCP", "claude-code-docs MCP"),
            ],
            dry_run,
        ):
            changes += 1

    # Summary
    print()
    if dry_run:
        print(f"Summary: {changes} change(s) would be made")
        print("\nTo apply changes, run: uv run scripts/migrate-extension-docs.py --apply")
    else:
        print(f"Summary: {changes} change(s) made")
        print("\nNext steps:")
        print("1. Rebuild MCP server: cd packages/mcp-servers/claude-code-docs && npm run build")
        print("2. Restart Claude Code to pick up new MCP server config")
        print("3. Delete orphaned cache: rm -rf ~/.cache/extension-docs/")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate extension-docs to claude-code-docs"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute changes (default is dry-run)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("Running in dry-run mode. Use --apply to execute changes.\n")

    return migrate(dry_run)


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Make executable and test dry-run**

```bash
chmod +x scripts/migrate-extension-docs.py
uv run scripts/migrate-extension-docs.py
```

Expected: Dry-run output showing all planned changes

**Step 3: Commit**

```bash
git add scripts/migrate-extension-docs.py
git commit -m "$(cat <<'EOF'
feat: add extension-docs to claude-code-docs migration script

Handles renaming of:
- MCP server directory
- Agent and skill files
- Tool references in various config files
- ~/.claude.json MCP server entry

Usage: uv run scripts/migrate-extension-docs.py [--apply]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 3: Production Migration

### Task 10: Execute Migration

**Step 1: Run dry-run to verify**

```bash
uv run scripts/migrate-extension-docs.py
```

Review output to ensure all expected files are listed.

**Step 2: Run migration**

```bash
uv run scripts/migrate-extension-docs.py --apply
```

**Step 3: Rebuild MCP server**

```bash
cd packages/mcp-servers/claude-code-docs && npm run build
```

**Step 4: Run tests**

```bash
cd packages/mcp-servers/claude-code-docs && npm test
```

Expected: PASS

**Step 5: Commit all changes**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat: complete extension-docs → claude-code-docs migration

Executed migration script to rename:
- packages/mcp-servers/extension-docs/ → claude-code-docs/
- .claude/agents/extension-docs-researcher.md → claude-code-docs-researcher.md
- .claude/skills/extension-docs/ → claude-code-docs/
- Updated all tool references and MCP config

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 11: Verify Search Works

**Important:** If Claude Code was running during migration, you must restart it to pick up the new MCP server configuration.

**Step 1: Start or restart Claude Code and test search**

Test these queries to verify the migration worked:

```
search_docs("hooks PreToolUse")  # Should return hooks docs
search_docs("quickstart")        # Should return getting-started docs (new category)
search_docs("bedrock")           # Should return providers docs (new category)
search_docs("permissions", category="security")  # Category filter test
```

**Step 2: Test category alias normalization**

```
search_docs("test", category="subagents")  # Should normalize to 'agents'
search_docs("test", category="claude-md")  # Should normalize to 'memory'
```

---

## Phase 4: Cleanup

### Task 12: Delete Orphaned Cache

**Step 1: Delete old cache directory**

```bash
rm -rf ~/.cache/extension-docs/
```

**Step 2: Verify old tool names error**

Try calling old tool name in Claude Code:
```
mcp__extension-docs__search_extension_docs("test")
```

Expected: Error (tool not found)

---

## Verification Checklist

- [ ] All 24 categories defined in `src/categories.ts`
- [ ] `deriveCategory()` uses `SECTION_TO_CATEGORY` mapping
- [ ] Filter module deleted (`src/filter.ts`, `tests/filter.test.ts`)
- [ ] Loader passes all sections through (no filtering)
- [ ] Server name is `claude-code-docs`
- [ ] Tool names are `search_docs` and `reload_docs`
- [ ] Category aliases normalize correctly
- [ ] Cache directory is `~/.cache/claude-code-docs/`
- [ ] Package name is `@claude-tools/claude-code-docs`
- [ ] All tests pass
- [ ] Migration script runs without error
- [ ] Search returns results for new categories
- [ ] Old cache directory deleted
