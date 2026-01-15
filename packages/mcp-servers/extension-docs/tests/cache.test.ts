import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  readCache,
  writeCache,
  getDefaultCachePath,
  getCacheTtlMs,
  readCacheIfFresh,
  getDefaultIndexCachePath,
  readIndexCache,
  writeIndexCache,
} from '../src/cache.js';
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

describe('getCacheTtlMs', () => {
  const originalEnv = process.env.CACHE_TTL_MS;

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.CACHE_TTL_MS;
    } else {
      process.env.CACHE_TTL_MS = originalEnv;
    }
  });

  it('returns default 24h when env not set', () => {
    delete process.env.CACHE_TTL_MS;
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for invalid values', () => {
    process.env.CACHE_TTL_MS = 'not-a-number';
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for negative values', () => {
    process.env.CACHE_TTL_MS = '-1000';
    expect(getCacheTtlMs()).toBe(86400000);
  });

  it('returns parsed value within bounds', () => {
    process.env.CACHE_TTL_MS = '3600000';
    expect(getCacheTtlMs()).toBe(3600000);
  });

  it('caps at 1 year max', () => {
    process.env.CACHE_TTL_MS = '999999999999999';
    expect(getCacheTtlMs()).toBe(1000 * 60 * 60 * 24 * 365);
  });
});

describe('readCacheIfFresh', () => {
  let tempDir: string;
  let cachePath: string;
  const originalEnv = process.env.CACHE_TTL_MS;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'cache-ttl-test-'));
    cachePath = path.join(tempDir, 'test-cache.txt');
    delete process.env.CACHE_TTL_MS;
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
    if (originalEnv === undefined) {
      delete process.env.CACHE_TTL_MS;
    } else {
      process.env.CACHE_TTL_MS = originalEnv;
    }
  });

  it('returns null for non-existent cache', async () => {
    const result = await readCacheIfFresh(cachePath);
    expect(result).toBeNull();
  });

  it('returns fresh cache when within TTL', async () => {
    await writeCache(cachePath, 'fresh content');
    const result = await readCacheIfFresh(cachePath);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('fresh content');
  });

  it('returns null for stale cache', async () => {
    await writeCache(cachePath, 'stale content');
    // Set TTL to 0 to make cache immediately stale
    process.env.CACHE_TTL_MS = '0';
    const result = await readCacheIfFresh(cachePath);
    expect(result).toBeNull();
  });
});

describe('index cache helpers', () => {
  let tempDir: string;
  let indexPath: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'index-cache-test-'));
    indexPath = path.join(tempDir, 'test-index.json');
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('getDefaultIndexCachePath returns json file path', () => {
    const indexCachePath = getDefaultIndexCachePath();
    expect(indexCachePath).toMatch(/extension-docs[/\\]llms-full\.index\.json$/);
  });

  it('writeIndexCache and readIndexCache round-trip', async () => {
    const data = { version: 1, chunks: [], test: 'value' };
    await writeIndexCache(indexPath, data);
    const result = await readIndexCache(indexPath);
    expect(result).toEqual(data);
  });

  it('readIndexCache returns null for non-existent file', async () => {
    const result = await readIndexCache(indexPath);
    expect(result).toBeNull();
  });

  it('readIndexCache returns null for invalid JSON', async () => {
    await fs.writeFile(indexPath, 'not valid json {{{');
    const result = await readIndexCache(indexPath);
    expect(result).toBeNull();
  });
});
