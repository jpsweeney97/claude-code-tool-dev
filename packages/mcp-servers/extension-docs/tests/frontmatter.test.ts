import { describe, it, expect, beforeEach } from 'vitest';
import {
  parseFrontmatter,
  formatMetadataHeader,
  deriveCategory,
  getParseWarnings,
  clearParseWarnings,
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
  it('extracts category from path', () => {
    expect(deriveCategory('hooks/input-schema.md')).toBe('hooks');
  });

  it('returns general for root files', () => {
    expect(deriveCategory('readme.md')).toBe('general');
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
