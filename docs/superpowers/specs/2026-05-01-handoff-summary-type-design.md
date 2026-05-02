# Handoff Summary Type — Design

## Problem

The handoff plugin has two types: full handoffs (400+ lines, 13 sections) and checkpoints (20-80 lines, 5 sections). The gap between them is too wide.

Full handoffs capture sessions exhaustively — deep decision analysis, conversation highlights, user preferences, codebase knowledge dumps. This depth is valuable for complex sessions with pivots and design work but overkill for routine sessions with moderate decisions and exploration.

Checkpoints capture the minimum needed to resume: current task, in-progress state, next action. They lose decisions, codebase knowledge, session narrative, and any sense of where the project stands.

The bigger problem: both types are **session-scoped**. Each handoff is an island — it captures what happened in *this* session but doesn't synthesize the project arc across sessions. Over a multi-session project, context from earlier sessions decays unless it happens to be re-mentioned. This causes **drift**: decisions from session 3 get forgotten, gotchas from session 5 disappear, the architectural picture that built up over sessions 1-7 evaporates.

## Solution

A third handoff type called **summary** that captures session context at moderate depth AND synthesizes the project arc.

**Identity:** A summary captures what happened this session and where the project stands. It's the handoff type you reach for when a checkpoint would lose too much and a full handoff would capture too much.

## Comparison

| Aspect | Checkpoint | **Summary** | Handoff |
|--------|-----------|-------------|---------|
| Command | `/quicksave` | **`/summary`** | `/save` |
| Body lines | 20-80 | **120-250** | 400+ |
| Required sections | 5 | **8** | 13 |
| Synthesis prompts | 4 (inline) | **7 (inline)** | 11 (separate guide) |
| Decision depth | Choice + driver | **4 elements** | 8 elements |
| Codebase knowledge | Key finding only | **20-40 lines** | 60-100 lines |
| Session narrative | None | **20-40 lines** | 60-100 lines |
| Project Arc | None | **20-50 lines** | None |
| Arc context gathering | None | **Archive + git + conversation** | None |

## Type and Naming

- **Type:** `summary` (added to `VALID_TYPES` alongside `handoff` and `checkpoint`)
- **Command:** `/summary` or `/summary <title>`
- **Skill name:** `summary` (new skill at `skills/summary/SKILL.md`)
- **Filename convention:** `YYYY-MM-DD_HH-MM_summary-<slug>.md`
- **Title convention:** `"Summary: <descriptive-title>"`
- **Frontmatter `type`:** `summary`

## Sections

Eight required sections. Depth targets are minimums — exceed when warranted.

| Section | Depth Target | Purpose |
|---------|-------------|---------|
| **Goal** | 5-10 lines | What we're working on, why, and how it connects to the project |
| **Session Narrative** | 20-40 lines | What happened, pivots, key understanding shifts — story, not list |
| **Decisions** | 10-15 lines per decision | Choice, driver, alternatives considered, trade-offs accepted (4 elements) |
| **Changes** | 5-10 lines per file | Files modified/created with purpose and key details |
| **Codebase Knowledge** | 20-40 lines | Patterns, architecture, key locations with file:line references |
| **Learnings** | 5-10 lines per item | Insights gained — gotchas fold in here |
| **Next Steps** | 5-10 lines per item | What to do next — dependencies, blockers, open questions fold in here |
| **Project Arc** | 20-50 lines | Where we are in the bigger effort (see dedicated section below) |

### Sections Removed from Full Handoff (and why)

| Removed Section | Disposition |
|----------------|-------------|
| User Preferences | Auto-memory system captures these durably across sessions |
| Conversation Highlights | Decision-driving quotes fold into Decisions; key exchanges fold into Session Narrative |
| Gotchas | Fold into Learnings or Codebase Knowledge |
| Dependencies | Fold into Next Steps |
| Open Questions | Fold into Next Steps |
| Risks | Fold into Next Steps or Project Arc (drift risks) |
| References | Fold into Codebase Knowledge |
| Context | Mental model folds into Project Arc; environment state folds into Codebase Knowledge |
| In Progress | Folds into Next Steps (current state) and Changes (what's done) |

### Hollow-Summary Guardrail

At least 1 of {Decisions, Changes, Learnings} must have substantive content. Same guardrail as full handoffs.

## Project Arc — The Key Differentiator

The Project Arc section synthesizes where the project stands across sessions. This is the section that prevents drift and keeps the long-term thread alive.

### What It Captures

| Element | Description |
|---------|-------------|
| **Accomplishments** | What's been completed across the project arc — not just this session |
| **Current position** | Where we are in the overall effort — what phase, what milestone |
| **What's ahead** | Remaining work, upcoming milestones, known future decisions |
| **Load-bearing decisions** | Key decisions from prior sessions that are still governing the work — the ones that would cause drift if forgotten |
| **Accumulated understanding** | Mental model, architecture insights, constraints that built up over multiple sessions |
| **Drift risks** | Things that are easy to forget or misremember — subtle constraints, rejected approaches from prior sessions, scope boundaries |
| **Downstream impacts** | Things done this session that necessitate changes elsewhere — cascading updates, things now out of sync |

### How Claude Gathers Arc Context

1. List files in `docs/handoffs/archive/` — scan titles and dates to identify relevant prior handoffs
2. Read any archived handoffs/checkpoints/summaries that appear relevant to the current project arc (Claude uses judgment — not all archived files may be relevant, especially in repos with multiple workstreams)
3. Check recent git history — commits, branch history, commit messages
4. Combine with: conversation context, any loaded handoff from `/load`, and general awareness of the project
5. Synthesize into the Project Arc section

**Key instruction:** "You are not summarizing prior handoffs. You are answering: where does this project stand right now, and what would a new Claude need to know to avoid drift?" Prior handoffs and git history are *input* to this synthesis, not the output.

**When no prior handoffs exist:** Claude fills from conversation context and git history alone. Even a first-session summary benefits from capturing "this is the beginning of X, and the plan is Y."

### Depth Target

20-50 lines. Should feel like a briefing — dense and actionable, not a history lesson.

## Synthesis Prompts

Seven prompts, kept inline in the skill (no separate guide file). Claude answers these internally before writing sections.

| # | Prompt | Maps to |
|---|--------|---------|
| 1 | What did I set out to do, and why does it matter? | Goal |
| 2 | What happened this session — what was the arc from start to finish? | Session Narrative |
| 3 | What choices were made, and what were the alternatives? | Decisions |
| 4 | What did I build or change? | Changes |
| 5 | What did I learn about the codebase that future-Claude needs? | Codebase Knowledge |
| 6 | What insights or gotchas should survive this session? | Learnings |
| 7 | Where does the project stand now — what's done, what's next, what's at risk of being forgotten? Did anything we did this session necessitate changes elsewhere — downstream impacts, cascading updates, things that are now out of sync? | Project Arc + Next Steps |

Prompt 7 is the critical differentiator — it forces Claude to step back from the session and think about the arc, drift risks, and cascading impacts.

**No separate synthesis guide file.** The full handoff's `synthesis-guide.md` is 520 lines of deep guidance. The summary's 7 prompts live directly in the SKILL.md with brief inline guidance, keeping the skill self-contained.

## Decision Depth

Summaries use 4-element decisions (vs checkpoint's 2 and handoff's 8):

| Element | Checkpoint | Summary | Handoff |
|---------|-----------|---------|---------|
| Choice | Yes | Yes | Yes |
| Driver | Yes | Yes | Yes |
| Alternatives considered | — | Yes | Yes |
| Trade-offs accepted | — | Yes | Yes |
| Rejection reasons | — | — | Yes |
| Confidence level | — | — | Yes |
| Reversibility | — | — | Yes |
| Change triggers | — | — | Yes |

The 4-element set captures the "what and why" of each decision without the full analytical depth of a handoff decision entry.

## When to Use

**Use `/summary`:**
- End of a meaningful session where `/save` feels like overkill but `/quicksave` would lose too much
- Session had decisions, exploration, or codebase learning worth preserving at moderate depth
- Working on a multi-session project where arc awareness matters
- User says "summary" or "summarize"

**Do NOT use:**
- Context pressure / need to cycle fast — use `/quicksave`
- Complex session with deep decisions, pivots, or design work — use `/save`
- Session was trivial — skip entirely

**Heuristic:** If the session had 3+ significant decisions with trade-offs worth recording in depth, lean toward `/save`. If the session was mostly execution with 0-2 decisions, `/summary` is the right fit.

## Procedure

1. **Check prerequisites** — project root, write permissions, non-trivial session (same as save/quicksave)
2. **Note session ID** from `${CLAUDE_SESSION_ID}`
3. **Gather arc context:**
   - List `docs/handoffs/archive/` — scan titles and dates
   - Read relevant archived handoffs/checkpoints/summaries (Claude's judgment)
   - Check recent git history (`git log --oneline` or similar)
   - Combine with conversation context and any loaded handoff
4. **Answer 7 synthesis prompts** (internal — do not output to chat)
5. **Check state file** per chain protocol in `handoff-contract.md`
6. **Write file** to `docs/handoffs/YYYY-MM-DD_HH-MM_summary-<slug>.md` with `type: summary`
   - Summaries are local-only working memory — not committed
7. **Cleanup state file** per chain protocol
8. **Verify and confirm:** "Summary saved: `<path>`"
   - Do NOT reproduce content in chat. The file is the deliverable.

## Quality Enforcement

The `quality_check.py` PostToolUse hook validates summaries:

| Check | Rule |
|-------|------|
| `VALID_TYPES` | Add `"summary"` |
| Required frontmatter | Same 7 fields as handoff/checkpoint |
| Title prefix | Must start with `"Summary: "` |
| Required sections | 8: Goal, Session Narrative, Decisions, Changes, Codebase Knowledge, Learnings, Next Steps, Project Arc |
| Min body lines | 120 (error) |
| Max body lines | 250 (warning — "This summary is getting long. Consider `/save` for a full capture.") |
| Hollow-summary guardrail | At least 1 of {Decisions, Changes, Learnings} must have substantive content |

## Integration

### Components That Need Changes

| Component | Change | Severity |
|-----------|--------|----------|
| `quality_check.py` | Add summary validation rules (type, sections, line counts, title prefix) | Required |
| `handoff-contract.md` | Add `summary` to type field, title convention, filename convention | Required |
| `format-reference.md` | Add summary section table and quality calibration row | Required |
| `/load` skill | Add `"Resuming from **summary**: ..."` display string | Required |
| `/defer` skill | Accept `summary` as valid `source_type` | Required |
| New `summary` skill | Create `skills/summary/SKILL.md` | Required |
| `plugin.json` | Version bump | Required |

### Components That Work Without Changes

| Component | Why it works |
|-----------|-------------|
| `/search` (`search.py`) | Type-agnostic — reads `type` for display, doesn't filter on it |
| `handoff_parsing.py` | Type-agnostic — parses any markdown with frontmatter + sections |
| `cleanup.py` | Only prunes state files by age, type-unaware |
| Chain protocol | Summaries participate identically to handoffs and checkpoints |

### Design Decisions for Edge Cases

**`/triage` and summaries:** Triage scans for `Open Questions` and `Risks` sections. Summaries fold both into `Next Steps`. Triage won't find orphaned items in summaries because the section names don't match. **Accepted limitation** — summaries are more synthesized, and triage focuses on full handoffs where untracked items are most likely to surface.

**`/distill` and summaries:** Distill extracts from `Decisions`, `Learnings`, `Codebase Knowledge`, `Gotchas`. Summaries have the first three (Gotchas folds into Learnings). Distill will find content in summaries — gotcha-type content just lives under Learnings. **No code change needed.**

**`/quicksave` streak guardrail:** Currently warns after 2 consecutive checkpoints. Summaries do NOT count toward the streak — the chain walk stops at the first non-checkpoint type, so a summary in the chain naturally terminates the streak count. No code change needed. Summaries capture enough depth that consecutive-summary streaking isn't a concern.

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Using summary when session was complex with deep decisions | Loses the 8-element decision depth and full narrative | Use `/save` |
| Skipping arc context gathering | Defeats the primary purpose — arc awareness | Always scan archive and git before writing |
| Writing Project Arc as a summary of prior handoffs | Arc should be a synthesis of project state, not a handoff digest | Answer "where does the project stand?" not "what happened before?" |
| Exceeding 250 lines | Drifting toward full handoff territory | If content demands it, switch to `/save` |
| Reproducing content in chat | File is the deliverable | Brief confirmation only |
