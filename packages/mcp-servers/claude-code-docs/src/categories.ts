// src/categories.ts

/**
 * Canonical list of all documentation categories.
 * These are the 29 categories used for categorizing all Claude Code docs.
 */
export const KNOWN_CATEGORIES = new Set([
  // Extension categories (10)
  'hooks',
  'skills',
  'commands',
  'agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'channels',
  'settings',
  'memory',
  // General categories (19)
  'overview',
  'getting-started',
  'cli',
  'best-practices',
  'interactive',
  'security',
  'providers',
  'gateways',
  'ide',
  'ci-cd',
  'automation',
  'agent-sdk',
  'desktop',
  'integrations',
  'config',
  'operations',
  'troubleshooting',
  'changelog',
  'uncategorized',  // fallback for URLs with no segment in SECTION_TO_CATEGORY
]);

/**
 * Maps URL section segments to their canonical category.
 * Section names correspond to URL paths on docs.anthropic.com.
 */
export const SECTION_TO_CATEGORY: Record<string, string> = {
  // Extension categories
  'hooks': 'hooks',
  'hooks-guide': 'hooks',
  'skills': 'skills',
  'commands': 'commands',
  'slash-commands': 'commands',
  'sub-agents': 'agents',
  'agent-teams': 'agents',
  'plugins': 'plugins',
  'plugins-reference': 'plugins',
  'discover-plugins': 'plugins',
  'plugin-marketplaces': 'plugin-marketplaces',
  'mcp': 'mcp',
  'channels': 'channels',
  'channels-reference': 'channels',
  'settings': 'settings',
  'server-managed-settings': 'settings',
  'memory': 'memory',
  'claude-md': 'memory',
  // General categories
  'overview': 'overview',
  'features-overview': 'overview',
  'how-claude-code-works': 'overview',
  'context-window': 'overview',
  'platforms': 'overview',
  'quickstart': 'getting-started',
  'web-quickstart': 'getting-started',
  'setup': 'getting-started',
  'cli-reference': 'cli',
  'tools-reference': 'cli',
  'best-practices': 'best-practices',
  'common-workflows': 'best-practices',
  'interactive-mode': 'interactive',
  'fast-mode': 'interactive',
  'keybindings': 'interactive',
  'checkpointing': 'interactive',
  'voice-dictation': 'interactive',
  'security': 'security',
  'authentication': 'security',
  'data-usage': 'security',
  'sandboxing': 'security',
  'iam': 'security',
  'legal-and-compliance': 'security',
  'permissions': 'security',
  'permission-modes': 'security',
  'zero-data-retention': 'security',
  'amazon-bedrock': 'providers',
  'google-vertex-ai': 'providers',
  'microsoft-foundry': 'providers',
  'llm-gateway': 'gateways',
  'gateways': 'gateways',
  'claude-apps-gateway': 'gateways',
  'vs-code': 'ide',
  'jetbrains': 'ide',
  'devcontainer': 'ide',
  'github-actions': 'ci-cd',
  'github-enterprise-server': 'ci-cd',
  'gitlab-ci-cd': 'ci-cd',
  'code-review': 'ci-cd',
  'headless': 'automation',
  'scheduled-tasks': 'automation',
  'web-scheduled-tasks': 'automation',
  'desktop-scheduled-tasks': 'automation',
  'computer-use': 'automation',
  'routines': 'automation',
  'agent-sdk': 'agent-sdk',
  'remote-control': 'interactive',
  'ultraplan': 'interactive',
  'desktop': 'desktop',
  'desktop-quickstart': 'desktop',
  'fullscreen': 'desktop',
  'chrome': 'desktop',
  'claude-code-on-the-web': 'desktop',
  'slack': 'integrations',
  'third-party-integrations': 'integrations',
  'claude-directory': 'plugins',
  'configuration': 'config',
  'model-config': 'config',
  'network-config': 'config',
  'terminal-config': 'config',
  'output-styles': 'config',
  'statusline': 'config',
  'env-vars': 'config',
  'analytics': 'operations',
  'costs': 'operations',
  'monitoring-usage': 'operations',
  'troubleshooting': 'troubleshooting',
  'changelog': 'changelog',
  'whats-new': 'changelog',
  // Standalone pages with no family-prefix parent key. Family sub-pages
  // (llm-gateway-*, claude-apps-gateway-*, mcp-*, security-*, desktop-*)
  // resolve via resolveSegmentCategory's longest-prefix rule instead.
  'agents': 'agents',
  'agent-view': 'agents',
  'admin-setup': 'settings',
  'auto-mode-config': 'security',
  'sandbox-environments': 'security',
  'claude-platform-on-aws': 'providers',
  'managed-mcp': 'mcp',
  'plugin-dependencies': 'plugins',
  'plugin-hints': 'plugins',
  'plugin-relevance': 'plugins',
  'debug-your-config': 'troubleshooting',
  'troubleshoot-install': 'troubleshooting',
  'errors': 'troubleshooting',
  'ultrareview': 'ci-cd',
  'feature-availability': 'overview',
  'glossary': 'overview',
  'large-codebases': 'best-practices',
  'prompt-library': 'best-practices',
  'champion-kit': 'best-practices',
  'communications-kit': 'best-practices',
  'sessions': 'interactive',
  'worktrees': 'interactive',
  'advisor': 'interactive',
  'artifacts': 'interactive',
  'deep-links': 'integrations',
  'workflows': 'automation',
  'goal': 'automation',
  'prompt-caching': 'operations',
};

/**
 * Keys of SECTION_TO_CATEGORY sorted longest-first (ties alphabetical) so prefix
 * resolution deterministically prefers the most specific family key
 * (e.g. 'desktop-scheduled-tasks' over 'desktop').
 */
const SECTION_KEYS_LONGEST_FIRST: readonly string[] = Object.keys(SECTION_TO_CATEGORY)
  .sort((a, b) => b.length - a.length || a.localeCompare(b));

/**
 * Resolve one URL path segment to its canonical category.
 *
 * Resolution order:
 * 1. Exact key match in SECTION_TO_CATEGORY.
 * 2. Longest key K such that the segment starts with `K + '-'` — new sub-pages of a
 *    known family (e.g. 'llm-gateway-connect', 'claude-apps-gateway-config',
 *    'mcp-quickstart', 'desktop-linux') resolve without a table edit.
 *
 * The '-' boundary prevents bare-prefix false positives ('pluginsomething' must not
 * match 'plugins'). Returns null when nothing matches.
 */
export function resolveSegmentCategory(segment: string): string | null {
  if (Object.hasOwn(SECTION_TO_CATEGORY, segment)) {
    return SECTION_TO_CATEGORY[segment];
  }
  for (const key of SECTION_KEYS_LONGEST_FIRST) {
    if (segment.startsWith(key + '-')) {
      return SECTION_TO_CATEGORY[key];
    }
  }
  return null;
}

/**
 * Maps category aliases to their canonical category.
 * These are accepted as input but normalized before use.
 */
export const CATEGORY_ALIASES: Record<string, string> = {
  'subagents': 'agents',
  'sub-agents': 'agents',
  'slash-commands': 'commands',
  'claude-md': 'memory',
  'configuration': 'config',
  'gateway': 'gateways',
};
