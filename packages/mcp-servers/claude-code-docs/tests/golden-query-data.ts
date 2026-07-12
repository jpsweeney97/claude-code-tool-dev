// tests/golden-query-data.ts
// Shared golden-query table.
// - golden-queries.test.ts runs the non-liveOnly entries against a deterministic
//   mock corpus with strict top-1 assertions.
// - golden-queries.live.test.ts runs ALL entries against the real cached corpus
//   with top-3 assertions.

export interface GoldenQuery {
  query: string;
  expectedTopCategory: string;
  /**
   * True for queries about doc areas that exist only in the real corpus (no mock
   * section in golden-queries.test.ts). Run only by golden-queries.live.test.ts.
   */
  liveOnly?: boolean;
}

export const GOLDEN_QUERIES: GoldenQuery[] = [
  // Extension categories (existing)
  { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
  { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
  { query: 'skill frontmatter', expectedTopCategory: 'skills' },
  { query: 'MCP server registration', expectedTopCategory: 'mcp' },
  { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  { query: 'subagent isolated context delegation', expectedTopCategory: 'agents' },
  // New categories
  // The old generic quickstart/npm query ranked Agent SDK first live. This wording
  // targets the product-installation page and passes mock top-1 + live top-3.
  { query: 'install Claude Code npm package manager', expectedTopCategory: 'getting-started' },
  { query: 'bedrock AWS credentials region', expectedTopCategory: 'providers' },
  { query: 'VS Code keybindings extension', expectedTopCategory: 'ide' },
  { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
  { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
  { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
  { query: 'agent teams leader worker coordination', expectedTopCategory: 'agents' },
  { query: 'authentication login API key', expectedTopCategory: 'security' },
  // Uses the current permissions page's allow/ask/deny vocabulary; the old query
  // ranked Agent SDK permission material above the exact product page.
  { query: 'fine grained permissions allow ask deny rules', expectedTopCategory: 'security' },
  // New priority categories (B12)
  // Custom-command YAML is no longer the product commands page's contract. The
  // current page is the complete built-in/bundled command reference.
  { query: 'built-in commands bundled skills complete reference', expectedTopCategory: 'commands' },
  { query: 'plugin manifest structure install', expectedTopCategory: 'plugins' },
  { query: 'settings hierarchy configuration', expectedTopCategory: 'settings' },
  { query: 'CLAUDE.md memory persistent sessions', expectedTopCategory: 'memory' },
  { query: 'CLI flags model allowedTools', expectedTopCategory: 'cli' },
  { query: 'vim mode interactive editing', expectedTopCategory: 'interactive' },
  { query: 'desktop application native install', expectedTopCategory: 'desktop' },
  { query: 'overview agentic terminal tool', expectedTopCategory: 'overview' },
  // New categories (channels, automation, agent-sdk)
  { query: 'channel push events Telegram Discord', expectedTopCategory: 'channels' },
  { query: 'sender allowlist channel security', expectedTopCategory: 'channels' },
  { query: 'Agent SDK agent loop turns messages', expectedTopCategory: 'agent-sdk' },
  { query: 'scheduled tasks loop recurring prompt', expectedTopCategory: 'automation' },
  // Remaining categories (full coverage)
  // Browse/install is correctly answered by discover-plugins; marketplace authoring
  // is the stable discriminator for the plugin-marketplaces category.
  { query: 'plugin marketplace schema host distribute marketplace', expectedTopCategory: 'plugin-marketplaces' },
  { query: 'effective prompts iterative workflow tips', expectedTopCategory: 'best-practices' },
  { query: 'configuration files model settings override', expectedTopCategory: 'config' },
  { query: 'token usage cost dashboard spending limits', expectedTopCategory: 'operations' },
  { query: 'Slack app mention channel thread integration', expectedTopCategory: 'integrations' },
  { query: 'changelog release version history fixes', expectedTopCategory: 'changelog' },
  // Morphological variant queries (stemming coverage)
  { query: 'configuring MCP servers', expectedTopCategory: 'mcp' },
  { query: 'creating custom skills', expectedTopCategory: 'skills' },
  // Live-only queries — doc areas added upstream 2026-06/07; no mock sections exist.
  { query: 'Claude apps gateway OIDC SSO identity provider', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'connect Claude Code to LLM gateway ANTHROPIC_BASE_URL', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'gateway spend limits cap developer spend', expectedTopCategory: 'gateways', liveOnly: true },
  { query: 'advisor consult stronger model before committing', expectedTopCategory: 'interactive', liveOnly: true },
  { query: 'artifacts publish interactive page from session', expectedTopCategory: 'interactive', liveOnly: true },
  { query: 'claude mcp add connect first MCP server', expectedTopCategory: 'mcp', liveOnly: true },
  { query: 'plugin relevance marketplace signals suggestion', expectedTopCategory: 'plugins', liveOnly: true },
  { query: 'feature availability by provider and plan', expectedTopCategory: 'overview', liveOnly: true },
  { query: 'install Claude desktop app Ubuntu Debian apt', expectedTopCategory: 'desktop', liveOnly: true },
];
