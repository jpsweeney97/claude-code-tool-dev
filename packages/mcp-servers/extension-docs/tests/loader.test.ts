// tests/loader.test.ts
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { loadMarkdownFiles } from '../src/loader.js';
import { parseFrontmatter } from '../src/frontmatter.js';
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
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

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
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

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
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

    // Parse should succeed even with special characters
    const { frontmatter, warnings } = parseFrontmatter(files[0].content, files[0].path);

    expect(warnings).toHaveLength(0);
    expect(frontmatter.topic).toBe('Hooks: The "Complete" Guide');
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
    const files = await loadFromOfficial('https://example.com/docs', cachePath);

    const { frontmatter } = parseFrontmatter(files[0].content, files[0].path);

    expect(frontmatter.category).toBe('hooks');
    expect(frontmatter.id).toBe('hooks-input-schema');
  });
});
