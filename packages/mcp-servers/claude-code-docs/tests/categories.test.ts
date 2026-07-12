// tests/categories.test.ts
import { describe, it, expect } from 'vitest';
import { KNOWN_CATEGORIES, SECTION_TO_CATEGORY, CATEGORY_ALIASES, resolveSegmentCategory } from '../src/categories.js';

describe('KNOWN_CATEGORIES', () => {
  it('contains all 29 canonical categories', () => {
    const expected = [
      // Extension categories (10)
      'hooks', 'skills', 'commands', 'agents', 'plugins',
      'plugin-marketplaces', 'mcp', 'channels', 'settings', 'memory',
      // General categories (19)
      'overview', 'getting-started', 'cli', 'best-practices',
      'interactive', 'security', 'providers', 'gateways', 'ide', 'ci-cd',
      'automation', 'agent-sdk', 'desktop', 'integrations', 'config',
      'operations', 'troubleshooting', 'changelog', 'uncategorized',
    ];

    expect(KNOWN_CATEGORIES.size).toBe(29);
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
    expect(KNOWN_CATEGORIES.has('gateway')).toBe(false);
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
    expect(SECTION_TO_CATEGORY['desktop-scheduled-tasks']).toBe('automation');
    expect(SECTION_TO_CATEGORY['computer-use']).toBe('automation');
    expect(SECTION_TO_CATEGORY['routines']).toBe('automation');
  });

  it('maps agent-sdk segment to agent-sdk category', () => {
    expect(SECTION_TO_CATEGORY['agent-sdk']).toBe('agent-sdk');
  });

  it('maps remaining unmapped segments to correct categories', () => {
    expect(SECTION_TO_CATEGORY['code-review']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['github-enterprise-server']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['env-vars']).toBe('config');
    expect(SECTION_TO_CATEGORY['permission-modes']).toBe('security');
    expect(SECTION_TO_CATEGORY['platforms']).toBe('overview');
    expect(SECTION_TO_CATEGORY['context-window']).toBe('overview');
    expect(SECTION_TO_CATEGORY['tools-reference']).toBe('cli');
    expect(SECTION_TO_CATEGORY['voice-dictation']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['ultraplan']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['fullscreen']).toBe('desktop');
    expect(SECTION_TO_CATEGORY['web-quickstart']).toBe('getting-started');
    expect(SECTION_TO_CATEGORY['whats-new']).toBe('changelog');
    expect(SECTION_TO_CATEGORY['claude-directory']).toBe('plugins');
  });

  it('maps the gateway family to gateways', () => {
    expect(SECTION_TO_CATEGORY['gateways']).toBe('gateways');
    expect(SECTION_TO_CATEGORY['claude-apps-gateway']).toBe('gateways');
    expect(SECTION_TO_CATEGORY['llm-gateway']).toBe('gateways');
  });

  it('maps segments added with the 2026-07 corpus growth', () => {
    expect(SECTION_TO_CATEGORY['agents']).toBe('agents');
    expect(SECTION_TO_CATEGORY['agent-view']).toBe('agents');
    expect(SECTION_TO_CATEGORY['admin-setup']).toBe('settings');
    expect(SECTION_TO_CATEGORY['auto-mode-config']).toBe('security');
    expect(SECTION_TO_CATEGORY['sandbox-environments']).toBe('security');
    expect(SECTION_TO_CATEGORY['claude-platform-on-aws']).toBe('providers');
    expect(SECTION_TO_CATEGORY['managed-mcp']).toBe('mcp');
    expect(SECTION_TO_CATEGORY['plugin-dependencies']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['plugin-hints']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['plugin-relevance']).toBe('plugins');
    expect(SECTION_TO_CATEGORY['debug-your-config']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['troubleshoot-install']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['errors']).toBe('troubleshooting');
    expect(SECTION_TO_CATEGORY['ultrareview']).toBe('ci-cd');
    expect(SECTION_TO_CATEGORY['feature-availability']).toBe('overview');
    expect(SECTION_TO_CATEGORY['glossary']).toBe('overview');
    expect(SECTION_TO_CATEGORY['large-codebases']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['prompt-library']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['champion-kit']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['communications-kit']).toBe('best-practices');
    expect(SECTION_TO_CATEGORY['sessions']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['worktrees']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['advisor']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['artifacts']).toBe('interactive');
    expect(SECTION_TO_CATEGORY['deep-links']).toBe('integrations');
    expect(SECTION_TO_CATEGORY['workflows']).toBe('automation');
    expect(SECTION_TO_CATEGORY['goal']).toBe('automation');
    expect(SECTION_TO_CATEGORY['prompt-caching']).toBe('operations');
  });

  it('all values target a known category', () => {
    for (const [segment, category] of Object.entries(SECTION_TO_CATEGORY)) {
      expect(
        KNOWN_CATEGORIES.has(category),
        `segment '${segment}' maps to unknown category '${category}'`,
      ).toBe(true);
    }
  });
});

describe('CATEGORY_ALIASES', () => {
  it('maps aliases to canonical categories', () => {
    expect(CATEGORY_ALIASES['subagents']).toBe('agents');
    expect(CATEGORY_ALIASES['sub-agents']).toBe('agents');
    expect(CATEGORY_ALIASES['slash-commands']).toBe('commands');
    expect(CATEGORY_ALIASES['claude-md']).toBe('memory');
    expect(CATEGORY_ALIASES['configuration']).toBe('config');
    expect(CATEGORY_ALIASES['gateway']).toBe('gateways');
  });
});

describe('resolveSegmentCategory', () => {
  it('resolves exact keys', () => {
    expect(resolveSegmentCategory('hooks')).toBe('hooks');
    expect(resolveSegmentCategory('llm-gateway')).toBe('gateways');
  });

  it('resolves family sub-pages by hyphen-bounded prefix', () => {
    expect(resolveSegmentCategory('llm-gateway-rollout')).toBe('gateways');
    expect(resolveSegmentCategory('claude-apps-gateway-on-gcp')).toBe('gateways');
    expect(resolveSegmentCategory('mcp-quickstart')).toBe('mcp');
    expect(resolveSegmentCategory('security-guidance')).toBe('security');
    expect(resolveSegmentCategory('desktop-linux')).toBe('desktop');
  });

  it('prefers the longest matching key', () => {
    // 'desktop-scheduled-tasks' has its own key (automation); the shorter
    // 'desktop' prefix (desktop) must not shadow it — including for deeper
    // hypothetical sub-pages of the more specific family.
    expect(resolveSegmentCategory('desktop-scheduled-tasks')).toBe('automation');
    expect(resolveSegmentCategory('desktop-scheduled-tasks-reference')).toBe('automation');
  });

  it('returns null for unknown segments and bare-prefix lookalikes', () => {
    expect(resolveSegmentCategory('nonexistent-page')).toBe(null);
    expect(resolveSegmentCategory('pluginsomething')).toBe(null);
    expect(resolveSegmentCategory('constructor')).toBe(null);
  });
});

describe('KNOWN_CATEGORIES: uncategorized fallback', () => {
  it("includes 'uncategorized' for fallback classification", () => {
    expect(KNOWN_CATEGORIES.has('uncategorized')).toBe(true);
  });
});
