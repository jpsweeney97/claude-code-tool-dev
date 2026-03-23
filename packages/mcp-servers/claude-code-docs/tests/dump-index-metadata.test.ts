import { describe, it, expect } from 'vitest';
import type { BM25Index } from '../src/bm25.js';
import type { Chunk } from '../src/types.js';
import { computeTermFreqs } from '../src/chunk-helpers.js';
import { tokenize } from '../src/tokenizer.js';
import {
  buildMetadataResponse,
  extractCodeLiterals,
  extractConfigKeys,
  extractHeadings,
  computeDistinctiveTerms,
  DumpIndexMetadataOutputSchema,
} from '../src/dump-index-metadata.js';

function makeChunk(
  id: string,
  content: string,
  opts: {
    category?: string;
    source_file?: string;
    heading?: string;
    merged_headings?: string[];
  } = {},
): Chunk {
  const tokens = tokenize(content);
  const headingTokens = new Set<string>();
  if (opts.heading) for (const t of tokenize(opts.heading)) headingTokens.add(t);
  if (opts.merged_headings)
    for (const h of opts.merged_headings)
      for (const t of tokenize(h)) headingTokens.add(t);

  return {
    id,
    content,
    tokens,
    tokenCount: tokens.length,
    termFreqs: computeTermFreqs(tokens),
    category: opts.category ?? 'test',
    tags: [],
    source_file: opts.source_file ?? 'test.md',
    heading: opts.heading,
    merged_headings: opts.merged_headings,
    headingTokens: headingTokens.size > 0 ? headingTokens : undefined,
  };
}

function makeIndex(chunks: Chunk[]): BM25Index {
  const docFrequency = new Map<string, number>();
  const invertedIndex = new Map<string, Set<number>>();
  const totalLength = chunks.reduce((sum, c) => sum + c.tokenCount, 0);

  for (let i = 0; i < chunks.length; i++) {
    const uniqueTerms = new Set(chunks[i].tokens);
    for (const term of uniqueTerms) {
      docFrequency.set(term, (docFrequency.get(term) ?? 0) + 1);
      let postings = invertedIndex.get(term);
      if (!postings) {
        postings = new Set();
        invertedIndex.set(term, postings);
      }
      postings.add(i);
    }
  }

  return {
    chunks,
    avgDocLength: chunks.length > 0 ? totalLength / chunks.length : 0,
    docFrequency,
    invertedIndex,
  };
}

// ---------------------------------------------------------------------------
// extractCodeLiterals
// ---------------------------------------------------------------------------
describe('extractCodeLiterals', () => {
  it('extracts backticked identifiers from content', () => {
    const content = 'Use `PreToolUse` hook with `permissionDecision` output.';
    expect(extractCodeLiterals(content)).toEqual(['PreToolUse', 'permissionDecision']);
  });

  it('deduplicates within a single content string', () => {
    const content = 'The `foo` value and the `foo` value again.';
    expect(extractCodeLiterals(content)).toEqual(['foo']);
  });

  it('handles dotted property paths', () => {
    const content = 'Set `hookSpecificOutput.permissionDecision` to control it.';
    expect(extractCodeLiterals(content)).toEqual(['hookSpecificOutput.permissionDecision']);
  });

  it('returns empty array when no backticked identifiers', () => {
    expect(extractCodeLiterals('No code here.')).toEqual([]);
  });

  it('ignores empty backtick pairs', () => {
    expect(extractCodeLiterals('Empty `` backticks')).toEqual([]);
  });

  it('extracts identifiers with underscores and hyphens', () => {
    const content = 'Use `my_var` and `some-flag` in config.';
    expect(extractCodeLiterals(content)).toEqual(['my_var', 'some-flag']);
  });
});

// ---------------------------------------------------------------------------
// extractConfigKeys
// ---------------------------------------------------------------------------
describe('extractConfigKeys', () => {
  it('extracts dotted paths from code literals', () => {
    const literals = ['hookSpecificOutput.permissionDecision', 'PreToolUse', 'simple'];
    expect(extractConfigKeys(literals)).toContain('hookSpecificOutput.permissionDecision');
  });

  it('extracts camelCase identifiers as config keys', () => {
    const literals = ['hookSpecificOutput', 'permissionDecision', 'UPPER', 'lower'];
    const keys = extractConfigKeys(literals);
    expect(keys).toContain('hookSpecificOutput');
    expect(keys).toContain('permissionDecision');
  });

  it('excludes all-uppercase and all-lowercase identifiers without dots', () => {
    const literals = ['ALLCAPS', 'simple', 'noDots'];
    const keys = extractConfigKeys(literals);
    expect(keys).not.toContain('ALLCAPS');
    expect(keys).not.toContain('simple');
    // noDots is camelCase so it qualifies
    expect(keys).toContain('noDots');
  });

  it('returns empty array when no config-like keys', () => {
    expect(extractConfigKeys(['UPPER', 'lower', 'a'])).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// extractHeadings
// ---------------------------------------------------------------------------
describe('extractHeadings', () => {
  it('extracts from heading and merged_headings fields', () => {
    const chunk = makeChunk('c1', 'content', {
      heading: 'PreToolUse',
      merged_headings: ['Hooks', 'Hook Events', 'PreToolUse'],
    });
    expect(extractHeadings(chunk)).toEqual(['Hooks', 'Hook Events', 'PreToolUse']);
  });

  it('uses heading alone when merged_headings absent', () => {
    const chunk = makeChunk('c1', 'content', { heading: 'Overview' });
    expect(extractHeadings(chunk)).toEqual(['Overview']);
  });

  it('falls back to markdown headings from content', () => {
    const chunk = makeChunk('c1', '# Main Title\n\nSome text\n\n## Sub Section\n\nMore text');
    expect(extractHeadings(chunk)).toEqual(['Main Title', 'Sub Section']);
  });

  it('returns empty array when no headings anywhere', () => {
    const chunk = makeChunk('c1', 'Just some plain text without any headings.');
    expect(extractHeadings(chunk)).toEqual([]);
  });

  it('deduplicates headings', () => {
    const chunk = makeChunk('c1', 'content', {
      heading: 'Hooks',
      merged_headings: ['Hooks', 'Hooks'],
    });
    expect(extractHeadings(chunk)).toEqual(['Hooks']);
  });
});

// ---------------------------------------------------------------------------
// computeDistinctiveTerms
// ---------------------------------------------------------------------------
describe('computeDistinctiveTerms', () => {
  it('returns code literals appearing in 3 or fewer chunks', () => {
    // 4 chunks: literal "PreToolUse" appears in 2, "hooks" appears in all 4
    const c1 = makeChunk('c1', 'Use `PreToolUse` with `hooks` config', { category: 'hooks' });
    const c2 = makeChunk('c2', 'The `PreToolUse` event and `hooks` system', { category: 'hooks' });
    const c3 = makeChunk('c3', 'Configure `hooks` settings', { category: 'hooks' });
    const c4 = makeChunk('c4', 'More about `hooks` internals', { category: 'hooks' });
    const index = makeIndex([c1, c2, c3, c4]);

    // For chunk c1, PreToolUse is in 2 chunks (<=3), hooks is in 4 chunks (>3)
    const distinctive = computeDistinctiveTerms(c1, index);
    expect(distinctive).toContain('PreToolUse');
    expect(distinctive).not.toContain('hooks');
  });

  it('returns empty when all literals are common', () => {
    const c1 = makeChunk('c1', 'Use `common`', { category: 'a' });
    const c2 = makeChunk('c2', 'The `common` thing', { category: 'a' });
    const c3 = makeChunk('c3', 'More `common` stuff', { category: 'a' });
    const c4 = makeChunk('c4', 'Even `common` more', { category: 'a' });
    const index = makeIndex([c1, c2, c3, c4]);

    expect(computeDistinctiveTerms(c1, index)).toEqual([]);
  });

  it('returns empty when chunk has no code literals', () => {
    const c1 = makeChunk('c1', 'No backticks here', { category: 'a' });
    const index = makeIndex([c1]);
    expect(computeDistinctiveTerms(c1, index)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// buildMetadataResponse — empty index
// ---------------------------------------------------------------------------
describe('buildMetadataResponse — empty index', () => {
  it('returns empty categories and null docs_epoch', () => {
    const index = makeIndex([]);
    const result = buildMetadataResponse(index, null);

    expect(result.categories).toEqual([]);
    expect(result.docs_epoch).toBeNull();
    expect(result.index_version).toBeDefined();
    expect(result.built_at).toBeDefined();
  });

  it('validates against the output schema', () => {
    const index = makeIndex([]);
    const result = buildMetadataResponse(index, null);
    const parsed = DumpIndexMetadataOutputSchema.safeParse(result);
    expect(parsed.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// buildMetadataResponse — chunks grouped by category
// ---------------------------------------------------------------------------
describe('buildMetadataResponse — category grouping', () => {
  it('groups chunks by category with correct counts', () => {
    const c1 = makeChunk('hooks#pretooluse', 'Use `PreToolUse` hook', {
      category: 'hooks',
      source_file: 'https://code.claude.com/docs/en/hooks',
      heading: 'PreToolUse',
      merged_headings: ['Hooks', 'Hook Events', 'PreToolUse'],
    });
    const c2 = makeChunk('hooks#posttooluse', 'Use `PostToolUse` hook', {
      category: 'hooks',
      source_file: 'https://code.claude.com/docs/en/hooks',
      heading: 'PostToolUse',
      merged_headings: ['Hooks', 'Hook Events', 'PostToolUse'],
    });
    const c3 = makeChunk('skills#overview', 'Create `SKILL.md` files', {
      category: 'skills',
      source_file: 'https://code.claude.com/docs/en/skills',
      heading: 'Overview',
    });
    const index = makeIndex([c1, c2, c3]);
    const result = buildMetadataResponse(index, 'abc123');

    expect(result.docs_epoch).toBe('abc123');
    expect(result.categories).toHaveLength(2);

    const hooksCategory = result.categories.find((c) => c.name === 'hooks');
    expect(hooksCategory).toBeDefined();
    expect(hooksCategory!.chunk_count).toBe(2);
    expect(hooksCategory!.chunks).toHaveLength(2);

    const skillsCategory = result.categories.find((c) => c.name === 'skills');
    expect(skillsCategory).toBeDefined();
    expect(skillsCategory!.chunk_count).toBe(1);
  });

  it('includes category aliases from CATEGORY_ALIASES', () => {
    const c1 = makeChunk('agents#overview', 'Agent docs', {
      category: 'agents',
      source_file: 'agents.md',
    });
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const agentsCategory = result.categories.find((c) => c.name === 'agents');
    expect(agentsCategory).toBeDefined();
    // agents has aliases: subagents, sub-agents
    expect(agentsCategory!.aliases).toContain('subagents');
    expect(agentsCategory!.aliases).toContain('sub-agents');
  });

  it('returns empty aliases for categories without aliases', () => {
    const c1 = makeChunk('hooks#a', 'hook content', {
      category: 'hooks',
      source_file: 'hooks.md',
    });
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const hooksCategory = result.categories.find((c) => c.name === 'hooks');
    expect(hooksCategory!.aliases).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// buildMetadataResponse — chunk fields
// ---------------------------------------------------------------------------
describe('buildMetadataResponse — chunk fields', () => {
  it('extracts headings from chunk fields', () => {
    const c1 = makeChunk('hooks#pretooluse', 'Use `PreToolUse` with `permissionDecision`', {
      category: 'hooks',
      source_file: 'https://code.claude.com/docs/en/hooks',
      heading: 'PreToolUse',
      merged_headings: ['Hooks', 'Hook Events', 'PreToolUse'],
    });
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const chunk = result.categories[0].chunks[0];
    expect(chunk.headings).toEqual(['Hooks', 'Hook Events', 'PreToolUse']);
  });

  it('extracts code_literals from backticked identifiers', () => {
    const c1 = makeChunk(
      'hooks#pretooluse',
      'Use `PreToolUse` hook with `permissionDecision` and `updatedInput` output.',
      {
        category: 'hooks',
        source_file: 'hooks.md',
        heading: 'PreToolUse',
      },
    );
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const chunk = result.categories[0].chunks[0];
    expect(chunk.code_literals).toContain('PreToolUse');
    expect(chunk.code_literals).toContain('permissionDecision');
    expect(chunk.code_literals).toContain('updatedInput');
  });

  it('extracts config_keys from dotted paths and camelCase identifiers', () => {
    const c1 = makeChunk(
      'hooks#output',
      'Set `hookSpecificOutput.permissionDecision` for the `PreToolUse` event.',
      {
        category: 'hooks',
        source_file: 'hooks.md',
        heading: 'Output',
      },
    );
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const chunk = result.categories[0].chunks[0];
    expect(chunk.config_keys).toContain('hookSpecificOutput.permissionDecision');
    // PreToolUse is PascalCase which has mixed case → qualifies as config key
    expect(chunk.config_keys).toContain('PreToolUse');
  });

  it('includes distinctive_terms for literals in ≤3 chunks', () => {
    // PreToolUse appears in 1 chunk, common appears in 4
    const c1 = makeChunk('hooks#pretooluse', 'Use `PreToolUse` and `common`', {
      category: 'hooks',
      source_file: 'hooks.md',
    });
    const c2 = makeChunk('hooks#a', 'The `common` thing', { category: 'hooks', source_file: 'hooks.md' });
    const c3 = makeChunk('hooks#b', 'More `common` stuff', { category: 'hooks', source_file: 'hooks.md' });
    const c4 = makeChunk('hooks#c', 'Even more `common`', { category: 'hooks', source_file: 'hooks.md' });
    const index = makeIndex([c1, c2, c3, c4]);
    const result = buildMetadataResponse(index, 'hash');

    const preToolUseChunk = result.categories[0].chunks.find(
      (c) => c.chunk_id === 'hooks#pretooluse',
    );
    expect(preToolUseChunk).toBeDefined();
    expect(preToolUseChunk!.distinctive_terms).toContain('PreToolUse');
    expect(preToolUseChunk!.distinctive_terms).not.toContain('common');
  });

  it('passes chunk_id and source_file through', () => {
    const c1 = makeChunk('hooks#pretooluse', 'content', {
      category: 'hooks',
      source_file: 'https://code.claude.com/docs/en/hooks',
    });
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash');

    const chunk = result.categories[0].chunks[0];
    expect(chunk.chunk_id).toBe('hooks#pretooluse');
    expect(chunk.source_file).toBe('https://code.claude.com/docs/en/hooks');
  });
});

// ---------------------------------------------------------------------------
// buildMetadataResponse — docs_epoch passthrough
// ---------------------------------------------------------------------------
describe('buildMetadataResponse — docs_epoch', () => {
  it('passes through a non-null contentHash', () => {
    const index = makeIndex([]);
    const result = buildMetadataResponse(index, 'sha256-abc123');
    expect(result.docs_epoch).toBe('sha256-abc123');
  });

  it('passes through null when no contentHash', () => {
    const index = makeIndex([]);
    const result = buildMetadataResponse(index, null);
    expect(result.docs_epoch).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Output schema validation
// ---------------------------------------------------------------------------
describe('DumpIndexMetadataOutputSchema', () => {
  it('validates a complete response', () => {
    const c1 = makeChunk('hooks#pretooluse', 'Use `PreToolUse` with `permissionDecision`', {
      category: 'hooks',
      source_file: 'https://code.claude.com/docs/en/hooks',
      heading: 'PreToolUse',
      merged_headings: ['Hooks', 'Hook Events', 'PreToolUse'],
    });
    const index = makeIndex([c1]);
    const result = buildMetadataResponse(index, 'hash123');
    const parsed = DumpIndexMetadataOutputSchema.safeParse(result);
    expect(parsed.success).toBe(true);
  });

  it('rejects response missing required fields', () => {
    const parsed = DumpIndexMetadataOutputSchema.safeParse({
      // Missing index_version, built_at, categories
      docs_epoch: null,
    });
    expect(parsed.success).toBe(false);
  });
});
