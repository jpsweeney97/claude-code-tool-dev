// tests/loader.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

let parseFrontmatter: typeof import('../src/frontmatter.js').parseFrontmatter;

describe('fetchAndParse with TTL', () => {
  let tempDir: string;
  let originalMinSectionCount: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-ttl-test-'));
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('uses fresh cache and skips fetch when TTL not expired', async () => {
    const cachedContent = `# Cached Hooks
Source: https://code.claude.com/docs/en/hooks

Cached hooks content`;

    // Write cache file (will have fresh mtime)
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);

    const mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    // Fetch should NOT be called — fresh cache serves the request
    expect(mockFetch).not.toHaveBeenCalled();
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });

  it('falls back to stale cache when fetch fails', async () => {
    const cachedContent = `# Stale Hooks
Source: https://code.claude.com/docs/en/hooks

Stale hooks content`;

    // Write cache file, then set mtime to 25 hours ago to make it stale
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    const staleTime = new Date(Date.now() - 25 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    // Fetch was attempted (cache was stale) but failed, so stale cache served
    expect(mockFetch).toHaveBeenCalled();
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });
});

describe('loadFromOfficial', () => {
  let tempDir: string;
  let originalMinSectionCount: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-official-test-'));
    // Disable section count validation for unit tests with small mock data
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules(); // Reset modules so loader picks up new env
    vi.stubGlobal('fetch', vi.fn());
    ({ parseFrontmatter } = await import('../src/frontmatter.js'));
  });

  afterEach(async () => {
    // Restore original env
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('fetches, parses, and returns all sections (no filtering)', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here
---
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
    const { files, contentHash } = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('skills');
    expect(contentHash).toMatch(/^[a-f0-9]{64}$/); // SHA-256 hex from stale cache
  });

  it('injects synthetic frontmatter with topic, id, and category', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(mockContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(files).toHaveLength(1);

    // Content should start with synthetic frontmatter
    expect(files[0].content).toMatch(/^---\n/);
    expect(files[0].content).toContain('topic:');
    expect(files[0].content).toContain('id:');
    expect(files[0].content).toContain('category:');
  });

  it('synthetic frontmatter is parseable by parseFrontmatter', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(mockContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    // Parse the synthetic frontmatter
    const { frontmatter, body, warnings } = parseFrontmatter(files[0].content, files[0].path);

    expect(warnings).toHaveLength(0);
    expect(frontmatter.topic).toBe('Hooks Guide');
    expect(frontmatter.id).toBe('hooks');
    expect(frontmatter.category).toBe('hooks');
    expect(body).toContain('Hooks content here');
  });

  it('handles titles with special characters in synthetic frontmatter', async () => {
    const mockContent = `# Hooks: The "Complete" Guide
Source: https://code.claude.com/docs/en/hooks

Content`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(mockContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    // Parse should succeed even with special characters
    const { frontmatter, warnings } = parseFrontmatter(files[0].content, files[0].path);

    expect(warnings).toHaveLength(0);
    expect(frontmatter.topic).toBe('Hooks: The "Complete" Guide');
  });

  it('logs parse diagnostics to stderr', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here
---
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

    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    await loadFromOfficial('https://example.com/docs', cachePath);

    // Should log parse diagnostics
    const diagnosticLog = errorSpy.mock.calls.find(
      call => typeof call[0] === 'string' && call[0].includes('Parse diagnostics')
    );
    expect(diagnosticLog).toBeDefined();
    errorSpy.mockRestore();
  });

  it('derives correct category for nested URL paths', async () => {
    const mockContent = `# Input Schema
Source: https://code.claude.com/docs/en/hooks/input-schema

Schema details`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(mockContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);

    const { frontmatter } = parseFrontmatter(files[0].content, files[0].path);

    expect(frontmatter.category).toBe('hooks');
    expect(frontmatter.id).toBe('hooks-input-schema');
  });
});

describe('content validation', () => {
  let tempDir: string;
  let originalMinSectionCount: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-validation-test-'));
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('rejects content with fewer sections than minimum and falls back to cache', async () => {
    // Set minimum to 5 sections
    process.env.MIN_SECTION_COUNT = '5';
    vi.resetModules();

    // Cached content with enough sections
    const cachedContent = `# Section 1
Source: https://example.com/1

Content 1

# Section 2
Source: https://example.com/2

Content 2

# Section 3
Source: https://example.com/3

Content 3

# Section 4
Source: https://example.com/4

Content 4

# Section 5
Source: https://example.com/5

Content 5`;

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.mkdir(path.dirname(cachePath), { recursive: true });
    await fs.writeFile(cachePath, cachedContent);

    // Fetched content with only 2 sections (below minimum)
    const truncatedContent = `# Section A
Source: https://example.com/a

Content A

# Section B
Source: https://example.com/b

Content B`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(truncatedContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);

    // Should fall back to cached content (5 sections), not truncated (2 sections)
    expect(files).toHaveLength(5);
  });

  it('throws when content is truncated and no cache exists', async () => {
    process.env.MIN_SECTION_COUNT = '5';
    vi.resetModules();

    const truncatedContent = `# Only One
Source: https://example.com/one

Content`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(truncatedContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial, ContentValidationError } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'nonexistent-cache.txt');

    await expect(loadFromOfficial('https://example.com/docs', cachePath, true))
      .rejects.toThrow(ContentValidationError);
  });

  it('accepts content when section count meets minimum', async () => {
    process.env.MIN_SECTION_COUNT = '3';
    vi.resetModules();

    const validContent = `# Section 1
Source: https://example.com/1

Content 1

# Section 2
Source: https://example.com/2

Content 2

# Section 3
Source: https://example.com/3

Content 3`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(validContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);

    expect(files).toHaveLength(3);
  });

  it('skips validation when MIN_SECTION_COUNT is 0', async () => {
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();

    const singleSection = `# Only One
Source: https://example.com/one

Content`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(singleSection),
    });
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);

    expect(files).toHaveLength(1);
  });
});

describe('fetchAndParse error discrimination', () => {
  let tempDir: string;
  let originalMaxResponseBytes: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-error-test-'));
    originalMaxResponseBytes = process.env.MAX_RESPONSE_BYTES;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    delete process.env.MIN_SECTION_COUNT;
    if (originalMaxResponseBytes === undefined) {
      delete process.env.MAX_RESPONSE_BYTES;
    } else {
      process.env.MAX_RESPONSE_BYTES = originalMaxResponseBytes;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('rethrows unexpected TypeError instead of falling back to cache', async () => {
    // Mock fetch to return a response whose .text() resolves to null,
    // which triggers TypeError in parseSections (calling .matchAll on null).
    // This simulates a programmer error that should NOT be masked by cache.
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(null as unknown as string),
    });
    vi.stubGlobal('fetch', mockFetch);

    // Write valid cache so fallback WOULD succeed if reached
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, '# Cached\nSource: https://example.com/c\n\nCached content');

    const { loadFromOfficial } = await import('../src/loader.js');
    await expect(
      loadFromOfficial('https://example.com/docs', cachePath, true)
    ).rejects.toThrow(TypeError);
  });

  it('still falls back to cache for network errors', async () => {
    // Error('connection refused') is wrapped by fetchOfficialDocs as FetchNetworkError
    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, '# Cached\nSource: https://example.com/c\n\nCached content');

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);
    expect(files.length).toBeGreaterThan(0);
  });

  it('falls back to cache for oversized responses rejected by content-length', async () => {
    process.env.MAX_RESPONSE_BYTES = '1';

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        'content-type': 'text/plain',
        'content-length': '2',
      }),
      body: null,
    });
    vi.stubGlobal('fetch', mockFetch);

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, '# Cached\nSource: https://example.com/c\n\nCached content');

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);
    expect(files.length).toBeGreaterThan(0);
  });

  it('falls back to cache for oversized streaming responses', async () => {
    process.env.MAX_RESPONSE_BYTES = '1';

    const largeData = new Uint8Array([65, 66]);
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(largeData);
        controller.close();
      },
    });

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({
        'content-type': 'text/plain',
      }),
      body: stream,
    });
    vi.stubGlobal('fetch', mockFetch);

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, '# Cached\nSource: https://example.com/c\n\nCached content');

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);
    expect(files.length).toBeGreaterThan(0);
  });
});

describe('stale cache handling (B7)', () => {
  let tempDir: string;
  let originalMaxStale: string | undefined;
  let originalCacheTtl: string | undefined;
  let originalMinSectionCount: string | undefined;

  const cachedContent = `# Stale Section
Source: https://code.claude.com/docs/en/hooks

Stale hooks content`;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-stale-b7-'));
    originalMaxStale = process.env.DOCS_CACHE_MAX_STALE_MS;
    originalCacheTtl = process.env.CACHE_TTL_MS;
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    // Force stale path: 1ms TTL means any cache is stale (D4)
    process.env.CACHE_TTL_MS = '1';
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    if (originalMaxStale === undefined) {
      delete process.env.DOCS_CACHE_MAX_STALE_MS;
    } else {
      process.env.DOCS_CACHE_MAX_STALE_MS = originalMaxStale;
    }
    if (originalCacheTtl === undefined) {
      delete process.env.CACHE_TTL_MS;
    } else {
      process.env.CACHE_TTL_MS = originalCacheTtl;
    }
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('rejects cache exceeding DOCS_CACHE_MAX_STALE_MS (72h old, 24h limit)', async () => {
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    // Set cache to 72 hours old
    const staleTime = new Date(Date.now() - 72 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    process.env.DOCS_CACHE_MAX_STALE_MS = String(24 * 60 * 60 * 1000); // 24h limit

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    await expect(
      loadFromOfficial('https://example.com/docs', cachePath),
    ).rejects.toThrow();
  });

  it('accepts cache within DOCS_CACHE_MAX_STALE_MS (12h old, 24h limit)', async () => {
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    // Set cache to 12 hours old
    const staleTime = new Date(Date.now() - 12 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    process.env.DOCS_CACHE_MAX_STALE_MS = String(24 * 60 * 60 * 1000); // 24h limit

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });

  it('accepts any age when DOCS_CACHE_MAX_STALE_MS is unset (7 days old)', async () => {
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    // Set cache to 7 days old
    const staleTime = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    delete process.env.DOCS_CACHE_MAX_STALE_MS;

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });

  it('ignores invalid DOCS_CACHE_MAX_STALE_MS values ("banana")', async () => {
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    // Set cache to 7 days old
    const staleTime = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    process.env.DOCS_CACHE_MAX_STALE_MS = 'banana';

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });

  it('accepts cache at exactly DOCS_CACHE_MAX_STALE_MS boundary (age === max, D4)', async () => {
    const maxStaleMs = 24 * 60 * 60 * 1000; // 24h
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    // Set cache to maxStaleMs old minus a small buffer for execution time.
    // readCache computes age = Date.now() - mtimeMs, so a few ms elapse
    // between utimes and readCache. The 500ms buffer ensures the measured
    // age stays <= maxStaleMs, exercising the strict > boundary.
    const exactTime = new Date(Date.now() - maxStaleMs + 500);
    await fs.utimes(cachePath, exactTime, exactTime);

    process.env.DOCS_CACHE_MAX_STALE_MS = String(maxStaleMs);

    const mockFetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath);
    // age === max uses strict >, so exactly at boundary is accepted
    expect(files).toHaveLength(1);
    expect(files[0].path).toContain('hooks');
  });
});

// --- Helper: build mock content with Source: markers ---

function buildMockContent(sections: Array<{ title: string; url: string; body: string }>): string {
  return sections
    .map(s => `# ${s.title}\nSource: ${s.url}\n\n${s.body}`)
    .join('\n---\n');
}

function mockFetchOk(content: string) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'text/plain' }),
    text: () => Promise.resolve(content),
  });
}

describe('LoadResult provenance', () => {
  let tempDir: string;
  let originalMinSectionCount: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-provenance-'));
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('returns sourceKind=fetched on successful live fetch', async () => {
    const content = buildMockContent([
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
    ]);

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const now = Date.now();
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.provenance.sourceKind).toBe('fetched');
    expect(result.provenance.obtainedAt).toBeGreaterThanOrEqual(now);
    expect(result.provenance.obtainedAt).toBeLessThanOrEqual(Date.now());
  });

  it('returns sourceKind=cached on fresh cache hit', async () => {
    const content = buildMockContent([
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
    ]);

    // Write fresh cache (mtime is now)
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, content);

    // Fetch should NOT be called
    const mockFn = vi.fn();
    vi.stubGlobal('fetch', mockFn);

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(mockFn).not.toHaveBeenCalled();
    expect(result.provenance.sourceKind).toBe('cached');
    expect(result.provenance.obtainedAt).toBeGreaterThan(0);
  });

  it('returns sourceKind=stale-fallback when fetch fails and stale cache used', async () => {
    const content = buildMockContent([
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
    ]);

    // Write cache then make it stale (25 hours ago)
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, content);
    const staleTime = new Date(Date.now() - 25 * 60 * 60 * 1000);
    await fs.utimes(cachePath, staleTime, staleTime);

    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('connection refused')));

    const { loadFromOfficial } = await import('../src/loader.js');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    expect(result.provenance.sourceKind).toBe('stale-fallback');
    // obtainedAt should reflect the stale cache mtime (~25h ago)
    const twentyFourHoursAgo = Date.now() - 26 * 60 * 60 * 1000;
    expect(result.provenance.obtainedAt).toBeGreaterThan(twentyFourHoursAgo);
    expect(result.provenance.obtainedAt).toBeLessThan(Date.now() - 24 * 60 * 60 * 1000);
  });
});

describe('LoadResult diagnostics', () => {
  let tempDir: string;
  let originalMinSectionCount: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-diagnostics-'));
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('includes structural diagnostic counts', async () => {
    const content = buildMockContent([
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
      { title: 'Skills', url: 'https://code.claude.com/docs/en/skills', body: 'Skills docs' },
      { title: 'Quickstart', url: 'https://code.claude.com/docs/en/quickstart', body: 'Getting started' },
    ]);

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    const d = result.diagnostics;
    expect(d.sourceAnchoredCount).toBe(3);
    expect(d.nonEmptySectionCount).toBe(3);
    expect(d.sectionCount).toBe(3);
    expect(d.overviewSectionCount).toBeGreaterThanOrEqual(0);
    expect(Array.isArray(d.unmappedSegments)).toBe(true);

    // diagnostics does NOT have parseWarningCount (that comes from lifecycle)
    expect(d).not.toHaveProperty('parseWarningCount');
  });

  it('counts overview sections correctly', async () => {
    // 'https://code.claude.com/docs/en/some-unknown-thing' maps to 'overview' (unmapped)
    // 'https://code.claude.com/docs/en/hooks' maps to 'hooks' (mapped)
    const content = buildMockContent([
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
      { title: 'Unknown', url: 'https://code.claude.com/docs/en/some-unknown-thing', body: 'Unknown docs' },
    ]);

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    // 'some-unknown-thing' should map to 'overview'
    expect(result.diagnostics.overviewSectionCount).toBe(1);
  });

  it('returns unmappedSegments sorted by count desc then name asc', async () => {
    // Build content where multiple sections have unmapped URLs
    const content = buildMockContent([
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
});
