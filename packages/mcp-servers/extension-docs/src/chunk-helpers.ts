import type { MarkdownFile } from './types.js';
import { isHttpUrl, extractContentPath } from './url-helpers.js';

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/\.md$/, '') // Strip .md extension
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Generate a chunk ID for a documentation file.
 *
 * For URLs, extracts the content path to create readable IDs:
 * - 'https://code.claude.com/docs/en/hooks' → 'hooks'
 * - 'https://code.claude.com/docs/en/hooks/input-schema' → 'hooks-input-schema'
 *
 * For file paths, uses the path directly:
 * - 'hooks/overview.md' → 'hooks-overview'
 */
export function generateChunkId(
  file: MarkdownFile,
  heading?: string,
  splitIndex?: number,
): string {
  let fileSlug: string;

  if (isHttpUrl(file.path)) {
    // For URLs, use the content path segments for a cleaner ID
    const segments = extractContentPath(file.path);
    fileSlug = slugify(segments.join('-') || 'unknown');
  } else {
    // For file paths, use the path directly
    fileSlug = slugify(file.path);
  }

  if (!heading) return fileSlug;

  const headingSlug = slugify(heading);
  // Append suffix for forced splits using 1-based indexing:
  // - undefined or 1 → no suffix (e.g., file#section)
  // - 2+ → suffix (e.g., file#section-2, file#section-3)
  const suffix = splitIndex != null && splitIndex > 1 ? `-${splitIndex}` : '';
  return `${fileSlug}#${headingSlug}${suffix}`;
}

export function computeTermFreqs(tokens: string[]): Map<string, number> {
  const freqs = new Map<string, number>();
  for (const token of tokens) {
    freqs.set(token, (freqs.get(token) ?? 0) + 1);
  }
  return freqs;
}
