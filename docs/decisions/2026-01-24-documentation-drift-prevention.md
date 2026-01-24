# Decision: Documentation Drift Prevention Approach

**Date:** 2026-01-24
**Status:** Decided
**Stakes:** Rigorous

## Decision Statement

How should this repo prevent its extension documentation from drifting from (a) official Anthropic docs and (b) each other?

## Context

Multiple files cover the same extension topics (skills, hooks, subagents, etc.) but serve different purposes:

| File Type | Example | Loaded When |
|-----------|---------|-------------|
| Rules | `.claude/rules/extensions/skills.md` | Always (via paths frontmatter) |
| Writing guide | `brainstorming-skills/references/skill-writing-guide.md` | On-demand by skill |
| Template | `brainstorming-skills/assets/skill-template.md` | On-demand by skill |
| Pattern guide | `ideating-extensions/references/extension-patterns.md` | On-demand by skill |

The files have intentional overlap because some content (persuasion principles, quality dimensions, etc.) genuinely belongs in multiple contexts.

An initial approach — a manifest-based audit skill — was rejected because it tracked drift rather than preventing it.

## Decision

**Hybrid approach: Delineate where possible, managed summaries where necessary.**

### For Internal Drift

1. **Clear ownership:** Each topic has ONE authoritative file. Other files may summarize but must explicitly defer.

2. **Delineation rules:**
   - Rules files (`rules/extensions/*.md`): What Claude must do, brief summaries of why, explicit links to guides for depth
   - Writing guides (`references/*-writing-guide.md`): Full explanations, rationale, patterns — authoritative for "how to write well"
   - Templates (`assets/*-template.md`): Structure only, no guidance (remove redundant sections like "Writing the Description")
   - Pattern guides (`references/extension-patterns.md`): Decision guidance for which extension type — authoritative for that purpose

3. **Summary convention:** When a rules file summarizes content from a guide, mark it:
   ```markdown
   ## Persuasion Principles

   Use deliberately for discipline-enforcing skills. See [skill-writing-guide.md](path) for full details.

   [Brief 5-10 line summary]
   ```

### For External Drift

Lightweight habit, not tooling:
- When editing extension docs, query extension-docs MCP for relevant official content
- Verify local content matches
- Update if needed

The reminder hook (`drift-reminder.py`) can stay as a gentle nudge but is optional.

## Alternatives Considered

| Option | Rejected Because |
|--------|------------------|
| **Consolidation** (merge files) | Breaks loading model — rules file is always-loaded, guide should be on-demand |
| **Build step** (partials + assembly) | Adds tooling complexity to plain markdown files |
| **Audit skill** (manifest-based tracking) | Tracks drift rather than preventing it; high maintenance |
| **Null** (accept drift) | Problem is real enough to address structurally |

## Trade-offs Accepted

- Some duplication remains (summaries in rules files)
- Requires discipline to keep summaries brief and properly marked
- Doesn't fully automate external drift detection

## Implementation

1. Audit current files to identify all overlapping content
2. Designate authoritative file for each topic
3. Update non-authoritative files to summary + link format
4. Remove redundant guidance sections from templates
5. (Optional) Keep or remove drift-reminder hook based on preference

## Confidence

**Medium-high**

The hybrid approach addresses the core tension (some overlap is intentional) while reducing drift risk. Main uncertainty: whether the "summary + link" discipline will hold over time.

## What Would Change This

- If external drift becomes a frequent problem, add more structured verification
- If summary sections keep growing, consider build-step approach
- If loading model changes (e.g., Claude Code supports conditional loading), reconsider consolidation
