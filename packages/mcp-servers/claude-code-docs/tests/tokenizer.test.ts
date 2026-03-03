import { describe, it, expect } from 'vitest';
import { tokenize } from '../src/tokenizer.js';

describe('tokenize', () => {
  it('handles empty string', () => {
    expect(tokenize('')).toEqual([]);
  });

  it('handles whitespace-only', () => {
    expect(tokenize('   ')).toEqual([]);
  });

  it('handles punctuation-only', () => {
    expect(tokenize('!@#$%')).toEqual([]);
  });

  it('lowercases terms', () => {
    expect(tokenize('HELLO World')).toEqual(['hello', 'world']);
  });

  it('splits CamelCase', () => {
    expect(tokenize('PreToolUse')).toEqual(['pre', 'tool', 'use']);
  });

  it('handles consecutive capitals (MCPServer)', () => {
    expect(tokenize('MCPServer')).toEqual(['mcp', 'server']);
  });

  it('handles consecutive capitals (JSONSchema)', () => {
    expect(tokenize('JSONSchema')).toEqual(['json', 'schema']);
  });

  it('splits on hyphens', () => {
    // "use" stems to "us" (Porter algorithm) — this is correct behavior
    expect(tokenize('pre-tool-use')).toEqual(['pre', 'tool', 'us']);
  });

  it('splits on underscores', () => {
    // "use" stems to "us" (Porter algorithm) — this is correct behavior
    expect(tokenize('pre_tool_use')).toEqual(['pre', 'tool', 'us']);
  });

  it('drops single characters', () => {
    expect(tokenize('a b c')).toEqual([]);
  });

  it('keeps two-character terms', () => {
    expect(tokenize('go is ok')).toEqual(['go', 'is', 'ok']);
  });

  describe('stemming', () => {
    it('stems plural to singular', () => {
      expect(tokenize('hooks')).toEqual(['hook']);
    });

    it('stems -ing form', () => {
      expect(tokenize('running')).toEqual(['run']);
    });

    it('stems -tion/-ation to common root', () => {
      const configureTokens = tokenize('configure');
      const configurationTokens = tokenize('configuration');
      expect(configureTokens).toEqual(configurationTokens);
    });

    it('protects CamelCase tokens from stemming', () => {
      // "PreToolUse" splits to pre/tool/use — all protected from stemming
      // Without protection, "use" might stem to "us"
      expect(tokenize('PreToolUse')).toEqual(['pre', 'tool', 'use']);
    });

    it('protects acronym tokens from stemming', () => {
      // "MCPServer" splits to mcp/server — all protected
      expect(tokenize('MCPServer')).toEqual(['mcp', 'server']);
    });

    it('stems regular words adjacent to CamelCase', () => {
      // "PreToolUse hooks" — PreToolUse is protected, hooks is stemmed
      expect(tokenize('PreToolUse hooks')).toEqual(['pre', 'tool', 'use', 'hook']);
    });

    it('does not stem NO_STEM words', () => {
      expect(tokenize('claude')).toEqual(['claude']);
      expect(tokenize('anthropic')).toEqual(['anthropic']);
    });

    it('stems hyphenated regular words', () => {
      // "hook-based" → spans ["hook", "based"] → stemmed individually
      const tokens = tokenize('hook-based');
      expect(tokens[0]).toBe('hook');
      // "based" stems to "base"
      expect(tokens[1]).toBe('base');
    });

    it('protects digit-to-uppercase CamelCase', () => {
      // "Pre2Tool" has digit-to-uppercase transition — protected
      expect(tokenize('Pre2Tool')).toEqual(['pre2', 'tool']);
    });

    it('does not stem digit-only tokens', () => {
      // "hooks" stems to "hook", but "123" passes through unchanged
      expect(tokenize('hooks 123')).toEqual(['hook', '123']);
    });

    it('does not produce empty or single-char tokens after stemming', () => {
      const tokens = tokenize('the a is an by');
      for (const t of tokens) {
        expect(t.length).toBeGreaterThanOrEqual(2);
      }
    });
  });
});
