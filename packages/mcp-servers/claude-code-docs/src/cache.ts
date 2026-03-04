import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

export interface CacheResult {
  content: string;
  age: number;
}

const DEFAULT_TTL_MS = 86400000; // 24 hours
const MAX_TTL_MS = 1000 * 60 * 60 * 24 * 365; // 1 year

export function getCacheTtlMs(): number {
  const raw = process.env.CACHE_TTL_MS?.trim();
  if (!raw) return DEFAULT_TTL_MS;
  const val = Number(raw);
  if (!Number.isFinite(val) || val < 0) return DEFAULT_TTL_MS;
  return Math.min(val, MAX_TTL_MS);
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
  return path.join(baseDir, 'claude-code-docs', filename);
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function acquireLock(lockPath: string, timeoutMs = 2000, pollMs = 50): Promise<fs.FileHandle> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const handle = await fs.open(lockPath, 'wx');
      // Write PID to lock file so stale locks can be detected
      await handle.write(process.pid.toString());
      return handle;
    } catch (err: unknown) {
      const code = (err as NodeJS.ErrnoException).code;
      if (code !== 'EEXIST') {
        throw err;
      }
      await sleep(pollMs);
    }
  }

  // Timeout reached — check if the lock holder is still alive
  try {
    const pidStr = await fs.readFile(lockPath, 'utf8');
    const pid = parseInt(pidStr, 10);
    if (!Number.isNaN(pid)) {
      try {
        process.kill(pid, 0); // Throws ESRCH if process is dead
      } catch (killErr: unknown) {
        if ((killErr as NodeJS.ErrnoException).code === 'ESRCH') {
          // Lock holder is dead — steal the lock
          try {
            await fs.unlink(lockPath);
          } catch {
            // Another process may have already cleaned it up
          }
          // Retry once
          const handle = await fs.open(lockPath, 'wx');
          await handle.write(process.pid.toString());
          return handle;
        }
        // EPERM means process exists but we can't signal it — lock is valid
      }
    }
  } catch {
    // Could not read or parse lock file — fall through to error
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
      console.warn(`WARN: Failed to remove cache lock ${lockPath}`);
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

export async function readCacheIfFresh(cachePath: string): Promise<CacheResult | null> {
  const cached = await readCache(cachePath);
  if (!cached) return null;
  const ttl = getCacheTtlMs();
  if (cached.age >= ttl) {
    return null;
  }
  return cached;
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
      console.warn(`WARN: Failed to remove temp cache file ${tempPath}`);
    }
    throw err;
  } finally {
    await releaseLock(lockPath, lockHandle);
  }
}

export function getDefaultIndexCachePath(filename = 'llms-full.index.json'): string {
  const base = getDefaultCachePath('llms-full.txt');
  return path.join(path.dirname(base), filename);
}

const DEFAULT_MAX_INDEX_CACHE_BYTES = 50 * 1024 * 1024; // 50MB

export async function writeIndexCache(cachePath: string, data: unknown): Promise<void> {
  const content = JSON.stringify(data);
  const maxBytes = parseInt(process.env.MAX_INDEX_CACHE_BYTES ?? '', 10) || DEFAULT_MAX_INDEX_CACHE_BYTES;
  if (content.length > maxBytes) {
    throw new Error(
      `writeIndexCache failed: serialized index is ${content.length} bytes, exceeds ${maxBytes} byte limit`,
    );
  }
  await writeCache(cachePath, content);
}

export async function readIndexCache(cachePath: string): Promise<unknown | null> {
  const cached = await readCache(cachePath);
  if (!cached) return null;
  try {
    return JSON.parse(cached.content);
  } catch {
    console.warn(`WARN: Failed to parse index cache at ${cachePath}`);
    return null;
  }
}

export async function clearIndexCache(cachePath?: string): Promise<void> {
  const target = cachePath ?? getDefaultIndexCachePath();
  try {
    await fs.unlink(target);
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).code !== 'ENOENT') {
      console.warn(`WARN: Failed to remove index cache ${target}`);
    }
  }
}
