# Handoff Plugin

> **v1.5.0** · MIT · Python ≥3.11 · Runtime dependency: `pyyaml>=6.0` · Recommended host tool: `trash`

Session handoff and resume for Claude Code. Captures decisions, changes, learnings, and next steps at the end of a session, then restores that context at the start of the next one. Sessions link together through a chain protocol, so you can trace how work evolved across multiple sessions.

## What Problem Does This Solve?

Claude Code sessions are ephemeral — when a session ends, everything Claude learned about your codebase, the decisions you made together, and the work in progress disappears. Starting a new session means re-explaining context, re-reading files, and re-discovering constraints. The handoff plugin gives Claude a structured way to *persist session knowledge* and restore it later, turning disconnected sessions into a continuous workflow.

Beyond save/load, the plugin also provides tools for extracting durable knowledge from handoffs (`/distill`), creating work items from deferred tasks (`/defer`), triaging the backlog (`/triage`), and searching across handoff history (`/search`).

## Quick Start

### Prerequisites

| Requirement | Why it matters |
|-------------|----------------|
| Python 3.11+ | Runs the plugin's hook and helper scripts |
| `pyyaml>=6.0` | Used by ticket parsing and related frontmatter helpers |
| `trash` on `PATH` | Lets cleanup and state-file removal delete safely; without it, cleanup becomes best-effort and stale files persist until TTL pruning or manual cleanup |

The plugin does not use a separate config file. Installation plus the runtime defaults below are enough.

```bash
claude plugin install handoff@turbo-mode
```

At the end of a session:

```
/save
```

At the start of the next session:

```
/load
```

That's it. Claude captures context on save, archives the handoff on load, and links the two sessions via `resumed_from` for chain tracking.

## How It Works

### Storage Layout

```
~/.claude/
├── handoffs/
│   └── <project>/
│       ├── 2026-03-04_14-30_fix-auth-bug.md        # Active handoffs
│       ├── 2026-03-04_16-45_checkpoint-mutex-wip.md # Quicksave checkpoints
│       └── .archive/                                # Archived after /load
│           └── 2026-03-04_14-30_fix-auth-bug.md
├── .session-state/
│   └── handoff-<session-uuid>                       # Chain state files
```

| Location | Content | Retention |
|----------|---------|-----------|
| `~/.claude/handoffs/<project>/` | Active handoffs and checkpoints | 30 days |
| `~/.claude/handoffs/<project>/.archive/` | Archived after `/load` | 90 days |
| `~/.claude/.session-state/handoff-<UUID>` | Chain state (archive path) | 24 hours |
| `docs/tickets/` | Deferred work tickets (via `/defer`) | Permanent |
| `docs/learnings/learnings.md` | Distilled knowledge (via `/distill`) | Permanent |

File naming: `YYYY-MM-DD_HH-MM_<slug>.md`. Checkpoints use `YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`.

### The Handoff Format

Full handoffs are markdown files with YAML frontmatter and 13 required sections:

```yaml
---
date: 2026-03-04
time: "14:30"
created_at: "2026-03-04T14:30:00Z"
session_id: abc-123-def
resumed_from: ~/.claude/handoffs/my-project/.archive/2026-03-03_16-00_previous.md
project: my-project
branch: feature/auth
commit: a1b2c3d
title: Implement token refresh with mutex
type: handoff
files:
  - src/auth.py
  - tests/test_auth.py
---
```

#### Required Sections

1. Session Narrative (60-100 lines)
2. What Was Accomplished
3. What Happened (Since Last Handoff)
4. Decisions Made (20-30 lines each, 8-element template)
5. Changes Made
6. Current State of Work
7. In-Progress Work
8. Open Questions / Risks
9. Learnings / Discoveries
10. Codebase Knowledge
11. Next Steps
12. Gotchas
13. Session Metadata

The quality check hook enforces: 400+ body lines, all 13 sections present, at least one of {Decisions, Changes, Learnings} with substance.

### The Chain Protocol

The chain protocol links sessions together through `resumed_from` tracking:

```
Session A: /save → writes handoff-A.md
Session B: /load → archives handoff-A.md, writes state file
Session B: /save → reads state file → writes handoff-B.md with resumed_from: handoff-A.md
Session C: /load → archives handoff-B.md, writes state file
...
```

Three steps:

1. **`/load` writes state** — Archives the handoff to `.archive/`, writes the archive path to `~/.claude/.session-state/handoff-<session_id>`
2. **`/save` reads state** — Checks for a state file; if found, includes the path as `resumed_from` in the new handoff's frontmatter
3. **`/save` cleans state** — Removes the state file after writing the handoff (24-hour TTL as safety net)

This creates a traceable chain: each handoff points to its predecessor, enabling `/search` and `/triage` to correlate work across sessions.

### The Checkpoint Format

`/quicksave` produces lightweight 22-55 line checkpoints for context-pressure scenarios:

```yaml
---
# ... same frontmatter as above, but type: checkpoint ...
type: checkpoint
title: "Checkpoint: mutex implementation WIP"
---
```

5 required sections: Current Task, In Progress, Active Files, Next Action, Verification Snapshot. 3 conditional: Don't Retry, Key Finding, Decisions.

A guardrail warns after 2 consecutive quicksaves (detected via chain walking) — suggests a full `/save` to avoid context loss.

## Configuration

The plugin is intentionally low-configuration: there is no plugin-local YAML or JSON settings file. Most behavior is fixed by the handoff contract so saved context stays portable and deterministic.

### Fixed Conventions

| Area | Default | User configurable? | Notes |
|------|---------|--------------------|-------|
| Storage root | `~/.claude/handoffs/<project>/` | No | `<project>` is the git root directory name, falling back to the current directory name |
| Archive root | `~/.claude/handoffs/<project>/.archive/` | No | `/load` moves the loaded handoff or checkpoint here |
| Session chain state | `~/.claude/.session-state/handoff-<session_id>` | No | Written by `/load`; read and trashed by `/save` and `/quicksave` |
| Retention policy | Active: 30 days, archive: 90 days, state files: 24 hours | No | Enforced by `cleanup.py` during `SessionStart` |
| Search scope | Active plus archived handoffs for the current project | No | `/search` does not cross project boundaries |

### Overrideable Inputs

| Surface | Defaults | Valid values |
|---------|----------|--------------|
| `/save [title]` | Auto-generated title when omitted | Any descriptive title string |
| `/load [path]` | Most recent handoff for the current project | Optional path to a specific handoff or checkpoint |
| `/quicksave [title]` | Auto-generated checkpoint title when omitted | Any descriptive title string |
| `/search <query> [--regex]` | Literal, case-insensitive search | Query string; optional `--regex` for regex search |
| `distill.py --learnings <path> --include-section <name>` | `docs/learnings/learnings.md`; all eligible sections | Any writable path; optional handoff section names |
| `defer.py --tickets-dir <path> --date YYYY-MM-DD` | `docs/tickets/`; date is required | Any writable directory; date must match `YYYY-MM-DD` |
| `triage.py --tickets-dir <path> --handoffs-dir <path>` | `docs/tickets/`; current project's handoffs dir | Any readable tickets directory and handoffs directory |

## Environment Variables

Claude Code provides these at runtime. In normal plugin use, you do not set them manually.

| Variable | Provided by | Used by | Required? | Notes |
|----------|-------------|---------|-----------|-------|
| `CLAUDE_PLUGIN_ROOT` | Claude Code plugin runtime | Hook commands and skill shell snippets that invoke `scripts/*.py` | Yes for installed plugin execution | In the development repo, several skills document a git-root fallback when this variable is absent |
| `CLAUDE_SESSION_ID` | Claude Code skill runtime | `/save`, `/load`, and `/quicksave` chain-state and frontmatter handling | Yes for session-linking commands | Saved as `session_id` and used to name the state file |

No other plugin-specific environment variables are read by the current scripts.

## Skills

### `/save [title]`

Creates a full handoff document with synthesis process. Reads `synthesis-guide.md` internally (11 synthesis prompts covering narrative, decisions, codebase learnings, failed attempts, debugging state, etc.). ~750 lines loaded.

### `/load [path]`

Resumes from the most recent handoff (or a specific path). Archives the loaded file, writes chain state. Also handles `/list-handoffs` for browsing available handoffs. Lightweight — ~220 lines loaded.

### `/quicksave [title]`

Fast checkpoint under context pressure. Minimum viable context to resume: what you're doing, what's in progress, what to do next. ~120 lines loaded.

### `/search <query> [--regex]`

Searches active and archived handoffs for decisions, learnings, and context. Literal search is case-insensitive; regex is case-sensitive (embed `(?i)` for case-insensitive regex). 1-5 results show full sections; 6+ show summary table + 3 most recent in full. ~75 lines loaded.

### `/distill [path]`

Extracts durable knowledge from handoffs into `docs/learnings/learnings.md`. 8-step pipeline: locate handoff → extract candidates from Decisions/Learnings/Codebase Knowledge/Gotchas → dedup (exact source, exact content, updated source, new) → semantic dedup via Claude comparison → user confirmation → append. Each entry includes `<!-- distill-meta -->` provenance comment. ~210 lines loaded.

### `/defer [filter]`

Extracts deferred work items from the conversation and creates tickets in `docs/tickets/`. 3-tier signal detection (hint-scoped high, deterministic high, contextual medium). Every candidate requires an identifiable action and user confirmation before creation. Tickets include provenance tracking for `/triage` correlation. ~205 lines loaded.

### `/triage`

Read-only backlog review. Lists open tickets grouped by priority and age. Scans recent handoffs (30 days) for orphaned Open Questions and Risks that don't have corresponding tickets. 3 matching strategies: `uid_match` (session correlation), `id_ref` (ticket ID in item text), `manual_review`. Reports match counts for observability. ~161 lines loaded.

## Hooks

| Event | Matcher | Script | Timeout | Behavior |
|-------|---------|--------|---------|----------|
| `SessionStart` | n/a | `cleanup.py` | Not overridden in `hooks.json` | Best-effort prune of active handoffs older than 30 days, archived handoffs older than 90 days, and state files older than 24 hours. Always exits `0` so session start is never blocked. |
| `PostToolUse` | `Write` | `quality_check.py` | Not overridden in `hooks.json` | Validates newly written handoff and checkpoint files: required frontmatter fields, required sections, body line count bounds (400+ handoffs, 20-80 checkpoints), and the hollow-handoff guardrail. Returns `additionalContext` when it finds issues. |

## Script Reference

| Script | Purpose |
|--------|---------|
| `search.py` | CLI: `search.py <query> [--regex]`. Searches active + archived handoffs, returns JSON results sorted by date. |
| `distill.py` | CLI: `distill.py <path> [--learnings <path>] [--include-section <name>]`. Extracts candidates with 4-state dedup and durability classification. |
| `defer.py` | CLI: reads JSON array from stdin. Creates ticket files with `T-YYYYMMDD-NN` IDs and fenced YAML. |
| `triage.py` | CLI: `triage.py [--tickets-dir] [--handoffs-dir]`. Reads open tickets, scans handoffs for orphaned items, matches via 3 strategies. |
| `cleanup.py` | SessionStart hook. Prunes old handoffs and state files silently. |
| `quality_check.py` | PostToolUse hook. Validates handoff/checkpoint quality. |
| `handoff_parsing.py` | Shared library: `parse_frontmatter()`, `parse_sections()`, `parse_handoff()`. Code-fence-aware section splitting. |
| `project_paths.py` | Shared library: `get_project_name()`, `get_handoffs_dir()`, `get_archive_dir()`. Git-root detection with cwd fallback. |
| `ticket_parsing.py` | Shared library: Parses fenced-YAML ticket format (used by `triage.py`). |
| `provenance.py` | Shared library: Dual-read provenance (YAML field + HTML comment fallback) for session correlation. |

## Reference Files

| File | Purpose |
|------|---------|
| `references/handoff-contract.md` | Canonical contract: frontmatter schema, chain protocol, storage, project name detection. Wins over format-reference on conflicts. |
| `references/format-reference.md` | Section content guidance: depth targets per section, worked examples (~400 lines) for new and resumed sessions. |
| `skills/save/synthesis-guide.md` | Internal to `/save`: 11 synthesis prompts + completeness self-check. Loaded before writing handoffs. |

## Tests

354 tests across 10 test files:

| Test File | Coverage Area |
|-----------|--------------|
| `test_cleanup.py` | Pruning logic, project detection, trash integration |
| `test_quality_check.py` | Frontmatter validation, section validation, line counts, hollow-handoff guardrail |
| `test_handoff_parsing.py` | Frontmatter parsing, section splitting, code-fence awareness |
| `test_project_paths.py` | Git-root detection, directory fallback, archive paths |
| `test_search.py` | Search across active + archived, CLI interface |
| `test_distill.py` | Candidate extraction, durability classification, dedup states, content hashing |
| `test_defer.py` | ID allocation, slug generation, ticket rendering, priority/effort validation |
| `test_ticket_parsing.py` | Fenced-YAML extraction, schema validation |
| `test_provenance.py` | Provenance parsing (YAML + HTML comment), session matching |
| `test_triage.py` | Status normalization, orphan detection, 3-strategy matching, defer+triage integration |

```bash
cd packages/plugins/handoff && uv run pytest
```

## Known Limitations

1. **Resume-crash recovery** — If a session resumes then crashes before saving, the state file persists but no successor references the archived handoff. The chain has a gap.
2. **Archive-failure chain poisoning** — If archive creation fails but the state file is written, `resumed_from` points to a non-existent file.
3. **State-file TTL race** — Sessions lasting >24 hours may lose the `resumed_from` link if `cleanup.py` prunes the state file before the next save.
4. **uid_match scope** — Session correlation only works for tickets created via `/defer` from handoff contexts. Other source types (`pr-review`, `codex`, `ad-hoc`) route to manual review.
5. **Consecutive checkpoint detection** — Only detects within a connected `resumed_from` chain. Cross-session checkpoints without `/load` don't trigger the guardrail.
