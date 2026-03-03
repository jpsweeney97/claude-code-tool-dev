import { describe, it, expect, beforeEach } from 'vitest';
import {
  parseFrontmatter,
  formatMetadataHeader,
  deriveCategory,
  getParseWarnings,
  clearParseWarnings,
  getUnmappedSegments,
} from '../src/frontmatter.js';

describe('parseFrontmatter', () => {
  beforeEach(() => {
    clearParseWarnings();
  });

  it('returns empty frontmatter for content without YAML', () => {
    const { frontmatter, body } = parseFrontmatter('Just content', 'test.md');
    expect(frontmatter).toEqual({});
    expect(body).toBe('Just content');
  });

  it('parses valid YAML frontmatter', () => {
    const content = '---\ncategory: hooks\ntags: [api, schema]\ntopic: input\n---\nBody content';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.category).toBe('hooks');
    expect(frontmatter.tags).toEqual(['api', 'schema']);
    expect(frontmatter.topic).toBe('input');
    expect(body).toBe('Body content');
  });

  it('handles single string tag', () => {
    const content = '---\ntags: api\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.tags).toEqual(['api']);
  });

  it('warns on non-string tag values', () => {
    const content = '---\ntags: [123, "valid"]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Non-string tag value ignored: number',
    });
  });

  it('warns on non-string category', () => {
    const content = '---\ncategory: [hooks, skills]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid category type: expected string, got object',
    });
  });

  it('warns on non-string topic', () => {
    const content = '---\ntopic: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid topic type: expected string, got number',
    });
  });

  it('warns on malformed YAML', () => {
    const content = '---\n[unclosed\n---\nBody';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter).toEqual({});
    expect(body).toBe('---\n[unclosed\n---\nBody');
    const warnings = getParseWarnings();
    expect(warnings.length).toBeGreaterThan(0);
    expect(warnings[0].file).toBe('test.md');
  });

  it('normalizes CRLF line endings', () => {
    const content = '---\r\ncategory: hooks\r\n---\r\nBody';
    const { frontmatter, body } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.category).toBe('hooks');
    expect(body).toBe('Body');
  });
});

describe('formatMetadataHeader', () => {
  it('returns empty string for empty frontmatter', () => {
    expect(formatMetadataHeader({})).toBe('');
  });

  it('formats category', () => {
    expect(formatMetadataHeader({ category: 'hooks' })).toBe('Category: hooks\n\n');
  });

  it('formats tags', () => {
    expect(formatMetadataHeader({ tags: ['api', 'schema'] })).toBe('Tags: api, schema\n\n');
  });

  it('formats all fields in v2 order (Topic, ID, Category, Tags)', () => {
    const header = formatMetadataHeader({
      category: 'hooks',
      tags: ['api'],
      topic: 'input',
      id: 'hooks-input',
    });
    expect(header).toBe('Topic: input\nID: hooks-input\nCategory: hooks\nTags: api\n\n');
  });
});

describe('deriveCategory', () => {
  // File path tests (original behavior)
  it('extracts category from path', () => {
    expect(deriveCategory('hooks/input-schema.md')).toBe('hooks');
  });

  it('returns general for root files', () => {
    expect(deriveCategory('readme.md')).toBe('general');
  });

  // URL tests (new behavior)
  it('extracts category from URL with language code', () => {
    expect(deriveCategory('https://code.claude.com/docs/en/hooks')).toBe('hooks');
    expect(deriveCategory('https://code.claude.com/docs/en/skills')).toBe('skills');
    expect(deriveCategory('https://code.claude.com/docs/en/mcp')).toBe('mcp');
  });

  it('extracts category from URL without language code', () => {
    expect(deriveCategory('https://code.claude.com/docs/hooks')).toBe('hooks');
    expect(deriveCategory('https://code.claude.com/docs/plugins')).toBe('plugins');
  });

  it('handles nested URL paths', () => {
    expect(deriveCategory('https://code.claude.com/docs/en/hooks/input-schema')).toBe('hooks');
    expect(deriveCategory('https://code.claude.com/docs/en/mcp/servers')).toBe('mcp');
    expect(deriveCategory('https://code.claude.com/docs/en/agents/sub-agents')).toBe('agents');
  });

  it('handles hyphenated URL sections via SECTION_TO_CATEGORY mapping', () => {
    // These URL sections map to canonical categories
    expect(deriveCategory('https://code.claude.com/docs/en/slash-commands')).toBe('commands');
    expect(deriveCategory('https://code.claude.com/docs/en/plugin-marketplaces')).toBe(
      'plugin-marketplaces',
    );
    expect(deriveCategory('https://code.claude.com/docs/en/claude-md')).toBe('memory');
    expect(deriveCategory('https://code.claude.com/docs/en/sub-agents')).toBe('agents');
  });

  it('handles regional language codes (zh-cn, pt-br)', () => {
    expect(deriveCategory('https://code.claude.com/docs/zh-cn/hooks')).toBe('hooks');
    expect(deriveCategory('https://code.claude.com/docs/pt-br/skills')).toBe('skills');
  });

  it('returns overview for URL with no content path', () => {
    expect(deriveCategory('https://code.claude.com/')).toBe('overview');
    expect(deriveCategory('https://code.claude.com/docs/en/')).toBe('overview');
  });

  it('returns overview for unknown URL sections', () => {
    // Unknown sections default to overview, not the first segment
    expect(deriveCategory('https://example.com/custom/page')).toBe('overview');
  });

  // New tests for SECTION_TO_CATEGORY mapping
  it('uses SECTION_TO_CATEGORY mapping for URLs', () => {
    // Known sections map to their category
    expect(deriveCategory('https://code.claude.com/docs/en/quickstart')).toBe('getting-started');
    expect(deriveCategory('https://code.claude.com/docs/en/amazon-bedrock')).toBe('providers');
    expect(deriveCategory('https://code.claude.com/docs/en/vs-code')).toBe('ide');
    expect(deriveCategory('https://code.claude.com/docs/en/github-actions')).toBe('ci-cd');
  });

  it('returns overview for unmapped URL sections', () => {
    // Unknown sections default to 'overview' not 'general'
    expect(deriveCategory('https://code.claude.com/docs/en/unknown-page')).toBe('overview');
    expect(deriveCategory('https://code.claude.com/docs/en/some-new-page')).toBe('overview');
  });
});

describe('parseFrontmatter - requires and related_to', () => {
  beforeEach(() => {
    clearParseWarnings();
  });

  it('parses requires as array of strings', () => {
    const content = '---\nrequires: [hooks-overview, hooks-events]\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.requires).toEqual(['hooks-overview', 'hooks-events']);
  });

  it('parses requires as single string', () => {
    const content = '---\nrequires: hooks-overview\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.requires).toEqual(['hooks-overview']);
  });

  it('parses related_to as array of strings', () => {
    const content = '---\nrelated_to: [skills-overview, commands-overview]\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.related_to).toEqual(['skills-overview', 'commands-overview']);
  });

  it('parses related_to as single string', () => {
    const content = '---\nrelated_to: skills-overview\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.related_to).toEqual(['skills-overview']);
  });

  it('warns on non-string requires items', () => {
    const content = '---\nrequires: [123, "valid"]\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid requires item type: expected string, got number',
    });
  });

  it('warns on invalid requires type', () => {
    const content = '---\nrequires: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid requires type: expected string or array, got number',
    });
  });

  it('parses id field', () => {
    const content = '---\nid: hooks-exit-codes\n---\nBody';
    const { frontmatter } = parseFrontmatter(content, 'test.md');
    expect(frontmatter.id).toBe('hooks-exit-codes');
  });

  it('warns on non-string id', () => {
    const content = '---\nid: 123\n---\nBody';
    parseFrontmatter(content, 'test.md');
    const warnings = getParseWarnings();
    expect(warnings).toContainEqual({
      file: 'test.md',
      issue: 'Invalid id type: expected string, got number',
    });
  });
});

describe('parseFrontmatter warnings', () => {
  it('returns warnings in result instead of global state', () => {
    const content = '---\ncategory: [invalid]\n---\nBody';
    const { warnings } = parseFrontmatter(content, 'test.md');

    expect(warnings).toBeDefined();
    expect(Array.isArray(warnings)).toBe(true);
  });

  it('isolates warnings between calls', () => {
    // First call with invalid content
    const { warnings: w1 } = parseFrontmatter('---\ncategory: [x]\n---\n', 'a.md');

    // Second call with valid content
    const { warnings: w2 } = parseFrontmatter('---\ncategory: valid\n---\n', 'b.md');

    // Second call should have no warnings (isolated)
    expect(w2.length).toBe(0);
  });
});

describe('getUnmappedSegments', () => {
  it('returns empty for fully mapped URL', () => {
    expect(getUnmappedSegments('https://code.claude.com/docs/en/hooks')).toEqual([]);
  });

  it('returns empty when at least one segment is mapped (URL is categorizable)', () => {
    // 'hooks' is mapped, 'input-schema' is not — but URL is categorizable
    expect(getUnmappedSegments('https://code.claude.com/docs/en/hooks/input-schema')).toEqual([]);
  });

  it('returns all segments when no segment is mapped (URL is uncategorizable)', () => {
    expect(getUnmappedSegments('https://code.claude.com/docs/en/unknown-page')).toEqual(['unknown-page']);
  });

  it('returns empty for empty sourceUrl', () => {
    expect(getUnmappedSegments('')).toEqual([]);
  });

  it('does not match prototype properties as mapped', () => {
    // Object.hasOwn prevents 'constructor' from matching via Object.prototype
    expect(getUnmappedSegments('https://code.claude.com/docs/en/constructor')).toEqual(['constructor']);
  });

  it('returns empty for invalid URL', () => {
    expect(getUnmappedSegments('not-a-url')).toEqual([]);
  });
});
