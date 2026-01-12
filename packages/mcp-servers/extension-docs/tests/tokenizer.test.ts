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
    expect(tokenize('pre-tool-use')).toEqual(['pre', 'tool', 'use']);
  });

  it('splits on underscores', () => {
    expect(tokenize('pre_tool_use')).toEqual(['pre', 'tool', 'use']);
  });

  it('drops single characters', () => {
    expect(tokenize('a b c')).toEqual([]);
  });

  it('keeps two-character terms', () => {
    expect(tokenize('go is ok')).toEqual(['go', 'is', 'ok']);
  });
});
