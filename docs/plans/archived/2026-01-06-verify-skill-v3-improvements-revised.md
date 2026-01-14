# Verify Skill v3.0.0 Improvement Plan (Revised)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan phase-by-phase.

**Goal:** Evolve verify skill from v2.6.1 to v3.0.0 with improved reliability, usability, and maintainability.

**Current State:** 76 verified claims, 10 scripts, timelessness score 7/10

**Target State:** URL validation, backup/restore, interactive batch, test coverage, timelessness score 8/10

**Tech Stack:** Python 3.12, standard library only (no external dependencies)

**Revision Notes:** This plan addresses gaps from audit:
- Complete integration code (not just snippets)
- Complete test files (not placeholder references)
- Documentation diffs included
- Priority reordering: tests elevated to High

---

## Summary of Improvements

| Priority | Improvement | Effort | Phase |
|----------|-------------|--------|-------|
| Critical | Source URL Validation | Medium | 1 |
| High | Cache Backup and Restore | Low | 1 |
| High | Script Test Coverage | Medium | 1 |
| Medium | Interactive Batch Verification | Medium | 2 |
| Low | Quick-Add from Conversation | Low | 2 |

**Priority Changes from v1:**
- Test Coverage: Medium → **High** (tests prevent data-corrupting bugs)
- Tests moved to Phase 1 (foundation work)

---

## Phase 1: Foundation

### Task 1.1: Create Source URL Validation Script

**Priority:** Critical
**Risk Mitigated:** Stale documentation links silently corrupt cache trust

**Files:**
- Create: `.claude/skills/verify/scripts/validate_sources.py`

#### Step 1: Write the script

```python
#!/usr/bin/env python3
"""
Validate source URLs in known-claims.md.

Checks that documentation URLs are accessible and reports broken links
that may indicate stale or invalid claims.

Exit codes:
    0 - All URLs valid
    1 - Input error
    2 - One or more URLs invalid
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple


class URLResult(NamedTuple):
    """Result of URL validation."""
    url: str
    section: str
    status: int | None  # HTTP status code or None if unreachable
    error: str | None   # Error message if failed


@dataclass
class ValidationResult:
    """Overall validation result."""
    valid: list[URLResult] = field(default_factory=list)
    invalid: list[URLResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def extract_source_urls(content: str) -> dict[str, str]:
    """Extract section -> source URL mapping from known-claims.md."""
    urls: dict[str, str] = {}
    current_section = None

    for line in content.splitlines():
        # Match section headers like "## Skills"
        section_match = re.match(r"^## (\w+)", line)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Match source lines like "**Source:** https://..."
        source_match = re.match(r"\*\*Source:\*\*\s+(https?://\S+)", line)
        if source_match and current_section:
            urls[current_section] = source_match.group(1)

    return urls


def validate_url(url: str, section: str, timeout: int = 10) -> URLResult:
    """Check if URL is accessible using HEAD request."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "verify-skill-validator/1.0")

        with urllib.request.urlopen(req, timeout=timeout) as response:
            return URLResult(url=url, section=section, status=response.status, error=None)

    except urllib.error.HTTPError as e:
        return URLResult(url=url, section=section, status=e.code, error=str(e.reason))
    except urllib.error.URLError as e:
        return URLResult(url=url, section=section, status=None, error=str(e.reason))
    except TimeoutError:
        return URLResult(url=url, section=section, status=None, error="Timeout")
    except Exception as e:
        return URLResult(url=url, section=section, status=None, error=str(e))


def validate_sources(
    known_path: Path,
    timeout: int = 10,
    rate_limit: float = 1.0,
    section_filter: str | None = None,
) -> ValidationResult:
    """Validate all source URLs in known-claims.md."""
    result = ValidationResult()

    if not known_path.exists():
        return result

    content = known_path.read_text(encoding="utf-8")
    urls = extract_source_urls(content)

    # Filter to specific section if requested
    if section_filter:
        section_lower = section_filter.lower()
        urls = {k: v for k, v in urls.items() if k.lower() == section_lower}

    for i, (section, url) in enumerate(urls.items()):
        # Rate limiting between requests
        if i > 0 and rate_limit > 0:
            time.sleep(rate_limit)

        # Skip placeholder URLs
        if "(pending" in url.lower():
            result.skipped.append(f"{section}: {url}")
            continue

        url_result = validate_url(url, section, timeout)

        if url_result.error is None and url_result.status and 200 <= url_result.status < 400:
            result.valid.append(url_result)
        else:
            result.invalid.append(url_result)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source URLs in known-claims.md")
    parser.add_argument(
        "--known-claims",
        type=Path,
        default=Path(__file__).parent.parent / "references" / "known-claims.md",
        help="Path to known-claims.md",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout in seconds per URL (default: 10)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between requests to avoid rate limiting (default: 1.0)",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        help="Only validate URLs for this section",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    result = validate_sources(
        args.known_claims,
        timeout=args.timeout,
        rate_limit=args.rate_limit,
        section_filter=args.section,
    )

    if args.json:
        import json
        output = {
            "valid": [{"url": r.url, "section": r.section, "status": r.status} for r in result.valid],
            "invalid": [{"url": r.url, "section": r.section, "status": r.status, "error": r.error} for r in result.invalid],
            "skipped": result.skipped,
        }
        print(json.dumps(output, indent=2))
    else:
        print("Source URL Validation Report\n")

        if result.valid:
            print(f"Valid ({len(result.valid)}):")
            for r in result.valid:
                print(f"  ✓ {r.section}: {r.url} [{r.status}]")

        if result.invalid:
            print(f"\nInvalid ({len(result.invalid)}):")
            for r in result.invalid:
                status = r.status or "unreachable"
                print(f"  ✗ {r.section}: {r.url} [{status}] - {r.error}")

        if result.skipped:
            print(f"\nSkipped ({len(result.skipped)}):")
            for s in result.skipped:
                print(f"  - {s}")

        print(f"\nSummary: {len(result.valid)} valid, {len(result.invalid)} invalid, {len(result.skipped)} skipped")

    return 2 if result.invalid else 0


if __name__ == "__main__":
    sys.exit(main())
```

#### Step 2: Test the script

```bash
python .claude/skills/verify/scripts/validate_sources.py
python .claude/skills/verify/scripts/validate_sources.py --section Skills
python .claude/skills/verify/scripts/validate_sources.py --json
```

Expected: Report showing valid/invalid URLs with rate limiting

#### Step 3: Integrate with verify.py

**Location:** `.claude/skills/verify/scripts/verify.py`

**Add import after line 73:**

```python
from validate_sources import validate_sources, ValidationResult
```

**Add argument after line ~180 (in argparse setup, after --health group):**

Find the section with `parser.add_argument("--health"` and add after it:

```python
    parser.add_argument(
        "--validate-urls",
        action="store_true",
        help="Validate source documentation URLs",
    )
```

**Add handler function after `cmd_health` function (around line 234):**

```python
def cmd_validate_urls(args: argparse.Namespace) -> int:
    """Validate source documentation URLs."""
    if not KNOWN_CLAIMS_PATH.exists():
        print(f"Error: Cache not found: {KNOWN_CLAIMS_PATH}", file=sys.stderr)
        return 1

    print("Validating source URLs (this may take a moment)...")
    print()

    result = validate_sources(
        KNOWN_CLAIMS_PATH,
        timeout=10,
        rate_limit=1.0,
        section_filter=args.section,
    )

    # Display results
    section_note = f" for {args.section}" if args.section else ""
    print(f"Source URL Validation{section_note}")
    print("=" * 40)

    if result.valid:
        print(f"\n✓ Valid ({len(result.valid)}):")
        for r in result.valid:
            print(f"    {r.section}: {r.url}")

    if result.invalid:
        print(f"\n✗ Invalid ({len(result.invalid)}):")
        for r in result.invalid:
            status = r.status or "unreachable"
            print(f"    {r.section}: {r.url}")
            print(f"      └─ {status}: {r.error}")

    if result.skipped:
        print(f"\n⊘ Skipped ({len(result.skipped)}):")
        for s in result.skipped:
            print(f"    {s}")

    print()
    print(f"Summary: {len(result.valid)} valid, {len(result.invalid)} invalid, {len(result.skipped)} skipped")

    if result.invalid:
        print("\n⚠️  Action: Review claims in sections with broken URLs")
        return 2

    return 0
```

**Add dispatch in main() around line 450 (in the if/elif chain for args):**

Find `if args.health:` and add before it:

```python
    if args.validate_urls:
        return cmd_validate_urls(args)
```

#### Step 4: Commit

```bash
git add .claude/skills/verify/scripts/validate_sources.py
git add .claude/skills/verify/scripts/verify.py
git commit -m "feat(verify): add source URL validation script

- New validate_sources.py validates documentation URLs
- Detects broken links that may indicate stale claims
- Rate limiting prevents server blocking
- Integrated via verify.py --validate-urls"
```

---

### Task 1.2: Create Cache Backup and Restore Script

**Priority:** High
**Risk Mitigated:** No recovery from cache corruption

**Files:**
- Create: `.claude/skills/verify/scripts/backup_cache.py`
- Create: `.claude/skills/verify/references/.backups/.gitkeep`

#### Step 1: Write the backup script

```python
#!/usr/bin/env python3
"""
Backup and restore known-claims.md cache.

Maintains rolling backups (last 5) to protect against data loss.

Exit codes:
    0 - Success
    1 - Input error
    10 - No backups to restore
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


BACKUP_DIR = Path(__file__).parent.parent / "references" / ".backups"
KNOWN_CLAIMS = Path(__file__).parent.parent / "references" / "known-claims.md"
MAX_BACKUPS = 5


def create_backup(source: Path = KNOWN_CLAIMS, backup_dir: Path = BACKUP_DIR) -> Path | None:
    """Create timestamped backup of known-claims.md."""
    if not source.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"known-claims_{timestamp}.md"

    shutil.copy2(source, backup_path)

    # Cleanup old backups (keep MAX_BACKUPS)
    backups = sorted(backup_dir.glob("known-claims_*.md"), reverse=True)
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink()

    return backup_path


def list_backups(backup_dir: Path = BACKUP_DIR) -> list[Path]:
    """List available backups, newest first."""
    if not backup_dir.exists():
        return []
    return sorted(backup_dir.glob("known-claims_*.md"), reverse=True)


def restore_backup(backup_path: Path, target: Path = KNOWN_CLAIMS) -> bool:
    """Restore from a backup file."""
    if not backup_path.exists():
        return False

    # Create backup of current before restoring
    if target.exists():
        create_backup(target)

    shutil.copy2(backup_path, target)
    return True


def diff_backup(backup_path: Path, current: Path = KNOWN_CLAIMS) -> tuple[int, int, int]:
    """Compare backup with current file. Returns (added, removed, unchanged) line counts."""
    if not backup_path.exists() or not current.exists():
        return (0, 0, 0)

    backup_lines = set(backup_path.read_text().splitlines())
    current_lines = set(current.read_text().splitlines())

    added = len(current_lines - backup_lines)
    removed = len(backup_lines - current_lines)
    unchanged = len(backup_lines & current_lines)

    return (added, removed, unchanged)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup and restore known-claims.md")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument("--source", type=Path, default=KNOWN_CLAIMS)

    # list command
    list_parser = subparsers.add_parser("list", help="List backups")
    list_parser.add_argument("--diff", action="store_true", help="Show diff stats")

    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup", nargs="?", help="Backup file to restore (latest if omitted)")
    restore_parser.add_argument("--dry-run", action="store_true", help="Preview without restoring")

    args = parser.parse_args()

    if args.command == "backup":
        backup_path = create_backup(args.source)
        if backup_path:
            print(f"Created backup: {backup_path.name}")
            return 0
        else:
            print("Error: Source file not found", file=sys.stderr)
            return 1

    elif args.command == "list":
        backups = list_backups()
        if backups:
            print("Available backups:")
            for i, b in enumerate(backups):
                timestamp = b.stem.replace("known-claims_", "")
                size = b.stat().st_size
                marker = " (latest)" if i == 0 else ""

                if args.diff:
                    added, removed, unchanged = diff_backup(b)
                    diff_info = f" | +{added} -{removed}"
                else:
                    diff_info = ""

                print(f"  {i+1}. {timestamp} ({size:,} bytes){marker}{diff_info}")
        else:
            print("No backups found")
        return 0

    elif args.command == "restore":
        backups = list_backups()

        if not backups:
            print("No backups available", file=sys.stderr)
            return 10

        if args.backup:
            # Find matching backup
            backup_path = None
            for b in backups:
                if args.backup in str(b):
                    backup_path = b
                    break
            if not backup_path:
                print(f"Backup not found: {args.backup}", file=sys.stderr)
                return 1
        else:
            backup_path = backups[0]  # Latest

        if args.dry_run:
            added, removed, unchanged = diff_backup(backup_path)
            print(f"[DRY RUN] Would restore from: {backup_path.name}")
            print(f"  Changes: +{added} -{removed} ~{unchanged}")
            return 0

        if restore_backup(backup_path):
            print(f"Restored from: {backup_path.name}")
            return 0
        else:
            print("Restore failed", file=sys.stderr)
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### Step 2: Create .gitkeep

```bash
mkdir -p .claude/skills/verify/references/.backups
touch .claude/skills/verify/references/.backups/.gitkeep
```

#### Step 3: Add .gitignore for backup files

Create `.claude/skills/verify/references/.backups/.gitignore`:

```
# Ignore backup files (they're local state)
known-claims_*.md
!.gitkeep
!.gitignore
```

#### Step 4: Integrate with promote_claims.py

**Location:** `.claude/skills/verify/scripts/promote_claims.py`

**Add import after line 29:**

```python
from backup_cache import create_backup
```

**Modify promote_claims function** (find the function around line 150). Add backup call at the start:

Find the line that starts with `def promote_claims(` and add inside the function, before any file writes:

```python
    # Create backup before modifying known-claims.md
    if not dry_run:
        backup_path = create_backup(known_path)
        if backup_path:
            # Record in result for reporting
            pass  # Could add backup_path to result if needed
```

#### Step 5: Integrate with verify.py

**Location:** `.claude/skills/verify/scripts/verify.py`

**Add import after validate_sources import:**

```python
from backup_cache import create_backup, list_backups, restore_backup
```

**Add arguments after --validate-urls:**

```python
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup of known-claims cache",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const="latest",
        metavar="BACKUP",
        help="Restore cache from backup (latest if no argument)",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List available backups",
    )
```

**Add handlers after cmd_validate_urls:**

```python
def cmd_backup(args: argparse.Namespace) -> int:
    """Create backup of known-claims cache."""
    backup_path = create_backup(KNOWN_CLAIMS_PATH)
    if backup_path:
        print(f"Created backup: {backup_path.name}")
        return 0
    else:
        print("Error: No cache to backup", file=sys.stderr)
        return 1


def cmd_list_backups(args: argparse.Namespace) -> int:
    """List available backups."""
    backups = list_backups()
    if not backups:
        print("No backups found")
        return 0

    print("Available backups:")
    for i, b in enumerate(backups):
        timestamp = b.stem.replace("known-claims_", "")
        size = b.stat().st_size
        marker = " (latest)" if i == 0 else ""
        print(f"  {i+1}. {timestamp} ({size:,} bytes){marker}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    """Restore cache from backup."""
    backups = list_backups()

    if not backups:
        print("No backups available", file=sys.stderr)
        return 10

    if args.restore == "latest":
        backup_path = backups[0]
    else:
        # Find matching backup
        backup_path = None
        for b in backups:
            if args.restore in str(b):
                backup_path = b
                break
        if not backup_path:
            print(f"Backup not found: {args.restore}", file=sys.stderr)
            return 1

    if args.dry_run:
        print(f"[DRY RUN] Would restore from: {backup_path.name}")
        return 0

    if restore_backup(backup_path, KNOWN_CLAIMS_PATH):
        print(f"Restored from: {backup_path.name}")
        return 0
    else:
        print("Restore failed", file=sys.stderr)
        return 1
```

**Add dispatch in main():**

```python
    if args.backup:
        return cmd_backup(args)

    if args.list_backups:
        return cmd_list_backups(args)

    if args.restore:
        return cmd_restore(args)
```

#### Step 6: Commit

```bash
git add .claude/skills/verify/scripts/backup_cache.py
git add .claude/skills/verify/scripts/promote_claims.py
git add .claude/skills/verify/scripts/verify.py
git add .claude/skills/verify/references/.backups/
git commit -m "feat(verify): add cache backup and restore

- New backup_cache.py with backup/list/restore commands
- Rolling backups (keeps last 5)
- Auto-backup before promote operations
- Integrated via verify.py --backup/--restore/--list-backups"
```

---

### Task 1.3: Create Test Infrastructure

**Priority:** High (elevated from Medium)
**Risk Mitigated:** Bugs in scripts cause data corruption

**Files:**
- Create: `.claude/skills/verify/tests/__init__.py`
- Create: `.claude/skills/verify/tests/test_common.py`
- Create: `.claude/skills/verify/tests/test_match_claim.py`
- Create: `.claude/skills/verify/tests/test_validate_sources.py`
- Create: `.claude/skills/verify/tests/test_backup_cache.py`

#### Step 1: Create test directory

```bash
mkdir -p .claude/skills/verify/tests
touch .claude/skills/verify/tests/__init__.py
```

#### Step 2: Create test_common.py

```python
#!/usr/bin/env python3
"""Tests for _common.py utilities."""

import sys
import unittest
from datetime import date
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from _common import parse_verified_date, Version, DEFAULT_MAX_AGE_DAYS, SECTION_ALIASES


class TestParseVerifiedDate(unittest.TestCase):
    """Tests for parse_verified_date function."""

    def test_plain_date(self):
        result = parse_verified_date("2026-01-05")
        self.assertEqual(result, date(2026, 1, 5))

    def test_version_tagged_date(self):
        result = parse_verified_date("2026-01-05 (v2.0.76)")
        self.assertEqual(result, date(2026, 1, 5))

    def test_version_tagged_with_extra_spaces(self):
        result = parse_verified_date("2026-01-05  (v2.0.76)")
        self.assertEqual(result, date(2026, 1, 5))

    def test_none_input(self):
        result = parse_verified_date(None)
        self.assertIsNone(result)

    def test_invalid_date(self):
        result = parse_verified_date("not-a-date")
        self.assertIsNone(result)

    def test_empty_string(self):
        result = parse_verified_date("")
        self.assertIsNone(result)

    def test_partial_date(self):
        result = parse_verified_date("2026-01")
        self.assertIsNone(result)


class TestVersion(unittest.TestCase):
    """Tests for Version class."""

    def test_parse_simple(self):
        v = Version.parse("2.0.76")
        self.assertIsNotNone(v)
        self.assertEqual(v.major, 2)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 76)
        self.assertIsNone(v.prerelease)

    def test_parse_with_v_prefix(self):
        v = Version.parse("v2.0.76")
        self.assertIsNotNone(v)
        self.assertEqual(v.major, 2)

    def test_parse_with_prerelease(self):
        v = Version.parse("3.0.0-beta.1")
        self.assertIsNotNone(v)
        self.assertEqual(v.prerelease, "beta.1")

    def test_parse_invalid(self):
        v = Version.parse("not-a-version")
        self.assertIsNone(v)

    def test_str(self):
        v = Version(2, 0, 76)
        self.assertEqual(str(v), "2.0.76")

    def test_str_with_prerelease(self):
        v = Version(3, 0, 0, "beta.1")
        self.assertEqual(str(v), "3.0.0-beta.1")

    def test_comparison_major(self):
        v1 = Version(1, 0, 0)
        v2 = Version(2, 0, 0)
        self.assertLess(v1, v2)

    def test_comparison_minor(self):
        v1 = Version(2, 0, 0)
        v2 = Version(2, 1, 0)
        self.assertLess(v1, v2)

    def test_comparison_patch(self):
        v1 = Version(2, 0, 0)
        v2 = Version(2, 0, 1)
        self.assertLess(v1, v2)


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_default_max_age_days(self):
        self.assertEqual(DEFAULT_MAX_AGE_DAYS, 90)

    def test_section_aliases_exist(self):
        self.assertIn("hook", SECTION_ALIASES)
        self.assertIn("skill", SECTION_ALIASES)
        self.assertEqual(SECTION_ALIASES["hook"], "Hooks")


if __name__ == "__main__":
    unittest.main()
```

#### Step 3: Create test_match_claim.py

```python
#!/usr/bin/env python3
"""Tests for match_claim.py fuzzy matching."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from match_claim import (
    parse_known_claims,
    find_best_match,
    find_top_matches,
    normalize_section,
    similarity_score,
    MatchResult,
)


class TestSimilarityScore(unittest.TestCase):
    """Tests for similarity scoring."""

    def test_exact_match(self):
        score = similarity_score("exit code 0 means success", "exit code 0 means success")
        self.assertEqual(score, 1.0)

    def test_case_insensitive(self):
        score = similarity_score("Exit Code 0", "exit code 0")
        self.assertGreater(score, 0.9)

    def test_partial_match(self):
        score = similarity_score("exit code 0", "exit code 0 means success")
        self.assertGreater(score, 0.5)

    def test_no_match(self):
        score = similarity_score("completely different", "something else entirely")
        self.assertLess(score, 0.3)

    def test_word_overlap(self):
        score = similarity_score("hook exit code", "hooks use exit codes")
        self.assertGreater(score, 0.4)


class TestParseKnownClaims(unittest.TestCase):
    """Tests for parsing known-claims.md format."""

    def setUp(self):
        self.test_content = """# Known Claims

## Skills

**Source:** https://example.com/skills

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| name field is required | ✓ Verified | "must include name" | 2026-01-05 |
| license is optional | ✓ Verified | "not required" | 2026-01-05 |

## Hooks

**Source:** https://example.com/hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| exit code 0 means success | ✓ Verified | "Exit code 0: Success" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_parse_claims_count(self):
        claims = parse_known_claims(self.temp_path)
        self.assertEqual(len(claims), 3)

    def test_parse_claims_sections(self):
        claims = parse_known_claims(self.temp_path)
        sections = set(c.section for c in claims)
        self.assertEqual(sections, {"Skills", "Hooks"})

    def test_parse_claims_verdict(self):
        claims = parse_known_claims(self.temp_path)
        for c in claims:
            self.assertIn("✓", c.verdict)


class TestFindBestMatch(unittest.TestCase):
    """Tests for best match finding."""

    def setUp(self):
        self.test_content = """# Known Claims

## Hooks

| Claim | Verdict | Evidence | Verified |
|-------|---------|----------|----------|
| Exit code 0 means success | ✓ Verified | "Success" | 2026-01-05 |
| Exit code 1 is non-blocking error | ✓ Verified | "Non-blocking" | 2026-01-05 |
| Exit code 2 blocks execution | ✓ Verified | "Blocking" | 2026-01-05 |
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        self.temp_path = Path(self.temp_file.name)

    def tearDown(self):
        self.temp_path.unlink()

    def test_exact_match(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("Exit code 0 means success", claims)
        self.assertIsNotNone(result)
        self.assertGreater(result.score, 0.9)

    def test_partial_match(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("exit code 2", claims)
        self.assertIsNotNone(result)
        self.assertIn("2", result.claim.claim)

    def test_no_match(self):
        claims = parse_known_claims(self.temp_path)
        result = find_best_match("something completely unrelated xyz", claims)
        # Should return something but with low score
        if result:
            self.assertLess(result.score, 0.3)


class TestNormalizeSection(unittest.TestCase):
    """Tests for section normalization."""

    def test_exact_match(self):
        valid = ["Skills", "Hooks", "Commands"]
        result = normalize_section("Skills", valid)
        self.assertEqual(result, "Skills")

    def test_case_insensitive(self):
        valid = ["Skills", "Hooks", "Commands"]
        result = normalize_section("skills", valid)
        self.assertEqual(result, "Skills")

    def test_alias(self):
        valid = ["Skills", "Hooks", "Commands"]
        result = normalize_section("hook", valid)
        self.assertEqual(result, "Hooks")

    def test_invalid(self):
        valid = ["Skills", "Hooks", "Commands"]
        result = normalize_section("NotASection", valid)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
```

#### Step 4: Create test_validate_sources.py

```python
#!/usr/bin/env python3
"""Tests for validate_sources.py URL validation."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_sources import extract_source_urls, validate_url, URLResult


class TestExtractSourceUrls(unittest.TestCase):
    """Tests for URL extraction from known-claims.md."""

    def test_extract_single_url(self):
        content = """## Skills

**Source:** https://example.com/skills.md

| Claim | Verdict |
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls["Skills"], "https://example.com/skills.md")

    def test_extract_multiple_urls(self):
        content = """## Skills

**Source:** https://example.com/skills.md

## Hooks

**Source:** https://example.com/hooks.md
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls["Skills"], "https://example.com/skills.md")
        self.assertEqual(urls["Hooks"], "https://example.com/hooks.md")

    def test_no_source_line(self):
        content = """## Skills

| Claim | Verdict |
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 0)

    def test_source_without_section(self):
        content = """**Source:** https://example.com/orphan.md
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 0)


class TestValidateUrl(unittest.TestCase):
    """Tests for URL validation (mocked)."""

    @patch('validate_sources.urllib.request.urlopen')
    def test_valid_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = validate_url("https://example.com", "Test")
        self.assertEqual(result.status, 200)
        self.assertIsNone(result.error)

    def test_url_result_structure(self):
        result = URLResult(url="https://test.com", section="Test", status=200, error=None)
        self.assertEqual(result.url, "https://test.com")
        self.assertEqual(result.section, "Test")
        self.assertEqual(result.status, 200)


if __name__ == "__main__":
    unittest.main()
```

#### Step 5: Create test_backup_cache.py

```python
#!/usr/bin/env python3
"""Tests for backup_cache.py backup/restore functionality."""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from backup_cache import create_backup, list_backups, restore_backup, diff_backup, MAX_BACKUPS


class TestBackupCache(unittest.TestCase):
    """Tests for backup and restore operations."""

    def setUp(self):
        # Create temp directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "known-claims.md"
        self.backup_dir = self.temp_dir / ".backups"

        # Create test content
        self.test_file.write_text("# Known Claims\n\nTest content line 1\nTest content line 2\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_backup(self):
        backup_path = create_backup(self.test_file, self.backup_dir)
        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.startswith("known-claims_"))

    def test_backup_content_matches(self):
        backup_path = create_backup(self.test_file, self.backup_dir)
        original_content = self.test_file.read_text()
        backup_content = backup_path.read_text()
        self.assertEqual(original_content, backup_content)

    def test_list_backups_empty(self):
        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 0)

    def test_list_backups_after_create(self):
        create_backup(self.test_file, self.backup_dir)
        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 1)

    def test_list_backups_order(self):
        # Create multiple backups
        import time
        create_backup(self.test_file, self.backup_dir)
        time.sleep(0.01)  # Ensure different timestamps
        create_backup(self.test_file, self.backup_dir)

        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), 2)
        # Newest should be first
        self.assertGreater(backups[0].stat().st_mtime, backups[1].stat().st_mtime)

    def test_max_backups_enforced(self):
        import time
        # Create more than MAX_BACKUPS
        for _ in range(MAX_BACKUPS + 3):
            create_backup(self.test_file, self.backup_dir)
            time.sleep(0.01)

        backups = list_backups(self.backup_dir)
        self.assertEqual(len(backups), MAX_BACKUPS)

    def test_restore_backup(self):
        # Create backup
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Modify original
        self.test_file.write_text("Modified content")
        self.assertEqual(self.test_file.read_text(), "Modified content")

        # Restore
        success = restore_backup(backup_path, self.test_file)
        self.assertTrue(success)
        self.assertIn("Test content", self.test_file.read_text())

    def test_restore_creates_backup_of_current(self):
        # Create initial backup
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Modify original
        self.test_file.write_text("Modified content")

        # Restore - should create backup of modified version first
        initial_backup_count = len(list_backups(self.backup_dir))
        restore_backup(backup_path, self.test_file)
        final_backup_count = len(list_backups(self.backup_dir))

        self.assertEqual(final_backup_count, initial_backup_count + 1)

    def test_diff_backup(self):
        # Create backup
        backup_path = create_backup(self.test_file, self.backup_dir)

        # Modify original (add lines)
        current_content = self.test_file.read_text()
        self.test_file.write_text(current_content + "New line 1\nNew line 2\n")

        added, removed, unchanged = diff_backup(backup_path, self.test_file)
        self.assertEqual(added, 2)  # Two new lines
        self.assertEqual(removed, 0)


if __name__ == "__main__":
    unittest.main()
```

#### Step 6: Run tests

```bash
cd .claude/skills/verify
python -m pytest tests/ -v

# Or without pytest:
python -m unittest discover -s tests -v
```

#### Step 7: Commit

```bash
git add .claude/skills/verify/tests/
git commit -m "test(verify): add unit tests for core scripts

- test_common.py: date parsing, version class, constants
- test_match_claim.py: similarity scoring, parsing, matching
- test_validate_sources.py: URL extraction and validation
- test_backup_cache.py: backup/restore operations"
```

---

## Phase 2: Usability

### Task 2.1: Add Interactive Batch Verification

**Priority:** Medium
**Benefit:** Human oversight for batch operations

**Files:**
- Modify: `.claude/skills/verify/scripts/batch_verify.py`

#### Step 1: Add interactive confirmation function

**Location:** After the `BatchVerifyResult` class (around line 78), add:

```python
def confirm_claim(claim: PendingClaim, index: int, total: int) -> str:
    """
    Prompt user to confirm, skip, or edit a claim verdict.

    Returns: 'confirm', 'skip', 'edit', or 'quit'
    """
    print(f"\n[{index}/{total}] Claim: {claim.claim}")
    print(f"  Section: {claim.section}")
    print(f"  Current verdict: {claim.verdict}")
    print(f"  Evidence: {claim.evidence[:100]}{'...' if len(claim.evidence) > 100 else ''}")

    while True:
        response = input("\n[c]onfirm, [s]kip, [e]dit verdict, [q]uit? ").strip().lower()
        if response in ("c", "confirm", ""):
            return "confirm"
        elif response in ("s", "skip"):
            return "skip"
        elif response in ("e", "edit"):
            return "edit"
        elif response in ("q", "quit"):
            return "quit"
        else:
            print("Invalid response. Use c/s/e/q")


def edit_claim_verdict(claim: PendingClaim) -> PendingClaim:
    """Prompt user to edit claim verdict and evidence."""
    print("\nEdit claim:")
    print("  Current verdict:", claim.verdict)

    new_verdict = input("  New verdict (verified/false/partial/unverified) [keep]: ").strip()
    if new_verdict and new_verdict in ("verified", "false", "partial", "unverified", "✓", "✗", "~", "?"):
        # Normalize to symbols
        verdict_map = {
            "verified": "✓ Verified",
            "false": "✗ Contradicted",
            "partial": "~ Partial",
            "unverified": "? Unverified",
        }
        claim.verdict = verdict_map.get(new_verdict, new_verdict)

    print("  Current evidence:", claim.evidence[:50] + "...")
    new_evidence = input("  New evidence [keep]: ").strip()
    if new_evidence:
        claim.evidence = new_evidence

    return claim
```

#### Step 2: Add --interactive argument

**Location:** In the argument parsing section (around line 130), add after `--auto-promote`:

```python
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Confirm each claim interactively before including in batch",
    )
```

#### Step 3: Modify main function to use interactive mode

**Location:** In the main() function, find where claims are processed (around line 180). Add interactive handling:

Find the section that iterates over claims and modify to:

```python
    # Interactive mode: confirm each claim
    if args.interactive:
        confirmed_claims: list[PendingClaim] = []
        skipped_claims: list[PendingClaim] = []

        for i, claim in enumerate(claims, 1):
            action = confirm_claim(claim, i, len(claims))

            if action == "quit":
                print(f"\nQuitting. Processed {i-1}/{len(claims)} claims.")
                break
            elif action == "skip":
                skipped_claims.append(claim)
            elif action == "edit":
                edited = edit_claim_verdict(claim)
                confirmed_claims.append(edited)
            else:  # confirm
                confirmed_claims.append(claim)

        claims = confirmed_claims

        print(f"\nInteractive review complete:")
        print(f"  Confirmed: {len(confirmed_claims)}")
        print(f"  Skipped: {len(skipped_claims)}")

        if not claims:
            print("No claims to process after review.")
            return 10
```

#### Step 4: Commit

```bash
git add .claude/skills/verify/scripts/batch_verify.py
git commit -m "feat(verify): add interactive mode to batch verification

- --interactive flag enables per-claim confirmation
- Options: confirm, skip, edit verdict, quit
- Edit mode allows changing verdict and evidence inline"
```

---

### Task 2.2: Add Quick-Add Mode

**Priority:** Low
**Benefit:** Faster claim capture from conversations

**Files:**
- Modify: `.claude/skills/verify/scripts/verify.py`

#### Step 1: Add inference functions

**Location:** After imports, before PATH CONFIGURATION (around line 75), add:

```python
# =============================================================================
# QUICK-ADD INFERENCE
# =============================================================================

def infer_section(claim: str) -> str:
    """Infer section from claim keywords."""
    claim_lower = claim.lower()

    # Check for specific keywords
    section_keywords = {
        "Hooks": ["hook", "exit code", "pretooluse", "posttooluse", "timeout", "matcher"],
        "Skills": ["skill", "frontmatter", "allowed-tools", "skill.md"],
        "Commands": ["command", "$arguments", "slash", "argument-hint"],
        "MCP": ["mcp", ".mcp.json", "server", "mcpservers"],
        "Agents": ["agent", "task tool", "subagent", "subagent_type"],
        "Settings": ["setting", "permissions", "settings.json"],
        "CLI": ["cli", "flag", "--", "environment variable"],
    }

    for section, keywords in section_keywords.items():
        if any(kw in claim_lower for kw in keywords):
            return section

    return "General"


def infer_severity(claim: str) -> str:
    """Infer severity from claim keywords."""
    claim_lower = claim.lower()

    # Critical indicators
    if any(kw in claim_lower for kw in ["exit code", "required", "must", "block", "error"]):
        return "CRITICAL"

    # High indicators
    if any(kw in claim_lower for kw in ["default", "limit", "max", "min", "timeout"]):
        return "HIGH"

    return "LOW"
```

#### Step 2: Add --quick-add argument

**Location:** In argument parsing, after the `--add` group (around line 180), add:

```python
    parser.add_argument(
        "--quick-add",
        action="store_true",
        help="Quick add with smart defaults (infers section and severity)",
    )
```

#### Step 3: Modify cmd_add to support quick-add

**Location:** In the `cmd_add` function (around line 340), modify the section validation:

Find the section that validates `args.add_section` and modify to:

```python
    # Handle quick-add: infer missing fields
    if args.quick_add:
        if not args.add_section:
            args.add_section = infer_section(args.claim)
            print(f"Inferred section: {args.add_section}")

        if not args.severity:
            args.severity = infer_severity(args.claim)
            print(f"Inferred severity: {args.severity}")

    # Validate section (now required after potential inference)
    if not args.add_section:
        print("Error: --add-section is required (or use --quick-add)", file=sys.stderr)
        return 1
```

#### Step 4: Commit

```bash
git add .claude/skills/verify/scripts/verify.py
git commit -m "feat(verify): add quick-add mode with smart defaults

- --quick-add infers section from claim keywords
- Infers severity based on impact indicators
- Reduces friction for capturing claims during verification"
```

---

## Phase 3: Documentation

### Task 3.1: Update SKILL.md

**Files:**
- Modify: `.claude/skills/verify/SKILL.md`

#### Changes Required

**1. Update frontmatter (line 8):**

```yaml
metadata:
  version: "3.0.0"
  model: claude-sonnet-4-20250514
  timelessness_score: 8
```

**2. Add to Quick Start section (after line 55):**

```markdown
**Validate source URLs:**
```
python scripts/verify.py --validate-urls

→ Checks documentation URLs → Reports broken links
```

**Backup and restore:**
```
python scripts/backup_cache.py backup    # Create backup
python scripts/backup_cache.py list      # List backups
python scripts/backup_cache.py restore   # Restore latest
```
```

**3. Add to Components table (around line 295):**

```markdown
| `scripts/validate_sources.py` | Validate documentation source URLs |
| `scripts/backup_cache.py` | Backup and restore cache |
| `tests/` | Unit tests for scripts |
```

**4. Add to Scripts Quick Reference (around line 315):**

```markdown
| `verify.py` | `python scripts/verify.py --validate-urls` |
| `verify.py` | `python scripts/verify.py --backup` |
| `verify.py` | `python scripts/verify.py --restore` |
| `backup_cache.py` | `python scripts/backup_cache.py list --diff` |
```

**5. Add to Extension Points table:**

```markdown
| Source URL validation | `scripts/validate_sources.py` | ✓ |
| Cache backup/restore | `scripts/backup_cache.py` | ✓ |
| Quick-add inference | `infer_section()`, `infer_severity()` | ✓ |
```

**6. Add changelog entry (after line 354):**

```markdown
### v3.0.0
- **Source URL validation**: New `validate_sources.py` detects broken documentation links
  - Rate limiting prevents server blocking
  - `--validate-urls` flag in unified CLI
- **Cache backup/restore**: Automatic backups before promotion, manual control via `backup_cache.py`
  - Rolling backups (keeps last 5)
  - `--backup`, `--restore`, `--list-backups` flags
- **Interactive batch mode**: `batch_verify.py --interactive` for human oversight
  - Per-claim confirm/skip/edit/quit
- **Quick-add mode**: `verify.py --quick-add` with smart section/severity inference
- **Test coverage**: Unit tests for _common.py, match_claim.py, validate_sources.py, backup_cache.py
- Timelessness score increased from 7 to 8 (added resilience, not just features)
```

---

### Task 3.2: Update scripts-reference.md

**Files:**
- Modify: `.claude/skills/verify/references/scripts-reference.md`

#### Add after batch_verify.py section (around line 200):

```markdown
---

## validate_sources.py

Validate source documentation URLs in known-claims.md.

### Usage

```bash
# Validate all source URLs
python scripts/validate_sources.py

# Validate specific section
python scripts/validate_sources.py --section Skills

# JSON output for scripting
python scripts/validate_sources.py --json

# Custom timeout and rate limit
python scripts/validate_sources.py --timeout 15 --rate-limit 2.0
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--known-claims PATH` | references/known-claims.md | Path to claims file |
| `--timeout SECONDS` | 10 | HTTP request timeout |
| `--rate-limit SECONDS` | 1.0 | Delay between requests |
| `--section NAME` | (all) | Filter to specific section |
| `--json` | false | Output as JSON |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All URLs valid |
| 1 | Input error (file not found) |
| 2 | One or more URLs invalid |

---

## backup_cache.py

Backup and restore known-claims.md cache.

### Usage

```bash
# Create backup
python scripts/backup_cache.py backup

# List available backups
python scripts/backup_cache.py list
python scripts/backup_cache.py list --diff  # Show changes

# Restore from latest backup
python scripts/backup_cache.py restore

# Restore specific backup
python scripts/backup_cache.py restore 20260106_120000

# Preview restore
python scripts/backup_cache.py restore --dry-run
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Input error |
| 10 | No backups available to restore |

### Behavior

- Keeps rolling 5 backups (oldest automatically deleted)
- Creates backup of current file before restore (safety net)
- Backups stored in `references/.backups/`
- Auto-backup runs before every promote operation
```

---

### Task 3.3: Commit Documentation

```bash
git add .claude/skills/verify/SKILL.md
git add .claude/skills/verify/references/scripts-reference.md
git commit -m "docs(verify): update documentation for v3.0.0

- Add validate_sources.py and backup_cache.py to components
- Add new CLI flags to quick reference
- Document interactive batch and quick-add modes
- Update changelog with v3.0.0 features"
```

---

## Final Steps

### Version Bump and Tag

```bash
# Final commit with version bump
git add -A
git commit -m "chore(verify): bump version to 3.0.0"

# Tag release
git tag -a verify-v3.0.0 -m "Verify skill v3.0.0: URL validation, backup/restore, tests"
```

---

## File Summary

| File | Action | Priority | Phase |
|------|--------|----------|-------|
| `scripts/validate_sources.py` | Create | Critical | 1 |
| `scripts/backup_cache.py` | Create | High | 1 |
| `scripts/verify.py` | Modify | Critical+High | 1 |
| `scripts/promote_claims.py` | Modify | High | 1 |
| `tests/__init__.py` | Create | High | 1 |
| `tests/test_common.py` | Create | High | 1 |
| `tests/test_match_claim.py` | Create | High | 1 |
| `tests/test_validate_sources.py` | Create | High | 1 |
| `tests/test_backup_cache.py` | Create | High | 1 |
| `references/.backups/.gitkeep` | Create | High | 1 |
| `references/.backups/.gitignore` | Create | High | 1 |
| `scripts/batch_verify.py` | Modify | Medium | 2 |
| `SKILL.md` | Modify | All | 3 |
| `references/scripts-reference.md` | Modify | All | 3 |

---

## Verification Checklist

After implementation:

- [ ] `python scripts/validate_sources.py` runs without error
- [ ] `python scripts/backup_cache.py backup` creates backup
- [ ] `python scripts/backup_cache.py restore --dry-run` shows diff
- [ ] `python scripts/verify.py --validate-urls` works
- [ ] `python scripts/verify.py --backup` works
- [ ] `python scripts/verify.py --quick-add --claim "test" --verdict verified --evidence "test"` infers section
- [ ] `python -m pytest tests/ -v` all tests pass
- [ ] promote_claims creates backup before writing
- [ ] SKILL.md shows version 3.0.0
- [ ] scripts-reference.md includes new scripts
