// tests/chunker.test.ts
import { describe, it, expect } from 'vitest';
import { chunkFile, MAX_CHUNK_CHARS } from '../src/chunker.js';
import type { MarkdownFile } from '../src/types.js';

describe('chunkFile', () => {

  describe('whole file chunks', () => {
    it('keeps small file as single chunk', () => {
      const file: MarkdownFile = {
        path: 'test/small.md',
        content: '# Title\n\nSome content here.',
      };
      const { chunks } = chunkFile(file);
      expect(chunks).toHaveLength(1);
      expect(chunks[0].id).toBe('test-small');
    });

    it('includes frontmatter metadata in content', () => {
      const file: MarkdownFile = {
        path: 'hooks/test.md',
        content: '---\ncategory: hooks\ntags: [api]\n---\n# Title\nContent',
      };
      const { chunks } = chunkFile(file);
      expect(chunks[0].content).toContain('Category: hooks');
      expect(chunks[0].content).toContain('Tags: api');
    });

    it('derives category from path when not in frontmatter', () => {
      const file: MarkdownFile = {
        path: 'hooks/test.md',
        content: '# Title\nContent',
      };
      const { chunks } = chunkFile(file);
      expect(chunks[0].category).toBe('hooks');
    });
  });

  describe('splitting at H2', () => {
    it('splits large file at H2 boundaries', () => {
      const lines = ['# Title', '', ...Array(200).fill('Line of content')];
      // Insert H2 headings
      lines[50] = '## Section 1';
      lines[100] = '## Section 2';
      lines[150] = '## Section 3';

      const file: MarkdownFile = {
        path: 'test/large.md',
        content: lines.join('\n'),
      };
      const { chunks } = chunkFile(file);
      expect(chunks.length).toBeGreaterThan(1);
    });

    it('includes intro content in first H2 chunk', () => {
      const content = '# Title\n\nIntro paragraph.\n\n## Section 1\nSection content.\n\n## Section 2\nMore content.';
      // Pad to exceed 150 lines
      const padded = content + '\n' + Array(150).fill('padding').join('\n');
      const file: MarkdownFile = { path: 'test/intro.md', content: padded };
      const { chunks } = chunkFile(file);

      // First chunk should contain both intro and Section 1
      expect(chunks[0].content).toContain('Intro paragraph');
      expect(chunks[0].content).toContain('## Section 1');
    });

    it('does not split H2 inside code fence', () => {
      const content = [
        '# Title',
        '',
        '```markdown',
        '## This is not a real heading',
        '```',
        '',
        '## Real Heading',
        'Content',
        '',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/fence.md', content };
      const { chunks } = chunkFile(file);

      // Should NOT split at "## This is not a real heading" inside fence
      const fenceChunk = chunks.find((c) => c.content.includes('```markdown'));
      expect(fenceChunk?.content).toContain('## This is not a real heading');
    });

    it('handles indented code fences (0-3 spaces)', () => {
      const content = [
        '# Title',
        '',
        '   ```python',
        '## Not a heading',
        '   ```',
        '',
        '## Real Heading',
        'Content',
        '',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/indented.md', content };
      const { chunks } = chunkFile(file);

      // Indented fence should be recognized
      const fenceChunk = chunks.find((c) => c.content.includes('```python'));
      expect(fenceChunk?.content).toContain('## Not a heading');
    });
  });

  describe('merging small chunks', () => {
    it('merges small consecutive chunks', () => {
      // Create file with many small H2 sections
      const sections = Array.from({ length: 10 }, (_, i) => `## Section ${i}\nShort content.`);
      const content = ['# Title', '', ...sections, '', ...Array(150).fill('pad')].join('\n');

      const file: MarkdownFile = { path: 'test/merge.md', content };
      const { chunks } = chunkFile(file);

      // Should have fewer chunks than sections due to merging
      expect(chunks.length).toBeLessThan(10);
    });

    it('records merged_headings', () => {
      const sections = Array.from({ length: 5 }, (_, i) => `## Section ${i}\nShort.`);
      const content = ['# Title', '', ...sections, '', ...Array(150).fill('pad')].join('\n');

      const file: MarkdownFile = { path: 'test/merged.md', content };
      const { chunks } = chunkFile(file);

      // At least one chunk should have merged_headings
      const mergedChunk = chunks.find((c) => c.merged_headings && c.merged_headings.length > 1);
      expect(mergedChunk).toBeDefined();
    });
  });

  describe('metadata in tokens', () => {
    it('includes category and tags in all chunk tokens', () => {
      const content = [
        '---',
        'category: hooks',
        'tags: [api, schema]',
        '---',
        '# Title',
        'Intro',
        '## Section 1',
        'Content 1',
        '## Section 2',
        'Content 2',
        ...Array(150).fill('pad'),
      ].join('\n');

      const file: MarkdownFile = { path: 'hooks/meta.md', content };
      const { chunks } = chunkFile(file);

      for (const chunk of chunks) {
        // "hooks" stems to "hook" via Porter stemmer
        expect(chunk.tokens).toContain('hook');
        expect(chunk.tokens).toContain('api');
        expect(chunk.tokens).toContain('schema');
      }
    });
  });

  describe('metadata token inclusion', () => {
    it('includes requires/related_to in tokens even when not in body', () => {
      const content = [
        '---',
        'category: hooks',
        'requires: [hooks-overview]',
        'related_to: [hooks-events]',
        '---',
        '# Title',
        '## Section',
        'Body does not mention prerequisites or related pages.',
        ...Array(150).fill('pad'),
      ].join('\n');

      const file: MarkdownFile = { path: 'hooks/x.md', content };
      const { chunks } = chunkFile(file);
      const tokens = chunks[0].tokens;

      // Verify relationship metadata appears in tokens (stemmed)
      expect(tokens).toContain('hook');
      expect(tokens).toContain('overview');
      expect(tokens).toContain('event');
    });

    it('includes id and topic in tokens', () => {
      const content = [
        '---',
        'id: special-doc-id',
        'topic: Special Topic Name',
        'category: test',
        '---',
        '# Title',
        'Body content without id or topic words.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/meta.md', content };
      const { chunks } = chunkFile(file);
      const tokens = chunks[0].tokens;

      // id tokens
      expect(tokens).toContain('special');
      expect(tokens).toContain('doc');
      // topic tokens
      expect(tokens).toContain('topic');
      expect(tokens).toContain('name');
    });

    it('handles requires/related_to as single strings', () => {
      const content = [
        '---',
        'requires: single-prereq',
        'related_to: single-related',
        '---',
        '# Title',
        'Body content.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/single.md', content };
      const { chunks } = chunkFile(file);
      const tokens = chunks[0].tokens;

      // "single" stems to "singl", "related" stems to "relat"
      expect(tokens).toContain('singl');
      expect(tokens).toContain('prereq');
      expect(tokens).toContain('relat');
    });
  });

  describe('hierarchical splitting', () => {
    it('splits oversized H2 at H3 boundaries when available', () => {
      // Simulate a large H2 section with multiple H3 subsections
      const h3Sections = Array.from({ length: 9 }, (_, i) =>
        `### Subsection ${i + 1}\n${Array(15).fill(`Content line ${i}`).join('\n')}`
      ).join('\n\n');

      const content = [
        '---',
        'category: hooks',
        '---',
        '# Title',
        '## Oversized Section',
        h3Sections,
      ].join('\n');

      const file: MarkdownFile = { path: 'hooks/oversized.md', content };
      const { chunks } = chunkFile(file);

      // Should produce multiple chunks
      expect(chunks.length).toBeGreaterThan(1);

      // All chunks within bounds
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
        expect(chunk.content.split('\n').length).toBeLessThanOrEqual(150);
      }
    });

    it('falls back to paragraph splitting when H3 unavailable', () => {
      // Large H2 section with no H3 structure, just paragraphs
      // Each paragraph is ~250 chars, 40 paragraphs = ~10000 chars (exceeds 8000 limit)
      const paragraphs = Array.from({ length: 40 }, (_, i) =>
        Array(10).fill(`Paragraph ${i} content word with more text to make it longer`).join(' ')
      ).join('\n\n');

      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Large Section Without H3',
        paragraphs,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/no-h3.md', content };
      const { chunks } = chunkFile(file);

      // Should produce multiple chunks via paragraph splitting
      expect(chunks.length).toBeGreaterThan(1);

      // All share the same H2 heading reference
      for (const chunk of chunks) {
        expect(chunk.heading).toContain('## Large Section');
      }
    });
  });

  describe('forced split overlap', () => {
    it('forced splits include overlap from previous chunk', () => {
      // Create content that requires hard splitting
      const hugeSection = Array(200).fill('unique-line-content-here').join('\n');
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Huge Section',
        hugeSection,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/overlap.md', content };
      const { chunks } = chunkFile(file);

      // Should produce multiple chunks due to size
      expect(chunks.length).toBeGreaterThan(1);

      // Chunks after the first should start with overlap from previous
      if (chunks.length > 1) {
        const firstChunkLines = chunks[0].content.split('\n');
        const overlapLines = firstChunkLines.slice(-5).join('\n');
        expect(chunks[1].content).toContain(overlapLines);
      }
    });

    it('H2 boundary splits do NOT include overlap', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Section 1',
        ...Array(100).fill('content-a'),
        '## Section 2',
        ...Array(100).fill('content-b'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/no-overlap.md', content };
      const { chunks } = chunkFile(file);

      // Section 2 chunk should NOT start with Section 1 content
      const section2Chunk = chunks.find((c) => c.content.includes('## Section 2'));
      expect(section2Chunk?.content).not.toContain('content-a');
    });
  });

  describe('size guards', () => {
    it('splits file exceeding char limit even if under line limit', () => {
      // 60 lines but >8000 chars
      const longLine = 'x'.repeat(200);
      const content = [
        '# Title',
        '## Section 1',
        ...Array(25).fill(longLine),
        '## Section 2',
        ...Array(25).fill(longLine),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/chars.md', content };
      const { chunks } = chunkFile(file);

      expect(chunks.length).toBeGreaterThan(1);
    });

    it('respects char limit when merging', () => {
      // Create chunks that fit line limit but exceed char limit when combined
      const longContent = 'y'.repeat(5000);
      const sections = [
        `## Section 1\n${longContent}`,
        `## Section 2\n${longContent}`,
      ];
      const content = ['# Title', '', ...sections].join('\n');

      // Pad to force splitting
      const padded = content + '\n' + Array(150).fill('pad').join('\n');
      const file: MarkdownFile = { path: 'test/charmerge.md', content: padded };
      const { chunks } = chunkFile(file);

      // Each section's content is 5000 chars; merging would exceed 8000
      // So they should remain separate
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS + 1000); // Allow some overhead
      }
    });

    it('hard split respects character limit on very long lines', () => {
      // 100 lines at 300 chars each = 30,000 chars total
      // This exceeds MAX_CHUNK_CHARS (8000) even though line count (100) is under MAX_CHUNK_LINES (150)
      const longLine = 'x'.repeat(300);
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Section',
        ...Array(100).fill(longLine),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/longlines.md', content };
      const { chunks } = chunkFile(file);

      // Should produce multiple chunks since total chars exceed limit
      expect(chunks.length).toBeGreaterThan(1);

      // All chunks must respect the character limit
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      }
    });
  });

  describe('table-aware splitting', () => {
    it('keeps small tables atomic', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Small Table',
        '| A | B |',
        '|---|---|',
        '| 1 | 2 |',
        '| 3 | 4 |',
        '',
        'Paragraph after table.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/small-table.md', content };
      const { chunks } = chunkFile(file);

      // Small file should be one chunk
      expect(chunks.length).toBe(1);
      // Table should be intact (all rows present)
      expect(chunks[0].content).toContain('| 1 | 2 |');
      expect(chunks[0].content).toContain('| 3 | 4 |');
    });

    it('does not treat pipe-lines inside code fence as table', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Code Example',
        '```bash',
        'echo "| Not | A | Table |"',
        'cat file | grep pattern | head',
        '```',
        '',
        'Paragraph after code.',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/fence-pipe.md', content };
      const { chunks } = chunkFile(file);

      // Code block should stay intact
      const codeChunk = chunks.find((c) => c.content.includes('```bash'));
      expect(codeChunk?.content).toContain('echo "| Not | A | Table |"');
      expect(codeChunk?.content).toContain('cat file | grep pattern | head');
    });

    it('handles tables mixed with paragraphs', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Mixed Content',
        'Paragraph before table.',
        '',
        '| Col1 | Col2 |',
        '|------|------|',
        '| a    | b    |',
        '',
        'Paragraph after table.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/mixed.md', content };
      const { chunks } = chunkFile(file);

      // Content should preserve table integrity
      const contentStr = chunks.map((c) => c.content).join('');
      expect(contentStr).toContain('| Col1 | Col2 |');
      expect(contentStr).toContain('| a    | b    |');
    });

    it('splits oversized tables at row boundaries with header preservation', () => {
      // Create a table that exceeds MAX_CHUNK_CHARS (8000)
      // Each row is ~34 chars, so 250 rows = ~8500 chars for the table alone
      const header = '| Column A | Column B | Column C |';
      const separator = '|----------|----------|----------|';
      const row = '| data-a   | data-b   | data-c   |';
      const tableRows = Array(250).fill(row).join('\n'); // ~8500+ chars

      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Table Section',
        header,
        separator,
        tableRows,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/big-table.md', content };
      const { chunks } = chunkFile(file);

      // Should produce multiple chunks due to oversized table
      expect(chunks.length).toBeGreaterThan(1);

      // Each chunk with table data should have the header
      for (const chunk of chunks) {
        if (chunk.content.includes('data-a')) {
          // Table chunks should have header
          expect(chunk.content).toContain(header);
          expect(chunk.content).toContain(separator);
        }
      }

      // Each chunk within size limit
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      }
    });

    it('preserves paragraph boundaries after tables', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Section',
        '| A | B |',
        '|---|---|',
        '| 1 | 2 |',
        '', // This blank line should preserve paragraph boundary
        'First paragraph after table.',
        '',
        'Second paragraph.',
        ...Array(150).fill('padding'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/table-para.md', content };
      const { chunks } = chunkFile(file);

      // Paragraphs after table should not be merged incorrectly
      const contentStr = chunks.map((c) => c.content).join('');
      expect(contentStr).toContain('First paragraph after table.');
      expect(contentStr).toContain('Second paragraph.');

      // Verify the two paragraphs are NOT on the same line (i.e., separated by blank line or newlines)
      // If merged incorrectly, they'd appear as "First paragraph after table.Second paragraph."
      expect(contentStr).not.toMatch(/First paragraph after table\.Second/);
    });
  });

  describe('table handling edge cases', () => {
    it('handles malformed table without separator', () => {
      const content = [
        '# Title',
        '## Section',
        '| A | B |',
        '| 1 | 2 |', // This is data, not separator
        '| 3 | 4 |',
        '',
        'After table.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/bad-table.md', content };
      const { chunks } = chunkFile(file);

      // Should not crash, should preserve content
      expect(chunks.length).toBeGreaterThan(0);
      const allContent = chunks.map((c) => c.content).join('');
      expect(allContent).toContain('| A | B |');
    });

    it('handles empty table (header + separator only)', () => {
      const content = [
        '# Title',
        '## Section',
        '| A | B |',
        '|---|---|',
        '',
        'After table.',
      ].join('\n');

      const file: MarkdownFile = { path: 'test/empty-table.md', content };
      const { chunks } = chunkFile(file);

      expect(chunks.length).toBeGreaterThan(0);
      const allContent = chunks.map((c) => c.content).join('');
      expect(allContent).toContain('| A | B |');
    });

    it('handles oversized malformed table without separator', () => {
      // Create a large table-like structure without a proper separator
      // This should trigger splitOversizedTable but with invalid table structure
      const rows = Array(300).fill('| data-a | data-b |').join('\n');
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Section',
        '| Header A | Header B |',
        '| not-a-separator | still-data |', // Missing --- separator
        rows,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/oversized-bad-table.md', content };
      const { chunks } = chunkFile(file);

      // Should not crash, should preserve content
      expect(chunks.length).toBeGreaterThan(0);
      const allContent = chunks.map((c) => c.content).join('');
      expect(allContent).toContain('| Header A | Header B |');
      expect(allContent).toContain('| data-a | data-b |');
    });
  });

  describe('edge cases', () => {
    it('handles intro-only oversized files (no H2 headings)', () => {
      const content = [
        '---',
        'category: test',
        '---',
        '# Title Only',
        ...Array(200).fill('Very long intro paragraph content line that fills the file.'),
      ].join('\n');

      const file: MarkdownFile = { path: 'test/no-h2.md', content };
      const { chunks } = chunkFile(file);

      expect(chunks.length).toBeGreaterThan(1);
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      }
    });

    it('does not excessively duplicate content via overlap', () => {
      const longParagraph = Array(60).fill('word').join(' ');
      const manyParagraphs = Array(50).fill(longParagraph).join('\n\n');

      const content = [
        '# Title',
        '## Section',
        manyParagraphs,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/overlap.md', content };
      const { chunks } = chunkFile(file);

      const allContent = chunks.map(c => c.content).join('|||');
      const wordCount = (allContent.match(/word/g) || []).length;
      const expectedMax = 50 * 60 * 1.3;  // Original + 30% for overlap
      expect(wordCount).toBeLessThan(expectedMax);
    });
  });

  describe('oversized single-line truncation', () => {
    it('truncates a single line exceeding MAX_CHUNK_CHARS', () => {
      const oversizedLine = 'x'.repeat(MAX_CHUNK_CHARS + 5000);
      const content = [
        '---',
        'category: test',
        '---',
        '# Title',
        '## Section',
        oversizedLine,
      ].join('\n');

      const file: MarkdownFile = { path: 'test/oversized-line.md', content };
      const { chunks } = chunkFile(file);

      // Every chunk's content must respect the MAX_CHUNK_CHARS limit
      for (const chunk of chunks) {
        expect(chunk.content.length).toBeLessThanOrEqual(MAX_CHUNK_CHARS);
      }
    });
  });

  describe('chunkFile error handling', () => {
    it('throws with file context on parse error', () => {
      // Malformed content that will cause an error
      const file: MarkdownFile = {
        path: 'test/malformed.md',
        content: null as unknown as string, // Force invalid input
      };

      expect(() => chunkFile(file)).toThrow('test/malformed.md');
    });

    it('throws on missing path', () => {
      const file: MarkdownFile = {
        path: '',
        content: '# Test',
      };

      expect(() => chunkFile(file)).toThrow('file.path is required');
    });
  });
});
