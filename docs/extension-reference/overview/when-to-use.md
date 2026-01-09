---
id: when-to-use
topic: Choosing the Right Extension Type
category: overview
tags: [decision, selection, guidance]
requires: [extension-types]
related_to: [precedence]
official_docs: https://code.claude.com/docs/llms.txt
---

# Choosing the Right Extension Type

Decision guide for selecting the appropriate extension.

## Decision Tree

| Need | Extension |
|------|-----------|
| Simple prompt injection, no logic | Command |
| Complex workflow with verification | Skill |
| Autonomous background task | Agent |
| React to events automatically | Hook |
| Integrate external tools/APIs | MCP Server |
| Code intelligence (types, diagnostics) | LSP Server |
| Distribute to others | Plugin |

## When to Use Commands

- One-shot prompt templates
- Team standardization of prompts
- No conditional logic needed
- Quick setup, immediate use

## When to Use Skills

- Multi-step procedures
- "If X then Y otherwise Z" logic
- Quality gates and verification
- Reusable across projects

## When to Use Agents

- Long-running analysis
- Parallel work streams
- Tasks needing separate context
- Specialized autonomous workers

## When to Use Hooks

- Validate before tool execution
- Log or audit operations
- Transform inputs/outputs
- Block dangerous operations

## Key Points

- Commands → Skills: When you need conditional logic
- Skills → Plugins: When you need distribution
- If event-driven: Always hooks
- If external integration: Always MCP
