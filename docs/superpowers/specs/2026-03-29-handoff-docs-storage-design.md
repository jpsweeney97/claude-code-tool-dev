# Handoff Plugin: docs/ Storage Migration Design

Move handoff storage from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`, making handoffs git-tracked, auto-committed project documentation.

## Motivation

Three drivers for this change:

1. **Handoffs as documentation** — handoffs are a permanent project record, searchable in git history and available for later analysis.
2. **Collaboration** — other people and sessions can discover and read handoffs without knowing about `.claude/`.
3. **Reduced friction** — writing to `.claude/` triggers permission prompts on every save. `docs/` is a normal project directory.

## Current State

The plugin was just migrated from global (`~/.claude/handoffs/<project>/`) to project-local (`<project_root>/.claude/handoffs/`). That migration is committed on `feature/handoff-project-local-storage` at `2b444453` with 344 tests passing. This design builds on that work — same branch, incremental changes.

## Design

### Storage model

```
<project_root>/
  docs/
    handoffs/
      2026-03-29_21-30_some-topic.md      # active handoffs
      archive/
        2026-03-28_14-00_older-topic.md    # loaded/consumed handoffs
```

| Aspect | Previous (`<project_root>/.claude/handoffs/`) | New (`<project_root>/docs/handoffs/`) |
|--------|-----------------------------------------------|---------------------------------------|
| Git visibility | Gitignored | Tracked and committed |
| Archive subdir | `.archive/` (hidden) | `archive/` (visible) |
| Write permissions | Requires approval prompt | Normal project directory |
| Discovery | Must know about `.claude/` | Visible in `docs/` tree |

Path resolution is unchanged: `get_project_root()` returns git root, `get_handoffs_dir()` composes `root/docs/handoffs`.

Session-state files remain at `~/.claude/.session-state/` (ephemeral, session-scoped).

### Git integration

Every handoff state change gets its own commit:

| Operation | Trigger | Commit message | Files |
|-----------|---------|----------------|-------|
| Create | `/save`, `/quicksave` | `docs(handoff): save <title>` | `docs/handoffs/<filename>.md` |
| Archive | `/load` | `docs(handoff): archive <filename>` | Move from `docs/handoffs/` to `docs/handoffs/archive/` |

Implementation: after writing/moving the file, the skill procedure instructs Claude to run `git add <file> && git commit -m "<message>"`. For archive moves, use `git mv` (handles both the delete and add in one operation). This is in the skill text, not in a hook or Python script.

Edge cases:

| Situation | Behavior |
|-----------|----------|
| Detached HEAD / rebase in progress | Skip auto-commit, warn: "Handoff saved but not committed — resolve git state first" |
| Dirty index (other staged files) | Commit only the handoff file (`git add <specific file>`, not `git add -A`) |
| No git repo | Write file, skip commit, warn user |

### Retention model

Auto-pruning is disabled for `docs/handoffs/`. The archive accumulates; git history is the lifecycle manager.

| Aspect | Previous | New |
|--------|----------|-----|
| Active retention | 30-day auto-prune | No auto-prune |
| Archive retention | 90-day auto-prune | No auto-prune |
| Session-state files | 24h auto-prune | 24h auto-prune (unchanged) |
| Cleanup mechanism | SessionStart hook | Manual (user deletes + commits) |

The `cleanup.py` SessionStart hook prunes session-state files only and stops touching handoff/archive directories.

## Code Change Scope

### Handoff plugin (`packages/plugins/handoff/`)

**Path changes** (`.claude/handoffs` → `docs/handoffs`, `.archive` → `archive`):

| File | Changes |
|------|---------|
| `scripts/project_paths.py` | `get_handoffs_dir()` returns `root/docs/handoffs` |
| `scripts/cleanup.py` | Remove handoff/archive pruning; keep session-state pruning only |
| `scripts/quality_check.py` | `is_handoff_path()` matches `docs/handoffs` as path components |
| `scripts/search.py` | `.archive` → `archive` |
| `scripts/triage.py` | `.archive` → `archive` |
| `references/handoff-contract.md` | Storage location, archive path, retention policy |
| `references/format-reference.md` | Storage location, archive path, retention policy |
| `README.md` | Path references, retention table, gitignore note |
| `CHANGELOG.md` | New entry |

**Skill updates** (path changes + git commit steps):

| Skill | Path changes | Git additions |
|-------|-------------|---------------|
| `save/SKILL.md` | ~18 path refs | Add commit step after file write |
| `load/SKILL.md` | ~12 path refs | Add commit step after archive move |
| `quicksave/SKILL.md` | Path refs | Add commit step after file write |
| `distill/SKILL.md` | Path refs | None (reads only) |

**Test updates:**

| File | Changes |
|------|---------|
| `tests/test_project_paths.py` | Assert `docs/handoffs` instead of `.claude/handoffs` |
| `tests/test_cleanup.py` | Remove handoff pruning tests; keep session-state tests |
| `tests/test_quality_check.py` | Assert `docs/handoffs` pattern matching |
| `tests/test_search.py` | `.archive` → `archive` |
| `tests/test_triage.py` | `.archive` → `archive` |
| `tests/test_distill.py` | `.archive` → `archive` |

### Outside the plugin

| File | Change |
|------|--------|
| `.gitignore` | Remove `.claude/handoffs/` entry |
| `.claude/settings.json` | Remove `**/.claude/handoffs/**` from `GITFLOW_ALLOW_FILES` (`**/docs/**` already covers `docs/handoffs/`) |
| `.claude/hooks/test_require_gitflow.py` | Update test to use `docs/handoffs` path |
| `.claude/skills/changelog/SKILL.md` | Update archive path reference |
| `.claude/skills/changelog/references/entry-writing.md` | Update archive path reference |

### Not changed (historical)

Files in `docs/superpowers/plans/`, engram specs, and `.planning/` reference old paths but are historical records. Updating them would misrepresent what was true when they were written.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Session-state files stay global | Ephemeral (24h TTL), session-scoped, not project content |
| No automated migration | Old handoffs at `.claude/handoffs/` are gitignored and disposable; `docs/handoffs/` already has one old file from Feb |
| No auto-pruning | Deleting committed files contradicts permanent-record goal |
| Auto-commit on all state changes | Full git lifecycle: create and archive both tracked |
| Narrow commits (one file) | Avoid sweeping in unrelated staged work |
| `archive/` not `.archive/` | Git-tracked, visible — no reason to hide |
