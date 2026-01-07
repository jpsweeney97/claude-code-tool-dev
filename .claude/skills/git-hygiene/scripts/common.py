#!/usr/bin/env python3
"""Shared utilities for git-hygiene scripts. Stdlib only."""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple


@dataclass
class Result:
    """Standard result for JSON output."""
    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat(),
        }


def run_git(args: List[str], timeout: int = 60) -> Tuple[int, str, str]:
    """Run git command. Returns (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", "git not found in PATH"


def get_git_dir() -> Optional[Path]:
    """Get .git directory path."""
    code, stdout, _ = run_git(["rev-parse", "--git-dir"])
    if code == 0 and stdout:
        return Path(stdout).resolve()
    return None


def get_default_branch() -> str:
    """Get default branch (main or master)."""
    code, stdout, _ = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0 and stdout:
        return stdout.split("/")[-1]
    code, _, _ = run_git(["rev-parse", "--verify", "main"])
    return "main" if code == 0 else "master"


def get_worktree_branches() -> set[str]:
    """Get branches checked out in worktrees."""
    code, stdout, _ = run_git(["worktree", "list", "--porcelain"])
    if code != 0:
        return set()
    branches = set()
    for line in stdout.split("\n"):
        if line.startswith("branch refs/heads/"):
            branches.add(line.replace("branch refs/heads/", ""))
    return branches


def is_branch_merged(branch: str, target: Optional[str] = None) -> Tuple[bool, str]:
    """Check if branch is merged into target. Returns (is_merged, method).

    Methods: 'ancestor' (direct), 'cherry' (rebased), 'none' (not merged)
    """
    if target is None:
        target = get_default_branch()

    # Method 1: Direct ancestry
    code, _, _ = run_git(["merge-base", "--is-ancestor", branch, target])
    if code == 0:
        return True, "ancestor"

    # Method 2: Cherry (finds rebased equivalents)
    code, stdout, _ = run_git(["cherry", target, branch])
    if code == 0:
        lines = [l for l in stdout.strip().split("\n") if l.strip()]
        if not lines or all(l.startswith("-") for l in lines):
            return True, "cherry"

    return False, "none"
