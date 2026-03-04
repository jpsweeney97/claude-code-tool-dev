// tests/corpus-validation.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import { parseSections } from '../src/parser.js';
import { readCache, getDefaultCachePath } from '../src/cache.js';
import { existsSync } from 'fs';

const cachePath = getDefaultCachePath();
const cacheExists = existsSync(cachePath);

if (!cacheExists) {
  console.warn(
    `SKIPPING corpus validation: content cache not found at ${cachePath}\n` +
      `Run the server once to populate the cache, then re-run tests.`
  );
}

const MAX_CHUNK_LINES = 150;

async function loadCorpusFiles() {
  const cached = await readCache(cachePath);
  if (!cached) throw new Error(`Cache not readable at ${cachePath}`);

  const sections = parseSections(cached.content);
  return sections
    .filter((s) => s.content.trim().length > 0)
    .map((s) => ({
      path: s.sourceUrl || s.title || 'unknown',
      content: s.content,
    }));
}

describe.skipIf(!cacheExists)('corpus validation', () => {
  it('all chunks within size bounds', async () => {
    const files = await loadCorpusFiles();
    const stats = {
      totalFiles: 0,
      totalChunks: 0,
      maxChunkLines: 0,
      maxChunkChars: 0,
      oversizedChunks: [] as string[],
    };

    for (const file of files) {
      const { chunks } = chunkFile(file);

      stats.totalFiles++;
      stats.totalChunks += chunks.length;

      for (const chunk of chunks) {
        const lines = chunk.content.split('\n').length;
        const chars = chunk.content.length;
        stats.maxChunkLines = Math.max(stats.maxChunkLines, lines);
        stats.maxChunkChars = Math.max(stats.maxChunkChars, chars);

        if (lines > MAX_CHUNK_LINES || chars > MAX_CHUNK_CHARS) {
          stats.oversizedChunks.push(`${chunk.id}: ${lines} lines, ${chars} chars`);
        }
      }
    }

    console.log('Corpus stats:', {
      ...stats,
      oversizedChunks: stats.oversizedChunks.length,
    });

    expect(stats.oversizedChunks).toEqual([]);
    expect(stats.totalFiles).toBeGreaterThan(0);
  });

  it('all chunks have valid IDs', async () => {
    const files = await loadCorpusFiles();
    const ids = new Set<string>();
    const duplicates: string[] = [];

    for (const file of files) {
      const { chunks } = chunkFile(file);

      for (const chunk of chunks) {
        if (ids.has(chunk.id)) {
          duplicates.push(chunk.id);
        }
        ids.add(chunk.id);
      }
    }

    expect(duplicates).toEqual([]);
  });
});
