// tests/golden-queries.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import * as path from 'path';
import { loadMarkdownFiles } from '../src/loader.js';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';
import { clearParseWarnings } from '../src/frontmatter.js';

// These tests validate search quality against the real corpus
// Skip if extension-reference docs don't exist (CI without corpus)
const DOCS_PATH = path.resolve(__dirname, '../../../../docs/extension-reference');

describe('golden queries', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let skipTests = false;

  beforeAll(async () => {
    clearParseWarnings();
    try {
      const files = await loadMarkdownFiles(DOCS_PATH);
      if (files.length === 0) {
        skipTests = true;
        return;
      }
      const chunks = files.flatMap((f) => chunkFile(f));
      index = buildBM25Index(chunks);
    } catch {
      skipTests = true;
    }
  });

  const goldenQueries = [
    { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
    { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
    { query: 'skill frontmatter', expectedTopCategory: 'skills' },
    { query: 'MCP server registration', expectedTopCategory: 'mcp' },
    { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  ];

  for (const { query, expectedTopCategory } of goldenQueries) {
    it(`"${query}" returns ${expectedTopCategory} category in top result`, (context) => {
      if (skipTests) {
        context.skip();
        return;
      }

      const results = search(index, query, 5);
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].category).toBe(expectedTopCategory);
    });
  }
});
