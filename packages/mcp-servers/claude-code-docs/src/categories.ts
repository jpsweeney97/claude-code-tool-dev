// src/categories.ts

/**
 * Canonical list of all documentation categories.
 * These are the 24 categories used for categorizing all Claude Code docs.
 */
export const KNOWN_CATEGORIES = new Set([
  // Extension categories (9)
  'hooks',
  'skills',
  'commands',
  'agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'memory',
  // General categories (15)
  'overview',
  'getting-started',
  'cli',
  'best-practices',
  'interactive',
  'security',
  'providers',
  'ide',
  'ci-cd',
  'desktop',
  'integrations',
  'config',
  'operations',
  'troubleshooting',
  'changelog',
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
  'plugins': 'plugins',
  'plugins-reference': 'plugins',
  'discover-plugins': 'plugins',
  'plugin-marketplaces': 'plugin-marketplaces',
  'mcp': 'mcp',
  'settings': 'settings',
  'memory': 'memory',
  'claude-md': 'memory',
  // New categories
  'overview': 'overview',
  'features-overview': 'overview',
  'how-claude-code-works': 'overview',
  'quickstart': 'getting-started',
  'setup': 'getting-started',
  'cli-reference': 'cli',
  'best-practices': 'best-practices',
  'common-workflows': 'best-practices',
  'interactive-mode': 'interactive',
  'checkpointing': 'interactive',
  'security': 'security',
  'data-usage': 'security',
  'sandboxing': 'security',
  'iam': 'security',
  'legal-and-compliance': 'security',
  'amazon-bedrock': 'providers',
  'google-vertex-ai': 'providers',
  'microsoft-foundry': 'providers',
  'llm-gateway': 'providers',
  'vs-code': 'ide',
  'jetbrains': 'ide',
  'devcontainer': 'ide',
  'github-actions': 'ci-cd',
  'gitlab-ci-cd': 'ci-cd',
  'headless': 'ci-cd',
  'desktop': 'desktop',
  'chrome': 'desktop',
  'claude-code-on-the-web': 'desktop',
  'slack': 'integrations',
  'third-party-integrations': 'integrations',
  'configuration': 'config',
  'model-config': 'config',
  'network-config': 'config',
  'terminal-config': 'config',
  'output-styles': 'config',
  'statusline': 'config',
  'analytics': 'operations',
  'costs': 'operations',
  'monitoring-usage': 'operations',
  'troubleshooting': 'troubleshooting',
  'changelog': 'changelog',
};

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
};
