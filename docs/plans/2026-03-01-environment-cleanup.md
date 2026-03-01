# Environment Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Transform a messy, ad-hoc macOS development environment into a declarative, reproducible system with strict tool ownership boundaries.

**Architecture:** Three-layer model with "one executable, one owner" principle. Homebrew owns OS-level packages and GUI apps. mise owns language runtimes and version-pinned dev tools. GNU stow manages dotfile deployment from `~/dotfiles/`. A `doctor-env` script enforces invariants.

**Tech Stack:** Homebrew (Brewfile), mise (config.toml), GNU stow, zsh, bash (bootstrap script)

**Scope:** All changes target `~/dotfiles/` repo and live dotfiles. The `environment-improvement/` directory in claude-code-tool-dev is reference-only and retired at the end.

**Revision note:** v4 — revised after adversarial Codex dialogue (6 turns, converged). v2: fixed 8 ship-blockers from first adversarial review. v3: fixed 5 issues from deep evaluative review. v4 fixes: Task 2 FZF deletion (ship-blocker), `commit_if_changed` untracked-file blindness, Task 6 `git add -A` contamination, Task 11 `stow --adopt` symlink failure, parallelization claim correction, rollback completeness. v4 additions: Task 0 (clean working tree prerequisite).

**Verification convention:** All verification steps use `zsh -lc '...'` (one-shot login shell) instead of `exec zsh` because this plan is designed for execution via Claude Code, where `exec zsh` replaces the subshell process and is untestable.

**Commit convention:** Many tasks end with a conditional commit. To avoid the shell operator-precedence bug (`||` and `&&` have equal precedence in bash/zsh and left-associate, so `git diff --quiet || git add && git commit` runs commit unconditionally), all conditional commits use this helper:

```bash
commit_if_changed() {
  local path="$1" msg="$2"
  cd ~/dotfiles
  local has_changes=false
  # Check unstaged tracked changes
  git diff --quiet -- "$path" || has_changes=true
  # Check staged changes
  git diff --cached --quiet -- "$path" || has_changes=true
  # Check untracked files (respects .gitignore)
  [[ -n "$(git ls-files --others --exclude-standard -- "$path")" ]] && has_changes=true
  if $has_changes; then
    git add "$path" && git commit -m "$msg"
  else
    echo "No changes in $path — skipping commit."
  fi
}
```

Define this function in the shell session before starting Phase 0. Unconditional commits (where changes are guaranteed) still use the direct `git add && git commit` pattern.

---

## Phase 0: Baseline

### Task 0: Establish clean working tree in dotfiles

The dotfiles repo has uncommitted changes (deletions, modifications, untracked files). All subsequent tasks assume a clean baseline — without this, `git add` stages unrelated changes, `git diff` gives misleading results, and commits contaminate the migration history.

**Do not skip this task.** It is the prerequisite for every other task.

**Step 1: Inspect current state**

```bash
cd ~/dotfiles && git status
```

Review the output. Categorize each change:
- **Intentional:** Changes you want to keep (commit them)
- **Unintended drift:** Changes to defer (stash them)
- **Junk:** Files that shouldn't exist (trash them)

**Step 2: Resolve all pending changes**

For intentional changes:
```bash
cd ~/dotfiles && git add <specific-files> && git commit -m "chore: commit pre-migration state"
```

For changes to defer:
```bash
cd ~/dotfiles && git stash push -m "pre-migration stash $(date +%Y%m%d)"
```

For junk (e.g., `.DS_Store`, `__pycache__`):
```bash
cd ~/dotfiles && find . -name .DS_Store -exec trash {} + && find . -name __pycache__ -exec trash {} +
```

**Step 3: Verify clean state**

```bash
cd ~/dotfiles && git status
```

Expected: `nothing to commit, working tree clean` (or only gitignored files remaining).

**Do not proceed to Phase 1 until the working tree is clean.**

---

## Phase 1: Preflight — Prerequisites and Snapshot

### Task 1: Verify prerequisites and snapshot current state

**Files:**
- Create: `~/dotfiles/MIGRATION-LOG.md`

**Step 1: Verify required tools are installed**

```bash
for cmd in brew stow mise trash; do
  command -v "$cmd" &>/dev/null || echo "MISSING: $cmd"
done
```

Expected: No output. If any tool is missing, install it before proceeding:
- `brew`: See https://brew.sh
- `stow`: `brew install stow`
- `mise`: `brew install mise`
- `trash`: `brew install trash` (or use the zsh function if already defined)

**Do not proceed if any prerequisite is missing.**

**Step 2: Record current homebrew state**

```bash
brew bundle dump --file=/tmp/Brewfile.snapshot --describe
```

Expected: File at `/tmp/Brewfile.snapshot` with ~128 lines.

**Step 3: Record current mise state**

```bash
mise ls --current > /tmp/mise-snapshot.txt
```

**Step 4: Record current stow state**

```bash
cd ~/dotfiles && stow -n -v zsh bin hammerspoon karabiner kitty launchagents nvim starship tmux > /tmp/stow-snapshot.txt 2>&1
```

Expected: Conflicts for `bin` (fix-claude-docs-links), `zsh` (.zprofile, .DS_Store), `launchagents` (.DS_Store).

**Step 5: Create migration log**

Create `~/dotfiles/MIGRATION-LOG.md`:

```markdown
# Environment Migration Log

Started: 2026-03-01

## Pre-migration State
- Homebrew leaves: 85 formulae, 11 casks
- Stow packages: bin, hammerspoon, karabiner, kitty, launchagents, nvim, starship, tmux, zsh
- Stow conflicts: bin (fix-claude-docs-links, __pycache__), zsh (.zprofile, .DS_Store), launchagents (.DS_Store)
- Known bugs: direnv double-load, zsh-rebuild-cache rm interception, uv dual ownership

## Phases
- [ ] Phase 1: Preflight
- [ ] Phase 2: Shell fixes
- [ ] Phase 3: Stow deployment
- [ ] Phase 4: Declarative manifests
- [ ] Phase 5: Ownership enforcement
- [ ] Phase 6: Cleanup
```

**Step 6: Commit**

```bash
cd ~/dotfiles && git add MIGRATION-LOG.md && git commit -m "docs: start environment migration log"
```

---

## Phase 2: Shell Fixes

### Task 2: Apply all tools.zsh fixes atomically

Tasks 2, 3, and 4 from v1 all edit `~/dotfiles/zsh/.config/zsh/tools.zsh` in overlapping regions. They MUST be applied as a single atomic edit to avoid conflicts.

This task combines three fixes:
1. **zsh-rebuild-cache rm bug** (lines 27-30): `rm -f` intercepted by `rm()` override at line 148
2. **Tool init reordering** (lines 224-240): mise must precede uv; direnv becomes uncached
3. **direnv dedup** (line 239): cached `_cache_load "direnv"` replaced with uncached eval

**Files:**
- Modify: `~/dotfiles/zsh/.config/zsh/tools.zsh`

**Step 1: Fix zsh-rebuild-cache (lines 27-30)**

Replace the `zsh-rebuild-cache` function:

```bash
# old:
zsh-rebuild-cache() {
  rm -f "$_zsh_cache_dir"/*.zsh
  echo "Cache cleared. Restart shell to rebuild."
}

# new:
zsh-rebuild-cache() {
  setopt local_options null_glob
  local files=("$_zsh_cache_dir"/*.zsh)
  if (( ${#files} )); then
    trash "${files[@]}"
    echo "Cache cleared (${#files} files trashed). Restart shell to rebuild."
  else
    echo "Cache already clean."
  fi
}
```

**Step 2: Reorder and fix tool initialization section (lines 224-240)**

Replace the entire tool init section (from `# --- Prompt ---` through `# --- FZF ---`) with:

```bash
# --- Prompt ---
_cache_load "starship" "starship init zsh" "starship.zsh"

# --- Version Manager (must precede tools it manages) ---
# Note: Cached mise won't auto-detect new .mise.toml until cache expires.
# For immediate pickup, run zsh-rebuild-cache.
_cache_load "mise" "mise activate zsh" "mise.zsh"

# --- Navigation ---
_cache_load "zoxide" "zoxide init zsh" "zoxide.zsh"

# --- Completions (after mise, so shims are available) ---
_cache_load "uv" "uv generate-shell-completion zsh" "uv-completions.zsh"

# --- Direnv (uncached — hooks modify shell behavior, stale caches break things) ---
(( $+commands[direnv] )) && eval "$(direnv hook zsh)"

# --- FZF ---
_fzf_zsh="${XDG_CONFIG_HOME:-$HOME/.config}/zsh/integrations/fzf.zsh"
[[ -f "$_fzf_zsh" ]] && source "$_fzf_zsh"
unset _fzf_zsh
```

This reordering:
- Moves mise before uv (so mise shim is available for uv completion generation)
- Moves mise before zoxide (no functional dependency, but logical grouping)
- Replaces cached direnv with uncached eval (~5ms, not worth caching)
- Removes the `_cache_load "direnv"` line entirely

**Step 3: Verify**

```bash
zsh -lc 'type zsh-rebuild-cache'
```

Expected: Function definition showing `trash` instead of `rm`.

```bash
zsh -lc 'zsh-rebuild-cache'
```

Expected: "Cache cleared (N files trashed)..." — not "rm is disabled."

```bash
zsh -lc 'type _direnv_hook 2>/dev/null && echo "direnv loaded" || echo "direnv not loaded"'
```

Expected: "direnv loaded"

**Step 4: Commit**

```bash
cd ~/dotfiles && git add zsh/.config/zsh/tools.zsh && git commit -m "fix: rebuild-cache rm bug, reorder tool init (mise before uv), uncache direnv"
```

### Task 3: Remove direnv eval from .zshrc

The direnv hook is now loaded uncached in tools.zsh (Task 2). Remove the redundant `eval` from `.zshrc`.

**Files:**
- Modify: `~/dotfiles/zsh/.zshrc`

**Step 1: Remove the eval line**

Remove the last line of `~/dotfiles/zsh/.zshrc`:

```bash
eval "$(direnv hook zsh)"
```

The file should end after the profiling comment (`# zprof`), with a trailing newline.

**Step 2: Verify direnv loads exactly once**

```bash
zsh -lc 'typeset -f _direnv_hook | head -1'
```

Expected: `_direnv_hook () {` — confirming direnv is loaded (from tools.zsh, not .zshrc).

**Step 3: Commit**

```bash
cd ~/dotfiles && git add zsh/.zshrc && git commit -m "fix: remove redundant direnv eval from .zshrc"
```

### Task 4: Fix secrets.zsh triple-listing in .gitignore

**Files:**
- Modify: `~/dotfiles/zsh/.config/zsh/.gitignore`

**Step 1: Deduplicate**

Replace the contents of `~/dotfiles/zsh/.config/zsh/.gitignore`:

```
secrets.zsh
```

One line. Not three.

**Step 2: Commit**

```bash
cd ~/dotfiles && git add zsh/.config/zsh/.gitignore && git commit -m "fix: deduplicate secrets.zsh in gitignore"
```

### Task 5: Add PIPX_DEFAULT_PYTHON mise guard

`settings.zsh` runs `mise which python` unconditionally, which emits noise on systems without mise.

**Files:**
- Modify: `~/dotfiles/zsh/.config/zsh/settings.zsh`

**Step 1: Guard the mise call**

Find and replace the `PIPX_DEFAULT_PYTHON` line:

```bash
# old:
export PIPX_DEFAULT_PYTHON="${$(mise which python 2>/dev/null):-python3}"

# new:
if (( $+commands[mise] )); then
  export PIPX_DEFAULT_PYTHON="${$(mise which python 2>/dev/null):-python3}"
else
  export PIPX_DEFAULT_PYTHON="python3"
fi
```

**Step 2: Verify**

```bash
zsh -lc 'echo $PIPX_DEFAULT_PYTHON'
```

Expected: Path to mise-managed python or `python3`.

**Step 3: Commit**

```bash
cd ~/dotfiles && git add zsh/.config/zsh/settings.zsh && git commit -m "fix: guard PIPX_DEFAULT_PYTHON against missing mise"
```

---

## Phase 3: Stow Deployment

### Task 6: Clean .DS_Store conflicts across all stow packages

.DS_Store files in the dotfiles repo block stow operations. Clean them all before any stow operations.

**Files:**
- Modify: `~/dotfiles/` (remove .DS_Store files)

**Step 1: Find and remove all .DS_Store files in dotfiles**

```bash
find ~/dotfiles -name .DS_Store -exec trash {} +
```

**Step 2: Verify .gitignore already covers .DS_Store**

```bash
grep -q '.DS_Store' ~/dotfiles/.gitignore && echo "covered" || echo "NOT covered"
```

Expected: "covered" (confirmed in preflight: `.gitignore` has `.DS_Store` and `**/.DS_Store`).

**Step 3: Commit**

```bash
# .DS_Store files are gitignored — this commit will be skipped (expected).
# The trash step is still valuable: it removes filesystem conflicts that block stow.
commit_if_changed . "chore: remove .DS_Store files from dotfiles"
```

### Task 7: Deploy .zprofile via mv-then-stow

The live `~/.zprofile` is a 4-line pipx-generated file. The dotfiles repo has a better version with architecture detection and re-entry guard. Using `mv` instead of `stow --adopt` to avoid adopting other conflicts.

**Files:**
- Modify: `~/.zprofile`

**Step 1: Back up and move the current .zprofile**

```bash
cp ~/.zprofile ~/.zprofile.bak.$(date +%Y%m%d)
mv ~/.zprofile /tmp/.zprofile.moved
```

**Step 2: Stow the zsh package**

```bash
cd ~/dotfiles && stow zsh
```

Now `~/.zprofile` is a symlink to `~/dotfiles/zsh/.zprofile` (the good version).

**Step 3: Verify**

```bash
ls -la ~/.zprofile
```

Expected: Symlink pointing to `dotfiles/zsh/.zprofile`.

```bash
zsh -lc 'echo $ZPROFILE_LOADED'
```

Expected: `1` (the guard variable from the proper .zprofile).

**Step 4: Verify stow reports clean**

```bash
cd ~/dotfiles && stow -n -v zsh 2>&1
```

Expected: No conflict errors.

**Step 5: Commit (if changed)**

```bash
commit_if_changed zsh/ "fix: deploy proper .zprofile with architecture detection via stow"
```

---

## Phase 4: Declarative Manifests

### Task 8: Generate and curate Brewfile

**Files:**
- Create: `~/dotfiles/homebrew/Brewfile`

**Step 1: Create the homebrew directory**

```bash
mkdir -p ~/dotfiles/homebrew
```

Note: The Brewfile is NOT stow-managed. It lives in `~/dotfiles/homebrew/` for version control. `brew bundle` points at it directly.

**Step 2: Dump current state**

```bash
brew bundle dump --file=~/dotfiles/homebrew/Brewfile --describe
```

**Step 3: Curate the Brewfile**

Edit `~/dotfiles/homebrew/Brewfile`:

1. **Remove `brew "uv"`** — mise owns it
2. **Remove `go "cmd/go"` and `go "cmd/gofmt"`** if present — Go stdlib, not installable via brew
3. **Organize into sections** with comments:
   - Taps
   - Core CLI tools (bat, eza, fd, ripgrep, etc.)
   - Development tools (gh, git-delta, direnv, etc.)
   - System utilities (coreutils, gnu-sed, htop, etc.)
   - Media tools (ffmpeg, imagemagick, sox, etc.)
   - Shell (zsh-syntax-highlighting, zsh-autosuggestions, starship, zoxide)
   - Casks (GUI apps)
   - Mac App Store
   - VS Code extensions
4. **Add comments** to non-obvious formulae explaining why they're installed

**Step 4: Verify Brewfile is valid**

```bash
brew bundle check --file=~/dotfiles/homebrew/Brewfile || echo "Some dependencies unmet (expected if uv removed)"
```

**Step 5: Commit**

```bash
cd ~/dotfiles && git add homebrew/Brewfile && git commit -m "feat: add declarative Brewfile with curated package list"
```

### Task 9: Add mise config to dotfiles

The live `~/.config/mise/config.toml` exists. Stow will refuse to create a symlink over it. Use mv-then-stow to avoid the curation clobber trap (where `stow --adopt` overwrites curated edits with the old live file).

**Files:**
- Create: `~/dotfiles/mise/.config/mise/config.toml`

**Step 1: Create the mise stow package structure**

```bash
mkdir -p ~/dotfiles/mise/.config/mise
```

**Step 2: Copy current mise config into dotfiles**

```bash
cp ~/.config/mise/config.toml ~/dotfiles/mise/.config/mise/config.toml
```

**Step 3: Curate the mise config**

Edit `~/dotfiles/mise/.config/mise/config.toml`:

1. **Pin runtime versions explicitly** (node, python, go — no "latest" for runtimes)
2. **Keep "latest" for convenience CLI tools** (pipx, cargo, npm tools)
3. **Add `[settings]` section:**

```toml
[settings]
experimental = true
legacy_version_file = true
```

4. **Unpin repomix** if the pinning at 1.9.2 was accidental:

```toml
"npm:repomix" = "latest"
```

**Step 4: Move live config out of the way, then stow**

```bash
mv ~/.config/mise/config.toml ~/.config/mise/config.toml.bak
cd ~/dotfiles && stow mise
```

Now `~/.config/mise/config.toml` is a symlink to the curated version.

**Step 5: Verify**

```bash
readlink ~/.config/mise/config.toml
```

Expected: Path containing `dotfiles/mise/.config/mise/config.toml`.

```bash
mise doctor 2>&1 | head -5
```

Expected: Healthy report.

**Step 6: Commit**

```bash
cd ~/dotfiles && git add mise/ && git commit -m "feat: add mise config to dotfiles, stow-managed"
```

---

## Phase 5: Ownership Enforcement

### Task 10: Remove uv from Homebrew

uv is now owned by mise. Remove the Homebrew copy.

**Step 1: Uninstall brew uv**

```bash
brew uninstall uv
```

**Step 2: Verify mise uv still works**

```bash
zsh -lc 'which uv && uv --version'
```

Expected: Path to mise-managed uv with version output.

**Step 3: Verify Brewfile doesn't list uv**

```bash
grep -n 'brew "uv"' ~/dotfiles/homebrew/Brewfile || echo "uv not in Brewfile (correct)"
```

Expected: "uv not in Brewfile (correct)".

### Task 11: Fix bin stow package conflicts

The `bin` stow package has two problems: `__pycache__` directory and `fix-claude-docs-links` existing as a real file.

**Files:**
- Modify: `~/dotfiles/bin/`

**Step 1: Add .stow-local-ignore to prevent __pycache__ deployment**

```bash
echo '__pycache__' > ~/dotfiles/bin/.stow-local-ignore
```

This prevents stow from ever linking `__pycache__` directories, even if they regenerate.

**Step 2: Remove __pycache__ from dotfiles**

```bash
trash ~/dotfiles/bin/.local/bin/__pycache__
```

**Step 3: Remove absolute symlink and stow**

`~/.local/bin/fix-claude-docs-links` is an absolute symlink (not a stow-managed relative symlink). `stow --adopt` only works with regular files, not symlinks. Remove the symlink, then stow normally to create a proper relative symlink.

```bash
[[ -L ~/.local/bin/fix-claude-docs-links ]] && trash ~/.local/bin/fix-claude-docs-links
cd ~/dotfiles && stow bin
```

**Step 4: Verify**

```bash
cd ~/dotfiles && stow -n -v bin 2>&1
```

Expected: No conflicts.

**Step 5: Commit**

```bash
cd ~/dotfiles && git add bin/ && git commit -m "fix: clean up bin stow package, adopt fix-claude-docs-links"
```

### Task 12: Fix launchagents stow package

The `launchagents` package has zero tracked files (the source plists were removed in Task 0). Two broken stow symlinks remain in `~/Library/LaunchAgents/` pointing at the deleted sources. Re-stowing an empty package is a no-op — these broken links must be cleaned up explicitly.

**Step 1: Unstow to remove broken symlinks**

```bash
cd ~/dotfiles && stow -D launchagents
```

This removes all stow-managed symlinks for the package, including the 2 broken ones (`com.jp.prompt-index-watcher.plist`, `com.jp.zsh-sessions-quarantine.plist`).

**Step 2: Verify broken links are gone**

```bash
ls -la ~/Library/LaunchAgents/com.jp.*.plist 2>/dev/null || echo "No broken symlinks (correct)"
```

Expected: "No broken symlinks (correct)".

**Step 3: Retire the empty package**

The package directory has no tracked content. Remove it from the dotfiles repo:

```bash
trash ~/dotfiles/launchagents
```

**Step 4: Commit**

```bash
cd ~/dotfiles && git add -A launchagents/ && git commit -m "fix: unstow and retire empty launchagents package (broken symlinks cleaned)"
```

**Step 5: Remove from doctor-env stow list**

When executing Task 13, omit `launchagents` from the stow package loop (it no longer exists).

### Task 13: Create doctor-env script

A self-enforcement script that checks all environment invariants.

**Files:**
- Create: `~/dotfiles/bin/.local/bin/doctor-env`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
# doctor-env — Verify environment management invariants
# Run periodically or after dotfiles changes to catch drift.

set -uo pipefail
# NOTE: Do NOT use set -e. Arithmetic operations like ((errors+=1))
# return exit code 1 when the result is 0, which kills the script under -e.

errors=0
warnings=0

pass() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; errors=$((errors + 1)); }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; warnings=$((warnings + 1)); }

echo "doctor-env: checking environment invariants"
echo ""

# 1. Brewfile satisfied
echo "Homebrew:"
if command -v brew &>/dev/null; then
  if brew bundle check --file="$HOME/dotfiles/homebrew/Brewfile" &>/dev/null; then
    pass "Brewfile dependencies satisfied"
  else
    fail "Brewfile has unmet dependencies (run: brew bundle install --file=~/dotfiles/homebrew/Brewfile)"
  fi
else
  warn "brew not found"
fi

# 2. mise healthy
echo "mise:"
if command -v mise &>/dev/null; then
  if mise doctor &>/dev/null; then
    pass "mise doctor reports healthy"
  else
    warn "mise doctor reported issues"
  fi
else
  fail "mise not found"
fi

# 3. No dual-ownership (uv should not be in both brew and mise)
echo "Ownership:"
if command -v brew &>/dev/null; then
  brew_uv="no"
  brew list uv &>/dev/null && brew_uv="yes"
  mise_uv="no"
  grep -Eq '^[[:space:]]*"?uv"?[[:space:]]*=' "$HOME/.config/mise/config.toml" 2>/dev/null && mise_uv="yes"
  if [[ "$brew_uv" == "yes" && "$mise_uv" == "yes" ]]; then
    fail "uv is managed by both brew and mise — pick one owner"
  else
    pass "No dual-ownership detected for uv"
  fi
fi

# 4. Stow links intact
echo "Stow:"
for pkg in zsh bin hammerspoon karabiner kitty nvim starship tmux mise; do
  if [[ -d "$HOME/dotfiles/$pkg" ]]; then
    if (cd "$HOME/dotfiles" && stow -n --ignore=DS_Store "$pkg" >/dev/null 2>&1); then
      pass "stow package '$pkg' is clean"
    else
      fail "stow package '$pkg' has conflicts"
    fi
  fi
done

# 5. Single direnv hook — check for actual hook function calls, not just the word "direnv"
echo "Shell:"
hook_count=0
# Count eval "$(direnv hook zsh)" or _cache_load "direnv" in tools.zsh
grep -qE '(eval "\$\(direnv|_cache_load "direnv)' "$HOME/.config/zsh/tools.zsh" 2>/dev/null && hook_count=$((hook_count + 1))
# Count eval "$(direnv hook zsh)" in .zshrc
grep -qE 'eval "\$\(direnv' "$HOME/.zshrc" 2>/dev/null && hook_count=$((hook_count + 1))
if [[ "$hook_count" -le 1 ]]; then
  pass "direnv hook loaded once"
else
  fail "direnv hook loaded $hook_count times (check .zshrc and tools.zsh)"
fi

# 6. .zprofile is a symlink
if [[ -L "$HOME/.zprofile" ]]; then
  pass ".zprofile is stow-managed (symlink)"
else
  fail ".zprofile is not a symlink — run: cd ~/dotfiles && stow zsh"
fi

# 7. mise config is a symlink
if [[ -L "$HOME/.config/mise/config.toml" ]]; then
  pass "mise config is stow-managed (symlink)"
else
  warn "mise config is not a symlink"
fi

# 8. zsh-rebuild-cache uses trash, not rm (Task 2 regression guard)
if grep -qF 'rm -f' "$HOME/.config/zsh/tools.zsh" 2>/dev/null; then
  fail "tools.zsh contains 'rm -f' — zsh-rebuild-cache regression (should use trash)"
else
  pass "No rm -f in tools.zsh"
fi

echo ""
if [[ $errors -gt 0 ]]; then
  printf "\033[31m%d error(s)\033[0m, %d warning(s)\n" "$errors" "$warnings"
  exit 1
else
  printf "\033[32mAll checks passed\033[0m (%d warning(s))\n" "$warnings"
  exit 0
fi
```

Key fixes from v1:
- `set -uo pipefail` without `-e` — `((errors++))` returns 1 when errors was 0 (falsy), killing the script under `set -e`
- Uses `errors=$((errors + 1))` instead of `((errors++))` for clarity
- Direnv check uses pattern-matching for actual hook invocations instead of `grep -c 'direnv'` which counts comment lines too

Key fixes from v3 (deep-review):
- Dual-ownership grep uses `^[[:space:]]*"?uv"?[[:space:]]*=` to match both quoted and unquoted TOML keys
- Stow check uses stow exit code instead of fragile grep for "conflict" keyword
- Added zsh-rebuild-cache regression check (no `rm -f` in tools.zsh)

**Step 2: Make executable**

```bash
chmod +x ~/dotfiles/bin/.local/bin/doctor-env
```

**Step 3: Stow and verify**

```bash
cd ~/dotfiles && stow bin
doctor-env
```

Expected: All checks pass (assuming prior tasks are complete).

**Step 4: Commit**

```bash
cd ~/dotfiles && git add bin/.local/bin/doctor-env && git commit -m "feat: add doctor-env self-enforcement script"
```

---

## Phase 6: Cleanup

### Task 14: Update claude-dev() function

The `claude-dev()` function in tools.zsh references `superserum` as the default repo name. The project has been renamed to `claude-code-tool-dev`.

**Files:**
- Modify: `~/dotfiles/zsh/.config/zsh/tools.zsh`

**Step 1: Verify target path exists**

```bash
ls -d ~/Projects/active/claude-code-tool-dev/packages/plugins/ || echo "MISSING — create directory or adjust path"
```

Expected: Directory exists. **Do not proceed if missing.**

**Step 2: Update the defaults**

Replace:

```bash
local plugins_dir="${CLAUDE_DEV_PLUGINS:-$HOME/Projects/active/superserum/plugins}"
local repo="${CLAUDE_DEV_REPO:-jpsweeney97/superserum}"
```

With:

```bash
local plugins_dir="${CLAUDE_DEV_PLUGINS:-$HOME/Projects/active/claude-code-tool-dev/packages/plugins}"
local repo="${CLAUDE_DEV_REPO:-jpsweeney97/claude-code-tool-dev}"
```

**Step 3: Commit**

```bash
cd ~/dotfiles && git add zsh/.config/zsh/tools.zsh && git commit -m "fix: update claude-dev repo reference to claude-code-tool-dev"
```

### Task 15: Remove stale named directory

**Files:**
- Modify: `~/dotfiles/zsh/.config/zsh/settings.zsh`

**Step 1: Check if Phaser project exists**

```bash
ls -d ~/Projects/active/Phaser 2>/dev/null || echo "STALE — remove hash -d ph line"
```

If STALE, remove the line `hash -d ph=~/Projects/active/Phaser` from settings.zsh.

**Step 2: Commit (if changed)**

```bash
commit_if_changed zsh/.config/zsh/settings.zsh "fix: remove stale Phaser named directory"
```

### Task 16: Retire environment-improvement directory

The 2.9GB homebrew copy has served its purpose.

**Step 1: Verify all data has been captured**

Checklist:
- [ ] Brewfile generated and curated (Task 8)
- [ ] mise config in dotfiles (Task 9)
- [ ] zsh fixes applied (Tasks 2-5)
- [ ] doctor-env passes (Task 13)

**Step 2: Remove the directory**

```bash
cd ~/Projects/active/claude-code-tool-dev
trash environment-improvement/
```

**Step 3: Verify**

```bash
git -C ~/Projects/active/claude-code-tool-dev status -- environment-improvement/
```

Expected: `environment-improvement/` no longer appears (it was untracked).

### Task 17: Update MIGRATION-LOG.md and run final verification

**Step 1: Mark all phases complete**

Update `~/dotfiles/MIGRATION-LOG.md` to mark all checkboxes done and add a post-migration summary.

**Step 2: Run doctor-env**

```bash
doctor-env
```

Expected: All checks pass, 0 errors.

**Step 3: Verify shell loads correctly**

```bash
zsh -lic '
  echo "uv: $(which uv)"
  echo "bat: $(which bat)"
  echo "direnv: $(typeset -f _direnv_hook | head -1)"
  echo "PIPX_PYTHON: $PIPX_DEFAULT_PYTHON"
  zsh-rebuild-cache 2>&1 | head -1
'
```

Expected:
- `uv`: mise shim path
- `bat`: `/opt/homebrew/bin/bat`
- `direnv`: function definition
- `PIPX_PYTHON`: mise python path
- `zsh-rebuild-cache`: "Cache cleared..." message

**Step 4: Final commit**

```bash
cd ~/dotfiles && git add MIGRATION-LOG.md && git commit -m "docs: mark environment migration complete"
```

**Step 5: Push to origin**

After verifying everything works, push all migration commits to the remote:

```bash
cd ~/dotfiles && git push
```

The pre-push hook (Task 19) will run doctor-env as a final gate. If it fails, fix the issue before retrying.

### Task 18: Create ownership decision document

The ownership matrix (what Homebrew owns vs mise vs stow) is the plan's core intellectual contribution. Without a durable document, this knowledge lives only in plan prose and commit messages.

**Files:**
- Create: `~/dotfiles/OWNERSHIP.md`

**Step 1: Write the ownership document**

Create `~/dotfiles/OWNERSHIP.md`:

```markdown
# Tool Ownership Matrix

**Governing principle:** One executable, one owner. No tool managed by two package managers.

## Layers

| Layer | Tool | Scope | Change Frequency |
|-------|------|-------|-----------------|
| System packages | Homebrew (Brewfile) | OS-level CLIs, GUI apps, shell plugins | Monthly |
| Language runtimes | mise (config.toml) | Runtimes, version-pinned dev tools | Weekly |
| Configuration | GNU stow (~/dotfiles/) | Dotfile deployment | Daily |

## Ownership Rules

| Category | Owner | Examples |
|----------|-------|---------|
| OS-level CLI tools | Homebrew | bat, eza, fd, ripgrep, jq, htop |
| GUI applications | Homebrew (cask) | Docker Desktop, Kitty, VS Code |
| Shell plugins | Homebrew | zsh-syntax-highlighting, zsh-autosuggestions |
| Language runtimes | mise | node, python, go, rust |
| Language-specific dev tools | mise | ruff, pytest, prettier, cargo-nextest |
| uv (Python package manager) | mise | Previously dual-owned (brew + mise) |
| Dotfile deployment | stow | .zshrc, .zshenv, .zprofile, tools.zsh |
| mise config | stow | ~/.config/mise/config.toml |

## Adding New Tools

1. Is it a language runtime or language-specific tool? → **mise**
2. Is it an OS-level CLI or GUI app? → **Homebrew**
3. Is it a configuration file? → **stow** (via ~/dotfiles/)
4. Run `doctor-env` after adding to verify no dual ownership

## Update Policy

- **Homebrew:** `brew bundle install --file=~/dotfiles/homebrew/Brewfile` after Brewfile changes
- **mise:** `mise install` after config.toml changes (auto-detected via stow symlink)
- **stow:** `cd ~/dotfiles && stow <package>` after adding files to a package

## Enforcement

`doctor-env` checks: Brewfile satisfaction, mise health, no dual ownership, stow link integrity, single direnv hook, symlink state, no rm -f regression.

Updated: 2026-03-01
```

**Step 2: Commit**

```bash
cd ~/dotfiles && git add OWNERSHIP.md && git commit -m "docs: add tool ownership matrix and update policy"
```

### Task 19: Install doctor-env git hooks

Without automation, doctor-env is write-once-run-never. Git hooks provide event-driven enforcement at commit and push time.

**Files:**
- Create: `~/dotfiles/.githooks/post-commit`
- Create: `~/dotfiles/.githooks/pre-push`

**WARNING:** Step 4 sets `core.hooksPath` to `.githooks/`, which makes git **stop reading `.git/hooks/` entirely**. The existing `pre-commit` hook at `.git/hooks/pre-commit` (which runs `sanity-check.sh`) will silently stop working. Step 1b migrates it.

**Step 1: Create hooks directory**

```bash
mkdir -p ~/dotfiles/.githooks
```

**Step 1b: Migrate existing pre-commit hook**

The existing pre-commit hook lives at `.git/hooks/pre-commit` and runs `sanity-check.sh`. Copy it to the new hooks directory so it continues to work after `core.hooksPath` is set.

```bash
cp ~/dotfiles/.git/hooks/pre-commit ~/dotfiles/.githooks/pre-commit
chmod +x ~/dotfiles/.githooks/pre-commit
```

Verify both will coexist:
```bash
head -5 ~/dotfiles/.githooks/pre-commit
```

Expected: The sanity-check.sh pre-commit hook header.

**Step 2: Create post-commit hook**

Create `~/dotfiles/.githooks/post-commit`:

```bash
#!/usr/bin/env bash
# Run doctor-env after each commit to catch drift early.
# Failures are reported but do not block the commit (it's already done).

if command -v doctor-env &>/dev/null; then
  echo ""
  echo "Running post-commit environment check..."
  doctor-env || echo "doctor-env reported issues — run 'doctor-env' for details."
fi
```

**Step 3: Create pre-push hook**

Create `~/dotfiles/.githooks/pre-push`:

```bash
#!/usr/bin/env bash
# Block push if doctor-env fails — don't push broken dotfiles.

if command -v doctor-env &>/dev/null; then
  echo "Running pre-push environment check..."
  if ! doctor-env; then
    echo ""
    echo "Push blocked: doctor-env reported errors."
    echo "Fix the issues above, then push again."
    echo "To bypass: git push --no-verify"
    exit 1
  fi
fi
```

**Step 4: Make executable and configure git**

```bash
chmod +x ~/dotfiles/.githooks/post-commit ~/dotfiles/.githooks/pre-push
cd ~/dotfiles && git config core.hooksPath .githooks
```

**Step 5: Verify**

```bash
cd ~/dotfiles && git config core.hooksPath
```

Expected: `.githooks`

**Step 6: Commit**

```bash
cd ~/dotfiles && git add .githooks/ && git commit -m "feat: add doctor-env git hooks (post-commit, pre-push)"
```

---

## Dependency Graph

```
Task 0 (clean working tree) ── MUST complete before all other tasks
  │
  Task 1 (prerequisites + snapshot)
  │
  ├── Task 2 (tools.zsh atomic edit: rebuild-cache + reorder + direnv + FZF)
  │     └── Task 3 (.zshrc direnv removal) ── depends on Task 2
  │
  ├── Task 4 (gitignore dedup) ── independent
  │
  └── Task 5 (mise guard) ── independent
        │
        Task 6 (clean .DS_Store) ── depends on Tasks 2-5
          │
          Task 7 (stow .zprofile) ── depends on Task 6
            │
            ├── Task 8 (Brewfile) ── parallel with Task 9
            └── Task 9 (mise config)
                  │
                  ├── Task 10 (remove brew uv) ── depends on Task 8
                  ├── Task 11 (bin stow fix)
                  └── Task 12 (launchagents cleanup + retire)
                        │
                        Task 13 (doctor-env) ── depends on Tasks 8, 9, 10-12
                        │  (explicit: checks Brewfile from Task 8, mise symlink from Task 9)
                          │
                          ├── Task 14 (claude-dev update)
                          ├── Task 15 (stale named dir)
                          ├── Task 18 (ownership doc) ── independent of 14, 15
                          └── Task 19 (doctor-env git hooks) ── depends on Task 13
                                │
                                Task 16 (retire env-improvement) ── depends on Tasks 13-15, 18-19
                                  │
                                  Task 17 (final verification) ── depends on all
```

## Parallelization

**Independent tasks (can be executed in any order, but NOT concurrently):**
- Tasks 4 and 5 (different files: `.gitignore` vs `settings.zsh`)
- Tasks 8 and 9 (different manifests: Brewfile vs mise config)
- Tasks 11 and 12 (different stow packages: bin vs launchagents)

Note: "Independent" means no data dependencies between them. They still share a git repo, so `git commit` acquires `.git/index.lock` — truly concurrent commits will fail. Execute them sequentially but in any order.

**Strictly sequential:**
- Tasks 2 and 3 (both modify zsh config; Task 3 depends on Task 2's direnv fix)
- Tasks 2, 4, 5 with Task 6 (Task 6 should follow all shell fixes)
- Tasks 14, 15, 18, and 19 (all commit to `~/dotfiles` — git lock contention; Task 19 also changes `core.hooksPath`, altering commit behavior for concurrent tasks)

## Rollback

If anything breaks mid-migration:

1. **Shell won't load:** `env PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH" ZDOTDIR=/tmp zsh` to get a minimal shell with Homebrew in PATH, then `cd ~/dotfiles && git diff` to see what changed
2. **Stow conflicts:** `cd ~/dotfiles && stow -D <package>` to unstow, fix conflict, restow
3. **Brewfile wrong:** `brew bundle install --file=~/dotfiles/homebrew/Brewfile` to reconcile
4. **Full rollback:** `cd ~/dotfiles && git log --oneline` and `git revert` the migration commits
5. **Restore .zprofile:** First unstow: `cd ~/dotfiles && stow -D zsh`, then restore: `cp ~/.zprofile.bak.$(date +%Y%m%d) ~/.zprofile` (use exact filename — glob `*.bak.*` may match multiple files and cause `cp` to fail)
6. **Restore mise config:** First unstow: `cd ~/dotfiles && stow -D mise`, then restore: `cp ~/.config/mise/config.toml.bak ~/.config/mise/config.toml`
7. **Restore brew uv:** `brew install uv` (if Task 10 removed it and mise uv is broken)
8. **Remove git hooks:** `cd ~/dotfiles && git config --unset core.hooksPath` (if Task 19 hooks are blocking operations)
9. **Restore pre-migration state:** `cd ~/dotfiles && git stash pop` (if Task 0 stashed changes)
10. **Partial stow cleanup:** If `stow` partially completed (some symlinks created, then hit a conflict), `stow -D <package>` may also fail. Manual cleanup: `find ~ -maxdepth 3 -lname '*/dotfiles/<package>/*' -exec trash {} +` to remove stow-created symlinks, then fix the conflict and restow
