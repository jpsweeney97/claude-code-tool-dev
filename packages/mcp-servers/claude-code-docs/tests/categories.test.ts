// tests/categories.test.ts
import { describe, it, expect } from 'vitest';
import { KNOWN_CATEGORIES, SECTION_TO_CATEGORY, CATEGORY_ALIASES } from '../src/categories.js';

describe('KNOWN_CATEGORIES', () => {
  it('contains all 26 canonical categories', () => {
    const expected = [
      // Extension categories (10)
      'hooks', 'skills', 'commands', 'agents', 'plugins',
      'plugin-marketplaces', 'mcp', 'channels', 'settings', 'memory',
      // General categories (16)
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'ide', 'ci-cd',
      'automation', 'desktop', 'integrations', 'config', 'operations',
      'troubleshooting', 'changelog',
    ];

    expect(KNOWN_CATEGORIES.size).toBe(26);
    for (const cat of expected) {
      expect(KNOWN_CATEGORIES.has(cat)).toBe(true);
    }
  });

  it('does not contain aliases as canonical categories', () => {
    expect(KNOWN_CATEGORIES.has('subagents')).toBe(false);
    expect(KNOWN_CATEGORIES.has('sub-agents')).toBe(false);
    expect(KNOWN_CATEGORIES.has('slash-commands')).toBe(false);
    expect(KNOWN_CATEGORIES.has('claude-md')).toBe(false);
    expect(KNOWN_CATEGORIES.has('configuration')).toBe(false);
  });
});

describe('SECTION_TO_CATEGORY', () => {
  it('maps extension sections to categories', () => {
    expect(SECTION_TO_CATEGORY['hooks']).toBe('hooks');
    expect(SECTION_TO_CATEGORY['hooks-guide']).toBe('hooks');
    expect(SECTION_TO_CATEGORY['slash-commands']).toBe('commands');
    expect(SECTION_TO_CATEGORY['sub-agents']).toBe('agents');
    expect(SECTION_TO_CATEGORY['plugins-reference']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['discover-plugins']).toBe('plugins');
  });

  it('maps newly discovered URL segments to categories', () => {
    expect(SECTION_TO_CATEGORY['agent-teams']).toBe('agents');
    expect(SECTION_TO_CATEGORY['authentication']).toBe('security');
    expect(SECTION_TO_CATEGORY['desktop-quickstart']).toBe('desktop');
    expect(SECTION_TO_CATEGORY['fast-mode']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['keybindings']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['permissions']).toBe('security');
    expect(SECTION_TO_CATEGORY['remote-control']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['server-managed-settings']).toBe('settings');
    expect(SECTION_TO_CATEGORY['zero-data-retention']).toBe('security');
  });

  it('maps new sections to categories', () => {
    expect(SECTION_TO_CATEGORY['quickstart']).toBe('getting-started');
    expect(SECTION_TO_CATEGORY['setup']).toBe('getting-started');
    expect(SECTION_TO_CATEGORY['amazon-bedrock']).toBe('providers');
    expect(SECTION_TO_CATEGORY['google-vertex-ai']).toBe('providers');
    expect(SECTION_TO_CATEGORY['vs-code']).toBe('ide');
    expect(SECTION_TO_CATEGORY['github-actions']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['sandboxing']).toBe('security');
    expect(SECTION_TO_CATEGORY['model-config']).toBe('config');
  });

  it('maps channels segments to channels category', () => {
    expect(SECTION_TO_CATEGORY['channels']).toBe('channels');
    expect(SECTION_TO_CATEGORY['channels-reference']).toBe('channels');
  });

  it('maps automation segments to automation category', () => {
    expect(SECTION_TO_CATEGORY['headless']).toBe('automation');
    expect(SECTION_TO_CATEGORY['scheduled-tasks']).toBe('automation');
    expect(SECTION_TO_CATEGORY['web-scheduled-tasks']).toBe('automation');
  });

  it('maps remaining unmapped segments to correct categories', () => {
    expect(SECTION_TO_CATEGORY['code-review']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['env-vars']).toBe('config');
    expect(SECTION_TO_CATEGORY['permission-modes']).toBe('security');
    expect(SECTION_TO_CATEGORY['platforms']).toBe('overview');
    expect(SECTION_TO_CATEGORY['tools-reference']).toBe('cli');
    expect(SECTION_TO_CATEGORY['voice-dictation']).toBe('interactive');
  });
});

describe('CATEGORY_ALIASES', () => {
  it('maps aliases to canonical categories', () => {
    expect(CATEGORY_ALIASES['subagents']).toBe('agents');
    expect(CATEGORY_ALIASES['sub-agents']).toBe('agents');
    expect(CATEGORY_ALIASES['slash-commands']).toBe('commands');
    expect(CATEGORY_ALIASES['claude-md']).toBe('memory');
    expect(CATEGORY_ALIASES['configuration']).toBe('config');
  });
});
