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
