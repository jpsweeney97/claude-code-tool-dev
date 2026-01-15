# Extension-Docs MCP Server: Complete Technical Reference & Gap Analysis

**Date**: 2026-01-15
**Status**: Open
**Severity**: High (search quality significantly degraded)

## Table of Contents
1. [What is MCP and Why This Server Exists](#1-what-is-mcp-and-why-this-server-exists)
2. [Directory Structure](#2-directory-structure)
3. [Data Structures](#3-data-structures)
4. [Module-by-Module Reference](#4-module-by-module-reference)
5. [Complete Data Flow](#5-complete-data-flow)
6. [What Changed (The Auto-Sync Plan)](#6-what-changed-the-auto-sync-plan)
7. [The Contract Mismatch](#7-the-contract-mismatch)
8. [Specific Breakages with Code Examples](#8-specific-breakages-with-code-examples)
9. [Test Suite Analysis](#9-test-suite-analysis)
10. [Required Fixes](#10-required-fixes)

---

## 1. What is MCP and Why This Server Exists

### Model Context Protocol (MCP)
MCP is a protocol that allows Claude to communicate with external tools and data sources. An MCP server exposes "tools" that Claude can invoke during a conversation.

### Purpose of extension-docs
Claude Code is Anthropic's CLI tool with an extensibility system (hooks, skills, commands, agents, plugins, MCP servers). The official documentation lives at `https://code.claude.com/docs/`.

**Problem**: Claude's training data may be outdated, but extension APIs evolve rapidly.

**Solution**: This MCP server provides a `search_extension_docs` tool that Claude can invoke to search current, authoritative documentation.

### How It's Used

```
User: "How do I create a PreToolUse hook?"
         │
         ▼
┌─────────────────────────────────────────┐
│           Claude Code CLI               │
│  (Sees the question is about hooks)     │
└─────────────────────────────────────────┘
         │
         ▼ Invokes MCP tool
┌─────────────────────────────────────────┐
│     extension-docs MCP Server           │
│                                         │
│  Tool: search_extension_docs            │
│  Query: "PreToolUse hook"               │
│  Limit: 5                               │
└─────────────────────────────────────────┘
         │
         ▼ Returns ranked results
┌─────────────────────────────────────────┐
│  SearchResult[]                         │
│  - chunk_id: "hooks#pretooluse"         │
│  - content: "PreToolUse hooks run..."   │
│  - category: "hooks"                    │
│  - source_file: ".../hooks"             │
└─────────────────────────────────────────┘
         │
         ▼
Claude uses the retrieved docs to answer accurately
```

### Tools Exposed

| Tool | Purpose |
|------|---------|
| `search_extension_docs` | BM25 semantic search over documentation chunks |
| `reload_extension_docs` | Force refresh of the search index (useful after doc edits) |

---

## 2. Directory Structure

```
packages/mcp-servers/extension-docs/
├── package.json          # NPM package definition
├── tsconfig.json         # TypeScript config (extends monorepo base)
├── .gitignore           # Ignores dist/, node_modules/
├── .claude/             # Claude Code project-specific settings
├── src/                 # Source files (13 modules, 1680 lines total)
│   ├── index.ts         # (232 lines) MCP server entry point
│   ├── loader.ts        # (81 lines)  Load docs from source
│   ├── fetcher.ts       # (88 lines)  HTTP fetch with retry/timeout
│   ├── parser.ts        # (100 lines) Parse llms-full.txt format
│   ├── filter.ts        # (49 lines)  Filter to extension sections
│   ├── cache.ts         # (95 lines)  Disk cache for offline fallback
│   ├── chunker.ts       # (649 lines) Split docs into searchable chunks
│   ├── frontmatter.ts   # (193 lines) Parse YAML frontmatter
│   ├── chunk-helpers.ts # (33 lines)  ID generation, term frequencies
│   ├── fence-tracker.ts # (49 lines)  Track code fence state
│   ├── bm25.ts          # (68 lines)  BM25 search algorithm
│   ├── tokenizer.ts     # (14 lines)  Text tokenization
│   └── types.ts         # (29 lines)  TypeScript interfaces
├── tests/               # Test files (15 files, 1867 lines total)
│   ├── golden-queries.test.ts    # Search quality validation
│   ├── corpus-validation.test.ts # Chunk size bounds validation
│   ├── chunker.test.ts           # Chunking logic (678 lines)
│   ├── frontmatter.test.ts       # YAML parsing
│   ├── bm25.test.ts              # Search algorithm
│   └── ... (10 more test files)
└── dist/                # Compiled JavaScript output
```

---

## 3. Data Structures

### Core Types (`types.ts`)

```typescript
// Input: A documentation file (path + content)
interface MarkdownFile {
  path: string;     // OLD: "hooks/hooks-overview.md"
                    // NEW: "https://code.claude.com/docs/en/hooks"
  content: string;  // The markdown content
}

// Intermediate: Parsed from llms-full.txt
interface ParsedSection {
  sourceUrl: string;  // "https://code.claude.com/docs/en/hooks"
  title: string;      // "Hooks" (extracted from heading before Source:)
  content: string;    // The section's markdown content
}

// Output: A searchable chunk
interface Chunk {
  id: string;                    // "hooks-overview#pretooluse"
  content: string;               // Markdown with metadata header prepended
  tokens: string[];              // ["hooks", "pretooluse", "event", ...]
  termFreqs: Map<string, number>;// {"hooks": 5, "event": 3, ...}
  category: string;              // "hooks" - CRITICAL FOR SEARCH
  tags: string[];                // ["events", "automation"]
  source_file: string;           // Original file path
  heading?: string;              // H2 heading if split
  merged_headings?: string[];    // All headings if chunks were merged
}

// Final: What the search returns
interface SearchResult {
  chunk_id: string;    // Displayed to Claude
  content: string;     // The actual documentation text
  category: string;    // Used for filtering/display
  source_file: string; // For reference
}
```

### Frontmatter Structure (`frontmatter.ts`)

The old local files had YAML frontmatter:

```typescript
interface Frontmatter {
  id?: string;         // "hooks-overview"
  topic?: string;      // "Hooks Overview"
  category?: string;   // "hooks"
  tags?: string[];     // ["events", "automation", "validation"]
  requires?: string[]; // ["hooks-types"]
  related_to?: string[];// ["hooks-events", "hooks-debugging"]
}
```

---

## 4. Module-by-Module Reference

### Entry Point: `index.ts` (232 lines)

**Purpose**: MCP server setup, tool registration, lifecycle management.

**Key functions**:
- `main()` - Initializes MCP server, registers tools, connects transport
- `ensureIndex()` - Lazy-loads search index on first request
- `doLoadIndex()` - Fetches docs, chunks them, builds BM25 index
- `shutdown()` - Graceful shutdown with 5s timeout

**State**:
```typescript
let index: BM25Index | null = null;      // The search index
let loadError: string | null = null;     // Last error message
let lastLoadAttempt = 0;                 // Timestamp for retry throttling
let loadingPromise: Promise<...> | null; // Prevents concurrent loads
```

**Tool Registration**:
```typescript
server.registerTool('search_extension_docs', {
  inputSchema: z.object({
    query: z.string().max(500),
    limit: z.number().int().min(1).max(20).optional()
  }),
  // ...
}, async ({ query, limit = 5 }) => {
  const idx = await ensureIndex();
  const results = search(idx, query, limit);
  return { content: [...], structuredContent: { results } };
});
```

---

### Data Loading Layer

#### `loader.ts` (81 lines)

**Purpose**: Load documentation from source (local files OR remote URL).

**Functions**:

```typescript
// OLD approach - read local markdown files
export async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]>

// NEW approach - fetch from URL, parse, filter
export async function loadFromOfficial(url: string, cachePath?: string): Promise<MarkdownFile[]>
```

**`loadFromOfficial` implementation**:
```typescript
export async function loadFromOfficial(url: string, cachePath?: string): Promise<MarkdownFile[]> {
  const resolvedCachePath = resolveCachePath(cachePath);
  const sections = await fetchAndParse(url, resolvedCachePath);  // Fetch + parse
  const filtered = filterToExtensions(sections);                  // Keep only extension docs
  return filtered.map((s) => ({
    path: s.sourceUrl || s.title || 'unknown',  // ⚠️ URL becomes "path"
    content: s.content,                          // Raw markdown, NO frontmatter
  }));
}
```

#### `fetcher.ts` (88 lines)

**Purpose**: HTTP fetch with timeout, retry, and typed errors.

**Exports**:
```typescript
export interface FetchResult { content: string; status: number; }

export class FetchTimeoutError extends Error { ... }
export class FetchHttpError extends Error { status: number; ... }
export class FetchNetworkError extends Error { ... }

export async function fetchOfficialDocs(url: string, timeoutMs?: number): Promise<FetchResult>
```

**Behavior**:
- Default timeout: 30 seconds (configurable via `FETCH_TIMEOUT_MS` env var)
- Uses `AbortController` for cancellation
- Follows redirects automatically
- Warns on non-text content types

#### `parser.ts` (100 lines)

**Purpose**: Parse `llms-full.txt` format into sections.

The `llms-full.txt` file from `code.claude.com` looks like:

```
# Claude Code on Amazon Bedrock
Source: https://code.claude.com/docs/en/amazon-bedrock

Learn about configuring Claude Code through Amazon Bedrock...

## Prerequisites
...

# Analytics
Source: https://code.claude.com/docs/en/analytics

Track usage and performance...
```

**`parseSections` function**:
```typescript
export function parseSections(raw: string): ParsedSection[]
```

Splits on `^Source:\s+(\S+)\s*$` pattern, extracting:
- `sourceUrl` - The URL after "Source:"
- `title` - The nearest heading BEFORE the Source: line
- `content` - Everything until the next Source: line

#### `filter.ts` (49 lines)

**Purpose**: Filter parsed sections to only extension-related documentation.

```typescript
const EXTENSION_URL_PATTERNS: RegExp[] = [
  /\/hooks/i, /\/skills/i, /\/commands/i, /\/slash-commands/i,
  /\/agents/i, /\/subagents/i, /\/sub-agents/i, /\/plugins/i,
  /\/plugin-marketplaces/i, /\/mcp/i, /\/settings/i, /\/claude-md/i,
  /\/memory/i, /\/configuration/i,
];

const EXTENSION_TITLE_PATTERNS: RegExp[] = [
  /\bhooks?\b/i, /\bskills?\b/i, /\bcommands?\b/i, ...
];

export function isExtensionSection(section: ParsedSection): boolean
export function filterToExtensions(sections: ParsedSection[]): ParsedSection[]
```

#### `cache.ts` (95 lines)

**Purpose**: Cache fetched content for offline fallback.

```typescript
export interface CacheResult { content: string; age: number; }

export function getDefaultCachePath(filename?: string): string
// Returns: ~/Library/Caches/extension-docs/llms-full.txt (on macOS)

export async function readCache(cachePath: string): Promise<CacheResult | null>
export async function writeCache(cachePath: string, content: string): Promise<void>
```

**Features**:
- Atomic writes (write to temp file, then rename)
- File locking to prevent concurrent writes
- XDG-compliant cache directory

---

### Chunking Layer

#### `chunker.ts` (649 lines)

**Purpose**: Split documentation into searchable chunks that fit within size limits.

**Constants**:
```typescript
export const MAX_CHUNK_CHARS = 8000;
const MAX_CHUNK_LINES = 150;
const OVERLAP_LINES_FOR_FORCED_SPLITS = 5;
```

**Main function**:
```typescript
export function chunkFile(file: MarkdownFile): Chunk[]
```

**Algorithm (hierarchical splitting)**:
1. Parse YAML frontmatter if present
2. If file is small enough, return as single chunk
3. Otherwise, split at H2 boundaries
4. If H2 sections too large, split at H3 boundaries
5. If still too large, split at paragraph boundaries (blank lines)
6. If still too large, hard split with line overlap
7. Merge small adjacent chunks back together

**Code fence awareness** (`fence-tracker.ts`):
- Never splits inside ``` code blocks
- CommonMark compliant (0-3 leading spaces, 3+ backticks/tildes)

**Table handling**:
- Keeps tables atomic when possible
- If table exceeds limits, splits at row boundaries while preserving header

#### `frontmatter.ts` (193 lines)

**Purpose**: Parse YAML frontmatter and derive metadata.

**Key functions**:

```typescript
// Parse YAML between --- delimiters
export function parseFrontmatter(content: string, filePath: string): ParseResult

// Format frontmatter as readable header
export function formatMetadataHeader(fm: Frontmatter): string
// Output: "Topic: Hooks Overview\nID: hooks-overview\nCategory: hooks\n\n"

// Extract category from file path
export function deriveCategory(path: string): string
// Input:  "hooks/hooks-overview.md"
// Output: "hooks"
```

**BROKEN**: `deriveCategory` uses regex `^([^/]+)/` which:
- Correctly extracts `hooks` from `hooks/overview.md`
- Incorrectly extracts `https:` from `https://code.claude.com/docs/en/hooks`

#### `chunk-helpers.ts` (33 lines)

**Purpose**: Generate chunk IDs and compute term frequencies.

```typescript
export function slugify(text: string): string
// "Hooks Overview" → "hooks-overview"
// "https://code.claude.com/docs/en/hooks" → "https-code-claude-com-docs-en-hooks"

export function generateChunkId(file: MarkdownFile, heading?: string, splitIndex?: number): string
// Output: "hooks-overview#pretooluse" or "https-code-claude-com-docs-en-hooks#pretooluse"

export function computeTermFreqs(tokens: string[]): Map<string, number>
```

---

### Search Layer

#### `tokenizer.ts` (14 lines)

**Purpose**: Convert text to searchable tokens.

```typescript
export function tokenize(text: string): string[]
```

**Transformations**:
1. Split CamelCase: `PreToolUse` → `Pre Tool Use`
2. Handle consecutive capitals: `MCPServer` → `MCP Server`
3. Lowercase: `Pre Tool Use` → `pre tool use`
4. Split on non-alphanumeric: `pre-tool-use` → `["pre", "tool", "use"]`
5. Filter tokens with length > 1

#### `bm25.ts` (68 lines)

**Purpose**: BM25 (Best Matching 25) ranking algorithm for search.

```typescript
export interface BM25Index {
  chunks: Chunk[];
  avgDocLength: number;           // Average token count per chunk
  docFrequency: Map<string, number>; // How many chunks contain each term
}

export function buildBM25Index(chunks: Chunk[]): BM25Index
export function search(index: BM25Index, query: string, limit?: number): SearchResult[]
```

**BM25 Configuration**:
```typescript
const BM25_CONFIG = {
  k1: 1.2,  // Term frequency saturation
  b: 0.75,  // Length normalization
};
```

**Scoring formula** (per query term):
```
IDF(term) = log((N - df + 0.5) / (df + 0.5) + 1)
TF_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
Score += IDF * TF_norm
```

---

## 5. Complete Data Flow

### Old Flow (Local Files)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ docs/extension-reference/hooks/hooks-overview.md                           │
├────────────────────────────────────────────────────────────────────────────┤
│ ---                                                                        │
│ id: hooks-overview                                                         │
│ topic: Hooks Overview                                                      │
│ category: hooks                                                            │
│ tags: [hooks, events, automation, validation]                              │
│ related_to: [hooks-events, hooks-types, hooks-debugging]                   │
│ ---                                                                        │
│                                                                            │
│ # Hooks Overview                                                           │
│                                                                            │
│ Hooks are event-driven automations that execute before or after...         │
│                                                                            │
│ ## Purpose                                                                 │
│ - Validate tool inputs before execution                                    │
│ - Log and audit operations                                                 │
│ ...                                                                        │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ loadMarkdownFiles(docsPath)                                                │
├────────────────────────────────────────────────────────────────────────────┤
│ Returns: MarkdownFile {                                                    │
│   path: "hooks/hooks-overview.md",                                         │
│   content: "---\nid: hooks-overview\n..."                                  │
│ }                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ chunkFile(file)                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ 1. parseFrontmatter() extracts:                                            │
│    { id: "hooks-overview", topic: "Hooks Overview", category: "hooks",     │
│      tags: ["hooks", "events", "automation", "validation"],                │
│      related_to: ["hooks-events", "hooks-types", "hooks-debugging"] }      │
│                                                                            │
│ 2. formatMetadataHeader() creates:                                         │
│    "Topic: Hooks Overview\nID: hooks-overview\nCategory: hooks\n           │
│     Tags: hooks, events, automation, validation\n\n"                       │
│                                                                            │
│ 3. deriveCategory("hooks/hooks-overview.md") returns: "hooks"              │
│                                                                            │
│ 4. getMetadataTerms() returns:                                             │
│    ["hooks", "overview", "events", "automation", "validation",             │
│     "hooks", "events", "hooks", "types", "hooks", "debugging"]             │
│                                                                            │
│ 5. Splits at H2 boundaries, creates chunks with rich metadata              │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Chunk {                                                                    │
│   id: "hooks-hooks-overview#purpose",                                      │
│   content: "Topic: Hooks Overview\n...\n## Purpose\n...",                  │
│   tokens: ["topic", "hooks", "overview", "purpose", "validate", ...        │
│            "hooks", "events", "automation", "validation", ...],  ← RICH    │
│   category: "hooks",                          ← CORRECT                    │
│   tags: ["hooks", "events", "automation", "validation"],                   │
│   source_file: "hooks/hooks-overview.md"                                   │
│ }                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

### New Flow (Remote URL)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ https://code.claude.com/docs/llms-full.txt (excerpt)                       │
├────────────────────────────────────────────────────────────────────────────┤
│ ...                                                                        │
│ # Hooks                                                                    │
│ Source: https://code.claude.com/docs/en/hooks                              │
│                                                                            │
│ Learn how to automate actions in Claude Code using hooks—shell commands    │
│ that run automatically before or after specific events.                    │
│                                                                            │
│ ## What are hooks                                                          │
│                                                                            │
│ Hooks are shell commands that Claude Code executes automatically at        │
│ specific points during its operation...                                    │
│ ...                                                                        │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ fetchOfficialDocs(url) → parseSections(raw) → filterToExtensions(sections) │
├────────────────────────────────────────────────────────────────────────────┤
│ ParsedSection {                                                            │
│   sourceUrl: "https://code.claude.com/docs/en/hooks",                      │
│   title: "Hooks",                              ← Extracted from heading    │
│   content: "Learn how to automate actions..."  ← NO frontmatter            │
│ }                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ loadFromOfficial(url)                                                      │
├────────────────────────────────────────────────────────────────────────────┤
│ Returns: MarkdownFile {                                                    │
│   path: "https://code.claude.com/docs/en/hooks",  ← URL as path!           │
│   content: "Learn how to automate..."             ← No frontmatter!        │
│ }                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ chunkFile(file)                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ 1. parseFrontmatter() finds no "---" delimiters:                           │
│    { } ← Empty frontmatter                                                 │
│                                                                            │
│ 2. formatMetadataHeader() returns: "" ← Empty                              │
│                                                                            │
│ 3. deriveCategory("https://code.claude.com/docs/en/hooks"):                │
│    Regex ^([^/]+)/ matches "https:" ← WRONG!                               │
│                                                                            │
│ 4. getMetadataTerms() returns:                                             │
│    ["https"] ← Only the broken category, nothing else!                     │
│                                                                            │
│ 5. Creates chunks with degraded metadata                                   │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ Chunk {                                                                    │
│   id: "https-code-claude-com-docs-en-hooks#what-are-hooks", ← UGLY         │
│   content: "Learn how to automate...\n## What are hooks\n...",             │
│   tokens: ["learn", "automate", "actions", "claude", "code", ...           │
│            "https"],                                         ← SPARSE      │
│   category: "https:",                         ← BROKEN                     │
│   tags: [],                                   ← EMPTY                      │
│   source_file: "https://code.claude.com/docs/en/hooks"                     │
│ }                                                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. What Changed (The Auto-Sync Plan)

### Goal
Replace manual documentation maintenance with automatic fetching from `code.claude.com` on every MCP server startup.

### Files Modified

| File | Lines | Change |
|------|-------|--------|
| `src/types.ts` | +5 | Added `ParsedSection` interface |
| `src/fetcher.ts` | +88 | **New** - HTTP fetch with timeout/retry |
| `src/parser.ts` | +100 | **New** - Parse `Source:` delimited sections |
| `src/filter.ts` | +49 | **New** - Filter to extension-related content |
| `src/cache.ts` | +95 | **New** - Disk cache for offline fallback |
| `src/loader.ts` | +43 | Added `loadFromOfficial()` function |
| `src/index.ts` | ~10 | Changed to use `loadFromOfficial()` |

### Files NOT Modified (But Should Have Been)

| File | Lines | Issue |
|------|-------|-------|
| `src/frontmatter.ts` | 193 | `deriveCategory()` assumes file paths, not URLs |
| `src/chunker.ts` | 649 | `getMetadataTerms()` expects frontmatter fields |
| `src/chunk-helpers.ts` | 33 | `generateChunkId()` produces ugly URL slugs |

---

## 7. The Contract Mismatch

### Expected Input Contract (Chunking Layer)

The chunking layer was designed with these assumptions:

```typescript
// MarkdownFile.path should be:
"hooks/hooks-overview.md"          // Relative path with category prefix

// MarkdownFile.content should have:
`---
id: hooks-overview
topic: Hooks Overview
category: hooks
tags: [hooks, events, automation]
---

# Actual Content Here`
```

### Actual Input (After Auto-Sync)

```typescript
// MarkdownFile.path is now:
"https://code.claude.com/docs/en/hooks"  // Full URL

// MarkdownFile.content is now:
`Learn how to automate actions in Claude Code using hooks...

## What are hooks

Hooks are shell commands...`              // No frontmatter at all
```

### Why This Matters

The chunking layer uses metadata for **search quality boosting**:

```typescript
// chunker.ts:59-68
function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const sources = [
    derivedCategory,        // Adds category to tokens → boosts category matches
    fm.id,                  // Adds ID to tokens → enables ID-based search
    fm.topic,               // Adds topic to tokens → boosts topic matches
    ...(fm.tags ?? []),     // Adds tags to tokens → boosts tag matches
    ...(fm.related_to ?? []),// Adds related IDs → enables relationship discovery
  ];
  return sources.flatMap(tokenize);
}
```

When you search for "hook events", chunks with `tags: ["events"]` rank higher because "events" appears in their token list. Without metadata, ranking relies solely on content text.

---

## 8. Specific Breakages with Code Examples

### 8.1 Category Derivation

**File**: `src/frontmatter.ts:190-193`

```typescript
export function deriveCategory(path: string): string {
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

**Test cases**:

| Input | Regex Match | Output | Expected |
|-------|-------------|--------|----------|
| `hooks/overview.md` | `["hooks/", "hooks"]` | `hooks` | ✅ |
| `skills/examples.md` | `["skills/", "skills"]` | `skills` | ✅ |
| `https://code.claude.com/docs/en/hooks` | `["https:/", "https:"]` | `https:` | ❌ Should be `hooks` |
| `https://code.claude.com/docs/en/skills` | `["https:/", "https:"]` | `https:` | ❌ Should be `skills` |

**Fix needed**: Parse URL path to extract doc type:
```typescript
export function deriveCategory(path: string): string {
  // Handle URLs
  if (path.startsWith('http://') || path.startsWith('https://')) {
    const url = new URL(path);
    const segments = url.pathname.split('/').filter(Boolean);
    // /docs/en/hooks → ["docs", "en", "hooks"] → "hooks"
    return segments[segments.length - 1] || 'general';
  }
  // Original logic for file paths
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

### 8.2 Metadata Term Enrichment

**File**: `src/chunker.ts:59-68`

```typescript
function getMetadataTerms(fm: Frontmatter, derivedCategory: string): string[] {
  const sources: (string | undefined)[] = [
    derivedCategory,        // "https:" with new data
    fm.id,                  // undefined
    fm.topic,               // undefined
    ...(fm.tags ?? []),     // []
    ...(fm.requires ?? []), // []
    ...(fm.related_to ?? []),// []
  ];
  return sources.filter((s): s is string => s !== undefined).flatMap(tokenize);
}
```

**Before (old format)**:
```javascript
getMetadataTerms(
  { id: "hooks-overview", topic: "Hooks Overview",
    tags: ["hooks", "events", "automation"],
    related_to: ["hooks-events", "hooks-types"] },
  "hooks"
)
// Returns: ["hooks", "hooks", "overview", "hooks", "overview",
//           "hooks", "events", "automation", "hooks", "events", "hooks", "types"]
// (12+ metadata tokens)
```

**After (new format)**:
```javascript
getMetadataTerms({}, "https:")
// Returns: ["https"]
// (1 token, and it's wrong)
```

**Impact**: Queries like "hook events automation" won't match hooks documentation as strongly because those terms aren't in the metadata tokens.

### 8.3 Chunk ID Generation

**File**: `src/chunk-helpers.ts:3-25`

```typescript
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/\.md$/, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function generateChunkId(file: MarkdownFile, heading?: string): string {
  const fileSlug = slugify(file.path);
  if (!heading) return fileSlug;
  return `${fileSlug}#${slugify(heading)}`;
}
```

**Before**:
```javascript
generateChunkId({ path: "hooks/hooks-overview.md" }, "PreToolUse Events")
// Returns: "hooks-hooks-overview#pretooluse-events"
```

**After**:
```javascript
generateChunkId({ path: "https://code.claude.com/docs/en/hooks" }, "PreToolUse Events")
// Returns: "https-code-claude-com-docs-en-hooks#pretooluse-events"
```

**Impact**: Chunk IDs are verbose and hard to read in search results. Not broken, but suboptimal.

### 8.4 Search Result Example

**Query**: `"PreToolUse hook input schema"`

**Before (old format)**:
```json
{
  "chunk_id": "hooks-input-schema#pretooluse-input",
  "content": "Topic: Hook Input Schema\nID: hooks-input-schema\nCategory: hooks\nTags: hooks, input, schema, pretooluse\n\n## PreToolUse Input\n\nThe input object for PreToolUse hooks contains...",
  "category": "hooks",
  "source_file": "hooks/hooks-input-schema.md"
}
```

**After (new format)**:
```json
{
  "chunk_id": "https-code-claude-com-docs-en-hooks#pretooluse-input",
  "content": "## PreToolUse Input\n\nThe input object for PreToolUse hooks contains...",
  "category": "https:",
  "source_file": "https://code.claude.com/docs/en/hooks"
}
```

---

## 9. Test Suite Analysis

### Test Files and Status

| Test File | Lines | Status | Notes |
|-----------|-------|--------|-------|
| `golden-queries.test.ts` | 52 | ❌ **Would Fail** | Expects `category: "hooks"`, gets `category: "https:"` |
| `corpus-validation.test.ts` | 92 | ⚠️ **Skipped** | References old `docs/extension-reference` path |
| `chunker.test.ts` | 678 | ✅ Passes | Uses mock data with old format |
| `frontmatter.test.ts` | 203 | ✅ Passes | Tests parsing logic, not URL handling |
| `bm25.test.ts` | 111 | ✅ Passes | Tests algorithm, not data format |
| `loader.test.ts` | 121 | ✅ Passes | New tests only cover new functions |
| `fetcher.test.ts` | 68 | ✅ Passes | Tests HTTP behavior with mocks |
| `parser.test.ts` | 86 | ✅ Passes | Tests Source: parsing |
| `filter.test.ts` | 82 | ✅ Passes | Tests URL/title matching |
| `cache.test.ts` | 59 | ✅ Passes | Tests file I/O |
| `chunk-helpers.test.ts` | 82 | ✅ Passes | Tests slugify with old-style paths |
| `fence-tracker.test.ts` | 98 | ✅ Passes | Tests code fence detection |
| `tokenizer.test.ts` | 48 | ✅ Passes | Tests text tokenization |
| `server.test.ts` | 70 | ⚠️ **May fail** | May depend on data format |
| `integration.test.ts` | 17 | ⚠️ **Skipped** | Marked `.skip`, tests real network |

### Golden Queries Test (Critical)

**File**: `tests/golden-queries.test.ts`

```typescript
const goldenQueries = [
  { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
  { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
  { query: 'skill frontmatter', expectedTopCategory: 'skills' },
  { query: 'MCP server registration', expectedTopCategory: 'mcp' },
  { query: 'common fields hook input', expectedTopCategory: 'hooks' },
];

for (const { query, expectedTopCategory } of goldenQueries) {
  it(`"${query}" returns ${expectedTopCategory} category in top result`, () => {
    const results = search(index, query, 5);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].category).toBe(expectedTopCategory);  // ❌ Gets "https:"
  });
}
```

**Why this fails**: With the new data flow, ALL chunks have `category: "https:"`, so no query can ever return `expectedTopCategory: "hooks"`.

---

## 10. Required Fixes

### Priority 1: Fix Category Derivation

**File**: `src/frontmatter.ts`

**Current** (line 190-193):
```typescript
export function deriveCategory(path: string): string {
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

**Fixed**:
```typescript
export function deriveCategory(path: string): string {
  // Handle URLs: extract last path segment
  if (path.startsWith('http://') || path.startsWith('https://')) {
    try {
      const url = new URL(path);
      const segments = url.pathname.split('/').filter(Boolean);
      // /docs/en/hooks → "hooks", /docs/en/hooks-guide → "hooks-guide"
      const lastSegment = segments[segments.length - 1] || 'general';
      // Normalize: "hooks-guide" → "hooks"
      return lastSegment.split('-')[0];
    } catch {
      return 'general';
    }
  }
  // Original logic for file paths
  const match = path.match(/^([^/]+)\//);
  return match?.[1] ?? 'general';
}
```

### Priority 2: Enrich Metadata from ParsedSection

**File**: `src/loader.ts`

**Current**:
```typescript
return filtered.map((s) => ({
  path: s.sourceUrl || s.title || 'unknown',
  content: s.content,
}));
```

**Option A - Synthesize frontmatter**:
```typescript
return filtered.map((s) => {
  const category = deriveCategoryFromUrl(s.sourceUrl);
  const syntheticFrontmatter = `---
topic: ${s.title}
category: ${category}
---

`;
  return {
    path: s.sourceUrl || s.title || 'unknown',
    content: syntheticFrontmatter + s.content,
  };
});
```

**Option B - Extend MarkdownFile type** (cleaner but more changes):
```typescript
interface MarkdownFile {
  path: string;
  content: string;
  metadata?: {        // Optional metadata for URL-sourced content
    title?: string;
    category?: string;
  };
}
```

### Priority 3: Simplify Chunk IDs (Optional)

**File**: `src/chunk-helpers.ts`

```typescript
export function generateChunkId(file: MarkdownFile, heading?: string): string {
  let fileSlug: string;

  if (file.path.startsWith('http')) {
    // For URLs, use just the last path segment
    const url = new URL(file.path);
    const segments = url.pathname.split('/').filter(Boolean);
    fileSlug = slugify(segments[segments.length - 1] || 'unknown');
  } else {
    fileSlug = slugify(file.path);
  }

  if (!heading) return fileSlug;
  return `${fileSlug}#${slugify(heading)}`;
}
```

### Priority 4: Update Tests

**Files**:
- `tests/golden-queries.test.ts` - Update to use new loader or verify with new format
- `tests/corpus-validation.test.ts` - Point to cache file or use loadFromOfficial
- `tests/chunk-helpers.test.ts` - Add test cases for URL paths

---

## Summary

The auto-sync implementation successfully built the **data acquisition pipeline** (fetch → parse → filter → cache) but failed to update the **data processing pipeline** (chunk → tokenize → index) that was designed for a different input format.

**Root cause**: The `MarkdownFile` interface is too generic—it doesn't distinguish between file-path-based sources and URL-based sources, leading the downstream code to apply file-path logic to URLs.

**Key metrics**:
- 6 files modified by the plan
- 3 files broken but not modified
- 1,680 lines of source code
- 1,867 lines of tests
- 5 golden queries that would fail
- 16 extension doc sections being loaded with wrong category
