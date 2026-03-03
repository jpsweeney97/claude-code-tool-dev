import { describe, it, expect } from 'vitest';
import { JsxBlockTracker } from '../src/jsx-block-tracker.js';

describe('JsxBlockTracker', () => {
  it('returns false for plain text lines', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('Hello world')).toBe(false);
    expect(tracker.processLine('## Heading')).toBe(false);
    expect(tracker.processLine('')).toBe(false);
  });

  it('tracks a simple <Warning>...</Warning> block', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('<Warning>')).toBe(true);
    expect(tracker.processLine('  Some warning text')).toBe(true);
    expect(tracker.processLine('</Warning>')).toBe(false);
  });

  it('tracks all known tags', () => {
    const knownTags = [
      'Warning', 'Note', 'Tip', 'Steps', 'Step',
      'Frame', 'Card', 'CodeGroup',
      'Accordion', 'AccordionGroup', 'Tabs', 'Tab',
      'Callout', 'CardGroup', 'Info', 'MCPServersTable',
    ];
    for (const tag of knownTags) {
      const tracker = new JsxBlockTracker();
      expect(tracker.processLine(`<${tag}>`)).toBe(true);
      expect(tracker.processLine(`</${tag}>`)).toBe(false);
    }
  });

  it('ignores unknown tags', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('<div>')).toBe(false);
    expect(tracker.processLine('<UnknownComponent>')).toBe(false);
    expect(tracker.processLine('</div>')).toBe(false);
  });

  it('handles nested known tags', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('<Steps>')).toBe(true);
    expect(tracker.processLine('  <Step title="First">')).toBe(true);
    expect(tracker.processLine('    Step content')).toBe(true);
    expect(tracker.processLine('  </Step>')).toBe(true); // Still inside <Steps>
    expect(tracker.processLine('</Steps>')).toBe(false);
  });

  it('handles tags with attributes', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('<Step title="Install dependencies">')).toBe(true);
    expect(tracker.processLine('  Content')).toBe(true);
    expect(tracker.processLine('</Step>')).toBe(false);
  });

  it('prefers line-start tag detection', () => {
    const tracker = new JsxBlockTracker();
    // Inline component-like text should NOT trigger tracking
    expect(tracker.processLine('Use <Warning> for important notes')).toBe(false);
    // But indented tags at line start should
    expect(tracker.processLine('  <Warning>')).toBe(true);
    expect(tracker.processLine('  </Warning>')).toBe(false);
  });

  it('ignores self-closing tags', () => {
    const tracker = new JsxBlockTracker();
    expect(tracker.processLine('<Step />')).toBe(false);
    expect(tracker.processLine('<Frame src="image.png" />')).toBe(false);
  });

  it('handles unmatched close tag gracefully', () => {
    const tracker = new JsxBlockTracker();
    // Close tag without open — should not go negative or throw
    expect(tracker.processLine('</Warning>')).toBe(false);
    expect(tracker.processLine('Normal text')).toBe(false);
  });

  it('recovers from missing close tag via depth cap', () => {
    const tracker = new JsxBlockTracker();
    // Push 16 opens without close — should hit depth cap and reset
    for (let i = 0; i < 16; i++) {
      tracker.processLine('<Warning>');
    }
    // After cap, tracker should have reset
    expect(tracker.processLine('Normal text')).toBe(false);
  });

  it('can be reset', () => {
    const tracker = new JsxBlockTracker();
    tracker.processLine('<Warning>');
    expect(tracker.isInBlock).toBe(true);
    tracker.reset();
    expect(tracker.isInBlock).toBe(false);
  });
});
