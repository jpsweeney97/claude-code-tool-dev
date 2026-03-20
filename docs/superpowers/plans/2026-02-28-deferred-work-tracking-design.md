# Design: Deferred Work Tracking (`/defer` + `/triage`)

```yaml
date: 2026-02-28
status: approved
reviewed_by: codex-dialogue (collaborative + evaluative + adversarial)
codex_threads:
  - "019ca299-4a87-7b83-9192-d4f1b5411723"  # collaborative design (6/10 turns)
  - "019ca2dd-edda-70a3-884a-64372b4bf260"  # evaluative deep-review (6/8 turns)
  - "019ca2fc-ecb5-78b3-b860-b2d466b8b185"  # adversarial review (6/12 turns)
codex_outcome: converged (34 resolved, 7 emerged, 8 P0/P1 fixes applied across 3 reviews)
plugin: packages/plugins/handoff
```

## Problem

Deferred work items get permanently lost across sessions. Items arise from PR reviews, Codex consultations, handoff Open Questions, and ad-hoc observations. Current systems capture these in prose (handoff "Open Questions", MEMORY.md "Deferred:" list) but provide no structured tracking, no status lifecycle, and no pull mechanism to resurface them. Items that don't get explicitly ticketed age silently.

**Evidence:** The MEMORY.md "Deferred:" list has carried 3 Codex review findings + 1 governance rule + O2 since 2026-02-17 with no progress. PR #29 review generated 6 more deferred items with no tracking mechanism beyond this conversation.

## Solution

Two skills in the handoff plugin:

- **`/defer`** — extract deferred items from current conversation context, create tickets in `docs/tickets/`
- **`/triage`** — read open tickets, scan recent handoffs for orphaned items, present report

## Key Design Decisions

All decisions reviewed via Codex collaborative dialogue (6 turns, full convergence).

### Unified ticket schema (no fork)

Deferred items use the exact same `docs/tickets/` format as hand-crafted tickets. Provenance tracked via `defer-meta` HTML comment in the body, not in the ticket ID.

**Rationale:** Prefixing provenance into the ID creates two namespaces for the same artifact type. Provenance is metadata, not identity.

**Rejected:** Separate `D-NNN` prefix scheme — adds complexity without benefit.

### Handoff plugin as home

`/defer` and `/triage` live in `packages/plugins/handoff/` alongside save, load, search, distill.

**Rationale:** `/triage` correctness is coupled to handoff contract semantics (section parsing, retention behavior). Lockstep versioning is a feature. Logic stays modular (`defer.py`, `triage.py`) for cheap future relocation.

### 6-state status enum with read-time normalization

```
deferred → open → in_progress → done
                → blocked → (unblocked) → in_progress
                → wontfix
```

| Status | Entry point | Meaning |
|--------|-------------|---------|
| `deferred` | `/defer` creates | Captured, not yet triaged |
| `open` | Hand-crafted or triaged | Ready to work |
| `in_progress` | Manual | Actively being worked |
| `blocked` | Manual | Waiting on dependency |
| `done` | Manual | Completed |
| `wontfix` | `/triage` or manual | Intentionally not addressing |

"triaged" is an event, not a durable state.

**Legacy status normalization:** Existing tickets use values outside this enum (`closed`, `complete`, `implemented`, `planning`, `implementing`). `triage.py` applies read-time normalization:

| Legacy value | Normalized to | Confidence |
|-------------|---------------|------------|
| `complete`, `implemented`, `closed` | `done` | high |
| `planning` | `open` | medium |
| `implementing` | `in_progress` | high |

The `triage.py` JSON output includes `status_raw` (original) and `status_normalized` (mapped). No migration of existing ticket files.

### Extract-confirm-create pattern (from `/distill`)

`/defer` follows the same UX contract as `/distill`: extract candidates from context, present for confirmation, create artifacts on approval. Never auto-write.

### Extraction reliability model: best-effort assistant

`/defer` uses LLM extraction with deterministic rendering. `/distill` uses the inverse: deterministic extraction with LLM synthesis. This means `/defer`'s failure mode is invisible false negatives — missed deferred items never appear in the confirmation UX, so the user cannot catch them.

**Coverage guarantee:** Best-effort assistant (not comprehensive capture). The skill's confirmation UX catches false positives but not false negatives. To mitigate:
- Each candidate must include an **evidence anchor** (quoted text from conversation).
- After presenting candidates, run a second-pass coverage check and present "possible misses" section.
- The confirmation UX must declare: "This is a best-effort extraction. Review the conversation if completeness matters."

**Phase 1 trigger:** If users report missed items > 2 per session, add a structured deferral signal (e.g., `<!-- defer: ... -->` in conversation) that enables deterministic extraction.

### Dual-write provenance (YAML + HTML comment)

Provenance is stored in two locations:
1. **Primary:** `provenance` field in the ticket's fenced YAML frontmatter (durable, survives editing)
2. **Secondary:** `defer-meta` HTML comment at end of body (backward-compatible, parseable by regex)

**Rationale:** Trailing HTML comments are fragile — editors and markdown formatters may strip them. Zero production `distill-meta` comments exist in `docs/learnings/learnings.md` despite 20 entries, so comment survival is empirically unvalidated. The YAML field is the authoritative source; the comment is a secondary signal for tools that grep rather than parse.

**`provenance.py` reads both:** YAML field first, fall back to comment. If both exist and disagree, YAML wins.

### `/save` stays untouched

We are explicitly keeping `/save` unchanged. Deferral is handled by `/defer`, not embedded in the save workflow.

**Interaction model:** `/defer` explicit + `/save` unchanged + `/triage` reconciles.

### Deterministic-only orphan detection (Phase 0)

No lexical scoring for MVP. Three matching strategies:

1. **UID match** — handoff `session_id` matched against `defer-meta.source_session` in ticket bodies (the machine join key). `source_ref` is human-readable display text only, not used for matching. `source_session` stores the **full UUID** (not truncated).
2. **Ticket ID reference search** — handoff text contains a ticket ID pattern. Regex union covers both new and legacy formats:
   - New: `T-\d{8}-\d{2}` (e.g., `T-20260228-01`)
   - Legacy numeric: `T-\d{3}` (e.g., `T-004`)
   - Legacy alpha: `T-[A-F]` (e.g., `T-A`)
   - Legacy noun: `handoff-\w+` (e.g., `handoff-distill`)
3. **`manual_review`** — unmatched items presented to user for manual classification

**Source-type coverage:** UID match only works for tickets created from handoff-derived contexts (where a `session_id` exists in both the handoff and the `defer-meta`). Tickets with `source_type: pr-review`, `codex`, or `ad-hoc` route to `manual_review` by design — these source types have no corresponding handoff file with a joinable `session_id`. This is an acknowledged Phase 0 limitation, not a bug.

**Phase 1 triggers:**
- Lexical scoring: manual-review backlog > 2 weeks, corpus > 100 tickets, or user request.
- PR-review matching: add a PR-review-specific artifact or matching path when PR-review tickets are a significant portion of `manual_review` items.

### `/defer` and `/distill` are orthogonal by artifact intent

Same handoff source can produce both:
- `/distill` → knowledge artifacts (learnings)
- `/defer` → work artifacts (tickets)

Separated by intent, not location. No shared "already-extracted" registry for MVP.

**Cross-skill awareness (informational only):** When processing the same handoff source, `/defer` shows "Found N distill entries from this handoff" and `/distill` shows "Found M tickets deferred from this handoff." Uses existing `distill-meta` and `defer-meta` provenance data. Never blocking — informational notices only.

## Architecture

```
packages/plugins/handoff/
  scripts/
    ticket_parsing.py    # Parse fenced-YAML ticket format (NOT handoff frontmatter)
    provenance.py        # Shared join contract: defer-meta parsing, session matching
    defer.py             # Ticket creation logic (deterministic)
    triage.py            # Ticket reading + orphan detection (deterministic)
  skills/
    defer/SKILL.md       # Extract from conversation → create tickets
    triage/SKILL.md      # Review open tickets + scan handoffs
  tests/
    test_ticket_parsing.py
    test_provenance.py
    test_defer.py
    test_triage.py
```

**Critical:** Existing tickets use fenced YAML (` ```yaml ... ``` `) format, NOT `---` frontmatter. `handoff_parsing.py` cannot parse tickets — its regex skips multiline values and requires `---` at byte 0.

**`ticket_parsing.py` approach:** Extract the fenced YAML block (text between ` ```yaml ` and ` ``` `), then parse with `yaml.safe_load` (PyYAML). This handles multiline values (`files:`, `blocked_by:`, `blocks:` arrays) that appear in 14 of 17 existing tickets. Schema validation after parse: required fields (`id`, `date`, `status`), type checks (`files` is list, `status` is string). PyYAML is added to `pyproject.toml` as a dependency.

**`HandoffFile.frontmatter` is `dict[str, str]`** — ticket frontmatter is `dict[str, Any]` (lists for `files`, `blocked_by`, `blocks`). These are separate types; `ticket_parsing.py` returns its own `TicketFile` type.

### Script responsibilities

| Script | Input | Output | Side effects |
|--------|-------|--------|--------------|
| `ticket_parsing.py` | Ticket markdown file path | Parsed ticket (frontmatter dict + body sections) | None |
| `provenance.py` | Ticket body text or handoff body text | Parsed `defer-meta` / `distill-meta` comments | None |
| `defer.py` | Candidate JSON (from skill) | Ticket markdown file content | Write to `docs/tickets/` |
| `triage.py` | `docs/tickets/` path, handoffs dir | JSON report (open tickets + orphans) | None (read-only) |

### Responsibility split: SKILL.md vs script

| Responsibility | Owner | Rationale |
|---------------|-------|-----------|
| Heuristic extraction (LLM judgment) | SKILL.md | Conversation analysis requires LLM |
| Candidate presentation + confirmation | SKILL.md | UX interaction |
| ID allocation, markdown rendering, file writes | `defer.py` | Deterministic, testable |
| Ticket parsing, status normalization | `ticket_parsing.py` | Deterministic, testable |
| Provenance matching (session join) | `provenance.py` | Shared between defer + triage |

### Skill types

| Skill | Primary type | Invocation | Execution | Side effects |
|-------|-------------|------------|-----------|--------------|
| `/defer` | Technique | Manual (`/defer`) | Inline | Writes ticket files, commits |
| `/triage` | Technique | Manual (`/triage`) | Inline | Read-only (Phase 0) |

## Ticket Schema

### Frontmatter (YAML)

Same fields as existing tickets. New additions marked with *.

```yaml
id: T-20260228-01            # Auto-generated: T-YYYYMMDD-NN
date: 2026-02-28
status: deferred              # *New status value (existing: open, in_progress, etc.)
priority: medium              # low | medium | high | critical
source_type: pr-review        # *pr-review | codex | handoff | ad-hoc
source_ref: "PR #29"          # *Human-readable display text (not used for matching)
branch: feature/knowledge-graduation
blocked_by: []
blocks: []
effort: XS                    # XS | S | M | L | XL
files:                        # *Affected files (minimize future re-exploration)
  - path/to/affected/file.py
provenance:                   # *Machine join key (dual-write with defer-meta comment)
  source_session: "5136e38e-efc5-403f-ad5e-49516f47884b"  # Full UUID, not truncated
  source_type: pr-review
  created_by: defer-skill
```

### ID format

`T-YYYYMMDD-NN` where NN is a zero-padded sequence number within the date. Auto-increment by parsing the `id` field from each ticket's fenced YAML (not by scanning filenames — filenames use title slugs like `2026-02-27-analytics-A-codex-stats-skill.md`, not ID prefixes).

Existing legacy IDs (T-004, T-A, handoff-distill, etc.) are unchanged. The new format applies only to `/defer`-created tickets.

### Body (Markdown)

Five sections, auto-generated from conversation context:

```markdown
# T-20260228-01: Section.level is always 2 — dead field

## Problem

`Section.level` is always 2 — dead field creates false generality in the parser.

## Source

PR #29 review, type-design-analyzer agent finding I8.
Branch: `feature/knowledge-graduation`. Session: `5136e38e-efc5-403f-ad5e-49516f47884b`.

## Proposed Approach

Remove `level` field from `Section` dataclass. Update all callers.

## Acceptance Criteria

- [ ] `Section` dataclass has no `level` field
- [ ] All tests pass
- [ ] No callers reference `Section.level`

<!-- defer-meta {"v": 1, "source_session": "5136e38e-efc5-403f-ad5e-49516f47884b", "source_type": "pr-review", "source_ref": "PR #29", "created_by": "defer-skill"} -->
```

### `defer-meta` comment

Provenance tracking, same pattern as `distill-meta`. Enables `/triage` to match tickets back to their source context.

```json
{
  "v": 1,
  "source_session": "<full UUID from ${CLAUDE_SESSION_ID}, not truncated>",
  "source_type": "pr-review|codex|handoff|ad-hoc",
  "source_ref": "<PR #N, thread ID, handoff filename — human display text only>",
  "created_by": "defer-skill"
}
```

**Note:** `defer-meta` is the **secondary** provenance store. The `provenance` YAML field in the ticket frontmatter is primary. `provenance.py` reads YAML first, falls back to comment. The comment exists for backward compatibility with grep-based tools.

**Structural difference from `distill-meta`:** `defer-meta` uses `source_session` (bare UUID). `distill-meta` uses `source_uid` (SHA-256 encoding session_id + section + heading). `provenance.py` must parse both formats independently — they are not interchangeable despite similar naming.

## `/defer` Skill Design

### Trigger

User runs `/defer` or says "defer these", "track these for later", "create tickets for the remaining items".

### Procedure

1. **Analyze conversation** — scan for deferred items using hybrid extraction:
   - **Hint-scoped:** Look for explicit deferral language ("defer", "out of scope", "follow-up", "not blocking", "address later", "separate PR")
   - **Deterministic signals:** Review findings marked as suggestions/deferred, Codex unresolved items, noted-but-not-acted-on observations, items explicitly marked "not in this PR"
   - **Actionability filter:** Each candidate must have an identifiable action (fix, add, remove, refactor, investigate). Observations without clear actions are not tickets.
   - **Evidence anchor:** Each candidate must include a quoted excerpt from the conversation where the item was identified. This enables user verification.

2. **Present candidates** — table with: finding summary, source, suggested priority, affected files, evidence anchor. Use `AskUserQuestion` for confirmation (multi-select). Include a "possible misses" section listing conversation segments that *might* contain deferred items but didn't meet the actionability filter. Declare: "This is a best-effort extraction. Review the conversation if completeness matters."

3. **For each confirmed candidate:**
   - Auto-generate ticket ID (`T-YYYYMMDD-NN`)
   - Auto-populate frontmatter from conversation context (branch, source_type, source_ref)
   - Auto-generate body sections (Problem, Source, Proposed Approach, Acceptance Criteria)
   - Write ticket file to `docs/tickets/`

4. **Commit** — stage only newly created ticket files by name (explicit paths, not globs), never `git add .`. Commit with message: `chore(tickets): defer N items from <source_type>` where `<source_type>` is the most common `source_type` among confirmed candidates (e.g., `pr-review`). If mixed, use `mixed`. If commit fails, report `partial_success` with created file paths and recovery commands — do not claim "created and committed" when only "created on disk" happened.

### Extraction heuristics

| Signal type | Examples | Confidence | Evidence anchor |
|-------------|----------|------------|-----------------|
| Explicit deferral | "defer to follow-up", "out of scope for this PR" | High | Quote the deferral statement |
| Review categorization | "suggestion", "not blocking", "design debt" | High | Quote the finding |
| Conditional action | "if X happens, then Y", "when corpus grows" | Medium | Quote the condition |
| Observation without action | "this could be improved" | Low (report in "possible misses") | N/A |

**Coverage guarantee:** Best-effort assistant. False positives are caught by user confirmation. False negatives (missed items) are invisible — mitigated by the "possible misses" section and explicit coverage disclaimer.

### Failure modes

| Failure | Recovery |
|---------|----------|
| No deferred items found in conversation | Report "No deferred items identified" and stop |
| User confirms 0 candidates | Report "Nothing to defer" and stop |
| Ticket ID collision | Increment sequence number |
| `docs/tickets/` doesn't exist | Create directory |
| Git commit fails | Report `partial_success`: list created file paths, suggest `git add <paths> && git commit` for recovery |

## `/triage` Skill Design

### Trigger

User runs `/triage` or says "what's in the backlog", "review deferred items", "any open tickets".

### Procedure (Phase 0 — read-only)

1. **Read open tickets** — scan `docs/tickets/*.md`, parse YAML frontmatter, filter by `status` not in (`done`, `wontfix`).

2. **Scan recent handoffs for orphans** — read handoffs from last 30 days in both active (`~/.claude/handoffs/<project>/*.md`) and archive (`~/.claude/handoffs/<project>/.archive/*.md`) directories. Note: `project_paths.py` needs a `get_archive_dir()` helper for the archive path.

   **Extraction input contract:** Extract items from `## Open Questions` and `## Risks` sections only. These are optional sections per the handoff contract — skip handoffs that lack them. Within these sections, extract **structured list items only** (lines starting with `-` or `1.`). Prose paragraphs and conditional items are out of scope for Phase 0 — report count of skipped prose items.

   **Match against existing tickets** using deterministic strategies:
   - UID match: handoff `session_id` matched against ticket `provenance.source_session` (YAML field, primary) or `defer-meta.source_session` (comment, fallback) via `provenance.py`. Only works for `/defer`-created tickets.
   - Ticket ID reference: handoff text contains a ticket ID matching the regex union (new + legacy formats, see orphan detection section above)
   - Unmatched items flagged as `manual_review`

   **Match-path observability:** Report counts per matching strategy (`uid_match: N`, `id_ref: N`, `manual_review: N`) to surface coverage gaps.

3. **Present report** — grouped by priority, then by age (oldest first):

   **Open tickets:**
   | ID | Priority | Age | Summary | Source |
   |----|----------|-----|---------|--------|

   **Orphaned handoff items** (Open Questions/Risks with no matching ticket):
   | Handoff | Section | Item | Match status |
   |---------|---------|------|-------------|

4. **User action** — for each orphaned item, user can:
   - "Create ticket" → invoke `/defer` pattern for that item
   - "Already tracked" → skip (no state change in Phase 0)
   - "Not actionable" → skip

### Staleness heuristics (Phase 1)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| `status: deferred` and age > 30 days | 30 days | Flag as stale |
| `status: deferred` and `blocked_by` non-empty and age > 60 days | 60 days | Flag as stale |
| `status: open` and age > 14 days | 14 days | Flag as aging |

### Triage state file (Phase 1)

Phase 0 is stateless — `/triage` reports and exits. No persistent state.

Phase 1 adds a triage state file:

```
~/.claude/.triage-state/<project>/last-triage.json
```

Contains: last triage date, items reviewed, orphans found. Enables `/triage` to show "N new items since last triage" on subsequent runs. Not committed to git (session-local state). TTL: 90 days (aligned with handoff archive retention).

### Failure modes

| Failure | Recovery |
|---------|----------|
| No tickets directory | Report "No tickets found at docs/tickets/" and stop |
| No handoffs directory | Skip orphan scan, report tickets only |
| Malformed ticket YAML | Skip ticket, report warning |
| Handoff parsing fails | Skip handoff, report warning |

## Phased Delivery

### Phase 0 (this design)

| Component | Scope |
|-----------|-------|
| `/defer` | Full: extract, confirm, create tickets, commit |
| `/triage` | Read-only: report open tickets + scan for orphans |
| `defer.py` | Ticket file generation, ID assignment |
| `triage.py` | Ticket reading, orphan detection (deterministic) |
| Tests | Unit + integration for both scripts |

### Phase 1 (future, triggered by usage)

| Component | Addition |
|-----------|----------|
| `/triage` | Write actions: reprioritize, close, wontfix |
| `/triage` | Staleness detection and flagging |
| Orphan detection | Lexical scoring (trigger: manual-review backlog > 2 weeks, corpus > 100 tickets, or user request) |
| Integration | `/defer` at end of PR review workflows (optional, user-triggered) |

## Non-Goals

- No auto-injection at session start (explicit `/triage` only)
- No GitHub Issues integration (local-first, git-committed)
- No automatic `/defer` at session end (user triggers explicitly)
- No priority decay or auto-escalation (Phase 1)
- No changes to `/save` skill
- No shared "already-extracted" registry between `/defer` and `/distill`

## Open Questions

- **Ticket ID date coupling:** `T-YYYYMMDD-NN` confirmed as format (avoids legacy ID collision). Add optional `origin_date` field for cases where discovery date differs from creation date. New ID regex for detection: `\bT-\d{8}-\d{2}\b`.
- ~~**Legacy ticket ID regex patterns:**~~ RESOLVED (adversarial review). Regex union covers 4 patterns: `T-\d{8}-\d{2}` (new), `T-\d{3}` (legacy numeric), `T-[A-F]` (legacy alpha), `handoff-\w+` (legacy noun).
- **30-day lookback configurability:** Hardcoded for Phase 0. Phase 1 may add `--lookback` flag if needed.
- **`closed` normalization:** Whether `closed` maps to `done` or `wontfix` depends on specific legacy ticket context. Use `normalization_confidence: medium` for ambiguous cases. No user-facing correction affordance in Phase 0 — user must manually edit the ticket.
- **Filename slug derivation:** `/defer` creates ticket files but the design doesn't specify how the filename slug is derived from the candidate title. Determine during implementation (likely: lowercase, hyphenated, truncated to 50 chars).
- **Cross-skill awareness implementation location:** The informational notice ("Found N distill entries from this handoff") requires reading `learnings.md` for `distill-meta` comments, but the matching key differs (`source_uid` encodes session_id + section + heading, not bare session_id). Determine during implementation whether this feature is in Phase 0 or deferred.

## References

| Resource | Location |
|----------|----------|
| Existing ticket examples | `docs/tickets/` |
| Handoff contract | `packages/plugins/handoff/references/handoff-contract.md` |
| Handoff format reference | `packages/plugins/handoff/references/format-reference.md` |
| `/distill` skill (pattern reference) | `packages/plugins/handoff/skills/distill/SKILL.md` |
| `/learn` skill (pattern reference) | `.claude/skills/learn/SKILL.md` |
| Skills guide | `docs/references/skills-guide.md` |
| Skills rules | `.claude/rules/skills.md` |
| Codex collaborative thread | `019ca299-4a87-7b83-9192-d4f1b5411723` |
| Codex deep-review thread | `019ca2dd-edda-70a3-884a-64372b4bf260` |
| Codex adversarial thread | `019ca2fc-ecb5-78b3-b860-b2d466b8b185` |
