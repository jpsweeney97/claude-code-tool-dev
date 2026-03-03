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
 * Determine if a line at a given index is a standalone --- separator.
 * A standalone separator is:
 * - Exactly "---" (with optional trailing whitespace)
 * - At the start of a line (beginning of string or preceded by \n)
 */
function isStandaloneSeparator(raw: string, lineStart: number): boolean {
  // Check the line content from lineStart
  const lineEnd = raw.indexOf('\n', lineStart);
  const line = raw.slice(lineStart, lineEnd === -1 ? raw.length : lineEnd);
  return /^---\s*$/.test(line);
}

/**
 * Find the start of the line at or before a given index.
 */
function findLineStart(raw: string, index: number): number {
  const prevNewline = raw.lastIndexOf('\n', index - 1);
  return prevNewline === -1 ? 0 : prevNewline + 1;
}

/** Max blank lines to skip when looking backward for a --- separator. */
const MAX_LOOKBACK_NEWLINES = 3;

/**
 * Parse raw llms-full.txt content into sections using a two-pass approach.
 *
 * Pass 1: Collect all Source: line positions.
 * Pass 2: For each Source: line, resolve the section boundary (pageStart)
 *          by looking backward for the nearest heading and optional --- separator.
 *
 * Section content runs from after the Source: line to the next section's pageStart.
 * The # Title line is naturally excluded from content because it precedes the
 * Source: line — no post-processing stripping needed.
 *
 * Supports both old format (# Title + Source:) and new format (--- + # Title + Source:).
 * The --- lookback finds nothing in the old format, so boundaries degrade gracefully.
 */
export function parseSections(raw: string): ParsedSection[] {
  const sourceRe = /^Source:\s+(\S+)\s*$/gm;
  const matches = Array.from(raw.matchAll(sourceRe));
  const sections: ParsedSection[] = [];

  // No Source: lines found — return entire content as single section
  if (matches.length === 0) {
    const title = findFirstHeadingInRange(raw, 0, raw.length);
    if (raw.trim().length > 0) {
      sections.push({ sourceUrl: '', title, content: raw });
    }
    return sections;
  }

  // Pass 1: Resolve pageStart for each Source: match
  // pageStart is the earliest boundary of this section — the --- line,
  // the heading line, or the Source: line itself (whichever comes first).
  const pageStarts: number[] = [];

  for (const match of matches) {
    const matchIndex = match.index ?? 0;
    const heading = findLastHeadingBefore(raw, matchIndex);

    let pageStart = matchIndex; // Default: Source: line itself

    if (heading.index >= 0) {
      pageStart = heading.index; // Heading found — section starts at heading

      // Check for a --- line immediately before the heading (within MAX_LOOKBACK_NEWLINES)
      const headingLineStart = findLineStart(raw, heading.index);
      if (headingLineStart > 0) {
        // Walk backward past blank lines (whitespace-only lines count as blank)
        let checkPos = headingLineStart - 1;
        let newlineCount = 0;
        while (
          checkPos >= 0 &&
          (raw[checkPos] === '\n' || raw[checkPos] === '\r' ||
           raw[checkPos] === ' ' || raw[checkPos] === '\t')
        ) {
          if (raw[checkPos] === '\n') newlineCount++;
          if (newlineCount > MAX_LOOKBACK_NEWLINES) break;
          checkPos--;
        }
        if (checkPos >= 0 && newlineCount <= MAX_LOOKBACK_NEWLINES) {
          const candidateLineStart = findLineStart(raw, checkPos);
          if (isStandaloneSeparator(raw, candidateLineStart)) {
            pageStart = candidateLineStart;
          }
        }
      }
    }

    pageStarts.push(pageStart);
  }

  // Handle preamble: content before the first section's pageStart
  if (pageStarts[0] > 0) {
    const preamble = raw.slice(0, pageStarts[0]);
    // Filter non-meaningful preamble (blank or just ---)
    const meaningful = preamble.replace(/^---\s*$/gm, '').trim();
    if (meaningful.length > 0) {
      const title = findFirstHeadingInRange(raw, 0, pageStarts[0]);
      sections.push({ sourceUrl: '', title, content: preamble.trim() });
    }
  }

  // Pass 2: Extract sections using pageStarts as boundaries
  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const sourceUrl = match[1];
    const matchIndex = match.index ?? 0;
    const lineEnd = matchIndex + match[0].length;
    const contentStart = lineBreakAfter(raw, lineEnd);

    // Content ends at the next section's pageStart, or end of file
    const contentEnd = i + 1 < matches.length ? pageStarts[i + 1] : raw.length;

    const content = raw.slice(contentStart, contentEnd).trimEnd();

    // Extract title from the heading before Source:
    const heading = findLastHeadingBefore(raw, matchIndex);
    const title = heading.title;

    sections.push({ sourceUrl, title, content });
  }

  return sections;
}
