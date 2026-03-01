# Claude Environment Awareness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Make Claude Code fully aware of the macOS environment ownership model (Homebrew/mise/stow) and enforce compliance through documentation + targeted hooks.

**Architecture:** Documentation-first with graduated enforcement. Five components: updated environment reference, global CLAUDE.md rules, dotfiles project CLAUDE.md, extended ownership enforcement hook, and SessionStart doctor-env injection.

**Tech Stack:** Markdown (CLAUDE.md, environment.md), Python (hooks), JSON (settings.json)

**Design doc:** `docs/plans/2026-03-01-claude-environment-awareness-design.md`

---

## Task 1: Rewrite `~/.claude/references/environment.md`

The source of truth for the ownership model. Loaded into every session via global CLAUDE.md reference.

**Files:**
- Modify: `~/.claude/references/environment.md`

**Step 1: Replace the entire file with the updated content**

```markdown
# Environment Reference

## System

- **OS:** macOS Tahoe (Darwin 25.3.0), Apple Silicon (`/opt/homebrew`)
- **Shell:** zsh (starship prompt)
- **Editor:** VS Code, Claude Code CLI
- **Dotfiles:** `~/dotfiles/` managed by GNU stow

## Tool Ownership Model

One executable, one owner. No tool managed by two package managers.

| Layer | Manager | Scope | Source of Truth |
|-------|---------|-------|-----------------|
| System packages | Homebrew | OS-level CLIs, GUI apps, shell plugins | `~/dotfiles/homebrew/Brewfile` |
| Runtimes + dev tools | mise | Language runtimes, version-pinned dev tools | `~/dotfiles/mise/.config/mise/config.toml` (stow-managed) |
| Configuration | GNU stow | Dotfile deployment from `~/dotfiles/` | `~/dotfiles/<package>/` directories |

### Ownership Rules

| Category | Owner | Examples |
|----------|-------|---------|
| OS-level CLI tools | Homebrew | bat, eza, fd, ripgrep, jq, htop, stow, mise |
| GUI applications | Homebrew (cask) | Docker Desktop, Kitty, VS Code |
| Shell plugins | Homebrew | zsh-syntax-highlighting, zsh-autosuggestions |
| Language runtimes | mise | node, python, go, rust |
| Language-specific dev tools | mise | uv, ruff, pytest, prettier, cargo-nextest |
| Dotfile deployment | stow | .zshrc, .zshenv, .zprofile, tools.zsh |

### Adding a New Tool

1. Language runtime or language-specific tool? → `mise use <tool>@<version>` in `~/.config/mise/config.toml`
2. OS-level CLI or GUI app? → Add to `~/dotfiles/homebrew/Brewfile`, run `brew bundle install --file=~/dotfiles/homebrew/Brewfile`
3. Configuration file? → Add to `~/dotfiles/<package>/`, run `cd ~/dotfiles && stow <package>`
4. Run `doctor-env` after adding to verify no dual ownership

### Violations

- **Never** `brew install` a mise-owned tool (uv, ruff, node, python, go, rust, or anything in mise config)
- **Never** bypass stow by writing directly to `~/.<dotfile>` — edit in `~/dotfiles/` and stow
- **Never** `brew uninstall stow` or `brew uninstall mise` — these are infrastructure

## Environment Invariants

`doctor-env` verifies: Brewfile satisfaction, mise health, no dual ownership (uv), stow link integrity (9 packages), single direnv hook, .zprofile symlink, mise config symlink, no rm -f regression in tools.zsh.

Run: `doctor-env` (available via stow bin package at `~/.local/bin/doctor-env`)

## Dotfiles Architecture

```
~/dotfiles/
├── bin/           → ~/.local/bin/ (scripts, doctor-env)
├── hammerspoon/   → ~/.hammerspoon/
├── karabiner/     → ~/.config/karabiner/
├── kitty/         → ~/.config/kitty/
├── mise/          → ~/.config/mise/
├── nvim/          → ~/.config/nvim/
├── starship/      → ~/.config/starship.toml
├── tmux/          → ~/.tmux.conf
├── zsh/           → ~/.zshrc, ~/.zprofile, ~/.config/zsh/
├── homebrew/      → NOT stowed (Brewfile used directly by brew bundle)
├── .githooks/     → pre-commit, post-commit, pre-push (via core.hooksPath)
├── OWNERSHIP.md   → Tool ownership matrix
└── MIGRATION-LOG.md
```

## Shell

| Alias | Replaces | Notes |
|-------|----------|-------|
| `rg` | `grep -E` | ripgrep syntax |
| `eza` | `ls` | plain: `command ls` |
| `bat` | `cat` | plain: `command cat` |
| `trash` | `rm` | **Required.** Never use `rm`. |

## Common Commands

```bash
# Testing and linting
uv run pytest tests/    # test
ruff check .            # lint
ruff format .           # format

# Environment management
doctor-env                                                    # check invariants
brew bundle install --file=~/dotfiles/homebrew/Brewfile        # reconcile brew
mise install                                                   # reconcile mise
cd ~/dotfiles && stow <package>                                # deploy dotfiles
cd ~/dotfiles && stow -n -v <package>                          # dry-run stow

# Deletion
trash <path>            # move to macOS Trash (REQUIRED — never rm)
```
```

**Step 2: Verify the file is valid markdown and under 100 lines**

```bash
wc -l ~/.claude/references/environment.md
```

Expected: ~90 lines.

---

## Task 2: Update global `~/.claude/CLAUDE.md`

Add environment rules section and update the Environment section.

**Files:**
- Modify: `~/.claude/CLAUDE.md`

**Step 1: Add Environment Rules section**

Insert this section AFTER the existing `## Environment` section (after line 140, before `## Git`):

```markdown
## Environment Rules

**Ownership model:** One executable, one owner. Homebrew for OS-level, mise for runtimes/dev tools, stow for config. See `~/.claude/references/environment.md` for full details.

**Hard rules:**
- Never `brew install` a mise-owned tool (uv, ruff, node, python, go, rust). Use `mise use` instead.
- Never write directly to `~/.<dotfile>`. Edit in `~/dotfiles/` and stow.
- Never `brew uninstall stow` or `brew uninstall mise`.
- Run `doctor-env` after environment changes to verify compliance.

**Dotfiles repo:** `~/dotfiles/` — all config changes go here, deployed via `stow`.
```

**Step 2: Verify the edit didn't break surrounding sections**

Read the file and confirm `## Environment`, `## Environment Rules`, and `## Git` appear in that order.

---

## Task 3: Create `~/dotfiles/.claude/CLAUDE.md`

Project-level context for working directly in the dotfiles repo.

**Files:**
- Create: `~/dotfiles/.claude/CLAUDE.md`

**Step 1: Create the directory**

```bash
mkdir -p ~/dotfiles/.claude
```

**Step 2: Write the file**

```markdown
# Dotfiles Project

GNU stow-managed dotfiles for macOS. Changes here deploy to `~/` via symlinks.

## Stow Conventions

- Package structure: `<package>/<target-path-relative-to-home>`
- Example: `zsh/.config/zsh/tools.zsh` deploys to `~/.config/zsh/tools.zsh`
- Dry-run before stow: `cd ~/dotfiles && stow -n -v <package>`
- Always use `--ignore=DS_Store` in scripts that check stow status
- Stow packages: zsh, bin, hammerspoon, karabiner, kitty, nvim, starship, tmux, mise
- `homebrew/` is NOT a stow package — `Brewfile` is used directly by `brew bundle`

## Editing Rules

**Critical-path files** (syntax error prevents shell startup):
- `zsh/.config/zsh/tools.zsh` — verify after edits: `zsh -lc 'echo ok'`
- `zsh/.zshrc` — verify after edits: `zsh -lc 'echo ok'`
- `zsh/.zprofile` — verify after edits: `zsh -lc 'echo $ZPROFILE_LOADED'`

**Never edit live files directly.** Edit in `~/dotfiles/`, then stow. Stow creates symlinks — the live file IS the dotfiles file.

**Verification convention:** Use `zsh -lc '...'` (one-shot login shell) for all shell verification. Never `exec zsh`.

## Commit Conventions

- Commit per logical change (not per file)
- Use `git add <specific-files>` — never `git add -A` (captures unrelated changes across packages)
- Conditional commits for operations that may produce no git changes:

```bash
commit_if_changed() {
  local path="$1" msg="$2"
  cd ~/dotfiles
  local has_changes=false
  git diff --quiet -- "$path" || has_changes=true
  git diff --cached --quiet -- "$path" || has_changes=true
  [[ -n "$(git ls-files --others --exclude-standard -- "$path")" ]] && has_changes=true
  if $has_changes; then
    git add "$path" && git commit -m "$msg"
  else
    echo "No changes in $path — skipping commit."
  fi
}
```

## Doctor-env

Run after any change: `doctor-env`

Checks: Brewfile satisfaction, mise health, no dual ownership (uv), stow link integrity (9 packages), single direnv hook, .zprofile symlink, mise config symlink, no rm -f regression.

Location: `bin/.local/bin/doctor-env` (deployed via `stow bin`)

## Git Hooks

Located in `.githooks/` (via `core.hooksPath`):
- **pre-commit:** runs `sanity-check.sh` (invariant checks)
- **post-commit:** runs `doctor-env` (non-blocking — reports but doesn't fail)
- **pre-push:** runs `doctor-env` (blocking — push fails if doctor-env fails)

## Adding a New Stow Package

1. `mkdir -p ~/dotfiles/<name>/<target-path>`
2. Add files to the package directory
3. `cd ~/dotfiles && stow <name>`
4. Add `<name>` to the doctor-env stow loop (in `bin/.local/bin/doctor-env`, check #4)
5. `git add <name>/ && git commit -m "feat: add <name> stow package"`
```

**Step 3: Commit the new CLAUDE.md to the dotfiles repo**

```bash
cd ~/dotfiles && git add .claude/CLAUDE.md && git commit -m "docs: add Claude Code project context for dotfiles"
```

---

## Task 4: Extend `~/.claude/hooks/mise-tool-guidance.py` to cover `brew install`

The existing hook handles `pipx install`, `cargo install`, and `go install`. It needs to also catch `brew install` of mise-owned tools and `brew uninstall` of infrastructure tools.

**Files:**
- Modify: `~/.claude/hooks/mise-tool-guidance.py`

**Step 1: Add `brew install` to the install_patterns list**

In the `main()` function, find the `install_patterns` list:

```python
install_patterns = [
    (r"pipx\s+install\s+(\S+)", "pipx"),
    (r"cargo\s+install\s+(\S+)", "cargo"),
    (r"go\s+install\s+(\S+)", "go"),
]
```

Replace with:

```python
install_patterns = [
    (r"brew\s+install\s+(\S+)", "brew"),
    (r"pipx\s+install\s+(\S+)", "pipx"),
    (r"cargo\s+install\s+(\S+)", "cargo"),
    (r"go\s+install\s+(\S+)", "go"),
]
```

**Step 2: Add infrastructure protection**

After the install pattern loop (after the `# No installation detected` comment), add a check for `brew uninstall` of infrastructure tools:

```python
        # Block uninstalling infrastructure tools
        infra_tools = {"stow", "mise"}
        uninstall_match = re.search(r"brew\s+uninstall\s+(\S+)", command)
        if uninstall_match:
            tool_name = uninstall_match.group(1)
            if tool_name in infra_tools:
                print(
                    f"'{tool_name}' is infrastructure — do not uninstall. "
                    f"stow manages dotfile deployment; mise manages runtimes.",
                    file=sys.stderr,
                )
                sys.exit(2)
```

**Step 3: Update the module docstring**

Update the docstring at the top of the file to reflect the expanded coverage:

```python
"""
PreToolUse hook: Enforces tool ownership boundaries.
Blocks installing mise-managed tools via brew/pipx/cargo/go.
Blocks uninstalling infrastructure tools (stow, mise).
Provides guidance for unknown tool installations.

Exit codes:
  0 - Allow (stdout guidance shown in verbose mode)
  2 - Block (tool is managed by mise or is infrastructure)
"""
```

**Step 4: Test the hook manually**

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"brew install uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```

Expected: stderr message about uv being mise-managed, exit code 2.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```

Expected: exit code 0 (bat is not mise-managed).

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"brew uninstall stow"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```

Expected: stderr message about infrastructure, exit code 2.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"brew uninstall bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```

Expected: exit code 0 (bat is not infrastructure).

**Step 5: No commit needed** — this is in `~/.claude/hooks/`, not a git-tracked location.

---

## Task 5: Create SessionStart hook for doctor-env in dotfiles

Runs doctor-env when starting a Claude session in `~/dotfiles/` and injects results into context.

**Files:**
- Create: `~/dotfiles/.claude/settings.json`

**Step 1: Create the settings file**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "if command -v doctor-env >/dev/null 2>&1; then output=$(doctor-env 2>&1); rc=$?; if [ $rc -eq 0 ]; then echo 'Environment healthy: doctor-env passed all checks.'; else echo \"doctor-env found issues:\n$output\"; fi; else echo 'doctor-env not found — run: cd ~/dotfiles && stow bin'; fi"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Verify the JSON is valid**

```bash
python3 -m json.tool ~/dotfiles/.claude/settings.json
```

Expected: Pretty-printed JSON, no errors.

**Step 3: Commit**

```bash
cd ~/dotfiles && git add .claude/settings.json && git commit -m "feat: add SessionStart hook for doctor-env context injection"
```

---

## Task 6: Push dotfiles changes and verify end-to-end

**Step 1: Run doctor-env**

```bash
doctor-env
```

Expected: All checks pass.

**Step 2: Push dotfiles commits**

```bash
cd ~/dotfiles && git push
```

Pre-push hook runs doctor-env as gate.

**Step 3: Verify Claude awareness**

Start a new Claude session in `~/dotfiles/` and check:
- Does the SessionStart hook inject doctor-env output?
- Does Claude know the ownership rules (from global CLAUDE.md)?
- Does `brew install uv` trigger the hook warning?

This step is manual verification in a new session.

---

## Dependency Graph

```
Task 1 (environment.md) ── independent
Task 2 (global CLAUDE.md) ── depends on Task 1 (references environment.md)
Task 3 (dotfiles CLAUDE.md) ── independent
Task 4 (extend hook) ── independent
Task 5 (SessionStart hook) ── independent
Task 6 (push + verify) ── depends on Tasks 3, 5
```

Tasks 1, 3, 4, 5 are independent and can be executed in any order.
Task 2 should follow Task 1.
Task 6 is the final verification.
