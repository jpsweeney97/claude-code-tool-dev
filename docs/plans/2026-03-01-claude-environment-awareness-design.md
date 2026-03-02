# Claude Environment Awareness Design

**Goal:** Make Claude Code fully aware of the macOS environment ownership model (Homebrew/mise/stow) and enforce compliance through documentation + targeted hooks.

**Approach:** Documentation-first with graduated enforcement. Claude understands the system via CLAUDE.md + references (passive awareness). Hooks provide a safety net for dangerous violations (active enforcement).

**Trigger:** Environment cleanup complete (20-task migration plan executed). The declarative system exists but Claude doesn't know about it.

## Components

### 1. Updated `~/.claude/references/environment.md`

**Purpose:** Source of truth for the ownership model. Loaded into every session via CLAUDE.md reference.

**Current state:** 32-line tool list with aliases and commands. Stale — doesn't reflect ownership model, stow management, doctor-env, or Brewfile/mise architecture.

**New structure (~80-100 lines):**
- System: OS, shell, architecture (keep existing, update)
- Tool ownership model: three-layer architecture (Homebrew → mise → stow), "one executable, one owner" principle
- Ownership rules: condensed from OWNERSHIP.md — which categories belong to which owner, with examples
- Adding new tools: decision tree (runtime? → mise. OS-level? → brew. Config? → stow)
- Environment invariants: what doctor-env checks, how to run it
- Dotfiles architecture: stow packages, directory structure, where things live
- Shell aliases: keep existing section, updated
- Common commands: updated with brew bundle, mise install, stow commands

**Key constraint:** Loads into every session globally — reference-density, not prose. ~80-100 lines max.

### 2. Global `~/.claude/CLAUDE.md` Updates

**Purpose:** Establish environment rules that apply everywhere Claude works.

**Changes (~10-15 lines added):**
- Environment rules section stating the ownership principle
- Hard rules: never `brew install` a mise-owned tool, never bypass stow with direct file placement
- Reference to `~/.claude/references/environment.md` for full details
- `doctor-env` added to common commands section

### 3. `~/dotfiles/.claude/CLAUDE.md`

**Purpose:** Project-level context for working directly in the dotfiles repo. Only loaded when Claude is in `~/dotfiles/`.

**Content (~60-80 lines):**
- Repo purpose: declarative dotfiles managed by GNU stow
- Stow conventions: package structure, `stow -n` dry-run, `--ignore=DS_Store`
- Commit conventions: `commit_if_changed` helper, why `git add -A` is dangerous in dotfiles
- Doctor-env: run after any change, what it checks, how to interpret output
- Git hooks: `.githooks/` via `core.hooksPath`, pre-commit/post-commit/pre-push behavior
- Protected files: tools.zsh, .zshrc, .zprofile require `zsh -lc` verification after editing
- Adding a new stow package: mkdir, add files, stow, add to doctor-env loop

### 4. PreToolUse Hook — Ownership Enforcement

**Purpose:** Graduated enforcement for environment rule violations. Global scope.

**Hard block (exit 2 + stderr):**
- `rm` / `rm -rf` — already handled by existing hook. No duplication.
- `brew uninstall`/`brew remove`/`brew rm` of infrastructure tools (`stow`, `mise`) — removing these breaks the environment

**Warn via JSON additionalContext (exit 0 + `hookSpecificOutput`):**
- `brew install`/`brew reinstall` of mise-owned tools (read dynamically from `~/.config/mise/config.toml`)

**Deferred (v2) — tool-surface limitation:**
- Direct file writes to `~/.<dotfile>` that bypass stow — PreToolUse hook on `Bash` matcher cannot see Edit/Write/MultiEdit tool calls. Enforcement requires a separate hook on file-editing tools or documentation-only approach.

**Allow (exit 0, no output):**
- `brew bundle` — operates on the Brewfile, which IS the source of truth

**Implementation:** Python script. Parses Bash tool input. Detects brew operation type, strips flags, normalizes package names (tap prefix, @version). Reads mise config dynamically — adding a tool to mise automatically extends the hook's awareness.

**Failure mode:** Fail-open (exit 1 + stderr). Internal errors allow the command to proceed while preserving observability. Consistent with the learning that PreToolUse hooks are mechanically fail-open.

### 5. SessionStart Hook — Doctor-env Context Injection

**Purpose:** Inject environment health into Claude's context when starting a session in `~/dotfiles/`.

**Behavior:**
- Activates only in `~/dotfiles/` via project-scoped `settings.json`
- Runs `doctor-env` silently
- Pass: injects brief "Environment healthy" into additionalContext
- Fail: injects full error output so Claude sees issues immediately

**Location:** `~/dotfiles/.claude/settings.json` — only activates for the dotfiles repo.

**Cost:** One doctor-env invocation at session start (~2-3 seconds). No ongoing cost.

## Component Summary

| Component | Location | Purpose | Scope |
|-----------|----------|---------|-------|
| `environment.md` update | `~/.claude/references/` | Ownership model source of truth | Global (every session) |
| Global CLAUDE.md update | `~/.claude/CLAUDE.md` | Rules + reference pointer | Global (every session) |
| Dotfiles CLAUDE.md | `~/dotfiles/.claude/CLAUDE.md` | Stow/commit/hook conventions | Only in ~/dotfiles/ |
| Ownership enforcement hook | `~/.claude/settings.json` | Warn on ownership violations | Global (every session) |
| Doctor-env SessionStart | `~/dotfiles/.claude/settings.json` | Inject environment health | Only in ~/dotfiles/ |

## Enforcement Model

| Violation | Response | Mechanism |
|-----------|----------|-----------|
| `rm` / `rm -rf` | Hard block (exit 2) | Existing PreToolUse hook |
| `brew uninstall`/`remove`/`rm` stow\|mise | Hard block (exit 2) | Extended PreToolUse hook |
| `brew install`/`reinstall` mise-owned tool | Warn (exit 0 + JSON `additionalContext`) | Extended PreToolUse hook |
| `brew bundle` | Allow (exit 0) | Extended PreToolUse hook (explicit pass-through) |
| Direct dotfile write (bypass stow) | Deferred (v2) | Cannot enforce: PreToolUse on `Bash` cannot see Edit/Write/MultiEdit tool calls. Documentation handles awareness. |
| Unknown tool installation | Claude decides using CLAUDE.md rules | Documentation (passive) |
| Environment drift | Detected at session start | SessionStart hook + doctor-env |

## Non-Goals

- No `/env` or `/dotfiles` interactive skill (could be added later)
- No PostToolUse hooks (doctor-env after every bash command is too noisy)
- No hook-based enforcement for stow operations (documentation is sufficient — stow is safe and reversible)
- No automatic remediation (Claude sees the problem, human decides the fix)
