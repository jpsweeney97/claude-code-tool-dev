# Verify Skill Script Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate code duplication across verify skill scripts by extracting shared utilities into a common module.

**Architecture:** Create `_common.py` in the scripts directory containing shared utilities (date parsing, version detection, constants). Update all scripts to import from this module. No behavioral changes—pure refactoring with existing tests validating correctness.

**Tech Stack:** Python 3.12, standard library only (no external dependencies per skill-embedded script conventions)

---

## Task 1: Create Common Utilities Module

**Files:**
- Create: `.claude/skills/verify/scripts/_common.py`

**Step 1: Write the failing test**

```python
# Test file: test_common.py (temporary, run manually)
from _common import (
    parse_verified_date,
    get_claude_code_version,
    SECTION_ALIASES,
    DEFAULT_MAX_AGE_DAYS,
)
from datetime import date

# Test parse_verified_date
assert parse_verified_date("2026-01-05") == date(2026, 1, 5)
assert parse_verified_date("2026-01-05 (v2.0.76)") == date(2026, 1, 5)
assert parse_verified_date(None) is None
assert parse_verified_date("invalid") is None

# Test constants exist
assert DEFAULT_MAX_AGE_DAYS == 90
assert "skill" in SECTION_ALIASES
print("All tests pass!")
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python -c "from _common import parse_verified_date"`
Expected: FAIL with "ModuleNotFoundError: No module named '_common'"

**Step 3: Write the common module**

```python
#!/usr/bin/env python3
"""
Shared utilities for verify skill scripts.

This module consolidates common functions and constants used across
multiple scripts to maintain consistency and reduce duplication.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date, datetime


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

DEFAULT_MAX_AGE_DAYS: int = 90  # Claims older than this are considered stale


# Section normalization: map common variants to canonical names
# Keys are lowercase for case-insensitive matching
SECTION_ALIASES: dict[str, str] = {
    "feature": "Features",
    "setting": "Settings",
    "hook": "Hooks",
    "command": "Commands",
    "skill": "Skills",
    "agent": "Agents",
}


# =============================================================================
# DATE PARSING
# =============================================================================


def parse_verified_date(verified_date: str | None) -> date | None:
    """
    Parse a verification date, handling both plain and version-tagged formats.

    Supported formats:
        - "2026-01-05"               -> plain ISO date
        - "2026-01-05 (v2.0.76)"     -> date with version suffix

    Args:
        verified_date: Date string to parse, or None

    Returns:
        Parsed date object or None if invalid/missing.
    """
    if not verified_date:
        return None

    # Extract date portion (handles both plain dates and version-tagged dates)
    # Format: "YYYY-MM-DD" or "YYYY-MM-DD (vX.Y.Z)"
    date_str = verified_date.split(" ")[0].strip()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# =============================================================================
# VERSION DETECTION
# =============================================================================


def get_claude_code_version() -> str | None:
    """
    Get current Claude Code version by running 'claude --version'.

    Returns:
        Version string (e.g., "2.0.76") or None if unavailable.
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python -c "
from _common import parse_verified_date, get_claude_code_version, SECTION_ALIASES, DEFAULT_MAX_AGE_DAYS
from datetime import date
assert parse_verified_date('2026-01-05') == date(2026, 1, 5)
assert parse_verified_date('2026-01-05 (v2.0.76)') == date(2026, 1, 5)
assert parse_verified_date(None) is None
assert DEFAULT_MAX_AGE_DAYS == 90
assert 'skill' in SECTION_ALIASES
print('All tests pass!')
"`
Expected: "All tests pass!"

**Step 5: Commit**

```bash
git add .claude/skills/verify/scripts/_common.py
git commit -m "refactor(verify): add shared utilities module"
```

---

## Task 2: Update match_claim.py to Use Common Module

**Files:**
- Modify: `.claude/skills/verify/scripts/match_claim.py:40-64` (remove duplicate code)
- Modify: `.claude/skills/verify/scripts/match_claim.py:200-207` (remove duplicate SECTION_ALIASES)

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python match_claim.py "exit code 2 blocks" --quick`
Expected: Output showing match result (record actual output for comparison)

**Step 2: Update imports at top of file**

Replace lines 40-64 (the duplicate `parse_verified_date` and `DEFAULT_MAX_AGE_DAYS`) with import:

```python
# After line 33 (from pathlib import Path), add:
from _common import parse_verified_date, DEFAULT_MAX_AGE_DAYS, SECTION_ALIASES
```

**Step 3: Remove duplicate DEFAULT_MAX_AGE_DAYS declaration**

Delete line ~40:
```python
DEFAULT_MAX_AGE_DAYS: int = 90  # Claims older than this are considered stale
```

**Step 4: Remove duplicate parse_verified_date function**

Delete lines ~43-64 (the `parse_verified_date` function definition)

**Step 5: Remove duplicate SECTION_ALIASES**

Delete lines ~200-207:
```python
SECTION_ALIASES: dict[str, str] = {
    "feature": "Features",
    ...
}
```

**Step 6: Update check_staleness function**

The `check_staleness` function at ~67-84 uses `parse_verified_date` - verify it still works by running:

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python match_claim.py "exit code 2 blocks" --quick`
Expected: Same output as baseline

**Step 7: Commit**

```bash
git add .claude/skills/verify/scripts/match_claim.py
git commit -m "refactor(verify): use common module in match_claim.py"
```

---

## Task 3: Update refresh_claims.py to Use Common Module

**Files:**
- Modify: `.claude/skills/verify/scripts/refresh_claims.py:43-72` (remove duplicates)
- Modify: `.claude/skills/verify/scripts/refresh_claims.py:103-118` (remove duplicate version detection)

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python refresh_claims.py --summary`
Expected: Cache health report output (record for comparison)

**Step 2: Update imports**

After the existing imports, add:
```python
from _common import parse_verified_date, get_claude_code_version, DEFAULT_MAX_AGE_DAYS
```

**Step 3: Remove duplicate DEFAULT_MAX_AGE_DAYS**

Delete line ~43:
```python
DEFAULT_MAX_AGE_DAYS: int = 90
```

**Step 4: Remove duplicate parse_verified_date**

Delete lines ~51-72 (the function definition)

**Step 5: Remove duplicate get_claude_code_version**

Delete lines ~103-118 (the function definition)

**Step 6: Verify behavior unchanged**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python refresh_claims.py --summary`
Expected: Same output as baseline

**Step 7: Commit**

```bash
git add .claude/skills/verify/scripts/refresh_claims.py
git commit -m "refactor(verify): use common module in refresh_claims.py"
```

---

## Task 4: Update promote_claims.py to Use Common Module

**Files:**
- Modify: `.claude/skills/verify/scripts/promote_claims.py:36-49` (remove duplicate version detection)
- Modify: `.claude/skills/verify/scripts/promote_claims.py:78-85` (remove duplicate SECTION_ALIASES)

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python promote_claims.py --dry-run`
Expected: Output showing what would be promoted (record for comparison)

**Step 2: Update imports**

After existing imports, add:
```python
from _common import get_claude_code_version, SECTION_ALIASES
```

**Step 3: Remove duplicate get_claude_code_version**

Delete lines ~36-49 (the function definition)

**Step 4: Remove duplicate SECTION_ALIASES**

Delete lines ~78-85:
```python
SECTION_ALIASES: dict[str, str] = {
    ...
}
```

**Step 5: Verify behavior unchanged**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python promote_claims.py --dry-run`
Expected: Same output as baseline

**Step 6: Commit**

```bash
git add .claude/skills/verify/scripts/promote_claims.py
git commit -m "refactor(verify): use common module in promote_claims.py"
```

---

## Task 5: Update check_version.py to Use Common Module

**Files:**
- Modify: `.claude/skills/verify/scripts/check_version.py:122-141` (remove duplicate version detection)

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python check_version.py`
Expected: Version check output (record for comparison)

**Step 2: Update imports**

After existing imports, add:
```python
from _common import get_claude_code_version
```

**Step 3: Remove duplicate get_claude_code_version**

Delete lines ~122-141 (the function definition)

**Step 4: Verify behavior unchanged**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python check_version.py`
Expected: Same output as baseline

**Step 5: Commit**

```bash
git add .claude/skills/verify/scripts/check_version.py
git commit -m "refactor(verify): use common module in check_version.py"
```

---

## Task 6: Update verify-health-check.py Hook to Use Common Module

**Files:**
- Modify: `.claude/skills/verify/hooks/verify-health-check.py:59-70` (remove duplicate version detection)
- Modify: `.claude/skills/verify/hooks/verify-health-check.py:106-120` (remove duplicate date parsing)

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify && python hooks/verify-health-check.py`
Expected: Output (may be empty if cache is healthy) - record for comparison

**Step 2: Update imports**

The hook needs to import from the scripts directory. Add after existing imports:
```python
import sys
# Add scripts directory to path for _common import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from _common import parse_verified_date, get_claude_code_version
```

**Step 3: Remove duplicate parse_verified_date**

Delete lines ~106-120 (the function definition)

**Step 4: Remove duplicate get_claude_code_version**

Delete lines ~59-70 (the function definition)

**Step 5: Verify behavior unchanged**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify && python hooks/verify-health-check.py`
Expected: Same output as baseline

**Step 6: Commit**

```bash
git add .claude/skills/verify/hooks/verify-health-check.py
git commit -m "refactor(verify): use common module in health check hook"
```

---

## Task 7: Update validate_skill.py Expected Scripts List

**Files:**
- Modify: `.claude/skills/verify/scripts/validate_skill.py:178-186`

**Step 1: Verify current behavior (baseline)**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python validate_skill.py`
Expected: Validation output (record for comparison)

**Step 2: Update expected_scripts list**

Change lines 178-186 to include `verify.py`:
```python
    expected_scripts = [
        "verify.py",          # ADD THIS
        "match_claim.py",
        "promote_claims.py",
        "extract_claims.py",
        "refresh_claims.py",
        "check_version.py",
        "batch_verify.py",
        "validate_skill.py",
        "_common.py",         # ADD THIS
    ]
```

**Step 3: Run validation**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python validate_skill.py`
Expected: Validation passes with fewer warnings

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/validate_skill.py
git commit -m "fix(verify): add verify.py and _common.py to expected scripts"
```

---

## Task 8: Run Full Validation Suite

**Files:**
- None (verification only)

**Step 1: Run validate_skill.py**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python validate_skill.py`
Expected: No errors, possibly some warnings

**Step 2: Test unified CLI**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python verify.py --health`
Expected: Cache health report without errors

**Step 3: Test match_claim**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python match_claim.py "hooks use exit code 2 to block" --top 3`
Expected: Top 3 matches displayed

**Step 4: Test refresh_claims**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python refresh_claims.py --version-aware --summary`
Expected: Cache health summary with version info

**Step 5: Test promote_claims dry-run**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python promote_claims.py --dry-run`
Expected: Dry run output (no actual changes)

**Step 6: Test check_version**

Run: `cd /Users/jp/Projects/active/claude-code-tool-dev/.claude/skills/verify/scripts && python check_version.py`
Expected: Version comparison output

**Step 7: Commit summary**

```bash
git log --oneline -7
```
Expected: 7 commits from this plan

---

## Summary

After completing this plan:

| Metric | Before | After |
|--------|--------|-------|
| `parse_verified_date` copies | 3 | 1 |
| `get_claude_code_version` copies | 4 | 1 |
| `SECTION_ALIASES` copies | 2 | 1 |
| `DEFAULT_MAX_AGE_DAYS` copies | 2 | 1 |
| Total lines removed | ~150 | - |
| New shared module | 0 | 1 (`_common.py`) |

**Benefits:**
- Single source of truth for shared utilities
- Consistent behavior across all scripts
- Easier maintenance (update one place)
- Reduced risk of drift between implementations
