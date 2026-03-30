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

**Directory bootstrapping:** on first `/save` or `/quicksave`, the skill creates `docs/handoffs/` (and `docs/handoffs/archive/` on first `/load`) via `mkdir -p` if they don't exist. No `.gitkeep` needed — the directory gets committed with the first handoff file. The save skill already handles this pattern (check-and-create before writing).

Session-state files remain at `~/.claude/.session-state/` (ephemeral, session-scoped).

### Git integration

Every handoff state change gets its own commit:

| Operation | Trigger | Commit message | Files |
|-----------|---------|----------------|-------|
| Create | `/save`, `/quicksave` | `docs(handoff): save <title>` | `docs/handoffs/<filename>.md` |
| Archive | `/load` | `docs(handoff): archive <filename>` | Move from `docs/handoffs/` to `docs/handoffs/archive/` |

**Responsibility split:** the skill owns file operations (write, move); `auto_commit.py` owns only the commit.

`scripts/auto_commit.py` (~30 lines):

1. Checks git state (detached HEAD, rebase in progress, no git repo)
2. Stages only the specified file(s) — or accepts `--staged` when files are already staged
3. Commits with the provided message and Claude's author identity
4. Returns success/failure with a human-readable reason

**Create flow:** skill writes file → calls `auto_commit.py <file> "<message>"`

**Archive flow:** skill runs `git mv source dest` (stages automatically) → calls `auto_commit.py --staged "<message>"`. If `git mv` fails (file is untracked — e.g., loaded from legacy location at `.claude/handoffs/`, which is gitignored), skill falls back to `mv` + calls `auto_commit.py <new_path> "<message>"` to stage only the destination. The source deletion is invisible to git since it was gitignored — only the new file at `docs/handoffs/archive/` gets staged and committed.

Edge cases (enforced by `auto_commit.py`, not skill prose):

| Situation | Behavior |
|-----------|----------|
| Detached HEAD / rebase in progress | Skip commit, warn: "Handoff saved but not committed — resolve git state first" |
| Dirty index (other staged files) | Commit only the handoff file (`git add <specific file>`, not `git add -A`) |
| No git repo | Skip commit, warn user |

Commit authorship: uses the user's existing git config as-is. No magic identity injection. If the user wants Claude-attributed commits, they configure their git author settings accordingly.

The `docs(handoff):` commit prefix enables git log filtering:

```bash
git log --invert-grep --grep='docs(handoff):'   # hide handoff commits
git log --grep='docs(handoff):'                   # show only handoff commits
```

When multiple branches save handoffs concurrently, the unique timestamp filenames prevent merge conflicts (additive, no content overlap).

### Retention model

Auto-pruning is disabled for `docs/handoffs/`. The archive accumulates; git history is the lifecycle manager.

| Aspect | Previous | New |
|--------|----------|-----|
| Active retention | 30-day auto-prune | No auto-prune |
| Archive retention | 90-day auto-prune | No auto-prune |
| Session-state files | 24h auto-prune | 24h auto-prune (unchanged) |
| Cleanup mechanism | SessionStart hook | Manual (user deletes + commits) |

The `cleanup.py` SessionStart hook prunes session-state files only and stops touching handoff/archive directories.

At ~200+ archived files, linear search in `/search` and `/triage` may slow noticeably. Users can prune manually (`trash docs/handoffs/archive/2025-*.md && git add -A docs/handoffs/archive/ && git commit -m "docs(handoff): prune old archives"`) or filter by date range in `/search`.

## Code Change Scope

### Handoff plugin (`packages/plugins/handoff/`)

**Path changes** (`.claude/handoffs` → `docs/handoffs`, `.archive` → `archive`):

| File | Changes |
|------|---------|
| `scripts/project_paths.py` | `get_handoffs_dir()` returns `root/docs/handoffs`; add `get_legacy_handoffs_dir()` returning `root/.claude/handoffs` |
| `scripts/cleanup.py` | Remove `get_project_root()`, `get_handoffs_dir()`, and `prune_old_handoffs()`; rewrite `main()` to call only `prune_old_state_files()` (remove the two `prune_old_handoffs()` calls at lines 126-129). Keep `_trash()` — it's used by `prune_old_state_files()` |
| `scripts/auto_commit.py` | **New file.** Testable git commit logic (~30 lines): check state, stage file, commit with message |
| `scripts/quality_check.py` | `is_handoff_path()` matching rule and `.archive` → `archive` rename (see below) |
| `scripts/search.py` | `.archive` → `archive` |
| `scripts/triage.py` | `.archive` → `archive` |
| `references/handoff-contract.md` | Storage location, archive path, retention policy |
| `references/format-reference.md` | Storage location, archive path, retention policy |
| `README.md` | Path references, retention table, gitignore note |
| `CHANGELOG.md` | New entry |

**Skill updates** (path changes + git commit steps + frontmatter):

| Skill | Path changes | Git additions | Frontmatter |
|-------|-------------|---------------|-------------|
| `save/SKILL.md` | ~18 path refs | Add `auto_commit.py` call after file write | Add `Bash` to `allowed-tools` |
| `load/SKILL.md` | ~12 path refs | Add `auto_commit.py` call after archive move; add legacy fallback (see below) | Add `Bash` to `allowed-tools` |
| `quicksave/SKILL.md` | Path refs | Add `auto_commit.py` call after file write | Add `Bash` to `allowed-tools` |
| `distill/SKILL.md` | Path refs | None (reads only) | None |

**Why `Bash` in `allowed-tools`:** skills call `auto_commit.py` and `git mv` via shell execution. Without `Bash` in `allowed-tools`, every `/save` and `/load` triggers a permission prompt — trading one friction point (`.claude/` write prompt) for another (Bash prompt). Adding `Bash` to `allowed-tools` auto-approves these calls.

**Alternative considered:** PostToolUse hook on `Write` that auto-commits when the path matches `docs/handoffs/`. This would avoid the `Bash` dependency for creates, but the archive flow uses `git mv` (not `Write`), so the load skill still needs `Bash` regardless. One mechanism (`Bash` in `allowed-tools`) is simpler than two (hook for creates + `Bash` for archives).

**Test updates:**

| File | Changes |
|------|---------|
| `tests/test_project_paths.py` | Assert `docs/handoffs` instead of `.claude/handoffs`; add test for `get_legacy_handoffs_dir()` |
| `tests/test_cleanup.py` | Remove handoff pruning tests and path function tests; keep session-state tests |
| `tests/test_quality_check.py` | Assert `docs/handoffs` pattern matching; add near-miss test cases (see below) |
| `tests/test_auto_commit.py` | **New file.** Tests for git state checks, narrow staging, edge cases |
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

### Legacy location fallback

`project_paths.py` exports `get_legacy_handoffs_dir()` → `root/.claude/handoffs`. This gives scripts a testable function for the fallback path.

**Where the fallback logic lives:**

| Component | Fallback approach | Rationale |
|-----------|-------------------|-----------|
| `search.py` | Checks both directories (primary then legacy) | Script has directory scanning logic already; adding a second directory is natural |
| `triage.py` | Checks both directories (primary then legacy) | Same as search |
| `/load` skill | Bash `ls` on primary, then legacy if empty | Simple directory existence check — no edge cases that need a Python script |
| `quality_check.py` | **No fallback — matches `docs/handoffs/` only** | The plugin no longer writes to `.claude/handoffs/`. Quality check fires on `Write`, not on pre-existing files. Legacy files are read-only artifacts; validating them has no value. |

When handoffs are found at the legacy location, all three emit:

> "Found handoffs at legacy location `.claude/handoffs/`. Run `/save` to migrate — the next save will write to `docs/handoffs/`."

No automated file migration — the warning is self-documenting and the old files expire or get superseded naturally.

### `is_handoff_path()` matching rule

The current implementation walks `path.parts` looking for `.claude` → `handoffs` adjacency. The new rule:

**Match when `docs` and `handoffs` are adjacent path components, the file extension is `.md`, and the file is a direct child of `handoffs/` or `handoffs/archive/`.**

This also requires renaming the archive check inside `is_handoff_path()`: the current `if ".archive" in parts` becomes `if "archive" in parts` (same rename as `search.py` and `triage.py`).

Near-miss test cases:

| Path | Expected | Why |
|------|----------|-----|
| `<root>/docs/handoffs/2026-03-29.md` | Match | Active handoff |
| `<root>/docs/handoffs/archive/2026-03-29.md` | Match | Archived handoff |
| `<root>/docs/handoffs-v2/foo.md` | No match | `handoffs-v2` is not `handoffs` |
| `<root>/other-docs/handoffs/foo.md` | No match | `other-docs` is not `docs` |
| `<root>/docs/handoffs/foo.txt` | No match | Not `.md` |
| `<root>/docs/handoffs/subdir/deep/foo.md` | No match | Not direct child of `handoffs/` or `archive/` |

### Ordering constraint

All code changes, contract updates, reference doc updates, and skill updates land in a single commit. The handoff contract has runtime precedence over skill text — a stale contract with old paths would override correct skill text. Atomic commit prevents any window of contract-code disagreement.

Post-edit verification (run before committing):

```bash
# No stale path references in contract or format-reference
grep -r '\.claude/handoffs' packages/plugins/handoff/references/
# No stale archive references
grep -r '\.archive' packages/plugins/handoff/references/
# No stale retention periods
grep -rE '30.day|90.day' packages/plugins/handoff/references/
```

All three commands should return empty (no matches).

### Rollback

The atomic single-commit design makes rollback trivial: `git revert <commit>` undoes all changes. Committed handoff files remain in git history even after revert.

### Changelog skill pre-existing bug

The changelog skill references `~/.claude/handoffs/{project-name}/.archive/` — the global path from two migrations ago (pre-project-local). This design updates it to `docs/handoffs/archive/`, but the implementer should be aware this is a two-step jump, not a simple rename from the project-local path.

### Not changed (historical)

Files in `docs/superpowers/plans/`, engram specs, and `.planning/` reference old paths but are historical records. Updating them would misrepresent what was true when they were written.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Session-state files stay global | Ephemeral (24h TTL), session-scoped, not project content |
| No automated migration | Legacy fallback warns users; old files expire or get superseded naturally |
| No auto-pruning | Deleting committed files contradicts permanent-record goal |
| Auto-commit on all state changes | Full git lifecycle: create and archive both tracked |
| Narrow commits (one file) | Avoid sweeping in unrelated staged work |
| `archive/` not `.archive/` | Git-tracked, visible — no reason to hide |
| Git logic in `auto_commit.py`, not skill prose | Edge case checks (detached HEAD, dirty index, no git) must be testable; prose instructions are non-deterministic |
| `Bash` added to `allowed-tools` for save/load/quicksave | Skills call `auto_commit.py` and `git mv` via Bash; without auto-approval, every save/load prompts. PostToolUse hook alternative evaluated and declined (works for creates but not archives) |
| `quality_check.py` matches `docs/handoffs/` only, no legacy fallback | Plugin no longer writes to `.claude/handoffs/`; quality check fires on Write, not Read; legacy files are read-only artifacts |
| `**/.claude/handoffs/**` removed from `GITFLOW_ALLOW_FILES` | `**/docs/**` already covers `docs/handoffs/`; entry removed as part of docs/ migration (intentional, not accidental) |
| Atomic commit for all changes | Contract has runtime precedence over skill text; stale contract with old paths would override correct skills. Rollback via `git revert <commit>` |
| User's existing git config for authorship | No magic identity injection; user configures git author settings if they want Claude-attributed commits |
| Directory bootstrapping via `mkdir -p` in skills | No `.gitkeep` needed; directory committed with first handoff file |
