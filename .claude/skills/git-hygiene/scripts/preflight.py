#!/usr/bin/env python3
"""
Preflight checks for git hygiene operations.

Detects active git operations that would make cleanup unsafe.
Exit codes:
    0 - Safe to proceed
    1 - Not a git repository or error
    2 - Active operation detected (blocks cleanup)
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from common import run_git, get_git_dir


@dataclass
class PreflightResult:
    """Result of preflight checks."""
    safe: bool
    git_dir: Optional[str] = None
    is_shallow: bool = False
    active_operations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "safe": self.safe,
            "git_dir": self.git_dir,
            "is_shallow": self.is_shallow,
            "active_operations": self.active_operations,
            "warnings": self.warnings,
            "error": self.error,
        }


def check_active_operations(git_dir: Path) -> list[str]:
    """Check for active git operations that would block cleanup."""
    operations = []

    # Rebase in progress
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        operations.append("rebase")

    # Merge in progress
    if (git_dir / "MERGE_HEAD").exists():
        operations.append("merge")

    # Cherry-pick in progress
    if (git_dir / "CHERRY_PICK_HEAD").exists():
        operations.append("cherry-pick")

    # Bisect in progress
    if (git_dir / "BISECT_LOG").exists():
        operations.append("bisect")

    # Revert in progress
    if (git_dir / "REVERT_HEAD").exists():
        operations.append("revert")

    # Sequence in progress (multi-commit operation)
    if (git_dir / "sequencer").exists():
        operations.append("sequencer")

    return operations


def check_shallow(git_dir: Path) -> bool:
    """Check if this is a shallow clone."""
    return (git_dir / "shallow").exists()


def check_worktrees(git_dir: Path) -> list[str]:
    """Check for linked worktrees that might be affected."""
    warnings = []
    worktrees_dir = git_dir / "worktrees"
    if worktrees_dir.exists():
        worktree_count = len(list(worktrees_dir.iterdir()))
        if worktree_count > 0:
            warnings.append(f"Repository has {worktree_count} linked worktree(s)")
    return warnings


def run_preflight() -> PreflightResult:
    """Run all preflight checks."""
    # Find git directory
    git_dir = get_git_dir()
    if not git_dir:
        return PreflightResult(
            safe=False,
            error="Not a git repository (or git not installed)",
        )

    # Check for active operations
    active_ops = check_active_operations(git_dir)

    # Check for shallow clone
    is_shallow = check_shallow(git_dir)

    # Check for worktrees
    warnings = check_worktrees(git_dir)

    if is_shallow:
        warnings.append("Shallow clone detected - some operations may be limited")

    return PreflightResult(
        safe=len(active_ops) == 0,
        git_dir=str(git_dir),
        is_shallow=is_shallow,
        active_operations=active_ops,
        warnings=warnings,
    )


def format_human(result: PreflightResult) -> str:
    """Format result for human reading."""
    lines = []

    if result.error:
        lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    if result.safe:
        lines.append("Preflight checks passed")
        lines.append(f"  Git directory: {result.git_dir}")
    else:
        lines.append("Preflight checks FAILED - active operations detected:")
        for op in result.active_operations:
            resolution = {
                "rebase": "Complete with 'git rebase --continue' or abort with 'git rebase --abort'",
                "merge": "Complete merge or abort with 'git merge --abort'",
                "cherry-pick": "Complete or abort with 'git cherry-pick --abort'",
                "bisect": "Complete or reset with 'git bisect reset'",
                "revert": "Complete or abort with 'git revert --abort'",
                "sequencer": "Complete the operation in progress",
            }.get(op, "Complete or abort the operation")
            lines.append(f"  - {op}: {resolution}")

    if result.warnings:
        lines.append("\nWarnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Preflight checks for git hygiene operations",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    result = run_preflight()

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_human(result))

    # Exit codes
    if result.error:
        sys.exit(1)
    elif not result.safe:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
