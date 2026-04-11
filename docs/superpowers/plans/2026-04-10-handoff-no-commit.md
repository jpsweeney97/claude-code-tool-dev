# Handoff No-Commit Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gitignore `docs/handoffs/` and remove the auto-commit layer from the handoff plugin so handoffs become ephemeral local-only working memory; bundle a one-shot cleanup of current local pollution (14 unpushed commits on local main, 3 on the fix branch).

**Architecture:** Delete `scripts/auto_commit.py` + its test, strip auto-commit bash blocks from the three skill procedures (save/load/quicksave), update README + contract + CHANGELOG, add `docs/handoffs/` to the repo `.gitignore`, and un-track existing archive files via `git rm --cached`. Work on a fresh `feature/handoff-no-commit` branch cut from clean `origin/main`. The design doc commit currently on the fix branch is preserved via cherry-pick to the feature branch before Phase 2a resets the fix branch. All destructive operations in Phase 2 are local-only resets with backup tags — no force-push anywhere.

**Tech Stack:** Python 3.11+ (handoff plugin), pytest (test runner via `uv run pytest`), Keep a Changelog format, Git (with PreToolUse branch protection hook), Bash, GitHub CLI (`gh`) for PR creation.

**Spec:** `docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md`

---

## File Structure

### Files deleted
- `packages/plugins/handoff/scripts/auto_commit.py` (80 lines — the commit wrapper)
- `packages/plugins/handoff/tests/test_auto_commit.py` (159 lines — its test suite)

### Files modified
- `.gitignore` (root) — add `docs/handoffs/` under the "Ephemeral" section
- `packages/plugins/handoff/skills/save/SKILL.md` — step 8: remove auto-commit bash block
- `packages/plugins/handoff/skills/load/SKILL.md` — step 5: collapse dual `git mv`/fallback to a single plain `mv`
- `packages/plugins/handoff/skills/quicksave/SKILL.md` — step 6: remove auto-commit bash block
- `packages/plugins/handoff/README.md` — remove `auto_commit.py` row from scripts table, update "git-tracked" claims, remove/update line ~83 sentence
- `packages/plugins/handoff/references/handoff-contract.md` — add a new "Git Tracking" section after Storage
- `packages/plugins/handoff/CHANGELOG.md` — rewrite Unreleased block per strategy C3 (consolidate)

### Files intentionally NOT edited
- `packages/plugins/handoff/.claude-plugin/plugin.json` — version stays at `1.5.0`; the refactor joins the existing Unreleased cluster, version bump happens at release time
- `packages/plugins/handoff/skills/defer/SKILL.md` — `/defer` uses its own git commit logic for tickets, out of scope

### Commit structure
- **Commit 1:** `chore(handoff): gitignore handoffs and un-track existing archives` — `.gitignore` + `git rm --cached`
- **Commit 2:** `refactor(handoff): remove auto-commit from save/load/quicksave` — delete `auto_commit.py` + `test_auto_commit.py` + edit 3 SKILL.md files
- **Commit 3:** `docs(handoff): update README, contract, CHANGELOG for local-only model` — README + handoff-contract + CHANGELOG

### Branch strategy
- New feature branch: `feature/handoff-no-commit` cut from clean `origin/main`
- Design doc (committed as `5a1b7edb` on fix branch) preserved via cherry-pick onto feature branch before Phase 2a
- Phase 2a: reset `fix/clean-stale-shakedown-script-conventions` to its origin tip (`8649ef04`)
- Phase 2b: reset local `main` to `origin/main`
- Safety tags: `backup-fix-refactor-pre-reset`, `backup-main-refactor-pre-reset`

---

## Pre-flight and Safety Phase

### Task 1: Pre-flight verification

**Files:** (read-only)
- Verify: `.git/refs/heads/`, `docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md`

- [ ] **Step 1: Verify current branch**

Run: `git branch --show-current`
Expected: `fix/clean-stale-shakedown-script-conventions`

If the branch is different, STOP and switch to that branch before continuing.

- [ ] **Step 2: Verify fix-branch unpushed commits**

Run: `git log --oneline origin/fix/clean-stale-shakedown-script-conventions..HEAD`
Expected: exactly 3 commits, top to bottom:
```
5a1b7edb docs(spec): add handoff no-commit refactor design
d2f77360 docs(handoff): archive 2026-04-10_03-10_pr-102-rebuilt-clean-after-t04-scrutiny-cycle.md
05f5b269 docs(handoff): save PR #102 rebuilt clean after T-04 scrutiny cycle
```

If the list is different (more or fewer commits), STOP. The plan assumes these specific commits. Investigate and update the plan before proceeding.

- [ ] **Step 3: Verify local main has unpushed handoff commits**

Run: `git log --oneline origin/main..main | wc -l`
Expected: `14` (or thereabouts — the exact count is not critical, but there should be multiple)

- [ ] **Step 4: Verify the design doc exists and is committed**

Run: `git log --oneline -1 -- docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md`
Expected: output starts with `5a1b7edb` and subject `docs(spec): add handoff no-commit refactor design`

- [ ] **Step 5: Verify no backup tags exist yet from this refactor**

Run: `git tag --list 'backup-fix-refactor-pre-reset' 'backup-main-refactor-pre-reset'`
Expected: empty output (both tags absent)

If either tag already exists, STOP. This means a prior execution of this plan left state behind. Investigate before re-running.

- [ ] **Step 6: Verify working tree is clean (other than untracked files)**

Run: `git status --short | grep -v '^??'`
Expected: empty output (no staged or modified tracked files)

Untracked files are OK — they'll be ignored by the operations in this plan.

- [ ] **Step 7: Count currently-tracked handoff files (baseline for Commit 1 verification)**

Run: `git ls-files docs/handoffs/ | wc -l`
Expected: approximately `55` (or a similar number). Record this number — after Commit 1 it should be `0`.

- [ ] **Step 8: Run baseline test suite**

Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -5`
Expected: all tests pass (e.g., "354 passed" or similar). Record the total test count — after Commit 2 it should decrease by exactly the number of tests in `test_auto_commit.py`.

If any tests fail at baseline, STOP. The refactor should not be run on a broken baseline.

- [ ] **Step 9: Record test count from test_auto_commit.py (for later comparison)**

Run: `cd packages/plugins/handoff && uv run pytest tests/test_auto_commit.py --collect-only -q 2>&1 | tail -3`
Expected: a count like "12 tests collected" (or similar). Record this number — after Commit 2, total tests should decrease by exactly this amount.

---

### Task 2: Create safety tags

**Files:** (git refs)
- Create: `.git/refs/tags/backup-fix-refactor-pre-reset`
- Create: `.git/refs/tags/backup-main-refactor-pre-reset`

- [ ] **Step 1: Tag current fix-branch HEAD**

Run: `git tag backup-fix-refactor-pre-reset`
Expected: no output (silent success)

- [ ] **Step 2: Verify fix-branch tag points at design doc commit**

Run: `git rev-parse backup-fix-refactor-pre-reset`
Expected: `5a1b7edb` (or full SHA starting with this prefix)

- [ ] **Step 3: Fetch origin to make sure we have the latest refs**

Run: `git fetch origin`
Expected: output showing fetched refs, or silent if already up-to-date

- [ ] **Step 4: Switch to main and tag it**

Run: `git checkout main && git tag backup-main-refactor-pre-reset`
Expected: "Switched to branch 'main'" followed by no output from tag

- [ ] **Step 5: Verify both tags exist**

Run: `git tag --list 'backup-*-refactor-pre-reset'`
Expected:
```
backup-fix-refactor-pre-reset
backup-main-refactor-pre-reset
```

- [ ] **Step 6: Return to fix branch**

Run: `git checkout fix/clean-stale-shakedown-script-conventions`
Expected: "Switched to branch 'fix/clean-stale-shakedown-script-conventions'"

**Rollback (if anything in later tasks fails):** These tags preserve the full state. Recovery commands:
- Fix branch: `git checkout fix/clean-stale-shakedown-script-conventions && git reset --hard backup-fix-refactor-pre-reset`
- Main: `git checkout main && git reset --hard backup-main-refactor-pre-reset`

---

### Task 3: Create feature branch and cherry-pick the design doc

**Files:** (new branch)
- Create: `.git/refs/heads/feature/handoff-no-commit`
- Preserve: `docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md` on the feature branch

- [ ] **Step 1: Record the design doc commit SHA into a variable**

Run: `DESIGN_SHA=$(git log --oneline --format=%H -1 -- docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md) && echo "$DESIGN_SHA"`
Expected: full SHA starting with `5a1b7edb`

- [ ] **Step 2: Create the feature branch from clean origin/main**

Run: `git checkout -b feature/handoff-no-commit origin/main`
Expected: "Switched to a new branch 'feature/handoff-no-commit'" followed by "branch 'feature/handoff-no-commit' set up to track 'origin/main'"

- [ ] **Step 3: Verify we're on the feature branch at origin/main's tip**

Run: `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git rev-parse origin/main`
Expected: first line `feature/handoff-no-commit`, next two SHAs identical

- [ ] **Step 4: Cherry-pick the design doc commit**

Run: `git cherry-pick "$DESIGN_SHA"`
Expected: output like "[feature/handoff-no-commit <new-sha>] docs(spec): add handoff no-commit refactor design" with 1 file changed

**If cherry-pick fails:** Run `git cherry-pick --abort`, then fall back to the `/tmp/` preservation path:
```bash
git checkout fix/clean-stale-shakedown-script-conventions
cp docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md /tmp/handoff-no-commit-design.md.bak
git checkout feature/handoff-no-commit
mkdir -p docs/superpowers/specs
cp /tmp/handoff-no-commit-design.md.bak docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md
git add docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md
git commit -m "docs(spec): add handoff no-commit refactor design"
```

- [ ] **Step 5: Verify the design doc is present on the feature branch**

Run: `ls docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md && wc -l docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md`
Expected: path echoed, and `439` lines (or close — within ±5 is fine)

- [ ] **Step 6: Return to fix branch for Phase 2a**

Run: `git checkout fix/clean-stale-shakedown-script-conventions`
Expected: "Switched to branch 'fix/clean-stale-shakedown-script-conventions'"

---

## Cleanup Phase (Phase 2 — reset current pollution)

### Task 4: Phase 2a — Reset fix branch to origin

**Files:** (branch state)
- Modify: `.git/refs/heads/fix/clean-stale-shakedown-script-conventions`

- [ ] **Step 1: Verify we're on the fix branch**

Run: `git branch --show-current`
Expected: `fix/clean-stale-shakedown-script-conventions`

- [ ] **Step 2: Verify origin fix-branch tip is 8649ef04**

Run: `git rev-parse --short origin/fix/clean-stale-shakedown-script-conventions`
Expected: `8649ef04` (or similar — matches the clean T-04 fix commit)

- [ ] **Step 3: Reset fix branch to origin**

Run: `git reset --hard origin/fix/clean-stale-shakedown-script-conventions`
Expected: "HEAD is now at 8649ef04 fix(shakedown): align clean_stale_shakedown conventions"

- [ ] **Step 4: Verify fix branch now matches origin exactly**

Run: `git log --oneline origin/fix/clean-stale-shakedown-script-conventions..HEAD`
Expected: empty output (branch is at origin, no unpushed commits)

- [ ] **Step 5: Verify design doc file was removed from disk (expected side effect)**

Run: `ls docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md 2>&1 || echo "absent (expected)"`
Expected: "absent (expected)" — the design doc is not on fix branch anymore (it lives on feature branch via cherry-pick)

**Rollback:** `git reset --hard backup-fix-refactor-pre-reset`

---

### Task 5: Phase 2b — Reset local main to origin

**Files:** (branch state)
- Modify: `.git/refs/heads/main`

- [ ] **Step 1: Switch to main**

Run: `git checkout main`
Expected: "Switched to branch 'main'"

If the PreToolUse branch protection hook fires on checkout (it shouldn't — the hook fires on Edit/Write, not checkout), STOP and investigate.

- [ ] **Step 2: Verify we're on main and it has unpushed commits**

Run: `git branch --show-current && git log --oneline origin/main..HEAD | wc -l`
Expected: first line `main`, second line `14` (or similar — non-zero)

- [ ] **Step 3: Reset main to origin**

Run: `git reset --hard origin/main`
Expected: output showing HEAD moved to origin/main's tip

- [ ] **Step 4: Verify main is clean**

Run: `git log --oneline origin/main..main`
Expected: empty output

- [ ] **Step 5: Switch to the feature branch for Phase 1 work**

Run: `git checkout feature/handoff-no-commit`
Expected: "Switched to branch 'feature/handoff-no-commit'"

**Rollback:** `git checkout main && git reset --hard backup-main-refactor-pre-reset && git checkout feature/handoff-no-commit`

---

### Task 6: Baseline on feature branch

**Files:** (read-only)

- [ ] **Step 1: Verify current branch**

Run: `git branch --show-current`
Expected: `feature/handoff-no-commit`

- [ ] **Step 2: Verify design doc is present (preserved via cherry-pick)**

Run: `ls docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md`
Expected: path echoed (file exists)

- [ ] **Step 3: Verify working tree is clean**

Run: `git status --short`
Expected: empty (or only untracked files unrelated to this refactor)

- [ ] **Step 4: Verify branch is one commit ahead of origin/main (the cherry-picked design doc)**

Run: `git log --oneline origin/main..HEAD`
Expected: exactly 1 line — the design doc commit (new SHA from cherry-pick)

- [ ] **Step 5: Run baseline tests on feature branch**

Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -5`
Expected: all tests pass. The count should match the Task 1 Step 8 baseline exactly (nothing has changed yet).

If tests fail here, STOP. The feature branch is supposed to be `origin/main` + design doc only — there should be no code changes yet.

- [ ] **Step 6: Return to repo root for subsequent tasks**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev`
Expected: silent

---

## Commit 1 — Gitignore and Un-track Archives

### Task 7: Edit .gitignore to add docs/handoffs/

**Files:**
- Modify: `/Users/jp/Projects/active/claude-code-tool-dev/.gitignore`

- [ ] **Step 1: Read the current .gitignore "Ephemeral" section**

Use Read on `.gitignore`. Look for lines 18-21:
```
# Ephemeral
tmp/
docs/decisions/
```

- [ ] **Step 2: Add `docs/handoffs/` to the Ephemeral section**

Use Edit on `.gitignore`:
- old_string:
```
# Ephemeral
tmp/
docs/decisions/
```
- new_string:
```
# Ephemeral
tmp/
docs/decisions/
docs/handoffs/
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n '^docs/handoffs/' .gitignore`
Expected: one line matching `docs/handoffs/` with a line number in the `Ephemeral` section range

- [ ] **Step 4: Verify gitignore is effective for a new file (sanity check)**

Run: `touch docs/handoffs/.test-ignore && git check-ignore -v docs/handoffs/.test-ignore && rm docs/handoffs/.test-ignore`
Expected: `.gitignore:<line>:docs/handoffs/  docs/handoffs/.test-ignore` then silent `rm`

Note: use `rm` here for the temporary test file (the global CLAUDE.md `trash` rule is for user-visible deletions; this is an inline sanity check of a file we just created and immediately remove). If you prefer, use `trash docs/handoffs/.test-ignore` instead.

---

### Task 8: Un-track existing archive files via git rm --cached

**Files:**
- Modify (index only): ~55 previously-tracked files under `docs/handoffs/archive/`. The working tree is not touched — `--cached` only removes entries from the git index.

- [ ] **Step 1: List all currently-tracked files under docs/handoffs/ for audit**

Run: `git ls-files docs/handoffs/ | head -20 && echo "..." && git ls-files docs/handoffs/ | wc -l`
Expected: list of 20 file paths plus a total count (~55)

- [ ] **Step 2: Un-track them (working tree preserved)**

Run: `git rm --cached -r docs/handoffs/`
Expected: output of the form `rm 'docs/handoffs/archive/2026-03-29_07-16_review-fix-merge-pr89-to-main.md'` (one line per file) repeated ~55 times

- [ ] **Step 3: Verify no tracked files remain under docs/handoffs/**

Run: `git ls-files docs/handoffs/`
Expected: empty output

- [ ] **Step 4: Verify the files are still on disk**

Run: `ls docs/handoffs/archive/ | head -5 && ls docs/handoffs/archive/ | wc -l`
Expected: 5 file names listed, then a count (~55 files still on disk). The `--cached` flag only touches the index, not the working tree.

- [ ] **Step 5: Inspect the staged changes before committing**

Run: `git status --short | head -10`
Expected: lines starting with `M  .gitignore` and `D  docs/handoffs/...` (55 deletions plus the gitignore edit)

- [ ] **Step 6: Commit**

Run:
```bash
git commit -m "$(cat <<'EOF'
chore(handoff): gitignore handoffs and un-track existing archives

Add docs/handoffs/ to the root .gitignore (under "Ephemeral") and
un-track all previously-committed handoff files via git rm --cached.
Working tree is untouched — files remain on disk as local-only state.

This is commit 1 of 3 in the handoff no-commit refactor. See:
docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: commit created with a line count delta matching "~55 files deleted (from index), 1 file changed (.gitignore), 1 insertion"

- [ ] **Step 7: Verify commit landed**

Run: `git log --oneline -1`
Expected: first line starts with a new SHA and subject `chore(handoff): gitignore handoffs and un-track existing archives`

- [ ] **Step 8: Verify git ls-files is empty for handoffs**

Run: `git ls-files docs/handoffs/`
Expected: empty output

- [ ] **Step 9: Verify tests still pass (nothing should have changed from pre-commit)**

Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -5 && cd /Users/jp/Projects/active/claude-code-tool-dev`
Expected: all tests pass, count unchanged from baseline

**Rollback (Commit 1 only):** `git reset --hard HEAD~1` (returns to the cherry-pick commit)

---

## Commit 2 — Remove auto-commit code

### Task 9: Delete auto_commit.py and its test

**Files:**
- Delete: `packages/plugins/handoff/scripts/auto_commit.py`
- Delete: `packages/plugins/handoff/tests/test_auto_commit.py`

- [ ] **Step 1: Delete auto_commit.py**

Run: `trash packages/plugins/handoff/scripts/auto_commit.py`
Expected: silent success

- [ ] **Step 2: Delete test_auto_commit.py**

Run: `trash packages/plugins/handoff/tests/test_auto_commit.py`
Expected: silent success

- [ ] **Step 3: Verify both files are gone**

Run: `ls packages/plugins/handoff/scripts/auto_commit.py packages/plugins/handoff/tests/test_auto_commit.py 2>&1`
Expected: both paths reported as "No such file or directory"

- [ ] **Step 4: Grep for any remaining references to auto_commit in the plugin**

Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/`, output_mode `files_with_matches`.
Expected: output should include only the SKILL.md files (save, load, quicksave) which still contain references — those will be edited in the next tasks.

Acceptable matches at this point:
```
packages/plugins/handoff/skills/save/SKILL.md
packages/plugins/handoff/skills/load/SKILL.md
packages/plugins/handoff/skills/quicksave/SKILL.md
```

If any other file matches (besides these three), STOP — there's an unexpected consumer that wasn't identified during design.

- [ ] **Step 5: Grep across the whole repo for any OTHER consumer of auto_commit (verification)**

Use Grep with pattern `auto_commit`, output_mode `files_with_matches`.
Expected: only the three SKILL.md files from Step 4, plus possibly the design doc and this plan file. No other consumers.

If there are unexpected hits, investigate before proceeding.

---

### Task 10: Edit save/SKILL.md — remove step 8 auto-commit block

**Files:**
- Modify: `packages/plugins/handoff/skills/save/SKILL.md:151-157`

- [ ] **Step 1: Read the current step 8 block**

Use Read on `packages/plugins/handoff/skills/save/SKILL.md` with `offset=149, limit=12` to see the current step 8 content and its surroundings.

Expected current content around line 151:
```
8. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_<slug>.md`

   **Auto-commit the handoff:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn: "Handoff saved but not committed — <reason>". The file is already written; only the commit is skipped.

9. **Cleanup state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
```

- [ ] **Step 2: Apply the edit**

Use Edit on `packages/plugins/handoff/skills/save/SKILL.md`:
- old_string:
```
8. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_<slug>.md`

   **Auto-commit the handoff:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn: "Handoff saved but not committed — <reason>". The file is already written; only the commit is skipped.

9. **Cleanup state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
```
- new_string:
```
8. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_<slug>.md`

   Handoffs are local-only working memory — the file is durable on disk but is not committed. See `references/handoff-contract.md` for the Git Tracking section.

9. **Cleanup state file** per chain protocol in [handoff-contract.md](../../references/handoff-contract.md):
```

- [ ] **Step 3: Verify the edit**

Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/skills/save/SKILL.md`.
Expected: no matches

---

### Task 11: Edit load/SKILL.md — collapse step 5 dual path to single mv

**Files:**
- Modify: `packages/plugins/handoff/skills/load/SKILL.md:128-142`

- [ ] **Step 1: Read the current step 5 block**

Use Read on `packages/plugins/handoff/skills/load/SKILL.md` with `offset=126, limit=20` to see the current step 5 block.

Expected current content (lines ~128-142):
```
5. **Archive the handoff:**
   - Create `<project_root>/docs/handoffs/archive/` if needed
   - Move handoff to `archive/<filename>`

   **Auto-commit the archive:**
   ```bash
   git mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" --staged "<source_path>" "<archive_path>"
   ```
   If `git mv` fails (file is untracked — e.g., loaded from legacy `.claude/handoffs/`), fall back:
   ```bash
   mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" "<source_path>" "<archive_path>"
   ```
   If the commit fails, warn: "Handoff archived but not committed — <reason>".
```

- [ ] **Step 2: Apply the edit**

Use Edit on `packages/plugins/handoff/skills/load/SKILL.md`:
- old_string:
```
5. **Archive the handoff:**
   - Create `<project_root>/docs/handoffs/archive/` if needed
   - Move handoff to `archive/<filename>`

   **Auto-commit the archive:**
   ```bash
   git mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" --staged "<source_path>" "<archive_path>"
   ```
   If `git mv` fails (file is untracked — e.g., loaded from legacy `.claude/handoffs/`), fall back:
   ```bash
   mv "<source_path>" "<archive_path>"
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): archive <filename>" "<source_path>" "<archive_path>"
   ```
   If the commit fails, warn: "Handoff archived but not committed — <reason>".
```
- new_string:
```
5. **Archive the handoff:**
   - Create `<project_root>/docs/handoffs/archive/` if needed
   - Move handoff to `archive/<filename>` via plain `mv`:
   ```bash
   mv "<source_path>" "<archive_path>"
   ```
   Handoffs are local-only working memory — no git operation fires. See `references/handoff-contract.md` for the Git Tracking section.
```

- [ ] **Step 3: Verify the edit**

Use Grep with pattern `auto_commit|git mv`, path `packages/plugins/handoff/skills/load/SKILL.md`.
Expected: no matches

---

### Task 12: Edit quicksave/SKILL.md — remove step 6 auto-commit block

**Files:**
- Modify: `packages/plugins/handoff/skills/quicksave/SKILL.md:58-68`

- [ ] **Step 1: Read the current step 6 block**

Use Read on `packages/plugins/handoff/skills/quicksave/SKILL.md` with `offset=56, limit=16` to see the current step 6 block.

Expected current content:
```
6. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
   - Use frontmatter from [handoff-contract.md](../../references/handoff-contract.md) with `type: checkpoint`
   - Title: `"Checkpoint: <descriptive-title>"`
   - Populate frontmatter `files:` from file paths listed in the Active Files section
   - Required sections (5) are always included — use placeholder content for thin sessions (e.g., "No commands run yet" for Verification Snapshot). Conditional sections (3) are omitted when not applicable.

   **Auto-commit the checkpoint:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn but continue.
```

- [ ] **Step 2: Apply the edit**

Use Edit on `packages/plugins/handoff/skills/quicksave/SKILL.md`:
- old_string:
```
6. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
   - Use frontmatter from [handoff-contract.md](../../references/handoff-contract.md) with `type: checkpoint`
   - Title: `"Checkpoint: <descriptive-title>"`
   - Populate frontmatter `files:` from file paths listed in the Active Files section
   - Required sections (5) are always included — use placeholder content for thin sessions (e.g., "No commands run yet" for Verification Snapshot). Conditional sections (3) are omitted when not applicable.

   **Auto-commit the checkpoint:**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/auto_commit.py" -m "docs(handoff): save <title>" "<file_path>"
   ```
   If the commit fails, warn but continue.
```
- new_string:
```
6. **Write file** to `<project_root>/docs/handoffs/YYYY-MM-DD_HH-MM_checkpoint-<slug>.md`
   - Use frontmatter from [handoff-contract.md](../../references/handoff-contract.md) with `type: checkpoint`
   - Title: `"Checkpoint: <descriptive-title>"`
   - Populate frontmatter `files:` from file paths listed in the Active Files section
   - Required sections (5) are always included — use placeholder content for thin sessions (e.g., "No commands run yet" for Verification Snapshot). Conditional sections (3) are omitted when not applicable.

   Checkpoints are local-only working memory — the file is durable on disk but is not committed. See `references/handoff-contract.md` for the Git Tracking section.
```

- [ ] **Step 3: Verify the edit**

Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/skills/quicksave/SKILL.md`.
Expected: no matches

---

### Task 13: Run tests and commit Commit 2

**Files:** (none — verification + commit)

- [ ] **Step 1: Final grep to confirm zero consumers of auto_commit**

Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/`, output_mode `files_with_matches`.
Expected: empty output (no matches anywhere in the plugin)

- [ ] **Step 2: Run the full test suite**

Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -10 && cd /Users/jp/Projects/active/claude-code-tool-dev`
Expected:
- All tests pass
- Total test count is reduced by exactly the number of tests that were in `test_auto_commit.py` (recorded during Task 1 Step 9). For example, if baseline was 354 and `test_auto_commit.py` had 12 tests, the new count should be 342.

If tests fail, STOP. Investigate: read the failing test output, determine whether the refactor accidentally broke something, and fix before committing.

- [ ] **Step 3: Review the staged changes before committing**

Run: `git status --short`
Expected: lines for the 5 affected files (2 deletions + 3 modifications):
```
 D packages/plugins/handoff/scripts/auto_commit.py
 D packages/plugins/handoff/tests/test_auto_commit.py
 M packages/plugins/handoff/skills/save/SKILL.md
 M packages/plugins/handoff/skills/load/SKILL.md
 M packages/plugins/handoff/skills/quicksave/SKILL.md
```

- [ ] **Step 4: Stage all changes**

Run: `git add packages/plugins/handoff/scripts/auto_commit.py packages/plugins/handoff/tests/test_auto_commit.py packages/plugins/handoff/skills/save/SKILL.md packages/plugins/handoff/skills/load/SKILL.md packages/plugins/handoff/skills/quicksave/SKILL.md`
Expected: silent

- [ ] **Step 5: Commit**

Run:
```bash
git commit -m "$(cat <<'EOF'
refactor(handoff): remove auto-commit from save/load/quicksave

Delete scripts/auto_commit.py (80 lines) and tests/test_auto_commit.py
(159 lines). Strip auto-commit bash blocks from save step 8, load
step 5 (collapses dual git mv/mv path to single mv), and quicksave
step 6. Each skill now writes or moves files only — no git operations
fire.

This is commit 2 of 3 in the handoff no-commit refactor. See:
docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: commit created with 5 files changed (2 deletions, 3 modifications)

- [ ] **Step 6: Verify commit landed**

Run: `git log --oneline -1`
Expected: new SHA with subject `refactor(handoff): remove auto-commit from save/load/quicksave`

**Rollback (Commit 2 only):** `git reset --hard HEAD~1`

---

## Commit 3 — Documentation updates

### Task 14: Edit README.md

**Files:**
- Modify: `packages/plugins/handoff/README.md`

- [ ] **Step 1: Remove the auto_commit.py row from the scripts table (around line 59)**

Use Edit on `packages/plugins/handoff/README.md`:
- old_string:
```
| `auto_commit.py` | Narrow-scope git commit for handoff files | `/save`, `/load`, `/quicksave` skills |
| `cleanup.py` | Archive pruning and state file TTL | SessionStart hook |
```
- new_string:
```
| `cleanup.py` | Archive pruning and state file TTL | SessionStart hook |
```

- [ ] **Step 2: Update the "No auto-prune (git-tracked)" phrasing in Storage Locations**

Use Edit on `packages/plugins/handoff/README.md`:
- old_string:
```
| `<project_root>/docs/handoffs/` | Active handoffs and checkpoints | No auto-prune (git-tracked) |
| `<project_root>/docs/handoffs/archive/` | Archived handoffs (moved by `/load`) | No auto-prune (git-tracked) |
```
- new_string:
```
| `<project_root>/docs/handoffs/` | Active handoffs and checkpoints | No auto-prune (gitignored, local-only) |
| `<project_root>/docs/handoffs/archive/` | Archived handoffs (moved by `/load`) | No auto-prune (gitignored, local-only) |
```

- [ ] **Step 3: Replace the "Handoff files are git-tracked and auto-committed" sentence**

Use Edit on `packages/plugins/handoff/README.md`:
- old_string:
```
Handoff files are git-tracked and auto-committed on create and archive. Use `git log --grep='docs(handoff):'` to view handoff history.
```
- new_string:
```
Handoff files are gitignored and local-only — `/save`, `/load`, and `/quicksave` write or move files on the filesystem without committing. See `references/handoff-contract.md` for the Git Tracking section.
```

- [ ] **Step 4: Verify no remaining "git-tracked" references in README**

Use Grep with pattern `git-tracked`, path `packages/plugins/handoff/README.md`, output_mode `content`.
Expected: no matches

- [ ] **Step 5: Verify no remaining auto_commit references in README**

Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/README.md`, output_mode `content`.
Expected: no matches

---

### Task 15: Edit handoff-contract.md — add Git Tracking section

**Files:**
- Modify: `packages/plugins/handoff/references/handoff-contract.md` (add a new section after "Storage", before "Project Root")

- [ ] **Step 1: Read the section between "## Storage" and "## Project Root"**

Use Read on `packages/plugins/handoff/references/handoff-contract.md` with `offset=53, limit=18`.

Expected current content (lines ~53-70):
```
## Storage

| Location | Format | Retention |
|----------|--------|-----------|
| `<project_root>/docs/handoffs/` | `YYYY-MM-DD_HH-MM_<slug>.md` | No auto-prune |
| `<project_root>/docs/handoffs/archive/` | Same | No auto-prune |
| `<project_root>/docs/handoffs/.session-state/handoff-<UUID>` | Plain text (path) | 24 hours |

**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.

## Project Root
```

- [ ] **Step 2: Insert the Git Tracking section**

Use Edit on `packages/plugins/handoff/references/handoff-contract.md`:
- old_string:
```
**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.

## Project Root
```
- new_string:
```
**Filename slug:** Lowercase, hyphens for spaces, no special characters. Checkpoints use `checkpoint-<slug>`, full handoffs use `<slug>` directly.

## Git Tracking

Handoff files and archives are **local-only working memory** — they are gitignored at the repository level and never auto-committed by any skill. Implications:

- `/save`, `/load`, and `/quicksave` write or move files on the filesystem only. No git operations fire.
- `docs/handoffs/` (active and archive) is gitignored alongside other ephemeral state (`docs/decisions/`, `.claude/sessions/`).
- `/search` and `/distill` read via Python `open()` — gitignore status is invisible to them.
- Chain protocol (`resumed_from`, state files) is filesystem-based and unaffected by git tracking.

Handoffs are not shared across machines by design. If cross-machine continuity is needed, copy individual files manually — the plugin does not manage that case.

## Project Root
```

- [ ] **Step 3: Verify the section was added**

Use Grep with pattern `## Git Tracking`, path `packages/plugins/handoff/references/handoff-contract.md`.
Expected: one match

---

### Task 16: Edit CHANGELOG.md — rewrite Unreleased block (strategy C3)

**Files:**
- Modify: `packages/plugins/handoff/CHANGELOG.md`

- [ ] **Step 1: Read the current Unreleased block**

Use Read on `packages/plugins/handoff/CHANGELOG.md` with `offset=1, limit=40`.

Expected current content (lines 7-19 for the first Changed + Added blocks):
```
## [Unreleased]

### Changed
- **BREAKING:** Handoff storage moved from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`. Handoffs are now git-tracked and auto-committed. Archive renamed from `.archive/` to `archive/`. No auto-pruning — git history manages lifecycle.
- Cleanup hook (`cleanup.py`) no longer prunes handoff files — only session-state files (24h TTL)
- `is_handoff_path()` now matches `docs/handoffs/` (active and archived) instead of `.claude/handoffs/`
- `search.py` and `triage.py` check legacy `.claude/handoffs/` location as fallback

### Added
- `auto_commit.py` — testable git commit logic for handoff state changes
- `get_legacy_handoffs_dir()` in `project_paths.py` for fallback discovery
- `Bash` added to `allowed-tools` for save, load, quicksave skills
- Legacy fallback warning when handoffs found at old location
```

- [ ] **Step 2: Rewrite the first Changed entry (soften language, remove "git-tracked and auto-committed")**

Use Edit on `packages/plugins/handoff/CHANGELOG.md`:
- old_string:
```
### Changed
- **BREAKING:** Handoff storage moved from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`. Handoffs are now git-tracked and auto-committed. Archive renamed from `.archive/` to `archive/`. No auto-pruning — git history manages lifecycle.
- Cleanup hook (`cleanup.py`) no longer prunes handoff files — only session-state files (24h TTL)
- `is_handoff_path()` now matches `docs/handoffs/` (active and archived) instead of `.claude/handoffs/`
- `search.py` and `triage.py` check legacy `.claude/handoffs/` location as fallback
```
- new_string:
```
### Changed
- **BREAKING:** Handoff storage moved from `<project_root>/.claude/handoffs/` to `<project_root>/docs/handoffs/`. Handoffs remain local-only working memory — gitignored and never auto-committed. Archive renamed from `.archive/` to `archive/`. No auto-pruning — handoffs are ephemeral by design.
- Cleanup hook (`cleanup.py`) prunes session-state files only (24h TTL); handoff files are never auto-pruned.
- `is_handoff_path()` now matches `docs/handoffs/` (active and archived) instead of `.claude/handoffs/`.
- `search.py` and `triage.py` check legacy `.claude/handoffs/` location as fallback.
```

- [ ] **Step 3: Remove the auto_commit.py Added entry**

Use Edit on `packages/plugins/handoff/CHANGELOG.md`:
- old_string:
```
### Added
- `auto_commit.py` — testable git commit logic for handoff state changes
- `get_legacy_handoffs_dir()` in `project_paths.py` for fallback discovery
- `Bash` added to `allowed-tools` for save, load, quicksave skills
- Legacy fallback warning when handoffs found at old location
```
- new_string:
```
### Added
- `get_legacy_handoffs_dir()` in `project_paths.py` for fallback discovery.
- `Bash` added to `allowed-tools` for save, load, quicksave skills.
- Legacy fallback warning when handoffs found at old location.
```

- [ ] **Step 4: Verify no "git-tracked and auto-committed" or "auto_commit.py" remain in CHANGELOG**

Use Grep with pattern `git-tracked and auto-committed|auto_commit\.py`, path `packages/plugins/handoff/CHANGELOG.md`, output_mode `content`.
Expected: no matches

- [ ] **Step 5: Verify the Unreleased block still parses as valid Keep-a-Changelog**

Run: `head -40 packages/plugins/handoff/CHANGELOG.md | grep -E '^(##|###)'`
Expected: headings in order:
```
## [Unreleased]
### Changed
### Added
### Fixed
### Changed
### Added
## [1.5.0] - 2026-02-28
```

(Note: the duplicated `### Changed`/`### Added` blocks are pre-existing structure — leave them unchanged.)

---

### Task 17: Run tests and commit Commit 3

**Files:** (none — verification + commit)

- [ ] **Step 1: Run the test suite (should be unchanged from Commit 2 — docs-only change)**

Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -5 && cd /Users/jp/Projects/active/claude-code-tool-dev`
Expected: all tests pass, total count identical to post-Commit-2 count

- [ ] **Step 2: Review staged changes**

Run: `git status --short`
Expected: 3 modified files:
```
 M packages/plugins/handoff/README.md
 M packages/plugins/handoff/CHANGELOG.md
 M packages/plugins/handoff/references/handoff-contract.md
```

- [ ] **Step 3: Stage changes and commit**

Run:
```bash
git add packages/plugins/handoff/README.md packages/plugins/handoff/references/handoff-contract.md packages/plugins/handoff/CHANGELOG.md && git commit -m "$(cat <<'EOF'
docs(handoff): update README, contract, CHANGELOG for local-only model

Update README Storage Locations table to reflect "gitignored, local-only"
retention, remove the auto_commit.py row from the scripts table, and
replace the "git-tracked and auto-committed" sentence with a pointer to
the new Git Tracking section of the contract.

Add a "Git Tracking" section to handoff-contract.md documenting that
handoffs are filesystem-local, never committed by any skill, and that
filesystem-based features (/search, /distill, chain protocol) are
unaffected by git tracking.

Rewrite the CHANGELOG Unreleased block (strategy C3 consolidate): soften
the storage migration entry to reflect "gitignored, not committed", and
delete the auto_commit.py Added entry entirely. The reversed decision
never shipped, so this is a course-correction rather than a breaking
change against production.

This is commit 3 of 3 in the handoff no-commit refactor. See:
docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: commit created with 3 files changed

- [ ] **Step 4: Verify all three refactor commits are on the feature branch**

Run: `git log --oneline origin/main..HEAD`
Expected: 4 commits (top to bottom):
```
<sha> docs(handoff): update README, contract, CHANGELOG for local-only model
<sha> refactor(handoff): remove auto-commit from save/load/quicksave
<sha> chore(handoff): gitignore handoffs and un-track existing archives
<sha> docs(spec): add handoff no-commit refactor design
```

**Rollback (Commit 3 only):** `git reset --hard HEAD~1`

---

## Push and PR Creation Phase

### Task 18: Push feature branch to origin

**Files:** (git ref update on remote)

- [ ] **Step 1: Push with upstream tracking**

Run: `git push -u origin feature/handoff-no-commit`
Expected: output like "Branch 'feature/handoff-no-commit' set up to track remote branch 'feature/handoff-no-commit' from 'origin'" and "To github.com:jpsweeney97/claude-code-tool-dev.git" with the pushed commits listed

- [ ] **Step 2: Verify the remote branch exists**

Run: `git ls-remote --heads origin feature/handoff-no-commit`
Expected: one line with a SHA + `refs/heads/feature/handoff-no-commit`

---

### Task 19: Create the PR

**Files:** (GitHub PR)

- [ ] **Step 1: Create PR via gh**

Run:
```bash
gh pr create --title "refactor(handoff): gitignore handoff files, remove auto-commit" --body "$(cat <<'EOF'
## Why

Handoffs were previously auto-committed on whatever branch was checked out, which caused recurring friction across sessions:

- Handoff commits landed on feature branches, polluting open PRs (e.g., PR #102 needed a full rebuild mid-session after 14 handoff commits rode along from stale local main).
- Local main accumulated unpushed handoff commits that contaminated any feature branch cut from it via the default `git checkout -b`.
- Cleanup required force-pushes, safety tags, and cross-validation of eventually-consistent PR diffs.

The git-tracked behavior was part of an in-flight **unreleased** migration. This PR course-corrects before that release ships.

## What changes

- `docs/handoffs/` is gitignored (joins `docs/decisions/` and `.claude/sessions/` as ephemeral local-only state).
- `/save`, `/load`, `/quicksave` no longer commit — they write or move files only.
- `scripts/auto_commit.py` and its test are deleted (~240 lines).
- ~55 previously-tracked archive files are un-tracked via `git rm --cached`.
- README, handoff-contract, and CHANGELOG updated to reflect local-only semantics.

## What's preserved

- `/search` across active + archive (filesystem-based, gitignore-invariant).
- `/distill` extraction from archive corpus.
- Chain protocol via `resumed_from` and state files.
- `/quicksave` checkpoint-streak guardrail.
- `quality_check.py` frontmatter/section validation on write.
- `cleanup.py` session-state TTL pruning.
- `/defer` ticket commits (out of scope — tickets are durable project artifacts).

## Migration

Pulling this PR un-tracks existing archive files on disk (content preserved, no longer in git). Future handoffs are written but not committed. No user action required unless you want to manually prune on-disk archives.

## Testing

- `cd packages/plugins/handoff && uv run pytest` — all tests pass (only `test_auto_commit.py` missing)
- `git ls-files docs/handoffs/` returns empty
- `grep -r auto_commit packages/plugins/handoff/` returns no hits

## Rollback

`gh pr revert` reverses all three commits. Archive files would need manual `git checkout <pre-merge-commit> -- docs/handoffs/archive/` restoration if re-tracking is desired.

## Spec

See `docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md` for the full design rationale, alternatives considered, and edge-case analysis.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
Expected: output containing the PR URL (e.g., `https://github.com/jpsweeney97/claude-code-tool-dev/pull/<N>`)

- [ ] **Step 2: Record the PR number for verification**

Run: `gh pr view --json number,url,title`
Expected: JSON with PR number, URL, and title matching the create command

---

### Task 20: Post-PR verification

**Files:** (read-only checks)

- [ ] **Step 1: Verify PR file list shows only intended files**

Run: `gh pr diff --name-only feature/handoff-no-commit 2>&1 | sort`
Expected (sorted):
```
.gitignore
docs/superpowers/specs/2026-04-10-handoff-no-commit-design.md
packages/plugins/handoff/CHANGELOG.md
packages/plugins/handoff/README.md
packages/plugins/handoff/references/handoff-contract.md
packages/plugins/handoff/scripts/auto_commit.py
packages/plugins/handoff/skills/load/SKILL.md
packages/plugins/handoff/skills/quicksave/SKILL.md
packages/plugins/handoff/skills/save/SKILL.md
packages/plugins/handoff/tests/test_auto_commit.py
```

Plus up to ~55 deleted files under `docs/handoffs/archive/` from the `git rm --cached` operation.

If unexpected files appear (e.g., `.venv/`, `__pycache__/`, files from other plugins), STOP and investigate before letting a reviewer see the PR.

- [ ] **Step 2: Run the spec's 11-check verification list**

For each check, record PASS or FAIL with evidence:

1. **`git status` clean on feature branch** — Run: `git status --short`. Expected: empty output.
2. **After commit #1: `git ls-files docs/handoffs/`** — Run: `git ls-files docs/handoffs/`. Expected: empty output.
3. **After commit #2: auto_commit.py absent** — Run: `ls packages/plugins/handoff/scripts/auto_commit.py 2>&1`. Expected: "No such file or directory".
4. **After commit #2: grep finds no auto_commit references in skills/** — Use Grep with pattern `auto_commit`, path `packages/plugins/handoff/skills/`. Expected: no matches.
5. **After commit #3: grep finds no "git-tracked" in README** — Use Grep with pattern `git-tracked`, path `packages/plugins/handoff/README.md`. Expected: no matches.
6. **`pytest` passes** — Run: `cd packages/plugins/handoff && uv run pytest 2>&1 | tail -5 && cd /Users/jp/Projects/active/claude-code-tool-dev`. Expected: all tests pass (count reduced by exactly the auto_commit test count).
7. **E2E /save smoke test** — Deferred until post-merge and fresh session; record as "Deferred — post-merge smoke test required".
8. **E2E /load smoke test** — Same: deferred.
9. **/quicksave smoke test + chain walk** — Same: deferred.
10. **`gh pr diff --name-only` shows only intended files** — Confirmed in Step 1 above.
11. **PR body documents the course-correction** — Confirmed by the `gh pr create` body in Task 19.

- [ ] **Step 3: Review the PR in the browser (manual)**

Run: `gh pr view --web`
Expected: PR page opens in the browser. Skim the file list and commits to confirm everything looks right.

---

## Optional Post-Merge Phase

### Task 21: (After PR merges) Clean up backup tags

**Dependencies:** Refactor PR merged, confidence established (no regressions reported), PR #102 status noted.

**Files:** (git tag deletion)

- [ ] **Step 1: Verify PR is merged**

Run: `gh pr view --json state,mergedAt`
Expected: `"state": "MERGED"` with a non-null `mergedAt` timestamp

- [ ] **Step 2: Verify main is clean after pulling**

Run: `git checkout main && git pull origin main && git log --oneline origin/main..HEAD`
Expected: empty output (main matches origin)

- [ ] **Step 3: Delete the two refactor backup tags**

Run:
```bash
git tag -d backup-fix-refactor-pre-reset
git tag -d backup-main-refactor-pre-reset
```
Expected:
```
Deleted tag 'backup-fix-refactor-pre-reset' (was <sha>)
Deleted tag 'backup-main-refactor-pre-reset' (was <sha>)
```

- [ ] **Step 4: Verify the tags are gone**

Run: `git tag --list 'backup-*-refactor-pre-reset'`
Expected: empty output

- [ ] **Step 5: (Optional) Delete feature branch locally**

Run: `git branch -d feature/handoff-no-commit`
Expected: "Deleted branch feature/handoff-no-commit (was <sha>)"

If `git branch -d` refuses because the branch is not fully merged (e.g., GitHub squash-merged), use `git branch -D feature/handoff-no-commit` to force. Squash-merge is common and expected here.

---

## Global Rollback Reference

Each phase has a local rollback:

| Stage | Command | Effect |
|---|---|---|
| Task 1-2 | Delete tags: `git tag -d backup-fix-refactor-pre-reset backup-main-refactor-pre-reset` | Nothing committed — tags only |
| Task 3 (feature branch + cherry-pick) | `git checkout fix/clean-stale-shakedown-script-conventions && git branch -D feature/handoff-no-commit` | Delete feature branch; fix branch is still at its pre-reset tip (backup tag still preserves it) |
| Task 4 (Phase 2a) | `git reset --hard backup-fix-refactor-pre-reset` while on fix branch | Restores fix branch to pre-reset state |
| Task 5 (Phase 2b) | `git checkout main && git reset --hard backup-main-refactor-pre-reset` | Restores main to pre-reset state |
| Task 7 (Commit 1 uncommitted) | `git checkout .gitignore && git reset HEAD docs/handoffs/` | Unstages + reverts `.gitignore` edit |
| Task 7 (Commit 1 committed) | `git reset --hard HEAD~1` | Drops the commit |
| Task 9-13 (Commit 2 uncommitted) | `git checkout .` on feature branch | Reverts all working-tree changes |
| Task 13 (Commit 2 committed) | `git reset --hard HEAD~1` | Drops the commit |
| Task 14-17 (Commit 3 uncommitted) | `git checkout .` on feature branch | Reverts working-tree changes |
| Task 17 (Commit 3 committed) | `git reset --hard HEAD~1` | Drops the commit |
| Task 18 (pushed) | `git push --delete origin feature/handoff-no-commit` | Deletes the remote branch |
| Task 19 (PR open) | `gh pr close <number> --delete-branch` | Closes PR and deletes remote branch |
| Post-merge regret | `gh pr revert <number>` | Creates a revert PR |

**Nuclear option:** If multiple things have gone sideways and you want to start completely fresh:
1. `git checkout main && git reset --hard origin/main`
2. `git checkout fix/clean-stale-shakedown-script-conventions && git reset --hard origin/fix/clean-stale-shakedown-script-conventions`
3. `git branch -D feature/handoff-no-commit` (if it exists)
4. `git push --delete origin feature/handoff-no-commit` (if it was pushed)
5. Then re-run the plan from Task 1. Backup tags (if not yet deleted) still provide safety.

---

## Notes for the Implementer

1. **The PreToolUse branch protection hook only fires on Edit/Write tool calls, not on Bash git operations.** Phase 2b (resetting local main) is a Bash `git reset` — no hook interference. However, if you accidentally try to `Write` a file while on `main`, the hook will block.

2. **All filesystem deletions must use `trash`, not `rm`.** Per the global CLAUDE.md rule. The only exception is the inline `.gitignore` sanity test in Task 7 Step 4, which creates and immediately removes a throwaway file — that one is narrow-scope and acceptable.

3. **The test suite lives in `packages/plugins/handoff/tests/`.** After Commit 2, one file (`test_auto_commit.py`) is deleted. No other tests should be affected. If ANY other test fails after Commit 2, STOP — something else broke.

4. **The PR body includes a `🤖 Generated with` footer.** This is a standard Claude Code attribution; remove if you prefer.

5. **`gh pr diff --name-only` has a known stale-cache window after force-push.** This plan does not use force-push anywhere, so the cache issue should not apply — but if results look wrong, wait 30 seconds and retry or cross-check with `gh pr view --json files`.

6. **The design doc cherry-pick in Task 3 creates a new commit with a different SHA than the original `5a1b7edb`** (committer timestamp changes during cherry-pick). Use file path, not SHA, as the authoritative reference in subsequent steps.

7. **Commit 2's final grep (Task 13 Step 1) is the strongest integration test** — if it returns any matches, the refactor is incomplete. If it returns empty, all three skills + the script deletion are consistent.

8. **The CHANGELOG has two `### Added` and two `### Changed` blocks in Unreleased** (pre-existing structure from multiple batches of work). Do not merge them — just edit the first ones. The second blocks contain unrelated work that should stay intact.

9. **The stranded `docs/handoffs/archive/2026-04-09_01-37_t4-publication-and-security-review.md` file** (still on disk from a prior session) will be implicitly gitignored by Commit 1. It becomes local-only clutter that stops drifting across sessions. Trash it manually if desired.

10. **Phase 2 is destructive against local state.** Run this plan in a session where no other concurrent work is on the fix branch or local main — otherwise those concurrent changes get dropped too. Safety tags preserve everything if something goes wrong.
