// src/loader.ts
import { createHash } from 'crypto';
import { glob } from 'glob';
import { readFile } from 'fs/promises';
import * as path from 'path';
import type { MarkdownFile, ParsedSection } from './types.js';
import { fetchOfficialDocs, FetchHttpError, FetchNetworkError, FetchTimeoutError } from './fetcher.js';
import { parseSections } from './parser.js';
import { readCache, readCacheIfFresh, writeCache, getDefaultCachePath } from './cache.js';
import { extractContentPath } from './url-helpers.js';
import { deriveCategory, getUnmappedSegments } from './frontmatter.js';

/**
 * Default minimum number of sections required for content to be considered valid.
 * Prevents caching truncated or incomplete documentation.
 * Current full docs have ~50 sections; 40 provides margin for minor changes.
 * Override with MIN_SECTION_COUNT env var for testing (set to 0 to disable).
 */
const DEFAULT_MIN_SECTION_COUNT = 40;

export function getMinSectionCount(): number {
  const raw = process.env.MIN_SECTION_COUNT?.trim();
  if (raw !== undefined && raw.length > 0) {
    const val = parseInt(raw, 10);
    if (Number.isFinite(val) && val >= 0) {
      return val;
    }
  }
  return DEFAULT_MIN_SECTION_COUNT;
}

/**
 * Error thrown when fetched content fails validation checks.
 */
export class ContentValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ContentValidationError';
  }
}

function hashContent(content: string): string {
  return createHash('sha256').update(content).digest('hex');
}

export async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = [];
  const pattern = path.join(docsPath, '**/*.md').replace(/\\/g, '/');

  let filePaths: string[];
  try {
    filePaths = await glob(pattern);
  } catch (err) {
    const code = (err as NodeJS.ErrnoException).code;
    console.error(
      `WARN: Failed to glob ${pattern}: ${
        err instanceof Error ? err.message : 'unknown'
      }${code ? ` (code: ${code})` : ''}`,
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

export interface LoadResult {
  files: MarkdownFile[];
  contentHash: string;
}

interface FetchResult {
  sections: ParsedSection[];
  contentHash: string;
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

export async function loadFromOfficial(
  url: string,
  cachePath?: string,
  forceRefresh = false,
): Promise<LoadResult> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const { sections, contentHash } = await fetchAndParse(url, resolvedCachePath, forceRefresh);
  const filtered = sections.filter((s) => s.content.trim().length > 0);

  // Parse diagnostics: count only Source:-anchored sections (exclude preamble pseudo-section)
  const sourceAnchoredCount = sections.filter(s => s.sourceUrl !== '').length;
  const diagnostics = {
    sourceLineCount: sourceAnchoredCount,
    nonEmptySectionCount: filtered.length,
  };
  console.error(
    `Parse diagnostics: ${diagnostics.sourceLineCount} Source: lines, ` +
    `${diagnostics.nonEmptySectionCount} non-empty sections`
  );

  // Report unmapped URL segments (per-load, no module-level state)
  // Guard: skip preamble sections with empty sourceUrl (defense-in-depth —
  // getUnmappedSegments handles '' safely, but the guard makes intent explicit)
  const unmapped = new Map<string, number>();
  for (const section of filtered) {
    if (section.sourceUrl === '') continue;
    for (const seg of getUnmappedSegments(section.sourceUrl)) {
      unmapped.set(seg, (unmapped.get(seg) ?? 0) + 1);
    }
  }
  if (unmapped.size > 0) {
    const entries = [...unmapped.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([seg, count]) => `${seg} (${count}x)`)
      .join(', ');
    console.warn(`Category: ${unmapped.size} unmapped URL segment(s): ${entries}`);
  }

  return {
    contentHash,
    files: filtered.map((s) => {
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
    }),
  };
}

async function fetchAndParse(
  url: string,
  cachePath: string,
  forceRefresh = false,
): Promise<FetchResult> {
  // Skip fresh cache check if force refresh requested
  if (!forceRefresh) {
    const fresh = await readCacheIfFresh(cachePath);
    if (fresh) {
      return {
        sections: parseSections(fresh.content),
        contentHash: hashContent(fresh.content),
      };
    }
  }

  try {
    const { content } = await fetchOfficialDocs(url);
    const sections = parseSections(content);

    // Validate section count to detect truncated content
    const minSections = getMinSectionCount();
    if (minSections > 0 && sections.length < minSections) {
      throw new ContentValidationError(
        `Fetched content has only ${sections.length} sections (minimum: ${minSections}). ` +
          'Content may be truncated or incomplete.',
      );
    }

    const contentHash = hashContent(content);
    await writeCache(cachePath, content);
    return { sections, contentHash };
  } catch (err: unknown) {
    // Only fall back to stale cache for expected operational errors.
    // Programmer errors (TypeError, RangeError, etc.) propagate immediately
    // so parser regressions are not masked by serving stale data.
    const isExpected =
      err instanceof FetchHttpError ||
      err instanceof FetchNetworkError ||
      err instanceof FetchTimeoutError ||
      err instanceof ContentValidationError;

    if (!isExpected) throw err;

    if (err instanceof ContentValidationError) {
      console.error(`Content validation failed: ${err.message}`);
    } else {
      console.error(err.message);
    }

    // Fall back to stale cache on expected fetch/validation error
    const cached = await readCache(cachePath);
    if (cached) {
      const ageHours = (cached.age / 3600000).toFixed(1);
      console.warn(`Using cached docs (${ageHours}h old)`);
      return {
        sections: parseSections(cached.content),
        contentHash: hashContent(cached.content),
      };
    }

    throw err;
  }
}
