# Ingestion Pipeline Enhancement — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update the claude-code-docs MCP server's ingestion pipeline to correctly parse the updated `llms-full.txt` format, which now uses `---` section separators and includes JSX-like components.

**Architecture:** Source-anchored two-pass parser that uses `Source:` lines as the canonical section anchor and `---` as an optional boundary signal. A composite `ProtectedBlockTracker` wrapping `FenceTracker` + `JsxBlockTracker` prevents chunk splits inside JSX components. Section content naturally excludes `# Title` and `Source:` lines because content is extracted from after the `Source:` line — no post-processing stripping needed.

**Tech Stack:** TypeScript, Vitest, BM25 search index

**Working directory:** `packages/mcp-servers/claude-code-docs/` (all paths relative to this unless noted)

**Run tests:** `npm test` (runs `vitest run`)

**Build:** `npm run build` (runs `tsc`)

---

## Codex Review Amendments

### Review 1 — Adversarial (6 turns, converged)

Stress-tested the original plan. These amendments are incorporated into the tasks below:

| Priority | Finding | Amendment |
|----------|---------|-----------|
| **P0** | `stripLeadingTitle` defined but never called — tests pass by accident via extraction semantics | Removed function entirely. Tests reframed to verify extraction behavior. |
| **P1-A** | JSX allowlist missing 8 live-corpus tags | Added: `Accordion`, `AccordionGroup`, `Tabs`, `Tab`, `Callout`, `CardGroup`, `Info`, `MCPServersTable` |
| **P1-B** | `---` lookback: off-by-one at index 0, ignores whitespace-only blanks, no distance guard | Added `headingLineStart > 0` guard (skips lookback when heading is at file start — no preceding `---` possible), whitespace-aware blank handling, max 3 blank-line guard |
| **P1-C** | Task 6 (fixtures) after Tasks 2-5 hides regressions behind stale mock content | Moved fixture updates to Task 3 (immediately after parser rewrite) |
| **P1-D** | Module-level mutable `unmappedSegments` Map leaks across tests | Changed to per-load local state in loader |
| **P1-E** | `sourceLineCount` includes preamble pseudo-section | Fixed to count only `Source:`-anchored sections |
| **P1-F** | Task 7 bleed check only tests trailing `---`, not `Source:` line or `# Title` bleed | Added `Source:` and heading+Source pattern checks |
| **P2-A** | Fence-unaware `findLastHeadingBefore` (latent, 0 active cases in corpus) | Deferred — add corpus canary test in follow-up |
| **P2-B** | `OPEN_TAG_RE` doesn't support multiline JSX attributes (0 instances in corpus) | Deferred — forward-compat gap only |
| **P2-C** | `splitByHeadingOutsideFences` name outdated after ProtectedBlockTracker swap | Deferred — documentation debt, low risk |

**Task resequencing:** Original order was 1→2→3→4→5→6→7. New order moves fixture updates earlier: 1→2→**3**(was 6)→**4**(was 3)→**5**(was 4)→**6**(was 5)→7.

### Review 2 — Adversarial-Challenge (6 turns, converged)

Stress-tested the amendments from Review 1. Found 3 P0 bugs introduced by the amendments themselves:

| Priority | Finding | Amendment |
|----------|---------|-----------|
| **P0-1** | `getUnmappedSegments` uses `new URL().pathname.split()` returning `['docs','en','hooks']`, diverging from `deriveCategory`'s `extractContentPath` which returns `['hooks']` — plan test at line 1197 would fail | Replaced with `extractContentPath(sourceUrl)` + `Object.hasOwn(SECTION_TO_CATEGORY, seg)`. Root cause: P1-D amendment kept inline URL parsing instead of reusing existing helper. |
| **P0-2** | `getUnmappedSegments` calls `new URL('')` on preamble sections with empty `sourceUrl`, throwing `TypeError` | Fixed by using `extractContentPath` (returns `[]` for non-HTTP URLs). Added `sourceUrl !== ''` guard in loader loop as defense-in-depth. |
| **P0-3** | Task 7 bleed checks are manual-only (`node -e` script) with no automated CI guard — content bleed is a core correctness invariant | Promoted bleed patterns to automated test assertions in `tests/parser.test.ts`. Tests are fence-aware to avoid false positives from code examples. |
| **P1-G** | `toContain('unknown-page')` test passes under both buggy and fixed `getUnmappedSegments` — vacuous assertion | Replaced with 5 discriminating exact-output test cases. |
| **P1-H** | `seg in SECTION_TO_CATEGORY` returns `true` for `'constructor'` via `Object.prototype` chain | Changed to `Object.hasOwn(SECTION_TO_CATEGORY, seg)`. |

**No task resequencing.** Amendments are localized to Task 6 (diagnostics) and Task 7 (verification).

---

## Task 1: Parser — New Format Test Fixtures

Add tests for the new `llms-full.txt` format to `parser.test.ts`. These tests define the expected behavior before any parser changes.

**Files:**
- Modify: `tests/parser.test.ts`

**Step 1: Write tests for new format parsing**

Add a new `describe` block after the existing tests:

```typescript
describe('parseSections — new format with --- separators', () => {
  it('splits sections with --- separator between them', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content
---
# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].sourceUrl).toBe('https://example.com/first');
    expect(sections[0].title).toBe('First Topic');
    expect(sections[0].content.trim()).toBe('First content');
    expect(sections[1].sourceUrl).toBe('https://example.com/second');
    expect(sections[1].title).toBe('Second Topic');
    expect(sections[1].content.trim()).toBe('Second content');
  });

  it('section content excludes heading and Source: line by extraction', () => {
    // Content starts after the Source: line — the # Title is captured
    // as title metadata and naturally excluded from content.
    // This is extraction semantics, not post-processing stripping.
    const raw = `# My Page Title
Source: https://example.com/page

Some actual content here

## Subsection
More content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(1);
    expect(sections[0].title).toBe('My Page Title');
    // # Title and Source: line are NOT in content (above the extraction window)
    expect(sections[0].content).not.toMatch(/^# My Page Title/m);
    expect(sections[0].content).not.toMatch(/^Source:/m);
    expect(sections[0].content).toContain('Some actual content here');
    expect(sections[0].content).toContain('## Subsection');
  });

  it('does not include trailing --- or next section title in content', () => {
    const raw = `# First
Source: https://example.com/first

Content of first
---
# Second
Source: https://example.com/second

Content of second`;
    const sections = parseSections(raw);
    expect(sections[0].content).not.toContain('---');
    expect(sections[0].content).not.toContain('# Second');
  });

  it('handles first section without leading ---', () => {
    // The new format starts immediately with # Title + Source (no leading ---)
    const raw = `# First Topic
Source: https://example.com/first

First content
---
# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].title).toBe('First Topic');
  });

  it('preserves --- horizontal rules inside section content', () => {
    const raw = `# Topic
Source: https://example.com/topic

Some content

---

More content after horizontal rule
---
# Next Topic
Source: https://example.com/next

Next content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    // The mid-content --- (with blank lines around it) should be preserved
    // Only the --- immediately preceding # Next Topic should be a boundary
    expect(sections[0].content).toContain('---');
    expect(sections[0].content).toContain('More content after horizontal rule');
  });

  it('does not consume distant --- as section boundary', () => {
    // A --- separated from the heading by many blank lines should NOT
    // be treated as a section boundary (max 3 blank-line lookback guard)
    const raw = `# First
Source: https://example.com/first

Content with a horizontal rule

---




More content after many blank lines
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    // The distant --- should be in first section's content, not consumed as boundary
    expect(sections[0].content).toContain('Content with a horizontal rule');
    expect(sections[0].content).toContain('More content after many blank lines');
  });

  it('produces no preamble when file starts with # Title + Source', () => {
    const raw = `# Topic
Source: https://example.com/topic

Content`;
    const sections = parseSections(raw);
    // No preamble section — only the Source-anchored section
    expect(sections).toHaveLength(1);
    expect(sections[0].sourceUrl).toBe('https://example.com/topic');
  });

  it('filters bare --- preamble as non-meaningful', () => {
    const raw = `---
# Topic
Source: https://example.com/topic

Content`;
    const sections = parseSections(raw);
    // The leading --- should not create a preamble section
    const sourceSections = sections.filter(s => s.sourceUrl !== '');
    expect(sourceSections).toHaveLength(1);
    expect(sourceSections[0].title).toBe('Topic');
  });
});

describe('parseSections — backward compatibility with old format', () => {
  it('still handles old format without --- separators', () => {
    const raw = `# First Topic
Source: https://example.com/first

First content

# Second Topic
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    expect(sections).toHaveLength(2);
    expect(sections[0].title).toBe('First Topic');
    expect(sections[1].title).toBe('Second Topic');
    // Content excludes heading by extraction (content starts after Source: line)
    expect(sections[0].content).not.toMatch(/^# First Topic/m);
  });
});
```

**Step 1b: Update existing parser test if needed**

Check the existing test at `parser.test.ts` (near line 15) that asserts `sections[0].content` includes `# Hello`. This test should still pass with the new parser because content extraction semantics are unchanged for content that appears after the `Source:` line. Verify during implementation — if it breaks, the test's fixture has content structured differently than expected.

**Step 2: Run tests to verify they fail**

Run: `npm test -- tests/parser.test.ts`
Expected: New tests FAIL (content boundary assertions fail because current parser includes trailing `---` and next section's title in content).

**Step 3: Commit failing tests**

```bash
git add tests/parser.test.ts
git commit -m "test(parser): add test fixtures for new llms-full.txt format

Tests define expected behavior for:
- --- section separators (new format)
- Content extraction semantics (heading excluded by extraction window)
- Trailing --- scaffold removal
- Horizontal rule preservation inside content
- Distant --- not consumed as boundary (max blank-line guard)
- Preamble filtering for bare ---
- Backward compatibility with old format"
```

---

## Task 2: Parser — Two-Pass Boundary Resolution

Rewrite `parseSections` to use a two-pass approach: Pass 1 collects `Source:` matches, Pass 2 resolves each section's `pageStart` by looking backward for the nearest heading and optional `---`.

**Files:**
- Modify: `src/parser.ts`

**Step 1: Implement the two-pass parser**

Replace the `parseSections` function in `src/parser.ts`. Keep `findLastHeadingBefore`, `findFirstHeadingInRange`, and `lineBreakAfter` unchanged. Replace only `parseSections`:

```typescript
/**
 * Determine if a line at a given index is a standalone --- separator.
 * A standalone separator is:
 * - Exactly "---" (with optional trailing whitespace)
 * - At the start of a line (beginning of string or preceded by \n)
 */
function isStandaloneSeparator(raw: string, lineStart: number): boolean {
  // Check the line content from lineStart
  const lineEnd = raw.indexOf('\n', lineStart);
  const line = raw.slice(lineStart, lineEnd === -1 ? raw.length : lineEnd);
  return /^---\s*$/.test(line);
}

/**
 * Find the start of the line at or before a given index.
 */
function findLineStart(raw: string, index: number): number {
  const prevNewline = raw.lastIndexOf('\n', index - 1);
  return prevNewline === -1 ? 0 : prevNewline + 1;
}

/** Max blank lines to skip when looking backward for a --- separator. */
const MAX_LOOKBACK_NEWLINES = 3;

/**
 * Parse raw llms-full.txt content into sections using a two-pass approach.
 *
 * Pass 1: Collect all Source: line positions.
 * Pass 2: For each Source: line, resolve the section boundary (pageStart)
 *          by looking backward for the nearest heading and optional --- separator.
 *
 * Section content runs from after the Source: line to the next section's pageStart.
 * The # Title line is naturally excluded from content because it precedes the
 * Source: line — no post-processing stripping needed.
 *
 * Supports both old format (# Title + Source:) and new format (--- + # Title + Source:).
 * The --- lookback finds nothing in the old format, so boundaries degrade gracefully.
 */
export function parseSections(raw: string): ParsedSection[] {
  const sourceRe = /^Source:\s+(\S+)\s*$/gm;
  const matches = Array.from(raw.matchAll(sourceRe));
  const sections: ParsedSection[] = [];

  // No Source: lines found — return entire content as single section
  if (matches.length === 0) {
    const title = findFirstHeadingInRange(raw, 0, raw.length);
    if (raw.trim().length > 0) {
      sections.push({ sourceUrl: '', title, content: raw });
    }
    return sections;
  }

  // Pass 1: Resolve pageStart for each Source: match
  // pageStart is the earliest boundary of this section — the --- line,
  // the heading line, or the Source: line itself (whichever comes first).
  const pageStarts: number[] = [];

  for (const match of matches) {
    const matchIndex = match.index ?? 0;
    const heading = findLastHeadingBefore(raw, matchIndex);

    let pageStart = matchIndex; // Default: Source: line itself

    if (heading.index >= 0) {
      pageStart = heading.index; // Heading found — section starts at heading

      // Check for a --- line immediately before the heading (within MAX_LOOKBACK_NEWLINES)
      const headingLineStart = findLineStart(raw, heading.index);
      if (headingLineStart > 0) {
        // Walk backward past blank lines (whitespace-only lines count as blank)
        let checkPos = headingLineStart - 1;
        let newlineCount = 0;
        while (
          checkPos >= 0 &&
          (raw[checkPos] === '\n' || raw[checkPos] === '\r' ||
           raw[checkPos] === ' ' || raw[checkPos] === '\t')
        ) {
          if (raw[checkPos] === '\n') newlineCount++;
          if (newlineCount > MAX_LOOKBACK_NEWLINES) break;
          checkPos--;
        }
        if (checkPos >= 0 && newlineCount <= MAX_LOOKBACK_NEWLINES) {
          const candidateLineStart = findLineStart(raw, checkPos);
          if (isStandaloneSeparator(raw, candidateLineStart)) {
            pageStart = candidateLineStart;
          }
        }
      }
    }

    pageStarts.push(pageStart);
  }

  // Handle preamble: content before the first section's pageStart
  if (pageStarts[0] > 0) {
    const preamble = raw.slice(0, pageStarts[0]);
    // Filter non-meaningful preamble (blank or just ---)
    const meaningful = preamble.replace(/^---\s*$/gm, '').trim();
    if (meaningful.length > 0) {
      const title = findFirstHeadingInRange(raw, 0, pageStarts[0]);
      sections.push({ sourceUrl: '', title, content: preamble.trim() });
    }
  }

  // Pass 2: Extract sections using pageStarts as boundaries
  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const sourceUrl = match[1];
    const matchIndex = match.index ?? 0;
    const lineEnd = matchIndex + match[0].length;
    const contentStart = lineBreakAfter(raw, lineEnd);

    // Content ends at the next section's pageStart, or end of file
    const contentEnd = i + 1 < matches.length ? pageStarts[i + 1] : raw.length;

    const content = raw.slice(contentStart, contentEnd).trimEnd();

    // Extract title from the heading before Source:
    const heading = findLastHeadingBefore(raw, matchIndex);
    const title = heading.title;

    sections.push({ sourceUrl, title, content });
  }

  return sections;
}
```

**Step 2: Run tests**

Run: `npm test -- tests/parser.test.ts`
Expected: All parser tests PASS — both old and new format tests.

**Step 3: Run full test suite**

Run: `npm test`
Expected: Most tests pass. Existing loader/golden-query tests may fail because they use old-format mock content — those are updated in Task 3 (next).

**Step 4: Build to verify TypeScript compiles**

Run: `npm run build`
Expected: Clean compilation, no errors.

**Step 5: Commit**

```bash
git add src/parser.ts
git commit -m "feat(parser): two-pass boundary resolution for new llms-full.txt format

Source: remains the canonical section anchor. For each Source: match,
resolve pageStart by looking backward for nearest heading, then
optionally extending to a preceding standalone --- line.

Lookback has a max blank-line guard (3 lines) and treats
whitespace-only lines as blank to prevent consuming distant
horizontal rules as section boundaries.

Content naturally excludes # Title (above extraction window).
Handles both old format (no ---) and new format (--- separators)
via graceful degradation."
```

---

## Task 3: Update Test Fixtures for New Format

Update the golden-queries mock content and loader tests to use the new `--- / # Title / Source:` format. This ensures the test suite validates the full pipeline with realistic input **before** adding JSX tracking.

**Rationale for early sequencing:** Running Tasks 4-6 against old-format fixtures masks regressions — golden-query tests assert search relevance, not parse correctness. Moving fixture updates here ensures all subsequent tasks run against realistic input.

**Files:**
- Modify: `tests/golden-queries.test.ts`
- Modify: `tests/loader.test.ts`

**Step 1: Update golden queries mock content**

Replace `MOCK_LLMS_CONTENT` in `tests/golden-queries.test.ts` to use the new format with `---` separators and JSX components:

```typescript
const MOCK_LLMS_CONTENT = `# Hooks
Source: https://code.claude.com/docs/en/hooks

Learn how to automate actions in Claude Code using hooks—shell commands that run automatically before or after specific events.

## What are hooks

Hooks are shell commands that Claude Code executes automatically at specific points during its operation. They allow you to customize behavior, enforce policies, and integrate with external tools.

<Note>
  Hooks run locally on your machine and are not sent to Anthropic servers.
</Note>

## Exit codes and blocking

Exit codes control hook behavior:
- Exit code 0: Success, Claude Code continues
- Exit code 2: Block the operation (for PreToolUse hooks)
- Other non-zero: Warning logged, operation continues

## PreToolUse JSON output

When using JSON output mode, PreToolUse hooks receive tool input as structured JSON on stdin. The output format includes tool name, parameters, and context.

## Common fields in hook input

All hooks receive common fields including session_id, timestamp, tool_name (for tool hooks), and user context.
---
# Skills
Source: https://code.claude.com/docs/en/skills

Learn how to extend Claude Code with custom skills—reusable instruction sets that guide Claude's behavior for specific tasks.

## Skill frontmatter

Skills use YAML frontmatter to define metadata:
- name: Skill identifier
- description: What the skill does
- model_invocable: Whether Claude can invoke directly

<Tip>
  Use descriptive skill names that clearly indicate when the skill should be activated.
</Tip>

## Creating skills

Create a SKILL.md file in your .claude/skills directory with the appropriate frontmatter and instructions.
---
# MCP Servers
Source: https://code.claude.com/docs/en/mcp

Model Context Protocol (MCP) enables Claude to communicate with external tools and data sources.

## MCP server registration

Register MCP servers in your settings.json under the "mcpServers" key. Each server needs a command to launch and optional arguments.

## Building MCP servers

MCP servers expose tools that Claude can invoke. Use the @modelcontextprotocol/sdk to build servers with tool definitions.
---
# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Get started with Claude Code in minutes. This quickstart guide walks you through installation and your first interaction.

## Installation steps

<Steps>
  <Step title="Install Claude Code">
    Install Claude Code globally using npm package manager: npm install -g @anthropic-ai/claude-code. The npm package includes all dependencies.
  </Step>
  <Step title="Run your first session">
    Run claude in your terminal to start an interactive session.
  </Step>
</Steps>

## First run

Run claude in your terminal to start an interactive session. This quickstart covers the basics.
---
# Amazon Bedrock
Source: https://code.claude.com/docs/en/amazon-bedrock

Configure Claude Code to use Amazon Bedrock as the model provider for enterprise deployments.

## Setting up Bedrock credentials

Configure your AWS credentials using the AWS CLI or environment variables. Set ANTHROPIC_BEDROCK_REGION and AWS_ACCESS_KEY_ID for Bedrock authentication.

## Bedrock model selection

Choose the appropriate Bedrock model ID for your use case.
---
# VS Code Integration
Source: https://code.claude.com/docs/en/vs-code

Integrate Claude Code with Visual Studio Code for inline coding assistance.

## Installing the VS Code extension

Install the Claude Code VS Code extension from the Visual Studio Code marketplace. Search for "Claude Code" in the extensions panel.

## VS Code keybindings

Configure VS Code keyboard shortcuts for quick access to Claude Code features.
---
# GitHub Actions
Source: https://code.claude.com/docs/en/github-actions

Run Claude Code in CI/CD pipelines with GitHub Actions for automated workflows.

## GitHub Actions workflow setup

Add Claude Code to your GitHub Actions workflow YAML file for automated code review. Configure the actions/checkout step first.

## GitHub Actions secrets

Store your ANTHROPIC_API_KEY in GitHub Actions secrets for secure CI/CD integration.
---
# Security
Source: https://code.claude.com/docs/en/security

Understand Claude Code's security model, permissions, and best practices for secure usage.

## Sandboxing and isolation

Claude Code uses sandbox isolation to limit filesystem access and restrict command execution. The sandbox prevents unauthorized system modifications.

<Warning>
  Always review Claude Code's suggested commands before approving execution in production environments.
</Warning>

## Permission boundaries

Configure permission boundaries to control what Claude Code can access.
---
# Troubleshooting
Source: https://code.claude.com/docs/en/troubleshooting

Common troubleshooting issues and diagnostic solutions when using Claude Code.

## Connection troubleshooting

If you see connection errors during troubleshooting, check your network settings, firewall rules, and API key validity. Common network issues include proxy misconfiguration.

## Debug logging

Enable debug logging for troubleshooting by setting CLAUDE_DEBUG=1.
---
# Create custom subagents
Source: https://code.claude.com/docs/en/sub-agents

Subagents are specialized assistants defined in .claude/agents/ that Claude can delegate to for isolated tasks. They run in their own context with their own set of allowed tools.

## Defining subagents

Create agent files in .claude/agents/<agent-name>.md with YAML frontmatter specifying name, description, tools, and model.

## Subagent isolation

Each subagent runs in a separate context window. This keeps the main conversation clean by offloading investigation and analysis to isolated specialists.

## Using subagents

Invoke subagents with phrases like "use a subagent to review this code" or delegate specific tasks to specialized agents for focused analysis.
`;
```

**Step 2: Update loader test mock content**

Update the mock content in `tests/loader.test.ts` for the `loadFromOfficial` describe block. Multi-section test fixtures should use `---` separators:

```typescript
  it('fetches, parses, and returns all sections (no filtering)', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here
---
# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Getting started content`;

    // ... rest of test unchanged
  });
```

The other tests in `loadFromOfficial` use single-section content and don't need `---` separators.

**Step 3: Run full test suite**

Run: `npm test`
Expected: All tests pass. Golden queries should still match their expected categories with the new format.

**Step 4: Commit**

```bash
git add tests/golden-queries.test.ts tests/loader.test.ts
git commit -m "test: update mock content fixtures to new llms-full.txt format

Golden queries and loader tests now use --- separators and JSX
components (<Note>, <Tip>, <Warning>, <Steps>/<Step>) matching
the current production format. All golden queries still hit their
expected categories."
```

---

## Task 4: JSX Block Tracker

Create `JsxBlockTracker` — a known-tag stack tracker for JSX-like Mintlify components. It tells the chunker not to split inside these blocks.

**Files:**
- Create: `src/jsx-block-tracker.ts`
- Create: `tests/jsx-block-tracker.test.ts`

**Step 1: Write the failing tests**

Create `tests/jsx-block-tracker.test.ts`:

```typescript
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
```

**Step 2: Run tests to verify they fail**

Run: `npm test -- tests/jsx-block-tracker.test.ts`
Expected: FAIL — module not found.

**Step 3: Implement JsxBlockTracker**

Create `src/jsx-block-tracker.ts`:

```typescript
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
```

**Step 4: Run tests**

Run: `npm test -- tests/jsx-block-tracker.test.ts`
Expected: All tests PASS.

**Step 5: Build**

Run: `npm run build`
Expected: Clean compilation.

**Step 6: Commit**

```bash
git add src/jsx-block-tracker.ts tests/jsx-block-tracker.test.ts
git commit -m "feat: add JsxBlockTracker for Mintlify component awareness

Known-tag stack tracker for 16 Mintlify components (Warning, Note,
Tip, Steps, Step, Frame, Card, CodeGroup, Accordion, AccordionGroup,
Tabs, Tab, Callout, CardGroup, Info, MCPServersTable).
Line-start preference reduces false positives from inline text.
Depth cap (16) with reset prevents runaway state."
```

---

## Task 5: Protected Block Tracker (Composite)

Create `ProtectedBlockTracker` that wraps `FenceTracker` + `JsxBlockTracker`, then swap it into the chunker.

**Files:**
- Create: `src/protected-block-tracker.ts`
- Create: `tests/protected-block-tracker.test.ts`
- Modify: `src/chunker.ts`

**Step 1: Write the failing tests**

Create `tests/protected-block-tracker.test.ts`:

```typescript
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
```

**Step 2: Run tests to verify they fail**

Run: `npm test -- tests/protected-block-tracker.test.ts`
Expected: FAIL — module not found.

**Step 3: Implement ProtectedBlockTracker**

Create `src/protected-block-tracker.ts`:

```typescript
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
```

**Step 4: Run tests**

Run: `npm test -- tests/protected-block-tracker.test.ts`
Expected: All tests PASS.

**Step 5: Integrate into chunker**

Modify `src/chunker.ts`. Verify actual line numbers before editing — the plan references approximate locations.

1. Update the import:

```typescript
// Replace:
import { FenceTracker } from './fence-tracker.js';

// With:
import { ProtectedBlockTracker } from './protected-block-tracker.js';
```

2. In `splitByHeadingOutsideFences` (find the function — verify line number): replace `new FenceTracker()` with `new ProtectedBlockTracker()`:

```typescript
// Replace:
  const fence = new FenceTracker();
// With:
  const tracker = new ProtectedBlockTracker();
```

And update the variable references:

```typescript
// Replace:
    const inFence = fence.processLine(line);
// With:
    const inProtected = tracker.processLine(line);

// Replace:
    if (!inFence && pattern.test(line)) {
// With:
    if (!inProtected && pattern.test(line)) {
```

3. In `splitByParagraphOutsideFences` (find the function — verify line number): same replacement:

```typescript
// Replace:
  const fence = new FenceTracker();
// ...
    const inFence = fence.processLine(line);
// ...
    if (!inFence) {
// ...
    } else {
      // Inside a fence - just accumulate
// With:
  const tracker = new ProtectedBlockTracker();
// ...
    const inProtected = tracker.processLine(line);
// ...
    if (!inProtected) {
// ...
    } else {
      // Inside a protected block - just accumulate
```

**Step 6: Run full test suite**

Run: `npm test`
Expected: All tests pass. The chunker tests should continue passing since `ProtectedBlockTracker` is a superset of `FenceTracker` behavior.

**Step 7: Build**

Run: `npm run build`
Expected: Clean compilation.

**Step 8: Commit**

```bash
git add src/protected-block-tracker.ts tests/protected-block-tracker.test.ts src/chunker.ts
git commit -m "feat: composite ProtectedBlockTracker + chunker integration

ProtectedBlockTracker wraps FenceTracker + JsxBlockTracker. Replaces
bare FenceTracker in splitByHeadingOutsideFences and
splitByParagraphOutsideFences so chunk splits respect both code
fences and JSX component boundaries.

FenceTracker is unchanged — new behavior is purely additive."
```

---

## Task 6: Loader — Parse Diagnostics and Category Warnings

Add observability to `loadFromOfficial`: log section count diagnostics and warn about unmapped URL segments in category derivation. Use per-load local state to avoid module-level mutable state that leaks across tests.

**Files:**
- Modify: `src/loader.ts`
- Modify: `src/frontmatter.ts`
- Modify: `tests/loader.test.ts`
- Modify: `tests/frontmatter.test.ts`

**Step 1: Write tests for diagnostics**

Add to the `loadFromOfficial` describe block in `tests/loader.test.ts`:

```typescript
  it('logs parse diagnostics to stderr', async () => {
    const mockContent = `# Hooks Guide
Source: https://code.claude.com/docs/en/hooks

Hooks content here
---
# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Getting started content`;

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(mockContent),
    });
    vi.stubGlobal('fetch', mockFetch);

    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const cachePath = path.join(tempDir, 'cache.txt');
    await loadFromOfficial('https://example.com/docs', cachePath);

    // Should log parse diagnostics
    const diagnosticLog = errorSpy.mock.calls.find(
      call => typeof call[0] === 'string' && call[0].includes('Parse diagnostics')
    );
    expect(diagnosticLog).toBeDefined();
    errorSpy.mockRestore();
  });
```

**Note on test setup:** Use the module-level `loadFromOfficial` import rather than dynamic `import()` inside the test. Dynamic imports inside tests hit module caching in Vitest's default isolation mode, making spies unreliable. If the existing test file uses dynamic imports for `loadFromOfficial`, refactor to top-level import.

**Step 2: Run test to verify it fails**

Run: `npm test -- tests/loader.test.ts`
Expected: FAIL — no diagnostic log found.

**Step 3: Add unmapped segment detection to frontmatter.ts**

Add a pure function (no side effects, no module-level state) to `frontmatter.ts`:

```typescript
import { extractContentPath } from './url-helpers.js';

/**
 * Find URL path segments not mapped in SECTION_TO_CATEGORY.
 * Returns unmapped segment names for diagnostics.
 * Uses extractContentPath to strip /docs/{lang}/ prefix — same normalization as deriveCategory.
 * Pure function — no side effects.
 */
export function getUnmappedSegments(sourceUrl: string): string[] {
  const segments = extractContentPath(sourceUrl);
  return segments.filter(seg => !Object.hasOwn(SECTION_TO_CATEGORY, seg));
}
```

Note: `extractContentPath` returns `[]` for non-HTTP URLs and empty strings, so `getUnmappedSegments('')` safely returns `[]` without throwing.

Also add a test to `tests/frontmatter.test.ts`:

```typescript
describe('getUnmappedSegments', () => {
  it('returns empty for fully mapped URL', () => {
    expect(getUnmappedSegments('https://code.claude.com/docs/en/hooks')).toEqual([]);
  });

  it('returns only unmapped segments (excludes docs/en prefix)', () => {
    expect(getUnmappedSegments('https://code.claude.com/docs/en/unknown-page')).toEqual(['unknown-page']);
  });

  it('returns empty for empty sourceUrl', () => {
    expect(getUnmappedSegments('')).toEqual([]);
  });

  it('does not match prototype properties as mapped', () => {
    // Object.hasOwn prevents 'constructor' from matching via Object.prototype
    expect(getUnmappedSegments('https://code.claude.com/docs/en/constructor')).toEqual(['constructor']);
  });

  it('returns empty for invalid URL', () => {
    expect(getUnmappedSegments('not-a-url')).toEqual([]);
  });
});
```

**Step 4: Add parse diagnostics to loader.ts**

In `loadFromOfficial`, after the `fetchAndParse` call and filtering, add diagnostics:

```typescript
// After filtering: const filtered = sections.filter(...)
// Count only Source:-anchored sections (exclude preamble pseudo-section)
const sourceAnchoredCount = sections.filter(s => s.sourceUrl !== '').length;
const diagnostics = {
  sourceLineCount: sourceAnchoredCount,
  nonEmptySectionCount: filtered.length,
};
console.error(
  `Parse diagnostics: ${diagnostics.sourceLineCount} Source: lines, ` +
  `${diagnostics.nonEmptySectionCount} non-empty sections`
);

// Report unmapped URL segments (per-load, no module-level state)
// Guard: skip preamble sections with empty sourceUrl (defense-in-depth —
// getUnmappedSegments handles '' safely, but the guard makes intent explicit)
const unmapped = new Map<string, number>();
for (const section of filtered) {
  if (section.sourceUrl === '') continue;
  for (const seg of getUnmappedSegments(section.sourceUrl)) {
    unmapped.set(seg, (unmapped.get(seg) ?? 0) + 1);
  }
}
if (unmapped.size > 0) {
  const entries = [...unmapped.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([seg, count]) => `${seg} (${count}x)`)
    .join(', ');
  console.warn(`Category: ${unmapped.size} unmapped URL segment(s): ${entries}`);
}
```

Add the import:

```typescript
import { getUnmappedSegments } from './frontmatter.js';
```

**Step 5: Run tests**

Run: `npm test`
Expected: All tests pass.

**Step 6: Build**

Run: `npm run build`
Expected: Clean compilation.

**Step 7: Commit**

```bash
git add src/loader.ts src/frontmatter.ts tests/loader.test.ts tests/frontmatter.test.ts
git commit -m "feat: add parse diagnostics and category unmapped-segment warnings

loadFromOfficial now logs section count diagnostics (sourceLineCount
excludes preamble pseudo-section). Unmapped URL segments are collected
per-load (local Map, no module-level state) and reported once via
console.warn.

getUnmappedSegments is a pure function in frontmatter.ts with
dedicated test coverage."
```

---

## Task 7: End-to-End Verification

Verify the full pipeline works against the live `llms-full.txt`, add automated bleed-detection tests, and run the complete test suite.

**Files:**
- Modify: `tests/parser.test.ts` (add bleed-detection test suite)

**Step 1: Run full test suite**

Run: `npm test`
Expected: All tests pass (253+ tests, 0 failures).

**Step 2: Build**

Run: `npm run build`
Expected: Clean TypeScript compilation.

**Step 3: Run against live docs (manual smoke test)**

Run: `DOCS_URL=https://code.claude.com/docs/llms-full.txt npm run start:dev`

Or test by temporarily importing and calling the loader:

```bash
node -e "
  import('./dist/loader.js').then(async m => {
    const { files } = await m.loadFromOfficial('https://code.claude.com/docs/llms-full.txt');
    console.log('Sections:', files.length);
    console.log('First 3 paths:', files.slice(0, 3).map(f => f.path));
    console.log('First section content preview:', files[0]?.content.slice(0, 200));
  });
"
```

Expected:
- Section count matches the number of `Source:` lines in the live docs (40+)
- Section paths are clean URLs (not polluted with `---` or next section's heading)
- Section content starts with synthetic frontmatter, not with `# Title`

**Step 4: Write automated bleed-detection tests**

Content bleed is a core correctness invariant — CI must enforce it, not a manual script.
Add to `tests/parser.test.ts`:

```typescript
describe('parseSections — content bleed detection', () => {
  it('section content does not end with trailing ---', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      expect(section.content.trimEnd()).not.toMatch(/---$/);
    }
  });

  it('section content does not contain Source: URL lines', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      // Only match Source: lines that look like section anchors (with URL),
      // not literal "Source:" text in prose or code fences
      expect(section.content).not.toMatch(/^Source:\s+https?:\/\//m);
    }
  });

  it('section content does not end with heading+Source pattern', () => {
    const raw = `# First
Source: https://example.com/first

First content
---
# Second
Source: https://example.com/second

Second content`;
    const sections = parseSections(raw);
    for (const section of sections) {
      const lines = section.content.trimEnd().split('\n');
      const lastFew = lines.slice(-5).join('\n');
      expect(lastFew).not.toMatch(/^#\s+.+\nSource:\s+/m);
    }
  });

  it('bleed checks are fence-aware — Source: inside code fences is not bleed', () => {
    // Code examples may contain literal "Source:" or "---" patterns.
    // These are content, not bleed.
    const raw = `# Config Guide
Source: https://example.com/config

Here is an example:

\`\`\`yaml
Source: https://internal.example.com/api
---
# Config header
\`\`\`

More content after code block
---
# Next Section
Source: https://example.com/next

Next content`;
    const sections = parseSections(raw);
    // First section should contain the code fence content (not bleed)
    expect(sections[0].content).toContain('Source: https://internal.example.com/api');
    expect(sections[0].content).toContain('# Config header');
    // But should not contain the real next section's Source: line
    expect(sections[0].content).not.toMatch(/^Source:\s+https:\/\/example\.com\/next/m);
  });
});
```

**Step 5: Run manual smoke test against live docs**

The automated tests above cover the bleed invariant in CI. This manual step is a supplementary
check against the live corpus (not a substitute for CI):

```bash
node -e "
  import('./dist/loader.js').then(async m => {
    const { files } = await m.loadFromOfficial('https://code.claude.com/docs/llms-full.txt');
    let bleedCount = 0;
    for (let i = 0; i < files.length; i++) {
      const body = files[i].content;
      if (body.trimEnd().endsWith('---')) {
        console.log('BLEED: section', i, 'ends with ---');
        bleedCount++;
      }
      if (/^Source:\s+https?:\/\//m.test(body)) {
        console.log('BLEED: section', i, 'contains Source: line in body');
        bleedCount++;
      }
      const lines = body.trimEnd().split('\n');
      const lastFew = lines.slice(-5).join('\n');
      if (/^#\s+.+\nSource:\s+/m.test(lastFew)) {
        console.log('BLEED: section', i, 'ends with heading+Source pattern');
        bleedCount++;
      }
    }
    console.log('Total bleed:', bleedCount, 'of', files.length, 'sections');
  });
"
```

Expected: `Total bleed: 0`

**Step 6: Commit**

```bash
git add tests/parser.test.ts
git commit -m "test: add automated bleed-detection tests for parser

Four bleed-invariant assertions: trailing ---, Source: URL in body,
heading+Source pattern, and fence-aware false-positive check. These
promote the manual smoke-test bleed checks to CI-enforced tests."
```

If Step 3/5 revealed issues that required additional fixes, include those files in the commit.
