/**
 * dump_index_metadata tool — exposes BM25 index structure as metadata.
 */

import { z } from 'zod';
import type { BM25Index } from './bm25.js';
import type { Chunk } from './types.js';
import { CATEGORY_ALIASES } from './categories.js';
import { INDEX_FORMAT_VERSION } from './index-cache.js';

// ---------------------------------------------------------------------------
// Zod output schema — mirrors the integration.md response spec
// ---------------------------------------------------------------------------

const ChunkMetadataSchema = z.object({
  chunk_id: z.string(),
  source_file: z.string(),
  headings: z.array(z.string()),
  code_literals: z.array(z.string()),
  config_keys: z.array(z.string()),
  distinctive_terms: z.array(z.string()),
});

const CategoryMetadataSchema = z.object({
  name: z.string(),
  aliases: z.array(z.string()),
  chunk_count: z.number().int(),
  chunks: z.array(ChunkMetadataSchema),
});

export const DumpIndexMetadataOutputSchema = z.object({
  index_version: z.string(),
  index_created_at: z.string(),
  built_at: z.string().describe('DEPRECATED: Response generation time. Use index_created_at for actual index build time.'),
  docs_epoch: z.string().nullable(),
  categories: z.array(CategoryMetadataSchema),
});

export type DumpIndexMetadataOutput = z.infer<typeof DumpIndexMetadataOutputSchema>;

// ---------------------------------------------------------------------------
// Extraction helpers
// ---------------------------------------------------------------------------

/** Match backtick-delimited identifiers: word chars, dots, hyphens. */
const BACKTICK_RE = /`([a-zA-Z_][\w.\-]*)`/g;

/** Match camelCase or PascalCase: lowercase followed by uppercase, or starts uppercase with later lowercase. */
const CAMEL_CASE_RE = /^[a-z]+[A-Z]|^[A-Z][a-z]/;

/** Match markdown heading lines: # Heading */
const HEADING_LINE_RE = /^#{1,6}\s+(.+)$/gm;

/**
 * Extract backtick-delimited identifiers from chunk content.
 * Deduplicates per invocation.
 */
export function extractCodeLiterals(content: string): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const match of content.matchAll(BACKTICK_RE)) {
    const literal = match[1];
    if (!seen.has(literal)) {
      seen.add(literal);
      result.push(literal);
    }
  }

  return result;
}

/**
 * Extract config-like keys from a list of code literals.
 * Qualifies if: contains a dot (dotted path) OR is camelCase/PascalCase.
 */
export function extractConfigKeys(literals: string[]): string[] {
  return literals.filter((lit) => lit.includes('.') || CAMEL_CASE_RE.test(lit));
}

/**
 * Extract headings from a chunk.
 * Priority: merged_headings > heading alone > markdown headings from content.
 * Deduplicates while preserving order.
 */
export function extractHeadings(chunk: Chunk): string[] {
  let raw: string[];

  if (chunk.merged_headings && chunk.merged_headings.length > 0) {
    raw = chunk.merged_headings;
  } else if (chunk.heading) {
    raw = [chunk.heading];
  } else {
    // Fall back: extract markdown headings from content
    raw = [];
    for (const match of chunk.content.matchAll(HEADING_LINE_RE)) {
      raw.push(match[1]);
    }
  }

  // Deduplicate while preserving order
  const seen = new Set<string>();
  const result: string[] = [];
  for (const h of raw) {
    if (!seen.has(h)) {
      seen.add(h);
      result.push(h);
    }
  }
  return result;
}

/**
 * Compute distinctive terms for a chunk: code literals that appear
 * in 3 or fewer chunks across the entire index.
 */
export function computeDistinctiveTerms(chunk: Chunk, index: BM25Index): string[] {
  const literals = extractCodeLiterals(chunk.content);
  if (literals.length === 0) return [];

  // Build a set of chunks each literal appears in (by scanning all chunks)
  const literalChunkCount = new Map<string, number>();
  for (const lit of literals) {
    literalChunkCount.set(lit, 0);
  }

  for (const other of index.chunks) {
    const otherLiterals = new Set(extractCodeLiterals(other.content));
    for (const lit of literals) {
      if (otherLiterals.has(lit)) {
        literalChunkCount.set(lit, (literalChunkCount.get(lit) ?? 0) + 1);
      }
    }
  }

  return literals.filter((lit) => (literalChunkCount.get(lit) ?? 0) <= 3);
}

// ---------------------------------------------------------------------------
// Reverse alias map: canonical category → [alias1, alias2, ...]
// ---------------------------------------------------------------------------

function buildReverseAliases(): Map<string, string[]> {
  const reverse = new Map<string, string[]>();
  for (const [alias, canonical] of Object.entries(CATEGORY_ALIASES)) {
    let arr = reverse.get(canonical);
    if (!arr) {
      arr = [];
      reverse.set(canonical, arr);
    }
    arr.push(alias);
  }
  return reverse;
}

const REVERSE_ALIASES = buildReverseAliases();

// ---------------------------------------------------------------------------
// Main builder
// ---------------------------------------------------------------------------

/**
 * Build the metadata response for the dump_index_metadata tool.
 *
 * @param index - The current BM25 index
 * @param contentHash - Content hash from the loader (docs_epoch); null when index is empty
 * @param indexCreatedAt - Unix timestamp (ms) when the index was built; null falls back to now
 */
export function buildMetadataResponse(
  index: BM25Index,
  contentHash: string | null,
  indexCreatedAt: number | null = null,
): DumpIndexMetadataOutput {
  // Group chunks by category
  const categoryMap = new Map<string, Chunk[]>();
  for (const chunk of index.chunks) {
    let arr = categoryMap.get(chunk.category);
    if (!arr) {
      arr = [];
      categoryMap.set(chunk.category, arr);
    }
    arr.push(chunk);
  }

  // Build category metadata
  const categories = Array.from(categoryMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, chunks]) => {
      const aliases = REVERSE_ALIASES.get(name) ?? [];

      return {
        name,
        aliases,
        chunk_count: chunks.length,
        chunks: chunks.map((chunk) => {
          const codeLiterals = extractCodeLiterals(chunk.content);
          return {
            chunk_id: chunk.id,
            source_file: chunk.source_file,
            headings: extractHeadings(chunk),
            code_literals: codeLiterals,
            config_keys: extractConfigKeys(codeLiterals),
            distinctive_terms: computeDistinctiveTerms(chunk, index),
          };
        }),
      };
    });

  return {
    index_version: String(INDEX_FORMAT_VERSION),
    index_created_at: new Date(indexCreatedAt ?? Date.now()).toISOString(),
    built_at: new Date().toISOString(),
    docs_epoch: contentHash,
    categories,
  };
}
