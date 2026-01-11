---
id: memory-managed
topic: Managed Memory Deployment
category: memory
tags: [memory, enterprise, managed, deployment]
requires: [memory-overview]
related_to: [security-managed]
official_docs: https://code.claude.com/en/memory
---

# Managed Memory Deployment

Organizations can deploy centrally managed CLAUDE.md files that apply to all users.

## Enterprise Policy Locations

| Platform | Path |
|----------|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

## Deployment Process

1. Create the managed memory file at the enterprise policy location
2. Deploy via configuration management (MDM, Group Policy, Ansible, etc.)
3. File applies to all users on the machine

## Use Cases

| Use Case | Example Content |
|----------|-----------------|
| Coding standards | Language-specific conventions |
| Security policies | Credential handling, approved libraries |
| Compliance requirements | Regulatory documentation, audit trails |
| Tool configurations | Build commands, deployment targets |

## Precedence

Enterprise policy has highest precedence, loading first and overriding all other memory sources.

| Priority | Source |
|----------|--------|
| 1 (highest) | Enterprise policy |
| 2 | Project memory |
| 3 | User memory |
| 4 (lowest) | Project local |

## Key Points

- Deploy to platform-specific enterprise location
- Use configuration management for distribution
- Highest precedence in memory hierarchy
- Cannot be overridden by users or projects
