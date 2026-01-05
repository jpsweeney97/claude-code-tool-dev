---
name: report
description: Generate a coherence report showing what documentation describes as a unified design
argument-hint: "[docs-path]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
---

Generate a documentation coherence report.

## Your Task

Create a "forest view" of documentation coherence — a synthesis of what the docs actually describe when read holistically.

## Setup

1. **Read the configuration** (if it exists):
   - Config location: `.claude/doc-auditor.local.md`
   - If missing, use defaults

2. **Determine scope**:
   - If argument provided: use `$ARGUMENTS` as the docs path
   - If no argument: use config `include_patterns` or default to `**/*.md`
   - Apply `exclude_patterns` (default: `node_modules/**`, `.git/**`, `vendor/**`)

3. **Read reference files** to understand analysis framework:
   - `${CLAUDE_PLUGIN_ROOT}/references/analysis-framework.md`

## Spawning the Agent

Use the Task tool to spawn the `coherence-analyzer` agent with this prompt:

```
You are the coherence-analyzer agent for doc-auditor.

## Analysis Framework

[INJECT: Read and include content from ${CLAUDE_PLUGIN_ROOT}/references/analysis-framework.md]

## Configuration

- Include patterns: [from config or defaults]
- Exclude patterns: [from config or defaults]
- Docs path: [from $ARGUMENTS or defaults]

## Your Task

Analyze the documentation set and produce a coherence report to stdout following the format specified in the analysis framework.

Start by using Glob to find all matching documents, then read and analyze each one.
```

## Output

The agent will output a markdown report showing:
- Executive summary synthesizing what the docs describe
- Document inventory
- Terminology map
- Key assertions and contradictions
- Gaps identified
- Recommendations

Display the agent's report to the user.
