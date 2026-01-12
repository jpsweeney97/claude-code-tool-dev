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
  private inFence = false;
  private fencePattern = '';

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
      } else if (
        line.match(
          new RegExp(`^ {0,3}${this.fencePattern[0]}{${this.fencePattern.length},}\\s*$`)
        )
      ) {
        this.inFence = false;
        this.fencePattern = '';
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
    this.fencePattern = '';
  }
}
