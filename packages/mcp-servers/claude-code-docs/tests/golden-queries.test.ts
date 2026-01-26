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

# Quickstart
Source: https://code.claude.com/docs/en/quickstart

Get started with Claude Code in minutes. This quickstart guide walks you through installation and your first interaction.

## Installation steps

Install Claude Code globally using npm package manager: npm install -g @anthropic-ai/claude-code. The npm package includes all dependencies.

## First run

Run claude in your terminal to start an interactive session. This quickstart covers the basics.

# Amazon Bedrock
Source: https://code.claude.com/docs/en/amazon-bedrock

Configure Claude Code to use Amazon Bedrock as the model provider for enterprise deployments.

## Setting up Bedrock credentials

Configure your AWS credentials using the AWS CLI or environment variables. Set ANTHROPIC_BEDROCK_REGION and AWS_ACCESS_KEY_ID for Bedrock authentication.

## Bedrock model selection

Choose the appropriate Bedrock model ID for your use case.

# VS Code Integration
Source: https://code.claude.com/docs/en/vs-code

Integrate Claude Code with Visual Studio Code for inline coding assistance.

## Installing the VS Code extension

Install the Claude Code VS Code extension from the Visual Studio Code marketplace. Search for "Claude Code" in the extensions panel.

## VS Code keybindings

Configure VS Code keyboard shortcuts for quick access to Claude Code features.

# GitHub Actions
Source: https://code.claude.com/docs/en/github-actions

Run Claude Code in CI/CD pipelines with GitHub Actions for automated workflows.

## GitHub Actions workflow setup

Add Claude Code to your GitHub Actions workflow YAML file for automated code review. Configure the actions/checkout step first.

## GitHub Actions secrets

Store your ANTHROPIC_API_KEY in GitHub Actions secrets for secure CI/CD integration.

# Security
Source: https://code.claude.com/docs/en/security

Understand Claude Code's security model, permissions, and best practices for secure usage.

## Sandboxing and isolation

Claude Code uses sandbox isolation to limit filesystem access and restrict command execution. The sandbox prevents unauthorized system modifications.

## Permission boundaries

Configure permission boundaries to control what Claude Code can access.

# Troubleshooting
Source: https://code.claude.com/docs/en/troubleshooting

Common troubleshooting issues and diagnostic solutions when using Claude Code.

## Connection troubleshooting

If you see connection errors during troubleshooting, check your network settings, firewall rules, and API key validity. Common network issues include proxy misconfiguration.

## Debug logging

Enable debug logging for troubleshooting by setting CLAUDE_DEBUG=1.
`;

describe('golden queries (URL-based)', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let originalMinSectionCount: string | undefined;

  beforeAll(async () => {
    clearParseWarnings();

    // Disable section count validation for test with small mock data
    originalMinSectionCount = process.env.MIN_SECTION_COUNT;
    process.env.MIN_SECTION_COUNT = '0';
    vi.resetModules();

    // Mock fetch to return our test content
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'text/plain' }),
      text: () => Promise.resolve(MOCK_LLMS_CONTENT),
    });
    vi.stubGlobal('fetch', mockFetch);

    // Import and call loadFromOfficial with mocked fetch
    // Use forceRefresh=true to bypass cache and use the mocked fetch
    const { loadFromOfficial } = await import('../src/loader.js');
    const { files } = await loadFromOfficial(
      'https://code.claude.com/docs/llms-full.txt',
      undefined,
      true, // forceRefresh
    );

    // Build the search index
    const chunks = files.flatMap((f) => chunkFile(f));
    index = buildBM25Index(chunks);
  });

  afterAll(() => {
    // Restore original env
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();
  });

  const goldenQueries = [
    // Extension categories (existing)
    { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
    { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
    { query: 'skill frontmatter', expectedTopCategory: 'skills' },
    { query: 'MCP server registration', expectedTopCategory: 'mcp' },
    { query: 'common fields hook input', expectedTopCategory: 'hooks' },
    // New categories
    { query: 'quickstart npm package installation', expectedTopCategory: 'getting-started' },
    { query: 'bedrock AWS credentials region', expectedTopCategory: 'providers' },
    { query: 'VS Code keybindings extension', expectedTopCategory: 'ide' },
    { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
    { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
    { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
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

  it('new category chunks exist and have correct categories', () => {
    // Verify new category sections are being indexed with correct categories
    const quickstartChunks = index.chunks.filter((c) => c.source_file.includes('quickstart'));
    const bedrockChunks = index.chunks.filter((c) => c.source_file.includes('bedrock'));
    const vscodeChunks = index.chunks.filter((c) => c.source_file.includes('vs-code'));
    const actionsChunks = index.chunks.filter((c) => c.source_file.includes('github-actions'));
    const securityChunks = index.chunks.filter((c) => c.source_file.includes('security'));
    const troubleshootingChunks = index.chunks.filter((c) =>
      c.source_file.includes('troubleshooting'),
    );

    expect(quickstartChunks.length).toBeGreaterThan(0);
    expect(bedrockChunks.length).toBeGreaterThan(0);
    expect(vscodeChunks.length).toBeGreaterThan(0);
    expect(actionsChunks.length).toBeGreaterThan(0);
    expect(securityChunks.length).toBeGreaterThan(0);
    expect(troubleshootingChunks.length).toBeGreaterThan(0);

    // Verify categories are correctly derived from URLs
    for (const chunk of quickstartChunks) {
      expect(chunk.category).toBe('getting-started');
    }
    for (const chunk of bedrockChunks) {
      expect(chunk.category).toBe('providers');
    }
    for (const chunk of vscodeChunks) {
      expect(chunk.category).toBe('ide');
    }
    for (const chunk of actionsChunks) {
      expect(chunk.category).toBe('ci-cd');
    }
    for (const chunk of securityChunks) {
      expect(chunk.category).toBe('security');
    }
    for (const chunk of troubleshootingChunks) {
      expect(chunk.category).toBe('troubleshooting');
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
