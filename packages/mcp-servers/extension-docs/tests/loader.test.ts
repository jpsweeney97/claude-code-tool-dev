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
