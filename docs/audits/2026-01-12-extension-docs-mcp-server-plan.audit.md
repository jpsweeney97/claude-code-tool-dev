# Audit: Extension Docs MCP Server Plan (2026-01-11)

**Audience:** Claude Code contributors implementing `packages/mcp-servers/extension-docs/src/index.ts`  
**Audited artifact:** `docs/plans/2026-01-11-extension-docs-mcp-server.md`  
**Audit date:** 2026-01-12  
**Goal:** Identify correctness risks, spec/SDK mismatches, repo-convention mismatches, and concrete implementation deltas.

---

## Executive Summary

The plan is a strong “implementation-ready” design for a local stdio MCP server that provides BM25 search over extension documentation. It is operationally thoughtful (lazy init, structured errors, retry backoff, concurrent-load mutex, and parsing warnings) and likely to work well once the MCP SDK integration details are verified.

However, there are **three high-impact gaps/risks** to address during implementation:

1. **SDK typing / API assumptions are unverified in this workspace**: there is no `node_modules/` installed here, so the plan’s `@modelcontextprotocol/sdk` import paths, `registerTool` schema typing, and tool result shape must be validated against the actual installed SDK version before you rely on the code compiling/running.
2. **“Staleness” is stated as a solved problem, but the plan does not implement doc refresh** beyond retry-on-failure. If docs change during a session, results remain stale until restart unless you add watch/reload behavior.
3. **A few parsing/tokenization edge cases can degrade search quality or produce odd metadata**, mainly around frontmatter type validation and chunk sizing heuristics.

---

## What Was “Truncated” Previously

Earlier terminal output showed `... truncated ...` markers due to output limits, **not because the plan file is missing content**.

To review the portions that were cut off in output:

- MCP server section (lazy init, warning emission, zod schemas, `registerTool`, shutdown):  
  `docs/plans/2026-01-11-extension-docs-mcp-server.md` (around the “MCP Server with Lazy Init…” heading)
- Tail end (integration tests, success criteria, upgrade paths):  
  `docs/plans/2026-01-11-extension-docs-mcp-server.md` (from “Integration Tests” through “Upgrade Paths”)

---

## Repo Reality Check (Conventions + Current State)

### Workspaces exist, but no workspace packages currently exist on disk

- Root `package.json` defines npm workspaces:
  - `packages/mcp-servers/*`
  - `packages/plugins/*`
- In this repo state, there are **no `package.json` files under `packages/`**, so there are currently **no actual npm workspace packages** to copy conventions from.
- `packages/mcp-servers/` currently contains only a `.gitkeep`.

**Implication for implementation:** you will be creating the first “real” npm workspace package under `packages/` (unless other branches differ). Decide/encode conventions (TS config, build scripts, test runner) that do not yet exist in `packages/`.

### Plugins are not npm packages here

Most existing `packages/plugins/*` entries are Claude Code plugins described by `.claude-plugin/plugin.json`, not npm packages. This is a different packaging model than the MCP server plan’s proposed npm package.

---

## SDK/Typing Cross-Check Status (What’s Verified vs Not)

### Not currently verifiable in this workspace

There is **no `node_modules/` directory** in this repo checkout, so the following plan assumptions cannot be verified locally yet:

- Import paths:
  - `@modelcontextprotocol/sdk/server/mcp.js`
  - `@modelcontextprotocol/sdk/server/stdio.js`
- `McpServer.registerTool(...)` signature and expected schema types
- Whether `inputSchema`/`outputSchema` accept:
  - a Zod shape object (plain `{ field: z... }`), or
  - `z.object({...})`, or
  - JSON Schema
- Tool result object fields:
  - `isError`
  - `content` array shape
  - `structuredContent`

**Action required:** Install deps (or otherwise provide the SDK typings locally) before treating the plan’s SDK integration as compile-correct.

### SDK-sensitive code in the plan (likely compile errors without adjustment)

1. **Schema definition shape**
   - Plan uses:
     - `const SearchInputSchema = { query: z.string()..., limit: z.number()... }`
     - and passes it as `inputSchema`.
   - Many libraries require `z.object({...})` instead.

2. **ESM path exports**
   - The plan uses `.js`-suffixed subpath imports. Depending on SDK version/export map, you may need:
     - `.../mcp` not `.../mcp.js`
     - or different module path entirely.

3. **Return type / structured output**
   - Plan returns both:
     - JSON in `content[0].text` and
     - typed `structuredContent`.
   - This may need adjustment based on:
     - what Claude Code consumes, and/or
     - what the SDK type definition permits.

---

## Design/Implementation Review (Correctness + Behavior)

### Strengths (keep as-is unless evidence contradicts)

- **Lazy init + structured tool errors**: avoids hard crashes on missing `DOCS_PATH`.
- **Concurrent request mutex** (`loadingPromise`): prevents duplicate loads on concurrent tool calls.
- **Retry throttling**: prevents log spam and repeated expensive reload attempts on a broken path.
- **Parse warning aggregation**: more actionable than silent stderr spam.
- **BM25 with precomputed term frequency map**: correct performance optimization for scoring.

### Major mismatch: “Staleness” is not solved

The plan lists “Documentation updates aren't immediately available” as a core problem, but the implementation only retries on failure. It does not:

- watch for file changes,
- periodically reload,
- expose a manual `reload` tool,
- use MCP dynamic update notifications (`list_changed`) for refresh.

**Impact:** During a long Claude Code session, doc edits won’t appear in search until the MCP server restarts (or until you add reload behavior).

**Concrete options (choose one):**
- Add a `reload_extension_docs` tool (simple, explicit, low-risk).
- Add periodic reload with mtime caching (more implicit, more moving parts).
- Add filesystem watch (best freshness, but needs careful debouncing and cross-platform behavior).

### Chunking correctness and edge cases

#### Whole-file threshold uses line count

- Plan uses `countLines(preparedContent) <= 150` to decide “whole file chunk”.
- Line count is a weak proxy for token count/size, especially with long lines (schemas, long code lines).

**Impact:** tool output can exceed Claude’s preferred size, and retrieval precision can degrade with very large chunks.

**Concrete improvement:** add a secondary guard like `content.length` or an approximate token count heuristic.

#### H2 splitting is fence-aware (good), but assumes ATX headings

- Splits only on `## ` ATX headings; setext H2 style (`---` underline) won’t split.
- Likely fine if docs are consistent.

#### Merging small chunks keeps first chunk ID

- `combineChunks` preserves `id` of `chunks[0]`.

**Impact:** merged chunk’s id/heading can misrepresent contents (it may contain multiple sections). This is probably acceptable, but be aware for golden tests and UX.

### Frontmatter parsing correctness

Strengths:
- CRLF normalization is explicit.
- Warnings for malformed YAML and non-string tags are aggregated.

Risk:
- `category` and `topic` are not type-validated (unlike tags).

**Impact:** non-string `category/topic` can become `[object Object]`-like output, odd derived categories, and confusing filters/debugging.

**Concrete improvement:** validate `category/topic` are strings; else warn+ignore.

### Retrieval characteristics (BM25 + tokenizer)

Tokenizer is reasonable for v1, but note:
- No stemming: “hook” vs “hooks” mismatch.
- Dropping single-character tokens can reduce recall for certain code identifiers.
- No stopword removal: mostly OK for small corpora; BM25 IDF typically handles this.

If search quality is insufficient, the best low-risk upgrade is usually:
- boost heading matches, or
- boost metadata terms (category/tags) more explicitly, rather than adding heavy NLP.

---

## Testing Plan Review (Practical Adjustments)

The plan’s tests are largely solid, but one practical note:

- Tests that say “fix `DOCS_PATH`” after server start must do so **in-process** (e.g., `process.env.DOCS_PATH = ...`) rather than expecting the shell to change env vars of an already-running process.

---

## Concrete “Implementation Delta List” (What you will likely change from the plan)

When you actually implement `packages/mcp-servers/extension-docs/src/index.ts`, expect to adjust:

1. **SDK imports** to match the installed SDK export map.
2. **Schema types** (`inputSchema`/`outputSchema`) to match `registerTool`’s expected types (Zod object vs JSON schema vs “shape object”).
3. **Tool result return type** to match SDK/client expectations (possibly removing or reshaping `structuredContent`).
4. **Repo scaffolding**: create a real workspace package (there are no existing examples in `packages/`), including `package.json`, `tsconfig.json`, and build/test scripts consistent with your root tooling choices.
5. (Optional but recommended) **Staleness handling** via manual reload tool or watch-based reload, if “staleness” is truly a requirement.

---

## Next Step (To Make This “Precisely Verified”)

To precisely verify SDK typing and eliminate speculation, ensure the SDK is installed locally in this repo so we can inspect:

- `node_modules/@modelcontextprotocol/sdk` export paths and `.d.ts` signatures
- the exact `McpServer.registerTool` type
- tool result types (fields like `isError`/`structuredContent`)

Without local typings present, this audit can only flag the likely version-sensitive points; it cannot confirm exact compile-correct code.

