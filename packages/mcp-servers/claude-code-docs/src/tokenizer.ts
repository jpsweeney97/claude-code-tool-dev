import { stemmer } from 'stemmer';

/**
 * Words that should never be stemmed. Technical proper nouns and
 * terms where stemming would produce misleading roots.
 */
const NO_STEM = new Set(['claude', 'anthropic']);

/**
 * Detect if a raw span (pre-lowercase) contains CamelCase or acronym patterns.
 * These spans produce technical tokens that should not be stemmed.
 *
 * Matches:
 * - CamelCase: "PreToolUse" (lowercase/digit followed by uppercase)
 * - Acronyms: "MCPServer" (2+ uppercase followed by lowercase)
 *
 * The first pattern uses [a-z\d] (not just [a-z]) to match the splitting
 * regex /([a-z\d])([A-Z])/g — digit-to-uppercase transitions like
 * "Pre2Tool" are also CamelCase identifiers.
 */
function isCamelOrAcronym(span: string): boolean {
  return /[a-z\d][A-Z]/.test(span) || /[A-Z]{2,}[a-z]/.test(span);
}

/**
 * Apply Porter stemming to a token, unless it is protected.
 * Skips stemming for: protected tokens, NO_STEM words, and
 * digit-only tokens (stemmer expects alphabetic input).
 */
function maybeStem(token: string, isProtected: boolean): string {
  if (isProtected || NO_STEM.has(token) || !/[a-z]/.test(token)) return token;
  return stemmer(token);
}

export function tokenize(text: string): string[] {
  // Split into raw alphanumeric spans (before any case transformation).
  // This span-based approach is necessary to detect CamelCase BEFORE
  // lowercasing destroys the case signal.
  const spans = text.match(/[a-zA-Z0-9]+/g);
  if (!spans) return [];

  const result: string[] = [];

  for (const span of spans) {
    // Detect CamelCase/acronym BEFORE lowercasing (case info is lost after)
    const isProtected = isCamelOrAcronym(span);

    // Apply the same splitting logic as the original tokenizer:
    // 1. Split CamelCase: "PreToolUse" → "Pre Tool Use"
    // 2. Handle consecutive capitals: "MCPServer" → "MCP Server"
    // 3. Lowercase
    // 4. Split on whitespace (introduced by step 1-2)
    // 5. Filter single-character tokens
    const tokens = span
      .replace(/([a-z\d])([A-Z])/g, '$1 $2')
      .replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
      .toLowerCase()
      .split(/\s+/)
      .filter((t) => t.length > 1);

    for (const t of tokens) {
      const stemmed = maybeStem(t, isProtected);
      // Filter out tokens that became single-char after stemming
      if (stemmed.length > 1) {
        result.push(stemmed);
      }
    }
  }

  return result;
}
