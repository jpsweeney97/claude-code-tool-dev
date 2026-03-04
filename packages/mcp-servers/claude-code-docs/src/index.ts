// src/index.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { loadFromOfficial } from './loader.js';
import { chunkFile } from './chunker.js';
import { buildBM25Index, search, type BM25Index } from './bm25.js';
import { getParseWarnings, clearParseWarnings } from './frontmatter.js';
import { KNOWN_CATEGORIES, CATEGORY_ALIASES } from './categories.js';
import {
  serializeIndex,
  deserializeIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  type SerializedIndex,
  parseSerializedIndex,
} from './index-cache.js';
import { readIndexCache, writeIndexCache, getDefaultIndexCachePath, clearIndexCache } from './cache.js';
import { formatSearchError } from './error-messages.js';

// === State Management ===
let index: BM25Index | null = null;
let loadError: string | null = null;
let lastLoadAttempt = 0;
let loadingPromise: Promise<BM25Index | null> | null = null;

// === Configuration ===
const RETRY_INTERVAL_MS = parseInt(process.env.RETRY_INTERVAL_MS ?? '60000', 10);
const EFFECTIVE_RETRY_INTERVAL =
  RETRY_INTERVAL_MS >= 1000 && RETRY_INTERVAL_MS <= 600000 ? RETRY_INTERVAL_MS : 60000;

async function ensureIndex(forceRefresh = false): Promise<BM25Index | null> {
  if (index && !forceRefresh) return index;

  if (loadingPromise) return loadingPromise;

  const now = Date.now();
  if (loadError && now - lastLoadAttempt < EFFECTIVE_RETRY_INTERVAL && !forceRefresh) {
    return null;
  }

  loadingPromise = doLoadIndex(forceRefresh);

  try {
    return await loadingPromise;
  } finally {
    loadingPromise = null;
  }
}

async function doLoadIndex(forceRefresh = false): Promise<BM25Index | null> {
  const isRetry = loadError !== null;

  lastLoadAttempt = Date.now();
  loadError = null;
  clearParseWarnings();

  if (isRetry) {
    console.error('Retrying documentation load...');
  }

  const docsUrl = process.env.DOCS_URL ?? 'https://code.claude.com/docs/llms-full.txt';

  try {
    const { files, contentHash } = await loadFromOfficial(docsUrl, undefined, forceRefresh);
    if (files.length === 0) {
      loadError = 'No extension documentation found after filtering';
      console.error(`ERROR: ${loadError}`);
      return null;
    }

    // Try to load cached index
    const indexCachePath = getDefaultIndexCachePath();
    const cached = parseSerializedIndex(await readIndexCache(indexCachePath));

    if (
      cached &&
      cached.version === INDEX_FORMAT_VERSION &&
      cached.contentHash === contentHash &&
      cached.metadata?.tokenizerVersion === TOKENIZER_VERSION &&
      cached.metadata?.chunkerVersion === CHUNKER_VERSION
    ) {
      index = deserializeIndex(cached);
      console.error(`Loaded cached index (${index.chunks.length} chunks)`);
      return index;
    }

    // Build fresh index
    const chunks = files.flatMap((f) => chunkFile(f));

    const warnings = getParseWarnings();
    if (warnings.length > 0) {
      console.error(`\nWARNING: ${warnings.length} file(s) with parse issues:`);
      for (const w of warnings) {
        console.error(`  - ${w.file}: ${w.issue}`);
      }
      console.error('');
    }

    index = buildBM25Index(chunks);
    console.error(`Built fresh index (${chunks.length} chunks from ${files.length} sections)`);

    // Persist index
    try {
      const serialized = serializeIndex(index, contentHash);
      await writeIndexCache(indexCachePath, serialized);
      console.error('Index cached for future use');
    } catch (err) {
      console.error(`WARN: Failed to write index cache: ${err instanceof Error ? err.message : 'unknown'}`);
    }

    return index;
  } catch (err) {
    loadError = `Failed to load docs: ${err instanceof Error ? err.message : 'unknown'}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }
}

// === Zod Schemas ===
const CATEGORY_VALUES = [...KNOWN_CATEGORIES] as const;

const SearchInputSchema = z.object({
  query: z
    .string()
    .max(500, 'Query too long: maximum 500 characters')
    .transform((s) => s.trim())
    .pipe(z.string().min(1, 'Query cannot be empty'))
    .describe(
      'Search query — be specific (e.g., "PreToolUse JSON output", "skill frontmatter properties")',
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .describe('Maximum results to return (default: 5, max: 20)'),
  category: z
    .enum([...CATEGORY_VALUES, ...Object.keys(CATEGORY_ALIASES)] as [string, ...string[]])
    .transform((val) => CATEGORY_ALIASES[val] ?? val)
    .optional()
    .describe('Filter to a specific category (e.g., "hooks", "plugins", "security")'),
});

const SearchOutputSchema = z.object({
  results: z.array(
    z.object({
      chunk_id: z.string(),
      content: z.string(),
      snippet: z.string(),
      category: z.string(),
      source_file: z.string(),
    }),
  ),
  error: z.string().optional().describe('Error message if search failed'),
});

async function main() {
  const server = new McpServer({
    name: 'claude-code-docs',
    version: '1.0.0',
  });

  server.registerTool(
    'search_docs',
    {
      title: 'Search Claude Code Docs',
      description:
        'Search Claude Code documentation (extensions, setup, security, providers, IDE integration, CI/CD, and more). Use specific queries.',
      inputSchema: SearchInputSchema,
      outputSchema: SearchOutputSchema,
    },
    async ({ query, limit = 5, category }: z.infer<typeof SearchInputSchema>) => {
      const idx = await ensureIndex();
      if (!idx) {
        const error = loadError ?? 'Index not available';
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Search unavailable: ${error}` }],
          structuredContent: { results: [], error },
        };
      }

      try {
        const results = search(idx, query, limit, category);
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }],
          structuredContent: { results },
        };
      } catch (err) {
        console.error('Search error:', err);
        const error = formatSearchError(err);
        return {
          isError: true,
          content: [{ type: 'text' as const, text: error }],
          structuredContent: { results: [], error },
        };
      }
    },
  );

  server.registerTool(
    'reload_docs',
    {
      title: 'Reload Claude Code Docs',
      description:
        'Force reload of Claude Code documentation. Use after editing docs to refresh search index.',
      inputSchema: z.object({}),
    },
    async () => {
      if (loadingPromise) {
        console.error('Waiting for in-progress load to complete before reload...');
        await loadingPromise;
      }

      // Keep old index alive during reload — concurrent searches continue to work.
      // doLoadIndex() overwrites `index` on success (lines 85, 102) and preserves
      // it on failure (returns null without touching `index`).
      clearParseWarnings();

      console.error('Forcing documentation reload...');

      await clearIndexCache();

      const idx = await ensureIndex(true);
      if (!idx) {
        const hasStaleIndex = index !== null;
        return {
          isError: true,
          content: [
            {
              type: 'text' as const,
              text: hasStaleIndex
                ? `Reload failed (serving previous index): ${loadError}`
                : `Reload failed: ${loadError}`,
            },
          ],
        };
      }

      const warnings = getParseWarnings();
      return {
        content: [
          {
            type: 'text' as const,
            text: `Reloaded ${idx.chunks.length} chunks from documentation.${
              warnings.length > 0 ? ` Warning: ${warnings.length} file(s) had parse issues.` : ''
            }`,
          },
        ],
      };
    },
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Eagerly load the index to avoid first-search latency.
  // If a search arrives while loading, ensureIndex() will wait for this same promise.
  ensureIndex().then((idx) => {
    if (idx) {
      console.error(`Index ready (${idx.chunks.length} chunks)`);
    }
    // If idx is null, loadError was already logged by doLoadIndex
  });

  const shutdown = async (signal: string) => {
    console.error(`Received ${signal}, shutting down...`);

    let exitCode = 0;
    const timeoutId = setTimeout(() => {
      console.error('Shutdown timeout');
      process.exit(1);
    }, 5000);

    try {
      await server.close();
      console.error('Graceful shutdown complete');
    } catch (err) {
      console.error('Shutdown error:', err instanceof Error ? err.message : 'unknown');
      exitCode = 1;
    } finally {
      clearTimeout(timeoutId);
    }

    process.exit(exitCode);
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
