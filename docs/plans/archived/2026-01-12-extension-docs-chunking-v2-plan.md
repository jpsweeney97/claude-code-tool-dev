# Extension Docs MCP — Chunking v2 Plan (Robust + Corpus-Aware)

**Status:** Plan only (no implementation changes in this document)  
**Targets:** `packages/mcp-servers/extension-docs` and `docs/extension-reference` corpus  
**Goal:** Improve search quality and robustness while staying offline-only and keeping complexity low.

This plan is written against the *actual* corpus in `docs/extension-reference`:
- ~107 markdown files organized by category directories (`hooks/`, `skills/`, `settings/`, etc.).
- Consistent YAML frontmatter with fields like `id`, `topic`, `category`, `tags`, `requires`, `related_to`.
- Many documents use multiple `##` sections; some are long (200–300 lines) with tables and code fences.

---

## Motivation / Why change?

Current behavior (v1) in `packages/mcp-servers/extension-docs/src/chunker.ts`:
- Parse frontmatter for `{category, tags, topic}` and prepend a metadata header to returned chunk content.
- Decide between whole-file chunk vs split-at-H2 chunks, then merge small adjacent chunks.
- Fence-aware H2 splitting (good).

Main gaps for this corpus:
1. **Doc identity and relationships aren’t searchable enough.** The corpus frontmatter is high quality. Not using `topic`, `requires`, `related_to`, and `id` wastes signal.
2. **Chunk size bounds are not guaranteed after H2 splitting.** A single large H2 can produce an oversized chunk (especially with large tables or long code samples).
3. **H2-only segmentation isn’t robust to docs that use deeper headings.** Some docs can have long H2 sections with multiple H3 subsections.

Desired outcomes:
- Better recall for "navigation" queries (e.g. "what depends on hooks-overview?").
- Better precision for long reference sections (smaller, more focused chunks).
- Preserve determinism and speed (offline-only).

---

## Corpus Validation (2026-01-12)

Analysis of the actual corpus validates the plan assumptions:

### File Statistics

| Metric | Value |
|--------|-------|
| Total files | 107 |
| Category directories | 14 |
| Largest file (lines) | 307 (`skills-examples.md`) |
| Largest file (chars) | 7,791 (`skills-content-sections.md`) |
| Files > 150 lines | 8 |

### Frontmatter Field Coverage

| Field | Files | Coverage |
|-------|-------|----------|
| `id` | 107 | 100% |
| `topic` | 107 | 100% |
| `category` | 107 | 100% |
| `requires` | 91 | 85% |
| `related_to` | 98 | 92% |

### Critical Finding: Oversized H2 Section

**`hooks/hooks-exit-codes.md`** contains "## JSON Output (Advanced)" — a **149-line H2 section** that approaches MAX_CHUNK_LINES.

This section has **9 H3 subsections**, validating the H3 fallback strategy:
- `### Common JSON Fields`
- `### continue: false Behavior by Event`
- `### PreToolUse Decision Control`
- `### PermissionRequest Decision Control`
- `### PostToolUse Decision Control`
- `### UserPromptSubmit Decision Control`
- `### Stop/SubagentStop Decision Control`
- `### SessionStart Output`
- `### SessionEnd Decision Control`

### Table-Heavy Files

| File | Table Rows |
|------|------------|
| `settings-environment-variables.md` | 86 |
| `settings-schema.md` | 49 |
| `commands-builtin.md` | 47 |

Large tables are semantic units that shouldn't be split mid-row. See **Enhancement D** below.

---

## Design Summary

### A. Parse more frontmatter fields

Extend frontmatter parsing to include:
- `id: string`
- `topic: string`
- `requires: string[]`
- `related_to: string[]`

These fields are used in two ways:
1. **User-visible header (optional but recommended):** include `Topic` and `ID` in the metadata header added to chunk content.
2. **Search-only tokens:** include `requires` and `related_to` values in the chunk tokens (so searching for dependency relationships works even if not mentioned in body text).

### B. Add stable doc context to every chunk

Prepend a short doc header to every chunk content:
- `Topic: ...`
- `ID: ...`
- `Category: ...`
- `Tags: ...`

**Note:** Per Open Question 1 recommendation, `Requires` and `Related` are tokens-only (not in visible header). This keeps chunk content cleaner while still enabling relationship queries via token matching.

### C. Hierarchical, bounded splitting

Robust splitting strategy:
1. Split by H2 (`##`) outside code fences.
2. If an H2 chunk exceeds size limits, split that chunk by H3 (`###`) outside code fences.
3. If still too large, split by paragraphs (blank lines), outside code fences.
4. If still too large, hard split by character/line budget (last resort).

Add a small overlap (only for "forced splits" (H3/paragraph/hard), not for normal H2 boundaries):
- e.g. carry last `N` lines of previous piece (default `N=5`) into the next piece.

### D. Table-aware splitting (integrated into paragraph splitting)

**Motivation:** Corpus analysis found table-heavy files (`settings-environment-variables.md` has 86 table rows). Tables are semantic units that shouldn't be split mid-row. If a table appears in a long H2 section that gets paragraph-split, rows could be separated, producing nonsensical chunks.

**Approach:** Table awareness is **integrated directly into `splitByParagraphOutsideFences`** (see Section 2 below) rather than implemented as a preprocessing step. This avoids type mismatches and ensures tables are handled in the same pass as fence tracking and paragraph detection.

**Key behaviors:**
1. Consecutive table lines (starting with `|`) are accumulated as atomic blocks
2. Tables are never split at blank lines (unlike paragraphs)
3. Oversized tables exceeding `MAX_CHUNK_CHARS` are split at row boundaries with header preservation
4. The `splitOversizedTable` helper handles header row duplication

**Priority:** Included in v2 — while current corpus tables fit within limits, the 86-row table in `settings-environment-variables.md` (potentially 4,000-8,600 chars) could exceed limits as the corpus evolves. Header preservation ensures split tables remain readable.

**Test cases** (see Tests & Validation section below for full implementation):
- `splits oversized tables at row boundaries with header preservation`
- `keeps small tables atomic`
- `handles tables mixed with paragraphs`

---

## Concrete API/Type Changes (TypeScript)

### 1) Update `Frontmatter` types and parsing

**File:** `packages/mcp-servers/extension-docs/src/frontmatter.ts`

```ts
// src/frontmatter.ts
import { parse as parseYaml } from 'yaml';

export interface Frontmatter {
  id?: string;
  topic?: string;
  category?: string;
  tags?: string[];
  requires?: string[];
  related_to?: string[];
}

// Module-level warnings array (existing pattern in codebase)
const parseWarnings: { file: string; issue: string }[] = [];

export function getParseWarnings() { return [...parseWarnings]; }
export function clearParseWarnings() { parseWarnings.length = 0; }

function parseStringArrayField(
  yaml: Record<string, unknown>,
  filePath: string,
  fieldName: string,
): string[] | undefined {
  const value = yaml[fieldName];
  if (value == null) return undefined;

  if (Array.isArray(value)) {
    const out: string[] = [];
    for (const item of value) {
      if (typeof item === 'string') out.push(item);
      else {
        parseWarnings.push({
          file: filePath,
          issue: `Invalid ${fieldName} item type: expected string, got ${typeof item}`,
        });
      }
    }
    return out.length ? out : undefined;
  }

  if (typeof value === 'string') return [value];

  parseWarnings.push({
    file: filePath,
    issue: `Invalid ${fieldName} type: expected string or array, got ${typeof value}`,
  });
  return undefined;
}

export function parseFrontmatter(
  content: string,
  filePath: string,
): { frontmatter: Frontmatter; body: string } {
  const normalized = content.replace(/\r\n/g, '\n');
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) return { frontmatter: {}, body: normalized };

  try {
    const yamlRaw = parseYaml(match[1]);
    const yaml = (yamlRaw && typeof yamlRaw === 'object') ? (yamlRaw as Record<string, unknown>) : {};

    let id: string | undefined;
    if (typeof yaml.id === 'string') {
      id = yaml.id;
    } else if (yaml.id != null) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid id type: expected string, got ${typeof yaml.id}`,
      });
    }

    let topic: string | undefined;
    if (typeof yaml.topic === 'string') {
      topic = yaml.topic;
    } else if (yaml.topic != null) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid topic type: expected string, got ${typeof yaml.topic}`,
      });
    }

    // Existing: category/tags parsing (keep current warnings behavior)
    let category: string | undefined;
    if (typeof yaml.category === 'string') {
      category = yaml.category;
    } else if (yaml.category != null) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid category type: expected string, got ${typeof yaml.category}`,
      });
    }

    let tags: string[] | undefined;
    if (Array.isArray(yaml.tags)) {
      tags = yaml.tags.filter((t): t is string => {
        if (typeof t === 'string') return true;
        parseWarnings.push({
          file: filePath,
          issue: `Non-string tag value ignored: ${typeof t}`,
        });
        return false;
      });
    } else if (typeof yaml.tags === 'string') {
      tags = [yaml.tags];
    } else if (yaml.tags != null) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid tags type: expected string or array, got ${typeof yaml.tags}`,
      });
    }

    const requires = parseStringArrayField(yaml, filePath, 'requires');
    const related_to = parseStringArrayField(yaml, filePath, 'related_to');

    return {
      frontmatter: { id, topic, category, tags, requires, related_to },
      body: match[2],
    };
  } catch (err) {
    parseWarnings.push({
      file: filePath,
      issue: `Invalid YAML frontmatter: ${err instanceof Error ? err.message : 'unknown error'}`,
    });
    return { frontmatter: {}, body: content };
  }
}
```

**Rationale**
- `requires` / `related_to` are present in the corpus and directly support queries like “what depends on X” or “what’s related to Y”.
- Guarding `yamlRaw` to `object` prevents “yaml is scalar/array” issues from turning into noisy parse warnings.

### 2) Expand chunk token metadata to include relationships

**File:** `packages/mcp-servers/extension-docs/src/chunker.ts`

```ts
// src/chunker.ts (snippet)
function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const category = fm.category ?? derivedCategory;
  const tags = fm.tags ?? [];
  const requires = fm.requires ?? [];
  const related = fm.related_to ?? [];
  const id = fm.id ? [fm.id] : [];
  const topic = fm.topic ? [fm.topic] : [];

  // tokenize will split CamelCase and punctuation, so ids like "hooks-overview" or "PreToolUse"
  // contribute meaningful tokens.
  return [category, ...tags, ...requires, ...related, ...id, ...topic];
}

function createSplitChunk(...) {
  const derivedCategory = deriveCategory(file.path);
  const category = frontmatter.category ?? derivedCategory;
  const tags = frontmatter.tags ?? [];

  const metadataTerms = getMetadataTerms(frontmatter, derivedCategory).flatMap(tokenize);
  const tokens = [...tokenize(content), ...metadataTerms];

  return { ... };
}
```

**Rationale**
- Including `requires/related_to` as *tokens* means a query for `hooks-overview` can surface all pages that list it as a prerequisite even if body text never mentions it.
- Including `id/topic` as tokens improves “navigate by doc name” queries.

---

## Chunking v2: Bounded Hierarchical Splitting (Legit Code)

**File:** `packages/mcp-servers/extension-docs/src/chunker.ts`

This plan proposes extracting “split outside fences” into a reusable helper and adding a bounded splitter.

### 1) Fence-aware heading splitting helper

```ts
// src/chunker.ts (new helper snippet)
type HeadingLevel = 2 | 3;

function splitByHeadingOutsideFences(
  content: string,
  level: HeadingLevel,
): Array<{ headingLine?: string; body: string }> {
  const headingRe = level === 2 ? /^##\s/ : /^###\s/;

  const lines = content.split('\n');
  const parts: Array<{ headingLine?: string; bodyLines: string[] }> = [];

  let inFence = false;
  let fencePattern = '';
  let current: { headingLine?: string; bodyLines: string[] } = { bodyLines: [] };

  for (const line of lines) {
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

    if (!inFence && headingRe.test(line)) {
      if (current.bodyLines.length) parts.push(current);
      current = { headingLine: line, bodyLines: [line] };
      continue;
    }

    current.bodyLines.push(line);
  }

  if (current.bodyLines.length) parts.push(current);

  return parts.map((p) => ({ headingLine: p.headingLine, body: p.bodyLines.join('\n') }));
}
```

**Rationale**
- Same fence rules as v1 (0–3 spaces), applied to H3 as well.
- Keeps section heading line inside the chunk content (preserves readability).

### 2) Paragraph splitting outside fences (with integrated table awareness)

```ts
function isTableLine(line: string): boolean {
  return line.trimStart().startsWith('|');
}

function splitByParagraphOutsideFences(content: string): string[] {
  const lines = content.split('\n');
  const blocks: string[] = [];

  let inFence = false;
  let fencePattern = '';
  let inTable = false;
  let current: string[] = [];

  const flush = (wasTable: boolean) => {
    const text = current.join('\n').trimEnd();
    if (text.length) {
      // If this was a table block exceeding limits, split at row boundaries
      if (wasTable && text.length > MAX_CHUNK_CHARS) {
        blocks.push(...splitOversizedTable(current));
      } else {
        blocks.push(text);
      }
    }
    current = [];
  };

  for (const line of lines) {
    // Fence tracking (unchanged from v1)
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

    // Compute line classification (outside fence only)
    const lineIsTable = !inFence && isTableLine(line);
    const lineIsBlank = !inFence && line.trim() === '';

    // Transition: table → non-table or non-table → table (flush on mode change)
    // Skip blank lines in transition check — they don't change the mode
    if (!inFence && !lineIsBlank && inTable !== lineIsTable && current.length) {
      flush(inTable);
      inTable = lineIsTable;
    }

    // Blank line outside fence: flush paragraph (but NOT table — tables stay atomic)
    if (lineIsBlank && !inTable) {
      current.push(line);
      flush(false);
      continue;
    }

    current.push(line);
    // Update inTable state based on current line (only when line is a table line)
    if (lineIsTable) inTable = true;
  }

  flush(inTable);
  return blocks;
}

/**
 * Splits an oversized table at row boundaries, preserving header in each chunk.
 * Header = first 2 lines (header row + separator row like |---|---|)
 */
function splitOversizedTable(tableLines: string[]): string[] {
  const headerLines = tableLines.slice(0, 2);
  const dataRows = tableLines.slice(2);
  const result: string[] = [];

  let currentChunk = [...headerLines];
  for (const row of dataRows) {
    const projected = [...currentChunk, row].join('\n');

    if (projected.length > MAX_CHUNK_CHARS && currentChunk.length > 2) {
      result.push(currentChunk.join('\n'));
      currentChunk = [...headerLines, row]; // New chunk: header + this row
    } else {
      currentChunk.push(row);
    }
  }

  if (currentChunk.length > 2) {
    result.push(currentChunk.join('\n'));
  }

  return result;
}
```

**Rationale**
- For long sections with no H3, paragraph splitting provides semantic boundaries.
- Fence-aware ensures code blocks are not fragmented by blank lines inside code fences.
- **Table-aware** ensures tables are kept atomic; oversized tables split at row boundaries with header preservation.
- Single-pass design avoids type mismatches from preprocessing steps.

### 3) Enforce max chunk bounds with minimal overlap

```ts
const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;
const OVERLAP_LINES_FOR_FORCED_SPLITS = 5;

function withinLimits(text: string): boolean {
  if (text.length > MAX_CHUNK_CHARS) return false;
  const lines = text.split('\n').length;
  return lines <= MAX_CHUNK_LINES;
}

function takeTailLines(text: string, n: number): string {
  if (n <= 0) return '';
  const lines = text.split('\n');
  return lines.slice(Math.max(0, lines.length - n)).join('\n');
}

function hardSplitWithOverlap(text: string): string[] {
  const out: string[] = [];
  let remaining = text;
  let prev = '';

  // Reserve space for overlap in budget to ensure combined chunk stays within limits.
  // Budget applies to the NEW content being added, so when prev is prepended,
  // the total (prev + new) must still fit within MAX_CHUNK_CHARS.
  // 200 chars/line is conservative for worst case (wide tables).
  // Typical prose averages 80-100 chars/line, so this over-reserves
  // but guarantees the post-condition assertion never fails.
  const overlapBudget = OVERLAP_LINES_FOR_FORCED_SPLITS * 200;
  const effectiveBudget = MAX_CHUNK_CHARS - overlapBudget;

  // Prefer splitting on newline near budget to avoid mid-line splits
  while (!withinLimits(remaining)) {
    // Use reduced budget to leave room for overlap prefix
    const budget = Math.min(effectiveBudget, remaining.length);
    const candidate = remaining.slice(0, budget);
    const cut = candidate.lastIndexOf('\n');
    const head = (cut > 0 ? remaining.slice(0, cut) : candidate).trimEnd();
    if (!head) break;

    // First chunk has no overlap prefix; subsequent chunks include prev
    const withOverlap = prev ? `${prev}\n${head}` : head;
    out.push(withOverlap);

    remaining = remaining.slice(head.length).replace(/^\n+/, '');
    prev = takeTailLines(head, OVERLAP_LINES_FOR_FORCED_SPLITS);
  }

  if (remaining.trim().length) {
    const tail = prev ? `${prev}\n${remaining}` : remaining;
    out.push(tail);
  }

  // Post-condition: all chunks must be within bounds
  // This is a defensive assertion — if it fails, there's a bug in the budget math
  for (const chunk of out) {
    if (!withinLimits(chunk)) {
      throw new Error(
        `BUG: hardSplitWithOverlap produced oversized chunk: ` +
        `${chunk.length} chars, ${chunk.split('\n').length} lines`
      );
    }
  }

  return out;
}
```

**Rationale**
- Only uses overlap on forced splits (hard splitting), which minimizes duplication while improving boundary recall.
- Hard split tries to cut on newline, avoiding mid-line fragmentation.
- **Budget reserves space for overlap** so combined chunks (overlap + content) stay within `MAX_CHUNK_CHARS`.

**Safety margin justification (200 chars/line):**

| Line Type | Typical Width | Max Width |
|-----------|---------------|-----------|
| Prose | 80-100 chars | ~120 chars (long sentences) |
| Code | 80-120 chars | ~150 chars (wide expressions) |
| Tables | 60-150 chars | ~200 chars (multi-column) |

The 200 chars/line budget covers all observed corpus content. If a line exceeds 200 chars:
1. The post-condition assertion catches it immediately
2. The error message includes exact dimensions for debugging
3. The fix is to increase the budget or add line-width capping

**Future consideration:** If the corpus grows to include very wide tables (>200 chars), add a `MAX_LINE_WIDTH` constant and truncate overlap lines that exceed it.

### 4) Paragraph accumulation helper (extracted for clarity)

```ts
/**
 * Accumulates paragraph blocks into size-bounded chunks with overlap on forced splits.
 * Single-responsibility helper that handles iteration, size checking, and overlap management.
 */
function accumulateParagraphsWithOverlap(
  paragraphs: string[],
  heading: string | undefined,
): BoundedPart[] {
  const results: BoundedPart[] = [];
  let buffer = '';
  let prevTail = '';
  let chunkIndex = 1;  // 1-based: first chunk = 1, second = 2, etc.

  const flush = (content: string) => {
    if (!content.trim().length) return;
    const withOverlap = prevTail ? `${prevTail}\n${content}` : content;
    // splitIndex uses 1-based indexing:
    // - 1 → first chunk, no suffix (e.g., file#section)
    // - 2+ → subsequent chunks get suffix (e.g., file#section-2, file#section-3)
    results.push({ heading, content: withOverlap, splitIndex: chunkIndex, splitType: 'paragraph' });
    prevTail = takeTailLines(content, OVERLAP_LINES_FOR_FORCED_SPLITS);
    chunkIndex++;
  };

  for (const para of paragraphs) {
    const combined = buffer ? `${buffer}\n\n${para}` : para;

    if (withinLimits(combined)) {
      buffer = combined;
      continue;
    }

    // Current buffer is as full as it can get — flush it
    if (buffer.trim().length) {
      flush(buffer);
      buffer = para;
      continue;
    }

    // Single paragraph too big — hard split it
    const pieces = hardSplitWithOverlap(para);
    for (const piece of pieces) {
      results.push({ heading, content: piece, splitIndex: chunkIndex, splitType: 'hard' });
      chunkIndex++;  // 1, 2, 3, ... (1-based)
    }
  }

  // Flush remaining buffer
  if (buffer.trim().length) {
    flush(buffer);
  }

  return results;
}
```

**Rationale**
- Extracts the complex paragraph accumulation logic from `splitBounded` into a focused helper
- Single responsibility: iteration, size checking, and overlap management
- Easier to test in isolation and reason about

### 5) Putting it together: bounded section chunking

```ts
interface BoundedPart {
  heading?: string;
  content: string;
  splitIndex?: number;  // Set for forced splits (paragraph/hard) to prevent duplicate chunk IDs
  splitType?: 'h2' | 'h3' | 'paragraph' | 'hard';  // For debug logging during rollout
}

function splitBounded(content: string): BoundedPart[] {
  // 1) Start at H2 (same as v1, but we guarantee bounds)
  const h2Parts = splitByHeadingOutsideFences(content, 2);
  const results: BoundedPart[] = [];

  for (const part of h2Parts) {
    if (withinLimits(part.body)) {
      results.push({ heading: part.headingLine, content: part.body, splitType: 'h2' });
      continue;
    }

    // 2) Too big -> try H3
    const h3Parts = splitByHeadingOutsideFences(part.body, 3);
    if (h3Parts.length > 1) {
      for (const h3 of h3Parts) {
        if (withinLimits(h3.body)) {
          results.push({ heading: h3.headingLine ?? part.headingLine, content: h3.body, splitType: 'h3' });
        } else {
          // 3) Still too big -> use paragraph accumulation helper
          const paras = splitByParagraphOutsideFences(h3.body);
          if (paras.length > 1) {
            const accumulated = accumulateParagraphsWithOverlap(paras, h3.headingLine ?? part.headingLine);
            results.push(...accumulated);
          } else {
            // 4) Last resort -> hard split (1-based splitIndex for unique IDs)
            const heading = h3.headingLine ?? part.headingLine;
            const pieces = hardSplitWithOverlap(h3.body);
            for (let i = 0; i < pieces.length; i++) {
              results.push({ heading, content: pieces[i], splitIndex: i + 1, splitType: 'hard' });
            }
          }
        }
      }
      continue;
    }

    // No H3 structure available; use extracted helper for paragraph accumulation
    const paras = splitByParagraphOutsideFences(part.body);
    if (paras.length > 1) {
      const accumulated = accumulateParagraphsWithOverlap(paras, part.headingLine);
      results.push(...accumulated);
      continue;
    }

    // Direct hard split (no paragraph structure, 1-based splitIndex)
    const pieces = hardSplitWithOverlap(part.body);
    for (let i = 0; i < pieces.length; i++) {
      results.push({ heading: part.headingLine, content: pieces[i], splitIndex: i + 1, splitType: 'hard' });
    }
  }

  return results;
}
```

**Rationale**
- **Guarantees size bounds** for all chunks, improving retrieval precision.
- Uses structure when possible, falls back gracefully.
- Overlap is used sparingly and only when structural boundaries don't suffice.
- **`splitIndex` prevents duplicate chunk IDs** when forced splits produce multiple chunks from the same heading.

### 5) Update `generateChunkId` to support split index

**File:** `packages/mcp-servers/extension-docs/src/chunk-helpers.ts`

```ts
export function generateChunkId(
  file: MarkdownFile,
  heading?: string,
  splitIndex?: number,
): string {
  const fileSlug = slugify(file.path);
  if (!heading) return fileSlug;

  const headingSlug = slugify(heading);
  // Append suffix for forced splits using 1-based indexing:
  // - undefined or 1 → no suffix (e.g., file#section)
  // - 2+ → suffix (e.g., file#section-2, file#section-3)
  const suffix = splitIndex != null && splitIndex > 1 ? `-${splitIndex}` : '';
  return `${fileSlug}#${headingSlug}${suffix}`;
}
```

**Rationale**
- First chunk from a heading keeps the clean ID (`#section-name`)
- Subsequent forced-split chunks get numbered suffixes (`#section-name-2`, `#section-name-3`)
- H2/H3 structural splits don't set `splitIndex`, so they get unique IDs from their own headings

**`splitIndex` value semantics (simplified):**

The parameter uses **1-based indexing** with a simple rule:

| Value | Meaning | ID Suffix |
|-------|---------|-----------|
| `undefined` | Not a forced split (H2/H3 boundary) | None |
| `1` | First chunk from forced split | None |
| `2+` | Subsequent chunks from forced split | `-2`, `-3`, etc. |

**Why 1-based?** Zero-based indexing creates ambiguity between "not set" and "first chunk". With 1-based indexing:
- `undefined` = structural split (unique heading provides unique ID)
- `1` = first forced-split chunk (no suffix needed)
- `2+` = subsequent chunks (suffix required for uniqueness)

**Implementation pattern:**

```ts
// In accumulateParagraphsWithOverlap:
let chunkIndex = 1;  // Start at 1, not 0

const flush = (content: string) => {
  results.push({ heading, content, splitIndex: chunkIndex, splitType: 'paragraph' });
  chunkIndex++;  // Next chunk gets 2, 3, etc.
};

// In generateChunkId:
const suffix = splitIndex != null && splitIndex > 1 ? `-${splitIndex}` : '';
//                                            ^^^ Changed from > 0 to > 1
```

This eliminates the confusing case where both `undefined` and `0` behave identically.

### 6) Integration: Replace `splitAtH2` in `chunkFile`

```ts
// In chunkFile(), replace the existing split logic:
export function chunkFile(file: MarkdownFile): Chunk[] {
  const { frontmatter, body } = parseFrontmatter(file.content, file.path);
  const metadataHeader = formatMetadataHeader(frontmatter);
  const preparedContent = metadataHeader + body;

  if (isSmallEnoughForWholeFile(preparedContent)) {
    return [createWholeFileChunk(file, preparedContent, frontmatter)];
  }

  // v2: Use bounded splitting instead of splitAtH2
  const boundedParts = splitBounded(preparedContent);
  const rawChunks = boundedParts.map((part) =>
    createSplitChunk(file, part.content, part.heading, part.splitIndex, frontmatter)
  );

  return mergeSmallChunks(rawChunks);
}
```

Update `createSplitChunk` signature to accept `splitIndex`:

```ts
function createSplitChunk(
  file: MarkdownFile,
  content: string,
  heading: string | undefined,
  splitIndex: number | undefined,
  frontmatter: Frontmatter,
): Chunk {
  const category = frontmatter.category ?? deriveCategory(file.path);
  const tags = frontmatter.tags ?? [];

  const metadataTerms = getMetadataTerms(frontmatter, category).flatMap(tokenize);
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
```

---

## Metadata Header v2 (Legit Code)

**File:** `packages/mcp-servers/extension-docs/src/frontmatter.ts`

```ts
export function formatMetadataHeader(fm: Frontmatter): string {
  const lines: string[] = [];
  if (fm.topic) lines.push(`Topic: ${fm.topic}`);
  if (fm.id) lines.push(`ID: ${fm.id}`);
  if (fm.category) lines.push(`Category: ${fm.category}`);
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`);
  // Note: requires/related_to are tokens-only per Open Question 1 recommendation
  return lines.length ? lines.join('\n') + '\n\n' : '';
}
```

**Rationale**
- Makes chunks self-identifying and improves user-facing results.
- For this corpus, `topic` is often the clearest human label for a page.
- `requires`/`related_to` are tokens-only (not in header) to keep content cleaner while still enabling relationship queries.

---

## Tests & Validation (Concrete)

### Update / add tests

**File:** `packages/mcp-servers/extension-docs/tests/frontmatter.test.ts`
- Add cases for `requires` and `related_to` as:
  - string
  - array of strings
  - mixed arrays (warn + filter)
  - invalid types (warn)

**File:** `packages/mcp-servers/extension-docs/tests/chunker.test.ts`
- Add a test that a large single-H2 section is **split further** to satisfy `MAX_CHUNK_CHARS` / `MAX_CHUNK_LINES`.
- Add a test that `requires/related_to` terms appear in `chunk.tokens` even if not in the body.

Example new test (real TS):

```ts
import { describe, it, expect } from 'vitest';
import { chunkFile } from '../src/chunker.js';
import { tokenize } from '../src/tokenizer.js';

describe('metadata token inclusion', () => {
  it('includes requires/related_to in tokens even when not in body', () => {
    const content = [
      '---',
      'category: hooks',
      'requires: [hooks-overview]',
      'related_to: [hooks-events]',
      '---',
      '# Title',
      '## Section',
      'Body does not mention prerequisites or related pages.',
      ...Array(150).fill('pad'),
    ].join('\n');

    const chunks = chunkFile({ path: 'hooks/x.md', content });
    const tokens = chunks[0].tokens;

    // Verify tokenize behavior first (documents our assumption)
    const overviewTokens = tokenize('hooks-overview');
    expect(overviewTokens).toContain('hooks');
    expect(overviewTokens).toContain('overview');

    // Now verify chunk tokens include the relationship metadata
    expect(tokens).toContain('hooks');
    expect(tokens).toContain('overview');
    expect(tokens).toContain('events');

    // Verify these terms do NOT appear in the body (proving they came from metadata)
    expect(content).not.toContain('overview');
    expect(content).not.toContain('events');
  });

  it('handles requires/related_to as single strings', () => {
    const content = [
      '---',
      'requires: single-prereq',
      'related_to: single-related',
      '---',
      '# Title',
      'Body content.',
    ].join('\n');

    const chunks = chunkFile({ path: 'test/single.md', content });
    const tokens = chunks[0].tokens;

    expect(tokens).toContain('single');
    expect(tokens).toContain('prereq');
    expect(tokens).toContain('related');
  });
});

describe('hierarchical splitting', () => {
  it('splits oversized H2 at H3 boundaries when available', () => {
    // Simulate the hooks-exit-codes.md scenario: 149-line H2 with 9 H3 subsections
    const h3Sections = Array.from({ length: 9 }, (_, i) =>
      `### Subsection ${i + 1}\n${Array(15).fill(`Content line ${i}`).join('\n')}`
    ).join('\n\n');

    const content = [
      '---',
      'category: hooks',
      '---',
      '# Title',
      '## Oversized Section',
      h3Sections,
    ].join('\n');

    const file: MarkdownFile = { path: 'hooks/oversized.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks (one per H3 or merged adjacent small H3s)
    expect(chunks.length).toBeGreaterThan(1);

    // Each chunk should reference an H3 heading (or the parent H2 for preamble)
    const h3Chunks = chunks.filter(c => c.heading?.startsWith('###'));
    expect(h3Chunks.length).toBeGreaterThan(0);

    // All chunks within bounds
    for (const chunk of chunks) {
      expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      expect(chunk.content.split('\n').length).toBeLessThanOrEqual(MAX_CHUNK_LINES);
    }
  });

  it('falls back to paragraph splitting when H3 unavailable', () => {
    // Large H2 section with no H3 structure, just paragraphs
    const paragraphs = Array.from({ length: 20 }, (_, i) =>
      Array(10).fill(`Paragraph ${i} content`).join(' ')
    ).join('\n\n');

    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Large Section Without H3',
      paragraphs,
    ].join('\n');

    const file: MarkdownFile = { path: 'test/no-h3.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks via paragraph splitting
    expect(chunks.length).toBeGreaterThan(1);

    // All share the same H2 heading
    for (const chunk of chunks) {
      expect(chunk.heading).toContain('## Large Section');
    }
  });
});

describe('table-aware splitting', () => {
  it('splits oversized tables at row boundaries with header preservation', () => {
    // Create a table that exceeds MAX_CHUNK_CHARS
    const header = '| Column A | Column B | Column C |';
    const separator = '|----------|----------|----------|';
    const row = '| data-a   | data-b   | data-c   |';
    const tableRows = Array(200).fill(row).join('\n'); // ~8000+ chars

    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Table Section',
      header,
      separator,
      tableRows,
    ].join('\n');

    const file: MarkdownFile = { path: 'test/big-table.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks due to oversized table
    expect(chunks.length).toBeGreaterThan(1);

    // Each chunk should start with the table header (after metadata)
    for (const chunk of chunks) {
      expect(chunk.content).toContain(header);
      expect(chunk.content).toContain(separator);
    }

    // Each chunk within size limit
    for (const chunk of chunks) {
      expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
    }
  });

  it('keeps small tables atomic', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Small Table',
      '| A | B |',
      '|---|---|',
      '| 1 | 2 |',
      '| 3 | 4 |',
      '',
      'Paragraph after table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/small-table.md', content };
    const chunks = chunkFile(file);

    // Small file should be one chunk
    expect(chunks.length).toBe(1);
    // Table should be intact (all rows present)
    expect(chunks[0].content).toContain('| 1 | 2 |');
    expect(chunks[0].content).toContain('| 3 | 4 |');
  });

  it('handles tables mixed with paragraphs', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Mixed Content',
      'Paragraph before table.',
      '',
      '| Col1 | Col2 |',
      '|------|------|',
      '| a    | b    |',
      '',
      'Paragraph after table.',
    ].join('\n');

    const file: MarkdownFile = { path: 'test/mixed.md', content };
    const chunks = chunkFile(file);

    // Content should preserve table integrity
    const content_str = chunks.map(c => c.content).join('');
    expect(content_str).toContain('| Col1 | Col2 |');
    expect(content_str).toContain('| a    | b    |');
  });

  // Edge cases for table+fence interaction
  it('does not treat pipe-lines inside code fence as table', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Code Example',
      '```bash',
      'echo "| Not | A | Table |"',
      'cat file | grep pattern | head',
      '```',
      '',
      'Paragraph after code.',
      ...Array(150).fill('padding'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/fence-pipe.md', content };
    const chunks = chunkFile(file);

    // Code block should stay intact (not split as "table rows")
    const codeChunk = chunks.find(c => c.content.includes('```bash'));
    expect(codeChunk?.content).toContain('echo "| Not | A | Table |"');
    expect(codeChunk?.content).toContain('cat file | grep pattern | head');
  });

  it('handles table immediately after code fence', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Section',
      '```json',
      '{"key": "value"}',
      '```',
      '| Col1 | Col2 |',  // Table immediately after fence (no blank line)
      '|------|------|',
      '| a    | b    |',
      '',
      ...Array(150).fill('padding'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/fence-then-table.md', content };
    const chunks = chunkFile(file);

    // Both code and table should be preserved
    const content_str = chunks.map(c => c.content).join('');
    expect(content_str).toContain('{"key": "value"}');
    expect(content_str).toContain('| Col1 | Col2 |');
    expect(content_str).toContain('| a    | b    |');
  });

  it('handles consecutive tables separated by blank line', () => {
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## Two Tables',
      '| Table1 |',
      '|--------|',
      '| row1   |',
      '',  // Blank line between tables
      '| Table2 |',
      '|--------|',
      '| row2   |',
      '',
      ...Array(150).fill('padding'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/consecutive-tables.md', content };
    const chunks = chunkFile(file);

    // Both tables should be preserved (may be in same or different chunks)
    const content_str = chunks.map(c => c.content).join('');
    expect(content_str).toContain('| Table1 |');
    expect(content_str).toContain('| row1   |');
    expect(content_str).toContain('| Table2 |');
    expect(content_str).toContain('| row2   |');
  });

  it('handles table inside list item (indented pipe)', () => {
    // Tables in list items have leading spaces — should still be detected
    const content = [
      '---',
      'category: test',
      '---',
      '# Title',
      '## List with Table',
      '- Item with table:',
      '  | A | B |',
      '  |---|---|',
      '  | 1 | 2 |',
      '',
      ...Array(150).fill('padding'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/list-table.md', content };
    const chunks = chunkFile(file);

    // Indented table should be preserved intact
    const content_str = chunks.map(c => c.content).join('');
    expect(content_str).toContain('  | A | B |');
    expect(content_str).toContain('  | 1 | 2 |');
  });
});
```

### Run validation commands

From `packages/mcp-servers/extension-docs`:
- `npm test`
- `npm run build`

Optionally (from repo root if configured):
- `npm -w @claude-tools/extension-docs test`

### Corpus validation script (recommended)

Add a test that runs the chunker against the full corpus and reports statistics:

```ts
// tests/corpus-validation.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile } from '../src/chunker.js';
import { readdirSync, readFileSync, statSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

// Use import.meta.url for reliable path resolution in ESM
// Path: tests/ → extension-docs/ → mcp-servers/ → packages/ → repo-root → docs/
const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS_PATH = process.env.DOCS_PATH ?? resolve(__dirname, '../../../../docs/extension-reference');

function* walkMarkdownFiles(dir: string): Generator<string> {
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      yield* walkMarkdownFiles(fullPath);
    } else if (entry.endsWith('.md')) {
      yield fullPath;
    }
  }
}

describe('corpus validation', () => {
  it('all chunks within size bounds', () => {
    const stats = {
      totalFiles: 0,
      totalChunks: 0,
      maxChunkLines: 0,
      maxChunkChars: 0,
    };
    // Note: To track h3Fallbacks/paragraphFallbacks/hardSplits, the chunker
    // would need to expose split-type metadata on chunks or return stats.

    for (const filePath of walkMarkdownFiles(DOCS_PATH)) {
      const content = readFileSync(filePath, 'utf-8');
      const chunks = chunkFile({ path: filePath, content });

      stats.totalFiles++;
      stats.totalChunks += chunks.length;

      for (const chunk of chunks) {
        const lines = chunk.content.split('\n').length;
        const chars = chunk.content.length;
        stats.maxChunkLines = Math.max(stats.maxChunkLines, lines);
        stats.maxChunkChars = Math.max(stats.maxChunkChars, chars);

        expect(lines).toBeLessThanOrEqual(150);
        expect(chars).toBeLessThanOrEqual(8000);
      }
    }

    console.log('Corpus stats:', stats);
  });
});
```

This provides ongoing validation as the corpus grows and helps identify edge cases.

---

## Implementation Notes

### Implementation Sequence (Required Order)

**Important:** Extract `FenceTracker` *before* implementing the new splitting functions. This prevents introducing a fourth copy of the fence detection logic.

| Step | Action | Risk |
|------|--------|------|
| 1 | Extract `FenceTracker` class | Low — refactor only |
| 2 | Extend `Frontmatter` interface + parsing | Low — additive |
| 3 | Add relationship tokens to `getMetadataTerms` | Low — additive |
| 4 | Implement `splitBounded` + helpers using `FenceTracker` | Medium — behavioral |
| 5 | Add corpus validation test | Low — test only |
| 6 | Roll out and monitor | — |

### Refactoring: Extract fence detection to shared helper

The fence detection logic is duplicated in `splitByHeadingOutsideFences`, `splitByParagraphOutsideFences`, and the existing `splitAtH2`. Extract to a reusable helper:

```ts
// src/fence-tracker.ts
/**
 * Tracks code fence state while iterating through markdown lines.
 * CommonMark-compliant: 0-3 leading spaces, 3+ backticks or tildes.
 *
 * Usage:
 *   const fence = new FenceTracker();
 *   for (const line of lines) {
 *     const inFence = fence.processLine(line);
 *     if (!inFence && isHeading(line)) { ... }
 *   }
 */
export class FenceTracker {
  private inFence = false;
  private fencePattern = '';

  /**
   * Process a line and update fence state.
   * @returns true if currently inside a fence AFTER processing this line
   */
  processLine(line: string): boolean {
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!this.inFence) {
        this.inFence = true;
        this.fencePattern = fence[2];
      } else if (line.match(new RegExp(`^ {0,3}${this.fencePattern[0]}{${this.fencePattern.length},}\\s*$`))) {
        this.inFence = false;
        this.fencePattern = '';
      }
    }
    return this.inFence;
  }

  /** Check if currently inside a fence without advancing state */
  get isInFence(): boolean {
    return this.inFence;
  }

  /** Reset to initial state */
  reset(): void {
    this.inFence = false;
    this.fencePattern = '';
  }
}
```

Then update splitting functions to use it:

```ts
function splitByHeadingOutsideFences(content: string, level: HeadingLevel) {
  const fence = new FenceTracker();
  // ... use fence.processLine(line) instead of inline logic
}
```

### Design Decision: Empty H2/H3 Sections

When an H2 section is empty (just the heading line), `splitByHeadingOutsideFences` returns `{ headingLine: '## Foo', body: '## Foo' }`. This causes the heading to appear twice in output.

**Decision:** Skip empty sections entirely in `splitByHeadingOutsideFences`:

```ts
// In splitByHeadingOutsideFences, when building return value:
const mapped = parts.map((p) => {
  const bodyWithoutHeading = p.bodyLines.slice(1).join('\n').trim();
  return {
    headingLine: p.headingLine,
    body: p.bodyLines.join('\n'),
    isEmpty: !bodyWithoutHeading.length,
  };
});

// Log filtered sections during rollout for visibility
const emptySections = mapped.filter((p) => p.isEmpty);
if (emptySections.length > 0 && process.env.CHUNKER_DEBUG) {
  console.error(
    `[chunker] Filtered ${emptySections.length} empty section(s): ` +
    emptySections.map((p) => p.headingLine).join(', ')
  );
}

return mapped.filter((p) => !p.isEmpty);
```

**Rollout observability:** Set `CHUNKER_DEBUG=1` during rollout to see which sections are filtered. This helps identify corpus issues (e.g., accidentally empty sections that should have content) without adding noise in production.

**Rationale — empty sections are intentionally filtered out:**

1. **No searchable content** — an empty section contributes no tokens to the search index
2. **ID collision risk** — empty sections would create near-duplicate chunk IDs
3. **Semantic signal** — in this corpus, empty headings indicate placeholders or navigation anchors, not content
4. **Filtering early** prevents downstream logic from processing degenerate cases

**Alternative considered but rejected:** Appending empty section headings to the previous chunk's content. This was rejected because:
- It complicates the chunking logic
- Empty sections provide no search value
- The corpus doesn't use empty sections for meaningful navigation

If preserving empty section headings becomes necessary in the future, they could be appended to the previous chunk's content as a follow-up enhancement

---

## Rollout / Backwards Compatibility

Impact on external API:
- No changes to tool names or schemas (`search_extension_docs`, `reload_extension_docs` unchanged).
- Search results may change (expected); chunk IDs may change if you incorporate `topic/id` into the chunk ID. **Recommendation:** keep the current chunk ID scheme (`fileSlug[#headingSlug]`) for stability.

Migration strategy:
1. Land frontmatter parse extensions + token metadata additions (low risk).
2. Land bounded splitting changes (behavioral but internal; covered by tests).
3. Optionally add instrumentation logs for chunk count and largest chunk stats (stderr only).

### Metadata Header Format Change

The metadata header prepended to chunks changes format:

**v1 (current):**
```
Category: hooks
Tags: events, pretooluse
Topic: Hook Event Types
```

**v2 (proposed):**
```
Topic: Hook Event Types
ID: hooks-events
Category: hooks
Tags: events, pretooluse
```

**Changes:**
1. **Order:** Topic moved to first position (most human-readable identifier)
2. **Addition:** ID field added (enables exact document navigation)
3. **Removed from header:** `requires`, `related_to` (tokens-only for cleaner display)

**Impact:** Any tooling that parses chunk content headers by position may need updates. BM25 search is unaffected (tokenization ignores header structure).

---

## Rollback Instructions

### Detecting Problems

Monitor for these symptoms after deployment:

| Symptom | Likely Cause | Severity |
|---------|--------------|----------|
| `search_extension_docs` returns empty results | Index corruption or chunker crash | **Critical** |
| Search results missing expected docs | Frontmatter parsing regression | High |
| Chunks exceeding size limits in logs | `splitBounded` logic error | Medium |
| Slower index build times (>2x baseline) | Inefficient splitting loops | Low |

### Full Rollback (Git)

If critical issues occur, revert all changes:

```bash
# From packages/mcp-servers/extension-docs
git log --oneline -10  # Find the commit before v2 changes

# Option A: Revert specific commits (preserves history)
git revert <commit-hash>..HEAD --no-commit
git commit -m "revert: rollback chunking v2 due to [issue]"

# Option B: Hard reset (if not yet pushed)
git reset --hard <pre-v2-commit>

# Rebuild and verify
npm run build
npm test
```

### Partial Rollback (Phase-Specific)

Since implementation is phased, you can rollback selectively:

| Phase | Rollback Action | Files Affected |
|-------|-----------------|----------------|
| **Phase 1** (frontmatter) | Revert `Frontmatter` interface additions, remove `parseStringArrayField` | `frontmatter.ts` |
| **Phase 2** (tokens) | Revert `getMetadataTerms`, restore original `createSplitChunk` | `chunker.ts` |
| **Phase 3** (splitting) | Replace `splitBounded` call with original `splitAtH2` | `chunker.ts` |

**Phase 3 quick rollback** (most likely needed):

```ts
// In chunkFile(), revert to v1 splitting:
// Change this:
const boundedParts = splitBounded(preparedContent);
const rawChunks = boundedParts.map((part) =>
  createSplitChunk(file, part.content, part.heading, frontmatter)
);

// Back to this:
const rawChunks = splitAtH2(file, preparedContent, frontmatter);
```

### What to Preserve During Rollback

Even during rollback, **keep these if they're working**:
- New frontmatter fields in `Frontmatter` interface (additive, no breaking change)
- Additional token metadata (improves search without changing behavior)
- Corpus validation test (useful regardless of chunking strategy)

### Post-Rollback Verification

```bash
# 1. Rebuild
npm run build

# 2. Run tests
npm test

# 3. Verify corpus still indexes
DOCS_PATH=../../../docs/extension-reference npm test -- corpus-validation

# 4. Manual smoke test
claude  # Start new session
# Run: search_extension_docs with query "hooks PreToolUse"
# Verify results return expected documents
```

### Incident Documentation

If rollback is needed, document:
1. What broke (specific error or behavior)
2. Which phase introduced the issue
3. Root cause (if known)
4. What was rolled back vs preserved

Add findings to this plan or create a linked incident report.

---

## Open Questions (decide before implementation)

| Question | Recommendation | Rationale |
|----------|----------------|-----------|
| 1. Should `Requires/Related` appear in chunk content, or be tokens-only? | **Tokens-only** | Keeps chunk content cleaner; relationship queries work via token matching. Users see relationships via frontmatter if needed. |
| 2. Should `topic` be included in content header always? | **Yes, always** | Consistency > minor duplication. The header provides machine-readable context regardless of body content. |
| 3. Are there directories under `DOCS_PATH` to ignore? | **No, for now** | Current corpus is clean (107 files, all intended for indexing). Document that everything under `DOCS_PATH` is indexed; add exclusion patterns later if needed. |

---

## Technical Review Findings (2026-01-12)

### Resolved Questions

#### Q1: Does `mergeSmallChunks` need awareness of new split types?

**Answer: No changes needed.**

Analysis of `chunker.ts:120-144` shows `mergeSmallChunks` is purely size-based:
- Accumulates adjacent chunks while they fit within `MAX_CHUNK_LINES` and `MAX_CHUNK_CHARS`
- Tracks `merged_headings` when combining
- Doesn't care *how* chunks were created

With v2, more smaller chunks from H3/paragraph/hard splits will be produced. `mergeSmallChunks` will recombine them appropriately — overly-fragmented sections get reassembled automatically.

#### Q2: Chunk ID stability for forced splits

**Answer: Fix required — duplicate IDs possible.**

Current ID generation (`chunk-helpers.ts:11-16`):
```ts
const headingSlug = slugify(heading);
return `${fileSlug}#${headingSlug}`;
```

In v2's `splitBounded`:
- **H3 splits**: Each gets its own H3 heading → unique IDs ✓
- **Paragraph/hard splits**: All inherit the parent H2 → **duplicate IDs** ✗

Example: If "## JSON Output (Advanced)" (149 lines) gets split via paragraph/hard fallback, multiple chunks would all have ID `hooks-exit-codes#json-output-advanced`.

**Required fix**: Add sequence suffix for forced splits:

```ts
// In splitBounded, track split index per parent heading
function splitBounded(content: string): Array<{ heading?: string; content: string; splitIndex?: number }> {
  // When creating forced-split chunks, increment splitIndex
}

// In generateChunkId
export function generateChunkId(file: MarkdownFile, heading?: string, splitIndex?: number): string {
  const fileSlug = slugify(file.path);
  if (!heading) return fileSlug;

  const headingSlug = slugify(heading);
  const suffix = splitIndex != null && splitIndex > 0 ? `-${splitIndex + 1}` : '';
  return `${fileSlug}#${headingSlug}${suffix}`;
}
```

Produces: `hooks-exit-codes#json-output-advanced`, `hooks-exit-codes#json-output-advanced-2`, etc.

#### Q3: Test coverage for overlap correctness

**Answer: Yes, add specific tests.**

Current tests don't cover overlap (v1 has none). Required test cases:

| Test Case | Validates |
|-----------|-----------|
| Hard-split chunk starts with previous chunk's last N lines | Overlap content is correct |
| Overlap is exactly `OVERLAP_LINES_FOR_FORCED_SPLITS` lines | Overlap size is bounded |
| H2/H3 boundary splits have NO overlap | Overlap only on forced splits |
| Overlap doesn't push chunk over size limit | Bounds are respected |

**Add to `chunker.test.ts`:**

```ts
describe('forced split overlap', () => {
  it('forced splits include overlap from previous chunk', () => {
    // Create content that requires hard splitting (exceeds both line and char limits)
    const hugeSection = Array(200).fill('unique-line-content').join('\n');
    const content = `# Title\n\n## Huge Section\n${hugeSection}`;

    const file: MarkdownFile = { path: 'test/overlap.md', content };
    const chunks = chunkFile(file);

    // Should produce multiple chunks due to size
    expect(chunks.length).toBeGreaterThan(1);

    // Chunks after the first should start with overlap from previous
    if (chunks.length > 1) {
      const firstChunkLines = chunks[0].content.split('\n');
      const overlapLines = firstChunkLines.slice(-5).join('\n');
      expect(chunks[1].content).toContain(overlapLines);
    }
  });

  it('H2 boundary splits do NOT include overlap', () => {
    const content = [
      '# Title',
      '## Section 1',
      ...Array(100).fill('content-a'),
      '## Section 2',
      ...Array(100).fill('content-b'),
    ].join('\n');

    const file: MarkdownFile = { path: 'test/no-overlap.md', content };
    const chunks = chunkFile(file);

    // Section 2 chunk should NOT start with Section 1 content
    const section2Chunk = chunks.find(c => c.content.includes('## Section 2'));
    expect(section2Chunk?.content).not.toContain('content-a');
  });

  it('overlap with wide lines stays within bounds (stress test)', () => {
    // Worst case: 5 overlap lines at 200 chars each = 1000 chars reserved
    // This tests the 200 chars/line budget assumption
    const wideLine = 'X'.repeat(200);  // Maximum expected line width
    const content = [
      '# Title',
      '## Wide Content',
      ...Array(100).fill(wideLine),  // 100 lines × 200 chars = 20,000 chars
    ].join('\n');

    const file: MarkdownFile = { path: 'test/wide-overlap.md', content };
    const chunks = chunkFile(file);

    // All chunks must respect bounds even with maximum-width overlap lines
    for (const chunk of chunks) {
      expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      expect(chunk.content.split('\n').length).toBeLessThanOrEqual(MAX_CHUNK_LINES);
    }

    // Verify overlap is present (proves we're testing the right code path)
    if (chunks.length > 1) {
      const firstChunkTail = chunks[0].content.split('\n').slice(-5);
      const secondChunkStart = chunks[1].content.split('\n').slice(0, 5);
      // At least some overlap lines should match
      const hasOverlap = firstChunkTail.some(line => secondChunkStart.includes(line));
      expect(hasOverlap).toBe(true);
    }
  });
});
```

### Additional Technical Issues Identified

| Issue | Severity | Status | Description |
|-------|----------|--------|-------------|
| Overlap can exceed bounds | Medium | **Fixed** | `hardSplitWithOverlap` now includes post-condition assertion and conservative budget (200 chars/line) |
| Paragraph accumulation complexity | Low | **Fixed** | Extracted to `accumulateParagraphsWithOverlap` helper with single responsibility |
| Fence detection duplication | Low | **Addressed** | Same fence logic in 3 locations; extract to shared `FenceTracker` (see Implementation Sequence step 1) |
| Test path fragility | Low | **Fixed** | `DOCS_PATH` now uses `import.meta.url` for reliable ESM path resolution |
| Empty H2 edge case | Low | **Fixed** | Now filtered out in `splitByHeadingOutsideFences` — empty sections skipped entirely |
| Metadata token test coverage | Medium | **Fixed** | Tests now verify tokenize behavior and prove metadata terms come from frontmatter |
| Table-aware splitting | Medium | **Included** | Now part of v2 scope with oversized table handling and header preservation |
| Debug/stats mode missing | Low | **Fixed** | Added `splitType` field to `BoundedPart` for rollout instrumentation |
| Table state tracking fragility | Medium | **Fixed** | `flush()` now takes explicit `wasTable` parameter; `inTable` updated explicitly on mode transitions |
| Silent id/topic type mismatch | Low | **Fixed** | Type warnings now emitted for non-string `id` and `topic` fields, consistent with `requires`/`related_to` |
| splitIndex complexity | Low | **Fixed** | Simplified to only set when `> 0`; removed unused `isLast` parameter from `flush()` |

### Recommendations

| Suggestion | Priority | Status | Rationale |
|------------|----------|--------|-----------|
| Add debug/stats mode | Medium | **Addressed** | `splitType` field enables tracking H3 fallbacks, paragraph fallbacks, hard splits during rollout |
| Heading breadcrumbs | Low | Open | Prepend `## Parent > ### Child` context for deep splits |
| Table-aware splitting | Medium | **Included in v2** | Full implementation with oversized table handling and header preservation in section D |

