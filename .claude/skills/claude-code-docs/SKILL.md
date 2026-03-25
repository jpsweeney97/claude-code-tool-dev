---
name: claude-code-docs
description: "Use this skill when working with Claude Code's extension system — writing, debugging, or configuring hooks (PreToolUse, PostToolUse, PermissionRequest, SessionStart, Stop, SubagentStop), skills (SKILL.md frontmatter, allowed-tools, context: fork), plugins, MCP servers, subagents, or slash commands. Invoke it to look up exact JSON schemas, check frontmatter field names, or verify hook output formats. Never answer these from training memory alone — Claude Code's extension APIs evolve and documentation is authoritative. Not for general Claude API usage, Anthropic SDK questions, Claude Desktop settings, or non-Claude-Code development."
allowed-tools:
  - mcp__claude-code-docs__search_docs
  - mcp__claude-code-docs__reload_docs
---

# Claude Code Docs

The claude-code-docs MCP server indexes the official Claude Code documentation from code.claude.com and exposes it via BM25 full-text search. This skill teaches you how to use it effectively — the search strategies, query patterns, and workflows that produce reliable answers.

## Search Discipline

**Documentation is authoritative over training knowledge.** Claude Code's extension system evolves — hook schemas gain new fields, frontmatter properties change, features get deprecated. Your training data captures a snapshot; the docs capture the current state.

**When to search:**

- Configuration syntax, field names, or schemas (hook input/output, frontmatter properties, settings keys)
- "How do I..." about any extension type (hooks, skills, commands, agents, plugins, MCP)
- Verifying whether a feature exists or how it behaves
- Writing or reviewing extension code that needs to match documented contracts
- Anything where being wrong about the details causes broken configuration

**When training knowledge is sufficient:**

- General programming concepts unrelated to Claude Code extensions
- High-level "what is a hook" explanations (though search to confirm details)
- Questions about Claude API, Anthropic SDKs, or Claude Desktop (different documentation)

**When in doubt, search.** A redundant search costs seconds. A wrong answer from stale training data costs the user's time debugging a configuration that doesn't match current reality.

## Crafting Effective Queries

The search engine uses BM25 scoring with Porter stemming and heading boosts. Understanding this shapes how you query.

### Be specific, not conversational

The engine matches stemmed tokens, not natural language intent. Specific technical terms outperform conversational queries.

| Instead of | Use |
|------------|-----|
| "how do I make a hook that runs before tools" | "PreToolUse hook" |
| "what options can I put in the skill header" | "skill frontmatter properties" |
| "how to share skills with my team" | "plugin skills distribution" |
| "setting up MCP" | "MCP server configuration" |

### Use exact feature names

The tokenizer stems words but preserves casing for compound terms. Use the canonical names from Claude Code's vocabulary:

- `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`, `Stop` (hook events)
- `permissionDecision`, `additionalContext`, `updatedInput` (hook output fields)
- `allowed-tools`, `disable-model-invocation`, `user-invocable` (skill frontmatter)
- `context: fork`, `agent`, `model` (skill execution)

### Combine concept + detail level

When looking for something specific within a broad topic, combine the topic with the detail:

- "PreToolUse input schema" (not just "PreToolUse")
- "hook JSON output format" (not just "hooks")
- "skill frontmatter allowed-tools" (not just "skills")
- "plugin marketplace install" (not just "plugins")

### Use the category filter for focused results

The `category` parameter restricts search to a single documentation domain. Use it when you know the topic area — it eliminates noise from unrelated sections.

**High-value categories** (most commonly needed):

| Category | When to use |
|----------|-------------|
| `hooks` | Hook events, schemas, input/output, decision control, matchers |
| `skills` | SKILL.md format, frontmatter, invocation, arguments, context fork |
| `agents` / `subagents` | Agent files, delegation, Task tool, preloaded skills |
| `plugins` | Plugin structure, marketplace, installation, development |
| `mcp` | MCP server configuration, tool exposure |
| `commands` | Slash commands, command definitions |
| `settings` | Configuration options, permission modes, settings files |
| `claude-md` | CLAUDE.md format, rules files, instruction loading |

**Broader categories** (for cross-cutting topics):

| Category | When to use |
|----------|-------------|
| `security` | Permission system, trust boundaries, sandboxing |
| `ci-cd` | Headless mode, automation, non-interactive usage |
| `ide` | VS Code, JetBrains integration |
| `providers` | Model providers, API keys, configuration |
| `best-practices` | Recommended patterns across extension types |
| `getting-started` | Setup, installation, first-run guidance |
| `troubleshooting` | Common issues and solutions |

**Omit the category** when you're unsure which area the answer lives in, or when the query spans multiple areas. BM25 scoring handles relevance ranking across the full index.

## Multi-Search Strategies

A single search often isn't enough. These patterns handle common situations:

### When results are sparse or empty

1. **Try CamelCase variations:** `PreToolUse` vs `pre tool use` — the tokenizer handles these differently
2. **Try synonyms:** `before` / `pre`, `after` / `post`, `block` / `deny`, `allow` / `approve`
3. **Broaden the category:** Remove the category filter entirely
4. **Generalize the query:** "hook decision control" instead of "PreToolUse permissionDecision deny"

### When results are too broad

1. **Add the category filter:** Restrict to the relevant domain
2. **Add specificity:** "hook JSON output format" instead of "hook output"
3. **Reduce result limit:** `limit: 3` forces you to see only the best matches

### When building a complete answer

Some questions span multiple documentation sections. Search iteratively:

1. Search for the core concept first
2. Follow up with searches for specific details mentioned in the first results
3. If results reference other features, search for those too

**Example:** "How do I create a hook that modifies tool input?"
1. Search: "PreToolUse decision control" — learn about `updatedInput`
2. Search: "PreToolUse hook example" — see concrete configurations
3. Search: "hook configuration settings.json" — learn where to register it

## Using Results

### Cite your sources

Include chunk IDs from search results so the user can verify. Format: `file-slug#heading-slug` (e.g., `hooks#pretooluse-decision-control`).

### Prefer docs over memory

When search results contradict your training knowledge, go with the documentation. State the finding clearly. If you believe the docs might be wrong, note that possibility — but present the documented behavior as the primary answer.

### Handle gaps explicitly

If the documentation doesn't cover something:
- Say so directly: "The documentation doesn't cover [X]"
- Share any related information from search results
- Do not fill gaps with speculation about undocumented behavior

## Integration with Other Tools

### The claude-code-docs-researcher subagent

For questions requiring deep research across multiple documentation areas, delegate to the `claude-code-docs-researcher` agent. It runs focused multi-query searches and synthesizes findings without consuming your main context window. Use this when:

- The question requires 3+ searches to answer fully
- You need to compare documentation across extension types
- The user asks a broad "how does X work" question that spans multiple docs

### Refreshing the index

Run `reload_docs` when:
- Search returns results that seem outdated
- The user reports that documentation has changed
- You've been told the docs were recently updated

Do NOT run `reload_docs` speculatively before every search — the index has a TTL cache and refreshes automatically.

## Troubleshooting

**Search returns "MCP server not available":**
The claude-code-docs MCP server isn't running. Check `/mcp` to verify server status.

**Search returns few/no results for a known feature:**
Query terms don't match the documentation vocabulary. Try the exact feature name (e.g., `PreToolUse` not `before tool`), try with and without the category filter, or try `reload_docs` if the index might be stale.

**Results seem outdated:**
Run `reload_docs` to refresh the index from the remote source, then re-run your search.
