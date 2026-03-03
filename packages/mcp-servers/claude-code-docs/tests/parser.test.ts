import { describe, it, expect } from 'vitest';
import { parseSections } from '../src/parser.js';

describe('parseSections', () => {
  it('returns empty array for empty input', () => {
    expect(parseSections('')).toEqual([]);
  });

  it('returns single section with empty sourceUrl for content without Source: lines', () => {
    const raw = '# Hello\n\nSome content';
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('');
    expect(sections[0].title).toBe('Hello');
    expect(sections[0].content).toBe('# Hello\n\nSome content');
  });

  it('splits on Source: lines', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content

# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('https://example.com/first');
    expect(sections[0].title).toBe('First Topic');
    expect(sections[1].sourceUrl).toBe('https://example.com/second');
    expect(sections[1].title).toBe('Second Topic');
  });

  it('handles preamble before first Source: line', () => {
    const raw = `# Preamble

Some intro text

# Actual Topic
Source: https://example.com/topic

Topic content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('');
    expect(sections[0].title).toBe('Preamble');
    expect(sections[1].sourceUrl).toBe('https://example.com/topic');
  });

  it('handles missing title before Source: line', () => {
    const raw = `Source: https://example.com/notitle

Content without preceding heading`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('https://example.com/notitle');
    expect(sections[0].title).toBe('');
  });

  it('extracts nearest heading before Source: line', () => {
    const raw = `# Main Heading

## Subheading

### Deep Heading
Source: https://example.com/deep

Content`;
    const sections = parseSections(raw);
    // First section is preamble (headings before the one preceding Source)
    // Second section is the Source section with Deep Heading as title
    const sourceSection = sections.find((s) => s.sourceUrl !== '');
    expect(sourceSection?.title).toBe('Deep Heading');
  });

  it('does not match Source: in middle of line', () => {
    const raw = `# Topic
Source: https://example.com/topic

See Source: somewhere in text for details`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
  });
});

describe('parseSections — new format with --- separators', () => {
  it('splits sections with --- separator between them', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content
---
# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('https://example.com/first');
    expect(sections[0].title).toBe('First Topic');
    expect(sections[0].content.trim()).toBe('First content');
    expect(sections[1].sourceUrl).toBe('https://example.com/second');
    expect(sections[1].title).toBe('Second Topic');
    expect(sections[1].content.trim()).toBe('Second content');
  });

  it('section content excludes heading and Source: line by extraction', () => {
    // Content starts after the Source: line — the # Title is captured
    // as title metadata and naturally excluded from content.
    // This is extraction semantics, not post-processing stripping.
    const raw = `# My Page Title
Source: https://example.com/page

Some actual content here

## Subsection
More content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].title).toBe('My Page Title');
    // # Title and Source: line are NOT in content (above the extraction window)
    expect(sections[0].content).not.toMatch(/^# My Page Title/m);
    expect(sections[0].content).not.toMatch(/^Source:/m);
    expect(sections[0].content).toContain('Some actual content here');
    expect(sections[0].content).toContain('## Subsection');
  });

  it('does not include trailing --- or next section title in content', () => {
    const raw = `# First
Source: https://example.com/first

Content of first
---
# Second
Source: https://example.com/second

Content of second`;
    const sections = parseSections(raw);
    expect(sections[0].content).not.toContain('---');
    expect(sections[0].content).not.toContain('# Second');
  });

  it('handles first section without leading ---', () => {
    // The new format starts immediately with # Title + Source (no leading ---)
    const raw = `# First Topic
Source: https://example.com/first

First content
---
# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].title).toBe('First Topic');
  });

  it('preserves --- horizontal rules inside section content', () => {
    const raw = `# Topic
Source: https://example.com/topic

Some content

---

More content after horizontal rule
---
# Next Topic
Source: https://example.com/next

Next content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    // The mid-content --- (with blank lines around it) should be preserved
    // Only the --- immediately preceding # Next Topic should be a boundary
    expect(sections[0].content).toContain('---');
    expect(sections[0].content).toContain('More content after horizontal rule');
  });

  it('does not consume distant --- as section boundary', () => {
    // A --- separated from the heading by many blank lines should NOT
    // be treated as a section boundary (max 3 blank-line lookback guard)
    const raw = `# First
Source: https://example.com/first

Content with a horizontal rule

---




More content after many blank lines
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    // The distant --- should be in first section's content, not consumed as boundary
    expect(sections[0].content).toContain('Content with a horizontal rule');
    expect(sections[0].content).toContain('More content after many blank lines');
  });

  it('produces no preamble when file starts with # Title + Source', () => {
    const raw = `# Topic
Source: https://example.com/topic

Content`;
    const sections = parseSections(raw);
    // No preamble section — only the Source-anchored section
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('https://example.com/topic');
  });

  it('filters bare --- preamble as non-meaningful', () => {
    const raw = `---
# Topic
Source: https://example.com/topic

Content`;
    const sections = parseSections(raw);
    // The leading --- should not create a preamble section
    const sourceSections = sections.filter(s => s.sourceUrl !== '');
    expect(sourceSections).toHaveLength(1);
    expect(sourceSections[0].title).toBe('Topic');
  });
});

describe('parseSections — content bleed detection', () => {
  it('section content does not end with trailing ---', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      expect(section.content.trimEnd()).not.toMatch(/---$/);
    }
  });

  it('section content does not contain Source: URL lines', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      // Only match Source: lines that look like section anchors (with URL),
      // not literal "Source:" text in prose or code fences
      expect(section.content).not.toMatch(/^Source:\s+https?:\/\//m);
    }
  });

  it('section content does not end with heading+Source pattern', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      const lines = section.content.trimEnd().split('\n');
      const lastFew = lines.slice(-5).join('\n');
      expect(lastFew).not.toMatch(/^#\s+.+\nSource:\s+/m);
    }
  });

  it('Source: inside code fences is treated as a section boundary (known limitation)', () => {
    // The parser is not fence-aware: Source: lines inside code fences
    // are treated as section boundaries. This is acceptable because
    // the live llms-full.txt does not contain Source: URLs inside fences.
    // This test documents the actual behavior.
    const raw = `# Config Guide
Source: https://example.com/config

Here is an example:

\`\`\`yaml
Source: https://internal.example.com/api
\`\`\`

More content after code block
---
# Next Section
Source: https://example.com/next

Next content`;
    const sections = parseSections(raw);
    // Parser treats in-fence Source: as a section anchor, creating 3 sections:
    // 1. preamble (Config Guide heading before first Source:)
    //    — or the config section with empty content
    // 2. internal.example.com/api section
    // 3. next section
    const sourceUrls = sections.map(s => s.sourceUrl).filter(Boolean);
    expect(sourceUrls).toContain('https://example.com/config');
    expect(sourceUrls).toContain('https://internal.example.com/api');
    expect(sourceUrls).toContain('https://example.com/next');
    // The real bleed invariant: no section contains another section's Source: line
    for (const section of sections) {
      expect(section.content).not.toMatch(/^Source:\s+https?:\/\//m);
    }
  });
});

describe('parseSections — backward compatibility with old format', () => {
  it('still handles old format without --- separators', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content

# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].title).toBe('First Topic');
    expect(sections[1].title).toBe('Second Topic');
    // Content excludes heading by extraction (content starts after Source: line)
    expect(sections[0].content).not.toMatch(/^# First Topic/m);
  });
});
