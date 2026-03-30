#!/usr/bin/env python3
"""auto_commit.py — Narrow-scope git commit for handoff state changes.

Checks git state, stages specified files, commits with provided message.
Used by save/load/quicksave skills after file writes or archive moves.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def check_git_state() -> tuple[bool, str]:
    """Return (can_commit, reason). Checks: no repo, detached HEAD, rebase."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return False, "No git repository"
        git_dir = Path(r.stdout.strip())
        r2 = subprocess.run(
            ["git", "symbolic-ref", "-q", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if r2.returncode != 0:
            return False, "Detached HEAD"
        if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
            return False, "Rebase in progress"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return False, f"Git check failed: {exc}"
    return True, ""


def auto_commit(
    files: list[str], message: str, *, staged: bool = False,
) -> tuple[bool, str]:
    """Stage files and commit with --only. Returns (success, reason)."""
    ok, reason = check_git_state()
    if not ok:
        return False, reason
    try:
        if not staged:
            for f in files:
                subprocess.run(
                    ["git", "add", "--", f],
                    capture_output=True, text=True, timeout=10, check=True,
                )
        r = subprocess.run(
            ["git", "commit", "--only", *files, "-m", message],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            return False, f"Commit failed: {r.stderr.strip()}"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, subprocess.CalledProcessError) as exc:
        return False, f"Commit failed: {exc}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    """CLI: auto_commit.py -m MESSAGE [--staged] [FILES...]"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-commit handoff files")
    parser.add_argument("files", nargs="*", help="Files to commit")
    parser.add_argument("-m", "--message", required=True, help="Commit message")
    parser.add_argument("--staged", action="store_true", help="Files already staged")
    args = parser.parse_args(argv)
    ok, reason = auto_commit(args.files, args.message, staged=args.staged)
    if not ok:
        print(f"Warning: Handoff saved but not committed — {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
