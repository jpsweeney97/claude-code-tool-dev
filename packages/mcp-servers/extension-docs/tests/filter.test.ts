import { describe, it, expect } from 'vitest';
import { isExtensionSection, filterToExtensions, KNOWN_CATEGORIES } from '../src/filter.js';
import type { ParsedSection } from '../src/types.js';

describe('isExtensionSection', () => {
  it('matches URL with /hooks', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/hooks',
      title: 'Something',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /slash-commands', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/slash-commands',
      title: 'Commands',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /sub-agents (hyphenated)', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/sub-agents',
      title: 'Agents',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches URL with /plugin-marketplaces', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/plugin-marketplaces',
      title: 'Marketplaces',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('matches title with "hooks" word', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://example.com/other',
      title: 'Using Hooks in Claude Code',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(true);
  });

  it('does not match unrelated URL and title', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://code.claude.com/docs/en/quickstart',
      title: 'Getting Started',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(false);
  });

  it('does not match partial word in title', () => {
    const section: ParsedSection = {
      sourceUrl: 'https://example.com/other',
      title: 'Rehooking the system',
      content: 'content',
    };
    expect(isExtensionSection(section)).toBe(false);
  });
});

describe('filterToExtensions', () => {
  it('filters to only extension sections', () => {
    const sections: ParsedSection[] = [
      { sourceUrl: 'https://example.com/hooks', title: 'Hooks', content: 'a' },
      { sourceUrl: 'https://example.com/quickstart', title: 'Start', content: 'b' },
      { sourceUrl: 'https://example.com/mcp', title: 'MCP', content: 'c' },
    ];
    const filtered = filterToExtensions(sections);
    expect(filtered).toHaveLength(2);
    expect(filtered[0].title).toBe('Hooks');
    expect(filtered[1].title).toBe('MCP');
  });
});

describe('KNOWN_CATEGORIES', () => {
  it('includes all extension URL path segments', () => {
    // These are the path segments that can appear in extension URLs
    const expectedCategories = [
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
    ];

    for (const category of expectedCategories) {
      expect(KNOWN_CATEGORIES.has(category)).toBe(true);
    }
  });

  it('is used for URL-based category derivation', () => {
    // Verify the Set can be used for efficient lookup
    expect(KNOWN_CATEGORIES.has('hooks')).toBe(true);
    expect(KNOWN_CATEGORIES.has('unknown')).toBe(false);
  });
});
