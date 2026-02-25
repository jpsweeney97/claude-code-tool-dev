# Handoff Enhancement #4: Chain Visualization

```yaml
id: handoff-chain-viz
date: 2026-02-24
status: planning
priority: medium
blocked_by: []
blocks: []
related: [handoff-checkpoints, handoff-search]
plugin: packages/plugins/handoff/
```

## Problem

80% of handoffs (194/243) have `resumed_from` chains — multi-session arcs spanning planning through implementation through review. But chains are invisible. `resumed_from` records the link, nothing renders it.

Users can't answer "show me the arc of work that led to this PR" or "how many sessions did this feature take?" without manual file archaeology.

**Evidence:**
- 194/243 handoffs (80%) have `resumed_from` — heavy chaining is the dominant usage pattern
- Chains span 5-15 handoffs for complex work arcs (e.g., e-learning phase 1a: 7 handoffs from planning through PR merge)
- No command exists to trace or visualize chains
- `resumed_from` stores archive paths — must follow the link trail manually

**Cost:**
- Work arc narrative is fragmented across individual handoff files
- No way to audit how a decision evolved across sessions
- Impossible to see the full picture without manual reading

## Scope

**In scope:**
- Trace `resumed_from` links from a given handoff (or most recent)
- Render chain as timeline with dates, titles, and decision counts
- Handle broken chains (handoffs deleted by retention)
- Work across active and archived handoffs

**Out of scope:**
- Modifying chain structure
- Merging chains
- Cross-project chains
- Graphical visualization (text output only)

## Design Space

*To be filled during brainstorming. Key questions:*

1. **Invocation**: `/handoff:chain` (from most recent) vs `/handoff:chain <path>` (from specific)?
2. **Direction**: Trace backwards (from current to origin) or forwards (from origin to current)?
3. **Output format**: Timeline list? Table? Markdown tree?
4. **Detail level**: Just titles and dates? Or also key decisions per handoff?
5. **Broken chain handling**: Show gap marker? Stop at break?
6. **Checkpoint integration**: Show checkpoints differently from full handoffs in chain?
7. **Chain metadata**: Should handoffs record chain ID and position to make traversal cheaper?

## Files Affected

| File | Change |
|------|--------|
| `skills/chain-visualization/SKILL.md` | **New** — chain viz skill |
| `commands/chain.md` | **New** — command wrapper |
| `references/format-reference.md` | Add chain_id/chain_position to frontmatter (if adopted) |
| `skills/creating-handoffs/SKILL.md` | Record chain metadata in frontmatter (if adopted) |
| `.claude-plugin/plugin.json` | Version bump |

## Acceptance Criteria

- [ ] `/handoff:chain` traces `resumed_from` links from most recent handoff
- [ ] Renders timeline showing date, title, type for each link
- [ ] Handles broken chains (marks gap, continues if possible)
- [ ] Works with both active and archived handoffs
- [ ] Handles single handoffs with no chain (shows just the one)
- [ ] Skill context budget ≤100 lines
