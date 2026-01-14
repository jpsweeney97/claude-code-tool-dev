# Audit: extension-docs MCP Server

**Date:** 2026-01-12
**Target:** packages/mcp-servers/extension-docs
**Type:** MCP Server
**Verdict:** Ready

## Summary

The extension-docs MCP server is a well-designed, focused search tool for Claude Code extension documentation. It uses BM25 ranking over chunked markdown files with proper error handling, retry mechanisms, and graceful shutdown. No critical or major issues found. Several minor improvements could enhance robustness but none block implementation.

## Findings

### Module-Level Mutable State for Parse Warnings

- **What:** `parseWarnings` is a module-level array that accumulates warnings across parse operations.
- **Why it matters:** If concurrent load attempts occur (though mitigated by `loadingPromise` mutex), warnings could intermix. The state is also shared across the entire process lifetime.
- **Evidence:** `const parseWarnings: ParseWarning[] = []` at frontmatter.ts:14
- **Severity:** Minor
- **Suggestion:** Return warnings from `parseFrontmatter` directly rather than using module-level state, or pass a warnings collector as a parameter.

### No Corpus Size Limit

- **What:** All documentation files are loaded into memory without an upper bound.
- **Why it matters:** If `DOCS_PATH` points to an unexpectedly large corpus, memory could be exhausted. This is unlikely in the intended use case (extension docs are bounded) but is a theoretical concern.
- **Evidence:** `const chunks = files.flatMap((f) => chunkFile(f))` at index.ts:74
- **Severity:** Minor
- **Suggestion:** Add a configurable `MAX_FILES` or `MAX_TOTAL_SIZE` limit with a warning when exceeded.

### Single-Character Terms Filtered Out

- **What:** The tokenizer filters terms with length ≤ 1, losing meaningful single-character tokens.
- **Why it matters:** Searches for "I/O" become searches for empty string after "I" and "O" are filtered. Acronyms and abbreviations may not search as expected.
- **Evidence:** `.filter((term) => term.length > 1)` at tokenizer.ts:13
- **Severity:** Minor
- **Suggestion:** Consider keeping single-character terms that are alphanumeric, or handle common abbreviations specially.

### Generic Search Error Message

- **What:** When search throws an unexpected error, the user receives "Search failed. Please try a different query." without diagnostic information.
- **Why it matters:** Makes debugging difficult if unexpected errors occur, though the search function is simple enough that errors are unlikely in practice.
- **Evidence:** `return { isError: true, content: [{ type: 'text' as const, text: 'Search failed. Please try a different query.' }] }` at index.ts:157-161
- **Severity:** Minor
- **Suggestion:** Include sanitized error context in the response for debugging, or ensure errors are always logged with query context.

### No Rate Limiting

- **What:** Search requests are processed without rate limiting.
- **Why it matters:** BM25 search is O(n*m) where n=chunks and m=query terms. While efficient, rapid repeated searches could consume CPU. Low risk in the intended single-user CLI context.
- **Evidence:** `search` function processes every chunk on every call at bm25.ts:54-68
- **Severity:** Minor
- **Suggestion:** Consider adding simple rate limiting if the server will be exposed to multi-user scenarios.

## What's Working

- **Clean Architecture:** Well-separated concerns (tokenizer, chunker, bm25, loader, frontmatter) make the code maintainable and testable.
- **Robust Error Handling:** DOCS_PATH validation, YAML parse error recovery, graceful fallbacks, and structured error responses.
- **Efficient BM25 Implementation:** Precomputed term frequencies (`termFreqs: Map<string, number>`) enable O(1) term frequency lookups during scoring.
- **Lazy Loading with Retry:** The `ensureIndex()` pattern with retry intervals prevents thrashing on temporary failures.
- **Proper Zod Validation:** Input schemas with clear constraints (500 char limit, 1-20 results) and descriptive error messages.
- **Graceful Shutdown:** Signal handlers with timeout ensure clean process termination.
- **Golden Query Tests:** Integration tests against real corpus validate search quality, not just unit behavior.
