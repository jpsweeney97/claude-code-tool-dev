// tests/corpus-validation.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import { readdirSync, readFileSync, statSync, existsSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_PATH =
  process.env.DOCS_PATH ?? resolve(__dirname, '../../../../docs/extension-reference');

const MAX_CHUNK_LINES = 150;

function* walkMarkdownFiles(dir: string): Generator<string> {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      yield* walkMarkdownFiles(fullPath);
    } else if (entry.endsWith('.md')) {
      yield fullPath;
    }
  }
}

describe('corpus validation', () => {
  it('all chunks within size bounds', () => {
    const stats = {
      totalFiles: 0,
      totalChunks: 0,
      maxChunkLines: 0,
      maxChunkChars: 0,
      oversizedChunks: [] as string[],
    };

    for (const filePath of walkMarkdownFiles(DOCS_PATH)) {
      const content = readFileSync(filePath, 'utf-8');
      const chunks = chunkFile({ path: filePath, content });

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

    // Assertion: no oversized chunks
    expect(stats.oversizedChunks).toEqual([]);
    expect(stats.totalFiles).toBeGreaterThan(0);
  });

  it('all chunks have valid IDs', () => {
    const ids = new Set<string>();
    const duplicates: string[] = [];

    for (const filePath of walkMarkdownFiles(DOCS_PATH)) {
      const content = readFileSync(filePath, 'utf-8');
      const chunks = chunkFile({ path: filePath, content });

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
