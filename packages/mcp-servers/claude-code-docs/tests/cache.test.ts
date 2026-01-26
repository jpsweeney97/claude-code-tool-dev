import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as path from 'path';
import * as os from 'os';

vi.mock('node:fs/promises', async (importOriginal) => {
  const actual = await importOriginal<typeof import('node:fs/promises')>();
  const mocked = {
    ...actual,
    unlink: vi.fn(actual.unlink),
    writeFile: vi.fn(actual.writeFile),
  };
  return {
    ...mocked,
    default: mocked,
  };
});

let cache: typeof import('../src/cache.js');
let fs: typeof import('node:fs/promises');

beforeEach(async () => {
  cache = await import('../src/cache.js');
  const fsModule = await import('node:fs/promises');
  fs = fsModule as typeof import('node:fs/promises');
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.resetModules();
});

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
    const result = await cache.readCache(cachePath);
    expect(result).toBeNull();
  });

  it('writeCache creates file and readCache reads it', async () => {
    await cache.writeCache(cachePath, 'test content');
    const result = await cache.readCache(cachePath);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('test content');
    expect(result!.age).toBeGreaterThanOrEqual(0);
    expect(result!.age).toBeLessThan(1000);
  });

  it('writeCache creates parent directories', async () => {
    const nestedPath = path.join(tempDir, 'deep', 'nested', 'cache.txt');
    await cache.writeCache(nestedPath, 'nested content');
    const result = await cache.readCache(nestedPath);
    expect(result!.content).toBe('nested content');
  });

  it('writeCache overwrites existing file', async () => {
    await cache.writeCache(cachePath, 'first');
    await cache.writeCache(cachePath, 'second');
    const result = await cache.readCache(cachePath);
    expect(result!.content).toBe('second');
  });

  it('logs warning when lock cleanup fails', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.mocked(fs.unlink).mockImplementation(async (target, ...rest) => {
      if (String(target).endsWith('.lock')) {
        throw new Error('lock cleanup failed');
      }
      return (await vi.importActual<typeof import('node:fs/promises')>('node:fs/promises')).unlink(
        target as string,
        ...(rest as [any])
      );
    });

    await cache.writeCache(cachePath, 'lock-warning');

    expect(warnSpy).toHaveBeenCalled();
  });

  it('logs warning when temp cleanup fails after write error', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.mocked(fs.writeFile).mockRejectedValueOnce(new Error('write failed'));
    vi.mocked(fs.unlink).mockImplementation(async (target, ...rest) => {
      if (String(target).includes('.tmp')) {
        throw new Error('temp cleanup failed');
      }
      return (await vi.importActual<typeof import('node:fs/promises')>('node:fs/promises')).unlink(
        target as string,
        ...(rest as [any])
      );
    });

    await expect(cache.writeCache(cachePath, 'temp-warning')).rejects.toThrow('write failed');

    expect(warnSpy).toHaveBeenCalled();
  });

  it('throws when lock timeout is hit', async () => {
    const originalEnv = process.env.CACHE_LOCK_TIMEOUT_MS;
    process.env.CACHE_LOCK_TIMEOUT_MS = '50';

    const lockPath = `${cachePath}.lock`;
    await fs.writeFile(lockPath, 'lock');

    await expect(cache.writeCache(cachePath, 'content')).rejects.toThrow(
      /Timed out waiting for cache lock/
    );

    if (originalEnv === undefined) {
      delete process.env.CACHE_LOCK_TIMEOUT_MS;
    } else {
      process.env.CACHE_LOCK_TIMEOUT_MS = originalEnv;
    }
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
    expect(cache.getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for invalid values', () => {
    process.env.CACHE_TTL_MS = 'not-a-number';
    expect(cache.getCacheTtlMs()).toBe(86400000);
  });

  it('returns default for negative values', () => {
    process.env.CACHE_TTL_MS = '-1000';
    expect(cache.getCacheTtlMs()).toBe(86400000);
  });

  it('returns parsed value within bounds', () => {
    process.env.CACHE_TTL_MS = '3600000';
    expect(cache.getCacheTtlMs()).toBe(3600000);
  });

  it('caps at 1 year max', () => {
    process.env.CACHE_TTL_MS = '999999999999999';
    expect(cache.getCacheTtlMs()).toBe(1000 * 60 * 60 * 24 * 365);
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
    const result = await cache.readCacheIfFresh(cachePath);
    expect(result).toBeNull();
  });

  it('returns fresh cache when within TTL', async () => {
    await cache.writeCache(cachePath, 'fresh content');
    const result = await cache.readCacheIfFresh(cachePath);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('fresh content');
  });

  it('returns null for stale cache', async () => {
    await cache.writeCache(cachePath, 'stale content');
    process.env.CACHE_TTL_MS = '0';
    const result = await cache.readCacheIfFresh(cachePath);
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
    const indexCachePath = cache.getDefaultIndexCachePath();
    expect(indexCachePath).toMatch(/claude-code-docs[/\\]llms-full\.index\.json$/);
  });

  it('writeIndexCache and readIndexCache round-trip', async () => {
    const data = { version: 1, chunks: [], test: 'value' };
    await cache.writeIndexCache(indexPath, data);
    const result = await cache.readIndexCache(indexPath);
    expect(result).toEqual(data);
  });

  it('readIndexCache returns null for non-existent file', async () => {
    const result = await cache.readIndexCache(indexPath);
    expect(result).toBeNull();
  });

  it('readIndexCache returns null for invalid JSON', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    await fs.writeFile(indexPath, 'not valid json {{{');
    const result = await cache.readIndexCache(indexPath);
    expect(result).toBeNull();
    expect(warnSpy).toHaveBeenCalled();
  });

  it('clearIndexCache removes default index cache file', async () => {
    const originalXdg = process.env.XDG_CACHE_HOME;
    const tempCacheDir = await fs.mkdtemp(path.join(os.tmpdir(), 'index-cache-home-'));
    process.env.XDG_CACHE_HOME = tempCacheDir;

    const defaultIndexPath = cache.getDefaultIndexCachePath();
    await cache.writeIndexCache(defaultIndexPath, { version: 1, chunks: [] });

    await cache.clearIndexCache();

    await expect(fs.stat(defaultIndexPath)).rejects.toThrow();

    if (originalXdg === undefined) {
      delete process.env.XDG_CACHE_HOME;
    } else {
      process.env.XDG_CACHE_HOME = originalXdg;
    }
  });
});
