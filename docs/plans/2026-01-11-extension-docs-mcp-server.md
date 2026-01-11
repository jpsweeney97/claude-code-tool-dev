# Extension Docs MCP Server — Design & Implementation

**Date:** 2026-01-11
**Status:** Ready for implementation (audit corrections + implementation fixes incorporated)
**Location:** `packages/mcp-servers/extension-docs/`

---

## Problem

Claude Code extension documentation (108 files, ~79,000 tokens) has three problems:

1. **Context inefficiency** — Loading whole docs wastes context window
2. **Discoverability** — Claude can't find relevant docs when needed
3. **Staleness** — Documentation updates aren't immediately available

## Solution

A TypeScript MCP server that serves extension-reference documentation as searchable chunks. Claude Code connects via stdio and uses a `search_extension_docs` tool to retrieve relevant documentation on demand.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Claude Code                         │
└─────────────────────────┬───────────────────────────────┘
                          │ stdio
┌─────────────────────────▼───────────────────────────────┐
│              extension-docs MCP Server                   │
│                                                          │
│  ┌───────────┐  ┌─────────────────────────────────────┐ │
│  │  Loader   │→ │       2-Phase Chunker Pipeline       │ │
│  │ (glob +   │  │  ┌───────┐  ┌───────┐               │ │
│  │ frontmatter) │  Split  │→ │ Merge │               │ │
│  └───────────┘  │  (H2)   │  │ small │               │ │
│                 │  └───────┘  └───────┘               │ │
│                 └──────────────────┬──────────────────┘ │
│                                    ↓                    │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    BM25 Index                       ││
│  └─────────────────────────┬───────────────────────────┘│
│  ┌─────────────────────────▼───────────────────────────┐│
│  │            search_extension_docs() tool             ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## Audit Corrections Incorporated

This design incorporates corrections from the 2026-01-11 audit:

| ID | Finding | Severity | Correction Applied |
|----|---------|----------|-------------------|
| C1 | Hard `process.exit()` on missing DOCS_PATH | Major | Lazy init + structured error responses |
| C2 | 3-phase chunking over-engineered | Major | Removed Phase 3, 2-phase only |
| U1 | CLAUDE.md guidance won't persist across sessions | Major | SessionStart hook with `additionalContext` |
| U2 | Silent malformed YAML processing | Minor | Warning collection with file paths at startup |
| U3 | No recovery from transient load failures | Major | Retry with 60-second backoff interval |

## Implementation Fixes (Post-Design Review)

| ID | Issue | Severity | Fix Applied |
|----|-------|----------|-------------|
| F1 | Hardcoded `DEFAULT_DOCS_PATH` breaks distribution | High | Require `DOCS_PATH` env var, no default |
| F2 | O(n) tf calculation per query term | Medium | Precompute `termFreqs` map during indexing |
| F3 | Missing loading mutex allows concurrent loads | Medium | Promise-based deduplication with `loadingPromise` |
| F4 | Split chunks lose frontmatter metadata | Medium | Pass parsed frontmatter through to `createChunk` |
| F5 | `combineChunks` doesn't recompute tokens/termFreqs | Medium | Recompute tokens and termFreqs for merged content |
| F6 | SDK version `^1.0.0` outdated, missing zod peer dep | High | Updated to `^1.25.0`, added `zod` dependency |
| F7 | Division by zero in `avgDocLength` if no chunks | Medium | Guard with `chunks.length > 0` check |
| F8 | Windows CRLF line endings break frontmatter parsing | Low | Normalize to LF before regex matching |
| F9 | `glob()` errors not caught | Low | Wrap in try/catch, return empty array on failure |

---

## Design Decisions

### Retrieval Mechanism: Search Tool Only

**Decision:** Single `search_extension_docs` tool as the primary interface. No resources for v1.

**Rationale:**
- Discovery is the common case — Claude typically has a question, not a known location
- Claude's context resets between sessions, so it rarely "knows" resource URIs
- Search can return resource URIs in results for future upgrade path
- Simpler implementation, faster to ship

### Chunking Strategy: Two-Phase Pipeline

**Decision:** Files ≤150 lines stay whole. Files >150 lines go through a two-phase pipeline:
1. Split at H2 headings (outside code fences)
2. Merge small consecutive chunks (≤150 lines combined)

**Audit note (C2):** The original design included Phase 3 (shared context prepending) which affected only one file (`hooks-input-schema.md`). This was removed as over-engineering — the "Common Fields" content will either merge naturally or be found via search.

**Corpus analysis (2026-01-11):**
- All 108 extension-reference files contain at least one H2 heading
- No fallback needed for heading-less files — if future files lack H2s, they produce a single chunk
- 93 files (86%) are ≤150 lines → whole-file chunks
- 15 files (14%) are >150 lines → split at H2, then merge small chunks

### Error Handling: Graceful Degradation

**Decision:** Server stays running even if docs can't be loaded. Return structured errors on search attempts.

**Audit note (C1):** The original design used `process.exit(1)` on missing DOCS_PATH. This was wrong because Claude cannot restart MCP servers mid-session. The server must remain responsive and return actionable error messages.

### Discovery: SessionStart Hook

**Decision:** Use a SessionStart hook to inject search guidance into every session.

**Audit note (U1):** CLAUDE.md text guidance ("you MUST search") doesn't persist across sessions and competes with 70+ other tools for attention. A SessionStart hook with `additionalContext` reliably injects the reminder every time.

### YAML Parsing: Visible Warnings

**Decision:** Collect all parsing warnings and emit a summary at startup with file paths.

**Audit note (U2):** The original design logged warnings to stderr and continued silently. This makes debugging search quality issues difficult. Aggregated warnings with file paths are actionable.

### Error Recovery: Retry with Backoff

**Decision:** If documentation loading fails, retry after 60 seconds on subsequent search requests.

**Audit note (U3):** The original design set `loadError` once and never cleared it. This meant transient failures (network mount disconnect, permissions change, environment variable typo) permanently broke the server until Claude Code restarted. Since Claude cannot restart MCP servers mid-session, users would lose search functionality for the entire session.

**Mechanism:**
- Track `lastLoadAttempt` timestamp alongside `loadError`
- On search request: if `loadError` is set but 60+ seconds have passed, clear error and retry
- On retry: clear `parseWarnings` array to avoid duplicate warnings
- Log "Retrying documentation load..." for visibility

**Why 60 seconds:** Short enough that recovery feels responsive after fixing the underlying issue. Long enough that permanent failures don't flood logs (max 1 error per minute).

### Graceful Shutdown: Server Close Before Exit

**Decision:** Call `server.close()` in SIGTERM/SIGINT handlers before `process.exit()`.

**Rationale:**
- The MCP SDK `Server` class has a `close()` method that properly shuts down the transport
- For HTTP transports, examples show `transport.close()` on connection end
- For stdio transports, the streams close automatically on process exit, but `server.close()` ensures:
  - Pending responses are flushed
  - Internal protocol state is cleaned up
  - The transport's read loop terminates gracefully

**Implementation:** The shutdown handler is async to await `server.close()` before exiting. The `main()` function also has a `.catch()` handler for fatal startup errors.

---

## Implementation

### Imports

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from '@modelcontextprotocol/sdk/types.js'
import { glob } from 'glob'
import { parse as parseYaml } from 'yaml'
import * as fs from 'fs'
import { readFile } from 'fs/promises'
import * as path from 'path'
```

### Types

```typescript
interface MarkdownFile {
  path: string    // Relative to docs root: "hooks/input-schema.md"
  content: string
}

interface Frontmatter {
  category?: string
  tags?: string[]
  topic?: string
  // Fields ignored for search: id, requires, related_to, official_docs
}

interface Chunk {
  id: string              // "hooks-input-schema#pretooluse-input"
  content: string         // Includes metadata header + markdown content
  tokens: string[]        // Pre-tokenized content for BM25 scoring
  termFreqs: Map<string, number>  // F2: Precomputed term frequencies for O(1) lookup
  category: string        // From frontmatter or derived from path
  tags: string[]          // From frontmatter (for debugging/filtering)
  source_file: string     // "hooks/hooks-input-schema.md"
  heading?: string        // H2 heading if split chunk
  merged_headings?: string[]  // All headings if chunks were merged
}

interface BM25Index {
  chunks: Chunk[]
  avgDocLength: number                 // Pre-computed average tokens per chunk
  docFrequency: Map<string, number>    // term → count of docs containing term
}

interface SearchResult {
  chunk_id: string    // "hooks-input-schema#pretooluse-input"
  content: string     // The markdown content
  category: string    // "hooks"
  source_file: string // "hooks/hooks-input-schema.md"
  score: number       // BM25 score (for debugging)
}

interface ParseWarning {
  file: string
  issue: string
}
```

### Tokenizer

```typescript
function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    // Split CamelCase: "PreToolUse" → "pre tool use"
    .replace(/([a-z\d])([A-Z])/g, '$1 $2')
    // Handle consecutive capitals: "MCPServer" → "MCP Server" → "mcp server"
    .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    // Split on non-alphanumeric (handles hyphens, underscores, punctuation)
    .split(/[^a-z0-9]+/)
    .filter(term => term.length > 1)  // Drop single chars
}
```

**Tokenization rules:**
- Lowercase all terms
- Split CamelCase (`PreToolUse` → `pre`, `tool`, `use`)
- Handle consecutive capitals (`MCPServer` → `mcp`, `server`; `JSONSchema` → `json`, `schema`)
- Split on hyphens, underscores, punctuation
- No stemming for v1 (add if recall is poor)
- No stop words for v1 (corpus is small, context matters)

### Frontmatter Parsing (with U2 warning collection)

```typescript
const parseWarnings: ParseWarning[] = []

function parseFrontmatter(content: string, filePath: string): { frontmatter: Frontmatter; body: string } {
  // Normalize line endings to LF for consistent parsing
  const normalized = content.replace(/\r\n/g, '\n')
  const match = normalized.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  if (!match) return { frontmatter: {}, body: normalized }

  try {
    const yaml = parseYaml(match[1])

    // B5: Parse tags with strict type checking
    let tags: string[] = []
    if (Array.isArray(yaml.tags)) {
      tags = yaml.tags.filter((t): t is string => {
        if (typeof t === 'string') return true
        parseWarnings.push({
          file: filePath,
          issue: `Non-string tag value ignored: ${typeof t}`
        })
        return false
      })
    } else if (typeof yaml.tags === 'string') {
      tags = [yaml.tags]
    } else if (yaml.tags !== undefined) {
      parseWarnings.push({
        file: filePath,
        issue: `Invalid tags type: expected string or array, got ${typeof yaml.tags}`
      })
    }

    return {
      frontmatter: {
        category: yaml.category,
        tags,
        topic: yaml.topic
      },
      body: match[2]
    }
  } catch (err) {
    // U2: Collect warning with file path instead of silent log
    parseWarnings.push({
      file: filePath,
      issue: `Invalid YAML frontmatter: ${err instanceof Error ? err.message : 'unknown error'}`
    })
    return { frontmatter: {}, body: content }
  }
}

function formatMetadataHeader(fm: Frontmatter): string {
  const lines: string[] = []
  if (fm.category) lines.push(`Category: ${fm.category}`)
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`)
  if (fm.topic) lines.push(`Topic: ${fm.topic}`)
  return lines.length ? lines.join('\n') + '\n\n' : ''
}

function deriveCategory(path: string): string {
  // "hooks/input-schema.md" → "hooks"
  const match = path.match(/^([^/]+)\//)
  return match?.[1] ?? 'general'
}
```

### File Loading

```typescript
async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = []
  const pattern = path.join(docsPath, '**/*.md').replace(/\\/g, '/')  // Normalize for glob

  let filePaths: string[]
  try {
    filePaths = await glob(pattern)
  } catch (err) {
    console.error(`WARN: Failed to glob ${pattern}: ${err instanceof Error ? err.message : 'unknown'}`)
    return files
  }

  for (const filePath of filePaths) {
    try {
      const content = await readFile(filePath, 'utf-8')
      // B6: Normalize path separators for cross-platform
      const relativePath = path.relative(docsPath, filePath).replace(/\\/g, '/')
      files.push({ path: relativePath, content })
    } catch (err) {
      if (err instanceof Error) {
        // Log and skip — don't fail entire load for one bad file
        console.error(`WARN: Skipping ${filePath}: ${err.message}`)
      }
    }
  }

  return files
}
```

### Two-Phase Chunking (C2: Phase 3 removed)

```typescript
function chunkFile(file: MarkdownFile): Chunk[] {
  const { frontmatter, body } = parseFrontmatter(file.content, file.path)
  const metadataHeader = formatMetadataHeader(frontmatter)
  const preparedContent = metadataHeader + body

  if (countLines(preparedContent) <= 150) {
    return [wholeFileChunk(file, preparedContent, frontmatter)]
  }

  // F4: Pass frontmatter to splitAtH2 so chunks inherit metadata
  const rawChunks = splitAtH2(file, preparedContent, frontmatter)   // Phase 1
  return mergeSmallChunks(rawChunks)                                 // Phase 2
  // C2: Phase 3 (shared context detection) removed — over-engineering for 1 file
}

function countLines(content: string): number {
  return content.split('\n').length
}

// Phase 1: Split at H2 boundaries
// F4: Accept frontmatter parameter to pass to createChunk
function splitAtH2(file: MarkdownFile, content: string, frontmatter: Frontmatter): Chunk[] {
  const lines = content.split('\n')
  const chunks: Chunk[] = []
  let intro: string[] = []
  let current: string[] = []
  let currentHeading: string | undefined
  let inFence = false
  let fencePattern = ''  // B1: Store full fence pattern, not just character
  let isFirstH2 = true

  for (const line of lines) {
    // B1: CommonMark-compliant fence matching
    // Opening: captures full fence (```, ````, ~~~~, etc.)
    const fence = line.match(/^(`{3,}|~{3,})/)
    if (fence) {
      if (!inFence) {
        inFence = true
        fencePattern = fence[1]  // Store full pattern
      } else if (
        // Closing: same char, >= length, only trailing whitespace
        line[0] === fencePattern[0] &&
        line.match(new RegExp(`^${fencePattern[0]}{${fencePattern.length},}\\s*$`))
      ) {
        inFence = false
        fencePattern = ''
      }
    }

    // Split at H2 only outside code fences
    if (!inFence && /^##\s/.test(line)) {
      if (current.length > 0 && currentHeading) {
        // F4: Pass frontmatter to createChunk
        chunks.push(createChunk(file, current.join('\n'), currentHeading, frontmatter))
      } else if (current.length > 0) {
        // Content before first H2 is intro
        intro = current
      }

      // First H2 includes intro content (no orphan chunks)
      current = isFirstH2 ? [...intro, '', line] : [line]
      currentHeading = line
      isFirstH2 = false
    } else {
      current.push(line)
    }
  }

  if (current.length > 0) {
    // F4: Pass frontmatter to createChunk
    chunks.push(createChunk(file, current.join('\n'), currentHeading, frontmatter))
  }

  return chunks
}

// Phase 2: Merge small consecutive chunks
function mergeSmallChunks(chunks: Chunk[], maxLines = 150): Chunk[] {
  const result: Chunk[] = []
  let buffer: Chunk[] = []
  let bufferLines = 0

  for (const chunk of chunks) {
    const lines = chunk.content.split('\n').length
    if (bufferLines + lines <= maxLines) {
      buffer.push(chunk)
      bufferLines += lines
    } else {
      if (buffer.length) result.push(combineChunks(buffer))
      buffer = [chunk]
      bufferLines = lines
    }
  }
  if (buffer.length) result.push(combineChunks(buffer))
  return result
}

// F5: Recompute tokens and termFreqs for merged content
function combineChunks(chunks: Chunk[]): Chunk {
  const combinedContent = chunks.map(c => c.content).join('\n\n')
  const tokens = tokenize(combinedContent)
  return {
    ...chunks[0],
    content: combinedContent,
    tokens,
    termFreqs: computeTermFreqs(tokens),
    heading: chunks[0].heading,
    merged_headings: chunks.map(c => c.heading).filter(Boolean) as string[]
  }
}
```

### Chunk Creation & ID Generation

```typescript
function generateChunkId(file: MarkdownFile, heading?: string): string {
  const fileSlug = slugify(file.path)  // "hooks/input-schema.md" → "hooks-input-schema"
  if (!heading) return fileSlug        // Whole-file chunk or intro section

  const headingSlug = slugify(heading) // "## PreToolUse Input" → "pretooluse-input"
  return `${fileSlug}#${headingSlug}`
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

// F2: Helper to compute term frequency map
function computeTermFreqs(tokens: string[]): Map<string, number> {
  const freqs = new Map<string, number>()
  for (const token of tokens) {
    freqs.set(token, (freqs.get(token) ?? 0) + 1)
  }
  return freqs
}

function wholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  const tokens = tokenize(content)
  return {
    id: generateChunkId(file),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),  // F2: Precompute for O(1) search
    category: fm.category ?? deriveCategory(file.path),
    tags: fm.tags ?? [],
    source_file: file.path
  }
}

// F4: Accept frontmatter parameter instead of re-parsing chunk content
function createChunk(file: MarkdownFile, content: string, heading: string | undefined, frontmatter: Frontmatter): Chunk {
  const tokens = tokenize(content)
  return {
    id: generateChunkId(file, heading),
    content,
    tokens,
    termFreqs: computeTermFreqs(tokens),  // F2: Precompute for O(1) search
    category: frontmatter.category ?? deriveCategory(file.path),
    tags: frontmatter.tags ?? [],
    source_file: file.path,
    heading
  }
}
```

### BM25 Search

```typescript
const BM25_CONFIG = {
  k1: 1.2,   // Term frequency saturation (industry standard)
  b: 0.75,  // Length normalization (industry standard)
}

function buildBM25Index(chunks: Chunk[]): BM25Index {
  const docFrequency = new Map<string, number>()

  for (const chunk of chunks) {
    const uniqueTerms = new Set(chunk.tokens)
    for (const term of uniqueTerms) {
      docFrequency.set(term, (docFrequency.get(term) ?? 0) + 1)
    }
  }

  return {
    chunks,
    avgDocLength: chunks.length > 0
      ? chunks.reduce((sum, c) => sum + c.tokens.length, 0) / chunks.length
      : 0,
    docFrequency
  }
}

// BM25+ IDF variant — prevents negative IDF for common terms
function idf(N: number, df: number): number {
  return Math.log((N - df + 0.5) / (df + 0.5) + 1)
}

function bm25Score(queryTerms: string[], chunk: Chunk, index: BM25Index): number {
  const { k1, b } = BM25_CONFIG
  const N = index.chunks.length
  const avgdl = index.avgDocLength
  const dl = chunk.tokens.length

  // B3: Guard against empty index
  if (N === 0 || avgdl === 0) return 0

  return queryTerms.reduce((score, term) => {
    const df = index.docFrequency.get(term) ?? 0
    const tf = chunk.termFreqs.get(term) ?? 0  // F2: O(1) lookup instead of O(n) filter
    const idfScore = idf(N, df)
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    return score + idfScore * tfNorm
  }, 0)
}

function search(index: BM25Index, query: string, limit = 5): SearchResult[] {
  const queryTerms = tokenize(query)

  return index.chunks
    .map(chunk => ({ chunk, score: bm25Score(queryTerms, chunk, index) }))
    .filter(r => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(r => ({
      chunk_id: r.chunk.id,
      content: r.chunk.content,
      category: r.chunk.category,
      source_file: r.chunk.source_file,
      score: r.score
    }))
}
```

### Input Validation

```typescript
interface ValidationResult {
  isError?: true
  content?: Array<{ type: "text"; text: string }>
  query?: string
  limit?: number
}

function validateSearchInput(args: unknown): ValidationResult {
  if (!args || typeof args !== 'object') {
    return { isError: true, content: [{ type: "text", text: "Invalid arguments: expected object with query field" }] }
  }

  const { query, limit } = args as Record<string, unknown>

  if (typeof query !== 'string' || query.trim().length === 0) {
    return { isError: true, content: [{ type: "text", text: "Invalid query: expected non-empty string" }] }
  }

  if (query.length > 500) {
    return { isError: true, content: [{ type: "text", text: "Query too long: maximum 500 characters" }] }
  }

  const validLimit = Math.min(Math.max(Number(limit) || 5, 1), 20)

  return { query: query.trim(), limit: validLimit }
}
```

### MCP Server with Lazy Init, Retry, and Loading Mutex (C1 + U3 + F1 + F3)

```typescript
// === State Management ===
let index: BM25Index | null = null
let loadError: string | null = null
let lastLoadAttempt = 0  // U3: Track last attempt for retry throttling
let loadingPromise: Promise<BM25Index | null> | null = null  // F3: Mutex for concurrent requests

// === Configuration ===
// F1: No DEFAULT_DOCS_PATH — require explicit configuration
const RETRY_INTERVAL_MS = 60_000  // U3: 60 seconds between retry attempts

async function ensureIndex(): Promise<BM25Index | null> {
  // Fast path: already loaded successfully
  if (index) return index

  // F3: If a load is in progress, wait for it (prevents concurrent loads)
  if (loadingPromise) return loadingPromise

  // U3: Retry throttling — if we failed recently, return cached error
  const now = Date.now()
  if (loadError && (now - lastLoadAttempt) < RETRY_INTERVAL_MS) {
    return null  // Too soon to retry
  }

  // F3: Start loading with mutex
  loadingPromise = doLoadIndex()

  try {
    return await loadingPromise
  } finally {
    loadingPromise = null  // F3: Release mutex
  }
}

// F3: Extracted loading logic for mutex pattern
async function doLoadIndex(): Promise<BM25Index | null> {
  const isRetry = loadError !== null

  // Prepare for (re)load attempt
  lastLoadAttempt = Date.now()
  loadError = null
  parseWarnings.length = 0  // U3: Clear stale warnings before retry

  if (isRetry) {
    console.error('Retrying documentation load...')
  }

  // F1: Require DOCS_PATH — no fallback default
  const docsPath = process.env.DOCS_PATH
  if (!docsPath) {
    loadError = 'DOCS_PATH environment variable is required'
    console.error(`ERROR: ${loadError}`)
    return null
  }

  if (!fs.existsSync(docsPath)) {
    loadError = `DOCS_PATH not found: ${docsPath}`
    console.error(`ERROR: ${loadError}`)
    return null
  }

  try {
    const files = await loadMarkdownFiles(docsPath)
    if (files.length === 0) {
      loadError = `No markdown files found in ${docsPath}`
      console.error(`ERROR: ${loadError}`)
      return null
    }

    // U2: Emit warning summary after loading
    if (parseWarnings.length > 0) {
      console.error(`\nWARNING: ${parseWarnings.length} file(s) with parse issues:`)
      for (const w of parseWarnings) {
        console.error(`  - ${w.file}: ${w.issue}`)
      }
      console.error('')
    }

    const chunks = files.flatMap(f => chunkFile(f))
    index = buildBM25Index(chunks)
    console.error(`Loaded ${chunks.length} chunks from ${files.length} files`)
    return index
  } catch (err) {
    // F3: Catch unexpected errors to prevent unhandled rejections
    loadError = `Unexpected error: ${err instanceof Error ? err.message : 'unknown'}`
    console.error(`ERROR: ${loadError}`)
    return null
  }
}

const searchToolDefinition = {
  name: "search_extension_docs",
  description: "Search extension documentation for hooks, skills, commands, agents, plugins, and MCP servers. Returns relevant chunks ranked by relevance. Use specific queries like 'PreToolUse input schema' rather than broad terms like 'hooks'.",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query — be specific (e.g., 'PreToolUse JSON output', 'skill frontmatter properties', 'MCP server registration')"
      },
      limit: {
        type: "number",
        description: "Maximum results to return (default: 5, max: 20)"
      }
    },
    required: ["query"]
  }
}

async function main() {
  const server = new Server(
    { name: 'extension-docs', version: '1.0.0' },
    { capabilities: { tools: {} } }
  )

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [searchToolDefinition]
  }))

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === 'search_extension_docs') {
      const validation = validateSearchInput(request.params.arguments)
      if (validation.isError) {
        return validation
      }

      // C1: Lazy load on first search, return structured error if failed
      const idx = await ensureIndex()
      if (!idx) {
        return {
          isError: true,
          content: [{ type: "text", text: `Search unavailable: ${loadError}` }]
        }
      }

      try {
        const results = search(idx, validation.query!, validation.limit)
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }]
        }
      } catch (err) {
        console.error('Search error:', err)
        return {
          isError: true,
          content: [{ type: "text", text: "Search failed. Please try a different query." }]
        }
      }
    }

    throw new Error(`Unknown tool: ${request.params.name}`)
  })

  const transport = new StdioServerTransport()
  await server.connect(transport)

  // Graceful shutdown: close server before exit to flush pending responses
  const shutdown = async (signal: string) => {
    console.error(`Received ${signal}, shutting down...`)

    let timeoutId: NodeJS.Timeout
    let exitCode = 0

    try {
      // B4: Race between graceful close and timeout
      await Promise.race([
        server.close(),
        new Promise((_, reject) => {
          timeoutId = setTimeout(() => reject(new Error('Shutdown timeout')), 5000)
        })
      ])
      clearTimeout(timeoutId!)
      console.error('Graceful shutdown complete')
    } catch (err) {
      clearTimeout(timeoutId!)
      console.error('Shutdown error:', err instanceof Error ? err.message : 'unknown')
      exitCode = 1
    }

    process.exit(exitCode)
  }

  process.on('SIGTERM', () => shutdown('SIGTERM'))
  process.on('SIGINT', () => shutdown('SIGINT'))
}

main().catch((err) => {
  console.error('Fatal error:', err)
  process.exit(1)
})
```

---

## SessionStart Hook (U1)

**File:** `~/.claude/hooks/extension-docs-reminder.sh`

```bash
#!/bin/bash
# Note: Tool name format is mcp__<server-name>__<tool-name>
# Server registered as "extension-docs" → tool is "mcp__extension-docs__search_extension_docs"
# Verify actual name with `claude mcp list` after registration
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<extension-docs-reminder>\nWhen working with Claude Code extensions (hooks, skills, commands, agents, plugins, MCP servers):\n\n1. SEARCH FIRST: Use the search_extension_docs tool from the extension-docs MCP server\n2. Use specific queries: \"PreToolUse input schema\", not \"hooks\"\n3. Documentation is authoritative - training knowledge may be outdated\n</extension-docs-reminder>"
  }
}
EOF
```

**Add to `~/.claude/settings.json`:**

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|resume|clear|compact",
      "hooks": [{
        "type": "command",
        "command": "bash $HOME/.claude/hooks/extension-docs-reminder.sh"
      }]
    }]
  }
}
```

**Why this works:** The hook fires every session start (startup, resume, clear, compact) and injects guidance via `additionalContext`. This solves the memory persistence problem because the reminder appears in Claude's context even across sessions.

---

## Project Structure

```
packages/mcp-servers/extension-docs/
├── package.json
├── tsconfig.json
├── .gitignore
├── src/
│   └── index.ts          # All implementation (~400 lines)
├── dist/                 # Build output (gitignored)
└── tests/
    └── index.test.ts     # Unit + golden query tests
```

**package.json:**

```json
{
  "name": "@claude-tools/extension-docs",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "test": "vitest run"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.25.0",
    "glob": "^11.x",
    "yaml": "^2.x",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@types/node": "^22.x",
    "typescript": "^5.x",
    "vitest": "^2.x"
  }
}
```

**tsconfig.json:**

```json
{
  "extends": "../../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

**.gitignore:**

```
dist/
node_modules/
```

---

## Build and Register

```bash
# Build
cd /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/extension-docs
npm install
npm run build

# Register MCP server (F1: DOCS_PATH is required — no default)
claude mcp add --transport stdio --scope user \
  --env DOCS_PATH=/Users/jp/Projects/active/claude-code-tool-dev/docs/extension-reference \
  extension-docs \
  -- node /Users/jp/Projects/active/claude-code-tool-dev/packages/mcp-servers/extension-docs/dist/index.js
```

---

## Testing Strategy

### Golden Query Tests

| Query | Expected Top Result |
|-------|---------------------|
| "how do hooks work" | hooks-overview |
| "PreToolUse JSON output" | hooks-exit-codes |
| "skill frontmatter" | skills-frontmatter |
| "MCP server registration" | mcp-transports |
| "common fields hook input" | hooks-input-schema |

### Unit Tests

**Chunking pipeline:**
- Files ≤150 lines stay whole
- Files >150 lines split at H2
- Intro content (before first H2) included in first chunk, not orphaned
- Small consecutive chunks merged (≤150 lines combined)
- `skills-examples.md` (307 lines, 30 H2s) → ~5-6 chunks after merge

**Frontmatter:**
- Frontmatter parsed correctly from YAML
- Metadata header formatted as `Category: X\nTags: a, b\nTopic: Y`
- Category falls back to path if not in frontmatter
- Missing frontmatter handled gracefully
- Malformed YAML adds to parseWarnings array (U2)

**Search:**
- Tokenizer splits CamelCase correctly (`PreToolUse` → `pre`, `tool`, `use`)
- BM25 returns relevant results for exact matches
- Metadata header terms boost relevance (category/tag in query matches header)

**Term frequency precomputation (F2):**
- `computeTermFreqs(['a', 'b', 'a'])` returns `Map { 'a' => 2, 'b' => 1 }`
- Chunks created via `wholeFileChunk` have populated `termFreqs` map
- Chunks created via `createChunk` have populated `termFreqs` map
- BM25 scoring uses `chunk.termFreqs.get(term)` not `chunk.tokens.filter()`

**Frontmatter inheritance (F4):**
- Split chunks inherit `category` from file's frontmatter
- Split chunks inherit `tags` from file's frontmatter
- File with `category: hooks` and `tags: [api, schema]` produces chunks with same values

**Merged chunk recomputation (F5):**
- `combineChunks` produces chunk with recomputed `tokens` array
- `combineChunks` produces chunk with recomputed `termFreqs` map
- Merged chunk `tokens.length` equals tokenized combined content length

**Empty chunks edge case (F7):**
- `buildBM25Index([])` returns `{ chunks: [], avgDocLength: 0, docFrequency: Map {} }`
- No division by zero error

**CRLF handling (F8):**
- File with `---\r\nkey: value\r\n---\r\nBody` parses frontmatter correctly
- Body content has normalized LF line endings

**Path normalization (B6):**
```typescript
describe('path normalization', () => {
  it('normalizes Windows backslashes', () => {
    const windowsPath = 'hooks\\input-schema.md'
    expect(windowsPath.replace(/\\/g, '/')).toBe('hooks/input-schema.md')
  })
})
```

### Integration Tests

**Graceful degradation (C1):**
1. Set `DOCS_PATH=/nonexistent`
2. Start server
3. Call `search_extension_docs({ query: "test" })`
4. Verify: Returns `{ isError: true, content: [...] }`, not exception

**Required DOCS_PATH (F1):**
1. Unset `DOCS_PATH` environment variable
2. Start server
3. Call `search_extension_docs({ query: "test" })`
4. Verify: Returns `{ isError: true, content: [{ text: "...DOCS_PATH environment variable is required..." }] }`

**Error recovery with retry (U3):**
1. Set `DOCS_PATH=/nonexistent`
2. Start server
3. Call `search_extension_docs({ query: "test" })` → Returns error
4. Call again immediately → Returns same error (throttled)
5. Wait 60+ seconds (or mock `Date.now()`)
6. Fix `DOCS_PATH` to valid location
7. Call `search_extension_docs({ query: "test" })` → Retries load, succeeds
8. Verify: stderr shows "Retrying documentation load..."

**Concurrent request handling (F3):**
1. Set `DOCS_PATH` to valid location with slow filesystem (or mock delay)
2. Start server
3. Fire 5 concurrent `search_extension_docs({ query: "test" })` requests
4. Verify: Only ONE load occurs (check stderr for single "Loaded X chunks" message)
5. Verify: All 5 requests receive the same results

**Hook test (U1):**
1. Start new Claude Code session
2. Verify `<extension-docs-reminder>` appears in context
3. Confirm guidance mentions the `search_extension_docs` tool

---

## Implementation Tasks

| # | Task | Files | Est. Time |
|---|------|-------|-----------|
| 1 | Project setup | package.json, tsconfig.json, .gitignore | 15 min |
| 2 | Core implementation | src/index.ts (~400 lines) | 2.5 hrs |
| 3 | SessionStart hook | ~/.claude/hooks/extension-docs-reminder.sh | 10 min |
| 4 | Settings.json update | ~/.claude/settings.json | 10 min |
| 5 | Unit tests | tests/index.test.ts | 45 min |
| 6 | Build and register | npm install, npm run build, claude mcp add | 15 min |
| 7 | Golden query verification | Manual testing | 15 min |
| — | **Total** | | **4-5 hrs** |

---

## Success Criteria

1. **C1 verified:** Server returns structured error (not crash) when DOCS_PATH invalid
2. **C2 verified:** Source code uses 2-phase chunking only (no Phase 3)
3. **U1 verified:** New sessions show `<extension-docs-reminder>` in context
4. **U2 verified:** Malformed YAML files listed in startup stderr with file paths
5. **U3 verified:** After load failure, server retries after 60 seconds and recovers if path is fixed
6. **F1 verified:** Server returns structured error when DOCS_PATH environment variable is not set
7. **F2 verified:** `Chunk` interface includes `termFreqs` and BM25 scoring uses O(1) lookup
8. **F3 verified:** Concurrent search requests share a single load operation (no duplicate loads)
9. **F4 verified:** Split chunks inherit `category` and `tags` from file's frontmatter
10. **F5 verified:** Merged chunks have recomputed `tokens` and `termFreqs` for combined content
11. **F6 verified:** SDK version is `^1.25.0` and `zod` is listed as dependency
12. **F7 verified:** Empty chunks array produces `avgDocLength: 0` (no division by zero)
13. **F8 verified:** Files with CRLF line endings parse frontmatter correctly
14. **F9 verified:** `glob()` permission errors don't crash, return empty array
15. **Functional:** All 5 golden queries return expected top results
16. **Tests pass:** `npm test` runs successfully with vitest

---

## Upgrade Paths

Add these based on evidence of specific failure patterns, not speculation:

| If... | Then... |
|-------|---------|
| Search quality insufficient | Add metadata boosting, then synonym expansion |
| Startup time >1 second | Add file mtime caching |
| Claude asks "what categories exist?" | Add `list_categories` tool |
| Claude re-fetches same chunk | Add `get_chunk` tool |
| Specific file needs different chunking | Add per-file override (not config file — just code) |
| 60-second retry feels too slow | Reduce `RETRY_INTERVAL_MS` (e.g., 30 seconds) |
| Retry logs are noisy for permanent failures | Add exponential backoff (1m, 2m, 4m, max 10m) |
| Need to track loading state for debugging | Add `get_status` tool returning `{ loaded, chunkCount, loadError, lastLoadAttempt }` |
