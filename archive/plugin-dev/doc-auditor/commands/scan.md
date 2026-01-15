---
name: scan
description: Scan documentation for issues across 15 categories and save prioritized results
argument-hint: "[docs-path]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Task
  - Bash
---

Scan documentation for issues and save structured results.

## Your Task

Run a comprehensive documentation scan detecting issues across 15 categories, then save results for interactive fixing.

## Setup

1. **Read the configuration** (if it exists):
   - Config location: `.claude/doc-auditor.local.md`
   - If missing, use aggressive defaults (all 15 categories enabled, LOW confidence threshold)

2. **Create output directory** if it doesn't exist:
   ```bash
   mkdir -p .claude/doc-auditor
   ```

3. **Determine scope**:
   - If argument provided: use `$ARGUMENTS` as the docs path
   - If no argument: use config `include_patterns` or default to `**/*.md`
   - Apply `exclude_patterns` (default: `node_modules/**`, `.git/**`, `vendor/**`)

4. **Read reference files** to understand issue categories:
   - `${CLAUDE_PLUGIN_ROOT}/references/issue-categories.md`
   - `${CLAUDE_PLUGIN_ROOT}/references/output-schemas.md`
   - `${CLAUDE_PLUGIN_ROOT}/references/document-templates.md`

5. **Determine entry points** for orphan detection:
   - Check config `entry_points`
   - If not configured: auto-detect README.md, docs/index.md, index.md
   - If none found: skip orphan detection with warning

## Spawning the Agent

Use the Task tool to spawn the `issue-detector` agent with this prompt:

```
You are the issue-detector agent for doc-auditor.

## Issue Categories

[INJECT: Read and include content from ${CLAUDE_PLUGIN_ROOT}/references/issue-categories.md]

## Output Schema

[INJECT: Read and include content from ${CLAUDE_PLUGIN_ROOT}/references/output-schemas.md]

## Document Templates

[INJECT: Read and include content from ${CLAUDE_PLUGIN_ROOT}/references/document-templates.md]

## Configuration

- Include patterns: [from config or defaults]
- Exclude patterns: [from config or defaults]
- Entry points: [from config or auto-detected]
- Enabled categories: [all 15 by default, or per config]
- Min severity: [LOW by default, or per config]
- Confidence threshold: [LOW by default, or per config]
- Staleness days: [180 by default, or per config]
- Code paths: [for code-doc-drift, from config]
- Template strictness: [strict by default, or per config]

## Your Task

1. Use Glob to find all documents matching patterns
2. Read each document
3. Detect issues across all enabled categories
4. Generate stable issue IDs (hash of file+category+subcategory+evidence)
5. Propose fixes where possible (verify old_string uniqueness!)
6. Write results atomically to .claude/doc-auditor/scan-results.json
7. Output summary to stdout

Start by discovering documents, then systematically analyze each one.
```

## Output

The agent will:
1. Write full results to `.claude/doc-auditor/scan-results.json`
2. Return a summary showing issue counts by severity

Display the summary to the user and inform them they can run `/doc-auditor:repair` to walk through issues interactively.
