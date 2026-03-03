/**
 * Tracks JSX-like component blocks in Mintlify markdown.
 * Prevents the chunker from splitting inside known component blocks
 * like <Warning>...</Warning>, <Steps>...</Steps>, etc.
 *
 * Only tracks known tags to avoid false positives from inline HTML
 * or component-like text in prose.
 *
 * Usage:
 *   const jsx = new JsxBlockTracker();
 *   for (const line of lines) {
 *     const inBlock = jsx.processLine(line);
 *     if (!inBlock) { // safe to split here }
 *   }
 */

const KNOWN_TAGS = new Set([
  'Warning', 'Note', 'Tip', 'Steps', 'Step',
  'Frame', 'Card', 'CodeGroup',
  'Accordion', 'AccordionGroup', 'Tabs', 'Tab',
  'Callout', 'CardGroup', 'Info', 'MCPServersTable',
]);

const MAX_DEPTH = 16;

// Matches opening tags at line start (with optional indentation):
//   <TagName>  or  <TagName attr="value">
// Does NOT match self-closing: <TagName />
const OPEN_TAG_RE = /^\s*<([A-Z][A-Za-z0-9]*)\b[^>]*(?<!\/)>$/;

// Matches closing tags at line start:
//   </TagName>
const CLOSE_TAG_RE = /^\s*<\/([A-Z][A-Za-z0-9]*)\s*>$/;

// Matches self-closing tags at line start:
//   <TagName />  or  <TagName attr="value" />
const SELF_CLOSING_RE = /^\s*<[A-Z][A-Za-z0-9]*\b[^>]*\/>$/;

export class JsxBlockTracker {
  private stack: string[] = [];

  /**
   * Process a line and update block tracking state.
   * @returns true if currently inside a JSX block AFTER processing this line
   */
  processLine(line: string): boolean {
    // Self-closing tags don't change state
    if (SELF_CLOSING_RE.test(line)) {
      return this.stack.length > 0;
    }

    // Check for closing tag first (pops stack)
    const closeMatch = line.match(CLOSE_TAG_RE);
    if (closeMatch) {
      const tagName = closeMatch[1];
      if (KNOWN_TAGS.has(tagName)) {
        this.popTag(tagName);
      }
      return this.stack.length > 0;
    }

    // Check for opening tag (pushes stack)
    const openMatch = line.match(OPEN_TAG_RE);
    if (openMatch) {
      const tagName = openMatch[1];
      if (KNOWN_TAGS.has(tagName)) {
        this.stack.push(tagName);
        // Depth cap — reset to prevent runaway state
        if (this.stack.length >= MAX_DEPTH) {
          console.warn(`JsxBlockTracker: depth cap (${MAX_DEPTH}) hit, resetting`);
          this.stack = [];
          return false;
        }
      }
    }

    return this.stack.length > 0;
  }

  /**
   * Pop a tag from the stack with layered recovery:
   * 1. Top-of-stack match — normal case
   * 2. lastIndexOf match — skip mismatched inner tags
   * 3. No match — ignore the close tag
   */
  private popTag(tagName: string): void {
    if (this.stack.length === 0) return;

    // Try top-of-stack match
    if (this.stack[this.stack.length - 1] === tagName) {
      this.stack.pop();
      return;
    }

    // Try lastIndexOf match (handles skipped inner tags)
    const idx = this.stack.lastIndexOf(tagName);
    if (idx >= 0) {
      this.stack.splice(idx);
      return;
    }

    // No match — ignore the unmatched close tag
  }

  /** Check if currently inside a block without advancing state */
  get isInBlock(): boolean {
    return this.stack.length > 0;
  }

  /** Reset to initial state */
  reset(): void {
    this.stack = [];
  }
}
