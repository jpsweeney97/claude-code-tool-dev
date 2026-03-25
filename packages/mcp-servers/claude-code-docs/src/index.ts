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
import { buildMetadataResponse, DumpIndexMetadataOutputSchema } from './dump-index-metadata.js';
import { loadConfig } from './config.js';
import { evaluateCanaries } from './canary.js';
import { buildRuntimeStatus, projectSearchMeta, RuntimeStatusSchema } from './status.js';

async function main() {
  const config = loadConfig();
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
    evaluateCanariesFn: evaluateCanaries,
    docsUrl: config.docsUrl,
    retryIntervalMs: config.retryIntervalMs,
    trustMode: config.trustMode,
  });

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
        const status = buildRuntimeStatus({
          trustMode: serverState.getTrustMode(),
          docsUrl: serverState.getDocsUrl(),
          corpus: serverState.getCorpusProvenance(),
          index: idx ? { createdAt: serverState.getIndexCreatedAt()! } : null,
          lastLoadAttemptAt: serverState.getLastLoadAttempt() || null,
          lastLoadError: serverState.getLoadError(),
          warningCodes: serverState.getEvaluation()?.warnings.map(w => w.code) ?? [],
          isLoading: serverState.isLoading(),
        });
        const meta = projectSearchMeta(status);
        const structuredContent = { results, meta };
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(structuredContent) }],
          structuredContent,
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
      const idx = await serverState.clearAndReload();
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

  server.registerTool(
    'get_status',
    {
      title: 'Get Server Status',
      description:
        'Get current status of the claude-code-docs server: trust mode, documentation source, index age, and any active warnings.',
      inputSchema: z.object({}),
      outputSchema: RuntimeStatusSchema,
    },
    async () => {
      const corpusProvenance = serverState.getCorpusProvenance();
      const status = buildRuntimeStatus({
        trustMode: serverState.getTrustMode(),
        docsUrl: serverState.getDocsUrl(),
        corpus: corpusProvenance,
        index: serverState.getIndex() !== null ? { createdAt: serverState.getIndexCreatedAt()! } : null,
        lastLoadAttemptAt: serverState.getLastLoadAttempt() || null,
        lastLoadError: serverState.getLoadError(),
        warningCodes: serverState.getEvaluation()?.warnings.map(w => w.code) ?? [],
        isLoading: serverState.isLoading(),
      });
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(status) }],
        structuredContent: status,
      };
    },
  );

  server.registerTool(
    'dump_index_metadata',
    {
      title: 'Dump Index Metadata',
      description:
        'Dump full BM25 index metadata: categories, chunk IDs, headings, code literals, config keys, and distinctive terms. No parameters.',
      inputSchema: z.object({}),
      outputSchema: DumpIndexMetadataOutputSchema,
    },
    async () => {
      const idx = await serverState.ensureIndex();
      if (!idx) {
        const error = serverState.getLoadError() ?? 'Index not available';
        return {
          isError: true,
          content: [{ type: 'text' as const, text: `Metadata unavailable: ${error}` }],
          structuredContent: {
            index_version: '',
            index_created_at: '',
            built_at: '',
            docs_epoch: null,
            categories: [],
          },
        };
      }

      const metadata = buildMetadataResponse(idx, serverState.getContentHash(), serverState.getIndexCreatedAt());
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(metadata, null, 2) }],
        structuredContent: metadata,
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
  }).catch((err) => {
    console.error(`Startup index load failed: ${err instanceof Error ? err.message : 'unknown'}`);
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
