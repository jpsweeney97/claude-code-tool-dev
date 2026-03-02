# Hook Hardening + Deferred Items Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Fix 1 bug (shell metacharacters) and implement 5 deferred items (brew upgrade enforcement, Brewfile lint guard, ANSI stripping, dotfile write enforcement, uv tool deny rules) from the environment awareness plan.

**Architecture:** All changes are hook-layer enforcement. Tasks A+B modify the existing `mise-tool-guidance.py` PreToolUse hook. Task C modifies a SessionStart shell script. Task D creates a new PreToolUse hook for Edit/Write/MultiEdit. Task E adds settings.json deny rules. No tests framework — hooks are tested via stdin pipe commands.

**Tech Stack:** Python 3 (hooks), Bash (shell script), JSON (settings.json)

**Codex review:** Adversarial dialogue (6 turns, converged). Thread `019cacbc-ecb7-7d70-9115-0e89d931bf3a`. 5 findings applied to this plan.

---

## Task 1: Harden mise-tool-guidance.py — shell metacharacters + normalize helper

Applies: bug fix (metacharacters), deferred item 5 (flag consistency), Codex C2 (pipx flag capture).

**Files:**
- Modify: `~/.claude/hooks/mise-tool-guidance.py`

**Step 1: Read the current file and understand the structure**

The file has these sections (preserve all):
- Imports: `json`, `re`, `sys`, `tomllib`, `Path` (lines 24-28)
- Constants: `MISE_CONFIG`, `EXCEPTIONS` (lines 30-33)
- `load_mise_tools()` (lines 36-49)
- `emit_guidance()` (lines 52-65)
- `main()` (lines 68-185)

**Step 2: Add `normalize_package_name()` helper**

Add after `emit_guidance()`, before `main()`:

```python
def normalize_package_name(raw: str) -> str:
    """Strip tap prefix and @version suffix. Returns empty string for flags."""
    if raw.startswith("-"):
        return ""
    return raw.split("/")[-1].split("@")[0]
```

**Step 3: Add shell metacharacter stripping**

In `main()`, find `args_str = brew_match.group(2)` (line 83). Add immediately after:

```python
            # Strip shell metacharacters — prevents `brew install foo && echo done`
            # from treating shell operators as package names.
            args_str = re.split(r'[;&|<>()]', args_str)[0]
```

**Step 4: Replace inline normalization in brew section with helper**

Find the brew section's package normalization loop (lines 90-98). Replace:

```python
            raw_args = args_str.split()
            tool_names = []
            for arg in raw_args:
                if arg.startswith("-"):
                    continue  # Skip flags (--cask, -q, --force, etc.)
                # Normalize: strip tap prefix and @version
                name = arg.split("/")[-1].split("@")[0]
                if name:
                    tool_names.append(name)
```

With:

```python
            raw_args = args_str.split()
            tool_names = [
                name for arg in raw_args
                if (name := normalize_package_name(arg))
            ]
```

**Step 5: Fix pipx/cargo/go regex to skip flags before capture**

Find the install_patterns list (lines 148-152). Replace:

```python
        install_patterns = [
            (r"pipx\s+install\s+(\S+)", "pipx"),
            (r"cargo\s+install\s+(\S+)", "cargo"),
            (r"go\s+install\s+(\S+)", "go"),
        ]
```

With:

```python
        install_patterns = [
            (r"pipx\s+install\s+(?:-\S+\s+)*(\S+)", "pipx"),
            (r"cargo\s+install\s+(?:-\S+\s+)*(\S+)", "cargo"),
            (r"go\s+install\s+(?:-\S+\s+)*(\S+)", "go"),
        ]
```

The `(?:-\S+\s+)*` skips flags like `--force`, `--locked`, `-v` before capturing the actual tool name.

**Step 6: Replace inline normalization in pipx/cargo/go section with helper**

Find (line 155):

```python
                tool_name = match.group(1).split("/")[-1].split("@")[0]
```

Replace with:

```python
                tool_name = normalize_package_name(match.group(1))
                if not tool_name:
                    continue
```

**Step 7: Run existing tests to verify no regression**

Run all 15 existing test cases from the awareness plan. They must all still pass:

```bash
# Tier 1: brew install uv (mise-managed)
echo '{"tool_name":"Bash","tool_input":{"command":"brew install uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON warning, exit 0

# Tier 2: brew uninstall stow
echo '{"tool_name":"Bash","tool_input":{"command":"brew uninstall stow"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr, exit 2

# Tier 3: brew bundle
echo '{"tool_name":"Bash","tool_input":{"command":"brew bundle install --file=~/dotfiles/homebrew/Brewfile"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: exit 0, no output

# pipx block: ruff
echo '{"tool_name":"Bash","tool_input":{"command":"pipx install ruff"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr, exit 2

# Multi-package: brew install bat uv
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON warning about uv, exit 0
```

**Step 8: Run new test cases**

```bash
# Shell metacharacters: only "foo" extracted
echo '{"tool_name":"Bash","tool_input":{"command":"brew install foo && echo done"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON guidance for "foo" (non-managed), exit 0. NOT "echo"/"done".

# pipx with flags — ruff checked, --force skipped
echo '{"tool_name":"Bash","tool_input":{"command":"pipx install --force ruff"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr about mise, exit 2

# cargo with flags
echo '{"tool_name":"Bash","tool_input":{"command":"cargo install --locked just"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON guidance note (just is not mise-managed), exit 0
```

---

## Task 2: Add dedicated `brew upgrade` code path (Codex C1)

Depends on Task 1 (uses `normalize_package_name`).

**Files:**
- Modify: `~/.claude/hooks/mise-tool-guidance.py`

**Step 1: Extend the brew regex to include `upgrade`**

Find (line 78):

```python
            r"brew\s+(?:-[-\w]+\s+)*(install|reinstall|uninstall|remove|rm|bundle)\b(.*)",
```

Replace with:

```python
            r"brew\s+(?:-[-\w]+\s+)*(install|reinstall|uninstall|remove|rm|bundle|upgrade)\b(.*)",
```

**Step 2: Add the upgrade branch**

Find the comment `# All brew paths exit here` and the `sys.exit(0)` that follows the Tier 1 install/reinstall block (around line 145). Insert the upgrade branch BEFORE it, after the `if operation in ("install", "reinstall"):` block closes:

```python
            # Upgrade: dedicated path — different semantics from install/uninstall
            if operation == "upgrade":
                # Bare upgrade (no packages) — upgrades ALL including infrastructure
                if not tool_names:
                    print(
                        "Bare `brew upgrade` upgrades ALL packages including "
                        "infrastructure (stow, mise). Use `brew upgrade <specific-package>` "
                        "or `brew bundle install` to reconcile from Brewfile.",
                        file=sys.stderr,
                    )
                    sys.exit(2)

                # Check packages: infra block > mise warn > allow
                for name in tool_names:
                    if name in infra_tools:
                        print(
                            f"'{name}' is infrastructure — do not upgrade directly. "
                            f"Use `brew bundle install` to reconcile from Brewfile.",
                            file=sys.stderr,
                        )
                        sys.exit(2)

                managed_found = [
                    n for n in tool_names
                    if n not in EXCEPTIONS and n in mise_managed
                ]
                if managed_found:
                    names = ", ".join(dict.fromkeys(managed_found))
                    emit_guidance(
                        f"WARNING: {names} managed by mise. "
                        f"Upgrading via brew creates version conflicts. "
                        f"Use `mise use <tool>@latest` instead."
                    )
                sys.exit(0)
```

**Step 3: Run upgrade test cases**

```bash
# Bare upgrade — blocked
echo '{"tool_name":"Bash","tool_input":{"command":"brew upgrade"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr about bare upgrade, exit 2

# Upgrade infrastructure — blocked
echo '{"tool_name":"Bash","tool_input":{"command":"brew upgrade stow"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr about infrastructure, exit 2

# Upgrade mise — blocked
echo '{"tool_name":"Bash","tool_input":{"command":"brew upgrade mise"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: stderr about infrastructure, exit 2

# Upgrade mise-managed — warned
echo '{"tool_name":"Bash","tool_input":{"command":"brew upgrade uv"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON warning, exit 0

# Upgrade non-managed — allowed
echo '{"tool_name":"Bash","tool_input":{"command":"brew upgrade bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: exit 0, no output
```

**Step 4: Verify existing tests still pass**

Re-run the 5 key regression tests from Task 1 Step 7.

---

## Task 3: Add Brewfile awareness with combined messages (Codex C4)

Depends on Tasks 1-2.

**Files:**
- Modify: `~/.claude/hooks/mise-tool-guidance.py`

**Step 1: Add module-level constant and helper**

After `EXCEPTIONS` (line 33), add:

```python
BREWFILE = Path.home() / "dotfiles/homebrew/Brewfile"
```

After `normalize_package_name()`, add:

```python
def load_brewfile_packages() -> set[str]:
    """Load package names from Brewfile. Returns empty set on error (fail open)."""
    try:
        text = BREWFILE.read_text()
        packages = set()
        for match in re.finditer(r'^(?:brew|cask)\s+["\']([^"\']+)["\']', text, re.MULTILINE):
            packages.add(match.group(1).split("/")[-1])
        return packages
    except (FileNotFoundError, PermissionError):
        return set()
```

**Step 2: Replace the Tier 1 install/reinstall block**

Find the existing Tier 1 block (`if operation in ("install", "reinstall"):`). Replace the entire block with the three-category partition:

```python
            # Tier 1: Warn — install/reinstall with three-category partition
            # Scans ALL packages, emits combined message (no early-exit suppression).
            if operation in ("install", "reinstall"):
                managed_found = []
                in_brewfile = []
                unknown = []
                brewfile_packages = load_brewfile_packages()

                for name in tool_names:
                    if name in EXCEPTIONS:
                        continue
                    if name in mise_managed:
                        managed_found.append(name)
                    elif name in brewfile_packages:
                        in_brewfile.append(name)
                    else:
                        unknown.append(name)

                parts = []
                if managed_found:
                    names = ", ".join(dict.fromkeys(managed_found))
                    parts.append(
                        f"WARNING: {names} managed by mise. "
                        f"Use `mise use <tool>` instead of `brew {operation}`. "
                        f"Dual ownership creates conflicts."
                    )
                if in_brewfile:
                    names = ", ".join(dict.fromkeys(in_brewfile))
                    parts.append(
                        f"Note: {names} already in ~/dotfiles/homebrew/Brewfile. "
                        f"Use `brew bundle install` to install from Brewfile."
                    )
                if unknown:
                    names = ", ".join(dict.fromkeys(unknown))
                    parts.append(
                        f"Note: Consider adding {names} to "
                        f"~/.config/mise/config.toml if these are dev tools."
                    )

                if parts:
                    emit_guidance(
                        " | ".join(parts)
                        + " See ~/.claude/references/environment.md for ownership model."
                    )
```

**Step 3: Run Brewfile test cases**

```bash
# Package in Brewfile — Brewfile guidance
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON about bat in Brewfile, exit 0

# Mixed: managed + Brewfile — combined message (no suppression)
echo '{"tool_name":"Bash","tool_input":{"command":"brew install uv bat"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON with mise warning for uv AND Brewfile note for bat, exit 0

# Mixed: Brewfile + unknown — both in message
echo '{"tool_name":"Bash","tool_input":{"command":"brew install bat newpkg"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON with Brewfile note for bat AND "consider adding" for newpkg, exit 0

# Unknown only
echo '{"tool_name":"Bash","tool_input":{"command":"brew install somenewpkg"}}' | python3 ~/.claude/hooks/mise-tool-guidance.py; echo "exit: $?"
# Expected: JSON "consider adding" guidance, exit 0
```

**Step 4: Verify existing tests still pass**

Re-run the 5 key regression tests from Task 1 Step 7.

---

## Task 4: Doctor-env output sanitization

Independent of Tasks 1-3.

**Files:**
- Modify: `~/dotfiles/.claude/hooks/doctor-env-inject.sh`

**Step 1: Add ANSI stripping before truncation**

Read `~/dotfiles/.claude/hooks/doctor-env-inject.sh`. Find `output="${output:0:2000}"` (line 38). Insert BEFORE it:

```bash
# Strip ANSI color codes — prevents raw escape sequences in Claude's context
output=$(printf '%s' "$output" | sed 's/\x1b\[[0-9;]*m//g')
```

The strip goes BEFORE truncation so partial escape sequences at the 2000-byte boundary are avoided.

**Step 2: Test the script**

```bash
~/dotfiles/.claude/hooks/doctor-env-inject.sh; echo "exit: $?"
# Expected: "Environment healthy: doctor-env passed all checks." with exit 0
# No ANSI escape sequences in output
```

**Step 3: Commit**

```bash
cd ~/dotfiles && git add .claude/hooks/doctor-env-inject.sh && git commit -m "fix: strip ANSI codes from doctor-env output in SessionStart hook"
```

---

## Task 5: Direct dotfile write enforcement hook (Codex C3)

Independent of Tasks 1-4.

**Files:**
- Create: `~/.claude/hooks/dotfile-stow-guidance.py`
- Modify: `~/.claude/settings.json`

**Step 1: Create the hook script**

Write `~/.claude/hooks/dotfile-stow-guidance.py`:

```python
#!/usr/bin/env python3
"""
PreToolUse hook (Edit|Write|MultiEdit): Warns when writing to dotfile paths
that aren't stow-managed symlinks.

If the file is a symlink resolving into ~/dotfiles/, the edit flows through
stow correctly — no warning needed.

Exit codes:
  0 - Allow (with optional additionalContext warning)
  1 - Internal error (fail open)
"""
import json
import os
import sys
from pathlib import Path

DOTFILES_DIR = str(Path.home() / "dotfiles")
HOME = str(Path.home())

# Paths that look like dotfiles but are NOT stow-managed.
# Trailing os.sep ensures boundary-safe matching:
# ".git/" won't match ".gitconfig" (Codex C3 fix)
EXCLUDED_PREFIXES = [
    os.path.join(HOME, d) + os.sep
    for d in [".claude", ".ssh", ".git", ".local/share", ".local/bin",
              ".local/lib", ".cache", ".npm", ".cargo"]
]


def is_dotfile_path(path: str) -> bool:
    """Check if path looks like a user dotfile (~/.<something>)."""
    path = os.path.abspath(path)
    if not path.startswith(HOME + os.sep):
        return False
    relative = path[len(HOME):]
    if not relative.startswith("/."):
        return False
    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix) or path + os.sep == prefix:
            return False
    return True


def resolves_to_dotfiles(path: str) -> bool:
    """Check if path is a symlink that resolves into ~/dotfiles/."""
    try:
        resolved = os.path.realpath(path)
        return resolved.startswith(DOTFILES_DIR + os.sep)
    except (OSError, ValueError):
        return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
        file_path = data.get("tool_input", {}).get("file_path", "")
        if not file_path:
            sys.exit(0)

        lex_path = os.path.abspath(os.path.expanduser(file_path))

        if is_dotfile_path(lex_path) and not resolves_to_dotfiles(lex_path):
            relative = lex_path[len(HOME) + 1:]
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": (
                        f"Note: {relative} looks like a dotfile but isn't stow-managed. "
                        f"Consider creating it in ~/dotfiles/<package>/{relative} "
                        f"and deploying via `cd ~/dotfiles && stow <package>`. "
                        f"See ~/.claude/references/environment.md for the ownership model."
                    ),
                }
            }
            print(json.dumps(result))

        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Make executable**

```bash
chmod +x ~/.claude/hooks/dotfile-stow-guidance.py
```

**Step 3: Run test cases**

```bash
# Stow-managed symlink (~/.zshrc) — no warning
echo '{"tool_name":"Edit","tool_input":{"file_path":"~/.zshrc"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: exit 0, no output

# Non-stow dotfile — warning
echo '{"tool_name":"Write","tool_input":{"file_path":"~/.newrc"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: JSON warning, exit 0

# .gitconfig — no warning (.git/ exclusion does NOT match .gitconfig)
echo '{"tool_name":"Edit","tool_input":{"file_path":"~/.gitconfig"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: JSON warning, exit 0 (gitconfig IS a dotfile, not in exclusions, not a stow symlink)

# .claude path — no warning (excluded)
echo '{"tool_name":"Write","tool_input":{"file_path":"~/.claude/CLAUDE.md"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: exit 0, no output

# Non-dotfile — no warning
echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/foo.txt"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: exit 0, no output

# Path traversal — normalized, then checked
echo '{"tool_name":"Edit","tool_input":{"file_path":"~/.ssh/../.newrc"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: JSON warning for .newrc, exit 0 (abspath resolves traversal)

# .local/bin — no warning (excluded)
echo '{"tool_name":"Write","tool_input":{"file_path":"~/.local/bin/myscript"}}' | python3 ~/.claude/hooks/dotfile-stow-guidance.py; echo "exit: $?"
# Expected: exit 0, no output
```

**Step 4: Add hook to settings.json**

Read `~/.claude/settings.json`. Find the `"PreToolUse"` array. Add a new entry:

```json
{
  "matcher": "Edit|Write|MultiEdit",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/dotfile-stow-guidance.py"
    }
  ]
}
```

**Step 5: Verify settings.json is valid**

```bash
python3 -m json.tool ~/.claude/settings.json > /dev/null && echo "valid JSON"
```

---

## Task 6: Add `uv tool` deny rules to settings.json (Codex C5)

Independent. Trivial.

**Files:**
- Modify: `~/.claude/settings.json`

**Step 1: Add deny rules**

Read `~/.claude/settings.json`. Find the `"deny"` array. Add:

```json
"Bash(uv tool install:*)",
"Bash(uv tool upgrade:*)"
```

**Step 2: Verify settings.json is valid**

```bash
python3 -m json.tool ~/.claude/settings.json > /dev/null && echo "valid JSON"
```

---

## Dependency Graph

```
Task 1 (normalize, metacharacters, pipx regex) ── independent
Task 2 (brew upgrade) ── depends on Task 1
Task 3 (Brewfile awareness) ── depends on Tasks 1-2
Task 4 (ANSI stripping) ── independent
Task 5 (dotfile hook) ── independent
Task 6 (uv deny rules) ── independent
```

Tasks 1, 4, 5, 6 are independent. Tasks 1 → 2 → 3 are sequential (same file). Task 4 can run in parallel with anything.

## Deferred

- `brew bundle` subcommands (cleanup, dump) — separate enforcement
- npm `--global install` / `python -m pip install` variant deny coverage
