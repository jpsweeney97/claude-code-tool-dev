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

describe('FenceTracker safety limit', () => {
  it('force-closes unclosed fence after MAX_FENCE_LINES lines', () => {
    const tracker = new FenceTracker();

    // Open a fence that never closes
    tracker.processLine('```typescript');
    expect(tracker.isInFence).toBe(true);

    // Feed 200+ non-fence lines (exceeds MAX_FENCE_LINES = 150)
    for (let i = 0; i < 200; i++) {
      tracker.processLine(`line ${i}`);
    }

    // Fence should have been force-closed after MAX_FENCE_LINES
    expect(tracker.isInFence).toBe(false);
  });

  it('stays in fence when line count is within MAX_FENCE_LINES', () => {
    const tracker = new FenceTracker();

    tracker.processLine('```');
    // Feed lines up to but not exceeding the limit (opening line counts as 1)
    // MAX_FENCE_LINES = 150, opening line is line 1, so 149 more lines = still in fence
    for (let i = 0; i < 148; i++) {
      tracker.processLine(`line ${i}`);
    }

    expect(tracker.isInFence).toBe(true);
  });

  it('resets line count on normal fence close', () => {
    const tracker = new FenceTracker();

    tracker.processLine('```');
    for (let i = 0; i < 10; i++) {
      tracker.processLine(`line ${i}`);
    }
    tracker.processLine('```'); // Close normally

    // Open a new fence — line count should be fresh
    tracker.processLine('```');
    expect(tracker.isInFence).toBe(true);
    // Feed 140 lines — should still be in fence (fresh count)
    for (let i = 0; i < 140; i++) {
      tracker.processLine(`line ${i}`);
    }
    expect(tracker.isInFence).toBe(true);
  });
});

describe('FenceTracker edge cases', () => {
  it('handles null fencePattern gracefully', () => {
    const tracker = new FenceTracker();

    // Force invalid internal state (for robustness testing)
    // With null sentinel, this tests the guard check
    (tracker as any).inFence = true;
    (tracker as any).fencePattern = null;

    // Should not throw and should handle gracefully
    expect(() => tracker.processLine('```')).not.toThrow();
    // The fence should remain open since pattern is invalid
    expect(tracker.isInFence).toBe(true);
  });

  it('handles nested fence documentation pattern', () => {
    const tracker = new FenceTracker();

    expect(tracker.processLine('````markdown')).toBe(true);
    expect(tracker.processLine('Here is an example:')).toBe(true);
    expect(tracker.processLine('```python')).toBe(true); // Inside, NOT a new fence
    expect(tracker.processLine('print("hello")')).toBe(true);
    expect(tracker.processLine('```')).toBe(true); // Still inside outer
    expect(tracker.processLine('````')).toBe(false); // Now closed
  });
});
