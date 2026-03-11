# Learning System Redesign

**Date:** 2026-03-11
**Status:** Draft
**Supersedes:** `docs/plans/2026-02-10-cross-model-learning-system.md` (original spec)

## Background

The original cross-model learning system spec (1,300+ lines, 5 phases, 4 amendments) designed an elaborate infrastructure: structured episodes, card lifecycles, evidence badges, MCP retrieval, injection slots, extraction agents, security gates, and feedback tracking.

Phase 0 validated a different, simpler need. After 3+ weeks of use, `learnings.md` accumulated 18 entries from diverse sources (debugging, architecture, security, reviews, workflow). Key findings:

| Signal | What it proved | What it didn't prove |
|--------|---------------|----------------------|
| 18 entries captured | Developers capture insights when friction is low | That structured schemas add value |
| Entries from all source types | Capture surface is broad — not Codex-specific | That cross-model is a special source |
| Rules file loads at session start | Auto-context works via existing mechanisms | That a separate retrieval system is needed |
| Zero structured episodes created | `/learn log` friction too high for regular use | That structured episodes have no value at scale |

The validated need: **capture insights from any session, stage them, graduate the best ones into CLAUDE.md.** CLAUDE.md is already the retrieval system — it loads every session. The learning system is tooling around a funnel, not a parallel knowledge store.

## Architecture

```
Capture                      Staging              Promotion
───────                      ───────              ─────────
/learn   (any session)  →
                             learnings.md    →   /promote  →  CLAUDE.md
/distill (handoffs)     →
```

Three skills, one staging area, one destination. `/learn` and `/distill` already exist. `/promote` is the new component.

### Component Inventory

| Component | Status | Work Required |
|---|---|---|
| `/learn` | Deployed | Minor update: encourage structured format |
| `/distill` | Deployed | No changes |
| `/promote` | New | Build from this spec |
| `docs/learnings/learnings.md` | Active (18 entries) | No migration; promote-meta comments added over time |
| `.claude/rules/learnings.md` | Active | No changes |

## `/promote` — Graduate Learnings to CLAUDE.md

### Overview

A single skill that reads `learnings.md`, identifies mature entries, proposes CLAUDE.md edits, and executes approved promotions.

| Invocation | Behavior |
|---|---|
| `/promote` | Surface mature candidates, user selects, draft CLAUDE.md edit |
| `/promote --all` | Show all unpromoted entries (bypasses maturity filter, still skips already-promoted) |

A promotion means: the insight becomes a permanent part of project instructions. The learning entry is marked as promoted (not deleted — it retains the narrative context that CLAUDE.md entries lack).

### Flow

1. Read `learnings.md`, assess each entry for maturity
2. Present mature candidates (or all entries with `--all`)
3. User selects which to promote (selecting none exits cleanly with no changes)
4. For each selected: identify where in CLAUDE.md it belongs, draft the edit
5. User approves/modifies each edit
6. Mark entry as promoted in `learnings.md`

### Maturity Signals

An entry is "mature" when it's likely to be a durable, generalizable project insight rather than a one-off observation. Maturity is a judgment call by Claude, informed by these signals:

| Signal | What it indicates | Example |
|---|---|---|
| **Age** | Survived without being contradicted or superseded | Entry from 3 weeks ago vs yesterday |
| **Breadth** | Applies across contexts, not specific to one task | "Plugin MCP tool naming convention" vs "fixed bug in line 42" |
| **Reuse evidence** | Referenced or echoed in other entries | Same pattern noted independently in 2+ entries |
| **Actionability** | Can be turned into a concrete instruction | "Always use fail-closed for security hooks" vs "security is important" |
| **Independence from narrative** | The insight stands alone without session context | "PreToolUse hooks are fail-open" vs "After debugging for 2 hours we found..." |

**Not maturity signals:** entry length, number of tags, position in file, whether it came from `/learn` vs `/distill`.

**Missing fields in structured entries:** If an entry lacks the Implication field (or uses freeform format), treat it as a weak actionability signal — lower maturity confidence, but not disqualifying. The entry can still be promoted if other signals are strong.

**Threshold:** Surface entries Claude is >70% confident are promotable, erring toward inclusion. The user makes the final call. The `--all` flag bypasses maturity filtering (but still skips already-promoted entries).

### Promotion Placement

When the user selects an entry to promote, Claude determines where in CLAUDE.md it belongs and what form it takes.

**Placement logic:**

1. Read the current CLAUDE.md structure (sections, subsections, tables)
2. Identify the most relevant existing section for the insight
3. If no section fits, propose a new subsection under the most relevant parent. If no parent section is a reasonable fit, surface the placement question to the user before drafting.

**Transformation:** The learning narrative gets distilled into CLAUDE.md's style — prescriptive, concise, pattern-conformant with surrounding content.

| Learning entry (narrative) | CLAUDE.md entry (instruction) |
|---|---|
| "PreToolUse hooks are mechanically fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds..." (5 sentences) | In Gotchas: "**Hook failure polarity**: PreToolUse hooks are fail-open. Unhandled exceptions allow the tool call. For critical enforcement, catch all errors and return a block decision." |
| "Plugin-provided MCP tools use `mcp__plugin_<plugin>_<server>__<tool>` naming, not `mcp__<server>__<tool>`..." (4 sentences) | In relevant section: "**MCP tool naming**: Plugin tools use `mcp__plugin_<plugin>_<server>__<tool>`. This must match across hook matchers, skill `allowed-tools`, and agent `tools` frontmatter." |

**Rules:**

- Match the format of the target section (table row, bullet, paragraph — whatever the neighbors use)
- Check for semantic overlap with existing CLAUDE.md content before proposing (never duplicate)
- Show the proposed edit in context (a few lines before/after) so the user can judge fit

### Post-Promotion Bookkeeping

After a promotion is approved and the CLAUDE.md edit is made, mark the learning entry so it doesn't resurface in future `/promote` runs.

Append a metadata comment to the entry in `learnings.md`, matching the pattern `/distill` already uses:

```markdown
### 2026-02-18 [security, hooks]

PreToolUse hooks are mechanically fail-open — unhandled exceptions...
<!-- promote-meta {"promoted_at": "2026-03-11", "target": "CLAUDE.md#Gotchas"} -->
```

**Properties:**

- `/promote` skips entries with `promote-meta` (already promoted)
- The learning entry stays in `learnings.md` as narrative context
- Reversible — delete the comment to re-surface the entry
- No staleness tracking in v1 (if promoted content is later removed from CLAUDE.md, the learning remains marked as promoted)

### Failure Modes

| Failure | Recovery |
|---|---|
| `learnings.md` not found | Report "No learnings file found at `docs/learnings/learnings.md`" and STOP |
| No unpromoted entries | Report "All entries already promoted" and STOP |
| No mature candidates (without `--all`) | Report "No mature candidates found. Run `/promote --all` to see all entries." and STOP |
| Malformed `promote-meta` comment | Treat entry as unpromoted (fail-open — better to re-surface than silently skip) |
| CLAUDE.md not found | Report "No CLAUDE.md found at `.claude/CLAUDE.md`" and STOP |
| Global CLAUDE.md not found | Skip overlap check against global file, proceed with project CLAUDE.md only |
| Semantic overlap detected with existing CLAUDE.md content | Show the overlap, ask user whether to skip, merge, or replace |

## `/learn` — Updated Entry Format

Currently `/learn` appends freeform paragraphs with `### YYYY-MM-DD [tags]` headings. A light structure aids both readability and `/promote` maturity assessment.

**Encouraged format:**

```markdown
### YYYY-MM-DD [tag1, tag2]

**Context:** One sentence — what were you doing when this came up.

**Insight:** The actual learning — what you discovered, decided, or confirmed.

**Implication:** What to do differently going forward.
```

**Why these three fields:**

- **Context** helps `/promote` judge breadth (task-specific or general?)
- **Insight** is the core content that gets transformed into a CLAUDE.md instruction
- **Implication** signals actionability (no implication → may not be promotable)

**Not required — advisory.** `/learn` encourages this format but accepts freeform input. Existing entries stay as-is; no migration. `/promote` works with both structured and unstructured entries.

## What This Design Deliberately Omits

The original spec included significant infrastructure that this redesign does not carry forward:

| Original spec component | Why omitted |
|---|---|
| Structured episodes + validator | Phase 0 showed freeform capture with light structure is sufficient |
| Cards + card lifecycles (Draft/Active/Deprecated) | CLAUDE.md is the destination, not a card store |
| Evidence badges (Reasoned/Observed/Tested) | Maturity signals replace this with less ceremony |
| MCP retrieval server | CLAUDE.md is already loaded every session |
| Injection slots + token budgets | No injection system needed |
| Extraction agents (2 LLM call budget) | `/learn` is manual capture; `/distill` handles handoff extraction |
| Security gate linter | Promotion is human-approved; CLAUDE.md edits are reviewable in git |
| Feedback tracking (used/contradicted/irrelevant) | Not needed when the funnel is capture → curate → promote |
| Dashboard (`/review-learnings`) | `/promote --all` covers the "see everything" use case |
| Bootstrap cards | Not applicable to a funnel model |

Any of these could be added later if the simpler system reveals a genuine need. The original spec remains as prior art at `docs/plans/2026-02-10-cross-model-learning-system.md`.

## Implementation Notes

- Build `/promote` using `/skill-creator` for proper SKILL.md structure and frontmatter
- `/promote` targets project CLAUDE.md (`.claude/CLAUDE.md`) only. Global CLAUDE.md (`~/.claude/CLAUDE.md`) is out of scope for v1 — it's read for overlap checking but never written to
- The skill needs `Read` and `Edit` in `allowed-tools` (no `Bash` needed — all operations are file reads and edits)
- Light structure in `/learn` is a SKILL.md text change, not a code change

## Scope of Work

1. Build `/promote` skill (new)
2. Update `/learn` skill to encourage context/insight/implication format (minor edit)
3. Remove stale `/learn promote` rejection entry from `/learn` routing table
