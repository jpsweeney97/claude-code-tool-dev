# Verify Skill v3.0.0 Improvement Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan phase-by-phase.

**Goal:** Evolve verify skill from v2.6.1 to v3.0.0 with improved reliability, usability, and maintainability.

**Current State:** 76 verified claims, 10 scripts, timelessness score 7/10

**Target State:** URL validation, backup/restore, interactive batch, test coverage, timelessness score 8/10

**Tech Stack:** Python 3.12, standard library only (no external dependencies)

---

## Summary of Improvements

| Priority | Improvement | Effort | Phase |
|----------|-------------|--------|-------|
| Critical | Source URL Validation | Medium | 1 |
| High | Cache Backup and Restore | Low | 1 |
| High | Interactive Batch Verification | Medium | 2 |
| Low | Quick-Add from Conversation | Low | 2 |
| Medium | Script Test Coverage | Medium | 3 |

---

## Phase 1: Foundation

### Task 1.1: Create Source URL Validation Script

**Files:**
- Create: `.claude/skills/verify/scripts/validate_sources.py`

**Step 1: Write the script**

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


def validate_sources(known_path: Path, timeout: int = 10) -> ValidationResult:
    """Validate all source URLs in known-claims.md."""
    result = ValidationResult()

    if not known_path.exists():
        return result

    content = known_path.read_text(encoding="utf-8")
    urls = extract_source_urls(content)

    for section, url in urls.items():
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
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if not args.known_claims.exists():
        print(f"Error: {args.known_claims} not found", file=sys.stderr)
        return 1

    result = validate_sources(args.known_claims, args.timeout)

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

**Step 2: Test the script**

```bash
python .claude/skills/verify/scripts/validate_sources.py
```

Expected: Report showing valid/invalid URLs

**Step 3: Integrate with verify.py**

Add `--validate-urls` flag to verify.py that calls validate_sources.

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/validate_sources.py
git commit -m "feat(verify): add source URL validation script"
```

---

### Task 1.2: Create Cache Backup and Restore Script

**Files:**
- Create: `.claude/skills/verify/scripts/backup_cache.py`
- Create: `.claude/skills/verify/references/.backups/` directory

**Step 1: Write the backup script**

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup and restore known-claims.md")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # backup command
    backup_parser = subparsers.add_parser("backup", help="Create backup")
    backup_parser.add_argument("--source", type=Path, default=KNOWN_CLAIMS)

    # list command
    list_parser = subparsers.add_parser("list", help="List backups")

    # restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup", nargs="?", help="Backup file to restore (latest if omitted)")

    args = parser.parse_args()

    if args.command == "backup":
        backup_path = create_backup(args.source)
        if backup_path:
            print(f"Created backup: {backup_path}")
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
                print(f"  {i+1}. {timestamp} ({size:,} bytes){marker}")
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

        if restore_backup(backup_path):
            print(f"Restored from: {backup_path}")
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

**Step 2: Test the script**

```bash
python .claude/skills/verify/scripts/backup_cache.py backup
python .claude/skills/verify/scripts/backup_cache.py list
```

**Step 3: Integrate with promote_claims.py**

Add auto-backup call before writing to known-claims.md:

```python
# At top of promote_claims.py, add import
from backup_cache import create_backup

# Before writing to known_path, add:
create_backup(known_path)
```

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/backup_cache.py
git add .claude/skills/verify/references/.backups/.gitkeep
git commit -m "feat(verify): add cache backup and restore script"
```

---

## Phase 2: Usability

### Task 2.1: Add Interactive Batch Verification

**Files:**
- Modify: `.claude/skills/verify/scripts/batch_verify.py`

**Step 1: Add --interactive flag and implementation**

Add after line ~50 (argument parsing):

```python
parser.add_argument(
    "--interactive",
    action="store_true",
    help="Confirm each claim interactively",
)
```

Add interactive confirmation function:

```python
def confirm_claim(claim: dict) -> str:
    """Prompt user to confirm, skip, or edit a claim verdict."""
    print(f"\nClaim: {claim['claim']}")
    print(f"  Verdict: {claim['verdict']}")
    print(f"  Evidence: {claim['evidence'][:100]}...")
    print(f"  Section: {claim['section']}")

    while True:
        response = input("\n[c]onfirm, [s]kip, [e]dit verdict? ").strip().lower()
        if response in ("c", "confirm", ""):
            return "confirm"
        elif response in ("s", "skip"):
            return "skip"
        elif response in ("e", "edit"):
            new_verdict = input("New verdict (verified/false/partial/unverified): ").strip()
            if new_verdict in ("verified", "false", "partial", "unverified"):
                claim["verdict"] = new_verdict
                return "confirm"
            else:
                print("Invalid verdict")
        else:
            print("Invalid response")
```

**Step 2: Integrate into main loop**

Modify the batch processing loop to call confirm_claim when --interactive is set.

**Step 3: Test**

```bash
python .claude/skills/verify/scripts/batch_verify.py --interactive --dry-run
```

**Step 4: Commit**

```bash
git add .claude/skills/verify/scripts/batch_verify.py
git commit -m "feat(verify): add interactive mode to batch verification"
```

---

### Task 2.2: Add Quick-Add Mode

**Files:**
- Modify: `.claude/skills/verify/scripts/verify.py`

**Step 1: Add --quick-add flag**

Add after existing --add arguments:

```python
parser.add_argument(
    "--quick-add",
    action="store_true",
    help="Quick add with smart defaults (prompts for missing fields)",
)
```

**Step 2: Implement smart defaults**

```python
def infer_section(claim: str) -> str:
    """Infer section from claim keywords."""
    claim_lower = claim.lower()
    if any(kw in claim_lower for kw in ("hook", "exit code", "pretooluse", "posttooluse")):
        return "Hooks"
    elif any(kw in claim_lower for kw in ("skill", "frontmatter", "allowed-tools")):
        return "Skills"
    elif any(kw in claim_lower for kw in ("command", "$arguments", "slash")):
        return "Commands"
    elif any(kw in claim_lower for kw in ("mcp", ".mcp.json", "server")):
        return "MCP"
    elif any(kw in claim_lower for kw in ("agent", "task tool", "subagent")):
        return "Agents"
    return "General"


def infer_severity(claim: str) -> str:
    """Infer severity from claim keywords."""
    claim_lower = claim.lower()
    if any(kw in claim_lower for kw in ("exit code", "required", "must", "block")):
        return "CRITICAL"
    elif any(kw in claim_lower for kw in ("default", "limit", "max")):
        return "HIGH"
    return "LOW"
```

**Step 3: Commit**

```bash
git add .claude/skills/verify/scripts/verify.py
git commit -m "feat(verify): add quick-add mode with smart defaults"
```

---

## Phase 3: Quality

### Task 3.1: Create Test Directory Structure

**Files:**
- Create: `.claude/skills/verify/tests/__init__.py`
- Create: `.claude/skills/verify/tests/test_common.py`
- Create: `.claude/skills/verify/tests/test_match_claim.py`

**Step 1: Create test_common.py**

```python
#!/usr/bin/env python3
"""Tests for _common.py utilities."""

import sys
import unittest
from datetime import date
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from _common import parse_verified_date, Version, DEFAULT_MAX_AGE_DAYS


class TestParseVerifiedDate(unittest.TestCase):
    """Tests for parse_verified_date function."""

    def test_plain_date(self):
        result = parse_verified_date("2026-01-05")
        self.assertEqual(result, date(2026, 1, 5))

    def test_version_tagged_date(self):
        result = parse_verified_date("2026-01-05 (v2.0.76)")
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


class TestVersion(unittest.TestCase):
    """Tests for Version class."""

    def test_parse_simple(self):
        v = Version.parse("2.0.76")
        self.assertEqual(v.major, 2)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 76)
        self.assertIsNone(v.prerelease)

    def test_parse_with_v_prefix(self):
        v = Version.parse("v2.0.76")
        self.assertEqual(v.major, 2)

    def test_parse_with_prerelease(self):
        v = Version.parse("3.0.0-beta.1")
        self.assertEqual(v.prerelease, "beta.1")

    def test_parse_invalid(self):
        v = Version.parse("not-a-version")
        self.assertIsNone(v)

    def test_str(self):
        v = Version(2, 0, 76)
        self.assertEqual(str(v), "2.0.76")


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_default_max_age_days(self):
        self.assertEqual(DEFAULT_MAX_AGE_DAYS, 90)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run tests**

```bash
cd .claude/skills/verify && python -m pytest tests/ -v
# Or without pytest:
python tests/test_common.py
```

**Step 3: Add test_match_claim.py with matching accuracy tests**

**Step 4: Commit**

```bash
git add .claude/skills/verify/tests/
git commit -m "test(verify): add unit tests for common utilities"
```

---

## Version Update

After all improvements, update SKILL.md:

```yaml
metadata:
  version: "3.0.0"
```

Add changelog entry:

```markdown
### v3.0.0
- **Source URL validation**: New `validate_sources.py` detects broken documentation links
- **Cache backup/restore**: Automatic backups before promotion, `backup_cache.py` for manual control
- **Interactive batch mode**: `batch_verify.py --interactive` for human oversight
- **Quick-add mode**: `verify.py --quick-add` with smart section/severity inference
- **Test coverage**: Unit tests for _common.py and match_claim.py
- Timelessness score increased from 7 to 8
```

---

## File Summary

| File | Action | Priority |
|------|--------|----------|
| `scripts/validate_sources.py` | Create | Critical |
| `scripts/backup_cache.py` | Create | High |
| `scripts/batch_verify.py` | Modify | High |
| `scripts/verify.py` | Modify | High + Low |
| `scripts/promote_claims.py` | Modify | High |
| `tests/__init__.py` | Create | Medium |
| `tests/test_common.py` | Create | Medium |
| `tests/test_match_claim.py` | Create | Medium |
| `references/.backups/.gitkeep` | Create | High |
| `SKILL.md` | Modify | All |
| `references/scripts-reference.md` | Modify | All |
