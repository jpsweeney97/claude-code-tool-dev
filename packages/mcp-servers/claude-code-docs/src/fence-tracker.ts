/**
 * Tracks code fence state while iterating through markdown lines.
 * CommonMark-compliant: 0-3 leading spaces, 3+ backticks or tildes.
 *
 * Usage:
 *   const fence = new FenceTracker();
 *   for (const line of lines) {
 *     const inFence = fence.processLine(line);
 *     if (!inFence && isHeading(line)) { ... }
 *   }
 */
export class FenceTracker {
  /** Maximum lines inside a fence before force-closing (safety limit) */
  static readonly MAX_FENCE_LINES = 150;

  private inFence = false;
  private fencePattern: string | null = null;
  private fenceLineCount = 0;

  /**
   * Process a line and update fence state.
   * @returns true if currently inside a fence AFTER processing this line
   */
  processLine(line: string): boolean {
    const fence = line.match(/^( {0,3})(`{3,}|~{3,})/);
    if (fence) {
      if (!this.inFence) {
        this.inFence = true;
        this.fencePattern = fence[2];
        this.fenceLineCount = 0;
      } else if (this.fencePattern && this.fencePattern.length > 0) {
        const closeRegex = new RegExp(
          `^ {0,3}${this.fencePattern[0]}{${this.fencePattern.length},}\\s*$`
        );
        if (closeRegex.test(line)) {
          this.inFence = false;
          this.fencePattern = null;
          this.fenceLineCount = 0;
        }
      }
    }

    // Safety limit: force-close fence if it exceeds MAX_FENCE_LINES without closing
    if (this.inFence) {
      this.fenceLineCount++;
      if (this.fenceLineCount > FenceTracker.MAX_FENCE_LINES) {
        this.inFence = false;
        this.fencePattern = null;
        this.fenceLineCount = 0;
      }
    }

    return this.inFence;
  }

  /** Check if currently inside a fence without advancing state */
  get isInFence(): boolean {
    return this.inFence;
  }

  /** Reset to initial state */
  reset(): void {
    this.inFence = false;
    this.fencePattern = null;
    this.fenceLineCount = 0;
  }
}
