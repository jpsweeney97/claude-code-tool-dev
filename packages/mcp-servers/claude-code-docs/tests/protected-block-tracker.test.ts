import { describe, it, expect } from 'vitest';
import { ProtectedBlockTracker } from '../src/protected-block-tracker.js';

describe('ProtectedBlockTracker', () => {
  it('returns false for plain text', () => {
    const tracker = new ProtectedBlockTracker();
    expect(tracker.processLine('Hello world')).toBe(false);
  });

  it('returns true inside code fences', () => {
    const tracker = new ProtectedBlockTracker();
    expect(tracker.processLine('```typescript')).toBe(true);
    expect(tracker.processLine('const x = 1;')).toBe(true);
    expect(tracker.processLine('```')).toBe(false);
  });

  it('returns true inside JSX blocks', () => {
    const tracker = new ProtectedBlockTracker();
    expect(tracker.processLine('<Warning>')).toBe(true);
    expect(tracker.processLine('  Be careful!')).toBe(true);
    expect(tracker.processLine('</Warning>')).toBe(false);
  });

  it('skips JSX parsing while inside a code fence', () => {
    const tracker = new ProtectedBlockTracker();
    expect(tracker.processLine('```')).toBe(true);
    // <Warning> inside a fence should NOT push to JSX stack
    expect(tracker.processLine('<Warning>')).toBe(true); // true from fence, not JSX
    expect(tracker.processLine('```')).toBe(false); // fence closed
    // We should NOT be inside a JSX block now
    expect(tracker.processLine('Normal text')).toBe(false);
  });

  it('handles nested fence + JSX correctly', () => {
    const tracker = new ProtectedBlockTracker();
    expect(tracker.processLine('<Warning>')).toBe(true);  // JSX
    expect(tracker.processLine('```')).toBe(true);        // fence inside JSX
    expect(tracker.processLine('code')).toBe(true);       // inside both
    expect(tracker.processLine('```')).toBe(true);        // fence closed, still in JSX
    expect(tracker.processLine('</Warning>')).toBe(false); // JSX closed
  });

  it('can be reset', () => {
    const tracker = new ProtectedBlockTracker();
    tracker.processLine('<Warning>');
    tracker.processLine('```');
    expect(tracker.isProtected).toBe(true);
    tracker.reset();
    expect(tracker.isProtected).toBe(false);
  });
});
