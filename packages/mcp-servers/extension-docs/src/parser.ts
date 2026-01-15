import type { ParsedSection } from './types.js';

/**
 * Find the last markdown heading (any level) before a given index in the raw string.
 * Returns the heading title and its starting position in the string.
 * Returns empty string and -1 if no heading found.
 */
function findLastHeadingBefore(raw: string, endIndex: number): { title: string; index: number } {
  const prefix = raw.slice(0, endIndex);
  const headingRe = /^#{1,6}\s+(.+)$/gm;
  let match: RegExpExecArray | null = null;
  let lastTitle = '';
  let lastIndex = -1;
  while ((match = headingRe.exec(prefix)) !== null) {
    lastTitle = match[1].trim();
    lastIndex = match.index;
  }
  return { title: lastTitle, index: lastIndex };
}

/**
 * Find the first markdown heading in a range of the raw string.
 * Returns empty string if no heading found.
 */
function findFirstHeadingInRange(raw: string, startIndex: number, endIndex: number): string {
  const segment = raw.slice(startIndex, endIndex);
  const headingRe = /^#{1,6}\s+(.+)$/m;
  const match = headingRe.exec(segment);
  return match ? match[1].trim() : '';
}

/**
 * Return the index after any line break at the given position.
 * Handles both \r\n and \n.
 */
function lineBreakAfter(raw: string, index: number): number {
  if (raw[index] === '\r' && raw[index + 1] === '\n') return index + 2;
  if (raw[index] === '\n') return index + 1;
  return index;
}

/**
 * Parse raw llms-full.txt content into sections delimited by Source: lines.
 *
 * The llms-full.txt format contains concatenated documentation pages, each
 * prefixed with a "Source: <url>" line at the start of a line. This function
 * splits on those markers and extracts the nearest heading before each Source:
 * line as the section title.
 *
 * Content before the first Source: line is captured as a preamble section
 * with an empty sourceUrl.
 */
export function parseSections(raw: string): ParsedSection[] {
  const sourceRe = /^Source:\s+(\S+)\s*$/gm;
  const matches = Array.from(raw.matchAll(sourceRe));
  const sections: ParsedSection[] = [];

  // No Source: lines found - return entire content as single section
  if (matches.length === 0) {
    const title = findFirstHeadingInRange(raw, 0, raw.length);
    if (raw.trim().length > 0) {
      sections.push({ sourceUrl: '', title, content: raw });
    }
    return sections;
  }

  // Handle preamble content before first Source: line
  // Preamble is content that comes BEFORE the heading associated with the first Source
  const firstMatch = matches[0];
  const firstMatchIndex = firstMatch.index ?? 0;
  const firstHeading = findLastHeadingBefore(raw, firstMatchIndex);

  // If there's a heading for the first Source, preamble ends where that heading starts
  // If no heading, preamble ends at the Source line itself
  const preambleEnd = firstHeading.index >= 0 ? firstHeading.index : firstMatchIndex;

  if (preambleEnd > 0) {
    const preamble = raw.slice(0, preambleEnd);
    if (preamble.trim().length > 0) {
      const title = findFirstHeadingInRange(raw, 0, preambleEnd);
      sections.push({ sourceUrl: '', title, content: preamble });
    }
  }

  // Process each Source: delimited section
  for (let i = 0; i < matches.length; i += 1) {
    const match = matches[i];
    const sourceUrl = match[1];
    const matchIndex = match.index ?? 0;
    const lineEnd = matchIndex + match[0].length;
    const contentStart = lineBreakAfter(raw, lineEnd);
    const nextMatch = matches[i + 1];
    const contentEnd = nextMatch?.index ?? raw.length;
    const content = raw.slice(contentStart, contentEnd);
    const heading = findLastHeadingBefore(raw, matchIndex);
    sections.push({ sourceUrl, title: heading.title, content });
  }

  return sections;
}
