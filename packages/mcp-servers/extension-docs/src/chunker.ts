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

export const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;

export function chunkFile(file: MarkdownFile): Chunk[] {
  const { frontmatter, body } = parseFrontmatter(file.content, file.path);
  const metadataHeader = formatMetadataHeader(frontmatter);
  const preparedContent = metadataHeader + body;

  if (isSmallEnoughForWholeFile(preparedContent)) {
    return [createWholeFileChunk(file, preparedContent, frontmatter)];
  }

  const rawChunks = splitAtH2(file, preparedContent, frontmatter);
  return mergeSmallChunks(rawChunks, frontmatter);
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
  const lines = content.split('\n');
  const chunks: Chunk[] = [];
  let intro: string[] = [];
  let current: string[] = [];
  let currentHeading: string | undefined;
  let inFence = false;
  let fencePattern = '';
  let isFirstH2 = true;

  for (const line of lines) {
    // CommonMark-compliant fence matching: 0-3 leading spaces
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!inFence) {
        inFence = true;
        fencePattern = fence[2];
      } else if (line.match(new RegExp(`^ {0,3}${fencePattern[0]}{${fencePattern.length},}\\s*$`))) {
        inFence = false;
        fencePattern = '';
      }
    }

    // Split at H2 only outside code fences
    if (!inFence && /^##\s/.test(line)) {
      if (current.length > 0 && currentHeading) {
        chunks.push(createSplitChunk(file, current.join('\n'), currentHeading, frontmatter));
      } else if (current.length > 0) {
        intro = current;
      }

      current = isFirstH2 ? [...intro, '', line] : [line];
      currentHeading = line;
      isFirstH2 = false;
    } else {
      current.push(line);
    }
  }

  if (current.length > 0) {
    chunks.push(createSplitChunk(file, current.join('\n'), currentHeading, frontmatter));
  }

  return chunks;
}

function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  frontmatter: Frontmatter,
): Chunk {
  const category = frontmatter.category ?? deriveCategory(file.path);
  const tags = frontmatter.tags ?? [];

  // Include all metadata terms in tokens so chunks are searchable by category/tags/relationships
  const metadataTerms = getMetadataTerms(frontmatter, category);
  const tokens = [...tokenize(content), ...metadataTerms];

  return {
    id: generateChunkId(file, heading),
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

    if (bufferLines + lines <= MAX_CHUNK_LINES && bufferChars + chars <= MAX_CHUNK_CHARS) {
      buffer.push(chunk);
      bufferLines += lines;
      bufferChars += chars;
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
