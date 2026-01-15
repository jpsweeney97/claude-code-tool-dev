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
