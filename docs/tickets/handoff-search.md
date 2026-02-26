# Handoff Enhancement #1: Search/Query

```yaml
id: handoff-search
date: 2026-02-24
status: planning
priority: high
blocked_by: []
blocks: []
related: [handoff-distill, handoff-chain-viz]
plugin: packages/plugins/handoff/
```

## Problem

244 handoffs contain hundreds of decisions, architecture maps, learnings, and user preferences. There is no way to query them. Finding "what did we decide about X?" requires manually reading handoff files.

Knowledge captured in handoffs is only useful in the immediately next session (via `/resume`), then effectively dead. The handoff system is write-only.

**Evidence:**
- 244 handoffs across 43 days, all for one project
- Handoffs contain structured sections (Decisions, Learnings, Codebase Knowledge) with rich searchable content
- No search command exists; `/list-handoffs` shows only titles and dates
- Archived handoffs (80% of total) are only accessible by knowing the exact path

**Cost:**
- Re-discovery of decisions already made in prior sessions
- Re-exploration of codebase areas already mapped in prior handoffs
- Lost institutional knowledge when handoffs age past retention

## Scope

**In scope:**
- Search across active and archived handoffs for the current project
- Return matching sections with filename, title, and surrounding context
- Simple text/regex search (not semantic)

**Out of scope:**
- Cross-project search (only current project)
- Semantic/embedding-based search
- Search indexing or pre-processing
- Modifying handoff content from search results

## Design Space

*To be filled during brainstorming. Key questions:*

1. **Invocation**: `/handoff:search <query>` (skill) vs command that runs a script?
2. **Implementation**: Grep tool from within skill vs Python script vs hybrid?
3. **Output format**: Full matching sections vs snippets with line numbers?
4. **Scope control**: Search active only, archive only, or both? Flag to control?
5. **Section-aware**: Should search understand handoff sections (return full "## Decisions" block when a decision matches)?
6. **Result limit**: How many results before truncation?
7. **Context budget**: How much skill context to load for a search operation?

## Files Affected

| File | Change |
|------|--------|
| `skills/searching-handoffs/SKILL.md` | **New** — search skill |
| `commands/search-handoffs.md` | **New** — command wrapper |
| `.claude-plugin/plugin.json` | Version bump |

## Acceptance Criteria

- [ ] `/handoff:search <query>` returns matching handoff content
- [ ] Searches both active and archived handoffs
- [ ] Results include filename, title, and matching section context
- [ ] Handles no-results gracefully
- [ ] Skill context budget ≤100 lines
