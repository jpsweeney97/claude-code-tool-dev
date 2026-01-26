// src/url-helpers.ts
// Shared URL parsing utilities for handling documentation URLs

/**
 * Check if a string is an HTTP(S) URL.
 */
export function isHttpUrl(value: string): boolean {
  return value.startsWith('http://') || value.startsWith('https://');
}

/**
 * Parse a URL string into path segments.
 * Returns empty array if URL is invalid.
 */
export function urlPathSegments(urlString: string): string[] {
  try {
    const url = new URL(urlString);
    return url.pathname.split('/').filter(Boolean);
  } catch {
    return [];
  }
}

/**
 * Common language codes used in documentation URLs.
 * Matches 2-letter codes (en, fr, de) and regional variants (zh-cn, pt-br).
 */
const LANGUAGE_CODE_PATTERN = /^[a-z]{2}(-[a-z]{2})?$/i;

/**
 * Extract content path segments from a docs URL, stripping /docs/{lang}/ prefix if present.
 *
 * Examples:
 * - ['docs', 'en', 'hooks', 'overview'] → ['hooks', 'overview']
 * - ['docs', 'hooks', 'overview'] → ['hooks', 'overview'] (no language)
 * - ['hooks', 'overview'] → ['hooks', 'overview'] (no /docs/ prefix)
 */
export function docsContentSegments(segments: string[]): string[] {
  const docsIndex = segments.indexOf('docs');

  if (docsIndex >= 0) {
    const afterDocs = segments.slice(docsIndex + 1);
    // Skip language code if present (e.g., 'en', 'fr', 'zh-cn')
    if (afterDocs.length > 0 && LANGUAGE_CODE_PATTERN.test(afterDocs[0])) {
      return afterDocs.slice(1);
    }
    return afterDocs;
  }

  return segments;
}

/**
 * Extract content path from a URL, stripping the /docs/{lang}/ prefix.
 * Convenience function combining urlPathSegments and docsContentSegments.
 *
 * Examples:
 * - 'https://code.claude.com/docs/en/hooks' → ['hooks']
 * - 'https://code.claude.com/docs/en/hooks/input-schema' → ['hooks', 'input-schema']
 * - 'https://example.com/hooks' → ['hooks']
 */
export function extractContentPath(url: string): string[] {
  if (!isHttpUrl(url)) {
    return [];
  }
  return docsContentSegments(urlPathSegments(url));
}
