#!/usr/bin/env python3
"""
Execute git cleanup operations safely.

Performs cleanup with verification and generates undo instructions.
Exit codes:
    0 - All operations completed successfully
    1 - Error (not a git repo, git not found)
    2 - Some operations failed (partial success)
    10 - Validation failure (unsafe operation blocked)
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Optional

from common import run_git, get_default_branch, get_worktree_branches


@dataclass
class OperationResult:
    """Result of a single cleanup operation."""
    operation: str
    target: str
    success: bool
    message: str
    undo_command: Optional[str] = None


@dataclass
class CleanupResult:
    """Complete cleanup result."""
    operations: list[dict] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    blocked_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "operations": self.operations,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "blocked_count": self.blocked_count,
            "error": self.error,
        }


def is_branch_merged(branch: str, target: str = None) -> bool:
    """Check if branch is merged into target (or default branch)."""
    if target is None:
        target = get_default_branch()
    code, _, _ = run_git(["merge-base", "--is-ancestor", branch, target])
    return code == 0


def is_branch_gone(branch: str) -> bool:
    """Check if branch's upstream is gone."""
    code, stdout, _ = run_git(["branch", "-vv"])
    if code != 0:
        return False
    for line in stdout.split("\n"):
        if f"  {branch} " in line or f"* {branch} " in line:
            return "[gone]" in line
    return False


def get_branch_commit(branch: str) -> Optional[str]:
    """Get the commit hash for a branch (for undo)."""
    code, stdout, _ = run_git(["rev-parse", branch])
    return stdout if code == 0 else None


def delete_branch(branch: str, force: bool = False) -> OperationResult:
    """Delete a local branch."""
    # Safety checks
    current_code, current, _ = run_git(["branch", "--show-current"])
    if current_code == 0 and current == branch:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message="Cannot delete current branch",
        )

    # Check if branch is in a worktree
    worktree_branches = get_worktree_branches()
    if branch in worktree_branches:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message=f"Branch '{branch}' is checked out in a worktree",
        )

    default = get_default_branch()
    if branch == default:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message=f"Cannot delete default branch '{default}'",
        )

    # Check merge status if not forcing
    if not force and not is_branch_merged(branch) and not is_branch_gone(branch):
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message="Branch has unmerged commits. Use --force to delete anyway.",
        )

    # Get commit for undo before deleting
    commit = get_branch_commit(branch)

    # Delete
    flag = "-D" if force else "-d"
    code, _, stderr = run_git(["branch", flag, branch])

    if code == 0:
        undo = f"git branch {branch} {commit}" if commit else None
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=True,
            message=f"Deleted branch '{branch}'",
            undo_command=undo,
        )
    else:
        return OperationResult(
            operation="delete_branch",
            target=branch,
            success=False,
            message=f"Failed to delete: {stderr}",
        )


def get_stash_sha(stash_ref: str) -> Optional[str]:
    """Get SHA for a stash reference."""
    code, sha, _ = run_git(["rev-parse", stash_ref])
    return sha if code == 0 else None


def find_stash_index_by_sha(sha: str) -> Optional[int]:
    """Find current index for a stash SHA."""
    code, stdout, _ = run_git(["stash", "list", "--format=%H"])
    if code != 0 or not stdout:
        return None
    shas = stdout.strip().split("\n")
    try:
        return shas.index(sha)
    except ValueError:
        return None


def drop_stash(stash_ref: str) -> OperationResult:
    """Drop a stash entry safely by resolving SHA first."""
    # Get SHA to avoid race with shifting indices
    sha = get_stash_sha(stash_ref)
    if not sha:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Stash {stash_ref} not found",
        )

    # Find current index for this SHA
    current_index = find_stash_index_by_sha(sha)
    if current_index is None:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Stash {stash_ref} ({sha[:8]}) no longer exists",
        )

    # Drop by current index
    code, _, stderr = run_git(["stash", "drop", f"stash@{{{current_index}}}"])

    if code == 0:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=True,
            message=f"Dropped {stash_ref}",
        )
    else:
        return OperationResult(
            operation="drop_stash",
            target=stash_ref,
            success=False,
            message=f"Failed to drop: {stderr}",
        )


def run_gc(aggressive: bool = False) -> OperationResult:
    """Run git garbage collection."""
    args = ["gc"]
    if aggressive:
        args.append("--aggressive")

    code, stdout, stderr = run_git(args, timeout=300)  # GC can take a while

    if code == 0:
        return OperationResult(
            operation="gc",
            target="repository",
            success=True,
            message="Garbage collection completed",
        )
    else:
        return OperationResult(
            operation="gc",
            target="repository",
            success=False,
            message=f"GC failed: {stderr}",
        )


def prune_remote() -> OperationResult:
    """Prune stale remote-tracking branches."""
    code, stdout, stderr = run_git(["remote", "prune", "origin"])

    if code == 0:
        return OperationResult(
            operation="prune_remote",
            target="origin",
            success=True,
            message="Pruned stale remote-tracking branches",
        )
    else:
        return OperationResult(
            operation="prune_remote",
            target="origin",
            success=False,
            message=f"Prune failed: {stderr}",
        )


def run_cleanup(
    branches: list[str] = None,
    stashes: list[int] = None,
    gc: bool = False,
    gc_aggressive: bool = False,
    prune: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> CleanupResult:
    """Run cleanup operations."""
    # Verify we're in a git repo
    code, _, _ = run_git(["rev-parse", "--git-dir"])
    if code != 0:
        return CleanupResult(error="Not a git repository")

    result = CleanupResult()

    # Process branches
    if branches:
        for branch in branches:
            if dry_run:
                op = OperationResult(
                    operation="delete_branch",
                    target=branch,
                    success=True,
                    message=f"[DRY RUN] Would delete branch '{branch}'",
                )
            else:
                op = delete_branch(branch, force=force)

            result.operations.append({
                "operation": op.operation,
                "target": op.target,
                "success": op.success,
                "message": op.message,
                "undo_command": op.undo_command,
            })
            if op.success:
                result.success_count += 1
            else:
                if "unmerged" in op.message.lower():
                    result.blocked_count += 1
                else:
                    result.failure_count += 1

    # Process stashes (drop in reverse order to preserve indices)
    if stashes:
        for index in sorted(stashes, reverse=True):
            if dry_run:
                op = OperationResult(
                    operation="drop_stash",
                    target=f"stash@{{{index}}}",
                    success=True,
                    message=f"[DRY RUN] Would drop stash@{{{index}}}",
                )
            else:
                op = drop_stash(f"stash@{{{index}}}")

            result.operations.append({
                "operation": op.operation,
                "target": op.target,
                "success": op.success,
                "message": op.message,
                "undo_command": op.undo_command,
            })
            if op.success:
                result.success_count += 1
            else:
                result.failure_count += 1

    # Prune remote
    if prune:
        if dry_run:
            op = OperationResult(
                operation="prune_remote",
                target="origin",
                success=True,
                message="[DRY RUN] Would prune remote-tracking branches",
            )
        else:
            op = prune_remote()

        result.operations.append({
            "operation": op.operation,
            "target": op.target,
            "success": op.success,
            "message": op.message,
            "undo_command": op.undo_command,
        })
        if op.success:
            result.success_count += 1
        else:
            result.failure_count += 1

    # Run GC
    if gc or gc_aggressive:
        if dry_run:
            op = OperationResult(
                operation="gc",
                target="repository",
                success=True,
                message=f"[DRY RUN] Would run git gc{' --aggressive' if gc_aggressive else ''}",
            )
        else:
            op = run_gc(aggressive=gc_aggressive)

        result.operations.append({
            "operation": op.operation,
            "target": op.target,
            "success": op.success,
            "message": op.message,
            "undo_command": op.undo_command,
        })
        if op.success:
            result.success_count += 1
        else:
            result.failure_count += 1

    return result


def format_human(result: CleanupResult) -> str:
    """Format result for human reading."""
    lines = []

    if result.error:
        lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    lines.append("## Cleanup Results")
    lines.append("")

    for op in result.operations:
        status = "OK" if op["success"] else "FAILED"
        lines.append(f"  [{status}] {op['operation']}: {op['target']}")
        lines.append(f"         {op['message']}")
        if op.get("undo_command"):
            lines.append(f"         Undo: {op['undo_command']}")

    lines.append("")
    lines.append("## Summary")
    lines.append(f"  Successful: {result.success_count}")
    lines.append(f"  Failed: {result.failure_count}")
    lines.append(f"  Blocked (safety): {result.blocked_count}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Execute git cleanup operations",
    )
    parser.add_argument(
        "--branches",
        type=str,
        help="Comma-separated list of branches to delete",
    )
    parser.add_argument(
        "--stashes",
        type=str,
        help="Comma-separated list of stash indices to drop",
    )
    parser.add_argument(
        "--gc",
        action="store_true",
        help="Run git gc",
    )
    parser.add_argument(
        "--gc-aggressive",
        action="store_true",
        help="Run git gc --aggressive",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Prune stale remote-tracking branches",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force delete unmerged branches",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without doing it",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    # Parse inputs
    branches = args.branches.split(",") if args.branches else None
    stashes = [int(i) for i in args.stashes.split(",")] if args.stashes else None

    result = run_cleanup(
        branches=branches,
        stashes=stashes,
        gc=args.gc,
        gc_aggressive=args.gc_aggressive,
        prune=args.prune,
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_human(result))

    # Exit codes
    if result.error:
        sys.exit(1)
    elif result.failure_count > 0:
        sys.exit(2)
    elif result.blocked_count > 0:
        sys.exit(10)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
