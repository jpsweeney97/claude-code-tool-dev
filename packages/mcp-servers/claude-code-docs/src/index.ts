// src/index.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

import { loadFromOfficial } from './loader.js';
import { chunkFile } from './chunker.js';
import { buildBM25Index, search } from './bm25.js';
import {
  serializeIndex,
  deserializeIndex,
  parseSerializedIndex,
} from './index-cache.js';
import { readIndexCache, writeIndexCache, getDefaultIndexCachePath, clearIndexCache } from './cache.js';
import { formatSearchError } from './error-messages.js';
import { ServerState } from './lifecycle.js';
import { SearchInputSchema, SearchOutputSchema } from './schemas.js';

const serverState = new ServerState({
  loadFn: loadFromOfficial,
  chunkFn: chunkFile,
  buildIndexFn: buildBM25Index,
  readCacheFn: readIndexCache,
  writeCacheFn: writeIndexCache,
  clearCacheFn: clearIndexCache,
  indexCachePathFn: getDefaultIndexCachePath,
  serializeIndexFn: serializeIndex,
  deserializeIndexFn: deserializeIndex,
  parseSerializedIndexFn: parseSerializedIndex,
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
      const idx = await serverState.ensureIndex();
      if (!idx) {
        const error = serverState.getLoadError() ?? 'Index not available';
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
      const inProgress = serverState.getLoadingPromise();
      if (inProgress) {
        console.error('Waiting for in-progress load to complete before reload...');
        await inProgress;
      }

      // Keep old index alive during reload — concurrent searches continue to work.
      // doLoadIndex() overwrites index on success and preserves it on failure.
      console.error('Forcing documentation reload...');

      await clearIndexCache();

      const idx = await serverState.ensureIndex(true);
      if (!idx) {
        const hasStaleIndex = serverState.getIndex() !== null;
        return {
          isError: true,
          content: [
            {
              type: 'text' as const,
              text: hasStaleIndex
                ? `Reload failed (serving previous index): ${serverState.getLoadError()}`
                : `Reload failed: ${serverState.getLoadError()}`,
            },
          ],
        };
      }

      const warnings = serverState.getWarnings();
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
  serverState.ensureIndex().then((idx) => {
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
