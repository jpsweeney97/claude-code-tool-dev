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

  it('formats all fields', () => {
    const header = formatMetadataHeader({
      category: 'hooks',
      tags: ['api'],
      topic: 'input',
    });
    expect(header).toBe('Category: hooks\nTags: api\nTopic: input\n\n');
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
