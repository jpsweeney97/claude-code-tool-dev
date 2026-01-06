# Verify Skill Audit Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical and high-severity issues identified in the verify skill scripts audit, improving data integrity, consistency, and maintainability.

**Architecture:** Consolidate shared utilities into `_common.py`, fix section insertion logic in `promote_claims.py`, add atomic write patterns, and resolve import inconsistencies across all scripts.

**Tech Stack:** Python 3.12, standard library only (pathlib, tempfile, dataclasses)

---

## Task 1: Consolidate Version Class into _common.py

**Files:**
- Modify: `.claude/skills/verify/scripts/_common.py`
- Modify: `.claude/skills/verify/scripts/check_version.py`
- Modify: `.claude/skills/verify/scripts/refresh_claims.py`
- Modify: `.claude/skills/verify/hooks/verify-health-check.py`

**Step 1: Add Version class to _common.py**

Add after the existing imports in `_common.py`:

```python
class Version(NamedTuple):
    """Parsed semantic version."""
    major: int
    minor: int
    patch: int
    prerelease: str | None = None

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += f"-{self.prerelease}"
        return base

    @classmethod
    def parse(cls, version_str: str) -> "Version | None":
        """Parse a version string like '1.2.3' or '1.2.3-beta.1'."""
        match = re.match(
            r"v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?",
            version_str.strip()
        )
        if not match:
            return None
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4),
        )
```

**Step 2: Update check_version.py imports**

Replace the local Version class with import:

```python
from _common import get_claude_code_version, Version
```

Remove lines 36-64 (the local Version class definition).

**Step 3: Update refresh_claims.py imports**

Replace the local Version class with import:

```python
from _common import parse_verified_date, get_claude_code_version, DEFAULT_MAX_AGE_DAYS, Version
```

Remove lines 44-56 (the local Version class definition).

**Step 4: Update verify-health-check.py imports**

Replace lines 33-34:

```python
from _common import get_claude_code_version, parse_verified_date, Version
```

Remove lines 50-58 (the local Version class definition).

**Step 5: Run tests to verify no import errors**

Run:
```bash
python .claude/skills/verify/scripts/check_version.py --help
python .claude/skills/verify/scripts/refresh_claims.py --help
python .claude/skills/verify/hooks/verify-health-check.py
```

Expected: Help text displayed, no ImportError

**Step 6: Commit**

```bash
git add .claude/skills/verify/scripts/_common.py .claude/skills/verify/scripts/check_version.py .claude/skills/verify/scripts/refresh_claims.py .claude/skills/verify/hooks/verify-health-check.py
git commit -m "refactor(verify): consolidate Version class into _common.py"
```

---

## Task 2: Add Atomic Write Helper to _common.py

**Files:**
- Modify: `.claude/skills/verify/scripts/_common.py`

**Step 1: Add atomic_write function to _common.py**

Add at end of file:

```python
def atomic_write(path: Path, content: str) -> None:
    """
    Write content to file atomically using temp file + rename.

    Prevents data corruption if process is interrupted during write.

    Args:
        path: Target file path
        content: Content to write
    """
    import tempfile

    # Create temp file in same directory (ensures same filesystem for rename)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        # Atomic rename
        Path(temp_path).rename(path)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
```

**Step 2: Add os import at top of file**

Add to imports section:

```python
import os
```

**Step 3: Verify syntax**

Run:
```bash
python -c "from pathlib import Path; import sys; sys.path.insert(0, '.claude/skills/verify/scripts'); from _common import atomic_write; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/_common.py
git commit -m "feat(verify): add atomic_write helper for safe file updates"
```

---

## Task 3: Fix batch_verify.py to Use Atomic Writes

**Files:**
- Modify: `.claude/skills/verify/scripts/batch_verify.py`

**Step 1: Add import for atomic_write**

Add after existing imports (around line 30):

```python
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _common import atomic_write
```

**Step 2: Replace path.write_text with atomic_write**

Replace line 168:

```python
        path.write_text("\n".join(lines) + "\n")
```

With:

```python
        atomic_write(path, "\n".join(lines) + "\n")
```

**Step 3: Test the update operation**

Run:
```bash
python .claude/skills/verify/scripts/batch_verify.py --help
```

Expected: Help text displayed

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/batch_verify.py
git commit -m "fix(verify): use atomic writes in batch_verify.py"
```

---

## Task 4: Fix refresh_claims.py to Use Atomic Writes

**Files:**
- Modify: `.claude/skills/verify/scripts/refresh_claims.py`

**Step 1: Add import for atomic_write**

Update the import from _common (line 37):

```python
from _common import parse_verified_date, get_claude_code_version, DEFAULT_MAX_AGE_DAYS, Version, atomic_write
```

**Step 2: Replace path.write_text calls with atomic_write**

Replace line 253:

```python
        path.write_text("\n".join(lines) + "\n")
```

With:

```python
        atomic_write(path, "\n".join(lines) + "\n")
```

Replace line 297:

```python
    path.write_text("\n".join(lines) + "\n")
```

With:

```python
    atomic_write(path, "\n".join(lines) + "\n")
```

**Step 3: Test**

Run:
```bash
python .claude/skills/verify/scripts/refresh_claims.py --help
```

Expected: Help text displayed

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/refresh_claims.py
git commit -m "fix(verify): use atomic writes in refresh_claims.py"
```

---

## Task 5: Fix promote_claims.py Section Insertion Bug

**Files:**
- Modify: `.claude/skills/verify/scripts/promote_claims.py`

**Step 1: Refactor section creation to recalculate line positions**

Replace lines 376-404 with:

```python
    # Create new sections before Maintenance (at end of file if no Maintenance)
    if sections_to_create:
        # Sort sections alphabetically for consistent ordering
        for section in sorted(sections_to_create, reverse=True):
            section_block = create_new_section(section)
            section_lines = section_block.splitlines()

            # Add claims to the new section
            claims_for_section = by_section[section]
            for claim in claims_for_section:
                section_lines.append(format_known_claim_row(claim, version))

            # Recalculate maintenance line from current lines state
            maintenance_line = None
            for i, line in enumerate(lines):
                if line.startswith("## Maintenance"):
                    maintenance_line = i
                    break

            if maintenance_line is not None:
                # Find the --- separator before Maintenance
                insert_idx = maintenance_line
                for i in range(maintenance_line - 1, -1, -1):
                    if lines[i].strip() == "---":
                        insert_idx = i
                        break
                lines = lines[:insert_idx] + section_lines + [""] + lines[insert_idx:]
            else:
                # Append at end
                lines.extend([""] + section_lines)
```

**Step 2: Add import for atomic_write and use it**

Update the import from _common (line 29):

```python
from _common import get_claude_code_version, SECTION_ALIASES, atomic_write
```

Replace line 414:

```python
        known_path.write_text("\n".join(lines) + "\n")
```

With:

```python
        atomic_write(known_path, "\n".join(lines) + "\n")
```

Replace line 424:

```python
        pending_path.write_text(pending_header)
```

With:

```python
        atomic_write(pending_path, pending_header)
```

**Step 3: Test dry-run mode**

Run:
```bash
python .claude/skills/verify/scripts/promote_claims.py --dry-run
```

Expected: Shows "No pending claims to promote" or lists claims without errors

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/promote_claims.py
git commit -m "fix(verify): fix section insertion bug and use atomic writes"
```

---

## Task 6: Fix Duplicate Detection Case Sensitivity

**Files:**
- Modify: `.claude/skills/verify/scripts/promote_claims.py`

**Step 1: Normalize section name before duplicate lookup**

Replace lines 324-328:

```python
        # Check for duplicates (using normalized section)
        claim_normalized = claim.claim.strip("`").lower()
        existing = known_structure.get(claim.section, [])
        if claim_normalized in existing:
            result.skipped_duplicates.append(claim)
            continue
```

With:

```python
        # Check for duplicates (using normalized section - case insensitive lookup)
        claim_normalized = claim.claim.strip("`").lower()
        # Find section case-insensitively
        section_lower = claim.section.lower()
        existing: list[str] = []
        for known_section, known_claims in known_structure.items():
            if known_section.lower() == section_lower:
                existing = known_claims
                break
        if claim_normalized in existing:
            result.skipped_duplicates.append(claim)
            continue
```

**Step 2: Test**

Run:
```bash
python .claude/skills/verify/scripts/promote_claims.py --dry-run
```

Expected: No errors

**Step 3: Commit**

```bash
git add .claude/skills/verify/scripts/promote_claims.py
git commit -m "fix(verify): case-insensitive section lookup for duplicate detection"
```

---

## Task 7: Fix verify.py Import Source for DEFAULT_MAX_AGE_DAYS

**Files:**
- Modify: `.claude/skills/verify/scripts/verify.py`

**Step 1: Import DEFAULT_MAX_AGE_DAYS from _common instead of match_claim**

Replace lines 49-60:

```python
# Import from sibling scripts
from match_claim import (
    parse_known_claims,
    find_best_match,
    find_top_matches,
    discover_sections,
    normalize_section,
    list_sections,
    THRESHOLD_HIGH,
    THRESHOLD_MEDIUM,
    THRESHOLD_LOW,
    DEFAULT_MAX_AGE_DAYS,
)
```

With:

```python
# Import from common utilities
from _common import DEFAULT_MAX_AGE_DAYS

# Import from sibling scripts
from match_claim import (
    parse_known_claims,
    find_best_match,
    find_top_matches,
    discover_sections,
    normalize_section,
    list_sections,
    THRESHOLD_HIGH,
    THRESHOLD_MEDIUM,
    THRESHOLD_LOW,
)
```

**Step 2: Test**

Run:
```bash
python .claude/skills/verify/scripts/verify.py --help
```

Expected: Help text displayed

**Step 3: Commit**

```bash
git add .claude/skills/verify/scripts/verify.py
git commit -m "refactor(verify): import DEFAULT_MAX_AGE_DAYS from canonical source"
```

---

## Task 8: Update validate_skill.py Expected Scripts List

**Files:**
- Modify: `.claude/skills/verify/scripts/validate_skill.py`

**Step 1: Update expected_scripts to be complete**

The list at line 178-188 is already complete based on the audit. Verify it matches actual scripts:

```python
    expected_scripts = [
        "verify.py",
        "match_claim.py",
        "promote_claims.py",
        "extract_claims.py",
        "refresh_claims.py",
        "check_version.py",
        "batch_verify.py",
        "validate_skill.py",
        "_common.py",
    ]
```

**Step 2: Run validation**

Run:
```bash
python .claude/skills/verify/scripts/validate_skill.py
```

Expected: Validation passes or shows only info/warning level issues

**Step 3: Commit (if changes made)**

```bash
git add .claude/skills/verify/scripts/validate_skill.py
git commit -m "chore(verify): ensure validate_skill.py script list is current"
```

---

## Task 9: Add Logging to get_claude_code_version

**Files:**
- Modify: `.claude/skills/verify/scripts/_common.py`

**Step 1: Add optional verbose parameter**

Replace the `get_claude_code_version` function (lines 72-92):

```python
def get_claude_code_version(verbose: bool = False) -> str | None:
    """
    Get current Claude Code version by running 'claude --version'.

    Args:
        verbose: If True, print error details to stderr

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
            if verbose:
                print(f"Warning: Could not parse version from: {result.stdout[:100]}", file=sys.stderr)
        elif verbose:
            print(f"Warning: claude --version returned {result.returncode}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        if verbose:
            print("Warning: claude --version timed out", file=sys.stderr)
    except FileNotFoundError:
        if verbose:
            print("Warning: claude executable not found", file=sys.stderr)
    except OSError as e:
        if verbose:
            print(f"Warning: OSError running claude --version: {e}", file=sys.stderr)
    return None
```

**Step 2: Add sys import if not present**

Verify `import sys` is in the imports section.

**Step 3: Test**

Run:
```bash
python -c "import sys; sys.path.insert(0, '.claude/skills/verify/scripts'); from _common import get_claude_code_version; print(get_claude_code_version(verbose=True))"
```

Expected: Version number printed, or warning message to stderr

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/_common.py
git commit -m "feat(verify): add verbose mode to get_claude_code_version for debugging"
```

---

## Task 10: Update SKILL.md Version and Changelog

**Files:**
- Modify: `.claude/skills/verify/SKILL.md`

**Step 1: Update version in frontmatter**

Change line 6:

```yaml
  version: "2.5.0"
```

To:

```yaml
  version: "2.5.1"
```

**Step 2: Add changelog entry after line 319**

Insert after the v2.5.0 changelog entry:

```markdown
### v2.5.1
- **Bug fix**: Fixed section insertion offset bug in `promote_claims.py` that could corrupt file structure
- **Bug fix**: Fixed case-sensitive section lookup causing duplicate detection failures
- **Safety**: Added atomic write pattern to all file-modifying scripts (prevents data corruption on interrupted writes)
- **Refactor**: Consolidated `Version` class into `_common.py` (was duplicated in 3 files)
- **Refactor**: Canonical import source for `DEFAULT_MAX_AGE_DAYS` from `_common.py`
- **Improvement**: Added verbose mode to `get_claude_code_version()` for debugging

```

**Step 3: Commit**

```bash
git add .claude/skills/verify/SKILL.md
git commit -m "docs(verify): update changelog for v2.5.1 audit fixes"
```

---

## Summary

| Task | Priority | Description |
|------|----------|-------------|
| 1 | High | Consolidate Version class into _common.py |
| 2 | Critical | Add atomic_write helper |
| 3 | Critical | Fix batch_verify.py atomic writes |
| 4 | Critical | Fix refresh_claims.py atomic writes |
| 5 | Critical | Fix promote_claims.py section insertion bug |
| 6 | High | Fix duplicate detection case sensitivity |
| 7 | Medium | Fix verify.py import source |
| 8 | Low | Verify validate_skill.py script list |
| 9 | Medium | Add logging to get_claude_code_version |
| 10 | Low | Update SKILL.md changelog |

**Total estimated tasks:** 10 tasks, ~40-50 steps
**Commit frequency:** One commit per task
