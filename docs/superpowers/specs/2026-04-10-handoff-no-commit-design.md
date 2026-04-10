# Handoff Plugin: Remove Auto-Commit, Gitignore Handoffs

Revert the git-tracked + auto-committed handoff model (from [2026-03-29-handoff-docs-storage-design.md](2026-03-29-handoff-docs-storage-design.md), currently unreleased) back to ephemeral local-only working memory. Keep the `docs/handoffs/` storage path; drop the commit layer entirely.

## Motivation

The git-tracked handoff model introduced recurring friction across every session:

1. **Feature-branch pollution.** `/save`, `/load`, and `/quicksave` auto-commit on whatever branch is checked out. When that branch is a feature branch with an open PR, handoff commits ride into the PR alongside the actual feature work. Reviewers see `docs(handoff): save <title>` commits mixed into a fix/refactor PR they're trying to review.
2. **Local `main` drift.** Handoff commits accumulate on local `main` but never push to `origin/main` (they're not part of any feature work). Any new feature branch cut from local `main` via the default `git checkout -b <name> main` inherits that drift silently — the new branch is ahead of `origin/main` by all the handoff commits that piled up locally.
3. **High-cost cleanup.** Undoing the pollution requires force-pushes, safety tags, and cross-validation of eventually-consistent `gh pr diff` output (which has a known stale-cache window after force-push). Cleanup takes more time and cognitive load than the original work.

PR #102 ([claude-code-tool-dev/pull/102](https://github.com/jpsweeney97/claude-code-tool-dev/pull/102)) hit all three modes in a single session: polluted from local main drift on creation, required a full rebuild via `git reset --hard origin/main` + cherry-pick + `git push --force-with-lease`, and during verification was temporarily mis-diagnosed as still-polluted due to stale `gh pr diff` cache — needing three-way cross-validation via raw API, `--json files`, and command re-run to confirm the rebuild had actually worked.

The recurring friction signal, not the one-off incident, is the justification for reversing the design decision.

## Current State

The handoff plugin is at version `1.5.0` (last shipped 2026-02-28). The `Unreleased` CHANGELOG block contains an in-flight migration from [2026-03-29-handoff-docs-storage-design.md](2026-03-29-handoff-docs-storage-design.md) that:

- Moved handoff storage from `<project_root>/.claude/handoffs/` (gitignored) to `<project_root>/docs/handoffs/` (tracked and auto-committed)
- Added `scripts/auto_commit.py` (80 lines, 159 lines of tests) to centralize the commit logic
- Invoked `auto_commit.py` from the `save`, `load`, and `quicksave` skill procedures

**This migration has not shipped yet.** Users on `1.5.0` still use the `.claude/handoffs/` (gitignored) layout. The auto-commit behavior exists only in `Unreleased`. That means this course-correction is reversing an in-flight decision *before* it reaches users, not breaking production behavior.

## Design

### Decision

Adopt **Option A** from brainstorming: gitignore handoffs and remove the auto-commit layer entirely. Keep the `docs/handoffs/` path, the frontmatter schema, the chain protocol, the quality-check hook, and every filesystem-based feature unchanged.

Alternatives considered and rejected:

| Alternative | Rejection reason |
|---|---|
| **Branch-aware commit** (only auto-commit when HEAD is `main` or an allowlisted branch) | Partial fix; still leaves footguns when switching branches mid-session |
| **Orphan `handoffs` branch** (commits go to a dedicated non-merging branch via `git --work-tree` plumbing) | Preserves git history but at real complexity cost. Users value (d) ephemeral working memory, so the history benefit doesn't justify the plumbing overhead |
| **Opt-in toggle** (env var or settings.json flag to disable auto-commit) | Doesn't fix the root cause — users have to remember to set the flag. Default-on behavior keeps the footgun in place |
| **Keep auto-commit but add prune/retention** | Addresses disk growth but not the core pollution vector |

### Storage model

```
<project_root>/
  docs/
    handoffs/                              # gitignored (ephemeral, local-only)
      2026-04-10_03-10_some-topic.md       # active handoff
      archive/                             # also gitignored
        2026-03-28_14-00_older-topic.md    # loaded/consumed handoffs
      .session-state/                      # already gitignored (24h TTL)
        handoff-<UUID>                     # chain protocol state file
```

| Aspect | Current (Unreleased) | After this refactor |
|---|---|---|
| `docs/handoffs/` git tracking | Tracked, auto-committed | **Gitignored** |
| `/save` behavior | Write file + commit on current branch | Write file only |
| `/load` behavior | `git mv` to archive + commit | Plain `mv` to archive |
| `/quicksave` behavior | Write checkpoint + commit | Write checkpoint only |
| `scripts/auto_commit.py` | Present (80 lines) | Deleted |
| `tests/test_auto_commit.py` | Present (159 lines) | Deleted |
| `docs/handoffs/archive/` retention | Forever (git-tracked, git dedups) | Forever (local disk, no auto-prune — disk is a non-issue at ~50KB/handoff) |

### What remains unchanged

Every filesystem-based capability continues working identically. The refactor removes the commit layer but touches nothing that walks the working tree directly:

| Feature | Mechanism | Impact |
|---|---|---|
| `/search` across active + archive | Python `open()` on files | Unchanged — gitignore is invisible to filesystem reads |
| `/distill` extraction from archive corpus | Python `open()` on files | Unchanged |
| Chain protocol via `resumed_from` | State file written to `.session-state/`, archive file moved to `archive/` | Unchanged — both still happen via `mv` and `write` |
| `/quicksave` checkpoint-streak guardrail | Walks the `resumed_from` chain reading archive files | Unchanged |
| `quality_check.py` PostToolUse hook | Fires on `Write` tool, validates frontmatter | Unchanged — independent of git state |
| `cleanup.py` SessionStart hook | Prunes `.session-state/` files >24h | Unchanged |
| `/list-handoffs` | Shell `ls` on `docs/handoffs/` | Unchanged |
| `/defer` ticket commits | Out of scope — tickets at `docs/tickets/` are durable project artifacts with their own commit path | Unchanged |

### What is removed

- `scripts/auto_commit.py` — the 80-line git-commit wrapper
- `tests/test_auto_commit.py` — its 159-line test suite
- Auto-commit bash blocks in `save/SKILL.md` step 8, `load/SKILL.md` step 5, `quicksave/SKILL.md` step 6
- The `git mv` + "fallback to plain `mv`" dual-path in `/load` collapses to a single `mv` (no tracked/untracked split)
- Mention of "git-tracked" from `README.md`, `handoff-contract.md`, and `CHANGELOG.md` Unreleased block

### Precedent

Two sibling storage locations are already gitignored and serve the same "ephemeral local-only" role:

- `.claude/sessions/` — explicitly gitignored in root `.gitignore` under the "Session data (ephemeral)" block
- `.claude/handoffs/` — gitignored by the same block (the legacy handoff location, before the `docs/handoffs/` migration)
- `docs/decisions/` — gitignored under the "Ephemeral" block

Gitignoring `docs/handoffs/` resolves an inconsistency: the old handoff location was gitignored, the new location (never-shipped) is tracked, and the global CLAUDE.md still documents `.claude/handoffs/` as gitignored. All three inputs point the same direction.

## File-by-file edit plan

### Deletions

| File | Size | Why |
|---|---|---|
| `packages/plugins/handoff/scripts/auto_commit.py` | 80 lines | No consumers after refactor |
| `packages/plugins/handoff/tests/test_auto_commit.py` | 159 lines | Tests code that no longer exists |

### Skill procedure edits

| File | Change |
|---|---|
| `packages/plugins/handoff/skills/save/SKILL.md` | **Step 8** — remove "Auto-commit the handoff" bash block and the "if commit fails, warn" sentence. Step 8 collapses to "Write file" |
| `packages/plugins/handoff/skills/load/SKILL.md` | **Step 5** — replace the `git mv` + auto-commit primary path and the "fallback to plain `mv`" secondary path with a single plain `mv`. Step 5 collapses to "Create `archive/` if needed; `mv` handoff into archive" |
| `packages/plugins/handoff/skills/quicksave/SKILL.md` | **Step 6** — remove "Auto-commit the checkpoint" bash block and "if commit fails, warn" sentence |

### Documentation updates

| File | Change |
|---|---|
| `packages/plugins/handoff/README.md` | Line ~77: change "No auto-prune (git-tracked)" → "No auto-prune (gitignored, local-only)". Scripts table (line ~59): remove the `auto_commit.py` row. Any other mention of "git-tracked" in the What-It-Does section gets updated for consistency |
| `packages/plugins/handoff/references/handoff-contract.md` | Add a "Git tracking" section explicitly stating handoffs are filesystem-local and gitignored. Storage table retention columns stay the same (still "No auto-prune") |
| `packages/plugins/handoff/CHANGELOG.md` | **Strategy C3 (consolidate)** — rewrite the `Unreleased` block so it tells one coherent story: handoffs moved `.claude/handoffs/` → `docs/handoffs/`, remain gitignored, are never auto-committed. Delete the `auto_commit.py` Added entry entirely. Soften BREAKING language — this never shipped, so it's not a breaking change against production |

### Repo-level

| File | Change |
|---|---|
| `.gitignore` (root) | Add `docs/handoffs/` under the "Ephemeral" section (next to `docs/decisions/`) |

### Migration (one-time git operation)

| Step | Command | Effect |
|---|---|---|
| Un-track existing archives | `git rm --cached docs/handoffs/archive/*.md` (or `git rm --cached -r docs/handoffs/` for future-proofing against nesting) | Removes ~30+ files from the index. Working copy untouched. Files become untracked + gitignored in one commit |
| Verify migration complete | `git ls-files docs/handoffs/` returns empty | Confirms no lingering tracked files |

### Items deliberately NOT edited

- **`.claude-plugin/plugin.json`** — the version stays at `1.5.0`. This refactor joins the existing `Unreleased` block; the version bump happens at release time whenever the next release is cut, not as part of this refactor.

### Total scope

**7 files edited (including root `.gitignore`), 2 files deleted, 1 migration commit.**

## Execution sequence

### Branch strategy

The refactor lives on a **new branch `feature/handoff-no-commit`** cut from a clean `origin/main`. PR #102 (the T-04 fix, already clean at origin) continues independently. Zero file overlap — PR #102 edits `packages/plugins/codex-collaboration/scripts/clean_stale_shakedown.py`; the refactor edits `packages/plugins/handoff/*`. Whichever merges first, the other rebases trivially.

### Phase 2 — One-shot cleanup of current pollution (local-only, no force-push)

The current working tree has residual pollution that this refactor also cleans up:

- Local `main` is ahead of `origin/main` by 14 unpushed handoff commits
- Current fix branch (`fix/clean-stale-shakedown-script-conventions`) is ahead of origin by 2 unpushed commits: `05f5b269` (handoff save) + `d2f77360` (this session's `/load` archive)
- Plus the design doc commit on fix branch (this file), which needs preservation

Phase 2 resets both branches to their origin state. All operations are local-only — no force-pushes to any remote.

#### Safety tags (before any reset)

| Tag | Preserves |
|---|---|
| `backup-fix-refactor-pre-reset` | Current fix branch tip (with handoff save + archive commit + design doc commit) |
| `backup-main-refactor-pre-reset` | Current local main tip (14 unpushed handoff commits) |

The three existing backup tags (`backup-main-pre-b4-rebase`, `backup-pr102-polluted`, `backup-t04-b39d8d90`) are untouched.

#### Phase 2 sequence

```bash
# On fix/clean-stale-shakedown-script-conventions
git tag backup-fix-refactor-pre-reset
git fetch origin

# Cherry-pick the design doc commit to a temporary location before reset
# (see "Design doc preservation" below)

git reset --hard origin/fix/clean-stale-shakedown-script-conventions
# HEAD should now be 8649ef04 (clean T-04 fix)

git checkout main
git tag backup-main-refactor-pre-reset
git reset --hard origin/main
# Local main should now match origin/main exactly
```

#### Design doc preservation through Phase 2a

The design doc (this file) is committed on the fix branch during brainstorming. Phase 2a's `git reset --hard` would drop that commit, so it must be preserved before the reset.

**Preservation path:** Before running Phase 2a, create the feature branch from `origin/main` and cherry-pick the design doc commit onto it. The design doc then lives permanently on the feature branch; the fix branch reset drops nothing of value.

```bash
# Record the design doc commit SHA while still on fix branch
DESIGN_SHA=$(git log --oneline --format=%H docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md | head -1)

# Create the feature branch from a clean origin/main
git checkout -b feature/handoff-no-commit origin/main

# Cherry-pick the design doc commit onto the feature branch
git cherry-pick "$DESIGN_SHA"

# Switch back to fix branch for Phase 2a
git checkout fix/clean-stale-shakedown-script-conventions
```

If cherry-pick fails for any reason, fall back to copying the file to `/tmp/` before the reset and restoring it as an untracked file on the feature branch afterward. The implementation plan covers both paths.

#### File impact of Phase 2a

The handoff file at `docs/handoffs/archive/2026-04-10_03-10_pr-102-rebuilt-clean-after-t04-scrutiny-cycle.md` will be removed from disk by the reset (it exists only in the commits being dropped). Content is recoverable via `git show backup-fix-refactor-pre-reset:docs/handoffs/archive/2026-04-10_03-10_pr-102-rebuilt-clean-after-t04-scrutiny-cycle.md`. User chose to accept the deletion during brainstorming — the handoff was already loaded into this session's context and the tag provides a complete recovery path.

### Phase 1 — Refactor on fresh feature branch

After Phase 2:

```bash
# If the feature branch doesn't exist yet (alternative preservation path):
git checkout -b feature/handoff-no-commit origin/main

# Otherwise the feature branch already exists from the design-doc preservation step
git checkout feature/handoff-no-commit
```

**Commit structure — 3 logical commits for reviewability:**

| # | Commit | Files |
|---|---|---|
| 1 | `chore(handoff): gitignore handoffs and un-track existing archives` | Root `.gitignore` + `git rm --cached docs/handoffs/archive/*.md` |
| 2 | `refactor(handoff): remove auto-commit from save/load/quicksave` | Delete `auto_commit.py`, delete `test_auto_commit.py`, edit 3 SKILL.md files |
| 3 | `docs(handoff): update README, contract, CHANGELOG for local-only model` | `README.md`, `handoff-contract.md`, `CHANGELOG.md` |

Run `cd packages/plugins/handoff && uv run pytest` between commits. Only `test_auto_commit.py` should be missing from the suite after commit #2 — all other tests should continue passing.

Squashing to a single commit is also acceptable if the reviewer prefers a tighter PR. The 3-commit structure just helps walk the reviewer through the change.

### Push + PR

```bash
git push -u origin feature/handoff-no-commit
gh pr create --title "refactor(handoff): gitignore handoff files, remove auto-commit" --body "..."
```

PR body draft is in the CHANGELOG strategy section below.

### Timeline summary

| Step | What | Risk level |
|---|---|---|
| 1 | Create safety tags | Zero |
| 2 | Cherry-pick design doc to feature branch | Low |
| 3 | Phase 2a — reset fix branch | Low (local only, tagged) |
| 4 | Phase 2b — reset local main | Low (local only, tagged) |
| 5 | Phase 1 edits on feature branch | Low (isolated, testable) |
| 6 | Push + open refactor PR | Low (additive) |
| 7 | PR #102 merges independently | Unchanged |
| 8 | Refactor PR merges | Low (reviewed) |

Every destructive operation in Phase 2 is a *local* reset with a backup tag covering it. No force-pushes anywhere in this plan.

## Edge cases and risks

### Edge cases

| Case | Handling |
|---|---|
| Stranded `2026-04-09_01-37_t4-publication-and-security-review.md` untracked file (mentioned in prior-session handoff risks) | Handled automatically — after the `.gitignore` entry lands, this file becomes implicitly gitignored and stops drifting across sessions |
| `git rm --cached` on a flat vs. nested archive | Current structure is flat; `docs/handoffs/archive/*.md` works. `-r` flag future-proofs against nesting |
| Tests that import `auto_commit` | Only `tests/test_auto_commit.py` references it (verified via grep). Other test files do not touch it |
| PostToolUse `quality_check.py` hook | Fires on `Write`, not git. Unchanged |
| SessionStart `cleanup.py` hook | Prunes `.session-state/` only. Unchanged |
| `/search` and `/distill` on gitignored files | They read via filesystem; gitignore status invisible to them |
| Chain protocol + `resumed_from` | State file is filesystem-based; archive file is filesystem-based. Unchanged |
| `/quicksave` checkpoint-streak guardrail | Walks chain via Python `open()`. Unchanged |
| Merge conflicts with PR #102 | Zero file overlap. No conflicts possible |
| Other branches with lingering handoff commits | Untouched. They retain their history; future `/save` on them writes files without committing |
| Users of the plugin on other machines | Get new version on next plugin update. Existing tracked archive files become un-tracked on pull; files stay on disk |

### Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Phase 2 reset drops a needed file | Low | Safety tags preserve everything. Recoverable via `git show <tag>:path` or `git checkout <tag> -- path` |
| Forgetting to add `docs/handoffs/` to `.gitignore` | Low | Phase 1 commit #1 is literally that edit — if this commit is missing, nothing else makes sense |
| `git rm --cached` accidentally removes files from disk | Zero | `--cached` only removes from index; working tree is untouched. Well-known safe operation |
| Reviewer pushback on design decision | Medium | Mitigated by: the gitignore precedents, the never-shipped status of the reversed decision, and the explicit rollback path. Revert is a single PR |
| Plugin tests break after deletion | Low | Run `pytest` between commits. Only `test_auto_commit.py` is expected to be missing |
| Hook breakage | Very low | Neither `quality_check.py` nor `cleanup.py` touches commit logic |

## Verification

| # | Check | Expected |
|---|---|---|
| 1 | `git status` clean on feature branch before Phase 1 commits | Working tree clean |
| 2 | After commit #1: `git ls-files docs/handoffs/` | Empty output |
| 3 | After commit #2: `ls packages/plugins/handoff/scripts/auto_commit.py` | Not found |
| 4 | After commit #2: `grep -r auto_commit packages/plugins/handoff/skills/` | No matches |
| 5 | After commit #3: `grep -i "git-tracked" packages/plugins/handoff/README.md` | No matches (or contextual mention only) |
| 6 | `cd packages/plugins/handoff && uv run pytest` | All tests pass; only `test_auto_commit.py` missing |
| 7 | End-to-end `/save` smoke test (post-merge, fresh session) | Handoff file written; `git status` shows untracked; no commit created |
| 8 | End-to-end `/load` smoke test | Archive moved via `mv`; file on disk; no commit created |
| 9 | `/quicksave` smoke test + chain walk | Checkpoint written; `resumed_from` populated; guardrail fires after 3 consecutive |
| 10 | `gh pr diff --name-only feature/handoff-no-commit` | Shows only intended files |
| 11 | PR body documents the course-correction | Manual check |

## Rollback

| Stage | Rollback |
|---|---|
| Before Phase 2a | Nothing to roll back |
| After Phase 2a | `git reset --hard backup-fix-refactor-pre-reset` |
| After Phase 2b | `git checkout main && git reset --hard backup-main-refactor-pre-reset` |
| Phase 1 uncommitted | `git checkout .` on feature branch |
| Phase 1 committed but PR not merged | `git branch -D feature/handoff-no-commit` after switching off |
| Refactor PR merged and regretted | `gh pr revert`. Re-tracking old archives (if desired) requires manual `git checkout <pre-merge-commit> -- docs/handoffs/archive/` |

## CHANGELOG and PR communication

### CHANGELOG strategy: C3 (consolidate)

Rewrite the existing Unreleased block so it tells one coherent story: handoffs moved `.claude/handoffs/` → `docs/handoffs/`, remain gitignored, are never auto-committed. The `auto_commit.py` Added entry is deleted entirely — it never shipped.

Rationale: the CHANGELOG's audience is users reading release notes, not developers tracking decision evolution. The flip belongs in git history and this design doc. Since the reversed decision never reached users, retroactive consolidation doesn't mislead anyone.

### Draft CHANGELOG Unreleased block (post-refactor)

```markdown
## [Unreleased]

### Changed
- **BREAKING:** Handoff storage moved from `<project_root>/.claude/handoffs/`
  to `<project_root>/docs/handoffs/`. Handoffs remain local-only working
  memory (gitignored, not committed). Archive renamed from `.archive/` to
  `archive/`. `search.py` and `triage.py` fall back to the legacy
  `.claude/handoffs/` location for projects still on the old layout.
- Cleanup hook (`cleanup.py`) prunes session-state files (24h TTL) only.
  Handoff files are never auto-pruned.
- `is_handoff_path()` matches `docs/handoffs/` (active and archived).

### Added
- `get_legacy_handoffs_dir()` in `project_paths.py` for fallback discovery.
- `Bash` added to `allowed-tools` for save, load, quicksave skills.
- Legacy-layout fallback warning.

### Fixed
- (existing entries unchanged)
```

### Draft PR body

```markdown
# refactor(handoff): gitignore handoff files, remove auto-commit

## Why

Handoffs were previously auto-committed on whatever branch was checked out,
which caused recurring friction across sessions:

- Handoff commits landed on feature branches, polluting open PRs (e.g., PR #102
  needed a full rebuild mid-session after 14 handoff commits rode along from
  stale local main).
- Local main accumulated unpushed handoff commits that contaminated any
  feature branch cut from it via the default `git checkout -b`.
- Cleanup required force-pushes, safety tags, and cross-validation of
  eventually-consistent PR diffs.

The git-tracked behavior was part of an in-flight unreleased migration. This
PR course-corrects before that release ships.

## What changes

- `docs/handoffs/` is gitignored (joins `docs/decisions/` and `.claude/sessions/`
  as ephemeral local-only state).
- `/save`, `/load`, `/quicksave` no longer commit — they write/move files only.
- `scripts/auto_commit.py` and its test are deleted (~240 lines).
- ~30 previously-tracked archive files are un-tracked via `git rm --cached`.
- README, contract, and CHANGELOG updated to reflect local-only semantics.

## What's preserved

- `/search` across active + archive (filesystem-based, gitignore-invariant).
- `/distill` extraction from archive corpus.
- Chain protocol via `resumed_from` and state files.
- `/quicksave` checkpoint-streak guardrail.
- `quality_check.py` frontmatter/section validation on write.
- `cleanup.py` session-state TTL pruning.
- `/defer` ticket commits (out of scope — tickets are durable project artifacts).

## Migration

Pulling this PR un-tracks existing archive files on disk (content preserved,
no longer in git). Future handoffs are written but not committed. No user
action required unless you want to manually prune on-disk archives.

## Testing

- `cd packages/plugins/handoff && uv run pytest` — all tests pass
- `git ls-files docs/handoffs/` returns empty after migration commit
- `grep -r auto_commit packages/plugins/handoff/` returns no hits after deletion

## Rollback

`gh pr revert` reverses all three commits. Archive files would need manual
`git checkout` restoration if re-tracking is desired.
```

## Items to verify at implementation time

Non-design-blocking verifications to perform during the implementation pass:

1. **Grep once more for `auto_commit` across the whole repo** (not just the plugin dir) to catch any consumer missed during design exploration
2. **Confirm `docs/handoffs/archive/` remains flat, not nested** — adjust the `git rm --cached` glob accordingly if nested
3. **Confirm `turbo-mode` marketplace metadata** doesn't need a change beyond the plugin's own version bump (which happens at release time, not now)
4. **Confirm no other tests import `auto_commit`** beyond `test_auto_commit.py`
5. **Double-check the `/load` skill's SKILL.md** doesn't have any residual mentions of `git mv` or `auto_commit.py` after the edit

## Open questions

None blocking design finalization. All decisions were resolved during brainstorming:

- ✅ Option A chosen over B/C/D (branch-aware, orphan branch, opt-in toggle)
- ✅ Keep archive dir forever, no prune (disk is a non-issue)
- ✅ Phase 1 + Phase 2 bundled (not forward-only)
- ✅ File deletion during Phase 2a accepted (P1 — backup tag provides recovery)
- ✅ CHANGELOG strategy C3 (consolidate)
- ✅ Version stays at `1.5.0`; refactor joins existing Unreleased block

## References

- Previous spec being course-corrected: [2026-03-29-handoff-docs-storage-design.md](2026-03-29-handoff-docs-storage-design.md)
- Triggering incident: PR #102 rebuild ([GitHub #102](https://github.com/jpsweeney97/claude-code-tool-dev/pull/102))
- Last-session handoff documenting the incident: `docs/handoffs/archive/2026-04-10_03-10_pr-102-rebuilt-clean-after-t04-scrutiny-cycle.md` (will be deleted in Phase 2a; recoverable via backup tag)
- Plugin source: `packages/plugins/handoff/`
- Relevant auto-commit call sites:
  - `packages/plugins/handoff/skills/save/SKILL.md` — step 8
  - `packages/plugins/handoff/skills/load/SKILL.md` — step 5
  - `packages/plugins/handoff/skills/quicksave/SKILL.md` — step 6
- Root `.gitignore` precedent entries: `docs/decisions/`, `.claude/sessions/`, `.claude/handoffs/`
