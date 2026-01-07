#!/usr/bin/env python3
"""
Comprehensive git repository analysis for hygiene assessment.

Scans branches, stashes, untracked files, and repository health.
Exit codes:
    0 - Analysis completed successfully
    1 - Error (not a git repo, git not found)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from common import is_branch_merged


@dataclass
class BranchInfo:
    """Information about a branch."""
    name: str
    is_gone: bool = False
    is_merged: bool = False
    last_commit_days: Optional[int] = None
    tracking: Optional[str] = None


@dataclass
class StashInfo:
    """Information about a stash entry."""
    index: int
    message: str
    age_days: int
    branch: Optional[str] = None


@dataclass
class UntrackedInfo:
    """Categorized untracked files."""
    build_artifacts: list[str] = field(default_factory=list)
    temp_files: list[str] = field(default_factory=list)
    large_files: list[tuple[str, int]] = field(default_factory=list)  # (path, size_bytes)
    other: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    branches: dict = field(default_factory=dict)
    stashes: list[dict] = field(default_factory=list)
    untracked: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "branches": self.branches,
            "stashes": self.stashes,
            "untracked": self.untracked,
            "stats": self.stats,
            "error": self.error,
        }


# Common build artifact patterns
BUILD_PATTERNS = {
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", ".next", "dist", "build", "*.egg-info", ".eggs",
    "target", "*.class", "*.jar",
    ".gradle", ".idea", ".vscode",
    "*.o", "*.a", "*.so", "*.dylib",
    "Pods", ".build", "DerivedData",
}

# Temp file patterns
TEMP_PATTERNS = {
    ".DS_Store", "Thumbs.db", "*.swp", "*.swo", "*.tmp", "*.temp",
    "*~", "*.bak", "*.log", ".env.local",
}


def run_git(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
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


def get_default_branch() -> str:
    """Get the default branch name (main or master)."""
    code, stdout, _ = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0 and stdout:
        return stdout.split("/")[-1]
    # Fallback: check if main or master exists
    code, _, _ = run_git(["rev-parse", "--verify", "main"])
    if code == 0:
        return "main"
    return "master"


def get_current_branch() -> Optional[str]:
    """Get current branch name."""
    code, stdout, _ = run_git(["branch", "--show-current"])
    return stdout if code == 0 and stdout else None


def analyze_branches(days_threshold: int = 30) -> dict:
    """Analyze all local branches."""
    result = {
        "gone": [],
        "merged_stale": [],
        "unmerged_stale": [],
        "active": [],
        "current": get_current_branch(),
        "default": get_default_branch(),
    }

    # Get branch list with verbose info
    code, stdout, _ = run_git(["branch", "-vv"])
    if code != 0:
        return result

    default_branch = result["default"]
    current_branch = result["current"]

    for line in stdout.split("\n"):
        if not line.strip():
            continue

        # Parse branch line: "* main abc1234 [origin/main] commit message"
        is_current = line.startswith("*")
        line = line[2:].strip()  # Remove "* " or "  " prefix

        parts = line.split()
        if len(parts) < 2:
            continue

        branch_name = parts[0]
        if branch_name in (default_branch, "HEAD"):
            result["active"].append(branch_name)
            continue

        # Check if gone
        is_gone = "[gone]" in line

        if is_gone:
            result["gone"].append(branch_name)
            continue

        # Check if merged into default branch
        is_merged, _ = is_branch_merged(branch_name, default_branch)

        # Get last commit date
        code, date_str, _ = run_git([
            "log", "-1", "--format=%ci", branch_name
        ])
        last_commit_days = None
        if code == 0 and date_str:
            try:
                commit_date = datetime.fromisoformat(date_str.split()[0])
                last_commit_days = (datetime.now() - commit_date).days
            except (ValueError, IndexError):
                pass

        # Categorize
        if is_merged and (last_commit_days is None or last_commit_days > 7):
            result["merged_stale"].append(branch_name)
        elif not is_merged and last_commit_days and last_commit_days > days_threshold:
            result["unmerged_stale"].append(branch_name)
        else:
            result["active"].append(branch_name)

    return result


def analyze_stashes(days_threshold: int = 30) -> list[dict]:
    """Analyze stash entries."""
    stashes = []

    # Use null byte delimiter - stash messages can contain |
    code, stdout, _ = run_git(["stash", "list", "--format=%gd%x00%gs%x00%ci"])
    if code != 0 or not stdout:
        return stashes

    for line in stdout.split("\n"):
        if not line.strip():
            continue

        parts = line.split("\x00")
        if len(parts) < 3:
            continue

        try:
            # Parse stash index from "stash@{0}"
            index_match = re.search(r"stash@\{(\d+)\}", parts[0])
            if not index_match:
                continue
            index = int(index_match.group(1))

            message = parts[1].strip()

            # Parse date
            date_str = parts[2].strip()
            try:
                stash_date = datetime.fromisoformat(date_str.split()[0])
                age_days = (datetime.now() - stash_date).days
            except (ValueError, IndexError):
                age_days = 0

            stashes.append({
                "index": index,
                "message": message,
                "age_days": age_days,
                "stale": age_days > days_threshold,
            })
        except (ValueError, IndexError):
            continue

    return stashes


def matches_pattern(filepath: str, patterns: set[str]) -> bool:
    """Check if filepath matches any pattern.

    Handles:
    - Exact basename: .DS_Store
    - Suffix glob: *.pyc, *~ (matches files ending with suffix)
    - Prefix glob: test* (matches files starting with prefix)
    - Directory: node_modules (matches any path component)
    """
    name = os.path.basename(filepath)
    parts = filepath.replace("\\", "/").split("/")

    for pattern in patterns:
        # Exact basename match
        if name == pattern:
            return True
        # Suffix glob (*.pyc, *~) - asterisk at start
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
        # Prefix glob (test*) - asterisk at end
        if pattern.endswith("*") and name.startswith(pattern[:-1]):
            return True
        # Directory pattern - check path components
        if pattern in parts:
            return True
    return False


def analyze_untracked(large_threshold_mb: float = 1.0) -> dict:
    """Analyze untracked files."""
    result = {
        "build_artifacts": [],
        "temp_files": [],
        "large_files": [],
        "other": [],
    }

    code, stdout, _ = run_git(["status", "--porcelain", "-uall"])
    if code != 0:
        return result

    large_threshold_bytes = int(large_threshold_mb * 1024 * 1024)

    for line in stdout.split("\n"):
        if not line.strip():
            continue

        # Only process untracked files (start with ??)
        if not line.startswith("??"):
            continue

        filepath = line[3:].strip()

        # Check patterns
        if matches_pattern(filepath, BUILD_PATTERNS):
            result["build_artifacts"].append(filepath)
        elif matches_pattern(filepath, TEMP_PATTERNS):
            result["temp_files"].append(filepath)
        else:
            # Check file size for non-directories
            if os.path.isfile(filepath):
                try:
                    size = os.path.getsize(filepath)
                    if size > large_threshold_bytes:
                        result["large_files"].append({
                            "path": filepath,
                            "size_mb": round(size / (1024 * 1024), 2),
                        })
                        continue
                except OSError:
                    pass
            result["other"].append(filepath)

    return result


def get_gc_stats() -> dict:
    """Get garbage collection statistics."""
    stats = {
        "loose_objects": 0,
        "pack_files": 0,
    }

    # Count loose objects (approximate)
    code, stdout, _ = run_git(["count-objects", "-v"])
    if code == 0:
        for line in stdout.split("\n"):
            if line.startswith("count:"):
                try:
                    stats["loose_objects"] = int(line.split(":")[1].strip())
                except ValueError:
                    pass
            elif line.startswith("packs:"):
                try:
                    stats["pack_files"] = int(line.split(":")[1].strip())
                except ValueError:
                    pass

    return stats


def run_analysis(
    days_threshold: int = 30,
    large_threshold_mb: float = 1.0,
    category: str = "all",
) -> AnalysisResult:
    """Run complete repository analysis."""
    # Verify we're in a git repo
    code, _, _ = run_git(["rev-parse", "--git-dir"])
    if code != 0:
        return AnalysisResult(error="Not a git repository")

    result = AnalysisResult()

    # Analyze based on category
    if category in ("all", "branches"):
        result.branches = analyze_branches(days_threshold)

    if category in ("all", "stashes"):
        result.stashes = analyze_stashes(days_threshold)

    if category in ("all", "untracked"):
        result.untracked = analyze_untracked(large_threshold_mb)

    # Calculate stats
    result.stats = {
        "total_branches": len(result.branches.get("gone", [])) +
                          len(result.branches.get("merged_stale", [])) +
                          len(result.branches.get("unmerged_stale", [])) +
                          len(result.branches.get("active", [])),
        "cleanable_branches": len(result.branches.get("gone", [])) +
                              len(result.branches.get("merged_stale", [])),
        "stash_count": len(result.stashes),
        "stale_stashes": len([s for s in result.stashes if s.get("stale")]),
        "untracked_count": (
            len(result.untracked.get("build_artifacts", [])) +
            len(result.untracked.get("temp_files", [])) +
            len(result.untracked.get("large_files", [])) +
            len(result.untracked.get("other", []))
        ),
    }

    if category == "all":
        result.stats.update(get_gc_stats())

    return result


def format_human(result: AnalysisResult) -> str:
    """Format result for human reading."""
    lines = []

    if result.error:
        lines.append(f"Error: {result.error}")
        return "\n".join(lines)

    # Branches
    if result.branches:
        lines.append("## Branches")
        if result.branches.get("gone"):
            lines.append(f"  [gone] (safe to delete): {', '.join(result.branches['gone'])}")
        if result.branches.get("merged_stale"):
            lines.append(f"  Merged & stale (safe): {', '.join(result.branches['merged_stale'])}")
        if result.branches.get("unmerged_stale"):
            lines.append(f"  Unmerged & stale (review): {', '.join(result.branches['unmerged_stale'])}")
        lines.append(f"  Active: {len(result.branches.get('active', []))} branches")
        lines.append("")

    # Stashes
    if result.stashes:
        lines.append("## Stashes")
        for stash in result.stashes:
            status = "STALE" if stash["stale"] else "recent"
            lines.append(f"  stash@{{{stash['index']}}}: {stash['message'][:50]} ({stash['age_days']}d, {status})")
        lines.append("")

    # Untracked
    if result.untracked:
        lines.append("## Untracked Files")
        if result.untracked.get("build_artifacts"):
            lines.append(f"  Build artifacts: {len(result.untracked['build_artifacts'])} items")
        if result.untracked.get("temp_files"):
            lines.append(f"  Temp files: {len(result.untracked['temp_files'])} items")
        if result.untracked.get("large_files"):
            for item in result.untracked["large_files"]:
                lines.append(f"  Large file: {item['path']} ({item['size_mb']}MB)")
        if result.untracked.get("other"):
            lines.append(f"  Other: {len(result.untracked['other'])} items")
        lines.append("")

    # Stats
    lines.append("## Summary")
    lines.append(f"  Cleanable branches: {result.stats.get('cleanable_branches', 0)}")
    lines.append(f"  Stale stashes: {result.stats.get('stale_stashes', 0)}")
    lines.append(f"  Untracked files: {result.stats.get('untracked_count', 0)}")
    if result.stats.get("loose_objects"):
        lines.append(f"  Loose objects: {result.stats['loose_objects']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze git repository for hygiene issues",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Staleness threshold in days (default: 30)",
    )
    parser.add_argument(
        "--large-mb",
        type=float,
        default=1.0,
        help="Large file threshold in MB (default: 1.0)",
    )
    parser.add_argument(
        "--category",
        choices=["all", "branches", "stashes", "untracked"],
        default="all",
        help="Category to analyze (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    args = parser.parse_args()

    result = run_analysis(
        days_threshold=args.days,
        large_threshold_mb=args.large_mb,
        category=args.category,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_human(result))

    sys.exit(1 if result.error else 0)


if __name__ == "__main__":
    main()
