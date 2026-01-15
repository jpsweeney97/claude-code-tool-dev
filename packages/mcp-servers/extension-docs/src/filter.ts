import type { ParsedSection } from './types.js';

/**
 * Canonical list of extension category slugs.
 * Used for category derivation from URLs and validation.
 * Includes variant forms (e.g., 'subagents' and 'sub-agents').
 */
export const KNOWN_CATEGORIES = new Set([
  'hooks',
  'skills',
  'commands',
  'slash-commands',
  'agents',
  'subagents',
  'sub-agents',
  'plugins',
  'plugin-marketplaces',
  'mcp',
  'settings',
  'claude-md',
  'memory',
  'configuration',
]);

const EXTENSION_URL_PATTERNS: RegExp[] = [
  /\/hooks/i,
  /\/skills/i,
  /\/commands/i,
  /\/slash-commands/i,
  /\/agents/i,
  /\/subagents/i,
  /\/sub-agents/i,
  /\/plugins/i,
  /\/plugin-marketplaces/i,
  /\/mcp/i,
  /\/settings/i,
  /\/claude-md/i,
  /\/memory/i,
  /\/configuration/i,
];

const EXTENSION_TITLE_PATTERNS: RegExp[] = [
  /\bhooks?\b/i,
  /\bskills?\b/i,
  /\bcommands?\b/i,
  /\bslash commands?\b/i,
  /\bagents?\b/i,
  /\bsub[- ]?agents?\b/i,
  /\bplugins?\b/i,
  /\bplugin marketplaces?\b/i,
  /\bmcp\b/i,
  /\bsettings\b/i,
  /\bclaude[- ]md\b/i,
  /\bmemory\b/i,
  /\bconfiguration\b/i,
  /\bextensions?\b/i,
];

export function isExtensionSection(section: ParsedSection): boolean {
  const sourceUrl = section.sourceUrl ?? '';
  const title = section.title ?? '';

  return (
    EXTENSION_URL_PATTERNS.some((pattern) => pattern.test(sourceUrl)) ||
    EXTENSION_TITLE_PATTERNS.some((pattern) => pattern.test(title))
  );
}

export function filterToExtensions(sections: ParsedSection[]): ParsedSection[] {
  return sections.filter(isExtensionSection);
}
