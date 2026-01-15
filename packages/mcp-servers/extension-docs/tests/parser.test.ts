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
