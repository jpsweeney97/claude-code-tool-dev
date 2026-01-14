# Extension Docs Chunking v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve search quality by parsing more frontmatter fields, making chunk sizes bounded, and adding hierarchical splitting (H2 → H3 → paragraph → hard split).

**Architecture:** Extend frontmatter parsing to include `id`, `requires`, `related_to`. Extract fence detection to reusable `FenceTracker` class. Replace `splitAtH2` with bounded `splitBounded` that falls back through heading levels, paragraphs, and hard splits. Add overlap only for forced splits.

**Tech Stack:** TypeScript, Vitest, ESM modules

**Design Document:** `docs/plans/2026-01-12-extension-docs-chunking-v2-plan.md`

---

## Task 1: Extract FenceTracker Class

**Why first:** Fence detection is duplicated 3+ times. Extract before adding new splitting functions to avoid a 4th copy.

**Files:**
- Create: `packages/mcp-servers/extension-docs/src/fence-tracker.ts`
- Create: `packages/mcp-servers/extension-docs/tests/fence-tracker.test.ts`

**Step 1: Write the failing test**

```typescript
// tests/fence-tracker.test.ts
import { describe, it, expect } from 'vitest';
import { FenceTracker } from '../src/fence-tracker.js';

describe('FenceTracker', () => {
  it('detects backtick fence start and end', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('normal text')).toBe(false);
    expect(tracker.processLine('```typescript')).toBe(true);
    expect(tracker.processLine('code inside')).toBe(true);
    expect(tracker.processLine('```')).toBe(false);
    expect(tracker.processLine('after fence')).toBe(false);
  });

  it('detects tilde fence start and end', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('~~~python')).toBe(true);
    expect(tracker.processLine('code')).toBe(true);
    expect(tracker.processLine('~~~')).toBe(false);
  });

  it('handles indented fences (0-3 spaces)', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('   ```bash')).toBe(true);
    expect(tracker.processLine('code')).toBe(true);
    expect(tracker.processLine('   ```')).toBe(false);
  });

  it('ignores 4+ space indented fences', () => {
    const tracker = new FenceTracker();

    // 4 spaces = code block in CommonMark, not a fence
    expect(tracker.processLine('    ```bash')).toBe(false);
    expect(tracker.processLine('not in fence')).toBe(false);
  });

  it('requires matching fence character for close', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('```typescript')).toBe(true);
    expect(tracker.processLine('~~~')).toBe(true);  // ~~~ doesn't close ```
    expect(tracker.processLine('```')).toBe(false); // ``` closes ```
  });

  it('requires matching fence length for close', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('````typescript')).toBe(true);
    expect(tracker.processLine('```')).toBe(true);   // 3 backticks don't close 4
    expect(tracker.processLine('````')).toBe(false); // 4 closes 4
  });

  it('exposes isInFence property', () => {
    const tracker = new FenceTracker();

    expect(tracker.isInFence).toBe(false);
    tracker.processLine('```');
    expect(tracker.isInFence).toBe(true);
  });

  it('resets state', () => {
    const tracker = new FenceTracker();

    tracker.processLine('```');
    expect(tracker.isInFence).toBe(true);
    tracker.reset();
    expect(tracker.isInFence).toBe(false);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- fence-tracker`
Expected: FAIL with "Cannot find module '../src/fence-tracker.js'"

**Step 3: Write minimal implementation**

```typescript
// src/fence-tracker.ts

/**
 * Tracks code fence state while iterating through markdown lines.
 * CommonMark-compliant: 0-3 leading spaces, 3+ backticks or tildes.
 *
 * Usage:
 *   const fence = new FenceTracker();
 *   for (const line of lines) {
 *     const inFence = fence.processLine(line);
 *     if (!inFence && isHeading(line)) { ... }
 *   }
 */
export class FenceTracker {
  private inFence = false;
  private fencePattern = '';

  /**
   * Process a line and update fence state.
   * @returns true if currently inside a fence AFTER processing this line
   */
  processLine(line: string): boolean {
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!this.inFence) {
        this.inFence = true;
        this.fencePattern = fence[2];
      } else if (
        line.match(
          new RegExp(`^ {0,3}${this.fencePattern[0]}{${this.fencePattern.length},}\\s*$`)
        )
      ) {
        this.inFence = false;
        this.fencePattern = '';
      }
    }
    return this.inFence;
  }

  /** Check if currently inside a fence without advancing state */
  get isInFence(): boolean {
    return this.inFence;
  }

  /** Reset to initial state */
  reset(): void {
    this.inFence = false;
    this.fencePattern = '';
  }
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- fence-tracker`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/fence-tracker.ts packages/mcp-servers/extension-docs/tests/fence-tracker.test.ts
git commit -m "refactor(extension-docs): extract FenceTracker class for fence detection"
```

---

## Task 2: Extend Frontmatter Interface and Parsing

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/frontmatter.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/frontmatter.test.ts`

**Step 1: Write the failing tests**

Add to `tests/frontmatter.test.ts`:

```typescript
describe('parseFrontmatter - requires and related_to', () => {
  beforeEach(() => {
    clearParseWarnings();
  });

  it('parses requires as array of strings', () => {
    const content = '---\nrequires: [hooks-overview, hooks-events]\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.requires).toEqual(['hooks-overview', 'hooks-events']);
  });

  it('parses requires as single string', () => {
    const content = '---\nrequires: hooks-overview\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.requires).toEqual(['hooks-overview']);
  });

  it('parses related_to as array of strings', () => {
    const content = '---\nrelated_to: [skills-overview, commands-overview]\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.related_to).toEqual(['skills-overview', 'commands-overview']);
  });

  it('parses related_to as single string', () => {
    const content = '---\nrelated_to: skills-overview\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.related_to).toEqual(['skills-overview']);
  });

  it('warns on non-string requires items', () => {
    const content = '---\nrequires: [123, "valid"]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid requires item type: expected string, got number',
    });
  });

  it('warns on invalid requires type', () => {
    const content = '---\nrequires: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid requires type: expected string or array, got number',
    });
  });

  it('parses id field', () => {
    const content = '---\nid: hooks-exit-codes\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.id).toBe('hooks-exit-codes');
  });

  it('warns on non-string id', () => {
    const content = '---\nid: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid id type: expected string, got number',
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- frontmatter`
Expected: FAIL - `frontmatter.requires` is undefined

**Step 3: Implement frontmatter extensions**

Modify `src/frontmatter.ts`:

```typescript
import { parse as parseYaml } from 'yaml';

export interface Frontmatter {
  id?: string;
  topic?: string;
  category?: string;
  tags?: string[];
  requires?: string[];
  related_to?: string[];
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

function parseStringArrayField(
  yaml: Record<string, unknown>,
  filePath: string,
  fieldName: string,
): string[] | undefined {
  const value = yaml[fieldName];
  if (value == null) return undefined;

  if (Array.isArray(value)) {
    const out: string[] = [];
    for (const item of value) {
      if (typeof item === 'string') {
        out.push(item);
      } else {
        parseWarnings.push({
          file: filePath,
          issue: `Invalid ${fieldName} item type: expected string, got ${typeof item}`,
        });
      }
    }
    return out.length ? out : undefined;
  }

  if (typeof value === 'string') return [value];

  parseWarnings.push({
    file: filePath,
    issue: `Invalid ${fieldName} type: expected string or array, got ${typeof value}`,
  });
  return undefined;
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
    const yamlRaw = parseYaml(match[1]);
    const yaml =
      yamlRaw && typeof yamlRaw === 'object' ? (yamlRaw as Record<string, unknown>) : {};

    // Parse id
    let id: string | undefined;
    if (typeof yaml.id === 'string') {
      id = yaml.id;
    } else if (yaml.id != null) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid id type: expected string, got ${typeof yaml.id}`,
      });
    }

    // Parse topic
    let topic: string | undefined;
    if (typeof yaml.topic === 'string') {
      topic = yaml.topic;
    } else if (yaml.topic !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid topic type: expected string, got ${typeof yaml.topic}`,
      });
    }

    // Parse category
    let category: string | undefined;
    if (typeof yaml.category === 'string') {
      category = yaml.category;
    } else if (yaml.category !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid category type: expected string, got ${typeof yaml.category}`,
      });
    }

    // Parse tags (existing logic)
    let tags: string[] | undefined;
    if (Array.isArray(yaml.tags)) {
      tags = yaml.tags.filter((t: unknown): t is string => {
        if (typeof t === 'string') return true;
        parseWarnings.push({
          file: filePath,
          issue: `Non-string tag value ignored: ${typeof t}`,
        });
        return false;
      });
      if (tags.length === 0) tags = undefined;
    } else if (typeof yaml.tags === 'string') {
      tags = [yaml.tags];
    } else if (yaml.tags !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid tags type: expected string or array, got ${typeof yaml.tags}`,
      });
    }

    // Parse requires and related_to using helper
    const requires = parseStringArrayField(yaml, filePath, 'requires');
    const related_to = parseStringArrayField(yaml, filePath, 'related_to');

    return {
      frontmatter: { id, topic, category, tags, requires, related_to },
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
  // v2 order: Topic first (most human-readable), then ID, then category/tags
  if (fm.topic) lines.push(`Topic: ${fm.topic}`);
  if (fm.id) lines.push(`ID: ${fm.id}`);
  if (fm.category) lines.push(`Category: ${fm.category}`);
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`);
  // Note: requires/related_to are tokens-only, not in header
  return lines.length ? lines.join('\n') + '\n\n' : '';
}

export function deriveCategory(path: string): string {
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- frontmatter`
Expected: PASS

**Step 5: Update formatMetadataHeader test for new order**

Modify the test in `tests/frontmatter.test.ts`:

```typescript
  it('formats all fields in v2 order (Topic first)', () => {
    const header = formatMetadataHeader({
      category: 'hooks',
      tags: ['api'],
      topic: 'input',
      id: 'hooks-input',
    });
    expect(header).toBe('Topic: input\nID: hooks-input\nCategory: hooks\nTags: api\n\n');
  });
```

**Step 6: Run all frontmatter tests**

Run: `npm test -w packages/mcp-servers/extension-docs -- frontmatter`
Expected: PASS

**Step 7: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/frontmatter.ts packages/mcp-servers/extension-docs/tests/frontmatter.test.ts
git commit -m "feat(extension-docs): extend frontmatter to parse id, requires, related_to"
```

---

## Task 3: Add Relationship Tokens to Chunk Metadata

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write the failing test**

Add to `tests/chunker.test.ts`:

```typescript
describe('metadata token inclusion', () => {
  it('includes requires/related_to in tokens even when not in body', () => {
    const content = [
      '---',
      'category: hooks',
      'requires: [hooks-overview]',
      'related_to: [hooks-events]',
      '---',
      '# Title',
      '## Section',
      'Body does not mention prerequisites or related pages.',
      ...Array(150).fill('pad'),
    ].join('\n');

    const file: MarkdownFile = { path: 'hooks/x.md', content };
    const chunks = chunkFile(file);
    const tokens = chunks[0].tokens;

    // Verify relationship metadata appears in tokens
    expect(tokens).toContain('hooks');
    expect(tokens).toContain('overview');
    expect(tokens).toContain('events');
  });

  it('includes id and topic in tokens', () => {
    const content = [
      '---',
      'id: special-doc-id',
      'topic: Special Topic Name',
      'category: test',
      '---',
      '# Title',
      'Body content without id or topic words.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/meta.md', content };
    const chunks = chunkFile(file);
    const tokens = chunks[0].tokens;

    // id tokens
    expect(tokens).toContain('special');
    expect(tokens).toContain('doc');
    // topic tokens
    expect(tokens).toContain('topic');
    expect(tokens).toContain('name');
  });

  it('handles requires/related_to as single strings', () => {
    const content = [
      '---',
      'requires: single-prereq',
      'related_to: single-related',
      '---',
      '# Title',
      'Body content.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/single.md', content };
    const chunks = chunkFile(file);
    const tokens = chunks[0].tokens;

    expect(tokens).toContain('single');
    expect(tokens).toContain('prereq');
    expect(tokens).toContain('related');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: FAIL - tokens don't include 'overview' or 'events'

**Step 3: Update chunker to include relationship tokens**

Modify `src/chunker.ts` - add `getMetadataTerms` function and update `createSplitChunk`:

```typescript
// Add this function before createSplitChunk
function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const category = fm.category ?? derivedCategory;
  const tags = fm.tags ?? [];
  const requires = fm.requires ?? [];
  const related = fm.related_to ?? [];
  const id = fm.id ? [fm.id] : [];
  const topic = fm.topic ? [fm.topic] : [];

  // tokenize will split CamelCase and punctuation, so ids like "hooks-overview"
  // or "PreToolUse" contribute meaningful tokens.
  return [category, ...tags, ...requires, ...related, ...id, ...topic];
}

// Update createSplitChunk to use getMetadataTerms
function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  frontmatter: Frontmatter,
): Chunk {
  const derivedCategory = deriveCategory(file.path);
  const category = frontmatter.category ?? derivedCategory;
  const tags = frontmatter.tags ?? [];

  const metadataTerms = getMetadataTerms(frontmatter, derivedCategory).flatMap(tokenize);
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

// Also update createWholeFileChunk to use getMetadataTerms
function createWholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  const derivedCategory = deriveCategory(file.path);
  const metadataTerms = getMetadataTerms(fm, derivedCategory).flatMap(tokenize);
  const tokens = [...tokenize(content), ...metadataTerms];

  return {
    id: generateChunkId(file),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: fm.category ?? derivedCategory,
    tags: fm.tags ?? [],
    source_file: file.path,
  };
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "feat(extension-docs): include id/requires/related_to in chunk tokens"
```

---

## Task 4: Add generateChunkId Support for Split Index

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunk-helpers.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/chunk-helpers.test.ts`

**Step 1: Write the failing test**

Add to `tests/chunk-helpers.test.ts`:

```typescript
describe('generateChunkId with splitIndex', () => {
  it('adds no suffix for splitIndex undefined', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    const id = generateChunkId(file, '## Section');
    expect(id).toBe('hooks-test#section');
  });

  it('adds no suffix for splitIndex 1 (first chunk)', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    const id = generateChunkId(file, '## Section', 1);
    expect(id).toBe('hooks-test#section');
  });

  it('adds suffix for splitIndex 2+', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    expect(generateChunkId(file, '## Section', 2)).toBe('hooks-test#section-2');
    expect(generateChunkId(file, '## Section', 3)).toBe('hooks-test#section-3');
  });

  it('handles file-only id with splitIndex', () => {
    const file: MarkdownFile = { path: 'hooks/test.md', content: '' };
    // No heading, but has splitIndex (shouldn't happen in practice, but handle gracefully)
    expect(generateChunkId(file, undefined, 2)).toBe('hooks-test');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunk-helpers`
Expected: FAIL - generateChunkId doesn't accept splitIndex parameter

**Step 3: Update generateChunkId**

Modify `src/chunk-helpers.ts`:

```typescript
import type { MarkdownFile } from './types.js';

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/\.md$/, '') // Strip .md extension
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function generateChunkId(
  file: MarkdownFile,
  heading?: string,
  splitIndex?: number,
): string {
  const fileSlug = slugify(file.path);
  if (!heading) return fileSlug;

  const headingSlug = slugify(heading);
  // Append suffix for forced splits using 1-based indexing:
  // - undefined or 1 → no suffix (e.g., file#section)
  // - 2+ → suffix (e.g., file#section-2, file#section-3)
  const suffix = splitIndex != null && splitIndex > 1 ? `-${splitIndex}` : '';
  return `${fileSlug}#${headingSlug}${suffix}`;
}

export function computeTermFreqs(tokens: string[]): Map<string, number> {
  const freqs = new Map<string, number>();
  for (const token of tokens) {
    freqs.set(token, (freqs.get(token) ?? 0) + 1);
  }
  return freqs;
}
```

**Step 4: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunk-helpers`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunk-helpers.ts packages/mcp-servers/extension-docs/tests/chunk-helpers.test.ts
git commit -m "feat(extension-docs): add splitIndex parameter to generateChunkId"
```

---

## Task 5: Implement Bounded Splitting Helpers

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts`
- Add tests to: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write failing tests for bounded splitting**

Add to `tests/chunker.test.ts`:

```typescript
describe('hierarchical splitting', () => {
  it('splits oversized H2 at H3 boundaries when available', () => {
    // Simulate a large H2 section with multiple H3 subsections
    const h3Sections = Array.from({ length: 9 }, (_, i) =>
      `### Subsection ${i + 1}\n${Array(15).fill(`Content line ${i}`).join('\n')}`
    ).join('\n\n');

    const content = [
      '---',
      'category: hooks',
      '---',
      '# Title',
      '## Oversized Section',
      h3Sections,
    ].join('\n');

    const file: MarkdownFile = { path: 'hooks/oversized.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks
    expect(chunks.length).toBeGreaterThan(1);

    // All chunks within bounds
    for (const chunk of chunks) {
      expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      expect(chunk.content.split('\n').length).toBeLessThanOrEqual(150);
    }
  });

  it('falls back to paragraph splitting when H3 unavailable', () => {
    // Large H2 section with no H3 structure, just paragraphs
    const paragraphs = Array.from({ length: 20 }, (_, i) =>
      Array(10).fill(`Paragraph ${i} content word`).join(' ')
    ).join('\n\n');

    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Large Section Without H3',
      paragraphs,
    ].join('\n');

    const file: MarkdownFile = { path: 'test/no-h3.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks via paragraph splitting
    expect(chunks.length).toBeGreaterThan(1);

    // All share the same H2 heading reference
    for (const chunk of chunks) {
      expect(chunk.heading).toContain('## Large Section');
    }
  });
});

describe('forced split overlap', () => {
  it('forced splits include overlap from previous chunk', () => {
    // Create content that requires hard splitting
    const hugeSection = Array(200).fill('unique-line-content-here').join('\n');
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Huge Section',
      hugeSection,
    ].join('\n');

    const file: MarkdownFile = { path: 'test/overlap.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks due to size
    expect(chunks.length).toBeGreaterThan(1);

    // Chunks after the first should start with overlap from previous
    if (chunks.length > 1) {
      const firstChunkLines = chunks[0].content.split('\n');
      const overlapLines = firstChunkLines.slice(-5).join('\n');
      expect(chunks[1].content).toContain(overlapLines);
    }
  });

  it('H2 boundary splits do NOT include overlap', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Section 1',
      ...Array(100).fill('content-a'),
      '## Section 2',
      ...Array(100).fill('content-b'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/no-overlap.md', content };
    const chunks = chunkFile(file);

    // Section 2 chunk should NOT start with Section 1 content
    const section2Chunk = chunks.find((c) => c.content.includes('## Section 2'));
    expect(section2Chunk?.content).not.toContain('content-a');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: FAIL - oversized sections not split at H3 boundaries

**Step 3: Implement bounded splitting**

This is a larger change. Add the following to `src/chunker.ts`:

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
import { FenceTracker } from './fence-tracker.js';

export const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;
const OVERLAP_LINES_FOR_FORCED_SPLITS = 5;

type HeadingLevel = 2 | 3;

interface BoundedPart {
  heading?: string;
  content: string;
  splitIndex?: number;
  splitType?: 'h2' | 'h3' | 'paragraph' | 'hard';
}

export function chunkFile(file: MarkdownFile): Chunk[] {
  const { frontmatter, body } = parseFrontmatter(file.content, file.path);
  const metadataHeader = formatMetadataHeader(frontmatter);
  const preparedContent = metadataHeader + body;

  if (isSmallEnoughForWholeFile(preparedContent)) {
    return [createWholeFileChunk(file, preparedContent, frontmatter)];
  }

  // v2: Use bounded splitting instead of splitAtH2
  const boundedParts = splitBounded(preparedContent);
  const rawChunks = boundedParts.map((part) =>
    createSplitChunk(file, part.content, part.heading, part.splitIndex, frontmatter)
  );

  return mergeSmallChunks(rawChunks);
}

function countLines(content: string): number {
  return content.split('\n').length;
}

function withinLimits(text: string): boolean {
  if (text.length > MAX_CHUNK_CHARS) return false;
  return countLines(text) <= MAX_CHUNK_LINES;
}

function isSmallEnoughForWholeFile(content: string): boolean {
  return withinLimits(content);
}

function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const category = fm.category ?? derivedCategory;
  const tags = fm.tags ?? [];
  const requires = fm.requires ?? [];
  const related = fm.related_to ?? [];
  const id = fm.id ? [fm.id] : [];
  const topic = fm.topic ? [fm.topic] : [];
  return [category, ...tags, ...requires, ...related, ...id, ...topic];
}

function createWholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  const derivedCategory = deriveCategory(file.path);
  const metadataTerms = getMetadataTerms(fm, derivedCategory).flatMap(tokenize);
  const tokens = [...tokenize(content), ...metadataTerms];
  return {
    id: generateChunkId(file),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category: fm.category ?? derivedCategory,
    tags: fm.tags ?? [],
    source_file: file.path,
  };
}

function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  splitIndex: number | undefined,
  frontmatter: Frontmatter,
): Chunk {
  const derivedCategory = deriveCategory(file.path);
  const category = frontmatter.category ?? derivedCategory;
  const tags = frontmatter.tags ?? [];

  const metadataTerms = getMetadataTerms(frontmatter, derivedCategory).flatMap(tokenize);
  const tokens = [...tokenize(content), ...metadataTerms];

  return {
    id: generateChunkId(file, heading, splitIndex),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category,
    tags,
    source_file: file.path,
    heading,
  };
}

// ============ Bounded Splitting Helpers ============

function splitByHeadingOutsideFences(
  content: string,
  level: HeadingLevel,
): Array<{ headingLine?: string; body: string }> {
  const headingRe = level === 2 ? /^##\s/ : /^###\s/;
  const lines = content.split('\n');
  const parts: Array<{ headingLine?: string; bodyLines: string[] }> = [];
  const fence = new FenceTracker();
  let current: { headingLine?: string; bodyLines: string[] } = { bodyLines: [] };

  for (const line of lines) {
    fence.processLine(line);

    if (!fence.isInFence && headingRe.test(line)) {
      if (current.bodyLines.length) parts.push(current);
      current = { headingLine: line, bodyLines: [line] };
      continue;
    }

    current.bodyLines.push(line);
  }

  if (current.bodyLines.length) parts.push(current);

  // Filter out empty sections
  return parts
    .map((p) => {
      const bodyWithoutHeading = p.bodyLines.slice(p.headingLine ? 1 : 0).join('\n').trim();
      return {
        headingLine: p.headingLine,
        body: p.bodyLines.join('\n'),
        isEmpty: !bodyWithoutHeading.length,
      };
    })
    .filter((p) => !p.isEmpty)
    .map((p) => ({ headingLine: p.headingLine, body: p.body }));
}

function splitByParagraphOutsideFences(content: string): string[] {
  const lines = content.split('\n');
  const blocks: string[] = [];
  const fence = new FenceTracker();
  let current: string[] = [];

  const flush = () => {
    const text = current.join('\n').trimEnd();
    if (text.length) blocks.push(text);
    current = [];
  };

  for (const line of lines) {
    fence.processLine(line);
    const lineIsBlank = !fence.isInFence && line.trim() === '';

    if (lineIsBlank) {
      current.push(line);
      flush();
      continue;
    }

    current.push(line);
  }

  flush();
  return blocks;
}

function takeTailLines(text: string, n: number): string {
  if (n <= 0) return '';
  const lines = text.split('\n');
  return lines.slice(Math.max(0, lines.length - n)).join('\n');
}

function hardSplitWithOverlap(text: string): string[] {
  const out: string[] = [];
  let remaining = text;
  let prev = '';

  const overlapBudget = OVERLAP_LINES_FOR_FORCED_SPLITS * 200;
  const effectiveBudget = MAX_CHUNK_CHARS - overlapBudget;

  while (!withinLimits(remaining)) {
    const budget = Math.min(effectiveBudget, remaining.length);
    const candidate = remaining.slice(0, budget);
    const cut = candidate.lastIndexOf('\n');
    const head = (cut > 0 ? remaining.slice(0, cut) : candidate).trimEnd();
    if (!head) break;

    const withOverlap = prev ? `${prev}\n${head}` : head;
    out.push(withOverlap);

    remaining = remaining.slice(head.length).replace(/^\n+/, '');
    prev = takeTailLines(head, OVERLAP_LINES_FOR_FORCED_SPLITS);
  }

  if (remaining.trim().length) {
    const tail = prev ? `${prev}\n${remaining}` : remaining;
    out.push(tail);
  }

  return out;
}

function accumulateParagraphsWithOverlap(
  paragraphs: string[],
  heading: string | undefined,
): BoundedPart[] {
  const results: BoundedPart[] = [];
  let buffer = '';
  let prevTail = '';
  let chunkIndex = 1;

  const flush = (content: string) => {
    if (!content.trim().length) return;
    const withOverlap = prevTail ? `${prevTail}\n${content}` : content;
    results.push({ heading, content: withOverlap, splitIndex: chunkIndex, splitType: 'paragraph' });
    prevTail = takeTailLines(content, OVERLAP_LINES_FOR_FORCED_SPLITS);
    chunkIndex++;
  };

  for (const para of paragraphs) {
    const combined = buffer ? `${buffer}\n\n${para}` : para;

    if (withinLimits(combined)) {
      buffer = combined;
      continue;
    }

    if (buffer.trim().length) {
      flush(buffer);
      buffer = para;
      continue;
    }

    // Single paragraph too big - hard split
    const pieces = hardSplitWithOverlap(para);
    for (const piece of pieces) {
      results.push({ heading, content: piece, splitIndex: chunkIndex, splitType: 'hard' });
      chunkIndex++;
    }
  }

  if (buffer.trim().length) {
    flush(buffer);
  }

  return results;
}

function splitBounded(content: string): BoundedPart[] {
  const h2Parts = splitByHeadingOutsideFences(content, 2);
  const results: BoundedPart[] = [];

  for (const part of h2Parts) {
    if (withinLimits(part.body)) {
      results.push({ heading: part.headingLine, content: part.body, splitType: 'h2' });
      continue;
    }

    // Too big -> try H3
    const h3Parts = splitByHeadingOutsideFences(part.body, 3);
    if (h3Parts.length > 1) {
      for (const h3 of h3Parts) {
        if (withinLimits(h3.body)) {
          results.push({
            heading: h3.headingLine ?? part.headingLine,
            content: h3.body,
            splitType: 'h3',
          });
        } else {
          const paras = splitByParagraphOutsideFences(h3.body);
          if (paras.length > 1) {
            const accumulated = accumulateParagraphsWithOverlap(
              paras,
              h3.headingLine ?? part.headingLine
            );
            results.push(...accumulated);
          } else {
            const heading = h3.headingLine ?? part.headingLine;
            const pieces = hardSplitWithOverlap(h3.body);
            for (let i = 0; i < pieces.length; i++) {
              results.push({ heading, content: pieces[i], splitIndex: i + 1, splitType: 'hard' });
            }
          }
        }
      }
      continue;
    }

    // No H3 structure - use paragraph splitting
    const paras = splitByParagraphOutsideFences(part.body);
    if (paras.length > 1) {
      const accumulated = accumulateParagraphsWithOverlap(paras, part.headingLine);
      results.push(...accumulated);
      continue;
    }

    // Direct hard split
    const pieces = hardSplitWithOverlap(part.body);
    for (let i = 0; i < pieces.length; i++) {
      results.push({ heading: part.headingLine, content: pieces[i], splitIndex: i + 1, splitType: 'hard' });
    }
  }

  return results;
}

// ============ Merging ============

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

**Step 4: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "feat(extension-docs): implement bounded hierarchical splitting (H2→H3→paragraph→hard)"
```

---

## Task 6: Add Table-Aware Splitting

**Files:**
- Modify: `packages/mcp-servers/extension-docs/src/chunker.ts`
- Add tests to: `packages/mcp-servers/extension-docs/tests/chunker.test.ts`

**Step 1: Write the failing tests**

Add to `tests/chunker.test.ts`:

```typescript
describe('table-aware splitting', () => {
  it('keeps small tables atomic', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Small Table',
      '| A | B |',
      '|---|---|',
      '| 1 | 2 |',
      '| 3 | 4 |',
      '',
      'Paragraph after table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/small-table.md', content };
    const chunks = chunkFile(file);

    // Small file should be one chunk
    expect(chunks.length).toBe(1);
    // Table should be intact (all rows present)
    expect(chunks[0].content).toContain('| 1 | 2 |');
    expect(chunks[0].content).toContain('| 3 | 4 |');
  });

  it('does not treat pipe-lines inside code fence as table', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Code Example',
      '```bash',
      'echo "| Not | A | Table |"',
      'cat file | grep pattern | head',
      '```',
      '',
      'Paragraph after code.',
      ...Array(150).fill('padding'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/fence-pipe.md', content };
    const chunks = chunkFile(file);

    // Code block should stay intact
    const codeChunk = chunks.find((c) => c.content.includes('```bash'));
    expect(codeChunk?.content).toContain('echo "| Not | A | Table |"');
    expect(codeChunk?.content).toContain('cat file | grep pattern | head');
  });

  it('handles tables mixed with paragraphs', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Mixed Content',
      'Paragraph before table.',
      '',
      '| Col1 | Col2 |',
      '|------|------|',
      '| a    | b    |',
      '',
      'Paragraph after table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/mixed.md', content };
    const chunks = chunkFile(file);

    // Content should preserve table integrity
    const contentStr = chunks.map((c) => c.content).join('');
    expect(contentStr).toContain('| Col1 | Col2 |');
    expect(contentStr).toContain('| a    | b    |');
  });
});
```

**Step 2: Run test to verify current behavior**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: These should PASS with current implementation (basic table handling)

**Step 3: Add oversized table test**

```typescript
  it('splits oversized tables at row boundaries with header preservation', () => {
    // Create a table that exceeds MAX_CHUNK_CHARS
    const header = '| Column A | Column B | Column C |';
    const separator = '|----------|----------|----------|';
    const row = '| data-a   | data-b   | data-c   |';
    const tableRows = Array(200).fill(row).join('\n'); // ~8000+ chars

    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Table Section',
      header,
      separator,
      tableRows,
    ].join('\n');

    const file: MarkdownFile = { path: 'test/big-table.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks due to oversized table
    expect(chunks.length).toBeGreaterThan(1);

    // Each chunk should start with the table header (somewhere in content)
    for (const chunk of chunks) {
      if (chunk.content.includes('data-a')) {
        // Table chunks should have header
        expect(chunk.content).toContain(header);
        expect(chunk.content).toContain(separator);
      }
    }

    // Each chunk within size limit
    for (const chunk of chunks) {
      expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
    }
  });
```

**Step 4: Run test to verify it fails**

Run: `npm test -w packages/mcp-servers/extension-docs -- "splits oversized tables"`
Expected: FAIL - headers not preserved

**Step 5: Implement table-aware paragraph splitting**

Update `splitByParagraphOutsideFences` in `src/chunker.ts`:

```typescript
function isTableLine(line: string): boolean {
  return line.trimStart().startsWith('|');
}

function splitOversizedTable(tableLines: string[]): string[] {
  const headerLines = tableLines.slice(0, 2);
  const dataRows = tableLines.slice(2);
  const result: string[] = [];

  let currentChunk = [...headerLines];
  for (const row of dataRows) {
    const projected = [...currentChunk, row].join('\n');

    if (projected.length > MAX_CHUNK_CHARS && currentChunk.length > 2) {
      result.push(currentChunk.join('\n'));
      currentChunk = [...headerLines, row];
    } else {
      currentChunk.push(row);
    }
  }

  if (currentChunk.length > 2) {
    result.push(currentChunk.join('\n'));
  }

  return result;
}

function splitByParagraphOutsideFences(content: string): string[] {
  const lines = content.split('\n');
  const blocks: string[] = [];
  const fence = new FenceTracker();
  let inTable = false;
  let current: string[] = [];

  const flush = (wasTable: boolean) => {
    const text = current.join('\n').trimEnd();
    if (text.length) {
      if (wasTable && text.length > MAX_CHUNK_CHARS) {
        blocks.push(...splitOversizedTable(current));
      } else {
        blocks.push(text);
      }
    }
    current = [];
  };

  for (const line of lines) {
    fence.processLine(line);

    const lineIsTable = !fence.isInFence && isTableLine(line);
    const lineIsBlank = !fence.isInFence && line.trim() === '';

    // Transition: table → non-table or non-table → table
    if (!fence.isInFence && !lineIsBlank && inTable !== lineIsTable && current.length) {
      flush(inTable);
      inTable = lineIsTable;
    }

    // Blank line outside fence: flush paragraph (but NOT table)
    if (lineIsBlank && !inTable) {
      current.push(line);
      flush(false);
      continue;
    }

    current.push(line);
    if (lineIsTable) inTable = true;
  }

  flush(inTable);
  return blocks;
}
```

**Step 6: Run test to verify it passes**

Run: `npm test -w packages/mcp-servers/extension-docs -- chunker`
Expected: PASS

**Step 7: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/chunker.ts packages/mcp-servers/extension-docs/tests/chunker.test.ts
git commit -m "feat(extension-docs): add table-aware splitting with header preservation"
```

---

## Task 7: Add Corpus Validation Test

**Files:**
- Create: `packages/mcp-servers/extension-docs/tests/corpus-validation.test.ts`

**Step 1: Write the corpus validation test**

```typescript
// tests/corpus-validation.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import { readdirSync, readFileSync, statSync, existsSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_PATH =
  process.env.DOCS_PATH ?? resolve(__dirname, '../../../../docs/extension-reference');

const MAX_CHUNK_LINES = 150;

function* walkMarkdownFiles(dir: string): Generator<string> {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      yield* walkMarkdownFiles(fullPath);
    } else if (entry.endsWith('.md')) {
      yield fullPath;
    }
  }
}

describe('corpus validation', () => {
  it('all chunks within size bounds', () => {
    const stats = {
      totalFiles: 0,
      totalChunks: 0,
      maxChunkLines: 0,
      maxChunkChars: 0,
      oversizedChunks: [] as string[],
    };

    for (const filePath of walkMarkdownFiles(DOCS_PATH)) {
      const content = readFileSync(filePath, 'utf-8');
      const chunks = chunkFile({ path: filePath, content });

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

    // Assertion: no oversized chunks
    expect(stats.oversizedChunks).toEqual([]);
    expect(stats.totalFiles).toBeGreaterThan(0);
  });

  it('all chunks have valid IDs', () => {
    const ids = new Set<string>();
    const duplicates: string[] = [];

    for (const filePath of walkMarkdownFiles(DOCS_PATH)) {
      const content = readFileSync(filePath, 'utf-8');
      const chunks = chunkFile({ path: filePath, content });

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

**Step 2: Run test**

Run: `npm test -w packages/mcp-servers/extension-docs -- corpus-validation`
Expected: PASS (validates full corpus)

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/corpus-validation.test.ts
git commit -m "test(extension-docs): add corpus validation test for chunk size bounds"
```

---

## Task 8: Build and Final Verification

**Step 1: Build the package**

Run: `npm run build -w packages/mcp-servers/extension-docs`
Expected: Successful build with no TypeScript errors

**Step 2: Run all tests**

Run: `npm test -w packages/mcp-servers/extension-docs`
Expected: All tests PASS

**Step 3: Run linting (if configured)**

Run: `npm run lint -w packages/mcp-servers/extension-docs` (if available)
Expected: No lint errors

**Step 4: Commit build verification**

```bash
git add -A
git commit -m "chore(extension-docs): verify build and tests pass for chunking v2"
```

---

## Summary

| Task | Description | Risk |
|------|-------------|------|
| 1 | Extract FenceTracker class | Low - refactor only |
| 2 | Extend frontmatter parsing | Low - additive |
| 3 | Add relationship tokens | Low - additive |
| 4 | Add splitIndex to generateChunkId | Low - additive |
| 5 | Implement bounded splitting | Medium - behavioral |
| 6 | Add table-aware splitting | Medium - behavioral |
| 7 | Corpus validation test | Low - test only |
| 8 | Build and verify | Low - verification |

**Total estimated tasks:** 8 major tasks, ~30 steps

**Rollback:** If issues arise with Tasks 5-6 (bounded splitting), revert to `splitAtH2` by changing the `chunkFile` function to use the old path. Tasks 1-4 are purely additive and can remain.
