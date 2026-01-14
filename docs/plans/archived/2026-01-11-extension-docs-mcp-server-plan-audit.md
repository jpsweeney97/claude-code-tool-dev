Below is an updated critical analysis of `docs/plans/2026-01-11-extension-docs-mcp-server.md` with the remaining open questions resolved and the new SDK guidance applied.

**Findings (highest severity first)**

- **High — API mismatch with current MCP SDK guidance**
  The plan is written against `@modelcontextprotocol/sdk` (`Server`, `StdioServerTransport`), but the SDK overview (https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/refs/heads/main/docs/server.md) recommends `McpServer` from `@modelcontextprotocol/server` and highlights structured responses (`structuredContent`). This is a strategic mismatch: the plan's implementation will be immediately legacy relative to the current guidance. At minimum, update the plan to the new package/API style and adjust code examples to `McpServer`. Read https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/refs/heads/main/docs/capabilities.md and https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/refs/heads/main/examples/server/README.md for additional information about MCP SDK.
- **High — Tool output format is textified JSON instead of structured**
  The plan's `search_extension_docs` returns `content: [{ type: "text", text: JSON.stringify(results) }]`. The SDK overview (https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/refs/heads/main/docs/server.md) shows support for `structuredContent`, which is a safer and more ergonomic contract for clients. With the new API, there's no reason to embed JSON in text; update the plan to return structured output and optional text for display.
- **High — SessionStart hook output format likely incorrect**
  Hooks docs say `SessionStart` stdout is added as context. The plan emits a JSON wrapper with `hookSpecificOutput.additionalContext`, which is not documented. This is likely unnecessary and potentially ignored. Update the plan to emit plain text (or minimal JSON only if explicitly supported).
- **Medium — Tokenizer drops single-character tokens**
  The `.filter(term => term.length > 1)` rule can reduce recall for short identifiers (e.g., `C`, `v1`, `x`, `y`). This could affect queries involving short schema fields or versioned names. Consider allowing tokens containing digits (e.g., `v1`) or preserve single-letter tokens if uppercase in headings.
- **Medium — No guardrails for corpus size / memory**
  The plan keeps full chunk content, tokens, and term frequency maps in memory. This is fine for 108 files but scales poorly. The plan should explicitly call out this limit and add a simple size warning if `chunks.length` or total tokens exceed a threshold.
- **Medium — Large intro sections can create oversized chunks**
  For files with large pre-H2 content, the "intro + first H2" chunk can become large. The merge logic doesn't cap that. Consider a fallback split by line length if the intro alone exceeds the max.
- **Low — Glob without ignore list**
  The glob pulls all `*.md` files. If unrelated drafts or archived docs appear, they'll pollute search. Consider an allowlist per category or an ignore list.
- **Low — Slug collision handling absent (but currently not an issue)**
  The corpus has zero slug collisions today, so this is not an immediate bug. Still, the plan should note collision handling as a future hardening item.
