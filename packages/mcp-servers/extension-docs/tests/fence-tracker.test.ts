import { describe, it, expect } from 'vitest';
import { FenceTracker } from '../src/fence-tracker.js';

describe('FenceTracker', () => {
  it('detects backtick fence start and end', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('normal text')).toBe(false);
    expect(tracker.processLine('```typescript')).toBe(true);
    expect(tracker.processLine('code inside')).toBe(true);
    expect(tracker.processLine('```')).toBe(false);
    expect(tracker.processLine('after fence')).toBe(false);
  });

  it('detects tilde fence start and end', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('~~~python')).toBe(true);
    expect(tracker.processLine('code')).toBe(true);
    expect(tracker.processLine('~~~')).toBe(false);
  });

  it('handles indented fences (0-3 spaces)', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('   ```bash')).toBe(true);
    expect(tracker.processLine('code')).toBe(true);
    expect(tracker.processLine('   ```')).toBe(false);
  });

  it('ignores 4+ space indented fences', () => {
    const tracker = new FenceTracker();

    // 4 spaces = code block in CommonMark, not a fence
    expect(tracker.processLine('    ```bash')).toBe(false);
    expect(tracker.processLine('not in fence')).toBe(false);
  });

  it('requires matching fence character for close', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('```typescript')).toBe(true);
    expect(tracker.processLine('~~~')).toBe(true); // ~~~ doesn't close ```
    expect(tracker.processLine('```')).toBe(false); // ``` closes ```
  });

  it('requires matching fence length for close', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('````typescript')).toBe(true);
    expect(tracker.processLine('```')).toBe(true); // 3 backticks don't close 4
    expect(tracker.processLine('````')).toBe(false); // 4 closes 4
  });

  it('exposes isInFence property', () => {
    const tracker = new FenceTracker();

    expect(tracker.isInFence).toBe(false);
    tracker.processLine('```');
    expect(tracker.isInFence).toBe(true);
  });

  it('resets state', () => {
    const tracker = new FenceTracker();

    tracker.processLine('```');
    expect(tracker.isInFence).toBe(true);
    tracker.reset();
    expect(tracker.isInFence).toBe(false);
  });
});
