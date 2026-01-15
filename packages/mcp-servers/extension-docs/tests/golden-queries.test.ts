// tests/golden-queries.test.ts
import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';
import { clearParseWarnings } from '../src/frontmatter.js';

// Mock content that simulates the llms-full.txt format from code.claude.com
const MOCK_LLMS_CONTENT = `# Hooks
Source: https://code.claude.com/docs/en/hooks

Learn how to automate actions in Claude Code using hooks—shell commands that run automatically before or after specific events.

## What are hooks

Hooks are shell commands that Claude Code executes automatically at specific points during its operation. They allow you to customize behavior, enforce policies, and integrate with external tools.

## Exit codes and blocking

Exit codes control hook behavior:
- Exit code 0: Success, Claude Code continues
- Exit code 2: Block the operation (for PreToolUse hooks)
- Other non-zero: Warning logged, operation continues

## PreToolUse JSON output

When using JSON output mode, PreToolUse hooks receive tool input as structured JSON on stdin. The output format includes tool name, parameters, and context.

## Common fields in hook input

All hooks receive common fields including session_id, timestamp, tool_name (for tool hooks), and user context.

# Skills
Source: https://code.claude.com/docs/en/skills

Learn how to extend Claude Code with custom skills—reusable instruction sets that guide Claude's behavior for specific tasks.

## Skill frontmatter

Skills use YAML frontmatter to define metadata:
- name: Skill identifier
- description: What the skill does
- model_invocable: Whether Claude can invoke directly

## Creating skills

Create a SKILL.md file in your .claude/skills directory with the appropriate frontmatter and instructions.

# MCP Servers
Source: https://code.claude.com/docs/en/mcp

Model Context Protocol (MCP) enables Claude to communicate with external tools and data sources.

## MCP server registration

Register MCP servers in your settings.json under the "mcpServers" key. Each server needs a command to launch and optional arguments.

## Building MCP servers

MCP servers expose tools that Claude can invoke. Use the @modelcontextprotocol/sdk to build servers with tool definitions.
`;

describe('golden queries (URL-based)', () => {
  let index: ReturnType<typeof buildBM25Index>;

  beforeAll(async () => {
    clearParseWarnings();

    // Mock fetch to return our test content
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(MOCK_LLMS_CONTENT),
    });
    vi.stubGlobal('fetch', mockFetch);

    // Import and call loadFromOfficial with mocked fetch
    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial('https://code.claude.com/docs/llms-full.txt');

    // Build the search index
    const chunks = files.flatMap((f) => chunkFile(f));
    index = buildBM25Index(chunks);
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

  const goldenQueries = [
    { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
    { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
    { query: 'skill frontmatter', expectedTopCategory: 'skills' },
    { query: 'MCP server registration', expectedTopCategory: 'mcp' },
    { query: 'common fields hook input', expectedTopCategory: 'hooks' },
  ];

  for (const { query, expectedTopCategory } of goldenQueries) {
    it(`"${query}" returns ${expectedTopCategory} category in top result`, () => {
      const results = search(index, query, 5);

      expect(results.length).toBeGreaterThan(0);
      expect(results[0].category).toBe(expectedTopCategory);
    });
  }

  it('chunks have correct category derived from URL', () => {
    // Verify that chunks have proper categories, not "https:"
    const hooksChunks = index.chunks.filter((c) => c.source_file.includes('hooks'));
    const skillsChunks = index.chunks.filter((c) => c.source_file.includes('skills'));
    const mcpChunks = index.chunks.filter((c) => c.source_file.includes('mcp'));

    expect(hooksChunks.length).toBeGreaterThan(0);
    expect(skillsChunks.length).toBeGreaterThan(0);
    expect(mcpChunks.length).toBeGreaterThan(0);

    // All should have correct category, not "https:"
    for (const chunk of hooksChunks) {
      expect(chunk.category).toBe('hooks');
    }
    for (const chunk of skillsChunks) {
      expect(chunk.category).toBe('skills');
    }
    for (const chunk of mcpChunks) {
      expect(chunk.category).toBe('mcp');
    }
  });

  it('chunk IDs are simplified from URLs', () => {
    // Verify chunk IDs don't contain the full URL
    for (const chunk of index.chunks) {
      expect(chunk.id).not.toContain('https-code-claude-com');
      expect(chunk.id).not.toContain('http');
    }
  });
});
