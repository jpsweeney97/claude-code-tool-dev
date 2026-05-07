---
name: promote
description: Graduate mature learnings from docs/learnings/learnings.md into .claude/CLAUDE.md as permanent project instructions. Reads learnings, ranks by repo-wide leverage, presents candidates for user selection, drafts CLAUDE.md edits, and marks promoted entries. Use when user says "/promote", "promote learnings", "graduate to CLAUDE.md", or "what learnings are ready to promote".
argument-hint: "[--all | --limit N]"
allowed-tools:
  - Read
  - Edit
---

# Promote

Graduate mature learning entries into CLAUDE.md as permanent project instructions. A promotion means the insight becomes a durable part of project context loaded every session.

## Inputs

| Input | Behavior |
|-------|----------|
| `/promote` | Surface top 5 mature candidates ranked by leverage |
| `/promote --all` | Show all unpromoted entries (bypasses maturity filter and cap, still skips promoted) |
| `/promote --limit N` | Surface top N mature candidates (overrides default cap of 5) |

## Procedure

### Step 1: Read learnings

Read `docs/learnings/learnings.md`. Parse each `### YYYY-MM-DD [tags]` entry.

**If file not found:** Report "No learnings file found at `docs/learnings/learnings.md`" and STOP.

For each entry, check for metadata comments:
- `<!-- promote-meta {...} -->` — already promoted, skip
- `<!-- distill-meta {...} -->` — note provenance for context

**If all entries have `promote-meta`:** Report "All entries already promoted" and STOP.

**If malformed `promote-meta`:** Treat entry as unpromoted (fail-open — better to re-surface than silently skip).

### Step 2: Assess maturity

For each unpromoted entry, evaluate maturity using these signals:

| Signal | What it indicates | Example |
|--------|-------------------|---------|
| **Age** | Survived without contradiction | Entry from 3 weeks ago vs yesterday |
| **Breadth** | Applies across contexts | "Plugin MCP tool naming" vs "fixed bug in line 42" |
| **Reuse evidence** | Same pattern noted in 2+ entries | Independent observations converging |
| **Actionability** | Can become a concrete instruction | "Always use fail-closed for security hooks" vs "security is important" |
| **Independence** | Stands alone without session context | "PreToolUse hooks are fail-open" vs "After debugging for 2 hours..." |

**Not maturity signals:** Entry length, number of tags, position in file, whether it came from `/learn` vs `/distill`.

**Missing fields:** If a structured entry lacks the Implication field (or uses freeform format), treat as a weak actionability signal — lower confidence, not disqualifying.

**Threshold:** Surface entries you are >70% confident are promotable, erring toward inclusion.

**Ranking:** Rank passing candidates by repo-wide leverage — how broadly the insight applies and how much it would improve behavior across sessions.

**Filtering:**
- Default: top 5 candidates after maturity filter
- `--limit N`: top N candidates after maturity filter
- `--all`: all unpromoted entries, no maturity filter, no cap

**If no mature candidates (without `--all`):** Report "No mature candidates found. Run `/promote --all` to see all entries." and STOP.

### Step 3: Present candidates

Show each candidate with:

```
**#{n}** — {entry heading}
**Tags:** {tags}
**Age:** {days since entry date}
**Maturity:** {High/Medium} — {brief rationale}
**Provenance:** {"/learn capture" or "/distill from <source_anchor>" if distill-meta present}

> {entry content, abbreviated if long}

**Proposed placement:** {target section in CLAUDE.md}
```

After all candidates:

```
Select entries to promote (e.g., "1, 3, 5", "all", or "none"):
```

**If user selects none:** Exit cleanly with no changes.

### Step 4: Draft CLAUDE.md edits

For each selected entry, in order:

1. **Read current CLAUDE.md** (`.claude/CLAUDE.md`) structure — sections, subsections, tables
2. **Identify placement:**
   - Find the most relevant existing section
   - If no section fits, propose a new subsection under the most relevant parent
   - If no parent fits, surface the placement question to the user before drafting
3. **Check for semantic overlap** with existing CLAUDE.md content — never duplicate
4. **Transform** the learning narrative into CLAUDE.md style:
   - Prescriptive, concise, pattern-conformant with surrounding content
   - Match the format of the target section (table row, bullet, paragraph — whatever neighbors use)
   - Target ~40-50 words per promoted entry

**Transformation examples:**

| Learning entry (narrative) | CLAUDE.md entry (instruction) |
|---|---|
| "PreToolUse hooks are mechanically fail-open — unhandled exceptions don't produce exit code 2, so the tool call proceeds..." (5 sentences) | In Gotchas: "**Hook failure polarity**: PreToolUse hooks are fail-open. Unhandled exceptions allow the tool call. For critical enforcement, catch all errors and return a block decision." |
| "Plugin-provided MCP tools use `mcp__plugin_<plugin>_<server>__<tool>` naming..." (4 sentences) | In relevant section: "**MCP tool naming**: Plugin tools use `mcp__plugin_<plugin>_<server>__<tool>`. Must match across hook matchers, skill `allowed-tools`, and agent `tools` frontmatter." |

5. **Show the proposed edit in context** — a few lines before and after so the user can judge fit

```
Proposed edit for #{n}:
Section: {section name}

  ... existing line above ...
+ **New entry title**: New instruction text here.
  ... existing line below ...

Approve, modify, or skip?
```

### Step 5: Check escalation triggers

Before applying edits, check whether any trigger fires:

| Trigger | Condition |
|---------|-----------|
| New top-level section needed | Insight requires a section that doesn't exist |
| Cross-section edits | Single learning requires edits in 2+ sections |
| Section reorganization | Promoted entries would make an existing section incoherent |
| >15 net new content lines | Batch of promotions would substantially grow CLAUDE.md |

**If a trigger fires:** Report it to the user and suggest running `/claude-md` instead. Do not proceed with the promotion unless the user explicitly overrides.

### Step 6: Apply edits

Process one entry at a time to completion. Order: CLAUDE.md edit first, then `promote-meta`.

For each approved entry:

1. **Apply the CLAUDE.md edit** using the Edit tool
2. **Only after the edit succeeds**, append `promote-meta` to the entry in `learnings.md`:

```markdown
<!-- promote-meta {"promoted_at": "YYYY-MM-DD", "target": "CLAUDE.md#SectionName"} -->
```

Append the comment immediately after the entry's content paragraph (or after `distill-meta` if present).

**Entry-scoped durability:** Complete one entry (CLAUDE.md edit + `promote-meta`) before starting the next. Never write `promote-meta` before the CLAUDE.md edit succeeds.

**No partial promotion:** If an entry is too large or complex for a single CLAUDE.md edit, ask the user to split it via `/learn` first. Do not attempt multi-edit promotions.

### Step 7: Report

After all promotions complete:

```
Promoted {n} entries to CLAUDE.md:
- #{1}: {heading} → {target section}
- #{3}: {heading} → {target section}
```

## Editorial Budget

Promoted entries should be compact: ~40-50 words each. CLAUDE.md is loaded every session — verbosity compounds as context cost.

**Soft ceiling:** If CLAUDE.md exceeds ~200 content lines, prefer merge/replace over append (consolidate with existing entries on similar topics). Hard ceiling and automated pruning are deferred to v2.

## Interrupted Session Recovery

If a session is interrupted mid-promotion, the next `/promote` run may find an entry whose content is already in CLAUDE.md but lacks `promote-meta`. Surface this as a reconciliation choice:

- `attach metadata` — confirm the existing promotion, write `promote-meta`
- `re-draft` — update the CLAUDE.md entry
- `skip` — leave as-is (entry will re-surface next run)

## Metadata Interaction Contract

`learnings.md` entries may carry two independent metadata comments:

| Comment | Writer | Purpose |
|---------|--------|---------|
| `<!-- distill-meta {...} -->` | `/distill` | Provenance from handoff extraction |
| `<!-- promote-meta {...} -->` | `/promote` | Graduation to CLAUDE.md |

**Rules:**

1. `/promote` reads and writes `promote-meta` only. Never modify `distill-meta`.
2. Both comments can coexist on one entry.
3. `/promote` reads sibling `distill-meta` for context (provenance, source handoff) but never modifies it.
4. Malformed comments fail-open — treat as if absent.
5. No cross-references between comments.

## Failure Modes

| Failure | Recovery |
|---------|----------|
| `learnings.md` not found | Report path and STOP |
| No unpromoted entries | Report "All entries already promoted" and STOP |
| No mature candidates (without `--all`) | Report and suggest `--all` |
| Malformed `promote-meta` | Treat entry as unpromoted (fail-open) |
| CLAUDE.md not found | Report "No CLAUDE.md found at `.claude/CLAUDE.md`" and STOP |
| Semantic overlap with existing CLAUDE.md | Show overlap, ask: skip, merge, or replace |
| Escalation trigger fires | Report trigger, suggest `/claude-md` |

## Scope

- **Reads:** `docs/learnings/learnings.md`, `.claude/CLAUDE.md`
- **Writes:** `.claude/CLAUDE.md` (promoted instructions), `docs/learnings/learnings.md` (`promote-meta` comments only)
- **Does NOT:** modify `distill-meta`, delete learning entries, write to global `~/.claude/CLAUDE.md`, create new files
