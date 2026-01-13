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
  - merge:       WARN  — conflict resolution requires edits
  - cherry-pick: WARN  — may need edits for conflicts
  - bisect:      BLOCK — edits lost on next bisect step
  - stash-apply: WARN  — conflict resolution requires edits
  - detached:    WARN  — user explicitly checked out a commit

Configuration (environment variables):
  PROTECTED_BRANCHES    Comma-separated protected branches (default: main,master,develop)
  GITFLOW_ALLOW_FILES   Comma-separated glob patterns for files that bypass checks (e.g., *.lock)
  GITFLOW_STRICT        Set to "1" to block non-standard branch names (default: permissive)
  GITFLOW_BYPASS        Set to "1" to bypass all checks (emergency use only)
  GITFLOW_DEBUG         Set to "1" for debug output to stderr and log file
  GITFLOW_LOG_FILE      Custom log file path (default: ~/.claude/logs/gitflow-hook.log)

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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

MAX_PATH_DISPLAY_LEN = 50
BYPASS_ENV = "GITFLOW_BYPASS"

DEBUG = os.environ.get("GITFLOW_DEBUG", "") == "1"


def get_log_file() -> Path:
    """Get log file path from environment or default."""
    env_path = os.environ.get("GITFLOW_LOG_FILE", "").strip()
    if env_path:
        return Path(env_path)
    return Path.home() / ".claude/logs/gitflow-hook.log"


LOG_FILE = get_log_file()

_log_warning_shown = False


def log(level: str, message: str) -> None:
    """Log message to stderr (if debug) and log file."""
    global _log_warning_shown
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
    except PermissionError:
        pass  # Expected in sandboxed environments
    except OSError as e:
        if DEBUG and not _log_warning_shown:
            print(f"[GITFLOW] Warning: Could not write to log file: {e}", file=sys.stderr)
            _log_warning_shown = True


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

# Precompile patterns for performance (case-insensitive)
VALID_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in VALID_PATTERNS]


def get_protected_branches() -> set[str]:
    """Get protected branch names from environment or defaults."""
    env_value = os.environ.get("PROTECTED_BRANCHES", "main,master,develop")
    return {b.strip().lower() for b in env_value.split(",") if b.strip()}


def get_allowed_file_patterns() -> list[str]:
    """Get file patterns that bypass protected branch checks."""
    env_value = os.environ.get("GITFLOW_ALLOW_FILES", "")
    return [p.strip() for p in env_value.split(",") if p.strip()]


def is_file_allowed(file_path: str) -> bool:
    """Check if file matches any allowlist pattern."""
    patterns = get_allowed_file_patterns()
    if not patterns:
        return False
    path = Path(file_path)
    return any(path.match(pattern) for pattern in patterns)


def is_strict_mode() -> bool:
    """Check if strict mode is enabled (block non-standard branches)."""
    return os.environ.get("GITFLOW_STRICT", "").strip() == "1"


def matches_valid_pattern(branch: str) -> bool:
    """Check if branch name matches any valid GitFlow pattern (case-insensitive)."""
    return any(regex.match(branch) for regex in VALID_REGEXES)


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

WARN_MESSAGE_STASH = """You're resolving a stash apply conflict.

Edits are expected during stash conflict resolution. After resolving:
  git add <resolved-files>
  git stash drop               # if you used 'stash pop'

To abort:
  git checkout -- <conflicted-files>
  git stash                    # your changes are still in the stash"""

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
    except subprocess.TimeoutExpired:
        log("DEBUG", f"Git command timed out: git {' '.join(args)}")
        return False, ""
    except FileNotFoundError:
        log("DEBUG", "Git not found in PATH")
        return False, ""


def resolve_git_dir(git_dir: str) -> str:
    """
    Resolve git directory, following gitdir file indirection.

    In linked worktrees and some submodules, .git is a file containing:
        gitdir: /path/to/actual/.git/worktrees/name

    This function follows that indirection. On error, returns original path.
    """
    git_path = Path(git_dir)

    if git_path.is_file():
        try:
            content = git_path.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                pointed_path = content[7:].strip()
                if not os.path.isabs(pointed_path):
                    pointed_path = str(git_path.parent / pointed_path)
                resolved = os.path.normpath(pointed_path)
                log("DEBUG", f"Resolved gitdir indirection: {git_dir} -> {resolved}")
                return resolved
        except (OSError, UnicodeDecodeError) as e:
            log("DEBUG", f"Could not resolve git dir {git_dir!r}: {e}")

    return git_dir


@dataclass(frozen=True)
class GitContext:
    """
    Cached git repository context.

    Invariants:
    - is_repo=False implies all other fields are at defaults
    - is_repo=True implies git_dir is not None
    - branch and is_detached are mutually exclusive
    - is_detached requires has_commits=True
    - is_bare=True implies is_repo=True
    """

    is_repo: bool = False
    is_bare: bool = False
    has_commits: bool = False
    git_dir: Optional[str] = None
    branch: Optional[str] = None
    is_detached: bool = False

    def __post_init__(self) -> None:
        if not self.is_repo:
            if self.has_commits or self.git_dir or self.branch or self.is_detached or self.is_bare:
                raise ValueError(
                    f"GitContext invariant violated: is_repo=False but other fields set: "
                    f"has_commits={self.has_commits}, git_dir={self.git_dir!r}, "
                    f"branch={self.branch!r}, is_detached={self.is_detached}, is_bare={self.is_bare}"
                )
        elif self.git_dir is None:
            raise ValueError("GitContext invariant violated: is_repo=True but git_dir is None")
        if self.is_detached and not self.has_commits:
            raise ValueError("GitContext invariant violated: is_detached=True requires has_commits=True")
        if self.branch is not None and self.is_detached:
            raise ValueError("GitContext invariant violated: branch and is_detached are mutually exclusive")


class Decision(Enum):
    """Decision types for gitflow evaluation."""

    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True)
class HookDecision:
    """Result of evaluating gitflow rules."""

    decision: Decision
    message: str | None = None
    exit_code: int = 0
    output_json: dict | None = None


def evaluate_gitflow_rules(
    ctx: GitContext,
    file_path: str,
    operation: str | None,
) -> HookDecision:
    """
    Evaluate gitflow rules and return decision.

    Pure function - no side effects, no I/O.
    """
    # Not a repo
    if not ctx.is_repo:
        return HookDecision(Decision.ALLOW)

    # Bare repo
    if ctx.is_bare:
        return HookDecision(Decision.ALLOW)

    # No commits yet
    if not ctx.has_commits:
        return HookDecision(
            Decision.ALLOW,
            output_json={
                "systemMessage": "Note: This repository has no commits yet. GitFlow checks are bypassed during initial setup."
            },
        )

    # File allowlist check
    if is_file_allowed(file_path):
        return HookDecision(Decision.ALLOW)

    # Operation checks
    if operation == "rebase":
        return HookDecision(Decision.BLOCK, BLOCK_MESSAGE_REBASE, exit_code=2)
    if operation == "bisect":
        return HookDecision(Decision.BLOCK, BLOCK_MESSAGE_BISECT, exit_code=2)
    if operation == "merge":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_MERGE})
    if operation == "cherry-pick":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_CHERRY_PICK})
    if operation == "stash-apply":
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_STASH})

    # Detached HEAD
    if ctx.is_detached:
        return HookDecision(Decision.WARN, output_json={"systemMessage": WARN_MESSAGE_DETACHED})

    # Branch checks
    branch = ctx.branch
    if branch is None:
        return HookDecision(Decision.ALLOW)

    protected = get_protected_branches()
    branch_lower = branch.lower()

    if branch_lower in protected:
        file_context = get_file_context({"file_path": file_path})
        if branch_lower in {"main", "master"}:
            msg = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)
        elif branch_lower == "develop":
            msg = BLOCK_MESSAGE_DEVELOP.format(branch=branch, file=file_context)
        else:
            msg = BLOCK_MESSAGE_MAIN.format(branch=branch, file=file_context)
        return HookDecision(Decision.BLOCK, msg, exit_code=2)

    if matches_valid_pattern(branch):
        return HookDecision(Decision.ALLOW)

    # Non-standard branch
    suggested = suggest_branch_name(branch)
    if is_strict_mode():
        return HookDecision(
            Decision.BLOCK,
            BLOCK_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested),
            exit_code=2,
        )

    return HookDecision(
        Decision.WARN,
        output_json={
            "systemMessage": WARN_MESSAGE_NONSTANDARD.format(branch=branch, suggested=suggested)
        },
    )


def get_git_context() -> GitContext:
    """
    Gather all git context in minimal subprocess calls.

    Reduces 5 subprocess calls to 2-3 by combining checks.
    """
    # Call 1: Is this a git repo?
    # Try --absolute-git-dir (Git 2.13+), fallback to manual resolution
    success, git_dir = run_git("rev-parse", "--absolute-git-dir")
    if not success:
        success, git_dir = run_git("rev-parse", "--git-dir")
        if not success:
            return GitContext()  # Not a git repo (defaults: is_repo=False)

        if not os.path.isabs(git_dir):
            # Resolve relative path to absolute
            # First try --show-toplevel to get repository root
            toplevel_ok, toplevel = run_git("rev-parse", "--show-toplevel")
            if toplevel_ok and toplevel:
                git_dir = os.path.join(toplevel.strip(), git_dir.strip())
            else:
                # Fallback: use current working directory
                git_dir = os.path.abspath(git_dir.strip())

    # Follow gitdir file indirection for worktrees/submodules
    resolved_git_dir = resolve_git_dir(git_dir.strip())

    # Check if bare repo BEFORE other checks
    success, is_bare_output = run_git("rev-parse", "--is-bare-repository")
    is_bare = success and is_bare_output.strip().lower() == "true"

    if is_bare:
        return GitContext(is_repo=True, is_bare=True, git_dir=resolved_git_dir)

    # Call 2: Check for commits and get branch name
    # First check if commits exist (needed to distinguish new repo from detached HEAD)
    commits_exist, _ = run_git("rev-parse", "--verify", "HEAD")

    # Then check for branch name via symbolic-ref
    # symbolic-ref fails on detached HEAD, but may succeed on new repos with no commits
    success, branch_output = run_git("symbolic-ref", "--short", "HEAD")

    if success and branch_output:
        # On a branch
        return GitContext(
            is_repo=True,
            git_dir=resolved_git_dir,
            has_commits=commits_exist,
            branch=branch_output.strip(),
            is_detached=False,
        )
    else:
        # Detached HEAD (only if commits exist; otherwise it's just a new repo)
        return GitContext(
            is_repo=True,
            git_dir=resolved_git_dir,
            has_commits=commits_exist,
            branch=None,
            is_detached=commits_exist,
        )


def get_git_operation_state(git_dir: str | None) -> str | None:
    """
    Detect if a git operation is in progress.

    Args:
        git_dir: Path to .git directory (from GitContext)

    Returns:
        'rebase' | 'merge' | 'cherry-pick' | 'bisect' | 'stash-apply' | None
    """
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

    # Stash apply conflict (AUTO_MERGE exists without merge in progress)
    if os.path.exists(os.path.join(git_dir, "AUTO_MERGE")):
        return "stash-apply"

    return None


def main():
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        # Only check Edit and Write tools
        if tool_name not in ("Edit", "Write"):
            sys.exit(0)

        log("DEBUG", f"Hook invoked: tool={tool_name}")

        # Check bypass FIRST (before any git operations)
        if check_bypass():
            sys.exit(0)

        # Gather git context
        ctx = get_git_context()
        file_path = tool_input.get("file_path", "")
        operation = get_git_operation_state(ctx.git_dir) if ctx.is_repo else None

        log("DEBUG", f"Checking edit to: {file_path}")

        # Evaluate gitflow rules
        decision = evaluate_gitflow_rules(ctx, file_path, operation)

        # Log decision with context
        if not ctx.is_repo:
            log("DEBUG", "Not a git repo, allowing")
        elif ctx.is_bare:
            log("DEBUG", "Bare repository, skipping checks")
        elif not ctx.has_commits:
            log("INFO", "Repository has no commits yet - allowing edits for bootstrapping")
        elif decision.decision == Decision.ALLOW and is_file_allowed(file_path):
            log("DEBUG", f"File matches allowlist, bypassing protection: {file_path}")
        elif operation:
            log("DEBUG" if decision.decision != Decision.BLOCK else "INFO", f"Operation: {operation}")
        log("DEBUG", f"Decision: {decision.decision.value}")

        # Execute decision
        if decision.output_json:
            print(json.dumps(decision.output_json))

        if decision.message and decision.decision == Decision.BLOCK:
            log("INFO", f"BLOCKED: {decision.message[:50]}...")
            print(decision.message, file=sys.stderr)

        sys.exit(decision.exit_code)

    except json.JSONDecodeError as e:
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        raise  # Let these propagate with their exit codes
    except Exception as e:
        import traceback

        tool_info = (
            f"tool={data.get('tool_name', 'unknown')}" if "data" in dir() else "before parsing"
        )
        log("ERROR", f"Unexpected error ({tool_info}): {type(e).__name__}: {e}")
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        print(f"Hook error ({tool_info}): {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
