"""Tests for WorktreeManager — isolated worktree creation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from server.worktree_manager import WorktreeManager


def _init_repo(repo_path: Path) -> str:
    """Init a tmp git repo with one commit. Returns the HEAD SHA."""

    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
    )
    (repo_path / "README.md").write_text("hello\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_create_worktree_at_expected_base_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"

    mgr = WorktreeManager()
    mgr.create_worktree(repo_root=repo, base_commit=head, worktree_path=wk_path)

    assert wk_path.exists()
    assert (wk_path / "README.md").exists()
    # Worktree is in detached HEAD at the expected commit.
    wk_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=wk_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert wk_head == head


def test_create_worktree_fails_fast_on_unknown_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"

    mgr = WorktreeManager()
    with pytest.raises(RuntimeError, match="worktree add failed"):
        mgr.create_worktree(
            repo_root=repo,
            base_commit="0" * 40,
            worktree_path=wk_path,
        )


def test_create_worktree_fails_fast_if_path_exists(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    wk_path = tmp_path / "workspaces" / "wk-1"
    wk_path.mkdir(parents=True)
    (wk_path / "preexisting.txt").write_text("do not overwrite me")

    mgr = WorktreeManager()
    with pytest.raises(RuntimeError, match="worktree add failed"):
        mgr.create_worktree(repo_root=repo, base_commit=head, worktree_path=wk_path)
