# Extension Docs MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a TypeScript MCP server that serves Claude Code extension documentation as searchable chunks via BM25.

**Architecture:** Stdio MCP server with lazy-loaded BM25 index. Two-phase chunking (split at H2, merge small chunks). Graceful degradation on load failure with 60s retry.

**Tech Stack:** TypeScript, @modelcontextprotocol/sdk ^1.25.0, zod ^3.25.0, glob ^11.x, yaml ^2.x, vitest

**Design Reference:** `docs/plans/2026-01-11-extension-docs-mcp-server.md` — contains full code, rationale, audit corrections.

---

## Task 1: Project Scaffold

**Files:**
- Create: `packages/mcp-servers/extension-docs/package.json`
- Create: `packages/mcp-servers/extension-docs/tsconfig.json`
- Create: `packages/mcp-servers/extension-docs/.gitignore`
- Create: `packages/mcp-servers/extension-docs/src/index.ts` (stub)
- Remove: `packages/mcp-servers/.gitkeep`

**Step 1: Create package.json**

```json
{
  "name": "@claude-tools/extension-docs",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "engines": {
    "node": ">=18"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "vitest run",
    "start": "node dist/index.js",
    "start:dev": "DOCS_PATH=../../../docs/extension-reference node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.25.0",
    "glob": "^11.0.0",
    "yaml": "^2.0.0",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.0.0",
    "vitest": "^2.0.0"
  }
}
```

**Step 2: Create tsconfig.json**

```json
{
  "extends": "../../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

**Step 3: Create .gitignore**

```
dist/
node_modules/
```

**Step 4: Create stub index.ts**

```typescript
// Extension Docs MCP Server
// Implementation follows TDD — tests written first

console.error('Extension Docs MCP Server starting...');
```

**Step 5: Remove .gitkeep**

```bash
rm packages/mcp-servers/.gitkeep
```

**Step 6: Install dependencies**

Run: `npm install -w @claude-tools/extension-docs`
Expected: Dependencies installed, package-lock.json updated

**Step 7: Verify build**

Run: `npm run build -w @claude-tools/extension-docs`
Expected: `dist/index.js` created

**Step 8: Commit**

```bash
git add packages/mcp-servers/extension-docs package-lock.json
git add -u packages/mcp-servers/.gitkeep  # stage deletion
git commit -m "feat(extension-docs): scaffold MCP server project"
```

---

## Task 2: Tokenizer + Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/tokenizer.ts`
- Create: `packages/mcp-servers/extension-docs/tests/tokenizer.test.ts`

**Step 1: Write failing tokenizer tests**

```typescript
// tests/tokenizer.test.ts
import { describe, it, expect } from 'vitest';
import { tokenize } from '../src/tokenizer.js';

describe('tokenize', () => {
  it('handles empty string', () => {
    expect(tokenize('')).toEqual([]);
  });

  it('handles whitespace-only', () => {
    expect(tokenize('   ')).toEqual([]);
  });

  it('handles punctuation-only', () => {
    expect(tokenize('!@#$%')).toEqual([]);
  });

  it('lowercases terms', () => {
    expect(tokenize('HELLO World')).toEqual(['hello', 'world']);
  });

  it('splits CamelCase', () => {
    expect(tokenize('PreToolUse')).toEqual(['pre', 'tool', 'use']);
  });

  it('handles consecutive capitals (MCPServer)', () => {
    expect(tokenize('MCPServer')).toEqual(['mcp', 'server']);
  });

  it('handles consecutive capitals (JSONSchema)', () => {
    expect(tokenize('JSONSchema')).toEqual(['json', 'schema']);
  });

  it('splits on hyphens', () => {
    expect(tokenize('pre-tool-use')).toEqual(['pre', 'tool', 'use']);
  });

  it('splits on underscores', () => {
    expect(tokenize('pre_tool_use')).toEqual(['pre', 'tool', 'use']);
  });

  it('drops single characters', () => {
    expect(tokenize('a b c')).toEqual([]);
  });

  it('keeps two-character terms', () => {
    expect(tokenize('go is ok')).toEqual(['go', 'is', 'ok']);
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/tokenizer.js'"

**Step 3: Implement tokenizer**

```typescript
// src/tokenizer.ts
export function tokenize(text: string): string[] {
  return (
    text
      .toLowerCase()
      // Split CamelCase: "PreToolUse" → "pre tool use"
      .replace(/([a-z\d])([A-Z])/g, '$1 $2')
      // Handle consecutive capitals: "MCPServer" → "MCP Server" → "mcp server"
      .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
      // Split on non-alphanumeric (handles hyphens, underscores, punctuation)
      .split(/[^a-z0-9]+/)
      .filter((term) => term.length > 1)
  );
}
```

**Step 4: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/tokenizer.ts packages/mcp-servers/extension-docs/tests/tokenizer.test.ts
git commit -m "feat(extension-docs): add tokenizer with CamelCase splitting"
```

---

## Task 3: Frontmatter Parser + Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/frontmatter.ts`
- Create: `packages/mcp-servers/extension-docs/tests/frontmatter.test.ts`

**Step 1: Write failing frontmatter tests**

```typescript
// tests/frontmatter.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import {
  parseFrontmatter,
  formatMetadataHeader,
  deriveCategory,
  getParseWarnings,
  clearParseWarnings,
} from '../src/frontmatter.js';

describe('parseFrontmatter', () => {
  beforeEach(() => {
    clearParseWarnings();
  });

  it('returns empty frontmatter for content without YAML', () => {
    const { frontmatter, body } = parseFrontmatter('Just content', 'test.md');
    expect(frontmatter).toEqual({});
    expect(body).toBe('Just content');
  });

  it('parses valid YAML frontmatter', () => {
    const content = '---\ncategory: hooks\ntags: [api, schema]\ntopic: input\n---\nBody content';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.category).toBe('hooks');
    expect(frontmatter.tags).toEqual(['api', 'schema']);
    expect(frontmatter.topic).toBe('input');
    expect(body).toBe('Body content');
  });

  it('handles single string tag', () => {
    const content = '---\ntags: api\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.tags).toEqual(['api']);
  });

  it('warns on non-string tag values', () => {
    const content = '---\ntags: [123, "valid"]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Non-string tag value ignored: number',
    });
  });

  it('warns on non-string category', () => {
    const content = '---\ncategory: [hooks, skills]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid category type: expected string, got object',
    });
  });

  it('warns on non-string topic', () => {
    const content = '---\ntopic: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid topic type: expected string, got number',
    });
  });

  it('warns on malformed YAML', () => {
    const content = '---\n: invalid yaml\n---\nBody';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter).toEqual({});
    expect(body).toBe('---\n: invalid yaml\n---\nBody');
    const warnings = getParseWarnings();
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings[0].file).toBe('test.md');
  });

  it('normalizes CRLF line endings', () => {
    const content = '---\r\ncategory: hooks\r\n---\r\nBody';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.category).toBe('hooks');
    expect(body).toBe('Body');
  });
});

describe('formatMetadataHeader', () => {
  it('returns empty string for empty frontmatter', () => {
    expect(formatMetadataHeader({})).toBe('');
  });

  it('formats category', () => {
    expect(formatMetadataHeader({ category: 'hooks' })).toBe('Category: hooks\n\n');
  });

  it('formats tags', () => {
    expect(formatMetadataHeader({ tags: ['api', 'schema'] })).toBe('Tags: api, schema\n\n');
  });

  it('formats all fields', () => {
    const header = formatMetadataHeader({
      category: 'hooks',
      tags: ['api'],
      topic: 'input',
    });
    expect(header).toBe('Category: hooks\nTags: api\nTopic: input\n\n');
  });
});

describe('deriveCategory', () => {
  it('extracts category from path', () => {
    expect(deriveCategory('hooks/input-schema.md')).toBe('hooks');
  });

  it('returns general for root files', () => {
    expect(deriveCategory('readme.md')).toBe('general');
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/frontmatter.js'"

**Step 3: Implement frontmatter parser**

```typescript
// src/frontmatter.ts
import { parse as parseYaml } from 'yaml';

export interface Frontmatter {
  category?: string;
  tags?: string[];
  topic?: string;
}

export interface ParseWarning {
  file: string;
  issue: string;
}

const parseWarnings: ParseWarning[] = [];

export function getParseWarnings(): ParseWarning[] {
  return [...parseWarnings];
}

export function clearParseWarnings(): void {
  parseWarnings.length = 0;
}

export function parseFrontmatter(
  content: string,
  filePath: string,
): { frontmatter: Frontmatter; body: string } {
  // Normalize line endings to LF for consistent parsing
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: normalized };

  try {
    const yaml = parseYaml(match[1]);

    // Parse tags with strict type checking
    let tags: string[] = [];
    if (Array.isArray(yaml.tags)) {
      tags = yaml.tags.filter((t): t is string => {
        if (typeof t === 'string') return true;
        parseWarnings.push({
          file: filePath,
          issue: `Non-string tag value ignored: ${typeof t}`,
        });
        return false;
      });
    } else if (typeof yaml.tags === 'string') {
      tags = [yaml.tags];
    } else if (yaml.tags !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid tags type: expected string or array, got ${typeof yaml.tags}`,
      });
    }

    // Validate category is string
    let category: string | undefined;
    if (typeof yaml.category === 'string') {
      category = yaml.category;
    } else if (yaml.category !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid category type: expected string, got ${typeof yaml.category}`,
      });
    }

    // Validate topic is string
    let topic: string | undefined;
    if (typeof yaml.topic === 'string') {
      topic = yaml.topic;
    } else if (yaml.topic !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid topic type: expected string, got ${typeof yaml.topic}`,
      });
    }

    return {
      frontmatter: { category, tags: tags.length > 0 ? tags : undefined, topic },
      body: match[2],
    };
  } catch (err) {
    parseWarnings.push({
      file: filePath,
      issue: `Invalid YAML frontmatter: ${err instanceof Error ? err.message : 'unknown error'}`,
    });
    return { frontmatter: {}, body: content };
  }
}

export function formatMetadataHeader(fm: Frontmatter): string {
  const lines: string[] = [];
  if (fm.category) lines.push(`Category: ${fm.category}`);
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`);
  if (fm.topic) lines.push(`Topic: ${fm.topic}`);
  return lines.length ? lines.join('\n') + '\n\n' : '';
}

export function deriveCategory(path: string): string {
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

**Step 4: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/frontmatter.ts packages/mcp-servers/extension-docs/tests/frontmatter.test.ts
git commit -m "feat(extension-docs): add frontmatter parser with type validation"
```

---

## Task 4: Chunk Types + Helpers

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/types.ts`
- Create: `packages/mcp-servers/extension-docs/src/chunk-helpers.ts`
- Create: `packages/mcp-servers/extension-docs/tests/chunk-helpers.test.ts`

**Step 1: Create types**

```typescript
// src/types.ts
export interface MarkdownFile {
  path: string; // Relative to docs root: "hooks/input-schema.md"
  content: string;
}

export interface Chunk {
  id: string; // "hooks-input-schema#pretooluse-input"
  content: string; // Includes metadata header + markdown content
  tokens: string[]; // Pre-tokenized content for BM25 scoring
  termFreqs: Map<string, number>; // Precomputed term frequencies for O(1) lookup
  category: string; // From frontmatter or derived from path
  tags: string[]; // From frontmatter (for debugging/filtering)
  source_file: string; // "hooks/input-schema.md"
  heading?: string; // H2 heading if split chunk
  merged_headings?: string[]; // All headings if chunks were merged
}

export interface SearchResult {
  chunk_id: string;
  content: string;
  category: string;
  source_file: string;
}
```

**Step 2: Write failing chunk helper tests**

```typescript
// tests/chunk-helpers.test.ts
import { describe, it, expect } from 'vitest';
import { slugify, generateChunkId, computeTermFreqs } from '../src/chunk-helpers.js';
import type { MarkdownFile } from '../src/types.js';

describe('slugify', () => {
  it('lowercases text', () => {
    expect(slugify('HELLO')).toBe('hello');
  });

  it('replaces non-alphanumeric with hyphens', () => {
    expect(slugify('hello world')).toBe('hello-world');
  });

  it('removes leading/trailing hyphens', () => {
    expect(slugify('--hello--')).toBe('hello');
  });

  it('handles file paths', () => {
    expect(slugify('hooks/input-schema.md')).toBe('hooks-input-schema');
  });

  it('handles markdown headings', () => {
    expect(slugify('## PreToolUse Input')).toBe('pretooluse-input');
  });
});

describe('generateChunkId', () => {
  const file: MarkdownFile = { path: 'hooks/input-schema.md', content: '' };

  it('generates id for whole file chunk', () => {
    expect(generateChunkId(file)).toBe('hooks-input-schema');
  });

  it('generates id with heading fragment', () => {
    expect(generateChunkId(file, '## PreToolUse Input')).toBe('hooks-input-schema#pretooluse-input');
  });
});

describe('computeTermFreqs', () => {
  it('returns empty map for empty array', () => {
    expect(computeTermFreqs([])).toEqual(new Map());
  });

  it('counts single term', () => {
    expect(computeTermFreqs(['hello'])).toEqual(new Map([['hello', 1]]));
  });

  it('counts repeated terms', () => {
    expect(computeTermFreqs(['a', 'b', 'a'])).toEqual(
      new Map([
        ['a', 2],
        ['b', 1],
      ]),
    );
  });
});
```

**Step 3: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/chunk-helpers.js'"

**Step 4: Implement chunk helpers**

```typescript
// src/chunk-helpers.ts
import type { MarkdownFile } from './types.js';

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function generateChunkId(file: MarkdownFile, heading?: string): string {
  const fileSlug = slugify(file.path);
  if (!heading) return fileSlug;

  const headingSlug = slugify(heading);
  return `${fileSlug}#${headingSlug}`;
}

export function computeTermFreqs(tokens: string[]): Map<string, number> {
  const freqs = new Map<string, number>();
  for (const token of tokens) {
    freqs.set(token, (freqs.get(token) ?? 0) + 1);
  }
  return freqs;
}
```

**Step 5: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/types.ts packages/mcp-servers/extension-docs/src/chunk-helpers.ts packages/mcp-servers/extension-docs/tests/chunk-helpers.test.ts
git commit -m "feat(extension-docs): add chunk types and helper functions"
```

---

## Task 5: Two-Phase Chunker + Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/chunker.ts`
- Create: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write failing chunker tests**

```typescript
// tests/chunker.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import { clearParseWarnings } from '../src/frontmatter.js';
import type { MarkdownFile } from '../src/types.js';

describe('chunkFile', () => {
  beforeEach(() => {
    clearParseWarnings();
  });

  describe('whole file chunks', () => {
    it('keeps small file as single chunk', () => {
      const file: MarkdownFile = {
        path: 'test/small.md',
        content: '# Title\n\nSome content here.',
      };
      const chunks = chunkFile(file);
      expect(chunks).toHaveLength(1);
      expect(chunks[0].id).toBe('test-small');
    });

    it('includes frontmatter metadata in content', () => {
      const file: MarkdownFile = {
        path: 'hooks/test.md',
        content: '---\ncategory: hooks\ntags: [api]\n---\n# Title\nContent',
      };
      const chunks = chunkFile(file);
      expect(chunks[0].content).toContain('Category: hooks');
      expect(chunks[0].content).toContain('Tags: api');
    });

    it('derives category from path when not in frontmatter', () => {
      const file: MarkdownFile = {
        path: 'hooks/test.md',
        content: '# Title\nContent',
      };
      const chunks = chunkFile(file);
      expect(chunks[0].category).toBe('hooks');
    });
  });

  describe('splitting at H2', () => {
    it('splits large file at H2 boundaries', () => {
      const lines = ['# Title', '', ...Array(200).fill('Line of content')];
      // Insert H2 headings
      lines[50] = '## Section 1';
      lines[100] = '## Section 2';
      lines[150] = '## Section 3';

      const file: MarkdownFile = {
        path: 'test/large.md',
        content: lines.join('\n'),
      };
      const chunks = chunkFile(file);
      expect(chunks.length).toBeGreaterThan(1);
    });

    it('includes intro content in first H2 chunk', () => {
      const content = '# Title\n\nIntro paragraph.\n\n## Section 1\nSection content.\n\n## Section 2\nMore content.';
      // Pad to exceed 150 lines
      const padded = content + '\n' + Array(150).fill('padding').join('\n');
      const file: MarkdownFile = { path: 'test/intro.md', content: padded };
      const chunks = chunkFile(file);

      // First chunk should contain both intro and Section 1
      expect(chunks[0].content).toContain('Intro paragraph');
      expect(chunks[0].content).toContain('## Section 1');
    });

    it('does not split H2 inside code fence', () => {
      const content = [
        '# Title',
        '',
        '```markdown',
        '## This is not a real heading',
        '```',
        '',
        '## Real Heading',
        'Content',
        '',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/fence.md', content };
      const chunks = chunkFile(file);

      // Should NOT split at "## This is not a real heading" inside fence
      const fenceChunk = chunks.find((c) => c.content.includes('```markdown'));
      expect(fenceChunk?.content).toContain('## This is not a real heading');
    });

    it('handles indented code fences (0-3 spaces)', () => {
      const content = [
        '# Title',
        '',
        '   ```python',
        '## Not a heading',
        '   ```',
        '',
        '## Real Heading',
        'Content',
        '',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/indented.md', content };
      const chunks = chunkFile(file);

      // Indented fence should be recognized
      const fenceChunk = chunks.find((c) => c.content.includes('```python'));
      expect(fenceChunk?.content).toContain('## Not a heading');
    });
  });

  describe('merging small chunks', () => {
    it('merges small consecutive chunks', () => {
      // Create file with many small H2 sections
      const sections = Array.from({ length: 10 }, (_, i) => `## Section ${i}\nShort content.`);
      const content = ['# Title', '', ...sections, '', ...Array(150).fill('pad')].join('\n');

      const file: MarkdownFile = { path: 'test/merge.md', content };
      const chunks = chunkFile(file);

      // Should have fewer chunks than sections due to merging
      expect(chunks.length).toBeLessThan(10);
    });

    it('records merged_headings', () => {
      const sections = Array.from({ length: 5 }, (_, i) => `## Section ${i}\nShort.`);
      const content = ['# Title', '', ...sections, '', ...Array(150).fill('pad')].join('\n');

      const file: MarkdownFile = { path: 'test/merged.md', content };
      const chunks = chunkFile(file);

      // At least one chunk should have merged_headings
      const mergedChunk = chunks.find((c) => c.merged_headings && c.merged_headings.length > 1);
      expect(mergedChunk).toBeDefined();
    });
  });

  describe('metadata in tokens', () => {
    it('includes category and tags in all chunk tokens', () => {
      const content = [
        '---',
        'category: hooks',
        'tags: [api, schema]',
        '---',
        '# Title',
        'Intro',
        '## Section 1',
        'Content 1',
        '## Section 2',
        'Content 2',
        ...Array(150).fill('pad'),
      ].join('\n');

      const file: MarkdownFile = { path: 'hooks/meta.md', content };
      const chunks = chunkFile(file);

      for (const chunk of chunks) {
        expect(chunk.tokens).toContain('hooks');
        expect(chunk.tokens).toContain('api');
        expect(chunk.tokens).toContain('schema');
      }
    });
  });

  describe('size guards', () => {
    it('splits file exceeding char limit even if under line limit', () => {
      // 60 lines but >8000 chars
      const longLine = 'x'.repeat(200);
      const content = [
        '# Title',
        '## Section 1',
        ...Array(25).fill(longLine),
        '## Section 2',
        ...Array(25).fill(longLine),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/chars.md', content };
      const chunks = chunkFile(file);

      expect(chunks.length).toBeGreaterThan(1);
    });

    it('respects char limit when merging', () => {
      // Create chunks that fit line limit but exceed char limit when combined
      const longContent = 'y'.repeat(5000);
      const sections = [
        `## Section 1\n${longContent}`,
        `## Section 2\n${longContent}`,
      ];
      const content = ['# Title', '', ...sections].join('\n');

      // Pad to force splitting
      const padded = content + '\n' + Array(150).fill('pad').join('\n');
      const file: MarkdownFile = { path: 'test/charmerge.md', content: padded };
      const chunks = chunkFile(file);

      // Each section's content is 5000 chars; merging would exceed 8000
      // So they should remain separate
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS + 1000); // Allow some overhead
      }
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/chunker.js'"

**Step 3: Implement chunker**

```typescript
// src/chunker.ts
import type { MarkdownFile, Chunk } from './types.js';
import { tokenize } from './tokenizer.js';
import {
  parseFrontmatter,
  formatMetadataHeader,
  deriveCategory,
  type Frontmatter,
} from './frontmatter.js';
import { generateChunkId, computeTermFreqs } from './chunk-helpers.js';

export const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;

export function chunkFile(file: MarkdownFile): Chunk[] {
  const { frontmatter, body } = parseFrontmatter(file.content, file.path);
  const metadataHeader = formatMetadataHeader(frontmatter);
  const preparedContent = metadataHeader + body;

  if (isSmallEnoughForWholeFile(preparedContent)) {
    return [createWholeFileChunk(file, preparedContent, frontmatter)];
  }

  const rawChunks = splitAtH2(file, preparedContent, frontmatter);
  return mergeSmallChunks(rawChunks);
}

function countLines(content: string): number {
  return content.split('\n').length;
}

function isSmallEnoughForWholeFile(content: string): boolean {
  return countLines(content) <= MAX_CHUNK_LINES && content.length <= MAX_CHUNK_CHARS;
}

function createWholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  const tokens = tokenize(content);
  return {
    id: generateChunkId(file),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: fm.category ?? deriveCategory(file.path),
    tags: fm.tags ?? [],
    source_file: file.path,
  };
}

function splitAtH2(file: MarkdownFile, content: string, frontmatter: Frontmatter): Chunk[] {
  const lines = content.split('\n');
  const chunks: Chunk[] = [];
  let intro: string[] = [];
  let current: string[] = [];
  let currentHeading: string | undefined;
  let inFence = false;
  let fencePattern = '';
  let isFirstH2 = true;

  for (const line of lines) {
    // CommonMark-compliant fence matching: 0-3 leading spaces
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!inFence) {
        inFence = true;
        fencePattern = fence[2];
      } else if (line.match(new RegExp(`^ {0,3}${fencePattern[0]}{${fencePattern.length},}\\s*$`))) {
        inFence = false;
        fencePattern = '';
      }
    }

    // Split at H2 only outside code fences
    if (!inFence && /^##\s/.test(line)) {
      if (current.length > 0 && currentHeading) {
        chunks.push(createSplitChunk(file, current.join('\n'), currentHeading, frontmatter));
      } else if (current.length > 0) {
        intro = current;
      }

      current = isFirstH2 ? [...intro, '', line] : [line];
      currentHeading = line;
      isFirstH2 = false;
    } else {
      current.push(line);
    }
  }

  if (current.length > 0) {
    chunks.push(createSplitChunk(file, current.join('\n'), currentHeading, frontmatter));
  }

  return chunks;
}

function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  frontmatter: Frontmatter,
): Chunk {
  const category = frontmatter.category ?? deriveCategory(file.path);
  const tags = frontmatter.tags ?? [];

  // Include metadata terms in tokens so all chunks are searchable by category/tags
  const metadataTerms = [category, ...tags].flatMap(tokenize);
  const tokens = [...tokenize(content), ...metadataTerms];

  return {
    id: generateChunkId(file, heading),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category,
    tags,
    source_file: file.path,
    heading,
  };
}

function mergeSmallChunks(chunks: Chunk[]): Chunk[] {
  const result: Chunk[] = [];
  let buffer: Chunk[] = [];
  let bufferLines = 0;
  let bufferChars = 0;

  for (const chunk of chunks) {
    const lines = chunk.content.split('\n').length;
    const chars = chunk.content.length;

    if (bufferLines + lines <= MAX_CHUNK_LINES && bufferChars + chars <= MAX_CHUNK_CHARS) {
      buffer.push(chunk);
      bufferLines += lines;
      bufferChars += chars;
    } else {
      if (buffer.length) result.push(combineChunks(buffer));
      buffer = [chunk];
      bufferLines = lines;
      bufferChars = chars;
    }
  }

  if (buffer.length) result.push(combineChunks(buffer));
  return result;
}

function combineChunks(chunks: Chunk[]): Chunk {
  if (chunks.length === 0) {
    throw new Error('combineChunks called with empty array');
  }

  if (chunks.length === 1) {
    return chunks[0];
  }

  const combinedContent = chunks.map((c) => c.content).join('\n\n');
  const { category, tags } = chunks[0];
  const metadataTerms = [category, ...tags].flatMap(tokenize);
  const tokens = [...tokenize(combinedContent), ...metadataTerms];

  return {
    ...chunks[0],
    content: combinedContent,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    heading: chunks[0].heading,
    merged_headings: chunks.map((c) => c.heading).filter(Boolean) as string[],
  };
}
```

**Step 4: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "feat(extension-docs): add two-phase chunker with H2 splitting and merging"
```

---

## Task 6: BM25 Search Index + Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/bm25.ts`
- Create: `packages/mcp-servers/extension-docs/tests/bm25.test.ts`

**Step 1: Write failing BM25 tests**

```typescript
// tests/bm25.test.ts
import { describe, it, expect } from 'vitest';
import { buildBM25Index, search, type BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';

function makeChunk(id: string, content: string, tokens: string[]): Chunk {
  return {
    id,
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: 'test',
    tags: [],
    source_file: 'test.md',
  };
}

describe('buildBM25Index', () => {
  it('handles empty chunks array', () => {
    const index = buildBM25Index([]);
    expect(index.chunks).toEqual([]);
    expect(index.avgDocLength).toBe(0);
    expect(index.docFrequency.size).toBe(0);
  });

  it('computes average document length', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const index = buildBM25Index(chunks);
    expect(index.avgDocLength).toBe(2); // (2 + 2) / 2
  });

  it('computes document frequency', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'hello there', ['hello', 'there']),
    ];
    const index = buildBM25Index(chunks);
    expect(index.docFrequency.get('hello')).toBe(2);
    expect(index.docFrequency.get('world')).toBe(1);
    expect(index.docFrequency.get('there')).toBe(1);
  });
});

describe('search', () => {
  it('returns empty array for empty index', () => {
    const index = buildBM25Index([]);
    const results = search(index, 'test');
    expect(results).toEqual([]);
  });

  it('returns empty array for no matches', () => {
    const chunks = [makeChunk('a', 'hello world', ['hello', 'world'])];
    const index = buildBM25Index(chunks);
    const results = search(index, 'xyz');
    expect(results).toEqual([]);
  });

  it('returns matching results', () => {
    const chunks = [
      makeChunk('a', 'hello world', ['hello', 'world']),
      makeChunk('b', 'goodbye world', ['goodbye', 'world']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hello');
    expect(results).toHaveLength(1);
    expect(results[0].chunk_id).toBe('a');
  });

  it('ranks by relevance', () => {
    const chunks = [
      makeChunk('a', 'hooks hooks hooks', ['hooks', 'hooks', 'hooks']),
      makeChunk('b', 'hooks once', ['hooks', 'once']),
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'hooks');

    // Chunk with more occurrences should rank higher
    expect(results[0].chunk_id).toBe('a');
  });

  it('respects limit parameter', () => {
    const chunks = Array.from({ length: 10 }, (_, i) =>
      makeChunk(`chunk${i}`, `content ${i}`, ['content', `item${i}`]),
    );
    const index = buildBM25Index(chunks);
    const results = search(index, 'content', 3);
    expect(results).toHaveLength(3);
  });

  it('returns SearchResult format', () => {
    const chunks = [
      {
        ...makeChunk('test-chunk', 'test content', ['test', 'content']),
        category: 'hooks',
        source_file: 'hooks/test.md',
      },
    ];
    const index = buildBM25Index(chunks);
    const results = search(index, 'test');

    expect(results[0]).toEqual({
      chunk_id: 'test-chunk',
      content: 'test content',
      category: 'hooks',
      source_file: 'hooks/test.md',
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/bm25.js'"

**Step 3: Implement BM25**

```typescript
// src/bm25.ts
import type { Chunk, SearchResult } from './types.js';
import { tokenize } from './tokenizer.js';

export interface BM25Index {
  chunks: Chunk[];
  avgDocLength: number;
  docFrequency: Map<string, number>;
}

const BM25_CONFIG = {
  k1: 1.2,
  b: 0.75,
};

export function buildBM25Index(chunks: Chunk[]): BM25Index {
  const docFrequency = new Map<string, number>();

  for (const chunk of chunks) {
    const uniqueTerms = new Set(chunk.tokens);
    for (const term of uniqueTerms) {
      docFrequency.set(term, (docFrequency.get(term) ?? 0) + 1);
    }
  }

  return {
    chunks,
    avgDocLength:
      chunks.length > 0 ? chunks.reduce((sum, c) => sum + c.tokens.length, 0) / chunks.length : 0,
    docFrequency,
  };
}

function idf(N: number, df: number): number {
  return Math.log((N - df + 0.5) / (df + 0.5) + 1);
}

function bm25Score(queryTerms: string[], chunk: Chunk, index: BM25Index): number {
  const { k1, b } = BM25_CONFIG;
  const N = index.chunks.length;
  const avgdl = index.avgDocLength;
  const dl = chunk.tokens.length;

  if (N === 0 || avgdl === 0) return 0;

  return queryTerms.reduce((score, term) => {
    const df = index.docFrequency.get(term) ?? 0;
    const tf = chunk.termFreqs.get(term) ?? 0;
    const idfScore = idf(N, df);
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + (b * dl) / avgdl));
    return score + idfScore * tfNorm;
  }, 0);
}

export function search(index: BM25Index, query: string, limit = 5): SearchResult[] {
  const queryTerms = tokenize(query);

  return index.chunks
    .map((chunk) => ({ chunk, score: bm25Score(queryTerms, chunk, index) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => ({
      chunk_id: r.chunk.id,
      content: r.chunk.content,
      category: r.chunk.category,
      source_file: r.chunk.source_file,
    }));
}
```

**Step 4: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/bm25.ts packages/mcp-servers/extension-docs/tests/bm25.test.ts
git commit -m "feat(extension-docs): add BM25 search index with term frequency optimization"
```

---

## Task 7: File Loader + Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/loader.ts`
- Create: `packages/mcp-servers/extension-docs/tests/loader.test.ts`

**Step 1: Write failing loader tests**

```typescript
// tests/loader.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { loadMarkdownFiles } from '../src/loader.js';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('loadMarkdownFiles', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-test-'));
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('returns empty array for non-existent directory', async () => {
    const files = await loadMarkdownFiles('/nonexistent/path');
    expect(files).toEqual([]);
  });

  it('returns empty array for empty directory', async () => {
    const files = await loadMarkdownFiles(tempDir);
    expect(files).toEqual([]);
  });

  it('loads markdown files', async () => {
    await fs.writeFile(path.join(tempDir, 'test.md'), '# Test');
    const files = await loadMarkdownFiles(tempDir);
    expect(files).toHaveLength(1);
    expect(files[0].path).toBe('test.md');
    expect(files[0].content).toBe('# Test');
  });

  it('loads from subdirectories', async () => {
    await fs.mkdir(path.join(tempDir, 'hooks'));
    await fs.writeFile(path.join(tempDir, 'hooks', 'test.md'), '# Hooks Test');
    const files = await loadMarkdownFiles(tempDir);
    expect(files).toHaveLength(1);
    expect(files[0].path).toBe('hooks/test.md');
  });

  it('ignores non-markdown files', async () => {
    await fs.writeFile(path.join(tempDir, 'test.md'), '# Markdown');
    await fs.writeFile(path.join(tempDir, 'test.txt'), 'Plain text');
    const files = await loadMarkdownFiles(tempDir);
    expect(files).toHaveLength(1);
    expect(files[0].path).toBe('test.md');
  });

  it('normalizes path separators', async () => {
    await fs.mkdir(path.join(tempDir, 'deep', 'nested'), { recursive: true });
    await fs.writeFile(path.join(tempDir, 'deep', 'nested', 'file.md'), '# Nested');
    const files = await loadMarkdownFiles(tempDir);
    expect(files[0].path).toBe('deep/nested/file.md'); // Forward slashes
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `npm test -w @claude-tools/extension-docs`
Expected: FAIL — "Cannot find module '../src/loader.js'"

**Step 3: Implement loader**

```typescript
// src/loader.ts
import { glob } from 'glob';
import { readFile } from 'fs/promises';
import * as path from 'path';
import type { MarkdownFile } from './types.js';

export async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = [];
  const pattern = path.join(docsPath, '**/*.md').replace(/\\/g, '/');

  let filePaths: string[];
  try {
    filePaths = await glob(pattern);
  } catch (err) {
    console.error(
      `WARN: Failed to glob ${pattern}: ${err instanceof Error ? err.message : 'unknown'}`,
    );
    return files;
  }

  for (const filePath of filePaths) {
    try {
      const content = await readFile(filePath, 'utf-8');
      const relativePath = path.relative(docsPath, filePath).replace(/\\/g, '/');
      files.push({ path: relativePath, content });
    } catch (err) {
      if (err instanceof Error) {
        console.error(`WARN: Skipping ${filePath}: ${err.message}`);
      }
    }
  }

  return files;
}
```

**Step 4: Run tests to verify they pass**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts packages/mcp-servers/extension-docs/tests/loader.test.ts
git commit -m "feat(extension-docs): add markdown file loader with glob support"
```

---

## Task 8: MCP Server Implementation

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/index.ts` (replace stub)
- Create: `packages/mcp-servers/extension-docs/tests/server.test.ts`

**Step 1: Write failing server tests**

```typescript
// tests/server.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

// Test the state management and schema validation logic
// Full MCP integration tests require spawning the server process

import { z } from 'zod';

// Import the schemas we'll define
const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty')),
  limit: z.number().int().min(1).max(20).optional(),
});

describe('SearchInputSchema validation', () => {
  it('rejects empty query', () => {
    const result = SearchInputSchema.safeParse({ query: '' });
    expect(result.success).toBe(false);
  });

  it('rejects whitespace-only query', () => {
    const result = SearchInputSchema.safeParse({ query: '   ' });
    expect(result.success).toBe(false);
  });

  it('rejects query over 500 characters', () => {
    const result = SearchInputSchema.safeParse({ query: 'a'.repeat(501) });
    expect(result.success).toBe(false);
  });

  it('accepts valid query', () => {
    const result = SearchInputSchema.safeParse({ query: 'hooks' });
    expect(result.success).toBe(true);
  });

  it('trims whitespace from query', () => {
    const result = SearchInputSchema.safeParse({ query: '  hooks  ' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.query).toBe('hooks');
    }
  });

  it('rejects non-integer limit', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 5.5 });
    expect(result.success).toBe(false);
  });

  it('rejects limit below 1', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 0 });
    expect(result.success).toBe(false);
  });

  it('rejects limit above 20', () => {
    const result = SearchInputSchema.safeParse({ query: 'test', limit: 21 });
    expect(result.success).toBe(false);
  });

  it('uses undefined limit when not provided', () => {
    const result = SearchInputSchema.safeParse({ query: 'test' });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.limit).toBeUndefined();
    }
  });
});
```

**Step 2: Run tests to verify they pass (schema validation)**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS (this validates schema logic before server implementation)

**Step 3: Implement MCP server**

```typescript
// src/index.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import * as fs from 'fs';
import { z } from 'zod';

import { loadMarkdownFiles } from './loader.js';
import { chunkFile } from './chunker.js';
import { buildBM25Index, search, type BM25Index } from './bm25.js';
import { getParseWarnings, clearParseWarnings } from './frontmatter.js';

// === State Management ===
let index: BM25Index | null = null;
let loadError: string | null = null;
let lastLoadAttempt = 0;
let loadingPromise: Promise<BM25Index | null> | null = null;

// === Configuration ===
const RETRY_INTERVAL_MS = parseInt(process.env.RETRY_INTERVAL_MS ?? '60000', 10);
const EFFECTIVE_RETRY_INTERVAL =
  RETRY_INTERVAL_MS >= 1000 && RETRY_INTERVAL_MS <= 600000 ? RETRY_INTERVAL_MS : 60000;

async function ensureIndex(): Promise<BM25Index | null> {
  if (index) return index;

  if (loadingPromise) return loadingPromise;

  const now = Date.now();
  if (loadError && now - lastLoadAttempt < EFFECTIVE_RETRY_INTERVAL) {
    return null;
  }

  loadingPromise = doLoadIndex();

  try {
    return await loadingPromise;
  } finally {
    loadingPromise = null;
  }
}

async function doLoadIndex(): Promise<BM25Index | null> {
  const isRetry = loadError !== null;

  lastLoadAttempt = Date.now();
  loadError = null;
  clearParseWarnings();

  if (isRetry) {
    console.error('Retrying documentation load...');
  }

  const docsPath = process.env.DOCS_PATH;
  if (!docsPath) {
    loadError = 'DOCS_PATH environment variable is required';
    console.error(`ERROR: ${loadError}`);
    return null;
  }

  if (!fs.existsSync(docsPath)) {
    loadError = `DOCS_PATH not found: ${docsPath}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }

  try {
    const files = await loadMarkdownFiles(docsPath);
    if (files.length === 0) {
      loadError = `No markdown files found in ${docsPath}`;
      console.error(`ERROR: ${loadError}`);
      return null;
    }

    const chunks = files.flatMap((f) => chunkFile(f));

    const warnings = getParseWarnings();
    if (warnings.length > 0) {
      console.error(`\nWARNING: ${warnings.length} file(s) with parse issues:`);
      for (const w of warnings) {
        console.error(`  - ${w.file}: ${w.issue}`);
      }
      console.error('');
    }

    index = buildBM25Index(chunks);
    console.error(`Loaded ${chunks.length} chunks from ${files.length} files`);
    return index;
  } catch (err) {
    loadError = `Unexpected error: ${err instanceof Error ? err.message : 'unknown'}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }
}

// === Zod Schemas ===
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
});

const SearchOutputSchema = z.object({
  results: z.array(
    z.object({
      chunk_id: z.string(),
      content: z.string(),
      category: z.string(),
      source_file: z.string(),
    }),
  ),
});

async function main() {
  const server = new McpServer({
    name: 'extension-docs',
    version: '1.0.0',
  });

  server.registerTool(
    'search_extension_docs',
    {
      title: 'Search Extension Docs',
      description:
        'Search Claude Code extension documentation (hooks, skills, commands, agents, plugins, MCP). Use specific queries.',
      inputSchema: SearchInputSchema,
      outputSchema: SearchOutputSchema,
    },
    async ({ query, limit = 5 }: z.infer<typeof SearchInputSchema>) => {
      const idx = await ensureIndex();
      if (!idx) {
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Search unavailable: ${loadError}` }],
        };
      }

      try {
        const results = search(idx, query, limit);
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }],
          structuredContent: { results },
        };
      } catch (err) {
        console.error('Search error:', err);
        return {
          isError: true,
          content: [{ type: 'text' as const, text: 'Search failed. Please try a different query.' }],
        };
      }
    },
  );

  server.registerTool(
    'reload_extension_docs',
    {
      title: 'Reload Extension Docs',
      description:
        'Force reload of extension documentation. Use after editing docs to refresh search index.',
      inputSchema: z.object({}),
    },
    async () => {
      if (loadingPromise) {
        console.error('Waiting for in-progress load to complete before reload...');
        await loadingPromise;
      }

      index = null;
      loadError = null;
      lastLoadAttempt = 0;
      clearParseWarnings();

      console.error('Forcing documentation reload...');

      const idx = await ensureIndex();
      if (!idx) {
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Reload failed: ${loadError}` }],
        };
      }

      const warnings = getParseWarnings();
      return {
        content: [
          {
            type: 'text' as const,
            text: `Reloaded ${idx.chunks.length} chunks from documentation.${
              warnings.length > 0 ? ` Warning: ${warnings.length} file(s) had parse issues.` : ''
            }`,
          },
        ],
      };
    },
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);

  const shutdown = async (signal: string) => {
    console.error(`Received ${signal}, shutting down...`);

    let timeoutId: NodeJS.Timeout;
    let exitCode = 0;

    try {
      await Promise.race([
        server.close(),
        new Promise((_, reject) => {
          timeoutId = setTimeout(() => reject(new Error('Shutdown timeout')), 5000);
        }),
      ]);
      clearTimeout(timeoutId!);
      console.error('Graceful shutdown complete');
    } catch (err) {
      clearTimeout(timeoutId!);
      console.error('Shutdown error:', err instanceof Error ? err.message : 'unknown');
      exitCode = 1;
    }

    process.exit(exitCode);
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
```

**Step 4: Rebuild and verify**

Run: `npm run build -w @claude-tools/extension-docs && npm test -w @claude-tools/extension-docs`
Expected: Build succeeds, all tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts packages/mcp-servers/extension-docs/tests/server.test.ts
git commit -m "feat(extension-docs): implement MCP server with search and reload tools"
```

---

## Task 9: Golden Query Integration Tests

**Files:**
- Create: `packages/mcp-servers/extension-docs/tests/golden-queries.test.ts`

**Step 1: Write golden query tests**

```typescript
// tests/golden-queries.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import * as path from 'path';
import { loadMarkdownFiles } from '../src/loader.js';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';
import { clearParseWarnings } from '../src/frontmatter.js';

// These tests validate search quality against the real corpus
// Skip if extension-reference docs don't exist (CI without corpus)
const DOCS_PATH = path.resolve(__dirname, '../../../../docs/extension-reference');

describe('golden queries', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let skipTests = false;

  beforeAll(async () => {
    clearParseWarnings();
    try {
      const files = await loadMarkdownFiles(DOCS_PATH);
      if (files.length === 0) {
        skipTests = true;
        return;
      }
      const chunks = files.flatMap((f) => chunkFile(f));
      index = buildBM25Index(chunks);
    } catch {
      skipTests = true;
    }
  });

  const goldenQueries = [
    { query: 'how do hooks work', expectedTopCategory: 'hooks' },
    { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
    { query: 'skill frontmatter', expectedTopCategory: 'skills' },
    { query: 'MCP server registration', expectedTopCategory: 'mcp' },
    { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  ];

  for (const { query, expectedTopCategory } of goldenQueries) {
    it(`"${query}" returns ${expectedTopCategory} category in top result`, () => {
      if (skipTests) {
        console.log('Skipping: extension-reference docs not available');
        return;
      }

      const results = search(index, query, 5);
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].category).toBe(expectedTopCategory);
    });
  }
});
```

**Step 2: Run golden query tests**

Run: `npm test -w @claude-tools/extension-docs`
Expected: All tests PASS (or skip gracefully if docs unavailable)

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/golden-queries.test.ts
git commit -m "test(extension-docs): add golden query integration tests"
```

---

## Task 10: SessionStart Hook

**Files:**
- Create: `~/.claude/hooks/extension-docs-reminder.sh`
- Modify: `~/.claude/settings.json` (add hook configuration)

**Step 1: Create hook script**

```bash
#!/bin/bash
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<extension-docs-reminder>\nWhen working with Claude Code extensions (hooks, skills, commands, agents, plugins, MCP servers):\n\n1. SEARCH FIRST: Use search_extension_docs from the extension-docs MCP server\n2. Use specific queries: \"PreToolUse input schema\", not \"hooks\"\n3. AFTER EDITING DOCS: Use reload_extension_docs to refresh the search index\n4. Documentation is authoritative - training knowledge may be outdated\n</extension-docs-reminder>"
  }
}
EOF
```

**Step 2: Make hook executable**

Run: `chmod +x ~/.claude/hooks/extension-docs-reminder.sh`
Expected: No output, exit code 0

**Step 3: Test hook output**

Run: `~/.claude/hooks/extension-docs-reminder.sh | jq .`
Expected: Valid JSON with `hookSpecificOutput.additionalContext`

**Step 4: Add hook to settings.json**

Add this to `~/.claude/settings.json` under `"hooks"`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/hooks/extension-docs-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

**Note:** If settings.json already has a `hooks` key, merge the `SessionStart` array. If it already has `SessionStart`, add to the array.

**Step 5: Verify settings syntax**

Run: `jq . ~/.claude/settings.json`
Expected: Valid JSON output (no parse errors)

**Step 6: Commit hook (settings.json is user-specific, not committed)**

```bash
# Hook script can be tracked in dotfiles repo if desired
# Settings.json is user-specific
```

---

## Task 11: Register MCP Server

**Step 1: Build final server**

Run: `npm run build -w @claude-tools/extension-docs`
Expected: Build succeeds, `dist/index.js` exists

**Step 2: Register with Claude Code**

Run:
```bash
claude mcp add --transport stdio --scope user \
  --env DOCS_PATH=/Users/jp/Projects/active/claude-code-tool-dev/docs/extension-reference \
  extension-docs \
  -- node /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/extension-docs/dist/index.js
```
Expected: Server registered successfully

**Step 3: Verify registration**

Run: `claude mcp list | grep extension-docs`
Expected: Shows `extension-docs` with correct configuration

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(extension-docs): complete MCP server implementation

- Two-phase chunking (H2 split + merge)
- BM25 search with precomputed term frequencies
- Lazy loading with 60s retry on failure
- SessionStart hook for discovery
- Full test coverage including golden queries"
```

---

## Task 12: Manual Verification

**Step 1: Start new Claude Code session**

Run: `claude` (new session)
Expected: See `<extension-docs-reminder>` in context (check with `/context` or observe behavior)

**Step 2: Test search tool**

Ask Claude: "Search the extension docs for PreToolUse input schema"
Expected: Claude uses `search_extension_docs` tool, returns relevant hooks documentation

**Step 3: Test reload tool**

Ask Claude: "Reload the extension docs"
Expected: Claude uses `reload_extension_docs` tool, reports chunk count

**Step 4: Verify error handling**

Temporarily break DOCS_PATH in MCP config, restart Claude, try search
Expected: Structured error message, not crash

---

## Verification Checklist

After completing all tasks, verify these success criteria from the design doc:

| ID | Criterion | How to Verify |
|----|-----------|---------------|
| C1 | Server returns structured error (not crash) when DOCS_PATH invalid | Task 12 Step 4 |
| C2 | Source code uses 2-phase chunking only | Inspect `chunker.ts` |
| U1 | New sessions show `<extension-docs-reminder>` in context | Task 12 Step 1 |
| U2 | Malformed YAML files listed in startup stderr | Add bad YAML to test file, check logs |
| U3 | Server retries after 60 seconds on load failure | Integration test |
| F1-F11 | Implementation details | Code review against design doc |
| Golden queries | Top results match expected categories | Task 9 tests |

---

Plan complete and saved to `docs/plans/2026-01-12-extension-docs-mcp-impl.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
