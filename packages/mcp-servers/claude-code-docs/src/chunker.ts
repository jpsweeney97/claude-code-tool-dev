// src/chunker.ts
import type { MarkdownFile, Chunk } from './types.js';
import { tokenize } from './tokenizer.js';
import {
  parseFrontmatter,
  formatMetadataHeader,
  deriveCategory,
  type Frontmatter,
} from './frontmatter.js';
import { generateChunkId, computeTermFreqs } from './chunk-helpers.js';
import { ProtectedBlockTracker } from './protected-block-tracker.js';

export const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;
const OVERLAP_LINES_FOR_FORCED_SPLITS = 5;

export function chunkFile(file: MarkdownFile): Chunk[] {
  // Input validation
  if (!file.path) {
    throw new Error('chunkFile: file.path is required');
  }
  if (file.content === undefined || file.content === null) {
    throw new Error(`chunkFile: file.content is required for ${file.path}`);
  }

  try {
    const { frontmatter, body } = parseFrontmatter(file.content, file.path);
    // Warnings are pushed to the deprecated global by parseFrontmatter() for
    // backward compatibility. The caller (index.ts) handles warning display
    // via getParseWarnings()/clearParseWarnings().

    const metadataHeader = formatMetadataHeader(frontmatter);
    const preparedContent = metadataHeader + body;

    if (isSmallEnoughForWholeFile(preparedContent)) {
      return [createWholeFileChunk(file, preparedContent, frontmatter)];
    }

    const rawChunks = splitAtH2(file, preparedContent, frontmatter);
    return mergeSmallChunks(rawChunks, frontmatter);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to chunk file ${file.path}: ${message}`);
  }
}

function countLines(content: string): number {
  return content.split('\n').length;
}

function isSmallEnoughForWholeFile(content: string): boolean {
  return countLines(content) <= MAX_CHUNK_LINES && content.length <= MAX_CHUNK_CHARS;
}

/**
 * Collect all metadata fields that should contribute to searchable tokens.
 * Tokenizes each field so hyphenated values like "hooks-overview" become ["hooks", "overview"].
 */
function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const sources: (string | undefined)[] = [
    derivedCategory,
    fm.id,
    fm.topic,
    ...(fm.tags ?? []),
    ...(fm.requires ?? []),
    ...(fm.related_to ?? []),
  ];
  return sources.filter((s): s is string => s !== undefined).flatMap(tokenize);
}

function createWholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  const category = fm.category ?? deriveCategory(file.path);
  const metadataTerms = getMetadataTerms(fm, category);
  const tokens = [...tokenize(content), ...metadataTerms];
  return {
    id: generateChunkId(file),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category,
    tags: fm.tags ?? [],
    source_file: file.path,
  };
}

function splitAtH2(file: MarkdownFile, content: string, frontmatter: Frontmatter): Chunk[] {
  const { parts } = splitBounded(content, []);
  const chunks: Chunk[] = [];

  // Track split indices per heading for ID generation
  const headingSplitCounts = new Map<string, number>();

  for (const part of parts) {
    const headingKey = part.heading ?? '';

    // Safety check: if part exceeds limits, apply hard split
    if (!withinLimits(part.content)) {
      const hardParts = hardSplitWithOverlap(part.content);
      for (let i = 0; i < hardParts.length; i++) {
        const currentCount = headingSplitCounts.get(headingKey) ?? 0;
        const splitIndex = currentCount + 1;
        headingSplitCounts.set(headingKey, splitIndex);
        chunks.push(
          createSplitChunk(file, hardParts[i], part.heading, frontmatter, splitIndex)
        );
      }
      continue;
    }

    const currentCount = headingSplitCounts.get(headingKey) ?? 0;
    const splitIndex = currentCount + 1;
    headingSplitCounts.set(headingKey, splitIndex);
    chunks.push(
      createSplitChunk(file, part.content, part.heading, frontmatter, splitIndex)
    );
  }

  return chunks;
}

function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  frontmatter: Frontmatter,
  splitIndex?: number,
): Chunk {
  const category = frontmatter.category ?? deriveCategory(file.path);
  const tags = frontmatter.tags ?? [];

  // Include all metadata terms in tokens so chunks are searchable by category/tags/relationships
  const metadataTerms = getMetadataTerms(frontmatter, category);
  const tokens = [...tokenize(content), ...metadataTerms];

  return {
    id: generateChunkId(file, heading, splitIndex),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    category,
    tags,
    source_file: file.path,
    heading,
  };
}

function mergeSmallChunks(chunks: Chunk[], frontmatter: Frontmatter): Chunk[] {
  const result: Chunk[] = [];
  let buffer: Chunk[] = [];
  let bufferLines = 0;
  let bufferChars = 0;

  for (const chunk of chunks) {
    const lines = chunk.content.split('\n').length;
    const chars = chunk.content.length;

    // Account for \n\n separator added when combining chunks
    // Each additional chunk adds 2 chars (\n\n) and 1 line (blank line between)
    const separatorLines = buffer.length > 0 ? 1 : 0;
    const separatorChars = buffer.length > 0 ? 2 : 0;

    if (
      bufferLines + lines + separatorLines <= MAX_CHUNK_LINES &&
      bufferChars + chars + separatorChars <= MAX_CHUNK_CHARS
    ) {
      buffer.push(chunk);
      bufferLines += lines + separatorLines;
      bufferChars += chars + separatorChars;
    } else {
      if (buffer.length) result.push(combineChunks(buffer, frontmatter));
      buffer = [chunk];
      bufferLines = lines;
      bufferChars = chars;
    }
  }

  if (buffer.length) result.push(combineChunks(buffer, frontmatter));
  return result;
}

function combineChunks(chunks: Chunk[], frontmatter: Frontmatter): Chunk {
  if (chunks.length === 0) {
    throw new Error('combineChunks called with empty array');
  }

  if (chunks.length === 1) {
    return chunks[0];
  }

  const combinedContent = chunks.map((c) => c.content).join('\n\n');
  const { category, tags } = chunks[0];
  const metadataTerms = getMetadataTerms(frontmatter, category);
  const tokens = [...tokenize(combinedContent), ...metadataTerms];

  return {
    ...chunks[0],
    content: combinedContent,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    heading: chunks[0].heading,
    merged_headings: chunks.map((c) => c.heading).filter(Boolean) as string[],
  };
}

// ============================================================================
// Bounded Splitting Helpers
// ============================================================================

/** Check if text is within both character and line limits */
function withinLimits(text: string): boolean {
  return text.length <= MAX_CHUNK_CHARS && countLines(text) <= MAX_CHUNK_LINES;
}

/** Represents a part from bounded splitting */
interface BoundedPart {
  content: string;
  heading?: string;
  needsOverlap: boolean; // True for forced splits (paragraph/hard), false for natural splits (H2/H3)
}

/**
 * Split content at heading boundaries (H2 or H3) while respecting code fences.
 * Returns array of parts, each containing the heading line and its content.
 */
function splitByHeadingOutsideFences(
  content: string,
  level: 2 | 3
): { heading: string | undefined; content: string }[] {
  const lines = content.split('\n');
  const tracker = new ProtectedBlockTracker();
  const parts: { heading: string | undefined; content: string }[] = [];

  let currentLines: string[] = [];
  let currentHeading: string | undefined;
  const pattern = level === 2 ? /^##\s/ : /^###\s/;

  for (const line of lines) {
    const inProtected = tracker.processLine(line);

    if (!inProtected && pattern.test(line)) {
      // Save previous part if it has content
      if (currentLines.length > 0) {
        parts.push({ heading: currentHeading, content: currentLines.join('\n') });
      }
      currentLines = [line];
      currentHeading = line;
    } else {
      currentLines.push(line);
    }
  }

  // Save final part
  if (currentLines.length > 0) {
    parts.push({ heading: currentHeading, content: currentLines.join('\n') });
  }

  return parts;
}

/**
 * Check if a line is a table row (starts with |, ignoring leading whitespace).
 */
function isTableLine(line: string): boolean {
  return line.trimStart().startsWith('|');
}

/**
 * Split an oversized table at row boundaries, preserving headers in each chunk.
 * Returns array of table fragment strings, each starting with header+separator.
 */
function splitOversizedTable(tableLines: string[]): string[] {
  if (tableLines.length < 3) {
    // Not enough lines for header + separator + data
    return [tableLines.join('\n')];
  }

  // Validate table structure: second line should be a markdown table separator
  // Valid separators contain only |, -, :, and whitespace (e.g., |---|:---:|)
  const separator = tableLines[1];
  if (!/^\s*\|[\s\-:|]+\|\s*$/.test(separator)) {
    // Not a valid markdown table - return as-is without header duplication
    return [tableLines.join('\n')];
  }

  const headerLines = tableLines.slice(0, 2); // header + separator
  const dataRows = tableLines.slice(2);
  const result: string[] = [];

  let currentChunk = [...headerLines];
  for (const row of dataRows) {
    const projected = [...currentChunk, row].join('\n');

    if (projected.length > MAX_CHUNK_CHARS && currentChunk.length > 2) {
      // Current chunk is full, save it
      result.push(currentChunk.join('\n'));
      currentChunk = [...headerLines, row]; // Start new chunk with header
    } else {
      currentChunk.push(row);
    }
  }

  // Save remaining rows
  if (currentChunk.length > 2) {
    result.push(currentChunk.join('\n'));
  }

  return result;
}

/**
 * Split content at paragraph boundaries (blank lines) while respecting code fences
 * and keeping tables as atomic units (or splitting them with header preservation).
 */
function splitByParagraphOutsideFences(content: string): string[] {
  const lines = content.split('\n');
  const tracker = new ProtectedBlockTracker();
  const paragraphs: string[] = [];
  let currentLines: string[] = [];
  let inTable = false;
  let tableLines: string[] = [];

  for (const line of lines) {
    const inProtected = tracker.processLine(line);

    if (!inProtected) {
      const isTable = isTableLine(line);

      if (isTable && !inTable) {
        // Starting a new table - save any accumulated content first
        if (currentLines.length > 0) {
          paragraphs.push(currentLines.join('\n'));
          currentLines = [];
        }
        inTable = true;
        tableLines = [line];
      } else if (isTable && inTable) {
        // Continuing a table
        tableLines.push(line);
      } else if (!isTable && inTable) {
        // Exiting a table
        // Check if table is oversized and needs splitting
        const tableContent = tableLines.join('\n');
        if (tableContent.length > MAX_CHUNK_CHARS && tableLines.length > 2) {
          // Split oversized table with header preservation
          const tableParts = splitOversizedTable(tableLines);
          paragraphs.push(...tableParts);
        } else {
          // Table fits, keep it atomic
          paragraphs.push(tableContent);
        }
        tableLines = [];
        inTable = false;

        // Handle the current non-table line
        // Blank lines after tables act as paragraph separators. When currentLines is empty
        // (just exited a table), we intentionally drop the blank line since the table was
        // already pushed as a separate paragraph - the boundary is preserved by the \n\n
        // join in accumulateParagraphsWithOverlap().
        if (line.trim() === '' && currentLines.length > 0) {
          paragraphs.push(currentLines.join('\n'));
          currentLines = [];
        } else if (line.trim() !== '') {
          currentLines.push(line);
        }
      } else {
        // Normal paragraph handling
        if (line.trim() === '' && currentLines.length > 0) {
          paragraphs.push(currentLines.join('\n'));
          currentLines = [];
        } else {
          currentLines.push(line);
        }
      }
    } else {
      // Inside a protected block - just accumulate
      currentLines.push(line);
    }
  }

  // Handle any remaining content
  if (inTable && tableLines.length > 0) {
    const tableContent = tableLines.join('\n');
    if (tableContent.length > MAX_CHUNK_CHARS && tableLines.length > 2) {
      const tableParts = splitOversizedTable(tableLines);
      paragraphs.push(...tableParts);
    } else {
      paragraphs.push(tableContent);
    }
  }
  if (currentLines.length > 0) {
    paragraphs.push(currentLines.join('\n'));
  }

  return paragraphs;
}

/**
 * Hard split text into chunks respecting BOTH MAX_CHUNK_LINES AND MAX_CHUNK_CHARS.
 * Used as last resort when content can't be split at semantic boundaries.
 */
function hardSplitWithOverlap(text: string): string[] {
  const lines = text.split('\n');
  const chunks: string[] = [];
  let start = 0;

  while (start < lines.length) {
    // Find the end point that respects both line and character limits
    let end = start;
    let charCount = 0;

    while (end < lines.length) {
      const lineWithNewline = lines[end] + (end < lines.length - 1 ? '\n' : '');
      const newCharCount = charCount + lineWithNewline.length;
      const lineCount = end - start + 1;

      // Stop if adding this line would exceed either limit
      if (lineCount > MAX_CHUNK_LINES || newCharCount > MAX_CHUNK_CHARS) {
        break;
      }

      charCount = newCharCount;
      end++;
    }

    // Ensure at least one line per chunk (handles single lines exceeding char limit)
    if (end === start) {
      end = start + 1;
      // If a single line exceeds MAX_CHUNK_CHARS, truncate it
      if (lines[start].length > MAX_CHUNK_CHARS) {
        lines[start] = lines[start].slice(0, MAX_CHUNK_CHARS);
      }
    }

    chunks.push(lines.slice(start, end).join('\n'));

    // If not the last chunk, apply overlap
    if (end < lines.length) {
      const prevStart = start;
      start = end - OVERLAP_LINES_FOR_FORCED_SPLITS;
      // Ensure start doesn't go negative
      if (start < 0) start = 0;
      // Ensure monotonic progress to prevent infinite loops when overlap
      // pulls start back to where it was (e.g., short line + oversized line)
      if (start <= prevStart) start = prevStart + 1;
    } else {
      break;
    }
  }

  return chunks;
}

/**
 * Accumulate paragraphs into chunks that fit within limits.
 * When a chunk is full, create a new one with overlap from the previous.
 */
function accumulateParagraphsWithOverlap(
  paragraphs: string[],
  heading: string | undefined
): BoundedPart[] {
  const parts: BoundedPart[] = [];
  let currentContent: string[] = [];
  let isFirst = true;

  for (const para of paragraphs) {
    const tentative = [...currentContent, para].join('\n\n');

    if (withinLimits(tentative)) {
      currentContent.push(para);
    } else {
      // Current content is full, save it
      if (currentContent.length > 0) {
        parts.push({
          content: currentContent.join('\n\n'),
          heading,
          needsOverlap: !isFirst,
        });
        isFirst = false;

        // Start new content with overlap from previous
        const prevContent = currentContent.join('\n\n');
        const prevLines = prevContent.split('\n');
        const overlapLines = prevLines.slice(-OVERLAP_LINES_FOR_FORCED_SPLITS);
        currentContent = [overlapLines.join('\n'), para];
      } else {
        // Single paragraph exceeds limits, will need hard split later
        currentContent = [para];
      }
    }
  }

  // Save remaining content with bounds check
  if (currentContent.length > 0) {
    const finalContent = currentContent.join('\n\n');
    if (withinLimits(finalContent)) {
      parts.push({
        content: finalContent,
        heading,
        needsOverlap: !isFirst,
      });
    } else {
      // Final part exceeds limits (overlap + paragraph too large), needs hard split
      const hardParts = hardSplitWithOverlap(finalContent);
      for (let i = 0; i < hardParts.length; i++) {
        parts.push({
          content: hardParts[i],
          heading,
          needsOverlap: i > 0 || !isFirst,
        });
      }
    }
  }

  return parts;
}

/**
 * Split an H3 section that exceeds limits using paragraph boundaries.
 */
function splitH3Section(
  content: string,
  heading: string | undefined
): BoundedPart[] {
  // Try paragraph split first
  const paragraphs = splitByParagraphOutsideFences(content);

  if (paragraphs.length > 1) {
    const parts = accumulateParagraphsWithOverlap(paragraphs, heading);
    // Check if any part still exceeds limits
    const result: BoundedPart[] = [];
    for (const part of parts) {
      if (withinLimits(part.content)) {
        result.push(part);
      } else {
        // Hard split the oversized paragraph
        const hardParts = hardSplitWithOverlap(part.content);
        for (let i = 0; i < hardParts.length; i++) {
          result.push({
            content: hardParts[i],
            heading,
            needsOverlap: i > 0 || part.needsOverlap,
          });
        }
      }
    }
    return result;
  }

  // No paragraph boundaries, hard split
  const hardParts = hardSplitWithOverlap(content);
  return hardParts.map((text, i) => ({
    content: text,
    heading,
    needsOverlap: i > 0,
  }));
}

/**
 * Split an H2 section that exceeds limits using H3 boundaries first,
 * then falling back to paragraph/hard splits.
 */
function splitH2Section(
  content: string,
  heading: string | undefined
): BoundedPart[] {
  // Try H3 split first
  const h3Parts = splitByHeadingOutsideFences(content, 3);

  if (h3Parts.length > 1) {
    // We have H3 structure, process each H3 section
    const result: BoundedPart[] = [];

    for (const h3Part of h3Parts) {
      if (withinLimits(h3Part.content)) {
        result.push({
          content: h3Part.content,
          heading: h3Part.heading ?? heading,
          needsOverlap: false, // H3 is a natural boundary
        });
      } else {
        // H3 section too big, split further
        const subParts = splitH3Section(h3Part.content, h3Part.heading ?? heading);
        result.push(...subParts);
      }
    }

    return result;
  }

  // No H3 structure, fall back to paragraph/hard split
  return splitH3Section(content, heading);
}

/**
 * Main bounded splitting function implementing the hierarchy:
 * H2 -> H3 -> paragraph -> hard split
 */
function splitBounded(
  content: string,
  introContent: string[]
): { parts: BoundedPart[]; intro: string[] } {
  const h2Parts = splitByHeadingOutsideFences(content, 2);
  const result: BoundedPart[] = [];

  // Separate intro (content before first H2) from H2 sections
  let intro: string[] = [];
  let isFirstH2 = true;

  for (const h2Part of h2Parts) {
    // Content without a heading is intro content
    if (!h2Part.heading) {
      intro = h2Part.content.split('\n').filter((line) => line.trim() !== '');
      continue;
    }

    // For first H2, prepend intro content
    let contentToProcess = h2Part.content;
    if (isFirstH2 && intro.length > 0) {
      contentToProcess = [...intro, '', h2Part.content].join('\n');
      isFirstH2 = false;
    } else if (isFirstH2 && introContent.length > 0) {
      contentToProcess = [...introContent, '', h2Part.content].join('\n');
      isFirstH2 = false;
    }

    if (withinLimits(contentToProcess)) {
      result.push({
        content: contentToProcess,
        heading: h2Part.heading,
        needsOverlap: false, // H2 is a natural boundary
      });
    } else {
      // H2 section too big, split further
      const subParts = splitH2Section(contentToProcess, h2Part.heading);
      result.push(...subParts);
    }
  }

  // Handle intro-only content (no H2 headings found)
  // This occurs when the file has content but no H2 sections to split at
  if (result.length === 0 && intro.length > 0) {
    const introText = intro.join('\n');
    if (withinLimits(introText)) {
      result.push({
        content: introText,
        heading: undefined,
        needsOverlap: false,
      });
    } else {
      // Intro exceeds limits, split using paragraph/hard split
      const subParts = splitH3Section(introText, undefined);
      result.push(...subParts);
    }
  }

  return { parts: result, intro };
}
