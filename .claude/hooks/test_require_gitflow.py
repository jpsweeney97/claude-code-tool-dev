"""Unit tests for require-gitflow.py hook."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import hyphenated module using importlib
spec = importlib.util.spec_from_file_location(
    "require_gitflow",
    Path(__file__).parent / "require-gitflow.py"
)
if spec is None or spec.loader is None:
    raise ImportError("Could not load require-gitflow.py")
require_gitflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(require_gitflow)

# Import functions for unit testing
suggest_branch_name = require_gitflow.suggest_branch_name
matches_valid_pattern = require_gitflow.matches_valid_pattern
get_protected_branches = require_gitflow.get_protected_branches
is_strict_mode = require_gitflow.is_strict_mode


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository on 'main' branch."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    (repo / "file.txt").write_text("content")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)
    return repo


def run_hook(cwd, tool_name="Edit", tool_input=None):
    """Helper to run the hook script with given input."""
    if tool_input is None:
        tool_input = {"file_path": "test.py"}
    input_data = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    return subprocess.run(
        [sys.executable, str(Path(__file__).parent / "require-gitflow.py")],
        input=input_data,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
