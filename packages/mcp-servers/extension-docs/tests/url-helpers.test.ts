import { describe, it, expect } from 'vitest';
import {
  isHttpUrl,
  urlPathSegments,
  docsContentSegments,
  extractContentPath,
} from '../src/url-helpers.js';

describe('isHttpUrl', () => {
  it('returns true for https URLs', () => {
    expect(isHttpUrl('https://code.claude.com/docs/en/hooks')).toBe(true);
    expect(isHttpUrl('https://example.com')).toBe(true);
  });

  it('returns true for http URLs', () => {
    expect(isHttpUrl('http://localhost:3000')).toBe(true);
  });

  it('returns false for file paths', () => {
    expect(isHttpUrl('hooks/overview.md')).toBe(false);
    expect(isHttpUrl('/absolute/path.md')).toBe(false);
    expect(isHttpUrl('./relative/path.md')).toBe(false);
  });

  it('returns false for other protocols', () => {
    expect(isHttpUrl('ftp://files.example.com')).toBe(false);
    expect(isHttpUrl('file:///local/file')).toBe(false);
  });
});

describe('urlPathSegments', () => {
  it('extracts path segments from valid URLs', () => {
    expect(urlPathSegments('https://code.claude.com/docs/en/hooks')).toEqual([
      'docs',
      'en',
      'hooks',
    ]);
    expect(urlPathSegments('https://example.com/a/b/c')).toEqual(['a', 'b', 'c']);
  });

  it('handles URLs with trailing slashes', () => {
    expect(urlPathSegments('https://example.com/docs/en/')).toEqual(['docs', 'en']);
  });

  it('handles root URLs', () => {
    expect(urlPathSegments('https://example.com/')).toEqual([]);
    expect(urlPathSegments('https://example.com')).toEqual([]);
  });

  it('returns empty array for invalid URLs', () => {
    expect(urlPathSegments('not-a-url')).toEqual([]);
    expect(urlPathSegments('')).toEqual([]);
  });
});

describe('docsContentSegments', () => {
  it('strips /docs/{lang}/ prefix when language code present', () => {
    expect(docsContentSegments(['docs', 'en', 'hooks'])).toEqual(['hooks']);
    expect(docsContentSegments(['docs', 'en', 'hooks', 'overview'])).toEqual([
      'hooks',
      'overview',
    ]);
    expect(docsContentSegments(['docs', 'fr', 'skills'])).toEqual(['skills']);
  });

  it('handles regional language codes (zh-cn, pt-br)', () => {
    expect(docsContentSegments(['docs', 'zh-cn', 'hooks'])).toEqual(['hooks']);
    expect(docsContentSegments(['docs', 'pt-br', 'mcp', 'servers'])).toEqual(['mcp', 'servers']);
  });

  it('strips /docs/ prefix when no language code', () => {
    expect(docsContentSegments(['docs', 'hooks'])).toEqual(['hooks']);
    expect(docsContentSegments(['docs', 'hooks', 'overview'])).toEqual(['hooks', 'overview']);
  });

  it('returns segments as-is when no /docs/ prefix', () => {
    expect(docsContentSegments(['hooks', 'overview'])).toEqual(['hooks', 'overview']);
    expect(docsContentSegments(['api', 'v1', 'users'])).toEqual(['api', 'v1', 'users']);
  });

  it('handles empty segments', () => {
    expect(docsContentSegments([])).toEqual([]);
  });

  it('handles /docs/ with nothing after', () => {
    expect(docsContentSegments(['docs'])).toEqual([]);
    expect(docsContentSegments(['docs', 'en'])).toEqual([]);
  });

  it('does not treat category names as language codes', () => {
    // 'mcp' and 'hooks' are not valid language codes (not 2-letter)
    expect(docsContentSegments(['docs', 'mcp'])).toEqual(['mcp']);
    expect(docsContentSegments(['docs', 'hooks'])).toEqual(['hooks']);
  });
});

describe('extractContentPath', () => {
  it('extracts content path from full documentation URLs', () => {
    expect(extractContentPath('https://code.claude.com/docs/en/hooks')).toEqual(['hooks']);
    expect(extractContentPath('https://code.claude.com/docs/en/hooks/input-schema')).toEqual([
      'hooks',
      'input-schema',
    ]);
    expect(extractContentPath('https://code.claude.com/docs/en/mcp/servers')).toEqual([
      'mcp',
      'servers',
    ]);
  });

  it('handles URLs without language code', () => {
    expect(extractContentPath('https://code.claude.com/docs/hooks')).toEqual(['hooks']);
  });

  it('handles URLs without /docs/ prefix', () => {
    expect(extractContentPath('https://example.com/hooks/overview')).toEqual([
      'hooks',
      'overview',
    ]);
  });

  it('returns empty array for non-HTTP URLs', () => {
    expect(extractContentPath('hooks/overview.md')).toEqual([]);
    expect(extractContentPath('/absolute/path')).toEqual([]);
  });

  it('handles edge cases', () => {
    expect(extractContentPath('https://example.com/')).toEqual([]);
    expect(extractContentPath('https://example.com')).toEqual([]);
  });
});
