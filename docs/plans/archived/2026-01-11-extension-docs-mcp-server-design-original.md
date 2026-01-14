# Extension Docs MCP Server Design

**Date:** 2026-01-11
**Status:** Final (audit review complete: fail-fast startup, MCP-compliant error handling)
**Location:** `packages/mcp-servers/extension-docs/`

## Problem

Claude Code extension documentation (107 files, ~79,000 tokens) has three problems:

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
│  │  Loader   │→ │          Chunker Pipeline           │ │
│  │ (glob +   │  │  ┌───────┐  ┌───────┐  ┌─────────┐  │ │
│  │ frontmatter) │  Split  │→ │ Merge │→ │ Shared  │  │ │
│  └───────────┘  │  (H2)   │  │ small │  │ context │  │ │
│                 │  └───────┘  └───────┘  └─────────┘  │ │
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

## Design Decisions

### Retrieval Mechanism: Search Tool Only

**Decision:** Single `search_extension_docs` tool as the primary interface. No resources for v1.

**Rationale:**
- Discovery is the common case — Claude typically has a question, not a known location
- Claude's context resets between sessions, so it rarely "knows" resource URIs
- Search can return resource URIs in results for future upgrade path
- Simpler implementation, faster to ship

### Chunking Strategy: Three-Phase Pipeline

**Decision:** Files ≤150 lines stay whole. Files >150 lines go through a three-phase pipeline:
1. Split at H2 headings (outside code fences)
2. Merge small consecutive chunks (≤150 lines combined)
3. Prepend shared context where detected

**Rationale:**
- Phase 1 (split) creates natural boundaries at H2 headings
- Phase 2 (merge) prevents too-granular chunks in example files (e.g., `skills-examples.md` has 30 H2s in 307 lines — naive splitting creates 10-line chunks)
- Phase 3 (shared context) handles per-variant files where a "Common Fields" section applies to all subsequent sections (e.g., `hooks-input-schema.md`)

**Corpus analysis (2026-01-11):**
- All 107 extension-reference files contain at least one H2 heading
- No fallback needed for heading-less files — if future files lack H2s, they produce a single chunk
- 92 files (86%) are ≤150 lines → whole-file chunks
- 15 files (14%) are >150 lines → split at H2, then merge small chunks
- Only `hooks-input-schema.md` triggers shared-context detection ("Common Fields" H2)

**Implementation:**

```typescript
function chunkFile(file: MarkdownFile): Chunk[] {
  // Parse frontmatter and prepare content
  const { frontmatter, body } = parseFrontmatter(file.content)
  const metadataHeader = formatMetadataHeader(frontmatter)
  const preparedContent = metadataHeader + body

  if (countLines(preparedContent) <= 150) {
    return [wholeFileChunk(file, preparedContent, frontmatter)]
  }

  const rawChunks = splitAtH2(file, preparedContent)      // Phase 1
  const merged = mergeSmallChunks(rawChunks)              // Phase 2
  return addSharedContext(merged)                          // Phase 3
}

// Phase 1: Split at H2 boundaries
function splitAtH2(file: MarkdownFile, content: string): Chunk[] {
  const lines = content.split('\n')
  const chunks: Chunk[] = []
  let intro: string[] = []
  let current: string[] = []
  let currentHeading: string | undefined
  let inFence = false
  let fenceChar = ''
  let isFirstH2 = true

  for (const line of lines) {
    // Toggle fence state on ``` or ~~~
    const fence = line.match(/^(`{3,}|~{3,})/)
    if (fence) {
      if (!inFence) {
        inFence = true
        fenceChar = fence[1][0]
      } else if (line.startsWith(fenceChar.repeat(3))) {
        inFence = false
      }
    }

    // Split at H2 only outside code fences
    if (!inFence && /^##\s/.test(line)) {
      if (current.length > 0 && currentHeading) {
        chunks.push(createChunk(file, current.join('\n'), currentHeading))
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
    chunks.push(createChunk(file, current.join('\n'), currentHeading))
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

function combineChunks(chunks: Chunk[]): Chunk {
  return {
    ...chunks[0],
    content: chunks.map(c => c.content).join('\n\n'),
    heading: chunks[0].heading,  // Use first heading for ID
    merged_headings: chunks.map(c => c.heading).filter(Boolean)
  }
}

// Phase 3: Prepend shared context to variant chunks
function addSharedContext(chunks: Chunk[]): Chunk[] {
  if (chunks.length < 2) return chunks

  const first = chunks[0]
  const heading = first.heading?.replace(/^##\s*/, '').toLowerCase() ?? ''

  // Shared context detection: prepend to all subsequent chunks if first H2
  // indicates content that applies universally to later sections.
  // Currently matches: "Common Fields", "Shared Configuration", "Base Types", "Overview"
  //
  // Corpus analysis (2026-01-11): Only hooks-input-schema.md triggers this pattern.
  // Other large files use "Purpose", "Full Schema", etc. as first H2 — these are NOT
  // shared context. Expanding this regex would incorrectly prepend intro content to
  // unrelated sections. Keep narrow scope; expand only if more files adopt this pattern.
  const isShared = /^(common|shared|base|overview)/i.test(heading)

  if (!isShared) return chunks

  // Prepend shared context to all subsequent chunks
  return [
    first,
    ...chunks.slice(1).map(c => ({
      ...c,
      content: first.content + '\n\n---\n\n' + c.content,
      has_shared_context: true
    }))
  ]
}
```

**Chunk structure:**

```typescript
interface Chunk {
  id: string              // "hooks-input-schema#pretooluse-input"
  content: string         // Includes metadata header + markdown content
  tokens: string[]        // Pre-tokenized content for BM25 scoring
  category: string        // From frontmatter or derived from path
  tags: string[]          // From frontmatter (for debugging/filtering)
  source_file: string     // "hooks/hooks-input-schema.md"
  heading?: string        // H2 heading if split chunk
  merged_headings?: string[]  // All headings if chunks were merged
  has_shared_context: boolean // True if shared section was prepended
}
```

**Note:** `tokens` is pre-computed during chunk creation to avoid per-query tokenization.
The ~1% startup cost is negligible compared to query-time savings.

**Chunk ID generation:**

```typescript
function generateChunkId(file: MarkdownFile, heading?: string): string {
  const fileSlug = slugify(file.path)  // "hooks/input-schema.md" → "hooks-input-schema"
  if (!heading) return fileSlug        // Whole-file chunk or intro section

  const headingSlug = slugify(heading) // "## PreToolUse Input" → "pretooluse-input"
  return `${fileSlug}#${headingSlug}`
}

function buildIndex(chunks: Chunk[]): BM25Index {
  // IDs are unique by construction: full file path + heading slug
  // No collision detection needed — file paths are inherently unique
  return buildBM25Index(chunks)
}
```

**Chunk ID rules:**
- Format: `{file-slug}#{heading-slug}` or `{file-slug}` for whole files
- Slugify: lowercase, replace non-alphanumeric with hyphens, collapse runs
- **Uniqueness by construction:** File paths are inherently unique, so IDs cannot collide

**Helper functions:**

```typescript
function wholeFileChunk(file: MarkdownFile, content: string, fm: Frontmatter): Chunk {
  return {
    id: generateChunkId(file),
    content,
    tokens: tokenize(content),
    category: fm.category ?? deriveCategory(file.path),
    tags: fm.tags ?? [],
    source_file: file.path,
    has_shared_context: false
  }
}

function createChunk(file: MarkdownFile, content: string, heading?: string): Chunk {
  const fm = parseFrontmatter(content).frontmatter
  return {
    id: generateChunkId(file, heading),
    content,
    tokens: tokenize(content),
    category: fm.category ?? deriveCategory(file.path),
    tags: fm.tags ?? [],
    source_file: file.path,
    heading,
    has_shared_context: false
  }
}

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

function deriveCategory(path: string): string {
  // "hooks/input-schema.md" → "hooks"
  const match = path.match(/^([^/]+)\//)
  return match?.[1] ?? 'general'
}

function countLines(content: string): number {
  return content.split('\n').length
}
```

### Frontmatter Handling

**Decision:** Parse YAML frontmatter, extract useful fields, prepend as readable text header.

**Rationale:**
- Category and tag terms boost search relevance naturally via BM25 term frequency
- No explicit boosting logic needed — just include the terms in content
- YAML syntax and navigation fields (requires, related_to, official_docs) excluded to reduce noise
- Deterministic and debuggable

**Implementation:**

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

function parseFrontmatter(content: string): { frontmatter: Frontmatter; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/)
  if (!match) return { frontmatter: {}, body: content }

  try {
    const yaml = parseYaml(match[1])
    return {
      frontmatter: {
        category: yaml.category,
        tags: Array.isArray(yaml.tags) ? yaml.tags : [],
        topic: yaml.topic
      },
      body: match[2]
    }
  } catch (err) {
    // Malformed YAML — treat as plain markdown
    console.error(`WARN: Invalid frontmatter, treating as plain markdown`)
    return { frontmatter: {}, body: content }
  }
}

async function loadMarkdownFiles(docsPath: string): Promise<MarkdownFile[]> {
  const files: MarkdownFile[] = []
  const pattern = path.join(docsPath, '**/*.md')

  for await (const filePath of glob(pattern)) {
    try {
      const content = await fs.readFile(filePath, 'utf-8')
      files.push({ path: path.relative(docsPath, filePath), content })
    } catch (err) {
      if (err instanceof Error) {
        // Log and skip — don't fail entire load for one bad file
        console.error(`WARN: Skipping ${filePath}: ${err.message}`)
      }
    }
  }

  return files
}

function formatMetadataHeader(fm: Frontmatter): string {
  const lines: string[] = []
  if (fm.category) lines.push(`Category: ${fm.category}`)
  if (fm.tags?.length) lines.push(`Tags: ${fm.tags.join(', ')}`)
  if (fm.topic) lines.push(`Topic: ${fm.topic}`)
  return lines.length ? lines.join('\n') + '\n\n' : ''
}
```

**Example output:**

Input file with frontmatter:
```yaml
---
id: hooks-input-schema
topic: Hook Input Schemas
category: hooks
tags: [input, schema, json, stdin]
requires: [hooks-overview]
related_to: [hooks-exit-codes]
---

# Hook Input Schemas
...
```

Chunk content becomes:
```
Category: hooks
Tags: input, schema, json, stdin
Topic: Hook Input Schemas

# Hook Input Schemas
...
```

**Note:** Category falls back to path derivation (`hooks/foo.md` → `"hooks"`) if not in frontmatter.

**Expected output:**
- 92 files ≤150 lines → 92 whole-file chunks
- 15 files >150 lines → ~60-80 chunks after merge phase
- **Total: ~150-170 chunks**, averaging ~450-550 tokens each
- Corpus size: ~75,000-85,000 tokens indexed

### Search Implementation: BM25 with Metadata in Content

**Decision:** Plain BM25 on content that includes parsed frontmatter as text header.

**Rationale:**
- Category and tag terms appear naturally in indexed content via frontmatter header
- No explicit boosting logic needed — BM25 handles term frequency automatically
- ~170 chunks is tiny — BM25 is instant at this scale
- Terminology aligned — docs use Claude's vocabulary, semantic gap is small
- No external dependencies — self-contained, works offline
- Deterministic and debuggable — same query yields same results

**Note:** Earlier handoff mentioned "metadata-boosted BM25" — this referred to including metadata in content (implemented above via `formatMetadataHeader`), not explicit boost multipliers (deferred). The approach achieves the same effect with simpler implementation.

**Upgrade path:** If search quality is insufficient despite metadata-in-content:
1. Add explicit category boost (1.5x) when query contains category name
2. Add synonym expansion (e.g., "before tool runs" → "PreToolUse")
3. Consider embedding re-ranking on top-N results

**Tokenization specification:**

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

**BM25 Index structure:**

```typescript
interface BM25Index {
  chunks: Chunk[]
  avgDocLength: number                 // Pre-computed average tokens per chunk
  docFrequency: Map<string, number>    // term → count of docs containing term
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
    avgDocLength: chunks.reduce((sum, c) => sum + c.tokens.length, 0) / chunks.length,
    docFrequency
  }
}
```

**Note:** Index precomputation makes scoring O(queryTerms × chunkTokens) per query.
The O(1) df lookup replaces the original O(corpus) scan — acceptable for ~170 chunks,
essential if corpus grows.

**BM25 parameters:**

```typescript
const BM25_CONFIG = {
  k1: 1.2,   // Term frequency saturation (industry standard)
  b: 0.75,  // Length normalization (industry standard)
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

  return queryTerms.reduce((score, term) => {
    const df = index.docFrequency.get(term) ?? 0
    const tf = chunk.tokens.filter(t => t === term).length
    const idfScore = idf(N, df)
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    return score + idfScore * tfNorm
  }, 0)
}
```

**Parameter rationale:**
- **k1=1.2** — Standard value (Elasticsearch, Lucene). Controls how quickly term frequency saturates.
- **b=0.75** — Standard value. Moderate length normalization appropriate for mixed-size chunks.
- **BM25+ variant** — The `+ 1` in IDF ensures common terms still contribute positively.

**Implementation:**

```typescript
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

**Decision:** Validate all inputs before processing. Return structured error responses, not exceptions.

**Implementation:**

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

**Validation rules:**
- Empty/missing query → error response (not exception)
- Query >500 chars → error response
- Limit clamped to 1-20 range (no error, just normalized)

**Why structured errors, not exceptions:** Per [MCP spec](https://modelcontextprotocol.io/specification/2025-06-18/schema), tool-level errors should return `{ isError: true, content: [...] }` so the LLM can see the error and self-correct. Throwing exceptions is reserved for protocol-level errors (unknown tool, server malfunction).

### Tools: Single Search Tool

**Decision:** Expose only `search_extension_docs`. No navigation tools for v1.

**Tool interface (as Claude sees it):**

```typescript
mcp__extension_docs__search_extension_docs(
  query: string,
  limit?: number  // default 5, max 20
): SearchResult[]
```

**Note:** Claude Code applies the `mcp__{server-name}__` prefix automatically. The tool definition uses the base name `search_extension_docs`; when registered under server name `extension-docs`, Claude sees it as `mcp__extension_docs__search_extension_docs`.

**Full tool definition:**

```typescript
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
```

**SearchResult structure:**

```typescript
interface SearchResult {
  chunk_id: string    // "hooks-input-schema#pretooluse-input"
  content: string     // The markdown content
  category: string    // "hooks"
  source_file: string // "hooks/hooks-input-schema.md"
  score: number       // BM25 score (for debugging)
}
```

**Output size:** With default limit=5 and ~500-600 tokens/chunk, typical responses are ~2,500-3,000 tokens. Maximum (limit=20) could reach ~12,000 tokens, above the 10,000 token warning threshold but well under the 25,000 maximum. This is acceptable — warnings are informational.

**Rationale:**
- Search is sufficient for all use cases
- Simpler mental model — one tool, one pattern
- Category filter removed — BM25 handles this implicitly via query terms
- Add `list_categories`, `get_chunk`, category filter only if specific failure patterns emerge

### Pipeline: Runtime Processing

**Decision:** Parse and index docs at server startup. No build step.

**Rationale:**
- Always fresh — no risk of stale index
- Single source of truth — only docs matter
- Simpler workflow — edit doc, restart server, see changes
- Acceptable startup cost — ~300-500ms once per session
- The code exists anyway — parser/chunker needed regardless

**Startup sequence:**

```typescript
async function main() {
  const startTime = performance.now()
  const docsPath = process.env.DOCS_PATH || './docs'

  // Fail-fast: exit immediately if docs can't be loaded
  // Rationale: A tool that silently fails is worse than no tool.
  // User will see clear error and fix DOCS_PATH immediately.
  if (!fs.existsSync(docsPath)) {
    console.error(`ERROR: DOCS_PATH not found: ${docsPath}`)
    process.exit(1)
  }

  const files = await loadMarkdownFiles(docsPath)
  if (files.length === 0) {
    console.error(`ERROR: No markdown files found in ${docsPath}`)
    process.exit(1)
  }

  const chunks = files.flatMap(f => chunkFile(f))
  const index = buildBM25Index(chunks)
  const elapsed = (performance.now() - startTime).toFixed(0)
  console.error(`Loaded ${chunks.length} chunks from ${files.length} files in ${elapsed}ms`)

  // Server only starts after successful index build
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
        return validation  // Structured error response (MCP-compliant)
      }
      try {
        return search(index, validation)
      } catch (err) {
        console.error('Search error:', err)
        return {
          isError: true,
          content: [{ type: "text", text: "Search failed. Please try a different query." }]
        }
      }
    }
    // Unknown tool: throw exception (protocol-level error per MCP spec)
    throw new Error(`Unknown tool: ${request.params.name}`)
  })

  const transport = new StdioServerTransport()
  await server.connect(transport)
}

// Graceful shutdown
process.on('SIGTERM', () => process.exit(0))
process.on('SIGINT', () => process.exit(0))
```

**Notes:**
- All logging uses `console.error` (stderr) to avoid corrupting the stdio MCP protocol on stdout.
- Tool-level errors (validation, search failures) return `{ isError: true, content: [...] }` per [MCP spec](https://modelcontextprotocol.io/specification/2025-06-18/schema) — this lets the LLM see the error and self-correct.
- Protocol-level errors (unknown tool) throw exceptions — the SDK converts these to MCP error responses.

## Project Structure

```
packages/mcp-servers/extension-docs/
├── package.json          # With claudeCode.mcp metadata
├── tsconfig.json         # Extends ../../tsconfig.base.json
├── src/
│   ├── index.ts          # MCP server + search handler
│   └── loader.ts         # Load, parse, chunk markdown files
├── dist/                 # Build output (gitignored)
└── tests/
    └── search.test.ts
```

**Rationale:** Two source files are sufficient at ~200 lines total. Split into more files only if code exceeds 400 lines or distinct abstractions emerge.

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
    "test": "vitest"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0"
  },
  "devDependencies": {
    "vitest": "^2.x",
    "typescript": "^5.x"
  },
  "claudeCode": {
    "mcp": {
      "transport": "stdio",
      "command": "node dist/index.js",
      "env": ["DOCS_PATH"]
    }
  }
}
```

**tsconfig.json:**

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "rootDir": "src",
    "outDir": "dist"
  },
  "include": ["src"]
}
```

## Integration with Claude Code

**Registration:**

```bash
claude mcp add --transport stdio --scope user extension-docs \
  -- node /path/to/extension-docs/dist/index.js

# With docs path override
claude mcp add --transport stdio --scope user \
  --env DOCS_PATH=/path/to/extension-reference \
  extension-docs \
  -- node /path/to/extension-docs/dist/index.js
```

**Scope:** `user` for availability across all projects.

**CLAUDE.md guidance:**

```markdown
## Extension Documentation (Required)

Before answering ANY question about hooks, skills, commands, agents, plugins,
or MCP servers, you MUST search the extension documentation:

mcp__extension_docs__search_extension_docs("your query")

Do NOT rely on training knowledge for extension APIs — the documentation is
authoritative and may differ from what you learned. Always search first.

Use specific queries:
- "PreToolUse input schema" not "hooks"
- "skill frontmatter properties" not "skills"
- "MCP server registration" not "MCP"
```

**Rationale for mandatory language:** Claude has 70+ tools competing for attention. Optional guidance gets ignored. Training knowledge of extension APIs may be outdated or incorrect. The 3-line "use it when you need to" framing was flagged by audit as insufficiently directive.

## Testing Strategy

**Unit tests — Chunking pipeline:**
- Files ≤150 lines stay whole
- Files >150 lines split at H2
- Intro content (before first H2) included in first chunk, not orphaned
- Small consecutive chunks merged (≤150 lines combined)
- Shared context ("Common Fields" pattern) prepended to variant chunks
- `skills-examples.md` (307 lines, 30 H2s) → ~5-6 chunks after merge

**Unit tests — Frontmatter:**
- Frontmatter parsed correctly from YAML
- Metadata header formatted as `Category: X\nTags: a, b\nTopic: Y`
- Category falls back to path if not in frontmatter
- Missing frontmatter handled gracefully

**Unit tests — Search:**
- Tokenizer splits CamelCase correctly (`PreToolUse` → `pre`, `tool`, `use`)
- BM25 returns relevant results for exact matches
- Metadata header terms boost relevance (category/tag in query matches header)

**Golden query tests (required before shipping):**

| Query | Expected Top Result |
|-------|---------------------|
| "how do hooks work" | hooks-overview |
| "PreToolUse JSON output" | hooks-exit-codes (JSON section) |
| "skill frontmatter" | skills-frontmatter |
| "MCP server registration" | mcp-transports |
| "agent model selection" | agents-frontmatter |
| "common fields hook input" | hooks-input-schema#common-fields |

**Integration test:**
- Server starts successfully with valid DOCS_PATH
- Server starts with invalid DOCS_PATH but returns structured error on search
- Search returns expected structure with all Chunk fields
- Chunk count logged at startup (~150-170 expected)

**Algorithm trace tests (manual verification):**
1. `skills-examples.md`: 307 lines → 30 H2 chunks → merge → ~5-6 chunks
2. `hooks-input-schema.md`: Common Fields detected → prepended to 12 event-type chunks
3. Sample file frontmatter → correct metadata header format

## Estimated Effort

| Component | Lines |
|-----------|-------|
| Loader (glob, parse frontmatter) | ~60 |
| Chunker (3-phase pipeline) | ~100 |
| BM25 + tokenizer | ~60 |
| MCP server setup | ~50 |
| **Source total** | ~270 |
| Tests | ~150 |
| **Grand total** | ~420 lines |

## Upgrade Paths

Add these based on evidence of specific failure patterns, not speculation:

| If... | Then... |
|-------|---------|
| Search quality insufficient | Add metadata boosting, then synonym expansion |
| Startup time >1 second | Add file mtime caching |
| Claude asks "what categories exist?" | Add `list_categories` tool |
| Claude re-fetches same chunk | Add `get_chunk` tool |
| Specific file needs different chunking | Add per-file override (not config file — just code) |
