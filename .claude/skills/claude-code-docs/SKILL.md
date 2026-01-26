---
name: claude-code-docs
description: Search Claude Code extension documentation for hooks, skills, plugins, MCP, subagents, commands, and settings. Use when answering questions about Claude Code features or extension development.
allowed-tools:
  - mcp__claude-code-docs__search_docs
  - mcp__claude-code-docs__reload_docs
---

# Extension Docs Lookup

Search the official Claude Code extension documentation to answer questions accurately.

## When to Use

- User asks "how do I..." about hooks, skills, plugins, MCP, subagents, or commands
- User asks "what is..." about Claude Code extension concepts
- User asks "can Claude Code..." about feature capabilities
- Need to verify extension configuration syntax or options
- Writing or reviewing extension code and need reference

## When NOT to Use

- General programming questions unrelated to Claude Code extensions
- Questions about Claude API or Anthropic SDK (different documentation)
- Questions about Claude Desktop or claude.ai (different products)
- Debugging runtime errors in user code (search won't help)

## Inputs

**Required:**
- A question about Claude Code extensions

**Optional:**
- Category filter: `hooks`, `skills`, `commands`, `slash-commands`, `agents`, `subagents`, `sub-agents`, `plugins`, `plugin-marketplaces`, `mcp`, `settings`, `claude-md`, `memory`, `configuration`

**Constraints:**
- Requires claude-code-docs MCP server to be running
- Documentation may not cover bleeding-edge features

## Outputs

**Artifacts:**
- Answer synthesized from search results
- Source citations with chunk IDs (e.g., `hooks-input-schema#pretooluse-input`)

**Definition of Done:**
- [ ] At least one search query was executed
- [ ] Answer cites specific documentation sections
- [ ] If no results found, alternative search terms were tried

## Procedure

1. Parse the user's question to identify key terms
2. Search using `search_docs` with relevant query
3. If results are sparse, try alternative phrasings:
   - CamelCase vs spaces: `PreToolUse` ↔ `pre tool use`
   - Synonyms: `before` ↔ `pre`, `after` ↔ `post`
4. Review top results for relevance
5. Synthesize answer from documentation content
6. Cite sources with chunk IDs
7. If documentation is insufficient, state what's missing

## Decision Points

- If search returns 0 results:
  - Try CamelCase splitting or joining
  - Try category filter if topic is clear
  - If still 0, state "Documentation doesn't cover this" and suggest official docs

- If search returns results but none are relevant:
  - Rephrase query with different terms
  - If still irrelevant after 2 attempts, state uncertainty

- If documentation contradicts known behavior:
  - Prefer documentation over training knowledge
  - Note the discrepancy for user awareness

- If search returns many relevant results:
  - Narrow with category filter if topic is clear
  - Use more specific query terms
  - Focus on top 2-3 results for synthesis; mention others exist

## Verification

Quick check: Response includes at least one citation in format `file-slug#heading-slug` (e.g., `hooks-input-schema#pretooluse-input`).

If no citations present, re-run search or explicitly state "No documentation found."

## Troubleshooting

**Symptom:** Search returns "MCP server not available"
**Cause:** claude-code-docs MCP server not running or not configured
**Next steps:**
1. Check `/mcp` to verify server status
2. Run `reload_docs` to refresh index
3. If server missing, it needs to be added to MCP configuration

**Symptom:** Search returns few/no results for known feature
**Cause:** Query terms don't match documentation vocabulary
**Next steps:**
1. Try exact feature name (e.g., `PreToolUse` not `before tool`)
2. Try category filter to narrow scope
3. Run `reload_docs` in case index is stale

**Symptom:** Results seem outdated or don't reflect recent documentation changes
**Cause:** Cached index is stale
**Next steps:**
1. Run `reload_docs` to refresh the index from the remote source
2. Re-run the search query
