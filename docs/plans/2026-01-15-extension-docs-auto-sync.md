# Extension-Docs Auto-Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace manual documentation maintenance with automatic fetching from `code.claude.com` on every MCP server startup.

**Architecture:** Fetch `llms-full.txt` → parse into sections by `Source:` headers → filter to extension-related content → feed to existing chunker. Cache successful fetches for fallback when network unavailable.

**Tech Stack:** Node.js 18+, TypeScript, vitest, native fetch API

**Prototype code:** Reference implementations exist in `tmp/` directory (parser.ts, filter.ts, cache.ts, fetcher.ts, loader.ts). Move and adapt these.

---

## Task 1: Add ParsedSection Type

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/types.ts`

**Step 1: Add the ParsedSection interface**

Add to `src/types.ts`:

```typescript
export interface ParsedSection {
  sourceUrl: string;
  title: string;
  content: string;
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd packages/mcp-servers/extension-docs && npm run build`
Expected: No errors

**Step 3: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/types.ts
git commit -m "feat(extension-docs): add ParsedSection type"
```

---

## Task 2: Parser Module

**Files:**

- Create: `packages/mcp-servers/extension-docs/src/parser.ts`
- Create: `packages/mcp-servers/extension-docs/tests/parser.test.ts`

**Step 1: Write failing tests for parser**

Create `tests/parser.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { parseSections } from '../src/parser.js';

describe('parseSections', () => {
  it('returns empty array for empty input', () => {
    expect(parseSections('')).toEqual([]);
  });

  it('returns single section with empty sourceUrl for content without Source: lines', () => {
    const raw = '# Hello\n\nSome content';
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('');
    expect(sections[0].title).toBe('Hello');
    expect(sections[0].content).toBe('# Hello\n\nSome content');
  });

  it('splits on Source: lines', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content

# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('https://example.com/first');
    expect(sections[0].title).toBe('First Topic');
    expect(sections[1].sourceUrl).toBe('https://example.com/second');
    expect(sections[1].title).toBe('Second Topic');
  });

  it('handles preamble before first Source: line', () => {
    const raw = `# Preamble

Some intro text

# Actual Topic
Source: https://example.com/topic

Topic content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('');
    expect(sections[0].title).toBe('Preamble');
    expect(sections[1].sourceUrl).toBe('https://example.com/topic');
  });

  it('handles missing title before Source: line', () => {
    const raw = `Source: https://example.com/notitle

Content without preceding heading`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('https://example.com/notitle');
    expect(sections[0].title).toBe('');
  });

  it('extracts nearest heading before Source: line', () => {
    const raw = `# Main Heading

## Subheading

### Deep Heading
Source: https://example.com/deep

Content`;
    const sections = parseSections(raw);
    expect(sections[0].title).toBe('Deep Heading');
  });

  it('does not match Source: in middle of line', () => {
    const raw = `# Topic
Source: https://example.com/topic

See Source: somewhere in text for details`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/parser.test.ts`
Expected: FAIL (module not found)

**Step 3: Implement parser**

Create `src/parser.ts` (adapt from `tmp/parser.ts`):

```typescript
import type { ParsedSection } from './types.js';

function findLastHeadingBefore(raw: string, endIndex: number): string {
  const prefix = raw.slice(0, endIndex);
  const headingRe = /^#{1,6}\s+(.+)$/gm;
  let match: RegExpExecArray | null = null;
  let lastTitle = '';
  while ((match = headingRe.exec(prefix)) !== null) {
    lastTitle = match[1].trim();
  }
  return lastTitle;
}

function findFirstHeadingInRange(raw: string, startIndex: number, endIndex: number): string {
  const segment = raw.slice(startIndex, endIndex);
  const headingRe = /^#{1,6}\s+(.+)$/m;
  const match = headingRe.exec(segment);
  return match ? match[1].trim() : '';
}

function lineBreakAfter(raw: string, index: number): number {
  if (raw[index] === '\r' && raw[index + 1] === '\n') return index + 2;
  if (raw[index] === '\n') return index + 1;
  return index;
}

export function parseSections(raw: string): ParsedSection[] {
  const sourceRe = /^Source:\s+(\S+)\s*$/gm;
  const matches = Array.from(raw.matchAll(sourceRe));
  const sections: ParsedSection[] = [];

  if (matches.length === 0) {
    const title = findFirstHeadingInRange(raw, 0, raw.length);
    if (raw.trim().length > 0) {
      sections.push({ sourceUrl: '', title, content: raw });
    }
    return sections;
  }

  const firstMatch = matches[0];
  if (firstMatch.index !== undefined && firstMatch.index > 0) {
    const preamble = raw.slice(0, firstMatch.index);
    if (preamble.trim().length > 0) {
      const title = findFirstHeadingInRange(raw, 0, firstMatch.index);
      sections.push({ sourceUrl: '', title, content: preamble });
    }
  }

  for (let i = 0; i < matches.length; i += 1) {
    const match = matches[i];
    const sourceUrl = match[1];
    const matchIndex = match.index ?? 0;
    const lineEnd = matchIndex + match[0].length;
    const contentStart = lineBreakAfter(raw, lineEnd);
    const nextMatch = matches[i + 1];
    const contentEnd = nextMatch?.index ?? raw.length;
    const content = raw.slice(contentStart, contentEnd);
    const title = findLastHeadingBefore(raw, matchIndex);
    sections.push({ sourceUrl, title, content });
  }

  return sections;
}
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/parser.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/parser.ts packages/mcp-servers/extension-docs/tests/parser.test.ts
git commit -m "feat(extension-docs): add parser module for llms-full.txt"
```

---

## Task 3: Filter Module

**Files:**

- Create: `packages/mcp-servers/extension-docs/src/filter.ts`
- Create: `packages/mcp-servers/extension-docs/tests/filter.test.ts`

**Step 1: Write failing tests for filter**

Create `tests/filter.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { isExtensionSection, filterToExtensions } from '../src/filter.js';
import type { ParsedSection } from '../src/types.js';

describe('isExtensionSection', () => {
  it('matches URL with /hooks', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/hooks',
      title: 'Something',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /slash-commands', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/slash-commands',
      title: 'Commands',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /sub-agents (hyphenated)', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/sub-agents',
      title: 'Agents',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /plugin-marketplaces', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/plugin-marketplaces',
      title: 'Marketplaces',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches title with "hooks" word', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://example.com/other',
      title: 'Using Hooks in Claude Code',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('does not match unrelated URL and title', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/quickstart',
      title: 'Getting Started',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(false);
  });

  it('does not match partial word in title', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://example.com/other',
      title: 'Rehooking the system',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(false);
  });
});

describe('filterToExtensions', () => {
  it('filters to only extension sections', () => {
    const sections: ParsedSection[] = [
      { sourceUrl: 'https://example.com/hooks', title: 'Hooks', content: 'a' },
      { sourceUrl: 'https://example.com/quickstart', title: 'Start', content: 'b' },
      { sourceUrl: 'https://example.com/mcp', title: 'MCP', content: 'c' },
    ];
    const filtered = filterToExtensions(sections);
    expect(filtered).toHaveLength(2);
    expect(filtered[0].title).toBe('Hooks');
    expect(filtered[1].title).toBe('MCP');
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/filter.test.ts`
Expected: FAIL (module not found)

**Step 3: Implement filter**

Create `src/filter.ts` (adapt from `tmp/filter.ts`):

```typescript
import type { ParsedSection } from './types.js';

const EXTENSION_URL_PATTERNS: RegExp[] = [
  /\/hooks/i,
  /\/skills/i,
  /\/commands/i,
  /\/slash-commands/i,
  /\/agents/i,
  /\/subagents/i,
  /\/sub-agents/i,
  /\/plugins/i,
  /\/plugin-marketplaces/i,
  /\/mcp/i,
  /\/settings/i,
  /\/claude-md/i,
  /\/memory/i,
  /\/configuration/i,
];

const EXTENSION_TITLE_PATTERNS: RegExp[] = [
  /\bhooks?\b/i,
  /\bskills?\b/i,
  /\bcommands?\b/i,
  /\bslash commands?\b/i,
  /\bagents?\b/i,
  /\bsub[- ]?agents?\b/i,
  /\bplugins?\b/i,
  /\bplugin marketplaces?\b/i,
  /\bmcp\b/i,
  /\bsettings\b/i,
  /\bclaude[- ]md\b/i,
  /\bmemory\b/i,
  /\bconfiguration\b/i,
  /\bextensions?\b/i,
];

export function isExtensionSection(section: ParsedSection): boolean {
  const sourceUrl = section.sourceUrl ?? '';
  const title = section.title ?? '';

  return (
    EXTENSION_URL_PATTERNS.some((pattern) => pattern.test(sourceUrl)) ||
    EXTENSION_TITLE_PATTERNS.some((pattern) => pattern.test(title))
  );
}

export function filterToExtensions(sections: ParsedSection[]): ParsedSection[] {
  return sections.filter(isExtensionSection);
}
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/filter.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/filter.ts packages/mcp-servers/extension-docs/tests/filter.test.ts
git commit -m "feat(extension-docs): add filter module for extension sections"
```

---

## Task 4: Cache Module

**Files:**

- Create: `packages/mcp-servers/extension-docs/src/cache.ts`
- Create: `packages/mcp-servers/extension-docs/tests/cache.test.ts`

**Step 1: Write failing tests for cache**

Create `tests/cache.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { readCache, writeCache, getDefaultCachePath } from '../src/cache.js';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

describe('getDefaultCachePath', () => {
  it('returns path ending with extension-docs/llms-full.txt', () => {
    const cachePath = getDefaultCachePath();
    expect(cachePath).toMatch(/extension-docs[/\\]llms-full\.txt$/);
  });

  it('accepts custom filename', () => {
    const cachePath = getDefaultCachePath('custom.txt');
    expect(cachePath).toMatch(/extension-docs[/\\]custom\.txt$/);
  });
});

describe('readCache and writeCache', () => {
  let tempDir: string;
  let cachePath: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'cache-test-'));
    cachePath = path.join(tempDir, 'test-cache.txt');
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('readCache returns null for non-existent file', async () => {
    const result = await readCache(cachePath);
    expect(result).toBeNull();
  });

  it('writeCache creates file and readCache reads it', async () => {
    await writeCache(cachePath, 'test content');
    const result = await readCache(cachePath);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('test content');
    expect(result!.age).toBeGreaterThanOrEqual(0);
    expect(result!.age).toBeLessThan(1000);
  });

  it('writeCache creates parent directories', async () => {
    const nestedPath = path.join(tempDir, 'deep', 'nested', 'cache.txt');
    await writeCache(nestedPath, 'nested content');
    const result = await readCache(nestedPath);
    expect(result!.content).toBe('nested content');
  });

  it('writeCache overwrites existing file', async () => {
    await writeCache(cachePath, 'first');
    await writeCache(cachePath, 'second');
    const result = await readCache(cachePath);
    expect(result!.content).toBe('second');
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: FAIL (module not found)

**Step 3: Implement cache**

Create `src/cache.ts` (adapt from `tmp/cache.ts`):

```typescript
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

export interface CacheResult {
  content: string;
  age: number;
}

export function getDefaultCachePath(filename = 'llms-full.txt'): string {
  const xdgCacheHome = process.env.XDG_CACHE_HOME?.trim();
  let baseDir: string;
  if (xdgCacheHome && xdgCacheHome.length > 0) {
    baseDir = xdgCacheHome;
  } else if (process.platform === 'darwin') {
    baseDir = path.join(os.homedir(), 'Library', 'Caches');
  } else {
    baseDir = path.join(os.homedir(), '.cache');
  }
  return path.join(baseDir, 'extension-docs', filename);
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function acquireLock(lockPath: string, timeoutMs = 2000, pollMs = 50): Promise<fs.FileHandle> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      return await fs.open(lockPath, 'wx');
    } catch (err: unknown) {
      const code = (err as NodeJS.ErrnoException).code;
      if (code !== 'EEXIST') {
        throw err;
      }
      await sleep(pollMs);
    }
  }
  throw new Error(`Timed out waiting for cache lock: ${lockPath}`);
}

async function releaseLock(lockPath: string, handle: fs.FileHandle): Promise<void> {
  try {
    await handle.close();
  } finally {
    try {
      await fs.unlink(lockPath);
    } catch {
      // Best-effort cleanup only.
    }
  }
}

export async function readCache(cachePath: string): Promise<CacheResult | null> {
  try {
    const [content, stat] = await Promise.all([
      fs.readFile(cachePath, 'utf8'),
      fs.stat(cachePath),
    ]);
    const age = Math.max(0, Date.now() - stat.mtimeMs);
    return { content, age };
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
      return null;
    }
    throw err;
  }
}

export async function writeCache(cachePath: string, content: string): Promise<void> {
  const dir = path.dirname(cachePath);
  await fs.mkdir(dir, { recursive: true });
  const lockPath = `${cachePath}.lock`;

  const tempPath = path.join(
    dir,
    `.${path.basename(cachePath)}.${process.pid}.${Date.now()}.tmp`
  );

  const lockHandle = await acquireLock(lockPath);
  try {
    await fs.writeFile(tempPath, content, 'utf8');
    await fs.rename(tempPath, cachePath);
  } catch (err) {
    try {
      await fs.unlink(tempPath);
    } catch {
      // Best-effort cleanup only.
    }
    throw err;
  } finally {
    await releaseLock(lockPath, lockHandle);
  }
}
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/cache.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/cache.ts packages/mcp-servers/extension-docs/tests/cache.test.ts
git commit -m "feat(extension-docs): add cache module with atomic writes"
```

---

## Task 5: Fetcher Module

**Files:**

- Create: `packages/mcp-servers/extension-docs/src/fetcher.ts`
- Create: `packages/mcp-servers/extension-docs/tests/fetcher.test.ts`

**Step 1: Write failing tests for fetcher**

Create `tests/fetcher.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchOfficialDocs,
  FetchTimeoutError,
  FetchHttpError,
  FetchNetworkError,
} from '../src/fetcher.js';

describe('fetchOfficialDocs', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns content on successful fetch', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve('doc content'),
    });
    vi.stubGlobal('fetch', mockFetch);

    const result = await fetchOfficialDocs('https://example.com/docs');
    expect(result.content).toBe('doc content');
    expect(result.status).toBe(200);
  });

  it('throws FetchHttpError on 404', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers(),
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/missing')).rejects.toThrow(
      FetchHttpError
    );
  });

  it('throws FetchTimeoutError on abort', async () => {
    const mockFetch = vi.fn().mockImplementation(() => {
      const error = new Error('aborted');
      error.name = 'AbortError';
      return Promise.reject(error);
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/slow', 100)).rejects.toThrow(
      FetchTimeoutError
    );
  });

  it('throws FetchNetworkError on network failure', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('ECONNREFUSED'));
    vi.stubGlobal('fetch', mockFetch);

    await expect(fetchOfficialDocs('https://example.com/down')).rejects.toThrow(
      FetchNetworkError
    );
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/fetcher.test.ts`
Expected: FAIL (module not found)

**Step 3: Implement fetcher**

Create `src/fetcher.ts` (adapt from `tmp/fetcher.ts`):

```typescript
export interface FetchResult {
  content: string;
  status: number;
}

export class FetchTimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FetchTimeoutError';
  }
}

export class FetchHttpError extends Error {
  status: number;
  statusText?: string;

  constructor(status: number, statusText?: string) {
    const message = statusText ? `HTTP ${status}: ${statusText}` : `HTTP ${status}`;
    super(message);
    this.name = 'FetchHttpError';
    this.status = status;
    this.statusText = statusText;
  }
}

export class FetchNetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FetchNetworkError';
  }
}

function resolveTimeoutMs(explicit?: number): number {
  if (typeof explicit === 'number' && Number.isFinite(explicit) && explicit >= 0) {
    return explicit;
  }
  const envValue = process.env.FETCH_TIMEOUT_MS?.trim();
  if (envValue && envValue.length > 0) {
    const parsed = Number(envValue);
    if (Number.isFinite(parsed) && parsed >= 0) {
      return parsed;
    }
  }
  return 30000;
}

export async function fetchOfficialDocs(
  url: string,
  timeoutMs?: number
): Promise<FetchResult> {
  const resolvedTimeoutMs = resolveTimeoutMs(timeoutMs);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), resolvedTimeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      redirect: 'follow',
    });

    if (!response.ok) {
      const statusText = response.statusText || undefined;
      throw new FetchHttpError(response.status, statusText);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType && !contentType.toLowerCase().startsWith('text/')) {
      console.warn(`Unexpected content-type for ${url}: ${contentType}`);
    }

    const content = await response.text();
    return { content, status: response.status };
  } catch (err: unknown) {
    const anyErr = err as { name?: string; message?: string };
    if (anyErr?.name === 'AbortError') {
      throw new FetchTimeoutError(`Fetch timeout after ${resolvedTimeoutMs}ms`);
    }
    if (err instanceof FetchHttpError) {
      throw err;
    }
    if (anyErr?.message) {
      throw new FetchNetworkError(`Network error: ${anyErr.message}`);
    }
    throw new FetchNetworkError('Network error: Unknown error');
  } finally {
    clearTimeout(timeoutId);
  }
}
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/fetcher.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/fetcher.ts packages/mcp-servers/extension-docs/tests/fetcher.test.ts
git commit -m "feat(extension-docs): add fetcher module with typed errors"
```

---

## Task 6: Update Loader Module

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/loader.ts`
- Modify: `packages/mcp-servers/extension-docs/tests/loader.test.ts`

**Step 1: Add new tests for loadFromOfficial**

Add to `tests/loader.test.ts`:

```typescript
import { vi } from 'vitest';

// Add new describe block after existing tests:

describe('loadFromOfficial', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-official-test-'));
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('fetches, parses, and filters to extension sections', async () => {
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
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });

  it('falls back to cache on fetch failure', async () => {
    const cachedContent = `# Skills Reference
Source: https://code.claude.com/docs/en/skills

Skills content`;

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.mkdir(path.dirname(cachePath), { recursive: true });
    await fs.writeFile(cachePath, cachedContent);

    const mockFetch = vi.fn().mockRejectedValue(new Error('Network down'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('skills');
  });
});
```

**Step 2: Run tests to verify new tests fail**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/loader.test.ts`
Expected: New tests FAIL (loadFromOfficial not exported)

**Step 3: Update loader implementation**

Add to `src/loader.ts` (keep existing `loadMarkdownFiles` function):

```typescript
import type { MarkdownFile, ParsedSection } from './types.js';
import { fetchOfficialDocs, FetchHttpError, FetchNetworkError, FetchTimeoutError } from './fetcher.js';
import { parseSections } from './parser.js';
import { filterToExtensions } from './filter.js';
import { readCache, writeCache, getDefaultCachePath } from './cache.js';

function resolveCachePath(override?: string): string {
  if (override) return override;
  const envPath = process.env.CACHE_PATH?.trim();
  return envPath && envPath.length > 0 ? envPath : getDefaultCachePath();
}

export async function loadFromOfficial(url: string, cachePath?: string): Promise<MarkdownFile[]> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const sections = await fetchAndParse(url, resolvedCachePath);
  const filtered = filterToExtensions(sections).filter((s) => s.content.trim().length > 0);
  return filtered.map((s) => ({
    path: s.sourceUrl || s.title || 'unknown',
    content: s.content,
  }));
}

async function fetchAndParse(url: string, cachePath: string): Promise<ParsedSection[]> {
  try {
    const { content } = await fetchOfficialDocs(url);
    await writeCache(cachePath, content);
    return parseSections(content);
  } catch (err: unknown) {
    if (err instanceof FetchTimeoutError) {
      console.error(err.message);
    } else if (err instanceof FetchHttpError) {
      console.error(err.message);
    } else if (err instanceof FetchNetworkError) {
      console.error(err.message);
    } else {
      console.error(`Fetch failed: ${err instanceof Error ? err.message : String(err)}`);
    }

    const cached = await readCache(cachePath);
    if (cached) {
      const ageHours = (cached.age / 3600000).toFixed(1);
      console.warn(`Using cached docs (${ageHours}h old)`);
      return parseSections(cached.content);
    }

    throw err;
  }
}
```

**Step 4: Run tests to verify they pass**

Run: `cd packages/mcp-servers/extension-docs && npm test -- tests/loader.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/loader.ts packages/mcp-servers/extension-docs/tests/loader.test.ts
git commit -m "feat(extension-docs): add loadFromOfficial with cache fallback"
```

---

## Task 7: Update Index to Use New Loader

**Files:**

- Modify: `packages/mcp-servers/extension-docs/src/index.ts`

**Step 1: Update imports**

Add `loadFromOfficial` to imports, remove `fs` if only used for DOCS_PATH check:

```typescript
import { loadFromOfficial } from './loader.js';
```

**Step 2: Update doLoadIndex function**

Replace DOCS_PATH logic with DOCS_URL:

```typescript
async function doLoadIndex(): Promise<BM25Index | null> {
  const isRetry = loadError !== null;

  lastLoadAttempt = Date.now();
  loadError = null;
  clearParseWarnings();

  if (isRetry) {
    console.error('Retrying documentation load...');
  }

  const docsUrl = process.env.DOCS_URL ?? 'https://code.claude.com/docs/llms-full.txt';

  try {
    const files = await loadFromOfficial(docsUrl);
    if (files.length === 0) {
      loadError = 'No extension documentation found after filtering';
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
    console.error(`Loaded ${chunks.length} chunks from ${files.length} sections`);
    return index;
  } catch (err) {
    loadError = `Failed to load docs: ${err instanceof Error ? err.message : 'unknown'}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }
}
```

**Step 3: Verify build succeeds**

Run: `cd packages/mcp-servers/extension-docs && npm run build`
Expected: No errors

**Step 4: Run all tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add packages/mcp-servers/extension-docs/src/index.ts
git commit -m "feat(extension-docs): switch to auto-sync from official docs"
```

---

## Task 8: Update Server Tests

**Files:**

- Modify: `packages/mcp-servers/extension-docs/tests/server.test.ts`

**Step 1: Read current server tests to understand what needs updating**

**Step 2: Update tests to mock fetch instead of DOCS_PATH filesystem setup**

**Step 3: Run tests**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/server.test.ts
git commit -m "test(extension-docs): update server tests for auto-sync"
```

---

## Task 9: Integration Test

**Files:**

- Create: `packages/mcp-servers/extension-docs/tests/integration.test.ts`

**Step 1: Write integration test (skipped by default)**

```typescript
import { describe, it, expect } from 'vitest';
import { loadFromOfficial } from '../src/loader.js';

describe('integration: loadFromOfficial with real network', () => {
  it.skip('fetches real docs from code.claude.com', async () => {
    const files = await loadFromOfficial('https://code.claude.com/docs/llms-full.txt');

    expect(files.length).toBeGreaterThan(0);

    const hasHooks = files.some((f) => f.path.includes('hooks'));
    const hasSkills = files.some((f) => f.path.includes('skills'));
    const hasMcp = files.some((f) => f.path.includes('mcp'));

    expect(hasHooks || hasSkills || hasMcp).toBe(true);
  }, 60000);
});
```

**Step 2: Commit**

```bash
git add packages/mcp-servers/extension-docs/tests/integration.test.ts
git commit -m "test(extension-docs): add integration test for real fetch"
```

---

## Task 10: Clean Up

**Step 1: Remove tmp prototype files**

```bash
rm -rf tmp/
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove tmp prototype files"
```

---

## Task 11: Final Verification

**Step 1: Run full test suite**

Run: `cd packages/mcp-servers/extension-docs && npm test`
Expected: All tests PASS

**Step 2: Build**

Run: `cd packages/mcp-servers/extension-docs && npm run build`
Expected: No errors

**Step 3: Manual smoke test**

Run: `cd packages/mcp-servers/extension-docs && npm start`
Expected: Server starts, logs "Loaded N chunks from M sections"
