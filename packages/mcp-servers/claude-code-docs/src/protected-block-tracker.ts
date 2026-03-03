import { FenceTracker } from './fence-tracker.js';
import { JsxBlockTracker } from './jsx-block-tracker.js';

/**
 * Composite tracker that combines code fence and JSX block awareness.
 * Returns true when inside EITHER a code fence OR a JSX component block.
 *
 * Critical: JSX parsing is skipped while inside a code fence to prevent
 * JSX-like syntax in code examples from corrupting the tag stack.
 *
 * Drop-in replacement for FenceTracker in chunker splitting functions.
 */
export class ProtectedBlockTracker {
  private fence = new FenceTracker();
  private jsx = new JsxBlockTracker();

  /**
   * Process a line and update tracking state.
   * @returns true if currently inside a protected block (fence or JSX)
   */
  processLine(line: string): boolean {
    const inFence = this.fence.processLine(line);

    // Only process JSX when NOT inside a code fence
    if (!inFence) {
      this.jsx.processLine(line);
    }

    return inFence || this.jsx.isInBlock;
  }

  /** Check if currently inside a protected block */
  get isProtected(): boolean {
    return this.fence.isInFence || this.jsx.isInBlock;
  }

  /** Reset both trackers */
  reset(): void {
    this.fence.reset();
    this.jsx.reset();
  }
}
