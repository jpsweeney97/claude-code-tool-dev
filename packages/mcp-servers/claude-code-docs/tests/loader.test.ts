// tests/loader.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

let parseFrontmatter: typeof import('../src/frontmatter.js').parseFrontmatter;

/**
 * Build mock content with at least minCount sections, using a base URL prefix.
 * The content cache write guard requires ≥40 sections (CACHE_WRITE_MIN_SECTIONS).
 * Use this to build test fixtures that pass the guard so tests focus on other behavior.
 */
function buildLargeMockContent(
  primarySections: Array<{ title: string; url: string; body: string }>,
  padTo = 40,
  padUrlBase = 'https://code.claude.com/docs/en/pad',
): string {
  const sections = [...primarySections];
  while (sections.length < padTo) {
    const i = sections.length;
    sections.push({ title: `Pad Section ${i}`, url: `${padUrlBase}-${i}`, body: `Padding content ${i}` });
  }
  return sections
    .map(s => `# ${s.title}\nSource: ${s.url}\n\n${s.body}`)
    .join('\n---\n');
}

describe('fetchAndParse with TTL', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-ttl-test-'));
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
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

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-official-test-'));
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
    ({ parseFrontmatter } = await import('../src/frontmatter.js'));
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('fetches, parses, and returns all sections (no filtering)', async () => {
    const mockContent = buildLargeMockContent([
      { title: 'Hooks Guide', url: 'https://code.claude.com/docs/en/hooks', body: 'Hooks content here' },
      { title: 'Quickstart', url: 'https://code.claude.com/docs/en/quickstart', body: 'Getting started content' },
    ]);

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

    // Expects at least 2 real sections (plus padding to meet the fixed cache-write floor of 40)
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
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const mockContent = buildLargeMockContent([
      { title: 'Hooks Guide', url: 'https://code.claude.com/docs/en/hooks', body: 'Hooks content here' },
    ]);

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

    const hooksFile = files.find(f => f.path.includes('hooks'));
    expect(hooksFile).toBeDefined();

    // Content should start with synthetic frontmatter
    expect(hooksFile!.content).toMatch(/^---\n/);
    expect(hooksFile!.content).toContain('topic:');
    expect(hooksFile!.content).toContain('id:');
    expect(hooksFile!.content).toContain('category:');
  });

  it('synthetic frontmatter is parseable by parseFrontmatter', async () => {
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const mockContent = buildLargeMockContent([
      { title: 'Hooks Guide', url: 'https://code.claude.com/docs/en/hooks', body: 'Hooks content here' },
    ]);

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

    // The hooks section is the first primary section; parse its synthetic frontmatter
    const hooksFile = files.find(f => f.path.includes('hooks') && !f.path.includes('pad'));
    expect(hooksFile).toBeDefined();
    const { frontmatter, body, warnings } = parseFrontmatter(hooksFile!.content, hooksFile!.path);

    expect(warnings).toHaveLength(0);
    expect(frontmatter.topic).toBe('Hooks Guide');
    expect(frontmatter.id).toBe('hooks');
    expect(frontmatter.category).toBe('hooks');
    expect(body).toContain('Hooks content here');
  });

  it('handles titles with special characters in synthetic frontmatter', async () => {
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const mockContent = buildLargeMockContent([
      { title: 'Hooks: The "Complete" Guide', url: 'https://code.claude.com/docs/en/hooks', body: 'Content' },
    ]);

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
    const hooksFile = files.find(f => f.path.includes('hooks') && !f.path.includes('pad'));
    expect(hooksFile).toBeDefined();
    const { frontmatter, warnings } = parseFrontmatter(hooksFile!.content, hooksFile!.path);

    expect(warnings).toHaveLength(0);
    expect(frontmatter.topic).toBe('Hooks: The "Complete" Guide');
  });

  it('logs parse diagnostics to stderr', async () => {
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const mockContent = buildLargeMockContent([
      { title: 'Hooks Guide', url: 'https://code.claude.com/docs/en/hooks', body: 'Hooks content here' },
      { title: 'Quickstart', url: 'https://code.claude.com/docs/en/quickstart', body: 'Getting started content' },
    ]);

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
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const mockContent = buildLargeMockContent([
      { title: 'Input Schema', url: 'https://code.claude.com/docs/en/hooks/input-schema', body: 'Schema details' },
    ]);

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

    const inputSchemaFile = files.find(f => f.path.includes('hooks/input-schema'));
    expect(inputSchemaFile).toBeDefined();
    const { frontmatter } = parseFrontmatter(inputSchemaFile!.content, inputSchemaFile!.path);

    expect(frontmatter.category).toBe('hooks');
    expect(frontmatter.id).toBe('hooks-input-schema');
  });
});

describe('content validation', () => {
  // The cache-write guard uses a fixed floor: CACHE_WRITE_MIN_SECTIONS = 40.
  // It is not env-tunable. These tests verify the fixed-floor behavior.
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-validation-test-'));
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('rejects content below the fixed 40-section floor and falls back to cache', async () => {
    // Cached content with 40 sections (meets the floor)
    const cachedContent = buildLargeMockContent(
      [{ title: 'Good Section', url: 'https://code.claude.com/docs/en/hooks', body: 'Good content' }],
      40,
      'https://code.claude.com/docs/en/cached',
    );

    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.mkdir(path.dirname(cachePath), { recursive: true });
    await fs.writeFile(cachePath, cachedContent);

    // Fetched content with only 2 sections (below the fixed floor of 40)
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

    // Should fall back to cached content (40 sections), not truncated (2 sections)
    expect(files).toHaveLength(40);
  });

  it('throws ContentValidationError when content is below floor and no cache exists', async () => {
    // Only 1 section — below the fixed floor of 40
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

  it('rejects content at exactly floor minus one (39 sections) when no cache exists', async () => {
    // 39 sections — one below the fixed floor of 40 — pins the off-by-one boundary
    const truncatedContent = buildLargeMockContent(
      [{ title: 'Section 1', url: 'https://code.claude.com/docs/en/section-1', body: 'Content' }],
      39,
    );

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

  it('accepts content at exactly the fixed floor (40 sections)', async () => {
    // Build content with exactly 40 sections
    const validContent = buildLargeMockContent(
      [{ title: 'Section 1', url: 'https://code.claude.com/docs/en/section-1', body: 'Content' }],
      40,
    );

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

    expect(files).toHaveLength(40);
  });

  it('ContentValidationError fires BEFORE cache write (cache stays good)', async () => {
    // Pre-existing cache with 40 good sections
    const cachedContent = buildLargeMockContent(
      [{ title: 'Good', url: 'https://code.claude.com/docs/en/good', body: 'Good' }],
      40,
    );
    const cachePath = path.join(tempDir, 'cache.txt');
    await fs.writeFile(cachePath, cachedContent);
    const cacheStatBefore = await fs.stat(cachePath);

    // Truncated fetch (1 section) → should throw and NOT overwrite the cache
    const truncated = `# One\nSource: https://example.com/one\n\nContent`;
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true, status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(truncated),
    }));

    const { loadFromOfficial } = await import('../src/loader.js');
    // With good stale cache available, loader falls back (not throws)
    const { files } = await loadFromOfficial('https://example.com/docs', cachePath, true);

    // Good cache should still be served
    expect(files).toHaveLength(40);
    // Cache file should not have been overwritten (mtime unchanged)
    const cacheStatAfter = await fs.stat(cachePath);
    expect(cacheStatAfter.mtimeMs).toBe(cacheStatBefore.mtimeMs);
  });
});

describe('fetchAndParse error discrimination', () => {
  let tempDir: string;
  let originalMaxResponseBytes: string | undefined;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-error-test-'));
    originalMaxResponseBytes = process.env.MAX_RESPONSE_BYTES;
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
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

  const cachedContent = `# Stale Section
Source: https://code.claude.com/docs/en/hooks

Stale hooks content`;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-stale-b7-'));
    originalMaxStale = process.env.DOCS_CACHE_MAX_STALE_MS;
    originalCacheTtl = process.env.CACHE_TTL_MS;
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

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-provenance-'));
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('returns sourceKind=fetched on successful live fetch', async () => {
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const content = buildLargeMockContent([
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

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'loader-diagnostics-'));
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('includes structural diagnostic counts', async () => {
    // Use buildLargeMockContent to meet the fixed cache-write floor (CACHE_WRITE_MIN_SECTIONS = 40)
    const primarySections = [
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
      { title: 'Skills', url: 'https://code.claude.com/docs/en/skills', body: 'Skills docs' },
      { title: 'Quickstart', url: 'https://code.claude.com/docs/en/quickstart', body: 'Getting started' },
    ];
    const content = buildLargeMockContent(primarySections);

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    const d = result.diagnostics;
    // 3 primary + 37 padding = 40 total (buildLargeMockContent pads to 40)
    expect(d.sourceAnchoredCount).toBe(40);
    expect(d.nonEmptySectionCount).toBe(40);
    expect(d.sectionCount).toBe(40);
    expect(d.fallbackSectionCount).toBeGreaterThanOrEqual(0);
    expect(Array.isArray(d.unmappedSegments)).toBe(true);

    // diagnostics does NOT have parseWarningCount (that comes from lifecycle)
    expect(d).not.toHaveProperty('parseWarningCount');
  });

  it('counts fallback sections correctly', async () => {
    // The loader now computes fallbackSectionCount: sections where deriveCategory
    // returns 'uncategorized' (no URL segment matched in SECTION_TO_CATEGORY).
    // - 'https://code.claude.com/docs/en/some-unknown-thing' → 'uncategorized' (unmapped)
    // - 'https://code.claude.com/docs/en/overview' → 'overview' (explicitly mapped)
    // - 'https://code.claude.com/docs/en/hooks' → 'hooks' (mapped)
    // Pad with known-category (hooks) URLs to avoid inflating fallbackSectionCount.
    const primary = [
      { title: 'Overview', url: 'https://code.claude.com/docs/en/overview', body: 'Overview docs' },
      { title: 'Hooks', url: 'https://code.claude.com/docs/en/hooks', body: 'Hook docs' },
      { title: 'Unknown', url: 'https://code.claude.com/docs/en/some-unknown-thing', body: 'Unknown docs' },
    ];
    const content = buildLargeMockContent(primary, 40, 'https://code.claude.com/docs/en/hooks/pad');

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    // Only 'some-unknown-thing' is uncategorized; 'overview' and 'hooks' are mapped,
    // padding uses hooks URLs → category 'hooks', no fallback.
    expect(result.diagnostics.fallbackSectionCount).toBe(1);
  });

  it('returns unmappedSegments sorted by count desc then name asc', async () => {
    // Pad with a KNOWN-category base ('hooks') so the padding sections never land in
    // unmappedSegments — only the two intended unknown segments are unmapped. This lets
    // the ordering assertion be exact and UNCONDITIONAL (no length guard).
    const content = buildLargeMockContent(
      [
        { title: 'A', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'A' },
        { title: 'B', url: 'https://code.claude.com/docs/en/zzz-unknown', body: 'B' },
        { title: 'C', url: 'https://code.claude.com/docs/en/aaa-unknown', body: 'C' },
      ],
      40,
      'https://code.claude.com/docs/en/hooks/pad',
    );

    vi.stubGlobal('fetch', mockFetchOk(content));

    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'cache.txt');
    const result = await loadFromOfficial('https://example.com/docs', cachePath);

    const segs = result.diagnostics.unmappedSegments;
    // zzz-unknown appears 2x, aaa-unknown 1x → zzz first by count, aaa second.
    expect(segs).toHaveLength(2);
    expect(segs[0]).toEqual(['zzz-unknown', 2]); // count desc
    expect(segs[1]).toEqual(['aaa-unknown', 1]); // then name asc
  });
});
