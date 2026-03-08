"""Tests for marker-based project-root resolution."""
from __future__ import annotations

from pathlib import Path

from scripts.ticket_paths import discover_project_root


class TestDiscoverProjectRoot:
    """Marker-based project root discovery."""

    def test_finds_git_directory(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "src" / "pkg"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_finds_claude_directory(self, tmp_path: Path) -> None:
        (tmp_path / ".claude").mkdir()
        nested = tmp_path / "src" / "deep" / "pkg"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_finds_git_file_worktree(self, tmp_path: Path) -> None:
        """A .git file (worktree) is also a valid marker."""
        (tmp_path / ".git").write_text("gitdir: /some/other/.git/worktrees/x")
        nested = tmp_path / "src"
        nested.mkdir()
        root = discover_project_root(nested)
        assert root == tmp_path

    def test_prefers_nearest_ancestor(self, tmp_path: Path) -> None:
        """If multiple ancestors have markers, choose nearest."""
        (tmp_path / ".git").mkdir()
        inner = tmp_path / "subproject"
        inner.mkdir()
        (inner / ".claude").mkdir()
        deep = inner / "src"
        deep.mkdir()
        root = discover_project_root(deep)
        assert root == inner

    def test_returns_none_without_markers(self, tmp_path: Path) -> None:
        nested = tmp_path / "no" / "markers" / "here"
        nested.mkdir(parents=True)
        root = discover_project_root(nested)
        assert root is None

    def test_cwd_itself_is_root(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        root = discover_project_root(tmp_path)
        assert root == tmp_path

    def test_resolves_symlink_before_marker_lookup(self, tmp_path: Path) -> None:
        """Symlinked start paths resolve to the canonical project root."""
        (tmp_path / ".git").mkdir()
        real_nested = tmp_path / "real" / "src"
        real_nested.mkdir(parents=True)
        symlink_root = tmp_path.parent / f"{tmp_path.name}-link"
        symlink_root.symlink_to(tmp_path, target_is_directory=True)
        symlink_nested = symlink_root / "real" / "src"

        root = discover_project_root(symlink_nested)
        assert root == tmp_path.resolve()
