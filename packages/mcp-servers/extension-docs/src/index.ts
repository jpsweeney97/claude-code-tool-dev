// src/index.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { loadFromOfficial } from './loader.js';
import { chunkFile } from './chunker.js';
import { buildBM25Index, search, type BM25Index } from './bm25.js';
import { getParseWarnings, clearParseWarnings } from './frontmatter.js';
import {
  serializeIndex,
  deserializeIndex,
  INDEX_FORMAT_VERSION,
  TOKENIZER_VERSION,
  CHUNKER_VERSION,
  type SerializedIndex,
} from './index-cache.js';
import { readIndexCache, writeIndexCache, getDefaultIndexCachePath } from './cache.js';

// === State Management ===
let index: BM25Index | null = null;
let loadError: string | null = null;
let lastLoadAttempt = 0;
let loadingPromise: Promise<BM25Index | null> | null = null;

// === Configuration ===
const RETRY_INTERVAL_MS = parseInt(process.env.RETRY_INTERVAL_MS ?? '60000', 10);
const EFFECTIVE_RETRY_INTERVAL =
  RETRY_INTERVAL_MS >= 1000 && RETRY_INTERVAL_MS <= 600000 ? RETRY_INTERVAL_MS : 60000;

async function ensureIndex(): Promise<BM25Index | null> {
  if (index) return index;

  if (loadingPromise) return loadingPromise;

  const now = Date.now();
  if (loadError && now - lastLoadAttempt < EFFECTIVE_RETRY_INTERVAL) {
    return null;
  }

  loadingPromise = doLoadIndex();

  try {
    return await loadingPromise;
  } finally {
    loadingPromise = null;
  }
}

async function doLoadIndex(): Promise<BM25Index | null> {
  const isRetry = loadError !== null;

  lastLoadAttempt = Date.now();
  loadError = null;
  clearParseWarnings();

  if (isRetry) {
    console.error('Retrying documentation load...');
  }

  const docsUrl = process.env.DOCS_URL ?? 'https://code.claude.com/docs/llms-full.txt';

  try {
    const { files, contentHash } = await loadFromOfficial(docsUrl);
    if (files.length === 0) {
      loadError = 'No extension documentation found after filtering';
      console.error(`ERROR: ${loadError}`);
      return null;
    }

    // Try to load cached index
    const indexCachePath = getDefaultIndexCachePath();
    const cached = await readIndexCache(indexCachePath) as SerializedIndex | null;

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
const CATEGORY_VALUES = [
  'hooks',
  'skills',
  'commands',
  'slash-commands',
  'agents',
  'subagents',
  'sub-agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'claude-md',
  'memory',
  'configuration',
] as const;

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
    .enum(CATEGORY_VALUES)
    .optional()
    .describe('Filter to a specific category (e.g., "hooks", "plugins")'),
});

const SearchOutputSchema = z.object({
  results: z.array(
    z.object({
      chunk_id: z.string(),
      content: z.string(),
      category: z.string(),
      source_file: z.string(),
    }),
  ),
});

async function main() {
  const server = new McpServer({
    name: 'extension-docs',
    version: '1.0.0',
  });

  server.registerTool(
    'search_extension_docs',
    {
      title: 'Search Extension Docs',
      description:
        'Search Claude Code extension documentation (hooks, skills, commands, agents, plugins, MCP). Use specific queries.',
      inputSchema: SearchInputSchema,
      outputSchema: SearchOutputSchema,
    },
    async ({ query, limit = 5, category }: z.infer<typeof SearchInputSchema>) => {
      const idx = await ensureIndex();
      if (!idx) {
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Search unavailable: ${loadError}` }],
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
        return {
          isError: true,
          content: [
            { type: 'text' as const, text: 'Search failed. Please try a different query.' },
          ],
        };
      }
    },
  );

  server.registerTool(
    'reload_extension_docs',
    {
      title: 'Reload Extension Docs',
      description:
        'Force reload of extension documentation. Use after editing docs to refresh search index.',
      inputSchema: z.object({}),
    },
    async () => {
      if (loadingPromise) {
        console.error('Waiting for in-progress load to complete before reload...');
        await loadingPromise;
      }

      index = null;
      loadError = null;
      lastLoadAttempt = 0;
      clearParseWarnings();

      console.error('Forcing documentation reload...');

      const idx = await ensureIndex();
      if (!idx) {
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Reload failed: ${loadError}` }],
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

  const shutdown = async (signal: string) => {
    console.error(`Received ${signal}, shutting down...`);

    let timeoutId: NodeJS.Timeout;
    let exitCode = 0;

    try {
      await Promise.race([
        server.close(),
        new Promise((_, reject) => {
          timeoutId = setTimeout(() => reject(new Error('Shutdown timeout')), 5000);
        }),
      ]);
      clearTimeout(timeoutId!);
      console.error('Graceful shutdown complete');
    } catch (err) {
      clearTimeout(timeoutId!);
      console.error('Shutdown error:', err instanceof Error ? err.message : 'unknown');
      exitCode = 1;
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
