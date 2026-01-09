---
id: agents-examples
topic: Agent Examples
category: agents
tags: [examples, templates, patterns]
requires: [agents-overview, agents-frontmatter, agents-permissions]
official_docs: https://code.claude.com/en/sub-agents
---

# Agent Examples

Complete working agent examples.

## Security Analyzer Agent

`.claude/agents/security-analyzer.md`:

```yaml
---
description: Analyze code for security vulnerabilities
prompt: |
  You are a security-focused code reviewer. Your job is to:

  1. Identify potential security vulnerabilities
  2. Check for OWASP Top 10 issues
  3. Review authentication and authorization logic
  4. Check for injection vulnerabilities
  5. Verify input validation

  Be thorough but avoid false positives. Cite specific line numbers.

tools:
  - Read
  - Glob
  - Grep

model: opus

permissionMode: plan

hooks:
  PostToolUse:
    - matcher: Read
      hooks:
        - type: command
          command: echo "Analyzed: $TOOL_INPUT" >> /tmp/security-audit.log
---

Focus on:
- SQL injection in database queries
- XSS in template rendering
- CSRF in form handling
- Insecure deserialization
- Sensitive data exposure
```

## CLI-Based Agent Definition

Define agents inline via command line:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior engineer...",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  },
  "test-writer": {
    "description": "Test generation specialist",
    "prompt": "You write comprehensive tests...",
    "tools": ["Read", "Write", "Bash"],
    "model": "haiku"
  }
}'
```

## Key Points

- Use `permissionMode: plan` for analysis agents
- Add logging hooks to track agent activity
- CLI agents are useful for quick experiments
- Opus model for high-stakes analysis
