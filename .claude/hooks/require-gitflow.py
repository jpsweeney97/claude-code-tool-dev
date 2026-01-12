#!/usr/bin/env python3
# /// hook
# event: PreToolUse
# matcher: Edit|Write
# timeout: 5
# ///
"""
Enforce GitFlow branching workflow before editing files.

Behavior:
  - BLOCK on protected branches (main, master, develop)
  - BLOCK/WARN based on git operation state (rebase, merge, cherry-pick, bisect)
  - ALLOW on valid GitFlow working branches (feature/*, release/*, etc.)
  - WARN but ALLOW on non-standard branch names (permissive mode)

Git operation handling:
  - rebase:      BLOCK — edits during rebase are risky
  - merge:       ALLOW — conflict resolution requires edits
  - cherry-pick: WARN  — may need edits for conflicts
  - bisect:      BLOCK — edits lost on next bisect step
  - detached:    WARN  — user explicitly checked out a commit

Configuration:
  PROTECTED_BRANCHES: comma-separated (default: main,master,develop)
  GITFLOW_STRICT: set to "1" to block non-standard branches (default: permissive)

Exit codes:
  0 - Allow (valid branch or permissive warning)
  1 - Error (non-blocking)
  2 - Block (protected branch, rebase, or bisect)
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MAX_PATH_DISPLAY_LEN = 50
BYPASS_ENV = "GITFLOW_BYPASS"

DEBUG = os.environ.get("GITFLOW_DEBUG", "") == "1"
LOG_FILE = Path.home() / ".claude/logs/gitflow-hook.log"


def log(level: str, message: str) -> None:
    """Log message to stderr (if debug) and log file."""
    if not DEBUG and level == "DEBUG":
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} [{level}] {message}"

    if DEBUG:
        print(f"[GITFLOW] {message}", file=sys.stderr)

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass  # Fail silently


def check_bypass() -> bool:
    """Check if bypass is enabled. Returns True if should skip all checks."""
    bypass = os.environ.get(BYPASS_ENV, "").strip()
    if bypass == "1":
        output = {
            "systemMessage": (
                f"Warning: GitFlow enforcement bypassed via {BYPASS_ENV}=1\n"
                "All branch protection checks are disabled for this session."
            )
        }
        print(json.dumps(output))
        return True
    return False


def get_file_context(tool_input: dict) -> str:
    """Extract file path from tool input for context in messages."""
    file_path = tool_input.get("file_path", "")
    if file_path:
        if len(file_path) > MAX_PATH_DISPLAY_LEN:
            file_path = "..." + file_path[-(MAX_PATH_DISPLAY_LEN - 3) :]
        return f"'{file_path}'"
    return "files"


# Valid GitFlow working branch patterns (regex)
VALID_PATTERNS = [
    # GitFlow core
    r"^feature/.+",
    r"^feat/.+",
    r"^release/.+",
    r"^hotfix/.+",
    # Bug fixes
    r"^fix/.+",
    r"^bugfix/.+",
    # Conventional Commits aligned
    r"^docs/.+",
    r"^style/.+",
    r"^refactor/.+",
    r"^perf/.+",
    r"^test/.+",
    r"^build/.+",
    r"^ci/.+",
    r"^chore/.+",
    # Automation (dependency bots)
    r"^dependabot/.+",
    r"^renovate/.+",
    r"^deps/.+",
    # Exploratory
    r"^spike/.+",
    r"^experiment/.+",
    r"^poc/.+",
]


def get_protected_branches() -> set[str]:
    """Get protected branch names from environment or defaults."""
    env_value = os.environ.get("PROTECTED_BRANCHES", "main,master,develop")
    return {b.strip().lower() for b in env_value.split(",") if b.strip()}


def is_strict_mode() -> bool:
    """Check if strict mode is enabled (block non-standard branches)."""
    return os.environ.get("GITFLOW_STRICT", "").strip() == "1"


def matches_valid_pattern(branch: str) -> bool:
    """Check if branch name matches any valid GitFlow pattern (case-insensitive)."""
    return any(re.match(pattern, branch.lower()) for pattern in VALID_PATTERNS)


BLOCK_MESSAGE_MAIN = """Cannot edit {file} on '{branch}' — this is the production branch.

GitFlow requires working branches:

  For new features (branch from develop):
    git checkout develop
    git checkout -b feature/<name>

  For emergency fixes (branch from main):
    git checkout -b hotfix/<name>"""

BLOCK_MESSAGE_DEVELOP = """Cannot edit {file} on '{branch}' — this is the integration branch.

GitFlow requires working branches:

  For new features:
    git checkout -b feature/<name>

  For release preparation:
    git checkout -b release/<version>

  For bug fixes:
    git checkout -b fix/<name>"""

# Operation-specific messages
BLOCK_MESSAGE_REBASE = """Cannot edit files during rebase.

You're in the middle of a rebase operation. Editing now is risky — changes may
conflict with commits being replayed or get lost.

Options:
  git rebase --continue   # after staging resolved conflicts
  git rebase --abort      # cancel rebase, restore original state
  git rebase --skip       # skip current commit

If you intentionally need to edit during rebase:
  git checkout -b feature/rebase-wip"""

BLOCK_MESSAGE_BISECT = """Cannot edit files during bisect.

You're in the middle of a bisect operation. Any edits will be lost when you
run 'git bisect good' or 'git bisect bad' (bisect checks out different commits).

Options:
  git bisect reset        # end bisect, return to original branch
  git bisect good         # mark current commit as good
  git bisect bad          # mark current commit as bad

If you found the bug and want to fix it:
  git bisect reset
  git checkout -b fix/<bug-description>"""

WARN_MESSAGE_MERGE = """You're resolving a merge conflict.

Edits are expected during merge conflict resolution. After resolving:
  git add <resolved-files>
  git commit              # or 'git merge --continue'

To abort the merge:
  git merge --abort"""

WARN_MESSAGE_CHERRY_PICK = """You're in the middle of a cherry-pick.

Edits may be needed to resolve conflicts. After resolving:
  git add <resolved-files>
  git cherry-pick --continue

To abort:
  git cherry-pick --abort"""

WARN_MESSAGE_DETACHED = """You're on a detached HEAD (not on any branch).

Any commits you make will be orphaned when you switch branches unless you
create a branch first.

Options:
  git checkout -b feature/<name>   # create branch from current state
  git checkout <branch>            # return to an existing branch

Proceeding anyway — edits allowed but commits may be lost."""

WARN_MESSAGE_NONSTANDARD = """Branch '{branch}' doesn't follow GitFlow conventions.

Expected patterns:
  feature/*  feat/*  fix/*  bugfix/*  hotfix/*  release/*
  docs/*  style/*  refactor/*  perf/*  test/*  build/*  ci/*  chore/*
  dependabot/*  renovate/*  deps/*  spike/*  experiment/*  poc/*

Consider renaming:
  git branch -m {suggested}

Proceeding anyway (permissive mode)."""

BLOCK_MESSAGE_NONSTANDARD = """Cannot edit files — branch '{branch}' doesn't follow GitFlow conventions.

Expected patterns:
  feature/*  feat/*  fix/*  bugfix/*  hotfix/*  release/*
  docs/*  style/*  refactor/*  perf/*  test/*  build/*  ci/*  chore/*
  dependabot/*  renovate/*  deps/*  spike/*  experiment/*  poc/*

Create a valid branch:
  git checkout -b feature/<description>

Or rename current branch:
  git branch -m {suggested}"""


def suggest_branch_name(branch: str) -> str:
    """Suggest a GitFlow-compliant branch name."""
    # Clean up the branch name
    clean = re.sub(r"[^a-z0-9-]", "-", branch.lower())
    clean = re.sub(r"-+", "-", clean).strip("-")
    return f"feature/{clean}" if clean else "feature/my-feature"


def run_git(*args: str) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def is_git_repo() -> bool:
    """Check if current directory is inside a git repository."""
    success, _ = run_git("rev-parse", "--git-dir")
    return success


def has_commits() -> bool:
    """Check if repository has at least one commit."""
    success, _ = run_git("rev-parse", "HEAD")
    return success


def is_detached_head() -> bool:
    """Check if HEAD is detached (not on any branch)."""
    success, _ = run_git("symbolic-ref", "-q", "HEAD")
    return not success


def get_git_dir() -> str | None:
    """Get the .git directory path."""
    success, git_dir = run_git("rev-parse", "--git-dir")
    return git_dir if success else None


def get_git_operation_state() -> str | None:
    """
    Detect if a git operation is in progress.

    Returns:
        'rebase' | 'merge' | 'cherry-pick' | 'bisect' | None
    """
    git_dir = get_git_dir()
    if not git_dir:
        return None

    # Check for various in-progress operations
    # Order matters: more specific checks first

    # Rebase (interactive or regular)
    if os.path.exists(os.path.join(git_dir, "rebase-merge")):
        return "rebase"
    if os.path.exists(os.path.join(git_dir, "rebase-apply")):
        return "rebase"

    # Merge
    if os.path.exists(os.path.join(git_dir, "MERGE_HEAD")):
        return "merge"

    # Cherry-pick
    if os.path.exists(os.path.join(git_dir, "CHERRY_PICK_HEAD")):
        return "cherry-pick"

    # Bisect
    if os.path.exists(os.path.join(git_dir, "BISECT_LOG")):
        return "bisect"

    return None


def get_current_branch() -> str | None:
    """Get the current branch name, or None if error."""
    success, branch = run_git("branch", "--show-current")
    return branch if success and branch else None


def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        log("DEBUG", f"Hook invoked: tool={tool_name}")

        # Only check Edit and Write tools
        if tool_name not in ("Edit", "Write"):
            sys.exit(0)

        # Check bypass FIRST (before any git operations)
        if check_bypass():
            sys.exit(0)

        # Not a git repo - allow (untracked project)
        if not is_git_repo():
            sys.exit(0)

        # New repo with no commits - allow (bootstrapping)
        if not has_commits():
            sys.exit(0)

        # Check for in-progress git operations FIRST
        # These take precedence over branch checks
        operation = get_git_operation_state()

        if operation == "rebase":
            print(BLOCK_MESSAGE_REBASE, file=sys.stderr)
            sys.exit(2)

        if operation == "bisect":
            print(BLOCK_MESSAGE_BISECT, file=sys.stderr)
            sys.exit(2)

        if operation == "merge":
            # Allow edits during merge (conflict resolution), but inform Claude
            output = {"systemMessage": WARN_MESSAGE_MERGE}
            print(json.dumps(output))
            sys.exit(0)

        if operation == "cherry-pick":
            # Allow edits during cherry-pick (may need conflict resolution)
            output = {"systemMessage": WARN_MESSAGE_CHERRY_PICK}
            print(json.dumps(output))
            sys.exit(0)

        # Check for detached HEAD (no operation in progress)
        if is_detached_head():
            # Warn but allow - user explicitly checked out a commit
            output = {"systemMessage": WARN_MESSAGE_DETACHED}
            print(json.dumps(output))
            sys.exit(0)

        # Get current branch
        branch = get_current_branch()

        # Couldn't determine branch - allow (unexpected state, fail open)
        if branch is None:
            sys.exit(0)

        # Get file context for error messages
        tool_input = data.get("tool_input", {})
        file_context = get_file_context(tool_input)
        log("DEBUG", f"Checking edit to: {tool_input.get('file_path', 'unknown')}")

        # Check if on protected branch (case-insensitive)
        protected = get_protected_branches()
        branch_lower = branch.lower()

        if branch_lower in {"main", "master"}:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower == "develop":
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            print(BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        if branch_lower in protected:
            log("INFO", f"BLOCKED: Edit on protected branch {branch}")
            # Custom protected branch - use generic main message
            print(BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context), file=sys.stderr)
            sys.exit(2)

        # Check if matches valid GitFlow pattern (case-insensitive)
        if matches_valid_pattern(branch):
            log("DEBUG", f"Branch {branch} matches valid pattern, allowing")
            sys.exit(0)

        # Non-standard branch name
        suggested = suggest_branch_name(branch)

        if is_strict_mode():
            print(
                BLOCK_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested),
                file=sys.stderr,
            )
            sys.exit(2)

        # Permissive mode: warn but allow
        # Output warning as JSON so Claude sees it as context
        output = {
            "systemMessage": WARN_MESSAGE_NONSTANDARD.format(
                branch=branch, suggested=suggested
            ),
        }
        print(json.dumps(output))
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
