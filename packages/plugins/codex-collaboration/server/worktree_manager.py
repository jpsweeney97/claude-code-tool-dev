"""Isolated git worktree creation for delegation jobs.

See foundations.md §Execution Domain — one ephemeral worktree per job,
created from a specific base commit, in detached-HEAD state (no branch
pollution). Cleanup is deferred to the promotion slice.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class WorktreeManager:
    """Creates isolated git worktrees via `git worktree add --detach`."""

    def create_worktree(
        self,
        *,
        repo_root: Path,
        base_commit: str,
        worktree_path: Path,
    ) -> None:
        """Create a detached-HEAD worktree at `worktree_path` from `base_commit`.

        Fails fast on any git error. The parent directory of `worktree_path`
        is created if it does not exist. The leaf directory should be absent
        OR an empty directory that ``git worktree add`` can populate —
        a non-empty pre-existing leaf causes git to fail, which is propagated
        as ``RuntimeError``.
        """

        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "worktree",
                    "add",
                    "--detach",
                    str(worktree_path),
                    base_commit,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "worktree add failed: git returned non-zero. "
                f"Got: {(exc.stderr or exc.stdout).strip()!r:.200}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"worktree add failed: git timed out. Got: {worktree_path!r:.100}"
            ) from exc
