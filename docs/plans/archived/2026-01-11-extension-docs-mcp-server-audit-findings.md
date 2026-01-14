# Extension Docs MCP Server — Audit Findings

**Date:** 2026-01-12
**Source:** Audit of `/Users/jp/Projects/active/claude-code-tool-dev/docs/plans/2026-01-11-extension-docs-mcp-server.md`
**Status:** Verified and resolved

## Findings Summary

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| A1 | Zod schemas are plain objects | ~~High~~ | **INVALID** — SDK accepts shape objects |
| A2 | Parse warnings emitted before parsing | High | **FIXED** |
| A3 | Whitespace-only queries pass validation | Medium | **FIXED** |
| A4 | Metadata headers only in first chunk | Medium | **FIXED** |
| A5 | Fence regex not CommonMark-compliant | Low | **FIXED** |
| A6 | Path comment typo | Low | **FIXED** |

---

## Detailed Findings

### ~~High~~ INVALID: Zod schemas are plain objects

**Original claim:** `SearchInputSchema` and `SearchOutputSchema` are plain objects, not Zod schema instances, so `registerTool` likely won't validate inputs/outputs as intended. (Lines 690–711)

**Verification:** The MCP TypeScript SDK's `McpServer.registerTool` API explicitly accepts **shape objects** (`{ field: z.type() }`), not `z.object()` instances. The SDK wraps them internally.

**Evidence:** SDK documentation shows this pattern:
```typescript
server.registerTool('calculate-bmi', {
    inputSchema: {
        weightKg: z.number(),
        heightM: z.number()
    },
    outputSchema: { bmi: z.number() }
}, async ({ weightKg, heightM }) => { ... });
```

**Resolution:** No fix needed. Finding was based on incorrect assumption about SDK API.

---

### High: Parse warnings emitted before parsing (FIXED)

**Issue:** `parseWarnings` is populated during `chunkFile`, but warnings were printed in `doLoadIndex` before `chunkFile` runs, so U2's warning summary never appeared.

**Fix:** Moved warning emission to AFTER `chunkFile()` call:
```typescript
const chunks = files.flatMap(f => chunkFile(f))

// U2: Emit warning summary AFTER parsing (chunkFile calls parseFrontmatter)
if (parseWarnings.length > 0) { ... }
```

---

### Medium: Whitespace-only queries pass validation (FIXED)

**Issue:** `.min(1)` runs before `.transform(s => s.trim())`, so `'   '` passes validation then becomes empty.

**Fix:** Use `.pipe()` to validate after transform:
```typescript
query: z.string()
  .max(500, 'Query too long')
  .transform(s => s.trim())
  .pipe(z.string().min(1, 'Query cannot be empty'))
```

---

### Medium: Metadata headers only in first chunk (FIXED)

**Issue:** For files split by H2, only the first chunk gets the metadata header in content, reducing BM25 relevance matching for later chunks.

**Fix:** Include category/tags in all chunks' tokens:
```typescript
function createChunk(..., frontmatter: Frontmatter): Chunk {
  const category = frontmatter.category ?? deriveCategory(file.path)
  const tags = frontmatter.tags ?? []
  const metadataTerms = [category, ...tags].flatMap(tokenize)
  const tokens = [...tokenize(content), ...metadataTerms]
  ...
}
```

Also updated `combineChunks` to include metadata terms in recomputed tokens.

---

### Low: Fence regex not CommonMark-compliant (FIXED)

**Issue:** Regex didn't allow 0-3 leading spaces for fences, so indented fences weren't detected.

**Fix:** Updated regex to allow leading spaces:
```typescript
const fence = line.match(/^( {0,3})(`{3,}|~{3,})/)
// ...
fencePattern = fence[2]  // Group 2 is the fence, group 1 is leading spaces
```

Also updated closing fence detection to allow 0-3 leading spaces.

---

### Low: Path comment typo (FIXED)

**Issue:** `hooks/hooks-input-schema.md` should be `hooks/input-schema.md`.

**Fix:** Corrected both occurrences in the document.

---

## Questions Resolved

> Should metadata headers be injected into every chunk?

**Decision:** No. Instead, include category/tags as tokens in all chunks. This is cleaner than duplicating content and achieves the same search quality improvement.

> Should whitespace-only queries be rejected explicitly?

**Decision:** Yes. Explicit validation errors are better UX than silent empty results.

## Testing

All fixes incorporated into the design document with corresponding test cases added.
