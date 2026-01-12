// src/index.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import * as fs from 'fs';
import { z } from 'zod';

import { loadMarkdownFiles } from './loader.js';
import { chunkFile } from './chunker.js';
import { buildBM25Index, search, type BM25Index } from './bm25.js';
import { getParseWarnings, clearParseWarnings } from './frontmatter.js';

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

  const docsPath = process.env.DOCS_PATH;
  if (!docsPath) {
    loadError = 'DOCS_PATH environment variable is required';
    console.error(`ERROR: ${loadError}`);
    return null;
  }

  if (!fs.existsSync(docsPath)) {
    loadError = `DOCS_PATH not found: ${docsPath}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }

  try {
    const files = await loadMarkdownFiles(docsPath);
    if (files.length === 0) {
      loadError = `No markdown files found in ${docsPath}`;
      console.error(`ERROR: ${loadError}`);
      return null;
    }

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
    console.error(`Loaded ${chunks.length} chunks from ${files.length} files`);
    return index;
  } catch (err) {
    loadError = `Unexpected error: ${err instanceof Error ? err.message : 'unknown'}`;
    console.error(`ERROR: ${loadError}`);
    return null;
  }
}

// === Zod Schemas ===
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
    async ({ query, limit = 5 }: z.infer<typeof SearchInputSchema>) => {
      const idx = await ensureIndex();
      if (!idx) {
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Search unavailable: ${loadError}` }],
        };
      }

      try {
        const results = search(idx, query, limit);
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
