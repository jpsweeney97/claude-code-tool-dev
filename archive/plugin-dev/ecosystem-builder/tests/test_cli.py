"""Tests for CLI commands."""

import os
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent


class TestRunCommand:
    """Tests for run command."""

    def test_run_help_shows_mock_flag(self) -> None:
        """--mock flag should appear in help."""
        result = subprocess.run(
            ["uv", "run", "bin/ecosystem-builder", "run", "--help"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
        )

        assert result.returncode == 0
        assert "--mock" in result.stdout

    def test_run_mock_dry_run_succeeds(self) -> None:
        """--mock --dry-run should succeed without Claude Code runtime."""
        result = subprocess.run(
            ["uv", "run", "bin/ecosystem-builder", "run", "--artifacts", "1", "--mock", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            env={**os.environ, "HOME": str(PROJECT_DIR / "test_home")},
        )

        assert result.returncode == 0
        assert "Created run:" in result.stdout
        assert "Dry run" in result.stdout
