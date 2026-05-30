// src/loader.ts
import { createHash } from 'crypto';
import * as path from 'path';
import type { MarkdownFile, ParsedSection } from './types.js';
import {
  fetchOfficialDocs,
  FetchHttpError,
  FetchNetworkError,
  FetchResponseTooLargeError,
  FetchTimeoutError,
} from './fetcher.js';
import { parseSections } from './parser.js';
import { readCache, readCacheIfFresh, writeCache, getDefaultCachePath } from './cache.js';
import { extractContentPath } from './url-helpers.js';
import { deriveCategory, getUnmappedSegments } from './frontmatter.js';
import type { SourceKind, CorpusProvenance } from './trust.js';
import type { LoaderDiagnostics } from './canary.js';

/** Absolute floor below which fetched content is treated as truncated and must NOT overwrite the
 *  content cache (B1). Fixed, not env-tunable: MIN_SECTION_COUNT tunes only the canary/index floor
 *  (Task 2.4). The official corpus is ~141 sections, so 40 is a wide truncation margin. */
const CACHE_WRITE_MIN_SECTIONS = 40;

/**
 * Error thrown when fetched content fails validation checks.
 */
export class ContentValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ContentValidationError';
  }
}

function getMaxStaleCacheMs(): number {
  const raw = process.env.DOCS_CACHE_MAX_STALE_MS?.trim();
  if (!raw) return 0;
  const val = Number(raw);
  if (!Number.isFinite(val) || val < 0) return 0;
  return val;
}

function hashContent(content: string): string {
  return createHash('sha256').update(content).digest('hex');
}

function resolveCachePath(override?: string): string {
  if (override) return override;
  const envPath = process.env.CACHE_PATH?.trim();
  return envPath && envPath.length > 0 ? envPath : getDefaultCachePath();
}

export interface LoadResult {
  files: MarkdownFile[];
  contentHash: string;
  provenance: CorpusProvenance;
  diagnostics: LoaderDiagnostics;
}

interface FetchResult {
  sections: ParsedSection[];
  contentHash: string;
  sourceKind: SourceKind;
  obtainedAt: number;
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
  const { sections, contentHash, sourceKind, obtainedAt } = await fetchAndParse(url, resolvedCachePath, forceRefresh);
  const filtered = sections.filter((s) => s.content.trim().length > 0);

  // Parse diagnostics: count only Source:-anchored sections (exclude preamble pseudo-section)
  const sourceAnchoredCount = sections.filter(s => s.sourceUrl !== '').length;

  // Count fallback sections (sections where deriveCategory returns 'uncategorized' —
  // i.e. no URL segment was mapped). This is what the fallback-delta canary watches.
  //
  // NOTE — intentional population asymmetry: fallbackSectionCount is computed over the
  // PRE-filter `sections` array (matching sectionCount = sections.length, the value the
  // canary thresholds compare against), whereas fallbackSegmentCount / unmappedSegments
  // below are derived from the POST-filter `filtered` set (and skip empty-sourceUrl
  // preamble). The two are observability diagnostics over different populations; the
  // canary gates (fallback_segment_collapse FAIL, fallback_segment_drift WARN) read
  // fallbackSectionCount ONLY, so the asymmetry has no gate impact. Keep the gate input
  // on the same pre-filter basis as sectionCount.
  const fallbackSectionCount = sections.filter(s => {
    const sourceKey = s.sourceUrl || s.title || '';
    return deriveCategory(sourceKey) === 'uncategorized';
  }).length;

  console.error(
    `Parse diagnostics: ${sourceAnchoredCount} Source: lines, ` +
    `${filtered.length} non-empty sections`
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

  // Build sorted unmapped segments: count desc, then name asc
  const sortedUnmapped: Array<[string, number]> = [...unmapped.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));

  return {
    contentHash,
    provenance: { sourceKind, obtainedAt },
    // sectionCount = pre-filter total (includes empty preamble pseudo-sections);
    // nonEmptySectionCount = post-filter. Canary thresholds compare against sectionCount.
    diagnostics: {
      sourceAnchoredCount,
      nonEmptySectionCount: filtered.length,
      sectionCount: sections.length,
      fallbackSectionCount,
      fallbackSegmentCount: sortedUnmapped.length,
      unmappedSegments: sortedUnmapped,
    },
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
        sourceKind: 'cached',
        obtainedAt: Date.now() - fresh.age,
      };
    }
  }

  try {
    const { content } = await fetchOfficialDocs(url);
    const sections = parseSections(content);

    // Refuse to overwrite the content cache with truncated content (B1). Fixed floor; the canary
    // owns the tunable index floor (Task 2.4). The throw fires BEFORE writeCache, so the good cache survives.
    if (sections.length < CACHE_WRITE_MIN_SECTIONS) {
      throw new ContentValidationError(
        `Fetched content has only ${sections.length} sections (minimum: ${CACHE_WRITE_MIN_SECTIONS}). ` +
          'Content may be truncated or incomplete.',
      );
    }

    const contentHash = hashContent(content);
    await writeCache(cachePath, content);
    return { sections, contentHash, sourceKind: 'fetched', obtainedAt: Date.now() };
  } catch (err: unknown) {
    // Only fall back to stale cache for expected operational errors.
    // Programmer errors (TypeError, RangeError, etc.) propagate immediately
    // so parser regressions are not masked by serving stale data.
    const isExpected =
      err instanceof FetchHttpError ||
      err instanceof FetchNetworkError ||
      err instanceof FetchResponseTooLargeError ||
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

      // Reject stale cache exceeding hard age limit (if configured)
      const maxStaleMs = getMaxStaleCacheMs();
      if (maxStaleMs > 0 && cached.age > maxStaleMs) {
        const maxHours = (maxStaleMs / 3600000).toFixed(1);
        console.error(
          `Stale cache rejected: ${ageHours}h old exceeds max stale limit of ${maxHours}h`,
        );
        throw err;
      }

      console.warn(`Using cached docs (${ageHours}h old)`);
      return {
        sections: parseSections(cached.content),
        contentHash: hashContent(cached.content),
        sourceKind: 'stale-fallback',
        obtainedAt: Date.now() - cached.age,
      };
    }

    throw err;
  }
}
