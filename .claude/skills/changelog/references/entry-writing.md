# Entry Writing Patterns

Reference for writing changelog entries enriched by handoff context.

## With vs Without Handoff Context

Handoff-enriched entries describe impact and intent, not just mechanics:

| Without handoff context | With handoff context |
|------------------------|---------------------|
| Add comparative posture | Add `comparative` posture for structured trade-off analysis in multi-phase dialogues |
| Fix payload collision bug | Fix payload collision where guard hook's atomic inject overwrites new payloads with stale data between stages |
| Add phase tracking fields | Add phase-local convergence — track posture phases in `ConversationState` so each dialogue phase has independent convergence detection |
| Refactor auth module | Refactor auth into pipeline pattern — each auth step is a composable middleware, replacing nested if-chains |

The pattern: git tells you **what** changed (files, lines), PRs tell you **what** it's called (title, description), handoffs tell you **why** it matters (decisions, trade-offs, user impact).

## Handoff Section Value Map

When reading handoff files, these sections have the highest changelog value:

| Section | Value | What to Extract |
|---------|-------|-----------------|
| **Changes** | Implementation record — per-file changes with commit hashes, patterns followed | Raw material for entries. Each subsection typically maps to one changelog bullet. |
| **Decisions** | The "why" — alternatives rejected, trade-offs accepted, confidence levels | Transforms mechanical entries into meaningful ones. Use to write entries that explain impact, not just mechanics. |
| **Goal** | Session scope and stakes, connection to project arc | Groups changes into logical features. The "Connection to project arc" subfield shows how the session fits into a larger effort. |
| **In Progress** | Completion status: "clean stopping point" vs "work in flight" | Partial work → `[Unreleased]`, not a version. |
| **Next Steps** | Deferred work — what comes after this session | Negative filter — exclude from changelog. |

Sections to ignore (session-continuation context, not changelog material): Learnings, Risks, Gotchas, Codebase Knowledge, Context, User Preferences, References.

## Reading Strategy for Large Archives

Don't read entire handoff files. Extract targeted sections:

```bash
# Extract the Changes section from a handoff
awk '/^## Changes/{flag=1;next}/^## /{flag=0}flag' "$ARCHIVE_DIR/<filename>.md"

# Extract the Decisions section
awk '/^## Decisions/{flag=1;next}/^## /{flag=0}flag' "$ARCHIVE_DIR/<filename>.md"
```

For each relevant handoff:
1. Always read **Changes**
2. Read **Decisions** and **Goal** when changes are non-trivial (new features, architectural shifts, complex fixes)
3. Read **In Progress** to determine if work is complete
4. Check **Next Steps** to identify what should be excluded

## Locating the Handoff Archive

```bash
# Derive project name from repo root
PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel)")
ARCHIVE_DIR=~/.claude/handoffs/$PROJECT_NAME/.archive

# List files, filter by date
ls "$ARCHIVE_DIR" | grep "^YYYY-MM"

# Find handoffs touching specific paths
grep -l "packages/plugins/<name>" "$ARCHIVE_DIR"/YYYY-MM-*.md
```

If the archive directory doesn't exist, skip handoff evidence and note the gap explicitly.
