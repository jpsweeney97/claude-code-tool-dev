# Design: Handoff Checkpoint Tier

```yaml
date: 2026-02-24
status: approved
ticket: docs/tickets/handoff-checkpoints.md
plugin: packages/plugins/handoff/
```

## Problem

The handoff plugin treats every save-state operation as a full handoff: load synthesis guide (~520 lines), answer all prompts, produce 300+ line document. At 7.4 handoffs/day (peak 25), many are context-pressure saves — not comprehensive knowledge captures. 30% of handoffs are under 100 lines, indicating the full flow was triggered when a lighter-weight operation was needed.

## Solution

Add a `/checkpoint` command backed by a separate, self-contained skill that produces lighter-weight state captures optimized for context-pressure session cycling.

## Design Decisions

### Trigger: Context pressure
The primary checkpoint trigger is running low on context window. This means speed and low context cost matter above all. Checkpoints prioritize **state** (what's in flight, what's working/broken) and **knowledge** (files read, patterns found) over deep decision analysis.

### Architecture: Separate self-contained skill (Approach A)
New `skills/checkpointing/SKILL.md` (~200-250 lines) with abbreviated synthesis prompts inline. Does not load synthesis-guide.md or format-reference.md. Follows the existing plugin pattern where creating-handoffs and resuming-handoffs are already separate skills.

**Rejected alternatives:**
- **Mode within creating-handoffs:** Conditional logic in instruction documents is fragile. Claude Code skills have no native parameter mechanism. Would make the already-large skill more complex.
- **Shared core module:** Over-engineered for what's fundamentally "write a shorter handoff with fewer prompts." Would require refactoring existing skills.

### Invocation: `/checkpoint`
Dedicated top-level command — fastest to type, clearly distinct from `/handoff`.

```
/checkpoint           # save state quickly
/checkpoint <title>   # save with custom title
/handoff              # full handoff (unchanged)
```

### Resume: Same treatment
`/resume` loads the most recent file regardless of type. A checkpoint and a handoff are both "the last thing saved." Display shows the type for clarity.

### Chain: Same chain, labeled
Checkpoints participate in the same `resumed_from` chain as full handoffs. The `type` field in frontmatter distinguishes them. Future chain visualization (#4) can filter or annotate checkpoint vs handoff links.

## Content Model

### Sections

| Section | Required? | Depth Target | Purpose |
|---------|-----------|-------------|---------|
| **Goal** | Yes | 3-5 lines | What we're working toward (brief) |
| **In Progress** | Yes | 20-40 lines | Active work state: approach, working/broken, next action |
| **Changes** | If applicable | 5-10 lines/file | Files modified, purpose and key details |
| **Codebase Knowledge** | Yes | 40-80 lines | Files read, patterns, architecture, key locations |
| **Next Steps** | Yes | 10-20 lines | What to do next, dependencies, what to read first |
| **Decisions** | If applicable | 5-10 lines/decision | Lightweight: choice + driver + alternatives |
| **Gotchas** | If applicable | As needed | Surprising findings |

### Excluded vs full handoffs

No session narrative, conversation highlights, user preferences, rejected approaches, mental model, or full evidence requirements. Those belong in the full `/handoff` at natural stopping points.

### Abbreviated synthesis

Four inline prompts (not a separate file):

1. What's in flight right now? → In Progress
2. What did I learn about the codebase? → Codebase Knowledge
3. What should future-me do first? → Next Steps
4. Were any decisions made? → Decisions (if applicable)

### Output target

150-300 lines body content. Frontmatter adds ~15 lines.

## Frontmatter Schema

```yaml
---
date: YYYY-MM-DD
time: "HH:MM"
created_at: "YYYY-MM-DDTHH:MM:SSZ"
session_id: <UUID>
resumed_from: <path>                # optional
project: <project-name>
branch: <branch-name>              # optional
commit: <short-hash>               # optional
title: "Checkpoint: <descriptive-title>"
type: checkpoint                    # NEW — distinguishes from full handoffs
files:
  - <key files touched>
---
```

**Backwards compatibility:** Existing handoffs without `type` field are treated as `handoff`. The creating-handoffs skill will be updated to explicitly set `type: handoff`.

**Title convention:** Checkpoint titles use `"Checkpoint: "` prefix for scannability.

## File Plan

### New files

| File | Purpose | Est. Lines |
|------|---------|------------|
| `skills/checkpointing/SKILL.md` | Checkpoint skill — self-contained | ~200-250 |
| `commands/checkpoint.md` | Thin command wrapper | ~7 |

### Modified files

| File | Change |
|------|--------|
| `references/format-reference.md` | Add "Checkpoint Format" canonical spec (~50 lines) |
| `skills/resuming-handoffs/SKILL.md` | Show `type` column in `/list-handoffs`; display type on resume |
| `skills/creating-handoffs/SKILL.md` | Add `type: handoff` to frontmatter template |
| `.claude-plugin/plugin.json` | Version bump to 1.1.0 |

### Unchanged

| File | Why |
|------|-----|
| `scripts/cleanup.py` | Already handles all `.md` files in the directory |
| `skills/creating-handoffs/synthesis-guide.md` | Not loaded by checkpoints, not modified |
| `hooks/hooks.json` | No new hooks for checkpoints (quality hook is Enhancement #3) |

## Context Budget

| Operation | Context Loaded | Change |
|-----------|---------------|--------|
| `/handoff` (full) | ~570 lines | Unchanged (+`type: handoff` in template) |
| `/checkpoint` | ~200-250 lines | **New** — 56-65% less than full handoff |
| `/resume` | ~220 lines | Unchanged (minor display addition) |

## Resume & List Integration

**`/resume` behavior:** Unchanged logic. Loads most recent `.md` file regardless of type. Displays type: "Resuming from **checkpoint**: ..." or "Resuming from **handoff**: ...". Archive and state file behavior identical.

**`/list-handoffs` output:**

```
| Date       | Title                                          | Type       | Branch              |
|------------|------------------------------------------------|------------|---------------------|
| 2026-02-24 | Checkpoint: implementing Redis sync layer      | checkpoint | feature/rate-limit  |
| 2026-02-24 | Rate limiting — architecture and initial impl  | handoff    | feature/rate-limit  |
```

**Chain semantics:** Checkpoints are links in the chain. Chain visualization (Enhancement #4) will label them distinctly (e.g., `○` checkpoint vs `●` handoff).

## Quality Calibration

| Type | Target Lines | Minimum Sections |
|------|-------------|-----------------|
| Checkpoint | 150-300 | 4 (Goal, In Progress, Codebase Knowledge, Next Steps) |
| Full handoff | 300-700+ | 6-8 |

Enhancement #3 (quality hook) will use the `type` field to select appropriate thresholds.

## Verification

After implementation:

- [ ] `/checkpoint` produces a file at `~/.claude/handoffs/<project>/YYYY-MM-DD_HH-MM_checkpoint-*.md`
- [ ] Frontmatter includes `type: checkpoint` and all required fields
- [ ] Skill loads ≤250 lines of context (no synthesis guide, no format reference)
- [ ] Output is 150-300 lines
- [ ] `/resume` loads checkpoints identically to full handoffs
- [ ] `/list-handoffs` shows type column
- [ ] Existing `/handoff` flow unchanged (now includes `type: handoff`)
- [ ] `/resume` on a checkpoint archives and creates state file correctly
- [ ] Chain: checkpoint → full handoff preserves `resumed_from`
