# Claude Environment Awareness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Make Claude Code fully aware of the macOS environment ownership model (Homebrew/mise/stow) and enforce compliance through documentation + targeted hooks.

**Architecture:** Documentation-first with graduated enforcement. Five components: updated environment reference, global CLAUDE.md rules, dotfiles project CLAUDE.md, extended ownership enforcement hook, and SessionStart doctor-env injection.

**Tech Stack:** Markdown (CLAUDE.md, environment.md), Python (hooks), JSON (settings.json)

**Design doc:** `docs/plans/2026-03-01-claude-environment-awareness-design.md`

---

## Codex Review Findings

Adversarial Codex dialogue (8-turn budget, converged at turn 6). Thread: `019cab8c-c4f0-7161-bf86-92a35e5a4995`.

### Ship-Blockers (fixed in plan)

| # | Finding | Fix |
|---|---------|-----|
| 1 | PreToolUse warnings use `print()` + `exit(0)` — stdout invisible to Claude on exit 0 | JSON `hookSpecificOutput.additionalContext` for warn-but-allow |
| 2 | Brew regex `r"brew\s+install\s+(\S+)"` misses `--cask`, `reinstall`, flags, multi-package, tap-qualified | Operation-detecting regex with flag stripping + package normalization |

### Should-Fix (fixed in plan)

| # | Finding | Fix |
|---|---------|-----|
| 3 | No enforcement tier distinction (install vs uninstall vs bundle) | Three-tier: warn install, block uninstall infra, allow bundle |
| 4 | SessionStart hook missing `matcher` — fires on clear/compact | `matcher: "startup\|resume"` |
| 5 | `commit_if_changed()` in CLAUDE.md as function — unreliable across isolated shell calls | Script at `~/dotfiles/bin/.local/bin/commit-if-changed` |
| 6 | No explicit fail-open policy for internal hook errors | Exit 1 + stderr for internal errors |
| 7 | Task 2 uses line-number placement — fragile | Heading-anchored `###` subsection |

### Deferred

- Brewfile lint guard (implement separately if needed)
- `doctor-env` output sanitization/capping before context injection
- `brew upgrade` warning for infrastructure tools
- Flag handling consistency across pipx/cargo/go patterns
- Direct dotfile write enforcement (Edit/Write/MultiEdit bypass stow) — PreToolUse hook on `Bash` matcher cannot see file-editing tool calls. Tool-surface coverage limitation; document in design doc.

### Deep Review Findings (evaluative)

Evaluative Codex dialogue (8-turn budget, converged at turn 5). Thread: `019cabba-e7d0-7300-b43b-e3b060363f46`.

#### Ship-Blockers (fixed in plan)

| # | Finding | Fix |
|---|---------|-----|
| 8 | Tier 1 install loop exits on first match — `brew install bat uv` warns about `bat`, never checks `uv` | Partition all packages into managed/non-managed, emit single aggregated warning |
| 9 | `rc=${PIPESTATUS[0]:-$?}` after `|| true` — PIPESTATUS is for pipelines only, `|| true` masks exit code to 0 | `if/else` pattern with `case` for 0/124/137/other, resolve timeout vs gtimeout |
| 10 | Task 5 settings.json uses flat structure — must be nested `{matcher, hooks:[{type,command}]}` | Match production `~/.claude/settings.json` nested structure, use `bash "$HOME/..."` |

#### Should-Fix (fixed in plan)

| # | Finding | Fix |
|---|---------|-----|
| 11 | Empty `tool_names` fall-through (e.g., `brew install --cask` with no packages) reaches pipx/cargo/go parsing | Explicit `sys.exit(0)` at end of `if brew_match:` branch |
| 12 | Global brew flags before subcommand (`brew --quiet install uv`) bypass regex | Handle optional pre-subcommand flags in regex |
| 13 | Design doc promises "direct dotfile write (bypass stow)" enforcement but plan doesn't implement or defer | Added to Deferred with tool-surface scope statement |

### Agent-Team Review Findings

4-agent parallel review (doc, hook-logic, shell/config, integration). 0 ship-blockers found.

#### Should-Fix (fixed in plan)

| # | Finding | Fix |
|---|---------|-----|
| 14 | `commit-if-changed` commits unrelated staged files — `git commit` without path restriction | Added `-- "$path"` to `git commit` |
| 15 | stow/mise listed as normal Homebrew examples but also protected as infrastructure — contradictory | Separated into "Infrastructure" row in ownership table |
| 16 | Design doc says script "detects cwd" but actual mechanism is project-scoped `settings.json` | Updated design doc description |
| 17 | "Adding a New Tool" points to deployed symlink, not stow source path | Changed to `~/dotfiles/mise/.config/mise/config.toml` with symlink note |

#### Not Applied (acceptable as-is)

| # | Finding | Disposition |
|---|---------|-------------|
| — | Tier 2 blocks on first infra match without scanning all | Correct for blocking — safe direction |
| — | `elif` drops non-managed guidance in mixed installs | Managed warning is higher priority |
| — | `set -o pipefail` is a no-op in doctor-env-inject.sh | Cosmetic — no runtime impact |
| — | Plan doesn't note "preserve existing imports" for Task 4 | Clarity only — imports already exist |

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
| OS-level CLI tools | Homebrew | bat, eza, fd, ripgrep, jq, htop |
| Infrastructure (Homebrew-installed, never uninstall) | Homebrew | stow, mise |
| GUI applications | Homebrew (cask) | Docker Desktop, Kitty, VS Code |
| Shell plugins | Homebrew | zsh-syntax-highlighting, zsh-autosuggestions |
| Language runtimes | mise | node, python, go, rust |
| Language-specific dev tools | mise | uv, ruff, pytest, prettier, cargo-nextest |
| Dotfile deployment | stow | .zshrc, .zshenv, .zprofile, tools.zsh |

### Adding a New Tool

1. Language runtime or language-specific tool? → `mise use <tool>@<version>` in `~/dotfiles/mise/.config/mise/config.toml` (stow-managed → `~/.config/mise/config.toml`)
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

**Step 1: Add Environment Rules subsection**

Find the `## Environment` section in `~/.claude/CLAUDE.md`. Insert a `### Environment Rules` subsection at the end of the Environment section, before the next `##` heading (typically `## Git`). Do NOT use line numbers — find the heading anchor.

```markdown
### Environment Rules

**Ownership model:** One executable, one owner. Homebrew for OS-level, mise for runtimes/dev tools, stow for config. See `~/.claude/references/environment.md` for full details.

**Hard rules:**
- Never `brew install` a mise-owned tool (uv, ruff, node, python, go, rust). Use `mise use` instead.
- Never write directly to `~/.<dotfile>`. Edit in `~/dotfiles/` and stow.
- Never `brew uninstall stow` or `brew uninstall mise`.
- Run `doctor-env` after environment changes to verify compliance.

**Dotfiles repo:** `~/dotfiles/` — all config changes go here, deployed via `stow`.
```

**Step 2: Verify the edit didn't break surrounding sections**

Read the file and confirm `## Environment` contains `### Environment Rules` as a subsection, and `## Git` follows after.

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
- For conditional commits: `commit-if-changed <path> <message>` (script at `bin/.local/bin/commit-if-changed`, deployed via `stow bin`)

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

**Step 3: Create the `commit-if-changed` script**

Write `~/dotfiles/bin/.local/bin/commit-if-changed`:

```bash
#!/usr/bin/env bash
# Usage: commit-if-changed <path> <message>
# Commits <path> in ~/dotfiles only if there are actual changes (staged, unstaged, or untracked).
set -euo pipefail

path="${1:?Usage: commit-if-changed <path> <message>}"
msg="${2:?Usage: commit-if-changed <path> <message>}"
cd ~/dotfiles

has_changes=false
git diff --quiet -- "$path" 2>/dev/null || has_changes=true
git diff --cached --quiet -- "$path" 2>/dev/null || has_changes=true
[[ -n "$(git ls-files --others --exclude-standard -- "$path" 2>/dev/null)" ]] && has_changes=true

if $has_changes; then
    git add "$path" && git commit -m "$msg" -- "$path"
else
    echo "No changes in $path — skipping commit."
fi
```

```bash
chmod +x ~/dotfiles/bin/.local/bin/commit-if-changed
```

**Step 4: Commit both files to the dotfiles repo**

```bash
cd ~/dotfiles && git add .claude/CLAUDE.md bin/.local/bin/commit-if-changed && git commit -m "feat: add Claude Code project context and commit-if-changed script"
```

---

## Task 4: Extend `~/.claude/hooks/mise-tool-guidance.py` — three-tier enforcement

The existing hook handles `pipx install`, `cargo install`, and `go install`. This task adds three-tier brew enforcement and fixes the existing invisible-guidance bug (stdout on exit 0 is invisible to Claude for PreToolUse hooks).

**Three-tier model:**
- **Tier 1 (warn):** `brew install`/`brew reinstall` of mise-managed tools → exit 0 + JSON `additionalContext`
- **Tier 2 (block):** `brew uninstall`/`remove`/`rm` of infrastructure (stow, mise) → exit 2 + stderr
- **Tier 3 (allow):** `brew bundle` → exit 0 (no output)

**Also fixes:** The existing pipx/cargo/go guidance path uses `print()` + `exit(0)`, which is invisible to Claude. All non-blocking guidance must use JSON `hookSpecificOutput.additionalContext`.

**Files:**
- Modify: `~/.claude/hooks/mise-tool-guidance.py`

**Step 1: Replace the module docstring**

```python
"""
PreToolUse hook: Enforces tool ownership boundaries.

Three-tier brew enforcement:
  Tier 1 (warn):  brew install/reinstall of mise-managed tools
                   → exit 0 + JSON additionalContext
  Tier 2 (block): brew uninstall/remove/rm of infrastructure (stow, mise)
                   → exit 2 + stderr
  Tier 3 (allow): brew bundle (operates on Brewfile)
                   → exit 0 (no output)

Also blocks mise-managed tools via pipx/cargo/go (exit 2).
Provides guidance for unknown tool installations (exit 0 + additionalContext).

Exit codes:
  0 - Allow (JSON additionalContext injected into Claude's context)
  1 - Internal error (fail open — command proceeds, error logged)
  2 - Block (stderr message shown to Claude)

Fail-open policy: Internal errors (malformed input, missing config) exit 1.
Allows command to proceed while preserving observability via stderr.
"""
```

**Step 2: Add a helper function for JSON additionalContext output**

Add after the `load_mise_tools()` function:

```python
def emit_guidance(message: str) -> None:
    """Emit warn-but-allow guidance via JSON additionalContext.

    PreToolUse stdout on exit 0 is invisible to Claude unless structured
    as hookSpecificOutput JSON. Plain print() is only visible in verbose mode.
    """
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": message,
        }
    }
    print(json.dumps(result))
```

**Step 3: Replace the `main()` function body**

```python
def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        mise_managed = load_mise_tools()

        # --- brew operations (three-tier enforcement) ---
        brew_match = re.search(
            r"brew\s+(?:-[-\w]+\s+)*(install|reinstall|uninstall|remove|rm|bundle)\b(.*)",
            command,
        )
        if brew_match:
            operation = brew_match.group(1)
            args_str = brew_match.group(2)

            # Tier 3: Allow — brew bundle operates on Brewfile
            if operation == "bundle":
                sys.exit(0)

            # Extract tool names: strip flags, normalize
            raw_args = args_str.split()
            tool_names = []
            for arg in raw_args:
                if arg.startswith("-"):
                    continue  # Skip flags (--cask, -q, --force, etc.)
                # Normalize: strip tap prefix and @version
                name = arg.split("/")[-1].split("@")[0]
                if name:
                    tool_names.append(name)

            # Tier 2: Block — uninstall/remove/rm of infrastructure
            infra_tools = {"stow", "mise"}
            if operation in ("uninstall", "remove", "rm"):
                for name in tool_names:
                    if name in infra_tools:
                        print(
                            f"'{name}' is infrastructure — do not uninstall. "
                            f"stow manages dotfile deployment; mise manages runtimes.",
                            file=sys.stderr,
                        )
                        sys.exit(2)
                sys.exit(0)

            # Tier 1: Warn — install/reinstall of mise-managed tools
            # Scan ALL packages before deciding. Previous version exited on first
            # match, so `brew install bat uv` would warn about bat and miss uv.
            if operation in ("install", "reinstall"):
                managed_found = []
                non_managed_found = []
                for name in tool_names:
                    if name in EXCEPTIONS:
                        continue
                    if name in mise_managed:
                        managed_found.append(name)
                    else:
                        non_managed_found.append(name)

                if managed_found:
                    names = ", ".join(dict.fromkeys(managed_found))
                    emit_guidance(
                        f"WARNING: {names} managed by mise. "
                        f"Use `mise use <tool>` instead of `brew {operation}`. "
                        f"Dual ownership creates conflicts. "
                        f"See ~/.claude/references/environment.md for ownership model."
                    )
                elif non_managed_found:
                    names = ", ".join(dict.fromkeys(non_managed_found))
                    emit_guidance(
                        f"Note: Consider adding {names} to "
                        f"~/.config/mise/config.toml if these are dev tools "
                        f"you'll use across projects."
                    )

            # All brew paths exit here — prevents fall-through to pipx/cargo/go
            # parsing when tool_names is empty (e.g., `brew install --cask`)
            sys.exit(0)

        # --- pipx/cargo/go operations ---
        install_patterns = [
            (r"pipx\s+install\s+(\S+)", "pipx"),
            (r"cargo\s+install\s+(\S+)", "cargo"),
            (r"go\s+install\s+(\S+)", "go"),
        ]

        for pattern, installer in install_patterns:
            match = re.search(pattern, command)
            if match:
                tool_name = match.group(1).split("/")[-1].split("@")[0]

                if tool_name in EXCEPTIONS:
                    continue

                if tool_name in mise_managed:
                    print(
                        f"'{tool_name}' is managed by mise. "
                        f"Run `mise install` instead of `{installer} install`.",
                        file=sys.stderr,
                    )
                    sys.exit(2)
                else:
                    emit_guidance(
                        f"Note: Consider adding '{tool_name}' to "
                        f"~/.config/mise/config.toml if this is a dev tool "
                        f"you'll use across projects."
                    )
                    sys.exit(0)

        # No installation detected
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)  # Fail open — command proceeds, error logged
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)  # Fail open — command proceeds, error logged
```

**Step 4: Test the hook — all tiers and edge cases**

```bash
# Tier 1: Warn — brew install of mise-managed tool
echo '{"tool_name":"Bash","tool_input":{"command":"brew install uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv, exit 0.

```bash
# Tier 1: Warn — brew install with flags (flag stripping)
echo '{"tool_name":"Bash","tool_input":{"command":"brew install --cask uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv, exit 0.

```bash
# Tier 1: Warn — brew reinstall of mise-managed tool
echo '{"tool_name":"Bash","tool_input":{"command":"brew reinstall ruff"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning, exit 0.

```bash
# Tier 1: Guidance — brew install of non-mise tool
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` guidance note, exit 0.

```bash
# Tier 1: Normalization — tap-qualified name
echo '{"tool_name":"Bash","tool_input":{"command":"brew install homebrew/core/uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv, exit 0.

```bash
# Tier 2: Block — brew uninstall infrastructure
echo '{"tool_name":"Bash","tool_input":{"command":"brew uninstall stow"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: stderr about infrastructure, exit 2.

```bash
# Tier 2: Block — brew remove infrastructure (alias)
echo '{"tool_name":"Bash","tool_input":{"command":"brew remove mise"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: stderr about infrastructure, exit 2.

```bash
# Tier 2: Allow — brew uninstall non-infrastructure
echo '{"tool_name":"Bash","tool_input":{"command":"brew uninstall bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: exit 0 (no output).

```bash
# Tier 3: Allow — brew bundle
echo '{"tool_name":"Bash","tool_input":{"command":"brew bundle install --file=~/dotfiles/homebrew/Brewfile"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: exit 0 (no output).

```bash
# Existing: pipx install of mise-managed tool (still blocks)
echo '{"tool_name":"Bash","tool_input":{"command":"pipx install ruff"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: stderr about mise, exit 2.

```bash
# Tier 2: Block — brew rm alias (third uninstall alias)
echo '{"tool_name":"Bash","tool_input":{"command":"brew rm stow"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: stderr about infrastructure, exit 2.

```bash
# Tier 1: Multi-package — brew install of mixed tools (regression: must check all)
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv (managed takes priority), exit 0.

```bash
# Tier 1: @version suffix normalization
echo '{"tool_name":"Bash","tool_input":{"command":"brew install uv@0.5"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv, exit 0.

```bash
# Tier 1: Global flags before subcommand
echo '{"tool_name":"Bash","tool_input":{"command":"brew --quiet install uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: JSON with `additionalContext` warning about uv, exit 0.

```bash
# Empty tool_names: flags only, no packages (should not fall through to pipx/cargo/go)
echo '{"tool_name":"Bash","tool_input":{"command":"brew install --cask"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
```
Expected: exit 0 (no output — no packages to check).

**Step 5: No commit needed** — this is in `~/.claude/hooks/`, not a git-tracked location.

---

## Task 5: Create SessionStart hook for doctor-env in dotfiles

Runs doctor-env when starting or resuming a Claude session in `~/dotfiles/` and injects results into context. SessionStart stdout on exit 0 is added directly to Claude's context (unlike PreToolUse, no JSON wrapper needed).

**Files:**
- Create: `~/dotfiles/.claude/hooks/doctor-env-inject.sh`
- Create: `~/dotfiles/.claude/settings.json`

**Step 1: Create the hook script**

```bash
mkdir -p ~/dotfiles/.claude/hooks
```

Write `~/dotfiles/.claude/hooks/doctor-env-inject.sh`:

```bash
#!/usr/bin/env bash
# SessionStart hook: Inject doctor-env output into Claude's context.
# SessionStart stdout on exit 0 is added to Claude's context (plain text, no JSON needed).
# Timeout: doctor-env should complete in <5 seconds; bail after 10.
set -o pipefail

# Resolve timeout command (GNU coreutils via Homebrew)
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_CMD=timeout
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD=gtimeout
else
    TIMEOUT_CMD=""
fi

if ! command -v doctor-env >/dev/null 2>&1; then
    echo "doctor-env not found — run: cd ~/dotfiles && stow bin"
    exit 0
fi

# Capture exit code correctly. PIPESTATUS only tracks pipelines (|), not
# command substitution. The `|| true` pattern masks $? to 0. Use if/else.
if [ -n "$TIMEOUT_CMD" ]; then
    if output=$($TIMEOUT_CMD 10 doctor-env 2>&1); then
        rc=0
    else
        rc=$?
    fi
else
    if output=$(doctor-env 2>&1); then
        rc=0
    else
        rc=$?
    fi
fi

# Bound output to prevent excessive context injection
output="${output:0:2000}"

case $rc in
    0)
        echo "Environment healthy: doctor-env passed all checks."
        ;;
    124|137)
        echo "doctor-env timed out after 10 seconds. Run manually: doctor-env"
        ;;
    *)
        echo "doctor-env found issues (exit $rc):"
        echo "$output"
        ;;
esac

exit 0
```

```bash
chmod +x ~/dotfiles/.claude/hooks/doctor-env-inject.sh
```

**Step 2: Create the settings file**

Write `~/dotfiles/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/dotfiles/.claude/hooks/doctor-env-inject.sh\""
          }
        ]
      }
    ]
  }
}
```

**Step 3: Verify the JSON is valid**

```bash
python3 -m json.tool ~/dotfiles/.claude/settings.json
```

Expected: Pretty-printed JSON, no errors.

**Step 4: Test the hook script directly**

```bash
~/dotfiles/.claude/hooks/doctor-env-inject.sh; echo "exit: $?"
```

Expected: "Environment healthy: doctor-env passed all checks." and exit 0.

**Step 5: Commit both files**

```bash
cd ~/dotfiles && git add .claude/hooks/doctor-env-inject.sh .claude/settings.json && git commit -m "feat: add SessionStart hook for doctor-env context injection"
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

**Step 3: Verify Claude awareness (manual — new session)**

Start a new Claude session in `~/dotfiles/` and check:

1. **SessionStart hook:** Does doctor-env output appear in the session context?
   - Look for "Environment healthy" or issue details in the startup output.
   - The `matcher: "startup|resume"` means it fires on session start and resume, NOT on clear/compact.

2. **Ownership rules:** Does Claude know the rules?
   - Ask: "How should I install ruff?" — Claude should recommend `mise use ruff`.
   - Ask: "How do I edit my .zshrc?" — Claude should recommend editing `~/dotfiles/zsh/.zshrc`.

3. **Hook enforcement:** Does the brew hook fire?
   - Have Claude run `brew install uv` — should see additionalContext warning about mise ownership.
   - Have Claude run `brew uninstall stow` — should be blocked with stderr message.
   - Note: Hooks fire on Claude-generated tool calls only, not user-typed terminal commands.

4. **Trust boundary:** Hooks enforce rules for Claude's actions, not user terminal commands. This is by design — documentation handles awareness, hooks catch enforcement cases.

This step is manual verification in a new session.

---

## Dependency Graph

```
Task 1 (environment.md) ── independent
Task 2 (global CLAUDE.md) ── depends on Task 1 (references environment.md)
Task 3 (dotfiles CLAUDE.md + commit-if-changed script) ── independent
Task 4 (three-tier hook enforcement) ── independent
Task 5 (SessionStart hook + script) ── independent
Task 6 (push + verify) ── depends on Tasks 3, 5
```

Tasks 1, 3, 4, 5 are independent and can be executed in any order.
Task 2 should follow Task 1.
Task 6 is the final verification.
