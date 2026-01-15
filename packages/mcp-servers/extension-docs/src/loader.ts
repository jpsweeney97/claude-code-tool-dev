// src/loader.ts
import { glob } from 'glob';
import { readFile } from 'fs/promises';
import * as path from 'path';
import type { MarkdownFile, ParsedSection } from './types.js';
import { fetchOfficialDocs, FetchHttpError, FetchNetworkError, FetchTimeoutError } from './fetcher.js';
import { parseSections } from './parser.js';
import { filterToExtensions } from './filter.js';
import { readCache, writeCache, getDefaultCachePath } from './cache.js';
import { extractContentPath } from './url-helpers.js';
import { deriveCategory } from './frontmatter.js';

export async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = [];
  const pattern = path.join(docsPath, '**/*.md').replace(/\\/g, '/');

  let filePaths: string[];
  try {
    filePaths = await glob(pattern);
  } catch (err) {
    console.error(
      `WARN: Failed to glob ${pattern}: ${err instanceof Error ? err.message : 'unknown'}`,
    );
    return files;
  }

  for (const filePath of filePaths) {
    try {
      const content = await readFile(filePath, 'utf-8');
      const relativePath = path.relative(docsPath, filePath).replace(/\\/g, '/');
      files.push({ path: relativePath, content });
    } catch (err) {
      if (err instanceof Error) {
        console.error(`WARN: Skipping ${filePath}: ${err.message}`);
      }
    }
  }

  return files;
}

function resolveCachePath(override?: string): string {
  if (override) return override;
  const envPath = process.env.CACHE_PATH?.trim();
  return envPath && envPath.length > 0 ? envPath : getDefaultCachePath();
}

/**
 * Escape a string for safe inclusion in YAML.
 * Uses JSON.stringify which produces valid YAML double-quoted strings.
 */
function yamlEscape(value: string): string {
  return JSON.stringify(value);
}

/**
 * Build synthetic YAML frontmatter from parsed section metadata.
 * Only includes non-empty fields.
 */
function buildSyntheticFrontmatter(fields: {
  topic?: string;
  id?: string;
  category?: string;
}): string {
  const lines: string[] = ['---'];

  if (fields.topic) {
    lines.push(`topic: ${yamlEscape(fields.topic)}`);
  }
  if (fields.id) {
    lines.push(`id: ${yamlEscape(fields.id)}`);
  }
  if (fields.category) {
    lines.push(`category: ${yamlEscape(fields.category)}`);
  }

  // Only return frontmatter if we have at least one field
  if (lines.length === 1) {
    return '';
  }

  lines.push('---', '');
  return lines.join('\n');
}

/**
 * Derive a document ID from a URL's content path.
 * E.g., 'https://code.claude.com/docs/en/hooks/input-schema' → 'hooks-input-schema'
 */
function deriveIdFromUrl(url: string | undefined): string | undefined {
  if (!url) return undefined;
  const segments = extractContentPath(url);
  return segments.length > 0 ? segments.join('-') : undefined;
}

export async function loadFromOfficial(url: string, cachePath?: string): Promise<MarkdownFile[]> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const sections = await fetchAndParse(url, resolvedCachePath);
  const filtered = filterToExtensions(sections).filter((s) => s.content.trim().length > 0);

  return filtered.map((s) => {
    const sourceKey = s.sourceUrl || s.title || '';
    const topic = s.title?.trim() || undefined;
    const id = deriveIdFromUrl(s.sourceUrl);
    const category = deriveCategory(sourceKey);

    // Build synthetic frontmatter to enrich metadata for search
    const frontmatter = buildSyntheticFrontmatter({ topic, id, category });

    return {
      path: s.sourceUrl || s.title || 'unknown',
      content: frontmatter + s.content,
    };
  });
}

async function fetchAndParse(url: string, cachePath: string): Promise<ParsedSection[]> {
  try {
    const { content } = await fetchOfficialDocs(url);
    await writeCache(cachePath, content);
    return parseSections(content);
  } catch (err: unknown) {
    if (err instanceof FetchTimeoutError) {
      console.error(err.message);
    } else if (err instanceof FetchHttpError) {
      console.error(err.message);
    } else if (err instanceof FetchNetworkError) {
      console.error(err.message);
    } else {
      console.error(`Fetch failed: ${err instanceof Error ? err.message : String(err)}`);
    }

    const cached = await readCache(cachePath);
    if (cached) {
      const ageHours = (cached.age / 3600000).toFixed(1);
      console.warn(`Using cached docs (${ageHours}h old)`);
      return parseSections(cached.content);
    }

    throw err;
  }
}
