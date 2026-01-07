#!/usr/bin/env python3
"""Tests for preflight.py safety checks."""

import os
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from preflight import check_active_operations, check_shallow, run_preflight


class TestCheckActiveOperations:
    """Tests for detecting active git operations."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True, check=True)
        cls.git_dir = Path(cls.temp_dir) / ".git"

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_detects_merge_in_progress(self):
        """MERGE_HEAD file indicates merge in progress."""
        merge_head = self.git_dir / "MERGE_HEAD"
        merge_head.write_text("abc123\n")
        try:
            ops = check_active_operations(self.git_dir)
            assert "merge" in ops
        finally:
            merge_head.unlink()

    def test_detects_rebase_merge(self):
        """rebase-merge directory indicates rebase in progress."""
        rebase_dir = self.git_dir / "rebase-merge"
        rebase_dir.mkdir()
        try:
            ops = check_active_operations(self.git_dir)
            assert "rebase" in ops
        finally:
            rebase_dir.rmdir()

    def test_detects_cherry_pick(self):
        """CHERRY_PICK_HEAD file indicates cherry-pick in progress."""
        cherry_head = self.git_dir / "CHERRY_PICK_HEAD"
        cherry_head.write_text("abc123\n")
        try:
            ops = check_active_operations(self.git_dir)
            assert "cherry-pick" in ops
        finally:
            cherry_head.unlink()

    def test_clean_repo_has_no_operations(self):
        """Clean repo returns empty list."""
        ops = check_active_operations(self.git_dir)
        assert ops == []


class TestRunPreflight:
    """Integration tests for run_preflight."""

    @classmethod
    def setup_class(cls):
        cls.original_dir = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp()
        os.chdir(cls.temp_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], capture_output=True, check=True)

    @classmethod
    def teardown_class(cls):
        os.chdir(cls.original_dir)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_clean_repo_is_safe(self):
        """Clean repo passes preflight."""
        result = run_preflight()
        assert result.safe is True
        assert result.active_operations == []

    def test_merge_blocks_preflight(self):
        """Active merge blocks preflight."""
        git_dir = Path(self.temp_dir) / ".git"
        merge_head = git_dir / "MERGE_HEAD"
        merge_head.write_text("abc123\n")
        try:
            result = run_preflight()
            assert result.safe is False
            assert "merge" in result.active_operations
        finally:
            merge_head.unlink()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
