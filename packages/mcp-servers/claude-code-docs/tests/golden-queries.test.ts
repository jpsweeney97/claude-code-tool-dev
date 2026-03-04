// tests/golden-queries.test.ts
import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';
import { chunkFile } from '../src/chunker.js';
import { buildBM25Index, search } from '../src/bm25.js';

// Mock content that simulates the llms-full.txt format from code.claude.com
// IMPORTANT: This content is used for testing search quality, not loading.
// Any changes here affect the golden query tests below.
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
---
# Orchestrate teams of Claude Code sessions
Source: https://code.claude.com/docs/en/agent-teams

Coordinate multiple Claude Code instances working together as a team, with shared task lists and inter-agent messaging.

## How agent teams work

Agent teams use a leader-worker pattern where a team lead coordinates multiple Claude Code sessions working on related tasks simultaneously.

## When to use agent teams

Use agent teams when a task has multiple independent subtasks that benefit from parallel execution across separate context windows.
---
# Log in to Claude Code
Source: https://code.claude.com/docs/en/authentication

Log in to Claude Code and configure authentication for individuals, teams, and organizations.

## Authentication methods

Claude Code supports API key authentication, OAuth login, and enterprise SSO for team environments.

## Managing API keys

Store your ANTHROPIC_API_KEY securely. Never commit API keys to version control.
---
# Manage permissions
Source: https://code.claude.com/docs/en/permissions

Control what actions Claude Code can perform using the permission system.

## Permission system

Claude Code uses a tiered permission model. Tools are categorized by risk level and require different approval levels.

## Permission profiles

Choose between different permission modes: default, plan, or acceptEdits for varying levels of autonomy.
---
# Slash Commands
Source: https://code.claude.com/docs/en/slash-commands

Create and use custom slash commands in Claude Code for task automation.

## Defining custom commands

Create command files in .claude/commands/ with YAML frontmatter specifying name and description. Commands can accept arguments and execute shell scripts.

## Built-in commands

Claude Code includes built-in slash commands like /help, /clear, /compact, and /init for common operations.
---
# Plugins
Source: https://code.claude.com/docs/en/plugins

Extend Claude Code functionality with plugins. Plugins bundle commands, skills, hooks, agents, and MCP servers.

## Plugin structure

A plugin requires a plugin.json manifest file defining its components. Plugins are distributed via marketplaces.

## Installing plugins

Install plugins from marketplaces using claude plugin install or by specifying a local path.
---
# Settings
Source: https://code.claude.com/docs/en/settings

Configure Claude Code behavior through settings.json and environment variables.

## Settings hierarchy

Settings follow a hierarchy: global (~/.claude/settings.json), project (.claude/settings.json), and environment variables. More specific settings override general ones.

## Common settings

Configure model preferences, permission modes, and tool restrictions through the settings system.
---
# Memory and CLAUDE.md
Source: https://code.claude.com/docs/en/memory

Claude Code uses CLAUDE.md files as persistent memory across sessions. Project instructions are stored in CLAUDE.md.

## CLAUDE.md locations

CLAUDE.md files can exist at global (~/.claude/CLAUDE.md), project root, and subdirectory levels. Each level adds context for that scope.

## Auto-memory

Claude Code can automatically save insights to memory files for future reference across sessions.
---
# CLI Reference
Source: https://code.claude.com/docs/en/cli-reference

Command-line interface reference for Claude Code. Run claude with various flags and options.

## CLI flags

Common CLI flags include --model for model selection, --allowedTools for tool restrictions, and --print for non-interactive output mode.

## Environment variables

Configure Claude Code behavior through environment variables like ANTHROPIC_API_KEY and CLAUDE_DEBUG.
---
# Interactive Features
Source: https://code.claude.com/docs/en/interactive-mode

Interactive features in Claude Code including vim mode, multi-line editing, and fast mode.

## Vim mode

Enable vim keybindings for efficient text editing in the Claude Code terminal interface.

## Fast mode

Toggle fast mode for faster responses. Fast mode uses the same model with optimized output speed.
---
# Desktop Application
Source: https://code.claude.com/docs/en/desktop

Claude Code desktop application for macOS and Windows. Native app with terminal integration.

## Desktop installation

Download and install the Claude Code desktop app from the official website. The desktop app bundles the CLI.

## Desktop features

The desktop app provides a native window, system tray integration, and automatic updates.
---
# Overview
Source: https://code.claude.com/docs/en/overview

Claude Code is an agentic coding tool that lives in your terminal. It understands your codebase and helps with software engineering tasks.

## What Claude Code can do

Claude Code can edit files, run commands, search code, manage git, create pull requests, and more — all from your terminal.

## How Claude Code works

Claude Code operates as an interactive agent with access to tools for file editing, code search, and command execution.
`;

describe('golden queries (URL-based)', () => {
  let index: ReturnType<typeof buildBM25Index>;
  let originalMinSectionCount: string | undefined;
  let tempDir: string;

  beforeAll(async () => {
    // Create isolated temp directory for cache to avoid polluting production cache
    // This is critical: without this, the mock content would overwrite the real
    // cached docs at ~/Library/Caches/claude-code-docs/llms-full.txt
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'golden-queries-test-'));

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
    // IMPORTANT: Pass explicit cachePath to avoid writing to production cache
    const { loadFromOfficial } = await import('../src/loader.js');
    const cachePath = path.join(tempDir, 'test-cache.txt');
    const { files } = await loadFromOfficial(
      'https://code.claude.com/docs/llms-full.txt',
      cachePath,
      true, // forceRefresh
    );

    // Build the search index
    const chunks = files.flatMap((f) => chunkFile(f).chunks);
    index = buildBM25Index(chunks);
  });

  afterAll(async () => {
    // Restore original env
    if (originalMinSectionCount === undefined) {
      delete process.env.MIN_SECTION_COUNT;
    } else {
      process.env.MIN_SECTION_COUNT = originalMinSectionCount;
    }
    vi.unstubAllGlobals();

    // Clean up temp directory
    if (tempDir) {
      await fs.rm(tempDir, { recursive: true, force: true });
    }
  });

  const goldenQueries = [
    // Extension categories (existing)
    { query: 'hook exit codes blocking', expectedTopCategory: 'hooks' },
    { query: 'PreToolUse JSON output', expectedTopCategory: 'hooks' },
    { query: 'skill frontmatter', expectedTopCategory: 'skills' },
    { query: 'MCP server registration', expectedTopCategory: 'mcp' },
    { query: 'common fields hook input', expectedTopCategory: 'hooks' },
    { query: 'subagent isolated context delegation', expectedTopCategory: 'agents' },
    // New categories
    { query: 'quickstart npm package installation', expectedTopCategory: 'getting-started' },
    { query: 'bedrock AWS credentials region', expectedTopCategory: 'providers' },
    { query: 'VS Code keybindings extension', expectedTopCategory: 'ide' },
    { query: 'GitHub Actions workflow YAML', expectedTopCategory: 'ci-cd' },
    { query: 'sandbox isolation filesystem', expectedTopCategory: 'security' },
    { query: 'troubleshooting debug logging', expectedTopCategory: 'troubleshooting' },
    { query: 'agent teams leader worker coordination', expectedTopCategory: 'agents' },
    { query: 'authentication login API key', expectedTopCategory: 'security' },
    { query: 'permission system approval levels', expectedTopCategory: 'security' },
    // New priority categories (B12)
    { query: 'slash command definition YAML', expectedTopCategory: 'commands' },
    { query: 'plugin manifest structure install', expectedTopCategory: 'plugins' },
    { query: 'settings hierarchy configuration', expectedTopCategory: 'settings' },
    { query: 'CLAUDE.md memory persistent sessions', expectedTopCategory: 'memory' },
    { query: 'CLI flags model allowedTools', expectedTopCategory: 'cli' },
    { query: 'vim mode interactive editing', expectedTopCategory: 'interactive' },
    { query: 'desktop application native install', expectedTopCategory: 'desktop' },
    { query: 'overview agentic terminal tool', expectedTopCategory: 'overview' },
    // Morphological variant queries (stemming coverage)
    { query: 'configuring MCP servers', expectedTopCategory: 'mcp' },
    { query: 'creating custom skills', expectedTopCategory: 'skills' },
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
    const subagentChunks = index.chunks.filter((c) => c.source_file.includes('sub-agents'));

    expect(quickstartChunks.length).toBeGreaterThan(0);
    expect(bedrockChunks.length).toBeGreaterThan(0);
    expect(vscodeChunks.length).toBeGreaterThan(0);
    expect(actionsChunks.length).toBeGreaterThan(0);
    expect(securityChunks.length).toBeGreaterThan(0);
    expect(troubleshootingChunks.length).toBeGreaterThan(0);
    expect(subagentChunks.length).toBeGreaterThan(0);

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
    // sub-agents URL maps to 'agents' category via SECTION_TO_CATEGORY
    for (const chunk of subagentChunks) {
      expect(chunk.category).toBe('agents');
    }
  });

  it('B12 priority category chunks exist and have correct categories', () => {
    // Verify the 8 new priority category sections are indexed correctly
    const commandsChunks = index.chunks.filter((c) => c.source_file.includes('slash-commands'));
    const pluginsChunks = index.chunks.filter((c) =>
      c.source_file.includes('plugins') && !c.source_file.includes('plugin-marketplaces'),
    );
    const settingsChunks = index.chunks.filter((c) =>
      c.source_file.includes('settings') && !c.source_file.includes('server-managed'),
    );
    const memoryChunks = index.chunks.filter((c) => c.source_file.includes('memory'));
    const cliChunks = index.chunks.filter((c) => c.source_file.includes('cli-reference'));
    const interactiveChunks = index.chunks.filter((c) =>
      c.source_file.includes('interactive-mode'),
    );
    const desktopChunks = index.chunks.filter((c) =>
      c.source_file.includes('desktop') && !c.source_file.includes('desktop-quickstart'),
    );
    const overviewChunks = index.chunks.filter((c) => c.source_file.includes('overview'));

    expect(commandsChunks.length).toBeGreaterThan(0);
    expect(pluginsChunks.length).toBeGreaterThan(0);
    expect(settingsChunks.length).toBeGreaterThan(0);
    expect(memoryChunks.length).toBeGreaterThan(0);
    expect(cliChunks.length).toBeGreaterThan(0);
    expect(interactiveChunks.length).toBeGreaterThan(0);
    expect(desktopChunks.length).toBeGreaterThan(0);
    expect(overviewChunks.length).toBeGreaterThan(0);

    // Verify categories are correctly derived from URLs
    for (const chunk of commandsChunks) {
      expect(chunk.category).toBe('commands');
    }
    for (const chunk of pluginsChunks) {
      expect(chunk.category).toBe('plugins');
    }
    for (const chunk of settingsChunks) {
      expect(chunk.category).toBe('settings');
    }
    for (const chunk of memoryChunks) {
      expect(chunk.category).toBe('memory');
    }
    for (const chunk of cliChunks) {
      expect(chunk.category).toBe('cli');
    }
    for (const chunk of interactiveChunks) {
      expect(chunk.category).toBe('interactive');
    }
    for (const chunk of desktopChunks) {
      expect(chunk.category).toBe('desktop');
    }
    for (const chunk of overviewChunks) {
      expect(chunk.category).toBe('overview');
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
