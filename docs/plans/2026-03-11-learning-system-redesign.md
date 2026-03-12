# Learning System Redesign

**Date:** 2026-03-11
**Status:** Complete
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
| `/learn` | Deployed | Minor update: encourage structured format; mark `/learn log` as legacy; remove stale `promote` rejection |
| `/distill` | Deployed | Add metadata interaction rules for `promote-meta` coexistence (WU3) |
| `/promote` | New | Build from this spec |
| `docs/learnings/learnings.md` | Active (28 entries) | No migration; metadata comments added over time |
| `.claude/rules/learnings.md` | Active | Remove stale episode/`/learn log` references; convert to pointer |
| `.claude/CLAUDE.md` Systems table | Active | Update status and spec reference |
| Consultation contract §17 | Active | Add deferral note; remove MUST language for card injection |

## `/promote` — Graduate Learnings to CLAUDE.md

### Overview

A single skill that reads `learnings.md`, identifies mature entries, proposes CLAUDE.md edits, and executes approved promotions.

| Invocation | Behavior |
|---|---|
| `/promote` | Surface top 5 mature candidates ranked by leverage, user selects, draft CLAUDE.md edit |
| `/promote --all` | Show all unpromoted entries (bypasses maturity filter and cap, still skips already-promoted) |
| `/promote --limit N` | Surface top N mature candidates (overrides default cap of 5) |

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

**Threshold:** Surface entries Claude is >70% confident are promotable, erring toward inclusion.

**Ranking:** After filtering, rank candidates by repo-wide leverage — how broadly the insight applies and how much it would improve Claude's behavior across sessions. Present the top 5 by default. The user makes the final call.

**Batching:** Default cap is 5 candidates per run. `--limit N` overrides. `--all` bypasses both maturity filtering and the cap (but still skips already-promoted entries). The cap prevents first-run overwhelm — with 28 existing entries, most will pass the maturity filter.

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

**Escalation to `/claude-md`:** `/promote` is bounded instruction graduation — short, mechanical rules that fit within existing CLAUDE.md structure. Defer to `/claude-md` (structural authorship with 5-agent verification) when any of these triggers fire:

| Trigger | Example |
|---|---|
| New top-level section needed | Insight requires a "Security" section that doesn't exist |
| Single learning requires cross-section edits | Pattern affects both Gotchas and Workflow sections |
| Section reorganization required | Promoted entries would make an existing section incoherent |
| >15 net new content lines in one run | Batch of promotions would substantially grow CLAUDE.md |

When a trigger fires, report it to the user and suggest running `/claude-md` instead.

### Editorial Budget

Promoted entries should be compact: ~40-50 words each. CLAUDE.md is loaded every session — verbosity compounds as context cost.

**Soft ceiling:** If CLAUDE.md exceeds ~200 content lines, `/promote` should prefer merge/replace over append (consolidate with existing entries on similar topics). Hard ceiling and automated pruning are deferred to v2.

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
- Staleness tracking deferred to v2 (if promoted content is later removed from CLAUDE.md, the learning remains marked as promoted)

### Metadata Interaction Contract

`learnings.md` entries may carry two independent metadata comments: `distill-meta` (written by `/distill`) and `promote-meta` (written by `/promote`). These are separate namespaces — no unified schema in v1.

**Rules:**

1. **Each writer owns its namespace.** `/promote` reads and writes `promote-meta` only. `/distill` reads and writes `distill-meta` only.
2. **Both comments can coexist.** A distill-then-promote entry has both comments. Neither writer deletes the other's comment during normal operations.
3. **`/promote` reads sibling `distill-meta` for context** (provenance, source handoff) but never modifies it.
4. **`/distill` UPDATED_SOURCE must account for `promote-meta`.** When `/distill` replaces an entry (heading through `distill-meta` inclusive), it must also delete any `promote-meta` comment in that entry's block. The replaced entry is treated as new content — previous promotion is invalidated.
5. **UPDATED_SOURCE + promoted entry warning.** When `/distill` encounters an UPDATED_SOURCE entry that has `promote-meta`, surface the promotion target to the user before replacing. Default: replace + clear `promote-meta`. Override: replace + keep promoted (user asserts CLAUDE.md instruction is still correct).
6. **Malformed comments fail open.** Unrecognized comment format → treat as if absent.
7. **No cross-references.** Neither comment points to the other. Provenance is tracked independently.

### Processing Model

**Entry-scoped durability.** Process one entry to completion (CLAUDE.md edit + `promote-meta` written) before starting the next. Never write `promote-meta` before the CLAUDE.md edit succeeds.

**No partial promotion in v1.** If an entry is too large or complex for a single CLAUDE.md edit, ask the user to split it via `/learn` first. Do not attempt multi-edit promotions.

**Interrupted session recovery.** If a session is interrupted mid-promotion, the next `/promote` run may find an entry whose content is already in CLAUDE.md but lacks `promote-meta`. Surface this as a reconciliation choice: attach metadata (confirm the existing promotion), re-draft (update the CLAUDE.md entry), or skip.

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

## Deferred Systems

### Consultation Contract §17 (Codex Learning Injection)

The consultation contract §17 specifies injecting up to 5 learning cards into Codex briefings. This redesign omits the card model that §17 requires (cards, injection slots, token budgets, extraction agents). §17's MUST language must be amended to reflect this deferral.

**What §17 could become:** Deterministic query-scoped retrieval of *unpromoted* learnings for Codex briefings — a separate feature from the promotion funnel. This is a v2 consideration, not a v1 requirement.

**Required change:** Amend consultation contract to mark §17 as deferred. Remove MUST language. Add note: "Deferred pending learning system v2. See `docs/plans/2026-03-11-learning-system-redesign.md`."

### `/learn log` (Structured Episodes)

`/learn log` creates structured episodes in `docs/learnings/episodes/`. Zero episodes were created during Phase 0. The structured episode path is **legacy/dormant** — not actively deprecated, but no downstream consumer exists in this redesign.

**Required changes:**
- Remove the "Tip: consider `/learn log`" hint from `/learn` SKILL.md
- Mark the episode logging section as legacy in `/learn` SKILL.md
- Remove episode references from `.claude/rules/learnings.md`
- Episode schema reference (`references/episode-schema.md`) and validator (`scripts/validate_episode.py`) remain on disk — no deletion needed

## Implementation Notes

- Build `/promote` using `/skill-creator` for proper SKILL.md structure and frontmatter
- `/promote` targets project CLAUDE.md (`.claude/CLAUDE.md`) only. Global CLAUDE.md (`~/.claude/CLAUDE.md`) is out of scope for v1 — it's read for overlap checking but never written to
- The skill needs `Read` and `Edit` in `allowed-tools` (no `Bash` needed — all operations are file reads and edits)
- Light structure in `/learn` is a SKILL.md text change, not a code change

## Scope of Work

Four work units with strict dependency ordering:

```
WU1: Spec Alignment  →  WU2: Stale Cleanup  →  WU3: /distill Rules  →  WU4: Build /promote
     (concurrent↗)
```

### WU1: Normative Spec Alignment

Amend this spec and the consultation contract before touching skill files.

1. ~~Fix Component Inventory false claims~~ (done — this amendment)
2. ~~Add metadata interaction contract~~ (done — this amendment)
3. ~~Add ranked batching with default cap of 5~~ (done — this amendment)
4. ~~Add escalation rules~~ (done — this amendment)
5. ~~Add editorial budget~~ (done — this amendment)
6. ~~Mark `/learn log` as legacy/dormant~~ (done — this amendment)
7. ~~State "no partial promotion in v1"~~ (done — this amendment)
8. Amend consultation contract §17 — remove MUST language, add deferral note

### WU2: Stale Surface Cleanup (concurrent with or after WU1)

1. `.claude/rules/learnings.md` — remove episode and `/learn log` references; convert auto-load to pointer
2. `.claude/skills/learn/SKILL.md` — remove "Phase 1b" `promote` rejection; mark episode logging as legacy; remove `/learn log` tip
3. `.claude/CLAUDE.md` Systems table — update learning system status and spec reference

### WU3: /distill Interaction Rules (after WU1)

1. `packages/plugins/handoff/skills/distill/SKILL.md` — update entry block deletion to include both meta comments
2. Add promoted-entry warning flow for UPDATED_SOURCE + `promote-meta`
3. No `distill.py` code change required — behavior is skill-driven

### WU4: Build /promote (after all above)

1. Build `/promote` skill from this spec using `/skill-creator`
2. Update `/learn` skill to encourage context/insight/implication format
