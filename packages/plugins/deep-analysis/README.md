# Deep Analysis Plugin

Structured analysis for complex decisions with semantic search over past analyses.

## Overview

This plugin provides a systematic approach to analyzing complex problems:

- **6 Analytical Frameworks**: First Principles, Systems Thinking, Inversion, Second-Order Thinking, Trade-off Analysis, Pre-mortem
- **5-Stage Process**: Prior Art → Clarification → Investigation → Synthesis → Document
- **Institutional Memory**: Semantic search over past analyses via MCP server
- **Structured Output**: Markdown documents optimized for future retrieval

## When to Use

- Architectural decisions with multiple valid approaches
- Strategic trade-offs ("should we X or Y?")
- Technology or approach evaluation
- Any decision requiring systematic option evaluation

## When NOT to Use

- Debugging → use `systematic-debugging`
- Creative ideation → use `brainstorming`
- Simple questions with obvious answers

## Installation

### From Local Path

```bash
# Plugin is already at ~/.claude/plugins/deep-analysis/

# Install MCP server dependencies
cd ~/.claude/plugins/deep-analysis/mcp
uv sync
```

### Verify Installation

```bash
# Start Claude Code and check plugins
claude
/plugins
```

You should see `deep-analysis` in the list.

## Usage

### Command

```
/deep-analysis:analyze should we migrate to microservices?
```

### Skill Triggering

The skill activates automatically when you ask questions like:

- "Help me decide between X and Y"
- "What approach should we take for authentication?"
- "Analyze the trade-offs of using Kubernetes"
- "Evaluate our options for the database migration"

### The Process

1. **Stage 0: Prior Art Search** — Searches for relevant past analyses
2. **Stage 1: Clarification** — Understands the problem through questions
3. **Stage 2: Investigation** — Applies all 6 analytical frameworks
4. **Stage 3: Synthesis** — Deep-dives on top 2-3 options
5. **Stage 4: Document** — Saves structured analysis (optional)

### Save Locations

| Context | Path |
|---------|------|
| In a project | `./docs/analysis/YYYY-MM-DD-slug.md` |
| Global | `~/.claude/analyses/YYYY-MM-DD-slug.md` |

## MCP Server

The plugin includes an MCP server for semantic search over past analyses.

### Tools

| Tool | Purpose |
|------|---------|
| `search_analyses` | Semantic search over indexed analyses |
| `index_analysis` | Add/update analysis in index |
| `remove_analysis` | Remove from index |
| `rebuild_index` | Rebuild entire index |
| `list_analyses` | List with optional filters |

### Graceful Degradation

If the MCP server isn't running, the skill:
- Falls back to grep-based search
- Notes "Semantic search unavailable, using basic search"
- Completes the full analysis process

### Index Location

`~/.claude/deep-analysis/index/`

### Rebuild Index

If you have existing analyses, rebuild the index:

```
Ask Claude: "Rebuild the deep analysis index"
```

Or use the MCP tool directly.

## Components

```
deep-analysis/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── .mcp.json                # MCP server configuration
├── commands/
│   └── analyze.md           # /deep-analysis:analyze command
├── mcp/
│   ├── pyproject.toml       # Python dependencies
│   ├── server.py            # MCP server implementation
│   └── __main__.py          # Module entry point
└── skills/
    └── deep-analysis/
        ├── SKILL.md         # Core analysis process
        └── references/
            ├── frameworks.md    # 6 analytical frameworks
            └── document-spec.md # Output format specification
```

## Requirements

- Python 3.12+
- uv (for dependency management)
- ~150MB disk space (for txtai embeddings model)

## The 6 Frameworks

1. **First Principles** — Strip away assumptions. What fundamental truths apply?
2. **Systems Thinking** — Map interconnections. What feedback loops exist?
3. **Inversion** — Flip the question. What would guarantee failure?
4. **Second-Order Thinking** — Follow the chain. If we do X, then what?
5. **Trade-off Analysis** — Identify tensions. What values compete?
6. **Pre-mortem** — Imagine failure. It's one year later and this failed. Why?

## Document Format

Analyses are saved as structured markdown:

```markdown
---
type: deep-analysis
date: 2025-01-15
problem: microservices-migration
decision: strangler-fig-pattern
status: accepted
keywords: [microservices, migration, architecture]
---

# Problem
> Should we migrate our monolith to microservices?

# Context
- Team size, constraints, current state...

# Analysis
[Insights from each framework]

# Options Considered
[Each option with pros, cons, verdict]

# Decision
[Chosen option with rationale]

# Risks Accepted
[Known risks and mitigations]
```

## Troubleshooting

### MCP Server Not Starting

```bash
# Check dependencies are installed
cd ~/.claude/plugins/deep-analysis/mcp
uv sync

# Test the server directly
uv run python -m server
```

### Skill Not Triggering

Ensure your question matches the trigger patterns:
- Decision-oriented ("should we", "which approach")
- Multiple options implied ("X or Y", "trade-offs")
- Complexity warranted (not simple yes/no questions)

### Index Issues

```bash
# Remove and rebuild index
rm -rf ~/.claude/deep-analysis/index
# Then ask Claude to rebuild
```

## License

MIT
